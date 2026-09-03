# What uttt-zero believes about Ultimate Tic-Tac-Toe

*The claims file. One belief per line, with the evidence attached. Started 2026-09-03 from
PLAN5 Phases A and B; the opening book (C1) and the deep8 replications are added as they
finish. This is where a claim lives; PLAN5 §2–§3 hold the working notes, RETROSPECTIVE §6
the earlier form of the same beliefs.*

## How to read a claim

Every line carries:

- **a level** — *behavioural* (what the agent does), *predictive* (what its value head
  forecasts), *search-relative* (the number depends on the search budget it was measured
  with), *exact* (checked against the solver), or *descriptive* (a count over games);
- **an effect size with its 95 % CI** where there is one. Values are in units of expected
  score for the side to move (+1 = certain win, 0 = even, −1 = certain loss) unless the
  line says otherwise. Elo is always *vs a named opponent at a named number of sims*;
- **held across** — the nets on which the claim was tested. "Both strong nets" means
  `deep10_c1_300/net_0300.pt` (+242 Elo vs v2b @64) and `deep8_c1_300/net_0300.pt` (+211);
  "all nets" adds dev1, v2a, v2b (250–340 Elo weaker). A claim that held from dev1 to deep10
  survived a 340-Elo span; a magnitude is quoted from the strongest net;
- **the tool and the output file** so the number can be regenerated.

Rules used throughout (PLAN5 §1c): orderings and signs are trusted when they hold across
nets; magnitudes are quoted but expected to drift with strength; no result under the
±3-point rule on the paired suite is called a strength difference; nothing is claimed from
probe accuracy alone; "the net cannot represent X" is never said of a net that was not
trained to convergence.

The board: `m = 9*board + cell`, both row-major; **[40]** is the centre cell of the centre
board, [13] the centre cell of the top-centre board. Boards are called *centre* (4),
*corners* (0, 2, 6, 8) and *edges* (1, 3, 5, 7).

## 1. The opening

1. **[40] — centre of the centre board — is the best first move** on every net and every
   budget tested, and **[13] the worst**: rank 1 and rank 15 in all 9 columns of the atlas
   (v2b, deep8_300, deep10 × 1k / 4k / 16k sims, symmetry-averaged), as they were for dev1
   and v2a. *Search-relative; all nets.* `tools/atlas.py` → `runs/plan5_A1_atlas.out`,
   `runs/step7a.out`.
