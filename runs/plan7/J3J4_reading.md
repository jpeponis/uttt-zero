# J3 and J4, read: the empty board and the exact frontier

*PLAN7 §4 J3 and J4 — the two pre-registered readings of Phase J, in the forms M2 and its rebuttal
round fixed before either ran (§7e M2 rows 3, 4, 7, 15, 16; M2-R R5–R7). Run on the 3060 on
2026-09-13, **02:43–05:05**, once the `_e8` count pass freed it, with K1 training on the 3090 beside
them; script `runs/plan7/J3J4_3060.sh`, combined log `runs/plan7/J3J4.out`, every exit 0. Outputs:
`J3_empty_board_e8.{out,json}`, `J3_empty_board_e4.{out,json}`, `J4_frontier.{out,json}` and
`J4_frontier_positions.npz`. The readings became **KNOWLEDGE 52** (J3) and **53** (J4) and rows 52
and 53 of `docs/paper/01_claims_map.md`. Nothing was re-run to write this file: every number below is
copied from those outputs, or derived from them by an expression written out in §4.*

## 1. What ran

| | J3 | J4 |
|---|---|---|
| tool | `tools/empty_board.py` | `tools/frontier.py` (on `uttt/solver.py`'s `solve_bounded` / `solve_children_bounded`) |
| nets | `deep8_c1_300_e8/net_0300.pt`, `deep8_c1_300_e4/net_0300.pt` | `deep8_c1_300_e8/net_0300.pt` |
| population | the empty board | `_e8`'s own late corpus: 98 581 games, `games_0280.npz`..`games_0299.npz` |
| settings | `--games 2000 --sims 256 --root_sims 16384 --rule count`, `cuda:1` | `--plies 40 70 --per_ply 500 --max_nodes 1e8 --sims 256 --processes 8 --rule count`, `cuda:1` |
| wall | 60 min (`_e8`) + 50 min (`_e4`) | 32 min |

J4's wall clock is **a sixth of the ≈ 3.5 h the design estimated** (`J3J4_design_notes.md`, "≈ 6.5
min/ply"). The estimate was right where the budget binds — ply 40 took 386.9 s, ≈ 6.4 min — and far
over everywhere else, because it assumed every position spends the full 10⁸ nodes and only the
incomplete ones do. Aggregate throughput was 8.81 × 10⁷ nodes/s over 8 processes (1.10 × 10⁷ per
process) against the design's measured 1.6 × 10⁷ per process, the shortfall being K1's twelve
exact-label workers on the same 24 cores.

## 2. J3 — the numbers as read

### (a) The root, at 16 384 sims, symmetry-averaged, PUCT

| net | value for X | principal line |
|---|---|---|
| `_e8` | **+0.5242** (0.524246) | **[40, 36, 0, 8, 80, 77, 50, 48, 34, 66]** |
| `_e4` | **+0.4950** (0.495007) | **[40, 36, 0, 8, 80, 77, 48, 30, 32, 46]** |

Search-relative: what this net prefers at this budget, not a game-theoretic value. The arm reuses
`tools/atlas.py deep_values` (PUCT, `c_puct` 1.25, `m_considered` 81, Gumbel scale 0, depth cap 40),
so it is **a different search from arms (b) and (c)** — theirs is the trained Gumbel mode at depth cap
24 — and a separate measurement, never a matched-budget comparator for them (M2 row 15).

**It is not a new number.** `runs/plan7/K1_parent_A1_atlas.out:24` gives [40] **+0.524** on `_e8` and
`runs/plan6/I1_A1_atlas.out:24` gives **+0.495** on `_e4`; the atlas's PV after [40] is
`[36, 0, 8, 80, 77, 50, 48, 34, 66, 33]` on `_e8` and `[36, 0, 8, 80, 77, 48, 30, 32, 46, 10]` on
`_e4` — J3's line with [40] prepended and the tenth move dropped (`atlas`'s `max_len = 10`). J3 (a)
re-reads KNOWLEDGE 3's `_e8` and `_e4` numbers and writes their lines out. It is not a sixth point on
that chain and row 3's drift cell does not move.

