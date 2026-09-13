# 07 — Literature survey for the write-up (September 2026)

Compiled 2026-09-12. This is the arXiv-facing survey: what prior work actually claims, with
citations a reader can check, and how each claim bears on this project's results. It refreshes
and extends `03-prior-art-uttt-ai.md` (compiled 2026-08-29), `01-uttt-rules-and-game-theory.md`
(2026-08-29) and `06-exact-solving-feasibility.md` (2026-09-03), and it adds the methodology
comparators those files did not cover: the updates-per-position ratio in AlphaZero-style
systems (§4), equivariant architectures for board games (§4b), probing (§5) and solver
benchmarks (§6).

**Source-type tags used throughout.** *(journal)* peer-reviewed journal; *(conf)* peer-reviewed
conference or workshop with proceedings; *(thesis)*; *(arXiv)* preprint with no peer review
found; *(repo)* code repository with a README as its only write-up; *(blog)*; *(forum)*;
*(docs)* project documentation written by the system's own authors.

**Rule-variant shorthand** (from `01` §1.2):
- **OPEN** = Orlin's 2013 original: a won field stays playable (moves in it have no effect);
  free move only when the target field is *full*; no macro line ⇒ draw.
- **CLOSED/DRAW** = Wikipedia / uttt.ai / nelhage / OpenSpiel: won *or* full board is dead;
  sent there ⇒ play anywhere; no macro line ⇒ draw.
- **CLOSED/COUNT** = CodinGame and this project: as CLOSED/DRAW, but no macro line ⇒ the player
  with more won local boards wins; equal counts ⇒ draw.

---

## 1. Game-theoretic status of UTTT

### 1.1 The only solved variant, and exactly what it says

**Bertholon, Géraud-Stewart, Kugelmann, Lenoir, Naccache, "At Most 43 Moves, At Least 29:
Optimal Strategies and Bounds for Ultimate Tic-Tac-Toe"** *(arXiv)*,
[arXiv:2006.02353](https://arxiv.org/abs/2006.02353) (ENS Paris, v1 3 Jun 2020, v2 6 Jun 2020;
cs.GT). Claim: the first player has a winning strategy; an optimal one wins in ≤ 43 moves; the
second player can survive ≥ 29 rounds; and any optimal strategy's first move is a "double"
(i,i), with the second move forced given the reply. **Variant: OPEN.** Method: a hand-built
three-phase strategy with six inductive invariants P1–P6, plus an explicit second-player
delaying strategy for the lower bound. **No computer search anywhere in the paper**; no compute
reported; no code repository from the authors was found. I re-checked in September 2026 and
found no v3, no journal version, and no follow-up that strengthens or extends it.

