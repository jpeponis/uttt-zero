# Run dev1 — results and lessons learned

First end-to-end AlphaZero-style run on this machine, 2026-08-29.
Configuration: `runs/dev1/config.json` — 6×64 ResNet (0.53 M params), Gumbel
AlphaZero, 32 simulations/move (m = 16), 4096 lock-step games per iteration,
200 iterations, replay buffer 2 M positions (≈ 10 iterations), SGD lr 0.02
constant, batch 1024, ~1 pass over new positions per iteration, evaluation
every 10 iterations. Figure: `runs/dev1/curves.png`.

## 1. Numbers

| | |
|---|---|
| Games / positions generated | 819,200 / 40.9 M |
| Wall-clock | ~12.1 h: self-play **8.06 h**, training 0.33 h, **evaluation 4.18 h** |
| Self-play throughput | 25–33 games/s (~2.3 min per iteration; slower when another launch-bound process ran on the other GPU) |
| GPU utilisation during self-play | 20–35 % (launch-bound, see NOTES-v2 §1) |

Windowed training statistics (means over the iteration window):

| iters | X win | O win | draw | end: line | end: count | end: equal | length | policy loss | value loss | value acc | policy acc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0–10 | .518 | .434 | .048 | .854 | .098 | .048 | 50.6 | 2.03 | .816 | .548 | .246 |
| 10–30 | .551 | .376 | .074 | .796 | .130 | .074 | 50.2 | 1.68 | .827 | .585 | .397 |
| 30–60 | .583 | .320 | .097 | .753 | .150 | .096 | 50.6 | 1.24 | .835 | .615 | .592 |
| 60–100 | .587 | .309 | .103 | .743 | .154 | .103 | 50.1 | 0.88 | .830 | .623 | .704 |
| 100–150 | .596 | .304 | .100 | .748 | .152 | .100 | 49.7 | 0.86 | .817 | .633 | .712 |
| 150–200 | .595 | .298 | .107 | .745 | .148 | .107 | 49.6 | 0.79 | .820 | .633 | .737 |

Strength ladder — each checkpoint vs `net_0150`, 512 games at 64 sims, 2 random
opening plies (`runs/dev1/ladder.json`):

| ckpt | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 | 110 | 120 | 130 | 140 | 150 | 160 | 170 | 180 | 190 | 200 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| score % | 4.0 | 15.5 | 28.7 | 35.9 | 37.0 | 42.1 | 44.5 | 43.8 | 44.4 | 35.5 | 49.0 | 49.8 | 49.0 | 50.8 | 51.5* | 51.8 | 51.4 | 50.9 | 45.9 | 53.7 |

(* `net_0150` vs itself = 51.5 %, i.e. the noise level of a 512-game match is about ±2 points.)

Search scaling (`runs/dev1/eval_extra.out`, v2 graph-mode search): `net_0200` at **256 sims beats itself
at 64 sims 81.4 %** (+199 =19 −38 over 256 games, 2 random opening plies) — the net is nowhere near
search-saturated; each 4× in simulations is worth roughly +250 Elo at this level. In that match X won
49 %, O 43 %, 7 % draws, 13 % of games decided by the board count.

Strong-play statistics — `net_0200` vs itself at 256 sims, 2 random opening plies, 512 games: **X 51.4 %,
O 35.9 %, draws 12.7 %**; games ended by macro line 70.7 %, by board count 16.6 %, equal count 12.7 %; mean
length 51.5. So at this strength roughly **three games in ten are settled by the tiebreak rule** (count or
equal), up from 15 % under near-random play.

Deterministic 256-sim self-play from the empty board (no noise, no random plies) is a single game line: it
ends in an **O win by macro line at move 56**, although the net values the empty board at +0.29 for X. One
line is anecdotal, but it is a clean example of the value head and the agent's own deep-search play
disagreeing — the kind of position "surprise mining" (Phase E) should collect systematically.

Plain-UCT anchor (uniform prior, same 64-sim budget): 98 % at iteration 10,
100 % from iteration 40 on — saturated and useless thereafter. Raw policy with
no search beats random 100 % from iteration 20.

## 2. What the run showed

1. **Learning was fast, then flat.** Most of the strength arrived in the first
   60–90 iterations (250–370 k games). From iteration 110 on, every checkpoint
   scores 49–51 % against `net_0150`; iteration 100 was a real regression
   (35.5 %) that the next iterations recovered from. Policy loss kept falling
   (2.0 → 0.79) while the value loss never moved (0.82 ± 0.02) after iteration
   10: the value head hit its noise floor almost immediately.