### (b) and (c), 2 000 games each at 256 sims, plain evaluator, depth cap 24

| | `_e8` (b) | `_e8` (c) | `_e4` (b) | `_e4` (c) |
|---|---|---|---|---|
| X | **99.7 % [99.3, 99.9]** (1994) | **70.9 % [68.8, 72.8]** (1417) | **99.9 % [99.6, 100.0]** (1998) | **69.8 % [67.7, 71.7]** (1395) |
| O | 0.1 % [0.0, 0.4] (2) | 12.6 % [11.2, 14.1] (252) | 0.0 % [0.0, 0.2] (0) | 13.5 % [12.1, 15.1] (270) |
| draw | 0.2 % [0.1, 0.5] (4) | 16.6 % [15.0, 18.2] (331) | 0.1 % [0.0, 0.4] (2) | 16.8 % [15.2, 18.4] (335) |
| mean length | 54.0 (sd 0.29) | 53.3 (sd 4.94) | 51.0 (sd 0.30) | 54.0 (sd 4.95) |
| ends line / count / equal | 0.2 / **99.6** / 0.2 % | 65.0 / 18.5 / 16.6 % | **99.9** / 0.0 / 0.1 % | 65.6 / 17.6 / 16.8 % |
| distinct games | **9** | 1 716 | **7** | 1 683 |
| distinct 4-ply openings (canonical) | **9 (9)** | 299 (219) | **7 (7)** | 300 (209) |
| seconds | 1 671 | 1 887 | 1 635 | 1 278 |

Arm (b): the search policy sampled proportionally for the first 4 plies, **both** floors off
(`sample_uniform` 0, `root_prior_floor` 0), Gumbel scale 0. Arm (c): `sample_moves` 8, temperature
1.0, `sample_uniform` 0.15, `root_prior_floor` 0.03, Gumbel scale 1.0 — `MCTSConfig`'s default, which
neither run's `config.json` records, so both trained at it. Both arms play with the **plain**
`FusedEvaluator`, the agent that generated each run's corpus (M2 row 15); only (a) is symmetry-
averaged.

**The intervals are the policy's and the concentration sits beside them, uncorrected** (M2 row 3).
The 2 000 games are independent draws from a specified stochastic policy; identical games are
duplicate *outcomes* of independent draws, not dependent draws, so the Wilson interval is the correct
95 % interval for that policy's outcome distribution. What (b) therefore is: an accurate, narrow
estimate of a very concentrated policy. What (b) is **not**: opening coverage. Nine games at 99.7 %
tell you about nine lines; 2 000 unanimous draws would put the Wilson lower bound at
1 − z²/(n + z²) = **99.81 %** whatever the game is like (M2-R R7). The end-reason and mean-length
rows of arm (b) are properties of those nine (seven) lines and are not population statistics — note
that `_e8`'s near-greedy line ends **on the board count** (99.6 %) and `_e4`'s **on a macro line**
(99.9 %), two different games, not a drift.

### (b) − (c): the exploration package at a matched budget

| | X | O | draw |
|---|---|---|---|
| `_e8` | **+28.9** | −12.5 | −16.4 |
| `_e4` | **+30.2** | −13.5 | −16.7 |

Four knobs move together and **nothing is attributed to any one of them**: sampled plies 4 vs 8,
sampling floor 0 vs 0.15, root prior floor 0 vs 0.03, Gumbel scale 0 vs 1. The budget is matched (256
sims both arms) and the depth cap is matched (24 both arms). Neither arm is play as trained: the
trained budget is 32 → 48 → 64 and the trained depth cap is 12.

### The two first-move statistics (M2 row 7)

They measure different things and neither substitutes for the other:

- **raw policy** — the checkpoint's first-move probability on the empty board, `timeline.json`'s
  `first_top_share` = `probs.max()` (`tools/timeline.py:129–130`);
- **generated games** — the share of that iteration's self-play games whose first move was the modal
  one, `log.jsonl`'s `first_move_top_share`. The tool pairs timeline row *iter* with log row
  *iter − 1*, because `train2.py:397–399` writes `net_{it+1:04d}.pt`.

