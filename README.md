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
2. **`PLAN6.md`** — the live plan: the outside review adjudicated finding by finding (§1),
   then the work in order — repair the analysis instrument (Phase E), cheap measurements
   (F), the frozen-teacher architecture study (G) and the training runs to propose (H). Its
   **Handover** section says what is running and what to do next. The project's glossary
   (Elo, the paired suite, sims, iterations, checkpoints, the ±3-point rule and so on) is
   `docs/history/PLAN5.md`'s opening section; PLAN6 refers to it rather than repeating it.
3. **`KNOWLEDGE.md`** — what the agent believes about the game: one claim per line with
   its level, effect size, confidence interval, the nets it held across, and the tool and
   file that produced it. This is where a claim lives; the other files hold the working
   notes behind it.
4. **`RETROSPECTIVE.md`** — what was learned over the four days of work: the strength
   ladder, which training changes worked and which did nothing, engineering and
   measurement lessons, and the earlier form of the game beliefs.
5. **`docs/explainer.html`** — the public explainer (a 3Blue1Brown-style page for a
   reader with no background), also published at
   https://claude.ai/code/artifact/d3d1bef5-2140-48ee-b55b-ed09d2982791. Opens from
   disk. Its Part 8 is the plain-language version of the game beliefs in `KNOWLEDGE.md`.
6. History, only as needed, all under `docs/history/` (index in its README): `PLAN5.md`
   (the analysis programme, the D1/D3 training decisions and the glossary; superseded by
   PLAN6), `REVIEW-astra.md` with `review_astra/` (the outside review PLAN6 adjudicates, and
   its reproduction scripts), `PLAN4.md`
   (hand-off and review adjudication, superseded by PLAN5), `PLAN3.md` (measurement kit,
   strength ladder, game beliefs; corrections in PLAN4), `PLAN2.md` (detailed result
   sections 2b-2k), `PLAN.md` and `NOTES-v2.md` (original plan and notes),
   `RESULTS-dev1.md` and `RESULTS-v2a.md` (early run results), `REVIEW-codex.md`,
   `REVIEW-sol.md`, `REVIEW-claude.md` (outside reviews: codex in the v2a era; sol and
   claude in the PLAN3 era, adjudicated in PLAN4). References such as "PLAN4 §3c" in the
   live files mean these.

## Current state (2026-09-07)

- **Best network:** `runs/deep8_c1_300_e2/net_0300.pt` — 8 residual blocks of 128
  filters, 300 iterations, **512 optimizer steps per iteration** (PLAN6 H1, 2026-09-07):
  +291 Elo over the `v2b` reference at 64 search simulations per move (84 % expected
  score), **+100 over its parent deep8_c1_300 and +86 over the previous best,
  deep10_c1_300**, for 1.3 extra hours of training. The learner had been update-limited
  all along (KNOWLEDGE 46, 47).
- **Play configuration:** a flat `--sims 256` or more. The phased search schedule
  (`"0:128,24:384"`, fewer simulations early and more late) helped earlier nets but was
  **not** confirmed on this one (+10 [−7, +26], below the project's ±3-point rule;
  PLAN5 §2 A8c).
