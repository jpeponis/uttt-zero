# uttt-zero — PLAN2: status, lessons, and the road ahead (hand-off, updated 2026-08-30)

Read this first. It supersedes `PLAN.md` (kept as the original plan for comparison).
Detailed sources: `RESULTS-dev1.md`, `RESULTS-v2a.md`, `NOTES-v2.md` (§8 = what is
implemented), `REVIEW-codex.md` (independent outside review), `knowledge/01–06`
(research base), `runs/<run>/{log.jsonl,analysis.out,corpus.out,curves.png}`.

## 1. Where the project stands against the original plan

| Original phase | Status |
|---|---|
| A. Pipeline | Done. Reference + batched GPU engine (cross-checked; 41 M+ positions without a rules bug), D4 symmetries, ResNet with policy/WDL/ownership/margin heads, batched PUCT+Gumbel search (v1 `mcts.py`, v2 `search.py` incl. CUDA-graph mode), continuous self-play, GPU replay buffer, trainer, arena, tests. |
| B. Make it learn well | Runs: dev1 (12 h), v2a (2.75 h), v2b (2.3 h), v2c (+ exact labels, §2f: no gain), v2b_s1 (seed replicate, §2g: ±2.5 points), v2d (data hygiene, §2h: no gain). Throughput 155–220 games/s. dev1 → v2a +66 Elo, v2a → v2b +35 Elo (paired suite); v2b's recipe plateaus after ~100 iterations at the 6×64 net's capacity, confirmed by wide96 (6×96: **+36 Elo** over v2b, §2i); 6×128 queued after the c_scale and auxiliary-head ablations (`runs/queue_3090.sh`). |
| C. Evaluation anchors | Done: fixed-net anchors (dev1, v2b), paired opening suite with bootstrap CIs (§2b), independent rollout-UCT anchor (§2c), frozen balanced exact endgame set (§2d), solver-validated puzzle set (§2e), seed replicate for the noise band (§2g). Missing only external bots (CodinGame). |
| D. Play against it | `play.py` (terminal) and `web/server.py` (browser: play, hint, analyse with visit heat-map, WDL, PV, undo). |
| E. Analysis of the game | Rigorous first pass done (§2e): opening atlas with rank stability, decision time on held-out games, free-move and board-ownership effects from matched natural positions, solver-validated puzzle set with motifs, provenance on stored positions. Beliefs in §3 revised accordingly. |

Compute reality: a full 150-iteration run of 4096 games × 64 moves at 32–64 sims is
**~2.3 h** on the 3090 (0.8 M games), so experiments are cheap; wall-clock is no
longer the constraint — measurement quality and target quality are.

## 2. Results at a glance

| run | recipe delta | games / time | vs dev1 net (64 sims, 1024 games) | vs v2a net | notes |
|---|---|---|---|---|---|
| dev1 | v1 lock-step, eager | 819 k / 12.1 h | – | – | root policy collapse (99.9 % on move 40), opening duplication, value loss stuck at 0.82 |
| v2a | continuous self-play, graph search, sampled openings, prior floor, dedup weights, margin head, LR drops | 789 k / 2.75 h | **60.1 %** | – | passed dev1 at iter ~90; openings re-collapsed slowly (95 % move 40) |
| v2b | + exploration floor 0.15, sims 32→48→64, LR drops 100/140, graph-mode eval | 783 k / 2.3 h | **63.3 %** | **53.3 %** @64 (1024 g), **55.2 %** @256 (512 g) | buffer stayed 73–85 % distinct; draws under strong play doubled (20 %) |

Other v2b numbers (`runs/v2b/analysis.out`): 256 vs 64 sims self-match 77 % (v2a 80 %) —
still far from search-saturated; strong play (256 sims, 2 random plies, 1024 games):
X 47.6 %, O 32.3 %, **draws 20.1 %**, ended by line 68 %, by count 12 %, equal 20 %.
Exact-endgame test (3000 positions ≤16 moves left): raw value 3-way 0.76, search
move-error 1.1 % @32, 0.5 % @64, 0.3 % @256 (same as v2a within noise).

### 2b. Paired opening-suite results (`suites/openings_v1.npz`, 516 openings × 2 colours = 1032 games)

Scores are A's, 95 % percentile-bootstrap CIs over opening pairs; sub-suite columns are point
estimates (natural/random: 250 pairs each, ±4 points; orbits: 15 pairs, ±15 — coverage, not
evidence). Raw output: `runs/v2b/paired64.out`, `runs/v2b/paired.out`, per-opening JSON next to them.

| A vs B (sims) | all | Elo | natural | random | orbits | empty | X share | unpaired (old) |
|---|---|---|---|---|---|---|---|---|
| v2b vs dev1 (64) | **63.3 % [60.5, 66.1]** | +95 [+74, +116] | 60.9 | 65.4 | 65.0 | 1.0 | 59.0 % | 63.3 % |
| v2b vs v2a (64) | **55.1 % [52.4, 57.8]** | +35 [+17, +55] | 56.2 | 54.1 | 51.7 | 0.75 | 60.4 % | 53.3 % |
| v2a vs dev1 (64) | **59.4 % [56.6, 62.3]** | +66 [+46, +87] | 57.3 | 61.8 | 58.3 | 0.25 | 57.2 % | 60.1 % |
| v2b vs v2a (256) | **55.4 % [52.7, 58.2]** | +38 [+19, +58] | 53.5 | 56.7 | 63.3 | 1.0 | 57.5 % | 55.2 % |
| v2b @256 vs v2b @64 | **78.4 % [76.1, 80.6]** | +224 | 79.6 | 77.3 | 78.3 | 0.5 | 56.6 % | 77.2 % |