| iteration | `_e8` raw | `_e8` generated | `_e4` raw | `_e4` generated |
|---|---|---|---|---|
| 10 | [44] 0.215 | [42] 0.528 | [58] 0.050 | [80] 0.121 |
| 160 | [40] 0.976 | [40] 0.832 | [40] 0.928 | [40] 0.839 |
| 300 | [40] **0.982** | [40] **0.835** | [40] **0.990** | [40] **0.841** |

## 3. J4 — the numbers as read

Coverage is **complete legal-action value coverage within the budget**: the exact value of the
position *and of every legal child* obtained inside one shared budget of 10⁸ counted nodes. That is
stricter than proving the root's value — a cutoff can settle the root without valuing the other
children — and it is what grading a chosen move against its alternatives needs (M2 row 16). Coverage
is conditional on games alive at the ply (`length > ply`); nodes, the optimal-move rate and regret are
conditional on complete. Both proportions carry 95 % Wilson intervals; mean regret keeps the cluster
bootstrap and prints none where the sample is degenerate (M2 row 4).

| ply | alive | sampled | coverage | n | nodes med | nodes p90 | optimal % | non-optimal |
|---|---|---|---|---|---|---|---|---|
| 40 | 98 181 | 500 | **28.2 % [24.4, 32.3]** | 141 | 5 566 524 | 56 056 556 | 100.0 [97.3, 100.0] | 0 |
| 41 | 97 542 | 500 | 40.0 % [35.8, 44.4] | 200 | 1 510 568 | 61 635 210 | 100.0 [98.1, 100.0] | 0 |
| 42 | 97 285 | 500 | **50.0 % [45.6, 54.4]** | 250 | 2 503 148 | 46 821 695 | 100.0 [98.5, 100.0] | 0 |
| 43 | 95 768 | 500 | 62.8 % [58.5, 66.9] | 314 | 975 176 | 40 170 969 | 100.0 [98.8, 100.0] | 0 |
| 44 | 95 087 | 500 | **76.4 % [72.5, 79.9]** | 382 | 745 648 | 43 471 984 | **99.7 [98.5, 100.0]** | 1 |
| 45 | 91 724 | 500 | 82.6 % [79.0, 85.7] | 413 | 86 447 | 16 683 217 | 99.8 [98.6, 100.0] | 1 |
| 46 | 90 214 | 500 | **87.6 % [84.4, 90.2]** | 438 | 110 395 | 21 061 661 | 99.8 [98.7, 100.0] | 1 |
| 47 | 84 501 | 500 | 93.6 % [91.1, 95.4] | 468 | 31 347 | 14 603 043 | 99.8 [98.8, 100.0] | 1 |
| 48 | 82 079 | 500 | **94.8 % [92.5, 96.4]** | 474 | 16 134 | 4 853 800 | **99.8 [98.8, 100.0]** | 1 |
| 49 | 74 259 | 500 | 98.0 % [96.4, 98.9] | 490 | 3 796 | 1 574 209 | 99.8 [98.9, 100.0] | 1 |
| 50 | 70 386 | 500 | **99.0 % [97.7, 99.6]** | 495 | 2 457 | 1 060 232 | 100.0 [99.2, 100.0] | 0 |
| 51 | 60 700 | 500 | 99.6 % [98.6, 99.9] | 498 | 563 | 368 902 | 99.8 [98.9, 100.0] | 1 |
| 52 | 55 956 | 500 | **100.0 % [99.2, 100.0]** | 500 | 583 | 218 452 | **99.8 [98.9, 100.0]** | 1 |
| 53 | 46 034 | 500 | 100.0 % [99.2, 100.0] | 500 | 226 | 42 739 | 100.0 [99.2, 100.0] | 0 |
| 54 | 40 577 | 500 | 100.0 % [99.2, 100.0] | 500 | 122 | 69 008 | 100.0 [99.2, 100.0] | 0 |
| 55 | 31 545 | 500 | 100.0 % [99.2, 100.0] | 500 | 48 | 7 198 | 100.0 [99.2, 100.0] | 0 |
| 56 | 26 515 | 500 | 100.0 % [99.2, 100.0] | 500 | 38 | 4 320 | 100.0 [99.2, 100.0] | 0 |
| 57 | 19 352 | 500 | 100.0 % [99.2, 100.0] | 500 | 13 | 2 192 | 100.0 [99.2, 100.0] | 0 |
| 58 | 15 358 | 500 | 100.0 % [99.2, 100.0] | 500 | 20 | 1 812 | 100.0 [99.2, 100.0] | 0 |
| 59 | 10 473 | 500 | 100.0 % [99.2, 100.0] | 500 | 12 | 572 | 100.0 [99.2, 100.0] | 0 |
| 60 | 7 850 | 500 | **100.0 % [99.2, 100.0]** | 500 | **14** | **442** | 100.0 [99.2, 100.0] | 0 |
| 61 | 5 119 | 500 | 100.0 % [99.2, 100.0] | 500 | 8 | 233 | 100.0 [99.2, 100.0] | 0 |
| 62 | 3 640 | 500 | 100.0 % [99.2, 100.0] | 500 | 6 | 245 | 100.0 [99.2, 100.0] | 0 |
| 63 | 2 266 | 500 | 100.0 % [99.2, 100.0] | 500 | 4 | 113 | 100.0 [99.2, 100.0] | 0 |
| 64 | 1 505 | 500 | 100.0 % [99.2, 100.0] | 500 | 3 | 91 | 100.0 [99.2, 100.0] | 0 |
| 65 | 810 | 500 | 100.0 % [99.2, 100.0] | 500 | 2 | 57 | 100.0 [99.2, 100.0] | 0 |
| 66 | 492 | **492** | 100.0 % [99.2, 100.0] † | 492 | 2 | 52 | 100.0 [99.2, 100.0] | 0 |
| 67 | 253 | **253** | 100.0 % [98.5, 100.0] † | 253 | 2 | 30 | 100.0 [98.5, 100.0] | 0 |
| 68 | 142 | **142** | 100.0 % [97.4, 100.0] † | 142 | 3 | 27 | 100.0 [97.4, 100.0] | 0 |
| 69 | 73 | **73** | 100.0 % [95.0, 100.0] † | 73 | 2 | 13 | 100.0 [95.0, 100.0] | 0 |
| 70 | 50 | **50** | 100.0 % [92.9, 100.0] † | 50 | 2 | 13 | 100.0 [92.9, 100.0] | 0 |

