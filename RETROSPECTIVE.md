# uttt-zero — Retrospective (2026-09-02, at the owner-directed pause)

Four days of work: two building (the PLAN2/PLAN3 era), two scaling the network under
review discipline (the PLAN4 era). This document is the "what did we actually learn"
synthesis the pause was called for. Sources: PLAN2–PLAN4, NOTES-v2, the three reviews,
`runs/*/analysis.out`. Terms are explained where they first appear; PLAN5's glossary has
the full set.

## 1. The arc in six lines

1. **Build** (day 1–2): two game engines cross-checked against each other on 41 M+
   positions; batched Gumbel search (many games searched at once on the GPU); CUDA-graph
   replay (recorded GPU command sequences, replayed to cut launch overhead); continuous
   self-play; a replay buffer held on the GPU. Throughput went from 25 to 220 games/s.
2. **Measure** (day 2): the paired opening suite (516 fixed openings, each played from
   both sides), the exact endgame set (solved positions), the rollout anchor (a fixed
   opponent with no neural net), and seed replicates (the same recipe rerun with another
   random seed). Together these produced the ±3-point rule: believe no result under
   3 percentage points on the full suite. The measurement kit outlived every other
   decision.
3. **Map the recipe** (day 2): ten runs. Two levers were real (c_scale, width); five
   changes were nulls (no measurable effect).
4. **Review** (day 3): two independent model reviews were adjudicated — each finding
   accepted, rejected or deferred with a measured reason. Claims were corrected, probes
   run, operations hardened, git established.
5. **Scale** (day 3–4): depth +23 Elo, duration +127, depth-at-duration +35 — the ladder
   went from v2b to +242 in four runs. (The +35 was re-measured on a second seed on
   2026-09-05 at +9: inside the seed band, §2 addendum.)
6. **Survive** (day 3–4): three GPU driver faults, all in eval-path CUDA graphs. The
   recovery machinery (full-state checkpoints plus automatic retries) turned them from
   run-killers into blips of at most 10 lost iterations.

## 2. Final strength ladder (paired suite vs v2b @64 sims, final checkpoints)

Each row is one training run; each run changed one thing from the row above it ("recipe"
lists the change). Elo is measured on the paired suite against the `v2b` net, both sides
searching 64 simulations per move, using each run's final checkpoint. A difference of
+100 Elo means roughly a 64 % expected score; +242 is about 80 %. The last column is the
net's raw value head (no search) on the exact endgame set: WDL accuracy is the share of
positions where it names the right result, and regret is the average value lost by
playing its preferred move instead of the best one (0 = perfect).

| net | recipe | Elo | endgame raw WDL / regret |
|---|---|---|---|
| dev1 | v1 baseline | −95 | 71.2 / 0.083 |
| v2b | v2 pipeline + floor + sims schedule | 0 | 75.0 / 0.078 |
| abl_cscale1 | + c_scale 1.0 | +40 | 74.6 / 0.077 |
| wide128_c1 | + filters 128 | +77 | 76.3 / 0.067 |
| deep8_c1 | + blocks 8 | +100 | 77.6 / 0.064 |
| deep8_c1_300 | + 300 iters (drops 200/280) | +211 | 84.0 / 0.045 |
| **deep10_c1_300** | **+ blocks 10** | **+242** | **84.6 / 0.037** |
| deep10_c1_300_s1 | same recipe, seed 1 (the replicate, PLAN5 §5 D1) | +213 | 83.9 / 0.047 |
| deep10_c1_300_lr150 | LR drops at 150/250 instead of 200/280 (PLAN5 §5 D3) | +193 | 83.3 / 0.051 |

