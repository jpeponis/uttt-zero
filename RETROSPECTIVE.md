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
| **deep8_c1_300_e2** | **deep8_c1_300 + `--epochs 2` (512 optimizer steps per iteration; PLAN6 H1)** | **+291** | **87.6 / 0.036** |
| **deep8_c1_300_e4** | **deep8_c1_300_e2 + `--epochs 4` (1024 optimizer steps per iteration; PLAN6 H1b)** | **+363** | **90.1 / 0.022** |
| gcnn8_c1_300_e4 | deep8_c1_300_e4's recipe with the D4 group-convolutional trunk (`--gcnn 16`, exactly equivariant, same inference cost; PLAN6 H4) — hurt | +162 | 80.8 / 0.058 |
| **deep8_c1_300_e8** | **deep8_c1_300_e4 + `--epochs 8` (2048 optimizer steps per iteration; PLAN6 §9a H1c)** | **+363 (+40 vs e4)** | **91.3 / 0.022** |

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
*(Addendum 2026-09-07, PLAN6 H1: doubling the optimizer steps per iteration on 8 blocks, nothing
else changed, is +100 [+81, +119] over deep8_c1_300, +86 over deep10_c1_300 and +291 [+266,
+318] over v2b — the strongest net and the largest single step of the ladder, for +1.3 h of
training. The play agent is now `deep8_c1_300_e2/net_0300.pt`.)*
*(Addendum 2026-09-08, PLAN6 H1b: doubling them a second time — 1024 optimizer steps per
iteration, nothing else changed — is +64 [+44, +83] over `deep8_c1_300_e2`, +185 over
deep8_c1_300, +141 over deep10_c1_300 and +363 [+337, +395] over v2b, for +2.4 h of training
on a 16.9 h run. Two passes over each generated position was not the plateau either. The raw
value head now names 90.1 % of solved endgames correctly, recognises 79 % of the exact draws
and loses 0.022 of value to its preferred move. The play agent is now
`deep8_c1_300_e4/net_0300.pt`.)*
*(Addendum 2026-09-09, PLAN6 H4: the chain's one architectural arm — the same recipe with the
ResNet trunk replaced by a D4 group convolution, exactly equivariant, 312 k parameters against
2.46 M and exported to ordinary convolutions so it costs the same to evaluate — **hurt: 22.0 %
[19.9, 24.2], −220 Elo [−242, −199] against its parent**, +162 over v2b, and −50 [−69, −32]
below deep8_c1_300, the 1×-update ResNet of the same shape and duration. Exact symmetry held
throughout (D4 Jensen–Shannon 0.000 bits and value std 0.000 at all 30 checkpoints, against the
parent's 0.026 / 0.052) and nothing was unstable — it converged, stably, to a much weaker net.
The cause reads as capacity, not the learning rate: the supervised advantage that licensed the
run (0.078 of dev policy KL at 3 120 optimizer steps) has shrunk to 0.027 by 6 240 and reversed
by 12 480, where the plain ResNet overtakes, and a quarter of the learning rate at the same
steps recovers nothing. Its LR drops are the largest any run here has shown — +30.7 points at
the first and a resolved +6.5 at the second, where four ResNets showed nothing — which is the
same sharper basin read at play strength. Self-play cost 1.02× the parent's, training 1.52×,
the run 19.8 h against 16.9. The play agent stays `deep8_c1_300_e4/net_0300.pt`; KNOWLEDGE 50,
48 restated.)*
*(Addendum 2026-09-10, PLAN6 §9a H1c: doubling them a third time — 2048 optimizer steps per
iteration, nothing else changed — is **+40 [+23, +57] over `deep8_c1_300_e4`**, +110 over
`deep8_c1_300_e2`, +211 over deep8_c1_300 and +186 over deep10_c1_300, for +5.0 h of training
on a 21.96 h run. It is helped by the pre-registered rule, but only 2.8 points over the line and
inside one ≈ 3-point seed band of it — the narrowest adoption in the chain — so **the
dose–response of the update lever now reads +100 → +64 → +40**, each doubling worth about
two-thirds of the one before it and none of them the plateau. **The v2b column stops working
here:** the new net scores 89.0 % against the reference, the same +363 its parent scored, because
differences compress near 90 % — the head-to-head against the parent, not the ladder's yardstick,
is what resolved this rung, and would have to resolve any further one. The raw value head now
names 91.3 % of solved endgames correctly, recognises 81 % of the exact draws and loses 0.022 of
value to its preferred move; exact symmetry is not what the extra passes bought (D4
Jensen–Shannon 0.025 bits and value std 0.047, against `_e4`'s 0.026 / 0.052). The same 8×128
ResNet, so the +40 costs nothing per evaluation. The play agent is now
`deep8_c1_300_e8/net_0300.pt`; KNOWLEDGE 51.)*

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
  ≈ 5 points — −32 Elo [−50, −14] against the reference, −10 [−29, +9] against the seed
  replicate: one perturbed run read against the two-seed band, "hurt" by the pre-registered
  rule. "Same seed" here means the same start, not the same run — the pipeline is not
  bitwise deterministic and the two runs' self-play differed from iteration 1, before the
  intervention (PLAN6 §1 item 13). The drop is a fixed ≈ +9 step on the level the
  constant-LR phase has reached; strength settles within ≈ 20 iterations of it, while the
  raw head's endgame reads keep creeping (WDL 80.3 → 83.3 %, draw recognition 60 → 66–68 %
  over the low-LR phase). The second drop, read on the full suite at ±2.8 for all four
  300-iteration runs (PLAN6 F2), does nothing resolvable — 300 − 260 clears 3 points on one run
  of four — while the first drop is a resolved +5 … +9 on every run; "both drops delivered
  steps" above is withdrawn. The constant-LR iterations are where the strength is built.)* Corollary: some "capacity" conclusions from 150-iteration
  runs were really optimization conclusions — the nets had not finished learning.
  *(Addendum 2026-09-03, PLAN5 §3 B1: the checkpoint timelines split the +127 into ≈ +5
  points from iterations 150–200 at the constant LR and ≈ +8 from the first drop, at which
  every curve — score, endgame WDL, draw recognition, opening entropy, D4 consistency —
  steps once and then stays flat to 300. The second drop at 280 produces nothing visible
  in-run; "both drops delivered steps" is not supported by the curves.)*
- **Phased play-time search: +50 Elo (v2b), +26 (deep8_300)** at equal mean cost —
  spend fewer simulations early and more late, where games are decided.
- **Optimizer steps 256 → 512 per iteration: +100 Elo, for +1.3 h** (2026-09-07, PLAN6 H1;
  KNOWLEDGE 46). The one lever nobody had pulled: every run had trained ≈ one sampled
  example per generated position. With the same games, buffer and schedule, twice the
  updates beat the 8-block parent by +100, the 10-block nets by +86 / +97, and the
  reference by +291. The learner was update-limited; the +127 of duration was mostly its
  updates; and every recipe comparison in this ledger was made under under-training.
  The supervised twin (KNOWLEDGE 47): on a fixed teacher the fit depends on optimizer
  steps, not on distinct positions — eight passes over 50 000 positions equal one pass over
  400 000. Corollary for the next runs: dose–response (`--epochs 4`) before more games.
  *(2026-09-08, PLAN6 H1b, KNOWLEDGE 49: the dose–response answered — **512 → 1024 steps is
  another +64** [+44, +83] over `deep8_c1_300_e2` and +363 over v2b, for ≈ +2.5 h of training
  (t_train 4.98 h against 2.55 h) on a 16.9 h run. Four sampled examples per generated position
  is still not the plateau: the learner is update-limited at two passes exactly as it was at
  one, and nothing complains — the sampled replay age is unchanged at 3.35 iterations of a
  7.6-iteration buffer window, and 133 of 307 200 steps were skipped by the GradScaler, H1's
  rate. What this says about where the ladder's rungs came from: the largest confirmed rung,
  duration (+127), was mostly its updates; pulling the update lever on its own has now added
  +164 more on top of it; and the two depth rungs it was weighed against (+23 for 6 → 8 blocks,
  +35 for 8 → 10, the latter inside the seed band) were measured on nets trained at a quarter
  of the updates the same data supports.)*
  *(2026-09-10, PLAN6 §9a H1c, KNOWLEDGE 51: the third doubling, **1024 → 2048 steps, is +40**
  [+23, +57] over `deep8_c1_300_e4` for +5.0 h of training on a 21.96 h run — so the curve is
  **+100 → +64 → +40**, each doubling about two-thirds of the last, all three positive, and
  eight sampled examples per generated position is still not the plateau. What the run finally
  makes visible is the price: the sampled distinct-position fraction is down to **0.48 → 0.45**
  across the run, against `_e4`'s 0.63 and H1's 0.81 — each generated row is now drawn about
  eight times — and still nothing complains: the replay age is unchanged at 3.31 iterations, 244
  of 614 400 steps were skipped by the GradScaler at H1b's rate, the losses are lower, and the
  self-play statistics are H1b's to within half a ply and a point (53.2 plies, 16.6 % drawn). The over-fitting branch of H1's reading has
  now been tested three doublings deep and has not appeared; what has run out is the *yardstick*,
  not the lever — +363 vs v2b for the second run in a row. The lever's own cost is the training
  half of the run doubling again, 4.98 h → 9.97 h, while self-play stays at 11.9 h.)*

**Hurt:** **an exactly equivariant trunk, at equal inference cost** (2026-09-09, PLAN6 H4;
KNOWLEDGE 50). The one architectural change of the chain: the 8×128 ResNet trunk replaced by a
D4 group convolution — the board's symmetry built into the weights instead of augmented into
the data, 312 k parameters against 2.46 M, exported to ordinary convolutions so a game costs
the same to play — on the best recipe in the ladder with nothing else changed. It scored
**22.0 %, −220 Elo against its parent**, and −50 below even the 1×-update ResNet of the same
shape and duration. It did not misbehave: exact symmetry held at all 30 checkpoints (D4 JS
0.000 bits), 132 of 307 200 steps were skipped against the parent's 133, no loss diverged. It
converged, stably, to a much weaker net. What licensed the run was a supervised gate on a
frozen teacher read at 3 120 optimizer steps, where the group-convolutional net fit far better;
carried to 12 480 steps the plain ResNet overtakes it and the equivariant net begins over-fitting
the frozen set, and a quarter of the learning rate at the same steps makes it worse still —
capacity, not the learning rate, and a gate read at 1 % of the exposure it was gating (§5).

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
- **A reboot is the one failure a retry wrapper cannot cover.** A Windows Update restart
  killed H4 at iteration 268 of 300 (23:55, outside the configured active hours, nothing
  pending beforehand): the retry loop's own bash process died with the session
  (`STATUS_DLL_INIT_FAILED_LOGOFF`, `0xC000026B`), so the six-attempt retry loop never reached
  attempt 1 and nothing resumed unattended: the machine sat idle from 23:55 until it was
  relaunched by hand at 09:24. What did work is the two-file checkpointing above — relaunching
  the same launcher was the entire recovery, because `train2` prefers `latest_full.pt` (it
  resumed from the iteration-259 full checkpoint, buffer and generators restored, and re-ran
  260 onward) and the evaluation worker beside it skips whatever `eval_full.jsonl` already holds. Verify before resuming — every
  checkpoint loaded with a strict `state_dict` match and re-hashed to what the worker had
  recorded, `log.jsonl` had no gap or duplicate, `git fsck` was clean — and remember that the
  iterations after the resume point are a *perturbed re-run*, stamped `attempt: 1`, so that
  file must be read de-duplicated by iteration. The cheap prevention is the one now in place:
  pause Windows Update across the run window (paused here until 2026-10-14).
- **Provenance costs nothing if you start early.** git + `_provenance` in config.json
  (the exact command line, torch version and commit that started the run) + no-clobber
  configs took 30 minutes to add on day 3 and should have existed on day 1.

## 5. Measurement lessons (the real star of the project)

- **The paired suite + noise band is what made every claim above possible.** 516 openings
  × both colours, bootstrap over pairs, ±2.8-point CI, and the rule *believe nothing
  under +3 points on the full suite, final checkpoints only*. Every adopt/null verdict in
  §3 is a sentence because this exists. The rule is a decision rule for adopting a change,
  not an equivalence test: a result inside the band is "not established", never "equal" —
  the interval on the difference says how close (PLAN6 §1 item 21).
- **"Same seed" is the same start, not the same run.** Two runs with the same seed and
  recipe have the same initial weights and the same first iteration, differ at the fourth
  decimal of the first loss (`cudnn.benchmark`, fp16), and have visibly different self-play
  by iteration 1 — a 4096-game loop amplifies a last-bit difference within one iteration.
  RNG bookkeeping cannot make trajectories reproducible on this path; the defence is
  replication, and a "same-seed" comparison is read against the seed band, never as paired
  (PLAN6 §1 item 13; the RNG hygiene of PLAN6 E4 makes evaluation *observationally* neutral,
  which is a different, cheaper property).
- **In-run curves are for shape, not conclusions.** The evaluation run inside training
  is small (432 games, ±6; checkpoints ±4), enough to see a trend, not to call a result.
- **A screening gate on frozen data has to be read at a step count of the order of the run it
  is gating.** Phase G ranked five architectures at 3 120 optimizer steps — 1 % of the 307 200
  steps of the run it licensed — and the ordering it certified reverses by 12 480 steps, where
  the plain ResNet overtakes the group-convolutional net; self-play at full exposure then read
  the reversed ordering, at a cost of 20 GPU-hours (PLAN6 H4; KNOWLEDGE 48, 50). The cheap
  supervised screen was still worth its hour — it is the reading that was over-extended. Read
  such a gate out to the horizon it will be applied at, or until the curves have crossed or
  clearly will not.
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
  Ordering is stable, values are not. *(Addendum 2026-09-10, PLAN6 I1 on the +363 net: [40]
  is still rank 1 and [13] rank 15, and X's edge after [40] has risen again to +0.495; but
  "otherwise flat" is the weaker nets' reading — measured by reply **orbit** the gap after
  [13] is 0.142 and after [4] 0.090, only 9 of 15 first moves are flat at ≤ 0.03, and the
  best-to-worst range runs 0.09–0.26. KNOWLEDGE 3, 4, 5.)*
- Games are decided late: median settled at ply 38 of ~51 (64-sim best-child Q, the
  point from which the search's favourite move's value stops changing side); nothing is
  settled at ply 30. *(2026-09-10: 36 on the reference v2a games and **34** on strong play
  for the +363 net, with a first quartile of 25 — "nothing is settled at ply 30" was never
  right and the settling keeps moving earlier with strength. KNOWLEDGE 20.)*
- A free move is worth +0.16 ± 0.03 in expected score (matched natural positions,
  cluster-robust standard errors that allow for positions from the same game being
  related) — half the naive tensor-probe estimate, and largest late in the game when
  ahead. *(2026-09-10: **+0.195 ± 0.028 of utility** on the +363 net, the deep10 number to
  the third decimal, and **+0.30** at plies 44–50 when the count is level or better; on that
  net the middlegame value of a free move runs with the count, −0.16 two boards down to
  +0.24 two up, where deep10's was a flat +0.03. Values here are utilities, not expected
  score — KNOWLEDGE's header. KNOWLEDGE 8, 10.)*
- The board "value hierarchy" (centre worth more than corners, corners more than edges)
  is macro-line counting in disguise (±0.17 per line). *(Addendum 2026-09-03, PLAN5 §2 A5:
  on the two strong nets the lines are still ±0.15 each, but with them controlled an own
  board now carries a small residual of its own, +0.03 … +0.07 — a fifth to a third of a
  line; which class of board is worth most is not resolved between the nets.)* *(2026-09-10:
  the lines are ±0.15 on the +363 net too, and the residual is smaller there, +0.02 … +0.05 —
  it grew once, from v2b's zero, and has not grown since. The class order is still unresolved:
  that net's two fits disagree with each other. KNOWLEDGE 13, 14.)*
- The count tiebreak decides ~30 % of strong games and rises with strength; draws rise
  with strength too (12 % at 64-sim eval, 19–22 % between the newest nets — the
  strongest agents increasingly *prove* draws). *(2026-09-10: the share held flat at ~27 %
  from v2a to deep10 and then moved — **33 % on the +363 net** (16.5 % by a board count,
  16.6 % by an equal count), whose own self-play is **16.6 % drawn** against deep10's 13.1.
  KNOWLEDGE 24, 25.)*
- **Revised:** endgame value error is not a wall. Trained long enough, the raw head
  reaches 84.6 % WDL / 96.7 % optimal moves, and search at 256 sims is 99.9 % optimal
  with regret 0.001 — the endgame is, in practice, solved by the agent.

## 7. Where things stand, and the open list for whenever work resumes

- **Best net** `runs/deep8_c1_300_e8/net_0300.pt` (2026-09-10; +40 vs `deep8_c1_300_e4`, +110
  vs `deep8_c1_300_e2`, +211 vs deep8_c1_300, +186 vs deep10_c1_300, and +363 vs v2b — the same
  +363 `_e4` scored, the yardstick having saturated near 90 %); play config unchanged: flat
  `--sims 256` or more (the phased schedule is +10 on deep10 and +11 [−6, +26] on `_e2` — not
  confirmed on either; the 8-way average is +32 there as it was +35 on deep10, the canonical
  evaluator a null on both; none of the three re-run on `_e4` or `_e8`). Web UI:
  `python web/server.py runs/deep8_c1_300_e8/net_0300.pt --sims 800 --device cuda:1`.
- **The chain of three runs is closed** (PLAN6 Handover, owner-approved 2026-09-07, one change
  per run): H1b `deep8_c1_300_e4` done 2026-09-08 (+64, above); **H4 `gcnn8_c1_300_e4`** — the
  D4 group-convolutional net in self-play, exactly equivariant at the same inference cost —
  done 2026-09-09 and **hurt**: 22.0 % [19.9, 24.2], −220 Elo against its parent, +162 vs v2b,
  with exact symmetry held at all 30 checkpoints and nothing unstable; the cause reads as
  capacity, not the learning rate (PLAN6 log, 2026-09-09; KNOWLEDGE 50, and 48 restated).
  **H3 `deep8_c1_600_e4` was withdrawn by the owner on 2026-09-09, unrun** — as written it
  doubles data, updates and teacher exposure together, the confound PLAN6 §0 exists to remove,
  so its reading could not have said which term moved; its queue scripts stay in the repo,
  staged but withdrawn. **H5 (`--head_tying 1`) was not proposed**: the supervised margin closes
  across three doublings of the step count, so the prediction is null-to-small — inside the seed
  band — and exact policy symmetry has no consumer (41b).
- **The open list was three items and no more** (the owner's closing programme, PLAN6 §9,
  2026-09-09), in launch order: **H1c `deep8_c1_300_e8`** — the third doubling of the optimizer
  steps (2048 per iteration, parent `deep8_c1_300_e4`, ≈ 22–23 h on the 3090), reading the
  dose–response curve +100 → +64 → ? to its asymptote or its plateau, with the over-fitting
  branch of H1's reading finally testable; **G arm (g) `gcnn8x46`** — the D4 G-CNN at the
  ResNet's *parameter* count (46 base filters × 8 orientations, 2.46 M parameters, 7.0× the
  inference cost as measured) on the frozen teacher, to separate capacity from equivariance in
  H4's negative result, read at 12 480 steps as KNOWLEDGE 48's restatement requires; **I1** — the
  analysis second pass, PLAN5 Phase A's tools re-run on the +363 net at the same settings, every
  claim marked held / moved / reversed, which is the first test of the project's own central
  methodological claim on the strongest net it has. **All three are now done. Arm (g)
  came back on 2026-09-09 and closed the equivariant line**: at the ResNet's parameter count the
  G-CNN trails resnet8 at 12 480 steps (1.034 against 0.763) and the margin reverses by 6 240,
  so the width was not what cost H4 its 220 Elo and nothing is proposed (KNOWLEDGE 48, 50).
  **I1 ran 02:27–07:23 on 2026-09-10** and is written up in KNOWLEDGE (the note at the head of
  §1): of 34 claims re-read, 15 held, 18 moved and **1 reversed** — after [40] `_e4`
  prefers the corner reply orbit where both earlier strong nets preferred the edge, the first
  ordering in the file to flip with strength. **H1c came in on 2026-09-10 and closes the list**:
  `deep8_c1_300_e8` ran 21.96 h on the 3090 without a crash and is **+40 Elo [+23, +57] over its
  parent** — helped, but 2.8 points over the adoption line and inside one seed band of it — so
  the dose–response of the update lever reads **+100 → +64 → +40** and eight passes are still
  not the plateau, while the v2b yardstick has stopped resolving (+363 for the second run
  running; KNOWLEDGE 51). **The play agent is now `deep8_c1_300_e8/net_0300.pt`.** The closing
  programme is complete, and **nothing further is proposed** — the obvious
  continuation, `--epochs 16`, would cost ≈ 32 h for a step predicted inside the seed band.
  **E11**, the off-machine backup and the first push to a remote, followed on 2026-09-12 and is
  **half done**: the repository is public at `https://github.com/jpeponis/uttt-zero` — 52 commits
  and a 249.27 MiB pack on `main`, MIT for the code and CC BY 4.0 for the written work and the
  data — and **the off-machine copy is not made**, deferred by the owner for want of any
  destination on this machine (PLAN6's 2026-09-12 log entry and Handover). The open list is the
  write-up and that copy.
- **Neither depth nor duration is exhausted** — 12-block and 600-iteration runs are the
  obvious continuations, each a committed GPU-day, both on hold per the pause. *(2026-09-06:
  depth 8 → 10 is inside the seed band and an earlier LR drop hurts, so the continuation the
  evidence supports is more constant-LR learning on 8 blocks. "Duration" confounds data,
  updates, teacher and LR timing (PLAN6 §0), so the first run to propose is the cheap arm
  that separates one of them — `--epochs 2` at 300 iterations, PLAN6 H1 — and the
  600-iteration run with late drops follows its result, PLAN6 H3.)* *(2026-09-09: the
  update axis was separated twice and paid +164; the 600-iteration run was **withdrawn
  unrun** for the same confound, so duration is still neither separated nor bought.)*
- Also open, cheaper: a seed replicate of the final recipe (rigor — *done 2026-09-05*,
  PLAN5 §5 D1); an analysis second
  pass with the new net (atlas / decision / freemove / puzzles → `puzzles_v2_dev`, suites
  refresh with a dev/test split — *approved 2026-09-09 as I1, run 2026-09-10, done; it wrote
  `suites/puzzles_v3_dev.npz` and `runs/book_deep8_e4.json`*); the 6×64
  endgame-overfit diagnostic (now largely
  mooted by §3's revision); the CodinGame port (needs the batch-1 latency budget — one
  position at a time under a per-move time limit — not the ladder).
- Everything is committed **and pushed** — the repository has been public at
  `https://github.com/jpeponis/uttt-zero` since 2026-09-12. `runs/` holds **17.02 GB in 5 328
  files** (games corpora + checkpoints), not the ~11 GB recorded here until now. Git carries the
  code, the documents, `suites/` and every run's `net_0150/0200/0300.pt`, so what is **still
  single-copy on one machine is the `games/` corpora and the intermediate checkpoints** — 5.23 GB
  by PLAN6 §2 E11's list, deferred for want of a destination. The
  explainer artifact tells the story through queue5 and does not yet include the
  10-block result or the draw-blindness revision (since added; the 2026-09-05 revision
  carries the seed replicate too).
