# uttt-zero — PLAN3: hand-off (2026-08-30, end of the second working day)

Read this first; it supersedes `PLAN2.md` (kept — its §2b–§2k hold the detailed result tables
this file summarises). Older layers: `PLAN.md` (original plan), `NOTES-v2.md` §8 (what is
implemented, chronological), `RESULTS-dev1/v2a.md`, `REVIEW-codex.md` (outside review; all ten
findings closed), `knowledge/01–06` (research base). File map: `README.md`.

## 1. State in one paragraph

The pipeline (batched CUDA-graph Gumbel search, continuous self-play at 45–220 games/s,
GPU replay buffer, paired evaluation) is done and trustworthy; measurement is done and
trustworthy (see §2); the analysis programme has produced its first rigorous findings (§5);
a web UI exists for play/analysis. Ten training runs have mapped the recipe landscape: the
6×64 net's plateau was broken by **two levers that stack — Gumbel `c_scale` 1.0 (+40 Elo,
free) and network width (+36/+59/+77 Elo at 6×96/…/6×128)** — and by nothing else (exact
labels, data hygiene, auxiliary heads, SWA, dedup variants are all within the ±3-point noise
band). **Strongest net: `runs/wide128_c1/net_0150.pt`** (6×128, c_scale 1.0): +77 Elo over
v2b, +188 over dev1, ~+250 over a 100 k-playout rollout UCT at 64 sims, raw policy optimal
in 94.4 % of solved endgames. Width scaling has not flattened.

## 2. The measurement kit (use it, don't rebuild it)

- **Paired opening suite** `suites/openings_v1.npz` (516 openings: empty + 15 orbits + 250
  natural + 250 random, D4-canonical, frozen from the v2a corpus). Every opening plays both
  colours; CIs bootstrap over opening pairs. `tools/openings.py match --a X --b Y --sims 64`
  → 1032 games in ~50–70 s (3090). 95 % CI ≈ ±2.8 points. Players: checkpoint | `uct` |
  `rollout` (Numba UCT anchor, `--a_sims` = playouts) | `random`; `--a_sims "0:32,24:96"`
  gives a ply-scheduled budget; `--a_cscale` changes play-time c_scale (measured: no effect).
- **Exact endgame set** `suites/endgame_v1.npz` (3000 solver-labelled positions, balanced
  over 4 empties buckets × W/D/L × side, provenance kept). `tools/endgame.py eval <ckpt>`:
  WDL acc / Brier / log-loss, action regret, optimal-move rate, cluster-bootstrap CIs.
- **Rollout anchor** (`uttt/rollout.py`): fixed external yardstick, +440 Elo per 10×
  playouts; v2b@64 ≈ +169 over 100 k playouts. ~8 min per suite match on 24 threads.
- **Puzzles** `suites/puzzles_v1.npz` (208 positions where v2b's raw policy loses exact
  value; PVs, motifs). `tools/puzzles.py` regenerates against any net.
- **Noise bands** (PLAN2 §2g): seeds differ by ±2.5 points, consecutive checkpoints by up
  to 4 points, cross-process cuDNN nondeterminism ±0.4. **Believe an ablation only above
  +3 points on the full suite, comparing final checkpoints.** In-run evals (432 games,
  `vs_*`/`ci_*`/`eg_*` log keys) are for curves, not conclusions.
- **Post-run chain**: `bash runs/eval_run.sh <run> [device]` → `runs/<run>/analysis.out`
  (in-run tail + full-suite matches vs v2b and dev1 + endgame eval). A watcher pattern for
  queued runs is in `runs/watch_run.sh` / `runs/after_queue2.sh`.

## 3. Strength ladder (full paired suite vs `runs/v2b/net_0150.pt` @64 sims, final checkpoints)