2. **The first-move ordering is stable across 340 Elo**: Kendall τ between deep10@16k and
   v2b@16k is 0.96, deep8_300 vs v2b 0.92; the top four are [40] > [36] > [0] > [37] on
   every strong column (centre-centre, then the centre board's corner and the corner
   board's corner and edge). *Search-relative; all nets.* Same files.
3. **X's edge after [40] is rated +0.447 by deep10 at 16k sims** (v2b: +0.354; dev1: +0.28).
   The *magnitude* rises with strength and is not trusted; the *sign* and the gap to the
   next move (+0.11 to [36]) are. *Search-relative.* Same files.
4. **Openings are flat: the choice of reply hardly matters.** The root Q-gap between the
   two most-visited replies at 16k sims is ≤ 0.03 in 13 of 15 first-move orbits.
   *Search-relative; v2b and both strong nets.* Same files.
5. **The two exceptions are the orbits whose best reply is to take [40]:** after [13] the
   gap is 0.116 (v2b 0.079), after [4] it is 0.057 (v2b 0.017). The only opening edges a
   stronger net has *found* are "answer by taking the centre of the centre board".
   *Search-relative; grew with strength.* Same files.
6. **The opening is learned first.** Both 300-iteration nets put ≥ 0.95 of the raw
   first-move probability on [40] from iteration 20–30 on (deep8_300: 0.09 at iteration 10,
   0.79 at 20, 0.98 at 30) and never broaden again. *Descriptive of training.*
   `tools/timeline.py` → `runs/*/timeline.json`.
7. **The opening book** (`tools/book.py`, depth 4, top-3 replies per node, 16 384 sims,
   symmetry-averaged; `runs/book_deep10.md`, `runs/book_deep8.md`): the first-move values
   reproduce the atlas ordering ([40] +0.447 … [13] −0.047), and the paired-suite X score
   by opening follows it (74 % after [40] or [36], 69 % after [0], 45–51 % after [9], [8]
   and [13]). **The two strong nets choose the same most-visited move in 75 % of the 341
   nodes they share** (mean value difference 0.016), and disagree only where the book is
   flat — after [40] the top reply's visit share is 0.19 / 0.14 and the nets differ; where
   a reply's share is ≥ 0.7 they agree. *Search-relative; both strong nets.*
7a. **The reply rule the book contains: the self-send.** The most-visited reply is the
   cell whose index equals the board the mover was sent to — sending the opponent straight
   back into the board you just played in — in **52 % (deep10) / 57 % (deep8_300)** of
   the nodes where that cell is free, at every depth to 4, with a higher visit share when
   chosen (0.83 vs 0.73 for other replies). "Take the centre of the board you were sent
   to" is *not* the rule (the top reply is the centre cell in 4 % of nodes). *Behavioural;
   both strong nets.* `tools/book_stats.py`.

## 2. Tempo: the free move

8. **A free move is worth about +0.2 of expected score** to the side that gets it, with
   ply, count, open boards, empties, side and macro threats controlled: **+0.196 ± 0.028**
   (deep10, 256-sim values, 30 000 natural positions, cluster-robust by game); deep8_300
   +0.192 ± 0.027; v2b +0.163 ± 0.027. Same sign on every net; the magnitude grew a third
   and then stopped (the two strong nets agree to 0.004). *Search-relative; all nets.*
   `tools/freemove.py` → `runs/plan5_A4_freemove_deep10_on_deep8late.out`,
   `runs/plan5_A4b_freemove_deep8_on_deep10late.out`, `runs/step7b_freemove.out`.
9. **Half of that is the option to end the game at once.** With "the mover can complete a
   macro line this move" in the model (+0.675 ± 0.059 on its own; deep8_300 +0.625 ±
   0.056), the free-move coefficient is **+0.084 ± 0.026** (deep8_300 +0.102 ± 0.026): a
   free move is worth ≈ +0.08 … +0.10 as tempo and the rest as the chance to cash a macro
   threat immediately. *Search-relative; both strong nets.* `tools/value_decomp.py` →
   `runs/plan5_B3_value_deep10.out`, `runs/plan5_B3_value_deep8.out`.
10. **It is largest late, when level or ahead:** +0.25 at plies 44–50 with the count level
    or better, +0.03 at plies 32–43 (stratified check). *Search-relative; deep10, v2b.*
    `plan5_A4_*.out`.
11. **The value head over-credits it:** raw-head coefficient +0.290 ± 0.030 vs +0.196 for
    the search — a 0.094 gap that was 0.094 on v2b too. Over training the raw coefficient
    falls (+0.19 → +0.14 in the fuller model) while the search's rises (+0.04 → +0.09):
    intuition converges toward search. *Predictive vs search-relative; all nets.*
    `plan5_A4_*.out`, `plan5_B3_value_deep10.out`.
12. **Editing the tensor overstates it 2×.** Granting a free move by editing the position
    moves the raw value by +0.41 (median +0.32; v2a-era +0.27), against +0.20 from natural
    positions. The overstatement itself is stable, so tensor-edit numbers are read as
    upper bounds. *Predictive; v2a, deep10.* `tools/probe_value.py` →
    `runs/plan5_B4_probe_value_deep10.out`.

## 3. Macro lines, board ownership, the count

13. **A macro-line threat (two own boards in a line, the third open) is worth ≈ +0.15, an
    opponent's ≈ −0.14**, controlling for everything else in the model: +0.154 / −0.140
    (deep10), +0.145 / −0.139 (deep8_300), +0.16 / −0.17 (v2b). *Search-relative; all
    nets.* `plan5_A4_*.out`.
