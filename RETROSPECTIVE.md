# uttt-zero — Retrospective (2026-09-02, at the owner-directed pause)

Four days of work: two building (PLAN2/PLAN3 era), two scaling under review discipline
(PLAN4 era). This document is the "what did we actually learn" synthesis the pause was
called for. Sources: PLAN2–PLAN4, NOTES-v2, the three reviews, `runs/*/analysis.out`.

## 1. The arc in six lines

1. **Build** (day 1–2): engines cross-checked to 41 M+ positions, batched Gumbel search,
   CUDA-graph replay, continuous self-play, GPU replay buffer — 25 → 220 games/s.
2. **Measure** (day 2): paired opening suite, exact endgame set, rollout anchor, seed
   replicates → the ±3-point rule. The measurement kit outlived every other decision.
3. **Map the recipe** (day 2): ten runs; two levers real (c_scale, width), five nulls.
4. **Review** (day 3): two independent model reviews adjudicated; claims corrected,
   probes run, ops hardened, git established.
5. **Scale** (day 3–4): depth +23, duration +127, depth-at-duration +35 — the ladder
   went v2b → +242 in four runs.
6. **Survive** (day 3–4): three GPU faults, all in eval-path CUDA graphs; the recovery
   machinery (full-state checkpoints + retries) turned them from run-killers into
   ≤ 10-iteration blips.

## 2. Final strength ladder (paired suite vs v2b @64 sims, final checkpoints)

| net | recipe | Elo | endgame raw WDL / regret |
|---|---|---|---|
| dev1 | v1 baseline | −95 | 71.2 / 0.083 |
| v2b | v2 pipeline + floor + sims schedule | 0 | 75.0 / 0.078 |
| abl_cscale1 | + c_scale 1.0 | +40 | 74.6 / 0.077 |
| wide128_c1 | + filters 128 | +77 | 76.3 / 0.067 |
| deep8_c1 | + blocks 8 | +100 | 77.6 / 0.064 |
| deep8_c1_300 | + 300 iters (drops 200/280) | +211 | 84.0 / 0.045 |
| **deep10_c1_300** | **+ blocks 10** | **+242** | **84.6 / 0.037** |

Absolute anchor: v2b@64 ≈ +169 over a 100 k-playout rollout UCT (the CodinGame-Legend
recipe), so the current best is very roughly +400 over it. Play agent: `deep10_c1_300/
net_0300.pt`. *(Addendum 2026-09-02, PLAN5 §2 A8: the phased schedule `"0:128,24:384"`,
+26 on deep8_c1_300, was re-verified on this net at +10 [−7, +26] — below the rule, so
the play config is flat 256. Equal-compute: deep10@64 beats v2b@427 by +42 [+23, +61];
deep10@64 vs deep8_c1_300@80 is −11 [−30, +7] — the last rung is a wash at fixed budget.)*

## 3. What makes an AlphaZero recipe stronger here — the validated ledger

**Worked, in order of discovery:**
- **Exploration floor + opening sampling** (v2 era): the first-order fix; without it the
  policy collapses onto one opening and starves the buffer.
- **Gumbel c_scale 0.1 → 1.0: +40 Elo, free.** A sharper improved-policy *training
  target*. Play-time c_scale is irrelevant — the entire effect is in what the student is
  asked to fit. Lesson: audit every inherited library default that shapes the target.
- **Width 64 → 128: +77 endpoint** (adjacent steps individually inside noise — Sol's
  catch; only the endpoint is a claim).
- **Depth 6 → 8 → 10 blocks: +23, then +35 at 300 iters.** Cheaper per Elo than width at
  this scale (FLOP-proportional cost, measured 1.36× and 1.19×).
- **Duration 150 → 300 iters: +127 — the single largest gain in the project.** Both LR
  drops delivered visible steps; the 150-iteration schedule was starving every earlier
  architecture comparison of convergence. Corollary: some "capacity" conclusions from
  150-iteration runs were really optimization conclusions.
- **Phased play-time search: +50 Elo (v2b), +26 (deep8_300)** at equal mean cost —
  spend simulations late, where games are decided.

**Did nothing (each a clean, CI-bounded null):** exact endgame labels (self-play z is
already exact in 98.7 % of ≤14-empty positions at 64 sims); symmetric dedup, early-α,
extra input planes, 4-class ownership; auxiliary heads off; SWA (−28: LR phases don't
mix); a 96-sim final self-play phase (+1, though dosed post-drop); `--games 8192`
(+1–4 % throughput — the GPU-bound regime made "free batch scaling" a myth).