Absolute anchor: v2b@64 is ≈ +169 over a rollout UCT with 100 k playouts per move (the
recipe of the strong CodinGame bots, which run plain tree search with random playouts),
so the current best is very roughly +400 over it. Play agent: `deep10_c1_300/
net_0300.pt`. *(Addendum 2026-09-02, PLAN5 §2 A8: the phased schedule `"0:128,24:384"`,
+26 on deep8_c1_300, was re-verified on this net at +10 [−7, +26] — below the rule, so
the play config is flat 256. Equal-compute: deep10@64 beats v2b@427 by +42 [+23, +61];
deep10@64 vs deep8_c1_300@80 is −11 [−30, +7] — the last rung is a wash at fixed budget.)*
*(Addendum 2026-09-05, PLAN5 §5 D1: the seed replicate of the last rung scores +213 [+190,
+236] vs v2b, +9 [−10, +28] vs deep8_c1_300 and +4 [−13, +22] against the other seed. The
seed band at 10×128 is ≈ 3 points / ≈ 30 Elo on the v2b yardstick, and "+ blocks 10" is +35
on one seed and +9 on the other — inside the band, not an established rung. The last
confirmed rung is duration, +211; deep10_c1_300 remains the strongest single net measured.)*

## 3. What makes an AlphaZero recipe stronger here — the validated ledger

**Worked, in order of discovery:**
- **Exploration floor + opening sampling** (v2 era): the first-order fix. Opening
  sampling picks the first moves of each self-play game at random in proportion to the
  search's policy, rather than always taking its top move; the floor mixes 15 % uniform
  randomness into that choice, so every legal opening keeps a minimum chance of being
  played. Without them the policy collapses onto one opening and starves the buffer of
  variety.
- **Gumbel c_scale 0.1 → 1.0: +40 Elo, free.** `c_scale` controls how sharply the
  search's improved policy — the *training target* the net is asked to imitate —
  concentrates on the best moves. Play-time c_scale is irrelevant; the entire effect is
  in what the student is asked to fit. Lesson: audit every inherited library default
  that shapes the target.
- **Width 64 → 128: +77 endpoint.** The adjacent steps (64 → 96, 96 → 128) were each
  individually inside the noise — Sol's catch; only the endpoint is a claim. (+77 is
  wide128_c1's rung on the §2 ladder, measured against v2b, so it includes the +40 from
  c_scale above it. The width step on its own is about +37: PLAN5 §0, PLAN4 §3.)
- **Depth 6 → 8 → 10 blocks: +23, then +35 at 300 iters.** Cheaper per Elo than width at
  this scale — *as measured on one seed.* The seed replicate of the 10-block recipe
  (2026-09-05, PLAN5 §5 D1) scores +9 [−10, +28] over eight blocks and is even with the
  first seed head-to-head, so the 8 → 10 step is inside the ≈ 3-point seed band at this
  size and is not established; the +23 for 6 → 8 was never replicated either. The cost grows in proportion to the network's arithmetic (FLOPs): the two
  steps measured 1.36× and 1.19× their parent's cost.
- **Duration 150 → 300 iters: +127 — the single largest gain in the project.** Both LR
  drops (reductions of the learning rate, at iterations 200 and 280) delivered visible
  steps. The 150-iteration schedule had been starving every earlier architecture
  comparison of convergence. *(2026-09-06, PLAN5 §5 D3: moving the first drop to 150 costs
  ≈ 5 points — −32 Elo against the same-seed reference. The drop is a fixed ≈ +9 step on
  the level the constant-LR phase has reached, the low-LR phase settles within ≈ 20
  iterations and learns nothing further, and the second drop is unresolved on all three
  300-iteration runs. The constant-LR iterations are where the learning happens.)* Corollary: some "capacity" conclusions from 150-iteration
  runs were really optimization conclusions — the nets had not finished learning.
  *(Addendum 2026-09-03, PLAN5 §3 B1: the checkpoint timelines split the +127 into ≈ +5
  points from iterations 150–200 at the constant LR and ≈ +8 from the first drop, at which
  every curve — score, endgame WDL, draw recognition, opening entropy, D4 consistency —
  steps once and then stays flat to 300. The second drop at 280 produces nothing visible
  in-run; "both drops delivered steps" is not supported by the curves.)*
- **Phased play-time search: +50 Elo (v2b), +26 (deep8_300)** at equal mean cost —
  spend fewer simulations early and more late, where games are decided.

