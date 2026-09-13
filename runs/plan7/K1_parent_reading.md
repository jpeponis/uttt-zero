# K1's count-rule parent, re-read: `deep8_c1_300_e8` against `deep8_c1_300_e4`

*PLAN7 §5 item 1 and J1's cheap re-read. The I1 tool set (`runs/plan6/I1_second_pass_3060.sh`) run on
`deep8_c1_300_e8/net_0300.pt` (+40 Elo over `_e4`, +363 vs v2b) under the **count** rule, 2026-09-12
22:14 – 2026-09-13 02:40 on the 3060; script `runs/plan7/K1_parent_count_pass_3060.sh`, outputs
`runs/plan7/K1_parent_*.out` and `*.json`, plus `runs/book_deep8_e8.json` / `.md`,
`runs/probe_data_deep10late_e8.npz`, `runs/deep8_c1_300_e8/probes.{json,png}` and
`value_decomp.{json,png}`, `suites/puzzles_v4_dev.npz` / `.json`. The pre-registered rule is I1's:
**HELD** — sign and ordering agree with the `_e4` reading **and** the new magnitude is inside the
`_e4` interval; **MOVED** — sign and ordering agree, magnitude outside it; **REVERSED** — a sign or
an ordering disagrees. Where no interval was ever quoted the verdict is marked **[no CI]** and "held"
means the same rank, sign, share or profile — never "inside an interval that does not exist" (M1).
This pass is also the count-rule baseline every reading of the draw-rule run K1 is compared with
(PLAN7 §5 item 2).*

