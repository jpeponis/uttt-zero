# What uttt-zero believes about Ultimate Tic-Tac-Toe

*The claims file. One belief per line, with the evidence attached. Started 2026-09-03 from
PLAN5 Phases A and B; the opening book (C1) and the deep8 replications were added as they
finished; restated 2026-09-06 after the outside review (PLAN6 §1, E1–E3: two instrument bugs
repaired, seven over-statements tightened — each such line says what it used to say). This is
where a claim lives; PLAN5 §2–§3 hold the working notes, RETROSPECTIVE §6 the earlier form of
the same beliefs.*

## How to read a claim

Every line carries:

- **a level** — *behavioural* (what the agent does), *predictive* (what its value head
  forecasts), *search-relative* (the number depends on the search budget it was measured
  with), *exact* (checked against the solver), or *descriptive* (a count over games);
- **an effect size with its 95 % CI** where there is one. Values are *utility* for the side
  to move — P(win) − P(loss): +1 a certain win, 0 even, −1 a certain loss — unless the line
  says otherwise. The expected *score* (win 1, draw ½, loss 0) is (1 + v) / 2, so a +0.20
  utility effect is +10 points of expected score, not 20 (the earlier header called this
  scale "expected score"; the numbers were always utilities). Elo is always *vs a named
  opponent at a named number of sims*;
- **held across** — the nets on which the claim was tested. "Both strong nets" means
  `deep10_c1_300/net_0300.pt` (+242 Elo vs v2b @64) and `deep8_c1_300/net_0300.pt` (+211);
  "all three strong nets" or "both seeds" adds the seed replicate
  `deep10_c1_300_s1/net_0300.pt` (+213, PLAN5 §5 D1); "all nets" adds dev1, v2a, v2b (250–340 Elo weaker). A claim that held from dev1 to deep10
  survived a 340-Elo span; a magnitude is quoted from the strongest net. Since 2026-09-07 the
  strongest net is `deep8_c1_300_e2/net_0300.pt` (+291 vs v2b; 46); the game claims of §1–§8
  have not been re-run on it, and "strongest net" in those sections still means deep10;
- **the tool and the output file** so the number can be regenerated.

Rules used throughout (PLAN5 §1c): orderings and signs are trusted when they hold across
nets; magnitudes are quoted but expected to drift with strength; no result under the
±3-point rule on the paired suite is called a strength difference — and the rule is a
decision rule for adopting a change, not an equivalence test: a result inside the band is
"not established", never "equal" (the interval on the difference is what says how close);
nothing is claimed from probe accuracy alone; "the net cannot represent X" is never said of
a net that was not trained to convergence; "same seed" means the same initial weights and
the same first iteration, nothing after it (PLAN6 §1 item 13), so no two runs are read as
paired.

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
4. **After most first moves there are two or more comparably good replies — and the worst
   reply is clearly worse.** Between the two best *distinct reply orbits* (a reply and its
   images under the symmetries that fix the position count once) the 16k-sim value gap is
   ≤ 0.03 after 12 of the 15 first moves on deep10 (deep8_300 10, v2b 14), but the
   best-to-worst reply-orbit range is 0.07–0.19 after every first move except [40]
   (0.02), median 0.11 (deep8_300 0.12, v2b 0.08). *Restated 2026-09-06:* the earlier
   form ("the choice of reply hardly matters", gap ≤ 0.03 in 13 of 15) compared the two
   most-visited *individual* replies, which after [0], [8] and [40] were symmetry copies of
   one reply (REVIEW-astra §4.3). *Search-relative; v2b and both strong nets.*
   `tools/atlas.py --report runs/plan5_A1_atlas.json` → `runs/plan6_E2_atlas_orbits.out`.
5. **The clear exceptions are the first moves whose best reply is to take [40]:** after
   [13] the gap between the best reply orbit ([40]) and the next is 0.102 (deep8_300 0.075,
   v2b 0.071); after [4] it is 0.053 (deep8_300 0.048) — on v2b the best reply to [4] is
   [36], not [40], and the gap 0.008. A third first move, [37], sits at the edge (0.037,
   deep8_300 0.035, v2b 0.026). The only opening edges a stronger net has *found* are
   "answer by taking the centre of the centre board". *Search-relative; grew with
   strength.* Same file.