- The unpaired 2-random-ply numbers all lie inside the paired CIs: the earlier ranking
  dev1 < v2a < v2b stands, and v2b's edge over v2a is now a resolved +35 Elo rather than
  "+25–35 within noise".
- Reviewer finding 3's mechanism is visible but small: against dev1 (narrow openings) both
  newer nets score ~4 points higher on the broad random suite than on the natural one;
  v2b vs v2a (both trained with opening diversity) shows no such gap. Report the natural
  suite as the headline number and the random suite as the robustness number.
- The first-player effect is large at every budget (X scores 57–60 % of all games) and is
  exactly what the pairing cancels: v2b vs v2a scores 65.5 % as X and 44.7 % as O.
- Empty-board games are single pairs (deterministic players) and stay anecdotal; the
  15-orbit suite is too small for its own CI and serves as coverage.
- Cost: 1032 games ≈ 45 s at 64 sims, 160 s at 256 sims (3090). The in-run evaluation uses
  a fixed 216-opening subset (432 games, ±4 points, ~75 s for two anchors).
- Determinism: repeated matches in one process are bit-identical; a re-run while another
  process shared the GPU differed by 0.4 points (cuDNN fp16 algorithm choice) — inside the
  CI, but do not read tenths of a point off single matches.

### 2c. Independent anchor: rollout UCT (`uttt/rollout.py`, 100 k random playouts per move, paired suite)

| A vs B | all | Elo of B over A |
|---|---|---|
| rollout 100 k vs v2b @64 | 27.5 % [25.0, 30.1] | **+169** [+146, +191] |
| rollout 100 k vs dev1 @64 | 41.8 % [39.0, 44.7] | **+58** [+37, +78] |
| rollout 100 k vs rollout 10 k | 92.7 % [91.1, 94.1] | −441 (10× playouts ≈ +440 Elo) |
| rollout 10 k vs v2b @64 | 4.7 % [3.6, 6.0] | **+521** [+479, +569] |
| v2b @256 vs rollout 100 k | 87.5 % [85.7, 89.3] | **+338** [+310, +368] (4× net budget ≈ +170 Elo) |

The anchor is a fixed external yardstick (no net, no shared search code; rules checked move by move
against the reference engine). A 64-sim v2b search is ~170 Elo above a 100 k-playout UCT — the
CodinGame-Legend-class recipe — which is the first absolute strength statement in the project; the
anchor's own scaling is steep (+440 Elo per 10× playouts), so "v2b@64 ≈ rollout at ~250 k playouts"
is the rough equivalence. Elo is not transitive here (10 k → 100 k → v2b sums to +610 against a
direct +521). The anchor also beat v2b from the empty board as X (single game; anecdotal).
Timing: ~8 min per 1032-game match at 100 k playouts on 24 threads.

### 2d. Frozen exact endgame set (`suites/endgame_v1.npz`: 3000 solved positions, 125 per stratum of
4 empties buckets × W/D/L × side, from 2870 v2a games; `runs/endgame_eval.out`)

| net | raw WDL acc | draws | Brier | raw policy optimal | regret | search 64 optimal | search 256 optimal |
|---|---|---|---|---|---|---|---|
| dev1 | 71.2 [69.5, 72.9] | 42.1 | 0.385 | 93.2 % | 0.083 | 98.7 % | 99.8 % |
| v2a | 74.4 [72.7, 76.0] | 53.3 | 0.341 | 93.4 % | 0.080 | 99.0 % | 99.6 % |
| v2b | **75.0** [73.5, 76.6] | 54.7 | 0.335 | 93.5 % | 0.078 | 99.2 % | **99.9 %** |
| rollout 100 k | – | – | – | – | 0.003 | – | 99.7 % |

- The balanced set is harder than the old visitation-sampled one (76 % 3-way there vs 75 % WDL-argmax
  here) and shows where the value head fails: **drawn positions** (55 % recognised; wins 82 %, losses
  89 %) and 15–16 empties (65 %). CIs are clustered by source game.
- Action regret separates the raw policy (7–9 % of positions lose value) from the search (64 sims:
  0.8 %; 256 sims: 0.1 %). In *play* the endgame is nearly solved by the search; the value-head error
  matters as leaf evaluation for deeper positions and as the training signal — run v2c tests this.
- The search's *root value* thresholded three ways scores below the raw head on this set (70 vs 75 %):
  the mixed backed-up value is not a class predictor; use regret/optimal-move for search quality.
