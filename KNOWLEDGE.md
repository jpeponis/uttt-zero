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
  `deep10_c1_300_s1/net_0300.pt` (+213, PLAN5 §5 D1); **"all four strong nets" adds
  `deep8_c1_300_e4/net_0300.pt` (+363, 49), the net the game claims were re-read on**;
  "all nets" adds dev1, v2a, v2b (250–340 Elo weaker). A claim that held from dev1 to deep10
  survived a 340-Elo span; a magnitude is quoted from the strongest net. **Since 2026-09-10 the
  strongest net is `deep8_c1_300_e8/net_0300.pt`** — `_e4`'s recipe with a third doubling of the
  optimizer steps, +40 Elo [+23, +57] over it and +363 vs v2b (51). **The game claims of §1–§8
  were re-read on `_e4`, not on `_e8`** (PLAN6 §9c, I1 — the second analysis pass, 2026-09-10,
  120 Elo above the net they were first quoted from): each re-read claim below carries its `_e4`
  number beside the earlier one, and "strongest net" in those sections means the net they were
  read on, `deep8_c1_300_e4`, wherever a number was re-read. The five that were not re-read
  say so where they occur: 6
  (already read on this net), 12, 15, 18 and 38a (their tools are not in I1);
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

*Second pass, 2026-09-10 (PLAN6 §9c, I1). Every net-dependent tool of PLAN5 Phase A re-run on
`deep8_c1_300_e4/net_0300.pt` (+363) at the deep10 pass's settings, 02:27–07:23 on the 3060;
outputs `runs/plan6/I1_*.out`, script `runs/plan6/I1_second_pass_3060.sh`. Of the **34 claims
re-read: 15 held, 18 moved, 1 reversed**; 5 more (6, 12, 15, 18, 38a) were not re-run, and 28–31
were already read on this net (`runs/deep8_c1_300_e4/analysis.out`, 49). **The reversal is in 7:**
after [40] this net prefers the corner reply orbit where both earlier strong nets preferred the
edge — the first ordering in this file to flip with strength. The moves are mostly magnitudes
drifting the way strength has always pushed them (a sharper opening, 2–5; earlier settling, 20–22;
a raw policy that fails half as often, 32), with two that are not: the count rule now decides a
third of games rather than a quarter (25), and 16.6 % of this net's games are drawn (24). No other
*primary* sign or ordering changed — the ones each claim's first sentence states; within 32 the
second and third failure motifs swapped (holding a draw overtook giving a free move), and after [2]
the best reply orbit moved from a three-net tie to the self-send [20] (5) — both recorded in their
claims. (The earlier form of this sentence, "no other sign or ordering changed", was too broad; M0
review, 2026-09-12.)*

1. **[40] — centre of the centre board — is the best first move** on every net and every
   budget tested, and **[13] the worst**: rank 1 and rank 15 in all 9 columns of the atlas
   (v2b, deep8_300, deep10 × 1k / 4k / 16k sims, symmetry-averaged), as they were for dev1
   and v2a — and in all 3 of `deep8_c1_300_e4`'s columns (2026-09-10), 12 columns in all.
   *Search-relative; all nets, `deep8_c1_300_e4` included.* `tools/atlas.py` →
   `runs/plan5_A1_atlas.out`, `runs/step7a.out`, `runs/plan6/I1_A1_atlas.out`.
2. **The first-move ordering is stable across 340 Elo**: Kendall τ between deep10@16k and
   v2b@16k is 0.96, deep8_300 vs v2b 0.92; the top four are [40] > [36] > [0] > [37] on
   every strong column (centre-centre, then the centre board's corner and the corner
   board's corner and edge). **`deep8_c1_300_e4` has the same top four in the same order at
   16k** ([0] and [37] swap at 1k and 4k, as they already did on deep8_300), but its ordering
   sits further from the weak net's: **τ 0.85 against v2b@16k**, 0.89 against deep10@16k, 0.92
   against deep8_300@16k (2026-09-10) — the top and the bottom fixed, the middle looser than any
   earlier pair. *Search-relative; all nets.* Same files; `runs/plan6/I1_A1_atlas.json`.
3. **X's edge after [40] is rated +0.447 by deep10 at 16k sims** (v2b: +0.354; dev1: +0.28).
   The *magnitude* rises with strength and is not trusted; the *sign* and the gap to the
   next move (+0.11 to [36]) are. `deep8_c1_300_e4`: **+0.495**, gap to [36] **+0.100**
   (2026-09-10) — a fourth point on a rise that has not stopped (0.28 → 0.354 → 0.455 /
   0.447 → 0.495) while the gap stays ≈ 0.10. *Search-relative.* Same files;
   `runs/plan6/I1_A1_atlas.out`.
4. **After most first moves there are two or more comparably good replies — and the worst
   reply is clearly worse.** Between the two best *distinct reply orbits* (a reply and its
   images under the symmetries that fix the position count once) the 16k-sim value gap is
   ≤ 0.03 after 12 of the 15 first moves on deep10 (deep8_300 10, v2b 14), but the
   best-to-worst reply-orbit range is 0.07–0.19 after every first move except [40]
   (0.02), median 0.11 (deep8_300 0.12, v2b 0.08). **On `deep8_c1_300_e4` both numbers move
   the way strength has been moving them** (2026-09-10, at all three budgets): flat after **9 of
   15** first moves, and a best-to-worst range of **0.09–0.26 except [40] (0.022), median
   0.150** — fewer comparable replies and a wider spread between the best and the worst.
   *Restated 2026-09-06:* the earlier
   form ("the choice of reply hardly matters", gap ≤ 0.03 in 13 of 15) compared the two
   most-visited *individual* replies, which after [0], [8] and [40] were symmetry copies of
   one reply (REVIEW-astra §4.3). *Search-relative; v2b, both strong nets and
   `deep8_c1_300_e4`.* `tools/atlas.py --report runs/plan5_A1_atlas.json` →
   `runs/plan6_E2_atlas_orbits.out`, `runs/plan6/I1_A1_atlas_orbits.out`.
5. **The clear exceptions are the first moves whose best reply is to take [40]:** after
   [13] the gap between the best reply orbit ([40]) and the next is 0.102 (deep8_300 0.075,
   v2b 0.071); after [4] it is 0.053 (deep8_300 0.048) — on v2b the best reply to [4] is
   [36], not [40], and the gap 0.008. A third first move, [37], sits at the edge (0.037,
   deep8_300 0.035, v2b 0.026). The only opening edges the three earlier nets *found* are
   "answer by taking the centre of the centre board". **`deep8_c1_300_e4` widens all three
   again and adds a fourth of a different kind** (2026-09-10): [13] **0.142**, [4] **0.090**,
   [37] **0.051**, and after [2] a gap of **0.073** (deep10 0.003, deep8_300 0.006, v2b 0.004)
   whose best reply is the self-send [20], not [40]. The "answer by taking [40]" restriction is
   the earlier nets' reading; on the strongest net there is a sharp reply that is not a [40]
   reply. *Search-relative; grew with strength on every net.* Same file;
   `runs/plan6/I1_A1_atlas_orbits.out`.
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
   **Reversed on the strongest net (2026-09-10, PLAN6 I1).** `deep8_c1_300_e4`'s book
   (`runs/book_deep8_e4.json`, 562 nodes, the same settings) puts **0.71 of its visits after
   [40] on the corner orbit 36 [4] and 0.29 on the edge orbit 37** — the mirror of deep10's
   0.75 / 0.25 and deep8_300's 0.54 / 0.46 — and rates the *edge* subtree +0.022 better for X
   where both earlier nets rated the *corner* subtree +0.016 better. Its atlas agrees at all
   three budgets (36 is the best reply orbit at 1k, 4k and 16k, where all nine earlier columns
   said 37). So "after [40] the strong nets prefer the edge reply" is **strength-relative: it
   flipped between +242 and +363**, and it is the one ordering in this file that has. The rest
   of the claim holds: the first-move values reproduce the atlas ordering ([40] +0.495 …
   [13] −0.079); agreement with deep8_300 on the most-visited reply orbit is **70 % of the 415
   shared nodes** (by depth 73 / 67 / 69 / 71 %, mean value difference 0.042) and with deep10
   67 % of 404; and the flatness pattern survives with every level lower — **88 %** agreement
   where the top orbit carries ≥ 0.9 of the root's visits (was 98), 66 % at 0.7–0.9 (79),
   39–52 % below 0.7 (35–46). The new book's paired X-score column is **not** comparable with
   the earlier ones: its `--paired` file is this net's match against its parent, not a
   self-match (`runs/plan6/I1_second_pass_3060.sh` header).
   *Search-relative; both strong nets and `deep8_c1_300_e4`, the [40] reply strength-relative.*
   `runs/plan6/I1_C1_book.out`, `runs/book_deep8_e4.json`.
7a. **The reply rule the book contains: the self-send.** The most-visited reply orbit is
   the cell whose index equals the board the mover was sent to — sending the opponent
   straight back into the board you just played in — in **55 % (deep10, 250 of 458) /
   58 % (deep8_300, 263 of 455)** of the nodes where that cell is free, at every depth to 4,
   with a higher visit share when chosen (0.84 vs 0.74 for other replies). "Take the centre
   of the board you were sent to" is *not* the rule (the top reply is the centre cell in
   4 % of nodes). **On `deep8_c1_300_e4` the rule weakens for the first time: 48 % (213 of
   the 447 nodes where that cell is free)**, by depth 12 / 12, 15 / 31, 50 / 101, 136 / 303,
   with the same signature when it is chosen (visit share 0.85 against 0.78 for other replies)
   and the same 4 % centre-cell rate (25 of 562) (2026-09-10). The self-send is still the single
   most common reply and is still played with more conviction than anything else; it is no
   longer played in a majority of nodes. *Rebuilt book (was 52 / 57 % on the pre-E1 book).
   Behavioural; both strong nets and `deep8_c1_300_e4`.* `tools/book_stats.py` →
   `runs/plan6/E1_book_stats.out`, `runs/plan6/I1_C1_book_stats.out`.