| run | change vs base | score vs v2b | Elo | endgame WDL / regret_raw | verdict |
|---|---|---|---|---|---|
| dev1 | v1 baseline | ~37 % | −95 | 71.2 / 0.083 | superseded |
| v2a | v2 pipeline | ~45 % | −35 | 74.4 / 0.080 | superseded |
| v2b | + exploration floor, sims schedule | 50 (ref) | 0 | 75.0 / 0.078 | reference anchor |
| v2b_s1 | seed 1 | 51.1 [48.4, 53.7] | +7 | 75.1 / 0.075 | noise band |
| v2c | + exact endgame labels | 48.7 [45.8, 51.4] | −9 | 75.9 / 0.077 | no effect (z already exact ≤14 empties) |
| v2d | + sym dedup, α_early, 4-class own, 9 planes | 48.2 [45.4, 50.9] | −12 | 75.8 / 0.079 | no effect |
| abl_noheads | − ownership/margin heads | 50.3 [47.6, 53.1] | +2 | 74.3 / 0.080 | neutral; keep heads for analysis |
| abl_cscale1 | c_scale 0.1 → 1.0 | **55.7 [52.9, 58.5]** | **+40** | 74.6 / 0.077 | **adopt** |
| wide96 | filters 64 → 96 | **55.1 [52.3, 58.0]** | **+36** | 76.2 / 0.077 | **adopt** |
| wide96_c1 | both | **58.4 [55.7, 61.1]** | **+59** | 75.2 / 0.078 | |
| wide128_c1 | filters 128 + c_scale 1.0 | **60.9 [58.2, 63.5]** | **+77** | 76.3 / **0.067** | **current best** |

Costs on the 3090 (150 iterations × 4096 games × 64 moves, sims 32→48→64): 6×64 ≈ 2.3 h
(155–200 games/s), 6×96 ≈ 3.8 h (57/s), 6×128 ≈ 4.5 h (43/s). The current best recipe is
`runs/wide128_c1/config.json`: v2b's schedule + `--c_scale 1.0 --filters 128` + exact labels
(a no-op but free); 7 input planes, 3 ownership classes (the 9-plane/4-class options exist
and changed nothing).

## 4. What was tried and what it taught (details in PLAN2 §2f–§2k, §4)

- **c_scale 1.0**: +40 Elo, free. The gain is in the sharper improved-policy *training
  target*; play-time c_scale is irrelevant. Check every inherited mctx/paper default.
- **Width**: +36/+59/+77 not yet flat. Depth untested (blocks fixed at 6).
- **Exact labels** (`uttt/exact.py`, machinery works, overlaps training at no wall-clock):
  useless because 64-sim self-play outcomes already equal the exact value in 98.7 % of
  ≤14-empties positions. The endgame value error is representational.
- **Draw blindness**: the value head recognises only ~55 % of exact draws at every net size;
  it under-predicts draws (calibration curve bent). A post-hoc WDL logit bias
  (`tools/calibrate.py`, `FusedEvaluator(wdl_bias=)`) lifts WDL accuracy 75→80 % but play is
  unchanged — the search doesn't need it. Report regret for play; use the bias for analyses.