- **Why draws fail** (v2b and wide96 alike): the head is not confused but *under-confident about
  draws* — exact draws get mean draw probability 0.49–0.51, and the draw probability is
  mis-calibrated upward (predicted 0.27 → observed 0.58; 0.70 → 0.90). Misclassified draws go to
  "win" when the mover leads on boards and "loss" when behind (macro score +2: 62–67 % called wins).
  The 13 % draw share of self-play games is the likely prior. **Post-hoc calibration works for
  classification, not for play** (`tools/calibrate.py`, v2b): a logit bias fitted on half the set
  (win −0.47, draw +0.83, loss −0.36) lifts held-out WDL accuracy **75.1 → 79.6 %** (draws 53 →
  81 %, Brier 0.331 → 0.280), but the calibrated evaluator scores 48.8 % [45.9, 51.6] against the
  uncalibrated one on the paired suite (it draws more: 17.5 % vs 13 %). So a third of the
  "endgame value error" is a draw prior that the search does not need corrected; the metric to
  watch for play is action regret, and the WDL head should be read with the bias
  (`FusedEvaluator(..., wdl_bias=...)`) in analyses.

### 2e. Analysis programme, rigorous versions (step 7; `runs/step7a.out`, `step7b_freemove.out`, `step7d_puzzles.out`)