**The revised belief:** "draw blindness" — the value head recognising only ~55 % of exact
draws at every size — was called representational for two days. The 300-iteration runs
lifted it to 67–69 % without touching architecture, labels, or loss. It was substantially
an *optimization/duration* artefact. Lesson: never diagnose capacity from runs that were
never trained to convergence.

## 4. Engineering lessons

- **Windows + PyTorch is launch-bound until you make it not be.** The fix ladder
  (sync-free search → CUDA-graph replay → fused fp16 inference → continuous self-play)
  was worth 9×. But once the net is wide, the regime flips to GPU-bound and a different
  economics applies: batch scaling stops paying, FLOP ratios predict run cost to within
  a few percent, and phased budgets become affordable.
- **Measure before committing GPU-days.** The 15-minute probes (`probe_g8192`,
  `probe_b8`) killed one planned 9-hour run and priced two others. Every cost estimate
  in PLAN4 §4 came from a probe and landed within ~10 %.
- **CUDA-graph faults are real and survivable.** Three `nvlddmkm` faults, all in
  eval-path graph replay (depth-cap-24, small batch), zero in ~60 h of self-play graphs.
  Neither churn elimination (EvalKit) nor anything in our code was proven causal;
  `--eval_graph 0` removed the surface at a measured 6× eval cost (~3 h/run) — in
  hindsight graph eval + auto-retry (≤10 iterations lost per fault) was the better
  trade. The durable win: **two-file checkpointing** (`latest.pt` light every iteration,
  `latest_full.pt` with buffer every 10th, atomic writes) + retry wrappers made every
  run finish unattended. The old single-file scheme silently destroyed the buffer nine
  iterations out of ten — it bit exactly once, and cost a 79-iteration run.
- **Provenance costs nothing if you start early.** git + `_provenance` in config.json +
  no-clobber configs took 30 minutes to add on day 3 and should have existed on day 1.

## 5. Measurement lessons (the real star of the project)

- **The paired suite + noise band is what made every claim above possible.** 516 openings
  × both colours, bootstrap over pairs, ±2.8-point CI, and the rule *believe nothing
  under +3 points on the full suite, final checkpoints only*. Every adopt/null verdict
  in §3 is a sentence because this exists.
- **In-run curves are for shape, not conclusions** (432 games, ±6; checkpoints ±4).
- **"Strongest" is budget-relative.** At equal inference FLOPs, a small net with 4× the
  search beat the wide net (+101 Elo, v2b@256 vs wide128_c1@64). The ladder is an
  equal-sims instrument; deployment claims need the budget attached. (Sol's best catch.)
- **Reviews of the reviewers paid off.** Of Sol's 16 findings: the statistical ones
  (adjacent-step CIs, equal-compute framing, config clobber) were right and mattered;
  the micro-optimization ones were measurably not worth it; the orientation-bias worry
  was bounded at ≤ 0.6 points by a 20-minute experiment. Adjudicating with data beat
  both accepting and dismissing.
- Known open debts, accepted: no seed replicate of any wide/deep/300 recipe (the +127
  and +35 results dwarf the ±2.5-point seed band, so the ladder's shape is safe; the
  small steps are not individually resolved); suites all descend from v2a-era games;
  endgame_v1 is a development set after ~50 in-run reads.

## 6. What we learned about the game (levels: behavioural / predictive / search-relative / exact)

Unchanged from PLAN3 §5 except where noted:
- Centre-of-centre (m=40) is the best first move in every net × budget × seed tested;
  openings are otherwise flat (root Q-gaps ≤ 0.02). Ordering is stable, values are not.
- Games are decided late: median settled at ply 38 of ~51 (64-sim best-child Q);
  nothing is settled at ply 30.
- A free move is worth +0.16 ± 0.03 (matched natural positions, cluster-robust) —
  half the naive tensor-probe estimate, largest late when ahead.
- Board "value hierarchy" is macro-line counting in disguise (±0.17 per line).
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
  obvious continuations, each a committed GPU-day, both on hold per the pause.
- Also open, cheaper: seed replicate of the final recipe (rigor); analysis second pass
  with the new net (atlas / decision / freemove / puzzles → `puzzles_v2_dev`, suites
  refresh with dev/test split); the 6×64 endgame-overfit diagnostic (now largely mooted
  by §3's revision); CodinGame port (needs the batch-1 latency budget, not the ladder).
- Everything is committed; `runs/` holds ~11 GB (games corpora + checkpoints); the
  explainer artifact tells the story through queue5 and does not yet include the
  10-block result or the draw-blindness revision.
