# uttt-zero — PLAN4: hand-off (2026-08-30, after the two-model review)

Read this first; it supersedes `PLAN3.md` (kept — its §2 measurement kit, §3 ladder, §4 lessons
and §5 game beliefs remain the reference and are not repeated here; only corrections appear
below). New since PLAN3: two independent reviews (`REVIEW-claude.md`, `REVIEW-sol.md` — GPT-5.6
"Sol", 16 findings), throughput probes, robustness checks, a git repo, and the operational
fixes those reviews demanded. File map: `README.md`.

## 1. What changed since PLAN3

**Code/ops (committed, `git log`):**
- `git init` done; code, docs, suites, run configs/logs and every run's final checkpoint are
  tracked (~40 MB). Commit before and after every recipe change from now on.
- `train2.py`: `latest.pt` is written atomically (tmp + rename — a crash mid-save can no
  longer destroy the resume point); `config.json` is never clobbered (a resume writes
  `config_resume_*.json` beside it and warns on drift); provenance (`argv`, torch version,
  git rev, start time) is stored under `_provenance`; each log line now has `t_ckpt` and
  end-to-end `t_iter` (the previously untimed persistence/buffer/checkpoint overhead is
  visible); a finished run writes `runs/<run>/DONE`.
- `eval_run.sh` discovers the final checkpoint (no more hardcoded `net_0150.pt` — a 300-iter
  run would have been silently scored at its midpoint, Sol finding 15 = claude finding 2);
  it also matches vs `wide128_c1` now. `watch_run.sh` waits for `DONE`, not a checkpoint name.
- `tools/puzzles.py --out` is required (the default silently overwrote the frozen
  `suites/puzzles_v1.npz` — exactly the yardstick trap PLAN3 §7 warns about).
- `search.py`: `cap_hits` included in the CUDA-graph capture snapshot (first-call metric
  contamination, Sol finding 11; moves were never affected).

**Measurements (new, all reproducible from `runs/`):**
- `runs/probe_g8192.out`: wide128 recipe at `--games 8192` → 2236–2293 pos/s steady state vs
  2216 at 4096. **Batch doubling buys 1–4 %.** PLAN3 §6.1(b)'s "the wide nets are GPU-bound,
  so batch scaling is now nearly free" had the logic backwards — batch scaling is free in the
  *launch-bound* regime; wide128 at 4096 is ~95 % GPU-bound. `--games 8192` is dead as a
  throughput lever (and was a compound intervention anyway — window, steps, label fraction
  all shift with it; Sol finding 3). What survives of the idea: in a GPU-bound regime,
  *phase-dependent self-play budgets at equal mean sims cost roughly equal FLOPs* — but that
  needs `selfplay_cont` surgery (games migrating between per-budget pools), not a flag.
- `runs/probe_b8.out`: 8×128 at 4096 games → 1630 pos/s = 1.36× the cost of 6×128 (matches
  the 1.33 FLOP ratio; fully GPU-bound). A 150-iter 8-block run ≈ 6.1 h.
- `runs/plan4_checks.out`: (a) orientation robustness — the paired suite replayed with a
  random non-identity D4 image per opening (`runs/openings_v1_rotcheck.npz`, diagnostic
  only) gives wide128_c1 vs v2b **60.3 % [57.6, 63.0]** against the canonical 60.9 %
  [58.2, 63.5]: the canonical-orientation bias Sol's finding 6 posits is ≤ ~0.6 points —
  real concern, negligible magnitude, no yardstick change needed. (b) FLOP-matched play —
  wide128_c1@64 scores **35.9 % [33.2, 38.5] = −101 Elo** against v2b@256 (4× sims offsets
  4× width): at equal inference FLOPs the small net + deep search wins decisively.

## 2. Review adjudication (what was accepted, what was not)

Sol's 16 findings (`REVIEW-sol.md`) vs my independent pass (`REVIEW-claude.md`):

**Accepted and acted on** — provenance/git (S4), `net_0150` hardcodes (S15=C2), the 8192
compound-intervention critique (S3=C1/C4, settled by the probe), `cap_hits` capture (S11,
part), puzzles overwrite trap (C9), atomic saves (C3), config clobber on resume (S4, part).