- **Opening atlas** (`tools/atlas.py`; dev1/v2a/v2b × 1k/4k/16k sims, symmetry-averaged, PUCT):
  centre-of-centre [40] is the best first move in all 9 net×budget columns; the top four
  ([40], corner-of-corner [0], corner-of-centre [36], edge-of-centre [37]) hold ranks 1–5
  everywhere; centre-of-edge-board [13] is last everywhere. Kendall τ of the 15-orbit ranking:
  0.94–1.00 across budgets within v2b, 0.68–0.83 between nets — the *ordering* is stable, the
  values are not (v2b rates X's edge after [40] at +0.35, dev1 +0.28). Largest disagreement:
  centre-of-corner-board [4] (dev1 rank 14, v2b rank 9). Replies: after [40] every column
  prefers the edge-cell reply [37] over the corner [36]; best-reply agreement with v2b@16k is
  1.00 for [13], [16], [40] but 0.22–0.33 for [1], [4], [5], [37] — reply preferences are
  search-relative and unstable there. Principal variations at 16 k sims (`runs/atlas_pv.out`,
  v2b vs v2b_s1) agree on the reply *class* after [40] (an edge cell of the centre board: 37 /
  41) and diverge within a few plies; the root action-value gap between the two most visited
  replies is ≤ 0.02 for 12 of 15 first moves — the openings are flat in the search's eyes,
  except after the bad first moves [13] (gap +0.08–0.09: reply 40 is clearly best) and [36].
- **Decision time** (`tools/decision.py`; v2b net on 4000 held-out v2a games): the WDL head is
  at the base rate (log-loss 0.90, accuracy 0.61 = "X wins") until ply ~28, reaches 0.67 at
  ply 40, 0.84 at 48. The raw value's 3-way prediction is right from ply 43 onward for the
  median game (90 % of its length; quartiles 39–47), 5.7 % of games only settle on the last
  ply. The 64-sim search's *best-child Q* is the sharpest predictor: settled from ply 38 for
  the median game (78 % of its length; quartiles 32–42; 27 % of games settled by ply 32,
  69 % by ply 40, none unsettled), while the mixed root value is a poor classifier (median
  45). So "games are decided late" holds as a *predictive* statement: nothing at ply 30, most
  by ply 40. X wins settle earlier (ply 34) than O wins (40) and draws (41).
- **Board ownership** (same regression with per-class ownership counts, `step7b_freemove.out`):
  with macro threats, full boards, empties and side controlled, owning a board is worth
  centre +0.01, corner +0.01, edge +0.03 (all within ±0.03–0.04 CI) — the centre > corner >
  edge hierarchy of the tensor-flip probe does not survive; ownership value is carried by the
  **macro-line threats** it creates (+0.17 per line with two own boards and an open third,
  −0.17 per opponent line) and by the count. The hierarchy is the line-count ordering
  (centre 4 lines, corner 3, edge 2) in disguise, not a positional bonus.
- **Free-move effect** (`tools/freemove.py`; 30 k natural positions from 6 k held-out games,
  256-sim values, OLS with ply, macro score, open boards, empties, side, macro threats;
  cluster-robust SE by game): free-move coefficient **+0.16 ± 0.03** on the search value
  (+0.26 ± 0.03 on the raw value; R² 0.54 / 0.63); the unadjusted difference is −0.07 (free
  moves cluster in bad late positions) and a ply × macro-score stratified check gives +0.06,
  largest late when ahead (+0.52 at plies 44–50 with +2 boards). The tensor-edit probe's
  +0.27 overstated it. Other coefficients: X to move +0.59, macro threat for/against ±0.16.
- **Puzzles** (`tools/puzzles.py`, `suites/puzzles_v1.npz`): 6000 held-out positions with ≤ 14
  empties solved with children; v2b's raw policy loses exact value in **208 (3.5 %)**, the
  64-sim search in 11 (0.22 %). Motifs: tiebreak conversion 110, gives a free move 92,
  draw hold 71, denies a free move 68, local win 55 — the endgame errors are about the count
  rule and free-move handling, not local tactics. Regret 1 in 66 %, 2 (win→loss) in 34 %.

### 2f. Run v2c: exact-label training (step 2) — a clean negative result

v2c = the v2b recipe + 8192 exact labels per iteration (≤ 14 empties, value and policy targets
replaced, ×2 sampling weight; 1.23 M labels over the run, 2.7 % of the buffer), same seed.
`runs/v2c/analysis.out`:

| | v2b | v2c |
|---|---|---|
| paired suite vs v2b @64 (1032 games) | – | **48.7 % [45.8, 51.4]**, −9 Elo [−29, +10] |
| paired suite vs dev1 @64 | 63.3 % [60.5, 66.1] | 62.7 % [60.0, 65.4] |
| endgame WDL acc (draws) | 75.0 [73.5, 76.6] (54.7) | 75.9 [74.4, 77.5] (55.8) |
| raw policy optimal / regret | 93.5 % / 0.078 | 93.6 % / 0.077 |
| search 64 optimal | 99.2 % | 99.3 % |

Nothing moved. The reason is measurable: on v2b's final buffer the self-play outcome z already
equals the exact value in **98.7 %** of positions with ≤ 14 empties (0 % wrong at ≤ 5 empties,
0.2 % at 6–9, 2.3 % at 10–12, 2.8 % at 13–14; draw/decisive confusions 1 % each way). At 64 sims
the self-play *outcome* is exact there; the value head's 75 % is therefore not label noise but
**capacity / representation**: the 6×64 net cannot compute a 10–14-ply exact value from the
position, and it fails systematically on draws. Exact labels can only matter where z is wrong,
i.e. 15+ empties, where solving is 0.4 s per position and impractical in-loop. Levers for the
endgame floor are the network (width/depth, the count-difference plane in v2d) and the search
budget at play time (phase-dependent budgets, §5 step 3), not labels. The labelling machinery
stays available (`--exact_max_empty`), costs no wall-clock, and is on in v2d and the ablations.

### 2g. Seed replicate v2b_s1 (step 6): the noise band

v2b's recipe with seed 1 (`runs/v2b_s1`, trained on the 3060 in 4.0 h; `analysis.out`):

| | v2b | v2b_s1 | v2c |
|---|---|---|---|
| paired suite vs v2b @64 (1032 games) | – | **51.1 % [48.4, 53.7]**, +7 Elo | 48.7 % [45.8, 51.4] |
| paired suite vs dev1 @64 | 63.3 % [60.5, 66.1] | 62.6 % [59.9, 65.3] | 62.7 % [60.0, 65.4] |
| endgame WDL acc / draws | 75.0 / 54.7 | 75.1 / — | 75.9 / 55.8 |
| raw policy optimal / regret | 93.5 % / 0.078 | 93.7 % / 0.075 | 93.6 % / 0.077 |

Three runs of the same recipe (two seeds, ± exact labels) land within ±2.5 points of each other on
every yardstick: the recipe's final strength is reproducible to about the 1032-game CI. The in-run
432-game subset is noisier than its CI suggests because *checkpoints* differ: v2b_s1 scored
0.453 → 0.545 against v2b between iterations 139 and 149. Rules from this: (i) an ablation must
beat the base by > 3 points on the full suite to be believed; (ii) compare final checkpoints on
the full suite, not in-run points; (iii) checkpoint-to-checkpoint noise (`runs/seed_noise.out`):
against v2b's net_0150, v2b's own net_0130 / net_0140 score 47.2 / 47.5 % and v2b_s1's 48.6 /
44.1 % — consecutive checkpoints of one run differ by up to 4 points (−41 Elo), and the final
checkpoint after the second LR drop is the best of each run. Averaging the last three
checkpoints (`tools/swa.py`, BN statistics recomputed) makes it **worse**: v2b SWA 45.9 %
[43.1, 48.7] vs its own net_0150, endgame WDL 73.8 vs 75.0 — the pre-drop checkpoints drag the
post-drop one back. Checkpoints inside one LR phase would be needed (or an in-training EMA);
not pursued: the final checkpoint is the right one to report.

Opening ranking across seeds (`tools/atlas.py`, v2b / v2b_s1 / v2c at 1k and 4k sims): Kendall
τ 0.87–0.94 between runs, the same top four ([40] > [36] ≈ [0] > [37]) and the same last ([13]);
the atlas ordering is a property of the recipe, not of a seed (`runs/atlas_seeds.json`).

### 2h. Run v2d: data hygiene (step 4) — no strength change either

v2d = v2c + symmetric dedup hashing, α = 1 for plies < 8, 4-class ownership target, 9 input planes
(first player, won-board difference). `runs/v2d/analysis.out`, 2.5 h:

| | v2b | v2d |
|---|---|---|
| paired suite vs v2b @64 | – | **48.2 % [45.4, 50.9]**, −12 Elo |
| paired suite vs dev1 @64 | 63.3 % | 62.5 % [59.6, 65.3] |
| endgame WDL acc / draws | 75.0 / 54.7 | 75.8 / 55.8 |
| raw policy optimal / regret | 93.5 % / 0.078 | 93.4 % / 0.079 |
| value loss / value acc (last 20 iterations) | 0.820 / 0.625 | 0.779 / 0.644 |
| first-move top share / buffer distinct | 0.81 / 0.75 | 0.82 / 0.70 (symmetric copies now count) |

The extra planes lower the value loss (0.82 → 0.78: the count-difference plane is used) without
changing play; symmetric dedup and uniform early-ply sampling leave the first-move distribution
where the 15 % exploration floor already put it. Four runs of the 6×64 net (v2b, v2b_s1, v2c,
v2d) now sit within ±3 points of each other on every yardstick: the plateau is a property of the
network, not of these recipe details. The wide net (6×96, `runs/wide96`) is the running test.

### 2i. Run wide96: the 6×96 net (step 5) — the first real gain since v2b

Same recipe as v2c (exact labels on, a no-op), `--filters 96`; 3.7 h (57 games/s vs ~200 for 6×64).
`runs/wide96/analysis.out`:

| | v2b (6×64) | wide96 (6×96) |
|---|---|---|
| paired suite vs v2b @64 | – | **55.1 % [52.3, 58.0]**, **+36 Elo** [+16, +56] |
| paired suite vs dev1 @64 | 63.3 % (+95) | **68.7 % [66.2, 71.2]** (+136) |
| endgame WDL acc / draws | 75.0 / 54.7 | 76.2 [74.6, 77.7] / 55.9 |
| raw policy optimal / regret | 93.5 % / 0.078 | 93.6 % / 0.077 |
| search 64 optimal | 99.2 % | 99.4 % |
| value loss / value acc (last 20 it.) | 0.820 / 0.625 | 0.796 / 0.637 |

Width buys play strength (+36 Elo, clear of the ±3-point noise band of §2g) at 2.2× the
self-play cost per game, but it does not touch the endgame *draw* recognition (56 %) — that
error is not just capacity either. Next: 6×128 (`runs/wide128`, queued after the two
ablations) to see whether the gain continues.

### 2j. Ablation `c_scale` 0.1 → 1.0 (step 6): a free +40 Elo

Gumbel AlphaZero's completed-Q term σ(q̂) = (c_visit + max N) · c_scale · q̂; mctx's default
`value_scale` is 0.1, the paper's text quotes 1.0 (NOTES-v2 §0). `runs/abl_cscale1` = the v2c recipe
with `--c_scale 1.0`, 6×64, 2.3 h:

| | v2b (c_scale 0.1) | abl_cscale1 (1.0) |
|---|---|---|
| paired suite vs v2b @64 | – | **55.7 % [52.9, 58.5]**, **+40 Elo** [+20, +60] |
| paired suite vs dev1 @64 | 63.3 % (+95) | **67.3 % [64.7, 69.9]** (+126) |
| endgame WDL acc / regret / optimal | 75.0 / 0.078 / 93.5 % | 74.6 / 0.077 / 93.6 % |
| self-play (last 20 it.): policy loss / X wins / draws | 0.92 / 57 % / 14 % | 1.15 / 62 % / 10 % |

With c_scale = 1 the improved policy follows the search's Q ten times more sharply, so the
policy target is more decisive (higher policy loss = a harder, sharper target; self-play more
decisive). Same cost as v2b, same gain as the 6×96 net. The effect is in the *training
targets*, not in play: searching either net with c_scale 1.0 instead of 0.1 at play time
changes nothing (abl_cscale1 49.1 % [46.3, 52.1] vs itself; v2b 50.5 %), so the evaluation
default stays 0.1 and all match numbers remain comparable (`tools/openings.py --a_cscale`).
Next runs combine both gains: `wide96_c1` (6×96 + c_scale 1.0) to check additivity, then
`wide128_c1`.

### 2k. Combining the two gains: wide96_c1 (6×96 + c_scale 1.0) — the strongest net so far

`runs/wide96_c1/analysis.out` (3.8 h): **58.4 % [55.7, 61.1] vs v2b @64 = +59 Elo** [+40, +78];
66.5 % vs dev1 (+119); endgame WDL 75.2. The two ~+40 Elo changes combine sub-additively
(+36 and +40 → +59). **wide128_c1** (6×128 + c_scale 1.0, 4.5 h, 43 games/s) continues the
climb: **60.9 % [58.2, 63.5] vs v2b = +77 Elo** [+57, +96], 74.7 % vs dev1 (+188), endgame WDL
76.3, raw-policy optimal **94.4 %** / regret 0.067 (both bests). Width scaling has not
flattened — the ladder c_scale-1 runs read +40 (6×64) → +59 (6×96) → +77 (6×128). See
PLAN3.md for the hand-off and next steps.

## 3. What we currently believe about the game (with the reviewer's four levels)

Behavioural (what self-play did), predictive (net on natural states), search-relative
(net+search preference), game-theoretic (exact). Nothing below is game-theoretic
except the endgame solver's labels.

- First-player advantage: X 57–60 % / O 29–32 % / draws 11–13 % in 32–64-sim self-play;
  X 48 % / O 32 % / draws 20 % at 256 sims (behavioural; draws rise with strength).
- **The tiebreak rule matters and matters more with strength**: 15 % of random games,
  25–29 % of 32-sim games, **32–34 % of 256-sim games** end by board count or equal
  count (behavioural, robust across runs).
- First move: centre-of-centre dominates every net and search (search-relative,
  consistent across dev1/v2a/v2b at 4096–8192 sims: +0.33…+0.35 vs ≤ +0.27 for the
  best alternative). The two "cell 4 of a non-centre board" orbits (handing O the
  centre board) are the worst; centre-of-edge-board is the only negative one
  (−0.05…−0.17). Stable ordering, unstable magnitudes → report ordering only.
- Games are decided late — now a *predictive* statement (§2e): on held-out games the
  value head is at the base rate until ply ~28; the 64-sim search's best-child Q is right
  from ply 38 onward for the median game (78 % of its length), the raw value from ply 43;
  27 % of games are settled by ply 32, 69 % by ply 40.
- Free-move tempo: **+0.16 ± 0.03** in 256-sim search value after controlling for ply,
  macro score, open boards, empties, side and macro threats (predictive, natural positions,
  cluster-robust CI; §2e); largest late when ahead. The old tensor-edit +0.27 overstated it,
  and the unadjusted correlation has the opposite sign.
- Board hierarchy centre > corner > edge (~+0.11 steps) from ownership flips was an
  **off-distribution artefact**: on natural positions with macro threats controlled, owning
  any board class is worth ≈ 0 (±0.03); the value sits in macro-line threats (±0.17 per
  line) and the count — i.e. in the number of lines a board belongs to (§2e).
- Opening ordering is stable across nets and budgets (Kendall τ ≥ 0.68; [40] first in every
  column; [13] last), reply preferences after most first moves are not (§2e).
- The raw net is a decent opening player and a weaker endgame evaluator: on the balanced
  exact set its WDL argmax is right 75 % of the time (draws 55 %), its policy argmax loses
  exact value in 3.5–6.5 % of endgame positions (mostly count-rule and free-move motifs),
  while the 64-sim search errs in 0.2–0.8 % and 256 sims in 0.1 % (§2d, §2e).
- Absolute strength: v2b@64 ≈ +170 Elo over a 100 k-playout random-rollout UCT, whose own
  scaling is ~+440 Elo per 10× playouts (§2c).

## 4. Lessons learned

Engineering
- Windows + PyTorch: the search was 93 % launch/sync overhead (45 syncs, 550 kernels
  per simulation). Fixes in order of payoff: remove host syncs (boolean indexing,
  `.item()`), edge-statistics layout, **CUDA-graph replay** (7× on tree work, immune to
  CPU contention), fused fp16 inference (BN folded, channels_last), continuous
  self-play instead of lock-step. Result: 25 → 220 games/s.
- Two launch-bound processes slow each other even on different GPUs; graph-mode
  processes coexist fine. Torch `cuda:0` = the 3090 = `nvidia-smi` index 1.
- Evaluation must be cheap and in graph mode; dev1 spent a third of its wall-clock
  on evaluation that stopped being informative at iteration 40.
- Resume only from a buffer-checkpoint iteration (`--save_buffer_every`), otherwise
  the buffer restarts empty (now warns). Codex/PowerShell: pass prompts as a pwsh
  argument with stdin closed (`< /dev/null`), never via Windows PowerShell 5.1.

Learning
- Opening diversity is the first-order problem: deterministic root selection +
  uniform sampling of a duplicated buffer collapses the policy to one opening
  and starves alternatives. Sampling from the improved policy alone re-collapses
  as the policy sharpens; an explicit uniform floor (`--sample_uniform`) holds.
- Duplicate down-weighting `count^-0.5` helps but leaves opening mass ∝ √count;
  canonicalise positions under D4 before hashing and consider α → 1 for plies < 8.
- Constant LR plateaus; the first ×0.1 drop gave the clearest step in both runs.
- Progressive simulations gave a modest gain (+25–35 Elo) at +25 % time.
- Gumbel `c_scale`: mctx's default 0.1 was carried over from NOTES-v2 §0 as "A/B it"; the
  paper's 1.0 is worth +40 Elo here at no cost (§2j). Sharper improved-policy targets beat
  smoother ones for this game — check every inherited default that shapes the target.
- With Gumbel at 32 sims the policy target is a bounded improvement on the prior;
  the teacher is the limit once the student matches it — hence more/phase-dependent search
  is a lever. Exact labels are not (v2c): the self-play outcome is already exact where the
  solver reaches, so the endgame value error is a capacity problem → a wider net (step 5)
  moves ahead in priority.

Measurement (from REVIEW-codex.md — accepted)
- Matches used unpaired random 2-ply openings: fine for relative ranking, not for
  "empty-board strength". Replaced by the paired opening suite (§2b); the unpaired and
  paired numbers agree within 1–2 points, so the earlier rankings stand.
- 256-game in-run evaluations are ±6 points; only 1024-game matches resolve <5 points.
- "3-way accuracy" thresholds the scalar value; report WDL argmax, log-loss, calibration
  (done: `uttt/endgame.py`). A search's *root* value is a mean over simulations and a
  poor class predictor (70 % vs the raw head's 75 % on the same set); judge search by
  action regret, or by the best child's Q.
- The "UCT" anchor was a uniform-prior search, not rollout UCT; `uttt/rollout.py` is the
  independent engine now, and it scales steeply (+440 Elo per 10× playouts), so quote its
  budget with every number.
- Unadjusted correlations in self-play corpora can have the wrong sign (free moves: −0.07
  raw, +0.16 adjusted); prespecify controls and cluster by game.

## 5. Next steps, in order (each is a 1–3 h task unless noted)

1. **Measurement first** (prerequisite for judging anything below):
   a. **Done.** `uttt/openings.py` + `tools/openings.py` + `suites/openings_v1.npz`: empty
      board, the 15 first-move orbits, 250 natural 4-ply openings (canonical under D4,
      drawn ∝ frequency from the v2a corpus) and 250 broad random ones; every opening is
      played with both colours; per-suite scores with percentile-bootstrap CIs over
      opening pairs; `train2.evaluate` uses a fixed 216-opening subset. Results in §2b.
   b. **Done.** `uttt/rollout.py`: Numba bitboard UCT with random playouts, 3.7 M
      playouts/s on 24 threads; `tools/openings.py match --a rollout --a_sims 100000`.
      Results in §2c.
   c. **Done.** `uttt/endgame.py`, `tools/endgame.py`, `suites/endgame_v1.npz`: balanced
      solved set with per-move exact values; WDL-argmax, Brier, log-loss, action regret,
      optimal-move rate, cluster-bootstrap CIs; also scored in-run (`eg_*` log keys). §2d.
2. **Exact-label training** — **done, negative** (§2f). Implemented (`uttt/exact.py`,
   `train2 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12`; solving
   overlaps training, no wall-clock cost). Run v2c = v2b + labels: parity with v2b in play
   (48.7 % [45.8, 51.4]) and on the endgame set, because self-play z is already exact in
   98.7 % of ≤ 14-empties positions at 64 sims. The endgame floor is capacity, not labels.
3. **Phase-dependent search** — measured (`runs/v2b/step3.out`, `tests/diag_depth_cap.py`):
   - Depth cap 12 truncates ≤ 2.3 % of simulations at 64 sims (peak at ply 6), ≤ 0.3 % at
     48, 0 % at 32 → non-binding for self-play; `cap_hit` is now logged per iteration.
   - A ply-scheduled budget at play time — 32 sims until ply 24, then 96 (same mean cost
     as 64) — beats uniform 64: **57.2 % [54.5, 59.7], +50 Elo** (v2b vs itself, paired
     suite). `tools/openings.py match --a_sims "0:32,24:96"`; `arena.PhasedSearchPlayer`.
   - Not done: per-game budgets in self-play. In this batched, launch-bound design a
     search costs ≈ Σ sims regardless of batch size, so splitting the batch into an early
     pool (32 sims) and a late pool (96) costs ~2× at 4096 games; it only pays once
     batches are large enough to be GPU-bound (≥ 8192) — a `--games 8192` experiment for
     later. Tree reuse between moves conflicts with Gumbel's sequential-halving root
     schedule and the fixed slot layout; skipped.
4. **Data hygiene** — **done, no strength change** (§2h). `--dedup_sym 1`,
   `--dedup_alpha_early 1.0`, `--own_classes 4`, `--n_planes 9` implemented and tested
   (`tests/test_hygiene.py`); run v2d = v2c + all four scores 48.2 % [45.4, 50.9] vs v2b.
   The extra planes lower the value loss but not the Elo. Keep the options (harmless);
   no per-option ablation is warranted.
5. **Wider net** — **6×96 done: +36 Elo over v2b** (§2i), the first gain since v2b, at
   2.2× the cost per game. **6×128 queued** (`runs/wide128`, after the ablations) to map
   the scaling; the endgame draw stratum did not move with width, so that is a separate
   problem (representation / target), not a capacity one.
6. **Ablations** (2.3 h each on the 3090; `runs/queue_3090.sh`, evaluation chain
   `runs/eval_run.sh <run>`): seed replicate **done** (§2g: ±2.5 points between seeds);
   **`c_scale` 1.0: +40 Elo** (§2j) — adopt; **auxiliary heads off: no effect** (`abl_noheads`
   50.3 % [47.6, 53.1] vs v2b, endgame WDL 74.3 — keep the heads for analysis); `dedup_alpha`
   1.0 for early plies was part of v2d (no effect). Then `wide96_c1` and `wide128_c1`
   (`runs/after_queue2.sh`).
7. **Analysis programme (Phase E, rigorous versions)** — first pass done (§2e): opening
   atlas with rank stability (`tools/atlas.py`), free-move effect from matched natural
   positions with a prespecified model (`tools/freemove.py`), decision time from held-out
   prediction (`tools/decision.py`), surprise → solver-validated puzzles with motifs
   (`tools/puzzles.py`), board ownership by class in the same regression, best-child-Q
   settling metric, provenance on buffer positions (`game`, `iter`). Open: rank stability
   across *seeds* once v2b_s1 exists; opening-atlas PVs and action-value gaps.
8. **Web UI — done** (`web/server.py` + `web/index.html`: play either colour or both,
   hint, analyse with visit heat-map, WDL bar, top moves with Q and prior, PV, undo;
   `python web/server.py runs/v2b/net_0150.pt --sims 800 --device cuda:1`, then
   http://localhost:8765/). Later: K=1-open-board tablebase only if the on-demand solver
   cache proves insufficient; CodinGame submission as an external test.

## 6. Reviewer findings — status

| # | finding | status |
|---|---|---|
| 1 | probe/surprise "distinct" sampling wrong | **fixed** (`probe_value.load_positions`), rerun: numbers unchanged within 0.02 |
| 2 | value probes off-distribution | caveat added to RESULTS-v2a; paired-history version = step 7 |
| 3 | unpaired/random-opening evaluation | **fixed** (`uttt/openings.py`, `suites/openings_v1.npz`, `train2.evaluate`); paired numbers in §2b |
| 4 | resume without buffer silent; RNG/scaler not saved; mixed-generation trajectories | warning added; full state save open |
| 5 | terminal-root value diluted in v2 search | **fixed** (`search.py`) |
| 6 | corpus over-claims | wording fixed in RESULTS-v2a; rigorous versions = step 7 |
| 7 | 3-way accuracy ≠ WDL argmax; solver `max_nodes` ignored | **fixed**: parameter removed; `uttt/endgame.py` reports WDL argmax, Brier, log-loss, regret with cluster CIs (§2d) |
| 8 | dedup mass ∝ √count; ownership classes; parity feature | open → step 4 |
| 9 | depth cap unvalidated; "UCT" misnomer | cap verified non-binding at 32/64 sims (2048 positions, identical trees); logging + rename open |
| 10 | vacuous test assertion; no mctx golden test | assertion fixed; mctx CPU golden test open |

## 7. Operational notes for the next instance

- Environment: `.venv` (Python 3.10, torch 2.13+cu126, numba). `UTTT_DEV=cuda:1` runs
  tests/tools on the 3060 while the 3090 trains. Tests: run each `tests/*.py` directly.
- Train: `python -u -m uttt.train2 --run runs/<name> --iters 150 --games 4096 --steps 64
  --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15
  --root_prior_floor 0.03 --dedup_alpha 0.5 --lr 0.02 --lr_drops 100,140 --eval_every 10
  --eval_games 128 --eval_sims 64 --anchors runs/dev1/net_0200.pt,runs/v2b/net_0150.pt
  --save_buffer_every 10 --cuda_graph 1 --depth_cap 12` (v2b's config; ~2.3 h).
  The defaults now evaluate on `suites/openings_v1.npz` (`--suite`, `--eval_openings 100`
  → 432 paired games per anchor, ~75 s for two anchors) and log `vs_<run>_<ckpt>`,
  `ci_<…>` (95 % bootstrap over opening pairs) and `suites_<…>` (score per sub-suite);
  `--suite ''` gives the old unpaired random-opening evaluation. Anchor keys are now
  `<run>_<checkpoint>` (`vs_dev1_net_0200`), so two runs' `net_0150` no longer collide.
- After a run: `tools/openings.py match --a <new> --b <anchor> --sims 64` (paired suite,
  1032 games, ~45 s; `--out x.json` records per-opening results), `tools/match.py`
  (unpaired, for comparison with old numbers), `tools/analyze_opening.py`,
  `tools/corpus_stats.py`, `tools/endgame_accuracy.py`, `tools/probe_value.py`,
  `tools/surprise.py`, `tools/plot_run.py` — see `runs/v2b/analysis.out` and
  `runs/v2b/paired.out` for the standard chain. Rebuild the suite only deliberately
  (`tools/openings.py build`; a new file name = a new, incomparable yardstick).
- Play: `python play.py runs/v2b/net_0150.pt --sims 800 --human X` (type `hint`).
- Strongest current net: `runs/v2b/net_0150.pt` (v2b_s1 and v2c are equal within noise; it
  stays the reference anchor). Anchors: `runs/dev1/net_0200.pt`, `runs/v2b/net_0150.pt`.
  Game corpora: `runs/v2a/games` (the frozen "held-out" source for suites and analyses),
  `runs/v2b/games`, `runs/v2c/games`, `runs/v2b_s1/games` (~3 M games).
- New defaults in `train2`: paired-suite + endgame-set evaluation every 10 iterations
  (`vs_*`, `ci_*`, `suites_*`, `eg_*` keys), `cap_hit` logged; exact labels off unless
  `--exact_max_empty > 0`; `--n_planes 9 --own_classes 4 --dedup_sym 1 --dedup_alpha_early 1.0`
  are the step-4 options (v2d). Post-run chain: `bash runs/eval_run.sh <run> [device]`;
  the 3090 ablation queue: `bash runs/queue_3090.sh`.
- Yardsticks (never rebuild silently): `suites/openings_v1.npz`, `suites/endgame_v1.npz`,
  `suites/puzzles_v1.npz`; the rollout anchor at 100 k playouts (`--a rollout --a_sims 100000`).
- Rule set implemented: closed boards, free move on closed target, 3-in-a-row wins,
  else more won boards wins, equal = draw (CodinGame rules; confirmed against the
  referee source in `knowledge/01`).