**†** the whole alive set was measured (`positions_sampled == games_alive_at_ply`), so the coverage
figure is a **census** of this corpus at that ply and carries no sampling error with respect to it;
the Wilson interval beside it belongs to the wider population of games this checkpoint's self-play
could generate. Read as one or as the other, never as both — no finite-population *correction* is
applied, because applying one would assert that this corpus's alive set is the target population.

Totals: **14 010** positions sampled, **12 573** covered, 1 437 incomplete; 1.71 × 10¹¹ counted nodes;
1 945 s of per-ply wall time.

## 4. The derivations

### 4a. The eight non-optimal moves, from the per-position table

The aggregates print a rate, not a count. The count comes from `J4_frontier_positions.npz`, whose
rows are one per sampled position, complete or not:

```python
import numpy as np, collections
z = np.load("runs/plan7/J4_frontier_positions.npz", allow_pickle=True)
nonopt = z["complete"] & (z["optimal"] == 0)
int(nonopt.sum())                                     # -> 8
dict(collections.Counter(z["ply"][nonopt].tolist()))  # -> {44:1, 45:1, 46:1, 47:1, 48:1, 49:1, 51:1, 52:1}
dict(collections.Counter(z["optimal"][z["complete"]].tolist()))   # -> {1: 12565, 0: 8}
```

Incomplete rows carry the sentinels `move = -1`, `optimal = -1`, `regret = NaN`, so the
`complete & (optimal == 0)` conjunction is what isolates a graded, non-optimal move; `optimal` is
never `-1` on a complete row, and 12 565 + 8 = 12 573 closes against the sum of `n_complete` over the
31 plies.

