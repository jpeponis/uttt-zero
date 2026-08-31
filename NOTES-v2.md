# v2 notes — review of the v1 pipeline and candidate optimisations

Written 2026-08-29 while `runs/dev1` was training. Nothing here is implemented
yet. Items are ordered by expected payoff per hour of work. Numbers marked
*measured* come from `tests/diag_search.py` (run on the idle 3060, n=1024,
8 sims) and `tests/bench_net.py`.

## 0. Correctness review (no changes needed for the running job)

Re-read `batch.py`, `mcts.py`, `selfplay.py`, `train.py`, `arena.py`, `model.py`.

- Gumbel search matches mctx step by step: Sequential-Halving table, root score
  `g + logits + σ(q̂)` restricted to `N == considered_visit`, interior rule
  `π' − N/(1+ΣN)`, completed-Q with the mixed value, final action = best among
  the most-visited, policy target `softmax(logits + σ(completed q̂))`. One
  deliberate deviation: min/max rescaling of q̂ uses legal actions only (mctx
  uses all actions) — harmless, arguably better.
- Symmetry pipeline is consistent end to end: `apply_symmetry` permutes cells
  with `SYM_CELL_INV[s]`, macro/ownership with `SYM_BOARD_INV[s]`, policy with
  `SYM_CELL_INV[s]`; verified by replaying transformed move sequences.
- Policy index conversion (grid ↔ engine order) is applied identically in
  `Evaluator` and `train_steps` (`logits[:, INV_PERM]`).
- Value/ownership class mapping `(1 − target).clamp(0,2)` → win 0 / draw 1 / loss 2.
- Terminal roots (finished games inside a lock-step batch) are handled: the
  selection loop stops immediately, no node is expanded, nothing is recorded.
- Things that are *not bugs but worth knowing*:
  - `c_scale = 0.1` follows mctx's `value_scale` default with q̂ rescaled to
    [0,1]; the paper's text quotes `c_scale = 1.0`. This is a 10× difference in
    how sharply the improved policy follows Q. A/B it (item 3.6).
  - PUCT mode's Dirichlet α = 1.0 is right for ~9 legal moves but too large for
    free-move positions (up to ~50 legal moves). Not used by dev1 (Gumbel).
  - One symmetry is drawn *per training batch*, not per sample (item 4.4).
  - `latest.pt` re-saves the whole replay buffer (~0.5 GB) every iteration.

## 1. Search throughput — the dominant cost (expected 3–6× overall)