## 2. Tempo: the free move

8. **A free move is worth about +0.2 of utility (≈ +10 points of expected score)** to the side that gets it, with
   ply, count, open boards, empties, side and macro threats controlled: **+0.196 ± 0.028**
   (deep10, 256-sim values, 30 000 natural positions, cluster-robust by game); deep8_300
   +0.192 ± 0.027; v2b +0.163 ± 0.027; **`deep8_c1_300_e4` +0.1953 ± 0.0278** (2026-09-10, on
   deep10's late games) — the deep10 number to the third decimal, 120 Elo later. Same sign on
   every net; the magnitude grew a third and then stopped (the three strong readings agree to
   0.004). *Search-relative; all nets.* `tools/freemove.py` →
   `runs/plan5_A4_freemove_deep10_on_deep8late.out`,
   `runs/plan5_A4b_freemove_deep8_on_deep10late.out`, `runs/step7b_freemove.out`,
   `runs/plan6/I1_A4_freemove.out`.
9. **Conditioning on the immediate macro win halves the coefficient.** With "the mover can
   complete a macro line this move" in the model (+0.675 ± 0.059 on its own; deep8_300
   +0.625 ± 0.056), the free-move coefficient falls to **+0.084 ± 0.026** (deep8_300 +0.102
   ± 0.026). This is a conditional association in a regression on the search value, not a
   mediation split: it says that with the immediate win in the model a free move is worth
   ≈ +0.08 … +0.10, and ≈ +0.2 without it — not that half of a free move's value *is* the
   option to win at once (REVIEW-astra §8.3; the earlier line said "half of that is the
   option to end the game"). **On `deep8_c1_300_e4` the conditional coefficient is +0.117 ±
   0.027**, with the immediate macro win at +0.608 ± 0.058 (2026-09-10): still far below its own
   unconditional +0.195, but 0.60 of it against deep10's 0.43 — so "halves" is deep10's number,
   not a constant. Across the strong nets, with the immediate win in the model a free move is
   worth ≈ +0.08 … +0.12. *Search-relative; both strong nets and `deep8_c1_300_e4`.*
   `tools/value_decomp.py` → `runs/plan5_B3_value_deep10.out`, `runs/plan5_B3_value_deep8.out`,
   `runs/plan6/I1_B3_value_decomp.out`.
10. **It is largest late, when level or ahead:** +0.25 at plies 44–50 with the count level
    or better, +0.03 at plies 32–43 (stratified check). **`deep8_c1_300_e4` is larger still
    late, and its middlegame is no longer flat** (2026-09-10): **+0.30** at plies 44–50 with the
    count level or better (+0.24 / +0.39 / +0.33 at a count of 0 / +1 / +2, against deep10's
    +0.25 / +0.27 / +0.27), and at plies 32–43 the free-minus-confined difference runs with the
    count — **−0.16 two boards down, +0.01 one down, +0.11 level, +0.14 one up, +0.24 two up**
    — against deep10's +0.03 in every stratum. The ordering (largest late, largest when ahead)
    is the same on both; on the stronger net a free move is worth what the count can spend it
    on. *Search-relative; deep10, v2b, `deep8_c1_300_e4`.* `plan5_A4_*.out`,
    `runs/plan6/I1_A4_freemove.out`.
11. **The value head over-credits it:** raw-head coefficient +0.290 ± 0.030 vs +0.196 for
    the search — a 0.094 gap that was 0.094 on v2b too, and **+0.2835 ± 0.0310 against +0.1953,
    a 0.088 gap, on `deep8_c1_300_e4`** (2026-09-10): three nets, the same ≈ 0.09. Over training
    the raw coefficient
    falls (+0.19 → +0.14 in the fuller model) while the search's rises (+0.04 → +0.09):
    intuition converges toward search. **That second sentence is deep10's path alone.** On
    `deep8_c1_300_e4` the raw coefficient *rises* over training (+0.04 at iteration 10, +0.16 at
    20, +0.19 at 300 in the fuller model) while the search's rises too (+0.04 → +0.12), so the
    raw − search gap widens from ≈ 0 to +0.070; deep8_300 does the same (§10). What holds across
    nets is the over-crediting at the end of training, not the direction it arrives from.
    *Predictive vs search-relative; all nets.*
    `plan5_A4_*.out`, `plan5_B3_value_deep10.out`, `runs/plan6/I1_A4_freemove.out`,
    `runs/plan6/I1_B3_value_decomp.out`.
12. **Editing the tensor overstates it 2×.** Granting a free move by editing the position
    moves the raw value by +0.41 (median +0.32; v2a-era +0.27), against +0.20 from natural
    positions. The overstatement itself is stable, so tensor-edit numbers are read as
    upper bounds. *Predictive; v2a, deep10.* `tools/probe_value.py` →
    `runs/plan5_B4_probe_value_deep10.out`.

## 3. Macro lines, board ownership, the count

13. **A macro-line threat (two own boards in a line, the third open) is worth ≈ +0.15, an
    opponent's ≈ −0.14**, controlling for everything else in the model: +0.154 / −0.140
    (deep10), +0.145 / −0.139 (deep8_300), +0.16 / −0.17 (v2b), **+0.148 ± 0.021 / −0.132 ±
    0.018 (`deep8_c1_300_e4`, 2026-09-10)** — four strengths, the same pair of numbers.
    *Search-relative; all nets.* `plan5_A4_*.out`, `runs/plan6/I1_A4_freemove.out`.
14. **Owning a board is worth a little of its own — +0.03 … +0.08 — beyond the lines it
    sits on, and the number is not sharp.** With threats controlled, an own board adds:
    deep10 centre +0.070 ± 0.040, corner +0.065 ± 0.030, edge +0.056 ± 0.027 (A4's model),
    +0.076 / +0.079 / +0.066 (B3's fuller model, other positions); deep8_300 +0.051 /
    +0.030 / +0.037 and +0.031 (n.s.) / +0.044 / +0.041; the seed replicate +0.076 ± 0.044 /
    +0.078 ± 0.032 / +0.065 ± 0.028 (B3's model) — the reference's numbers to the third
    decimal. Positive in all five fits, significant in most, centre not significant on
    deep8_300. On v2b this was
    indistinguishable from zero (+0.008 / +0.011 / +0.033). **`deep8_c1_300_e4` is smaller
    again** (2026-09-10): +0.049 ± 0.039 / +0.026 ± 0.030 / +0.038 ± 0.027 (A4's model) and
    +0.021 ± 0.045 / +0.034 ± 0.034 / +0.032 ± 0.031 (B3's) — positive in all six, significant
    in three. Against deep10's A4 intervals the centre (0.049 in [+0.030, +0.110]) and the edge
    (0.038 in [+0.029, +0.083]) sit *inside*, and only the corner (0.026 against [+0.035,
    +0.095]) falls below — so by I1's rule the corner moved and the other two held. *(An earlier
    form of this line said "every one of them below deep10's interval", which its own numbers
    contradict; corrected after the M0 review, 2026-09-12.)* Over four strong nets the residual is
    **+0.02 … +0.08 and does not grow with strength**; "moved with strength" was the step up
    from v2b, and it has not moved again since deep8_300. *Search-relative; positive on all four
    strong nets, zero on v2b.* `plan5_A4_*.out`,
    `plan5_B3_value_deep10.out`, `plan5_B3_value_deep8.out`, `plan5_B3_value_s1.out`,
    `runs/plan6/I1_A4_freemove.out`, `runs/plan6/I1_B3_value_decomp.out`.
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
    the search's +0.097 → +0.036; deep8_300 +0.078 → +0.021; **`deep8_c1_300_e4` +0.082
    (iteration 10) → +0.022 ± 0.012, the search's +0.047 → +0.014** (2026-09-10) — below
    deep10's interval and on deep8_300's endpoint, so the discount deepens rather than
    saturating. *Predictive / search-relative; all four strong nets' checkpoints.*
    `plan5_B3_value_deep10.out`, `plan5_B3_value_s1.out`, `runs/plan6/I1_B3_value_decomp.out`.
17. **Line counting is learned first and never moves:** the threat coefficients are at
    their final values by iteration 10–20 of 300 on both seeds and on deep8_300 — and on
    `deep8_c1_300_e4`, whose search-value threats read +0.123 / −0.166 at iteration 10 against
    +0.131 / −0.136 at 300 (2026-09-10). *Descriptive of training; all four strong nets.*
    Same; `plan5_B3_value_s1.out`, `runs/plan6/I1_B3_value_decomp.out`.
18. **An open board that becomes nobody's is worth nothing to the mover:** removing an open
    board for both sides moves the raw value by +0.017 (v2a: +0.06). *Predictive.*
    `plan5_B4_probe_value_deep10.out`.
19. **An opponent's immediate local threat costs ≈ −0.10** (−0.099 ± 0.014); an own
    immediate local win, once the macro win is separated, is worth nothing by itself
    (−0.026 ± 0.017). Seed replicate: −0.098 ± 0.014 and −0.028 ± 0.017; deep8_300 −0.082
    ± 0.014; **`deep8_c1_300_e4` −0.086 ± 0.015 and −0.037 ± 0.018** (2026-09-10).
    *Search-relative; all four strong nets.* `plan5_B3_value_*.out`,
    `runs/plan6/I1_B3_value_decomp.out`.

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
    ply 30", which its own first quartile contradicted). **`deep8_c1_300_e4` settles earlier
    again** (2026-09-10): on the same 4000 v2a games its Q median is **36**, exactly the
    earlier nets' (quartiles 27–40 against their 30–41), while its raw value settles at 39
    (deep10 41, v2b 43) and its mixed root value at 45; on strong play (deep10's late games, mean length 51.9) everything
    moves two plies earlier than deep10's reading — **Q 34 (25–40)**, raw 40, root 47. The
    settled-by-ply curve moves with it: 21 % at ply 0, 23 % at 20, 30 % at 28, 41 % at 32,
    **60 % at 36**, 77 % at 40, 90 % at 44, 97 % at 48 (deep10: 17 / 20 / 27 / 36 / 52 / 72 /
    87 / 95). So the 2-ply shift from v2b did not saturate between the two strong nets; it
    resumed. *Predictive; all nets and `deep8_c1_300_e4`.* `tools/decision.py` →
    `runs/plan5_A3*_decision_*.out`, `runs/step7c_decision.out`,
    `runs/plan6/I1_A3a_decision_on_v2a.out`, `runs/plan6/I1_A3b_decision_on_deep10late.out`.
21. **X wins settle earlier (ply 32) than O wins (39–40) and draws (39–41).**
    `deep8_c1_300_e4`: 32 / 39 / 40 on the v2a games, 30 / 39 / 39 on strong play (2026-09-10).
    *Predictive; all nets and `deep8_c1_300_e4`.* Same files.
22. *Caveat:* the "settled" statistic uses a ±0.33 threshold on a 3-way prediction; deep10
    rates the opening above +0.33 for X, so 10–17 % of X-win games count as settled from
    ply 0. Medians are robust to this, the 10th percentile is not. The caveat grows with
    strength: `deep8_c1_300_e4` rates the opening +0.31 on average over its own games and
    counts **21–22 %** of games as settled at ply 0 (2026-09-10).
23. **Intuition and search part company in the middlegame.** The raw policy's move differs
    from the 256-sim search's in 34 % of positions overall, 20 % at plies 2–9, **44 % at
    plies 30–39**, 24 % after ply 50; the raw value differs from the search value by 0.19
    on average, peaking at 0.35 at plies 40–49. Same shape on v2a. **On `deep8_c1_300_e4`,
    on the same 7188 positions, the moves agree more and the values do not** (2026-09-10):
    disagreement **30.8 %** overall, 21.1 % at plies 2–9, **37.8 % at 30–39**, 23.2 % after
    ply 50, while the mean value gap is 0.191 (deep10 0.185), still peaking at 0.338 at plies
    40–49 (0.345). The middlegame is where they part on both nets; the stronger net's policy
    has closed 6 points on its search there and its value head has closed nothing.
    *Behavioural vs search-relative; deep10, v2a, `deep8_c1_300_e4`.* `tools/surprise.py` →
    `runs/plan5_B4_surprise_deep10.out`, `runs/plan6/I1_B4_surprise.out`.

## 5. How games end

24. **X wins about 63 % of strong self-play games, O 24 %, 13 % are drawn** (deep10's
    iterations 280–299, 100 854 games at 64 sims with exploration; deep8_300 61 / 26 / 13;
    v2a 60 / 29 / 11). In paired matches between the strong nets X's share is 59–62 % and
    15–25 % of games are drawn. **`deep8_c1_300_e4` (99 346 of its own games): X 62.7 %,
    O 20.7 %, drawn 16.6 %** (2026-09-10). X's share has stopped rising; O's keeps falling and
    the draw share is half again what it was at +242 — what a stronger net takes is not X wins
    but draws out of O's column. *Descriptive; X flat since deep10, draws still rising.*
    `tools/corpus_stats.py` → `runs/plan5_A6_corpus_*.out`; `runs/plan5_A8.out`;
    `runs/plan6/I1_A6_corpus_stats.out`.
25. **The count rule decides about a quarter of strong games:** 14 % end by a board count
    and 13 % by an equal count (a draw), 73 % by a macro line; flat since v2a (15 / 11 /
    74). **It is not flat any more: `deep8_c1_300_e4` ends 16.5 % by a board count and 16.6 %
    by an equal count — a third of its games, not a quarter — and 67.0 % by a macro line**
    (2026-09-10). The tiebreak rule stayed a constant share over 250 Elo of strength and then
    moved 6 points in the last 120. *Descriptive; flat to deep10, then rising.* Same;
    `runs/plan6/I1_A6_corpus_stats.out`.
26. **Nearly every draw is 4–4 with one full board:** 96.6 % of deep10's drawn games
    (deep8_300 97.0 %); 3–3 with three full boards is 3 %; the board-count lead changed
    hands during 63 % of draws; draws run 2 plies longer than the average game (53.8 vs
    51.9). `deep8_c1_300_e4`, over its 16 471 drawn games: 96.3 % / 3.7 %, the lead changed
    hands in 65.5 %, draws 1.7 plies longer (54.5 vs 52.8) (2026-09-10) — the shape of a draw
    is the same at +363, there are just far more of them (24). *Descriptive; all three of the
    nets whose own corpora were read.* `tools/principles.py` →
    `runs/principles_deep10.json`, `runs/principles_deep8.json`,
    `runs/plan6/I1_principles_deep8e4.json`.
27. **Games last ~52 plies** (mean 51.9, p10 46, p90 58, max 72–75) and lengthen with
    strength (v2a 49.4). About 4.4 free moves occur per game and 97 % of games contain
    one. **`deep8_c1_300_e4`: mean 52.8** (median 53, p10 47, p90 59, max 74), **5.08 free
    moves per game** and 98.5 % of games with one (2026-09-10) — both still climbing, the free
    moves fastest (4.4 → 5.1 over 120 Elo). *Descriptive; lengthens with strength on every net.*
    `plan5_A6_*.out`, `runs/plan6/I1_A6_corpus_stats.out`.

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
    development set from here on. `plan5_A9_test_*.out`. **The v3 split, read on the strongest
    net (2026-09-12, PLAN7 J1a — `endgame_v3_test` read once, as pre-registered):**
    `deep8_c1_300_e8` scores **92.7 [91.8, 93.6]** on the sealed `endgame_v3_test` (draws 85.3 %,
    regret 0.027 [0.021, 0.034], 256-sim search 99.9 % [99.8, 100.0] optimal) and **91.6 [90.6,
    92.6]** on its development half `endgame_v3_dev` (draws 83.6 %, regret 0.024 [0.018, 0.030],
    search 100.0 %) — the sealed half reads **1.1 points higher** than the dev half, intervals
    overlapping: on one source corpus the pair agrees to about a point, in the direction a
    flattered development set would not produce. Against `endgame_v2_dev`'s 91.7 the sealed read is
    +1.0, at the edge of the pre-registered band, the two sets being from different corpora.
    `endgame_v3_test` is a development set from here on.
    `runs/plan7/J1a_endgame_v3_test_e8.out`, `runs/plan7/J1a_endgame_v3_dev_e8.out`.
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
    64-sim search 100 %; v2b 99.0 / 99.6 / 100 %, dev1 94.0 / 98.7 / 100 %. `deep8_c1_300_e4`
    on the 689 one-open-board positions (1.1 %) of the held-out set built for it from deep10's
    late games (`runs/probe_data_deep10late_e4.npz` — not its own corpus, as an earlier form of
    this line said; M0 review, 2026-09-12): **100 / 100 / 100** again (2026-09-10). A tablebase spliced into the search as a terminal lookup therefore has
    nothing to add to any of these nets. *Exact; all nets and `deep8_c1_300_e4`.*
    `tools/tablebase_grade.py` → `runs/plan6/I1_C5_tablebase_grade.out`.
32. **What the raw policy still gets wrong late is the count rule and tempo, not local
    tactics.** On 6000 strong-play positions with ≤ 14 empties, deep10's raw move loses
    exact value in 2.1 % (v2b 3.5 %); the 64-sim search in 0.12 % (7 positions). Motifs of
    the failures, in the same order as on v2b: tiebreak conversion 71 > giving a free move
    61 > holding a draw 51 > denying a free move 37 > a local win 20 > closing a board 4 >
    a macro win 0. Local-tactics failures fell most (26 → 16 % of puzzles). **On
    `deep8_c1_300_e4` the rate halves again** (2026-09-10, a fresh
    6001-position sample of the same corpus, written as `suites/puzzles_v3_dev.npz`): the raw
    move loses exact value in **1.0 %** (61 puzzles) and the 64-sim search in **0.03 %** (2 of
    6001). The head of the motif order holds — tiebreak conversion 32 > holding a draw 26 >
    giving a free move 23 > denying a free move 21 > a local win 15 > a macro win 3 > closing a
    board 0 — but local tactics are now a *larger* share of a smaller set (25 % of puzzles
    against deep10's 16 %), so "local-tactics failures fell most" describes the step from v2b to
    deep10 and not this one; what the strongest net's raw policy still gets wrong is the count
    rule and tempo, in the same proportion as before. *Exact; v2b, deep10 and
    `deep8_c1_300_e4`.* `tools/puzzles.py` → `suites/puzzles_v2_dev.npz` (+ `.json`, the 5 hard
    puzzles), `suites/puzzles_v3_dev.npz` (+ `.json`, the 2 hard puzzles),
    `runs/plan5_A7_puzzles_deep10_on_deep8late.out`, `runs/plan6/I1_A7_puzzles.out`.

## 7. Folk claims, tested

33. **"Never send the opponent to a board where one move wins it" is false as a rule.**
    deep10's 256-sim move does exactly that in **24 %** of positions (a random legal move:
    36 %) — 2 % in the opening, 25 % at plies 20–31, 51 % at 32–43, 67 % from ply 44 —
    and the **solver's optimal move does it 69 % of the time** on solved positions (64 %
    when the mover is winning, 51 % in drawn positions, 84 % when lost). deep8_300: 24 %
    and 70 %. **`deep8_c1_300_e4`: 24.6 % and 70.2 %** — by ply 2.2 / 26.5 / 50.6 / 66.5 %
    (2026-09-10). (The solver's column is a property of the position set, not of the net: read
    on the same held-out positions it is deep8_300's number to every digit. It is also the rate
    for *one* optimal policy — `tools/probe.py exact_pv3` takes the lowest-indexed optimal move
    — not the rate at which sending to a winnable board is *necessary*: where several moves are
    optimal, another tie-break could give another number; M0 review, 2026-09-12.) *Behavioural and
    exact; all three nets read.* `runs/principles_*.json`,
    `runs/plan6/I1_principles_deep8e4.json`.
34. **What is true instead:** the optimal move *never* hands the opponent an immediate
    macro win when the mover is not already lost (0.0 % of 3000+ solved positions; 0.0 % of
    `deep8_c1_300_e4`'s 4791, 2026-09-10), and
    the agent avoids sending to a winnable board early. The rule is a macro-line rule and
    an opening rule, not a general one. Same files.
35. **Conceding the centre board ("the Orlin gambit") costs what its lines cost, no more.**
    With threats controlled, the opponent owning the centre is worth +0.01 ± 0.04 on the
    search value (the raw head: −0.05 ± 0.04); the centre's premium in the raw head's
    counterfactual (+0.11 over a corner) is the fourth line through it. `deep8_c1_300_e4`
    gives the same null on the search value, +0.032 ± 0.044 (raw head −0.060 ± 0.046)
    (2026-09-10; the counterfactual half was not re-read — `tools/probe_value.py` is not in
    I1). *Search-relative / predictive; deep10 and `deep8_c1_300_e4`.*
    `plan5_B3_value_deep10.out`, `plan5_B4_probe_value_deep10.out`,
    `runs/plan6/I1_B3_value_decomp.out`.

## 8. What the network computes (the net on its own terms)

36. **The board encoding already exposes** the free-move flag, the target board, the count
    margin, open boards, empties and every board's status: a linear read-out on a randomly
    initialised net recovers them at 98–100 %. No claim that the net "represents" these
    is meaningful. `deep8_c1_300_e4`'s control says the same, 98.5–100 % (2026-09-10).
    *Probe control; deep10 and `deep8_c1_300_e4`.* `tools/probe.py`, `tools/probe_report.py` →
    `runs/deep10_c1_300/probes.{json,png}`, `runs/deep8_c1_300_e4/probes.{json,png}`,
    `runs/plan6/I1_B2_probe_report.out`.
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
    by 110–140, local win +0.13 at block 5 by 40, z +0.05 by 180). **`deep8_c1_300_e4` gives
    the grid a fourth time, with the same gains and everything learned earlier** (2026-09-10;
    8 blocks, so its last block is 8): dead boards R² **+0.53 at block 4, by iteration 140**;
    the exact value of ≤ 14-empty positions **+27 points at block 8, by 140**; the search's best
    move +14 at block 8, by 160; macro threats for / against R² +0.16 / +0.14 at block 6, by
    40–100; an available local win +11 at block 5, **by 10**; an opponent's local threat +5 at
    block 7, by 60; the game result +5 at block 8, by 220. The gains repeat deep10's within a
    few points and the layer ordering is unchanged; the *learned-by* column is 20–50 iterations
    earlier on every concept but the last one. *Decodability; all four strong nets.* Same files;
    `runs/deep8_c1_300/probes.{json,png}`,
    `runs/deep10_c1_300_s1/probes.{json,png}`, `runs/deep8_c1_300_e4/probes.{json,png}`.
38. **Tactics are shallow and early, value is deep and late:** local concepts are readable
    by block 5 and learned in the first 60–80 iterations; macro-line threats peak in the
    middle of the trunk and fade toward the heads; the value-like concepts live in the last
    blocks and step at the LR drop, together with the endgame metrics they explain.
    Nothing new appears after iteration 240 (200 on the seed replicate). `deep8_c1_300_e4`
    repeats all of it (2026-09-10): tactics at block 5 and inside the first 60 iterations (an
    available local win by 10), threats peaking at block 6 and fading toward the heads, the
    exact value stepping **0.901 → 0.917 across the first LR drop** (checkpoints 200 → 220) as
    deep10's stepped 0.874 → 0.891, and nothing new after 240. *Decodability; all four strong
    nets.* Same.
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
    `deep8_c1_300_e4` reads higher on both and keeps the ordering: **44.8 % against a 37.8 %
    control** for the move two plies on, 72.8 vs 58.7 for the current move (2026-09-10) — +7
    points of gain for the line it is about to follow against +14 for the move it is about to
    play. *Decodability; both seeds and `deep8_c1_300_e4`.* Same.
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
    shape. `deep8_c1_300_e4` on deep10's games, 73 749 open boards (2026-09-10): 51.8 %
    overall (majority 39.3, local logistic 48.0, trained-trunk probe 51.7, random-trunk probe
    49.8), within 2 points of the local features before ply 32, 57.7 % against 49.7 / 52.9 at
    32–43, and **70.8 % against 51.1 (local) / 53.6 (random trunk) / 65.9 (trained trunk)** at
    plies 44+ — the same shape a third time. So the trunk computes late-game ownership that
    neither the board's local features
    nor an untrained trunk carry, and the head reads it; early ownership is not predictable
    from the position by any of these read-outs. Switching the auxiliary heads off was a
    strength null (RETROSPECTIVE §3): the head's late-game knowledge is what the value head
    needs anyway. *Decodability + behavioural null; both strong nets and `deep8_c1_300_e4`.*
    `tools/ownership_grade.py` → `runs/plan6_E9_ownership_deep10.out`,
    `runs/plan6_E9_ownership_deep8.out`, `runs/plan6/I1_E9_ownership_grade.out`.
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
    that account — its case is sample efficiency (PLAN6 Phase G; tested in self-play
    2026-09-09 and lost — the D4 group-convolutional net trained on the strongest recipe is
    −220 Elo against its parent, 50). On `deep8_c1_300_e2` the
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
    largest single step of the ladder (46); **doubling them again (`deep8_c1_300_e4`,
    2026-09-08) adds +64 more, +185 over deep8_c1_300 and +363 over v2b — then the
    strongest net measured (49).** The one architectural arm of that chain does not make a rung:
    `gcnn8_c1_300_e4` (the same recipe with a D4 group-convolutional trunk at the same
    inference cost, 2026-09-09) scores **+162 vs v2b** — between deep8_c1 and deep8_c1_300 —
    −220 against its parent `deep8_c1_300_e4` and −50 against deep8_c1_300: hurt (50).
    **A third doubling (`deep8_c1_300_e8`, `--epochs 8`, 2026-09-10) adds +40 [+23, +57] over
    `_e4` and is the strongest net measured — but it still reads +363 vs v2b, the same number as
    its parent: the reference has saturated at this strength, and the head-to-head against the
    parent, not the v2b score, is what resolves a rung from here on (51).**
    *Behavioural.* `runs/*/analysis.out`.
44. **At equal compute the deep, long-trained net wins for the first time:** deep10@64
    beats v2b@427 (6.7× the sims) by +42 [+23, +61]; but deep10@64 vs deep8_300@80 is −11
    [−30, +7] — the last rung is a wash at a fixed inference budget; duration, not depth,
    is where deployment strength came from. The seed replicate agrees from the other side:
    at equal sims the 8 → 10 step is inside the seed band (43). And the 8-block net trained
    with twice the updates beats the 10-block net by +86 [+67, +105] at equal sims while
    costing 0.81× per evaluation (46): *updates*, not depth. With four times the updates the
    same 8-block net beats it by +141 [+121, +160] at the same 0.81× (49) — and it costs
    exactly what the twice-updated net costs, so that +64 is free at play time. With eight times
    the updates it beats it by +186 [+165, +208] (51), at that same 0.81× again: the eight-pass
    net is exactly as expensive to evaluate as the one-, two- and four-pass nets of the same
    shape, so its +40 over `_e4` is free at play time too. *Behavioural.*
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
    throughout; 70 of 153 600 steps were skipped by the GradScaler. **Two passes is not the
    plateau either: the dose–response follow-up doubled them again for another +64 (49), and a
    third doubling adds +40 more (51)** — +100, +64, +40 across three doublings, each worth
    about two-thirds of the one before it, and none of them the plateau.
    *Behavioural; one run read against three references, seed band ≈ 3 points.*
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
    **Restated 2026-09-09 (PLAN6 H4's sweeps, the same two arms on `gdata_v1` carried past
    3 120 steps): the G-CNN's advantage is a *small-step* advantage, and it reverses.** At
    lr 0.02 and 400 000 × 16 = 6 240 steps the G-CNN is **0.7875** and the ResNet **0.8145** —
    the gap has shrunk from 0.078 to 0.027, the doubling worth 0.070 to the ResNet and 0.018 to
    the G-CNN. At 400 000 × 32 = 12 480 steps **the ResNet overtakes: 0.7630 against 0.8298**,
    and the G-CNN's dev KL is now worse than at 6 240 and worse than at 3 120 while its training
    loss keeps falling (0.899 → 0.782 over the last pass) — it is over-fitting the frozen 400 k
    set, its KL on the dev positions with no canonical twin in train rising 1.026 → 1.135 where
    the ResNet's falls 0.960 → 0.931. That is what a net for which D4 augmentation is an exact
    no-op does on its 32nd identical pass, while the ResNet is on its fourth pass over eight
    views. A lower LR is not the missing ingredient: at lr 0.005 × 12 480 steps the G-CNN is
    **0.8447**, worse than its own lr-0.02 number at the same steps. (The value head crosses
    earlier: at 6 240 steps the ResNet's Brier is 0.1006 against 0.1182 and its endgame_v2_dev
    WDL 69.7 against 67.5 %, both of which the G-CNN led at 3 120.) So the gate readings above —
    both equivariant arms passing gate (i), and the G-CNN passing gate (ii) — hold *at 3 120
    steps*, 1 % of the RL exposure they were gating, and do not survive 12 480: **a supervised
    gate has to be read at a step count of the
    order of the run's**, or until the curves have crossed or clearly will not. The self-play
    reading is 50 — the G-CNN loses 220 Elo to its parent, capacity and not the LR. **The
    tied-heads arm survives the same test** (sweep 3, the same day): resnet8_tied is **0.7877**
    at 6 240 steps and **0.7408** at 12 480 against the ResNet's 0.8145 / 0.7630 — ahead on every
    metric at 12 480 (top-1 0.620 vs 0.611, Brier 0.094 vs 0.096, exact 3-way 0.849 vs 0.840,
    disjoint-position KL 0.897 vs 0.931, endgame_v2_dev WDL 73.1 vs 72.6 %, regret 0.104 vs
    0.124) with no over-fitting signature; its margin shrinks slowly, 0.036 / 0.027 / 0.022 over
    the three doublings, rather than reversing, and a straight line in log-steps reaches zero
    near a run's 307 200 — so the self-play prediction for `--head_tying 1` is null-to-small,
    and it is proposable, not proposed (PLAN6 Handover). What separates it from the G-CNN is a
    full 2.39 M-parameter trunk on which augmentation is still informative; the tying is only
    in the read-out. `runs/plan6/H4_lr_*.json`, `runs/plan6/H4_lr2_*_x32.json`,
    `runs/plan6/H4_lr3_resnet8_tied_lr0.02.json`.
    **Restated 2026-09-10 (PLAN6 §9b, G arm (g)): at the ResNet's *parameter* count the G-CNN
    closes the same way, and the equivariant line closes with it.** `gcnn8x46` — 8 blocks of 46
    base filters × 8 orientations, **2 459 392 parameters against resnet8's 2 456 014** (0.1 %
    apart) and **7.0× its measured inference cost** (595 vs 85 ms per 4096 evaluations on the
    3060, 1.28× at batch 1; `runs/plan6/G_timing_3060_gcnn8x46.json`), so it is expressly *not*
    an equal-cost arm — on `gdata_v1` at lr 0.02, seed 0, dev policy KL vs the teacher, with
    resnet8 / gcnn8x16 at the same steps in brackets: 3 120 steps **0.7636** [0.884 / 0.806] —
    **the best fit of any student this project has trained at the gate's step count** (top-1
    0.639, exact 3-way 0.829, endgame_v2_dev WDL 69.4 %, regret 0.140); 6 240 steps **0.9195**
    [0.8145 / 0.7875]; 12 480 steps **1.0336** [0.7630 / 0.8298]. Its KL on the dev positions
    with no canonical twin in train rises 1.033 → 1.322 → 1.516 (the ResNet's 0.960 → 0.931 over
    the same last doubling); the D4 residual is 0 at every point. Read by §9b's pre-registered
    rule at 12 480 steps: **it trails resnet8, and the margin reverses by 6 240** — the
    equivariant line closes, and nothing is proposed. The caveat that goes with the number:
    at 3 120 steps the wide G-CNN extracts more per step than any net measured here, and what
    follows is memorisation of 400 000 positions for which D4 augmentation is an exact no-op
    (the ResNet sees eight views of each), so what the frozen-data protocol shows is that **the
    wide net is data-limited by ≈ 8× at equal capacity where the ResNet is not** — it cannot say
    whether its self-play prospect, with fresh data every iteration, differs from the narrow
    net's. A data-matched supervised test would need ≈ 8× `gdata_v1` (≈ 40 h of teacher
    labelling on the 3090) and is not proposed: the 7.0× inference cost disqualifies the net as
    a ladder rung, and the project's purpose does not need the answer.
    `runs/plan6/G_arm_gcnn8x46.json`, `runs/plan6/G_timing_3060_gcnn8x46.json`.
49. **Doubling the optimizer steps again is worth another +64 Elo** (PLAN6 H1b, 2026-09-08).
    `deep8_c1_300_e4` is `deep8_c1_300_e2`'s recipe with `--epochs 4`: 1024 steps of batch
    1024 per iteration instead of 512, over the same 4096 × 64 new positions per iteration,
    the same 2 M-row buffer (mean sampled replay age 3.35 iterations of a 7.6-iteration
    window), the same LR drops at 200 / 280, seed 0 — +2.4 h of training on a 16.9 h run.
    On the full paired suite at 64 sims it scores **59.1 % [56.3, 61.8], +64 Elo [+44, +83]
    against its parent** — helped, 6 points clear of the rule and twice the ≈ 3-point seed
    band — **74.4 % [72.0, 76.7], +185 [+164, +207] against deep8_c1_300**, 69.2 % [66.7,
    71.6], +141 [+121, +160] against deep10_c1_300, 71.3 % [68.9, 73.6], +158 [+138, +178]
    against the 10-block seed replicate, and **89.0 % [87.4, 90.6], +363 Elo [+337, +395]
    against v2b** (92.5 % [91.0, 94.0], +437 against dev1). Four sampled examples per generated position is not the plateau either:
    the learner is update-limited at two passes as it was at one (46), with no sign of the
    buffer window being over-fitted (the sampled distinct-position fraction falls 0.67 → 0.62
    against H1's 0.81 → 0.75, and 133 of 307 200 steps were skipped by the GradScaler —
    H1's rate). Raw heads: endgame_v1 WDL **90.1 % [89.0, 91.2]**, draw recognition 79.0 %,
    regret 0.022 [0.016, 0.028] (H1 87.6 / 74.8 / 0.036; deep10 84.6 / 0.037); endgame_v2_dev
    90.5 [89.5, 91.6], regret 0.029 [0.023, 0.036] (H1 87.5 / 0.034); the 256-sim search
    99.9 % optimal on both. The full-suite timeline (`eval_full.jsonl`, every 10th checkpoint
    at ±2.8): ahead of H1 at every checkpoint, most of it early (67.0 vs 52.1 % vs v2b at
    iteration 50), 80.5 vs 75.9 at 200 — where it is already level with H1's *final* net
    (47.3 %) — the first drop adds the usual ≈ +6 (86.1 at 210), then flat within ±3 to 300
    (86.6–89.0), the second drop nothing. Exact symmetry is not what it bought: the final D4
    Jensen–Shannon residual is 0.026 bits and the value std 0.052, against H1's 0.026 / 0.050.
    Cost: t_train 4.98 h vs 2.55 h, wall 16.9 h vs 14.6 h; the same 8×128 ResNet, so the same
    cost per evaluation as H1's and 0.81× deep10's. **Four passes is not the plateau either:
    the third doubling is another +40 [+23, +57], and the dose–response reads +100 → +64 → +40
    (51).** *Behavioural; one run read against its
    parent, seed band ≈ 3 points.*
    `runs/deep8_c1_300_e4/{analysis.out,eval_full.jsonl,timeline.png}`,
    `runs/plan6/H1b_timeline.out`, PLAN6 log.
50. **An exactly equivariant trunk at the same inference cost loses 220 Elo in self-play**
    (PLAN6 H4, 2026-09-09). `gcnn8_c1_300_e4` is `deep8_c1_300_e4`'s recipe with the ResNet
    trunk replaced by a D4 group convolution (`--gcnn 16`: 16 base filters × 8 orientations =
    an activation width of 128, 312 k parameters against the ResNet's 2.46 M, exported to
    ordinary convolutions so it costs what the 8×128 ResNet costs to evaluate), nothing else
    changed. On the full paired suite at 64 sims it scores **22.0 % [19.9, 24.2], −220 Elo
    [−242, −199] against its parent** — hurt by the pre-registered rule (≥ 53 % helped,
    ≤ 47 % hurt), 25 points below the line and eight seed bands — and **42.8 % [40.2, 45.4],
    −50 [−69, −32] against deep8_c1_300**, the 1×-update ResNet of the same shape and
    duration; 31.6 % [29.2, 34.2], −134 against `deep8_c1_300_e2`, 37.1 %, −92 against
    deep10_c1_300, 41.5 %, −59 against the 10-block seed replicate, +79 against deep8_c1,
    +114 against wide128_c1, **71.7 % [69.2, 74.1], +162 [+141, +182] against v2b** and +260
    against dev1 — a ladder rung between deep8_c1 (+100) and deep8_c1_300 (+211), with four
    times the updates of either. **The pre-registered secondary, exact symmetry, holds and is
    not what was missing:** the D4 Jensen–Shannon residual is 0.000 bits and the value std
    0.000 at all 30 checkpoints (the parent's 0.026 / 0.052) — the equivariant export survived
    the fused fp16 graph path for the whole run. Raw heads: endgame_v1 WDL **80.8 % [79.4,
    82.2]**, draw recognition 60.5 %, regret 0.058 [0.048, 0.068], optimal 95.1 % (parent
    90.1 / 79.0 / 0.022 / 98.1; deep8_c1_300 84.0 / 0.045); endgame_v2_dev 82.5 [81.1, 83.8],
    draws 68.1 %, regret 0.056 (parent 90.5 / 0.029); the 256-sim search 99.8 / 99.7 % optimal
    on the two sets — search repairs the raw head here as everywhere. Nothing was unstable:
    132 of 307 200 steps skipped by the GradScaler (parent 133), no NaN or Inf in any logged
    field, the losses falling to 1.12 policy / 0.73 value over the last 20 iterations against
    the parent's 1.00 / 0.67 — it converged, stably, to a much weaker net. Two things no
    ResNet showed. The **first LR drop is worth +30.7 points** to it (29.4 → 60.1 % vs v2b,
    +223 Elo) against the ResNets' +4.8 … +8.5, after a constant-LR phase in which it *lost*
    ground from 150 to 200 (39.9 → 29.4) while the parent gained; and **the second drop is a
    resolved +6.5** (65.2 at 260 → 71.7 at 300) where F2 found nothing resolvable on four
    ResNets (+2.6 / +4.1 / −0.4 / −0.3): each LR reduction lowers this net's floor by more
    than a ResNet's. Cost: t_selfplay 12.21 h against 11.93 (**1.02× — the equal-cost claim of
    48 holds at play**), t_train 7.58 h against 4.98 (1.52×, the per-step weight expansion and
    the per-iteration re-export), wall 19.8 h against 16.9. **The mechanism is capacity, not
    the effective learning rate.** The obvious story — a bank's gradient is the sum over its 8
    expanded copies, so the effective LR is 8× — is refuted by measurement: the summing is
    real (2.8–6.5× per trunk layer) but the BatchNorm weight-norm equilibrium absorbs it,
    leaving the relative step ‖g‖/‖w‖ 1.19× the ResNet's in the trunk and 1.41× in the heads.
    What is different is curvature — the top Hessian eigenvalue of the same loss is 2.3× the
    ResNet's — and, decisively, the supervised advantage that licensed the run is a small-step
    advantage: on `gdata_v1` at lr 0.02 the dev policy KL is 0.806 (G-CNN) against 0.884
    (ResNet) at 3 120 steps, 0.7875 against 0.8145 at 6 240, and 0.830 against **0.763** at
    12 480, where the ResNet overtakes and the G-CNN is over-fitting the frozen set; a quarter
    of the LR at those 12 480 steps recovers nothing (0.845). Phase G's gate was read at 1 % of
    this run's 307 200 steps, and self-play read the reversed ordering (48). The G-CNN is not
    proposed again at this width; the equal-cost requirement rules out a wider one; the play
    agent stays `deep8_c1_300_e4/net_0300.pt`. (The run was interrupted at iteration 268 by a
    Windows Update restart and resumed as attempt 1 from iteration 260, every file verified
    intact; iterations 260–268 are a perturbed re-run, so `log.jsonl` is read de-duplicated by
    iteration.) **And the width is not what cost it the 220 Elo:** the same architecture at the
    ResNet's parameter count (`gcnn8x46`, 2.46 M parameters at 7.0× the inference cost) also
    trails the plain ResNet at 12 480 supervised steps, with the margin reversing by 6 240 — the
    narrow net's curve, one capacity up (48, restated 2026-09-10). *Behavioural; one run read
    against its parent, seed band ≈ 3 points.*
    `runs/gcnn8_c1_300_e4/{analysis.out,eval_full.jsonl,timeline.json}`,
    `runs/plan6/H4_timeline.out`, `runs/plan6/H4_lr_*.json`, `runs/plan6/H4_lr2_*_x32.json`,
    `runs/plan6/H4_diag/`, PLAN6 log 2026-09-09.

51. **Doubling the optimizer steps a third time is worth another +40 Elo, and the v2b
    yardstick runs out** (PLAN6 §9a, H1c, 2026-09-10). `deep8_c1_300_e8` is
    `deep8_c1_300_e4`'s recipe with `--epochs 8`: 2048 steps of batch 1024 per iteration
    instead of 1024 — 614 400 in the run — over the same 4096 × 64 new positions per
    iteration, the same 2 M-row buffer (mean sampled replay age 3.31 iterations), the same
    LR drops at 200 / 280, seed 0, nothing else changed; launched 21:24 on 2026-09-09,
    done 19:22 on 2026-09-10 after 21.96 h, 0 crashes. On the full paired suite at 64 sims
    it scores **55.8 % [53.3, 58.2], +40 Elo [+23, +57] against its parent** — helped by the
    pre-registered rule (≥ 53 %), but 2.8 points over the line and within one ≈ 3-point seed
    band of it, the narrowest adoption in the chain (the E7 worker's independent read of the
    same checkpoint agrees: 55.8 [53.4, 58.2]) — **65.3 % [62.8, 67.8], +110 [+91, +130]
    against `deep8_c1_300_e2`**, 77.1 % [74.8, 79.2], +211 [+189, +232] against
    deep8_c1_300, 74.5 % [72.1, 76.8], +186 [+165, +208] against deep10_c1_300, 76.1 %
    [73.9, 78.2], +201 against the 10-block seed replicate, +311 against deep8_c1, +334
    against wide128_c1, and **89.0 % [87.2, 90.7], +363 Elo [+333, +397] against v2b — the
    same 89.0 % H1b read**: the reference has saturated at this strength (differences
    compress near 90 %), so the head-to-head against the parent, not the v2b score, is the
    instrument from here on. Against dev1, 95.3 % [94.2, 96.4], +523. **The dose–response of
    the update lever, in full: +100 (256 → 512 steps per iteration, 46), +64 (→ 1024, 49),
    +40 [+23, +57] (→ 2048)** — each doubling worth about two-thirds of the one before it,
    all three positive, and eight sampled examples per generated position is still not the
    plateau. The full-suite timeline (`eval_full.jsonl`, every 10th checkpoint at ±2.8),
    vs v2b at iterations 10 / 50 / 100 / 150 / 200 / 210 / 220 / 260 / 280 / 290 / 300 with
    H1b's beside it: 32.1 / 74.1 / 78.6 / 81.2 / 82.4 / 86.4 / 88.3 / 89.9 / 90.4 / 90.5 /
    89.0 against 24.7 / 67.0 / 75.0 / 79.1 / 80.5 / 86.1 / 87.3 / 86.6 / 87.2 / 88.1 / 89.0
    — ahead at every checkpoint before the drop, most of it early (+7.1 at iteration 50).
    Against H1b's *final* net over the same checkpoints: 7.0 / 22.5 / 31.4 / 33.6 / 33.7 /
    49.9 / 50.9 / 52.3 / 51.0 / 53.6 / 55.8 — level with it by 210, the first drop worth
    +4.0 (82.4 → 86.4 vs v2b), then 1–3 points ahead through the low-LR phase. Raw heads:
    endgame_v1 WDL **91.3 % [90.3, 92.4]**, draw recognition 81.0 %, regret 0.022 [0.016,
    0.028], optimal 98.1 % (H1b 90.1 / 79.0 / 0.022 / 98.1); endgame_v2_dev 91.7 [90.7,
    92.7], draws 83.6 %, regret 0.020 [0.015, 0.026] (H1b 90.5 / 0.029); the 256-sim search
    100.0 % optimal at regret 0.000 on both sets. On the timeline's 20 000 held-out
    positions from deep10_c1_300 the endgame WDL steps 87.0 → 89.9 across the first drop
    (200 → 210) and reaches 91.3 at 300, while the final D4 Jensen–Shannon residual is 0.025
    bits and the value std 0.047 (H1b 0.026 / 0.052): **eight passes bought no more symmetry
    consistency than four or two.** Budget axes: 244 of 614 400 steps were skipped by the
    GradScaler (H1b 133 of 307 200 — the same rate), the mean sampled replay age is unchanged
    at 3.31, and **the sampled distinct-position fraction is 0.48 → 0.45 against H1b's
    0.63 → 0.63 and H1's 0.81 → 0.75 — each generated row is now drawn about eight times** —
    and nothing else in the run complains: policy-target entropy 0.18 bits (0.165), raw/search
    KL 1.49 → 0.85 (the same), root Q range 0.36 → 0.51 (0.36 → 0.49), and over the last 20
    iterations policy loss 0.992 (1.001) and value loss 0.653 (0.667), self-play 53.2 plies
    (52.8), draws 16.6 % (16.6), count endings 15.7 % (16.5). Cost: t_train 9.97 h against
    4.98, t_selfplay 11.98 against 11.93, wall 21.96 h against 16.92 — the training half has
    doubled again and the self-play half has not — but it is the same 8×128 ResNet, so exactly
    the same cost per evaluation as `_e4`, `_e2` and deep8_c1_300: the +40 is free at play
    time (44). The reading: helped, still update-limited at eight passes, and the play agent
    becomes `runs/deep8_c1_300_e8/net_0300.pt`. Nothing further is proposed — PLAN6 §9's
    closing programme is complete and E11 follows. *Behavioural; one run read against its
    parent, seed band ≈ 3 points.*
    `runs/deep8_c1_300_e8/{analysis.out,eval_full.jsonl,timeline.json}`,
    `runs/plan6/H1c_timeline.out`, PLAN6 log 2026-09-10.

## 10. Open, and not claimed

- The dose–response of the optimizer-step lever is +100 → +64 → +40 and still positive (51),
  so `--epochs 16` — a fourth doubling, ≈ 32 h — is the obvious continuation; it is **not**
  proposed: the last step is 2.8 points over the adoption line, its successor is predicted
  inside the seed band, and PLAN6 §9's programme is closed.
- The opening book stops at depth 4 with three replies per node; nothing is claimed about
  lines beyond it.
- The per-owned-board residual (14) survived the seed replicate to the third decimal and is
  smaller again on `deep8_c1_300_e4` (+0.02 … +0.05); the class order (15) did not appear on
  the replicate and does not on `_e4` either, whose two fits of the same net disagree with each
  other (A4 centre > edge > corner, B3 corner > edge > centre), so it stays unresolved and is
  now best read as noise. One coefficient path is deep10-only — the raw head's free-move
  weight falling from +0.19 to +0.14 over
  training (PLAN5 §3 B3); the search value's rise +0.05 → +0.09 is on both seeds. *(2026-09-10:
  confirmed deep10-only. On `deep8_c1_300_e4` the raw path rises, +0.04 → +0.19, as deep8_300's
  does; 11.)*
- The self/opponent asymmetry in the ownership coefficients flips between the raw and the
  search value and is not reported.
- `endgame_v2_test` was read once (30). **A new sealed set exists (PLAN6 E10):** `suites/endgame_v3_test.npz`,
  3000 solved positions from `deep10_c1_300_s1`'s iterations 280–299, split from `endgame_v3_dev` by source
  game before solving, 0 canonical positions shared between the halves and none duplicated within them
  (`tools/suite_overlap.py`). Held out for deep10, deep8_300 and any Phase G student — not for the seed
  replicate, whose games it comes from. **Read once, on `deep8_c1_300_e8`, 2026-09-12 (PLAN7 J1a):
  92.7 [91.8, 93.6] against the dev half's 91.6 [90.6, 92.6] — the sealed half higher by 1.1 (30). A
  development set from here on; no sealed endgame set remains.**
- An exactly equivariant net at a full run's step budget is measured in self-play at one width
  only, 16 base filters × 8 orientations (50). **On frozen data the ResNet-capacity question is
  now answered, and the answer is no** (PLAN6 §9b arm (g), 2026-09-09, read 2026-09-10):
  `gcnn8x46` — the same architecture at 2.46 M parameters and 7.0× the measured inference cost —
  trails resnet8 at 12 480 steps and its margin reverses by 6 240 (48). The equivariant line is
  closed: no self-play run at any width is proposed. What stays open is narrower and is
  deliberately not being bought — the frozen-data protocol cannot separate "the inductive bias
  is wrong for this game" from "the net is data-limited by ≈ 8× because D4 augmentation is an
  exact no-op for it", and the data-matched test needs ≈ 8× `gdata_v1`, ≈ 40 h of teacher
  labelling, for a net the equal-cost rule already disqualifies as a rung. The cheaper
  D4-tied-heads hedge survives the step-count test of 48 to 12 480 steps with a slowly closing
  margin; whether that margin survives a full run is untested (proposable as PLAN6 H5, not
  proposed).
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
