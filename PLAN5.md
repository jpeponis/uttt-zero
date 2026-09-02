# uttt-zero — PLAN5 (draft for owner review, 2026-09-02): from strength to understanding

Written at the pause called in PLAN4 §3c, after RETROSPECTIVE.md. Sections: §0 the
decision (more training, or use the net we have?) with a recommendation; §1 a full review
of the work so far; §2–§4 the analysis programme in three phases; §5 the training runs
still worth doing and the ones that are not; §6 housekeeping; §7 order and budget.
Nothing here has been started. Numbers are from RETROSPECTIVE.md, PLAN4 §3–§4 and
`runs/*/analysis.out`.

## 0. The decision: stop climbing, start reading

**The question.** The ladder is v2b 0 → +77 → +100 → +211 → **+242** (deep10_c1_300) and
neither depth nor duration shows a knee. Each further rung is a committed GPU-day: 600
iterations ≈ 38 h, 12 blocks ≈ 23 h. Do we keep buying Elo, or turn the +242 net around
and use it?

**What Elo has been costing.** Marginal wall-clock per Elo, from `analysis.out`
wall-clocks (abl_cscale1 2.3 h, wide128_c1 4.5, deep8_c1 5.8, deep8_c1_300 14.2,
deep10_c1_300 18.9 — the last including ≈ 3 h of eager-eval tax that is not recipe cost):

| step | Elo (head-to-head) | extra hours | Elo / h |
|---|---|---|---|
| c_scale 0.1 → 1.0 | +40 | 0 | ∞ |
| width 64 → 128 (6 blocks, c_scale 1) | +37 | +2.2 | 17 |
| depth 6 → 8 (150 it) | +23 | +1.3 | 18 |
| duration 150 → 300 (8 blocks) | **+127** | +8.4 | 15 |
| depth 8 → 10 (300 it) | +35 | +1.7 recipe (+4.7 wall) | ≈ 20 |
| *duration 300 → 600 (10 blocks)* | *unknown; +50–90 if the log-compute trend holds* | *≈ +16* | *≈ 3–6* |
| *depth 10 → 12 (300 it)* | *unknown; +20–30 by the last two steps* | *≈ +3.5* | *≈ 6–9* |

The realised steps have not been diminishing in Elo per hour at all; only the
*projected* ones are, and those projections are guesses. If the goal were the strongest
possible net, the answer would be "run both, depth first because it is cheap". It isn't.

**What Elo buys for the project's actual purpose** (README, line 1: "built to *analyse*
the game"):