*Two numbers below are recomputations from the JSONs on disk, not tool output, and are marked
**[recomputed]**: the cross-net Kendall τ of claim 2 (from `runs/plan5_A1_atlas.json`,
`runs/plan6/I1_A1_atlas.json` and `runs/plan7/K1_parent_A1_atlas.json`, by `tools/atlas.py`'s own
`kendall_tau`, which reproduces M1's `_e4` values to six decimals) and claim 7's book agreement
against deep8_300 and deep10 and its flatness buckets (from the four `runs/book_*.json`, the method
validated by reproducing KNOWLEDGE 7's `_e4` figures — 70 % of 415, 88 / 66 / 39–52 — exactly).*

## The readings

| # | `_e4` reading (2026-09-10) | `_e8` reading (2026-09-13) | verdict | file |
|---|---|---|---|---|
| 1 | rank 1 [40] / rank 15 [13] in all 3 columns — 12 columns in all | rank 1 [40] / rank 15 [13] in all 3 columns — **15 of 15** | **HELD [no CI]** (the repeated rank) | `K1_parent_A1_atlas.out` |
| 2 | top four [40] > [36] > [0] > [37] at 16k ([0]/[37] swap at 1k, 4k); τ vs v2b 0.847619, vs deep10 0.885714, vs deep8_300 0.923810 | the same top four **in that order at all three budgets**; τ vs v2b **0.923810**, vs deep10 **0.923810**, vs deep8_300 **0.923810**, vs `_e4` **0.885714** **[recomputed]** | **MOVED [no CI]** | `K1_parent_A1_atlas.json` |
| 3 | [40] +0.495 at 16k, gap to [36] +0.100 | **+0.524**, gap to [36] **+0.095** | **MOVED [no CI]** | `K1_parent_A1_atlas.out` |
| 4 | flat (gap ≤ 0.03) after 9 of 15; range 0.09–0.26 except [40] (0.022), median 0.150 | flat after **10 of 15** at each of the three budgets; range **0.05–0.24** except [40] (**0.017**), median **0.144** | **HELD [no CI]** (the profile) | `K1_parent_A1_atlas_orbits.out` |
| 5 | [13] 0.142, [4] 0.090, [37] 0.051, [2] 0.073 (best reply the self-send [20]) | [13] **0.109**, [4] **0.041**, [37] **0.050**, [2] **0.017** — [20] still the best reply after [2] | **MOVED [no CI]** | `K1_parent_A1_atlas_orbits.out` |
| 7 | after [40] corner orbit 36 takes **0.709** of the visits, edge 37 0.291; the **edge** subtree +0.022 better for X; atlas agrees at 1k/4k/16k; agrees with deep8_300 on 70 % of 415 nodes, deep10 67 % of 404; flatness 88 / 66 / 39–52 % | after [40] corner orbit 36 takes **0.943**, edge 37 **0.057**; the **edge** subtree **+0.017** better for X (X +0.5399 after 37 against +0.5234 after 36); atlas agrees at all three budgets; agrees with `_e4` on **74 % of 465** (by depth 67 / 83 / 75 / 73, mean \|Δv\| 0.026), with deep8_300 **66 % of 439**, deep10 **65 % of 437** **[recomputed]**; flatness vs `_e4` **96 / 67 / 38–51 %** **[recomputed]** | **HELD** — the one enumerated reversal is confirmed and deepens | `K1_parent_C1_book.out`, `runs/book_deep8_e8.md` |
| 7a | self-send chosen in 213 of 447 free cells (**48 %**); visit share 0.85 vs 0.78; centre cell 4 % (25 of 562) | chosen in **226 of 465 (49 %)**; by depth 8/12, 17/32, 48/103, 153/318; visit share **0.86** vs 0.77; centre cell **4.8 %** (28 of 583) | **HELD [no CI]** (the rank and the profile) | `K1_parent_C1_book_stats.out` |
| 8 | free move **+0.1953 ± 0.0278** (search, A4, 30 000 positions) | **+0.1959 ± 0.0283** | **HELD [CI]** | `K1_parent_A4_freemove.out` |
| 9 | conditional free move **+0.1168 ± 0.0272**, macro win now +0.6083 ± 0.0582 — 0.60 of the unconditional | **+0.1187 ± 0.0277**, macro win now **+0.5991 ± 0.0595** — **0.61** of the unconditional | **HELD [CI]** | `K1_parent_B3_value_decomp.out` |
| 10 | plies 44–50 at count 0 / +1 / +2: +0.242 / +0.387 / +0.334; plies 32–43 runs with the count −0.156 / +0.013 / +0.108 / +0.140 / +0.244 | **+0.245 / +0.390 / +0.339**; plies 32–43 **−0.147 / +0.021 / +0.109 / +0.145 / +0.260** | **HELD [no CI]** (the profile) | `K1_parent_A4_freemove.out` |
| 11 | raw +0.2835 ± 0.0310 against search +0.1953 — gap **0.088**; the raw coefficient **rises** over training, the gap widens ≈ 0 → +0.070 | raw **+0.2868 ± 0.0319** against **+0.1959** — gap **0.091**; raw **rises** (+0.076 @10 → +0.189 @300, B3), the gap widens **+0.003 → +0.071** | **HELD [no CI]** (the gap has no interval; the path is a sign) | `K1_parent_A4_freemove.out`, `K1_parent_B3_value_decomp.out` |
| 12 | *not read* — deep10: tensor edit **+0.413** (median +0.324) against +0.20 natural, 2.1× | **+0.467** (median **+0.338**, p10 +0.064, p90 +1.034) on the identical 43 252 edits, against +0.196 natural — **2.4×** | **MOVED [no CI]** — first reading since deep10 | `K1_parent_B4b_probe_value.out` |
| 13 | threats **+0.148 ± 0.021 / −0.132 ± 0.018** | **+0.1410 ± 0.0217 / −0.1250 ± 0.0183** | **HELD [CI]** (against `_e4`'s intervals) | `K1_parent_A4_freemove.out` |
| 14 | A4 **+0.0489 ± 0.0388 / +0.0264 ± 0.0301 / +0.0382 ± 0.0271**; B3 **+0.0209 ± 0.0447 / +0.0337 ± 0.0336 / +0.0316 ± 0.0306** (centre / corner / edge); four of six exclude zero | A4 **+0.0410 ± 0.0394 / +0.0208 ± 0.0306 / +0.0341 ± 0.0275**; B3 **+0.0160 ± 0.0455 / +0.0324 ± 0.0342 / +0.0325 ± 0.0311**; **three** of six exclude zero — B3's corner now includes it | **HELD [CI]** in both models (all six inside `_e4`'s intervals) | `K1_parent_A4_freemove.out`, `K1_parent_B3_value_decomp.out` |
| 15 | A4 centre > edge > corner, B3 corner > edge > centre — the two fits disagree; the raw counterfactual *not re-read* (deep10 +1.052 / +0.941 / +0.827) | A4 centre 0.041 > edge 0.034 > corner 0.021; B3 edge 0.0325 ≈ corner 0.0324 > centre 0.016 (the top two 0.0001 apart); the raw counterfactual **+1.050 / +0.954 / +0.848**, the ordering a third time | **UNRESOLVED [no CI]** (the regressions); **HELD [no CI]** (the counterfactual ordering, first reading since deep10) | `K1_parent_A4_freemove.out`, `K1_parent_B3_value_decomp.out`, `K1_parent_B4b_probe_value.out` |
| 16 | raw **+0.082 @10 → +0.0222 ± 0.0122**; search **+0.047 → +0.0139 ± 0.0118** | raw **+0.074 @10 → +0.0188 ± 0.0126**; search **+0.049 → +0.0127 ± 0.0120** | **HELD [CI]** (raw and search) | `K1_parent_B3_value_decomp.out` |
| 17 | search threats +0.123 / −0.166 @10 against +0.1310 ± 0.0265 / −0.1363 ± 0.0201 @300; the widest swing 0.030, outside the final interval | **+0.128 / −0.166 @10** against **+0.1258 ± 0.0269 / −0.1285 ± 0.0205 @300**; the widest swing **0.0375**, again outside it | **HELD [no CI]** ("learned by 10–20"; "never moves" stays withdrawn) | `K1_parent_B3_value_decomp.out` |
| 18 | *not read* — deep10: centre **+0.017** (33 947 edits, p10 −0.647, p90 +0.677), corner +0.012, edge +0.014 | centre **+0.002** (p10 −0.671, p90 +0.669), corner **+0.016**, edge **+0.003**, on the identical edits | **HELD [no CI]** — first reading since deep10 | `K1_parent_B4b_probe_value.out` |
| 19 | local threat **−0.0860 ± 0.0145**; own local win **−0.0367 ± 0.0175** | **−0.0885 ± 0.0150**; **−0.0397 ± 0.0180** (both exclude zero) | **HELD [CI]** | `K1_parent_B3_value_decomp.out` |
| 20 | v2a games Q median **36** (27–40), raw 39, root 45; strong play Q **34** (25–40), raw 40, root 47; settled 21 / 23 / 30 / 41 / 60 / 77 / 90 / 97 % | v2a Q **36** (**22–40**), raw **38**, root 45; strong play Q **34** (**11–39**), raw **39**, root 47; settled **24 / 26 / 33 / 45 / 63 / 80 / 91 / 97 %** | **MOVED [no CI]** — the medians hold, the early half of the curve moves again | `K1_parent_A3a_decision_on_v2a.out`, `K1_parent_A3b_decision_on_deep10late.out` |
| 21 | X / O / draws **32 / 39 / 40** (v2a games), **30 / 39 / 39** (strong play) | **30 / 39 / 41**, **28 / 39 / 39** | **HELD [no CI]** (the ordering X < O ≈ draws) | same |
| 22 | rates the opening **+0.31** at ply 0; **21–22 %** of games settled from ply 0 | rates it **+0.33**; **24–25 %** settled from ply 0 (24.6 v2a, 24.0 strong play) | **MOVED [no CI]** — the caveat grows again | `K1_parent_A6_corpus_stats.out`, the two decision outputs |
| 23 | policy differs in **30.8 %** (21.1 / 37.8 / 23.2 by band); value gap **0.191**, peak 0.338 at 40–49 | **30.7 %** (**22.9 / 38.3 / 19.7**); gap **0.187**, peak **0.332** — the same 7 188 positions | **HELD [no CI]** | `K1_parent_B4_surprise.out` |
| 24 | X **62.7** / O **20.7** / drawn **16.6 %** (99 346 games) | X **63.2** / O **20.2** / drawn **16.6 %** (98 581 games) | **HELD [no CI]** — the split repeats within half a point; the *rise* in draws stops | `K1_parent_A6_corpus_stats.out` |
| 25 | by count **16.5 %**, equal count **16.6 %**, by line **67.0 %** — a third of games, up 6 points in 120 Elo | by count **15.7 %**, equal count **16.6 %**, by line **67.7 %** — **32.3 %**, down 0.8 | **MOVED [no CI]** — the level holds, the rise does not | `K1_parent_A6_corpus_stats.out` |
| 26 | 4–4 with one full board **96.3 %**, 3–3 with three **3.7 %**; lead changed hands **65.5 %**; draws 1.7 plies longer (54.5 vs 52.8); 16 471 draws | **95.6 %** / **4.3 %** (and one 2–2 with five full, 0.01 %); lead changed hands **64.3 %**; 1.5 plies longer (**54.7 vs 53.2**); 16 369 draws | **HELD [no CI]** (the shape of a draw) | `K1_parent_C2_principles.out`, `K1_parent_principles_deep8e8.json` |
| 27 | mean length **52.8** (median 53, p10 47, p90 59, max 74); **5.08** free moves; **98.5 %** with one | mean **53.2** (median 53, p10 47, p90 **60**, max **76**); **5.02** free moves; **98.4 %** | **MOVED [no CI]** — length climbs again, the free moves stop | `K1_parent_A6_corpus_stats.out` |
| 31a | **100 / 100 / 100** on 689 one-open-board positions (1.1 %) of `probe_data_deep10late_e4.npz` | **100 / 100 / 100** on the 689 of `probe_data_deep10late_e8.npz` — the same 60 000 source positions | **HELD [no CI]** (at the ceiling) | `K1_parent_C5_tablebase_grade.out` |
| 32 | raw fails on **61 of 6001 (1.0 %)**, search **2 (0.03 %)**; motifs 32 > 26 > 23 > 21 > 15 > 3 > 0 (tiebreak > draw-hold > free move given > denying > local win > macro win > closing); local tactics 25 % | raw **52 (0.9 %)**, search **1 (0.02 %)**; motifs **37 > 29 > 28 > 16 > 12**, `macro_win` and `closes_board` **absent**; local tactics **31 %**; the same 6 001 candidates from the same 3 076 games | **HELD [no CI]** on the rate and the head of the order; **the tail reordered again** | `K1_parent_A7_puzzles.out`, `suites/puzzles_v4_dev.json` |
| 33 (agent) | **24.6 %** (0.24597); by ply 2.2 / 26.5 / 50.6 / 66.5 % | **24.6 %** (0.24606); by ply **2.2 / 25.6 / 51.4 / 67.3 %**; random legal move 35.7 %, identical | **HELD [no CI]** | `K1_parent_principles_deep8e8.json` |
| 33 (solver) | **70.2 %** — 0.7021498643289501 on 4 791 solved positions, deep8_300's number to ten digits | **70.2 %** — the identical 0.7021498643289501 on the same 4 791: a third replication of the position set, not of strength | **HELD [no CI]** | same |
| 34 | **0.0 %** of its 4 791 | **0.0 %** of the same 4 791 | **HELD [no CI]** | same |
| 35 (regression) | opponent owns the centre: search **+0.032 ± 0.044**, raw head **−0.060 ± 0.046** | search **+0.0395 ± 0.0443**, raw head **−0.0490 ± 0.0475** — a null on both | **HELD [CI]** | `K1_parent_B3_value_decomp.out` |
| 35 (counterfactual) | *not read* — deep10: centre premium **+0.111** over a corner | **+0.096** over a corner (corner − edge +0.106), still matching the line count 4 / 3 / 2 | **HELD [no CI]** — first reading since deep10 | `K1_parent_B4b_probe_value.out` |
| 36 | random-init control **98.5–100 %** | **98.5–99.6 %** (free move 98.5, target board 99.5, count margin 99.5, open boards 99.4, empties 99.2, status 99.6) | **HELD [no CI]** | `K1_parent_B2_probe_report.out` |
| 37 | dead boards **+0.53 @block 4, by 140**; exact value **+27 @block 8, by 140**; best move **+14 @block 8, by 160**; threats +0.16 / +0.14 @block 6, by 40–100; local win +11 @block 5, by 10; opp. threat +5 @block 7, by 60; result +5 @block 8, by 220 | dead boards **+0.60 @block 3, by 220**; exact value **+29 @block 8, by 140**; best move **+14 @block 8, by 240**; threats **+0.14 / +0.15 @block 6, by 20–100**; local win **+11 @block 5, by 10**; opp. threat **+6 @block 6, by 40**; result **+6 @block 8, by 240** | **HELD [no CI]** (the gains and the layer ordering, a fifth net); **MOVED** (the learned-by column, later again on three concepts) | `K1_parent_B2_probe_report.out` |
| 38 | exact value steps **0.901 → 0.917** across checkpoints 200 → 220; local win by 10; nothing new after 240 | steps **0.913 → 0.931**; local win by **10**; nothing new after 240 (0.926 / 0.941 / 0.936 / 0.939 at 240 / 260 / 280 / 300) | **HELD [no CI]** | `K1_parent_B2_probe_fit.out`, `K1_parent_B2_probe_report.out` |
| 39 | move two plies on **44.8 % vs 37.8 %** control; current move **72.8 vs 58.7** (+7 against +14) | **44.9 % vs 38.6 %**; current move **71.8 vs 57.9** (**+6.3** against **+13.9**) | **HELD [no CI]** | `K1_parent_B2_probe_report.out` |
| 40 | **51.8 %** overall (majority 39.3, local 48.0, trained-trunk 51.7, random-trunk 49.8); 57.7 vs 49.7 / 52.9 at 32–43; **70.8 vs 51.1 / 53.6 / 65.9** at 44+ | **52.0 %** overall (39.3 / 48.0 / 51.6 / 49.8); **58.6** vs 49.7 / 52.9 at 32–43; **71.2 vs 51.1 / 53.6 / 66.7** at 44+ — the same 73 749 open boards | **HELD [no CI]** (the profile, a fourth time) | `K1_parent_E9_ownership_grade.out` |

## Tally

**37 claims re-read: 27 held, 9 moved, 1 unresolved, 0 reversed.**

- **HELD (27)** — 1, 4, 7, 7a, 8, 9, 10, 11, 13, 14, 16, 17, 18, 19, 21, 23, 24, 26, 31a, 32, 33, 34, 35, 36, 38, 39, 40.
- **MOVED (9)** — 2, 3, 5, 12, 20, 22, 25, 27, 37.
- **UNRESOLVED (1)** — 15 (the regressions; its counterfactual half held).
- **REVERSED (0).**

**[CI] 7, [no CI] 30.** Seven verdicts rest on an interval the `_e4` reading actually carries — 8, 9,
13, 14, 16, 19 and 35's regression half. The other thirty rest on a repeated rank (1, 2, 7a, 21, 33
solver), sign (11, 17), share (24, 25, 26, 27, 31a, 32, 33 agent, 34) or profile (4, 5, 7, 10, 20,
22, 23, 36, 37, 38, 39, 40; 3 is a point value on a ladder, 12, 15 and 18 are means with a printed
spread and no interval), and are marked **[no CI]** wherever they appear.

Three claims have a reading for the first time since deep10, because `tools/probe_value.py` was added
to the pass (J1's cheap re-read): **12, 18** and **35's counterfactual half**; **15's** counterfactual
half likewise. `38a` is now the only game claim with no reading above deep10.

## What moved, one sentence each

- **2** — the ordering claim is stronger and the τ claim weaker: `_e8` keeps [40] > [36] > [0] > [37]
  at 1k, 4k **and** 16k, where deep8_300 and `_e4` swapped [0] and [37] at the two lower budgets, but
  its τ against v2b@16k is 0.9238, back up from `_e4`'s 0.8476 — so "the ordering sits further from
  the weak net's at every step" is not a trend, and `_e4` is the low point of a 0.85–0.96 band.
- **3** — X's edge after [40] at 16k rises a fifth time, +0.495 → **+0.524**, with the gap to [36]
  still ≈ 0.10 (+0.095) and the sequence still not monotone.
- **5** — the sharp openings and their best replies are unchanged, but three of the four gaps narrow
  back toward deep10's ([13] 0.142 → 0.109, [4] 0.090 → 0.041, [2] 0.073 → **0.017**), so
  "grew with strength on every net" no longer describes the ladder; after [2] the self-send [20] is
  still the best reply but is a near-tie again.
- **12** — read for the first time since deep10: the tensor edit grants **+0.467** where the natural
  positions give +0.196, so the overstatement is **2.4×** against deep10's 2.1× — the upper-bound
  reading survives, "the overstatement itself is stable" is what moves.
- **20** — the medians are exactly `_e4`'s (36 on the v2a games, 34 on strong play), but the first
  quartile falls 27 → 22 and 25 → **11** and the settled-by-ply-28 share rises 30 → 33 %, all of it
  driven by the ply-0 count.
- **22** — that driver: `_e8` rates the opening **+0.33** for X (deep10 "above +0.33", `_e4` +0.31)
  and counts **24–25 %** of games as settled from ply 0 against `_e4`'s 21–22 %.
- **25** — the count rule still decides about a third of games (**32.3 %**), but the by-count share
  falls **16.5 → 15.7 %** with the equal-count share unchanged at 16.6, so the +6-point rise over the
  last 120 Elo does not extend to the next 40; 0.8 points is resolved on ≈ 98 k games (Wilson ± 0.3).
- **27** — games lengthen again (52.8 → **53.2** plies, max 74 → 76) but free moves per game stop at
  **5.02** against `_e4`'s 5.08, so "both still climbing, the free moves fastest" is `_e4`'s step, not
  this one.
- **37** — the grid repeats a fifth time with the same layers and gains within a few points (dead
  boards +0.53 → **+0.60** the exception), but the *learned-by* column moves **later** again on three
  concepts (dead boards 140 → 220, the best move 160 → 240, the game result 220 → 240), so `_e4`'s
  "20–50 iterations earlier on every concept but the last" is a property of that net, not of strength.

## Nothing reversed — and what that means for 7

`_e4`'s single reversal is **confirmed and deepened**: after [40] the corner reply orbit 36 now
carries **0.943** of the root's visits (`_e4` 0.709, deep10 0.246, deep8_300 0.458), it is the best
reply orbit at 1k, 4k and 16k, and the **edge** subtree is still the one rated better for X
(+0.017 here, +0.022 on `_e4`, against the corner's +0.016 on both earlier nets). Two nets 40 Elo
apart now agree on the corner; the near-tie in value is unchanged at ≈ 0.02 on every net measured.
For PLAN7 §5 item 2 this fixes the count-rule baseline the draw net's [40] reply is read against: a
0.94 / 0.06 visit split on the corner orbit at 16 384 sims, with the 0.02 tie tolerance applying to
that share.

Three further orderings changed below the level any claim's first sentence states, recorded in the
claims they belong to and not counted as reversals (M0 row 6's rule): **32**'s motif tail (denying a
free move 21 → 12 drops below a local win 15 → 16, and `macro_win` 3 → 0 disappears, as `closes_board`
did between deep10 and `_e4`); **15**'s B3 ordering (corner > edge becomes edge ≈ corner, 0.0001
apart — which is the claim's own point); and **18**'s three board classes (the centre's +0.017 falls
to +0.002 and the corner is now the largest of the three near-nulls, at +0.016).
