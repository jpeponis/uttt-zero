# uttt-zero — project plan

Goal: train an AlphaZero-style agent for Ultimate Tic-Tac-Toe under the
closed-board / most-boards rules (= CodinGame rules), play it, then use it to
analyse the game. Research basis: `knowledge/01`–`06`.

## 0. Findings that shape the plan (from the knowledge base)

- **The variant is exactly CodinGame's** (`knowledge/01`): won or full boards
  are closed, a closed target gives a free move, 3 boards in a row wins,
  otherwise more won boards wins, equal counts = draw.
- **Unsolved and not solvable here** (`knowledge/06`): the 2020 "at most 43
  moves" paper solves Orlin's *original* rules (you must keep playing inside a
  won board), by hand, with no computer. The closed-board game's state space is
  ~10^33–10^38; the best solver (Elhage's DFPN) extrapolates to hundreds of
  millions of CPU-hours. A K=1-open-board endgame tablebase (~10^10 positions)
  *is* feasible and is the one exact component worth building.
- **Not moot** (`knowledge/03`): no public AlphaZero-style agent exists for the
  most-boards variant (the two that exist for CodinGame rules are private
  bots); nothing resembling a strategy analysis has been published for any
  variant. Best public baselines: uttt.ai (draw variant, 5M params) and
  SaltZero (draw variant, beat the #2 CodinGame bot).
- **Algorithm** (`knowledge/02`): Gumbel AlphaZero at ~32 sims/move, 6×64
  ResNet on 9×9 planes, WDL value head + local-board ownership auxiliary,
  D4 symmetry augmentation, no gating, lock-step vectorised search on the GPU.
- **Compute** (`knowledge/04`): comparable games (Hex, Othello, Go 9×9) reach
  strong play in 3–18 GPU-hours with pgx-style vectorised self-play; expect
  0.3–2 M games = hours to ~2 days on the 3090.

## 1. Measured on this machine (2026-08-29)

| Component | Result |
|---|---|
| Batched engine, 32k games, 3090 | 6.6–6.9 M game-steps/s incl. encoding |
| Net 6×64 fp16, batch 4096, 3090 | 17 ms/batch = 0.24 M positions/s |
| Net 4×64 fp16, batch 4096, 3090 | 10 ms/batch = 0.39 M positions/s |
| Net 6×64 fp16, batch 4096, 3060 | 33 ms/batch = 0.12 M positions/s |
| Tree ops per simulation, 4096 trees | 16–18 ms (uniform evaluator, no net) |
| Self-play, dev1 (v1 lock-step, eager) | 25–33 games/s ≈ 100 k games/h, GPU 20–35 % busy |
| Self-play, v2 eager (edge stats, 2 syncs/sim) | 42–60 games/s |
| **Self-play, v2 CUDA-graph mode** (`runs/v2a`) | **155–170 games/s ≈ 600 k games/h**, ~10 k positions/s, GPU 84 % busy |

So 1 M self-play games ≈ 1.7 h in graph mode (was ~10 h in dev1).

## 2. Phases

### Phase A — pipeline (done)
- [x] Reference engine + tests (`uttt/game.py`, `tests/test_game.py`)
- [x] Batched tensor engine, encoding, D4 symmetries, cross-checked (`uttt/batch.py`)
- [x] ResNet with policy / WDL / ownership heads (`uttt/model.py`)
- [x] Batched MCTS: PUCT and Gumbel (`uttt/mcts.py`), tactical tests
- [x] Self-play, replay buffer, trainer, arena (`uttt/selfplay.py`, `train.py`, `arena.py`)
- [x] Smoke run; first real run `runs/dev1` (4096 games × 32 sims, 6×64, 200 iters)

### Phase B — make it learn well (in progress)
- [x] dev1 finished (200 iterations, 820 k games, ~12 h): see `RESULTS-dev1.md`.
      Plateau from iteration ~90; root policy collapse; heavy opening duplication;
      evaluation cost a third of the wall-clock.
- [x] v2 pipeline (`NOTES-v2.md` §8): sync-free edge-statistics search, fused
      inference, continuous self-play, GPU buffer with duplicate down-weighting,
      sampled opening moves + root prior floor, margin head, LR schedule, game
      persistence, cheap fixed-anchor evaluation.
- [x] v2a run (`runs/v2a`, `RESULTS-v2a.md`): 789 k games in 2.75 h; +70 Elo over dev1's final net;
      corpus statistics (tiebreak share, decision phase, free-move tempo); opening table.
- [x] CUDA-graph search (155–220 games/s), symmetry-averaged evaluator, per-orbit deep opening search.
- [ ] v2b run (`runs/v2b`): exploration floor, progressive sims 32 → 48 → 64, anchors dev1 + v2a.
- [ ] Search-value mixing, bigger batches, wider net (6×96 / 8×128), ownership/margin ablation.
- [ ] Scale the net (6×96, 8×128) once 6×64 plateaus under v2.

### Phase C — evaluation anchors
- Checkpoint Elo ladder (side-swapped matches, Bayesian Elo).
- Plain UCT with random rollouts at large budgets as a fixed classical anchor.
- Rebuild a CodinGame-Legend-grade bitboard MCTS (Numba) as an external anchor;
  optionally SaltZero / uttt.ai under *their* draw rules for calibration.
- Endgame tablebase (K = 1 open board) → exact labels for the value head.

### Phase D — play against it
- Text / web UI (`play.py` first; a browser page later) with search budget,
  hints, and the agent's evaluation shown per move.

### Phase E — analysis of the game (the real goal; `knowledge/05`)
1. Self-play corpus statistics: win rate by first move (15 symmetry orbits),
   share of games ending by line vs. count, closed-board counts by ply, free-move
   frequency and its value, which local boards are won first, centre control.
2. Opening value heatmaps and principal-variation trees from deep search
   (thousands of sims) at every first move / every 2-ply opening.
3. Counterfactual value probes: flip ownership of a local board, remove a
   free move, etc., and read the value-head delta — quantifies "the centre
   board is worth X", "a free move is worth Y".
4. Surprise mining: positions where the net's prior and the search disagree
   most — the tactical motifs the net has not internalised.
5. Ambitious: linear concept probes on the residual stream (McGrath et al.),
   with ablation checks, and distillation into a small rule set to test how
   much strength survives.

## 3. Open questions for John
- Rule check: tie on board count = draw (as on CodinGame) — confirmed as the
  implemented rule; say if you play it differently.
- Are you happy for the 3090 to be busy for hours at a time? Runs resume from
  `latest.pt`, so they can be stopped and restarted freely.