1. *Game knowledge.* Every belief in RETROSPECTIVE §6 was measured on nets 250–340 Elo
   below the current best (dev1/v2a/v2b, PLAN2 §2e). The beliefs are *orderings* and
   *signs* that were already stable across a 170-Elo span (dev1 → wide128_c1), and the
   magnitudes were declared untrusted at every strength ("report the ordering; distrust
   the magnitudes"). More Elo does not change which findings we can report. **Testing
   the findings at +242 does** — and it costs a day on the 3060, not a GPU-day on the 3090.
2. *Understanding the network.* A bigger net is harder to read, not easier. The most
   informative object for "what did it learn, and when" is the **checkpoint trajectory of
   a 300-iteration run** — fifteen checkpoints, `net_0020 … net_0300`, already on disk for
   deep10_c1_300 and deep8_c1_300. The +127 duration result is a question ("what changed
   between iteration 150 and 300?") that those checkpoints can answer and a 600-iteration
   run cannot.
3. *Deployment.* The only goal Elo serves directly is an external test (CodinGame), which
   is a batch-1 latency problem; the equal-compute result (v2b@256 beats wide128_c1@64 by
   +101) says the ladder's winner is not obviously the deployment winner anyway.

**The risk of *not* pausing** is the draw-blindness lesson. "Draw blindness is
representational" was stated in PLAN2, restated in PLAN3, accepted by both outside
reviewers, and explained on the public page with a satisfying why-story — and it was an
artefact of never training to convergence. Every other §6 belief rests on the same
150-iteration nets. **Re-verification is overdue, and building higher on unverified
beliefs is the wrong order.** We already know what a 600-iteration run would tell us
(the ceiling is higher). We do not know what the net we have has learned, or how.

**Recommendation.**
- **Pause the ladder.** No 600-iteration, no 12-block run.
- **Run the analysis programme (§2–§4) now, on `deep10_c1_300/net_0300.pt`**, with
  `deep8_c1_300` as the second strong net wherever a two-net comparison is cheap.
- **One training run is still worth doing, and it is not a rung: a seed replicate of the
  final recipe** (§5), because it is the *control* the analysis needs — a concept, value
  weight or opening preference found in one seed is a fact about the game only if it
  appears in the other. It runs unattended on the otherwise idle 3090 while the analysis
  runs on the 3060; nothing in Phase A waits for it. Owner's call — it is optional.
- **Resume the ladder only if** (i) Phase A finds beliefs whose *magnitudes* moved between
  deep8_c1_300 and deep10_c1_300 by more than their CIs — i.e. the analysis is
  strength-limited; or (ii) the checkpoint timeline (§3 B1) shows concepts still
  *appearing* at iteration 280–300 rather than sharpening — i.e. the net is still learning
  new things; or (iii) a deployment target appears that needs Elo at a fixed budget. Absent
  those, the marginal GPU-day goes to the opening book and the tablebase (§4).

## 1. Review of the work so far

### 1a. What stands
- **The measurement kit** — paired colour-swapped suite (516 openings, pair bootstrap,
  ±2.8), the exact endgame set, the rollout anchor, seed replicates at 6×64, and the
  pre-registered rule *believe nothing under +3 points, final checkpoints only*. Every
  adopt/null verdict in the project is a sentence because of it; it caught the four-run
  plateau, the SWA loss, and the games-8192 myth. This is the part that generalises.
- **One change per run.** Twelve runs, each a single intervention against a named parent,
  each judged on the frozen suite. The ladder is a chain of pairwise head-to-heads, not a
  leaderboard.
- **Nulls written down with a measured reason** (exact labels: z already exact in 98.7 %;
  hygiene: floor already fixed diversity; SWA: LR phases don't mix; games-8192: GPU-bound).
- **Engineering that survived contact**: 9× throughput ladder, two-file checkpoints, retry
  wrappers, config provenance, git. Three driver faults; zero lost runs after the fix.
- **Review adjudicated with data**, not accepted or dismissed (PLAN4 §2): the statistical
  findings were right and cheap to fix; the micro-optimisations were measured not worth
  it; the orientation-bias worry was bounded at ≤ 0.6 points in 20 minutes.

### 1b. What is weak, ranked by how much it threatens a claim
1. **Every game belief is from nets 250–340 Elo below the best, and one already fell.**
   Atlas, decision time, free-move value, ownership-as-line-counting, puzzle motifs, X
   share, tiebreak share — all PLAN2 §2e, all dev1/v2a/v2b. → Phase A re-runs every one on
   deep10_c1_300 with a written "what moved would look like" before looking (§2).
2. **The yardsticks descend from a −35 Elo net.** `openings_v1`'s "natural" half and
   `endgame_v1` are v2a-corpus positions; `puzzles_v1` is v2b-corpus. The suite is still a
   valid fixed ruler for *strength* (a yardstick need not be representative), but
   "natural" is no longer natural — the strong nets draw about a fifth of their games and
   settle a third by the count rule rather than a line — and `endgame_v1` has been read
   ~50 times in-run and is a development set. → v2 suites from a strong-play corpus, split
   by source game into dev/test *before* solving, test half read once (§2 A7, A9).
3. **No seed replicate of any wide/deep recipe.** The final claim (+35, 55.0 %) is +5.0
   points against a ±2.5-point seed band measured at 6×64 — about 2σ, and the seed band
   at 10×128 is unmeasured. The +23 (deep8_c1 vs wide128_c1) sits at the edge of the ±3
   rule. → §5.
4. **The equal-compute question is open at 10 blocks.** Per simulation deep10 costs
   ≈ 6.7× v2b (blocks × filters²: 10·128² / 6·64²), so the fair fight is v2b@427 vs
   deep10@64 — never played. The page's "small net that thinks longer wins" story was
   measured at width 128 / 6 blocks; it may not survive depth and duration. 15 minutes.
5. **The fault root cause was never found.** Three nvlddmkm faults, all eval-path graph
   replays, none in ~60 h of self-play graphs; `--eval_graph 0` removed the surface at
   ~3 h/run. Only matters if training resumes; then reopen graph eval with retries
   (≤ 10 iterations per fault) rather than pay 6× per eval.
6. **Best-play config is assumed, not verified, on the best net.** Phased "0:128,24:384"
   was verified on v2b and deep8_c1_300; `web/server.py` still takes a flat `--sims`.
7. **Elo non-transitivity** is visible (+127 direct vs +111 ladder-difference) and
   documented; the rule "always quote *vs whom* and *at what budget*" should be in every
   table, including this one.
8. **The knowledge/05 analysis programme stalled at item 3 of 8.** Corpus statistics,
   opening heatmap/atlas and surprise mining were done (v2b era); counterfactual ablation
   was superseded by the freemove regression; distillation, concept probing, look-ahead
   probing and concept discovery were never started. Two of the project's four days went
   to the ladder; the README's stated purpose got one.
9. **Documentation sprawl**: PLAN, PLAN2, PLAN3, PLAN4, NOTES-v2, two RESULTS, three
   REVIEWs, RETROSPECTIVE, now PLAN5 — twelve files, four of which say "START HERE" to
   somebody. The product this plan should end with is a single `KNOWLEDGE.md` (§4 C4);
   the process files can move to `docs/history/`.
10. **Storage and backup**: `runs/` is 11 GB, of which the `games/` corpora (≈ 1.5 M games
    per 300-iteration run) are the irreplaceable part; git ignores them and nothing else
    holds a copy. 302 GB free on C:. An hour (§6).

### 1c. Methodological notes going forward
- The ±3 rule worked. Keep it, and add its sibling for analysis claims: **each belief
  gets a pre-written "moved" criterion** before the new net is run against it (the
  table in §2 is that list).
- **Capacity claims need a convergence check.** The draw-blindness error was not a
  statistics error — the CIs were fine — it was an explanation that fit. Rule: no claim
  of the form "the network can't represent X" unless the relevant metric was flat over
  the run's final LR phase; otherwise say "not yet learned".
- **Probe accuracy ≠ causal use** (knowledge/05: Pálsson 2024, Othello-GPT). Every probing
  result in Phase B pairs with a behavioural or ablation test, and reports a
  randomly-initialised-net control.
- **Two seeds or it's a seed.** For network-internals findings, "replicated across seeds"
  is the bar — which is what §5's run is for.

## 2. Phase A — re-verify every belief at +242 (3060, ≈ 1 day, existing tools, unattended)

Net under test: `runs/deep10_c1_300/net_0300.pt`; second column `deep8_c1_300/net_0300.pt`
where cheap. Write the "moved" criterion first, then run.

| # | belief (level) | tool | measured on | "held" means | "moved" means |
|---|---|---|---|---|---|
| A1 | [40] best first move; [13] worst; ordering universal (search-relative) | `tools/atlas.py` deep10 + deep8_300 × 1k/4k/16k sims | dev1/v2a/v2b | [40] rank 1 in all columns; Kendall τ ≥ 0.85 vs v2b@16k | any column with [40] ≠ 1, or τ < 0.7 |
| A2 | root Q-gap between top replies ≤ 0.02 ("openings are flat") | same, `runs/atlas_pv.out` style | v2b | ≤ 0.03 for ≥ 12/15 orbits | gaps ≥ 0.05 in the majority — a stronger net *found* opening edges |
| A3 | games decided late: best-child-Q settled from ply 38 (median), nothing at 30 (predictive) | `tools/decision.py`, deep10 net on (a) the same 4000 held-out v2a games and (b) 4000 of deep8_c1_300's iteration-280+ games | v2b on v2a games | median settled ply within 36–42 on (a) | median < 34 on (a) (stronger net predicts earlier) — or > 42 on (b) (stronger play defends longer) — both are findings |
| A4 | free move +0.16 ± 0.03 (search-relative) | `tools/freemove.py`, 256-sim deep10 values, natural positions from deep8_c1_300's late games | v2b | CI overlaps [0.10, 0.22] | outside; also re-check the raw-head coefficient (was +0.26 — the gap is the "search corrects intuition" term) |
| A5 | ownership ≈ 0 with threats controlled; ±0.17 per macro line | same regression | v2b | line coefficient CI overlaps ±0.17; ownership within ±0.05 | ownership coefficients leave zero |
| A6 | X share 57–60 %; draws rise with strength; count decides ~30 % of strong games | `tools/corpus_stats.py` on deep10 iters 280–299 vs v2a's last 20; plus the `end reasons` lines already in every paired match | v2a/v2b | — descriptive; report the new numbers | — |
| A7 | raw-policy endgame failures are count-rule and free-move motifs, not local tactics | `tools/puzzles.py --out suites/puzzles_v2_dev.npz`, positions from deep8_c1_300's late games (not deep10's own training data), ≤ 14 empties | v2b (3.5 % puzzles, 11 hard) | motif ordering same | puzzle rate ≪ 1 % (the +242 net has nothing left to teach here) or motifs reshuffled |
| A8 | equal-compute: search beats width | `tools/openings.py match`: deep10@64 vs v2b@427; deep10@64 vs deep8_300@80; also phased "0:128,24:384" vs uniform 256 on deep10 | wide128_c1 vs v2b@256 (−101) | v2b@427 still wins | deep10@64 wins — depth+duration bought something 4× search cannot |
| A9 | endgame: raw WDL 84.6 / draws 68.7 / search 99.8 % optimal | `tools/endgame.py` build `suites/endgame_v2_{dev,test}.npz` from deep8_c1_300's iteration-280+ games (strong-play distribution; not deep10's training data — deep8_300's own score on it carries that caveat), split by source game before solving; eval both nets on v1 and v2_dev; v2_test once, at the end of PLAN5 | endgame_v1 (dev-contaminated) | v2_test within ±2 of v1 | v1 ≫ v2_test: the v1 numbers were overfit by selection |

Output: `runs/plan5_A.out` per tool, and a results table appended to this file with each
row marked **held / moved / reversed**. Rows that *moved* are the interesting ones and
feed §0's resume criterion (i).

## 3. Phase B — the network on its own terms (new tooling; both GPUs free)

Three questions: *what* does it compute, *how*, and *when* did it learn it. The
300-iteration checkpoint sequence makes "when" nearly free.

- **B1. Checkpoint timeline** (`tools/timeline.py`, new, ≈ 100 lines; 1–2 h GPU). For each
  of the 15 deep10_c1_300 checkpoints (and deep8_c1_300's): in-run paired score vs v2b
  (already in `log.jsonl`, ±6 — fine for a curve), endgame WDL / draw recognition / raw
  regret (`endgame.py eval`, ~1 min each), first-move policy entropy and top-1 share
  (McGrath's opening-narrowing statistic), policy entropy by ply bucket, D4 consistency
  (B5). One figure: every curve on the iteration axis with the LR drops marked. **This is
  the direct answer to "where did +127 come from"** — draw recognition 55 → 69 is the
  first curve to draw; if it steps at the LR drops rather than climbing, the story is
  "annealing", not "more data".
- **B2. Concept probes** (`uttt/concepts.py` label generator + `tools/probe.py`, new,
  ≈ 300 lines; a day). Hook the residual stream after the stem and after each block
  (128 × 9 × 9 per position). Labels computed from state, no oracle needed: per-board
  status (X / O / drawn-full / open), open-board count, dead boards (winnable by
  neither), macro threats for / against (count), free move available now, target board,
  count margin, empties, side to move; plus two *lookahead* labels — the exact value for
  ≤ 14-empty positions (from the endgame set) and the 2-ply-ahead best move (solver where
  exact, else 256-sim search) in the spirit of Jenner et al. Linear probes and
  one-hidden-layer probes, trained on 50 k positions from held-out games, tested on 10 k;
  **randomly-initialised deep10 as the control** (report accuracy above control, not raw);
  layer × checkpoint grid per concept. Two specific comparisons: (i) how much better a
  trunk probe for board ownership is than the net's own ownership head (is the aux head
  reading what the trunk already knows?); (ii) which layer the lookahead labels become
  decodable in, if any.
- **B3. Value decomposition** (generalise `freemove.py`'s regression; half a day). Regress
  the raw WDL expectation, and separately the 256-sim search value, on the B2 concept
  set, per checkpoint. Reports: R², the coefficient path over training (when does the
  head start weighing macro lines? free moves? the count?), and the raw-vs-search
  coefficient gap per concept — the part of each concept the net still under-weights.
  Ties directly to RETROSPECTIVE §6's "hierarchy is line-counting in disguise".
- **B4. Counterfactuals and surprise** (`tools/probe_value.py`, `tools/surprise.py`, exist;
  hours). Flip centre-board ownership, grant/deny a free move, force-close a board on
  natural deep10 positions; raw-head delta vs 256-sim delta. Then `surprise.py`'s top 30
  raw-vs-search disagreements, inspected by hand in the web UI, written up as annotated
  positions — the *Game Changer* format.
- **B5. Symmetry** (`uttt/symmetry.py`, exists; hours). Per position, the policy's
  Jensen–Shannon spread and the value's spread across the 8 orientations, by checkpoint
  and by ply. Measures how much of D4 the net learned versus what symmetry-averaging still
  adds (+1–2 WDL points at v2b — is it less at deep10?).
- **B6. Distillation to a legible surrogate** (`tools/distill.py`, new; a day). Fit a
  linear model and a depth-limited tree on the B2 hand features to imitate deep10's
  256-sim policy and value (VIPER-lite, one DAgger round), then **play the surrogate on
  the paired suite at 64 sims** against v2b@64 and deep10@64. The Elo gap is the share of
  the net's play that the named concepts do *not* capture — a number a reader can hold.

Order: B1 → B2 → B3 → B4/B5 → B6. All of it pairs a decodability result with a
behavioural one (§1c); nothing in Phase B is reported from probe accuracy alone.

## 4. Phase C — what the agent knows about the game (the product)

- **C1. Opening book.** The 15 first-move orbits, replies to depth 4–6, at ≥ 16 k sims with
  the symmetry-averaged deep10 evaluator (3090 time, now free; `atlas.py` PV mode). A
  human-readable table: orbit, canonical move, root value, X share and draw share from
  the paired-suite openings that start there, best reply class, agreement with
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
  deliverable. One claim per line, level, effect size, CI, held-across list, tool and
  output file. The explainer's Part 7 is rewritten from it. This replaces the beliefs
  sections of PLAN2/3/4/RETROSPECTIVE as the place a claim lives.
- **C5. Stretch: the ≤ 1-open-board tablebase** (knowledge/06 §5: ≈ 1.2 × 10¹⁰ positions,
  ≈ 12 GB at a byte each, Numba backward induction over a DAG). Extends exact ground
  truth from ~14 empties to the entire last-board phase, including the count rule
  exactly; splices into search as a terminal lookup (free strength) and gives the value
  head an exact grader far deeper than `endgame_v1`. A multi-day build; do it only if B3
  shows the value head's late-game error is where the remaining regret lives.

## 5. Training: the run that is worth doing, and the ones that are not

- **Worth doing (optional, owner's call): `deep10_c1_300_s1`** — the identical queue6
  recipe with a different seed, on the 3090, ≈ 19 h unattended. Changes from queue6:
  `--seed`, `--eval_graph 1` with the retry wrapper (a fault costs ≤ 10 iterations and we
  learn whether the surface is still live; saves ~3 h), `--eval_every 10` for a denser
  timeline, anchors v2b / deep8_c1_300 / **deep10_c1_300**. Purpose, in order: (1) the
  control for B2/B3/B5 — a concept, coefficient or opening preference is a fact about
  the game only if both seeds have it; (2) the seed band at 10×128, which no wide/deep
  recipe has; (3) a second measurement of +35 vs deep8_c1_300. It is not a rung; nothing
  in Phase A waits for it. Judged by the ±3 rule like everything else.
- **Not now: 600 iterations (≈ 38 h), 12 blocks (≈ 23 h).** Resume criteria are §0's
  (i)–(iii). If resumed, duration first (better Elo/h record), graph eval + retries,
  deep10 added to the anchors and to `eval_run.sh`.
- **Not at all, still**: exact labels, hygiene, aux-head ablations, SWA, games-8192 — the
  nulls stay null; a sims-96 phase dosed from iteration 60 remains the one un-run
  variant of a null and is not worth a GPU-day now.

## 6. Housekeeping (first hour)

- **Back up** `runs/{deep10_c1_300,deep8_c1_300,deep8_c1,wide128_c1,v2b,v2a,dev1}/{games,net_*.pt,log.jsonl,config*.json}`
  and `suites/` to a location outside the repo and the machine (302 GB free locally; git
  ignores all of it). The corpora are the one artefact that cannot be regenerated.
- `runs/eval_run.sh`: add the `deep10_c1_300/net_0300.pt` match line (guarded like the
  others). `web/server.py`: accept a ply schedule for `--sims` (the CLI matcher already
  does) so the UI plays the verified best config.
- Docs: README "START HERE" → PLAN5; PLAN/PLAN2/PLAN3/PLAN4/NOTES-v2/RESULTS-*/REVIEW-* →
  `docs/history/` with a one-line index; RETROSPECTIVE and KNOWLEDGE (when it exists)
  stay at top level.
- Explainer artifact: the share pin still points at v1; move it to the current version.

## 7. Order and budget

| when | 3060 | 3090 | writing |
|---|---|---|---|
| day 1 | §6; Phase A A1–A7 queued (`runs/plan5_A.sh`, unattended) | A8/A9 (matches + endgame_v2 solve, ~2 h); then the replicate if approved (19 h) | B1 script; A "moved" table |
| day 2 | B1 runs; B2 label generator + probe trainer | replicate running (or C1 opening book at 16 k sims) | B1 figure; A results into this file |
| day 3 | B2/B3 grids over 15 checkpoints | C1 opening book | B2/B3 write-up |
| day 4 | B4/B5; B6 surrogate + suite match | B2/B3 on the replicate (if run) | C2–C4: `KNOWLEDGE.md`; explainer Part 7 |
| decision | after Phase A: any *moved* rows → §0 (i); after B1: any late-appearing concepts → §0 (ii). Otherwise the ladder stays paused. | | |

GPU budget for §2–§4 without the replicate: under one 3090-day plus two 3060-days, all
of it interruptible. The replicate is one more 3090-day, unattended.

## 8. Operational notes

- All analysis tools take a checkpoint path; `--buffer` arguments (`probe_value.py`,
  `surprise.py`) should point at `runs/<run>/latest_full.pt` (the buffer-bearing file)
  — `latest.pt` no longer carries a buffer.
- Held-out corpus = games the checkpoint never trained on. A run's own games are all
  training data at some point (the 2 M-position buffer is a ≈ 10-iteration window over
  them), so the convention from PLAN2 §2e stands: probe a net on *another* run's games
  (deep10 on deep8_c1_300's iterations 280–299, and vice versa — same strength class,
  different trajectory), or on a fresh self-play corpus generated from the checkpoint.
  Phase A's A3(b)/A4/A7 all use this.
- `suites/` stays frozen: v1 files are never rewritten; v2 files are new names with
  `_dev` / `_test` suffixes; the test halves are read once, at the end, and the reading
  is logged in this file.
- Traps from PLAN4 §5 still apply (no analysis outputs into `suites/`; never edit a
  running run's config; `runs/probe_*` nets are untrained).