2. **Root policy collapse.** The final net's prior on the empty board is 99.9 %
   centre-of-centre (move 40). A 4096-simulation PUCT search from the empty
   board spent all 4096 visits on that move. The improved policy under Gumbel
   is a *bounded* improvement on the prior, so once the prior is one-hot the
   target stays one-hot — self-reinforcing. X's targets are one-hot at plies
   0, 2, 4 (entropy 0.003 / 0.012 / 0.089 nats); O's stay diffuse (1.28 / 0.58 /
   0.53).
3. **Opening duplication.** In the last 2 M positions of the buffer: ply 0 = 1
   distinct position × 36,864 copies; ply 4 = 71 distinct; ply 8 = 688; ply 12
   = 2,857; only by ply ~25 are positions mostly unique. Uniform sampling
   therefore trains the net thousands of times per iteration on the same few
   opening positions — the cause of (2), of the value head's early plateau, and
   of wasted compute. It also means the net's values for *non-chosen* openings
   are barely trained, which is fatal for the analysis goal (a first-move
   heatmap needs good values for all 15 orbits).
4. **Not symmetry-consistent.** Raw values of the four symmetric moves in the
   centre-board-edge orbit after the first move: +0.027 / +0.064 / +0.057 /
   +0.031. Over 512 random mid-game positions the value differs between a
   position and its 8-fold symmetry average by 0.044 on average and up to
   0.21 (`tests/test_symmetry_eval.py`). Random per-batch symmetry augmentation
   is not enough; symmetry averaging at inference (`uttt/symmetry.py`, exactly
   equivariant) is needed for any analysis number.
   With averaging, the net's first-move values for X are: centre-of-centre
   +0.25; corner of the centre board +0.06; corner of a corner board +0.07;
   everything else between −0.02 and +0.05. Whether that gap is a property of
   the game or of a net that only ever played 40 is what run v2a (81 distinct
   first moves in self-play) will show.
5. **Game facts that already emerged** (all under self-play with 32 sims, so
   provisional): X wins ~60 %, O ~30 %, draws ~10 %; the raw value of the
   empty board is +0.29 for X; centre-of-centre is the unanimous first move;
   about **25 % of games are decided by the board count or end equal** — the
   tiebreak is far from a footnote, and its share *rose* as play improved
   (from 15 % under near-random play).
6. **Evaluation ate a third of the wall-clock.** Three 512-game matches at 64
   sims every 10 iterations cost ~12 min each time — 4.2 h in total, on the
   same GPU as self-play. And the plain-UCT anchor gave no information after
   iteration 40.
7. **Throughput.** 8 h for 820 k games, at 20–35 % GPU utilisation; the search
   loop is host-bound (45 syncs and ~550 kernel launches per simulation).
   Running a second launch-bound process on the *other* GPU slowed self-play by
   ~20 % — the "evaluate on the 3060 in parallel" plan only pays off after the
   sync fixes.

## 3. Lessons → changes for v2 (in priority order)

1. **Opening diversity is the first problem, not throughput.** Sample X's
   *and* O's moves from the improved policy with a temperature for the first
   ~8 plies (instead of the deterministic Sequential-Halving winner), and/or
   start a fraction of games with random or buffer-sampled openings; add a
   small prior floor at the root (e.g. mix 3 % uniform over legal moves into
   the root logits for search) so a one-hot prior can be overturned by search;
   log target entropy and distinct-position counts per ply every iteration.
2. **Deduplicate / down-weight repeated positions** in the buffer (average
   targets over identical positions, or sample with weight 1/√count). Removes
   the opening over-training and gives the value head a chance to improve.
3. **Value target**: mix the search value into the target (variance reduction)
   and add the score-margin head; the value loss floor at 0.82 with 63 %
   accuracy is the metric to move.
4. **Learning-rate drops** once the ladder flattens (iteration ~70 here): the
   plateau at constant lr 0.02 plus the iteration-100 regression are the
   textbook signature of a too-high late learning rate.
5. **Progressive simulations** (32 → 64 → 128) after the plateau, so the
   teacher stays ahead of the student.
6. **Evaluation redesign**: fewer, cheaper, more informative — a ladder against
   a *fixed* set of earlier checkpoints run in a separate process only after the
   search is sync-free; drop the UCT anchor; paired openings; symmetry-averaged
   evaluation for analysis.
7. **Throughput work** (NOTES-v2 §1–2) — still worth 3–6×, but it comes after
   1–3 because faster generation of the same over-duplicated data would not
   have helped this run past iteration ~90.
8. **Persist the games** from every iteration; the corpus statistics above had
   to be reconstructed from the buffer, which only holds the last 10 iterations.

## 4. Things I would keep

Gumbel search at 32 sims worked (strong policy after 100 k games), the lock-step
GPU engine and tree were never the correctness problem (no rule bugs surfaced
in 41 M positions), the WDL head plus ownership head trained without
instability, and resuming from `latest.pt` worked.