The eight rows in full. `exact_root_value` and `child_values` are exact game values in {−1, 0, +1} for
the side to move, so a **regret of 1** is one step (a win played into a draw, or a draw into a loss)
and **2** is a win played into a loss; `regret == exact_root_value − child_values[move]` holds on
every complete row by construction and the tool asserts it.

| ply | game_id | empties | nodes | root | move | regret | what it cost |
|---|---|---|---|---|---|---|---|
| 44 | 3 150 456 | 24 | 26 022 737 | 0 | 37 | 1 | draw → loss |
| 45 | 7 344 827 | 24 | 6 598 584 | 0 | 9 | 1 | draw → loss |
| 46 | 3 701 | 30 | 14 877 607 | 0 | 17 | 1 | draw → loss |
| 47 | 8 392 249 | 25 | 5 039 923 | +1 | 5 | 1 | win → draw |
| 48 | 6 294 439 | 22 | 1 407 561 | +1 | 42 | **2** | win → loss |
| 49 | 10 490 626 | 13 | 165 027 | 0 | 71 | 1 | draw → loss |
| 51 | 13 633 865 | 25 | 33 676 437 | +1 | 43 | 1 | win → draw |
| 52 | 16 778 337 | 14 | 82 357 | +1 | 25 | 1 | win → draw |

Four turned a drawn root into a lost one, three a won root into a drawn one, one a won root into a
lost one. They cross-check against the printed mean regrets exactly: ply 44 is 1 / 382 = 0.00262 →
**0.003**; ply 48 is 2 / 474 = 0.00422 → **0.004**; every other non-zero ply is 1 / n → 0.002. And
each ply's printed optimal % is `(n_complete − non-optimal) / n_complete`: 381/382 = 99.74, 473/474 =
99.79, 499/500 = 99.80.

The eight fall at eight of the nine plies from 44 to 52 (all but 50), with none below 44 or above 52.
That is **not** evidence that the agent is perfect outside that band. Plies 40–43 have only 141, 200,
250 and 314 covered positions, so at the ≈ 0.2 % rate seen at 44–52 the expected number of errors
there is 0.3–0.6 and observing none is unremarkable; plies 53–70 are the run's shallowest positions.
The Wilson intervals are the statement; the count is what they are computed from.

### 4b. Recurrence across plies

```python
gid = z["game_id"]; recur = collections.Counter(gid.tolist())
len(set(gid.tolist()))                              # -> 11 172 distinct games over 14 010 rows
sum(1 for v in recur.values() if v > 1)             # -> 1 727 games appear at more than one ply
max(recur.values())                                 # -> 10 plies for one game
```

Within a ply each game contributes at most one position, so the cluster bootstrap degenerates and
Wilson applies directly to the two proportions. **Across** plies the same game recurs, so the rows of
the table above are not independent of one another and any across-ply comparison — a difference
between plies, a fitted curve, a joint interval — needs game-linked resampling over the per-position
table, which carries `game_id` for exactly that (M2 row 16).

### 4c. (b) − (c), and the two node conventions

(b) − (c) is a difference of two shares measured on the same 2 000-game budget: 99.70 − 70.85 =
**+28.85** on `_e8` and 99.90 − 69.75 = **+30.15** on `_e4` for X, and likewise for O and draws. No
interval is quoted on the difference: the two arms are independent samples from two policies, and the
package is four knobs at once, so the difference is reported as a magnitude and attributed to the
package, not to a knob.

A **node** in J4 is one recursive entry of the budgeted kernel `uttt.solver._negamax_bounded`. A child
that is already terminal after the move is decided directly in `solve_children_bounded`
(`uttt/solver.py:255–263`) and costs **zero** counted nodes — visible at plies 65–70, where the median
is 2. The budget therefore bounds **search work, not wall time**, and the median-node column is not a
timing.

### 4d. Why the generated-games share stops at ≈ 0.84

