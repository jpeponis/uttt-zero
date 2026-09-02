# uttt-zero — PLAN5 (draft for owner review, 2026-09-02): from strength to understanding

**What this plan is.** uttt-zero has spent four days making its network stronger at
Ultimate Tic-Tac-Toe. This plan proposes to stop doing that for now and to use the
strongest network we have, `runs/deep10_c1_300/net_0300.pt`, to study the game instead.
It was written at the pause the owner called in PLAN4 §3c, after RETROSPECTIVE.md. If you
are picking the project up: read §0 for the decision and the recommendation, then start
with §6 (housekeeping, one hour) and Phase A (§2). Nothing in this plan has been started
except A8, three 10-minute matches described in §2. Training is paused by owner directive.
No training run may be launched without the owner's approval (§5).

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
  optional.
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

## 4. Phase C — what the agent knows about the game (the product)

- **C1. Opening book.** The 15 first-move orbits, with replies to depth 4–6, at ≥ 16 k
  sims with the symmetry-averaged deep10 evaluator (3090 time, now free; `atlas.py` PV
  mode, where PV is the principal variation — the line of best moves the search
  expects). A human-readable table: orbit, canonical move, root value, X share and draw
  share from the paired-suite openings that start there, best reply class, agreement with
  deep8_c1_300. Compared line-by-line with the informal human/engine tables in
  knowledge/05 §3 (centre-centre vs centre-corner etc.).
- **C2. Named principles with effect sizes**, each tagged behavioural / predictive /
  search-relative / exact and each with its CI and the nets it held across: free move,
  macro line, centre-of-centre, decided-late, tiebreak share, X advantage at strong play,
  plus the untested folk claims — never send to a board where one move wins (minimax.dev's
  pruning rule: is it ever violated by deep10?), the Orlin gambit (deliberately conceding
  the centre board: what does the net say it costs?), what drawn games look like (count
  ties: which boards, how early are they foreseeable).
- **C3. Puzzle collection v2** (A7's output) with motifs; the *hard* set — where 64-sim
  search still fails — as the game's genuinely difficult ideas, with solver PVs.
- **C4. `KNOWLEDGE.md` — "What uttt-zero believes about Ultimate Tic-Tac-Toe."** The
  deliverable. One claim per line, with its level, effect size, CI, held-across list,
  tool and output file. The explainer's Part 7 is rewritten from it. This replaces the
  beliefs sections of PLAN2/3/4/RETROSPECTIVE as the place a claim lives.
- **C5. Stretch: the ≤ 1-open-board tablebase** (knowledge/06 §5: ≈ 1.2 × 10¹⁰
  positions, ≈ 12 GB at a byte each, Numba backward induction over a DAG). A tablebase is
  a precomputed table of the exact result of every position in some class — here every
  position with at most one open board — built by solving from the end of the game
  backwards. It extends exact ground truth from ~14 empties to the entire last-board
  phase, including the count rule exactly. It splices into search as a terminal lookup
  (free strength) and gives the value head an exact grader far deeper than `endgame_v1`.
  A multi-day build; do it only if B3 shows the value head's late-game error is where the
  remaining regret lives.

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
  `eval_run.sh` line for it (§6) before it ends.
- **D2. Resume the ladder — only if §0's criteria (i)–(iii) fire.** If they do, the run
  is **600 iterations on the current 10-block recipe (≈ 38 h), not 12 blocks (≈ 23 h)**.
  Duration has the better Elo/hour record *and* is the lever that pays at equal inference
  compute (A8b: blocks 8 → 10 did not). Graph eval + retries; deep10 added to the
  anchors. A 12-block run would need a new argument.
- **D3. Runs the analysis may suggest** (pure speculation until A–C report):
  - if B1 shows draw recognition and endgame accuracy *stepping* at the LR drops rather
    than climbing between them → a longer or earlier final annealing phase is the
    cheapest test (same iteration count, different `--lr_drops`);
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
