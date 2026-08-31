# uttt-zero

AlphaZero-style agent for Ultimate Tic-Tac-Toe, closed-board / most-boards
rules (CodinGame rules), trained on a single PC, built to *analyse* the game.

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
PLAN4.md        START HERE: hand-off, review adjudication, corrected claims, next steps (supersedes PLAN3)
PLAN3.md        measurement kit, strength ladder, game beliefs (referenced by PLAN4, corrections there)
PLAN2.md        detailed result sections (2b-2k) referenced by PLAN3
PLAN.md, NOTES-v2.md, RESULTS-dev1.md, RESULTS-v2a.md   original plan, notes, run results
REVIEW-codex.md, REVIEW-sol.md, REVIEW-claude.md        outside reviews (codex: v2a era; sol + claude: PLAN3 era, adjudicated in PLAN4)
```

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

Move index convention everywhere: `m = 9*board + cell`, board and cell both
row-major in their 3×3 grids (so 40 = centre of the centre board).