6. **The opening is learned first.** Both 300-iteration nets put ≥ 0.95 of the raw
   first-move probability on [40] from iteration 20–30 on (deep8_300: 0.09 at iteration 10,
   0.79 at 20, 0.98 at 30) and never broaden again. *Descriptive of training.*
   `tools/timeline.py` → `runs/*/timeline.json`.
7. **The opening book** (`tools/book.py`, depth 4, top-3 *reply orbits* per node, 16 384
   sims, symmetry-averaged; `runs/book_deep10.md`, `runs/book_deep8.md`; rebuilt 2026-09-06
   after PLAN6 E1 — the earlier book listed one orbit up to three times as its "top three"
   and printed lines that mixed coordinate frames, one of them illegal per book): the
   first-move values reproduce the atlas ordering ([40] +0.447 … [13] −0.047), and the
   paired-suite X score by opening follows it (74 % after [40] or [36], 69 % after [0],
   45–51 % after [9], [8] and [13]). **The two strong nets choose the same reply orbit in
   75 % of the 430 nodes they share** (321 / 430; by depth 73 / 78 / 73 / 75 %; mean value
   difference 0.016), and the disagreement is where the book is flat: where the top orbit
   carries ≥ 0.9 of the root's visits they agree in 98 % of nodes, at 0.7–0.9 in 79 %,
   below 0.7 in 35–46 %. After [40] both prefer the edge reply (deep10 puts 0.75 of its
   visits on the four edges and 0.25 on the corners, deep8_300 0.54 / 0.46), and the corner
   subtree — absent from the earlier book — is worth +0.02 more to X on both nets; the
   earlier "deep10 plays 37, deep8 plays 41 after [40]" was one reply under two names.
   *Search-relative; both strong nets.*
7a. **The reply rule the book contains: the self-send.** The most-visited reply orbit is
   the cell whose index equals the board the mover was sent to — sending the opponent
   straight back into the board you just played in — in **55 % (deep10, 250 of 458) /
   58 % (deep8_300, 263 of 455)** of the nodes where that cell is free, at every depth to 4,
   with a higher visit share when chosen (0.84 vs 0.74 for other replies). "Take the centre
   of the board you were sent to" is *not* the rule (the top reply is the centre cell in
   4 % of nodes). *Rebuilt book (was 52 / 57 % on the pre-E1 book). Behavioural; both
   strong nets.* `tools/book_stats.py` → `runs/plan6/E1_book_stats.out`.

## 2. Tempo: the free move

8. **A free move is worth about +0.2 of utility (≈ +10 points of expected score)** to the side that gets it, with
   ply, count, open boards, empties, side and macro threats controlled: **+0.196 ± 0.028**
   (deep10, 256-sim values, 30 000 natural positions, cluster-robust by game); deep8_300
   +0.192 ± 0.027; v2b +0.163 ± 0.027. Same sign on every net; the magnitude grew a third
   and then stopped (the two strong nets agree to 0.004). *Search-relative; all nets.*
   `tools/freemove.py` → `runs/plan5_A4_freemove_deep10_on_deep8late.out`,
   `runs/plan5_A4b_freemove_deep8_on_deep10late.out`, `runs/step7b_freemove.out`.