*Measured*: per simulation, uniform evaluator, n=1024: **548 CUDA kernels,
45 host↔device synchronisations, GPU busy 1.2 ms, CPU 24.6 ms.** With the
6×64 net: 720 kernels, GPU busy 10.5 ms. At n=4096 the wall-clock is ~17 ms of
tree work + ~17 ms of network per simulation, and `nvidia-smi` shows ~33 %
utilisation during training. The tree work is almost entirely launch overhead
and sync stalls (Windows/WDDM launch latency is ~2–4× Linux's).

1.1 **Remove every per-simulation sync** (largest single win, ~2× on tree ops).
    Sources, all in `mcts.py`:
    - `bool(active.any())` per depth level → bound the loop by a tracked
      `max_depth_seen + 1` (a tree's depth grows ≤ 1 per simulation) or by a
      fixed small D and treat the unfinished descent as the leaf.
    - `int(depth.max().item())` + `int(valid.sum())` per backup level → one
      vectorised backup: nodes `path[:, :D+1]`, `valid = j <= depth[:,None]`,
      `sign = (−1)^(depth−j)`, then a single `index_add_` on the flattened
      `(game*M + node)` index for `visit` and for `value_sum`.
    - `_put` boolean-mask assignments (7 fields × `nonzero`) → `torch.where`
      full-row writes: `s_cells[:, slot] = where(mask[:,None], cells, s_cells[:, slot])`.
    - `self.children[idx[need_expand], parent[need_expand], action[need_expand]] = i`
      → write for all rows with a dummy slot for non-expanding games, or
      `index_put_` on precomputed flat indices with a masked value.
    - `selfplay.py`: `res.policy[active]` etc. per ply → record everything and
      filter once at the end; `float(...)` of surprise per ply → accumulate on GPU.
1.2 **Edge-statistics layout.** Store `N[n,M,81]` and `W[n,M,81]` on the parent
    (from the parent's perspective) instead of gathering child rows through the
    `children` table. Selection becomes two gathers instead of five ops plus
    `where`; backup needs the action taken at each path step (`path_actions`).
    Cuts ~⅓ of the launches and removes the −W/N sign juggling.
1.3 **CUDA-graph the simulation.** Once 1.1 makes the simulation shape-static
    and sync-free (fixed depth loop D, e.g. 12, with truncation), capture
    selection + expansion + network forward + backup as one `torch.cuda.CUDAGraph`
    and replay it `n_sims` times per move; the Gumbel schedule column and the
    simulation index become static input tensors updated by `copy_`. Expected:
    tree work → ~1–2 ms/sim (its measured GPU time), leaving the net.
1.4 **Bigger batches once the tree work is cheap**: 8192–16384 parallel games
    make the run network-bound; positions/iteration scale accordingly, so
    also scale training steps (item 4).
1.5 **Continuous self-play instead of lock-step-to-the-last-game.** The batch
    currently runs until its *longest* game ends (up to ~75–81 plies) while the
    mean is 43–55; tail steps cost nearly as much as full steps because the
    cost is per simulation, not per live game. Reset finished games in place
    and run a fixed number of plies per iteration; assign outcomes per game id
    when each game ends (pgx/turbozero pattern). Expected ~1.4×.
1.6 **`torch.compile` via `triton-windows`** for the selection step (fuses the
    ~30 elementwise/gather ops per level into a handful). Optional if 1.3 works;
    cheaper to try first (pip install, `@torch.compile` on a function).
1.7 Windows settings to check before optimising: Hardware-accelerated GPU
    scheduling (Settings → Display → Graphics → Default graphics settings),
    and that the desktop is driven by the 3060, not the 3090.

## 2. Network inference (expected ~1.5×)

*Measured* on the 6×64 net, batch 1024 fp16 (per 8 sims): conv 27 ms,
**BatchNorm inference 15 ms (135 kernels)**, **NCHW↔NHWC conversions 15 ms
(324 kernels)**, elementwise 13 ms.

2.1 **Fold BatchNorm into the conv weights** for the inference copy
    (`torch.nn.utils.fusion.fuse_conv_bn_eval`) — removes ~18 % of GPU time and
    ~17 kernels/sim.
2.2 **`channels_last` + a true `.half()` inference copy** (no autocast casts):
    kills the layout-conversion kernels (~18 %) and per-op cast launches.
    Refresh the inference copy from the training weights once per iteration.
2.3 The conv itself: cudnn's implicit-GEMM at 9×9 spatial is ~50 % of the 3090's
    fp16 peak — acceptable. A 4×64 net is ~1.7× faster (0.39 vs 0.24 M pos/s)
    if strength permits; decide after dev1 plateaus. TensorRT is the only path
    to substantially better small-conv kernels; not worth it yet.
2.4 `encode()` recomputes the legal mask that the evaluator also computes;
    pass it in. Build planes directly in fp16.
2.5 Overlap tree work and network on two CUDA streams (ping-pong halves of the
    batch) — only relevant if 1.3 leaves the CPU as the bottleneck.

## 3. Learning efficiency (same games → stronger net)

3.1 **Persist the games.** Save each iteration's move sequences (uint8, ≤81
    per game; 4096 games ≈ 330 KB) plus root values. This is the corpus for
    Phase E statistics *and* lets us replay training history. Cheap; do first.
3.2 **Score-margin auxiliary head** (won-board difference at the end, 17 bins
    from −8..+8, or a regression) — the tiebreak is decided by this quantity;
    KataGo's score head was its largest single data-efficiency gain.
3.3 **Value target = mix of game result z and search root value** (e.g. 0.5/0.5,
    or z for the last k plies only): lower-variance targets; standard in
    reproductions that report faster early learning. Root values are already
    computed; store them in the buffer.
3.4 **Replay window schedule**: start ~4 iterations, grow to ~20 as the net
    stabilises (Oracle, KataGo). Currently fixed at 2 M positions ≈ 10 iterations.
3.5 **Learning-rate schedule**: warm-up 200 steps, then drop ×0.1 twice when
    `eval_vs_prev` stops improving; or switch to AdamW 1e-3 for the small net.
3.6 **A/B `c_scale` 0.1 vs 1.0** and `m_considered` 16 vs 9 at 32 sims; then
    **progressive sims** 32 → 64 → 128 after the plateau.
3.7 **Opening diversity**: all 4096 games start from the empty board and only
    Gumbel noise separates them; log the first-move histogram and the fraction
    of duplicated positions in the buffer per ply. Options: start a fraction of
    games from buffer-sampled positions, or weight duplicated positions down.
3.8 Extra input planes (cheap): side-to-move is X (first-player parity),
    "free move" flag, won-board count difference broadcast. The count plane
    gives the tiebreak logic directly instead of having to be computed by convs.
3.9 Per-sample symmetry during training (currently one symmetry per batch).
3.10 Consider playout-cap randomisation only if we return to PUCT; with Gumbel
    at 32 sims the paper's argument for it mostly disappears.

## 4. Training loop hygiene (small but free)

4.1 GPU-resident replay buffer (2 M positions ≈ 0.55 GB) → no CPU gather + H2D
    per step; training is 54 ms/step for a 0.5 M-param net, which is mostly
    host overhead.
4.2 Hoist `INV_PERM.to(device)` / `SYM_BOARD_INV.to(device)` out of the step
    loop; accumulate loss metrics on the GPU; one `.item()` per iteration.
4.3 Save the replay buffer every N iterations (or keep only positions, no
    optimiser state) — `latest.pt` is ~0.5 GB every 2.5 min.
4.4 Per-sample symmetry (see 3.9).
4.5 Log: first-move histogram (15 orbits), policy entropy by ply, buffer
    duplicate rate, end-by-count share under *evaluation* play, time split
    (self-play / train / eval / save).

## 5. Evaluation (needed before any strength claim)

5.1 **Anchor pool + Bayesian Elo**: random, uniform-UCT at 64/256/1024 sims,
    every 10th checkpoint; run matches on the 3060 in a separate process so
    the 3090 never idles (evaluation is ~15 % of dev1's wall-clock).
5.2 **Paired openings**: the two side-swapped halves of a match should reuse
    the same random opening moves (seeded), halving variance.
5.3 **Exact labels**: a Numba alpha-beta for positions with ≤ 2 open boards
    (fast — few plies remain) → a fixed test set of ~10 k solved positions;
    report value-head accuracy and search accuracy on it every evaluation.
    Later the K = 1-open-board tablebase (knowledge/06).
5.4 **External anchor**: Numba bitboard MCTS with random rollouts, ~100 k
    rollouts/turn — the CodinGame-Legend recipe — to get absolute strength.
5.5 **Symmetry-averaged inference** (8 transforms per position) for evaluation
    and analysis modes only.

## 6. Architecture for v2 (process layout)

- Self-play process on the 3090 (search + inference copy of the net, fp16,
  BN folded, CUDA-graphed).
- Trainer process on the 3060 (or the 3090 if idle) reading a shared on-disk
  position store (memory-mapped numpy files per iteration); publishes weights
  every k steps; self-play reloads them between moves.
- Evaluator process on the 3060 running the anchor matches on new checkpoints.
- Expected combined effect of §1–2 on this machine: from ~30 games/s (dev1)
  to ~150–250 games/s at 32 sims, i.e. ~1 M games in 1–2 h.

## 7. Verification to add before trusting v2

- Cross-check Gumbel numerics against mctx on CPU (`pip install jax mctx`,
  CPU only, works on Windows): identical tree statistics for a handful of
  positions with fixed Gumbel samples.
- Golden test: v1 vs v2 search must produce identical visit counts on fixed
  positions with the uniform evaluator (before/after each refactor step).
- `torch.cuda.set_sync_debug_mode("error")` around a search in the test
  suite so syncs cannot creep back in.

## 8. Status (2026-08-29, after run dev1)

Implemented and tested (`tests/test_search_v2.py`, `tests/test_infer.py`, `tests/test_selfplay_cont.py`):

- 1.1 sync removal: `uttt/search.py` — 2 host syncs per simulation (was 45); identical trees to v1 in all modes.
- 1.2 edge statistics + vectorised backup: same file. Tree work 12.4 ms/sim vs 17.8 (3090, 4096 trees, uniform evaluator).
- 1.5 continuous self-play: `uttt/selfplay_cont.py` (in-place reset, no lock-step tail).
- 2.1 / 2.2 fused inference: `uttt/infer.py` — BN folded, fp16 weights, channels_last: 11.6 ms vs 16.8 ms per 4096 positions.
- 3.1 game persistence: `runs/<run>/games/games_NNNN.npz`; `tools/corpus_stats.py` reads them.
- 3.2 margin head (`MARGIN_BINS = 19`) in `uttt/model.py`; margin target recorded per position.
- 3.5 LR warm-up and step drops (`--lr_drops`), 3.9 / 4.4 per-sample symmetry, 4.1 GPU replay buffer, 4.3 buffer saved every N iterations: `uttt/train2.py`.
- Lessons from dev1 (RESULTS-dev1.md): `--sample_moves` (early moves sampled from the improved policy), `--root_prior_floor`, duplicate down-weighting `count^-alpha` (`--dedup_alpha`), per-iteration diversity logging (first-move distinct count/share, duplicate counts by ply).
- 5: evaluation is now a small side-swapped match vs fixed anchor checkpoints (`--anchors`, default dev1 `net_0200`) with the v2 search; the UCT anchor is gone.
- `arena.SearchPlayer` uses the v2 search, so `tools/ladder.py`, `tools/match.py` and `uttt/train.py` inherit it.

Not done yet: 1.3 CUDA graphs (the remaining ~12 ms/sim of tree work is launch overhead), 1.4 bigger batches
(now cheap to try), 1.6 torch.compile, 2.5 stream overlap, 3.3 search-value mixing (root values are recorded,
head not added), 3.7 buffer-sampled openings, 5.2 paired openings, 5.3 exact-label test set, 5.4 rollout-MCTS
anchor, 5.5 symmetry-averaged inference, 6 multi-process layout.

### 8.1 CUDA-graph mode (done)

`SearchConfig(cuda_graph=True)`: one graph per descent length (`levels = min(i, depth_cap)`), captured on first
use on a private pool after two warm-up runs (tree state snapshotted and restored around capture), with the
simulation slot, Gumbel schedule column, Gumbel noise and root logits as static tensors. Constant index tensors
are now cached per device (`batch.consts`) — the per-call host->device copies were both a launch cost and a
capture blocker. `FusedEvaluator.refresh` copies weights in place so captured graphs follow training.
`tests/test_search_graph.py`: identical trees to eager mode (capture pass and replay pass), both search modes,
with and without the net. Benchmark on the 3060 while two other launch-bound jobs were running: tree work
66 -> 7.4 ms/sim, with the fused 6x64 net 111 -> 40 ms/sim (4096 trees, 32 sims). Graph replay is nearly
immune to host contention, which also makes the multi-process layout (§6) viable.
`SearchResult.visits/raw_value` are now clones (they aliased tree buffers overwritten by the next search).

Measured in production (`runs/v2a`, 3090, 4096 games x 32 sims, 6x64 fused net): self-play per 64-move iteration
100 s (eager v2) -> 25 s (graph mode); 155-170 finished games/s vs dev1's 25-33; ~10k positions/s; GPU 84 % busy.
Training (256 steps of 1024) is now 8-14 s of the ~35 s iteration — next candidate for the 3060.

### 8.2 After run v2a (RESULTS-v2a.md)

Added for v2b: `--sample_uniform` exploration floor for the sampled opening plies (sampling ∝ policy alone
re-collapsed the openings once the policy sharpened), `--sims_schedule` (progressive simulations; the
search object is rebuilt when the budget changes), graph-mode in-run evaluation, `tools/plot_run.py`
reads in-run anchor scores. `uttt/symmetry.py`: exactly equivariant symmetry-averaged evaluator (dev1's
net differs from its symmetry average by up to 0.21 in value). `tools/analyze_opening.py`: per-orbit deep
search after each first move — the raw net and the search disagree most on the two "cell 4" orbits
(centre of a non-centre board), which hand O the centre board.

### 8.3 Analysis tooling (after v2a)

`tools/probe_value.py` (counterfactual value probes), `tools/surprise.py` (net-vs-search disagreement),
`uttt/solver.py` + `tools/endgame_accuracy.py` (5.3: exact endgame labels; 3,000 positions with <= 16 moves
left solve in ~90 s; the 256-sim search's move-error rate there is 0.2 %, the raw value head's 3-way accuracy
78 %). Results in RESULTS-v2a.md §2b-2d.

### 8.4 Paired opening suite (PLAN2 §5 step 1a, after v2b)

`uttt/openings.py` + `tools/openings.py` + `tests/test_openings.py`. Suite `suites/openings_v1.npz` = empty board,
15 first-move orbit representatives, 250 natural 4-ply openings (canonical D4 forms of prefixes from the last 20
game files of `runs/v2a`, drawn without replacement ∝ frequency) and 250 uniformly random legal 4-ply openings
(canonical, disjoint from the natural set). Every opening is played with both colours; the pair score
(s_AX + s_AO)/2 is the unit, CIs are percentile bootstraps over pairs, Elo is mapped through the CI. The players
are deterministic (Gumbel scale 0), so the suite size is the sample size: 1032 games, ~45 s at 64 sims on the 3090.
`train2.evaluate` now plays the first 100 natural + 100 random openings plus empty + orbits (`--eval_openings`,
432 games per anchor, ~75 s for two anchors) and logs `vs_<anchor>`, `ci_<anchor>`, `suites_<anchor>`;
`--suite ''` restores the old unpaired random-2-ply evaluation. `tools/match.py` is unchanged (unpaired, for
comparison with older numbers).
Determinism caveat: a repeated evaluate() in one process is bit-identical, but the same match in two
processes differed by 0.4 points (62.9 vs 63.3 %, v2b vs dev1 @64) — cuDNN picks fp16 conv algorithms per
process (workspace/memory dependent), and a rounding flip in one logit changes a move. Inside the CI, not zero.

### 8.5 Rollout anchor and frozen endgame set (PLAN2 §5 steps 1b, 1c)

`uttt/rollout.py`: plain UCT (c = 1.4, rewards in [0, 1], one node per playout, linked-list children, 81-bit
untried mask, most-visited root child) with uniformly random playouts on 9-bit bitboards, Numba, one game per
thread (`prange`), no tree reuse. Rules re-implemented from scratch and checked move by move against
`uttt.game` (tests/test_rollout.py); 20 k-playout UCT keeps the exact value on 40/40 solved endgames.
Throughput on the 3900X: 0.21 M playouts/s per thread, 3.7 M/s on 24 threads; a full paired-suite match at
100 k playouts/move costs ~10–15 min. `tools/openings.py match --a rollout --a_sims 100000`.

`uttt/endgame.py` + `tools/endgame.py`: positions with 6–16 empties in open boards taken from replayed corpus
games (≤ 2 per game, provenance = file/game/ply), solved together with every legal child (`solve_children`,
multiprocessing pool), and selected to fill 24 strata (4 empties buckets × W/D/L × side to move) with equal
counts. Metrics: WDL-argmax accuracy, Brier, log-loss (value head as a 3-class predictor), scalar 3-way
accuracy (continuity with the old tool), action regret (exact value lost by the chosen move) and optimal-move
rate; 95 % CIs from a cluster bootstrap over source games. `tools/endgame_accuracy.py` is superseded.

### 8.6 Exact-label training (PLAN2 §5 step 2; run v2c)

`uttt/exact.py` `ExactLabeler`: after `buf.add`, sample ≤ `exact_per_iter` of the iteration's finished-game
positions with ≤ `exact_max_empty` empties in open boards and send them to a `multiprocessing.Pool`
(`uttt.solver.solve_batch`, numpy/numba-only workers) while the trainer runs; after training, `collect()`
returns exact values and uniform-over-optimal-moves policies, `buf.apply_exact` overwrites those rows
(`value`, `policy`, flag `exact`), and `update_weights(alpha, exact_weight)` multiplies their sampling weight.
Solve cost with children (contended CPU): ≤ 11 empties ~1 ms, 12 ~14 ms, 13–14 25–65 ms, 15–16 ~0.4 s —
hence `exact_max_empty 14`. With 8192 positions and 12 workers the labels are ready before training ends
(`t_exact_wait` 0). Under uniform-evaluator 8-sim self-play 18 % of ≤ 10-empties labels differed from z.
Log keys: `exact_new`, `exact_total`, `exact_frac` (buffer share), `exact_wdl`, `t_exact_wait`; the endgame
set is scored at every evaluation (`eg_wdl_acc`, `eg_brier`, `eg_regret_raw`, `eg_optimal_raw`,
`eg_acc3_search`, `eg_regret_search`, `eg_optimal_search`).

### 8.7 Steps 3 and 4 (after v2b; while v2c trained)

Step 3: `SearchResult.cap_hits` counts simulations that descended `depth_cap` levels without expanding (graph-safe
accumulator); self-play logs `cap_hit`. With the v2b net and self-play settings the cap of 12 bites in ≤ 2.3 % of
simulations at 64 sims (ply 6, the deepest trees), 0 % at 32 — non-binding. `arena.PhasedSearchPlayer` schedules
the budget by ply (batch-uniform in paired play); "0:32,24:96" beats uniform 64 by +50 Elo at equal mean cost.
Per-game budgets in self-play would need two search pools; cost ≈ Σ sims in the launch-bound regime, so not
worth it below ~8192 games. Also fixed: `torch.multinomial` device assert when a finished game sat in a
self-play batch during the sampled plies (guarded; production never hit it).

Step 4: `position_hash_sym` (min of the hash over the 8 images), `update_weights(alpha_early)`, ownership stored
as 1 / -1 / 2 (full) / 0 (open) with `OWN_CLASS` maps for 3- and 4-class heads (the 3-class map equals the old
`(1 - own).clamp(0, 2)` on {-1, 0, 1}), `encode(extra=True)` adds the first-player plane and (won boards self -
opponent)/4, `NetConfig(n_planes, own_classes)` is saved in every checkpoint's cfg and `load_checkpoint` rebuilds
the right net; all tools and `play.py` use it. Old checkpoints load unchanged (7 planes, 3 classes).

### 8.8 Analysis programme tools (PLAN2 §5 step 7; rigorous versions)

- `tools/atlas.py`: 15 first-move orbits and their canonical reply classes, deep PUCT search (symmetry-averaged
  evaluator, root prior floor 0) at several budgets with several nets; ranks, Kendall τ between every
  (net, budget) column, best-reply agreement. Search-relative statements only.
- `tools/decision.py`: held-out corpus games replayed in lock-step; per ply the WDL head's log-loss/accuracy for
  the final result, sign accuracy of raw and search values, and "settled" = the 3-way prediction is right from
  this ply to the end; settling-ply quantiles by result.
- `tools/freemove.py`: natural positions (≤ 5 per game, plies 8–50) from a held-out corpus; OLS of the 256-sim
  search value on the free-move indicator with ply, ply², macro score, open boards, empties, side, macro threats
  for/against; cluster-robust SE by game; stratified free-vs-confined table as a check.
- `tools/puzzles.py`: candidates with ≤ 14 empties from held-out games, solved with children; puzzle = raw policy
  argmax loses exact value; hard = the 64-sim search does too; greedy PV, end reason, motif tags
  (local_win, macro_win, closes_board, gives_free_move, denies_free_move, tiebreak_conversion, draw_hold);
  `suites/puzzles_v1.npz` + readable JSON of hard ones. v2b: 208 puzzles / 6000 candidates (3.5 %), 11 hard.
- Provenance: buffer positions now carry `game` (per-self-play-object counter) and `iter`; corpus-derived sets
  carry file/game/ply ids; the opening suite carries opening ids.
Result (run v2c, PLAN2 §2f): no effect — 48.7 % [45.8, 51.4] vs v2b on the paired suite, endgame WDL 75.9 vs
75.0. Diagnostic: on v2b's final buffer z == exact in 98.7 % of positions with ≤ 14 empties (2.3–2.8 % wrong at
10–14, 0.2 % at 6–9), so the labels barely change the targets; the value head's endgame error is capacity, not
label noise. Kept on (free) but not a lever.
Result (run v2d, PLAN2 §2h): 48.2 % [45.4, 50.9] vs v2b, endgame WDL 75.8 — no change; value loss 0.82 → 0.78 with
the extra planes. First-move top share unchanged at 0.82 (the exploration floor dominates). Four 6×64 runs within
±3 points: the plateau is the network's.
Run wide96 (6×96, PLAN2 §2i): 55.1 % [52.3, 58.0] vs v2b (+36 Elo), 68.7 % vs dev1; endgame WDL 76.2, draws 55.9
(unchanged). 57 games/s (2.2× the cost of 6×64). 6×128 queued.

### 8.9 Draw calibration (after wide96)

The value head under-predicts draws (exact draws get p(draw) ≈ 0.5; calibration curve bends upward). `FusedEvaluator(wdl_bias=)`
adds a bias to the WDL logits; `tools/calibrate.py` fits it by maximum likelihood on half of `suites/endgame_v1.npz` (split
by source game) and tests on the other half: v2b 75.1 → 79.6 % WDL accuracy, draws 53 → 81 %, Brier 0.331 → 0.280. In play
(paired suite, 64 sims) the calibrated evaluator is 48.8 % [45.9, 51.6] vs the uncalibrated one — no effect on strength,
more draws. Conclusion: report regret for play; use the bias for value-head analyses; a training-time fix (draw-weighted
value loss) is an optional ablation, unlikely to change Elo.
Ablation c_scale 1.0 (PLAN2 §2j): 55.7 % [52.9, 58.5] vs v2b (+40 Elo) at no cost; adopted. Policy loss 1.15 vs 0.92
(sharper targets), self-play X 62 % / draws 10 %. Next: wide96_c1, wide128_c1 (runs/after_queue2.sh).
