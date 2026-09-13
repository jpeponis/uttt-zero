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
GitHub before it went in). **M0 done** — launched 19:54, returned 20:03 (564 s; `docs/reviews/M0_plan/REVIEW.md`,
2 106 words; session `01a0980a-d906-7c61-a884-52d315a082d8`): seven prioritised findings and ≈ thirty
specific corrections, **every one checked against the code or the logs here and adjudicated in §7e**
— accepted, with the plan amended in §0 (title, the novelty sentence, the form of every headline
number), §1a (the tiers restated as level / coverage / drift; nine claim-level corrections, three of
them now written into KNOWLEDGE), §2 (four comparator corrections and one added), §3, §4 (J3
redesigned, J4 gains a bounded solver), §5 (K1 gains a relabel control, the `_e8` parent re-read, a
common position set, numerical thresholds and an *unresolved* verdict), §6, §7 and §8. The J1
draft's independent tier check (the log's third entry) converged with M0 on every structural point.
The rebuttal round is next.

**What the next instance does, in order.** (1) *Done 2026-09-12:* `knowledge/07` merged into §2, §3
re-ranked (C1's claim reworded, §2c). (2) *Done:* M0 launched, returned in 564 s, adjudicated (§7e),
the plan amended. The **rebuttal round** (`codex exec resume`, the four questions §7e names) was cut
off by the owner's Codex five-hour usage limit at 20:28 and **relaunches itself at 00:30** from a
background job in this session (the log's 20:29 entry; by hand: `pwsh -NoProfile -ExecutionPolicy
Bypass -File docs/reviews/M0_plan/launch_rebuttal.ps1`); its reply is recorded under §7e's table
when it lands. **M2 is armed behind it**: a second background job launches
`docs/reviews/M2_designs/launch.ps1` in the same window once `REBUTTAL.md` exists (by hand: the same
`pwsh … -File` form); M2's brief is scoped to the K1 diff and the J3 / J4 designs, and its
adjudication in §7e gates J3, J4 and K1's proposal to the owner. (3) Phase J (§4) on the desk and
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
- **2026-09-12, 20:03 — M0 returned and is adjudicated (§7e).** `codex-sp exec` on `gpt-6-astra` at xhigh,
  read-only, from the repo root at `fc79a9e`: **564 s**, 4 152 498 input tokens (3 929 728 cached), 13 564
  output, 26 commands (≈ 584 KB read), 13 MCP tool calls — it fetched ten of the survey's sources itself
  (pc29277, SaltZero, leela-zero#1480, KataGo's SelfplayTraining.md and `search.cpp`, Wang et al.'s HTML,
  gPress, the Padua thesis page, two 2025 arXiv pages) — and recomputed the four headline Elo numbers from
  the raw paired records (99.600 / 63.659 / 40.242 / −219.908; they match). Two launches failed before the
  one that ran: `Start-Process` with an array `-ArgumentList` split the script path at the space in the
  user name; then `codex-sp exec … -` hung on stdin (0 CPU, 0 bytes) because a pipeline into a PowerShell
  *function* never reaches the native binary inside it — the working form is a one-line prompt naming the
  brief file and the child's stdin redirected from an empty file (§7a, §11). **Seven prioritised findings;
  eleven of its specific claims were re-derived here before any verdict was written** (§7e's evidence
  column): the tablebase read's corpus, the evaluator at every expanded leaf, the opening-sampling gate,
  the solver's missing budget, the margin label, the exact-label overwrite, the solver tie-break, three
  errors in knowledge/06, KNOWLEDGE 14's intervals from its own numbers, `_e8`'s 1 501 606 games and
  8.0109 reuse quotient from its log. All accepted, two with a change of reading. Three corrections went
  straight into KNOWLEDGE (14, 31a, 33), six into knowledge/06, one into knowledge/07.
- **2026-09-12, 20:05 — J1's draft claims map returned** (Opus, scratchpad only; 56 rows, every cited
  output file resolved). Its tier check, made without sight of M0, **concurs with M0 on every structural
  point** — the tiers overlap by construction, five S members lack four-net coverage, 35 is half N,
  42–51 are in no tier, the count is 56 — and adds: 21 moved with 20 (same tool, no CI); §1a's E
  headline numbers (100 %, 91.3 %) are `_e8`'s from claim 51, not 28–30's; three capsule numbers in §1a
  were re-rounded; KNOWLEDGE 14 quotes three different ranges for one residual; and **claim 6 read from
  `timeline.json`: `_e4` [40] 0.941 / 0.950 / 0.990 at iterations 20 / 30 / 300 (verified here), `_e8`
  [38] 0.343 at 20, then [40] 0.760 at 30 and 0.951 at 40** — "≥ 0.95 from iteration 20–30" holds
  marginally on `_e4` and arrives ≈ 10 iterations later on `_e8` (J1's reading; `tools/timeline.py`'s own
  line confirms it before it enters KNOWLEDGE). The draft is being revised to the three-column form.
- **2026-09-12, 20:29 — the rebuttal round hit the owner's Codex usage limit and is deferred to 00:30.**
  `codex-sp exec -s read-only --json -o … resume 01a0980a-…` from `417e105` at 20:21:08 — the resume
  worked (its brief read, 15 commands, ≈ 256 KB re-read, three web fetches: Wang et al.'s HTML and the
  paper through the research tool, pc29277's README) and it was recomputing KNOWLEDGE 14's intervals
  from the A4 / B3 files when, at 456 s, the stream ended in `error` / `turn.failed`: *"You've hit your
  usage limit … try again at Sep 13th, 2026 12:24 AM."* No `REBUTTAL.md`. The cause is M0 itself:
  one whole-repository xhigh review (≈ 4.15 M input tokens) consumes most of a five-hour window, and
  the rebuttal began 18 minutes after it. **A background job in this session sleeps to 00:30 and
  relaunches the same script** (`docs/reviews/M0_plan/launch_rebuttal.ps1`, which resumes the same
  session, so the reviewer's cache and context survive); by hand it is `pwsh -NoProfile
  -ExecutionPolicy Bypass -File docs/reviews/M0_plan/launch_rebuttal.ps1` from the repo root. Rule
  for the remaining stages (§7a): one review per five-hour window, and briefs that name files rather
  than let the reviewer read the repository whole.
- **2026-09-12, 20:30 — J2's draft related-work section returned** (Opus, scratchpad only; 2 504 words,
  eight sections, a 16-row comparator table) with eight places where knowledge/07 and PLAN7 §2 disagree
  on a number or its net. Fixed in §2a now: Elhage's root estimate is "a few hundred million CPU-hours"
  (≈ 3 × 10⁸), not ≈ 10⁸; the centre-board null quoted was deep10's (+0.01 ± 0.04), `_e4`'s is +0.032
  ± 0.044; the "74 % X score after [40]" is the deep10 / deep8_300 books' self-match column, which
  `_e4`'s book does not have. Fixed in §1b: "+204" is a sum of three matches — the *measured*
  head-to-head of the eight-pass net over the one-pass net of the same shape is +211 [+189, +232]
  (51), and the paper quotes that. knowledge/07: MiniZero's ratio stated two ways (≈ 1–1.3 in the table,
  ≈ 1.2 in the closing claim) and the settling ply quoted unqualified (36 is the held-out v2a games; 34
  is strong play) — both corrected. The draft itself was written before M0's corrections reached §2 and
  carried five struck statements (the "confounders controlled" form, the root-only symmetry identity,
  "no dose–response exists", the MOPNS paragraph, "every net 100 / 100 / 100"); it is being revised
  against §7e before adoption into `docs/paper/`.
- **2026-09-12, 20:40 — J1's revised claims map returned:** 59 rows (56 claims; 31, 33 and 35 split
  where level *and* coverage differ; 11, 14, 21, 23, 30, 32, 37, 42 carry compound drift cells), **22
  judgement cells enumerated** for the human check, four cells read from files rather than KNOWLEDGE
  (6's `_e8` series from `timeline.json`; 28–30's `_e8` lines from `analysis.out`). Two findings:
  **KNOWLEDGE 30's sealed half has no reading above +242** and `endgame_v3_test` is still sealed —
  J1a (§4) pre-registers its one read on `_e8`; and KNOWLEDGE's §1 note still said "no other sign or
  ordering changed" against 32's motif swap — corrected now (with 5's reply move after [2] noted
  beside it). The map is adopted into `docs/paper/01_claims_map.md` after a read, as the draft M1
  reviews; its judgement cells are M1's first question.
- **2026-09-12, 20:37 — J1a done: `endgame_v3_test` read once on `_e8`, as pre-registered.** Sealed
  half: raw WDL **92.7 [91.8, 93.6]**, draws 85.3 %, regret **0.027 [0.021, 0.034]**, 256-sim search
  **99.9 [99.8, 100.0]** optimal (48 s on the 3060). The dev half of the same s1-derived split,
  `endgame_v3_dev`, read beside it for a like-for-like pair: **91.6 [90.6, 92.6]**, draws 83.6 %,
  regret 0.024, search 100.0 % (83 s). Against the pre-registration: regret and search inside their
  bands; WDL +1.0 over `endgame_v2_dev`'s 91.7 — at the band's edge, on the high side, and the two
  sets are different corpora. The reading that matters is the pair: **dev and sealed agree to 1.1
  points on one corpus, the sealed half higher** — claim 30's structure at the top of the ladder,
  and the opposite of what a flattered development set gives. KNOWLEDGE 30 and §10 carry it; no
  sealed endgame set remains. `runs/plan7/J1a_endgame_v3_{test,dev}_e8.out`.
- **2026-09-12, 20:55 — J3 / J4 engineering merged (`934113a`); J2's revised related-work section
  adopted.** The Opus agent's worktree work — `solve_bounded`, `tools/frontier.py`,
  `tools/empty_board.py`, `tests/test_solver_bounded.py` — read (the bounded kernel's abort unwinds
  before any value reaches the alpha-beta logic; `solve()` is byte-identical), committed in the
  worktree, merged, its test re-run on `main` (ok, +1.8 %), the worktree retired. Two findings from
  J3's smoke go to M2 (§4): two floors, and **`gumbel_scale` absent from `config.json`** — every run
  trained at 1.0, a provenance gap E8 missed, closed for K1 (§5); arm (b) as first specified replays
  lines (4 distinct of 16, 1 up to symmetry). The empty board reads +0.5087 for X at 256 sims with the
  corner-board principal line (16 384 sims in the real run, after M2). J2's revision landed with all
  nine §7e changes made and funded by cuts that drop no claim; adopted as
  `docs/paper/02_literature.md` (2 603 words), the draft M1 reviews. Still in flight: K1's `--rule`
  worktree and the 00:30 rebuttal.
- **2026-09-12, 21:20 — K1 engineering merged (`781dfca`); the bounded solver given the rule; M2's brief
  written.** The K1 agent's worktree (fast-forwarded by it to `417e105`, 30 files, 45 minutes of tests)
  committed and merged; the one conflict, `uttt/solver.py`, resolved by making the two agents' changes
  one design — `_negamax_bounded` takes the same `draw_rule` flag as `_negamax`, `solve_bounded` and
  `solve_children_bounded` take `rule` — and `tests/test_solver_bounded.py` now asserts equality under
  `draw` too (90 of 500 values differ from `count`: the flag reaches the kernel). `test_solver`,
  `test_exact`, `test_endgame`, `test_tablebase` pass on the merged tree; `test_rules.py` is re-running
  (≈ 10 min). Its report also found `tests/test_symmetry.py` failing — characterised here as
  device-specific, `cuda:1` only, the process-global capture stream (§11). §5 records what is not yet
  threaded and must be before K1's readings (five I1 tools). `docs/reviews/M2_designs/brief.md` and
  `launch.ps1` are written; M2 launches in the Codex window after the rebuttal.

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
reader believe either. A methods-only paper would discard the part that is unique. The working title,
after M0 (which found that "knows" invites confusing agreement with truth and that the bare game name
hides the variant): *"A strength-audited self-play analysis of closed-board, most-boards Ultimate
Tic-Tac-Toe."* The first form — *"What a strong self-play agent knows about Ultimate Tic-Tac-Toe, and
how much of it survives getting stronger"* — is withdrawn.

**What the evidence cannot support, said first so the paper never says it.** The game is unsolved
and this project does not change that (knowledge/06: 10³³–10³⁸ positions; Elhage's DFPN at ≈ 20 ply
in hours). Every game claim is *search-relative*, *behavioural* or *predictive* unless marked *exact*;
"the best first move" means "at 1k–16k simulations on four nets spanning 150 Elo", not a theorem. One
ordering has already flipped with strength (claim 7); the paper's central methodological claim is
that the *rest* did not, and the honest form of that sentence is "orderings and signs survived 120
Elo with one exception, and magnitudes did not saturate" — not "stable". **Every regression coefficient is an
adjusted association on a named corpus with a named estimator** — the free move is "+0.195 utility
on 30 000 natural positions against the 256-simulation search estimate, game-clustered 95 % interval
≈ ± 0.028", not a price with everything else controlled and not an exchange rate against boards or
threats; an insignificant coefficient is "no resolved residual in this regression", never "no
effect"; optimality on solved samples is that, never a solving milestone (M0). The architecture
result is "this equal-cost D4 implementation lost under this recipe" in the headline; the mechanism
evidence (48, 50) is stated as consistent with capacity, not as its proof. No "first AlphaZero on
these rules" claim: `pc29277/AlphaZero_UTTT` (2026-08-19) is one — 28 544 self-play games in
22 T4-hours against a depth-3 alpha-beta, where `_e8` played 1 501 606 games in 22 3090-hours, ≈ 53×
the games and roughly an order of magnitude the compute, not two (M0). What is first here is
*defined*, not asserted by exclusion: a strength scale anchored by an independent search sharing no
code (the rollout UCT) on a fixed paired suite, replicated across seeds with a measured band, read by
a pre-registered rule — and the agent used to produce game knowledge (knowledge/07 §2.2). No "strongest public agent"
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

This section is the investigation's first product: the **56** claims of `KNOWLEDGE.md` (1–51 and 7a,
31a, 38a, 41a, 41b; an earlier count said 55) sorted by the evidence behind each. **M0 found the first
form of this — five tiers in one column — was not a partition**: it mixed evidence *source*, drift
*status* and measurement *coverage*, so 31a, 32 and 33–34 sat in two tiers at once and compound claims
hid a reversed component (11's training path); J1's independent check found the same misses. It is
restated: **every claim carries three columns** — its *level* (exact / solver-anchored /
search-relative / predictive / behavioural / descriptive / decodability / supervised / single run
against a named parent), its *coverage* (the actual checkpoints, seeds, architectures and corpora it
was read on — never a category), and its *drift* verdict at the last re-read (compatible / magnitude
changed / sign or order changed / unresolved / not measured). "Compatible" means inside the earlier
interval — a descriptive rule, not an equivalence test; where precision differs the paper compares
on identical positions with a by-game bootstrap of the difference. The authoritative table is
`docs/paper/01_claims_map.md` (J1). The table below keeps the audit's shape — **E is now a level, and
every claim in it also carries a drift verdict** — with the corrections M0 and J1 made listed under it.

### 1a. About the game: the claims by level, coverage and drift

| group | meaning | claims | what the paper does with them |
|---|---|---|---|
| **E — exact** | checked against the solver or the one-open-board tablebase | 28 (search 99.7–100 % optimal on solved samples), 29–30 (raw head names the exact result: 84.6 → 91.3 % across the ladder; the sealed half agreed within 0.3), 31 (draw recognition was optimisation, not capacity), 31a (the one-open-board phase: 100 / 100 / 100 on every net), 32 (what the raw policy still gets wrong late: the count rule and tempo, 2.1 → 1.0 %), 33–34's solver columns (the optimal move sends the opponent to a winnable board 69–70 % of the time; never to an immediate macro win when not already lost) | stated as facts about positions sampled from strong play, with the sampling stated; never as "solved" |
| **S — stable** | sign and ordering held on all four strong nets *and* the last re-read's magnitude sat inside the earlier CI (I1's "held") | 1 ([40] best, [13] worst, 12 of 12 columns), 8 (a free move +0.195 ± 0.028 — deep10's number to the third decimal), 11 (the raw head over-credits it by ≈ 0.09, three nets), 13 (a macro threat ≈ +0.15 / −0.14, four strengths), 17 (line counting learned by iteration 10–20 and never moves), 19 (an opponent's local threat ≈ −0.09), 21 (X wins settle at 32, O wins and draws at 39–41), 26 (96 % of draws are 4–4 with one full board), 31a, 33–34 (the folk rule is false as a rule; the true rule is macro-immediate), 35 (conceding the centre is a null once lines are controlled), 36 (the encoding exposes the obvious concepts; a random net reads them at 98–100 %), 38 (tactics shallow and early, value deep and late), 40 (the ownership head learns late ownership, 68–71 % vs 50 % baselines; switching it off was a strength null) | the core of the game section; each quoted with all four nets' numbers |
| **M — moved** | sign and ordering held; the magnitude on the +363 net fell outside the earlier CI, in the direction strength has always pushed it (I1's "moved") | 2 (τ vs v2b 0.96 → 0.85: the opening sharpens), 3 (X's edge after [40] +0.28 → +0.354 → +0.447 → +0.495 and still rising), 4–5 (fewer flat replies, wider best-to-worst range, a new non-[40] sharp reply after [2]), 7a (the self-send 55 / 58 → 48 % — still the most common reply, no longer a majority), 9 (the conditional free-move coefficient 0.43 → 0.60 of the unconditional), 10 (a free move worth most late and when ahead; the middlegame now runs with the count), 14 (the per-board residual +0.02 … +0.08 and not growing), 16 (the raw board count discounted further, +0.037 → +0.022), 20 / 22 (settling median 36 → 34 on strong play; the ply-0 caveat grows to 21 %), 23 (policy–search disagreement 34 → 31 %, the value gap unchanged at 0.19), 24 (X 63 / O 21 / draws 16.6 %: X flat since deep10, draws still rising out of O's column), 25 (the count rule decides a third of games, not a quarter — flat for 250 Elo, then +6 points in 120), 27 (52.8 plies, 5.1 free moves per game, both climbing), 32 (failures halve again), 37 (the same probe grid learned 20–50 iterations earlier), 39 (the trunk carries a little more of the line ahead) | stated with the trajectory, not a point: "X's edge after [40] has risen at every strength measured and has not saturated" |
| **R — reversed** | an ordering flipped between +242 and +363 | 7 (after [40], `_e4` puts 0.71 of its visits on the corner reply orbit 36 where deep10 put 0.75 on the edge orbit 37, and rates the edge subtree +0.022 better where the earlier nets rated the corner +0.016 better; its atlas agrees at 1k, 4k and 16k). The two lines were within 0.02 of each other on every net. | the most important line in the game section: it is what the strength-drift test is *for*, and it lands where the method said a reversal could — on a near-tie. uttt.ai's prose ("O's best reply pushes play into a corner board") agrees with the stronger net, §2a |
| **N — not re-read at +363** | read on deep10 (and often deep8_300 / the replicate) but its tool is not in I1 | 6 (the opening is learned first: ≥ 0.95 on [40] by iteration 20–30), 12 (tensor edits overstate the free move 2×), 15 (which board class is worth most — unresolved on three nets and read as noise), 18 (a dead open board is worth nothing), 38a (which concepts the trunk computes vs merely re-formats: dead boards, exact value, best move survive the non-linear control; threats and the immediate win do not), 41 / 41b (residual asymmetry 0.027 bits; the 8-way average +35 / +32 at 8× the cost, −201 at equal compute; exact canonicalisation a null, deep10 and `_e2`), 41a (a legible surrogate reproduces 41 % of the search's moves and none of its strength, −661 vs v2b) | quoted from the nets they were read on, marked as such; J1 decides which are cheap to re-read on `_e8` and does those |

**Corrections from M0 and J1 (2026-09-12), each verified here in the file named.** 31: the
*measurement* (draw recognition against the solver) is exact; the *diagnosis* — optimisation, not
capacity — is inference and leaves E. 31a: the tablebase is exact and the nets' sampled accuracy is a
different fact; "100 / 100 / 100 on every net" was wrong (v2b 99.0 / 99.6 / 100, dev1 94.0 / 98.7 / 100
— strong nets only), and `_e4`'s 689 positions come from *deep10's* corpus,
`runs/probe_data_deep10late_e4.npz` (KNOWLEDGE 31a corrected). 11: the end-of-training gap is
compatible but the training-path component *reverses* on `_e4`; the row must show it. 14: only the
corner leaves deep10's interval — centre 0.049 ∈ [+0.030, +0.110], edge 0.038 ∈ [+0.029, +0.083] — so
"every one of them below" was false (KNOWLEDGE 14 corrected); its three quoted ranges (+0.03 … +0.08 /
+0.02 … +0.08 / +0.02 … +0.05) are reconciled in J1. 32: the failure *rate* moved and the second and
third motifs *swapped* (holding a draw overtook giving a free move) — "one reversal" holds only for the
primary orderings the paper enumerates, never for "every ordering in the file". 6: not N —
`timeline.json` carries `first_top_share`: `_e4` [40] 0.941 (iteration 20) / 0.950 (30) / 0.990 (300),
verified; J1 reads `_e8` at [38] 0.343 (20), [40] 0.760 (30), 0.951 (40) — "≥ 0.95 from iteration
20–30" holds marginally on `_e4` and arrives ≈ 10 iterations later on `_e8` (confirmed by
`tools/timeline.py`'s own line before it enters KNOWLEDGE). 35: "no resolved residual in this
regression", not "costs what its lines cost, no more"; its counterfactual half is N. 33–34: the solver
column is a property of the position set and the rate of *one* optimal policy — `tools/probe.py
exact_pv3` takes the lowest-indexed optimal move — not of necessity (KNOWLEDGE 33 corrected). 21: read
with 20 (same tool, the same 2-ply shift on strong play, no CI) — what held is the ordering X < O ≈
draws, not the plies. Coverage: 8 (deep10, deep8_300, v2b, `_e4` — not s1), 26, 33, 35, 36 and 40 were
read on two or three nets, not "all four"; the map records the actual list. 42–51, the training claims,
get rows of their own: level *single run against a named parent on the full suite at ± 2.8, seed band
≈ 3* (46, 49, 50, 51), *supervised, dev slice* (47, 48), ladder readings (43–45); the strength they
"held at" is the parent's. The E group's headline numbers (100 %, 91.3 %) are `_e8`'s from 51, not
28–30's, which stop at deep10 — J1 copies `_e8`'s lines down. Three capsule numbers in the table were
re-rounded (19's −0.09 for −0.10; 3's chain dropped deep8_300's 0.455; 14's range): **the manuscript
quotes KNOWLEDGE, never this table.**

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
- **The lever the field sets near 1: the sample-reuse ratio** — optimizer samples per generated position
  (`n_steps = epochs · games · steps / batch`, so `--epochs` *is* the ratio; Lc0 names it the sampling
  ratio, and Lc0 and KataGo are the only systems that publish theirs). One pass was the project's
  default for a week and the field's practice. Two passes: +100 Elo for +1.3 h of training. Four:
  +64 more. Eight: +40 more, with each generated row drawn about eight times, the sampled distinct
  fraction down to 0.45, and *nothing complaining* — replay age, skipped steps, losses and self-play
  statistics all unchanged (46, 49, 51). The three steps sum to +204; the *measured* head-to-head of
  the eight-pass net against the one-pass net of the same shape is **+211 [+189, +232]** (51), and
  the paper quotes the measurement, not the sum. The supervised twin says the same: for a fixed teacher the fit
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
three guards, and a claim is stated only where all three were passed; (vi) a coefficient is an
adjusted association on a named corpus with a named estimator and its game-clustered interval, and
the headline carries all three, not only the caveat (M0).

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
| Best first move | Centre-centre, "undoubtedly the best move" — uttt.ai's prose; gPress's uttt.ai scores CC +11.81 > centre-corner +11.07 > centre-edge +8.16 > corner-of-same-corner +6.47 > corner-of-opposite-corner +6.12, every edge-board opening "bad" — five of the 15 orbits, on uttt.ai's undocumented internal scale (closed / **draw**); royerk's rollout MC puts centre at ≈ 52 % (CG rules) | [40] +0.495 > [36] +0.395 > [0] +0.309 ≈ [37] +0.305 > [5] +0.254 > [8] +0.232 > … > [9] +0.039 > [13] −0.079 at 16k on `_e4`; rank 1 and 15 fixed in 12 of 12 columns; τ 0.85–0.96 across 340 Elo (1–3; `runs/plan6/I1_A1_atlas.out`) | **Agrees on the top two and on "edge-board openings worst"** ([13], [9], [15], [16] are the four lowest). uttt.ai has centre-edge third and corner-same fourth; here [0] and [37] are within 0.004 and swap with budget — the one place the two orderings differ is within noise here, and gPress's scale carries no uncertainty, so nothing is said about a tie *there* (M0). Extension: 15 orbits × 3 budgets × 4 nets with the drift stated, where the literature has one engine's undocumented scale |
| O's reply to [40] | "O's best reply pushes play into a corner board, and the next ≈ 8 moves stay in the corner boards" (uttt.ai prose, draw variant) | deep10 and deep8_300 prefer the *edge* reply (0.75 / 0.54 of visits); `_e4` prefers the *corner* orbit 36 (0.71) and its PV after [40] is `36, 0, 8, 80, 77, …` — corner boards for eight plies (7; `runs/book_deep8_e4.json`) | **The strongest net agrees with uttt.ai; the two weaker strong nets did not.** This is the one reversal, and an independent engine sits on the stronger side of it. The paper says so |
| First-player advantage | "P1 has a 60 % winrate" among Legend bots (darkhorse64); random play 50.9 / 7.2 / 41.9 (snowfrogdev, CG rules); "either P1 wins or a draw can be forced" (jacek, an impression) | Self-play with exploration: X 62.7 / O 20.7 / draws 16.6 % at +363 (24); the paired-suite X score by opening — 74 % after [40], 45–51 % after [9], [8], [13] — from the deep10 / deep8_300 books' self-match column, which `_e4`'s book does not have (its `--paired` file is the parent match; 7); the root after [40] reads +0.495 utility ≈ 75 % expected score at 16k | Same order as the arena's 60 %; **extension: conditioned on the opening and on strength, with CIs, and the draw share separated** — the literature has no side-conditioned numbers from a strong agent |
| Draws and the tiebreak | SaltZero vs the #2 CG bot: +65 =96 −39, **48 % draws** (closed / draw); Daporan's 2018 objection that the most-boards rule lets P1 "collect small boards"; nobody quantifies how often the count decides a game | 16.6 % drawn at +363 and rising with strength; **a third of games reach the count** (16.5 % decided by it, 16.6 % equal) — flat at a quarter for 250 Elo, then +6 points in the last 120 (24–25); 96 % of draws are 4–4 with one full board (26) | **New:** the first measurement of what the tiebreak does at strength. §5 buys the comparison under the same agent |
| Game length | uttt.ai self-play 40–50 plies; FLAIRS 2022 "at least 30"; CG folk 50–60 | 52.8 plies (p10 47, p90 59), lengthening with strength; 5.1 free moves per game, 98.5 % of games contain one (27) | Consistent; extension: the distribution and its drift |
| The free move | "Very powerful" (uttt.ai); "don't give up free moves for free" (gPress); a heuristic weight of 2 vs 5 for a board win and 10 for the centre board (BoardGameGeek); no quantification anywhere | **+0.195 ± 0.028 utility** with everything else controlled, the same to 0.004 on three strong nets; ≈ +0.08 … +0.12 with the immediate macro win in the model; largest late and when ahead (+0.30 at plies 44–50); the raw head over-credits it by 0.09 (8–11) | **New, and the paper's cleanest single number — stated as an adjusted association, not a price** (§0). Beside the folk weights: in the same regression the free-move coefficient (+0.195) exceeds the own-board residual (+0.02 … +0.08) and is of the order of a macro threat's (+0.15); no exchange rate is claimed |
| "Never send them to a winnable board" | Universal folk advice; Elhage's rigorous version (never send to a board where one move wins *the game*) | The strong move does it 24 % of the time and the **optimal** move 69–70 %; the optimal move never hands an immediate macro win when not already lost (33–34) | **The folk rule is false as stated and Elhage's is the true one** — confirmed against the solver, not against an agent |
| The centre board | HUJI weights 10 (centre) vs 3 (corner); "an enduring advantage" (gPress); the Orlin gambit | With lines controlled, the opponent owning the centre is +0.01 ± 0.04 on deep10 and +0.032 ± 0.044 on `_e4` — no resolved residual in this regression; the raw head's *counterfactual* centre premium (+0.11 over a corner) is the fourth line through it and was not re-read (35, 15) | The premium is line-counting in disguise |
| Solved status | Bertholon 2020: X wins in ≤ 43 (**open-board** rules — a different game); Elhage: ≈ 20-ply positions in hours, the root at "a few hundred million CPU-hours" (≈ 3 × 10⁸; $2–10 M) (closed / draw); nothing for the most-boards rule | Exact from ≤ 14–16 empties in ≈ 0.04–0.2 s per position (3 000 positions in 2–9 min); the one-open-board phase solved outright; the agent 100 % optimal at 256 sims on every solved sample (28–32, 31a) | Not a solution and not a milestone: **J4 reports solvability *conditional on games alive at each ply* under a stated node budget, and optimality *conditional on solved*** (M0); the count tiebreak is win / draw / loss for the mover, so draw-aware PNS suffices (knowledge/06 corrected) |
| Exploitability | D'Alberton 2024/25 (MSc, Padua; the variant is still to be verified — the page could not be retrieved by M0): best-response training finds "significant vulnerabilities in self-play agents" | Not measured; the stability argument rests on agreement among four *related* nets | **Missing from the argument and added to the limitations (M0):** agreement within one agent family is not adversarial validation; a best-response probe of the play agent is proposable, not proposed |

### 2b. Comparators on the method

| topic | the literature says | this project measures | reading |
|---|---|---|---|
| Sample reuse (optimizer samples per generated position) | Published practice clusters at ≈ 1: AlphaZero ≈ 0.5–0.7 (30 games per minibatch; Lc0's wiki computes 0.69 / 0.48), AlphaGo Zero ≈ 1.4, ELF OpenGo ≈ 0.8, Lc0 0.5–14 over its history settling near 1, KataGo ≤ 4 ("conservative"), MiniZero ≈ 1–1.3, pgx 1 (knowledge/07 §4.1; the AGZ / AZ / ELF / MiniZero figures are the survey's conversions, ± 30 %). The two explicit experiments warn *against* more: ELF, "decreasing this ratio significantly below 10:1 hinders training (likely due to severe overfitting)"; Lc0 at ≈ 12× reuse over-fitted its value head. Wang et al. 2020 (6×6 Othello, ep ∈ {5, 10, 15} passes over the *whole buffer*): the inner-loop knobs "should be set at lower values". The project's own recipe card said "~1–2" | 1 → 2 → 4 → 8: **+100, +64, +40 Elo**, monotone, no over-fitting signature at eight (46, 49, 51); the supervised twin: fit is a function of steps, not positions (47) | **The curve sits above the range published practice uses, in a regime the one prior sweep did not measure.** Wang et al. is reconciled, not contradicted: their *lowest* setting (5 passes over a buffer) is above this project's *highest* (8 passes over the new data ≈ 1.05 passes over the 7.6-iteration window) in reuse units — jointly consistent with an optimum between and a broad plateau, and both refute "≈ 1 is principled". The concept's home is model-free RL's replay / update-to-data ratio (Fedus 2020; Nikishin 2022; D'Oro 2023 — where high ratios need resets; here they need nothing), but Wang et al. *is* a published epochs sweep with tournament Elo, so "no dose–response exists" and "the lever nobody pulls" are withdrawn (M0): with their default 20-iteration replay history, ep = 5 / 10 / 15 passes over the buffer is ≈ 100–300 uses per position — a conversion the rebuttal round confirms — a regime above this project's 8, and KataGo's documentation *permits* raising its 4. The honest contribution: a positive, local 1 → 8 sweep under a documented recipe with a pre-registered rule and a seed band, in a regime nobody measured; the paper's second contribution |
| Scaling | Jones 2021 (AlphaZero on Hex): ≈ 500 Elo per decade of total training compute, ≈ 150 per doubling; Neumann & Gros 2022: strength a power law in parameters and compute on Connect Four / Pentago, published models "significantly smaller than their optimal size" | +100 / +64 / +40 per doubling of the *training half only* (self-play cost unchanged); width +37, depth +23 then inside the seed band | At this regime (9×9, 2.46 M parameters, 8× reuse still paying) the project is update-limited, not parameter-limited — stated as a regime, not as a contradiction of the scaling law |
| Symmetry | The prior is that equivariance buys sample efficiency (Cohen & Welling 2016; Carroll & Beel 2020 for board games — unnumbered, supervised, no peer-reviewed version found); VISA-VIS: augmentation halves value generalisation error; the one self-play test, **SLAP on Gomoku** (Suen & Alonso 2023): a supervised 8× data saving that "was not yet evident" to speed up RL. What the strong systems do: AlphaGo Zero, Leela Zero, KataGo **augment 8× with an ordinary CNN**; KataGo additionally averages the policy over symmetries at the search root, with no Elo figure published for it; REVIEW-astra §5.3 recommended an exact-D4 trunk as "the next useful architectural experiment" | Exact D4 trunk at equal cost **−220 Elo** (50); at equal parameters 7.0× the cost and memorising (48); tied heads' supervised margin closes slowly and does not reverse; canonicalisation a null at play (41b); the 8-way root average **+35 / +32 Elo at 8× the inference, −201 at equal inference** (41) | **Augment, do not enforce** — the first measurement of an exactly equivariant trunk in a full self-play run at matched inference cost, a clean negative with a mechanism (a small-step advantage that reverses; capacity, not LR), and the equal-cost vs equal-parameter distinction the equivariance literature rarely draws. 41's +35 is a *full-tree* 8-way ensemble — `SymmetryAveragedEvaluator` averages policy and value, and the search calls it at the root *and at every expanded leaf* (`uttt/search.py:181`, `:250`) — so it is **not** KataGo's root-only trick; that identity is withdrawn (M0), and the measured ensemble result with its equal-inference control stands (knowledge/07 §4b, gap 8) |
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
paper cites it — its README has paired openings, fixed opponents and confidence intervals, so
"calibrated" is *defined* (an independent search anchor, a replicated seed band, a pre-registered
rule; §0) rather than claimed by exclusion — and claims first *used to produce game knowledge*. *Extends with numbers nobody had:* the full first-move orbit table with drift; the reply
reversal; the free move's value and its conditional structure; the count rule's share and its rise;
the draw anatomy; settling plies; the failure-motif ordering of the raw policy; the sample-reuse
dose–response; the equivariance negative with mechanism; the Elo of a full-tree symmetry ensemble
against its equal-inference control; the four-net probe replication; a surrogate's residual in Elo.
*Sits outside published practice:* sampling ratios near 1 (ELF, Lc0, KataGo's conservative 4), with
Wang et al.'s sweep in a higher regime than this project's; the priority the first review and the
equivariance literature give to exact symmetry. *Corrects itself:* "the choice of
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
  ply, the fraction the solver completes within a fixed budget, and the agent's optimality there. Gives,
  per ply, the solved fraction *conditional on games alive at that ply* under a stated node budget
  (an unfinished search returns *unknown*) and the agent's optimality *conditional on solved* — a
  measured curve, not a milestone and not "solved from ply N" (M0). Needs a bounded solver first (J4);
  its design is reviewed in M2. No approval needed.
- **C4. The sample-reuse dose–response and the equivariance negative — already in hand, free.** The
  second contribution. The fourth point on the curve (`--epochs 16`) is not proposed; the paper
  states the three and their supervised twin and stops.
- **C5. The empty board's value and the side split under greedy play — an hour on the 3060 (J3).**
  One quotable number ("+0.50 utility for X at 16k simulations on the strongest net, and rising with
  strength") and the X / O / draw split without exploration noise. Cheap; clarifies 24's exploration
  caveat.
- **C6. External calibration — days of desk, GPU-hours (§6).** Places the ladder against outside
  opponents — an *independent algorithmic baseline* (L1) or the one *externally rated* opponent (L2,
  transitively through its 2020 match); only the latter touches the arena's scale (M0). The field has
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
  strength, the file. Three columns per row — level, coverage, drift — as §1a now specifies (the first draft's
  single tier column is replaced). 6 is read from `timeline.json` for free (§1a's corrections); 12, 15,
  18 and 35's counterfactual half are one `probe_value.py` run on the 3060; 28–30 gain `_e8`'s lines
  from `runs/deep8_c1_300_e8/analysis.out` (already quoted in 51); 38a and 41–41b need an MLP fit and
  paired GPU matches and stay quoted as read. KNOWLEDGE 14's three ranges are reconciled here.
  **J1a — one sealed read, pre-registered here and done once.** J1 found that KNOWLEDGE 30's sealed
  half, `endgame_v2_test`, has no reading above +242 (`_e4`'s and `_e8`'s `analysis.out` read v1 and
  v2_dev only), and that `suites/endgame_v3_test.npz` — PLAN6 E10: 3 000 solved positions from s1's
  iterations 280–299, split from its dev half by source game, held out for the deep8 family, **never
  read** — is still sealed. It is read **once, on `deep8_c1_300_e8/net_0300.pt`**, with `tools/endgame.py
  eval` at the standard settings (raw head; 64- and 256-sim search), logged in KNOWLEDGE 30 and §10 and
  in this log, and is a development set thereafter. Pre-registered: raw WDL within 1.0 point of
  `endgame_v2_dev`'s 91.7 %, regret within 0.010 of 0.020, the 256-sim search ≥ 99.9 % optimal; a
  miss beyond any of those is the finding, not a nuisance. ≈ 5 min on the 3060. *Done 20:34–20:37
  (`runs/plan7/J1a_endgame_v3_test_e8.out`, `…_v3_dev_e8.out`):* sealed **92.7 [91.8, 93.6]**, regret
  **0.027 [0.021, 0.034]**, 256-sim search **99.9 [99.8, 100.0]** — regret and search inside their
  bands, WDL at the band's edge and on the high side (+1.0 over v2_dev's 91.7, a different corpus);
  the like-for-like dev half of the same split reads **91.6 [90.6, 92.6]**, so dev and sealed agree
  to 1.1 points on one corpus, the sealed half higher. Claim 30's structure holds on the strongest
  net; KNOWLEDGE 30 and §10 carry it. No sealed endgame set remains. *Output also:* the list of every claim that the manuscript will quote, in order,
  which is the manuscript's outline.
- **J2. The literature table, final.** `knowledge/07` merged into §2; `docs/paper/02_literature.md`
  as the paper's related-work section with every comparator's variant stated. Any comparator the
  survey finds that bears on a claim is added to that claim's KNOWLEDGE line as a one-clause note
  ("uttt.ai's prose agrees").
- **J3. The empty board (C5) — redesigned after M0.** The first design ("2 000 greedy games") was
  defective: with sampling off the search is deterministic and repeats one trajectory; with it on,
  `sample_moves` / `temperature` gate the opening sampling, not the Gumbel scale
  (`uttt/search.py:308–318`). Three measurements on `deep8_c1_300_e8` and `_e4`, symmetry-averaged:
  (a) the root value of the empty board and its deterministic principal line at 16 384 sims — one
  number and one line, reported as search-relative; (b) 2 000 games at 256 sims with the search
  policy sampled proportionally for the first 4 plies and the uniform floor *off* — the X / O / draw
  split under near-greedy play; (c) 2 000 games at 256 sims under the self-play exploration settings
  (floor on, `sample_moves` as trained) — so (b) − (c) is exploration's contribution at a matched
  budget. Pre-registered: (b)'s split is compared with 24's; the design is reviewed in M2 before it
  runs. ≈ 1.5 h on the 3060. *Engineering done 2026-09-12 (merged as `934113a`; `tools/empty_board.py`;
  the implementer's fourteen design choices are `docs/reviews/M2_designs/J3J4_design_notes.md`, M2's
  material).* Smoke (16 games at 32 sims, root at 256): (a) the empty board reads **+0.5087 for X**
  with the principal line `40, 36, 0, 8, 80, 77, 50, 48, 34, 66` — the corner-board line; (b) X 81 /
  O 0 / draw 19 % over **4 distinct games of 16, 1 up to symmetry**; (c) X 44 / O 38 / draw 19 % over
  16 distinct. Two findings for M2: **there are two floors** (`sample_uniform` on the sampling
  distribution, `root_prior_floor` on the tree itself), and **`gumbel_scale` is not in `config.json`**
  — `train2.py` never sets it, so self-play ran at `MCTSConfig`'s default 1.0, root noise at every ply.
  Arm (b) as specified is deterministic after ply 4 and replays a handful of lines, so its interval is
  optimistic by exactly the duplication the tool now reports. M2 decides whether (b) keeps more
  sampled plies with the floors off or bootstraps over distinct lines; the four knobs that differ
  between (b) and (c) are stated in the output.
- **J4. The exact frontier (C3) — with the engineering M0 identified.** `uttt/solver.py solve()` has
  no node budget (its docstring says so): add `solve_bounded(…, max_nodes)` — the Numba negamax checks
  the node counter and unwinds, returning *unknown* — with a test that bounded and unbounded agree
  wherever the bounded one resolves. Then, from `deep8_c1_300_e8`'s late games, 500 positions at each
  ply from 40 to 70, budget 10⁸ nodes; record per ply the fraction solved *among games alive at that
  ply*, the median nodes, and the 256-sim search's optimality *on the solved ones*. The statement is
  conditional at both ends, never "solved from ply N". CPU, unattended, hours; design reviewed in M2.
  Output `runs/plan7/J4_frontier.{json,out}`. *Engineering done 2026-09-12 (merged as `934113a`):*
  `solve_bounded` / `solve_children_bounded` in `uttt/solver.py` — a copy of the kernel with an
  unwinding abort that never reaches the alpha-beta logic, `solve()` untouched;
  `tests/test_solver_bounded.py`: identical value *and node count* on 500 positions, a completed
  bounded search correct at budgets 10 / 10³ / 10⁵, +2 % cost — and `tools/frontier.py`, whose field
  names carry the conditioning. Smoke at plies 60–62 (10⁶ nodes): 100 % solved, 100 % optimal; at
  plies 40–42 with 2 × 10⁵ nodes, **8 → 17 → 50 % solved** — the selection effect the names exist
  for. Budget semantics: one `max_nodes` for the position and its whole child enumeration (the grading
  needs every child). Grading uses the plain evaluator, as `endgame.py eval` does; J3
  symmetry-averages — the asymmetry is deliberate and documented. Real cost ≈ 6.5 min per ply,
  ≈ 3.5 h for plies 40–70, after M2.
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
(`--rule`, default `count`); `config.json` `_provenance` records it. Added after M0:
`uttt/tablebase.py:76–90` (the one-open-board table's outcome map), the probe and puzzle label builders
(`tools/probe.py`, `tools/puzzles.py`), evaluator construction, and a rule tag in the name of every
cached dataset; a checkpoint's *training* rule is recorded in `config.json`, its *evaluation* rule is
an explicit argument everywhere, and the two are never conflated. And — found by J3's implementer —
**`gumbel_scale` is not recorded in `config.json`** (`train2.py` never sets it; every run so far
trained at `MCTSConfig`'s default 1.0): K1's provenance records every exploration knob explicitly
(`gumbel_scale`, `sample_moves`, `temperature`, `sample_uniform`, `root_prior_floor`), and the
count-rule parent's re-read states the same values.

*Engineering done 2026-09-12 (merged as `781dfca`; the implementer's eight design choices and its
list of what was deliberately not threaded are `docs/reviews/M2_designs/K1_design_notes.md`, M2's
material).* `uttt/rules.py`; the rule through both engines, the solver (one Numba specialisation per
rule — the bounded kernel too), exact labels, the tablebase's outcome map, search, arena, openings,
self-play, **the rollout anchor** (unasked: without it `--rule draw --b rollout` would pit a count bot
in a draw game), `train2.py` (`--rule`, `config.json`, `_provenance`), and twelve tools with `--rule`,
a `"rule"` field in every output and a `_draw` tag on cached datasets; mismatches are refused, never
inferred. `tests/test_rules.py`: `count` reproduces 2 000 pre-edit games bit for bit; `draw` turns
exactly the 280 count endings into draws; hand-made terminals; solver vs brute force under both rules
(43 of 200 positions differ); 100 000 cross-engine games per rule with the same 77 913 line endings.
**Before item 2's readings — not before the launch:** `decision.py`, `surprise.py`,
`ownership_grade.py`, `timeline.py` and `probe_value.py` are I1 tools that are not yet threaded and
would search under `count` on a draw net; they get the same two-line treatment first (`gdata.py`,
`annotate.py`, `endgame_accuracy.py` likewise if used). The K1 diff is M2's first object. Tests: the two engines
cross-checked under both rules on 10⁶ random games; a hand-made 4–4 final position that is a count
draw under both rules and a 5–3 one that is a win under `count` and a draw under `draw`; the solver
against brute force on tiny positions under both. The paired suite is opening positions and needs no
change; `v2b` and every anchor were trained under `count` and are used under both rules with that
stated.

*Cost.* ≈ 22 h on the 3090 (the parent took 21.96 h; the terminal test is not on the critical path),
plus ≈ 6 h on the 3060 for the readings. Inside the Windows Update pause (to 2026-10-14).

*Pre-registered readings, in order (amended after M0).*
0. **A no-training control first (desk, minutes).** Relabel `_e8`'s existing late games under the
   draw rule. From `_e4`'s corpus report, 16.5 % of outcomes change from a count decision to a draw
   and 33.1 % reach the no-line terminal (`runs/plan6/I1_A6_corpus_stats.out`) — two different
   quantities, both stated. This measures mechanical relabelling and claims nothing about how an agent
   trained under the rule would have played.
1. **The count-rule parent, re-read.** K1's parent is `_e8`, and the count-rule game claims were read
   on `_e4`; comparing a draw-trained `_e8` with a count-trained `_e4` would mix the rule with +40 Elo
   of strength. So the I1 tool set runs on **`deep8_c1_300_e8` under `count`** (≈ 5 h on the 3060,
   before or beside the run; §8's prohibition on a third pass is withdrawn for this purpose), and the
   comparison is `_e8`-draw against `_e8`-count.
2. **Rule-invariance of the game claims (primary; the reason for the run).** The I1 tool set on the
   draw net *under the draw rule* (`runs/plan7/K1_*.out`), each §1–§8 claim marked **rule-invariant**
   (sign and ordering as under `count`, magnitude inside the count reading's interval where one
   exists), **rule-dependent** (a sign or ordering differs, or the magnitude falls outside the interval
   by a stated margin), or **unresolved** (neither resolves at the precision available). Predictions,
   with thresholds: 1 invariant ([40] rank 1 at all three budgets; uttt.ai's draw-variant engine
   agrees); 24 dependent — the draw share of self-play games ≥ 30 % against 16.6 % under `count`
   (SaltZero's 48 % under `draw` is the only datum); 25 not applicable (no count endings); 16 — the
   board-count coefficient on the search value falls to |β| ≤ 0.015 with a 95 % interval excluding
   0.03, *or* unresolved, stated weakly on purpose: the count still correlates with line
   opportunities, and the unchanged recipe keeps the margin and ownership auxiliary targets
   (`uttt/selfplay_cont.py:159–169`), which are count-flavoured; 8 and 13 invariant (a free move and
   a macro threat within the count reading's intervals); 7's reply after [40] — no prediction, with a
   tie tolerance of 0.02 on the visit share; 33–34 invariant (a line rule).
3. **A common position set.** Both nets evaluated under both rules on one frozen set of natural
   positions (2 000 from each corpus), so the rule's effect on the *value* is read on identical
   inputs; on the solved subset the rule-induced change in the *exact* minimax value is computed with
   no net at all.
4. **Cross-play (secondary), defined algebraically.** The paired suite at 64 sims gives one
   independent score per rule — the draw net against the count net under `count`, and under `draw` —
   each with its pair-bootstrap interval (colour-swapped cells are complementary, not four numbers).
   Pre-registered contrast: the count-trained net's score under `draw` minus the draw-trained net's
   score under `count`; prediction positive (the count rule adds a skill the draw net never learned —
   the "collect boards" endgame, 32's tiebreak-conversion motif), read by the ± 3 rule.
5. **Corpus (tertiary).** Draw share, length, free moves per game, the self-send rate, end reasons
   over the last 20 iterations; the draw anatomy (26) under a rule where 5–3 is a draw.
6. **Strength under its own rule.** The draw net's E7 curve against the `count` anchors *under
   `draw`*, for shape only; there is no draw-trained reference, and none is proposed.

*What K1 cannot say.* Anything absolute about strength between the two nets (different games);
anything about the open-board variant (a third game). One seed confounds the rule change with one
optimisation trajectory, a rule-by-recipe interaction and a different visitation distribution, and
the two-seed count-rule band bounds none of those for regression coefficients or opening ranks — so
every reading is **"observed in this pair of runs"** (M0), read against the ≈ 3-point band where a
score is what is read.

## 6. Phase L — external calibration (optional; recommended for the paper; owner's budget)

The ladder's only outside anchor is a 100 k-playout rollout UCT (`uttt/rollout.py`; v2b ≈ +169 over
it). Three routes, priced from knowledge/03:

- **L1. A Legend-recipe rollout bot under the CodinGame referee.** Bitboards, 80–90 k rollouts per
  100 ms, an MCTS solver — the forum recipe; ≈ 1–2 days of desk to rebuild (no Legend source is
  public), then paired games through `Agade09/CG-UTTT-Arena` or `cg-brutaltester`. An *independent
  algorithmic baseline* under **exactly our rules** — stronger than `uttt/rollout.py`'s uniform
  playouts without tree reuse — but **not** an arena rating: only an independently rated opponent
  connects to that scale, and none is public (M0). The net needs a batch-1 stdin/stdout wrapper on the
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
  $prompt = "Your complete brief is the file docs/reviews/$tag/brief.md in this repository. Read it first and follow it exactly; it is the whole task. Deliver the review as your final message."
  codex-sp exec -s read-only --json -o "docs\reviews\$tag\REVIEW.md" $prompt 1> "docs\reviews\$tag\events.jsonl" 2> "docs\reviews\$tag\stderr.txt"
  ```
  — run as a detached hidden `pwsh -File` through `Start-Process` (the path **quoted inside one
  argument string**: the array form splits at the space in the user name) with the child's stdin
  redirected from an empty file. **Not** `exec … -` with the brief on stdin: `codex-sp` is a PowerShell
  function and a pipeline into it never reaches the native binary inside it, so `-` waits on the
  hidden console's stdin forever (M0's first launch: 0 CPU, 0 bytes; both lessons in §11). The
  reviewer reads the brief from the file, which the read-only sandbox allows. `--json` streams every event (agent messages, commands run, token
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
  `01a097ef-822f-74b1-9320-ea4f93e2799a`, exit 0. **M0 itself: 564 s, 4 152 498 input tokens
  (3 929 728 of them cached), 13 564 output, 26 commands and 13 MCP tool calls** — it fetches sources
  from the web through the `codex_apps` firecrawl plugin, so a review is not offline — far under the
  1–3 h first estimated. **The owner's Codex five-hour limit is the binding budget, and one such
  review nearly spends it:** the rebuttal round, resumed on the same session 18 minutes after M0, was
  cut off after 456 s by *"You've hit your usage limit … try again at Sep 13th, 2026 12:24 AM"*
  (`turn.failed`; the log's 20:29 entry). So: one whole-repository review per five-hour window; later
  stages' briefs name the files to read rather than the repository; a rebuttal is launched in the
  *next* window, not the same one.
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
5. **Freeze what is reviewed** (M0): each review names its commit, an artifact manifest and the claim
   IDs it covers; unresolved disagreements are recorded beside the verdicts, not dropped.
6. **Designs before execution** (M0): J3, J4 and K1 are reviewed as designs (M2) before they run, not
   only as wording in the draft afterwards.
7. **Three questions, kept apart** (M0): *was the finding correct*, *was the remedy worth buying*,
   and *did the experiment succeed* are judged separately — a recommendation framed as an experiment
   is not falsified by the experiment's result.
8. **Reproduction a read-only reviewer can do** (M0): the brief distinguishes recomputation from the
   saved JSON (asked for) from rerunning models (not), names the unsealed datasets it may open, and
   asks for no script-file deliverables; and "nothing outside KNOWLEDGE" binds *empirical* claims —
   methods, definitions and cited literature carry their own provenance.

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
| **M2 — K1's pre-registration, and J3 / J4's designs** | before K1's launch and before J3 / J4 run | Is the rule change complete (every place the terminal rule is read, §5's plumbing list)? Are §5's thresholds falsifiable as written, and is the relabel control read correctly? Should anything be measured in-run that cannot be recovered after? Are J3's three measurements the right isolation of exploration at matched budget, and is J4's bounded solver and conditional statement right? | §5, §4 J3–J4, `docs/reviews/M2_designs/J3J4_design_notes.md` (the implementer's fourteen choices), `uttt/batch.py`, `game.py`, `solver.py`, `exact.py`, `selfplay_cont.py`, the K1 diff and its tests, `tools/empty_board.py`, `tools/frontier.py` | `docs/reviews/M2_designs/`; none of the three runs until it is adjudicated |
| **M3 — the draft** | after J5 and K1's reading | Referee report, as for a venue: is each claim supported by the cited file at the stated level? Are the limitations complete? Is the contribution stated at the size the evidence supports? Recompute five numbers of the reviewer's choosing from the outputs. | `docs/paper/paper.md` and everything it cites | `docs/reviews/M3_draft/`, a report in referee form |
| **M4 — the final pass** | before submission | Adversarial: find the sentence that is false. Check every number in the abstract and the tables against its file. Check the rule variant is stated wherever a comparator is quoted. | the final manuscript, KNOWLEDGE, the outputs | `docs/reviews/M4_final/` |

Each stage's brief is written from the M0 template (Appendix A) with the question and the file list
changed; each is adjudicated in **§7e** (a table per stage, PLAN6 §1's columns) and rebutted once.

### 7d. Calibration: the first review's track record

Of REVIEW-astra's 22 adjudicated items (PLAN6 §1), judged by the three questions of 7b item 7. *Was
the finding correct:* the two instrument bugs (items 1–4) — yes, and they changed three claims; the
budget confound (15) — yes, decisively, it is where the update lever's +211 [+189, +232] came from (the three steps, +100 / +64 / +40, sum to +204); the ownership grading (17) and
the out-of-process evaluator (18) — yes; the RNG finding (13) — the fix was right and the stated cause
wrong (nondeterminism, not evaluation, is why same-seed runs diverge). *Was the remedy worth buying:*
every accepted remedy paid for itself within a day except one. *Did the experiment succeed:* the
review's headline recommendation, an exact-D4 trunk as "the next useful architectural experiment" (10),
was explicitly framed as an experiment — "the justification is not that symmetry must improve Elo …
whether that also improves learning or playing efficiency remains an experiment" (REVIEW-astra §1) —
and the experiment lost 220 Elo. That is information the project bought at one GPU-day and used to
close a line; it does not make the recommendation "confidently wrong", and the first form of this
paragraph, which said so, was outcome bias (M0). So: on instrument and statistics the reviewer was
reliable; on architecture it recommended a well-framed experiment whose result was negative. The
second review's findings are weighted on their evidence, and its brief quotes the first review's
stated uncertainty rather than a retrospective verdict.

### 7e. Adjudications

*(One table per stage, appended as each review returns, then the rebuttal round's reply.)*

**M0 — the plan (`docs/reviews/M0_plan/REVIEW.md`, commit `fc79a9e`, 2026-09-12).** Verdicts as in
PLAN6 §1: *accept* (the plan does it), *accept with change* (the finding stands, the reading or remedy
differs), *reject* (the evidence does not support it), *noted*. Every evidence cell was re-derived in
this session before the verdict was written.

| # | review item | verdict | evidence / reason | lands in |
|---|---|---|---|---|
| 1 | The five tiers are not a partition — they mix evidence source, drift status and coverage; claims sit in two tiers; compound claims hide changed components (finding 1) | **accept** | By construction: 31a, 32 and 33–34 appeared in E and in S / M; 11's training-path component reverses on `_e4` in KNOWLEDGE 11's own words. J1's independent check found the same. | §1a restated as level / coverage / drift; J1's map gets three columns |
| 2 | 31's diagnosis (optimisation, not capacity) is inference, not exact | accept | The metric is against the solver; the explanation is not | §1a corrections |
| 3 | 31a: split the tablebase from the nets' sampled accuracy; "100 / 100 / 100 on every net" is false; `_e4`'s 689 positions are from deep10's corpus | accept | KNOWLEDGE 31a: v2b 99.0 / 99.6 / 100, dev1 94.0 / 98.7 / 100. `runs/plan6/I1_C5_tablebase_grade.out` line 1: `runs/probe_data_deep10late_e4.npz` | KNOWLEDGE 31a corrected; §1a |
| 4 | 11's S assignment conceals the reversed training path | accept | KNOWLEDGE 11 states the reversal | §1a |
| 5 | 14: "every one of them below deep10's interval" is false — only the corner leaves it | accept | Recomputed from KNOWLEDGE 14's own ± values: centre 0.049 ∈ [0.030, 0.110], edge 0.038 ∈ [0.029, 0.083], corner 0.026 ∉ [0.035, 0.095] | KNOWLEDGE 14 corrected; J1 reconciles its three ranges |
| 6 | 32: the motif ordering changed too (holding a draw overtook giving a free move); "one reversal" only for enumerated orderings | accept | KNOWLEDGE 32: 71 / 61 / 51 → 32 / 26 / 23 | §1a; the paper enumerates the primary orderings |
| 7 | 6 is not N: `timeline.json` records the opening trajectory | accept | `first_top_share` verified: `_e4` [40] 0.941 / 0.950 / 0.990 at 20 / 30 / 300; J1 adds `_e8`'s later collapse | §1a; J1 |
| 8 | 35: "no resolved residual in this regression"; the counterfactual half is not re-read | accept | KNOWLEDGE 35's own note | §1a |
| 9 | 33–34: the solver column is a property of the position set and of one deterministic optimal policy, not of necessity | accept | `tools/probe.py exact_pv3`: `np.flatnonzero(ch == ch.max())[0]` — the lowest-indexed optimal move; `tools/principles.py:45` reads that label | KNOWLEDGE 33 corrected |
| 10 | S's "all four strong nets" is unmet by 8, 26, 35, 40 (J1 adds 33, 36; 21 has no CI) | accept | KNOWLEDGE's held-across clauses | §1a; the map records actual coverage |
| 11 | K1's parent is `_e8` but the count-rule readings are on `_e4` — the comparison mixes rule and strength | **accept** | K1 as written; +40 Elo between `_e4` and `_e8` | §5 item 1: the I1 tool set on `_e8` under `count`; §8 amended |
| 12 | Add a no-training relabel control (16.5 % of outcomes flip count → draw; 33.1 % reach the no-line terminal) | accept | Reviewer's recomputation from `runs/plan6/I1_A6_corpus_stats.out`; re-derived when J-work touches that file | §5 item 0 |
| 13 | Evaluate both nets under both rules on a common frozen set; use exact positions for the rule-induced minimax change | accept | — | §5 item 3 |
| 14 | Thresholds, populations, estimators and an *unresolved* verdict for the predictions; tie tolerance for ranks | accept | — | §5 item 2 |
| 15 | Cross-play is two scores, one per rule, colour-swapped cells complementary; pre-register the contrast | accept | The paired suite's construction | §5 item 4 |
| 16 | The board-count prediction is weak: count correlates with lines; the margin and ownership targets remain | accept | `uttt/selfplay_cont.py:159–169`: `margin` and `own` labels from the final macro, rule-independent | §5 item 2 (the weak form) |
| 17 | One seed confounds rule, trajectory, interaction and visitation; the count-rule band bounds none of it for coefficients or ranks | accept | — | §5 closing: "observed in this pair of runs" |
| 18 | Robustness promoted into game truth: associations as prices, insignificance as absence, sampled optimality as a milestone (finding 3) | **accept** | — | §0 (the surviving sentences), §1c (vi), §2a, §3 C3, §4 J4 |
| 19 | The working title: "knows" and the unnamed variant | accept | — | §0: "A strength-audited self-play analysis of closed-board, most-boards Ultimate Tic-Tac-Toe" |
| 20 | The architecture headline: "this equal-cost D4 implementation lost under this recipe"; "capacity, not LR" not established for self-play | **accept with change** | The headline as proposed. The mechanism evidence in KNOWLEDGE 50 (top Hessian eigenvalue 2.3×, relative step 1.19× / 1.41×, the supervised reversal by 12 480 steps, the lower-LR null) stays in the body as *consistent with* capacity, not as its proof | §0 |
| 21 | J3 is defective: greedy play repeats one trajectory; zero Gumbel noise does not disable opening sampling; budget changes were confounded with exploration | accept | `uttt/search.py:308–318`: sampling gated by `selfplay and cfg.sample_moves > 0 and cfg.temperature > 0`, not by the Gumbel scale | §4 J3 redesigned (three matched-budget measurements); M2 reviews it |
| 22 | J4: the solver has no node budget; aborted searches must return *unknown*; report conditionally at both ends | accept | `uttt/solver.py:93`: "No node budget" | §4 J4: `solve_bounded` first; the conditional statement |
| 23 | Withdraw "no dose–response exists" and "the lever nobody pulls": Wang et al. vary epochs at fixed settings and report tournament Elo; show the reuse conversion | **accept with change** | knowledge/07 §4.2 read them as a different regime; the phrases are withdrawn. The conversion (ep × a 20-iteration history ≈ 100–300 uses per position) is the rebuttal round's first question | §1b, §2b, §2c |
| 24 | KataGo's documentation permits raising its 4; not a universal warning | accept | Its `SelfplayTraining.md`, which the reviewer fetched | §2b |
| 25 | The +35 is not KataGo's root-only trick: the evaluator averages policy and value and is called at roots and expanded leaves | **accept** | `uttt/search.py:181` (expansion) and `:250` (root) both call `self.eval`; `uttt/symmetry.py:35–48` returns `back.mean(1), value.mean(1)` | §2b, §2c; KNOWLEDGE 41 never claimed the identity and is unchanged |
| 26 | "First calibrated" needs a definition that does not exclude pc29277 by fiat; "two orders of magnitude" is unsupported — ≈ 52.6× the games, ≈ 22 h each on different GPUs | accept | `runs/deep8_c1_300_e8/log.jsonl`: Σ games = 1 501 606; 1 501 606 / 28 544 = 52.6; its README has paired openings, fixed opponents and CIs | §0, §2c, knowledge/03's addendum (to amend) |
| 27 | L1 is a reproducible baseline, not an arena anchor; `rollout.py` is uniform playouts without tree reuse | accept | `uttt/rollout.py` header | §6, §3 C6 |
| 28 | gPress's 8.16 vs 6.47 is not a tie: undocumented scale, no uncertainty | accept | — | §2a |
| 29 | Exploitability is missing from the stability argument (D'Alberton); verify its variant | accept | knowledge/07 §2.4; the thesis page could not be retrieved by the reviewer | §2a row; the paper's limitations |
| 30 | knowledge/06 mislabels Elhage as open-board, derives no reachable-state lower bound, and wrongly treats the count tiebreak as richer than WDL | accept | knowledge/01 §2.2 and 03 §4 say closed / draw; `uttt/solver.py solve()` returns −1 / 0 / +1 | knowledge/06 corrected in six places |
| 31 | Protocol: freeze commit, manifest and claim IDs; review J3 / J4 designs; separate the three questions; fix the brief's calibration paragraph; make reproduction read-only-feasible; scope the KNOWLEDGE rule to empirical claims | accept | — | §7b items 5–8, §7c M2, §7d, Appendix A |
| 32 | The calibration paragraph had outcome bias: recommending an experiment was not predicting its success | accept | REVIEW-astra §1: "The justification is not that symmetry must improve Elo … remains an experiment" | §7d rewritten |
| 33 | Recomputed Elo from the 516 per-opening records: 99.600 / 63.659 / 40.242 / −219.908 | noted | Matches `runs/*/paired_vs_*.json` | — |
| 34 | K1 plumbing must include `tablebase.py:76–90`, probe / puzzle labels, evaluator construction, rule-tagged caches; distinguish training rule from evaluation rule | accept | — | §5 |
| 35 | Exact labels overwrite rows; the survey's 0.97 multiplier is wrong; logged reuse 1.0026 / 2.0027 / 4.0054 / 8.0109 | accept | `uttt/selfplay_cont.py apply_exact` overwrites `buf["value"][slots]`; `_e8`: 629 145 600 / 78 536 533 = 8.0109 | knowledge/07 corrected |
| 36 | KNOWLEDGE has 56 numbered claims, not 55 | accept | J1 counted programmatically: 1–51 + 7a, 31a, 38a, 41a, 41b | §1, Appendix A |

**What the review got right that was not asked.** It fetched ten of the survey's sources itself before
disputing any of them; it recomputed the ladder's four headline numbers from the raw records; and its
form of the free-move sentence (§0) is the one the paper will use.

**Open for the rebuttal round** (`codex exec resume 01a0980a-d906-7c61-a884-52d315a082d8`): (a) the
Wang et al. reuse conversion — is ep × a 20-iteration history the right arithmetic, and what reuse
range does their sweep therefore cover; (b) pc29277's compute in comparable units — 22 T4-hours
against 22 3090-hours, what ratio does the reviewer consider defensible; (c) the two relabel figures,
16.5 % and 33.1 % — the lines of `I1_A6_corpus_stats.out` they came from; (d) anything in this table
that misreads a finding. *Reply recorded below when it returns.*

## 8. Not proposed

`--epochs 16` (≈ 32 h for a step predicted inside the seed band; PLAN6 §9). Any depth or width change.
A G-CNN at any width in self-play; the data-matched supervised test (≈ 40 h of labelling for a net the
equal-cost rule disqualifies). `--head_tying 1` (proposable, predicted null-to-small; not needed for
the paper). A CodinGame submission (the 100 KB limit). A two-open-board tablebase (a reachable-only
generation project; J4's curve is the cheaper form of the same statement). A third analysis pass on
`_e8` *for its own sake* — but the I1 tool set does run on `_e8` under `count` as K1's parent reading
(§5 item 1; M0), and J1's cheap re-reads stand. A full solve.

## 9. Order, budget, GPU roles

| when | desk / this session | 3090 | 3060 |
|---|---|---|---|
| Day 0 (today) | PLAN7 committed; **M0 launched, returned in 9.4 min, adjudicated (§7e)**; the rebuttal round | idle | idle |
| Day 1 (done 2026-09-12, evening) | J1 and J2 adopted; K1's rule switch (`781dfca`), J3's script and J4's bounded solver (`934113a`) merged with their tests; M2's brief and launcher written — **M2 launches in the Codex window after the rebuttal** (§7a's one-review-per-window rule) | idle | **J1a, the sealed read** (5 min); **J1's cheap re-reads**; the `_e8` count-rule pass (K1 item 1, ≈ 5 h) |
| Day 1–2 | M2 adjudicated; **K1 put to the owner** | — | **J3** after M2 (≈ 1.5 h); **J4** on the CPU after M2 |
| Day 2 → 3 | J5 skeleton; **M1 launched** | **K1** (≈ 22 h) if approved | the E7 worker (≈ 6 min per checkpoint) |
| Day 3 | M1 adjudicated; K1 done and read by §5's rules | idle | **K1's readings** (≈ 6 h: the I1 tool set under `draw`, the 2 × 2 cross-play) |
| Day 4 | Manuscript draft; §10's file updates; **M3 launched** | idle (L1 if bought) | idle |
| Day 5 | M3 adjudicated; revisions; **M4 launched**; the E11 copy if a destination exists | | |

The trainer never shares the 3090; reviews run while this session is otherwise idle; the 50 % line
applies to every launch (above it, update this file first and hand over).

## 10. Files this plan changes

- **This file** — the live plan. *Done 2026-09-12 (J6, after M0's adjudication):* PLAN6 moved to
  `docs/history/PLAN6.md` (`docs/history/README.md` gained its row; README's "Start here" points here;
  PLAN6's open item — E11's copy — is carried in this Handover). Live files still cite it as "PLAN6
  §…", the convention for every superseded plan.
- **`README.md`** — "Start here" (PLAN7 second, PLAN6 to history), "Current state" (the paper as the
  open item; K1 if it runs), the ladder table unchanged.
- **`knowledge/03-prior-art-uttt-ai.md`** — *done 2026-09-12:* a dated addendum to judgment (a)
  (pc29277) and the refreshed arena figures; the rest of the file stands as the 2026-08-29 sweep.
- **`KNOWLEDGE.md`** — the header gains the tier of each claim (one word per line, from §1a); 46, 49
  and 51 name the lever "sample reuse" beside `--epochs` (J6, a wording change); new
  lines from J3 (the empty board), J4 (the frontier), K1 (one per claim re-read: rule-invariant /
  rule-dependent / unresolved, as I1 added held / moved / reversed); §10 updated. *Done 2026-09-12
  after M0:* 14 ("every one below" corrected), 31a (deep10's corpus), 33 (one optimal policy's rate).
  *To do in J1:* 14's three ranges reconciled, 28–30's `_e8` lines, 6's `_e8` reading, the level /
  coverage / drift columns.
- **`knowledge/06`** — *done 2026-09-12 after M0:* nelhage's variant corrected to closed-board / draw
  in three places; the MOPNS paragraph and takeaway corrected (the count tiebreak is win / draw / loss
  for the mover); the 10³³ lower end marked heuristic. **`knowledge/07`** — the 0.97 multiplier
  corrected (exact labels overwrite rows; `_e8`'s logged reuse quotient is 8.0109).
- **`RETROSPECTIVE.md`** — §7 (where things stand); a §8 "what the write-up changed" if the drafting
  changes any reading.
- **`docs/explainer.html`** — Part 8 (the game beliefs) carries the +363 numbers and the reversal; the
  training story gains the update lever and the equivariance negative. Republished.
- **New:** `knowledge/07-literature-2026-survey.md` (done); `docs/paper/01_claims_map.md` (done — J1's
  second draft) and `docs/paper/02_literature.md` (done — J2's revision), both drafts for M1;
  `docs/paper/paper.md` (J5); `docs/reviews/M0_plan/` (done), `docs/reviews/M2_designs/J3J4_design_notes.md`
  (done), the other `docs/reviews/M*/`; `tools/review_events.py`, `tools/frontier.py`,
  `tools/empty_board.py` and `uttt/solver.py`'s `solve_bounded` (done, merged `934113a`); `runs/plan7/`
  (J1a's two reads so far); `CITATION.cff`'s title once the paper's is fixed.

## 11. Operational notes

- PLAN6 §8's notes stand (one CUDA device per process; the E7 worker is a `cuda:1` process; hidden
  launchers; the retry wrapper; a reboot is the one failure it cannot cover — Windows Update is
  paused to 2026-10-14).
- **codex-sp from this session (learned the hard way on M0):** dot-source `~/.codex/codex-functions.ps1`
  first (the PowerShell tool's shell does not load it). **Never pass the brief on stdin** — `codex-sp` is
  a function, a pipeline into it does not reach the native `codex` inside, and `exec … -` then waits on
  the console's stdin forever (0 CPU, 0 bytes, no children); the preflight passed only because the tool's
  stdin was the null device. Give a one-line prompt naming the brief file. Detach with `Start-Process
  pwsh -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"<script>`""` — one string, the path
  quoted inside it; the array form splits at the space in `John Peponis` and the child exits in a second
  having run nothing — with `-RedirectStandardInput` from an empty file so any stdin read hits EOF, and
  the script's own `1>` / `2>` redirects for the JSONL and stderr. `--json` to a file for monitoring, `-o`
  for the review; the session id is the `thread.started` event's `thread_id`, for `exec resume`.
  Read-only unless a worktree is wanted. A review reaches the web through the `codex_apps` firecrawl
  plugin; expect it to fetch sources. The summariser for the stream is
  `tools/review_events.py` (commands run, output bytes, the reviewer's own text). The
  reviewer inherits `~/.codex/AGENTS.md` (the generated one) — its brief should say that the
  repository's own documents override any general instruction there about how to work.
- The 3090 is the display adapter: ≈ 830 MiB and ≈ 10 % utilisation is its idle state, not a job.
- `tests/test_symmetry.py` **passes on `cuda:0` and fails on `cuda:1`** with
  `cudaErrorStreamCaptureInvalidated` in the canonical evaluator's fp16 graph capture (2026-09-12;
  torch 2.13.0+cu126, driver 616.56, identical on pristine `HEAD`): the test captures with the
  process-global default capture stream, which lives on device 0 — REVIEW-astra §7.6 / PLAN6 §1 item
  20 exactly. Run it on `cuda:0`, or give the capture an explicit stream on its device. Not a K1
  regression; every other suite passes on `cuda:1`.
- Agent worktrees (`isolation: worktree`) live under `.claude/worktrees/<agent>/` inside the repo —
  ≈ 300 MB each, ignored since `a7c6136`; they lack `.venv` and `runs/*/games` (use the main
  checkout's by absolute path), start from whatever commit was current when the agent launched, and
  are merged with `--no-ff` after a read, then removed. Two agents editing one file (here
  `uttt/solver.py`) conflict at merge; resolve by making the two changes one design, not by picking a
  side.
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
> in this order: `PLAN7.md` in full; `KNOWLEDGE.md` (the claims file — 56 claims, each with level, CI,
> nets, tool and file); `RETROSPECTIVE.md`; `PLAN6.md` §0, §1 (how the first review was adjudicated —
> you will be adjudicated the same way) and §9; `knowledge/01`, `03`, `06` and `07` (the
> literature — `07` is the September 2026 survey; it names the one prior AlphaZero on these rules); `docs/history/REVIEW-astra.md` §1 and §9 (the first review, for calibration: its
> instrument findings were right and important; its architectural recommendation was framed as an
> experiment whose Elo effect it explicitly did not predict, and the experiment lost 220 Elo — judge a
> recommendation by its stated uncertainty, cost and information value, not by the outcome). Results live in `runs/*/analysis.out`, `runs/plan5_*.out`,
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