- **The ladder is paused by owner directive** (PLAN4 §3c, PLAN5 §5): no new rung without the
  owner's approval. **The one owner-approved run, D1 — the seed replicate
  `runs/deep10_c1_300_s1` (same recipe as the best net, `--seed 1`) — finished 2026-09-05**
  after a power loss and a closed console window cost it a day (PLAN5 Handover). It scores
  +213 [+190, +236] vs v2b, **+9 [−10, +28] vs deep8_c1_300 and +4 [−13, +22] against the
  other seed**: the seed band at 10×128 is ≈ 3 points / ≈ 30 Elo, and the last rung
  ("+ blocks 10", +35 on the first seed) is inside it — not an established rung; duration
  (+211) is the last confirmed one. `deep10_c1_300/net_0300.pt` stays the play agent. Its
  checkpoint timeline repeats the reference's (PLAN5 §3 B1); the probe and
  value-decomposition controls are in §3 B2/B3. **The one experiment the analysis suggested, D3
  (`runs/deep10_c1_300_lr150`, the same recipe with the LR drops moved earlier to 150/250),
  ran 2026-09-05/06 and hurt by its pre-registered criterion:** −32 Elo [−50, −14] against
  the reference (one perturbed run read against the seed band — "same seed" only fixes the
  start here, PLAN6 §1 item 13), −10 against the replicate, +193 vs v2b. The drop is a fixed
  ≈ +9 step on whatever the constant-LR phase has built; no strength gain resolves after it
  (the raw head's endgame reads creep a few points; PLAN5 §5 D3, KNOWLEDGE 42). Nothing is
  running; the ladder stays paused.
- **PLAN6 (2026-09-06), after an outside review of the project's method and its use of the
  game's symmetry:** the review found two bugs in the opening-book instrument (one orbit
  listed three times as the "top three" replies; principal lines that mixed coordinate
  frames — one illegal displayed line per book) and a confound in how "duration" had been
  reasoned about (an iteration doubles data *and* optimizer steps *and* moves the teacher and
  the LR phases). Phase E repairs the instrument (the book and the atlas are rebuilt by orbit;
  KNOWLEDGE claims 4, 5, 7, 7a, 9, 20, 28, 41, 42 restated — no number moves except the
  book's), then Phase F takes an hour of cheap play-time measurements, Phase G answers the
  architecture question on frozen data, and Phase H proposes runs in order: `--epochs 2` on
  8 blocks first (H1), 600 iterations after (H3). **Done 2026-09-06/07:** Phase E (E1–E10; E11,
  the backup, is deferred by the owner until the write-up — the repository has no remote yet),
  Phase F (exact equivariance at play is a null, 49.5 % [46.7, 52.3]; at ±2.8 the first LR drop is
  a resolved +5 … +9 on every run and the second does nothing resolvable; the ownership head does
  learn late-game ownership), **Phase G** on the frozen teacher (`runs/gdata_v1.npz`, 500 k
  positions labelled by deep10 8-way @256: the fit depends on optimizer steps, not on distinct
  positions; a D4 group-convolutional net at the same cost fits the teacher far better than the
  ResNet, tied heads alone a third as much, depth not at all — `uttt/equivariant.py`) and **H1**,
  above. See PLAN6's log; proposals for the next runs in its Handover.
- **Analysis programme (PLAN5 Phases A–C): complete, 2026-09-03.** Every ordering and sign
  from the earlier nets held on the +242 net; two magnitudes moved (the free-move value,
  +0.16 → +0.20, and a small residual value per owned board once macro lines are
  controlled); the endgame yardstick was not flattered by its in-run reads
  (`suites/endgame_v2_dev`; the sealed `endgame_v2_test` half, read once after D1, agrees
  within a point). The checkpoint
  timelines put the +127 duration gain at the first LR drop plus the constant-LR climb;
  probes with a random-init control say what the trunk computes and when; the opening
  book to depth 4 has the two strong nets agreeing on 75 % of nodes and a reply rule (the
  self-send); a legible linear surrogate captures 41 % of the search's moves and none of
  the strength (−661 Elo vs v2b); the one-open-board tablebase adds nothing because every
  net already plays that phase perfectly. **`KNOWLEDGE.md` holds the claims** (49, each with
  level, effect size, CI, nets, tool and file); PLAN5 §2–§4 hold the working notes.

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
| deep10_c1_300 | + blocks 10 | +242 | 84.6 / 0.037 |
| deep10_c1_300_s1 | same recipe, seed 1 (replicate) | +213 | 83.9 / 0.047 |
| deep10_c1_300_lr150 | LR drops at 150/250 (hurt) | +193 | 83.3 / 0.051 |
| **deep8_c1_300_e2** | **deep8_c1_300 + 512 steps / iteration (`--epochs 2`)** | **+291** | **87.6 / 0.036** |

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
uttt/concepts.py hand-written concept labels from the board state (free move, threats, dead boards, ...) for probing
uttt/surrogate.py per-move and per-position features in torch + a linear surrogate evaluator (PLAN5 B6)
uttt/tablebase.py exact one-open-board tablebase (1 MB) and an evaluator wrapper that splices it into the search (C5)
uttt/equivariant.py D4-tied heads and a group-convolutional ResNet, exactly equivariant, exporting to plain modules (PLAN6 G)
tools/          openings.py (build the suite, paired matches with CIs; players: checkpoint | uct | rollout | random;
                sims may be a ply schedule "0:32,24:96"; --a_sym/--b_sym for symmetry-averaged play),
                endgame.py (build / eval the exact endgame set; --split dev,test splits by source game),
                timeline.py (PLAN5 B1: every checkpoint of a run on one iteration axis), probe.py (B2: concept
                probes on the residual stream, random-init control), value_decomp.py (B3: value regressed on
                concepts per checkpoint), book.py (C1: opening book to depth d at deep search), book_stats.py,
                principles.py (C2: folk claims), annotate.py (C3: solver-annotated puzzles), distill.py (B6: fit and
                play the legible surrogate), tablebase_grade.py (C5: grade a net on one-open-board positions),
                eval_worker.py (PLAN6 E7: out-of-process full-suite evaluator of a run's checkpoints -> eval_full.jsonl),
                gdata.py (G-data: the frozen-teacher dataset), gstudy.py (G0 / the G arms: supervised students and
                their metrics), gtiming.py (inference cost per arm), ownership_grade.py (E9), suite_overlap.py (E10),
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
`runs/deep8_c1_300_e2/net_0300.pt` for the checkpoint path.

Move index convention everywhere: `m = 9*board + cell`, board and cell both
row-major in their 3×3 grids (so 40 = centre of the centre board).
