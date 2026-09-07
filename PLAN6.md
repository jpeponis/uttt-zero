# uttt-zero — PLAN6 (2026-09-06): after the outside review — repair the instrument, then ask the cheap questions first

**What this plan is.** PLAN5 ended with the analysis programme complete, the ladder paused, and
one continuation pencilled in: a 600-iteration run (PLAN5 §5 D2). Before resuming, the owner
commissioned an outside review of how the project is run and how it does and does not use the
game's symmetry (`docs/history/REVIEW-astra.md`, reviewed at commit `e386baa`; its reproduction scripts are
in `docs/history/review_astra/`, run from the repo root). This plan adjudicates that review finding by finding — each accepted, accepted
with a change, or rejected, with the reason verified in the code or the logs — and sets the order of
work that follows from it. The short version: the review found two real bugs in the analysis
instrument and one real confound in how "duration" has been reasoned about; it is right that the
next architectural question should be answered on frozen data before any self-play; and it is wrong,
in a way that matters for how D3 is written up, about why "same-seed" runs diverge. The 600-iteration
run is still on the list, but it is no longer first.

Terms are as in PLAN5's glossary. Rules that hold throughout, unchanged: one change per run against
a named parent; judged on the frozen paired suite by the ±3-point rule, final checkpoints only; no
training run starts without the owner's approval; every claim about the game carries its level, CI,
the nets it held on, and the file that produced it.

## Handover (2026-09-07)

**State (2026-09-07 13:20).** **H1b is running on the 3090:** `runs/deep8_c1_300_e4` (`runs/queue10.sh`, launched
13:15 through `runs/launch_queue10_hidden.vbs`; retry wrapper, 6 attempts) — deep8_c1_300_e2's recipe with
`--epochs 4` (1024 optimizer steps per iteration), `--eval_every 0 --ckpt_every 10 --anchors ""`. Iteration 0: 1024
steps, 0 skipped, self-play 81.5 s + training 61.9 s; `run_status` ETA 07:17 on 2026-09-08 (+17.9 h). The E7 worker
runs beside it on the 3060 (`runs/deep8_c1_300_e4_worker.out`; anchors v2b, deep8_c1_300_e2 (the parent),
deep8_c1_300 at 64 sims on the full suite, endgame_v2_dev → `eval_full.jsonl`). At the end queue10 runs
`eval_run.sh` (which now includes the parent matches `paired_vs_deep8c1_300e2_64.json` and, once it exists, `_e4`)
and the endgame_v2_dev read into `analysis.out`. Status: `python tools/run_status.py runs/deep8_c1_300_e4 --ref
runs/deep8_c1_300_e2`. Watch: a single-shot background `until [ -f runs/deep8_c1_300_e4/DONE ] || grep -q FAILED
runs/deep8_c1_300_e4.out; do sleep 300; done` (the Monitor tool delivers nothing from these files on this machine).

**The owner's decision (2026-09-07): H1b approved, and a conditional pre-approval of the chain H1b → H4 → H3.** The
next run starts without asking *as long as the instance is under 50 % of its context window when it would start it*;
above 50 % it updates everything (this Handover first, then the log, KNOWLEDGE, RETROSPECTIVE, README) and hands over
to the next instance instead of launching. Each result is read by its pre-registered rule and written up before the
next launch. Delegate the write-ups and any file-heavy reading to `directed` subagents (opus) to stay under the line.

Also running on the 3060, launched 13:16 (`runs/plan6/H1_reverify_3060.sh` via `runs/launch_reverify_hidden.vbs`,
≈ 1–1.5 h sharing the card with the worker; no approval needed — play-time measurements on an existing net):
the phased schedule "0:128,24:384" vs flat 256, the 8-way average vs plain @64, and the canonical evaluator vs plain
@64, all on `deep8_c1_300_e2` (PLAN5 A8c / B5 and PLAN6 F1 repeated on the new play agent) →
`runs/plan6/H1_reverify.out`, `runs/deep8_c1_300_e2/paired_{phased_vs_256,sym_vs_plain_64,canon_vs_plain_64}.json`.
Readings by the ±3 rule; KNOWLEDGE 45 / 41 / 41b each get a sentence.