**Accepted as wording/claim corrections** (PLAN3 §1/§6 are corrected *here*, the files stand):
- "Width scaling has not flattened" **overclaims** (S2). By the project's own ±3-point rule,
  only the endpoints are resolved: 6×64→6×128 at c_scale 1 is +5.1 points [+1.2, +9.1]
  (paired per-opening deltas); the adjacent steps +2.7 (64→96) and +2.5 (96→128) are inside
  the noise band. Correct statement: *the endpoint trend is positive; adjacent increments
  are unresolved; no wide run has a seed replicate.*
- "Strongest net" means **strongest at equal sims**, not equal compute (S1). Confirmed
  directly: v2b@256 beats wide128_c1@64 by +101 Elo at matched inference FLOPs
  (`runs/plan4_checks.out`). This does not
  undermine width for *training* (the 6×64 recipe plateaued across 4 runs — capacity was
  binding there), but deployment/best-play claims must quote the budget, and the CodinGame
  port should be sized by batch-1 latency, not by the ladder.
- The phased-search "+50 Elo at equal mean cost" is equal cost only for ~48-ply games;
  longer games get up to +20 % more sims under "0:32,24:96" (S12). Mostly a real schedule
  effect (game-length-weighted extra sims ≈ +3–5 % ≈ +5 Elo), but re-tune §6.3's play
  config under a per-move budget, which is the deployment constraint anyway.
- The suite's pooled "overall" mixes designed strata (S5): keep using it as the fixed index
  it is, but quote `natural` alongside (both are already in every `paired_*.json` and the
  `suites_*` log keys). The endgame set is a *development* set after 15 in-run reads per
  run (S14): fine for curves and recipe ranking; build any confirmation set fresh (§4.5).
- Exact-label negative ⇒ "capacity/representation" was too strong (S8): the experiment rules
  out label correction, not data-mixture/loss-weighting explanations of draw blindness. The
  cheap discriminating test (overfit a 6×64 on balanced exact endgames) is listed in §4.5;
  still irrelevant for Elo (search solves the endgame in play).

**Rejected / deferred, with reasons:**
- Hot-path micro-optimizations — redundant `legal_mask`, aux heads in inference, fp32
  encode (S9): real but ~1–3 % where it matters; the regime is conv-FLOP-bound at wide128
  and the redundant ops live inside already-captured graphs (launch cost zero). Not worth
  the regression risk now; revisit only if a profile ever shows otherwise.
- Dense-tree redesign / leaf bucketing / evaluation cache (S11): the fixed-slot design is
  what makes CUDA graphs possible; memory is a non-issue at 4096 games (~0.6 GB of 24).
- Structured/D4-equivariant architecture before more depth (S13): legitimate branch,
  wrong priority for a codebase with a working, unexhausted scaling lever and a 5-9 h run
  budget. Parked in §4.6.
- Full manifest/DVC apparatus, hierarchical seed-level bootstrap machinery (S2/S4): the
  proportionate versions were done (git + provenance + replicates in §4); the rest is
  process overhead a two-GPU solo project does not need yet.
- Replay-buffer incremental hashing, async checkpoint writer (S10): `t_iter` now measures
  the overhead directly; act only if it shows up (>5 % of an iteration).

## 2b. Incident 2026-08-30 night: both queue4 runs killed by GPU faults during in-run eval

`deep8_c1` (iter 79) and `wide128_c1_s96` (iter 29) both died with `CUDA error: an illegal
memory access` at `graph.replay()` inside `evaluate()`'s paired matches; the Windows event
log has an `nvlddmkm` id-153 driver fault at each crash time (23:08, 23:50) — the first GPU
faults in ~30 h of training on this stack. The new element that night: the third anchor made
every evaluation create and destroy **4** CUDA-graph-capturing search objects (plus a
batch-3000 endgame search), instead of 3. Root cause not proven (torch/driver race under
graph churn vs. marginal hardware under this load); response covers both:

- **`EvalKit`** (train2): all evaluation players and the endgame search are built once per
  run and reused, with the candidate's weights refreshed in place — zero graph churn, and
  evals got ~2× faster after the first (measured 10.3 s → 4.4 s on the smoke test).
  `--eval_graph 0` exists as an eager-eval fallback if a fault ever recurs.
