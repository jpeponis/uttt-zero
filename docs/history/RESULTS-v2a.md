# Run v2a — results

Second run, 2026-08-29, with the v2 pipeline (NOTES-v2 §8). Same net as dev1
(6×64, 0.53 M params), Gumbel search at 32 sims, continuous self-play of 4096
parallel games × 64 moves per iteration, 150 iterations, replay 2 M positions with
duplicate down-weighting (count^-0.5), early moves sampled from the improved
policy for 8 plies, 3 % root prior floor, margin head, LR 0.02 with ×0.1 drops
at iterations 90 and 130, evaluation vs dev1's final net every 10 iterations.
Iterations 0–9 ran the eager v2 search, 10–150 the CUDA-graph search.
Figure: `runs/v2a/curves.png`; corpus statistics: `runs/v2a/corpus.out`;
final-net analysis: `runs/v2a/analysis.out`.

## 1. Numbers

| | dev1 | v2a |
|---|---|---|
| Games / positions | 819 k / 40.9 M | 789 k / 39.1 M |
| Wall-clock | ~12.1 h | **~2.75 h** (self-play 1.28 h, training 0.35 h, evaluation 1.10 h) |
| Self-play throughput | 25–33 games/s | 155–220 games/s (graph mode) |
| Final value loss / accuracy | 0.82 / 0.636 | **0.77 / 0.656** |
| Buffer distinct positions | ~5 % at ply ≤ 12 | 95 % overall mid-run, 57 % at the end (see §3) |

Score vs dev1 `net_0200` during training (256 games at 64 sims each point, ±3):

```
iter     10   20   30   40   50   60   70   80   90  100  110  120  130  140  150
score   .08  .26  .40  .42  .38  .46  .46  .47  .53  .56  .57  .55  .53  .56  .58
```

v2a passed dev1's final net at iteration ~90 (≈480 k games, ≈1 h of graph-mode
compute) and finished at 0.58, i.e. roughly +55 Elo over a net that had 12 hours.
The LR drop at 90 coincides with the step from 0.47 to 0.53–0.56; the second
drop at 130 changed nothing measurable — the 6×64 net at 32 sims is near its
ceiling under this recipe.

Final-net matches (`runs/v2a/analysis.out`, graph-mode search, 2 random opening plies):

