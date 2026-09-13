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
externally anchored number — 113–87 at 400 ms/move against the then-#2 CodinGame bot — and **48 %
draws**, which matters: under CLOSED-COUNT most of those games would have had a winner. The CodinGame
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
| SaltZero *(repo)* | CLOSED-DRAW | #2 CG bot, 113–87 | code, weights, arbiter |
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
uttt.ai and gPress *(blog)*, and one integer — weight 2 against 5 for a board, 10 for the centre board,
in Lifshitz and Tsurel's 2016 heuristic *(course report)*. Ours is an adjusted association:
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
Emmerich, Preuss and Plaat *(arXiv 2020; journal version 2022)* ran the same knob on 6×6 Othello at
ep ∈ {5, 10, 15} passes over the whole buffer and recommend keeping the inner-loop parameters low.
**Their sweep is itself a published dose–response with tournament Elo, in a higher regime:** with
their 20-iteration replay history, ep ∈ {5, 10, 15} is ≈ 100–300 uses per position [being confirmed],
above our highest (eight passes over the new data ≈ 1.05 passes over our 7.6-iteration window). The
two therefore reconcile, consistent with an optimum between them; no claim is made that the lever is
unpulled, and KataGo's documentation permits raising its 4. Ours is the first positive local sweep
from 1 to 8 under a documented recipe, with a pre-registered rule and a measured seed band:
**+100, +64, +40 Elo**, one change per run [46, 49, 51], **+211 [+189, +232]** for the eight-pass net
over the one-pass net of the same shape, free at play time [44, 51], no over-fitting signature at
eight [51], and a supervised twin showing the fit is a function of optimizer steps, not
distinct positions [47]. The concept's home is model-free RL's replay / update-to-data ratio (Fedus
2020; Nikishin 2022; D'Oro 2023, all *(conf)*), where high ratios need resets;
here they needed nothing. Two scaling results size a doubling, as *regime* not contradiction: Jones
*(arXiv)* measures ≈ 500 Elo per decade of training compute on Hex, ≈ 150 per doubling, where ours
are per doubling of the *training half only*; Neumann and Gros *(arXiv)* [unverified: no venue] find
published models
"significantly smaller than their optimal size", whereas at 2.46 M parameters with 8× reuse still
paying we are update-limited, not parameter-limited. *Caution:* "Wu 2019" names two papers — D. J.
Wu's KataGo (arXiv:1902.10565) and T.-R. Wu et al.'s population-based training *(conf, AAAI 2020)*.

## Symmetry and equivariance

The prior is that equivariance buys sample efficiency: Cohen and Welling *(conf, ICML 2016)* argue
G-CNNs "reduce sample complexity by exploiting symmetries", in vision; Carroll and Beel *(arXiv)*,
the only board-game instance we found, report they "improve the performance of networks playing
checkers" [unverified: no numbers, no peer-reviewed version, supervised]. The closest published
analogue: SLAP on Gomoku (Suen and Alonso) *(conf, AISB 2023)* improved supervised
convergence by 83 % at one-eighth the data, but in self-play "it was not yet evident that it could
speed up reinforcement learning". The strong systems augment rather than enforce: AlphaZero does
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
10³³–10³⁸ [unverified: this project's estimate, knowledge/06 §2], five to ten orders higher. PN search aims "to produce a single boolean value"
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
| First move | CLOSED-DRAW | blog | 5 openings, no scale | 15 orbits, 4 nets [1–3] | best and worst agree |
| O's reply to [40] | CLOSED-DRAW | blog | corner boards | corner orbit 0.71 [7] | our reversal; engine agrees |
| First-player edge | CLOSED-COUNT | forum | 60 % for P1 | 62.7/20.7/16.6 %, `_e4` self-play, exploration on [24] | same order, conditioned |
| Draws, tiebreak | CLOSED-DRAW | repo | 48 % draws | count decides a third [25] | incomparable; ours new |
| Game length | CLOSED | conf, blog | 30–60 plies | 52.8 plies [27] | adds spread |
| Free move | CLOSED-DRAW | blog | one integer (2) | +0.195, adjusted association [8] | new; not a price |
| Never send to a winnable board | CLOSED-DRAW | docs | universal | 24.6 % vs 70.2 % [33] | false; nelhage's form true |
| Centre board | CLOSED | course report | weight 10 vs 3 | deep10 +0.01 ± 0.04, `_e4` +0.032 ± 0.044 [35] | no resolved residual, lines controlled |
| Exploitability | CLOSED [verify] | thesis | self-play agents exploitable | not measured | related nets ≠ adversarial |
| Solved status | OPEN | arXiv | X wins ≤ 43 | exact ≤ 16 empties, optimal given solved [28] | a frontier, not a value |
| Sample reuse | — | docs, conf | ≈ 1; one sweep at ≈ 100–300 | +100, +64, +40; +211 [46, 51] | above practice; prior sweep higher |
| Scaling | — | arXiv | models under-sized | update-limited [44] | regime, not conflict |
| Symmetry | — | conf | efficiency; SLAP did not transfer | −220 [50]; ensemble +35/−201 [41] | augment, don't enforce |
| LR schedule | — | forum/issue | drops invite memorisation | first real, second null [42] | only the first |
| Depth vs updates | — | arXiv | deeper is better | 8 × 2 beat 10 by +86 [44] | updates first |
| Concept probing | — | journal, conf | one trajectory | four nets [37]; −661 [41a] | replication and controls |
