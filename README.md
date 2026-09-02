# uttt-zero

AlphaZero-style agent for Ultimate Tic-Tac-Toe, closed-board / most-boards
rules (CodinGame rules), trained on a single PC, built to *analyse* the game.

In plain terms: a neural network learns to play Ultimate Tic-Tac-Toe entirely by playing
against itself, with a tree search on top of it to "think" before each move. The rules
are CodinGame's variant: a won or full small board is closed, a player sent to a closed
board may play anywhere (a free move), and if nobody makes a line of three boards the
player who won more boards wins (the most-boards count rule; equal is a draw). The point
of the project is not just a strong player. It is to use the trained agent to find out
what is true about the game: which openings are good, when games are decided, what a
free move is worth, and what the network has learned internally. Everything runs on one
Windows PC with two GPUs (an RTX 3090 for training, an RTX 3060 for analysis).

## Start here

Read in this order:

1. **This file** — what the project is, its current state, where things live, how to
   run it.
2. **`PLAN5.md`** — the live plan. It opens with a glossary of the project's terms (Elo,
   the paired suite, sims, iterations, checkpoints, the ±3-point rule and so on), then
   states the decision in front of the project and the analysis programme that follows.
3. **`RETROSPECTIVE.md`** — what was learned over the four days of work: the strength
   ladder, which training changes worked and which did nothing, engineering and
   measurement lessons, and what the agent believes about the game.
4. History, only as needed: `PLAN4.md` (hand-off and review adjudication, superseded by
   PLAN5), `PLAN3.md` (measurement kit, strength ladder, game beliefs; corrections in
   PLAN4), `PLAN2.md` (detailed result sections 2b-2k), `PLAN.md` and `NOTES-v2.md`
   (original plan and notes), `RESULTS-dev1.md` and `RESULTS-v2a.md` (early run results),
   `REVIEW-codex.md`, `REVIEW-sol.md`, `REVIEW-claude.md` (outside reviews: codex in the
   v2a era; sol and claude in the PLAN3 era, adjudicated in PLAN4).

## Current state (2026-09-02)

- **Best network:** `runs/deep10_c1_300/net_0300.pt` — 10 residual blocks of 128
  filters, trained for 300 iterations. It is +242 Elo over the `v2b` reference net at 64
  search simulations per move (about an 80 % expected score).
- **Play configuration:** a flat `--sims 256` or more. The phased search schedule
  (`"0:128,24:384"`, fewer simulations early and more late) helped earlier nets but was
  **not** confirmed on this one (+10 [−7, +26], below the project's ±3-point rule;
  PLAN5 §2 A8c).
- **Training is PAUSED by owner directive.** No training run is to be launched without
  the owner's approval (PLAN4 §3c, PLAN5 §5). The next work is the analysis programme in
  PLAN5 §2–§4.

The strength ladder. Each run changed one thing from the run above it. Elo is measured on
the paired opening suite (516 fixed openings, each played from both sides) against `v2b`,
both sides at 64 simulations per move, using each run's final checkpoint. The last
column is the raw value head (no search) on the exact endgame set: how often it names
the right result, and the average value it loses by playing its preferred move (0 =
perfect). Details in RETROSPECTIVE §2.

| net | recipe | Elo vs v2b @64 | endgame raw WDL / regret |
|---|---|---|---|
| dev1 | v1 baseline | −95 | 71.2 / 0.083 |
| v2b | v2 pipeline + floor + sims schedule | 0 | 75.0 / 0.078 |
| abl_cscale1 | + c_scale 1.0 | +40 | 74.6 / 0.077 |
| wide128_c1 | + filters 128 | +77 | 76.3 / 0.067 |
| deep8_c1 | + blocks 8 | +100 | 77.6 / 0.064 |
| deep8_c1_300 | + 300 iters (drops 200/280) | +211 | 84.0 / 0.045 |
| **deep10_c1_300** | **+ blocks 10** | **+242** | **84.6 / 0.037** |

## Where things live