9. **Conditioning on the immediate macro win halves the coefficient.** With "the mover can
   complete a macro line this move" in the model (+0.675 ± 0.059 on its own; deep8_300
   +0.625 ± 0.056), the free-move coefficient falls to **+0.084 ± 0.026** (deep8_300 +0.102
   ± 0.026). This is a conditional association in a regression on the search value, not a
   mediation split: it says that with the immediate win in the model a free move is worth
   ≈ +0.08 … +0.10, and ≈ +0.2 without it — not that half of a free move's value *is* the
   option to win at once (REVIEW-astra §8.3; the earlier line said "half of that is the
   option to end the game"). *Search-relative; both strong nets.* `tools/value_decomp.py`
   → `runs/plan5_B3_value_deep10.out`, `runs/plan5_B3_value_deep8.out`.
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
    +0.030 / +0.037 and +0.031 (n.s.) / +0.044 / +0.041; the seed replicate +0.076 ± 0.044 /
    +0.078 ± 0.032 / +0.065 ± 0.028 (B3's model) — the reference's numbers to the third
    decimal. Positive in all five fits, significant in most, centre not significant on
    deep8_300. On v2b this was
    indistinguishable from zero (+0.008 / +0.011 / +0.033). *Search-relative; moved with
    strength — all three strong nets, smaller on deep8_300.* `plan5_A4_*.out`,
    `plan5_B3_value_deep10.out`, `plan5_B3_value_deep8.out`, `plan5_B3_value_s1.out`.
15. **Which class of board is worth most is not resolved.** deep10 orders centre > corner >
    edge, deep8_300 has edge highest, the seed replicate corner > centre ≈ edge; the
    differences are inside the CIs on all three. The raw head's
    *counterfactual* hierarchy (flip a won board's owner: centre +1.05, corner +0.94, edge
    +0.83) is unchanged to the second decimal since v2a and is the line-count ordering
    (4 / 3 / 2 lines through the board) in disguise. *Predictive; all nets.*
    `plan5_B4_probe_value_deep10.out`, `runs/v2a/probe_surprise_rerun.out`.
16. **The raw board count is discounted as the net gets stronger.** The count-margin
    coefficient on the raw value falls from +0.106 (iteration 20) to +0.037 ± 0.010
    (iteration 300); the search's from +0.076 to +0.036. Early nets count boards; trained
    nets count lines and tempo. The seed replicate: +0.137 (iteration 10) → +0.033 ± 0.010,
    the search's +0.097 → +0.036; deep8_300 +0.078 → +0.021. *Predictive / search-relative;
    all three runs' checkpoints.* `plan5_B3_value_deep10.out`, `plan5_B3_value_s1.out`.
17. **Line counting is learned first and never moves:** the threat coefficients are at
    their final values by iteration 10–20 of 300 on both seeds and on deep8_300.
    *Descriptive of training; all three strong nets.* Same; `plan5_B3_value_s1.out`.
18. **An open board that becomes nobody's is worth nothing to the mover:** removing an open
    board for both sides moves the raw value by +0.017 (v2a: +0.06). *Predictive.*
    `plan5_B4_probe_value_deep10.out`.
19. **An opponent's immediate local threat costs ≈ −0.10** (−0.099 ± 0.014); an own
    immediate local win, once the macro win is separated, is worth nothing by itself
    (−0.026 ± 0.017). Seed replicate: −0.098 ± 0.014 and −0.028 ± 0.017; deep8_300 −0.082
    ± 0.014. *Search-relative; all three strong nets.* `plan5_B3_value_*.out`.

## 4. When games are decided

20. **Games are decided late — the median game around ply 36 of ~51; a quarter are settled
    by ply 28.** Median ply from which the 64-sim search's best-child value stops changing
    sign: **36** (quartiles 30–41) on 4000 held-out v2a games for both deep10 and deep8_300
    (v2b: 38); the raw value settles at 41 (v2b 43); the mixed root value at 45. On stronger
    play (deep8_300's late games, mean length 51.9) the same: Q 36 (28–41), raw 42. The
    fraction settled by ply, on those games: 17 % at ply 0 (see 22), 20 % at 20, 27 % at 28,
    36 % at 32, 52 % at 36, 72 % at 40, 87 % at 44, 95 % at 48. "Settled" is retrospective
    prediction stability — the ply from which the verdict never changes again — not the
    ply at which the result became forced (the earlier line said "nothing is settled by
    ply 30", which its own first quartile contradicted). *Predictive; all nets; the 2-ply
    shift from v2b saturated between the two strong nets.* `tools/decision.py` →
    `runs/plan5_A3*_decision_*.out`, `runs/step7c_decision.out`.
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

28. **On the solved samples the agent with search plays the endgame almost perfectly:** on
    3000 exactly solved positions with 6–16 empties, deep10's 256-sim search plays the
    optimal move in 99.9 % (v1 set) / 99.7 % (v2_dev, strong-play positions) with regret
    0.001 / 0.003; 64 sims: 99.8 / 99.5 %. That is a measurement on sampled positions
    (balanced strata from self-play), not a solution of every 6–16-empty position (the
    earlier line said "the endgame is, in practice, solved by the agent"). *Exact on the
    sample.* `tools/endgame.py eval` →
    `runs/plan5_A9_eval_*.out`, `runs/deep10_c1_300/analysis.out`.
29. **The raw value head names the exact result in 84.6 % of those positions** (95 % CI
    83.2–85.9; deep8_300 84.0; v2b 75.0; dev1 71.2), recognising **69 % of exact draws**
    (v2b 55 %), and its raw policy is optimal in 96.7 % with regret 0.037. *Exact; all
    nets.* Same.
30. **The yardstick was not flattered by being read 50 times during training:** on the
    fresh strong-play set `endgame_v2_dev` (split from `_test` by source game before
    solving) deep10 scores 84.7 [83.4, 85.9] — within 0.1 of v1. Draw recognition is
    higher there (72 %), raw-policy regret worse (0.048). *Exact.* `plan5_A9_*.out`.
    **`endgame_v2_test`, read once (2026-09-05):** deep10 85.0 [83.7, 86.3] (draws 72.3,
    regret 0.047), deep8_300 84.8 [83.5, 86.0], the seed replicate 85.1 [83.8, 86.3] —
    within 0.3 / 1.3 points of the dev half and within 0.3 of each other. It is a
    development set from here on. `plan5_A9_test_*.out`.
31. **"Draw blindness" was never a capacity limit.** The 150-iteration nets recognised
    ~55 % of exact draws at every width and depth; the annealed 300-iteration nets
    recognise 67–72 % with the same architecture, loss and labels. The step happens at
    the first learning-rate drop (deep8_300: 58.8 → 65.7 % between checkpoints 200 and
    210), and the draw metric wobbles by up to 20 points between adjacent checkpoints at
    constant LR. *Exact; deep8_300 and deep10 timelines.* `runs/*/timeline.json`,
    RETROSPECTIVE §3.
31a. **The last-board phase is solved outright.** On every position with exactly one open
    board in 60 000 held-out positions (701, 1.2 % of them; exact values from the
    one-open-board tablebase, `uttt/tablebase.py`), deep10's raw value head is 100 % exact
    (draws included), its raw policy plays an optimal move 100 % of the time, and the
    64-sim search 100 %; v2b 99.0 / 99.6 / 100 %, dev1 94.0 / 98.7 / 100 %. A tablebase
    spliced into the search as a terminal lookup therefore has nothing to add to any of
    these nets. *Exact; all nets.* `tools/tablebase_grade.py`.
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
    The seed replicate gives the grid a third time (dead boards +0.47 at block 6 by 200,
    the exact value +0.25 at block 10 by 180, the best move +0.14, threats +0.15 at block 6
    by 110–140, local win +0.13 at block 5 by 40, z +0.05 by 180). *Decodability; all three
    strong nets.* Same files; `runs/deep8_c1_300/probes.{json,png}`,
    `runs/deep10_c1_300_s1/probes.{json,png}`.
38. **Tactics are shallow and early, value is deep and late:** local concepts are readable
    by block 5 and learned in the first 60–80 iterations; macro-line threats peak in the
    middle of the trunk and fade toward the heads; the value-like concepts live in the last
    blocks and step at the LR drop, together with the endgame metrics they explain.
    Nothing new appears after iteration 240 (200 on the seed replicate). *Decodability; all
    three strong nets.* Same.
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
    (the current best move: 71 vs 56 %; seed replicate 38 vs 34 % and 70 vs 56 %).
    *Decodability; both seeds.* Same.
40. **The auxiliary ownership head learns the late game's ownership and little else — and
    none of it showed up as strength.** Graded on *open* boards only (PLAN6 E9; the earlier
    aggregate — head 60.3 %, trained-trunk probe 60.1 %, random-trunk probe 59.0 % — mixed in
    the boards whose owner was already fixed), on 73 330 open boards of the held-out test
    positions: overall the head names the final owner in 51.2 % (majority class 39.5 %, a
    logistic on hand-written per-board features 47.8 %, a linear probe on the trained trunk
    49.1 %, on a random trunk 47.0 %). By ply: before ply 32 the head is within 2 points of
    the local-feature logistic and the random-trunk probe (45–52 %); at plies 32–43 it is
    57 % against 51 / 51; at plies 44+ **68 % against 50 (local) / 50 (random trunk) / 65
    (trained trunk)**. deep8_300 on deep10's games: 66 % late against 51 / 54 / 64, the same
    shape. So the trunk computes late-game ownership that neither the board's local features
    nor an untrained trunk carry, and the head reads it; early ownership is not predictable
    from the position by any of these read-outs. Switching the auxiliary heads off was a
    strength null (RETROSPECTIVE §3): the head's late-game knowledge is what the value head
    needs anyway. *Decodability + behavioural null; both strong nets.*
    `tools/ownership_grade.py` → `runs/plan6_E9_ownership_deep10.out`,
    `runs/plan6_E9_ownership_deep8.out`.
41. **The net has not fully learned the board's symmetry, and it costs a rung.** Training
    augments every sampled example with an independent random D4 element
    (`train2.symmetrise`); equivariance is not enforced, and what follows is the residual
    that augmentation alone leaves (PLAN5 B5's "the buffer is not symmetrised" was true of
    the buffer and misleading about training). The policy's Jensen–Shannon divergence across
    the 8 orientations is 0.05 bits for 200 iterations, halves at the LR drop and ends at
    0.027 (0.028 on the seed replicate, by the same path; smallest in the opening, 0.010;
    largest in the middlegame, 0.034). Averaging the 8 orientations at play time beats the
    plain net **55.0 % [52.4, 57.7], +35 Elo [+17, +54]** at equal sims (8× the inference
    per sim) and adds +0.4 WDL points on the endgame set — but at equal inference the
    same averaging *loses* to plain search with 8× the sims, **23.9 % [21.8, 26.2], −201
    Elo**: the residual asymmetry is real and is cheaper to search through than to average
    away. On `deep8_c1_300_e2` the averaging gain is the same, **54.7 % [52.1, 57.2], +32
    [+14, +50]** (2026-09-07; its D4 JS at 300 is 0.026 bits). *Behavioural; deep10 and
    deep8_c1_300_e2.* `runs/deep10_c1_300/timeline.json`,
    `runs/deep8_c1_300_e2/paired_sym_vs_plain_64.json`,
    `runs/plan5_B5_sym_vs_plain.out`, `runs/plan5_B5b_sym_equal_compute.out`.
41b. **Exact equivariance alone buys nothing at play; the +35 above is an ensembling gain.**
    The one-call canonical evaluator (`uttt/symmetry.py CanonicalEvaluator`, PLAN6 F1: the net
    evaluated once in the position's canonical orientation, the policy transported back through
    the stabiliser coset — exactly equivariant at ≈ 1.03× the plain net's cost) scores
    **49.5 % [46.7, 52.3], −3 Elo [−23, +16]** against the plain net at equal sims (deep10 @64,
    full paired suite): null by the pre-registered rule (≥ 53 % adopt, ≤ 47 % hurts). On the
    endgame set it is 0.5 points *worse* in raw-policy optimality (96.1 vs 96.7 %): picking one
    orientation's errors consistently does not remove them. So the residual asymmetry of 41
    costs nothing at play, averaging it away is worth +35 only because it averages eight
    evaluations, and an exactly equivariant *architecture* has no play-time gain to promise on
    that account — its case is sample efficiency (PLAN6 Phase G). On `deep8_c1_300_e2` the
    same null: 50.4 % [47.7, 53.1], +3 [−16, +22] (2026-09-07). *Behavioural; deep10 and
    deep8_c1_300_e2.* `runs/deep10_c1_300/paired_canon_vs_plain_64.json`,
    `runs/deep8_c1_300_e2/paired_canon_vs_plain_64.json`, `docs/history/review_astra/canonical_demo.json`.
41a. **The named concepts do not carry the strength.** A legible surrogate — a linear
    score over 20 hand-written per-move features (wins the board, wins the game, gives a
    free move, lets the opponent win next, threats after, count after, the self-send, cell
    and target classes …) with a linear value on the position concepts, fitted to deep10's
    256-sim search on 50 000 held-out positions — reproduces the search's move in **41 %**
    of positions (the net's own raw policy: 66 %) and the value with R² 0.55, and then,
    playing with the same 64-sim search, scores **2.2 % vs v2b (−661 Elo), 0.4 % vs deep10
    (−943 Elo)** and 14 % against a 10 000-playout random-rollout search (−311). Its largest
    weights are readable and agree with the rest of this file (self-send +0.85, a macro win
    +0.89, letting the opponent win next −0.81, keeping local threats +0.70, a board won
    +0.62, count +0.62; a free move given +0.12). *Behavioural; deep10.* `tools/distill.py`,
    `runs/surrogate_deep10.json`, `runs/paired_surrogate_vs_*.json`.
42. **Where +127 Elo of "duration" came from:** ≈ +5 points of paired score from iterations
    150–200 at the constant learning rate and ≈ +8 from the first LR drop, at which every
    curve (score, endgame WDL, draw recognition, opening-policy entropy, D4 consistency)
    steps once; the second drop at 280 produces nothing visible. *Descriptive of training;
    all three 300-iteration runs (the seed replicate: 71.2 → 78.1 at the first drop, every
    curve flat after 220, nothing at 280).* `runs/*/timeline.{json,png}`, PLAN5 §3 B1.
    **Moving the first drop 50 iterations earlier hurts** (`deep10_c1_300_lr150`, drops at
    150/250, otherwise the reference's recipe and seed — where "same seed" fixes only the
    initial weights and the first iteration: the pipeline is not bitwise deterministic and
    the two runs' self-play differs from iteration 1, before any intervention, so this is
    one perturbed run read against the two reference seeds, not a paired comparison; PLAN6
    §1 item 13): the same ≈ +9 step arrives at 160, and the final net scores **45.4 % [42.8,
    48.0], −32 Elo** against the reference, −10 [−29, +9] against the replicate and +193 vs
    v2b — "hurt" by the pre-registered rule against the reference, inside the seed band
    against the replicate. After the drop no *strength* gain resolves on any of the four
    runs' in-run curves (±6), while the raw head keeps creeping: lr150's endgame WDL 80.3 →
    83.3 % and draw recognition 60 → 66–68 % over iterations 160–300 (the earlier line said
    "every curve is flat after it" and "learns nothing further"). The drop is a fixed step
    on whatever the constant-LR phase has built; strength settles within ≈ 20 iterations of
    it; the constant-LR iterations 150–200 were worth their ≈ 5 points. *Descriptive of
    training; four 300-iteration runs.* PLAN5 §5 D3,
    `runs/deep10_c1_300_lr150/{analysis.out,timeline.json}`.
    **Read at ±2.8 instead of ±6 (PLAN6 F2, full paired suite vs v2b @64 for the checkpoints
    around both drops of all four runs):** the first drop is a resolved step on every run —
    +8.5 (deep8_300, 200 → 220), +4.8 (deep10), +6.6 (the replicate), +5.9 (lr150, 150 → 160)
    — and **the second drop does nothing resolvable**: 300 − 260 is +2.6 / +4.1 / −0.4 / −0.3
    (lr150: 300 − 240), one run of four over the pre-registered 3 points. Checkpoint-to-
    checkpoint wobble at a constant LR is ≈ ±3 points on the full suite (the replicate reads
    77.7 / 75.3 / 77.3 at 260 / 280 / 300), so "flat after the drop" means "inside ±3", and
    the in-run ±6 reads missed the full-suite value by up to 4 points. *Descriptive of
    training; four 300-iteration runs.* `runs/*/eval_full.jsonl`, `runs/plan6/F2_second_drop.out`.

## 9. Strength (for reference; the full ladder is in RETROSPECTIVE §2)

43. **The ladder, vs v2b @64 sims on the frozen paired suite, final checkpoints:** dev1 −95,
    v2b 0, +c_scale 1.0 +40, +width 128 +77, +8 blocks +100, +300 iterations +211, +10
    blocks **+242** (≈ 80 % expected score). **The seed replicate of the last rung**
    (`deep10_c1_300_s1`, same recipe, seed 1) scores +213 [+190, +236] vs v2b, +9 [−10, +28]
    vs deep8_300 and +4 [−13, +22] against the other seed: the seed band at 10×128 is ≈ 3
    points / ≈ 30 Elo, and "+ blocks 10" (+35 on one seed, +9 on the other) is inside it —
    not an established rung. Duration (+211) is the last confirmed rung; deep10_c1_300 is
    the strongest 10-block net measured. An earlier first LR drop (`deep10_c1_300_lr150`)
    scores +193 — below both seeds: −32 [−50, −14] against the reference, −10 [−29, +9]
    against the replicate (42). **Doubling the optimizer steps per iteration on 8 blocks
    (`deep8_c1_300_e2`, 2026-09-07) is +100 over deep8_c1_300 and +291 over v2b — the
    strongest net, and the largest single step of the ladder (46).** *Behavioural.*
    `runs/*/analysis.out`.
44. **At equal compute the deep, long-trained net wins for the first time:** deep10@64
    beats v2b@427 (6.7× the sims) by +42 [+23, +61]; but deep10@64 vs deep8_300@80 is −11
    [−30, +7] — the last rung is a wash at a fixed inference budget; duration, not depth,
    is where deployment strength came from. The seed replicate agrees from the other side:
    at equal sims the 8 → 10 step is inside the seed band (43). And the 8-block net trained
    with twice the updates beats the 10-block net by +86 [+67, +105] at equal sims while
    costing 0.81× per evaluation (46): *updates*, not depth. *Behavioural.*
    `runs/plan5_A8.out`, `runs/deep10_c1_300_s1/analysis.out`.
45. **The phased search schedule ("0:128,24:384") is not confirmed on deep10:** +10
    [−7, +26] vs a flat 256 (was +50 on v2b, +26 on deep8_300) — the stronger the raw
    policy, the less late search adds. Re-verified on `deep8_c1_300_e2` (2026-09-07):
    51.6 % [49.2, 53.8], +11 [−6, +26] — null again. Play config: flat `--sims 256` or
    more. *Behavioural; deep10 and deep8_c1_300_e2.* Same;
    `runs/deep8_c1_300_e2/paired_phased_vs_256.json`.
46. **Doubling the optimizer steps per iteration is worth +100 Elo, with nothing else
    changed** (PLAN6 H1, 2026-09-07). `deep8_c1_300_e2` is deep8_c1_300's recipe with
    `--epochs 2`: 512 steps of batch 1024 per iteration instead of 256, over the same
    4096 × 64 new positions per iteration, the same 2 M-row buffer (mean sampled replay age
    3.35 iterations), the same LR drops at 200 / 280 — +1.3 h of training on a 14.6 h run.
    On the full paired suite at 64 sims it scores **64.0 % [61.4, 66.5], +100 Elo [+81,
    +119] against deep8_c1_300**, **62.1 % [59.6, 64.6], +86 [+67, +105] against
    deep10_c1_300**, 63.6 % [60.9, 66.3], +97 against the 10-block seed replicate, and
    **84.2 % [82.2, 86.2], +291 Elo [+266, +318] against v2b**. The learner was
    update-limited, not data-limited: the +127 of "duration" (150 → 300 iterations: twice
    the data *and* twice the updates) was mostly the updates. Raw heads: endgame_v1 WDL
    **87.6 % [86.4, 88.9]** (deep10 84.6), draw recognition 74.8 % (67–69), regret 0.036;
    endgame_v2_dev 87.5 [86.3, 88.6], regret 0.034 (deep8_300 83.5 / 0.050, deep10 84.7 /
    0.048); the 256-sim search 99.9 % optimal on both. The first full-suite timeline
    (`eval_full.jsonl`, every 10th checkpoint at ±2.8): ahead of the reference from
    iteration 10 (20.1 vs 11.9 % vs v2b), 75.9 vs 67.7 at 200 — even with deep8_c1_300's
    *final* net (48.0 %) before its own LR drop — the drop adds the usual ≈ +7 (82.2 at
    210), then flat within ±3 to 300 (83.0–84.9), the second drop nothing. Self-play games
    lengthen (52.5 vs 51.9 plies) and draw more (15.5 vs 13.0 %); the policy loss is lower
    throughout; 70 of 153 600 steps were skipped by the GradScaler. *Behavioural; one run
    read against three references, seed band ≈ 3 points.*
    `runs/deep8_c1_300_e2/{analysis.out,eval_full.jsonl,timeline.png}`, PLAN6 log.
47. **For a fixed teacher, the fit is a function of optimizer steps, not of distinct
    positions** (PLAN6 G0). ResNet 8×128 students trained on `runs/gdata_v1.npz`
    (deep10 8-way @256 sims as the teacher; held-out policy KL on the dev slice): at 384
    steps, 50 000 positions × 8 passes 1.188, 100 000 × 4 1.187, 200 000 × 2 1.182,
    400 000 × 1 1.183; at 780 steps 1.082 / 1.076 / 1.075; at 1560 steps 0.976 / 0.973;
    at 3120 steps (400 000 × 8) 0.884, still falling. Top-1 agreement, value Brier, exact
    3-way accuracy and endgame regret line up the same way, as does the subset of dev
    positions with no canonical twin in the training slice (1.014 at 3120 steps). Eight
    passes over 50 000 positions fit as well as one pass over 400 000. The supervised twin
    of 46. *Supervised, dev slice, one seed per cell (two-seed spread at 400k × 8: 0.0014).*
    `tools/gstudy.py` → `runs/plan6/G0_resnet8.json`.
48. **Exact D4 equivariance buys sample efficiency for a fixed teacher; the closed-board
    mask a little; depth nothing** (PLAN6 G arms, 400 000 × 8 = 3120 steps, two seeds, dev
    slice; policy KL vs the teacher). ResNet 8×128: 0.8839 / 0.8853 (top-1 0.552, exact
    3-way 0.756–0.760, endgame regret 0.164). ResNet 10×128: 0.8820 / 0.8803 — inside the
    seed spread. 8×128 with the closed-board input mask: 0.8769 / 0.8739 (−0.008, 6× the
    spread; 3-way +1.6 points; regret 0.152). **8×128 with D4-tied heads (861-orbit policy
    map, orbit-pooled value / margin, board-orbit ownership; `uttt/equivariant.py`):
    0.8480 / 0.8462 (−0.038; top-1 0.565; 3-way 0.782; regret 0.145; D4 residual 0.045
    bits vs 0.056).** **The D4 group-convolutional net at the same activation width (16
    base filters × 8 orientations): 0.8057 / 0.8066 (−0.078; top-1 0.600; 3-way 0.799;
    regret 0.147; D4 residual 0 by construction; 312 k parameters against 2.46 M; the same
    inference cost, 33.6 vs 33.2 ms per 4096 evaluations on the 3090, because it exports to
    ordinary convolutions of the expanded width).** Its value Brier is 0.002–0.006 worse
    (a narrower tied value read-out). The ordering holds on the positions with no canonical
    twin in train (1.014 / 1.012 / 1.006 / 0.969 / 1.006). Both equivariant arms pass §4's
    gate (i) on the dev slice at equal cost. **Sample efficiency (gate ii):** the G-CNN reaches
    the ResNet's 3120-step KL (0.884) with half the data (200 000 × 8: 0.880) or half the
    steps (400 000 × 4: 0.856); the tied heads do not (0.931 / 0.921). And for the G-CNN
    the fit at equal steps depends on the number of distinct positions (0.856 vs 0.880 at
    1560 steps, 400 000 vs 200 000 positions) where the ResNet's did not (47) — the
    equivariant net is the first student that is partly data-limited. The mask arm's
    endgame WDL is 67.2 / 67.3 % (ResNet 64.4 / 65.3; an earlier 48 % was an evaluation
    artefact, fixed). **The sealed test slice, read once (2026-09-07), agrees with dev to
    within 0.0012 on every arm** (KL 0.885 / 0.882 / 0.876 / 0.848 / 0.806 for ResNet 8 /
    ResNet 10 / mask / tied / G-CNN). *Supervised; dev slice, confirmed on the test slice.*
    `runs/plan6/G_arm_*.json`, `runs/plan6/G0_gcnn8x16.json`, `runs/plan6/G0b_*.json`,
    `runs/plan6/G_timing_*.json`, `tests/test_equivariant.py`.

## 10. Open, and not claimed

- The opening book stops at depth 4 with three replies per node; nothing is claimed about
  lines beyond it.
- The per-owned-board residual (14) survived the seed replicate to the third decimal; the
  class order (15) did not appear on it either, so it stays unresolved. One coefficient
  path is deep10-only — the raw head's free-move weight falling from +0.19 to +0.14 over
  training (PLAN5 §3 B3); the search value's rise +0.05 → +0.09 is on both seeds.
- The self/opponent asymmetry in the ownership coefficients flips between the raw and the
  search value and is not reported.
- `endgame_v2_test` was read once (30). **A new sealed set exists (PLAN6 E10):** `suites/endgame_v3_test.npz`,
  3000 solved positions from `deep10_c1_300_s1`'s iterations 280–299, split from `endgame_v3_dev` by source
  game before solving, 0 canonical positions shared between the halves and none duplicated within them
  (`tools/suite_overlap.py`). Held out for deep10, deep8_300 and any Phase G student — not for the seed
  replicate, whose games it comes from. To be read once, at the end of Phase G, and logged in PLAN6.
- The five hard puzzles are annotated in `docs/positions.md` (C3); a larger annotated set
  (the top surprises of B4) is not.
- A two-open-board tablebase (the useful frontier after 31a) — not built; it needs
  reachable-only generation, not enumeration.
- *A diagnostic of the input encoding, not a claim about the game* (PLAN6 F3): erasing the
  stones inside closed boards while keeping their macro status — information the rules no
  longer need — moves deep10's raw value by 0.061 on average and its policy argmax in 3.9 %
  of 311 natural positions (REVIEW-astra §3.4, `docs/history/review_astra/checks.json`).
  Those are out-of-distribution inputs for this net; whether a net trained on the masked
  encoding does as well is Phase G arm (c).
