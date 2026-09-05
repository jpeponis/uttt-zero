# uttt-zero — PLAN5 (draft for owner review, 2026-09-02): from strength to understanding

**What this plan is.** uttt-zero has spent four days making its network stronger at
Ultimate Tic-Tac-Toe. This plan proposes to stop doing that for now and to use the
strongest network we have, `runs/deep10_c1_300/net_0300.pt`, to study the game instead.
It was written at the pause the owner called in PLAN4 §3c, after RETROSPECTIVE.md. If you
are picking the project up: read §0 for the decision and the recommendation, then start
with §6 (housekeeping, one hour) and Phase A (§2). Training is paused by owner directive.
No training run may be launched without the owner's approval (§5).

## Handover (2026-09-03, end of the analysis session)

**State.** Phases A, B and C are complete and written up in this file (results blocks at the
end of §2, §3 and §4) and distilled into `KNOWLEDGE.md` (49 claims). §6 is done except the
off-machine copy of the backup (local copy at `C:/Users/John Peponis/uttt-zero-backup/`).
Neither §0 resume criterion fired: no belief's magnitude moved between deep8_c1_300 and
deep10_c1_300 by more than its CI, and nothing appears late in the checkpoint timelines.
The seed replicate (D1, 2026-09-05) changes nothing there: every Phase B fact is on both
seeds, nothing appears late on the third run either, and the last rung of the ladder turns
out to be inside the seed band (§5 D1) — which argues *against* resuming the ladder for
depth; §5 D3 (an earlier first LR drop) remains the cheapest experiment if any.
Everything is committed (last commit: the B6/C5 results). The explainer artifact is
republished; the owner moves the share pin.

**D1, the seed replicate — done 2026-09-05 07:40, results in §5 D1** — `runs/deep10_c1_300_s1`, launched 2026-09-03
11:52 by `runs/queue7.sh` (log `runs/deep10_c1_300_s1.out`, wrapper log
`runs/queue7.out`), on the 3090. **Interrupted by a power loss 2026-09-03 ≈ 15:52** (unclean
shutdown, Kernel-Power event 41; iteration 94 was the last logged; the retry wrapper died
with the machine, so nothing restarted by itself). **Relaunched 2026-09-04 16:33** by the
same `queue7.sh` through a Task Scheduler job; `train2` resumed from `latest_full.pt`
(iteration 89, buffer 2 M). **Killed again 2026-09-04 19:00** at iteration 128: that
launcher had opened a *visible* console window, and seconds after a VNC connection to the
desktop the whole console process group exited with `STATUS_CONTROL_C_EXIT` (a window
close or Ctrl-C; the `PermissionError` tracebacks in the `.out` are the exact-label pool
respawning workers from a dying parent — not a fault). **Relaunched 2026-09-04 19:49** with a
hidden console: `runs/launch_queue7_hidden.vbs` (wscript, window style 0) →
`runs/launch_queue7_run.cmd` → `queue7.sh`, resumed from `latest_full.pt` at iteration
119. Replayed iterations (90–94, 120–128) appear twice in `log.jsonl`; the last row wins
(the deep8_c1_300 convention); `config_resume_*.json` records each re-invocation. Expect
`runs/deep10_c1_300_s1/DONE` around 2026-09-05 07:30, after which `eval_run.sh` runs by
itself and writes
`runs/deep10_c1_300_s1/analysis.out` (paired matches vs v2b, wide128_c1, deep8_c1,
deep8_c1_300, deep10_c1_300, dev1, and the endgame set). Graph eval is *on* with the retry
wrapper: if the run dies, it resumes from `latest_full.pt` by itself (up to 6 attempts);
check the `.out` for "attempt … died" lines — a fault costs ≤ 10 iterations and tells us
the fault surface is still live. Do not touch its config while it runs. *Operating it:*
nothing is visible on the desktop (hidden console, by design); `python
tools/run_status.py runs/deep10_c1_300_s1` is the one-line status, `bash runs/watch_d1.sh`
the event stream. It was started through a Task Scheduler job `uttt-queue7` (action:
`wscript runs/launch_queue7_hidden.vbs`, no trigger of its own) so that it outlives any
terminal or Claude session; if it ever needs relaunching, `schtasks /Run /TN uttt-queue7`
resumes from `latest_full.pt`. To stop it deliberately, end the `bash queue7.sh` wrapper
first (it would otherwise restart the trainer after 60 s), then `uttt.train2`. When it is
done, `schtasks /Delete /TN uttt-queue7 /F` removes the job.