Why it does not transfer: the forcing chain depends on O being compelled to keep playing inside
a field O has already won. Under CLOSED rules O gets a free move the moment the centre closes
and the chain breaks (this project's `01` §2.1 works it through move by move).

**Diamond, "A Practical Method for Preventing Forced Wins in Ultimate Tic-Tac-Toe"** *(arXiv)*,
[arXiv:2207.06239](https://arxiv.org/abs/2207.06239) (2022, v3 2023). Same OPEN rules;
randomises the first four moves; the body computes the collision probability as 56/59,049
(0.0948 %) while the arXiv abstract says 64/59,049 (0.108 %) — the discrepancy is in the
source. Adds no computation and does not touch CLOSED rules.

### 1.2 Status of the CLOSED variants: unsolved, and nobody claims otherwise

- **Wikipedia** [Ultimate tic-tac-toe](https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe)
  (revision checked 2026-09-12; last substantive edit 2026-07-23) states the CLOSED/DRAW rules
  in its Rules section — "Once a small board is won by a player or it is filled completely, no
  more moves can be played in that board, and a player sent to that board may choose any other
  valid board to play in" and "there are no playable small boards remaining, in which case the
  game is a draw" — and confines the 2020 result to its Variants section, attributing it
  explicitly to "A variant of the game [that] requires players to continue playing in already
  decided boxes if there are still empty spaces." **Wikipedia is careful here; most secondary
  sources are not.**
- The *widely repeated, incorrectly attributed* claim is "UTTT is a first-player win." It is
  repeated across blogs, app stores, YouTube and Stack Exchange without the variant caveat,
  usually tracing back through Presh Talwalkar's [Mind Your Decisions
  video](https://mindyourdecisions.com/blog/2014/11/29/ultimate-tic-tac-toe-a-winning-strategy-video/)
  (2014) *(blog)* to Joachim Breitner's ["Ultimate Tic Tac Toe is always won by
  X"](https://www.joachim-breitner.de/blog/604-Ultimate_Tic_Tac_Toe_is_always_won_by_X) (2013)
  *(blog)*, which itself concerns OPEN rules and says of its own argument "not a formal proof
  yet, but hopefully close enough to convince you." Anson Hu's SaltZero README *(repo)* pushes
  back in the same terms: "some posts on the internet claim that ultimate tic-tac-toe is solved;
  however, this only applies to a weaker variant which does not forbid playing in won local
  boards. Real ultimate tic-tac-toe is unsolved"
  ([farmersrice/saltzero](https://github.com/farmersrice/saltzero)).
- **No source found claims the CLOSED/COUNT (CodinGame) variant's value**, and no solving
  attempt targets it. A newly maintained community index of solved games,
  [brianhliou/awesome-game-solving](https://github.com/brianhliou/awesome-game-solving) *(repo,
  last pushed 2026-09-11)*, lists plain tic-tac-toe as strongly solved and has no UTTT row of
  any kind. (Weak evidence — the list has 0 stars — but it is the only recent canonical index
  I could find, and it is consistent with everything else.)
- **Zirkelbach and Sadikov (2024)** *(conf)*, ["Puzzle Generation for Ultimate-Tic-Tac-Toe",
  Information Society 2024](https://doi.org/10.70314/is.2024.scai.7299), working in CLOSED
  rules, summarise the state as: "Some researchers have attempted to solve the game
  theoretically, but the spatial complexity proved too great to allow for a complete solution."

### 1.3 What is believed empirically about the first-player edge

All of this is impression or measurement against weak references; none of it is a theorem.

| Claim | Source | Type | Variant |
|---|---|---|---|
| "P1 has a 60 % winrate for UTTT so chances are not equal" | darkhorse64, [CG forum p.5](https://forum.codingame.com/t/ultimate-tic-tac-toe-puzzle-discussion/22616?page=5) (Aug 2020) | forum | CLOSED/COUNT |
| "it is agreed upon that either p1 wins or a draw can be forced"; the most-boards rule "probably further makes the p1 player better" | jacek, [CG forum p.7](https://forum.codingame.com/t/ultimate-tic-tac-toe-puzzle-discussion/22616?page=7) (Feb 2022) | forum | CLOSED/COUNT |
| A second-player win is "highly improbable" under optimal play | sscg13, same thread | forum | CLOSED/COUNT |
| Random playouts: X 50.9 %, draw 7.2 %, O 41.9 % over 1 M games | snowfrogdev, [CG forum p.2](https://forum.codingame.com/t/ultimate-tic-tac-toe-puzzle-discussion/22616?page=2) (2018) | forum | CLOSED/COUNT |
| Centre opening ≈ 52 % for X under mass random-playout MC | [Kevin Royer](https://royerk.github.io/Neural-Network-UT3/) | blog | CLOSED |
| "the game is not proven to be a draw with perfect play, but it likely is" | [gPress](https://gpress.soopergrape.com/index.php/2025/06/26/n-in-a-row-games-part-3/) (2025) | blog | CLOSED/DRAW |
| "far easier to win games of UTT as X than as O" (64,000 heuristic-bot games) | [Baker, Mukhoti, Chandavarkar, WREC 2021](https://books.aijr.org/index.php/press/catalog/download/114/44/1531-1?inline=1) | conf | CLOSED, tied boards count for *both* |

**Bearing on this project.** The project measures X 62.7 % / O 20.7 % / draw 16.6 % in
`deep8_c1_300_e4`'s own self-play (KNOWLEDGE 24), with X flat since `deep10` while draws rise
out of O's column. Nothing comparable exists in the literature for any variant: darkhorse64's
"60 %" is an arena impression across heterogeneous opponents, and the 50.9/7.2/41.9 split is
random play. The project's numbers are, as far as I can establish, the first side-conditioned
self-play outcome distribution published for UTTT at any strength — but note that self-play
rates from a single agent with exploration are not the game's value, and the write-up should
say so.

---

## 2. Strongest known agents, and how they were built

### 2.1 The two public reference systems (both CLOSED/DRAW)

**uttt.ai — Arkadiusz Nowaczyński (2021)** *(repo + blog)*.
[ar-nowaczynski/utttai](https://github.com/ar-nowaczynski/utttai) (Apache-2.0),
[uttt.ai](https://uttt.ai), [blog](https://uttt.ai/blog),
[HN thread](https://news.ycombinator.com/item?id=29594786).
- 5 M-parameter policy-value net (20 MB) with a non-standard trunk: a 3×3 stride-3 conv
  collapses each local board to one cell, residual work happens on the 3×3 macro grid, a
  ConvTranspose upsamples back to 9×9 for the policy; auxiliary action-value head; masked-KL
  policy loss; value target = root mean MCTS value, not the game result; flip augmentation.
- **Offline, two-stage, not a live AlphaZero loop**: stage 1 = 8.0 M positions labelled by pure
  rollout MCTS (1.36 M simulations per position on average); stage 2 = 8.0 M positions labelled
  by neural MCTS at 10 k sims.
- Hardware/budget: i7-10700K + 2 × RTX 2080 Ti + 64 GB, **≈ 10 weeks wall-clock**, mostly C++
  self-play.
- **Reported strength**: only against its own baselines — "NMCTS2 beats MCTS baseline even with
  4 orders of magnitude difference in the number of simulations (1k vs 10M)"; tournaments are
  100 games from 50 unique positions, each played twice with sides swapped. The author's own
  external claim is unquantified: "The resulting AI is very strong and beats any other solutions
  that you can find online" (HN, Dec 2021). **No match against a CodinGame Legend bot or against
  SaltZero was ever published**, and I could find no independent benchmark of it in the five
  years since.

**SaltZero — Anson Hu (2019–2020)** *(repo)*.
[farmersrice/saltzero](https://github.com/farmersrice/saltzero) (GPL-3.0).
- Dense net, no convolutions (the author's argument: cells adjacent across local-board borders
  are unrelated): 7 residual blocks of two 1024-unit dense layers; 200 visits/move in self-play;
  ~10 k games/hour on a Ryzen 7 3700X + RTX 2070 Super; 52.5 % gating over 400 games; Dirichlet
  α = 0.3.
- **The only external benchmark in the public UTTT literature**: 113–87 (+65 =96 −39) over 200
  games at 400 ms/move against NinjaDoggy's then-#2 CodinGame bot, whose source was supplied
  privately. **48 % draws** — a number that matters, because under CLOSED/COUNT most of those
  games would have had a winner.
- Ships `arbiter.cpp` / `bot.cpp` so third parties can play against it over a line protocol, and
  invites result submissions. Nobody appears to have taken it up.

### 2.2 The one public AlphaZero on *this project's exact rules* — found late, and it matters

**pc29277, "AlphaZero for Ultimate Tic-Tac-Toe"** *(repo)*,
[pc29277/AlphaZero_UTTT](https://github.com/pc29277/AlphaZero_UTTT). Created and pushed
**2026-08-19** — ten days before this project's prior-art note was compiled, and missed by it.
One commit, no license, 0 stars.
- **Variant: CLOSED/COUNT.** The README states it plainly: "if the board you are sent to is
  closed (already won by someone), you can play anywhere … If there is a draw, whoever has more
  local boards wins. If local boards are drawn and the rest of the macro board is equally won,
  the game is truly drawn." (The wording does not explicitly say a *full* unwon board also
  closes; that case is presumably handled by having no legal moves.)
- Network: 9 input planes → 3×3 stem conv to 128 filters → **10 residual blocks** → policy (81
  logits) + tanh value. **2,983,770 parameters.**
- Training: PUCT with Dirichlet noise at the root only; temperature 1.0 for 15 plies then
  greedy; 8× D4 augmentation ("the sending rule commutes with the symmetry group"); 500 k FIFO
  replay buffer; Adam 2e-3, wd 1e-4, batch 512; **100 simulations per move**; two runs totalling
  **28,544 self-play games in 22 GPU-hours on a T4**.
- **Reported strength** (100 paired games each, random 4-ply openings, 100 sims/move, CPU):
  76.0 % vs depth-3 alpha-beta [score 0.780 ± 0.079], 87.0 % vs a one-ply greedy heuristic,
  100.0 % vs uniform random. The ladder is internally consistent (greedy beats random 84 %,
  depth-3 beats random 95 % and greedy 87.5 %).
- **Honest self-criticism worth citing**: the author explains that the run's in-training "Elo"
  is meaningless because the baseline is reloaded from the current net each evaluation, so it is
  pinned near 1200 by construction and "only answers 'did the agent beat itself from 2000 games
  ago?', not 'how strong is the agent?'." The final net scored 1180 — it could not beat its own
  predecessor. The author diagnoses a policy-loss plateau (1.59–1.64 for the last 22 k games
  while value loss fell monotonically 0.869 → 0.382) and hypothesises the 100-sim search stopped
  producing improving targets. Engineering note: batched inference over 128–256 concurrent games
  gave a 7.8× self-play speed-up on a T4, because a forward pass cost ~4 ms of launch overhead
  against ~0.1 ms of compute.

**Bearing on this project.** This is a real, direct precedent and the write-up must cite it. It
changes the novelty claim: "first public AlphaZero on the CodinGame ruleset" is no longer
available. What survives, and is stronger, is: *first AlphaZero on the CodinGame ruleset with a
calibrated external strength measurement, a replicated recipe ladder, and the agent used to
produce game knowledge.* pc29277's strongest named opponent is a depth-3 alpha-beta — a bot at
roughly CodinGame Silver — against which this project's `v2b` yardstick would already be far
ahead (`v2b`@64 is ≈ +169 over a 100 k-playout rollout UCT, which is itself the Legend recipe).
Its 22 GPU-hours / 28.5 k games / 100 sims is also roughly two orders of magnitude below this
project's per-run budget.

### 2.3 CodinGame — the only arena with an Elo-like ladder on CLOSED/COUNT

**Live snapshot, 2026-09-12** (pulled from CodinGame's leaderboard API,
`POST /services/Leaderboards/getFilteredPuzzleLeaderboard` on the `tic-tac-toe` puzzle;
[public leaderboard](https://www.codingame.com/multiplayer/bot-programming/tic-tac-toe/leaderboard)):

- **10,085 entrants.** League sizes: Legend **431**, Gold 1,388, Silver 1,202, Bronze 5,671,
  Wood 1,397. (Wood league plays plain 3×3 tic-tac-toe; Bronze and above play UTTT.)
- Top 12 and languages: 1 Daporan (C++, 33.34), 2 zasmu (C++), 3 MrSubZero (C++), 4 Fancheng
  (C++), 5 **TomAlard (Python3, 30.54)**, 6 karliso (C++), 7 **reCurse (C++, 29.58)**,
  8 Minuet (C++), 9 RoboStac (Rust), 10 YurkovAS (C++), 11 **jacek (C++)**, 12 mires._. (C++).
- Constraints: 1000 ms on turn 1, 100 ms afterwards, single core, 100 KB source
  ([referee](https://github.com/CodinGame/game-ultimate-tictactoe)).

Technique, from the arena's own forum thread *(forum)*
([Ultimate Tic-Tac-Toe puzzle discussion](https://forum.codingame.com/t/ultimate-tic-tac-toe-puzzle-discussion/22616)):
bitboard MCTS with random playouts, an MCTS **solver** (proven-win backpropagation, citing
Winands), tree reuse, 1-ply win checks inside playouts, million-node pools. Throughput quoted:
~25 k rollouts/turn reaches Legend (Magus, 2018); "optimize further your bot to reach 80–90k and
add a solver to make it into top 50" (darkhorse64, p.8); MrSubZero reports **350–400 k rollouts
at the starting position and 40–43 k at turn 2** (Aug 2023, p.9); "the top of legend goes more
towards 100k+" per 100 ms (reCurse, 2019). The most recent substantive posts on that thread are
from late 2023 and are micro-optimisation (fast inverse square root for the UCT term, cheap PRNGs,
multiplication instead of modulo) — no new algorithmic direction since.

**Neural bots inside the arena.** reCurse built an AlphaGo-Zero-style RL pipeline over Christmas
2020 out of "accumulated years of frustration / hatred at being unable to gain a significant edge
with my bot at Ultimate-Tic-Tac-Toe", and with it "briefly took the #1 spot" in the UTTT arena
([Spring Challenge 2021 post-mortem](https://forum.codingame.com/t/spring-challenge-2021-feedbacks-strategies/190849/67))
*(forum)*; jacek describes his own as "mcts 'ept' with one-hots NN (very similar to NNUE)" and
confirms "reCurse uses mcts with CNN for his bot" *(forum)*. **Neither is released — no source,
no weights, no write-up beyond those forum lines.** These remain the only agents that are
plausibly both strong and trained on CLOSED/COUNT, and they are unverifiable.

A common misreading to avoid: SaltZero's README says "codingame does not allow the use of neural
networks." What the author means is that his C++/Python hybrid cannot run there; the platform
does permit nets whose weights are embedded in the 100 KB source as encoded strings, which is
exactly what reCurse and jacek do.

### 2.4 Everything else, and what it does and does not report

The long tail is catalogued in `03` §1.4 and unchanged; two additions found in this pass:
[Jaspvr/UTTT](https://github.com/Jaspvr/UTTT) (2024, MCTS with a PyTorch net guiding selection,
no strength reported) and [ishandutta2007/uttt](https://github.com/ishandutta2007/uttt) (browser
engine, no strength reported). [lunathanael/tacult](https://github.com/lunathanael/tacult) (MIT,
C++ bitboard engine + vectorised MCTS + ONNX + an Elo arena) has not been touched since
2025-04-16 and still reports Elo only against its own checkpoints.

Two consumer sites make unsupported superlative claims and should be treated as marketing, not
evidence: [theofekfoundation.org](https://www.theofekfoundation.org/games/UltimateTicTacToe)
("currently the strongest Ultimate Tic Tac Toe bot", pure MCTS) and
[ultimate-ttt.com](https://ultimate-ttt.com/) (a 2025-ish browser app advertising "MCTS AI …
puzzles, opening library, deep analysis and move-quality review"; the page is a JS bundle with
no documentation of engine, strength, or even which tiebreak it uses — I could not extract its
opening library or confirm any of its claims).

**Academic UTTT work** is unchanged from `03` §2 and remains thin: Addison, Peeler and Alvin
*(conf, 2-page abstract)*, ["Ultimate Tic-Tac-Toe Bot
Techniques", FLAIRS-35 2022](https://journals.flvc.org/FLAIRS/article/view/130698) — an
"AlphaZero-inspired" CNN trained 24 h on MCTS data won 88 % of its 50,000 games against random /
heat-map / MCTS(0.1 s, 1 s), with the telling admission that "with a typical game lasting at
least 30 moves, the MCTS cannot reach a depth that vastly outperforms random moves"; D'Alberton
*(thesis)*, ["A Reinforcement Learning Journey in Ultimate Tic Tac
Toe"](https://thesis.unipd.it/handle/20.500.12608/86899) (MSc, Padua 2024/25) — DQN/DDQN/A2C/PPO,
Elo and round-robins, **best-response training to measure exploitability**, finding "significant
vulnerabilities in self-play agents", best residual DDQN 85 % against the other trained agents,
no MCTS, no external baseline. Nothing peer-reviewed trains a serious AlphaZero for UTTT, and
nothing academic touches CLOSED/COUNT.

**Bearing on this project.** The field has no shared benchmark. uttt.ai, SaltZero, tacult,
pc29277 and the FLAIRS CNN each report against a different private ladder, and no two have ever
played each other. That is both the reason this project's paired-suite / rollout-anchor
measurement kit is a contribution and the reason its Elo numbers cannot be placed on anyone
else's scale without actually playing the match. The one externally-anchored number in the whole
literature is SaltZero's 113–87 against NinjaDoggy in 2020 (CLOSED/DRAW, 400 ms/move).

---

## 3. Analysis of the game itself

### 3.1 Opening theory

- **uttt.ai engine evaluations, tabulated by gPress** *(blog)*
  ([gPress, "N-in-a-Row Games, Part 3", 26 Jun 2025](https://gpress.soopergrape.com/index.php/2025/06/26/n-in-a-row-games-part-3/)):
  Center-Center ("The Main Line") **+11.81**, Center-Corner ("The Corner Attack") **+11.07**,
  Center-Edge **+8.16**, Corner-Home-Corner **+6.47**, Corner-Opposing-Corner **+6.12**, every
  edge-board opening "bad". Variant CLOSED/DRAW; the author plays "inert" tied boards. **The
  scale is uttt.ai's undocumented internal evaluation** — it is not a probability, not a utility,
  and not comparable to anything. This is the only published first-move table for UTTT and it
  covers 5 of 15 symmetry classes.
- **Nowaczyński's prose strategy** *(blog)*, [uttt.ai/blog](https://uttt.ai/blog) and relayed on
  [Board & Card Games SE](https://boardgames.stackexchange.com/questions/49291/strategy-for-ultimate-tic-tac-toe):
  open in the centre square of the centre board ("undoubtedly the best move"); O's best reply
  pushes play into a corner board and the next ~8 moves stay in corner boards; when play breaks
  out, "jump between the side subgames (these are the least useful to take)"; "maintain the
  overall balance … the game is a marathon, not a sprint"; and "think twice before sending your
  opponent to the finished subgame."
- **Royer** *(blog)*, [royerk.github.io](https://royerk.github.io/Neural-Network-UT3/): mass
  random-playout Monte Carlo puts (4,4) best at ≈ 52 % win for X, and he computed "a moves'
  matrix" of best replies which he **did not publish**.
- **Human guides** split between centre-of-centre ([tictoe.org](https://tictoe.org/games/ultimate-tic-tac-toe),
  [tictactoefun](https://tictactoefun.com/blog/ultimate-strategy.html)) and corner-of-centre
  ([Rare Pike](https://rarepike.com/three/ultimate-tic-tac-toe/)), with no evidence either way.

**Bearing on this project.** KNOWLEDGE 1–7 gives a 15-orbit first-move atlas across four nets
and three search budgets, with [40] rank 1 and [13] rank 15 in all 12 columns, Kendall τ = 0.85
between the strongest net and the weakest at 16 k sims, X's edge after [40] rated +0.447
(deep10) / **+0.495** (`_e4`) in utility with a +0.100 gap to [36], and a recorded **reversal**
at claim 7 (the strongest net prefers the corner reply orbit where both earlier strong nets
preferred the edge). Nothing of this shape exists anywhere. The gPress/uttt.ai table is the only
comparator and it agrees on the ordering of the classes it covers (centre-centre > centre-corner
> centre-edge > corner-corner) — a worthwhile independent corroboration to state, with the
caveat that it is a different tiebreak and an uncalibrated scale.

### 3.2 The free move / tempo

- **nelhage's critical-square rule** *(blog/docs)*,
  [minimax.dev "Pruning and positional analysis"](https://www.minimax.dev/docs/ultimate/pruning/):
  once a player is one local move from a macro win, every cell that would send the opponent to
  that board is losing and can be pruned outright; boards whose only open squares are such cells
  become forced losses. This is a *rigorous, variant-specific* statement (CLOSED/DRAW) used for
  search pruning — not a soft heuristic.
- **Heuristic weights as the only quantification** *(course reports, relayed on
  [BGG/SE](https://boardgames.stackexchange.com/questions/49291/strategy-for-ultimate-tic-tac-toe))*:
  Lifshitz & Tsurel (HUJI 2016) weight winning the centre board 10, any board 5, a corner board
  3, the centre square of a small board 3, and **being granted a free move 2**. Powell & Merrill
  (2021) use a different scale (board 100, double threat +200, blocking win 150). These are
  hand-tuned integers in a static evaluator, not measured values.
- **gPress** *(blog)*: "Never underestimate the power of a free move … Don't give up free moves
  for free", balanced against "don't underestimate the power of a good major board position,
  even if securing it gives up a free move."

**Bearing on this project.** KNOWLEDGE 8–12 puts a free move at **+0.196 ± 0.028 of utility**
(deep10; `_e4` +0.1953 ± 0.0278) with ply, count, open boards, empties, side and macro threats
controlled, cluster-robust by game over 30,000 natural positions — and shows it is largest late
and when ahead (+0.30 at plies 44–50 on `_e4`), that the raw value head over-credits it by a
stable ≈ 0.09 across three nets, and that granting it by editing the tensor overstates it 2×.
**No published number of this kind exists for UTTT in any variant.** The nearest comparator in
the whole literature is the integer "2" in a 2016 course project's heuristic. The correct claim
for a paper is therefore: first regression-controlled valuation of the free move, with an
explicit warning (from claim 12) that tensor-edit counterfactuals are upper bounds — which is
itself a methodological point the interpretability literature (§5) does not make.

### 3.3 Folk claims, game length, decisiveness, and the count rule

- **"Never send the opponent to a board where one move wins it."** Stated as a rule by gPress
  and implied by the human guides; the rigorous version is nelhage's macro-line-only statement
  above. The project tests it and finds it **false as a general rule** (KNOWLEDGE 33: deep10's
  256-sim move does it in 24 % of positions and *the solver's optimal move does it 69 % of the
  time*) while confirming the macro-line form exactly (KNOWLEDGE 34: 0.0 % of 3000+ solved
  positions hand the opponent an immediate macro win when the mover is not already lost). I
  found no prior published test of a UTTT folk rule against a solver.
- **Game length.** FLAIRS 2022: "a typical game lasting at least 30 moves." Baker et al.: ~50–58
  plies in decisive heuristic games. uttt.ai's self-play: 40–50 plies, ~7 legal moves per
  position. hodina.net *(blog)*: "Most of the games finish in 50-60 moves." The project measures
  mean 52.8 plies (p10 47, p90 59) and **rising with strength** (v2a 49.4 → deep10 51.9 → `_e4`
  52.8), with 5.08 free moves per game and 98.5 % of games containing one (KNOWLEDGE 27). The
  free-move frequency has no prior comparator at all.
- **Draw rate under strong play.** The one published datum is SaltZero's **48 % draws** in 200
  games at 400 ms/move (CLOSED/**DRAW**); gPress's opinion is that the game "likely is" a draw
  under perfect play. The project measures 13 % (deep10) → **16.6 %** (`_e4`) under
  CLOSED/**COUNT** and notes draws are still rising while X's share is flat (KNOWLEDGE 24), and
  that 96.3 % of its draws are 4–4 with one full board (KNOWLEDGE 26). The two tiebreaks are not
  comparable head-to-head, which is precisely the point worth making: the count rule converts
  most of what would be draws into decisions, and the residual 16.6 % is a different object from
  SaltZero's 48 %.
- **The count rule's frequency.** Daporan's 2018 objection when the tiebreak was introduced
  *(forum)* predicted the first player "can now focus on controlling small boards, which is easy,
  while preventing player 2 from making a line, which is also easy" — a qualitative prediction
  nobody has ever tested. **No source found quantifies how often the most-boards tiebreak decides
  a game.** The project does: 16.5 % end by a board count and 16.6 % by an equal count, 67.0 %
  by a macro line on `_e4` — and the share *moved* (from a flat 25 % over 250 Elo to 33 % in the
  last 120 Elo, KNOWLEDGE 25). That is a genuinely unclaimed fact about the CodinGame ruleset.
- **When games are decided.** No prior work on UTTT. The project's retrospective
  prediction-stability measure (median settle at ply 36 of ~51 on the held-out v2a games and 34 on strong play; 21 % at ply 0; 60 % by ply 36 on
  `_e4`, KNOWLEDGE 20–22) has no comparator; the nearest analogue in the wider literature is
  AlphaZero's per-move value curves in ELF OpenGo's Figure 1
  ([Tian et al., ICML 2019](http://proceedings.mlr.press/v97/tian19a/tian19a.pdf)) *(conf)*,
  which are illustrative rather than statistical.

---

## 4. Methodology comparator A: updates per self-play position ("sample reuse")

This is the section that matters most for the project's headline training result. Definitions
first, because the literature uses at least four incompatible ones.

**The project's lever, stated in comparable units.** From `runs/deep8_c1_300_e8/config.json` and
`uttt/train2.py:356`, `n_steps = epochs · games · steps / batch` with `games = 4096`,
`steps = 64`, `batch = 1024`. So each iteration generates **262,144 new positions** and trains on
**262,144 · epochs samples** drawn from a 2 M-position window (≈ 7.6 iterations deep). The
`epochs` knob is therefore *exactly* the **sample-reuse ratio**: each self-play position is used
≈ 1, 2, 4 or 8 times over its life in the buffer. (Exact endgame labels *overwrite* the value targets of existing rows —
`uttt/selfplay_cont.py apply_exact` — rather than adding rows, so the ratio is `epochs` to three
decimals: `_e8`'s log gives 629 145 600 rows sampled over 78 536 533 positions generated, **8.0109**;
M0's recomputation for the four runs is 1.0026 / 2.0027 / 4.0054 / 8.0109. An earlier form of this
sentence said "≈ 0.97 × epochs" on the assumption that the 8,192 exactly-solved positions per
iteration were added rows; corrected 2026-09-12.) Measured result:
**+100 → +64 → +40 Elo per doubling, 1 → 2 → 4 → 8, at fixed data and fixed architecture** —
+204 Elo in total, for +8.7 h of training on runs of 17–22 h.

### 4.1 What published AlphaZero systems actually use

| System | Stated ratio | In reuse units (times each position is trained on) | Source |
|---|---|---|---|
| AlphaGo Zero | 7 self-play games per training minibatch | ≈ **1.4** | ELF supplement *(conf)* |
| AlphaZero (chess/shogi/Go) | 30 games per minibatch; 700 k steps × batch 4096 | ≈ **0.5–0.7** | ELF supplement; [Lc0 training-runs wiki](https://lczero.org/dev/wiki/training-runs) computes 0.69 with resign / 0.48 without *(docs)* |
| ELF OpenGo | 13 games per minibatch | ≈ **0.8** | [Tian et al., ICML 2019, supplement §A](http://proceedings.mlr.press/v97/tian19a/tian19a-supp.pdf) *(conf)* |
| Leela Chess Zero | "sampling ratio" tracked explicitly; Main run 14.22 → 3.55 → 0.47; Test 10 = 0.95; Test 20 = 0.89 | **0.5 – 14** over the project's history, settling near **1** | [Lc0 training-runs wiki](https://lczero.org/dev/wiki/training-runs) *(docs, last updated 2020-11-28)* |
| KataGo | `-max-train-bucket-per-new-data 4`, i.e. "allowed to perform 4 training steps (measured in rows or samples, not batches) per data row generated by selfplay" | **≤ 4**, documented as conservative | [SelfplayTraining.md](https://github.com/lightvector/KataGo/blob/master/SelfplayTraining.md) *(docs)* |
| MiniZero (9×9 Go / 8×8 Othello) | 2,000 games per iteration, 200 steps × batch 1024 | ≈ **1.0–1.3** | [arXiv:2310.11305](https://arxiv.org/abs/2310.11305) *(arXiv/conf)* |
| pgx Gumbel-AlphaZero example | no replay buffer; each iteration trains on its own data | ≈ **1** | [Koyamada et al., NeurIPS 2023](https://arxiv.org/abs/2303.17503) *(conf)* |
| McGrath et al.'s AlphaZero reproduction | 1 M gradient steps × batch 4096 from a 1 M-position buffer, ≤ 30 positions sampled per game | very high, but with per-game subsampling explicitly "to reduce overfitting" | [arXiv:2111.09259](https://arxiv.org/abs/2111.09259) *(journal, PNAS)* |

*Caveat on the middle column: only Lc0 and KataGo publish the reuse ratio directly. The AGZ / AZ
/ ELF / MiniZero entries are **my conversions** from the stated games-per-minibatch figures,
assuming ~200 positions per 19×19 Go game (~75 for 9×9) and each system's published batch size;
they are accurate to about ±30 %, which is enough to place them all near 1 and nowhere near 8.
The Lc0 conversion is independently confirmed: the Lc0 wiki's own arithmetic gives AlphaZero 0.69
with resign and 0.48 without, matching the 30:1 figure at batch 4096.*

**The two explicit warnings in the literature, both about going higher:**

1. **ELF OpenGo** *(conf)*: "our ratio of selfplay games to training minibatches with a single
   training worker is roughly 13:1. For comparison, AlphaZero's ratio is 30:1 and AlphaGo Zero's
   ratio is 7:1. **We found that decreasing this ratio significantly below 10:1 hinders training
   (likely due to severe overfitting)**"
   ([supplement §A](http://proceedings.mlr.press/v97/tian19a/tian19a-supp.pdf)). Decreasing
   games-per-minibatch = increasing updates per position. Their floor of 10:1 corresponds to a
   reuse ratio of roughly **1.0–1.3** in 19×19 Go.
2. **Leela Chess Zero** *(forum/issue)*,
   [leela-zero#1480](https://github.com/leela-zero/leela-zero/issues/1480): in a no-gating setup
   "it was calculated that any single position was used **~12 times per training**", the value
   head overfitted and strength regressed, and the fix was dropping `value_loss_weight` to 0.25;
   the sampling ratio was subsequently reduced by tying training steps to the rate of game
   generation. The Lc0 wiki states the folk rule directly: "Sampling Ratio: How many times each
   position from self-play games is used for training. **Too high and your net may overfit.** Too
   low and your progress is too slow"
   ([Neural Net Training](https://lczero.org/dev/wiki/neural-net-training)) *(docs)*.

**KataGo's relevant side-evidence** *(arXiv/conf)*, Wu, ["Accelerating Self-Play Learning in
Go", arXiv:1902.10565](https://arxiv.org/abs/1902.10565): the window grows sublinearly,
`N_window = c(1 + β((N_total/c)^α − 1)/α)` with c = 250,000, α = 0.75, β = 0.4, from 250 k
samples to ~22 M; and in the FixedN = 600 ablation "the window size was also doubled, as an
informal test without doubling showed **major overfitting due to lack of data**." KataGo also
recommends "spending anywhere from 4x to 40x more GPU power on the selfplay than on the
training" *(docs)*. **KataGo never varies the reuse ratio as an experimental arm** — its 9.1×
efficiency ablation table covers playout-cap randomisation (1.37×), forced playouts + policy
target pruning (1.25×), global pooling (1.60×), auxiliary opponent policy (1.30×), ownership +
score targets (1.65×) and Go-specific inputs (1.55×), and no data/updates arm.

*(A naming caution for the write-up: the brief's "Accelerating and improving AlphaZero (Wu
2019)" conflates two papers. Wu, D. J., "Accelerating Self-Play Learning in Go"
([arXiv:1902.10565](https://arxiv.org/abs/1902.10565)) is KataGo. Wu, T.-R., Wei, T.-H. and Wu,
I.-C., "Accelerating and Improving AlphaZero Using Population Based Training"
([AAAI 2020](https://ojs.aaai.org/index.php/AAAI/article/view/5454),
[arXiv:2003.06212](https://arxiv.org/abs/2003.06212)) *(conf)* is a different result: dynamic
hyperparameter tuning via a 16-agent population, reaching "up to 74 % win rate against ELF
OpenGo" on 19×19 Go against 47 % for the non-PBT agent under the same conditions. Cite both, and
keep them apart.)*

### 4.2 The one study that ran the same lever and got the opposite sign

**Wang, Emmerich, Preuss, Plaat, "Analysis of Hyper-Parameters for Small Games: Iterations or
Epochs in Self-Play?"** *(arXiv 2020; journal version 2022 as "Analysis of hyper-parameters for
AlphaZero-like deep reinforcement learning",
[Leiden repository](https://scholarlypublications.universiteitleiden.nl/handle/1887/3502407))*,
[arXiv:2003.05988](https://arxiv.org/abs/2003.05988). Twelve hyper-parameters on
`alpha-zero-general`, mainly 6×6 Othello, with 5×5/6×6 Othello, Connect Four and Gobang for
follow-ups. Their epochs knob (`ep`) was tested at **5 / 10 / 15** — passes over the whole replay
buffer per iteration. Findings: "sometimes more training can not improve the playing strength but
decreases the training performance"; "the Elo rating of ep=10 is higher than that of ep=15 for
m=75"; "low epoch values achieves the highest Elo in a high iteration training session". Their
headline recommendation is the opposite of this project's result: "the number of self-play
iterations subsumes MCTS-search simulations, game-episodes, and training epochs … the overarching
outer-loop of self-play iterations should be maximized, in favor of the three inner-loop
hyper-parameters, which should be set at lower values."

**This is not a contradiction, and the write-up should say why.** Their *lowest* setting, ep = 5
passes over the whole buffer, is already far above this project's *highest* (8 passes over the
new data only, ≈ 1.05 passes over the 7.6-iteration window per pass). Read in reuse units their
result says the optimum is below their range, and this project's says it is above 1 — jointly
consistent with an optimum somewhere in between and a broad plateau. What both results do refute
is the idea that ≈ 1 is a principled setting rather than an inherited default. The right framing
for a paper: *the published default of ≈ 1 sample per generated position is a convention
inherited from 19×19 Go at scales where self-play is the bottleneck; at hobby scale on a small
game it is 200 Elo below the optimum, and nobody had measured the curve.*

### 4.3 The dose–response question in the wider RL literature

The concept the project's result belongs to is **replay ratio** / **update-to-data (UTD) ratio**,
studied systematically in model-free RL but not in AlphaZero-style board-game systems:

- **Fedus, Ramachandran, Agarwal, Bengio, Larochelle, Rowland, Dabney, "Revisiting Fundamentals
  of Experience Replay"** *(conf, ICML 2020)*,
  [PMLR v119](http://proceedings.mlr.press/v119/fedus20a.html) — the systematic study of replay
  capacity and replay ratio in Q-learning; establishes that the two interact and that
  conventional wisdom about capacity is wrong.
- **Nikishin, Schwarzer, D'Oro, Bacon, Courville, "The Primacy Bias in Deep Reinforcement
  Learning"** *(conf, ICML 2022)*, [arXiv:2205.07802](https://arxiv.org/abs/2205.07802) —
  identifies overfitting to early data as the failure mode at high replay ratio, and fixes it
  with periodic partial resets.
- **D'Oro, Schwarzer, Nikishin, Bacon, Bellemare, Courville, "Sample-Efficient Reinforcement
  Learning by Breaking the Replay Ratio Barrier"** *(conf, ICLR 2023 oral, top-5 %)*,
  [OpenReview](https://openreview.net/forum?id=OpC-9aBBVJe) — resets let agents be trained "using
  an order of magnitude more updates than usual", with large gains on Atari 100k and DMC.
- **Schwarzer et al., "Bigger, Better, Faster"** *(conf, ICML 2023)*,
  [arXiv:2305.19452](https://arxiv.org/abs/2305.19452) — super-human Atari 100K at a high replay
  ratio with network scaling.
- **Nauman et al., "Dissecting Deep RL with High Update Ratios: Combatting Value Divergence"**
  *(arXiv)*, [arXiv:2403.05996](https://arxiv.org/abs/2403.05996) — attributes the high-UTD
  failure to value divergence rather than primacy bias per se.

**Bearing on this project.** The replay-ratio literature lives entirely in single-agent
model-free RL on Atari/DMC, and its headline finding — that high replay ratios are *achievable*
once you add resets or regularisation — is about unlocking a regime that plain algorithms cannot
enter. This project's result is different in kind and simpler: an ordinary AlphaZero loop with no
resets, no regularisation changes and no architecture change gains 204 Elo by going from a reuse
ratio of 1 to 8, and the gains are still positive at the last doubling. That is the connective
tissue a paper wants: *the replay-ratio lever known to matter in model-free RL is unexploited in
AlphaZero-style board-game training, where published practice sits at ≈ 1 and the only documented
experiments went the other way.*

### 4.4 Scaling-law comparators for "how much is a doubling worth"

- **Jones, "Scaling Scaling Laws with Board Games"** *(arXiv)*,
  [arXiv:2104.03113](https://arxiv.org/abs/2104.03113) — AlphaZero on Hex 3×3 to 9×9, ~500
  GPU-hours over ~200 models, 2,800 snapshots, 700 M matches. Headline numbers: **"the slope of
  the incline is 500 Elo per order of magnitude increase in compute"**; **"for each additional
  10× of train-time compute, about 15× of test-time compute can be eliminated, down to a floor of
  a single-node tree search"**; the minimum compute for perfect play rises ~7× per board-size
  increment. Useful calibration: 500 Elo/decade is ≈ **150 Elo per doubling of total training
  compute**; this project's +100/+64/+40 are per doubling of the *optimizer-step* component only
  (self-play cost is unchanged), which is a strictly cheaper axis.
- **Neumann and Gros, "Scaling Laws for a Multi-Agent Reinforcement Learning Model"** *(arXiv; no
  venue recorded on the arXiv record — check before citing a conference)*,
  [arXiv:2210.00849](https://arxiv.org/abs/2210.00849) — AlphaZero on Connect Four
  and Pentago; Bradley-Terry strength scales as a power law in parameter count and in compute,
  with nearly identical exponents across the two games, and concludes "previously published
  state-of-the-art game-playing models are significantly smaller than their optimal size, given
  the respective compute budgets", with larger models more sample-efficient at equal data.
  **This is in tension with the project's ladder**, where width 64→128 was +37, depth 6→8→10 was
  +23 then an unreplicated +35 (+9 on the second seed), and the update lever was +204 — i.e. at
  this scale the project is *not* parameter-bottlenecked. Worth stating explicitly and
  attributing to the regime (a 9×9 board, 2.46 M parameters, a data budget where 8× reuse still
  pays) rather than contradicting the scaling law.
- **Neumann and Gros, "AlphaZero Neural Scaling and Zipf's Law"** *(conf, NeurIPS 2025)*,
  [arXiv:2412.11979](https://arxiv.org/abs/2412.11979) — game states in AlphaZero training and
  inference data are Zipf-distributed, offering a quanta-based account of the power laws;
  notably reports that on chess-puzzle accuracy "changing the state frequency has a strong
  effect … favoring uniform sampling over sampling from the Zipf distribution", which is adjacent
  to this project's `dedup_alpha` deduplication and worth a sentence.

---

## 4b. Methodology comparator B: exact group-equivariant networks for board games

The project's finding (RETROSPECTIVE §2 addendum 2026-09-09; KNOWLEDGE 50, 41b): the same recipe
with the ResNet trunk replaced by an exactly D4-equivariant group convolution, **exported to
ordinary convolutions so inference costs the same**, is −220 Elo [−242, −199] against its parent
and −50 below the 1×-update ResNet of the same shape. Exact symmetry held throughout (D4
Jensen-Shannon 0.000 bits at all 30 checkpoints). At matched *parameters* (`gcnn8x46`, 2.46 M
params, 7.0× the inference cost) it fits better early and is overtaken by 12,480 steps — it
over-fits. Separately, a one-call exactly equivariant *canonicalisation* of a plain net is a
strength null (+3 Elo / −3 Elo across two nets), while averaging the 8 orientations is +35 Elo at
8× the inference — an ensembling gain, not an equivariance gain.

**What the literature contains:**

- **Cohen and Welling, "Group Equivariant Convolutional Networks"** *(conf, ICML 2016)*,
  [arXiv:1602.07576](https://arxiv.org/abs/1602.07576) — the foundational claim that G-CNNs
  "reduce sample complexity by exploiting symmetries" and "increase the expressive capacity of
  the network without increasing the number of parameters". Vision, not games.
- **Carroll and Beel, "Finite Group Equivariant Neural Networks for Games"** *(arXiv, Sep 2020)*,
  [arXiv:2009.05027](https://arxiv.org/abs/2009.05027) — the only work I found that builds
  equivariant nets specifically for board games. Argues existing G-CNNs "lack the expressiveness
  to correctly reflect the move embeddings necessary for games", introduces FGNNs (equivariant
  nets with skip connections and arbitrary layer types), and reports that they "improve the
  performance of networks playing checkers". **The abstract gives no numbers, I found no peer-
  reviewed version, and the reported setting is supervised, not self-play.** So: a positive
  claim, weakly evidenced, in a different training regime.
- **Suen and Alonso, "Switchable Lightweight Anti-symmetric Processing (SLAP)"** *(conf, AISB
  2023)*, [arXiv:2301.04746](https://arxiv.org/abs/2301.04746) — the closest published analogue
  to this project's negative result. SLAP is a canonicalisation protocol (same output for every
  transformed variant) replacing data augmentation. Supervised on Gomoku game states it
  "improved the convergence speed of convolutional neural network learning by **83 %** … with
  only **one eighth of the sample size** compared with data augmentation". But in AlphaZero-style
  self-play on Gomoku it "reduced the number of training samples by a factor of 8 and achieved
  similar winning rate" while **"it was not yet evident that it could speed up reinforcement
  learning."** The same split this project measured: a real supervised-data advantage that does
  not convert into self-play strength.
- **Equivariance in RL generally** — van der Pol et al., "MDP Homomorphic Networks" *(conf,
  NeurIPS 2020)*, [arXiv:2006.16908](https://arxiv.org/abs/2006.16908); Mondal et al., "Group
  Equivariant Deep Reinforcement Learning" *(arXiv)*,
  [arXiv:2007.03437](https://arxiv.org/abs/2007.03437); Deac et al., "Equivariant MuZero"
  *(arXiv)*, [arXiv:2302.04798](https://arxiv.org/abs/2302.04798), which targets generalisation
  in learned world models rather than strength on a fixed board.
- **When exact equivariance is the wrong prior** — "Approximate Equivariance in
  Reinforcement Learning" *(arXiv)*,
  [arXiv:2411.04225](https://arxiv.org/abs/2411.04225), and "Partially Equivariant Reinforcement
  Learning in Symmetry-Breaking Environments" *(arXiv)*,
  [arXiv:2512.00915](https://arxiv.org/abs/2512.00915) (author lists not verified here).
  **These do not explain this project's
  result**: UTTT's D4 symmetry is exact (the send rule commutes with the group — a point
  independently asserted in pc29277's README), so the failure is not symmetry breaking. The
  project attributes it to capacity, and the frozen-data evidence (supervised advantage 0.078 of
  dev policy KL at 3,120 steps → 0.027 at 6,240 → reversed by 12,480) supports that.
- **Why G-convolutions can be redundant** — Lengyel et al., "Exploiting Learned Symmetries in
  Group Equivariant Convolutions" *(arXiv)*,
  [arXiv:2106.04914](https://arxiv.org/abs/2106.04914): G-conv filters become "highly redundant"
  under identified conditions and can be decomposed into depthwise-separable convolutions while
  preserving equivariance. Relevant as a capacity-side explanation.
- **What the strong systems actually do.** AlphaZero explicitly "does not augment the training
  data and does not transform the board position during MCTS"
  ([Silver et al., Science 2018](https://arxiv.org/abs/1712.01815)) *(journal)* — chess is not
  symmetric. AlphaGo Zero, Leela Zero and KataGo use **8× dihedral data augmentation with an
  ordinary CNN**, not an equivariant architecture. KataGo additionally **averages the policy head
  over board symmetries at the search root at play time**, documented externally by Wang et al.,
  "Adversarial Policies Beat Superhuman Go AIs" *(conf, ICML 2023)*,
  [PMLR v202](https://proceedings.mlr.press/v202/wang23g/wang23g.pdf): "KataGo will pass in
  different rotated/reflected copies of the game-board and average their results in order to
  obtain a more stable and symmetry-equivariant policy." **That is exactly this project's +35 Elo
  symmetry-averaging result (KNOWLEDGE 41), independently arrived at, and it is the first
  quantification of that trick I could find** — KataGo does it without publishing an Elo figure
  for it, and without the equal-inference control the project ran (at 8× sims instead, plain
  search wins by 201 Elo).

**Bearing on this project.** The literature's prior is that equivariance helps sample efficiency
(Cohen & Welling; Carroll & Beel; MDP homomorphic nets). The only published self-play test of a
symmetry-exploiting method on a board game (SLAP) found the supervised gain did not transfer.
This project is, as far as I can find, **the first measurement of an exactly equivariant
architecture in a full AlphaZero self-play run on a symmetric board game at matched inference
cost, and it is a clean negative** — with the matched-parameter arm separately showing
over-fitting, and the equal-cost/equal-parameter distinction made explicit (a distinction the
equivariance literature almost never draws, since it habitually matches parameters and lets
compute inflate).

---

## 5. Interpretability and probing of game-playing networks

The base references are already in `05-strategy-probing-and-interpretability.md` (McGrath et al.,
PNAS 2022; Schut et al., PNAS 2023/25; Pálsson et al., IJCAI 2023 and ECAI 2024; Jenner et al.,
NeurIPS 2024; Li et al., Othello-GPT; Lovering/Forde et al. on Hex; Hammersborg & Strümke,
Scientific Reports 2023; Piette et al., IEEE CoG 2021; Baier & Kaisers). What follows is what the
2025–2026 literature adds, and what is directly comparable to this project's probe results
(KNOWLEDGE 36–41a).

**Directly comparable, and the closest methodological precedent:**

- **Lovering, Forde, Konidaris, Pavlick, Littman, "Evaluation Beyond Task Performance: Analyzing
  Concepts in AlphaZero in Hex"** *(conf, NeurIPS 2022)*,
  [arXiv:2211.14673](https://arxiv.org/abs/2211.14673). The template this project's §8 follows:
  pair **probing** with **behavioural tests**, on a board game of comparable scale. Two findings
  that matter here: MCTS can encode a concept before the raw network does (so bare-network
  probing understates the agent), and short-term/endgame concepts localise to late layers while
  long-term concepts sit mid-trunk. The project's claim 38 — "tactics are shallow and early,
  value is deep and late", local concepts readable by block 5 and learned in the first 60
  iterations, macro-line threats peaking mid-trunk and fading toward the heads, value-like
  concepts in the last blocks stepping at the LR drop — is the same shape, replicated on four
  independently trained nets. **That four-net replication is the part the literature does not
  have**; McGrath and the Hex work each probe one training trajectory.
- **Pálsson and Björnsson, "Empirical Evaluation of Concept Probing for Game-Playing Agents"**
  *(conf, ECAI 2024)*, [IOS Press](https://ebooks.iospress.nl/doi/10.3233/FAIA240574): linear
  probe accuracy is an unreliable proxy for causal importance; more complex probes plus amnesic
  (nullspace) probing are recommended. The project's claim 38a is a direct response — a
  one-hidden-layer probe on a *randomly initialised* net reads macro threats at R² 0.81–0.83 and
  "the mover can win this move" at 98 %, so those are simple board functions that training only
  linearises (non-linear-control gains of +0.06 and +0.02); what survives the non-linear control
  is dead boards (R² 0.05 → 0.56), the exact value of ≤14-empty positions (68 → 89 %), the
  search's best move (+17), an available local win (+13), the move two plies on (+6) and the
  game result (+5). **Running a random-init non-linear control as a routine baseline is not
  standard practice in this literature and should be presented as a methodological
  contribution.**

**New since the project's notes (2025–2026), all *(arXiv)* unless marked:**

- **"Exploring Human-AI Conceptual Alignment through the Prism of Chess"**,
  [arXiv:2510.26025](https://arxiv.org/abs/2510.26025) — a 270 M-parameter grandmaster-level
  chess transformer: early layers encode human concepts (centre control, knight outposts) at up
  to 85 % accuracy, **deeper layers, despite driving the superior performance, drift toward alien
  representations, dropping to 50–65 %**. Introduces a Chess960 dataset to separate concept
  robustness from memorisation. Directly relevant contrast: the project finds the *opposite*
  layer profile (nameable tactical concepts early and shallow, value-like concepts deep and
  late), which is probably an architecture and task-scale difference worth a sentence rather than
  a disagreement.
- **"Tracing the Thought of a Grandmaster-level Chess-Playing Transformer"**,
  [arXiv:2604.10158](https://arxiv.org/abs/2604.10158) — sparse replacement layers decomposing
  Leela Chess Zero's MLP and attention into interpretable pathways.
- **Zhao et al., "Understanding the learned look-ahead behavior of chess neural networks"**,
  [arXiv:2505.21552](https://arxiv.org/abs/2505.21552) — extends Jenner et al.; the look-ahead is
  "highly context-dependent" and the network can carry board information up to **seven moves
  ahead**. Comparator for the project's claim 39: the move two plies down the PV is decodable at
  44.8 % against a 37.8 % control on `_e4` (+7 points of gain, against +14 for the move it is
  about to play) — i.e. a convolutional UTTT trunk carries **much less** of its own future line
  than a chess transformer does. That is a publishable negative with a clean control, and the
  architecture difference (no square-to-token correspondence) is the obvious candidate
  explanation.
- **"The Algorithm Is Not the Behavior: Learned Priors Override Look-Ahead in a Chess-Playing
  Neural Network"**, [arXiv:2508.21380](https://arxiv.org/abs/2508.21380) — correct solutions
  (including mates) appear in intermediate layers and are systematically overridden in the final
  output ("forgotten" solutions). Adjacent to the project's claim 23 (intuition and search part
  company in the middlegame: 30.8 % move disagreement overall, 37.8 % at plies 30–39).
- **"When Search Teaches Style: Causal Internalization of Tactical Priors in AlphaZero"**,
  [arXiv:2504.14636](https://arxiv.org/abs/2504.14636) — Cross-Phase Prior Intervention switches
  a root-level tactical prior on and off independently in training and in evaluation, separating
  what search rents at test time from what the weights absorb. Methodologically close to the
  project's questions about what the net computes versus what the search supplies.
- **Su et al., "Demystifying MuZero Planning: Interpreting the Learned Model"**,
  [arXiv:2411.04580](https://arxiv.org/abs/2411.04580) — latent-state interpretation on 9×9 Go
  and Gomoku; relevant only if a MuZero arm is ever discussed.
- **"Tensor Product Representation Probes Reveal Shared Structure Across Linear Directions"**,
  [arXiv:2605.09967](https://arxiv.org/abs/2605.09967) — Othello; argues a bag of linear
  directions misses relational structure and factorises probes into square- and
  piece-embeddings. A pointer for anyone extending the project's probe suite.

**Interpretable surrogates / distillation** — comparators for KNOWLEDGE 41a (a 20-feature linear
surrogate reproduces deep10's 256-sim move in 41 % of positions and its value at R² 0.55, then
plays at **−661 Elo vs v2b and −943 vs deep10**): Bastani, Pu, Solar-Lezama, **VIPER** *(conf,
NeurIPS 2018)*, [arXiv:1805.08328](https://arxiv.org/abs/1805.08328); Coppens et al.,
"Distilling Deep RL Policies in Soft Decision Trees" *(conf, IJCAI 2019 workshop)*; Kohler et
al., "Interpretable and Editable Programmatic Tree Policies" *(arXiv, 2024)*,
[arXiv:2405.14956](https://arxiv.org/abs/2405.14956); Costa et al., "Evolving interpretable
decision trees for reinforcement learning" *(journal, Artificial Intelligence 2023)*. The pattern
in that literature is that compact trees **match** the teacher on Atari, CartPole, Lunar Lander
and grid worlds. The project's result is the opposite and more interesting: on a two-player game
with a real strength scale, a legible surrogate over exactly the concepts the rest of the
knowledge file validates retains almost none of the playing strength. **I found no prior
distillation study that reports the residual gap in Elo against a graded ladder of opponents**;
the standard report is return or accuracy. That framing — "the named concepts are correct and do
not carry the strength" — is worth making the paper's contribution rather than a footnote.

---

## 6. Exact solving, endgame databases, and solver benchmarks

### 6.1 UTTT specifically

**nelhage/ultimattt — Nelson Elhage (2020–2022)** *(blog + repo + docs)*,
[github.com/nelhage/ultimattt](https://github.com/nelhage/ultimattt),
[blog post](https://blog.nelhage.com/post/solving-ultimate-ttt/),
[minimax.dev/docs/ultimate](https://minimax.dev/docs/ultimate/). CLOSED/DRAW. Rust, 40-byte
bitboard positions with SIMD win checks, Zobrist hashing, combined two-level PN + DFPN with a
lock-free parallel transposition table, plus a positional-analysis layer that solves some moves
without search. Reported: solves positions "after about 20 ply (10 moves by each player) in a
few hours of search on my Ryzen 3900X"; full-game estimate "a few hundred million CPU-hours",
"$2M – $10M" of AWS time. Explicitly: "I currently do not see a clear way to build endgame
databases." **This remains the only serious UTTT solving attempt.** The only other repository I
found, [abdavis/ultimattt](https://github.com/abdavis/ultimattt), is a 2022 fork of it with no
new results.

Note the tool-level limitation the project inherits and works around: PN search "aim[s] to
produce a single boolean value … They do not contemplate the third possibility present in many
games (including Ultimate Tic Tac Toe), of 'forced draw under optimal play'"
([minimax.dev PN-search page](https://minimax.dev/docs/ultimate/pn-search/)). Under CLOSED/COUNT
the terminal condition is a *count comparison*, which is worse than a third outcome. The relevant
machinery is Saffidine & Cazenave's Multiple-Outcome PNS and, newer, **Kowalski et al.,
"Generalized Proof-Number Monte-Carlo Tree Search"** *(arXiv 2025)*,
[arXiv:2506.13249](https://arxiv.org/abs/2506.13249), which tracks proof numbers per player and
explicitly "generalizes the technique to be applicable to games with more than two [outcomes]" —
the closest off-the-shelf starting point for a count-based tiebreak, and worth citing in the
write-up's solver section.

**No UTTT endgame tablebase exists publicly, for any variant.** Repeated targeted searches turn
up only chess/checkers tablebase literature. This project's exact ≤1-open-board table
(`uttt/tablebase.py`; 19,683 × 2 × 27 = 1.06 M entries, 1 MB, built in 0.2 s, `06` §5 correction
of 2026-09-03) and its exact endgame test suites (`suites/endgame_v1/v3`, 3,000 solved positions
with 6–16 empties) appear to be the first of their kind for the game — though the honest framing
is that the K=1 table turned out to add nothing over the existing solver, and the useful frontier
(K=2) is not built.

### 6.2 Solver benchmarks worth citing for scale

| Game | Size | Result | Method / cost | Source |
|---|---|---|---|---|
| Connect Four | 4.53 × 10¹² reachable | Strongly solved, first-player win | Knowledge-based search (Allis 1988); Tromp's full database | [Tromp](https://tromp.github.io/c4/c4.html) *(docs)* |
| Pentago | 3.0 × 10¹⁵ | **Strongly** solved, first player wins | Exhaustive parallel **in-core retrograde analysis**, 4 hours on 98,304 threads of NERSC Edison | [Irving, arXiv:1404.0743](https://arxiv.org/abs/1404.0743) *(arXiv/journal)* |
| Checkers | ≈ 5 × 10²⁰ | Weakly solved, draw | Forward PN/alpha-beta + a **10-piece retrograde endgame database (3.9 × 10¹³ positions)**; ~18 years of cumulative effort | [Schaeffer et al., Science 2007](https://webdocs.cs.ualberta.ca/~jonathan/publications/ai_publications/checksolved.pdf) *(journal)* |
| Othello 8×8 | ≈ 10²⁸ | Weakly solved, draw | Forward alpha-beta backed by exact databases at 36 and 50 empties; ≈ 1.5 × 10¹⁸ positions examined on a supercomputer | [Takizawa, arXiv:2310.19387](https://arxiv.org/abs/2310.19387) *(arXiv)* |
| Go 5×5 (positional superko) | — | **First solution of the empty board** | Expected Work Search | [Randall, Müller, Wei, Hayward, arXiv:2405.05594](https://arxiv.org/abs/2405.05594) *(arXiv/conf)* |
| Hex 8×8 | — | Empty board solved **in under 4 minutes** | Expected Work Search | same |
| **UTTT, CLOSED (either tiebreak)** | **~10³³–10³⁸ (this project's estimate, `06` §2)** | **Unsolved; no partial-solve milestone published** | — | — |

Adjacent technique papers worth a line each in a solver-related section: **Wu, Wei et al., "Game
Solving with Online Fine-Tuning"** *(conf, NeurIPS 2023)*,
[arXiv:2311.07178](https://arxiv.org/abs/2311.07178) — uses an AlphaZero policy/value net as the
heuristic inside a solver and fine-tunes it online on the positions the proof actually needs,
which is the natural way to use this project's net for solving; **"Relevance-Zone Reduction in
Game Solving"** *(arXiv 2025)*, [arXiv:2510.00689](https://arxiv.org/abs/2510.00689);
**"Solving 7×7 Killall-Go with Seki Database"** *(arXiv 2024)*,
[arXiv:2411.05565](https://arxiv.org/abs/2411.05565) — a worked example of a small pattern
database cutting a solver's search space, the shape the project's K≤1 table was meant to have;
**"Massively Parallel Proof-Number Search for Impartial Games and Beyond"** *(arXiv 2025)*,
[arXiv:2511.10339](https://arxiv.org/abs/2511.10339) — the first PNS variant that scales
efficiently on many cores, addressing exactly the bottleneck nelhage hit;
**"Compressed Game Solving"** *(arXiv 2024)*, [arXiv:2411.07273](https://arxiv.org/abs/2411.07273)
— compression for endgame databases; and **"Semi-Strongly solved: a New Definition Leading
Computer to Perfect Gameplay"** *(arXiv 2024)*,
[arXiv:2411.01029](https://arxiv.org/abs/2411.01029), which introduces the intermediate notion of
certifying correctness on a reachable region R — a useful vocabulary for any partial claim this
project might make about the endgame.

---

## What the literature does not contain

Stated as candidate claims a paper could make. Each is what I could not find after the searches
above; each is falsifiable by one counter-citation, so each should be phrased in the paper as
"we are not aware of" rather than "none exists".

**About the game.**

1. **No published first-move value map for UTTT under any variant beyond five named openings on
   an undocumented scale.** The project's 15-orbit atlas across four nets and three search
   budgets, with stability measured (Kendall τ = 0.85–0.96) and one ordering reversal recorded at
   the top of the ladder, is the first.
2. **No published quantification of the free move.** The literature offers one integer (2 points,
   in a 2016 course heuristic) and prose. A regression-controlled +0.196 ± 0.028 of utility,
   stable to the third decimal across 120 Elo of strength, stratified by ply and count, with the
   raw head's over-crediting isolated at ≈ 0.09 and the tensor-edit inflation measured at 2×, is
   new and is the single most quotable game fact the project has.
3. **Nothing at all is published about the CodinGame most-boards tiebreak.** Not its frequency,
   not its effect on strategy, not a comparison against the draw rule — only a 2018 forum
   objection predicting it would favour the first player. The project can claim the first
   measurement: 16.5 % of strong games decided by board count, 16.6 % drawn on an equal count,
   67.0 % by a macro line, and the share moving with strength.
4. **No decisiveness statistics for UTTT.** When games become settled, by result, at what ply, and
   how that moves with strength, is unstudied.
5. **No prior test of a UTTT folk rule against an exact solver.** "Never send the opponent to a
   board where one move wins it" is stated as a rule everywhere and is false as a rule (the
   solver's optimal move does it 69 % of the time); the true statement is the macro-line-only
   version. This is a small, crisp, checkable result.
6. **The value of the closed-board game is open, and the count-rule variant has never been
   attacked at all.** Any statement the project makes here must stay empirical.

**About methodology.**

7. **No dose–response curve of playing strength against the sample-reuse / replay ratio exists
   for an AlphaZero-style board-game system.** Published practice clusters at ≈ 1 sample trained
   per position generated (AlphaZero ≈ 0.5–0.7, AlphaGo Zero ≈ 1.4, ELF ≈ 0.8, Lc0 settling ≈ 1,
   MiniZero ≈ 1–1.3, pgx ≈ 1), KataGo caps at 4 and calls it conservative, and the two explicit
   experiments in the literature are warnings in the *other* direction (ELF: below 10:1 "hinders
   training … severe overfitting"; Lc0 at ~12× reuse overfitted its value head). The one
   systematic study of the epochs knob (Wang et al. 2020, 6×6 Othello, ep ∈ {5,10,15}) recommends
   keeping inner-loop parameters low. **+100 / +64 / +40 Elo for reuse 1 → 2 → 4 → 8 at fixed
   data, fixed architecture and fixed self-play cost, with a pre-registered adoption rule and a
   measured seed band, is the contribution** — and the paper should say plainly that the
   published convention is a Go-scale inheritance, not a measured optimum, and that the curve was
   still positive where the project stopped.
8. **No prior measurement of an exactly equivariant architecture inside a full AlphaZero self-play
   run on a symmetric board game at matched inference cost.** The equivariance literature reports
   supervised or sample-efficiency gains at matched parameters; the one self-play test (SLAP,
   Gomoku) found the supervised gain did not transfer and said so. A clean −220 Elo at matched
   cost, plus a matched-parameter arm that over-fits, plus exact symmetry verified at every
   checkpoint (D4 JS = 0.000 bits), is a negative result the field lacks and the equal-cost versus
   equal-parameter distinction is itself the methodological point.
9. **No published Elo figure for symmetry-averaging at play time**, despite KataGo doing it by
   default. The project's +35 Elo [+17, +54] at 8× inference, together with the equal-inference
   control where the same averaging *loses* by 201 Elo to plain search at 8× the simulations, and
   the canonical-evaluator null (+3 / −3 across two nets) that separates the ensembling gain from
   the equivariance, is the first decomposition of that trick I could find.
10. **No published interpretability study of a game-playing net runs a random-initialisation
    non-linear probe as a routine control**, and Pálsson et al. (2024) identify precisely that
    gap. The project's 38a — showing that macro threats and "can win this move" are read off a
    *random* net at R² 0.81 and 98 %, so their apparent decodability is the encoding not the
    training — should be presented as a method, not an aside.
11. **No distillation study reports the surrogate's residual strength gap in Elo against a graded
    ladder.** The tree/formula-distillation literature reports return or fidelity, on single-agent
    tasks where the surrogate matches the teacher. "The named concepts are individually correct,
    reproduce 41 % of the teacher's moves and R² 0.55 of its value, and lose 661–943 Elo" is a
    different and sharper statement about what a legible account of a game leaves out.
12. **No cross-net replication in the probing literature.** McGrath probes one AlphaZero
    trajectory; the Hex work one agent. The project's concept grid repeats on four independently
    trained nets (two seeds at 10×128, plus deep8_300 and `_e4`) with the same layers, the same
    gains within a few points, and the learned-by column shifting 20–50 iterations earlier with
    strength. Replication across seeds is the cheapest credibility this project can buy and almost
    nobody in this literature has it.

**About the field's state, worth one paragraph in the paper's related work.**

13. **UTTT has no shared benchmark.** uttt.ai, SaltZero, tacult, pc29277 and the FLAIRS CNN each
    report against a private ladder; no two have ever played each other; two consumer sites claim
    to be "the strongest" with no evidence; and the only externally anchored result in the entire
    literature is SaltZero's 113–87 against a top-2 CodinGame bot in 2020, under a different
    tiebreak. The strongest agents that certainly exist on this project's exact rules — reCurse's
    and jacek's CodinGame bots — are unreleased and undocumented beyond two forum sentences. A
    calibrated, reproducible measurement kit (paired openings played from both sides, a fixed
    rollout anchor, seed replicates, a pre-registered adoption threshold) is therefore a
    contribution to this game independent of the agent's strength.

**Honest negatives — things I looked for and did not find, which may exist.**

- Any UTTT work published between the project's 2026-08-29 sweep and today other than
  pc29277/AlphaZero_UTTT (created 2026-08-19, found in this pass).
- A peer-reviewed version of Carroll & Beel's FGNN paper, or any numbers from it.
- Any independent benchmark of uttt.ai, in five years.
- Any measured (rather than asserted) first-player win rate for UTTT under strong engine play.
- Any UTTT endgame database, or any "solved from ply N" claim for UTTT.
- Any replay-ratio/UTD study on a two-player board game.
- Royer's unpublished best-reply matrix, and uttt.ai's per-depth position histograms as summary
  statistics rather than raw files.