**Did nothing (each a clean, CI-bounded null):** exact endgame labels (replacing the
self-play outcome z with solver values as the value target — z was already exact in
98.7 % of ≤14-empty positions at 64 sims); symmetric dedup, early-α, extra input planes,
4-class ownership (four data-hygiene changes: treating symmetric positions as duplicates
in the buffer, applying duplicate down-weighting from the start, more input planes, and a
four-class ownership head); auxiliary heads off; SWA (averaging the last checkpoints:
−28, because LR phases don't mix); a 96-sim final self-play phase (+1, though dosed after
the LR drops); `--games 8192` (+1–4 % throughput — the GPU-bound regime made "free batch
scaling" a myth).

**The revised belief:** "draw blindness" — the value head recognising only ~55 % of exact
draws, at every network size — was called representational for two days: a limit of what
the net *could* express. The 300-iteration runs lifted it to 67–69 % without touching
architecture, labels, or loss. It was substantially an *optimization/duration* artefact.
Lesson: never diagnose capacity from runs that were never trained to convergence.

## 4. Engineering lessons

- **Windows + PyTorch is launch-bound until you make it not be.** Launch-bound means the
  GPU sits idle waiting for the CPU to issue each small piece of work. The fix ladder
  (sync-free search → CUDA-graph replay → fused fp16 inference → continuous self-play)
  was worth 9×. But once the net is wide, the regime flips to GPU-bound — the GPU's
  arithmetic is the bottleneck — and a different economics applies: batch scaling stops
  paying, FLOP ratios predict run cost to within a few percent, and phased budgets become
  affordable.
- **Measure before committing GPU-days.** The 15-minute throughput probes
  (`probe_g8192`, `probe_b8`; three-iteration runs made only to measure speed) killed
  one planned 9-hour run and priced two others. Every cost estimate in PLAN4 §4 came
  from a probe and landed within ~10 %.
- **CUDA-graph faults are real and survivable.** Three `nvlddmkm` (NVIDIA Windows
  driver) faults, all in eval-path graph replay (depth-cap-24, small batch), zero in
  ~60 h of self-play graphs. Neither churn elimination (EvalKit, which builds the
  evaluation players once and reuses them) nor anything in our code was proven causal.
  `--eval_graph 0` removed the surface at a measured 6× eval cost (~3 h/run); in
  hindsight graph eval + auto-retry (≤10 iterations lost per fault) was the better trade.
  The durable win: **two-file checkpointing** (`latest.pt`, light, every iteration;
  `latest_full.pt`, with the replay buffer, every 10th; atomic writes) + retry wrappers
  made every run finish unattended. The old single-file scheme silently destroyed the
  buffer nine iterations out of ten. It bit exactly once, and cost a 79-iteration run.
- **Provenance costs nothing if you start early.** git + `_provenance` in config.json
  (the exact command line, torch version and commit that started the run) + no-clobber
  configs took 30 minutes to add on day 3 and should have existed on day 1.

## 5. Measurement lessons (the real star of the project)

- **The paired suite + noise band is what made every claim above possible.** 516 openings
  × both colours, bootstrap over pairs, ±2.8-point CI, and the rule *believe nothing
  under +3 points on the full suite, final checkpoints only*. Every adopt/null verdict in
  §3 is a sentence because this exists.
- **In-run curves are for shape, not conclusions.** The evaluation run inside training
  is small (432 games, ±6; checkpoints ±4), enough to see a trend, not to call a result.
- **"Strongest" is budget-relative.** At equal inference FLOPs, a small net with 4× the
  search beat the wide net (+101 Elo, v2b@256 vs wide128_c1@64). The ladder is an
  equal-sims instrument; deployment claims need the budget attached. (Sol's best catch.)
- **Reviews of the reviewers paid off.** Of Sol's 16 findings: the statistical ones
  (adjacent-step CIs, equal-compute framing, config clobber) were right and mattered;
  the micro-optimization ones were measurably not worth it; the orientation-bias worry
  was bounded at ≤ 0.6 points by a 20-minute experiment. Adjudicating with data beat
  both accepting and dismissing.
- Known open debts, accepted at the time: no seed replicate of any wide/deep/300 recipe
  (the +127 and +35 results were taken to dwarf the ±2.5-point seed band measured at
  6×64); the suites all descend from v2a-era games; endgame_v1 is a development set after
  ~50 in-run reads. *Paid 2026-09-05:* the 10×128 replicate put the band at ≈ 3 points and
  the +35 inside it (+127 still dwarfs it); the v2 endgame suite's sealed half was read
  once and agreed with the dev half (PLAN5 §2 A9).

## 6. What we learned about the game (levels: behavioural / predictive / search-relative / exact)

Each belief carries a level: *behavioural* (what the agent does), *predictive* (what its
value head forecasts), *search-relative* (the number depends on the search budget it was
measured with), or *exact* (checked against the solver). Unchanged from PLAN3 §5 except
where noted:
- Centre-of-centre (m=40, the centre cell of the centre board) is the best first move in
  every net × budget × seed tested; openings are otherwise flat (root Q-gaps ≤ 0.02 —
  the search's values for the best and next-best replies differ by at most 0.02).
  Ordering is stable, values are not.
- Games are decided late: median settled at ply 38 of ~51 (64-sim best-child Q, the
  point from which the search's favourite move's value stops changing side); nothing is
  settled at ply 30.
- A free move is worth +0.16 ± 0.03 in expected score (matched natural positions,
  cluster-robust standard errors that allow for positions from the same game being
  related) — half the naive tensor-probe estimate, and largest late in the game when
  ahead.
- The board "value hierarchy" (centre worth more than corners, corners more than edges)
  is macro-line counting in disguise (±0.17 per line). *(Addendum 2026-09-03, PLAN5 §2 A5:
  on the two strong nets the lines are still ±0.15 each, but with them controlled an own
  board now carries a small residual of its own, +0.03 … +0.07 — a fifth to a third of a
  line; which class of board is worth most is not resolved between the nets.)*
- The count tiebreak decides ~30 % of strong games and rises with strength; draws rise
  with strength too (12 % at 64-sim eval, 19–22 % between the newest nets — the
  strongest agents increasingly *prove* draws).
- **Revised:** endgame value error is not a wall. Trained long enough, the raw head
  reaches 84.6 % WDL / 96.7 % optimal moves, and search at 256 sims is 99.9 % optimal
  with regret 0.001 — the endgame is, in practice, solved by the agent.

## 7. Where things stand, and the open list for whenever work resumes

- **Best net** `runs/deep10_c1_300/net_0300.pt`; best play config: flat `--sims 256`
  or more (phased re-verified 2026-09-02, not confirmed — §2 addendum). Web UI:
  `python web/server.py runs/deep10_c1_300/net_0300.pt --sims 800 --device cuda:1`.
- **Neither depth nor duration is exhausted** — 12-block and 600-iteration runs are the
  obvious continuations, each a committed GPU-day, both on hold per the pause. *(2026-09-06:
  depth 8 → 10 is inside the seed band and an earlier LR drop hurts, so the one continuation
  the evidence supports is a longer constant-LR phase — 600 iterations, drops late — on 8
  blocks; PLAN5 §5 D2/D3.)*
- Also open, cheaper: a seed replicate of the final recipe (rigor — *done 2026-09-05*,
  PLAN5 §5 D1); an analysis second
  pass with the new net (atlas / decision / freemove / puzzles → `puzzles_v2_dev`, suites
  refresh with a dev/test split); the 6×64 endgame-overfit diagnostic (now largely
  mooted by §3's revision); the CodinGame port (needs the batch-1 latency budget — one
  position at a time under a per-move time limit — not the ladder).
- Everything is committed; `runs/` holds ~11 GB (games corpora + checkpoints); the
  explainer artifact tells the story through queue5 and does not yet include the
  10-block result or the draw-blindness revision (since added; the 2026-09-05 revision
  carries the seed replicate too).
