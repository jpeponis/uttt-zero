# Related work

*PLAN7 J2 — the paper's related-work section. Drafted 2026-09-12 by an Opus agent from knowledge/01–07 and PLAN7 §2, revised the same day against the M0 adjudication (PLAN7 §7e rows 18, 20, 23, 25, 26, 28–30, 35, 36); adopted into `docs/paper/` as the draft M1 reviews. Every project-side number cites its KNOWLEDGE claim in brackets; `[being confirmed]` marks the two figures awaiting the rebuttal round.*

*Variant shorthand on every comparator: **OPEN** (won field stays playable; no macro line ⇒ draw);
**CLOSED-DRAW** (won or full board dead, sent there ⇒ play anywhere; no line ⇒ draw);
**CLOSED-COUNT** (as CLOSED-DRAW, but no line ⇒ more won boards wins). Source tags: journal / conf /
thesis / arXiv / repo / blog / forum / docs; bracketed numerals are `KNOWLEDGE.md` claims.*

## The game and its variants

UTTT names three games, and the commonest error in its literature is quoting a result for one as if
it held for another. OPEN is Orlin's 2013 original; CLOSED-DRAW is
[Wikipedia](https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe)'s, uttt.ai's, nelhage's and
OpenSpiel's; CLOSED-COUNT is the
[CodinGame referee](https://github.com/CodinGame/game-ultimate-tictactoe)'s *(repo)* and ours. The
only solved variant is OPEN: Bertholon, Géraud-Stewart, Kugelmann, Lenoir and Naccache, *"At Most 43
Moves, At Least 29"* *(arXiv)*, [arXiv:2006.02353](https://arxiv.org/abs/2006.02353) — the first
player wins in ≤ 43 moves, the second survives ≥ 29 rounds, any optimal first move is a "double"
(i,i) — proved by a hand-built strategy with six inductive invariants, **with no computer search
anywhere in the paper**. It does not transfer: the forcing chain needs O to keep playing inside a
field it has won, and under CLOSED rules O gets a free move once the centre closes. For
CLOSED-COUNT we are aware of no claim of the game's value and of no solving attempt that targets it:
Zirkelbach and Sadikov *(conf)*, [IS 2024](https://doi.org/10.70314/is.2024.scai.7299), summarise
CLOSED work as "the spatial complexity proved too great to allow for a complete solution".

## Agents for UTTT

Both public reference systems are CLOSED-DRAW. **uttt.ai** (Nowaczyński 2021) *(repo + blog)*, a
5 M-parameter offline two-stage net, is evaluated only against its own baselines, never
independently benchmarked. **SaltZero** (Hu 2019–20) *(repo)* carries the literature's only
externally anchored number — a **113–87 score** over 200 games at 400 ms/move against the then-#2
CodinGame bot, its README's "+ 65 = 96 - 39", so **96 of the 200 (48 %) were drawn**. What a count
tiebreak would do to those draws is not established: SaltZero publishes no final board-count
distribution, and in our own count-rule corpus the no-line third splits almost evenly — 16.5 %
decided by the count against 16.6 % equal [25] — under a policy trained to collect boards, which a
draw-rule agent is not. The CodinGame
arena *(forum)* is the only Elo-like ladder on CLOSED-COUNT; its two neural bots (reCurse's, briefly
#1, and jacek's) are unreleased and undocumented beyond two forum lines.
**pc29277/AlphaZero_UTTT** *(repo)*, created 2026-08-19, is an AlphaZero on **exactly these rules**,
so we make no "first AlphaZero on this variant" claim. It pairs openings and reports confidence
intervals against fixed opponents, so *calibrated* must be defined, not denied: what it lacks is an
independent anchor stronger than a depth-3 alpha-beta, a replicated seed band, a pre-registered rule,
and any analysis of the game. The compute gap is ≈ 53× the self-play games (1 501 606 against
28 544), ≈ 29× the nominal search work (a mean of 55.5 simulations per move over `_e8`'s schedule against a
flat 100), ≈ 22 h on each of two GPUs of different classes — ratios of games and of search work; no
total-compute ratio is established by either repository's records. The
academic tail is thin and nothing peer-reviewed touches CLOSED-COUNT; the one result bearing on our
claims is D'Alberton's best-response study *(thesis; variant to verify)*, finding "significant
vulnerabilities in self-play agents" — agreement among our four *related* nets is not
adversarial validation, and our limitations say so. The field has **no shared benchmark**: each
reports against a private ladder and no two have played each other. We state strength on our own
scale only — +363 Elo over `v2b` at 64 simulations [43, 51], itself ≈ +169 over a 100 k-playout
rollout UCT (PLAN7 §0).

| system | variant | strongest opponent | released |
|---|---|---|---|
| uttt.ai *(repo+blog)* | CLOSED-DRAW | own MCTS baselines | code, weights, data |
| SaltZero *(repo)* | CLOSED-DRAW | #2 CG bot, 113–87 **score** (+65 =96 −39) | code, weights, arbiter |
| reCurse / jacek *(forum)* | CLOSED-COUNT | arena (briefly #1) | nothing |
| pc29277 *(repo)* | CLOSED-COUNT | depth-3 alpha-beta, 76 % | code, no license |
| this work | CLOSED-COUNT | own ladder; rollout anchor | code, weights, suites |

## What is known about the game

gPress *(blog)* tabulates uttt.ai's
evaluations of five openings, +11.81 for Center-Center down to +6.12, every edge-board opening "bad"
— the only published first-move table for UTTT, five of 15 symmetry classes on an undocumented scale
with no uncertainty; ours is a 15-orbit atlas at three budgets on four nets, [40] rank 1 and [13]
rank 15 in all 12 columns, τ 0.85–0.96 across 340 Elo [1–3], agreeing on the top two and on
edge-board openings being worst. Nowaczyński *(blog)* calls centre-centre
"undoubtedly the best move" and has O's best reply pushing play into a corner board for ≈ 8 moves;
ours is the one recorded ordering reversal — the strongest net puts 0.71 of its visits after [40] on
the corner reply orbit where both weaker strong nets preferred the edge [7] — so the outside engine
sits on the stronger net's side. The free move has no published quantification: prose from
uttt.ai and gPress *(blog)*, and one integer — weight 2 against 5 for a board, 10 for the centre board and 3 for a corner
board, in Lifshitz and Tsurel's 2016 heuristic *(course report, HUJI; relayed on BGG/SE, its own link
dead, so its rule variant and whether the weights are additive are unverified)*. Ours is an adjusted association:
**+0.195 utility** against the 256-simulation search estimate on 30 000 natural positions,
game-clustered 95 % interval ≈ ± 0.028 (deep10 +0.196 ± 0.028; `_e4` +0.1953 ± 0.0278), falling to
≈ +0.08 … +0.12 with the immediate macro win in the model [8, 9]. It is not a price: in the same
regression the free-move coefficient exceeds the own-board residual (+0.02 … +0.08) and is of the
order of a macro threat's (+0.15) [13, 14]. The folk rule "never send the opponent to a board where
one move wins it" is universal, nelhage's
[critical-square analysis](https://www.minimax.dev/docs/ultimate/pruning/) *(docs)* its one rigorous
form — never send where one move wins *the game*. Against the solver the strong move does it 24.6 %
of the time and the **optimal move 70.2 %** [33], while the optimal move never hands an immediate
macro win when the mover is not already lost [34]: false as stated, true in nelhage's form, and we
are aware of no prior test of a UTTT folk rule against a solver. On the count rule there is one
datum — Daporan's 2018 *(forum)* objection that the first player can "collect small boards" — and **no source quantifies how often the tiebreak decides a game**; ours: 16.5 % of games
end on a board count and 16.6 % are drawn on an equal count — a third rather than a quarter, flat for
250 Elo then +6 points in 120 [25]. Game length is folklore (FLAIRS-35 *(conf)*, uttt.ai *(blog)*:
30–50 plies); ours is 52.8 plies, lengthening with strength, 5.08 free moves per game [27].

## Sample reuse in AlphaZero-style systems

Sample reuse is optimizer samples per generated position: our `--epochs` knob, Lc0's
*sampling ratio*. Published practice clusters at ≈ 1 (AlphaGo Zero ≈ 1.4, AlphaZero ≈ 0.5–0.7, ELF
≈ 0.8, Lc0 ≈ 1 *(docs)*, KataGo ≤ 4 *(docs)*, MiniZero ≈ 1–1.3 *(arXiv)*, pgx 1 *(conf)*);
only Lc0 and KataGo publish a ratio, the rest [unverified: the survey's conversions from
games-per-minibatch, ± 30 %]. Two experiments warn the *other* way: ELF OpenGo *(conf)*, where
pushing below 10 games per minibatch "hinders training … severe overfitting", and
[leela-zero#1480](https://github.com/leela-zero/leela-zero/issues/1480) *(forum/issue)*, a value head
over-fitting at ≈ 12× reuse — the same thread holds the maintainer's view that in-run
learning-rate drops invite memorisation, our schedule comparator [42]. Wang,
Emmerich, Preuss and Plaat *(arXiv 2020; journal version 2022)* ran the same knob on **6×6 Othello**
at ep ∈ {5, 10, 15} passes over the whole buffer, and their two findings must be quoted together:
at fixed outer settings "generally, larger *m* and larger *ep* lead to higher Elo ratings" — with one
exception, "the Elo rating of ep = 10 is higher than that of ep = 15 for *m* = 75" — while under a
fixed *time* budget "more training within one iteration does not show improvement for Elo ratings"
(§6.2 and Fig. 6). **Their sweep is a published dose–response with tournament Elo, in a higher
regime:** with their 20-iteration replay history (rs = 20, Table 1), ep ∈ {5, 10, 15} is a nominal
20·ep = **100–300** uses per position, or **≈ 62–262** over their finite runs of I ∈ {25,
50, 75} iterations with the history filling from empty (R_I = ep(20 − 190/I)) — above our highest
(eight passes over the new data ≈ 1.05 passes over our 7.6-iteration window). Different games, and
non-overlapping reuse regimes: **no common optimum is inferred, and none follows.** What does follow
is that nothing here says the lever is unpullable, and KataGo's documentation permits raising its 4. Ours is the first positive local sweep
from 1 to 8 under a documented recipe, with a pre-registered rule and a measured seed band:
**+100, +64, +40 Elo**, one change per run [46, 49, 51], **+211 [+189, +232]** for the eight-pass net
over the one-pass net of the same shape, free at play time [44, 51], no over-fitting signature at
eight [51], and a supervised twin showing the fit is a function of optimizer steps, not
distinct positions [47]. The concept's home is model-free RL's replay / update-to-data ratio (Fedus
2020; Nikishin 2022; D'Oro 2023, all *(conf)*), where high ratios need resets;
here they needed nothing. Two scaling results size a doubling, as *regime* not contradiction: Jones
*(arXiv)* measures "500 Elo per order of magnitude increase in compute" on Hex in its
linearly-increasing regime — 500·log₁₀ 2 = 150.5 per doubling of *training* compute
— where ours are per doubling of the *training half only*; Neumann and Gros *(conf, ICLR 2023; arXiv:2210.00849)* find, on
**Connect Four and Pentago**, strength a power law in parameter count "when not bottlenecked by
available compute" and published models "significantly smaller than their optimal size"; at 2.46 M
parameters with 8× reuse still paying we are update-limited **at this size**, which does not
exclude a parameter limit alongside it. *Caution:* "Wu 2019" names two papers — D. J.
Wu's KataGo (arXiv:1902.10565) and T.-R. Wu et al.'s population-based training *(conf, AAAI 2020)*.

## Symmetry and equivariance

The prior is that equivariance buys sample efficiency: Cohen and Welling *(conf, ICML 2016)* argue
G-CNNs "reduce sample complexity by exploiting symmetries", in vision; Carroll and Beel *(arXiv)*,
the only board-game instance we found, report they "improve the performance of networks playing
checkers" [unverified: no numbers, no peer-reviewed version, supervised]. The closest published
analogue: SLAP on **Gomoku** (Suen and Alonso) *(conf, AISB 2023)* improved supervised convergence by
83 % at one-eighth the data, and in reinforcement learning "reduced the number of training samples by
a factor of 8 and achieved similar winning rate against the same evaluator, but it was not yet evident
that it could speed up reinforcement learning" — an unproven speed-up, not a failure to transfer. The strong systems augment rather than enforce: AlphaZero does
neither (chess is unsymmetric) *(journal, Science 2018)*; AlphaGo Zero, Leela Zero and KataGo use 8×
dihedral augmentation with an **ordinary CNN**, KataGo also averaging its policy over symmetries at
the search root *(conf, ICML 2023)*. Ours: an exactly D4-equivariant trunk at matched
inference cost is **−220 Elo** against its parent, exact symmetry holding at all 30 checkpoints [50];
at matched *parameters* it is 7.0× the inference and over-fits [48]; canonicalisation alone is a
play-time null [41b]; and a **full-tree** 8-way symmetry ensemble — the averaged evaluator is called
at the root *and* every expanded leaf (`uttt/search.py:181`, `:250`), so it is not KataGo's
root-only trick — is +35 Elo at 8× the inference and **−201 at equal inference** [41], an ensembling gain,
not an equivariance gain. We are aware of no prior measurement of an exactly equivariant
architecture in a full self-play run at matched inference cost. The headline stays narrow: **this equal-cost
D4 implementation lost under this recipe.** The mechanism evidence — the supervised
advantage reversing by 12 480 steps, a quarter of the learning rate recovering nothing, 2.3× the top
Hessian eigenvalue [48, 50] — is consistent with capacity, not proof of it.

## Interpretability of game-playing networks

McGrath et al. *(journal, PNAS)* set the what–when–where template on one trajectory: concepts emerge
in a reproducible order, the opening policy narrows. Ours repeats the grid on **four independently
trained nets**, same layers, gains within a few points [37], the raw first-move policy collapsing
onto [40] within the first 30–40 iterations (≥ 0.94 by iteration 20 on `_e4`, ≈ 10 iterations later
on `_e8` — a `timeline.json` reading [being confirmed]) [6]. Lovering et al. on Hex *(conf, NeurIPS
2022)* find endgame concepts late and long-term concepts mid-trunk; ours is the same shape — tactics
at block 5 by iteration 60–80, threats mid-trunk, value in the last block by 180–220 [37, 38].
Their main body reads one agent (`grubby`, 8 layers × 512) over 21 checkpoints, and their
Appendix D replicates the key figures on **three further architectures** (`recent` 8×256, `baggy`
4×512, `vital` 2×1024, all from Jones's 9×9 Hex agents), so the precedent is a
cross-*architecture* replication; what is new here is a cross-*seed* one — two seeds of the same
10×128 net beside deep8_300 and `_e4`, on the full layer × iteration grid.
Pálsson and Björnsson *(conf, ECAI 2024)* show probe accuracy is an unreliable proxy for causal
importance, and Othello-GPT *(arXiv)* shows linear probes missing what non-linear ones find; ours
answers with a random-init non-linear control, stripping out what the encoding already exposes
[36, 38a], and a behavioural guard [41a]. The 2025–26 chess transformers *(arXiv)* are a contrast,
not a disagreement — nameable concepts early, alien representations deep (arXiv:2510.26025);
look-ahead to seven moves (Zhao et al.) — against which our layer profile is reversed (an
architecture difference, stated not argued) and our trunk carries far less of its own line: the move
two plies down the principal variation is decodable at 44.8 % against a 37.8 % control, +7 points
against +14 for the move it is about to play [39]. The distillation literature — VIPER *(conf,
NeurIPS 2018)* and successors — reports surrogates that *match* their teacher on single-agent tasks;
ours reproduces 41 % of the teacher's moves and then plays at −661 Elo against `v2b` [41a]. We are
aware of no distillation study reporting that residual in Elo against a graded ladder.

## Exact solving

nelhage's [ultimattt](https://github.com/nelhage/ultimattt) *(blog + repo + docs)* is the only serious
UTTT solving attempt: a Rust PN / DFPN hybrid under CLOSED-DRAW, solving positions "after about 20
ply … in a few hours" on a Ryzen 3900X and estimating the full game at **a few hundred million
CPU-hours** ($2M–$10M), with the note that he sees "no clear way to build endgame databases". Scale
places that: the largest game weakly solved is Othello at ≈ 10²⁸, with exact databases at 36 and 50
empties *(arXiv)*; checkers is ≈ 5 × 10²⁰ *(journal, Science 2007)* — against CLOSED UTTT's
10³³–10³⁸ [unverified: this project's **heuristic** estimate, knowledge/06 §2] — five
to ten orders above Othello's *if that estimate holds*, which is the only sense in which the
comparison is offered. PN search aims "to produce a single boolean value"
*(docs)*, but from the mover's side the count tiebreak is still win / draw / loss (`uttt/solver.py
solve()` returns −1 / 0 / +1), so draw-aware PNS suffices; Saffidine and Cazenave's MOPNS
[no source type in the survey] and the 2025 generalised PN-MCTS of Kowalski et al.
*(arXiv)* are options, not requirements (knowledge/06, corrected). We are aware of no public UTTT
endgame tablebase, for any variant, and of no "solved from ply N" claim like Othello's at 36 empties.
Ours is small by design: an exact ≤ 1-open-board table that measurement showed adds nothing, every
strong net already optimal there and the weaker ones close (v2b 99.0 / 99.6 / 100, dev1
94.0 / 98.7 / 100) [31a]; and on 3,000 solved 6–16-empty positions the 256-simulation search is
optimal in 100 % — conditional on solved, a sampled measurement, not a milestone [28].

## Summary of comparators

| comparator | variant | source | claims | ours | reading |
|---|---|---|---|---|---|
| First move | CLOSED-DRAW | blog | 5 of 15 orbits, undocumented scale | 15 orbits, 4 nets, 3 budgets [1–3] | the best move agrees, and the worst *class* (edge boards); [13]'s rank is ours alone |
| O's reply to [40] | CLOSED-DRAW | blog (prose) | corner boards | corner orbit 0.71 [7] | our reversal; the agreement is with prose, not a matched-budget engine experiment |
| First-player edge | CLOSED-COUNT | forum | 60 % for P1, in a bot arena's population | 62.7/20.7/16.6 %, `_e4` self-play, exploration on [24] | same order; different opponent population and an exploration floor |
| Draws, tiebreak | CLOSED-DRAW | repo | 96 of 200 drawn (48 %) | a third *reach* the no-line terminal; the count **decides 16.5 %**, 16.6 % equal [25] | incomparable; ours new |
| Game length | CLOSED-DRAW (uttt.ai) / unstated (FLAIRS-35) / CLOSED-COUNT (CG folk) | conf, blog, forum | 40–50 / ≥ 30 / 50–60 plies | 52.8 plies, p10 47, p90 59 [27] | adds the distribution and its drift |
| Free move | unverified (course report) | course report, blog | one integer (2, against 5 for a board) | +0.195 ± 0.028, adjusted association [8] | new; not a price |
| Never send to a winnable board | CLOSED-DRAW | folk + docs | universal folk rule; nelhage's narrow theorem | the agent 24.6 % on unsolved positions, the optimal move 70.2 % on 4 791 solved ones [33] | the folk form is false; nelhage's holds. Two populations, not a paired contrast |
| Centre board | unverified (course report) | course report, blog | centre board 10, any board 5, **corner** board 3; additivity unstated | deep10 +0.01 ± 0.04, `_e4` +0.032 ± 0.044 [35] | no resolved residual, lines controlled |
| Exploitability | unverified (page unreachable) | thesis | self-play agents exploitable | not measured | related nets ≠ adversarial |
| Solved status | OPEN | arXiv | X wins ≤ 43 | exact ≤ 14–16 empties on **sampled** positions, optimal given solved [28] | not a solution, and not an established frontier |
| Sample reuse | — (6×6 Othello for the sweep) | docs, conf | ≈ 1 (Lc0, KataGo published; the rest converted at ± 30 %); one sweep at a nominal 100–300 | +100, +64, +40; +211 [46, 51] | above practice; the prior sweep is a different game and a higher regime |
| Scaling | — (Hex; Connect Four, Pentago) | arXiv, conf | 500 Elo/decade; models under-sized | update-limited at 2.46 M [44] | regime, not conflict; a parameter limit is not excluded |
| Symmetry | — (Gomoku) | conf | efficiency; SLAP's RL kept 8× fewer samples at a similar winning rate, speed-up unproven | −220 [50]; ensemble +35/−201 [41] | this equal-cost implementation lost under this recipe; the strong systems augment |
| LR schedule | — | forum/issue | one maintainer's warning that in-run drops invite memorisation | first real, second null on four ResNets; a resolved +6.5 second drop on the G-CNN [42, 50] | only the first, on ResNets |
| Depth vs updates | — | practice (no citation) | "deeper is better" as folklore | 8 × 2 beat 10 by +86 at 0.81× the cost [44] | at equal compute and this size, updates first |
| Concept probing | — | journal, conf | one trajectory (McGrath); one agent + 3 architectures in an appendix (Lovering) | four independently trained nets, two of them seeds of one architecture [37]; −661 [41a] | seed replication and three controls |