- **SWA over the last checkpoints**: −28 Elo (LR-drop phases don't mix). Final checkpoint is
  the right one to report.
- **Phase-dependent search at play time**: 32 sims → 96 after ply 24 = +50 Elo at equal
  mean cost (`PhasedSearchPlayer`). Not exploitable in self-play below ~8192 games (search
  cost ≈ Σ sims in the launch-bound regime). Depth cap 12 truncates ≤2.3 % of simulations.
- **Data hygiene** (symmetric dedup, early-α, extra planes, 4-class ownership): no Elo; the
  extra planes lower the value loss only. The 15 % exploration floor already fixes openings.

## 5. What we believe about the game (levels: behavioural / predictive / search-relative / exact)

- Openings are flat and the *ordering* is universal: centre-of-centre [40] best in every
  net × budget × seed (Kendall τ ≥ 0.87 across all), centre-of-edge-board [13] always
  worst; root Q-gaps between top replies ≤ 0.02 except after bad first moves.
  (search-relative, highly stable). After [40], the edge-cell reply beats the corner.
- First-player effect: X scores 57–60 % of suite games at 64 sims; draws rise with strength
  (20 % at 256-sim self-play). The tiebreak rule decides ~30 % of strong games.
- Games are decided late (predictive, held-out): the 64-sim best-child Q is right from ply
  38 for the median game (78 % of length); nothing is settled at ply 30.
- Free moves are worth **+0.16 ± 0.03** (256-sim value, matched natural positions,
  cluster-robust) — half the old tensor-probe estimate; biggest late when ahead.
- Board-ownership "hierarchy" is an artefact: with macro threats controlled, owning any
  board class ≈ 0; value lives in macro-line threats (±0.17/line) — i.e. line counts.
- Endgame play is solved by search (256 sims: 99.8 % optimal, regret 0.002), and the raw
  policy's failures concentrate on tiebreak conversion and free-move handling (puzzle set).

## 6. Next steps, in order

1. **Keep scaling** (the only live strength lever): `wide128_c1` recipe with (a) 8 or 10
   blocks at 128 filters, (b) `--games 8192` (the wide nets are GPU-bound, so batch scaling
   is now nearly free — also unlocks per-pool phase-dependent self-play budgets), (c) longer
   runs (`--iters 300`, LR drops ~200/280, replay window up). One change per run; judge by
   §2 rules. Each ≈ 5–9 h; use `runs/queue_3090.sh` / `after_queue2.sh` as templates.
2. **Anchor upkeep**: keep dev1 + v2b as in-run anchors for continuity, add
   `runs/wide128_c1/net_0150.pt` as the third (`--anchors ...,runs/wide128_c1/net_0150.pt`);
   report new runs vs v2b (the ladder's zero) *and* vs wide128_c1.
3. **Best-play configuration**: the playing agent should use ≥256 sims with the phased
   schedule ("0:64,24:256" or similar — re-tune with `tools/openings.py --a_sims`);
   symmetry-averaged evaluation is +1–2 points of WDL accuracy for analysis only.
4. **External test (Phase C's last box)**: a CodinGame submission. The realistic port is the
   bitboard engine + a distilled/quantised small net in C++, or the rollout UCT as a
   baseline entry; treat as a separate engineering task.
5. **Analysis second pass** (cheap, 3060): rerun atlas / decision / freemove / puzzles with
   wide128_c1 (all tools take a checkpoint argument); opening book from the atlas PVs; the
   draw-blindness question — try a draw-weighted value loss (`--value_weight` split by
   class would need a small train2 change) only if the endgame WDL number matters to you,
   it will not move Elo.
6. **Housekeeping**: `runs/` holds 7.3 GB (buffers in `latest.pt` dominate; the `games/`
   corpora are the valuable part). No git repo yet — `git init` + LFS or at least back up
   `suites/`, `*.md`, `uttt/`, `tools/`, `tests/`, `web/`, and one `net_0150.pt` per run.

## 7. Operational notes

- Env: `.venv` (Python 3.10, torch 2.13+cu126, numba 0.67). 3090 = `cuda:0` = nvidia-smi
  index 1; 3060 = `cuda:1` (set `UTTT_DEV=cuda:1` for tests/tools while the 3090 trains).
  12-core 3900X: the exact-label pool uses 12 workers; two launch-bound self-play processes
  throttle each other (~2×) — one training run per machine, analysis on the other GPU.
- Train (current best recipe): `python -u -m uttt.train2 --run runs/<name> --iters 150
  --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8
  --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --c_scale 1.0
  --filters 128 --lr 0.02 --lr_drops 100,140 --eval_every 10 --eval_sims 64
  --anchors runs/dev1/net_0200.pt,runs/v2b/net_0150.pt,runs/wide128_c1/net_0150.pt
  --save_buffer_every 10 --cuda_graph 1 --depth_cap 12 --exact_max_empty 14
  --exact_per_iter 8192 --exact_processes 12` (~4.5 h; resume only from a
  buffer-checkpoint iteration).
- After a run: `bash runs/eval_run.sh <run> [device]`; plots: `tools/plot_run.py runs/<run>`.
- Play: `python web/server.py runs/wide128_c1/net_0150.pt --sims 800 --device cuda:1` →
  http://localhost:8765/ (or `play.py` in the terminal).
- Tests: run each `tests/*.py` directly; they cover engines (cross-checked move by move),
  search eager-vs-graph equality, suites, buffer, exact labels, hygiene, rollout anchor.
- Traps: never rebuild `suites/*` silently (new file = new incomparable yardstick); matches
  are deterministic in-process only (±0.4 points across processes); `torch.multinomial`
  asserts on all-zero rows (guarded once — keep finished games out of selfplay batches);
  Windows + PowerShell `$` quoting — write temp `.ps1` files; a background `Stop-Process`
  filter that matches its own command line kills your own shell (happened twice).
- Corpora: `runs/v2a/games` is the frozen "held-out" source for every suite and analysis
  tool — keep it. ~3 M games total across runs.