The play agent is `runs/deep8_c1_300_e2/net_0300.pt` (+291 vs v2b; the log's H1 entry). Phase G is complete,
including the one sealed test read. The G-CNN was smoke-tested through the self-play pipeline on 2026-09-07
(`runs/probe_gcnn_smoke`, untracked, an untrained net: 4 iterations of 256 games on the 3060 — fused graph self-play,
50 training steps per iteration with falling losses and no skipped steps, atomic checkpoints, a resume that restored
the scaler and generators, and the E7 worker scoring its checkpoints against a ResNet anchor with the endgame set), so
H4 is launchable as written. E11 (backup) stays deferred by the owner to the write-up; the repository has no remote.

**The chain, with the recipes fixed by the rules already written.** Operational settings for every run: copy
`runs/queue10.sh` (retry wrapper, `--eval_every 0 --ckpt_every 10`, the E7 worker on the 3060 with the parent among
its anchors, `eval_run.sh` + the endgame_v2_dev read at the end), a `launch_queue<N>_run.cmd` and
`launch_queue<N>_hidden.vbs` (sed the names), launched with `wscript runs/launch_queue<N>_hidden.vbs` from the repo
root; the trainer must never share the 3090 with anything. Every reading: the *final* checkpoint on the full paired
suite @64 against the named parent — ≥ 53 % helped, ≤ 47 % hurt, otherwise null — with the seed band (≈ 3 points)
stated beside it. E below is the epochs the chain carries forward.

1. **H1b `deep8_c1_300_e4` — running.** Primary `paired_vs_deep8c1_300e2_64.json`: **≥ 53 → still update-limited,
   E = 4** (and an `--epochs 8` run is worth proposing after the chain); **47–53 → epochs 2 is the plateau, E = 2**;
   **≤ 47 → over-fitting the 7.6-iteration buffer window, E = 2**, and the buffer size (not the update count) is the
   knob to propose after the chain. Secondary: vs deep8_c1_300, deep10_c1_300, `_s1`, v2b (all in `analysis.out`);
   the E7 curve against H1's (`runs/deep8_c1_300_e2/eval_full.jsonl`; H1 vs v2b: 10: 20.1, 50: 52.1, 100: 68.8,
   150: 75.5, 200: 75.9, 210: 82.2, 220: 83.4, 260: 84.2, 280: 84.9, 300: 84.2); the budget axes (E8: steps skipped,
   replay age, the sampled distinct-position fraction — H1: 3.35 iterations, 0.81 → 0.75, 70 of 153 600 skipped).
   Tertiary: endgame_v2_dev raw WDL / regret vs 87.5 / 0.034 (endgame_v1 87.6 / 0.036). Write-up: a new KNOWLEDGE
   claim 49 (and 46's last sentence), RETROSPECTIVE §2 ladder / §3 ledger / §7, README state and ladder, this log;
   the play agent changes only if H1b helped.
2. **H4 `gcnn8_c1_300_e<E>`** — `--gcnn 16 --filters 128 --blocks 8 --epochs <E>`, everything else as H1; parent
   the chain's best 8-block net at epochs E (`deep8_c1_300_e4` if E = 4, else `_e2`). ≈ 15–17 h. Worker anchors:
   v2b, the parent, deep8_c1_300. Primary vs the parent at 64 sims (equal inference cost by construction, so one
   comparison serves both of §5 H4's requirements); secondary the D4 residual (0 by construction — `timeline.py`'s
   D4 JS column should read 0.000) and the endgame reads. `--head_tying 1` on the plain trunk is the fallback if the
   G-CNN misbehaves in RL (diverging losses, many skipped steps). The first play agent with exact symmetry if it wins.
3. **H3 `deep8_c1_600_e<E>`** — `--iters 600 --lr_drops 500 --epochs <E>`, everything else as H1; parent the same
   net as H4's. ≈ 30–35 h (late iterations run ≈ 15 % slower than the mean). Reading: the E7 full-suite curve from
   300 to 500 — flat means duration is exhausted at this data rate, climbing means it is not — and the final net by
   the rule against the parent. `eval_run.sh` discovers the last `net_*.pt`; the queue's endgame_v2_dev line must say
   `net_0600.pt`.

Not proposed: H2 (the mask; its supervised gain is real but small — 0.008 in KL — and the licence it buys has no
consumer yet); a 10-block anything (46, 48); self-play on the 3060 (§6).

## Log

- **2026-09-06, E1.** `uttt/openings.py` gained the group tables (`compose`, `inverse`,
  `transform_move`, `canonicalise` → (key, g), `reply_orbits`). A book node's replies are now orbits
  (representative = the orbit's smallest member; for a canonical parent that is exactly the member whose
  sequence *is* the child's canonical key, so the edge transform is the identity by construction and
  every line stays in its first move's frame — the general composition is kept in `principal_line()` and
  the stored transforms are audited). `tools/book.py audit()` checks every book it builds (members legal,
  transforms map onto the child, children distinct, every principal line legal and canonicalising to the
  node it passes through); `tests/test_book.py` builds a small book on the CPU, audits it, and checks the
  audit catches both review bugs. Both books rebuilt (deep10 28 min on the 3090, deep8 38 min on the 3060,
  both audit-clean): **579 nodes each (was 459), 430 shared (was 341)**; after [40] the corner orbit is
  now expanded (+0.02 better for X than the edge reply on both nets; deep10 puts 0.75 of its root visits on
  the edges, deep8_300 0.54). Agreement on the top reply orbit **75 % (321 / 430)**, 98 % where the top
  orbit carries ≥ 0.9 of the visits, 35–46 % below 0.7. Self-send: 55 / 58 % (was 52 / 57).
  KNOWLEDGE 7, 7a restated. `runs/plan6/E1_*`.
- **E2.** `tools/atlas.py`: the in-tree gap is between the two most-visited reply *orbits*; `--report`
  re-reads a saved atlas. From `runs/plan5_A1_atlas.json` (child-root values): deep10@16k gap ≤ 0.03
  after 12 / 15 first moves (deep8_300 10, v2b 14); best-to-worst reply-orbit range median 0.11, 0.07–0.19
  except [40] (0.02). The [40]-reply exceptions: [13] 0.102, [4] 0.053; [37] 0.037 at the edge.
  `runs/plan6_E2_atlas_orbits.out`. KNOWLEDGE 4, 5 restated.
- **E3.** Done as listed in §2 (KNOWLEDGE header + rules, 4, 5, 7, 7a, 8's unit, 9, 20, 28, 40 (from E9),
  41, 42, 43; RETROSPECTIVE §3, §5, §7; README; explainer Part 8). No number moved except the book's.
- **E4.** `BatchedSearch(..., generator=)`, `ContinuousSelfPlay(..., generator=)`,
  `GPUReplayBuffer(..., generator=)`, `symmetrise(..., gen)`; a deterministic search draws nothing;
  `load_checkpoint` under `fork_rng`; evaluation additionally under `fork_rng`. `tests/test_rng_hygiene.py`:
  an evaluation between two iterations — even one that draws from the global RNG — changes no training
  draw; the pre-E4 idle draw would have. Golden tests (v1 = v2 trees, eager = graph) still pass.
- **E5.** Both checkpoint files carry `scaler`, `rng` (three generators + the exact labeler's) and
  `attempt`; `net_NNNN.pt` atomic; `--ckpt_every` (0 = at every evaluation, the old behaviour); resumes
  print "attempt N: a perturbed continuation".
- **E6.** `tests/test_symmetry.py`: engine commutation over 70 random plies (free moves, closures, count
  endings seen), encoder equivariance + colour-relabelling invariance, both exact evaluators' heads
  (invariant value, equivariant policy, constant on orbits at the empty board and after [40]), the
  canonical evaluator on the fused fp16 net under graph replay (bitwise identical across the 8
  orientations), deterministic search on the exact evaluator commuting as a distribution (100 % of 128
  positions). Passes on CPU and cuda:0.
- **E7.** `tools/eval_worker.py`: watches `net_NNNN.pt`, full suite vs anchors at 64 sims + endgame set,
  `eval_full.jsonl` with hash and settings, newest-first while live, backfills after DONE, `--once`.
  Measured: 55–66 s per full-suite match on the 3090 (the ≈ 2–3 min estimate was for the 3060).
  `tools/timeline.py` overlays the full-suite points with error bars.
- **E8.** Per iteration the log now has `rows_sampled`, `steps` (taken) and `steps_skipped`,
  `teacher_step`, `replay_age`, `sample_distinct_frac`, `target_entropy`, `raw_kl`, `q_range`, `attempt`.
  Replay pre-draw (`sample_batches`) in.
- **E9.** `tools/ownership_grade.py`. On open boards only, the head is at 51 % overall (majority 40,
  local logistic 48, trunk probe 49, random-trunk probe 47) and the gap opens with the ply: ≤ 2 points
  over local / random before ply 32, +6 at 32–43, **+18 at 44+ (68 vs 50 / 50)**; deep8_300 the same
  shape (66 vs 51 / 54). KNOWLEDGE 40 restated: the head learns late-game ownership that neither local
  features nor a random trunk carry; that knowledge did not translate into strength.
- **E10.** `suites/endgame_v3_{dev,test}.npz` from `deep10_c1_300_s1` games 280–299 (split by game
  before solving; `tools/endgame.py build --split dev,test`); overlap by `tools/suite_overlap.py`
  (`runs/plan6/E10_overlap.out`): 3000 + 3000 positions, balanced 125 per stratum, 2924 / 2933 source games,
  **0 shared canonical positions and 0 symmetric duplicates within either half**. `_test` is sealed until the end
  of Phase G; `_dev` is the development set for every net except `deep10_c1_300_s1` (its own games).
- **E11.** Not done: needs an off-machine destination from the owner.
- **F1.** deep10 canonical @64 vs deep10 plain @64, full suite: **49.5 % [46.7, 52.3], −3 Elo
  [−23, +16]** — null by the pre-registered rule, as predicted. KNOWLEDGE 41b.
  `runs/deep10_c1_300/paired_canon_vs_plain_64.json`.
- **F2.** Full-suite score vs v2b @64 (±2.8) by checkpoint, through the E7 worker on the 3090 (≈ 1 min per
  match; `runs/<run>/eval_full.jsonl`, `runs/plan6/F2_second_drop.out`):

  | run | 200 | 220 | 260 | 280 | 300 | first drop (220 − 200) | second drop (300 − 260) |
  |---|---|---|---|---|---|---|---|
  | deep8_c1_300 | 67.7 | 76.2 | 74.5 | 76.4 | 77.1 | **+8.5** | +2.6 |
  | deep10_c1_300 | 73.1 | 77.9 | 76.0 | 79.8 | 80.1 | **+4.8** | +4.1 |
  | deep10_c1_300_s1 | 69.0 | 75.6 | 77.7 | 75.3 | 77.3 | **+6.6** | −0.4 |
  | deep10_c1_300_lr150 (drops 150/250) | 150: 66.7 | 160: 72.6 | 240: 75.5 | 250: 72.4 · 260: 78.2 | 75.2 | **+5.9** (160 − 150) | −0.3 (300 − 240) |

  **Pre-registered reading: the second drop does nothing resolvable** — 300 − 260 ≥ 3 points on one run of
  four (the rule asked for three). The first drop is a resolved step on every run at ±2.8 (+4.8 … +8.5,
  median +6). Two things the in-run curves could not show: checkpoint-to-checkpoint wobble at a constant
  LR is itself ≈ ±3 points on the full suite (s1: 77.7 → 75.3 → 77.3 across 260/280/300; lr150: 75.5 → 72.4
  → 78.2), so a single-checkpoint 3-point criterion sits at the noise floor and "flat after 220" means
  "inside ±3", not "constant"; and the in-run ±6 reads missed by up to 4 points (s1 at 280: 79.5 in-run,
  75.3 full). **Consequence for H3:** a second drop earns nothing measurable; H3 is written with one drop
  (`--lr_drops 500`), and the final 20 iterations at the low LR are its settling time, not a second step.
  KNOWLEDGE 42 carries the numbers.
- **F3.** Recorded in KNOWLEDGE §10.
- **2026-09-07, H1 — `deep8_c1_300_e2` (owner-approved 2026-09-06, launched 18:51, finished 09:39 after
  14.6 h, 0 crashes).** deep8_c1_300's recipe with `--epochs 2` (512 steps of batch 1024 per iteration),
  `--eval_every 0 --ckpt_every 10`, the E7 worker scoring every checkpoint on the full suite. **Primary: 64.0 %
  [61.4, 66.5], +100 Elo [+81, +119] vs deep8_c1_300 — helped, by 11 points over the rule.** Secondary: 62.1 %
  [59.6, 64.6], +86 vs deep10_c1_300 and 63.6 % [60.9, 66.3], +97 vs its replicate — extra updates alone beat
  the depth step at equal sims (and at equal compute: 0.81× the cost per evaluation); 84.2 % [82.2, 86.2],
  +291 [+266, +318] vs v2b. The full-suite curve (`eval_full.jsonl`, ±2.8, every 10 iterations):

  | iteration | 10 | 50 | 100 | 150 | 200 | 210 | 220 | 260 | 280 | 300 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | H1 vs v2b | 20.1 | 52.1 | 68.8 | 75.5 | 75.9 | 82.2 | 83.4 | 84.2 | 84.9 | 84.2 |
  | deep8_c1_300 vs v2b (full suite where read, else in-run ±6) | 11.9 | 43.3 | 52.8 | 62.5 | 67.7 | 77.0 | 76.2 | 74.5 | 76.4 | 77.1 |
  | H1 vs deep8_c1_300's final net | 7.7 | 24.6 | 39.6 | 44.1 | 48.0 | 55.2 | 58.8 | 62.1 | 63.7 | 63.9 |

  The constant-LR climb is lifted by 8–13 points throughout; at iteration 200, before its own drop, H1 is
  even with the reference's *final* net; the first drop adds the usual ≈ +7; 220–300 is flat within ±3; the
  second drop nothing. Tertiary: endgame_v2_dev raw WDL 87.5 [86.3, 88.6] / regret 0.034 vs 83.5 / 0.050
  (deep8_300) and 84.7 / 0.048 (deep10); endgame_v1 87.6 / 0.036, draws 74.8 %. Budget axes (E8): replay age
  3.35 iterations, sampled distinct-position fraction 0.81 → 0.75, policy-target entropy 0.15 bits, raw/search
  KL 1.22 → 0.84, root Q range 0.39 → 0.46, 70 of 153 600 steps skipped; self-play games 52.5 plies (51.9),
  draws 15.5 % (13.0 %). Cost: t_train 2.55 h vs 1.26 h; wall 14.6 h vs 14.2 h. **Reading: the learner was
  update-limited; H3 is written with H1's epochs — and the cheaper question comes first (Handover).**
  KNOWLEDGE 46; RETROSPECTIVE §2, §3, §7; README. The play agent changes to `deep8_c1_300_e2/net_0300.pt`.
- **G0 (19:00–19:29, 3060).** ResNet 8×128 on `gdata_v1`, 50k–400k positions × 1–8 passes: the dev KL is a
  function of the step count alone (384 steps: 1.188 / 1.187 / 1.182 / 1.183 for 50k×8 / 100k×4 / 200k×2 /
  400k×1; 780: 1.082 / 1.076 / 1.075; 1560: 0.976 / 0.973; 3120: 0.884, still falling). KNOWLEDGE 47.
- **G arms (19:29–21:30, 3060; two seeds each at 400k × 8 = 3120 steps).** KL: resnet8 0.8839 / 0.8853;
  resnet10 0.8820 / 0.8803; resnet8_mask 0.8769 / 0.8739; **resnet8_tied 0.8480 / 0.8462; gcnn8x16 0.8057 /
  0.8066** (D4 residual exactly 0; 312 k parameters; the same inference cost). Arms (d) and (e) were
  implemented the same evening (`uttt/equivariant.py`: `TiedLinear` over the 861 / 15 / board-orbit weight
  classes; `GConv2d` regular-representation group convolutions with orientation-shared BatchNorm; both
  export to plain `Conv2d` / `BatchNorm2d` / `Linear` at fusion time so the fused fp16 graph path is
  untouched — `tests/test_equivariant.py`: exact laws at init and after training, export exact, fused fp16
  to 8e-5). Isolated inference cost (`tools/gtiming.py`; the queue's own timings were contaminated by the
  E7 worker on the same card): 3090, ms per 4096 evaluations — resnet8 33.2, resnet8_mask 33.2,
  resnet8_tied 33.3, gcnn8x16 33.6, resnet10 41.1; batch 1: 0.41 / 0.42 / 0.44 / 0.42 / 0.49 ms.
  **Gate (i) on the dev slice: resnet8_tied and gcnn8x16 pass at equal cost; resnet10 and resnet8_mask do
  not beat the ResNet's seed spread by enough to matter** (the mask: −0.008 in KL, real but small).
  KNOWLEDGE 48. *Artefact found and fixed:* the mask arm's endgame WDL came out at 48–51 % because
  `uttt.endgame.wdl_probs` encoded the set without the net's mask (fixed; the same fix in `tools/calibrate.py`,
  `probe.py`, `ownership_grade.py`); its regret (0.152, through the evaluator) was right. Rerun in queue 3.
- **G queue 3 (11:00, 3060):** the mask arm again with the fix, and the sample-efficiency points of gate (ii)
  for the two winning arms (100k × 8, 200k × 8, 400k × 4; students saved under `runs/plan6/students/`).
  (11:25) the mask arm with the fix: endgame WDL **67.2 / 67.3 %** (ResNet 64.4 / 65.3) — its value head is
  in fact slightly better, KL and regret unchanged (0.8769 / 0.8739; 0.152). Sample-efficiency points (dev KL;
  the ResNet's own G0 points in brackets): gcnn8x16 100k × 8 = 776 steps **0.969** [ResNet at 780 steps 1.08],
  200k × 8 = 1560 steps **0.880** [0.976], 400k × 4 = 1560 steps **0.856** [0.973]; resnet8_tied 1.022 / 0.931 /
  0.921. **Gate (ii) — the ResNet's 400k × 8 KL (0.884) reached with half the data (200k × 8: 0.880) or half the
  steps (400k × 4: 0.856) — passes for gcnn8x16 and fails for resnet8_tied.** A second thing the points show:
  for the G-CNN the fit at equal steps is *not* a function of steps alone (0.856 vs 0.880 at 1560 steps with 2×
  vs 1× the distinct positions), where the ResNet's was (0.973 vs 0.976) — the equivariant net extracts more per
  update and is the first student here that is partly data-limited.
- **G queue 4 — the sealed test read, once:** every arm at 400k × 8 seed 0 on `--split test`. Result:
(12:00, 400k × 8, seed 0; test KL with the same student's dev KL in brackets): resnet8 **0.8851** [0.8839],
  resnet10 0.8818 [0.8820], resnet8_mask 0.8763 [0.8769], resnet8_tied **0.8483** [0.8480], gcnn8x16 **0.8063**
  [0.8057]; top-1 0.551 / 0.550 / 0.555 / 0.563 / 0.602; exact 3-way 0.755 / 0.756 / 0.770 / 0.778 / 0.800;
  endgame_v2_dev regret 0.164 / 0.161 / 0.152 / 0.148 / 0.152. Test agrees with dev to within 0.0012 on every
  arm: the ordering, the gate readings and the sizes of the gaps stand as read on dev. `endgame_v3_test`
  was **not** opened (the students were graded on `endgame_v2_dev`; `_v3_test` stays sealed for a net that
  is not a supervised student). Phase G is complete; the 3060 is idle.

- **2026-09-07, 13:15 — H1b launched; the G-CNN smoke-tested; the re-verifications started.** Preflight: both cards
  idle, git clean, `tests/test_equivariant.py` passes on the 3060. `runs/probe_gcnn_smoke` (untracked; an untrained
  net): `train2 --gcnn 16 --filters 128 --blocks 8 --epochs 2` for 4 iterations of 256 games × 64 steps on the 3060
  — fused graph self-play (13–29 games/s at that batch), 50 steps per iteration with the losses falling
  (policy 4.18 → 1.98) and none skipped, `net_NNNN.pt` written atomically, a resume that restored the scaler and the
  generators, and `tools/eval_worker.py --once` scoring the four checkpoints against v2b with the endgame set. H4 is
  launchable. The owner approved H1b and the conditional chain (Handover). `runs/eval_run.sh` gained the parent
  matches vs `deep8_c1_300_e2` and `_e4`. H1b (`runs/queue10.sh`) launched 13:15 through the hidden launcher, the
  worker with it (iteration 0: 1024 steps, 0 skipped, self-play 81.5 s, training 61.9 s; ETA 07:17 on 2026-09-08);
  the three re-verifications on `deep8_c1_300_e2` (`runs/plan6/H1_reverify_3060.sh`) at 13:16 on the 3060.

## 0. The decision in front of the project

**Three things "more strength" could be for, and they call for different work.**

1. *Game knowledge* (the README's stated purpose). PLAN5 Phase A showed every ordering and sign
   stable across 340 Elo and the magnitudes saturated between deep8_300 and deep10 (the resume
   criteria did not fire). More Elo does not change what can be claimed. What does: repairing the
   two instrument bugs the review found (they touch claims 4, 7 and 7a), tightening seven
   over-statements (§2 E3), and extending *exact* knowledge (the two-open-board frontier, C5).
2. *The science of learning* — why 300 iterations beat 150 by +127, what an LR drop does, whether
   the network's architecture matters for sample efficiency, whether exact symmetry helps a learner.
   These are answerable, and mostly cheaply: on frozen data (Phase G) and with one 14-hour run that
   isolates the cheapest arm of the duration confound (H1).
3. *A deployable bot* (CodinGame). Then strength at a fixed *inference budget* is the goal, the
   instrument is batch-1 latency, and duration on 8 blocks is the lever (PLAN5 A8b: 8 → 10 blocks
   bought nothing at equal compute). This goal has never been stated by the owner; nothing here
   assumes it.

**Why the 600-iteration run is no longer first.** The review's §6.3 puts a finger on something the
project's own numbers support: an "iteration" is 262 144 new positions *and* 256 optimizer steps
over 262 144 sampled rows from a 2 M-row buffer that spans ≈ 7.6 iterations. `--epochs 1` means one
expected use per generated position, not one pass over the buffer; under uniform sampling ≈ 37 % of
rows are evicted unsampled (the real weights change this — `docs/history/review_astra/replay_audit.json`).
Doubling duration therefore doubles data, doubles updates, changes the teacher and moves the LR
phases, all at once. The project has never separated these. A 600-iteration run costs ≈ 27 h and
would not separate them either. A `--epochs 2` run at 300 iterations costs ≈ 14 h (training is 8 %
of wall-clock — `t_train` 1.2 h of 13.8 h on deep8_c1_300 — so doubling it adds ≈ 1.2 h) and answers
"is the learner update-limited?" directly. If it is, the 600-iteration run should be run with the
extra updates, or not at all; if it is not, the 600-iteration run is the right next test and its
result is interpretable as data/teacher-limited learning. That ordering is the core recommendation.

**Recommendation.** Repair the instrument (E), take the hour of cheap measurements (F), start the
frozen-teacher study on the 3060 (G), and propose H1 (`--epochs 2` on 8 blocks) to the owner as the
first run. The 600-iteration run (H3) follows H1's result. No equivariant or relational architecture
enters self-play until it has beaten the plain ResNet on frozen data by a pre-registered margin (G's
gate). The play agent does not change.

## 1. The review, adjudicated

Each row: the review's item, the verdict, the reason (verified in the code or the logs, with the
location), and where in this plan it lands. "Accept" means the plan does it; "accept with change"
means the finding stands but the remedy or the reading differs; "reject" means the evidence does not
support it.

| # | review item | verdict | evidence / reason | lands in |
|---|---|---|---|---|
| 1 | Opening-book principal lines mix coordinate frames (§4.1) | **accept** | `tools/book.py principal_line()` follows `best["child"]`, a *canonical* key, and appends `best["move"]`, which is in the *parent's* frame; the child's own moves are in the child's canonical frame. `docs/history/review_astra/book_audit.json`: one illegal displayed line per book (`[0, 6, 20, 23]` in deep10's, `[40, 41, 10, 16]` in deep8's). The stored nodes are fine; the display column is wrong. | E1 |
| 2 | "Top-3 replies" can be one orbit three times (§4.2) | **accept** | After [40], deep10's top three by visits are 37 / 39 / 41 — all canonicalise to `40 37`; deep8's 41 / 43 / 37 likewise. 28 (deep10) / 29 (deep8) nodes have duplicate child orbits. Consequence beyond display: the corner-reply subtree after [40] (`40 36`) was never expanded, so the book is missing lines it advertises. | E1 |
| 3 | The cited disagreement "deep10 plays 37, deep8 plays 41 after [40]" is a symmetry copy (§4.3) | **accept** | Same orbit. Agreement on canonical children is 258 / 341 (75.7 %), not 256 / 341 (75.1 %). Claim 7's example is wrong; its number barely moves. | E3 |
| 4 | The atlas root Q-gap compares two individual actions that may share an orbit (§4.3) | **accept** | `tools/atlas.py deep_values()`: `top2 = N0.topk(2)` over 81 actions. The two most-visited replies are in one orbit after [0], [8] and [40]. Recomputed from the atlas's separately searched reply orbits: the two best *distinct* orbits are within 0.03 in 12 / 15 first moves, but the best-to-worst reply-orbit range is 0.07–0.19 except after [40] (0.02). Claim 4 ("the choice of reply hardly matters") is restated as "there are usually two or more comparably good replies; the worst reply is clearly worse". | E2, E3 |
| 5 | The spatial group is the diagonal D4; independent local rotations, board permutations and the (b, c) swap are not symmetries (§3.1) | agree, nothing to change | Established at the start (knowledge/02 §3.4) and implemented in `uttt/batch.py`; the review's exhaustive check (8 automorphisms, 15 first-move orbits, 861 ordered-pair orbits) confirms it. | — |
| 6 | Stabilisers: after [40] no deterministic equivariant move selector exists; tests must compare distributions or orbits (§3.3) | **accept** | Correct, and a useful rule for how equivariance tests are written (compare orbit masses at [40] and the empty board, not argmaxes). | E6 |
| 7 | Closed-board interiors are irrelevant to the continuation; mask them (§3.4) | **accept as a candidate** | A true state abstraction: once a board is closed its cells affect nothing. The net's measured sensitivity to them (0.061 mean absolute value change, 3.9 % of argmaxes on 311 edited positions) is a diagnostic on out-of-distribution inputs, not evidence of harm. A one-line change to `encode()` (zero planes 0–1 where the board is closed; the macro planes carry the status). Test supervised first, then as a run. | G arm, H2 |
| 8 | D4 augmentation is already on; PLAN5 B5's wording implies it is not (§5.1) | **accept** | `train2.symmetrise()` applies an independent random D4 element to every sampled example. PLAN5 B5's "the buffer is not symmetrised" is true of the *buffer* and misleading about *training*; restate: the data is augmented, equivariance is not enforced, and 0.027 bits of residual policy asymmetry remain. | E3 |
| 9 | One-call canonical evaluator: exact equivariance at +2.6 % cost (§5.2) | **accept as a control; measure at play** | The review's prototype is exact (zero error on 256 states × 8 transforms, stabiliser at [40] handled) and costs 7.26 vs 7.07 ms at batch 256 on the 3060; on the endgame set it *loses* 0.5 points of raw-policy optimality (96.13 vs 96.67 %) — canonicalisation picks one orientation's errors, it does not average them. Whether that is worth anything at play is a 10-minute paired match (F1). Prediction: null. | F1 |
| 10 | A D4 group-equivariant CNN is "the next useful architectural experiment" (§5.3) | **accept as a supervised arm; reject the priority** | The "removes a nuisance variable from the instrument" argument is weak: every analysis tool already uses the exactly equivariant 8-way average (`uttt/symmetry.py`), and item 9 gives an exact one-call version. The inductive-bias argument is real but empirical, and it is answerable on frozen data for no GPU-days (G). The engineering cost is understated: the fused inference path (BN folding, fp16, channels_last, CUDA graphs) is what the throughput rests on; a new model class must reuse it. §4 says how (weight-expanded ordinary convolutions). | G |
| 11 | A local-boards / macro-lines / routing relational model (§5.4) | **accept as a later arm** | Its real case for this project is legibility — per-board and per-line features are what the probes look for by hand. It is a research project with unknown wall-clock cost and unproven expressiveness (the review says so). Behind G's gate; dense, fixed-shape, graph-capturable or not at all. | G (optional), H4 |
| 12 | Tests that make "respects symmetry" checkable (§5.5) | **accept** | Cheap; the list is right (transition commutation, encoder, heads after fusion / fp16 / graph capture, stabiliser positions, transported-noise search, canonical overlap between splits). `tests/test_symmetry_eval.py` covers one of these today. | E6 |
| 13 | Evaluation advances the training RNG; D3 diverged from its reference before the LR intervention (§6.1) | **accept the fix; reject the reading** | The draw is real: `uttt/search.py:258` draws `torch.rand(n, 81)` in Gumbel mode and multiplies by zero when not self-play; `symmetrise` and the buffer's `torch.multinomial` use the global generator. But the divergence has a different cause. D3's iteration 0 is *identical* to the reference (205 460 positions, 3848 games, the same statistics), its iteration-0 losses differ at the fourth decimal (2.5373 vs 2.5374 — `cudnn.benchmark = True`, fp16 autocast), and by iteration 1 the self-play differs (243 072 vs 226 202 positions) — before any evaluation has run (the first is at iteration 10 / 20). This pipeline is not bitwise deterministic and a 4096-game self-play loop amplifies a last-bit difference within one iteration. **Same seed does not mean same trajectory here, and RNG bookkeeping cannot make it so.** The defence is replication, which the project has (four 300-iteration runs). The D3 write-up is restated (E3): one perturbed run against two reference seeds, "hurt" by its pre-registered rule, with the seed band as the yardstick. | E4, E3 |
| 14 | `latest_full.pt` is recovery-capable, not continuation-complete (§6.2) | **accept in part** | Verified: it holds `net, opt, buffer, iter, global_step, cfg` — no RNG states, no GradScaler state, no in-flight games. Add the scaler and generator states (cheap) and atomic writes for `net_NNNN.pt` (`train2.py:325` writes it directly — needed once something else reads those files). Do not promise reproducible continuation (item 13); keep labelling resumes as perturbed (the `config_resume_*.json` records already do). | E5 |
| 15 | Define the data / update budget; "duration" confounds four things (§6.3) | **accept, strongly** | The most decision-relevant point in the review; §0 above. `n_steps = epochs × games × steps / batch` = 256 (`train2.py:301`); the `--epochs` knob is the cheap in-pipeline arm. Log the axes; run H1. | E8, H1, G0 |
| 16 | Buy better policy supervision (reanalysis, deeper targets, middlegame mixture, playout-cap randomisation) before more games (§6.4) | **accept the instrumentation; defer the rest** | Log Q-range, target entropy and raw/search KL per iteration (E8). G's teacher targets are the cheap version of "deeper targets". Playout-cap randomisation fights the fixed-shape graph path, as the review itself notes — not now. | E8, G |
| 17 | Grade the ownership head on open boards only, by phase, against a status baseline (§6.5) | **accept** | An hour; clarifies claim 40. | E9 |
| 18 | GPU roles: the 3060 as an out-of-process evaluator; no DDP; no self-play on the slower card (§7) | **accept, with a larger payoff than stated** | The review counts ≈ 1.1 h saved per run. The bigger gains: (i) the in-run evaluation, where all three driver faults happened, leaves the trainer entirely; (ii) every checkpoint can be scored on the *full* suite (±2.8) instead of 100 openings (±6), which is the instrument the timeline questions (the second drop, "flat after 220") actually need. | E7, F2 |
| 19 | Channels-last training is 4× slower here; replay pre-draw saves 0.2 %; persistence is already small (§7.5) | **accept** | Leave the training layout; pre-draw is a maintenance change; no buffer database. | E8 note |
| 20 | `torch.cuda.graph` caches a process-global capture stream; two devices in one process need explicit streams (§7.6) | **noted** | One device per process remains the rule; irrelevant to the earlier `nvlddmkm` faults, as the review says. | §8 |
| 21 | Seven scientific over-statements (§8) | **accept all** | (1) ±3 is a decision rule, not an equivalence test — say so where it is used; (2) "nothing learns after the drop" is too strong: D3's raw WDL creeps 80.3 → 83.3 and draw recognition 60 → 68 over the 80 low-LR iterations; (3) the free-move "decomposition" is a conditional association, not mediation; (4) the [−1, 1] scale is *utility* = P(win) − P(loss); expected score is (1 + v) / 2, so +0.196 is +9.8 points of score, not 19.6 — the numbers stand, the header is wrong; (5) "nothing is settled by ply 30" conflicts with a first quartile of 30; (6) 99.9 % optimal on 3000 solved samples is not "the endgame is solved"; (7) decodability is not use. | E3 |
| 22 | The programme: repair → frozen supervised comparison → judge → only then a self-play experiment (§9) | **accept the order, with two additions** | The cheap play-time measurements (F) and the cheap in-pipeline arm (H1) run on the idle 3090 while G runs on the 3060; neither waits for the other. | §7 |

**What the review did not cover, added here.** (a) The nondeterminism finding in item 13, which
changes how every "same-seed" comparison in the project should be read. (b) That numbered
checkpoints are written only inside the evaluation block (`train2.py:321–325`), so an out-of-process
evaluator needs its own `--ckpt_every`. (c) No sealed test set remains (`endgame_v2_test` was read
once); any new generalisation claim needs a new one (E10). (d) The off-machine backup from PLAN5 §6
is still not done (E11).

## 2. Phase E — repair the instrument (no GPU-days; ≈ 2 days of desk work)

- **E1. The opening book.** Canonicalisation returns the transform as well as the key
  (`uttt/openings.py canonical()` → `(key, g)`); each child stores the transform that maps the
  parent's frame to the child's canonical frame; `principal_line()` composes transforms and prints
  the whole line in the parent's original frame. Rank replies by *orbit*: aggregate root visits and
  visit-weighted Q over symmetry-equivalent moves before taking the top-k, store the full root arrays
  so later aggregation can change. Regression test: every displayed prefix replays legally *and*
  canonicalises to the stored node key. Then rebuild both books (`runs/book_deep10.json`,
  `runs/book_deep8.json`; 17 min on the 3090 / 29 min on the 3060 each) and re-run
  `tools/book_stats.py` — the self-send rule (claim 7a) is re-read from the corrected book, and the
  corner-reply subtree after [40] appears for the first time. Rewrite the `.md` tables.
- **E2. The atlas Q-gap.** `tools/atlas.py`: the gap is between the two best *distinct reply
  orbits* (aggregate root Q by orbit, visit-weighted), and the table also reports the best-to-worst
  orbit range. No new search: the saved reply-orbit values already answer it (the review's
  `book_audit.json` has the numbers); re-derive from `runs/plan5_A1_atlas.json` and record in
  `runs/plan6_E2_atlas_orbits.out`.
- **E3. Restate the claims.** In `KNOWLEDGE.md`: the header ("units of expected score" → "utility,
  P(win) − P(loss); expected score is (1 + v) / 2"); claim 4 (two or more comparably good replies;
  worst reply clearly worse; the range per orbit); claim 7 (258 / 341; drop the 37-vs-41 example);
  claim 7a (from the rebuilt book); claim 9 (conditional association, not a mediation split); claim
  20 ("a quarter of games are settled by ply 30, the median at 36"; add the settled-fraction-by-ply
  table); claim 28 ("on the solved sample", not "solved"); claim 41 (augmentation is on;
  equivariance is not enforced); claim 42 (D3 as one perturbed run vs two seeds; "no resolved strength
  gain after the drop; WDL and draw recognition creep for 80 iterations"); claim 43's D3 sentence
  likewise. In `RETROSPECTIVE.md` §3 and §5: the same D3 wording, the "same seed" caveat from item
  13, and the ±3 rule stated as a decision rule. In `docs/explainer.html` Part 8: the utility /
  score wording and the reply-flatness sentence. Every edit is a wording change; no number moves
  except 256 → 258.
- **E4. RNG hygiene.** Skip the unused Gumbel draw when `selfplay=False` (`uttt/search.py:258`);
  give self-play noise, replay sampling, augmentation and exact-label selection their own
  `torch.Generator`s seeded from `cfg.seed`; wrap checkpoint loading in an RNG-preserving context.
  Regression test: an evaluation inserted between two training iterations does not change the next
  sampled minibatch indices or symmetry draws. Record in the test's docstring that this makes
  evaluation *observationally* neutral and does **not** make trajectories reproducible (item 13);
  `torch.backends.cudnn.benchmark = True` stays (it is worth its throughput; determinism is not
  available on this path anyway).
- **E5. Checkpoints.** Add `scaler.state_dict()` and the generator states to both checkpoint files;
  write `net_NNNN.pt` through the same `.tmp` + `os.replace` path as `latest.pt`; add
  `--ckpt_every` (default = `eval_every`) so numbered checkpoints no longer depend on evaluation.
  Resumes stay labelled as perturbed continuations in `config_resume_*.json` (add an `attempt`
  counter). Keep the two-file scheme.
- **E6. Symmetry tests** (`tests/test_symmetry.py`): engine commutation `T(gs, ga) = g T(s, a)` on
  random play-outs including free moves, closures and count endings; encoder equivariance and the
  simultaneous X/O + side-to-move relabelling invariance of the seven planes; head transformation
  laws for the 8-way and the canonical evaluators at the empty board and after [40] (orbit masses,
  not argmaxes); the same after fusion, fp16 and graph capture at a fixed batch shape; a
  transported-noise search test (same Gumbel noise mapped through g gives the transformed policy
  under the exact evaluator). These are the tests G's models must pass before they are interpreted.
- **E7. The evaluator on the 3060** (`tools/eval_worker.py`, ≈ 150 lines, reusing
  `tools/openings.py match` and `tools/endgame.py eval`): watches `runs/<run>/net_*.pt`, scores each
  new checkpoint on the *full* paired suite vs v2b (and a second anchor) at 64 sims and on
  `endgame_v2_dev`, writes `runs/<run>/eval_full.jsonl` with the CI, records the checkpoint hash and
  evaluator settings, evaluates the newest checkpoint if it falls behind, and finishes the
  outstanding ones after `DONE`. `tools/timeline.py` reads `eval_full.jsonl` when present. The
  trainer then runs with `--eval_every 0 --ckpt_every 10`: no evaluation path in the training
  process at all. Cost per checkpoint on the 3060: ≈ 4–8 min for the match (2.5× the 3090's 1.5–3
  min) plus ≈ 2 min for the endgame set; an 8-block iteration is ≈ 165 s, so the worker keeps up at
  every tenth checkpoint with the 3060 about a third busy.
- **E8. Log the budget axes.** Per iteration: positions generated, rows sampled, optimizer steps
  taken (not planned), teacher checkpoint, mean sampled replay age, distinct-key fraction of the
  sample, policy-target entropy, raw/search KL at the root, and the Gumbel Q-range at the root. Most
  are one line each in `train2.py` / `selfplay_cont.py`. Take the review's replay pre-draw while
  there (0.45 s per iteration; changes RNG ordering, which E4 makes irrelevant).
- **E9. The ownership head, graded properly.** On the B2 test positions: accuracy on *open* boards
  only, by ply bucket, against (i) the current-status baseline and (ii) a per-board logistic on
  local features; the trunk probe and the random-trunk probe on the same subset. Rewrites claim 40
  at whatever strength the numbers support.
- **E10. A sealed set.** `suites/endgame_v3_{dev,test}.npz` from `deep10_c1_300_s1`'s iterations
  280–299 games (held out for deep10, deep8_300 and any G student; *not* for s1), split by source
  game before solving; `_test` is read once, at the end of Phase G, and logged here. Report the
  canonical-key overlap between the halves (should be ≈ 0 at ≤ 14 empties; say what it is).
- **E11. Backup.** The `games/` corpora (≈ 160 MB per 300-iteration run), `net_*.pt`, `log.jsonl`,
  `config*.json` and `suites/` to a location off this machine. PLAN5 §6's local copy is not a
  backup.

## 3. Phase F — cheap measurements on the nets we have (≈ 1 h of GPU)

- **F1. Does exact equivariance alone buy anything at play?** Port the review's canonical evaluator
  into `uttt/symmetry.py` (`CanonicalEvaluator`, exact lexicographic keys, stabiliser-averaged
  policy transport) with `--a_canon / --b_canon` in `tools/openings.py match`. Paired suite, deep10
  canonical @64 vs deep10 plain @64. Pre-registered: ≥ 53 % → a free rung (adopt for play); 47–53 % →
  null, the residual asymmetry costs nothing at play and the 8-way average's +35 is an ensembling
  gain; ≤ 47 % → canonicalisation hurts and is for analysis caches only. 10 min on the 3090.
  Prediction, on the endgame-set read: null.
- **F2. The second LR drop, at ±2.8 instead of ±6.** With E7's worker: `net_0200, 0220, 0260, 0280,
  0300` of deep8_c1_300, deep10_c1_300, `_s1` and `_lr150` (for lr150: 0150, 0160, 0240, 0250, 0260,
  0300) on the full suite vs v2b @64. ≈ 24 matches × 2–3 min on the 3090, unattended. Pre-registered:
  the 280 drop "does something" only if 0300 − 0260 ≥ 3 points on at least three of the four runs.
  This closes a question that three in-run curves could not.
- **F3. Closed-board sensitivity on natural positions** — already measured by the review (0.061,
  3.9 %); record it in `KNOWLEDGE.md` §10 as a diagnostic of the input encoding, not a claim about
  the game.

## 4. Phase G — the frozen-teacher study (3060; days; no self-play)

The architecture question, answered before it costs a GPU-day. Everything here is supervised
learning on a fixed corpus with a fixed teacher, so an arm costs minutes and every arm sees the same
examples in the same order.

- **G-data.** 500 000 positions from `deep10_c1_300_s1`'s iterations 280–299 games (held out for
  deep10 and deep8_300), sampled with a prespecified phase mixture (the replay audit's *sampling*
  fractions — 3 / 18 / 25 / 29 / 25 % by ply bucket — so the study sees what the learner sees), split
  by game 400k / 50k / 50k (train / dev / test; test sealed until the end of G). Teacher: deep10
  symmetry-averaged at 256 sims — search policy, search value, plus exact labels where ≤ 14 empties
  (solver). ≈ 5 h on the 3090 with the averaged evaluator (< 1 h plain); the averaged one, because
  an exactly symmetric target is what students' D4 residuals should be measured against. Report the
  canonical-key overlap between splits.
- **G0. Passes vs data.** The plain 8×128 ResNet trained on 50k / 100k / 200k / 400k positions for
  1 / 2 / 4 / 8 passes each: held-out policy KL and endgame regret as a function of (positions,
  passes). This is the offline twin of H1; it says whether fitting is data- or update-limited *for
  a fixed teacher*, which is not the same question as H1's but is free.
- **G arms**, each at two seeds: (a) ResNet 10×128 as is; (b) ResNet 8×128; (c) 8×128 with the
  closed-board mask (item 7); (d) 8×128 with equivariant tied heads — the review's 861-orbit weight
  tying for `p_fc` and orbit-pooled `v_fc1` / `o_fc` / `m_fc` — on the ordinary trunk; (e) a D4
  regular-representation G-CNN with the *activation* width held at 128 (16 base filters × 8
  orientations), implemented as **weight-expanded ordinary convolutions** — the tied parameter bank
  is expanded into a standard `Conv2d` weight (once, at fusion time) so BN folding, fp16,
  channels_last and CUDA graphs are untouched and inference cost equals an ordinary ResNet of the
  expanded width; (f) optionally the relational model of review §5.4, only as dense fixed-shape
  batched matmuls over precomputed incidence tensors, and only if (e) shows equivariance buys sample
  efficiency.
- **G metrics** (dev; test once at the end): held-out policy KL and top-1 vs the teacher; value Brier
  vs the teacher and 3-way accuracy vs exact labels; regret on `endgame_v2_dev` and, once, on
  `endgame_v3_test`; the D4 residual (policy JS across the 8 orientations — zero by construction for
  (e), measured for the rest); inference time per evaluation at batch 4096 and batch 1 on both
  cards, graph-replayed. Data-matched curves (50k … 400k) and wall-clock-matched curves.
- **G gate (pre-registered).** An arm goes to self-play (H4) only if, on the sealed test slice, it
  (i) matches the 8×128 ResNet's policy KL and endgame regret within the ResNet's two-seed spread
  *at ≤ its inference cost per evaluation on the 3090*, or (ii) reaches the ResNet's 400k-position
  KL with ≤ 200k positions (a 2× sample-efficiency gain) at ≤ 1.5× its cost; and (iii) passes E6.
  Otherwise the result is a finding about learning on this game and stays in `KNOWLEDGE.md` §8.
- **What G cannot say.** Supervised fit to a fixed teacher is not the RL loop: an architecture that
  fits better may not self-play better (its own search generates its data). That is why the gate is
  a *permission* to spend a GPU-day, not a claim of strength.

## 5. Phase H — training runs (each owner-approved, one change per run, pre-registered)

All on 8 blocks: the 8 → 10 step is inside the seed band at equal sims (PLAN5 D1) and a wash at
equal compute (A8b), so 8×128 is the established recipe and the cheaper one. Operational settings for
every run: E5's checkpoints, `--eval_every 0 --ckpt_every 10` with E7's worker on the 3060, the retry
wrapper, hidden-console launcher (`runs/launch_*_hidden.vbs`), anchors v2b / deep8_c1_300 /
deep10_c1_300 in the worker. Every reading is the *final* checkpoint on the full paired suite @64;
"helped" ≥ 53 %, "hurt" ≤ 47 %, otherwise null — a decision rule, with the seed band (≈ 3 points)
stated beside it.

- **H1. `deep8_c1_300_e2` — `--epochs 2` (512 optimizer steps per iteration), everything else as
  deep8_c1_300.** ≈ 14 h. The cheap arm of the duration confound (§0). Primary: vs deep8_c1_300.
  Secondary: vs deep10_c1_300 and `_s1` — ≥ 50 % against both means extra updates alone matched the
  depth step at equal sims (and beat it at equal compute); the E7 curve at the constant LR — does
  the 150 → 200 climb (+5 in-run on the reference) grow? Tertiary: `endgame_v2_dev` raw WDL /
  regret vs 84.0 / 0.045. Readings: *helped* → the learner was update-limited; H3 runs with epochs
  2 (or an epochs-3 run at 300 iterations replaces it); *null* → data/teacher-limited, H3 as
  written; *hurt* → over-fitting the 7.6-iteration window, which is itself a finding (and says the
  buffer, not the update count, is the knob).
- **H2. `deep8_c1_300_mask` — the closed-board mask (item 7).** ≈ 13 h. Only after G arm (c) shows
  no supervised loss. Primary vs deep8_c1_300. A null is fine: it licenses the smaller state key for
  caches and dedup at no cost.
- **H3. `deep8_c1_600` — 600 iterations, `--lr_drops 500` (one drop: F2 found the second one does nothing
  resolvable on four runs), with H1's epochs if H1 helped.**
  ≈ 27 h (deep8_c1_300's self-play was 11.3 h and its late iterations run 15 % slower than its
  mean). Drops late, because D3 showed the drop is a fixed step on whatever the constant-LR phase has
  built and the low-LR phase settles in ≈ 20 iterations — so this run is, in effect, "300 more
  constant-LR iterations". Primary: vs deep8_c1_300. Secondary: vs both 10-block seeds; the E7
  full-suite curve from 300 to 500 — flat means duration is exhausted at this data rate, climbing
  means it is not, and either is worth the run. Tertiary: endgame numbers. This is PLAN5's D2,
  demoted to third because H1 decides what it should look like.
- **H4. A G-gated student in self-play.** Only past §4's gate; the recipe is H1's winner with the
  student's architecture swapped in; primary vs its ResNet parent at equal sims *and* at equal
  compute (both are required, because the point of the architecture is cost).

No further runs on the nulls (PLAN5 §5's list stands). No 12-block run. No 600 iterations on 10
blocks.

## 6. Not recommended (and why, briefly)

DDP / DataParallel across the two cards (training is 8 % of wall-clock; the 3060 is 2.5× slower at
batch 4096: 104.9 vs 42.3 ms). Self-play on the 3060 (a ≤ 1.4× inference ceiling for a second
process, two sets of graphs, teacher staleness). Larger self-play batches (`--games 8192` was a
measured null; the 3090's graph time is nearly linear from 1024 to 4096). A dense-tree or dynamic-
skipping search rewrite (profile first; it must beat the fixed-shape graph path). Channels-last
training (4× slower here). Playout-cap randomisation (fights the fixed shapes; revisit only with a
few persistent pools). A replay database. Symmetric copies in the buffer (per-sample augmentation is
on). Any "the net cannot represent X" claim (PLAN5 §1c).

## 7. Order, budget, GPU roles

| when | 3060 | 3090 | writing |
|---|---|---|---|
| days 1–2 | E1 book rebuild (or on the 3090); E9; E10 solve | E1 book rebuild; F1; F2 (after E7) | E3 restatements; E4–E8 code + tests |
| day 3 | G-data students start (G0, arms a–d) | G-data teacher labels (≈ 5 h); then **H1** if approved (≈ 14 h) | G write-up as arms finish |
| days 4–5 | E7 worker for H1 (a third busy); G arms (e), (f) | H1 running → `analysis.out` | H1 result; decide H3's shape |
| day 6+ | G test slice read once; E7 worker | **H3** if approved (≈ 27 h); H2 in the gap | KNOWLEDGE / RETROSPECTIVE / explainer |

GPU budget: F ≈ 1 h; G ≈ 5 h of 3090 plus 3060-days; H1 ≈ 14 h; H2 ≈ 13 h; H3 ≈ 27 h; H4 only if
gated in. Nothing in E–G waits on a training run; H1 can start as soon as E5 and E7 exist.

Decision points: after F2 — *taken 2026-09-06: the second drop does nothing resolvable at ±2.8 (log), so
H3 keeps one drop* — ; after H1 (H3's shape); after G's gate (whether H4 exists).

## 8. Operational notes

- Traps from PLAN5 §8 and its Handover still apply: `runs/probe_*` nets are untrained; `suites/` v1
  files are never rewritten; test halves are read once and the reading is logged in the plan;
  analysis tools default to `--device cuda:1` except `openings.py match` and `book.py`; held-out
  positions for a net come from *another* run's games; never edit a running run's config; the
  auto-mode classifier blocks multi-hour launches from a shell — the owner launches, through the
  hidden-console task.
- One CUDA device per process. If a tool ever captures graphs on both cards in one process, pass an
  explicit `stream=` per device (review §7.6).
- `nvidia-smi` and `torch.cuda` number the cards in opposite orders; the 3090 is `cuda:0`. Log the
  device *name* at launch, not the ordinal.
- E7's worker and the trainer must not both hold the 3090; the worker is a `cuda:1` process by
  construction. The worker reads only atomically written checkpoints (E5).
- "Same seed" means the same initial weights and the same first iteration, and nothing after it
  (§1 item 13). Write comparisons as "against the seed band", never as "paired".
