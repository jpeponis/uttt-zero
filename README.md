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
2. **`PLAN7.md`** — the live plan: the write-up. What the paper is (one paper, working title
   *"A strength-audited self-play analysis of closed-board, most-boards Ultimate
   Tic-Tac-Toe"*, assembled from `KNOWLEDGE.md` and nothing else), the claims audited by
   level, coverage and drift (§1), the literature and where the project sits in it (§2), the
   one run it proposes (§5, K1 — the most-boards tiebreak as a controlled variable), and the
   staged outside review, each stage adjudicated finding by finding in §7e. Its
   **Handover** section says what is running and what to do next. The project's glossary
   (Elo, the paired suite, sims, iterations, checkpoints, the ±3-point rule and so on) is
   `docs/history/PLAN5.md`'s opening section; PLAN7 refers to it rather than repeating it.
3. **`KNOWLEDGE.md`** — what the agent believes about the game: one claim per line with
   its level, effect size, confidence interval, the nets it held across, and the tool and
   file that produced it. This is where a claim lives; the other files hold the working
   notes behind it.
4. **`RETROSPECTIVE.md`** — what was learned over the four days of work: the strength
   ladder, which training changes worked and which did nothing, engineering and
   measurement lessons, and the earlier form of the game beliefs.
5. **`docs/paper/`** — the manuscript in progress, assembled from the claims file:
   `01_claims_map.md` (every claim in `KNOWLEDGE.md` with its level, its coverage and how it
   moved with strength) and `02_literature.md` (the comparators and what is new here). Drafts
   for review, not adopted findings.
6. **`docs/reviews/`** — the outside reviews of this phase, verbatim, with the briefs that
   produced them and their launchers: `M0_plan/` (the review of PLAN7 itself, adjudicated in
   PLAN7 §7e) and `M2_designs/` (the K1 diff and the J3 / J4 designs). The earlier reviews are
   in `docs/history/`.
7. **`docs/explainer.html`** — the public explainer (a 3Blue1Brown-style page for a
   reader with no background), also published at
   https://claude.ai/code/artifact/d3d1bef5-2140-48ee-b55b-ed09d2982791. Opens from
   disk. Its Part 8 is the plain-language version of the game beliefs in `KNOWLEDGE.md`.
8. History, only as needed, all under `docs/history/` (index in its README): `PLAN6.md`
   (the review adjudication, Phases E–H and the closing programme — the update lever measured
   three doublings deep, the equivariant line closed, the second analysis pass; superseded by
   PLAN7), `PLAN5.md` (the analysis programme, the D1/D3 training decisions and the glossary;
   superseded by PLAN6), `REVIEW-astra.md` with `review_astra/` (the outside review PLAN6
   adjudicates, and its reproduction scripts), `PLAN4.md`
   (hand-off and review adjudication, superseded by PLAN5), `PLAN3.md` (measurement kit,
   strength ladder, game beliefs; corrections in PLAN4), `PLAN2.md` (detailed result
   sections 2b-2k), `PLAN.md` and `NOTES-v2.md` (original plan and notes),
   `RESULTS-dev1.md` and `RESULTS-v2a.md` (early run results), `REVIEW-codex.md`,
   `REVIEW-sol.md`, `REVIEW-claude.md` (outside reviews: codex in the v2a era; sol and
   claude in the PLAN3 era, adjudicated in PLAN4). References such as "PLAN4 §3c" in the
   live files mean these.

## Current state (2026-09-12)

- **Best network:** `runs/deep8_c1_300_e8/net_0300.pt` — 8 residual blocks of 128
  filters, 300 iterations, **2048 optimizer steps per iteration** (PLAN6 §9a H1c, 2026-09-10):
  **+40 Elo over its parent deep8_c1_300_e4** [+23, +57], +110 over deep8_c1_300_e2, +211 over
  deep8_c1_300, and +363 over the `v2b` reference at 64 search simulations per move (89 %
  expected score) — **the same +363 `_e4` scored**, because the reference has saturated at this
  strength and differences compress near 90 %; the head-to-head against the parent is the
  instrument now. Three doublings of the update count, one after the other, are worth +204
  between them (+100, +64, +40 — each about two-thirds of the last): the learner had been
  update-limited all along, and eight sampled examples per generated position is still not the
  plateau. Its raw value head names 91.3 % of solved endgames correctly and loses 0.022 of
  value to its preferred move (KNOWLEDGE 46, 47, 49, 51).
- **Play configuration:** a flat `--sims 256` or more. The phased search schedule
  (`"0:128,24:384"`, fewer simulations early and more late) helped earlier nets but is
  **not** confirmed on the strong ones: +10 [−7, +26] on deep10 (PLAN5 §2 A8c) and +11
  [−6, +26] on `deep8_c1_300_e2` (2026-09-07), both below the project's ±3-point rule; not
  re-run on the new net.
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
  (the raw head's endgame reads creep a few points; PLAN5 §5 D3, KNOWLEDGE 42). Nothing was
  running when PLAN6 opened; the ladder still moves only by owner approval — the approved
  chain is below.
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
  the backup, was deferred by the owner then — its push half was done on 2026-09-12 and its
  off-machine copy is still open, the E11 bullet below),
  Phase F (exact equivariance at play is a null, 49.5 % [46.7, 52.3]; at ±2.8 the first LR drop is
  a resolved +5 … +9 on every run and the second does nothing resolvable; the ownership head does
  learn late-game ownership), **Phase G** on the frozen teacher (`runs/gdata_v1.npz`, 500 k
  positions labelled by deep10 8-way @256: the fit depends on optimizer steps, not on distinct
  positions; a D4 group-convolutional net at the same cost fits the teacher far better than the
  ResNet, tied heads alone a third as much, depth not at all — `uttt/equivariant.py`) and **H1**,
  above. **On 2026-09-07 the owner approved a chain of three runs, H1b → H4 → H3.** H1b
  (`deep8_c1_300_e4`, `--epochs 4`) ran 2026-09-07/08 and helped, above; **H4
  (`runs/gcnn8_c1_300_e4`, the D4 group-convolutional net in self-play at the same inference
  cost) finished 2026-09-09 and hurt: 22.0 % [19.9, 24.2], −220 Elo [−242, −199] against its
  parent**, +162 vs v2b, and −50 below deep8_c1_300, the 1×-update ResNet of the same shape and
  duration. Exact symmetry held throughout — the D4 Jensen–Shannon residual is 0.000 bits at all
  30 checkpoints, against the parent's 0.026 — and nothing was unstable; it converged, stably,
  to a much weaker net whose raw head reads 80.8 % WDL and 0.058 regret on the endgame set
  against the parent's 90.1 / 0.022. The mechanism evidence is consistent with capacity rather than
  the learning rate — not its proof (PLAN7 §7e row 20): the
  supervised advantage that licensed the run reverses by 12 480 training steps, where the plain
  ResNet overtakes the equivariant net (KNOWLEDGE 50, 48 restated). (The run was interrupted at
  iteration 268 of 300 by a Windows Update restart at 23:55 on 2026-09-08 and resumed at 09:24
  the next morning with every file verified intact; iterations 260–268 are a perturbed re-run.)
- **The closing programme (owner's decisions, 2026-09-09; PLAN6 §9).** After H4 the owner closed the
  chain and approved **three items and no more**, in this launch order: **H1c `deep8_c1_300_e8`** — the
  third doubling of the optimizer steps (2048 per iteration, parent `deep8_c1_300_e4`, ≈ 22–23 h on the
  3090), reading the dose–response curve +100 → +64 → ? to its asymptote or its plateau; **G arm (g)
  `gcnn8x46`** — the D4 group-convolutional net at the *ResNet's parameter count* (46 base filters × 8
  orientations = 2.46 M parameters, ≈ 8× its inference cost, to be measured), supervised on the frozen
  teacher on the 3060, to separate capacity from equivariance in H4's negative result; and **I1** — the
  analysis second pass, re-running PLAN5 Phase A's tools on `deep8_c1_300_e4` so every game claim quoted from
  the +242 net is re-read 120 Elo higher, each marked held / moved / reversed. **Dropped: H3**
  (`deep8_c1_600_e4`, 600 iterations — it re-buys the data / updates / teacher confound PLAN6 §0 exists
  to remove; its queue scripts stay in the repo, staged but withdrawn) and **H5** (`--head_tying 1` — a
  predicted null whose exact policy symmetry has no consumer). **E11**, the off-machine backup and the
  first push to a remote, was scheduled after the three. Nothing else is proposed.
  **All three are now done.** Arm (g) came back on 2026-09-09 and closed the equivariant line; I1 ran
  on 2026-09-10 (below); and **H1c came in on 2026-09-10** — `runs/deep8_c1_300_e8`, 21.96 h on the
  3090 with no crash, **+40 Elo [+23, +57] over its parent**, helped by the pre-registered rule but
  2.8 points over the line and inside one ≈ 3-point seed band of it. So the dose–response curve is
  **+100 → +64 → +40**, each doubling about two-thirds of the last, and eight sampled examples per
  generated position is still not the plateau — what ran out first is the yardstick, not the lever:
  the new net scores the same +363 against v2b that `_e4` did, because differences compress near
  90 %. It is the play agent from now on (KNOWLEDGE 51, RETROSPECTIVE §2). **Nothing further is
  proposed** — the obvious continuation, `--epochs 16`, would cost ≈ 32 h for a step predicted inside
  the seed band. **E11 followed on 2026-09-12 and is half done — the next bullet.**
- **E11, the off-machine backup and the first push to a remote, 2026-09-12 (PLAN6 §2, §9d) — half
  done.** The repository is public at **`https://github.com/jpeponis/uttt-zero`**: 52 commits, 666
  tracked files, a 249.27 MiB pack on `main`, verified against `git ls-remote` after the push. It is
  licensed **MIT for the code and CC BY 4.0 for the written work and the data**, with `CITATION.cff`
  — see "License and citation" at the end. A pre-push sweep of every tracked file for credential
  shapes found none. **The off-machine copy is still open**: git carries the code, the documents,
  `suites/` and every run's `net_0150/0200/0300.pt`, but not the `games/` corpora or the intermediate
  checkpoints — 5.23 GB of payload (`games/` 2.40 GB, `net_*.pt` 2.81 GB), deferred by the owner for
  want of any destination on this machine, so **the self-play corpora remain single-copy**. `runs/`
  is 17.02 GB in 5 328 files.
- **PLAN7 (2026-09-12), the write-up: the systematic account, the literature, one new question and a
  second outside review.** Written and adopted as the live plan — one paper, working title *"A
  strength-audited self-play analysis of closed-board, most-boards Ultimate Tic-Tac-Toe"*, assembled
  from `KNOWLEDGE.md` and nothing else. **M0, the outside review of the plan itself** — `gpt-6-astra`
  through `codex-sp`, read-only, 564 s, ≈ 4.15 M input tokens — returned **36 findings, all accepted,
  two with a change of reading**, each adjudicated in PLAN7 §7e against the code or the logs here.
  They corrected **KNOWLEDGE 14** ("every one below deep10's interval" was false by its own numbers:
  only the corner leaves it), **31a** (the `_e4` tablebase read was on deep10's corpus), **33** (the
  solver column is one optimal policy's rate, not a property of necessity) and the **§1 note**; and
  **knowledge/06** (Elhage's solver is closed-board / draw; the count tiebreak is win / draw / loss
  for the mover) and **knowledge/07**. **The novelty correction:** `pc29277/AlphaZero_UTTT`
  (2026-08-19) is a public AlphaZero on these exact rules, so the paper claims first *calibrated*,
  first *replicated*, first *used to produce game knowledge* — not "first". **The literature survey**
  `knowledge/07` (885 lines) places the update lever: `--epochs` is Lc0's sampling ratio exactly,
  published practice clusters at ≈ 1, and Wang et al. 2020 is the one prior sweep, in a higher regime.
  **J1a:** the last sealed endgame set, `endgame_v3_test`, read once on `deep8_c1_300_e8` — raw WDL
  **92.7 % [91.8, 93.6]** against its own dev half's **91.6 [90.6, 92.6]**, the sealed half higher:
  claim 30's structure holding at the top of the ladder. No sealed endgame set remains. **The drafts:**
  `docs/paper/01_claims_map.md` (56 claims in 59 rows) and `02_literature.md`. **The engineering
  merged:** the `--rule count|draw` switch through both engines, the solver, exact labels, the
  tablebase, search, the rollout anchor, the trainer and twelve tools, with a regression fixture in
  which `count` reproduces 2 000 pre-edit games bit for bit (K1's prerequisite); `solve_bounded`,
  `tools/frontier.py`, `tools/empty_board.py`, `tools/review_events.py`. **One provenance finding:**
  `gumbel_scale` was never written to `config.json` and every run trained at the default 1.0 —
  constant across runs, so no result moves; it enters the methods section and K1's provenance.
  **Since then (2026-09-12/13):** the rebuttal round, **M2** (K1's diff and the J3 / J4 designs) and **M1** (the
  account) have all run and are adjudicated in PLAN7 §7e, M2's own rebuttal round too (M1's waits for the next Codex
  window); M2's engineering is merged and tested. **K1 — `runs/deep8_c1_300_e8_draw`, the play agent's recipe under
  the plain-draw tiebreak as its one change — was approved by the owner and launched at 00:20 on 2026-09-13**
  (≈ 22 h on the 3090; `runs/queue14.sh`; PLAN7 §5 holds the pre-registered readings, sharpened by M2). The `_e8`
  count-rule pass (K1's parent re-read, §5 item 1) ran on the 3060 the same night; J3 / J4 run after it. E11's
  off-machine copy (5.23 GB) is still owed. Pushed through 2026-09-12 22:00; later commits await the owner's word.
  The play agent is unchanged.
- **I1, the analysis second pass, done 2026-09-10 (PLAN6 §9c):** PLAN5 Phase A's tools re-run on
  `deep8_c1_300_e4` at the deep10 pass's settings — of 34 game claims re-read, **15 held, 18 moved and 1
  reversed** (after [40] that net prefers the corner reply orbit where both earlier strong
  nets preferred the edge), so the project's central methodological claim survives 120 Elo higher with
  exactly one strength-relative ordering; `KNOWLEDGE.md` carries every new number (`runs/plan6/I1_*.out`).
  The matched-parameter G-CNN study (§9b) closed the equivariant line the same night (KNOWLEDGE 48).
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
  net already plays that phase perfectly. **`KNOWLEDGE.md` holds the claims** (55, each with
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
| deep8_c1_300_e2 | + 512 steps / iteration (`--epochs 2`) | +291 | 87.6 / 0.036 |
| deep8_c1_300_e4 | + 1024 steps / iteration (`--epochs 4`) | +363 | 90.1 / 0.022 |
| gcnn8_c1_300_e4 | deep8_c1_300_e4's recipe with the D4 group-convolutional trunk (`--gcnn 16`, exactly equivariant, same inference cost; PLAN6 H4) — hurt | +162 | 80.8 / 0.058 |
| **deep8_c1_300_e8** | **deep8_c1_300_e4 + `--epochs 8` (2048 optimizer steps per iteration; PLAN6 §9a H1c)** | **+363 (+40 vs e4)** | **91.3 / 0.022** |

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
`runs/deep8_c1_300_e8/net_0300.pt` for the checkpoint path.

Move index convention everywhere: `m = 9*board + cell`, board and cell both
row-major in their 3×3 grids (so 40 = centre of the centre board).

## License and citation

This repository is two artifacts under one roof, and they are licensed separately.

- **The software** — `uttt/`, `tools/`, `tests/`, `web/`, `play.py` — is under the
  **MIT license** (`LICENSE`).
- **The written work and the data** — `README.md`, `KNOWLEDGE.md`, `PLAN7.md`,
  `RETROSPECTIVE.md`, `knowledge/`, `docs/`, and the released `suites/`, run logs and
  network checkpoints — is under **CC BY 4.0** (`LICENSE-CC-BY-4.0.txt`).

The split is deliberate. The prose is the substance of the project, not documentation of
the code: a claim in `KNOWLEDGE.md` carries a measurement, a confidence interval and the
tool that produced it, and CC BY 4.0 is the license that keeps attribution attached to it
while allowing reuse. MIT is the plainer instrument for the code, which people should be
able to lift into their own work without conditions beyond the notice.

Cite it with `CITATION.cff` (GitHub renders a "Cite this repository" button from it).

