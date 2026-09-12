# uttt-zero — PLAN7 (2026-09-12): from findings to a paper — the systematic account, the literature, one new question, and the second outside review

**What this plan is.** PLAN6 closed with its programme complete: the update lever measured three
doublings deep (+100 → +64 → +40), the equivariant line closed by a self-play run that hurt and two
supervised studies that explain why, the analysis second pass done on the +363 net (15 held, 18
moved, 1 reversed), the repository public. The owner now asks for the work to be *understood* rather
than extended: a systematic account of what has been learned about Ultimate Tic-Tac-Toe and about
training a network to play it, set against the literature, with whatever unique contribution the
evidence supports stated plainly — and a second outside review woven through it rather than bolted
on at the end. That is a write-up, and this plan is the plan for the write-up. It proposes exactly
one new training run (§5), because the one question the literature flags as open and this project
can answer cheaply — what the most-boards tiebreak does to the game — needs a controlled twin, and
nothing else in the open list does.

Terms are as in PLAN5's glossary (`docs/history/PLAN5.md`). Rules that hold throughout, unchanged:
one change per run against a named parent; judged on the frozen paired suite by the ±3-point rule,
final checkpoints only; no training run starts without the owner's approval; every claim about the
game carries its level, CI, the nets it held on, and the file that produced it. Two rules are added:
**nothing enters the manuscript that is not already a line in `KNOWLEDGE.md`** (the paper is
assembled from the claims file, not written beside it), and **every outside-review finding is
adjudicated in this file before anything acts on it** (§7, as PLAN6 §1 did).

## Handover (2026-09-12)

**State (2026-09-12, evening).** Nothing is running on either card (the 3090 shows 827 MiB and ≈ 10 %
because it drives the desktop; that is not a job). The play agent is `runs/deep8_c1_300_e8/net_0300.pt`
(+40 [+23, +57] over `_e4`, +363 vs v2b, endgame 91.3 / 0.022, 256-sim search 100 % optimal on both
solved sets). The repository is public at `https://github.com/jpeponis/uttt-zero` (commit `cfc290e`:
MIT for the code, CC BY 4.0 for the prose and data, `CITATION.cff`); **E11's off-machine copy is still
owed** — 5.23 GB (`games/` 2.40, `net_*.pt` 2.81) with no destination on this machine (PLAN6 Handover
2026-09-12; the `games/` corpora are single-copy). `runs/` is 17.02 GB.

**Done for this plan today:** the reading (KNOWLEDGE, RETROSPECTIVE, knowledge/01–06, PLAN6 §0–§1,
§5, §9, REVIEW-astra's structure and the codex-review log's brief); the audit in §1; the preflight of
the review mechanics (§7a — `codex-sp exec` ran `gpt-6-astra` at xhigh in a read-only sandbox in 6 s,
session `01a097ef-822f-74b1-9320-ea4f93e2799a`); the literature survey delegated to an Opus agent —
`knowledge/07-literature-2026-survey.md`, 885 lines, **landed and merged into §2** (the log's second
entry; its one novelty-changing finding, a public AlphaZero on these exact rules, was verified against
GitHub before it went in).

**What the next instance does, in order.** (1) *Done 2026-09-12:* `knowledge/07` merged into §2, §3
re-ranked (C1's claim reworded, §2c). (2) Commit this file; launch **M0**, the review of the plan
itself (§7c, Appendix A), from the repo root, monitored through its JSONL stream; adjudicate it into
§7e when it returns and amend the plan before anything else starts. (3) Phase J (§4) on the desk and
the 3060 — J1–J4 need no approval. (4) Put **K1** (§5) to the owner with M2's pre-registration review
attached; launch only on approval, and only if the instance is under the 50 % line (PLAN6 Handover's
rule, unchanged). (5) Phase L (§6) is the owner's call; §3 says why it is recommended. (6) The
manuscript (J5) and the file updates (§10) follow the readings; M3 and M4 review the draft.

## Log

- **2026-09-12, evening — PLAN7 written.** After E11's push (PLAN6 log 19:05). Inputs read in full:
  `KNOWLEDGE.md` (55 claims), `RETROSPECTIVE.md`, `knowledge/01, 02 §2, 03, 05, 06`, PLAN6 §0–§1
  (the 22-row adjudication), §5, §9; `docs/history/REVIEW-astra.md`'s structure and the brief that
  produced `REVIEW-codex.md` (`runs/codex-review.log`, lines 14–30). Review mechanics preflighted
  (§7a). Literature survey delegated (Opus `directed`, web tools) → `knowledge/07-literature-2026-survey.md`,
  pending at the time of writing. Both cards idle. No run launched.
- **2026-09-12, later — `knowledge/07` landed and merged.** 885 lines; 85 tool calls, ≈ 22 min of an Opus
  agent with every web tool. Three findings change this plan and are folded in. (1) **A public
  AlphaZero on the exact closed-board / most-boards rules exists** — `pc29277/AlphaZero_UTTT`, created
  2026-08-19 (ten days before knowledge/03 was compiled), 10 × 128, 2.98 M parameters, 22 T4-hours,
  28 544 games at 100 sims, 76 % vs a depth-3 alpha-beta, no license, no analysis of the game;
  **verified here against the GitHub API and its README** (`created_at 2026-08-19T22:48Z`; its rule
  statement names the count tiebreak). "First public AlphaZero on this variant" is withdrawn; "first
  calibrated, first replicated, first used to produce game knowledge" stands (§0, §2c, §3 C1;
  knowledge/03's judgment (a) carries the addendum). (2) The update lever is Lc0's **sampling ratio**
  exactly, and published practice clusters at ≈ 1 with the only two experiments in the literature
  warning *against* going higher — so the curve is not merely unpublished, it runs against the
  field's stated expectation (§0, §1b, §2b; the Lc0 figures spot-checked against its wiki). Wang et
  al. 2020's "more epochs hurt" is reconciled, not contradicted: their lowest setting is above this
  project's highest in reuse units. (3) The equivariance negative has one published analogue (SLAP on
  Gomoku: a supervised gain that did not transfer to self-play), and KataGo's root symmetry-averaging
  is the project's +35 trick, never given an Elo figure before (§2b). Also merged: the replay-ratio
  literature as the concept's home, the scaling-law comparators, the 2025–26 probing papers, the
  solver-technique pointers, the refreshed arena figures (10 085 entrants; Legend 431), and the
  survey's thirteen "not in the literature" candidate claims, which §2c now points at. Not merged
  uncritically: the survey's games-per-minibatch → reuse conversions for AGZ / AZ / ELF / MiniZero are
  its own arithmetic, flagged ± 30 %, and are quoted as estimates; venues it could not verify are
  cited as arXiv. Next: M0.

## 0. The decision in front of the project

**What the paper is.** Three papers could be written from this repository, and they want different
emphases:

1. *A paper about the game.* The first quantitative strategy account of closed-board, most-boards
   Ultimate Tic-Tac-Toe from a strong agent: the opening by orbit at three budgets and four
   strengths, the value of a free move with its conditional structure, when games settle, how they
   end, what the count rule decides, the folk claims tested against the solver — every number with
   its level and CI and a *strength-drift test* (held / moved / reversed across +211 → +363) that
   says which of them are facts about the game and which are facts about the net that produced them.
   Nothing like it exists for any variant (knowledge/03 §6: "not found anywhere: an 81-cell first-move
   value heatmap from a strong agent, a reply table for X's opening, a quantified value of a free
   move, draw/win rates by opening under either tiebreak, or any of this for the most-boards variant").
2. *A paper about training.* On this game and this budget the learner was **update-limited by a
   factor of eight** — three doublings of the **sample-reuse ratio** (optimizer samples per generated
   position; `--epochs` is exactly Lc0's "sampling ratio"), nothing else changed, were +100, +64,
   +40 Elo — where published practice sits at ≈ 1 (AlphaZero ≈ 0.5–0.7, AlphaGo Zero ≈ 1.4, ELF ≈ 0.8,
   Lc0 ≈ 1, MiniZero ≈ 1–1.3, pgx 1; KataGo caps at 4 and calls that conservative), the project's own
   recipe card said "~1–2", and the only two experiments in the literature warned in the *other*
   direction (ELF: below 10 games per minibatch "hinders training … severe overfitting"; Lc0 at ≈ 12×
   reuse over-fitted its value head; knowledge/07 §4). And an exactly D4-equivariant trunk at equal
   inference cost **lost 220 Elo** in self-play, with the mechanism traced (a small-step advantage that
   reverses by 12 480 supervised steps; capacity, not the learning rate; the parameter-matched net
   memorises). Both are clean, one-change-per-run, CI-bounded results with supervised twins.
3. *A paper about measurement.* The paired suite with the ±3-point rule, the seed band, the
   "same seed is the same start, not the same run" finding, the supervised gate that has to be read
   at the run's step count, the strength-drift test — a methods paper for people who train small
   AlphaZeros on one machine and want to say true things.

**Recommendation: one paper, the game as its subject, the other two as its instrument and its second
contribution.** The game account is what nobody has; the training results are what make the account
credible (they say how strong the instrument is and why); the measurement discipline is what lets the
reader believe either. A methods-only paper would discard the part that is unique. The working title
is stated so it can be argued with: *"What a strong self-play agent knows about Ultimate Tic-Tac-Toe,
and how much of it survives getting stronger."*

**What the evidence cannot support, said first so the paper never says it.** The game is unsolved
and this project does not change that (knowledge/06: 10³³–10³⁸ positions; Elhage's DFPN at ≈ 20 ply
in hours). Every game claim is *search-relative*, *behavioural* or *predictive* unless marked *exact*;
"the best first move" means "at 1k–16k simulations on four nets spanning 150 Elo", not a theorem. One
ordering has already flipped with strength (claim 7); the paper's central methodological claim is
that the *rest* did not, and the honest form of that sentence is "orderings and signs survived 120
Elo with one exception, and magnitudes did not saturate" — not "stable". No "first AlphaZero on
these rules" claim: `pc29277/AlphaZero_UTTT` (2026-08-19) is one, at two orders of magnitude less
compute and against a depth-3 alpha-beta — what is first here is the calibration, the replication and
the use of the agent to produce game knowledge (knowledge/07 §2.2). No "strongest public agent"
claim is made without an external match (§6); until then the calibrated statement is "+363 over the
project's own v2b reference at 64 simulations, itself ≈ +169 over a 100 k-playout rollout UCT, the
CodinGame Legend recipe".

**Why one more run, and only one.** PLAN6 §9's programme is complete and `--epochs 16` is not
proposed (predicted inside the seed band at ≈ 32 h). The question that *is* proposed (§5) is not a
rung: it is a controlled experiment on the rules — the same recipe trained under the plain-draw
tiebreak, so that every claim in KNOWLEDGE §1–§8 can be marked *rule-invariant* or *rule-dependent*.
That is the one thing the literature says would be new that this project is uniquely placed to do
(knowledge/03 judgment, item 3), it costs one GPU-day, and its readings are pre-registered in §5.
Nothing else is proposed.

## 1. What has been learned — the audit

This section is the investigation's first product: the 55 claims of `KNOWLEDGE.md` sorted by what
kind of evidence stands behind each, so the paper can be assembled tier by tier and a reviewer can
see at a glance what is proven, what is stable, what drifts, and what is not known. The tiers are
this plan's proposal; M0 reviews them.

### 1a. About the game: the claims in five evidential tiers

| tier | meaning | claims | what the paper does with them |
|---|---|---|---|
| **E — exact** | checked against the solver or the one-open-board tablebase | 28 (search 99.7–100 % optimal on solved samples), 29–30 (raw head names the exact result: 84.6 → 91.3 % across the ladder; the sealed half agreed within 0.3), 31 (draw recognition was optimisation, not capacity), 31a (the one-open-board phase: 100 / 100 / 100 on every net), 32 (what the raw policy still gets wrong late: the count rule and tempo, 2.1 → 1.0 %), 33–34's solver columns (the optimal move sends the opponent to a winnable board 69–70 % of the time; never to an immediate macro win when not already lost) | stated as facts about positions sampled from strong play, with the sampling stated; never as "solved" |
| **S — stable** | sign and ordering held on all four strong nets *and* the last re-read's magnitude sat inside the earlier CI (I1's "held") | 1 ([40] best, [13] worst, 12 of 12 columns), 8 (a free move +0.195 ± 0.028 — deep10's number to the third decimal), 11 (the raw head over-credits it by ≈ 0.09, three nets), 13 (a macro threat ≈ +0.15 / −0.14, four strengths), 17 (line counting learned by iteration 10–20 and never moves), 19 (an opponent's local threat ≈ −0.09), 21 (X wins settle at 32, O wins and draws at 39–41), 26 (96 % of draws are 4–4 with one full board), 31a, 33–34 (the folk rule is false as a rule; the true rule is macro-immediate), 35 (conceding the centre is a null once lines are controlled), 36 (the encoding exposes the obvious concepts; a random net reads them at 98–100 %), 38 (tactics shallow and early, value deep and late), 40 (the ownership head learns late ownership, 68–71 % vs 50 % baselines; switching it off was a strength null) | the core of the game section; each quoted with all four nets' numbers |
| **M — moved** | sign and ordering held; the magnitude on the +363 net fell outside the earlier CI, in the direction strength has always pushed it (I1's "moved") | 2 (τ vs v2b 0.96 → 0.85: the opening sharpens), 3 (X's edge after [40] +0.28 → +0.354 → +0.447 → +0.495 and still rising), 4–5 (fewer flat replies, wider best-to-worst range, a new non-[40] sharp reply after [2]), 7a (the self-send 55 / 58 → 48 % — still the most common reply, no longer a majority), 9 (the conditional free-move coefficient 0.43 → 0.60 of the unconditional), 10 (a free move worth most late and when ahead; the middlegame now runs with the count), 14 (the per-board residual +0.02 … +0.08 and not growing), 16 (the raw board count discounted further, +0.037 → +0.022), 20 / 22 (settling median 36 → 34 on strong play; the ply-0 caveat grows to 21 %), 23 (policy–search disagreement 34 → 31 %, the value gap unchanged at 0.19), 24 (X 63 / O 21 / draws 16.6 %: X flat since deep10, draws still rising out of O's column), 25 (the count rule decides a third of games, not a quarter — flat for 250 Elo, then +6 points in 120), 27 (52.8 plies, 5.1 free moves per game, both climbing), 32 (failures halve again), 37 (the same probe grid learned 20–50 iterations earlier), 39 (the trunk carries a little more of the line ahead) | stated with the trajectory, not a point: "X's edge after [40] has risen at every strength measured and has not saturated" |
| **R — reversed** | an ordering flipped between +242 and +363 | 7 (after [40], `_e4` puts 0.71 of its visits on the corner reply orbit 36 where deep10 put 0.75 on the edge orbit 37, and rates the edge subtree +0.022 better where the earlier nets rated the corner +0.016 better; its atlas agrees at 1k, 4k and 16k). The two lines were within 0.02 of each other on every net. | the most important line in the game section: it is what the strength-drift test is *for*, and it lands where the method said a reversal could — on a near-tie. uttt.ai's prose ("O's best reply pushes play into a corner board") agrees with the stronger net, §2a |
| **N — not re-read at +363** | read on deep10 (and often deep8_300 / the replicate) but its tool is not in I1 | 6 (the opening is learned first: ≥ 0.95 on [40] by iteration 20–30), 12 (tensor edits overstate the free move 2×), 15 (which board class is worth most — unresolved on three nets and read as noise), 18 (a dead open board is worth nothing), 38a (which concepts the trunk computes vs merely re-formats: dead boards, exact value, best move survive the non-linear control; threats and the immediate win do not), 41 / 41b (residual asymmetry 0.027 bits; the 8-way average +35 / +32 at 8× the cost, −201 at equal compute; exact canonicalisation a null, deep10 and `_e2`), 41a (a legible surrogate reproduces 41 % of the search's moves and none of its strength, −661 vs v2b) | quoted from the nets they were read on, marked as such; J1 decides which are cheap to re-read on `_e8` and does those |

### 1b. About training a model to play it: the ledger as a recipe card

What this project would tell someone training an AlphaZero for this game on one PC today, each line
with its evidence (RETROSPECTIVE §3, KNOWLEDGE 42–51):

- **Search:** Gumbel AlphaZero at 32–64 simulations in self-play, `c_scale` 1.0 (0.1 → 1.0 was +40
  Elo for nothing — the training *target*, not play, is what it sharpens). Play at a flat 256+; the
  phased schedule that helped weak nets (+50 on v2b) is a null on strong ones (+10 / +11).
- **Net:** an 8-block × 128-filter ResNet with a 3-way WDL head. Depth 8 → 10 is inside the seed band
  at equal sims and a wash at equal compute; width 64 → 128 was ≈ +37 on its own. **Do not build the
  symmetry in**: an exactly D4-equivariant trunk at equal inference cost is −220 Elo (50), at equal
  parameter count it is 7× the cost and memorises (48); D4 *augmentation* leaves 0.027 bits of
  residual asymmetry that costs nothing at play (41b) and is cheaper to search through than to
  average away (41). Tied heads are the one equivariant idea whose supervised margin does not
  reverse — untested in self-play, predicted null-to-small.
- **Data:** an exploration floor with sampled openings (without them the policy collapses onto one
  opening), a 2 M-row buffer spanning ≈ 7.6 iterations, D4 augmentation per sample. Exact endgame
  labels, symmetric dedup, extra planes, a four-class ownership head, auxiliary heads off, SWA, a
  96-sim final phase, bigger self-play batches — all clean nulls.
- **The lever nobody pulls: the sample-reuse ratio** — optimizer samples per generated position
  (`n_steps = epochs · games · steps / batch`, so `--epochs` *is* the ratio; Lc0 names it the sampling
  ratio, and Lc0 and KataGo are the only systems that publish theirs). One pass was the project's
  default for a week and the field's practice. Two passes: +100 Elo for +1.3 h of training. Four:
  +64 more. Eight: +40 more, with each generated row drawn about eight times, the sampled distinct
  fraction down to 0.45, and *nothing complaining* — replay age, skipped steps, losses and self-play
  statistics all unchanged (46, 49, 51). The supervised twin says the same: for a fixed teacher the fit
  is a function of steps, not of distinct positions — eight passes over 50 k positions equal one pass
  over 400 k (47). The +127 of "duration" (150 → 300 iterations) was mostly its updates.
- **Schedule:** 300 iterations with LR drops at 200 / 280. The first drop is a fixed ≈ +5 … +9 step on
  whatever the constant-LR phase has built; moving it earlier costs ≈ 5 points (−32 Elo, D3); the
  second drop does nothing resolvable on four runs (F2). Strength is built at the constant LR.
- **Measurement:** the paired suite (516 openings × both colours, ±2.8) with the ±3-point adoption
  rule and a measured seed band (≈ 3 points / ≈ 30 Elo at 10 × 128); an out-of-process evaluator on
  the second card scoring every tenth checkpoint on the full suite; a solver-labelled endgame set with
  a sealed half read once. In-run curves are for shape only (±6). And a reference saturates: at 89 %
  vs v2b two nets 40 Elo apart read the same number — the head-to-head against the parent is the
  instrument from +300 on.
- **Cost:** the strongest net is 21.96 h on an RTX 3090 (self-play 12 h, training 10 h), 2.46 M
  parameters, and evaluates for exactly what its 1×-update parent cost.

### 1c. About measuring either: the method

Five findings that are about the instrument, and belong in the paper's methods section because they
are what make the rest believable: (i) the ±3-point rule is a decision rule, not an equivalence test
(PLAN6 §1 item 21); (ii) "same seed" fixes the start, not the trajectory — a 4096-game loop amplifies
a last-bit difference within one iteration, so every same-seed comparison is one perturbed run
against the seed band (item 13); (iii) a supervised screening gate has to be read at a step count of
the order of the run it licenses — Phase G's ordering at 3 120 steps reversed by 12 480 and self-play
read the reversed ordering (48, 50; RETROSPECTIVE §5); (iv) the strength-drift test — re-read every
claim on a net 120 Elo stronger, three verdicts pre-registered (held / moved / reversed) — is how a
claim from a learned agent earns the word "about the game" (PLAN6 §9c); (v) probe decodability is not
use: the random-init control, the non-linear control (38a) and the surrogate's −661 Elo (41a) are the
three guards, and a claim is stated only where all three were passed.

### 1d. What is not known

The game's value (unsolved; the empty board reads +0.5 utility for X at 16k sims after the best first
move, an estimate, §4 J3). Anything beyond depth 4 of the opening book. Whether the [40]-reply
reversal is the first of several or an isolated near-tie (a `--epochs 16` net would say; not
proposed). Which board class carries the residual (15 — noise on four nets). The two-open-board exact
frontier. How the agent stands against any external opponent (§6). And the one this plan proposes to
buy: **which of these facts are facts about the most-boards rule** (§5).

## 2. The literature, and where this project sits

*Sources: knowledge/01, 03, 05, 06 (2026-08-29 / 09-03) and the 2026-09-12 survey `knowledge/07`,
merged here (the log's second entry). knowledge/07 carries the full citations, source-type tags and
the thirteen candidate "not in the literature" claims; this section keeps the comparisons.* Every comparator
carries its rule variant, because the single most common error in this literature is quoting a result
for one variant as if it held for another (knowledge/01 §0).

### 2a. Comparators on the game

| topic | the literature says (variant; source) | this project measures (closed-board / most-boards; file) | reading |
|---|---|---|---|
| Best first move | Centre-centre, "undoubtedly the best move" — uttt.ai's prose; gPress's uttt.ai scores CC +11.81 > centre-corner +11.07 > centre-edge +8.16 > corner-of-same-corner +6.47 > corner-of-opposite-corner +6.12, every edge-board opening "bad" — five of the 15 orbits, on uttt.ai's undocumented internal scale (closed / **draw**); royerk's rollout MC puts centre at ≈ 52 % (CG rules) | [40] +0.495 > [36] +0.395 > [0] +0.309 ≈ [37] +0.305 > [5] +0.254 > [8] +0.232 > … > [9] +0.039 > [13] −0.079 at 16k on `_e4`; rank 1 and 15 fixed in 12 of 12 columns; τ 0.85–0.96 across 340 Elo (1–3; `runs/plan6/I1_A1_atlas.out`) | **Agrees on the top two and on "edge-board openings worst"** ([13], [9], [15], [16] are the four lowest). uttt.ai has centre-edge third and corner-same fourth; here [0] and [37] are within 0.004 and swap with budget — the one place the two orderings differ is a tie on both. Extension: 15 orbits × 3 budgets × 4 nets with the drift stated, where the literature has one engine's undocumented scale |
| O's reply to [40] | "O's best reply pushes play into a corner board, and the next ≈ 8 moves stay in the corner boards" (uttt.ai prose, draw variant) | deep10 and deep8_300 prefer the *edge* reply (0.75 / 0.54 of visits); `_e4` prefers the *corner* orbit 36 (0.71) and its PV after [40] is `36, 0, 8, 80, 77, …` — corner boards for eight plies (7; `runs/book_deep8_e4.json`) | **The strongest net agrees with uttt.ai; the two weaker strong nets did not.** This is the one reversal, and an independent engine sits on the stronger side of it. The paper says so |
| First-player advantage | "P1 has a 60 % winrate" among Legend bots (darkhorse64); random play 50.9 / 7.2 / 41.9 (snowfrogdev, CG rules); "either P1 wins or a draw can be forced" (jacek, an impression) | Self-play with exploration: X 62.7 / O 20.7 / draws 16.6 % at +363 (24); paired-suite X score by opening 74 % after [40], 45–51 % after [9], [8], [13] (7); the root after [40] reads +0.495 utility ≈ 75 % expected score at 16k | Same order as the arena's 60 %; **extension: conditioned on the opening and on strength, with CIs, and the draw share separated** — the literature has no side-conditioned numbers from a strong agent |
| Draws and the tiebreak | SaltZero vs the #2 CG bot: +65 =96 −39, **48 % draws** (closed / draw); Daporan's 2018 objection that the most-boards rule lets P1 "collect small boards"; nobody quantifies how often the count decides a game | 16.6 % drawn at +363 and rising with strength; **a third of games reach the count** (16.5 % decided by it, 16.6 % equal) — flat at a quarter for 250 Elo, then +6 points in the last 120 (24–25); 96 % of draws are 4–4 with one full board (26) | **New:** the first measurement of what the tiebreak does at strength. §5 buys the comparison under the same agent |
| Game length | uttt.ai self-play 40–50 plies; FLAIRS 2022 "at least 30"; CG folk 50–60 | 52.8 plies (p10 47, p90 59), lengthening with strength; 5.1 free moves per game, 98.5 % of games contain one (27) | Consistent; extension: the distribution and its drift |
| The free move | "Very powerful" (uttt.ai); "don't give up free moves for free" (gPress); a heuristic weight of 2 vs 5 for a board win and 10 for the centre board (BoardGameGeek); no quantification anywhere | **+0.195 ± 0.028 utility** with everything else controlled, the same to 0.004 on three strong nets; ≈ +0.08 … +0.12 with the immediate macro win in the model; largest late and when ahead (+0.30 at plies 44–50); the raw head over-credits it by 0.09 (8–11) | **New, and the paper's cleanest single number.** Against the folk weights: a free move (+0.195) is worth more than an own board (+0.02 … +0.08) and about as much as a macro threat (+0.15) |
| "Never send them to a winnable board" | Universal folk advice; Elhage's rigorous version (never send to a board where one move wins *the game*) | The strong move does it 24 % of the time and the **optimal** move 69–70 %; the optimal move never hands an immediate macro win when not already lost (33–34) | **The folk rule is false as stated and Elhage's is the true one** — confirmed against the solver, not against an agent |
| The centre board | HUJI weights 10 (centre) vs 3 (corner); "an enduring advantage" (gPress); the Orlin gambit | With lines controlled, the opponent owning the centre is +0.01 ± 0.04 (a null); the raw head's centre premium is the fourth line through it (35, 15) | The premium is line-counting in disguise |
| Solved status | Bertholon 2020: X wins in ≤ 43 (**open-board** rules — a different game); Elhage: ≈ 20-ply positions in hours, the root at ≈ 10⁸ CPU-hours (closed / draw); nothing for the most-boards rule | Exact from ≤ 14–16 empties in ≈ 0.04–0.2 s per position (3 000 positions in 2–9 min); the one-open-board phase solved outright; the agent 100 % optimal at 256 sims on every solved sample (28–32, 31a) | Not a solution; **J4 turns it into a "solved from ply N on strong play" curve**, the closest thing to Othello's 36-empties milestone this game has |

### 2b. Comparators on the method

| topic | the literature says | this project measures | reading |
|---|---|---|---|
| Sample reuse (optimizer samples per generated position) | Published practice clusters at ≈ 1: AlphaZero ≈ 0.5–0.7 (30 games per minibatch; Lc0's wiki computes 0.69 / 0.48), AlphaGo Zero ≈ 1.4, ELF OpenGo ≈ 0.8, Lc0 0.5–14 over its history settling near 1, KataGo ≤ 4 ("conservative"), MiniZero ≈ 1–1.3, pgx 1 (knowledge/07 §4.1; the AGZ / AZ / ELF / MiniZero figures are the survey's conversions, ± 30 %). The two explicit experiments warn *against* more: ELF, "decreasing this ratio significantly below 10:1 hinders training (likely due to severe overfitting)"; Lc0 at ≈ 12× reuse over-fitted its value head. Wang et al. 2020 (6×6 Othello, ep ∈ {5, 10, 15} passes over the *whole buffer*): the inner-loop knobs "should be set at lower values". The project's own recipe card said "~1–2" | 1 → 2 → 4 → 8: **+100, +64, +40 Elo**, monotone, no over-fitting signature at eight (46, 49, 51); the supervised twin: fit is a function of steps, not positions (47) | **The curve is not merely unpublished — it runs against the field's stated expectation.** Wang et al. is reconciled, not contradicted: their *lowest* setting (5 passes over a buffer) is above this project's *highest* (8 passes over the new data ≈ 1.05 passes over the 7.6-iteration window) in reuse units — jointly consistent with an optimum between and a broad plateau, and both refute "≈ 1 is principled". The concept's home is model-free RL's replay / update-to-data ratio (Fedus 2020; Nikishin 2022; D'Oro 2023 — where high ratios need resets; here they need nothing), and no dose–response exists for an AlphaZero-style board-game system (knowledge/07 gap 7). The paper's second contribution |
| Scaling | Jones 2021 (AlphaZero on Hex): ≈ 500 Elo per decade of total training compute, ≈ 150 per doubling; Neumann & Gros 2022: strength a power law in parameters and compute on Connect Four / Pentago, published models "significantly smaller than their optimal size" | +100 / +64 / +40 per doubling of the *training half only* (self-play cost unchanged); width +37, depth +23 then inside the seed band | At this regime (9×9, 2.46 M parameters, 8× reuse still paying) the project is update-limited, not parameter-limited — stated as a regime, not as a contradiction of the scaling law |
| Symmetry | The prior is that equivariance buys sample efficiency (Cohen & Welling 2016; Carroll & Beel 2020 for board games — unnumbered, supervised, no peer-reviewed version found); VISA-VIS: augmentation halves value generalisation error; the one self-play test, **SLAP on Gomoku** (Suen & Alonso 2023): a supervised 8× data saving that "was not yet evident" to speed up RL. What the strong systems do: AlphaGo Zero, Leela Zero, KataGo **augment 8× with an ordinary CNN**; KataGo additionally averages the policy over symmetries at the search root, with no Elo figure published for it; REVIEW-astra §5.3 recommended an exact-D4 trunk as "the next useful architectural experiment" | Exact D4 trunk at equal cost **−220 Elo** (50); at equal parameters 7.0× the cost and memorising (48); tied heads' supervised margin closes slowly and does not reverse; canonicalisation a null at play (41b); the 8-way root average **+35 / +32 Elo at 8× the inference, −201 at equal inference** (41) | **Augment, do not enforce** — the first measurement of an exactly equivariant trunk in a full self-play run at matched inference cost, a clean negative with a mechanism (a small-step advantage that reverses; capacity, not LR), and the equal-cost vs equal-parameter distinction the equivariance literature rarely draws. And 41 is the first Elo figure for KataGo's root-averaging trick, with the equal-inference control it lacks (knowledge/07 §4b, gaps 8–9) |
| LR schedule | Standard step schedules; leela-zero's warning that in-run drops invite memorisation | The first drop a fixed +5 … +9 step on whatever the constant phase built, strength settling within ≈ 20 iterations; an earlier drop hurts (−32); the second drop nothing on four runs (42, F2) | "Both drops delivered" was withdrawn by the full-suite instrument; only the first is real |
| Depth vs updates | AlphaZero-scale wisdom: deeper is better | 8 → 10 blocks inside the seed band at equal sims, a wash at equal compute; the 8-block net with 2× the updates beats the 10-block net by +86 at 0.81× the cost (44) | At this budget, updates before depth |
| Concept probing | McGrath et al.: concepts emerge in order, opening policy narrows (one trajectory); Hex (Lovering et al. 2022): search knows before the net does, endgame concepts late, long-term mid-trunk (one agent); Pálsson et al. 2024: decodability ≠ importance, want non-linear and amnesic probes; Othello-GPT: linear probes can miss what non-linear ones find; the 2025–26 chess transformers: nameable concepts *early* and alien representations *deep* (arXiv:2510.26025), look-ahead up to seven moves (Zhao et al. 2025), intermediate-layer solutions overridden at the output (arXiv:2508.21380) | Tactics at block 5 by iteration 60–80, lines mid-trunk by 100–140, value at the last block by 180–220, **the grid repeated on four independently trained nets**; the opening collapses to [40] by iteration 30; a random-init control, a non-linear control on a random net (38a), and a surrogate that carries none of the strength (41a); the move two plies on decodable at +7 points over control against +14 for the current move (39) | Reproduces the Hex shape and honours the Pálsson caveat by construction — and the four-net replication is what the literature lacks (knowledge/07 gap 12). The layer profile is the *reverse* of the chess transformers' (an architecture and scale difference, to be said not argued); the trunk carries far less of its own line than a chess transformer (a clean negative). No distillation study reports its residual in Elo against a ladder; 41a's −661 / −943 is that number (gap 11) |
| Same-seed comparisons | Rarely discussed; "deterministic seeds" assumed | Same seed = same start only; divergence at iteration 1 before any intervention; replication is the defence (PLAN6 §1 item 13) | A methods footnote worth a paragraph |

*Citation cautions carried from the survey:* "Wu 2019" is two papers — D. J. Wu, "Accelerating
Self-Play Learning in Go" (KataGo, arXiv:1902.10565) and T.-R. Wu et al., "Accelerating and Improving
AlphaZero Using Population Based Training" (AAAI 2020) — cite both and keep them apart; the reuse-ratio
conversions for AlphaGo Zero, AlphaZero, ELF and MiniZero are the survey's arithmetic from
games-per-minibatch (± 30 %), and only Lc0's and KataGo's are published as ratios; venues the survey
could not verify are cited as arXiv.

### 2c. Where the project extends the literature, and where it only confirms it

*Confirms:* centre-centre best; edge-board openings worst; P1 advantage of the arena's order;
≈ 50-ply games; Elhage's form of the "poisoned square" rule; the Hex / McGrath emergence shape.
*Is preceded by:* `pc29277/AlphaZero_UTTT` (2026-08-19) — an AlphaZero on these exact rules, two
orders of magnitude less compute, strongest opponent a depth-3 alpha-beta, no game analysis; the
paper cites it and claims first *calibrated*, first *replicated*, first *used to produce game
knowledge*. *Extends with numbers nobody had:* the full first-move orbit table with drift; the reply
reversal; the free move's value and its conditional structure; the count rule's share and its rise;
the draw anatomy; settling plies; the failure-motif ordering of the raw policy; the sample-reuse
dose–response; the equivariance negative with mechanism; the Elo of root symmetry-averaging; the
four-net probe replication; a surrogate's residual in Elo. *Runs against the field's expectation:*
"keep the sampling ratio near 1" (ELF, Lc0, KataGo's cap, Wang et al.); the priority the first
review and the equivariance literature give to exact symmetry. *Corrects itself:* "the choice of
reply hardly matters" (the earlier form, fixed by orbit); "the endgame is a wall for the value head"
(optimisation, not capacity). knowledge/07's closing section lists **thirteen candidate claims** the
literature does not contain — six about the game, six about method, one about the field's lack of a
shared benchmark; the paper makes those §1a's tiers support, each phrased "we are not aware of",
never "none exists".

## 3. The contribution — candidates, ranked

Ranked by what each adds to the paper per unit of cost, with the honest form of its claim.

- **C1. The game account with the strength-drift test — already in hand, free.** §1a is the paper's
  spine. With `pc29277` on record (§2c) the novelty is not "an AlphaZero on these rules"; it is the
  *protocol* and what it produced: every claim carries the nets
  it held across and a pre-registered verdict at the next strength, so the reader can see the one
  ordering that flipped and the eighteen magnitudes that moved. Cost: J1, J5 (desk).
- **C2. The tiebreak as a controlled variable — one GPU-day, the one new run (§5).** Train the same
  recipe under the plain-draw rule and re-read every claim under it: *rule-invariant* or
  *rule-dependent*. Sharp predictions are available (the board-count coefficient, 16, should vanish;
  the draw share should approach SaltZero's 48 %; [40] should stay best; the reply after [40] is the
  open question). This is the one claim the literature names as new that this project can make
  cleanly; it turns "facts about closed-board / most-boards UTTT" into "facts about UTTT, and the part
  the tiebreak adds". Owner's approval required.
- **C3. The exact frontier as a curve — hours on the CPU (J4).** For strong-play positions at each
  ply, the fraction the solver completes within a fixed budget, and the agent's optimality there. Gives
  "from ply ≈ N on strong play the game is exactly solved and the agent plays it perfectly" as a
  measured curve rather than a sampled anecdote — the closest thing to a partial-solve milestone
  available for this game. No approval needed.
- **C4. The sample-reuse dose–response and the equivariance negative — already in hand, free.** The
  second contribution. The fourth point on the curve (`--epochs 16`) is not proposed; the paper
  states the three and their supervised twin and stops.
- **C5. The empty board's value and the side split under greedy play — an hour on the 3060 (J3).**
  One quotable number ("+0.50 utility for X at 16k simulations on the strongest net, and rising with
  strength") and the X / O / draw split without exploration noise. Cheap; clarifies 24's exploration
  caveat.
- **C6. External calibration — days of desk, GPU-hours (§6).** Places the ladder on an outside scale
  (SaltZero, uttt.ai's engine, a Legend-recipe rollout bot under the CodinGame referee). The field has
  no shared benchmark — uttt.ai, SaltZero, tacult, pc29277 and the FLAIRS CNN each report against a
  private ladder and no two have ever played each other (knowledge/07 gap 13) — so this adds nothing to
  the *game* claims, which are self-contained, but everything to the sentence "a strong agent";
  without it the paper says "+363 over an internal reference that is ≈ +169 over a 100 k rollout UCT"
  and no more. Recommended if the paper is going out; the owner decides the budget.

**The recommendation:** C1 + C4 + C3 + C5 are the paper (desk and hours). **C2 is proposed** as the
single new experiment. C6 is recommended and priced in §6.

## 4. Phase J — the systematic account (desk and the 3060; no approval needed)

- **J1. The claims audit, finished.** §1a's tiers written into `docs/paper/01_claims_map.md` as a
  table with one row per claim: number, one-line statement, level, tier, nets, the numbers at each
  strength, the file. The N-tier's cheap re-reads on `_e8` are done here if a tool runs in under an
  hour on the 3060 (`probe_value.py` for 12 / 18; `timeline.py` for 6 — both cheap); the rest are
  quoted as read. *Output also:* the list of every claim that the manuscript will quote, in order,
  which is the manuscript's outline.
- **J2. The literature table, final.** `knowledge/07` merged into §2; `docs/paper/02_literature.md`
  as the paper's related-work section with every comparator's variant stated. Any comparator the
  survey finds that bears on a claim is added to that claim's KNOWLEDGE line as a one-clause note
  ("uttt.ai's prose agrees").
- **J3. The empty board (C5).** `tools/atlas.py` already searches the 15 first-move orbits; add the
  root itself: `deep8_c1_300_e8` and `_e4` at 16 384 sims, symmetry-averaged, from the empty board;
  and 2 000 greedy games (`gumbel_scale 0`, 256 sims, no floor) from the empty board on each — the X /
  O / draw split without exploration. ≈ 1 h on the 3060. Pre-registered: the root value is reported
  with its search-relative label; the split is compared with 24's exploration split and the
  difference is the exploration's contribution.
- **J4. The exact frontier (C3).** From `deep8_c1_300_e8`'s late games, 500 positions at each ply from
  40 to 70; run `uttt/solver.py` with a node budget (10⁸) and a wall cap; record per ply the fraction
  solved, the median nodes, and the 256-sim search's optimality on the solved ones. CPU, unattended,
  hours. Output `runs/plan7/J4_frontier.{json,out}`; a KNOWLEDGE line: "on strong play the solver
  completes N % of positions from ply P within B nodes, and the agent is optimal in M % of them".
- **J5. The manuscript skeleton.** `docs/paper/paper.md` — abstract, the game and its variant,
  methods (the pipeline in a page; the measurement kit; the drift test), the training ledger, the game
  account tier by tier, the equivariance negative, limitations (§0's list), reproducibility (the
  repository, the suites, the exact commands). Figures listed with the file that produces each. No
  sentence without a KNOWLEDGE number behind it. Written after M1, revised after K1's reading.
- **J6. The file updates** (§10).

## 5. Phase K — the one new run: the tiebreak as a controlled variable (owner's approval)

**K1. `deep8_c1_300_e8_draw`** — `deep8_c1_300_e8`'s recipe with one change: when all nine boards
close with no macro line, **the game is a draw** (the Wikipedia / uttt.ai / SaltZero / OpenSpiel rule)
instead of going to the board count. Everything else identical: 8 × 128, 300 iterations, drops at
200 / 280, `--epochs 8`, seed 0, the same floor and openings, the E7 worker beside it.

*Engineering (a day of desk, before the launch).* A `rule` field (`count` | `draw`) threaded through
the terminal logic — `uttt/batch.py:180–183` (`count_winner` → 0 under `draw`; `end_reason` 2 becomes
3), `uttt/game.py:99–101`, `uttt/solver.py`'s terminal value, `uttt/exact.py` (exact labels during
training), `tools/endgame.py build` (a draw-rule solved set for the run's endgame reads),
`tools/corpus_stats.py` / `principles.py` (end reasons), `tools/atlas.py`, `book.py`, `freemove.py`,
`value_decomp.py` (they search, so they must search under the rule), `tools/openings.py match`
(`--rule`, default `count`); `config.json` `_provenance` records it. Tests: the two engines
cross-checked under both rules on 10⁶ random games; a hand-made 4–4 final position that is a count
draw under both rules and a 5–3 one that is a win under `count` and a draw under `draw`; the solver
against brute force on tiny positions under both. The paired suite is opening positions and needs no
change; `v2b` and every anchor were trained under `count` and are used under both rules with that
stated.

*Cost.* ≈ 22 h on the 3090 (the parent took 21.96 h; the terminal test is not on the critical path),
plus ≈ 6 h on the 3060 for the readings. Inside the Windows Update pause (to 2026-10-14).

*Pre-registered readings, in order.*
1. **Rule-invariance of the game claims (primary; the reason for the run).** The I1 tool set run on
   the draw net *under the draw rule* (`runs/plan7/K1_*.out`), each §1–§8 claim marked
   **rule-invariant** (sign and ordering as under `count`) or **rule-dependent** (a sign or ordering
   differs), with the magnitude beside it. Predictions written now: 1 invariant ([40] best — uttt.ai's
   draw-variant engine agrees); 16 dependent (the board-count coefficient goes to ≈ 0: under `draw`
   the count decides nothing); 25 not applicable (no count endings) and 24 dependent (the draw share
   rises far above 16.6 % — SaltZero's 48 % is the only datum); 8 and 13 invariant (a free move and a
   macro threat are tempo and lines, not count); 7's reply after [40] — no prediction, and that is the
   interesting row; 33–34 invariant (macro-immediate is a line rule).
2. **Cross-play (secondary).** The full paired suite at 64 sims, 2 × 2: each net under each rule
   against the other. The ±3 rule applies to each cell. Prediction: the `count` net under `draw` loses
   less than the `draw` net under `count` — the count rule adds a skill the draw net never learned
   (the "collect boards" endgame, 32's tiebreak-conversion motif) — stated as a prediction, not a
   result.
3. **Corpus (tertiary).** Draw share, length, free moves per game, the self-send rate, end reasons
   over the last 20 iterations; the draw anatomy (26) under a rule where 5–3 is a draw.
4. **Strength under its own rule.** The draw net's E7 curve vs the `count` anchors *under `draw`*,
   for shape only; there is no draw-trained reference, and none is proposed.

*What K1 cannot say.* Anything about strength between the two nets in an absolute sense (different
games); anything about the open-board variant (a third game). One run, one seed: read against the
≈ 3-point band like every other.

## 6. Phase L — external calibration (optional; recommended for the paper; owner's budget)

The ladder's only outside anchor is a 100 k-playout rollout UCT (`uttt/rollout.py`; v2b ≈ +169 over
it). Three routes, priced from knowledge/03:

- **L1. A Legend-recipe rollout bot under the CodinGame referee.** Bitboards, 80–90 k rollouts per
  100 ms, an MCTS solver — the forum recipe; ≈ 1–2 days of desk to rebuild (no Legend source is
  public), then paired games through `Agade09/CG-UTTT-Arena` or `cg-brutaltester`. Connects to the
  arena's Elo scale under **exactly our rules**. The net needs a batch-1 stdin/stdout wrapper on the
  GPU (100 ms per move is generous for one 8 × 128 evaluation; 256 sims at batch 1 is the question —
  measure first, `tools/gtiming.py` has the harness).
- **L2. SaltZero** (GPL-3, weights released, ships an arbiter and a line protocol; the only public NN
  bot with an external benchmark — 113–87 over the then-#2 CG bot at 400 ms). **Draw variant**, a
  bit-rotted TF 2.12 stack. Play it under its rules (with K1's draw net, if K1 runs) and under ours
  with the caveat stated. ≈ 1 day of desk if the stack installs.
- **L3. uttt.ai's C++ NMCTS** (Apache-2.0, weights on Drive; probably the stronger engine, never
  benchmarked). Draw variant. ≈ 1 day of desk. Playing L2 against L3 would itself be a new result.

Any of the three turns "+363 vs v2b" into a number a reader outside this repository can place. L1 is
the one under our rules and is the recommendation if only one is bought. None is required for the
game claims. A CodinGame *submission* is not proposed: the 100 KB source limit makes a 10 MB net
impossible without a distillation project of its own.

## 7. Phase M — the second outside review: mechanics and protocol

### 7a. Mechanics (verified 2026-09-12)

`codex-sp` is a PowerShell function (`~/.codex/codex-functions.ps1`, deployed from claude-config)
that runs `codex --profile personal --config model_instructions_file="<claude-config>/System Prompt.txt" @args`.
The `personal` profile (`~/.codex/personal.config.toml`) sets **`model = "gpt-6-astra"`,
`model_reasoning_effort = "xhigh"`**. Codex CLI is 0.154.0; `gpt-6-astra` is in its model cache.

- **Launch, non-interactive, from the repo root** (PowerShell; the launcher is not in the PowerShell
  tool's profile, so dot-source it first):
  ```
  . "$env:USERPROFILE\.codex\codex-functions.ps1"
  Set-Location "C:\Users\John Peponis\Desktop\uttt-zero"
  $tag = "M0_plan"; New-Item -ItemType Directory -Force "docs\reviews\$tag" | Out-Null
  Get-Content "docs\reviews\$tag\brief.md" -Raw | codex-sp exec -s read-only --json -o "docs\reviews\$tag\REVIEW.md" - > "docs\reviews\$tag\events.jsonl"
  ```
  `-` reads the brief from stdin (piped — PowerShell has no `<`); `--json` streams every event (agent messages, commands run, token
  counts) as JSONL to stdout, which is what makes **"analysis along the way"** possible — the file is
  tailed from this session while the review runs; `-o` writes the final message verbatim as the
  review; `-s read-only` means the reviewer can run anything and change nothing. The session id is on
  the first lines of the stream; **`codex exec resume <id>`** continues that session with our
  adjudication for a rebuttal round. When a reviewer should write reproduction scripts,
  `--worktree` gives it a managed git worktree to write in, and `docs/reviews/<tag>/` is copied out of
  it — the working tree is never the reviewer's.
- **Preflight (2026-09-12):** `codex-sp exec -s read-only "Reply with exactly the word OK"` from the
  repo root — `model: gpt-6-astra`, `reasoning effort: xhigh`, `sandbox: read-only`, answer `OK`,
  **6 s, 17 932 tokens** (the injected prompt and AGENTS.md are the floor), session
  `01a097ef-822f-74b1-9320-ea4f93e2799a`, exit 0. A whole-repository review will run to millions of
  tokens over 1–3 h; the owner's Codex five-hour and weekly limits are the budget, and a review is
  launched when the GPUs are busy and this session is idle.
- **Monitoring from this session:** a background shell per review, its JSONL tailed with `Read`;
  the event types worth watching are the agent's messages (its running commentary), each `exec`
  (what it is checking) and the final `-o` write. A review that stops emitting for 20 min is checked,
  not killed.

### 7b. Protocol — what changes from PLAN6

PLAN6's review was one shot: a brief, a 460-line document at a named commit, a 22-row adjudication
(§1) — and it worked (RETROSPECTIVE §5: "adjudicating with data beat both accepting and dismissing").
Four things improve on it here:

1. **Staged, not terminal.** Five reviews at the five points where a wrong turn is cheapest to
   catch (7c), each with a narrow question and a word budget, instead of one review of everything.
2. **A rebuttal round.** Every adjudication is sent back through `exec resume` with the evidence;
   the reviewer's reply is recorded beside the verdict. PLAN6 could not do this; the astra review's
   RNG reading (item 13 — right fix, wrong cause) would have been settled in one exchange.
3. **Reproduction as a deliverable.** The brief names the outputs (`runs/plan6/*.out`, `runs/*/analysis.out`,
   the JSON) and asks the reviewer to *recompute* a named number from them before it disputes it.
   REVIEW-astra's `review_astra/` scripts were the best part of that review; they are the norm now.
4. **Calibration stated in advance.** 7d records the first review's track record so the adjudicator
   weights the second one on evidence rather than authority — in both directions.

Unchanged: the reviewer reads the repository at a named commit; it never sees this session's
reasoning; the brief states the rule variant and which files are results and which are plans; it is
read-only unless writing reproduction scripts in a worktree; the review is saved verbatim; every
finding lands in an adjudication table (verdict / evidence / lands in) in this file before anything
acts on it; the owner sees the adjudication, not just the review.

### 7c. The stages

| stage | when | question put to the reviewer | reads | output |
|---|---|---|---|---|
| **M0 — the plan** | now, before Phase J | Are §1's tiers the right partition of the claims? Is §0's recommendation (one paper, the game as subject) right, and is the working title honest? Is K1 the right single run, and are its pre-registered readings sharp enough to be wrong? What in §2 is mis-stated or missing? What is the most likely way the paper over-claims? | this file, KNOWLEDGE, RETROSPECTIVE, PLAN6 §0–§1 and §9, knowledge/01–07 | `docs/reviews/M0_plan/REVIEW.md`, ≤ 2 500 words, a prioritised findings list first |
| **M1 — the account** | after J1–J2 | Is `01_claims_map.md` faithful to KNOWLEDGE (spot-check 10 claims against their files)? Is `02_literature.md` fair to each comparator's variant? Which claims would a hostile reader call over-stated, and what is the sentence that would survive? | the two docs, KNOWLEDGE, knowledge/07, the named `runs/` outputs | `docs/reviews/M1_account/` |
| **M2 — K1's pre-registration** | before K1's launch | Is the rule change complete (every place the terminal rule is read)? Are the predictions in §5 falsifiable as written? What confound does one seed under a new rule carry that the seed band does not cover? Should anything be measured in-run that cannot be recovered after? | §5, `uttt/batch.py`, `game.py`, `solver.py`, `exact.py`, the K1 diff and its tests | `docs/reviews/M2_K1/`; K1 does not launch until it is adjudicated |
| **M3 — the draft** | after J5 and K1's reading | Referee report, as for a venue: is each claim supported by the cited file at the stated level? Are the limitations complete? Is the contribution stated at the size the evidence supports? Recompute five numbers of the reviewer's choosing from the outputs. | `docs/paper/paper.md` and everything it cites | `docs/reviews/M3_draft/`, a report in referee form |
| **M4 — the final pass** | before submission | Adversarial: find the sentence that is false. Check every number in the abstract and the tables against its file. Check the rule variant is stated wherever a comparator is quoted. | the final manuscript, KNOWLEDGE, the outputs | `docs/reviews/M4_final/` |

Each stage's brief is written from the M0 template (Appendix A) with the question and the file list
changed; each is adjudicated in **§7e** (a table per stage, PLAN6 §1's columns) and rebutted once.

### 7d. Calibration: the first review's track record

Of REVIEW-astra's 22 adjudicated items (PLAN6 §1): the two instrument bugs (items 1–4) were **right
and important** — they changed three claims; the budget confound (15) was **right and decisive** — it
is where +204 Elo came from; the ownership grading (17) and the out-of-process evaluator (18) were
right and cheap; the RNG finding (13) had the **right fix and the wrong cause** (nondeterminism, not
evaluation, is why same-seed runs diverge); and the review's **headline recommendation — an exact-D4
trunk as "the next useful architectural experiment" (10) — was tested and hurt by 220 Elo**, with the
supervised gate that licensed it later shown to reverse. So: on *instrument and statistics* the
reviewer was reliable; on *architecture priority* it was confidently wrong. The second review's
findings are weighted accordingly, and its brief tells it so.

### 7e. Adjudications

*(One table per stage, appended as each review returns: `| # | review item | verdict | evidence / reason | lands in |`, then the rebuttal round's reply. Empty until M0 returns.)*

## 8. Not proposed

`--epochs 16` (≈ 32 h for a step predicted inside the seed band; PLAN6 §9). Any depth or width change.
A G-CNN at any width in self-play; the data-matched supervised test (≈ 40 h of labelling for a net the
equal-cost rule disqualifies). `--head_tying 1` (proposable, predicted null-to-small; not needed for
the paper). A CodinGame submission (the 100 KB limit). A two-open-board tablebase (a reachable-only
generation project; J4's curve is the cheaper form of the same statement). A third analysis pass on
`_e8` (I1 showed +40 is inside the drift of magnitudes; the N-tier's cheap re-reads in J1 are the
exception). A full solve.

## 9. Order, budget, GPU roles

| when | desk / this session | 3090 | 3060 |
|---|---|---|---|
| Day 0 (today) | PLAN7 committed; **M0 launched** (1–3 h, monitored) | idle | idle |
| Day 1 | M0 adjudicated (§7e), plan amended; J1, J2 (knowledge/07 merged); K1's rule flag and tests written; **M2 launched** on the K1 diff | idle | **J3** (≈ 1 h), then **J1's cheap re-reads** |
| Day 1–2 | M2 adjudicated; **K1 put to the owner** | — | **J4** on the CPU beside it |
| Day 2 → 3 | J5 skeleton; **M1 launched** | **K1** (≈ 22 h) if approved | the E7 worker (≈ 6 min per checkpoint) |
| Day 3 | M1 adjudicated; K1 done and read by §5's rules | idle | **K1's readings** (≈ 6 h: the I1 tool set under `draw`, the 2 × 2 cross-play) |
| Day 4 | Manuscript draft; §10's file updates; **M3 launched** | idle (L1 if bought) | idle |
| Day 5 | M3 adjudicated; revisions; **M4 launched**; the E11 copy if a destination exists | | |

The trainer never shares the 3090; reviews run while this session is otherwise idle; the 50 % line
applies to every launch (above it, update this file first and hand over).

## 10. Files this plan changes

- **This file** — the live plan; PLAN6 moves to `docs/history/PLAN6.md` when M0 is adjudicated and
  the owner adopts PLAN7 (`docs/history/README.md` gains its row; README's "Start here" points here;
  PLAN6's open item — E11's copy — is carried in this Handover).
- **`README.md`** — "Start here" (PLAN7 second, PLAN6 to history), "Current state" (the paper as the
  open item; K1 if it runs), the ladder table unchanged.
- **`knowledge/03-prior-art-uttt-ai.md`** — *done 2026-09-12:* a dated addendum to judgment (a)
  (pc29277) and the refreshed arena figures; the rest of the file stands as the 2026-08-29 sweep.
- **`KNOWLEDGE.md`** — the header gains the tier of each claim (one word per line, from §1a); 46, 49
  and 51 name the lever "sample reuse" beside `--epochs` (J6, a wording change); new
  lines from J3 (the empty board), J4 (the frontier), K1 (one per claim re-read: rule-invariant /
  rule-dependent, as I1 added held / moved / reversed); §10 updated.
- **`RETROSPECTIVE.md`** — §7 (where things stand); a §8 "what the write-up changed" if the drafting
  changes any reading.
- **`docs/explainer.html`** — Part 8 (the game beliefs) carries the +363 numbers and the reversal; the
  training story gains the update lever and the equivariance negative. Republished.
- **New:** `knowledge/07-literature-2026-survey.md` (the agent's survey); `docs/paper/{01_claims_map,02_literature,paper}.md`;
  `docs/reviews/M*/`; `runs/plan7/`; `CITATION.cff`'s title once the paper's is fixed.

## 11. Operational notes

- PLAN6 §8's notes stand (one CUDA device per process; the E7 worker is a `cuda:1` process; hidden
  launchers; the retry wrapper; a reboot is the one failure it cannot cover — Windows Update is
  paused to 2026-10-14).
- **codex-sp from this session:** dot-source `~/.codex/codex-functions.ps1` first (the PowerShell tool's
  shell does not load it); pass the brief on stdin with `-`; `--json` to a file for monitoring, `-o`
  for the review; note the session id for `exec resume`. Read-only unless a worktree is wanted. The
  reviewer inherits `~/.codex/AGENTS.md` (the generated one) — its brief should say that the
  repository's own documents override any general instruction there about how to work.
- The 3090 is the display adapter: ≈ 830 MiB and ≈ 10 % utilisation is its idle state, not a job.
- `runs/probe_gcnn_smoke/` stays untracked. E11's copy stays open until a destination exists.

## Appendix A — the M0 brief (saved as `docs/reviews/M0_plan/brief.md` at launch)

> You are the second outside reviewer of `uttt-zero`, a research project at this working directory:
> an AlphaZero-style agent for Ultimate Tic-Tac-Toe under the closed-board / most-boards rules (a won
> or full local board is closed; a player sent to a closed board plays anywhere; three boards in a
> line wins; otherwise more won boards wins; equal is a draw), trained on one PC, built to *analyse*
> the game. Your sandbox is read-only; do not try to write. Deliver the complete review as your final
> message in Markdown — no preamble — it is saved verbatim.
>
> **What you are reviewing.** `PLAN7.md`: the plan for writing the project up, at commit `<sha>`. Read
> in this order: `PLAN7.md` in full; `KNOWLEDGE.md` (the claims file — 55 claims, each with level, CI,
> nets, tool and file); `RETROSPECTIVE.md`; `PLAN6.md` §0, §1 (how the first review was adjudicated —
> you will be adjudicated the same way) and §9; `knowledge/01`, `03`, `06` and `07` (the
> literature — `07` is the September 2026 survey; it names the one prior AlphaZero on these rules); `docs/history/REVIEW-astra.md` §1 and §9 (the first review, for calibration: its
> instrument findings were right and important; its architectural recommendation was tested in
> self-play and lost 220 Elo). Results live in `runs/*/analysis.out`, `runs/plan5_*.out`,
> `runs/plan6/*.out|json`; recompute before you dispute a number. Skip `.venv/`, `runs/*/games/`,
> `*.pt`.
>
> **Answer, in priority order:** (1) §1's five tiers — is this the right partition of the claims, and
> is any claim in the wrong tier (say which, and why, with the file)? (2) §0's recommendation — one
> paper, the game as subject, training and measurement as its instrument — and the working title: right,
> and honest? What is the most likely way this paper over-claims, and the sentence that would survive?
> (3) §5, K1 — is a draw-rule twin the right single run? Are the pre-registered predictions sharp
> enough to be wrong? What does one seed under a new rule confound that the seed band does not cover?
> (4) §2 — what is mis-stated about any comparator (variant, number, source) and what comparator is
> missing? (5) §7 — is the staged review protocol sound, and what would you change in your own brief?
> (6) Anything in the plan that is wrong in the code or the logs.
>
> **Format:** a prioritised findings list first (severity; section or file:line; what is wrong; why it
> matters; the fix), then your answers to (1)–(6), then a short list of what is right and should not
> be changed. Cite file paths. Say when you are unsure and name the check that would settle it.
> ≤ 2 500 words. Depth over breadth. The repository's own documents override any general working
> instructions you were given about how to behave.