- **Two-file checkpointing**: `latest.pt` (every iteration, no buffer) + `latest_full.pt`
  (every `save_buffer_every`, with buffer, atomic). Resume prefers `latest_full.pt`, so a
  crash costs ≤ 10 iterations — the old single-file scheme had let iters 70–78 overwrite
  the only buffer-bearing checkpoint, making the crashed 79-iteration run unresumable
  (REVIEW-codex finding 4's residual, now actually fixed).
- **`runs/queue4.sh` auto-retries** each run up to 6 times (a fresh process = clean CUDA
  context), gated on the `DONE` marker.

The crashed partials are archived as `runs/*_crash1` (their pre-drop numbers say nothing
about depth/sims — do not read them as results). Queue relaunched with the fixes; a resumed
run's `log.jsonl` may contain a few replayed iteration lines (append mode) — harmless.

## 3. State of the ladder (unchanged from PLAN3 §3, with corrected wording)

Ladder at 64 sims vs v2b (superseding PLAN3 §3's top): wide128_c1 +77 → deep8_c1 +100
(§4.1) → **deep8_c1_300 +211** (§4.2) — current best `runs/deep8_c1_300/net_0300.pt`.
The stacked levers: c_scale 1.0 (+40, free), width (endpoint +5.1 pts), depth (+23),
**duration (+127)**. PLAN3 §2 (measurement kit) and §5 (game beliefs) stand as written,
with one revision: the "draw blindness at every net size" belief — the 300-iteration run
lifted exact-draw recognition from ~55 % to 67.5 % (§4.2), so it was substantially an
optimization/duration artefact, not a representational wall.

## 4. Next steps, in order

1. **Done — queue4 results (2026-08-31, full paired suite, final checkpoints @64):**
   - **A. `deep8_c1`** (8×128, c_scale 1.0): **adopt**. 53.3 % [50.5, 56.0] = **+23 Elo
     [+4, +42] head-to-head vs wide128_c1**; 64.0 % (+100) vs v2b; endgame bests across
     the board (raw WDL 77.6, raw regret 0.064, raw optimal 94.7 %). +3.3 points —
     borderline clear of the ±3 rule, CI excludes zero, every secondary metric agrees.
     Cost 1.36× (≈6.2 h/150 it). **New best net: `runs/deep8_c1/net_0150.pt`.**
   - **B. `wide128_c1_s96`** (final phase at 96 sims): **null**. 50.2 % [47.4, 53.0] vs
     wide128_c1 (+1 Elo); 59.9 % vs v2b ≈ wide128_c1's 60.9 %; endgame unchanged;
     `cap_hit` 0.2–0.4 % at 96/cap 16 (not a truncation artifact). Caveat for any retry:
     the 50-iteration dose sat entirely after the LR drops, where learning is slowest —
     a from-iteration-60 dose would be the stronger test, not currently scheduled.
   - Ladder rewrite: v2b 0 → wide128_c1 +77 → **deep8_c1 +100** (vs v2b, 64 sims).
2. **Done — queue5, the long run (2026-09-01): the biggest single gain of the project.**
   `deep8_c1_300` = deep8_c1's recipe, one change (`--iters 300 --lr_drops 200,280`,
   14.5 h wall incl. one crash-recovery). Full paired suite, `net_0300.pt` @64:
   - vs **deep8_c1** (its 150-iter parent): **67.5 % [65.0, 70.0] = +127 Elo** — duration
     alone, from the later LR drops landing on ~2× the data. Each drop gave a visible step.
   - vs v2b: **77.1 % [74.9, 79.3] = +211**; vs wide128_c1: 71.3 % (+158); vs dev1:
     86.7 % (+326). (Direct +127 vs ladder-difference +111 — usual non-transitivity, CIs
     overlap.) **New best net: `runs/deep8_c1_300/net_0300.pt`.**
   - Endgame: raw WDL **84.0** [82.6, 85.4] (previous best 77.6), Brier 0.221, raw regret
     **0.045**, raw optimal **96.1 %**; search@256 regret 0.001 / 99.9 % optimal. And the
     headline within the headline: **the draw stratum moved — 67.5 %** after sitting at
     ~55 % across every 6-block net and 150-iteration run in the project. "Draw blindness
     is not capacity" (PLAN2 §2i) and the S8 adjudication both get revised: a large part
     of it was *optimization/duration*, not representation, labels, or width.
   - Ops note: one nvlddmkm fault again — in the eval path again (3 of 3 all-time), with
     EvalKit's persistent graphs, so churn is exonerated and the eval-graph configuration
     itself (depth-cap-24 graphs at small batch) is the suspect surface. Recovery worked
     unattended (resume from `latest_full.pt` at iter 99, ≤10 iterations lost). Next runs:
     consider `--eval_graph 0` (~+1.5 % run time) to remove the surface entirely.
   - Open question this result raises: duration is NOT exhausted at 300 — the natural
     next probes are (a) another duration doubling (600 iters, drops ~400/560, ~29 h),
     (b) 10×128 at 300 iters (~18 h), (c) the §3-item seed replicate of this recipe
     (14 h). One change per run; owner's call on which GPU-day to spend first.
3. **Seed-replicate the winner** (3060, overnight, ~2× the 3090 time): the wide runs have
   no replicate and the adjacent-step CIs are unresolved (S2). One replicate of the final
   recipe bounds the seed noise where it is actually being spent.
3b. **Done — next 3090 run chosen** (owner, 2026-09-01): 10×128 at 300 iterations
   (`runs/queue6.sh`, ~18 h, `--eval_graph 0`, `--eval_every 20`, anchors v2b /
   wide128_c1 / deep8_c1_300).
3c. **OWNER DIRECTIVE (2026-09-01): after queue6 and its analysis, PAUSE.** No further
   training runs — no duration-600, no seed replicate — until a full retrospective is
   written: everything done and learned across the project (engineering, measurement
   methodology, training levers and nulls, game knowledge, the review arc). The
   retrospective is the next deliverable after queue6's numbers land.
4. **Best-play configuration — done** (`runs/plan4_retune.out`): phased schedules beat
   uniform 256 at equal mean cost with the new net too — "0:128,24:384" **+26 Elo
   [+8, +43]**, "0:64,24:448" +25 [+7, +42] (both vs deep8_c1_300@256, paired suite).
   **The playing agent is `deep8_c1_300/net_0300.pt` with `--a_sims "0:128,24:384"`**
   (the milder ramp; equal strength, better early-game floor). `web/server.py` still
   takes a flat `--sims` — pass 800 there as before, the schedule is a CLI-match concept.
5. **Analysis second pass** (3060, as PLAN3 §6.5, with the review's upgrades): rerun atlas /
   decision / freemove with wide128_c1; puzzles → `--out suites/puzzles_v2_dev.npz` (v1
   stays frozen); if a confirmation endgame/opening set is built, split by source game
   into dev/test *before* solving (S14) and keep the test half unread until a final
   comparison. Optional, only if draw blindness is ever worth chasing: the 6×64
   overfit-on-balanced-endgames diagnostic (S8).
6. **Parked branches** (in preference order, none scheduled): per-pool phased self-play
   budgets (needs selfplay_cont surgery; equal-FLOP argument in §1); Gumbel target sweep
   beyond c_scale (`c_visit`, `m_considered` — one 6×64 run each on the 3060 if idle);
   replay reanalysis by a stronger teacher; structured/equivariant architectures (S13);
   CodinGame port (batch-1 latency budget first — see §2 on equal-compute).

## 5. Operational notes (deltas to PLAN3 §7)

- Git: repo lives in the project root; `git log` is the run-provenance spine now — commit
  before launching a run so `config.json`'s `_provenance.git` points at real code.
- Train command: PLAN3 §7's line still current, plus `--c_scale 1.0 --filters 128` and the
  third anchor `runs/wide128_c1/net_0150.pt`; see `runs/queue4.sh` for the exact live text.
- `runs/<run>/DONE` marks completion; `eval_run.sh <run> [device]` finds the last
  checkpoint itself. In-run tail in `analysis.out` is the last 30 iterations.
- New log keys: `t_ckpt`, `t_iter` (end-to-end). If `t_iter` exceeds
  `t_selfplay + t_train + t_eval + t_exact_wait` by more than ~5 %, the untimed overhead
  (S10) has become real — look at buffer save and games persistence first.
- The rotated-suite diagnostic and FLOP-matched match live in `runs/plan4_checks.out`;
  `runs/openings_v1_rotcheck.npz` is *not* a yardstick.
- Probes (`runs/probe_g8192`, `runs/probe_b8`) were 3-iteration throughput measurements —
  their nets are untrained garbage; only the `.out` files matter.
- Traps (all of PLAN3 §7's, plus): never write analysis outputs into `suites/`; a resumed
  run now refuses to clobber `config.json` — if you *meant* to change the config mid-run,
  don't (start a new run).