| match | result (A's view) |
|---|---|
| v2a `net_0150` @64 vs dev1 `net_0200` @64, 1024 games | **60.1 %** (+544 =142 −338) |
| v2a `net_0150` @256 vs dev1 `net_0200` @256, 512 games | **60.2 %** (+283 =50 −179) |
| v2a `net_0150` @256 vs itself @64, 512 games | 80.1 % — still far from search-saturated |
| v2a `net_0150` @256 vs itself @256, 1024 games | X 53.0 %, O 31.2 %, draws 15.7 %; ended by line 65.8 %, by count 18.5 %, equal 15.7 % |

So v2a's net is about +70 Elo over dev1's at both budgets, and under 256-sim play **a third of games
(34 %) are settled by the tiebreak rule**. The deterministic 256-sim main line from the empty board is
now an X win by macro line at move 51 (dev1's main line was an O win at 56) — single lines, anecdotal.

Opening table of the final net (symmetry-averaged; deep = 4096-sim search after the move, X's view):

```
first-move orbit                              raw policy  raw value   deep value
centre of centre board [40]                       94.9 %     +0.22       +0.33
corner of a corner board [0,20,60,80]              0.6 %     +0.15       +0.20
corner of the centre board [36,38,42,44]           0.7 %     +0.11       +0.19
edge of the centre board [37,39,41,43]             1.5 %     +0.10       +0.13
other edge/corner-board cells                    <1 % each  +0.00…+0.09  +0.05…+0.13
centre of a corner board [4,22,58,76]              0.4 %     +0.08       +0.07
centre of an edge board [13,31,49,67]              0.0 %     −0.01       −0.07
```
Empty-board value +0.31 for X. Compared with dev1's net, the *ordering* is the same (40 first, the two
"cell 4" orbits last), but every alternative is valued higher now that the net has actually played
them — the gap between 40 and the best alternative shrank from 0.18 to 0.13. Both nets agree that
opening in the centre of a non-centre board (handing O the centre board) is the worst choice.

## 2. What the corpus says about the game (last 30 iterations, 159 k games, 32-sim self-play with sampled openings)

- **Outcomes**: X 60.0 %, O 28.7 %, draws 11.3 %. Games end by macro line
  74 %, by board count 14 %, equal count 11 % — **one game in four is settled
  by the tiebreak rule**, and that share grew with strength (15 % under random
  play, 25–29 % under strong play in dev1's 256-sim matches).
- **Length**: mean 49.4 plies, p10–p90 = 43–55, longest 72 (of 81 possible).
  On average 7.65 of the 9 local boards are closed when the game ends.
- **First move**: centre-of-centre in 95 % of games (X score 66 %). Among the
  sampled alternatives the ranking is consistent with the deep-search table
  from dev1: corner of an edge board 62 %, corner of the centre board 64 %,
  corner of a corner board 60 % … centre of an edge board **49 %** (worst) and
  centre of a corner board 56 % — the two "cell 4" orbits, which hand O the
  centre board. (Sampled-opening games are noisy; the ordering is the point.)
- **When games are decided**: the mean search value in games X eventually
  wins vs. games O wins is indistinguishable until ply ~24 (+0.26 vs +0.24),
  starts separating at ply 30 (+0.23 vs +0.16), and is decided by ply 42
  (+0.32 vs −0.54). The critical phase is plies 30–45, i.e. when boards start
  closing and free moves appear.
- **Free moves (tempo)**: 3.9 per game at final strength, 95 % of games have
  one. Whoever gets more of them wins: X scores **84 %** when X had more free
  moves, 69 % when equal, **43 %** when O had more. Correlation, not yet
  causation (closing boards both wins material and creates free moves) — the
  counterfactual value probe in Phase E is the way to separate the two.

> **Reviewer caveats (REVIEW-codex.md, 2026-08-29).** (i) The original "distinct positions" sampling in
> `probe_value.py` was wrong (duplicates retained); fixed and rerun — numbers below are from the corrected
> run (`runs/v2a/probe_surprise_rerun.out`) and differ from the first run by ≤ 0.02. (ii) The ownership
> and board-removal probes edit tensors into states that are not reachable by legal play (stone-count
> parity, a FULL board holding X lines, possibly terminal macro lines evaluated as non-terminal); they
> measure the net's response to unreachable inputs, not causal game values. The free-move probe is the
> least affected (a free move is a legal state). Treat §2b as hypothesis generation; the paired-history
> version is in PLAN2.md. (iii) "Decided by ply 42" (§2) is a statement about conditional means, not
> about individual games being settled; "forced loss" in §2c means the 256-sim search's value, not an
> exact result; "3-way accuracy" in §2d thresholds the scalar value at ±0.33, not the WDL argmax.

## 2b. Counterfactual value probes (`tools/probe_value.py`, v2a net, 49 k distinct buffer positions, plies 6–60)

Symmetry-averaged raw values, side-to-move perspective, expected-score units (win = +1):

| probe | mean Δ | p10 / median / p90 | by phase (ply 0–19 / 20–34 / 35+) |
|---|---|---|---|
| given a free move instead of being confined | **+0.27** | +0.06 / +0.20 / +0.56 | +0.17 / +0.19 / +0.44 |
| … with 9 open boards | +0.18 | | |
| … with 5 open boards | +0.43 | | |
| … with 3 open boards | +0.53 | | |
| owning the centre board vs opponent owning it | **+1.03** | +0.09 / +1.03 / +1.89 | – / +1.07 / +1.02 |
| owning a corner board vs opponent owning it | +0.91 | +0.08 / +0.94 / +1.75 | – / +0.87 / +0.92 |
| owning an edge board vs opponent owning it | +0.79 | +0.10 / +0.80 / +1.47 | +0.81 / +0.79 / +0.80 |
| an open centre board removed (drawn) for both | +0.06 | −0.36 / +0.07 / +0.48 | +0.05 / +0.09 / +0.02 |
| an open corner / edge board removed for both | +0.03 / +0.03 | wide | ≈ 0 late |

Reading: a free move is worth a quarter of the draw-to-win distance on average and half of it once
few boards remain; a won board swings the game by about one full point, with the hierarchy centre >
corner > edge in steps of ~0.11; whether an open board disappears matters little on average — what
matters is who would have won it. These are the net's beliefs, not ground truth; the search-scaling
result (256 sims beats 64 sims 80 %) says the beliefs are still coarse, so the numbers will move with
stronger nets.

## 2c. Surprise mining (`tools/surprise.py`, v2a net, 6,969 distinct buffer positions, 256-sim search)

| ply | search move ≠ raw argmax | mean \|search − raw value\| | mean raw p(search move) |
|---|---|---|---|
| 2–9 | 25.7 % | 0.025 | 0.72 |
| 10–19 | 21.5 % | 0.037 | 0.70 |
| 20–29 | 33.9 % | 0.080 | 0.58 |
| 30–39 | **37.5 %** | 0.243 | 0.52 |
| 40–49 | 29.5 % | **0.366** | 0.57 |
| 50–70 | 21.6 % | 0.298 | 0.66 |

The raw net is a good opening player and a poor endgame evaluator: from ply 30 the search overturns
its move choice in a third of positions and its value by 0.25–0.37 on average. The largest surprises
(`runs/v2a/surprise.out`) are late positions where the net's value is +0.8–0.9 for the mover and the
search finds a forced loss (−0.95…−0.99), typically a free move or a forced sequence closing the
last boards. Consequences: (1) an exact endgame solver gives ground truth exactly where it is needed
(NOTES-v2 §5.3); (2) more simulations late in the game buy the most; (3) the value-head loss plateau
is mostly an endgame-tactics floor, not an opening one.

## 2d. Exact endgame test (`uttt/solver.py`, `tools/endgame_accuracy.py`; v2a net, 3,000 distinct buffer positions with 6–16 moves left)

A Numba alpha-beta solver (verified against brute-force minimax) labels positions exactly: 45.9 % are
wins for the mover, 13.7 % draws, 40.4 % losses.

| evaluator | 3-way accuracy | mean \|value error\| | move-error rate |
|---|---|---|---|
| raw net | 0.777 | 0.351 | – |
| raw net, symmetry-averaged | 0.779 | 0.348 | – |
| search, 32 sims (self-play budget) | 0.733 | 0.365 | **1.2 %** |
| search, 64 sims | 0.753 | 0.332 | 0.7 % |
| search, 256 sims | 0.750 | 0.328 | **0.2 %** |

By remaining moves, raw 3-way accuracy falls from 0.85 (6–9 left) to 0.72 (15–16 left); the 256-sim
search's move-error rate is 0.0 % up to 12 moves left and 0.5–0.6 % at 13–16. So the value head is wrong
about the exact result of a near-finished game one time in five, but the search at play-time budgets
almost never throws the exact value away — the strength lives in net + search, and the raw value head's
endgame errors are the obvious place for exact labels as an auxiliary training target (v3 idea).

## 3. What went wrong or is still open

- **Opening diversity collapsed again, more slowly.** Sampling moves from the
  improved policy diversified the first plies early (top first move 2–5 % of
  games until iteration ~20) but the policy sharpened and sampling followed
  it: 72 % by iteration 30, 95 % by 40. The buffer's distinct-position share
  fell from 95 % to 57 % by the end. Alternatives still received hundreds of
  games per iteration (never zero, as in dev1), which is why the orbit table
  above exists at all, but the fix is an explicit exploration floor
  (`--sample_uniform`, implemented for v2b).
- **Plateau at ~0.58 vs dev1** from iteration 100: the 32-sim teacher and/or
  the 6×64 capacity. v2b tests progressive simulations (32 → 48 → 64); a wider
  net is the next experiment after that.
- **Evaluation still cost 1.1 h** because the in-run evaluator used the eager
  search; switched to graph mode for v2b (expected ~10 min).
- Ownership/margin heads train (margin CE 2.19 → 1.61 over 19 bins) but their
  effect on strength is untested — an ablation is cheap now (a run is 2–3 h).

## 4. Keep / change for v2b

Keep: everything in the v2 pipeline. Change: `--sample_uniform 0.15`,
`--sims_schedule 60:48,100:64`, `--lr_drops 100,140`, anchors = dev1 `net_0200`
+ v2a `net_0150`, graph-mode evaluation.