14. **Owning a board is worth a little of its own — +0.03 … +0.08 — beyond the lines it
    sits on, and the number is not sharp.** With threats controlled, an own board adds:
    deep10 centre +0.070 ± 0.040, corner +0.065 ± 0.030, edge +0.056 ± 0.027 (A4's model),
    +0.076 / +0.079 / +0.066 (B3's fuller model, other positions); deep8_300 +0.051 /
    +0.030 / +0.037 and +0.031 (n.s.) / +0.044 / +0.041. Positive in all four fits,
    significant in most, centre not significant on deep8_300. On v2b this was
    indistinguishable from zero (+0.008 / +0.011 / +0.033). *Search-relative; moved with
    strength — both strong nets, at different sizes.* `plan5_A4_*.out`,
    `plan5_B3_value_deep10.out`, `plan5_B3_value_deep8.out`.
15. **Which class of board is worth most is not resolved.** deep10 orders centre > corner >
    edge, deep8_300 has edge highest; the differences are inside the CIs. The raw head's
    *counterfactual* hierarchy (flip a won board's owner: centre +1.05, corner +0.94, edge
    +0.83) is unchanged to the second decimal since v2a and is the line-count ordering
    (4 / 3 / 2 lines through the board) in disguise. *Predictive; all nets.*
    `plan5_B4_probe_value_deep10.out`, `runs/v2a/probe_surprise_rerun.out`.
16. **The raw board count is discounted as the net gets stronger.** The count-margin
    coefficient on the raw value falls from +0.106 (iteration 20) to +0.037 ± 0.010
    (iteration 300); the search's from +0.076 to +0.036. Early nets count boards; trained
    nets count lines and tempo. *Predictive / search-relative; deep10 checkpoints.*
    `plan5_B3_value_deep10.out`.
17. **Line counting is learned first and never moves:** the threat coefficients are at
    their final values by iteration 20 of 300. *Descriptive of training; deep10.* Same.
18. **An open board that becomes nobody's is worth nothing to the mover:** removing an open
    board for both sides moves the raw value by +0.017 (v2a: +0.06). *Predictive.*
    `plan5_B4_probe_value_deep10.out`.
19. **An opponent's immediate local threat costs ≈ −0.10** (−0.099 ± 0.014); an own
    immediate local win, once the macro win is separated, is worth nothing by itself
    (−0.026 ± 0.017). *Search-relative; deep10.* `plan5_B3_value_deep10.out`.

## 4. When games are decided

20. **Games are decided late — around ply 36 of ~51 — and nothing is settled by ply 30.**
    Median ply from which the 64-sim search's best-child value stops changing sign: **36**
    (quartiles 30–41) on 4000 held-out v2a games for both deep10 and deep8_300 (v2b: 38);
    the raw value settles at 41 (v2b 43); the mixed root value at 45. On stronger play
    (deep8_300's late games, mean length 51.9) the same: Q 36 (28–41), raw 42. *Predictive;
    all nets; the 2-ply shift from v2b saturated between the two strong nets.*
    `tools/decision.py` → `runs/plan5_A3*_decision_*.out`, `runs/step7c_decision.out`.
21. **X wins settle earlier (ply 32) than O wins (39–40) and draws (39–41).** *Predictive;
    all nets.* Same files.
22. *Caveat:* the "settled" statistic uses a ±0.33 threshold on a 3-way prediction; deep10
    rates the opening above +0.33 for X, so 10–17 % of X-win games count as settled from
    ply 0. Medians are robust to this, the 10th percentile is not.
23. **Intuition and search part company in the middlegame.** The raw policy's move differs
    from the 256-sim search's in 34 % of positions overall, 20 % at plies 2–9, **44 % at
    plies 30–39**, 24 % after ply 50; the raw value differs from the search value by 0.19
    on average, peaking at 0.35 at plies 40–49. Same shape on v2a. *Behavioural vs
    search-relative.* `tools/surprise.py` → `runs/plan5_B4_surprise_deep10.out`.

## 5. How games end

24. **X wins about 63 % of strong self-play games, O 24 %, 13 % are drawn** (deep10's
    iterations 280–299, 100 854 games at 64 sims with exploration; deep8_300 61 / 26 / 13;
    v2a 60 / 29 / 11). In paired matches between the strong nets X's share is 59–62 % and
    15–25 % of games are drawn. *Descriptive; rises with strength.*
    `tools/corpus_stats.py` → `runs/plan5_A6_corpus_*.out`; `runs/plan5_A8.out`.
25. **The count rule decides about a quarter of strong games:** 14 % end by a board count
    and 13 % by an equal count (a draw), 73 % by a macro line; flat since v2a (15 / 11 /
    74). *Descriptive.* Same.
26. **Nearly every draw is 4–4 with one full board:** 96.6 % of deep10's drawn games
    (deep8_300 97.0 %); 3–3 with three full boards is 3 %; the board-count lead changed
    hands during 63 % of draws; draws run 2 plies longer than the average game (53.8 vs
    51.9). *Descriptive; both strong nets.* `tools/principles.py` →
    `runs/principles_deep10.json`, `runs/principles_deep8.json`.
27. **Games last ~52 plies** (mean 51.9, p10 46, p90 58, max 72–75) and lengthen with
    strength (v2a 49.4). About 4.4 free moves occur per game and 97 % of games contain
    one. *Descriptive.* `plan5_A6_*.out`.

## 6. The endgame and what the raw policy misses

28. **The endgame is, in practice, solved by the agent with search:** on 3000 exactly
    solved positions with 6–16 empties, deep10's 256-sim search plays the optimal move in
    99.9 % (v1 set) / 99.7 % (v2_dev, strong-play positions) with regret 0.001 / 0.003;
    64 sims: 99.8 / 99.5 %. *Exact.* `tools/endgame.py eval` →
    `runs/plan5_A9_eval_*.out`, `runs/deep10_c1_300/analysis.out`.
29. **The raw value head names the exact result in 84.6 % of those positions** (95 % CI
    83.2–85.9; deep8_300 84.0; v2b 75.0; dev1 71.2), recognising **69 % of exact draws**
    (v2b 55 %), and its raw policy is optimal in 96.7 % with regret 0.037. *Exact; all
    nets.* Same.
30. **The yardstick was not flattered by being read 50 times during training:** on the
    fresh strong-play set `endgame_v2_dev` (split from `_test` by source game before
    solving) deep10 scores 84.7 [83.4, 85.9] — within 0.1 of v1. Draw recognition is
    higher there (72 %), raw-policy regret worse (0.048). *Exact.* `plan5_A9_*.out`.
    `endgame_v2_test` has not been read.
31. **"Draw blindness" was never a capacity limit.** The 150-iteration nets recognised
    ~55 % of exact draws at every width and depth; the annealed 300-iteration nets
    recognise 67–72 % with the same architecture, loss and labels. The step happens at
    the first learning-rate drop (deep8_300: 58.8 → 65.7 % between checkpoints 200 and
    210), and the draw metric wobbles by up to 20 points between adjacent checkpoints at
    constant LR. *Exact; deep8_300 and deep10 timelines.* `runs/*/timeline.json`,
    RETROSPECTIVE §3.
32. **What the raw policy still gets wrong late is the count rule and tempo, not local
    tactics.** On 6000 strong-play positions with ≤ 14 empties, deep10's raw move loses
    exact value in 2.1 % (v2b 3.5 %); the 64-sim search in 0.12 % (7 positions). Motifs of
    the failures, in the same order as on v2b: tiebreak conversion 71 > giving a free move
    61 > holding a draw 51 > denying a free move 37 > a local win 20 > closing a board 4 >
    a macro win 0. Local-tactics failures fell most (26 → 16 % of puzzles). *Exact; v2b and
    deep10.* `tools/puzzles.py` → `suites/puzzles_v2_dev.npz` (+ `.json`, the 5 hard
    puzzles), `runs/plan5_A7_puzzles_deep10_on_deep8late.out`.

## 7. Folk claims, tested

33. **"Never send the opponent to a board where one move wins it" is false as a rule.**
    deep10's 256-sim move does exactly that in **24 %** of positions (a random legal move:
    36 %) — 2 % in the opening, 25 % at plies 20–31, 51 % at 32–43, 67 % from ply 44 —
    and the **solver's optimal move does it 69 % of the time** on solved positions (64 %
    when the mover is winning, 51 % in drawn positions, 84 % when lost). deep8_300: 24 %
    and 70 %. *Behavioural and exact; both strong nets.* `runs/principles_*.json`.
34. **What is true instead:** the optimal move *never* hands the opponent an immediate
    macro win when the mover is not already lost (0.0 % of 3000+ solved positions), and
    the agent avoids sending to a winnable board early. The rule is a macro-line rule and
    an opening rule, not a general one. Same files.
35. **Conceding the centre board ("the Orlin gambit") costs what its lines cost, no more.**
    With threats controlled, the opponent owning the centre is worth +0.01 ± 0.04 on the
    search value (the raw head: −0.05 ± 0.04); the centre's premium in the raw head's
    counterfactual (+0.11 over a corner) is the fourth line through it. *Search-relative /
    predictive; deep10.* `plan5_B3_value_deep10.out`, `plan5_B4_probe_value_deep10.out`.

## 8. What the network computes (the net on its own terms)

36. **The board encoding already exposes** the free-move flag, the target board, the count
    margin, open boards, empties and every board's status: a linear read-out on a randomly
    initialised net recovers them at 98–100 %. No claim that the net "represents" these
    is meaningful. *Probe control; deep10.* `tools/probe.py`, `tools/probe_report.py` →
    `runs/deep10_c1_300/probes.{json,png}`.
37. **What the trunk computes, where, and when** (linear probe gain over the random-init
    control, on 10 000 held-out test positions; layer of best read-out; iteration at which
    90 % of the final gain is reached): dead boards (boards neither side can win) R² +0.48
    at block 5, by iteration 180; the exact value of ≤ 14-empty positions +25 points at
    block 10, by 180; the search's best move +16 points at block 10, by 220; macro threats
    for / against R² +0.15 at blocks 7–8, by 100–140; an available local win +13 points at
    block 5, by 60; an opponent's local threat +6 points at block 8, by 80; the game result
    +5 points at block 10, by 220. deep8_300, probed on deep10's games, gives the same
    gains within a few points, the same layers (tactics at block 5, value at the last block)
    and the same learned-by checkpoints (tactics 60–80, lines 80–120, value 180–220).
    *Decodability; both strong nets.* Same files; `runs/deep8_c1_300/probes.{json,png}`.
38. **Tactics are shallow and early, value is deep and late:** local concepts are readable
    by block 5 and learned in the first 60–80 iterations; macro-line threats peak in the
    middle of the trunk and fade toward the heads; the value-like concepts live in the last
    blocks and step at the LR drop, together with the endgame metrics they explain.
    Nothing new appears after iteration 240. *Decodability; both strong nets.* Same.
38a. **Which of those the trunk actually computes, and which it merely re-formats.** A
    probe with one hidden layer of its own reads macro threats off a *random* net at R²
    0.81–0.83 and "the mover can win the game this move" at 98 %: those are simple
    functions of the board that training only linearises (trained-vs-control gain with the
    non-linear probe: +0.06 and +0.02). The gains that survive the non-linear control —
    the computations training added — are dead boards (R² 0.05 → 0.56), the exact value
    of ≤ 14-empty positions (68 → 89 %), the search's best move (+17 points), an available
    local win (+13), the move two plies on (+6), the game result (+5). *Decodability with a
    non-linear control; deep10, six checkpoints.* `runs/deep10_c1_300/probes_mlp.json`.
39. **The trunk carries little of the line it is about to follow:** the move two plies
    down the search's principal variation is decodable at 38 % vs 34 % on the control
    (the current best move: 71 vs 56 %). *Decodability; deep10.* Same.
40. **The auxiliary ownership head learns almost nothing beyond the board.** It predicts
    the final owner of each board at 60.3 % (majority 41 %); a linear probe on the trained
    trunk gets 60.1 % — and on a *random* trunk 59.0 % (deep8_300: 59.9 / 61.8 / 60.9 %).
    This is why switching the auxiliary heads off was a null. *Decodability + behavioural
    null; both strong nets.* Same; RETROSPECTIVE §3.
41. **The net has not fully learned the board's symmetry, and it costs a rung.** The
    policy's Jensen–Shannon divergence across the 8 orientations is 0.05 bits for 200
    iterations, halves at the LR drop and ends at 0.027 (smallest in the opening, 0.010;
    largest in the middlegame, 0.034). Averaging the 8 orientations at play time beats the
    plain net **55.0 % [52.4, 57.7], +35 Elo [+17, +54]** at equal sims (8× the inference
    per sim) and adds +0.4 WDL points on the endgame set — but at equal inference the
    same averaging *loses* to plain search with 8× the sims, **23.9 % [21.8, 26.2], −201
    Elo**: the residual asymmetry is real and is cheaper to search through than to average
    away. *Behavioural; deep10.* `runs/deep10_c1_300/timeline.json`,
    `runs/plan5_B5_sym_vs_plain.out`, `runs/plan5_B5b_sym_equal_compute.out`.
42. **Where +127 Elo of "duration" came from:** ≈ +5 points of paired score from iterations
    150–200 at the constant learning rate and ≈ +8 from the first LR drop, at which every
    curve (score, endgame WDL, draw recognition, opening-policy entropy, D4 consistency)
    steps once; the second drop at 280 produces nothing visible. *Descriptive of training;
    both 300-iteration runs.* `runs/*/timeline.{json,png}`, PLAN5 §3 B1.

## 9. Strength (for reference; the full ladder is in RETROSPECTIVE §2)

43. **The ladder, vs v2b @64 sims on the frozen paired suite, final checkpoints:** dev1 −95,
    v2b 0, +c_scale 1.0 +40, +width 128 +77, +8 blocks +100, +300 iterations +211, +10
    blocks **+242** (≈ 80 % expected score). *Behavioural.* `runs/*/analysis.out`.
44. **At equal compute the deep, long-trained net wins for the first time:** deep10@64
    beats v2b@427 (6.7× the sims) by +42 [+23, +61]; but deep10@64 vs deep8_300@80 is −11
    [−30, +7] — the last rung is a wash at a fixed inference budget; duration, not depth,
    is where deployment strength came from. *Behavioural.* `runs/plan5_A8.out`.
45. **The phased search schedule ("0:128,24:384") is not confirmed on the best net:** +10
    [−7, +26] vs a flat 256 (was +50 on v2b, +26 on deep8_300) — the stronger the raw
    policy, the less late search adds. Play config: flat `--sims 256` or more.
    *Behavioural.* Same.

## 10. Open, and not claimed

- The opening book stops at depth 4 with three replies per node; nothing is claimed about
  lines beyond it.
- Whether the +0.03 … +0.08 per owned board (14) and the class order (15) survive a seed replicate
  (PLAN5 §5 D1 — not run; owner's call).
- The self/opponent asymmetry in the ownership coefficients flips between the raw and the
  search value and is not reported.
- `endgame_v2_test` is unread; it is read once, at the end of PLAN5.
- The five hard puzzles are annotated in `docs/positions.md` (C3); a larger annotated set
  (the top surprises of B4) is not.
- A legible surrogate's Elo (B6) — not built.
- The ≤ 1-open-board tablebase (C5) — not built; B3 says the value head's remaining
  error is tactical-horizon (the ply and empties terms and the macro-win-in-one), which
  is what it would grade.