```
knowledge/      research notes (rules & theory, algorithm, prior art, compute, analysis methods, solving)
uttt/game.py    reference single-game engine (numpy)
uttt/batch.py   batched tensor engine, NN encoding, D4 symmetries
uttt/model.py   ResNet (policy / WDL value / board-ownership heads), evaluators
uttt/mcts.py    v1 batched MCTS, PUCT and Gumbel AlphaZero modes (reference implementation)
uttt/search.py  v2 search: same algorithms, edge statistics, sync-free (identical trees to v1)
uttt/infer.py   fused inference copy of the net (BN folded, fp16, channels_last)
uttt/symmetry.py symmetry-averaged evaluator (exactly equivariant; for analysis)
uttt/solver.py  exact endgame solver (Numba alpha-beta), practical to ~16-18 remaining moves
uttt/exact.py   exact endgame labels during training (a process pool solves late positions while the trainer runs)
uttt/selfplay.py      v1 lock-step self-play + CPU replay buffer
uttt/selfplay_cont.py v2 continuous self-play + GPU replay buffer with duplicate down-weighting
uttt/arena.py   side-swapped evaluation matches (v2 search)
uttt/openings.py fixed opening suite (empty / 15 orbits / natural / random), paired colour-swapped play, pair bootstrap
uttt/rollout.py independent anchor: Numba bitboard UCT with random playouts (no net, no shared search code)
uttt/endgame.py frozen exact-label endgame set (balanced strata, per-move exact values, cluster-bootstrap metrics)
uttt/train.py   v1 training loop (run dev1)
uttt/train2.py  v2 training loop (game persistence, margin head, LR schedule, paired-suite anchor evaluation)
tools/          openings.py (build the suite, paired matches with CIs; players: checkpoint | uct | rollout | random;
                sims may be a ply schedule "0:32,24:96"), endgame.py (build / eval the exact endgame set),
                atlas.py (opening atlas: first-move and reply orbits, rank stability across nets/budgets),
                decision.py (when games become predictable, held-out games), freemove.py (free-move effect,
                prespecified regression with cluster-robust SE), puzzles.py (surprise -> solver-validated puzzles),
                swa.py (checkpoint averaging; negative result), calibrate.py (post-hoc WDL draw bias), ladder.py, match.py (unpaired matches),
                analyze_opening.py, corpus_stats.py, probe_value.py, surprise.py, endgame_accuracy.py (old), plot_run.py
tests/          unit tests and benchmarks (run each file directly; UTTT_DEV=cuda:1 to use the 3060);
                diag_depth_cap.py measures depth-cap truncation
suites/         frozen yardsticks: openings_v1.npz (516 openings from the v2a corpus), endgame_v1.npz (solved
                endgame positions balanced over empties x result x side, from the v2a corpus), puzzles_v1.npz
                (positions where the raw policy loses exact value; PVs, motifs, provenance)
runs/           training runs: config.json, log.jsonl, latest.pt, net_NNNN.pt, games/*.npz, paired_*.json (suite matches)
web/            server.py + index.html: local play/analysis UI (python web/server.py <ckpt> --sims 800 --device cuda:1)
```

A few of the words above, briefly. The *net* is the neural network; a *checkpoint*
(`net_NNNN.pt`) is a saved copy of it after iteration NNNN. An *iteration* is one lap of
self-play followed by training. *Sims* are search simulations per move. *MCTS*, *PUCT*
and *Gumbel* are the tree-search algorithm and its two move-selection rules. The *replay
buffer* is the store of recent self-play positions the trainer samples from. *D4* is the
group of 8 rotations and reflections of the board. *UCT* is the classic tree search with
random playouts and no network. The *paired suite* and the *exact endgame set* are the
project's two frozen yardsticks: never rewritten, so every net is measured on the same
ruler. Each run's `analysis.out` (written by `runs/eval_run.sh`) holds its final in-run
evaluations, its paired-suite matches and its endgame-set scores. PLAN5's glossary has
the rest.

## Setup and standard commands

Setup: `.venv` (Python 3.10) with torch 2.13+cu126, numpy, numba.

```
.venv/Scripts/python.exe tests/test_game.py
.venv/Scripts/python.exe tests/test_batch.py
.venv/Scripts/python.exe tests/test_mcts.py
.venv/Scripts/python.exe -m uttt.train2 --run runs/v2a --iters 150 --games 4096 --steps 64 --sims 32   # v2
.venv/Scripts/python.exe tools/corpus_stats.py runs/v2a --last 20
.venv/Scripts/python.exe tools/openings.py match --a runs/v2b/net_0150.pt --b runs/dev1/net_0200.pt --sims 64   # paired suite match
.venv/Scripts/python.exe play.py runs/v2a/latest.pt --sims 400
.venv/Scripts/python.exe web/server.py runs/v2b/net_0150.pt --sims 800 --device cuda:1   # then open http://localhost:8765/
```

Line by line: the first three run the engine and search unit tests; the fourth starts a
training run (the example is the v2a recipe — do not start one now, see Current state);
the fifth prints statistics over a run's last 20 iterations of self-play games; the sixth
plays a paired-suite match between two checkpoints and reports the score, Elo and
confidence interval; the seventh plays against a net in the terminal; the last serves the
local web UI for play and analysis. To play the current best net, substitute
`runs/deep10_c1_300/net_0300.pt` for the checkpoint path.

Move index convention everywhere: `m = 9*board + cell`, board and cell both
row-major in their 3×3 grids (so 40 = centre of the centre board).