**What the next instance does, in order.** *Status 2026-09-05 10:00:* steps 2–4 are done —
§5 D1 (strength; RETROSPECTIVE §2, KNOWLEDGE 43–44), §3 B1 / B2 / B3 "replication on the
seed replicate" (KNOWLEDGE 14–17, 19, 37–42 now say which facts held on both seeds: all of
them, with one deep10-only coefficient path noted in B3), §2 A9 (the sealed test half, read
once; KNOWLEDGE 30). Step 5 decided: the ladder stays paused; **D3, the earlier-LR-drop run
`runs/deep10_c1_300_lr150`, is running** (launched 2026-09-05 12:12 via the scheduled job
`uttt-queue8` -> `runs/launch_queue8_hidden.vbs` -> `runs/queue8.sh`; log
`runs/deep10_c1_300_lr150.out`, status `python tools/run_status.py runs/deep10_c1_300_lr150`,
events `bash runs/watch_train.sh deep10_c1_300_lr150 queue8`; ~14 h, then `eval_run.sh` by
itself, including a match against the seed replicate). When it finishes, read its result
against the pre-registered criterion in §5 D3 and record it there. Outputs of steps 2-4:
`runs/plan5_D1_control.{sh,out}`, `runs/plan5_B1_timeline_s1.out`, `plan5_B2_fit_s1.out`,
`plan5_B2_report_s1.out`, `plan5_B3_value_s1.out`, `plan5_A9_test_{deep10,deep8,s1}.out`.
1. *While D1 runs* (3060 free; nothing else is queued): nothing is required. Optional: the
   Game-Changer-style annotation of B4's top surprises (C3, not done); a two-open-board
   reachable-only tablebase design (C5's real frontier, not started).
2. *When D1 finishes*: read `analysis.out`. The numbers that matter: its score vs v2b @64
   (deep10_c1_300's was 80.6 % in-run / +242 Elo on the suite), vs deep8_c1_300 (+35 was
   the last rung — this is its second measurement) and vs deep10_c1_300 (the **seed band
   at 10×128**, previously unmeasured; the 6×64 band was ±2.5 points). Record all three in
   §5 D1 and in RETROSPECTIVE §2.
3. *The control for Phase B*: run the same three tools on the replicate and compare with
   `runs/deep10_c1_300/`'s outputs — `tools/timeline.py runs/deep10_c1_300_s1 --corpus
   runs/deep8_c1_300 --last 20`, `tools/probe.py fit --data runs/probe_data_deep8late.npz
   --run runs/deep10_c1_300_s1 --control`, `tools/value_decomp.py runs/deep10_c1_300_s1
   --data runs/probe_data_deep8late.npz`, then `tools/probe_report.py`. A concept, layer,
   "learned by" checkpoint or coefficient is a fact about the game only if both seeds have
   it (§1c "two seeds or it's a seed"). Update KNOWLEDGE claims 14–17, 37–42 with "both
   seeds" or the disagreement. Also `tools/atlas.py`/`tools/book.py` on the replicate if the
   agreement question (claim 7) is worth a third net.
4. *Then* the sealed test set: `tools/endgame.py eval <net> --set suites/endgame_v2_test.npz`
   for deep10_c1_300, deep8_c1_300 and the replicate — **once**, log the reading in §2 A9
   and KNOWLEDGE claim 30. After that it is a development set like the others.
5. *Then* decide with the owner: the ladder stays paused unless §0's criteria fire; the
   cheapest training experiment on B1's evidence is an earlier first LR drop
   (`--lr_drops 150,250`, §5 D3), not more iterations.

**Traps.** `runs/probe_*` nets are untrained; `suites/` v1 files are never rewritten;
`endgame_v2_test` is read once; every analysis tool defaults to `--device cuda:1` (the 3060)
except `tools/openings.py match` and `tools/book.py` (cuda:0 — pass `--device cuda:1`
while D1 holds the 3090); held-out positions for deep10 come from deep8_c1_300's late games
and vice versa (§8) — for the replicate, deep8_c1_300's games are held out too. The
auto-mode classifier blocks launching multi-hour training from a shell; the owner launches.

**Files added this session** (all in git): tools `timeline`, `probe`, `probe_report`,
`value_decomp`, `book`, `book_stats`, `principles`, `annotate`, `distill`,
`tablebase_grade`; modules `uttt/concepts.py`, `uttt/surrogate.py`, `uttt/tablebase.py`
(+ tests); `tools/endgame.py --split`, `tools/openings.py --a_sym/--b_sym/--a_tb/--b_tb`
and `surrogate:<file>` players; suites `endgame_v2_{dev,test}`, `puzzles_v2_dev`; docs
`KNOWLEDGE.md`, `docs/positions.md`, `docs/history/`; queue scripts `runs/plan5_*.sh`,
`runs/queue7.sh`; every `runs/plan5_*.out`, `runs/book_*`, `runs/principles_*`,
`runs/surrogate_deep10.json` and the per-run `timeline / probes / value_decomp` outputs.

**How this file is organised.** §0 states the decision to be made (more training, or use
the net we have?) and recommends an answer. §1 reviews the work so far. §2–§4 describe the
analysis programme in three phases, A, B and C. §5 is Phase D, the training that may
follow, provisional until Phases A–C report. §6 is housekeeping, §7 the order of work and
the GPU budget, §8 operational notes. Numbers are from RETROSPECTIVE.md, PLAN4 §3–§4,
`runs/*/analysis.out` and `runs/plan5_A8.out`.

## Glossary

Terms used in this file and across the project. Later sections assume them.

- **The game.** Ultimate Tic-Tac-Toe is a 3×3 grid of small tic-tac-toe boards. The cell
  you play in sends your opponent to the matching small board. Winning three small boards
  in a line wins the game. In this project's rules (CodinGame's) a won or full board is
  *closed*, and a player sent to a closed board gets a **free move** (may play on any open
  board). If nobody makes a line, whoever won more small boards wins — the **count rule**,
  also called the most-boards tiebreak; equal counts is a draw. A **macro line** is a
  line of three small boards on the big board. A **ply** is one move by one player; games
  last about 50 plies.
- **Net, checkpoint, run.** The *net* is the neural network. Given a position it outputs
  a *policy* (a probability for each move) and a *value* (who is winning). A
  **checkpoint** is a saved copy of the net's weights: `runs/<run>/net_0300.pt` is the
  net after iteration 300 of that run. A **run** is one complete training job, kept in
  `runs/<name>/` with its `config.json`, `log.jsonl`, checkpoints and games. Each run's
  name says what it changed: `deep10_c1_300` is 10 blocks, c_scale 1.0, 300 iterations.
- **Iteration.** One lap of the training loop. The current net plays a batch of games
  against itself (**self-play**; 4096 games per iteration here), the positions go into
  the **buffer** (a store of the most recent 2 M positions), and the net is trained on
  samples drawn from the buffer. Runs here are 150 or 300 iterations long (dev1, the v1
  baseline, ran 200).
- **Sims.** Search simulations per move — how long the program "thinks" before it moves.
  The net's output with no search at all is the **raw policy** or **raw head**; with
  search it is the **search** move or value. Self-play here uses 32–64 sims, the strength
  ladder is measured at 64, and play uses 256 or more. A **phased** schedule such as
  `"0:128,24:384"` means 128 sims per move from ply 0 and 384 from ply 24. The training
  recipe's **sims schedule** (`--sims_schedule 60:48,100:64`) is a different thing: it
  raises self-play sims over the run, 32 until iteration 60, then 48, then 64 from 100.
- **Heads.** The net's outputs. The **policy head** gives move probabilities. The **WDL
  head** (win/draw/loss) gives the value as three probabilities. The **ownership head**
  is an auxiliary output that predicts which side will own each small board at the end.
  The **residual stream** is the internal activation passed from block to block.
- **Blocks and filters (depth and width).** The net is a stack of residual *blocks*, each
  with some number of *filters* (channels). "6×64" means 6 blocks of 64 filters; "10×128"
  means 10 blocks of 128. More blocks is deeper, more filters is wider. The cost of one
  evaluation grows roughly as blocks × filters².
- **Elo.** A rating scale for relative strength. A difference of +100 means the stronger
  side is expected to score about 64 % (a win counts 1, a draw ½); +242 means about
  80 %. Elo here is always relative to a named opponent at a named number of sims. It is
  not transitive: A's Elo over C need not equal A over B plus B over C.
- **The paired suite.** The project's fixed strength yardstick. 516 fixed opening
  positions (`suites/openings_v1.npz`: the empty board, 15 first-move orbits, 250
  "natural" and 250 random 4-ply openings). Each is played twice, once with each side as
  X, so any colour advantage cancels — 1032 games. The **score** is the percentage of
  points won (50 % = equal), and a **point** is one percentage point of score. The **95 %
  CI** (confidence interval) is the range the true score would fall in 19 times out of
  20 if the match were repeated; it is computed by **bootstrap** (resampling the opening
  pairs) and is about ±2.8 points on the full suite. **The ±3-point rule:** no result is
  believed unless the run's *final* checkpoint scores at least 3 points above 50 % on the
  full suite.
- **D4 symmetry and orbits.** The 8 rotations and reflections of the board (the dihedral
  group D4) do not change what a position means. The 81 possible first moves fall into
  15 classes under those symmetries; each class is an **orbit**.
- **Ladder and rung.** The ladder is the chain of runs in which each beat its parent run
  on the paired suite, quoted as Elo over the `v2b` net at 64 sims. A **rung** is one
  such step. RETROSPECTIVE §2 has the full table.
- **Null result.** An intervention that produced no measurable change — a score inside
  the noise band — and was written down as such.
- **LR drops.** The learning rate (LR) is the size of each weight update during training.
  Dropping it late in a run (here at iterations 200 and 280, `--lr_drops 200,280`) lets
  the net settle. This is also called **annealing**, and each drop usually produces a
  visible step in quality.
- **Seed replicate.** The same recipe run again with a different random seed. The
  difference between the two results is the **seed band**: the noise floor for judging
  small effects.
- **Held-out.** Data the net never trained on. A run's own self-play games are all
  training data at some point, so held-out games have to come from a different run.
- **Probe** — three uses. (1) A *throughput probe* (`runs/probe_g8192`, `runs/probe_b8`):
  a 3-iteration run made only to measure speed; its nets are untrained. (2) A *concept
  probe* (Phase B): a small classifier trained on the net's internal activations to test
  whether a concept, say "a free move is available", can be read off them. (3)
  `tools/probe_value.py`: a tool that changes one feature of a position and measures how
  the value head responds.
- **FLOP-matched / equal-compute.** A comparison at equal total arithmetic (FLOPs) rather
  than at equal sims. A net that costs 6.7× more per simulation gets 6.7× fewer sims:
  deep10@64 vs v2b@427. "@64" means "playing at 64 sims".
- **Endgame set.** `suites/endgame_v1.npz`: 3000 positions with 6–16 empty cells left in
  open boards, each solved exactly by `uttt/solver.py`. **Raw WDL** accuracy is how often
  the value head names the correct result. **Regret** is the value lost by playing the
  net's move instead of the best one, averaged (0 = perfect). **Optimal %** is how often
  the chosen move is exactly best. **Draw recognition** is WDL accuracy on the drawn
  third of the set.
- **Rollout anchor.** `uttt/rollout.py`: a plain tree search with random playouts and no
  net, used as an independent fixed opponent. "100 k playouts" is its budget per move.
- **The GPUs.** The 3090 (`cuda:0`) trains; the 3060 (`cuda:1`) runs analysis.
  `nvlddmkm` is the NVIDIA Windows driver; a "fault" is that driver crashing. A **CUDA
  graph** is a recorded sequence of GPU commands replayed to avoid launch overhead;
  **eager** means running without graphs.
- **Gumbel and c_scale.** The search is the Gumbel AlphaZero variant. `c_scale` sets how
  sharply the search's improved policy — the target the net is trained to imitate —
  concentrates on the best moves.
- **Draw blindness.** The value head's failure to recognise drawn endgame positions
  (about 55 % of exact draws recognised, on every 150-iteration net).
- **Dev / test split.** A development set may be read many times while tuning. A test
  set is read once, at the end, so its number is not flattered by the tuning.

## 0. The decision: stop climbing, start reading

**The question.** The ladder is v2b 0 → +77 → +100 → +211 → **+242** (deep10_c1_300).
Neither depth nor duration shows a knee — a point where more stops helping. Each further
rung is a committed GPU-day: 600 iterations ≈ 38 h, 12 blocks ≈ 23 h. Do we keep buying
Elo, or turn the +242 net around and use it?

**What Elo has been costing.** The table gives the marginal wall-clock per Elo point for
each step of the ladder. The hours are the run wall-clocks from `analysis.out`:
abl_cscale1 2.3 h, wide128_c1 4.5, deep8_c1 5.8, deep8_c1_300 14.2, deep10_c1_300 18.9.
The last includes ≈ 3 h of eager-eval tax: the cost of running the in-run evaluation
without CUDA graphs (`--eval_graph 0`), which was a safety choice and is not part of the
recipe. Read each row as: this change gained this many Elo against its parent, for this
many extra hours; the last column is the rate. The Elo figures are direct head-to-head
matches except the width row, which is a ladder difference (wide128_c1's +77 minus
abl_cscale1's +40; the two were never played against each other). The two italic rows
are the un-run continuations, and their numbers are projections.

| step | Elo vs parent | extra hours | Elo / h |
|---|---|---|---|
| c_scale 0.1 → 1.0 | +40 | 0 | ∞ |
| width 64 → 128 (6 blocks, c_scale 1) | +37 (ladder difference) | +2.2 | 17 |
| depth 6 → 8 (150 it) | +23 | +1.3 | 18 |
| duration 150 → 300 (8 blocks) | **+127** | +8.4 | 15 |
| depth 8 → 10 (300 it) | +35 | +1.7 recipe (+4.7 wall) | ≈ 20 |
| *duration 300 → 600 (10 blocks)* | *unknown; +50–90 if the log-compute trend holds* | *≈ +16* | *≈ 3–6* |
| *depth 10 → 12 (300 it)* | *unknown; +20–30 by the last two steps* | *≈ +3.5* | *≈ 6–9* |

The realised steps have not been diminishing in Elo per hour at all. Only the *projected*
ones are, and those projections are guesses. If the goal were the strongest possible net,
the answer would be "run both, depth first because it is cheap". That is not the goal.

**What Elo buys for the project's actual purpose** (README, line 1: "built to *analyse*
the game"):

1. *Game knowledge.* Every belief about the game in RETROSPECTIVE §6 was measured on nets
   250–340 Elo below the current best (dev1, v2a and v2b; PLAN2 §2e). Those beliefs are
   *orderings* (which first move is best) and *signs* (a free move is worth something
   positive). They were already stable across a 170-Elo span, from dev1 to wide128_c1,
   and their magnitudes were declared untrusted at every strength ("report the ordering;
   distrust the magnitudes"). More Elo does not change which findings we can report.
   **Testing the findings at +242 does** — and it costs a day on the 3060, not a GPU-day
   on the 3090.
2. *Understanding the network.* A bigger net is harder to read, not easier. The most
   informative object for "what did it learn, and when" is the **checkpoint trajectory of
   a 300-iteration run** — fifteen checkpoints, `net_0020 … net_0300`, already on disk
   for deep10_c1_300 and deep8_c1_300. The +127 duration result poses a question: what
   changed between iteration 150 and 300? Those checkpoints can answer it. A
   600-iteration run cannot.
3. *Deployment.* The only goal Elo serves directly is an external test (CodinGame, the
   online bot arena whose rules this project uses). That is a batch-1 latency problem —
   one position evaluated at a time, under a per-move time limit — whereas the ladder is
   an equal-*sims* instrument. The one cheap decision-relevant measurement is A8:
   equal-*FLOP* matches, run before this plan was finalised (`runs/plan5_A8.out`,
   10 minutes on the 3090). It says:
   - **deep10@64 beats v2b@427 by +42 [+23, +61]** (56.0 % of pairs). The earlier "small
     net that thinks 4× longer wins" result (v2b@256 over wide128_c1@64, +101) does not
     survive depth and duration. The ladder's winner is now also the winner at equal
     compute.
   - **deep10@64 vs deep8_c1_300@80: −11 [−30, +7]** (48.4 %, inside the ±3 band). The
     last rung's +35 at equal sims is *entirely paid for* by its 1.25× per-simulation
     cost. At a fixed inference budget, going from 8 blocks to 10 bought nothing. A
     12-block run would have to beat that. The same measurement says duration (150 → 300
     iterations, same per-sim cost, +127) is where free deployment strength came from.
   - Phased "0:128,24:384" vs uniform 256 on deep10: **+10 [−7, +26]** (51.4 %), below
     the rule. The phased gain shrinks with strength (+50 on v2b, +26 on deep8_300, +10
     here). It is no longer a claim for this net.

**The risk of *not* pausing** is the draw-blindness lesson. "Draw blindness is
representational" — the claim that the value head *could not* learn to recognise draws,
however long it trained — was stated in PLAN2, restated in PLAN3, accepted by both
outside reviewers, and explained on the public page with a satisfying why-story. It was an
artefact of never training to convergence: the 300-iteration runs lifted draw recognition
from ~55 % to 67–69 % with no change to the architecture (RETROSPECTIVE §3). Every other
§6 belief rests on the same 150-iteration nets. **Re-verification is overdue, and building
higher on unverified beliefs is the wrong order.** We already know what a 600-iteration
run would tell us (the ceiling is higher). We do not know what the net we have has
learned, or how.

**Recommendation.**
- **Pause the ladder.** No 600-iteration run, no 12-block run.
- **Run the analysis programme (§2–§4) now, on `deep10_c1_300/net_0300.pt`**, with
  `deep8_c1_300` as the second strong net wherever a two-net comparison is cheap.
- **One training run is still worth doing, and it is not a rung: a seed replicate of the
  final recipe** (Phase D, §5, item D1). It is the *control* the analysis needs. A
  concept, value weight or opening preference found in one seed is a fact about the game
  only if it appears in the other. It runs unattended on the otherwise idle 3090 while the
  analysis runs on the 3060; nothing in Phase A waits for it. Owner's call — it is
  optional. *(Approved and run: §5 D1, done 2026-09-05.)*
- **Resume the ladder only if** one of three things happens. (i) Phase A finds beliefs
  whose *magnitudes* moved between deep8_c1_300 and deep10_c1_300 by more than their
  CIs — meaning the analysis is strength-limited. (ii) The checkpoint timeline (§3 B1)
  shows concepts still *appearing* at iteration 280–300 rather than sharpening — meaning
  the net is still learning new things. (iii) A deployment target appears that needs Elo
  at a fixed budget. If the ladder does resume, the run is **600 iterations, not 12
  blocks**: A8b says depth no longer pays at equal compute, duration does. Absent those,
  the marginal GPU-day goes to the opening book and the tablebase (§4).

## 1. Review of the work so far

### 1a. What stands
- **The measurement kit.** The paired colour-swapped suite (516 openings, pair bootstrap,
  ±2.8), the exact endgame set, the rollout anchor, seed replicates at 6×64, and the
  pre-registered rule *believe nothing under +3 points, final checkpoints only*. Every
  adopt/null verdict in the project is a sentence because of it. It caught the four-run
  plateau (four 6×64 runs in a row that did not improve), the SWA loss (averaging
  checkpoints made the net worse), and the games-8192 myth (doubling the self-play batch
  was supposed to be free and was not). This is the part that generalises.
- **One change per run.** Twelve runs, each a single intervention against a named parent,
  each judged on the frozen suite. The ladder is a chain of pairwise head-to-heads, not a
  leaderboard.
- **Nulls written down with a measured reason.** Exact labels: the self-play game outcome
  z, which is the value target, was already exact in 98.7 % of the positions the labels
  would have corrected. Hygiene: the exploration floor had already fixed diversity. SWA:
  LR phases don't mix. Games-8192: the run was GPU-bound, so a bigger batch could not be
  free.
- **Engineering that survived contact**: the 9× throughput ladder (a sequence of speed
  fixes that together made self-play 9× faster), two-file checkpoints, retry wrappers,
  config provenance, git. Three driver faults; zero lost runs after the fix.
- **Review adjudicated with data**, not accepted or dismissed (PLAN4 §2). The statistical
  findings were right and cheap to fix. The micro-optimisations were measured and not
  worth it. The orientation-bias worry (that the suite might favour one board
  orientation) was bounded at ≤ 0.6 points in 20 minutes.

### 1b. What is weak, ranked by how much it threatens a claim
1. **Every game belief is from nets 250–340 Elo below the best, and one already fell.**
   The atlas (first-move ranking), decision time (when games become predictable), the
   free-move value, ownership-as-line-counting, puzzle motifs, X share, tiebreak share —
   all PLAN2 §2e, all measured on dev1/v2a/v2b. → Phase A re-runs every one on
   deep10_c1_300, with a written "what moved would look like" before looking (§2).
2. **The yardsticks descend from a −35 Elo net.** `openings_v1`'s "natural" half and
   `endgame_v1` are positions from the v2a corpus (the games v2a played while training),
   and v2a is 35 Elo below v2b; `puzzles_v1` is from the v2b corpus. The suite is still a
   valid fixed ruler for *strength* (a yardstick need not be representative), but
   "natural" is no longer natural: the strong nets draw about a fifth of their games and
   settle a third by the count rule rather than a line (that third includes the drawn
   fifth, where the count is equal). And `endgame_v1` has been read ~50 times in-run —
   every in-run evaluation scores it — so it is a development set. → Build v2 suites from
   a strong-play corpus, split by source game into dev/test *before* solving, and read
   the test half once (§2 A7, A9).
3. **No seed replicate of any wide/deep recipe.** The final claim (+35 Elo, a 55.0 %
   score) is +5.0 points against a ±2.5-point seed band measured at 6×64 — about 2σ, two
   standard deviations: probably real, not certainly. The seed band at 10×128 is
   unmeasured. The +23 (deep8_c1 vs wide128_c1) sits at the edge of the ±3 rule. → §5.
   *Measured 2026-09-05 (§5 D1): the band at 10×128 is ≈ 3 points / ≈ 30 Elo, and the
   second seed scores +9 [−10, +28] over deep8_300 — "probably real" became "inside the
   band". The +127 is unaffected.*
4. **The equal-compute question was open at 10 blocks — now closed (A8, §2).** Per
   simulation, deep10 costs ≈ 6.7× v2b (cost scales as blocks × filters²: 10·128² /
   6·64²). The fair fight, v2b@427 vs deep10@64, went to deep10 by +42 [+23, +61]. So the
   public page's "small net that thinks longer wins" story — measured at width 128,
   6 blocks, 150 iterations — does not survive depth and duration. But deep10@64 vs
   deep8_c1_300@80 is −11 [−30, +7]: the *last* rung is a wash at equal compute. Both
   belong in the explainer and in `KNOWLEDGE.md`.
5. **The fault root cause was never found.** Three nvlddmkm faults, all during eval-path
   graph replays, none in ~60 h of self-play graphs. `--eval_graph 0` (evaluation without
   CUDA graphs) removed the surface at ~3 h per run. This only matters if training
   resumes. Then reopen graph eval with retries — a fault costs ≤ 10 iterations, which
   the retry wrapper replays from the last full checkpoint — rather than pay 6× per eval.
6. **Best-play config was assumed, not verified, on the best net — now measured (A8c).**
   Phased "0:128,24:384" vs uniform 256 on deep10 is +10 [−7, +26], under the rule. The
   RETROSPECTIVE's "assumed to transfer" did not. `web/server.py`'s flat `--sims` is fine
   as it is. The trend (+50 → +26 → +10 with strength) is itself a small finding: the
   stronger the raw policy, the less late search adds.
7. **Elo non-transitivity** is visible (+127 measured directly vs +111 as the difference
   of two ladder positions) and documented. The rule "always quote *vs whom* and *at what
   budget*" should be in every table, including this one.
8. **The knowledge/05 analysis programme stalled at item 3 of 8.** Corpus statistics, the
   opening heatmap/atlas and surprise mining (finding the positions where the net's
   intuition and its search disagree most) were done, in the v2b era. Counterfactual
   ablation was superseded by the freemove regression. Distillation, concept probing,
   look-ahead probing and concept discovery were never started. Two of the project's four
   days went to the ladder; the README's stated purpose got one.
9. **Documentation sprawl**: PLAN, PLAN2, PLAN3, PLAN4, NOTES-v2, two RESULTS, three
   REVIEWs, RETROSPECTIVE, now PLAN5 — twelve files, several of which once said "START
   HERE" to somebody (the README now points only at PLAN5). The product this plan should
   end with is a single `KNOWLEDGE.md` (§4 C4); the process files can move to
   `docs/history/`.
10. **Storage and backup**: `runs/` is 11 GB. The `games/` corpora (≈ 1.5 M games per
    300-iteration run) are the irreplaceable part; git ignores them and nothing else
    holds a copy. 302 GB free on C:. An hour (§6).

### 1c. Methodological notes going forward
- The ±3 rule worked. Keep it, and add its sibling for analysis claims: **each belief
  gets a pre-written "moved" criterion** — a statement of what result would count as a
  change — before the new net is run against it. The table in §2 is that list.
- **Capacity claims need a convergence check.** The draw-blindness error was not a
  statistics error — the CIs were fine — it was an explanation that fit. Rule: no claim
  of the form "the network can't represent X" unless the relevant metric was flat over
  the run's final LR phase; otherwise say "not yet learned".
- **Probe accuracy ≠ causal use** (knowledge/05: Pálsson 2024, Othello-GPT). That a
  concept can be read off the net's activations does not show the net uses it. Every
  probing result in Phase B pairs with a behavioural or ablation test, and reports a
  randomly-initialised-net control: the same probe trained on an untrained net, which
  shows what is decodable from the board encoding alone.
- **Two seeds or it's a seed.** For findings about the network's internals, "replicated
  across seeds" is the bar — which is what §5's run is for.

## 2. Phase A — re-verify every belief at +242 (3060, ≈ 1 day, existing tools, unattended)

Net under test: `runs/deep10_c1_300/net_0300.pt`; second column `deep8_c1_300/net_0300.pt`
where cheap. For each row, write the "moved" criterion first, then run.

How to read the table: each row is one belief about the game from the earlier nets, the
tool that measures it, the nets it was measured on, and the two pre-written verdicts —
what result would count as the belief *holding*, and what would count as it having
*moved*. The level in brackets after each belief is from RETROSPECTIVE §6: *behavioural*
is what the agent does; *predictive* is what its value head forecasts; *search-relative*
means the number depends on the search budget it was measured with; *exact* means checked
against the solver.

| # | belief (level) | tool | measured on | "held" means | "moved" means |
|---|---|---|---|---|---|
| A1 | [40] best first move; [13] worst; ordering universal (search-relative) | `tools/atlas.py` deep10 + deep8_300 × 1k/4k/16k sims | dev1/v2a/v2b | [40] rank 1 in all columns; Kendall τ ≥ 0.85 vs v2b@16k | any column with [40] ≠ 1, or τ < 0.7 |
| A2 | root Q-gap between top replies ≤ 0.02 ("openings are flat") | same, `runs/atlas_pv.out` style | v2b | ≤ 0.03 for ≥ 12/15 orbits | gaps ≥ 0.05 in the majority — a stronger net *found* opening edges |
| A3 | games decided late: best-child-Q settled from ply 38 (median), nothing at 30 (predictive) | `tools/decision.py`, deep10 net on (a) the same 4000 held-out v2a games and (b) 4000 of deep8_c1_300's iteration-280+ games | v2b on v2a games | median settled ply within 36–42 on (a) | median < 34 on (a) (stronger net predicts earlier) — or > 42 on (b) (stronger play defends longer) — both are findings |
| A4 | free move +0.16 ± 0.03 (search-relative) | `tools/freemove.py`, 256-sim deep10 values, natural positions from deep8_c1_300's late games | v2b | CI overlaps [0.10, 0.22] | outside; also re-check the raw-head coefficient (was +0.26 — the gap is the "search corrects intuition" term) |
| A5 | ownership ≈ 0 with threats controlled; ±0.17 per macro line | same regression | v2b | line coefficient CI overlaps ±0.17; ownership within ±0.05 | ownership coefficients leave zero |
| A6 | X share 57–60 %; draws rise with strength; count decides ~30 % of strong games | `tools/corpus_stats.py` on deep10 iters 280–299 vs v2a's last 20; plus the `end reasons` lines already in every paired match | v2a/v2b | — descriptive; report the new numbers | — |
| A7 | raw-policy endgame failures are count-rule and free-move motifs, not local tactics | `tools/puzzles.py --out suites/puzzles_v2_dev.npz`, positions from deep8_c1_300's late games (not deep10's own training data), ≤ 14 empties | v2b (3.5 % puzzles, 11 hard) | motif ordering same | puzzle rate ≪ 1 % (the +242 net has nothing left to teach here) or motifs reshuffled |
| A8 | equal-compute: search beats width | `tools/openings.py match`: deep10@64 vs v2b@427; deep10@64 vs deep8_300@80; also phased "0:128,24:384" vs uniform 256 on deep10 | wide128_c1 vs v2b@256 (−101) | v2b@427 still wins | deep10@64 wins — depth+duration bought something 6.7× search cannot. **Run 2026-09-02: MOVED** (see results table) |
| A9 | endgame: raw WDL 84.6 / draws 68.7 / search 99.8 % optimal | `tools/endgame.py` build `suites/endgame_v2_{dev,test}.npz` from deep8_c1_300's iteration-280+ games (strong-play distribution; not deep10's training data — deep8_300's own score on it carries that caveat), split by source game before solving; eval both nets on v1 and v2_dev; v2_test once, at the end of PLAN5 | endgame_v1 (dev-contaminated) | v2_test within ±2 of v1 | v1 ≫ v2_test: the v1 numbers were overfit by selection |

Notes on the table's terms:
- *[40]* and *[13]* are move indices (`m = 9*board + cell`, README): 40 is the centre
  cell of the centre board, 13 is the centre cell of the top-centre board.
- *Kendall τ* is a rank-correlation coefficient: 1 means two rankings agree exactly,
  0 means no relation. Here it compares the new net's first-move ranking with v2b's at
  16 k sims.
- *Root Q-gap*: Q is the search's estimated value of a move at the root of the tree. The
  gap is the difference between the best and second-best reply. A small gap means the
  choice hardly matters.
- *Best-child-Q settled*: the ply from which the search's favourite move's value stops
  changing sign for the rest of the game — the point at which the game is decided.
- *Coefficient*: the values in A4 and A5 come from a regression, a fit that assigns each
  feature (a free move, each macro line, board ownership) a weight in units of expected
  score. "Threats controlled" means the fit includes the line-threat features, so
  ownership is measured over and above them. The *raw-head coefficient* is the same
  weight when the value head is asked directly, without search.
- *Motifs* (A7): the recurring reasons the raw policy fails a puzzle, classified by hand.
- *Iteration-280+ games*: games played during the last 20 iterations of a run, i.e. by
  its strongest nets.

Output: `runs/plan5_A.out` per tool, and a results table appended to this file with each
row marked **held / moved / reversed**. Rows that *moved* are the interesting ones and
feed §0's resume criterion (i).

**Phase A results so far** (paired suite, 516 openings / 1032 games, ±2.8 points). The
score is A's share of points; "draws" is the share of games drawn.

| row | match | score | Elo [95 % CI] | draws | verdict |
|---|---|---|---|---|---|
| A8a | deep10@64 vs v2b@427 (FLOP-matched, 6.7×) | 56.0 % [53.2, 58.6] | **+42 [+23, +61]** | 15.2 % | **moved** — at equal compute the deep, long-trained net beats the small net for the first time (was −101 at 6×128 vs 6×64@256) |
| A8b | deep10@64 vs deep8_c1_300@80 (FLOP-matched, 1.25×) | 48.4 % [45.7, 51.1] | −11 [−30, +7] | 20.3 % | **null** — blocks 8 → 10 bought nothing at equal compute; the +35 at equal sims is the cost difference |
| A8c | deep10 phased "0:128,24:384" vs uniform 256 | 51.4 % [48.9, 53.7] | +10 [−7, +26] | 24.7 % | **not confirmed** on this net (was +50 v2b, +26 deep8_300); uniform 256 is the play config until something beats it by 3 points |

Files: `runs/deep10_c1_300/paired_vs_v2b_flopmatched.json`, `paired_vs_deep8c1_300_flopmatched.json`,
`paired_phased_vs_256.json`; log `runs/plan5_A8.out`. Note the draw rate rising down the
table — deep10 against itself draws a quarter of the suite.

**Phase A results, rows A1–A7 and A9 (run 2026-09-03, `runs/plan5_A_3060.sh` +
`runs/plan5_A_3090.sh`, log `runs/plan5_A.out`, one `runs/plan5_A<row>_*.out` per tool).**
Net under test `deep10_c1_300/net_0300.pt`; second column `deep8_c1_300/net_0300.pt`. Every
row was judged against the pre-written criterion in the table above.

| row | measured (deep10 unless said) | earlier (v2b) | verdict |
|---|---|---|---|
| A1 | [40] rank 1 and [13] rank 15 in all 9 columns (v2b / deep8_300 / deep10 × 1k / 4k / 16k, symmetry-averaged); Kendall τ deep10@16k vs v2b@16k **0.96**, deep8_300@16k vs v2b@16k 0.92; top four identical in order: [40] > [36] > [0] > [37]. Values for X rose (+0.354 → +0.447 after [40]) — magnitudes, as always, untrusted | same ordering | **held** |
| A2 | root Q-gap at 16k ≤ 0.03 in **13 / 15** orbits. The two exceptions are the orbits whose best reply is to take centre-of-centre: after [13] the gap grew 0.079 → **0.116**, after [4] 0.017 → **0.057** | 13 / 15 ≤ 0.03; max 0.079 | **held** — with a footnote: the only opening edges a stronger net finds are "answer by taking [40]" |
| A3 | best-child-Q settling median **ply 36** (quartiles 30–41) on the same 4000 v2a games; raw-value median 41; on deep8_300's late games (mean length 51.9): Q median 36 (28–41), raw 42, search-root 47. deep8_300 on the v2a games: Q 36, raw 41 — identical to deep10 | Q 38 (32–42), raw 43 | **held**, at the edge of the band; the 2-ply shift is a strength effect that has saturated (deep8_300 = deep10). Caveat: the 3-way threshold (±0.33) now sits below deep10's opening value for X, so 10–17 % of X-win games count as "settled at ply 0" |
| A4 | free move **+0.196 ± 0.028** (search, 256 sims, 30 000 positions from deep8_300's late games); raw head +0.290 ± 0.030; raw − search gap 0.094; stratified check +0.130, up to +0.25 late when level or ahead. Second column, deep8_300 on deep10's late games: **+0.192 ± 0.027**, raw +0.290 | +0.163 ± 0.027; raw +0.256; gap 0.094 | **held** (CI overlaps [0.10, 0.22]); magnitude up a third and identical on both strong nets, the search-corrects-intuition gap unchanged |
| A5 | macro-line threats +0.154 / −0.140 per line (CIs overlap ±0.17; deep8_300 +0.145 / −0.139). With threats controlled, owning a board is no longer zero: deep10 centre_self **+0.070 ± 0.040**, corners_self **+0.065 ± 0.030**, edges_self **+0.056 ± 0.027**, net worth centre +0.092 / corner +0.078 / edge +0.053; deep8_300 +0.051 / +0.030 / +0.037 (all three significant), net worth +0.038 / +0.035 / +0.056. Opponent-owned boards ≈ 0 on both | ±0.17 per line; ownership +0.008 / +0.011 / +0.033 | lines **held**; ownership **moved** — a small positive residual per own board beyond the lines it sits on (+0.03 … +0.07, a fifth to a third of a threat line) on both strong nets. The centre > corner > edge order appears on deep10 only (deep8_300 has edge highest), so the *class* ordering is not a finding. The self / opponent asymmetry is unexplained (B3 revisits it with the full concept set) |
| A6 | deep10 iterations 280–299 self-play: X 63.0 / O 23.9 / draw 13.1 %; ends by line 72.8 %, count 14.1 %, equal 13.1 % (count rule + equal = 27 %); mean length 51.9; 4.42 free moves per game; [40] opened 83 % of games (the rest is the 15 % exploration floor). deep8_300: 61.1 / 25.8 / 13.0, 27 %, 51.9. v2a last 20: 60.1 / 28.6 / 11.4, 26 %, 49.4. Paired matches between the strong nets (A8): draws 15–25 %, count 11–13 % | — | descriptive: X share up, draws up, games 2.5 plies longer, count-rule share flat at ~27 % of self-play |
| A7 | 6000 strong-play positions ≤ 14 empties (deep8_300's late games): **126 puzzles (2.1 %), 7 hard at 64 sims (0.12 %)**; motifs tiebreak_conversion 71 > gives_free_move 61 > draw_hold 51 > denies_free_move 37 > local_win 20 > closes_board 4 > macro_win 0; regret 1 in 68 % | 3.5 %, 13 hard (0.22 %); same order (110 > 92 > 71 > 68 > 55 > 4 > 2) | **held** — the count rule and free-move tempo remain what the raw policy misses; local tactics fell most (26 → 16 % of puzzles). `suites/puzzles_v2_dev.npz` (+ `.json`, 5 hard puzzles) |
| A9 | `endgame_v2_{dev,test}` built from deep8_300's iterations 280–299, split by source game before solving (3000 positions each, balanced strata). deep10 on v2_dev: raw WDL **84.7 [83.4, 85.9]**, draws 72.2, regret 0.048, optimal 95.7; search-256 optimal 99.7. deep8_300 on v2_dev: 84.7 [83.4, 86.0] (symmetry-averaged; plain 83.5), draws 70.4, regret 0.050. Both re-scored on v1 in the same session: 84.6 / 0.037 and 84.0 / 0.045, reproducing `analysis.out` | v1: 84.6 / 68.7 / 0.037 | **held** — the ~50 in-run reads did not flatter v1 (WDL within 0.1); the strong-play set is harder for the raw *policy* (regret 0.037 → 0.048) and easier for draw recognition. **v2_test read once, 2026-09-05** (`runs/plan5_A9_test_*.out`): deep10 raw WDL **85.0 [83.7, 86.3]**, draws 72.3, regret 0.047, optimal 95.8, search-256 optimal 99.7; deep8_300 84.8 [83.5, 86.0], draws 71.1, regret 0.050; the seed replicate 85.1 [83.8, 86.3], draws 69.6, regret 0.044, optimal 96.1. Test agrees with dev within 0.3 (deep10) / 1.3 (deep8_300, plain head) points, and the three strong nets are within 0.3 points of each other on the sealed half. It is a development set from here on. |

What moved, in one paragraph: nothing that was an *ordering* or a *sign*. [40] is still the
best first move and [13] the worst on every net and budget; games are still decided late; a
free move is still worth about +0.2; the value head's endgame numbers were not a selection
artefact; the raw policy's failures are still the count rule and tempo. Two magnitudes moved,
both in the direction of a sharper net: the free-move value (+0.16 → +0.20, CIs touching)
and, the one genuine revision, **board ownership carries a small value of its own once
macro-line threats are controlled** (+0.03 … +0.07 per own board on both strong nets,
previously indistinguishable from zero; which board class is worth most is not resolved).
Two orbits also acquired a visible opening edge ([13] and [4],
both "reply by taking the centre of the centre board"). For §0's resume criterion (i): no
belief's magnitude moved between deep8_c1_300 and deep10_c1_300 by more than its CI — A3, A4,
A9 and the atlas all give the two nets the same numbers — so the analysis is not
strength-limited and the ladder stays paused on this evidence.

## 3. Phase B — the network on its own terms (new tooling; both GPUs free)

Three questions: *what* does the net compute, *how*, and *when* did it learn it. The
300-iteration checkpoint sequence makes "when" nearly free.

- **B1. Checkpoint timeline** (`tools/timeline.py`, new, ≈ 100 lines; 1–2 h GPU). For
  each of the 15 deep10_c1_300 checkpoints (and deep8_c1_300's), record: the in-run
  paired score vs v2b (already in `log.jsonl`, ±6 — fine for a curve); endgame WDL, draw
  recognition and raw regret (`endgame.py eval`, ~1 min each); first-move policy entropy
  and top-1 share (how spread out the net's first-move probabilities are, and how much
  of that probability its favourite move gets — McGrath's opening-narrowing statistic,
  from the AlphaZero chess interpretability paper); policy entropy by ply bucket; and D4
  consistency (B5). One figure: every curve on the iteration axis with the LR drops
  marked. **This is the direct answer to "where did +127 come from."** Draw recognition
  55 → 69 is the first curve to draw. If it steps at the LR drops rather than climbing
  between them, the story is "annealing", not "more data".
- **B2. Concept probes** (`uttt/concepts.py` label generator + `tools/probe.py`, new,
  ≈ 300 lines; a day). Record the residual stream after the stem (the first layer) and
  after each block: a 128 × 9 × 9 activation grid per position. Labels are computed from
  the board state, so no oracle is needed: per-board status (X / O / drawn-full / open),
  open-board count, dead boards (winnable by neither), macro threats for / against
  (count), free move available now, target board, count margin, empties, side to move.
  Plus two *lookahead* labels — the exact value for ≤ 14-empty positions (from the
  endgame set) and the 2-ply-ahead best move (solver where exact, else 256-sim search) —
  in the spirit of Jenner et al. (who tested whether a chess net represents future
  forced sequences). Train linear probes and one-hidden-layer probes on 50 k positions
  from held-out games, test on 10 k. **Randomly-initialised deep10 is the control**
  (report accuracy above the control, not raw accuracy). Produce a layer × checkpoint
  grid per concept: one accuracy per (layer, checkpoint) cell. Two specific comparisons:
  (i) how much better a trunk probe for board ownership is than the net's own ownership
  head (is the auxiliary head reading what the trunk already knows?); (ii) which layer
  the lookahead labels become decodable in, if any.
- **B3. Value decomposition** (generalise `freemove.py`'s regression; half a day).
  Regress the raw WDL expectation, and separately the 256-sim search value, on the B2
  concept set, per checkpoint. Reports: R² (the share of the value the concepts explain),
  the coefficient path over training (when does the head start weighing macro lines?
  free moves? the count?), and the raw-vs-search coefficient gap per concept — the part
  of each concept the net still under-weights. Ties directly to RETROSPECTIVE §6's
  "hierarchy is line-counting in disguise".
- **B4. Counterfactuals and surprise** (`tools/probe_value.py`, `tools/surprise.py`,
  exist; hours). Flip centre-board ownership, grant/deny a free move, force-close a board
  on natural deep10 positions; compare the raw-head delta with the 256-sim delta. Then
  take `surprise.py`'s top 30 raw-vs-search disagreements, inspect them by hand in the
  web UI, and write them up as annotated positions — the *Game Changer* format (the book
  of annotated AlphaZero chess games).
- **B5. Symmetry** (`uttt/symmetry.py`, exists; hours). Per position, the policy's
  Jensen–Shannon spread (a measure of how different probability distributions are) and
  the value's spread across the 8 orientations, by checkpoint and by ply. This measures
  how much of D4 the net learned versus what symmetry-averaging still adds (+1–2 WDL
  points at v2b — is it less at deep10?).
- **B6. Distillation to a legible surrogate** (`tools/distill.py`, new; a day). Fit a
  linear model and a depth-limited decision tree on the B2 hand features to imitate
  deep10's 256-sim policy and value (VIPER-lite, one DAgger round: let the imitator play,
  then ask the net what it would have done in the positions the imitator reached, and
  refit). Then **play the surrogate on the paired suite at 64 sims** against v2b@64 and
  deep10@64. The Elo gap is the share of the net's play that the named concepts do *not*
  capture — a number a reader can hold.

Order: B1 → B2 → B3 → B4/B5 → B6. All of it pairs a decodability result with a
behavioural one (§1c); nothing in Phase B is reported from probe accuracy alone.

**B1 results (2026-09-03; `tools/timeline.py`, outputs `runs/<run>/timeline.{json,png}`,
logs `runs/plan5_B1_timeline_*.out`).** deep10_c1_300 has 15 checkpoints (every 20
iterations), deep8_c1_300 has 30 (every 10); the second resolves the timing. Held-out
positions for the policy statistics: 20 000 from the other run's iteration-280+ games; D4
statistics on 4096 of them; endgame numbers on `endgame_v1` (raw head only).

- **Where +127 came from.** Two things, and the timeline separates them. (i) *More
  iterations at the constant LR*: deep8_300's in-run score vs v2b climbs 62.5 (it 150) →
  69.2 (it 200), deep10's 67.7 → 70.5 — about +5 points that a 150-iteration run never
  gets. (ii) *The first LR drop*: a clean step at the first post-drop checkpoint — deep8_300
  69.2 → 77.0 (net_0200 → net_0210), deep10 70.5 → 78.9 (net_0200 → net_0220) — about +8
  points, and the same step shows in every other curve at the same checkpoint: raw WDL
  79.7 → 82.7, draw recognition 58.8 → 65.7, regret 0.057 → 0.051, opening-ply policy
  entropy 1.71 → 1.35 bits, D4 policy divergence 0.051 → 0.030 bits (deep8_300 numbers;
  deep10's are 81.7 → 83.1, 62.5 → 65.5, 1.80 → 1.35, 0.052 → 0.030). After that step
  every curve is flat to iteration 300 on both runs. (iii) *The second LR drop (280) does
  nothing visible*: deep8_300 77.8 → 75.5 → 77.3, WDL 83.6 → 83.7 → 84.0; deep10 76.7 →
  80.6 with WDL 84.2 → 84.6 — inside the ±6 in-run noise. RETROSPECTIVE §3's "both LR
  drops delivered visible steps" is therefore half right: the first drop is the event, the
  second is not resolved by these curves (the paired-suite result for the final checkpoint
  still stands; it just cannot be attributed to the 280 drop).
- **Draw recognition is an annealing product, not a slow climb — and it is a noisy metric
  at constant LR.** On deep8_300 it wobbles between 38 % and 63 % from iteration 100 to
  200 (adjacent checkpoints differ by up to 20 points on the 1000-position draw stratum),
  then steps to 66–68 % at the drop and stays there. deep10 shows the same: 53–57 % flat
  from 100 to 180, 62.5 at 200 (still LR 0.02 — inside the wobble), 65.5 → 68.3 after the
  drop, flat to 300. So "≈ 55 % on every 150-iteration net" was the un-annealed plateau
  read through noise, which is why it looked like a wall. This is the §5 D3 trigger: the
  step is at the drop, so the cheapest training experiment is an *earlier* first drop (or a
  longer low-LR phase), not more iterations at 0.02.
- **D4 consistency is also annealing.** Policy JS across the 8 orientations sits at
  0.05 bits for 200 iterations on both runs and halves at the drop (0.030), ending at 0.027;
  the value's orientation spread goes 0.073 → 0.052. By ply it is smallest in the opening
  (0.010 bits at plies 0–7) and largest in the middlegame (0.034 at plies 20–31).
  Symmetry-averaging at play time therefore has less left to add on the annealed nets
  (B5 measures how much).
- **Opening narrowing is immediate.** Both nets put ≥ 0.95 of the first-move policy on [40]
  from iteration 20–30 on (deep8_300: 0.09 at it 10, 0.79 at 20, 0.98 at 30); it never
  broadens again except a dip to 0.86 at deep10's iterations 140–160. The opening is
  learned in the first 10 % of training; what the rest of the run buys is the middlegame
  (regret) and the endgame (WDL, draws).
- **Policy entropy on held-out positions** drops in the opening (plies 0–7: 2.6 → 1.2 bits
  over the run, half of it at the LR drop) and hardly at all late (plies 44+: 1.7 → 1.4
  bits, flat from iteration 50) — the late-game entropy is the game's, not the net's.
- **For §0's resume criterion (ii):** nothing appears late. Every curve is flat from
  iteration 220 (deep8_300) / 240 (deep10) to 300; the last 60–80 iterations sharpen
  nothing measurable here. Criterion (ii) does not fire. B2's layer × checkpoint grid is
  the finer test.
- **Replication on the seed replicate `deep10_c1_300_s1` (2026-09-05;
  `runs/deep10_c1_300_s1/timeline.{json,png}`, `runs/plan5_B1_timeline_s1.out`, 30
  checkpoints).** Every feature above is on the third run. The first LR drop is the event:
  in-run score vs v2b 71.2 (net_0200) → 75.5 (0210) → 78.1 (0220), raw WDL 77.6 → 81.9 →
  83.0, draw recognition 52.5 → 62.6 → 65.9, regret 0.064 → 0.049 → 0.047, opening-ply
  policy entropy 1.84 → 1.38 bits, D4 policy divergence 0.055 → 0.032 bits (deep10: 70.5 →
  78.9, 81.7 → 83.1, 62.5 → 65.5, 1.80 → 1.35, 0.052 → 0.030). Every curve is flat from 220
  to 300 (v2b 75.3–80.1, WDL 82.0–83.9, draws 62.6–68.3, D4 0.028–0.034) and the second
  drop at 280 does nothing (79.5 → 78.7 → 77.5; WDL 83.3 → 83.4 → 83.9). Draw recognition at
  the constant LR wobbles even more than on the earlier runs — 37–62 % between adjacent
  checkpoints from iteration 100 to 200 — then settles at 66–68 % after the drop. Opening
  narrowing: [21] at net_0010, [40] at 0.68 from net_0020 and ≥ 0.88 from net_0030 on, with
  the same mid-run dips (0.88–0.90 at 130 and 160; deep10 0.86 at 140–160). Constant-LR
  gain, iterations 150 → 200: 61.1 → 71.2 (deep10 67.7 → 70.5; the replicate was in its
  mid-run trough at 150). Nothing appears late. §0 criterion (ii) does not fire on the
  third run either.

**B4 results, first half (2026-09-03; `runs/plan5_B4_probe_value_deep10.out`,
`runs/plan5_B4_surprise_deep10.out`; positions from deep8_c1_300's replay buffer, held-out
for deep10; the v2a-era comparison is `runs/v2a/probe_surprise_rerun.out`).**

- *Counterfactual tensor edits, raw symmetry-averaged value head, 48 576 positions.* Grant a
  free move instead of confinement: **+0.413** mean (median +0.324; v2a-era +0.269) —
  twice the regression estimate of +0.20 on natural positions (A4), the same overstatement
  the earlier nets showed, so "the tensor edit overstates the free move by ~2×" is itself a
  stable finding. Flip the owner of a won board: centre **+1.05**, corner **+0.94**, edge
  **+0.83** (v2a: +1.03 / +0.91 / +0.79); centre − corner +0.111, corner − edge +0.114
  (v2a: +0.116 / +0.116). The raw head's ownership hierarchy is unchanged to the second
  decimal across 340 Elo — and A5 says the *search* value with threats controlled sees only
  a residual +0.03 … +0.07 per board, so the hierarchy is a property of the intuition
  (the raw head), most of which the lines explain. Removing an open board for both sides:
  +0.017 (v2a +0.06) — an open board is worth nothing to the mover once it is nobody's.
- *Surprise (raw vs 256-sim search), 7188 positions.* Search move ≠ raw argmax in
  **33.6 %** of positions (v2a on its own buffer: 29.8 %), mean |search − raw value|
  0.185 (0.172); the disagreement peaks at plies 30–39 (43.8 %; v2a 37.5 %) and the raw
  policy's probability on the search's move is lowest there (0.44). The two position sets
  differ (deep8_300's late games are more contested), so the rise is not a strength
  comparison; the shape — intuition and search part company in the middlegame, agree in
  the opening and the late endgame — is the same on both. The top-30 disagreements are
  in the `.out` as boards; the largest value surprises are mostly late tactics the raw
  head misreads by a full point (e.g. ply 50, raw −0.62, search +0.97: a forced local
  win the policy ranks second). The hand-annotated *Game Changer*-style write-up is still
  to do (C3).

**B5 results (2026-09-03).** *Decodability half* — from B1: the policy's D4 divergence is
0.05 bits for 200 iterations and halves at the first LR drop to 0.027 at the end; by ply
it is 0.010 in the opening and 0.034 in the middlegame. *Behavioural half*
(`runs/plan5_B5_sym_vs_plain.out`, `runs/deep10_c1_300/paired_sym_vs_plain_64.json`):
deep10 with symmetry-averaged evaluation @64 vs plain deep10 @64 on the paired suite scores
**55.0 % [52.4, 57.7], +35 Elo [+17, +54]** — above the ±3 rule, at 8× the inference cost
per simulation. On the endgame set the same averaging adds +0.4 WDL points (84.6 → 85.0 on
v1, 84.7 → 85.1 on v2_dev; deep8_300 +1.2). So the 0.027 bits of residual orientation
inconsistency are not cosmetic: the net has *not* fully learned D4, and averaging is worth
a rung of the ladder at equal sims. **At equal compute it is a bad trade**
(`runs/plan5_B5b_sym_equal_compute.out`, `paired_sym64_vs_plain512.json`): symmetry-averaged
deep10 @64 against plain deep10 @512 — the same inference per move — scores **23.9 %
[21.8, 26.2], −201 Elo [−222, −180]**. Eight times the search buys far more than eight
evaluations per node spent on orientation-averaging. So the +35 is real and only matters
when inference is not the bottleneck (analysis, the atlas, the book — where it is used).
*Interpretation:* the D4 gap is the one place where the training data's symmetry (the
buffer is not symmetrised; the null "symmetric dedup" only changed duplicate weighting)
leaves a measurable strength on the table — small, and cheaper to close by search than by
averaging.

**B2 results, deep10 linear probes (2026-09-03; `tools/probe.py`, `tools/probe_report.py`;
`runs/probe_data_deep8late.npz` = 60 000 positions from deep8_300's iteration-280+ games,
50 000 / 10 000 by source game; `runs/deep10_c1_300/probes.{json,png}`,
`runs/plan5_B2_fit_deep10.out`).** Linear read-outs at the input planes, the stem and each
of the 10 blocks, for all 15 checkpoints and a randomly initialised 10×128 net (the
control). Every number below is *gain over the control at the same layer* (test accuracy
or R²), as §1c requires.

- **What the encoding already exposes (gain ≈ 0, so the probe cannot speak):** the count
  margin (R² 1.000 on the input planes — it is linear in the won-board planes), open
  boards, empties, per-board status, the target board (99.5 % on the control) and the
  free-move flag (98.4 % on the control, 99.8 % trained). These concepts are *inputs*, not
  things the net learned; any claim that "the net represents the free move" is empty.
- **What is computed, where, and when** (gain at the best layer; "learned by" = the
  checkpoint reaching 90 % of the final gain there):

  | concept | control → final | gain | best layer | learned by |
  |---|---|---|---|---|
  | dead boards (count; R²) | 0.01 → 0.49 | **+0.48** | block05 | 180 |
  | exact value, ≤ 14 empties (3-class) | 64.5 → 89.4 % | **+0.25** | block10 | 180 |
  | search's best move now (81-class) | 55.6 → 71.2 % | +0.16 | block10 | 220 |
  | macro threats for / against (count; R²) | 0.68 → 0.84 / 0.71 → 0.86 | +0.15 | block07 / 08 | 100 / 140 |
  | local win available now | 86.2 → 99.4 % | +0.13 | block05 | 60 |
  | any macro threat for | 91.2 → 96.8 % | +0.06 | block10 | 80 |
  | opponent local threat | 92.8 → 98.4 % | +0.06 | block08 | 80 |
  | game result z (3-class) | 59.9 → 64.9 % | +0.05 | block10 | 220 |
  | best move two plies on (81-class) | 33.8 → 38.3 % | +0.05 | block08 | 240 |
  | macro win available now | 92.5 → 95.9 % | +0.03 | block10 | 100 |
  | final owner of the centre board (3-class) | 60.8 → 62.0 % | +0.01 | block06 | — |

  Tactical, local concepts (a local win, an opponent's local threat) are linearly readable
  by block05 and learned by iteration 60–80; the macro-line threats sharpen through the
  middle of the trunk (peak at block07–08, then *fade* toward block10 — the trunk has
  used them by the time the heads read it) and are learned by 100–140; the value-like
  concepts (dead boards, the exact value, z) live in the deepest blocks and are the last
  to settle (180–220), stepping at the LR drop as B1 showed (exact-value gain at block10:
  0.229 at it 200 → 0.246 at 220 → 0.249 at 300). Nothing appears after 240; the policy
  read-out creeps (+0.009 from 220 to 300). **§0 criterion (ii) does not fire.**
- **Look-ahead.** The search's current best move is decodable at 71 % from block10 (the
  policy head's job, unsurprisingly); the move two plies on only at 38 % vs 34 % on the
  control — the trunk carries little of the line it is about to follow, in the linear
  sense. (Jenner et al.'s chess result was for a much deeper net; here the "future" is
  mostly the *target-board* constraint, which is in the input.)
- **Comparison (i), the ownership head.** The net's own ownership head predicts the final
  owner of each board at **60.3 %** on the test positions (majority class 41.2 %). The best
  linear trunk probe gets 60.1 % (mean over boards) — the head reads what the trunk has.
  But the same probe on the *random* net's trunk already gets **59.0 %**: final ownership
  is about 59 % predictable from the board encoding alone, and 300 iterations add one
  point. The auxiliary ownership head is therefore learning almost nothing beyond the
  current board, which is why turning the auxiliary heads off was a null (RETROSPECTIVE
  §3) — the target is nearly a function of the input.
- **Draw blindness, seen from inside.** The exact value becomes linearly readable from
  block10 at 89 % (control 64 %). Its "learned by 180" and the step at the drop match B1's
  draw-recognition curve; the representation *and* the head arrive together, which is
  what "optimisation, not capacity" predicts.

**Replication on deep8_c1_300** (`runs/deep8_c1_300/probes.{json,png}`; positions from
deep10's late games, look-ahead labels from deep8_300's own 256-sim search; 16 checkpoints
+ control × 10 layers). The grid is the same to within a few points: dead boards +0.48 at
block 5 (deep10 +0.48, block 5), the exact value +0.25 at the last block (+0.25, last
block), the search's best move +0.13 at the last block (+0.16), macro threats +0.14 / +0.13
at blocks 6 / 5 (+0.15 / +0.15 at 7 / 8), local win +0.12 at block 5 (+0.13, block 5),
opponent local threat +0.06 (+0.06), z +0.04 (+0.05), the move two plies on +0.05 (+0.05),
final ownership of the centre +0.02 (+0.01). The "learned by" checkpoints match as well:
local tactics 60–80 (deep10 60–80), macro threats 80–120 (100–140), dead boards 200 (180),
the exact value 180 (180), z 220 (220), the best move 200 (220). Ownership head 59.9 %,
best trunk probe 61.8 %, random-trunk probe 60.9 %, majority 41.2 % (deep10: 60.3 / 60.1 /
59.0 / 41.2). Every §8 claim in KNOWLEDGE.md about what the trunk computes, where and
when, therefore holds on both strong nets.

**Replication on the seed replicate `deep10_c1_300_s1`** (2026-09-05;
`runs/deep10_c1_300_s1/probes.{json,png}`, `runs/plan5_B2_fit_s1.out`,
`runs/plan5_B2_report_s1.out`; the same 60 000 deep8_300-late positions, 30 checkpoints +
control × 12 layers). The grid is the reference's to within a few points and one or two
blocks: dead boards **+0.47** at block 6 (deep10 +0.48, block 5), the exact value **+0.25**
at block 10 (+0.25, block 10), the search's best move +0.14 at block 10 (+0.16), macro
threats +0.15 / +0.15 at block 6 (+0.15 / +0.15 at 7 / 8) with the same fade toward the
heads (+0.15 at block 6 → +0.13 / +0.11 at block 10), local win +0.13 at block 5 (+0.13,
block 5), opponent local threat +0.06 at block 7 (+0.06, block 8), any macro threat +0.06,
z +0.05 at block 10 (+0.05), the move two plies on +0.04 (+0.05), macro win now +0.04
(+0.03), final ownership of the centre +0.01 (+0.01); the input-exposed concepts (count
margin, open boards, empties, board status, target board, free move) have gain ≈ 0 on all
three runs. "Learned by" (the replicate has a checkpoint every 10 iterations, the reference
every 20): local tactics 40–80 (deep10 60–80), macro threats 110–140 (100–140), the exact
value 180 (180), dead boards 200 (180), z 180 (220), the best move 180 (220), the move two
plies on 180 (240). Nothing appears after 200. So the layer × checkpoint picture — tactics
shallow and early, lines mid-trunk and fading, value deep and last — is a fact about
training this net on this game, not about one seed: KNOWLEDGE 37–39 are stated for all
three strong nets.

**Non-linear probes** (`runs/deep10_c1_300/probes_mlp.json`, one hidden layer of 256, six
deep10 checkpoints + control, `runs/plan5_B2_fit_deep10_mlp.out`). The point of the
non-linear control is to separate *concepts the trunk computes* from *concepts a probe can
compute from the input planes if allowed one layer of its own*. With the MLP probe the
random net already yields macro threats at R² 0.81–0.83 (linear: 0.68–0.70) and
macro-win-now at 98 %, so the trained net's gain over the control shrinks from +0.15 to
+0.06 (threats) and from +0.03 to +0.02 (macro win): these are simple functions of the
board that the trunk *linearises* rather than discovers. The gains that survive the
non-linear control are the real computations: dead boards R² +0.58 (control 0.05 → 0.56),
the exact value +0.21 (0.68 → 0.89), the search's best move +0.17, an available local win
+0.13, the move two plies on +0.06, z +0.05. (The 81-class MLP heads fit slightly worse
than the linear ones in 10 epochs — 66 vs 71 % for the best move — which is a probe
budget effect, not a finding.) KNOWLEDGE claims 37–38 are stated with this split.

**B3 results, deep10 (2026-09-03; `tools/value_decomp.py`; 20 000 of the B2 positions,
256-sim search; `runs/deep10_c1_300/value_decomp.{json,png}`,
`runs/plan5_B3_value_deep10.out`).** The raw WDL expectation and the search value, each
regressed on the concept set (free move, ply, count margin, open boards, empties, side,
macro threats for / against, dead boards, local win now, opponent local threat, macro win
now, full boards), per checkpoint, cluster-robust by game. R² at net_0300: raw 0.59,
search 0.56 — the same share as freemove.py's smaller model, so the added concepts
re-attribute rather than explain more.

- **The free move decomposes.** With the immediate-tactics concepts in the model the
  free-move coefficient on the search value is **+0.084 ± 0.026** (A4's model, without
  them: +0.196). The difference is carried by *macro win now* (**+0.675 ± 0.059** — the
  mover can end the game this move), which a free move makes far more available. So
  about half of "a free move is worth +0.2" is the option to cash a macro threat at once,
  and the residual tempo value is ≈ +0.08. The raw head weighs the free move at +0.140
  (gap +0.056) and a macro-win-in-one at +0.764 (gap +0.089): intuition over-credits both.
- **Coefficient paths over training** (figure): macro threats for / against are at their
  final values (+0.10 / −0.14) by iteration 20 — line counting is learned first and never
  moves. The count margin *falls* from +0.106 (raw, it 20) to +0.037 (300): the early net
  counts boards, the trained net counts lines and tempo, and discounts the raw count to a
  third. The free move on the search value *rises* from +0.04 to +0.09 while the raw head's
  falls from +0.19 to +0.14, the raw − search gap shrinking from 0.15 to 0.06: intuition
  converges toward search here, as A4 observed for the earlier nets. Macro-win-now is
  constant at +0.68 on the search value from iteration 20 (the search sees a one-move win
  regardless of the net) while the raw head takes 80 iterations to reach it.
- **Small or null:** local win available now −0.026 ± 0.017 (once the macro win is separate,
  an available local win is worth nothing by itself); dead boards +0.04 ± 0.08 (null);
  opponent local threat −0.099 ± 0.014 (real, a third of a macro threat).
- **Ownership by class** (count margin replaced by boards owned per class, as A5): search
  value centre_self +0.076 ± 0.044, corners_self +0.079 ± 0.032, edges_self +0.066 ± 0.029,
  opponent-owned ≈ 0; net worth +0.066 / +0.090 / +0.066 — A5's residual reproduced on an
  independent 20 000-position sample with the fuller model, again with no class ordering.
  On the *raw* value the asymmetry flips (self ≈ 0, opponent −0.05), so the self/opponent
  asymmetry is not robust and should not be reported; the symmetric statement — *an owned
  board is worth ≈ +0.07 of expected score beyond the lines it lies on* — is.
- **What the value head still under-weights relative to search:** the largest raw − search
  gaps are the ply and empties terms (the raw head does not scale its confidence with how
  much game is left) and the macro-win-in-one (+0.09), not any positional concept. The
  remaining regret is tactical-horizon, which is what a search is for and what C5's
  tablebase would grade exactly.
- **Replication on deep8_c1_300** (`runs/plan5_B3_value_deep8.out`; 20 000 positions from
  deep10's late games, 11 checkpoints): free move on the search value **+0.102 ± 0.026**
  (deep10 +0.084), raw +0.170; macro win now +0.625 ± 0.056 (+0.675); threats +0.125 /
  −0.141; opponent local threat −0.082 ± 0.014 (−0.099); count margin +0.021 ± 0.011
  (+0.036). Ownership by class on the search value: centre_self +0.031 ± 0.043 (n.s.),
  corners_self +0.044 ± 0.032, edges_self +0.041 ± 0.029; net worth +0.005 / +0.049 /
  +0.035. Same coefficient paths (count margin falling from +0.078 at iteration 20, threats
  flat from the start, the raw free-move coefficient above the search's throughout). The
  ownership residual is therefore *small and positive on both nets but not sharp*: +0.07
  on deep10, +0.04 on deep8_300 for corners and edges and nothing for the centre. KNOWLEDGE
  claim 14 is stated at that strength.
- **Replication on the seed replicate `deep10_c1_300_s1`** (2026-09-05;
  `runs/plan5_B3_value_s1.out`, `runs/deep10_c1_300_s1/value_decomp.{json,png}`; the same
  20 000 positions, 30 checkpoints). The final coefficients are the reference's to the
  second decimal: free move on the search value **+0.088 ± 0.026** (deep10 +0.084), raw
  +0.140 (+0.140), gap +0.052 (+0.056); macro win now +0.676 ± 0.058 (+0.675), raw +0.782
  (+0.764); threats +0.103 / −0.138 (+0.10 / −0.14); opponent local threat −0.098 ± 0.014
  (−0.099); local win now −0.028 ± 0.017 (−0.026); dead boards +0.044 ± 0.076 (null on
  both); count margin +0.036 ± 0.010 on the search value, +0.033 raw (+0.036 / +0.037);
  R² raw 0.59 / search 0.56 (0.59 / 0.56). Ownership by class on the search value:
  centre_self **+0.076 ± 0.044**, corners_self **+0.078 ± 0.032**, edges_self **+0.065 ±
  0.028** (deep10 +0.076 / +0.079 / +0.066), opponent-owned ≈ 0, net worth +0.070 / +0.089
  / +0.067 (+0.066 / +0.090 / +0.066); on the raw value the same flip as on deep10 (self
  ≈ 0, opponent −0.04 … −0.05). The class order is corner > centre ≈ edge here, centre >
  corner > edge on deep10, edge highest on deep8_300 — all inside the CIs, so the
  non-ordering (claim 15) holds a third time. Coefficient paths: the threats are at their
  final values at net_0010 (+0.111 / −0.132); the count margin on the raw value falls from
  +0.137 (net_0010) / +0.090 (0020) to +0.033 (0300), the search's from +0.097 to +0.036;
  the free move on the search value rises from +0.01 (0010) / +0.05 (0020) to +0.09;
  macro-win-now on the search value is +0.67–0.69 at every checkpoint while the raw head
  reaches it by net_0020–0030 (deep10: by 80). One deep10 observation is *not* on the
  replicate: the raw head's free-move coefficient falling from +0.19 (iteration 20) to
  +0.14 — here it wanders between +0.06 and +0.18 at the constant LR and settles at
  +0.13–0.14 after the drop. The search-value rise and the +0.05 raw − search gap at the end
  are on both seeds; "intuition converges toward search on the free move" is a one-seed
  path and is not claimed. KNOWLEDGE 14, 16, 17, 19 are stated for both seeds.

**B6 results (2026-09-03; `uttt/surrogate.py`, `tools/distill.py`, `runs/surrogate_deep10.json`,
`runs/plan5_B6_distill.out`, `runs/paired_surrogate_vs_*.json`).** The surrogate is a
conditional logit over 20 hand-written *per-move* features (the position after the move
from the mover's view: wins the board / the game, ends it lost or drawn, gives a free move,
lets the opponent win a board or the game next, threats for and against after, count margin
after, dead boards after, the self-send, cell and target-board classes, the target board's
emptiness) plus a tanh-linear value on the B2 position concepts — everything in torch so
it sits inside the batched search like a net. Fitted to deep10's 256-sim root visits and
value on the 50 000 held-out B2 positions, one DAgger round (2048 surrogate self-play
games, 9048 positions labelled by the net; it changed nothing measurable). *Imitation:*
top-1 agreement with the search's move **41.3 %** on the 10 000 test positions (the net's
own raw policy agrees with its search 66 % of the time, B4), probability on the search's
move 0.21, value R² 0.55. *Play* (paired suite, 64 sims each side): vs v2b **2.2 %
[1.4, 3.1], −661 Elo [−745, −601]**; vs deep10 **0.4 %, −943 Elo**; vs the rollout anchor
at 10 000 playouts per move 14.3 % [12.2, 16.6], **−311 Elo**. So the named concepts
account for two fifths of the move choices and for essentially none of the strength:
the surrogate is ~660 Elo under the small reference net and ~940 under deep10, and loses
to random-playout search with a tenth of the anchor's budget. The legible part is the
weight table (score of a move, before the softmax): send to an emptier board +0.98, wins
the game +0.89, **self-send +0.85** (the book's rule, C1), lets the opponent win the game
next −0.81, local threats kept +0.70, wins a board +0.62, count margin after +0.62, ends the
game lost −0.35; a free move given is +0.12 (not negative — consistent with A4/C2). Value:
side to move is X +0.37, threats against −0.15, open boards +0.15, macro win now +0.15,
count +0.09, threats for +0.08. *Reading:* what the net knows that a linear rule-set
cannot say is not any one of these features but their interaction over several plies —
which is the same conclusion B2 reached from the inside (the concepts that survive the
non-linear control are look-ahead quantities: dead boards, the exact value, the best move).

## 4. Phase C — what the agent knows about the game (the product)

- **C1. Opening book.** The 15 first-move orbits, with replies to depth 4–6, at ≥ 16 k
  sims with the symmetry-averaged deep10 evaluator (3090 time, now free; `atlas.py` PV
  mode, where PV is the principal variation — the line of best moves the search
  expects). A human-readable table: orbit, canonical move, root value, X share and draw
  share from the paired-suite openings that start there, best reply class, agreement with
  deep8_c1_300. Compared line-by-line with the informal human/engine tables in
  knowledge/05 §3 (centre-centre vs centre-corner etc.).
  **Done 2026-09-03** (`tools/book.py`, `runs/book_deep10.{json,md}`, `runs/book_deep8.{json,md}`,
  `runs/plan5_C1*.out`; depth 4, top-3 replies per node, 16 384 sims, symmetry-averaged;
  459 and 437 nodes; 17 min on the 3090 / 29 min on the 3060). First-move values from
  deep10: [40] +0.447, [36] +0.336, [0] +0.282, [37] +0.258, [5] +0.197, [8] +0.196,
  [10] +0.188, [2] +0.183, [4] +0.162, [1] +0.128, [12] +0.113, [16] +0.099, [15] +0.083,
  [9] +0.046, [13] −0.047 — the atlas ordering, and the paired-suite X score by opening
  (deep10 self-play at 256 sims) follows it: 74 % after [40] and [36], 69 % after [0],
  45–51 % after [9], [8], [13]. **The two nets agree on the most-visited move in 75 % of
  the 341 nodes they share** (depth 1: 0.60, depths 2–4: 0.75–0.79; mean |value
  difference| 0.016), and the disagreements are where the book is flat: after [40] the
  top reply has a visit share of 0.19 (deep10: 37) / 0.14 (deep8: 41), after [0] 0.27 /
  0.32; where the reply's share is ≥ 0.7 (after [4], [13], [37], [10], [9], [1], [16]) the
  nets pick the same move. The reply principle the book contains (`tools/book_stats.py`):
  the most-visited reply is the **self-send** — the cell whose index equals the board the
  mover was sent to, which sends the opponent back into that same board — in 52 % (deep10)
  / 57 % (deep8) of the nodes where that cell is free, at every depth, and with a higher
  visit share when chosen (0.83 vs 0.73). Giving a free move is never the top reply in
  the first four plies (no board is closed yet), and "send them back to the board they
  played from" is the top reply in 8–9 %.
- **C2. Named principles with effect sizes**, each tagged behavioural / predictive /
  search-relative / exact and each with its CI and the nets it held across: free move,
  macro line, centre-of-centre, decided-late, tiebreak share, X advantage at strong play,
  plus the untested folk claims — never send to a board where one move wins (minimax.dev's
  pruning rule: is it ever violated by deep10?), the Orlin gambit (deliberately conceding
  the centre board: what does the net say it costs?), what drawn games look like (count
  ties: which boards, how early are they foreseeable). **Done 2026-09-03**: the principles
  are KNOWLEDGE.md §1–§7; the folk claims are `tools/principles.py` →
  `runs/principles_deep10.json`, `runs/principles_deep8.json` (the sending rule is false
  as a rule — 24 % of the search's moves and 69 % of the solver's optimal moves violate
  it — and true as a macro-line rule and an opening rule; the Orlin gambit costs what its
  lines cost; 97 % of draws are 4–4 with one full board), plus the self-send reply rule
  from C1.
- **C3. Puzzle collection v2** (A7's output) with motifs; the *hard* set — where 64-sim
  search still fails — as the game's genuinely difficult ideas, with solver PVs. **Done
  2026-09-03:** `suites/puzzles_v2_dev.npz` (126 puzzles, 5 hard); `tools/annotate.py`
  prints the board, the exact value of every legal move and the solver's lines after the
  best and the net's move (`docs/positions_raw.md`); `docs/positions.md` is the commentary
  on the five hard positions — three of the five winning moves hand the opponent a free
  move, none is a local tactic.
- **C4. `KNOWLEDGE.md` — "What uttt-zero believes about Ultimate Tic-Tac-Toe."** The
  deliverable. One claim per line, with its level, effect size, CI, held-across list,
  tool and output file. The explainer's Part 7 is rewritten from it. This replaces the
  beliefs sections of PLAN2/3/4/RETROSPECTIVE as the place a claim lives. **Drafted
  2026-09-03** (45 claims from Phases A and B, C2's folk claims included via
  `tools/principles.py`); the opening book (C1) and the deep8 replications are still to
  go in, and the explainer rewrite has not been done.
- **C5. Stretch: the ≤ 1-open-board tablebase** (knowledge/06 §5: ≈ 1.2 × 10¹⁰
  positions, ≈ 12 GB at a byte each, Numba backward induction over a DAG). A tablebase is
  a precomputed table of the exact result of every position in some class — here every
  position with at most one open board — built by solving from the end of the game
  backwards. It extends exact ground truth from ~14 empties to the entire last-board
  phase, including the count rule exactly. It splices into search as a terminal lookup
  (free strength) and gives the value head an exact grader far deeper than `endgame_v1`.
  A multi-day build; do it only if B3 shows the value head's late-game error is where the
  remaining regret lives.
  **Built 2026-09-03, and it corrects itself** (`uttt/tablebase.py`, `tests/test_tablebase.py`,
  `tools/tablebase_grade.py`, `tools/openings.py --a_tb/--b_tb`). Two corrections first.
  (i) *The count.* With one board open every legal move is in it, so the value depends only
  on that board's cells, the side to move and the map from its three outcomes (X wins it /
  O wins it / it fills) to the game result — 19 683 × 2 × 27 = **1.06 million entries, 1 MB**,
  built by backward induction in 0.2 s. knowledge/06's 1.2 × 10¹⁰ counted the closed
  boards' identities and the send, neither of which changes the value. (ii) *The reach.* A
  one-open-board position has ≤ 9 empties, which `uttt/solver.py` already solves exactly;
  what the table adds is a GPU-batched lookup (one gather per search batch), which is what
  a terminal lookup inside the search needs. It agrees with the solver on every one of 300
  random positions. **The finding:** on the 701 one-open-board positions among the 60 000
  held-out B2 positions (1.2 %), deep10's raw value head is **100 %** exact (3-way and
  draws), its raw policy plays the optimal move **100 %** of the time, and so does the
  64-sim search — and even v2b is at 99.0 / 99.6 / 100 % and dev1 at 94.0 / 98.7 / 100 %.
  The last-board phase is already solved by every net's search and by the strong nets'
  raw heads; a terminal lookup there has nothing to add to deep10. The splice match
  confirms it (`runs/plan5_C5_tablebase.out`): deep10 @64 with the table vs without,
  **50.0 % [49.9, 50.2]**, 513 of 516 pairs identical, the table consulted on 1.3 % of the
  2.3 M positions the search evaluated; v2b the same, 50.0 %, 509 pairs identical. The
  useful frontier is two open boards
  (≤ 18 empties, where the solver starts to struggle), which needs reachable-only
  generation, not enumeration — knowledge/06's stretch goal, not built.

## 5. Phase D — training (provisional: rewrite this section after Phases A–C)

Training comes last because the analysis decides what training is *for*. Everything
below is a best guess made before Phase A has run; expect the details — and possibly the
list itself — to change once the results of A, B and C are in. Three rules hold
regardless: one change per run against a named parent; judged on the frozen paired suite
by the ±3-point rule, final checkpoints only; and no run starts without the owner's
approval (the pause called in PLAN4 §3c is still in effect).

- **D1. Seed replicate `deep10_c1_300_s1`** — the identical queue6 recipe (`runs/queue6.sh`,
  the script that launched deep10_c1_300) with a different `--seed`, on the 3090, ≈ 19 h
  unattended. Other changes from queue6: `--eval_graph 1` with the retry wrapper (a fault
  costs ≤ 10 iterations, and we learn whether the fault surface is still live; saves
  ~3 h); `--eval_every 10` for a denser timeline; anchors (the fixed opponents the in-run
  evaluation plays) v2b / deep8_c1_300 / **deep10_c1_300**. Purpose, in order: (1) the
  *control* for B2/B3/B5 — a concept, coefficient or opening preference is a fact about
  the game only if both seeds have it; (2) the seed band at 10×128, which no wide/deep
  recipe has; (3) a second measurement of +35 vs deep8_c1_300. It is not a rung of the
  ladder. This is the one Phase D item whose case does not depend on A–C's outcome (its
  job is to check A–C's findings), so it may be started early — during Phase B, on the
  otherwise idle 3090 — if the owner wants the control ready when B2/B3 finish. Add the
  `eval_run.sh` line for it (§6) before it ends. **Launched 2026-09-03 11:52**
  (`runs/queue7.sh` → `runs/deep10_c1_300_s1`, owner-approved); the `eval_run.sh` line is
  in place and runs automatically at the end. Results go here when it finishes (see the
  Handover at the top for what to record). Power loss 2026-09-03 ≈ 15:52 at iteration 94
  (not a GPU fault: an unclean shutdown of the whole machine); relaunched 2026-09-04 16:33
  from `latest_full.pt` at iteration 89; killed by a console-window close at 19:00
  (iteration 128); relaunched 19:49 with a hidden console from iteration 119 — details in
  the Handover. Lesson for launchers: a scheduled task or `cmd` start opens a console
  window that anyone can close, and closing it ends every process attached to it; launch
  training through `wscript` with window style 0 (`runs/launch_queue7_hidden.vbs`).
  **Result (2026-09-05; `runs/deep10_c1_300_s1/analysis.out`; 300 iterations, 43.9 h wall
  including the two interruptions; no GPU fault in 30 graph evals).** Final checkpoint on the
  paired suite @64: **vs v2b 77.3 % [75.0, 79.5], +213 Elo [+190, +236]** (deep10_c1_300:
  80.1 %, +242 [+218, +267]); vs wide128_c1 71.4 %, +159 (73.9 %, +181); vs deep8_c1 67.2 %,
  +125 (69.2 %, +141); **vs deep8_c1_300 51.4 % [48.6, 54.0], +9 [−10, +28]** (55.0 %, +35
  [+16, +54]); **vs deep10_c1_300 50.6 % [48.1, 53.1], +4 [−13, +22]**; vs dev1 83.8 %, +286
  (85.5 %, +308). Endgame set, raw head: WDL 83.9 [82.5, 85.2], draws 68.3 %, regret 0.047
  [0.038, 0.056], optimal 95.9 % (deep10_c1_300 84.6 / 68.7 / 0.037 / 96.7; deep8_c1_300 84.0
  / 0.045); search @256 optimal 99.9 % on both. Readings, in the Handover's order: (1) *the
  seed band at 10×128* — the two seeds are even head-to-head (+4 [−13, +22]) and 2–4 points
  apart against every older opponent (v2b 2.8, wide128 2.5, deep8_c1 2.0, deep8_300 3.6,
  dev1 1.7, always in the reference's favour), so the band on the v2b yardstick is ≈ 3
  points / ≈ 30 Elo, the same size as the ±2.5 measured at 6×64; (2) *the second
  measurement of the last rung* — +9 [−10, +28] vs deep8_c1_300 is below the ±3-point rule:
  **"+ blocks 10" is +35 on one seed and +9 on the other, i.e. inside the seed band**, and
  with A8b's equal-compute result (deep10@64 vs deep8_300@80 −11) the 8 → 10 step is not an
  established rung; duration (+211) is the last confirmed one. `deep10_c1_300/net_0300.pt`
  stays the play agent — still the strongest single net measured — what changes is the
  attribution. (3) *In-run* — the replicate ran 4–10 points under the reference on the
  432-game v2b evals from iteration 110 to 160 with identical self-play statistics (game
  length, result mix, buffer diversity, losses within 0.03), caught up by 189 and matched it
  after the LR drop: a slower trajectory, not a different one; the in-run read and the full
  suite agree at the end (0.775 vs 77.3 %). The control analyses on the replicate are in §3
  (B1, B2, B3 "replication on the seed replicate").
- **D2. Resume the ladder — only if §0's criteria (i)–(iii) fire.** If they do, the run
  is **600 iterations on the current 10-block recipe (≈ 38 h), not 12 blocks (≈ 23 h)**.
  Duration has the better Elo/hour record *and* is the lever that pays at equal inference
  compute (A8b: blocks 8 → 10 did not). Graph eval + retries; deep10 added to the
  anchors. A 12-block run would need a new argument. *Note 2026-09-05:* with D1's result
  the 10-block recipe's own last step is inside the seed band, so a 600-iteration run on
  8 blocks (≈ 32 h) would test duration at lower cost with no established loss; the
  choice is open if D2 is ever triggered.
- **D3. Runs the analysis may suggest** (pure speculation until A–C report):
  - if B1 shows draw recognition and endgame accuracy *stepping* at the LR drops rather
    than climbing between them → a longer or earlier final annealing phase is the
    cheapest test (same iteration count, different `--lr_drops`). **B1 says yes** (§3):
    the step is at the first drop (200), the second drop (280) shows nothing, and every
    curve is flat from 220/240 on. The candidate run is therefore `--lr_drops 150,250` at
    300 iterations (or 200 iterations with drops at 120/180 — the same annealed net at
    two-thirds the cost, if the constant-LR climb from 150 to 200 turns out to be worth
    less than its 3 h). Owner's call, like every run. **Approved 2026-09-05** (after D1):
    run `deep10_c1_300_lr150` — the deep10_c1_300 recipe unchanged except
    `--lr_drops 150,250` (300 iterations, seed 0, graph eval with retries, `--eval_every 10`,
    anchors v2b / deep8_c1_300 / deep10_c1_300; `runs/queue8.sh`, ≈ 14 h; `eval_run.sh` now
    also plays the replicate). *Pre-registered reading.* Primary: the final checkpoint on
    the full paired suite @64 against **both** 10-block seeds. "Helped" only if it scores
    ≥ 53 % against both (the ±3 rule against each); "no effect" if inside ±3 of both;
    "hurt" if ≤ 47 % against either. The seed band is ≈ 3 points, so one run resolves only
    an effect larger than the band — a null therefore means "the constant-LR climb from
    150 to 200 plus a 50-iteration-earlier drop are together worth < 3 points", which is
    itself useful: it licenses the 200-iteration recipe (drops at 120/180) at two-thirds
    the cost. Secondary, from the timeline (±6 in-run): the step should land at the first
    post-drop checkpoint (net_0160) with the reference's size (in-run vs v2b +7–8, raw
    WDL +3–4, draw recognition +10, D4 divergence halved); and after it, the 100
    low-LR iterations either stay flat (the reference's shape after 220: the drop is the
    event) or keep climbing (a longer annealing phase pays) — the shape question this run
    exists to answer. Tertiary: endgame_v1 raw WDL / regret at 300 against 84.6 / 0.037
    (deep10) and 83.9 / 0.047 (replicate). **Launched 2026-09-05 12:12** (after the 3090's
    Afterburner overclock was reset: memory 9751 MHz, power limit 350 W; the driver's
    "prefer maximum performance" mode was left on — irrelevant under load);
  - if A9 shows the v1 endgame numbers were overfit by selection → nothing to train,
    but every future eval reads `endgame_v2_dev`;
  - if B3 finds the value head's remaining error is concentrated in the last-board
    phase → the C5 tablebase spliced in as a terminal lookup is a *search* change, not
    a training one, and should be tried first;
  - if B6's distilled rules capture most of the strength → a smaller net trained longer
    may be the better deployment target, which reopens the width/depth question at
    equal compute rather than equal sims.
- **No further experiments on the nulls**: exact endgame labels, symmetric dedup /
  early-α / extra planes / 4-class ownership, auxiliary-head ablations, SWA,
  `--games 8192` — each was measured once and made no difference (RETROSPECTIVE §3), so
  none is worth another run in either direction. Note that the exact labels are still
  *on* in the current recipe (`--exact_max_empty 14 --exact_per_iter 8192`, weight 2.0
  in `deep10_c1_300/config.json`): they were inherited, measured as harmless, and left in
  place, so D1's "identical recipe" carries them too. A sims-96 phase dosed from
  iteration 60 remains the one un-run variant of a null and is not worth a GPU-day.

## 6. Housekeeping (first hour)

- **Back up** `runs/{deep10_c1_300,deep8_c1_300,deep8_c1,wide128_c1,v2b,v2a,dev1}/{games,net_*.pt,log.jsonl,config*.json}`
  and `suites/` to a location outside the repo and the machine (302 GB free locally; git
  ignores all of it). The corpora are the one artefact that cannot be regenerated.
- `runs/eval_run.sh`: add the `deep10_c1_300/net_0300.pt` match line (guarded like the
  others). `web/server.py`: no change — A8c did not confirm the phased schedule on
  deep10, so flat `--sims 256` (or more) is the play config.
- Docs: README "START HERE" → PLAN5; PLAN/PLAN2/PLAN3/PLAN4/NOTES-v2/RESULTS-*/REVIEW-* →
  `docs/history/` with a one-line index; RETROSPECTIVE and KNOWLEDGE (when it exists)
  stay at top level.
- Explainer artifact: the share pin still points at v1; move it to the current version.

## 7. Order and budget

Each row is a day; the columns say what each GPU is doing and what is being written.
Phase A's tools are all existing, so A1–A7 can be queued in one script and left alone.

| when | 3060 | 3090 | writing |
|---|---|---|---|
| day 1 | §6; Phase A A1–A7 queued (`runs/plan5_A.sh`, unattended) | A9 (endgame_v2 solve, ~2 h; A8 already done); then the replicate if approved (19 h) | B1 script; A "moved" table |
| day 2 | B1 runs; B2 label generator + probe trainer | replicate running (or C1 opening book at 16 k sims) | B1 figure; A results into this file |
| day 3 | B2/B3 grids over 15 checkpoints | C1 opening book | B2/B3 write-up |
| day 4 | B4/B5; B6 surrogate + suite match | B2/B3 on the replicate (if run) | C2–C4: `KNOWLEDGE.md`; explainer Part 7 |
| decision | after Phase A: any *moved* rows → §0 (i); after B1: any late-appearing concepts → §0 (ii). Otherwise the ladder stays paused. | | |

GPU budget for §2–§4 without the replicate: under one 3090-day plus two 3060-days, all
of it interruptible. The replicate is one more 3090-day, unattended.

## 8. Operational notes

- All analysis tools take a checkpoint path. The `--buffer` arguments (`probe_value.py`,
  `surprise.py`) should point at `runs/<run>/latest_full.pt`, the file that carries the
  replay buffer — `latest.pt` no longer carries a buffer.
- Held-out corpus = games the checkpoint never trained on. A run's own games are all
  training data at some point (the 2 M-position buffer is a ≈ 10-iteration window over
  them), so the convention from PLAN2 §2e stands: probe a net on *another* run's games
  (deep10 on deep8_c1_300's iterations 280–299, and vice versa — same strength class,
  different trajectory), or on a fresh self-play corpus generated from the checkpoint.
  Phase A's A3(b)/A4/A7 all use this.
- `suites/` stays frozen: v1 files are never rewritten; v2 files are new names with
  `_dev` / `_test` suffixes; the test halves are read once, at the end, and the reading
  is logged in this file.
- Traps from PLAN4 §5 still apply: no analysis outputs into `suites/`; never edit a
  running run's config; `runs/probe_*` nets are untrained.