Arithmetic, offered as a consistency check and not as a measurement. Arm (c)'s and self-play's
sampling floor is `sample_uniform = 0.15` spread over the 81 legal first moves, so the modal move's
share of generated first moves is at most `0.85 · p + 0.15/81` for a search policy of modal mass `p`.
At `_e8`'s iteration-300 raw probability p = 0.982 that is 0.835 + 0.002 = **0.837**, against the
**0.835** the log records. The ceiling on the generated share is the floor, not the policy — which is
why the raw statistic reaching 0.982 and the generated one sitting at 0.835 is not a contradiction
(M2 row 7), and it assumes the search policy is as concentrated as the raw head, which was not
measured.

## 5. The comparison with claim 24, written out

KNOWLEDGE **24** on `_e8`: **X 63.2 % / O 20.2 % / draw 16.6 %** over that net's own **98 581** games
(`runs/plan7/K1_parent_A6_corpus_stats.out:2`), generated during iterations 280–299 at the trained
budget (32 sims, schedule `60:48,100:64` → 64 by then), depth cap 12, under the as-trained exploration
settings, by the *changing* policies of those twenty iterations.

J3 arm **(c)** on `_e8`: **X 70.9 % [68.8, 72.8] / O 12.6 % [11.2, 14.1] / draw 16.6 % [15.0, 18.2]**
over 2 000 games at 256 sims, depth cap 24, under the same exploration settings, by the **final
checkpoint alone**.

| | claim 24 (corpus) | J3 (c) | difference |
|---|---|---|---|
| X | 63.2 % | 70.9 % | **+7.7** |
| O | 20.2 % | 12.6 % | **−7.6** |
| draw | 16.6 % | 16.55 % | **−0.05** |

**This is a comparison and not a test.** Three things differ at once and none of them can be held
fixed after the fact:

1. **budget** — 256 sims against 32 → 64, a 4–8× increase;
2. **depth cap** — 24 against 12;
3. **the policy's identity** — 24 is a statistic of an exploratory, *changing* training policy over
   twenty iterations, (c) of one frozen checkpoint. A disagreement would therefore not refute 24
   (PLAN7 §4 J3, as amended; M2-R R7).

What is worth recording anyway: the whole movement is between the **X and O columns**, and the draw
share does not move at all. 24's 16.6 sits inside (c)'s [15.0, 18.2], and (c)'s 16.55 rounds to the
same 16.6 — a coincidence to one decimal place on two populations that differ in budget, depth cap and
policy. Arm (b), at 0.2 % drawn, shows that this is not a property the draw share keeps once the
exploration package is removed; the stability is of the *explored* distribution, at two budgets.

The `_e4` pair for reference: claim 24 has X 62.7 / O 20.7 / draw 16.6 over 99 346 games; J3 (c) reads
69.8 / 13.5 / 16.8. The same shape — X up ≈ 7, O down ≈ 7, draws flat — on the second net.

## 6. What these two readings do not say

- **Not** that the empty board's value is +0.52. It is what one net prefers at 16 384 simulations of
  one search; the claim is search-relative and the number is 3's, re-read.
- **Not** that X wins 99.7 % of well-played games. Arm (b) is nine lines, and the interval is that
  concentrated policy's, not the opening's. Arm (b) provides **no opening coverage**.
- **Not** that the exploration package costs X 29 points. It is four knobs at one budget on one
  checkpoint, and (b) − (c) is attributed to the package, never to a knob.
- **Not** that claim 24 is confirmed or contradicted. See §5.
- **Not** that the endgame is solved from ply 52, or from any ply. The coverage column is a fraction
  of *sampled positions from games alive at that ply* completing inside a *stated budget*; the covered
  subset is the easy end of each ply and gets easier as the budget binds, so ply 40's 100 % optimal is
  a rate on the cheapest 28 % of ply 40 and not on ply 40. **No monotonicity between plies is claimed,
  there is no frontier, and "solved from ply N" follows from none of it** — the 100 % rows included.
- **Not** that the 8 non-optimal moves are all the agent's errors in this corpus. They are its errors
  on 12 573 *covered* positions at 256 simulations; the 1 437 uncovered ones were never graded, and
  they are the hard ones.
