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

## Handover (2026-09-09)

**State (2026-09-09 13:30).** H1b is done (E = 4). **H4 is done and read: hurt.** `gcnn8_c1_300_e4/net_0300.pt`
scores **22.0 % [19.9, 24.2], −220 Elo against its parent `deep8_c1_300_e4`** on the full suite @64 (the log's 12:35
entry) — the run was interrupted at iteration 268 by a Windows Update restart at 23:55 on 2026-09-08 and resumed at
09:24 as attempt 1 from iteration 260 (files verified bit-clean; the log's 08:25 entry; iterations 260–268 carry
`attempt: 1` in `log.jsonl`, de-duplicate by iteration when reading it). Exact symmetry held throughout (D4 JS 0.000
at all 30 checkpoints), nothing was unstable, and the cause reads as capacity, not the LR (the sweeps in the 08:25
entry: at 12 480 supervised steps the plain ResNet overtakes the G-CNN, dev KL 0.763 vs 0.830, the G-CNN over-fits the
frozen set, and a lower LR at equal steps makes it worse, 0.845; Phase G's gate was read at 3 120 steps, 1 % of the
run's, and the ordering it certified does not survive 12 480 — a supervised gate has to be read at a step count of
the order of the run's). Written up: KNOWLEDGE 50 and 48, RETROSPECTIVE §2 / §3 / §4 / §5 / §7, README. **Sweep 3
read (13:01): the tied-heads hedge survives the same test** — resnet8_tied 0.7408 against resnet8's 0.7630 at 12 480
steps, ahead on every metric, the margin shrinking slowly (0.036 / 0.027 / 0.022 over three doublings) rather than
reversing (the 08:25 entry's last paragraph). **The owner read H4 and the instance's assessment at ~13:30 and closed
the chain; the decisions are §9.** H3 is withdrawn — as written it re-buys §0's confound — and H5 is not proposed:
sweep 3's margin closes across the doublings and exact policy symmetry has no consumer (41b). The approved work is
three items and no more — **H1c `deep8_c1_300_e8`** on the 3090, then **G arm (g) `gcnn8x46`** and **I1**, the
analysis second pass on `deep8_c1_300_e4`, on the 3060 — with **E11**, the backup, after them. Still not to propose:
a G-CNN at a lower LR (the sweeps), and no wider G-CNN in *self-play* except through §9b's reading with its measured
inference cost declared. Both cards are idle (13:05). Windows Update is paused until 2026-10-14; the play agent
is `runs/deep8_c1_300_e4/net_0300.pt`.

**State at 19:50 on 2026-09-10: §9's programme is complete.** H1c done and read — helped, **55.8 % [53.3, 58.2], +40 [+23, +57] over `deep8_c1_300_e4`**; the play agent is now `runs/deep8_c1_300_e8/net_0300.pt` (+363 vs v2b, the yardstick saturated; endgame 91.3 / 0.022); G arm (g) and I1 done and read (the log's 07:30, 08:10 and 19:45 entries; §9a–c). Both cards idle. **Nothing further is proposed. Next: E11** — the owner creates the empty GitHub repository, then `git remote add origin <url> && git push -u origin main`, and the off-machine copy of `runs/*/games` (≈ 160 MB per 300-iteration run), the `net_*.pt` not tracked by git, and `suites/`. The game claims of KNOWLEDGE §1–§8 were re-read on `_e4` (I1), not on `_e8`; a third pass on `_e8` is not proposed (+40 is inside what I1 showed to be the drift of magnitudes, and the orderings held). **Next: the closing programme of §9, in this order — H1c on the 3090, then G arm (g) and I1 on the 3060, then E11.**

*1. H1c `deep8_c1_300_e8`* (§9a; ≈ 22–23 h, inside the update pause if launched before 2026-10-13). `runs/queue13.sh`
is **not yet written**: copy `runs/queue11.sh` and change four things — `R=deep8_c1_300_e8` and
`PARENT=deep8_c1_300_e4`; **drop `--gcnn 16`** from the `train2` line (H1c is the plain 8×128 ResNet); set
`--epochs 8` (`--iters 300 --lr_drops 200,280` are already right); point the worker's anchors at
v2b / `deep8_c1_300_e4` / `deep8_c1_300` and the closing `endgame.py eval` line at `net_0300.pt` — plus
`runs/launch_queue13_run.cmd` and `runs/launch_queue13_hidden.vbs` from queue12's (change `queue12` → `queue13` and
the run name in the .vbs comments). Launch: **`wscript runs/launch_queue13_hidden.vbs`** from the repo root.
Preflight: both cards idle (`nvidia-smi`; the trainer never shares the 3090), git clean of tracked changes, the
parent's `net_0300.pt` present. Status: `python tools/run_status.py runs/deep8_c1_300_e8 --ref
runs/deep8_c1_300_e4`; watch: a single-shot background `until [ -f runs/deep8_c1_300_e8/DONE ] || grep -q "FAILED
after" runs/deep8_c1_300_e8.out; do sleep 300; done` (the Monitor tool delivers nothing from these files on this
machine). A reboot is the one failure the retry wrapper cannot cover: if the machine restarts mid-run, relaunch the
same `.vbs` — `train2` resumes from `latest_full.pt` and the worker skips what `eval_full.jsonl` holds (the H4
precedent, the log's 08:25 entry).

*2. The 3060 queue, started as soon as H1c is launched and running beside it.* First **G arm (g)** (§9b): add
`"gcnn8x46": lambda: NetConfig(blocks=8, filters=368, gcnn=46)` to `tools/gstudy.py`'s `ARMS`, measure the arm's
inference cost with `tools/gtiming.py` and record it, then `gstudy.py --arm gcnn8x46 --positions 400000 --passes
8,16,32 --seeds 0 --lr 0.02 --device cuda:1`, read at the 12 480-step point. Then **I1** (§9c): the Phase A tools
re-run on `deep8_c1_300_e4/net_0300.pt` at the deep10 pass's settings (`runs/plan5_A_3060.sh`,
`runs/plan5_A_3090.sh`), everything on `cuda:1` — `book.py` needs `--device cuda:1` passed, its default is the 3090
— into `runs/plan6/I1_*.out`, each claim marked held / moved / reversed. The E7 worker shares the card throughout
(≈ 6 min per checkpoint every ≈ 43 min).

*3. E11* (§9d): after all three, the owner creates an empty GitHub repository; then `git remote add origin <url>`,
`git push -u origin main`, and the `games/`, `net_*.pt` and `suites/` copies off-machine.

The 50 % line still applies to every launch: above it, update this Handover, the log, KNOWLEDGE, RETROSPECTIVE and
README and hand over rather than launch.

**The owner's decision (2026-09-07): H1b approved, and a conditional pre-approval of the chain H1b → H4 → H3.** The
next run starts without asking *as long as the instance is under 50 % of its context window when it would start it*;
above 50 % it updates everything (this Handover first, then the log, KNOWLEDGE, RETROSPECTIVE, README) and hands over
to the next instance instead of launching. *Amended by the owner at 13:55: H4 is to be launched after H1b regardless
of the instance's estimate (it judged itself at ≈ 55–60 % after the preflight; the owner judged that fine); the line
applies again to H3.* *(H3 is withdrawn as of 2026-09-09, §9; the line now applies to H1c.)* Each result is read by its pre-registered rule and written up before the
next launch. Delegate the write-ups and any file-heavy reading to `directed` subagents (opus) to stay under the line.

The Handover's optional hour is done (13:16–13:36 on the 3060, `runs/plan6/H1_reverify.out`; the log's 13:36
entry): on `deep8_c1_300_e2` the phased schedule is a null again (+11), the 8-way average the same +32 it was on
deep10, the canonical evaluator a null again (+3). KNOWLEDGE 45 / 41 / 41b, README and RETROSPECTIVE §7 carry them.
The play configuration stays flat `--sims 256` or more.

The play agent is `runs/deep8_c1_300_e4/net_0300.pt` (+363 vs v2b; the log's H1b entry). Phase G is complete,
including the one sealed test read. The G-CNN was smoke-tested through the self-play pipeline on 2026-09-07
(`runs/probe_gcnn_smoke`, untracked, an untrained net: 4 iterations of 256 games on the 3060 — fused graph self-play,
50 training steps per iteration with falling losses and no skipped steps, atomic checkpoints, a resume that restored
the scaler and generators, and the E7 worker scoring its checkpoints against a ResNet anchor with the endgame set), so
H4 was launchable as written. E11 (backup) stays deferred by the owner to the write-up; the repository has no remote.

**The chain, with the recipes fixed by the rules already written.** Operational settings for every run: copy
`runs/queue11.sh` (retry wrapper, `--eval_every 0 --ckpt_every 10`, the E7 worker on the 3060 with the parent among
its anchors, `eval_run.sh` + the endgame_v2_dev read at the end), a `launch_queue<N>_run.cmd` and
`launch_queue<N>_hidden.vbs` (sed the names), launched with `wscript runs/launch_queue<N>_hidden.vbs` from the repo
root; the trainer must never share the 3090 with anything. Every reading: the *final* checkpoint on the full paired
suite @64 against the named parent — ≥ 53 % helped, ≤ 47 % hurt, otherwise null — with the seed band (≈ 3 points)
stated beside it. E below is the epochs the chain carries forward.

1. **H1b `deep8_c1_300_e4` — done 2026-09-08** (the log's entry). Primary `paired_vs_deep8c1_300e2_64.json`:
   **59.1 % [56.3, 61.8], +64 Elo [+44, +83] — helped**, 6 points clear of the rule and twice the ≈ 3-point seed
   band. **So the chain carries E = 4**: the learner is still update-limited at four passes, and an `--epochs 8`
   run is worth proposing after the chain. Secondary and tertiary readings, the curve and the budget axes are in
   the log entry; KNOWLEDGE 49 (43, 44, 46 extended), RETROSPECTIVE §2 / §3 / §7 and README carry them. The play
   agent is now `runs/deep8_c1_300_e4/net_0300.pt`.
2. **H4 `gcnn8_c1_300_e4` — done 2026-09-09, hurt** (the log's 12:35 entry; interrupted at 268 by a restart and
   resumed as attempt 1, the log's 08:25 entry). `--gcnn 16 --filters 128 --blocks 8 --epochs 4`, everything else
   as H1; parent `deep8_c1_300_e4`. Primary `paired_vs_deep8c1_300e4_64.json`: **22.0 % [19.9, 24.2], −220 Elo
   [−242, −199] vs the parent — hurt**, by 25 points; −50 vs deep8_c1_300, +162 vs v2b. Secondary: D4 JS 0.000 at
   all 30 checkpoints — exact symmetry held and is not what was missing; endgame_v1 80.8 / 0.058 (parent 90.1 /
   0.022). 19.8 h (self-play 1.02× the parent, training 1.52×). `--head_tying 1` was the fallback if the G-CNN
   misbehaved in RL (diverging losses, many skipped steps) — it did not misbehave; it converged, stably, to a much
   weaker net, and the sweeps read the cause as capacity, not the LR. Not proposed again at this width; the play
   agent stays the parent.
3. **H3 `deep8_c1_600_e4` — WITHDRAWN by the owner 2026-09-09, not run** (§9). `--iters 600 --lr_drops 500
   --epochs 4`, everything else as H1; parent `deep8_c1_300_e4`; ≈ 34–36 h. The reason: as written it doubles data,
   updates and teacher exposure together — the confound §0 was written to remove — so its "flat or climbing"
   reading could not say which of the three moved, and the update axis has now been separated twice (46, 49) while
   the data and teacher axes never have. `runs/queue12.sh`, `runs/launch_queue12_run.cmd` and
   `runs/launch_queue12_hidden.vbs` **stay in the repo as staged but withdrawn** — a correct recipe for a run that
   is not being bought, kept so the shape is on record. Not to be launched.
4. **H1c `deep8_c1_300_e8` — done 2026-09-10, helped: 55.8 % [53.3, 58.2], +40 [+23, +57] over the parent** (§9a; the log's 19:45 entry; the play agent is now `deep8_c1_300_e8/net_0300.pt`). `deep8_c1_300_e4`'s
   recipe with `--epochs 8` (2048 optimizer steps of batch 1024 per iteration) and nothing else changed; parent
   `deep8_c1_300_e4`. ≈ 22–23 h on the 3090 (t_train ≈ 10 h against H1b's 4.98; self-play ≈ 12 h unchanged — the
   same 8×128 ResNet). It is the third point of the dose–response curve +100 → +64 → ? and the first direct test of
   the over-fitting branch H1's reading wrote and never fired. Primary by the rule against the parent; the full
   pre-registered reading, the queue13 names and the reboot recipe are in §9a.

Not proposed: H2 (the mask; its supervised gain is real but small — 0.008 in KL — and the licence it buys has no
consumer yet); H5 (`--head_tying 1`; §9's dropped list); a 10-block anything (46, 48); self-play on the 3060 (§6);
the G-CNN again at width 128 (50).

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
- **13:36 — the re-verifications on `deep8_c1_300_e2`** (full paired suite, 516 pairs, the 3060 shared with the
  worker, 20 min in all; `runs/plan6/H1_reverify.out`): phased "0:128,24:384" vs flat 256 **51.6 % [49.2, 53.8],
  +11 Elo [−6, +26]** — null (deep10: +10, deep8_300: +26, v2b: +50; the stronger the net the less the late
  search adds); the 8-way symmetry average @64 vs plain @64 **54.7 % [52.1, 57.2], +32 [+14, +50]** — the same
  ensembling gain as deep10's +35, at 8× the inference; the canonical evaluator @64 vs plain @64 **50.4 % [47.7,
  53.1], +3 [−16, +22]** — null (deep10: −3). KNOWLEDGE 45, 41, 41b restated with the new net; README and
  RETROSPECTIVE §7 updated. Play config unchanged.

- **2026-09-08, H1b — `deep8_c1_300_e4` (owner-approved 2026-09-07, launched 2026-09-07 13:15, DONE 06:11 the
  next morning after 16.9 h, 0 crashes).** `deep8_c1_300_e2`'s recipe with `--epochs 4` (1024 steps of batch 1024 per iteration instead of
  512) and nothing else changed: the same 4096 × 64 new positions per iteration, the same 2 M-row buffer, the same
  LR drops at 200 / 280, seed 0; `--eval_every 0 --ckpt_every 10 --anchors ""`, the E7 worker scoring every 10th
  checkpoint on the full suite against v2b, the parent and deep8_c1_300. **Primary: 59.1 % [56.3, 61.8], +64 Elo
  [+44, +83] vs `deep8_c1_300_e2` — helped**, 6 points clear of the rule and twice the ≈ 3-point seed band.
  Secondary: 74.4 % [72.0, 76.7], +185 [+164, +207] vs deep8_c1_300; 69.2 % [66.7, 71.6], +141 [+121, +160] vs
  deep10_c1_300 and 71.3 % [68.9, 73.6], +158 [+138, +178] vs its replicate; **89.0 % [87.4, 90.6], +363 Elo
  [+337, +395] vs v2b**; +310 vs wide128_c1, +291 vs deep8_c1, 92.5 % [91.0, 94.0], +437 vs dev1. The worker's
  independent final read agrees (`eval_full.jsonl` iteration 300: 0.890 vs v2b, 0.5906 vs the parent). The
  full-suite curve (`eval_full.jsonl`, ±2.8, every 10 iterations, H1's beside it):

  | iteration | 10 | 50 | 100 | 150 | 200 | 210 | 220 | 260 | 280 | 300 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | H1b vs v2b | 24.7 | 67.0 | 75.0 | 79.1 | 80.5 | 86.1 | 87.3 | 86.6 | 87.2 | 89.0 |
  | H1 vs v2b | 20.1 | 52.1 | 68.8 | 75.5 | 75.9 | 82.2 | 83.4 | 84.2 | 84.9 | 84.2 |
  | H1b vs H1's final net | 8.1 | 20.6 | 30.2 | 38.9 | 47.3 | 52.7 | 56.2 | 57.7 | 55.3 | 59.1 |

  The gain is built in the constant-LR phase and then carried: H1b leads H1 by 3.6–14.9 points at every
  checkpoint to 200 (most of it early — +14.9 at iteration 50), and at 200, before its own drop, it is already
  level with H1's *final* net (47.3 %). The first drop then does for it what it did for H1 — +5.6 (80.5 → 86.1)
  against H1's +6.3, both inside F2's +4.8 … +8.5 band — and **220–300 is flat within ±3** (86.6–89.0 vs v2b; the
  head-to-head wobbles 55.3–59.1 over the same window, a 3.8-point spread at the ≈ ±3 checkpoint noise floor), the
  second drop nothing. Tertiary: endgame_v1 raw WDL **90.1 % [89.0, 91.2]**, draw recognition 79.0 %, regret 0.022
  [0.016, 0.028], optimal 98.1 % (H1 87.6 / 74.8 / 0.036; deep10 84.6 / 0.037); endgame_v2_dev 90.5 [89.5, 91.6],
  regret 0.029 [0.023, 0.036] (H1 87.5 / 0.034); the 256-sim search 99.9 % optimal and 0.001 regret on both.
  Timeline (`runs/plan6/H1b_timeline.out`, 20 000 held-out positions from deep10_c1_300): endgame WDL 62.3 → 90.1
  and draw recognition 25.7 → 79.0 % over the run, stepping at the first drop as every run's does; final **D4 JS
  0.026 bits, value std 0.052** — H1's 0.026 / 0.050, so four passes bought no more symmetry consistency than two.
  Budget axes (E8): 133 of 307 200 steps skipped by the GradScaler (H1 70 of 153 600 — the same rate); mean sampled
  replay age 3.35 iterations of a 7.6-iteration buffer window (H1 3.35); sampled distinct-position fraction
  0.67 → 0.62 (H1 0.81 → 0.75 — each row is now drawn twice as often); policy-target entropy 0.15 bits; raw/search
  KL 1.13 → 0.84 (1.22 → 0.84); root Q range 0.41 → 0.50 (0.39 → 0.46); self-play games 52.8 plies (52.5), draws
  16.6 % (15.5 %). Cost: t_train 4.98 h vs 2.55 h, t_selfplay 11.93 h vs 12.06 h; wall 16.9 h vs 14.6 h; the net is
  the same 8×128 ResNet, so it costs exactly what H1's costs to evaluate. **Reading: still update-limited at four
  passes — E = 4 for the chain**, and an `--epochs 8` run is worth proposing after it. H4 was launched at 06:23 on
  2026-09-08 at `--epochs 4` with `deep8_c1_300_e4` as its parent (Handover). KNOWLEDGE 49 (43, 44, 46 extended);
  RETROSPECTIVE §2, §3, §7; README. The play agent changes to `deep8_c1_300_e4/net_0300.pt`.

- **2026-09-09, 08:25–09:30 — H4 interrupted at iteration 268 by a Windows Update restart; every file verified
  intact; resumed 09:24 as a perturbed continuation; the reading at 260 is already "hurt"; the mechanism traced to
  the constant LR.** The restart: Windows Update installed the 2026-09 cumulative (KB5124008) and `MoUsoCoreWorker`
  restarted the machine at 23:55:03 on 2026-09-08 (a second, TrustedInstaller restart at 23:57:23), outside the
  01:00–15:00 active hours, nothing pending beforehand. Iteration 268's shard (23:52:24), `latest.pt` and its log line
  (23:53:52) were complete; the kill landed ≈ 70 s into iteration 269's self-play. The bash wrapper died with the
  session (`runs/queue11.out`: `dofork … 0xC000026B`, `STATUS_DLL_INIT_FAILED_LOGOFF`), so the 6-attempt retry loop
  never reached attempt 1 — a reboot is the one failure the wrapper cannot cover; updates are now paused until
  2026-10-14. **Integrity** (an opus `directed` agent, read-only, CPU; `runs/plan6/H4_diag/ck_check.py`): no `.tmp`
  under `runs/` or anywhere in the repo, no zero-byte or truncated file; `latest.pt` (iteration 268: net, opt, scaler,
  rng), `latest_full.pt` (iteration 259, 578 MB: the same plus the full 2 000 000-row buffer, all 14 fields at 2 M
  rows, no non-finite value; its net byte-identical to `net_0260.pt`), `net_0250/0260.pt` and the play agent
  `deep8_c1_300_e4/net_0300.pt` all load with a strict `state_dict` match; `log.jsonl` 269/269 lines, iterations
  0…268 with no gap or duplicate, the `global_step` arithmetic tying out (274 432 + 1024 = 275 456); `eval_full.jsonl`
  26/26; all 269 game shards open with one key set and consistent shapes (1 340 385 games); all 26 numbered
  checkpoints re-hash to the sha256 the worker recorded before the crash; the three suites open; `git fsck --full`
  clean, no tracked file modified; both cards enumerate after the update. **Resume:** `queue11.sh` relaunched as
  written (`wscript runs/launch_queue11_hidden.vbs`, 09:24): `train2` prefers `latest_full.pt`, so it restarted at
  iteration 260 as attempt 1 (`config_resume_20260909_092443.json`; `resumed from iteration 259 (latest_full.pt,
  buffer 2000000, scaler restored, generators restored)`), overwriting `games_0260–0268.npz` and appending
  `attempt: 1` rows for 260–268 to `log.jsonl` (`net_0260.pt` stays; the D1 precedent, PLAN5 Handover); the worker
  restarted beside it and skips what `eval_full.jsonl` holds. 40 iterations ≈ 2.9 h + `eval_run.sh`.

  **The interim reading — the worker's full-suite reads at ±2.8, H4 and its parent at the same iteration:**

  | iteration | 10 | 50 | 100 | 150 | 190 | 200 | 210 | 220 | 250 | 260 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | H4 vs v2b | 8.0 | 22.0 | 32.9 | 39.9 | 40.0 | 29.4 | 60.1 | 65.4 | 65.1 | 65.2 |
  | parent (H1b) vs v2b | 24.7 | 67.0 | 75.0 | 79.1 | 80.5 | 80.5 | 86.1 | 87.3 | 88.9 | 86.6 |
  | H4 vs deep8_c1_300's final net | 2.3 | 5.1 | 12.1 | 15.0 | 16.4 | 10.5 | 29.8 | 32.6 | 31.9 | 35.7 |
  | parent vs the same | 10.8 | 32.9 | 48.5 | 56.1 | 54.6 | 60.7 | 69.2 | 68.8 | 70.4 | 70.1 |
  | **H4 vs the parent's final net** | 0.7 | 1.8 | 4.8 | 5.9 | 7.8 | 5.1 | 15.7 | 17.6 | 17.7 | **19.3 [17.2, 21.5]** |

  H4 trails at all 26 common checkpoints with non-overlapping intervals; at 260 the gap through the shared anchors
  is −21.4 points vs v2b (+109 against +324 Elo) and −34.4 vs deep8_c1_300, and head-to-head with the parent's final
  net it is **19.3 % [17.2, 21.5], −248 Elo** — the rule's "hurt" line is 47 %, and neither 40 more iterations nor
  the second drop (nothing resolvable on four runs, F2) can move 19 to 47. Its post-drop plateau (65 % vs v2b) is
  where the parent was at iteration ≈ 20. endgame_v2_dev at 260: raw WDL 80.4 %, regret 0.050 (parent 89.5 / 0.029).
  **The fallback clause does not fire:** no divergence (policy loss 1.71 at 0 → 1.36 at 200 → 1.13 at 250 → 1.18 at
  268, the same late wobble as the parent's), **122 steps skipped of 275 456 against the parent's 118**, at most 2 in
  any iteration of either run, no NaN or Inf in any logged field, target entropy 0.163 vs 0.161 bits over 239–268,
  self-play *more* diverse than the parent's (distinct fraction 0.69 vs 0.58), `attempt: 0` on every line. Cost:
  17.5 h to 268 against the parent's 15.0 (self-play 1.02× — the exported net costs what the ResNet costs, as
  claimed; training 1.52×, the per-step weight expansion and the per-iteration re-export). An equivariance
  signature in the run itself: when the top first move leaves cell 40 (13 of the last 119 iterations) the mass is
  split exactly across a 4-cell orbit (share × orbit size 0.71–0.86); the parent never leaves cell 40 after 150.

  **Mechanism** (an opus `directed` agent, read-only, CPU; `runs/plan6/H4_diag/{gradscale,gradscale2,sharpness,
  rootpolicy}.py`): a stable convergence to a far weaker fixed point at the top LR — a different failure from the
  one the fallback anticipated. (i) The policy loss is *flat over iterations 100–190* (1.362 → 1.374 → 1.377) and
  falls 15 % in ten iterations at the first drop (the parent: 8 %); `raw_kl` sits 32 % above the parent's through
  the plateau; `surprise` is 1.5× the parent's at the constant LR and collapses to parity at the drop (−0.073
  against −0.004). The drop was worth **+223 Elo to H4 (−152 → +71 vs v2b) against +70 to the parent**; its endgame
  WDL jumped 70.8 → 81.2 in one step. (ii) The raw opening prior at the empty board flips between orbits across
  adjacent checkpoints — p([40]) 0.24 / 0.69 / 0.15 / 0.67 at 180 / 190 / 200 / 260, the four corners of the centre
  board taking the rest, exactly tied — where the parent sits at 0.97–0.99 throughout; `first_move_top_share` has
  sd 0.227 over 100–190 against the parent's 0.039 and settles after the drop (0.058). The root value swings with it
  (+0.34 / +0.12 / +0.20 at 180 / 190 / 200; parent +0.43 / +0.34). (iii) The obvious story — a bank's gradient is
  the sum over its 8 (64 for group-to-group layers) expanded copies, so the effective LR is 8× — is **refuted by
  measurement**: the summing is real (amplification 2.8–6.5 per trunk layer, the copies positively correlated) but
  the BatchNorm weight-norm equilibrium absorbs it (the G-CNN's trunk norm settles 1.9× above init against the
  ResNet's 1.45×, because decay acts on one copy while the data gradient acts on eight), leaving the relative step
  ‖g‖/‖w‖ **1.19× the ResNet's in the trunk and 1.41× in the heads** at iteration 190. What *is* different is
  curvature: the top Hessian eigenvalue of the same loss is **2.26× the ResNet's at 190** (1373 vs 607; 1.97× at
  260), so lr·λ_max sits ≈ 2.3× further past the stability edge. (iv) `gstudy.py` used the identical SGD (0.02,
  momentum 0.9, wd 1e-4, nesterov, warmup 200, fp16) — but 2 080 top-LR steps against the run's 204 800; the
  supervised win was measured 98× short of the RL exposure. Also real, ranked lower: 312 k parameters against a
  moving target; D4 augmentation is an exact no-op for an equivariant net (up to 8× less per-step diversity from
  the same rows — KNOWLEDGE 48 already called it the first partly data-limited student); weight decay effectively
  3–6× weaker on the shared banks; the tied invariant value read-out (value loss *rose* after the drop, 0.654 →
  0.718, the parent's fell). Refuted, not to chase: the GradScaler / fp16 path (BN runs fp32 under autocast; skips
  at the parent's rate), a broken export (`tests/test_equivariant.py` passes; the fused path is exact). **The
  sweep** launched 09:25 on the 3060 (`runs/plan6/H4_lr_sweep_3060.sh`): gcnn8x16 and resnet8 on `gdata_v1`,
  400k × 16 passes (6 250 steps, twice the G points) at lr 0.02 and at 0.005, one seed, ≈ 14 min per arm.
  Pre-registered reading against the 8-pass points on file (0.806 / 0.884): the G-CNN's dev-KL advantage *shrinks or
  inverts at 0.02 as steps grow but holds at 0.005* → the LR; shrinks at both → capacity; holds at both → neither,
  and the RL-specific hypotheses (the augmentation no-op, the moving target) are next.
  **Sweep read (10:27; dev policy KL vs the teacher, one seed; `runs/plan6/H4_lr_*.json`, the 8-pass lr-0.02 points
  in brackets):** at lr 0.02, 16 passes (6 240 steps) — gcnn8x16 **0.7875** [0.8057 / 0.8066], resnet8 **0.8145**
  [0.8839 / 0.8853]: the G-CNN's advantage shrinks from 0.078 to 0.027 — the ResNet gains 0.070 from the doubling,
  the G-CNN 0.018. At lr 0.005, 16 passes: gcnn8x16 0.846, resnet8 0.894 — both worse than at 0.02 (6 240 steps at
  a quarter of the LR is under-trained; the drops sit at the same fractions), the advantage 0.048. Beyond the KL: at
  16 passes @0.02 the ResNet's value head is now the better one (Brier 0.1006 vs 0.1182; endgame_v2_dev raw WDL
  69.7 vs 67.5 %, regret 0.132 vs 0.148 — at 8 passes the G-CNN led on both), while the G-CNN keeps the policy edge
  (top-1 0.620 vs 0.582, exact 3-way 0.818 vs 0.807). D4 JS: G-CNN 3 × 10⁻⁶ bits (exact), ResNet 0.060. Reading:
  **the supervised advantage is a few-step advantage that erodes with steps** — the rule's first branch ("shrinks at
  0.02") fires, but one step count at 0.005 cannot say whether it "holds" there, and the erosion is equally what
  capacity saturation (312 k parameters) looks like, so LR and capacity are not yet separated. At the ResNet's
  per-doubling gain the crossover is ≈ 1–2 more doublings (12–25 k steps), a thirtieth of the run's 307 200 —
  consistent with the RL result either way. Second sweep (`runs/plan6/H4_lr_sweep2_3060.sh`, launched 10:31,
  ≈ 1.4 h → `H4_lr_sweep2.out`, `H4_lr2_*_x32.json`): both arms at lr 0.02 × 32 passes (does the ResNet overtake?)
  and gcnn8x16 at lr 0.005 × 32 (does the G-CNN beat its own lr-0.02 number at equal steps — an LR floor, propose the
  G-CNN at a lower LR — or not — capacity, the wider G-CNN or `--head_tying 1`?).
  **Sweep 2 read (12:10; 400k × 32 = 12 480 steps, `runs/plan6/H4_lr2_*_x32.json`):** at lr 0.02 the ResNet
  **overtakes** — resnet8 **0.7630** (top-1 0.611, Brier 0.096, exact 3-way 0.840, endgame_v2_dev raw WDL 72.6 %,
  regret 0.124), gcnn8x16 **0.8298** (0.629 / 0.116 / 0.822 / 66.0 % / 0.151) — and the G-CNN's dev KL is now *worse*
  than at 16 passes (0.7875) and at 8 (0.806) while its training loss keeps falling (0.899 → 0.782 at the last
  pass): it is over-fitting the frozen 400 k set (KL on the positions with no canonical twin in train 1.026 →
  1.135; the ResNet's 0.960 → 0.931, still improving) — what a net for which D4 augmentation is an exact no-op does
  on its 32nd identical pass, while the ResNet is on its fourth pass over eight views. At lr 0.005 × 32 the G-CNN is
  worse again, **0.8447** (disjoint 1.119, endgame WDL 60.9 %): a lower LR at equal steps recovers nothing.
  **Reading: capacity, not the LR.** The G-CNN's supervised advantage (0.078 at 3 120 steps) is a small-step
  advantage; the ordering flips between 6 240 and 12 480 steps — 4 % of the run's 307 200 — and the RL result is
  that ordering read at full exposure. The interpretation that fits the run's "flat, then a cliff at the drop" is
  then the noise floor of a sharper basin (λ_max 2.3×) that a smaller LR lowers but that no LR puts under the
  ResNet's — and the *second* drop, worth nothing to any ResNet (F2), gives the G-CNN +7.3 vs v2b (net_0280 66.3 →
  net_0290 73.6), which says the same. Consequence for the method: Phase G's gate was read at 3 120 steps, 1 % of
  the RL exposure, and the ordering it certified does not survive 12 480; a supervised gate has to be read at a
  step count of the order of the run's, or until the curves have crossed or clearly will not — KNOWLEDGE 48 is to
  be restated with this. Consequence for the chain: no G-CNN at a lower LR; a wider G-CNN breaks §5 H4's equal-cost
  requirement; `--head_tying 1` (KL 0.848 at 3 120 steps, the pre-registered hedge) is not proposed either until the
  same test has been run on it — sweep 3 (`runs/plan6/H4_lr_sweep3_3060.sh`, 12:15, ≈ 36 min): resnet8_tied at
  lr 0.02 × 16 and × 32 against the resnet8 points above (0.8145 / 0.7630).
  **Sweep 3 read (13:01; `runs/plan6/H4_lr3_resnet8_tied_lr0.02.json`): the tied heads survive.** resnet8_tied at
  6 240 steps **0.7877** (resnet8 0.8145) and at 12 480 **0.7408** (0.7630) — ahead at every step count and on every
  metric at 12 480 (top-1 0.620 vs 0.611, Brier 0.094 vs 0.096, exact 3-way 0.849 vs 0.840, disjoint-position KL
  0.897 vs 0.931, endgame_v2_dev raw WDL 73.1 vs 72.6 %, regret 0.104 vs 0.124), with no over-fitting signature (its
  disjoint KL falls 0.922 → 0.897 as the ResNet's does). The margin shrinks slowly — 0.036 / 0.027 / 0.022 across the
  three doublings — rather than reversing; a straight line in log-steps reaches zero near the run's 307 200, so the
  honest self-play prediction is null-to-small, not a rung. What it has that the G-CNN lacks: a full 2.39 M-parameter
  ResNet trunk on which D4 augmentation is still informative; the tying is confined to the read-out (861 policy
  orbits, orbit-pooled value / margin, board-orbit ownership), which is exactly symmetric only when the trunk is
  (D4 JS 0.058, the ResNet's 0.071). **Status: `--head_tying 1` on the `deep8_c1_300_e4` recipe is proposable to the
  owner as H5, after H3** — zero inference cost (33.3 vs 33.2 ms per 4096, G timing), a pre-registered rule against
  the parent, and, given the shrinking margin, a 64-pass point (25 k steps, ≈ 50 min on the 3060) first would say
  whether the margin stabilises or keeps closing; not proposed by this instance.

- **2026-09-09, 12:35 — H4 `gcnn8_c1_300_e4` DONE (12:21, after 19.8 h of distinct iterations, 20.45 h of GPU
  time with the nine re-run ones; attempt 1 from 260) — hurt.** The D4 group-convolutional net (`--gcnn 16`: 16 base
  filters × 8 orientations = activation width 128, 312 k parameters against the ResNet's 2.46 M, exported to plain
  convolutions so it costs what the 8×128 ResNet costs to evaluate) on `deep8_c1_300_e4`'s recipe, nothing else
  changed. **Primary `paired_vs_deep8c1_300e4_64.json`: 22.0 % [19.9, 24.2], −220 Elo [−242, −199] against the
  parent — hurt**, 25 points below the rule's line and eight seed bands; the worker's independent read of the same
  checkpoint agrees (22.0 [19.9, 24.3]). Secondary: 31.6 % [29.2, 34.2], −134 vs `deep8_c1_300_e2`; **42.8 % [40.2,
  45.4], −50 [−69, −32] vs deep8_c1_300** — below the 1×-update ResNet of the same shape and duration; 37.1 %, −92 vs
  deep10_c1_300 and 41.5 %, −59 vs its replicate; +79 vs deep8_c1 (150 iterations), +114 vs wide128_c1, **71.7 %
  [69.2, 74.1], +162 [+141, +182] vs v2b**, +260 vs dev1. On the ladder it lands between deep8_c1 (+100) and
  deep8_c1_300 (+211), with four times the updates of either. **The pre-registered secondary, exact symmetry, holds:
  D4 JS 0.000 bits and value std 0.000 at all 30 checkpoints** (`runs/plan6/H4_timeline.out`, `timeline.{json,png}`;
  the ResNet's 0.026 / 0.052) — the equivariant export survived the fused fp16 graph path for the whole run, and
  exact symmetry is not what was missing. Tertiary: endgame_v1 raw WDL **80.8 % [79.4, 82.2]**, draw recognition
  60.5 %, regret 0.058 [0.048, 0.068], optimal 95.1 % (parent 90.1 / 79.0 / 0.022 / 98.1; deep8_c1_300 84.0 / 0.045;
  the 150-iteration deep8_c1 77.6 / 0.064); endgame_v2_dev 82.5 [81.1, 83.8], draws 68.1 %, regret 0.056 (parent
  90.5 / 0.029); the 256-sim search 99.8 / 99.7 % optimal, regret 0.002 / 0.003 — search repairs the raw head here
  as everywhere. The full-suite curve (`eval_full.jsonl`, ±2.8; the parent's beside it):

  | iteration | 10 | 50 | 100 | 150 | 200 | 210 | 220 | 260 | 280 | 290 | 300 |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | H4 vs v2b | 8.0 | 22.0 | 32.9 | 39.9 | 29.4 | 60.1 | 65.4 | 65.2 | 66.3 | 73.6 | 71.7 |
  | parent vs v2b | 24.7 | 67.0 | 75.0 | 79.1 | 80.5 | 86.1 | 87.3 | 86.6 | 87.2 | 88.1 | 89.0 |
  | H4 vs the parent's final net | 0.7 | 1.8 | 4.8 | 5.9 | 5.1 | 15.7 | 17.6 | 19.3 | 18.9 | 21.7 | 22.0 |

  Two things no ResNet showed. (i) The first drop is worth **+30.7 points** to it (29.4 → 60.1; +223 Elo) against
  the ResNets' +4.8 … +8.5, after a constant-LR phase in which it *lost* ground from 150 to 200 (39.9 → 29.4) while
  the parent gained; (ii) **the second drop is a resolved step, +6.5** (65.2 at 260 → 71.7 at 300; the worker's
  280 / 290 reads 66.3 / 73.6), where F2 found it nothing on four ResNets (+2.6 / +4.1 / −0.4 / −0.3): each LR
  reduction lowers this net's floor by more than the ResNet's — the sharper basin (λ_max 2.3×, the mechanism
  paragraph) read at play strength. Budget axes (E8; the logs de-duplicated by iteration, attempt 1 for 260–268):
  132 of 307 200 steps skipped (parent 133); replay age 3.31 (3.31); sampled distinct-position fraction 0.63 → 0.67
  (0.63 → 0.63); target entropy 0.162 bits (0.165); raw/search KL 1.83 → 1.02 (1.49 → 0.85); root Q range 0.48 → 0.46
  (0.36 → 0.49); policy loss 1.12 against 1.00 and value loss 0.73 against 0.67 over the last 20 iterations;
  self-play 51.9 plies (52.8), draws 14.1 % (16.6), count endings 13.7 % (16.5). Cost: t_selfplay 12.21 h (11.93 —
  the exported net costs what the ResNet costs at play, as claimed), t_train 7.58 h (4.98 — the per-step weight
  expansion and the per-iteration re-export), wall 19.8 h (16.9). **Reading: hurt, decisively, with no instability
  and exact symmetry intact — the supervised gate (48) certified an ordering at 3 120 steps that reverses by 12 480
  (the sweeps, above), and self-play at 307 200 steps read the reversed ordering.** The G-CNN is not proposed again
  at this width; the equal-cost requirement rules out a wider one; the tied-heads hedge waits for sweep 3. The play
  agent stays `deep8_c1_300_e4/net_0300.pt`. KNOWLEDGE 50 (48 restated); RETROSPECTIVE §2, §3, §5, §7; README.

- **2026-09-09, ~13:30 — the owner's decisions after H4: the chain is closed, three items are approved, and the
  project's remaining work is named.** Read against H4's result (hurt, decisively, with exact symmetry intact) and
  the instance's assessment of what was left to propose. Recorded in full as **§9**; in short:
  **Dropped.** *H3 `deep8_c1_600_e4`* — not run. As written it doubles data, updates and teacher exposure together,
  the confound §0 was written to remove; the update axis has been separated twice (46, 49), the data and teacher
  axes never, and a 600-iteration run at E = 4 buys the bundle again for ≈ 35 h without saying which term moved.
  `runs/queue12.sh` and its two launchers stay in the repo as **staged but withdrawn**. *H5 `--head_tying 1`* —
  not proposed. Sweep 3's margin closes across the three doublings (0.036 / 0.027 / 0.022, the 13:01 entry), so the
  honest prediction is null-to-small — inside the seed band — and exact policy symmetry has no consumer: the
  analysis tools already hold the exact 8-way average (41b), which is itself a null at play.
  **Approved, in launch order.** (1) **H1c `deep8_c1_300_e8`** on the 3090, ≈ 22–23 h: the third doubling of the
  optimizer steps (2048 per iteration), parent `deep8_c1_300_e4`, `runs/queue13.sh` copied from queue11's form and
  launched with `wscript runs/launch_queue13_hidden.vbs`. Primary vs the parent on the full suite @64 by the rule;
  the readings — *helped* → still update-limited at eight passes, *null* → the plateau is between four and eight
  passes and +164 is the update lever's total, *hurt* → the buffer window is over-fitted, so the buffer is the knob
  — are §9a. (2) **G arm (g) `gcnn8x46`** on the 3060: the D4 G-CNN at the ResNet's *parameter* count, to separate
  capacity from equivariance in H4's result. The width was chosen by building the nets, not estimated — 46 base
  filters × 8 orientations (activation width 368) is 2 459 392 parameters against resnet8's 2 456 014; 44 would be
  8 % short. It is **not** an equal-cost arm: the exported trunk is 368 filters wide, ≈ 8× (measured 7.0×) the ResNet's convolution
  work by the square of the width, to be measured with `tools/gtiming.py` and declared before anything else is
  said about it. Supervised on `gdata_v1` at lr 0.02 × 8 / 16 / 32 passes, **read at 12 480 steps** as 48's
  restatement requires: a margin over resnet8 that is not closing → the bias is right at equal capacity and a
  self-play run becomes a proposable science question (never a ladder rung, at that cost); a trailing or closing
  margin → the bias is wrong for this game at any affordable capacity and the equivariant line closes.
  (3) **I1**, the analysis second pass on `deep8_c1_300_e4/net_0300.pt` (+363): the net-dependent Phase A tools at
  the deep10 pass's settings, so every §1–§8 claim quoted from deep10 (+242) is re-read 120 Elo higher and the
  method's own central claim — orderings and signs stable, magnitudes saturating — is tested on the strongest net
  for the first time. Per claim: **held / moved / reversed**, defined in §9c; outputs `runs/plan6/I1_*.out`.
  **Then E11:** the owner will create an empty GitHub repository once the three are done; the instance pushes and
  copies `runs/*/games`, the remaining `net_*.pt` and `suites/` off-machine. **Nothing else is proposed.** The
  chain H1b → H4 → H3 is closed with H3 withdrawn. §9, the Handover, README and RETROSPECTIVE §7 carry this.

- **2026-09-09, 21:25 — the closing programme launched.** H1c `deep8_c1_300_e8` at 21:24 through `wscript
  runs/launch_queue13_hidden.vbs` (`runs/queue13.sh`: queue11's form with `--gcnn 16` dropped and `--epochs 8`; the E7
  worker beside it on the 3060 with anchors v2b, the parent `deep8_c1_300_e4`, deep8_c1_300 — the 1× point every
  earlier curve shares; ≈ 22–23 h, so DONE ≈ 20:00 on 2026-09-10 plus `eval_run.sh`). The 3060 queue
  `runs/plan6/closing_3060.sh` at 21:25, detached (hidden bash): `G_arm_g_3060.sh` first — `gcnn8x46` (2 459 392
  parameters against resnet8's 2 456 014; **measured cost 7.0× resnet8 at batch 4096 on the 3060, 595 vs 85 ms, 1.28×
  at batch 1**, `runs/plan6/G_timing_3060_gcnn8x46.json`; the arm added to `tools/gstudy.py`, `--arms` added to
  `tools/gtiming.py`), 400k × 32 / 8 / 16 passes in that order, ≈ 9–10 h with the worker sharing the card → `G_arm_g.out`,
  `G_arm_gcnn8x46.json` — then `I1_second_pass_3060.sh` (14 tools, cheapest first, ≈ 4–5 h → `I1_second_pass.out`,
  `I1_*.out`, `suites/puzzles_v3_dev.npz`, `runs/probe_data_deep10late_e4.npz`, `runs/book_deep8_e4.json`,
  `runs/deep8_c1_300_e4/{probes,value_decomp}.*`). Two reconstructions in I1 are flagged in its header: the
  `tablebase_grade` invocation (no recorded one; PLAN5 C5's text plus the tool's defaults) and the book's `--paired`
  file (the parent match `paired_vs_deep8c1_300e2_64.json`, since `_e4` has no self-match). The instance that launched
  is above the 50 % line: the readings and write-ups (§9's pre-registered rules) fall to the next instance, from this
  Handover. E11 after all three: the owner creates the empty GitHub repository, then push and the off-machine copy.

- **2026-09-10, 07:30 — G arm (g) read (§9b): the matched-parameter G-CNN over-fits the frozen set; the pre-registered
  reading closes the equivariant line under this protocol, with a caveat.** `gcnn8x46` (2 459 392 parameters; 7.0×
  resnet8's cost at batch 4096, measured) on `gdata_v1` at lr 0.02, seed 0, dev policy KL against the teacher (resnet8 /
  gcnn8x16 at the same steps in brackets; `runs/plan6/G_arm_gcnn8x46.json`, 21:24–02:27 on the 3060 shared with the E7
  worker): 3 120 steps **0.7636** [0.884 / 0.806] — the best fit of any student at the gate's step count, top-1 0.639;
  6 240 steps **0.9195** [0.8145 / 0.7875]; 12 480 steps **1.0336** [0.7630 / 0.8298]; its KL on the dev positions with
  no canonical twin in train 1.033 → 1.322 → 1.516 (the ResNet's 0.960 → 0.931 over the last doubling); endgame_v2_dev
  raw WDL 69.4 / 68.4 / 67.0 %, regret 0.140 / 0.164 / 0.159; D4 residual 0 at every point. **Reading by the rule: it
  trails resnet8 at 12 480 steps and the margin does not close but reverses by 6 240 — the equivariant line closes;
  nothing is proposed.** The caveat, stated because the rule was written before the 8-pass point was seen: at 3 120
  steps the wide G-CNN extracts more per step than any net measured, and what follows is memorisation of 400 000
  positions for which D4 augmentation is an exact no-op (the ResNet sees eight views of each) — so the protocol shows
  the wide net data-limited by ≈ 8× at equal capacity where the ResNet is not, and cannot say whether its self-play
  prospect (fresh data every iteration) differs from the narrow net's. A data-matched supervised test would need ≈ 8×
  `gdata_v1` (≈ 40 h of teacher labelling on the 3090) and is not proposed: the 7.0× inference cost disqualifies the net
  as a rung, and the project's purpose does not need the answer. KNOWLEDGE 48 / 50 / §10 restated. I1 finished 07:23
  (its reading follows in the next entry); H1c at iteration 147 at 07:26, ETA 20:23, the worker's curve 81.1 % vs v2b at
  140 (H1b: 79.1 at 150) and 35.1 % against H1b's final net.

- **2026-09-10, 08:10 — I1 read (§9c): the second analysis pass on the +363 net. Of 34 claims re-read, 15 held, 18
  moved, 1 reversed.** Every net-dependent PLAN5 Phase A tool re-run on `runs/deep8_c1_300_e4/net_0300.pt` at the
  deep10 pass's settings, 02:27–07:23 on the 3060 beside H1c's worker; `runs/plan6/I1_second_pass_3060.sh`, outputs
  `runs/plan6/I1_*.out`, every exit code 0. **The reversal is claim 7.** After [40] this net's book puts **0.71 of
  its visits on the corner reply orbit 36** and 0.29 on the edge orbit 37 — the mirror of deep10's 0.75 / 0.25 and
  deep8_300's 0.54 / 0.46 — and rates the *edge* subtree +0.022 better for X where both earlier nets rated the corner
  +0.016 better; its atlas says 36 at 1k, 4k and 16k where all nine earlier columns said 37. One ordering in
  KNOWLEDGE is therefore strength-relative, and it flipped between +242 and +363. **Held (15):** 1, 8 (+0.1953 ±
  0.0278 against deep10's +0.196 ± 0.028), 11, 13, 17, 19, 21, 26, 31a (100 / 100 / 100 on 689 one-open-board
  positions), 33, 34, 35, 36, 38, 40 (70.8 % late ownership against 51.1 / 53.6 / 65.9). **Moved (18):** the opening
  sharpens — 2 (τ vs v2b@16k 0.96 → 0.85), 3 (+0.495), 4 (flat after 9 of 15, range median 0.150), 5 ([13] 0.142,
  plus a new non-[40] exception after [2], 0.073), 7a (self-send 55 / 58 → 48 %); games settle earlier — 20 (Q 34 on
  strong play against 36, raw 39 against 41), 22, 23 (policy disagreement 33.6 → 30.8 %, the value gap unchanged at
  0.19); the corpus moves — 24 (X 62.7 / O 20.7 / draws 16.6), 25 (the count rule decides a third, not a quarter),
  27 (52.8 plies, 5.08 free moves); the regressions shrink — 9 (+0.117, so "halves" is 0.60 here), 10 (+0.30 late,
  and the middlegame now runs with the count, −0.16 to +0.24), 14 (+0.02 … +0.05), 16 (+0.022); the net reads better
  and earlier — 32 (raw failures 2.1 → 1.0 %, search 0.12 → 0.03 %), 37 (the same gains 20–50 iterations earlier),
  39. **Not re-read:** 6, 12, 15, 18, 38a (their tools are not in §9c's table); 28–31 were already read on this net.
  Two caveats: the new book's paired X-score column uses the parent match, not a self-match, so it is not comparable
  with the earlier books'; and `principles.py`'s solved-position column is a property of the held-out set, not of the
  net (it reproduces deep8_300's digits exactly). **On the method (PLAN5 §1c):** signs and orderings survive 120 Elo
  with one exception, and that exception sits where two lines are within 0.02 of each other; PLAN5 §2's "the
  magnitudes saturated between deep8_300 and deep10" is wrong for the count rule, the draw share and the settling
  ply, which all resumed moving. KNOWLEDGE header, §1 note, 1–5, 7, 7a, 8–11, 13, 14, 16, 17, 19–27, 31a–40, §10
  restated; RETROSPECTIVE §6 and §7. Two of §9's three items are read; H1c remains (DONE ≈ 20:30, then its write-up
  by §9a's rule), then E11.

- **2026-09-10, 19:45 — H1c `deep8_c1_300_e8` DONE (19:22, 21.96 h, 0 crashes) and read (§9a): helped, +40 — the third
  doubling of the optimizer steps is worth about two-thirds of the second.** `deep8_c1_300_e4`'s recipe with
  `--epochs 8` (2048 steps of batch 1024 per iteration, 614 400 in the run), nothing else changed. **Primary
  `paired_vs_deep8c1_300e4_64.json`: 55.8 % [53.3, 58.2], +40 Elo [+23, +57] against the parent — helped by the rule**,
  2.8 points over the line and within one ≈ 3-point seed band of it (the worker's independent read of the same
  checkpoint: 55.8 [53.4, 58.2]). Secondary: 65.3 % [62.8, 67.8], +110 vs `deep8_c1_300_e2`; 77.1 %, +211 vs
  deep8_c1_300; 74.5 %, +186 vs deep10_c1_300; 76.1 %, +201 vs its replicate; +311 vs deep8_c1, +334 vs wide128_c1;
  **89.0 % [87.2, 90.7], +363 vs v2b — the same 89.0 as H1b's: the v2b yardstick has saturated at this strength**
  (differences compress near 90 %; the head-to-head is the instrument); 95.3 %, +523 vs dev1. **The dose–response:
  +100 (256 → 512 steps per iteration), +64 (→ 1024), +40 [+23, +57] (→ 2048)** — each doubling about two-thirds of the
  last, +204 in all, still not the plateau at eight sampled examples per generated position. The E7 curve (±2.8):

  | iteration | 10 | 50 | 100 | 150 | 200 | 210 | 220 | 260 | 280 | 290 | 300 |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | H1c vs v2b | 32.1 | 74.1 | 78.6 | 81.2 | 82.4 | 86.4 | 88.3 | 89.9 | 90.4 | 90.5 | 89.0 |
  | H1b vs v2b | 24.7 | 67.0 | 75.0 | 79.1 | 80.5 | 86.1 | 87.3 | 86.6 | 87.2 | 88.1 | 89.0 |
  | H1c vs H1b's final net | 7.0 | 22.5 | 31.4 | 33.6 | 33.7 | 49.9 | 50.9 | 52.3 | 51.0 | 53.6 | 55.8 |

  Ahead of H1b at every checkpoint before the drop (most of it early, +7.1 at 50), level with H1b's *final* net by
  210, the first drop worth +4.0 (82.4 → 86.4), then 1–3 points ahead through the low-LR phase; the second drop
  nothing, as on every ResNet. Tertiary: endgame_v1 raw WDL **91.3 % [90.3, 92.4]**, draws 81.0 %, regret 0.022,
  optimal 98.1 % (H1b 90.1 / 79.0 / 0.022 / 98.1); endgame_v2_dev 91.7 [90.7, 92.7], draws 83.6 %, regret 0.020
  (H1b 90.5 / 0.029); the 256-sim search 100.0 % optimal, regret 0.000 on both sets. Timeline
  (`runs/plan6/H1c_timeline.out`): endgame WDL 87.0 → 89.9 across the drop, 91.3 at 300; **D4 JS 0.025 bits, value
  std 0.047** (H1b 0.026 / 0.052) — eight passes bought no more symmetry consistency than four or two. Budget axes
  (E8): 244 of 614 400 steps skipped (H1b 133 of 307 200, the same rate); replay age 3.31 (3.31); **sampled
  distinct-position fraction 0.48 → 0.45** (H1b 0.68 → 0.63, H1 0.81 → 0.75 — each generated row now drawn about eight
  times, and nothing complains: policy loss 0.992 against 1.001, value 0.653 against 0.667 over the last 20
  iterations); target entropy 0.18 bits (0.165); raw/search KL 1.49 → 0.85 (the same); root Q range 0.36 → 0.51
  (0.49); self-play 53.2 plies (52.8), draws 16.6 % (16.6), count endings 15.7 % (16.5). Cost: t_train 9.97 h vs
  4.98, t_selfplay 11.98 vs 11.93, wall 21.96 h vs 16.92 (t_iter 282 s against 225 late); the same 8×128 ResNet, so
  the +40 is free at play time. **Reading: helped — still update-limited at eight passes; the curve is stated. The
  play agent changes to `runs/deep8_c1_300_e8/net_0300.pt`.** Not proposed: `--epochs 16` (the obvious next point,
  ≈ +5 h of training for a predicted +25; §9's programme is complete as the owner set it). KNOWLEDGE 51 (46, 49,
  43, 44, header restated); RETROSPECTIVE §2, §3, §7; README. §9 is done: E11 follows (the owner creates the empty
  GitHub repository; then push, and the off-machine copy of `runs/*/games`, the remaining `net_*.pt` and `suites/`).

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

## 9. The closing programme (owner's decisions, 2026-09-09)

After reading H4's result and the instance's assessment, the owner closed the chain and approved
three items — one training run, one supervised arm, one analysis pass — and no more. Two proposals
are dropped. Nothing else is proposed: when these three are done the project's remaining work is the
off-machine backup (E11) and the write-up.

**Dropped.**

- **H3 `deep8_c1_600_e4` — withdrawn, not run.** As written it doubles data, updates and teacher
  exposure together: exactly the confound §0 was written to remove. The project has now separated
  the update axis twice (46, 49) and has never separated the data axis from the teacher axis; a
  600-iteration run buys the confounded bundle again for ≈ 35 h, and its "flat or climbing" reading
  cannot say which of the three moved. `runs/queue12.sh`, `runs/launch_queue12_run.cmd` and
  `runs/launch_queue12_hidden.vbs` **stay in the repo as staged but withdrawn** — a correct recipe
  for a run the owner has decided not to buy, kept so the shape is on record. They are not to be
  launched.
- **H5 `--head_tying 1` on the `deep8_c1_300_e4` recipe — not proposed.** Two reasons, neither
  fatal alone. Sweep 3's margin over the plain ResNet closes across the three doublings — 0.036 /
  0.027 / 0.022 at 3 120 / 6 240 / 12 480 steps (the log's 13:01 entry) — and a straight line in
  log-steps reaches zero near the run's 307 200, so the pre-registered prediction is null-to-small:
  a predicted effect inside the ≈ 3-point seed band. And the thing it buys, exact policy symmetry in
  the read-out, has no consumer: every analysis tool already uses the exact 8-way average
  (`uttt/symmetry.py`), which is itself a null at play (41b), and the canonical evaluator is a null
  too (F1). A GPU-day for a predicted null whose product nothing reads is not the right purchase
  here.

**Approved, in this order of launch: H1c on the 3090, then arm (g) and I1 on the 3060.**

### 9a. H1c `deep8_c1_300_e8` — the third doubling of the optimizer steps (3090, ≈ 22–23 h) — **done 2026-09-10 19:22, read in the log (19:45): helped, +40 [+23, +57]**

**Recipe.** `deep8_c1_300_e4`'s recipe with `--epochs 8` and nothing else changed: **2048 optimizer
steps of batch 1024 per iteration** (`n_steps = epochs × games × steps / batch` = 8 × 4096 × 64 /
1024, `train2.py:356`), 614 400 in the run against H1b's 307 200; the same 4096 × 64 new positions
per iteration, the same 2 M-row buffer, LR drops at 200 / 280, seed 0. Parent `deep8_c1_300_e4`.

**Purpose.** The dose–response curve of 46 / 49 — +100 for the first doubling of the update count,
+64 for the second, then what — read to its asymptote or its plateau. Either is a finding, and this
is the last cheap point on the axis: at eight passes each generated position is sampled eight times
in expectation from a buffer window of 7.6 iterations, so the run is also the first direct test of
the over-fitting branch H1's reading wrote and never fired.

**Cost.** t_train ≈ 10 h against H1b's 4.98 (training is the only term that doubles); self-play
unchanged at ≈ 12 h, because the net is the same 8×128 ResNet and plays and evaluates at exactly
H1b's cost; wall ≈ 22–23 h against 16.9. Inside the update pause (2026-10-14) with room to spare.

**Operational settings, as every chain run.** Copy `runs/queue11.sh`'s form: the 6-attempt retry
wrapper, `--eval_every 0 --ckpt_every 10 --anchors ""`, and the E7 worker
(`tools/eval_worker.py --run runs/deep8_c1_300_e8 --anchors runs/v2b/net_0150.pt,runs/deep8_c1_300_e4/net_0300.pt,runs/deep8_c1_300/net_0300.pt --sims 64 --set suites/endgame_v2_dev.npz --poll 60 --device cuda:1`)
on the 3060 with anchors v2b, the parent `deep8_c1_300_e4` and `deep8_c1_300`; then
`bash runs/eval_run.sh deep8_c1_300_e8 cuda:0` and the `endgame_v2_dev` read
(`tools/endgame.py eval runs/deep8_c1_300_e8/net_0300.pt --set suites/endgame_v2_dev.npz`) at the
end. Files: `runs/queue13.sh` + `runs/launch_queue13_run.cmd` + `runs/launch_queue13_hidden.vbs`
(sed the names from queue11's), launched with **`wscript runs/launch_queue13_hidden.vbs`** from the
repo root. `eval_run.sh` discovers the last `net_*.pt` by itself; the queue's own endgame line must
say `net_0300.pt`. Status: `python tools/run_status.py runs/deep8_c1_300_e8 --ref runs/deep8_c1_300_e4`.

**Pre-registered reading.**

- *Primary:* the final net vs `deep8_c1_300_e4` on the full paired suite @64 —
  **≥ 53 % helped, ≤ 47 % hurt, otherwise null** — with the seed band (≈ 3 points) stated beside it.
- *Secondary:* vs `deep8_c1_300_e2` and `deep8_c1_300`, so the dose–response is read as a curve
  across 1× / 2× / 4× / 8× the updates and not as one more pairwise step; the E7 full-suite curve
  against H1b's at matched iterations (does the constant-LR phase lift again, and by how much less);
  and the budget axes for over-fitting the buffer window (E8's per-iteration fields) — the sampled
  distinct-position fraction (H1 0.81 → 0.75, H1b 0.67 → 0.62; eight passes should read lower again),
  the skipped-step count (H1 70 of 153 600, H1b 133 of 307 200 — the same rate) and the policy
  loss's late trend.
- *Tertiary:* the endgame reads on `endgame_v1` and `endgame_v2_dev` against H1b's **90.1 % raw
  WDL / 79.0 % draw recognition / 0.022 regret**.

**Readings, written before the run.** *Helped* → the learner is still update-limited at eight
passes; state the curve (+100, +64, +X) and where it puts the plateau. *Null* → the plateau lies
between four and eight passes at this data rate, the update lever is exhausted, and the **+164** of
the first two doublings stands as its total. *Hurt* → the buffer window is over-fitted at eight
passes, which is itself the finding — the buffer, not the update count, is the knob. The play agent
changes only if it helps.

**Reboot recovery.** Windows Update is paused until **2026-10-14**, and a reboot is the one failure
the retry wrapper cannot cover (the log's 08:25 entry: the bash wrapper dies with the session). If
the machine restarts mid-run, **relaunch the same `.vbs`** — `train2` prefers `latest_full.pt` and
restarts from the last buffer save as a perturbed continuation (`attempt: N`; de-duplicate
`log.jsonl` by iteration when reading it), and the worker skips what `eval_full.jsonl` already holds.

### 9b. G arm (g) `gcnn8x46` — the G-CNN at the ResNet's parameter count, on frozen data (3060) — **done 2026-09-10 02:27, read in the log (07:30): the equivariant line closes**

**Purpose.** Separate *capacity* from *equivariance* in H4's negative result. The sweeps read H4 as
capacity rather than the learning rate (50, 48 restated), but the only equivariant net this project
has ever trained carries **312 k parameters against the ResNet's 2.46 M**, so the outsider's
question is still open: is the inductive bias wrong for this game, or was the net simply too small?
Phase G exists to answer exactly this kind of question on frozen data for no GPU-day.

**The arm.** The same D4 regular-representation G-CNN (`uttt/equivariant.py`) at the base width that
matches the ResNet's parameter count. Trunk parameters scale with the square of the base width, so
the width was picked by building the nets rather than estimated: 8 blocks at **46 base filters × 8
orientations = activation width 368** has **2 459 392 parameters** against resnet8's **2 456 014**
(0.1 % apart); 44 base filters gives 2 251 710, 8 % short. One line in `tools/gstudy.py`'s `ARMS`:
`"gcnn8x46": lambda: NetConfig(blocks=8, filters=368, gcnn=46)` — `filters == 8 * gcnn` is asserted
in `uttt/equivariant.py`, and `tools/gtiming.py` iterates `ARMS`, so the new arm is timed for free.

**Cost — and the number to measure before queueing.** This is **not** an equal-cost arm and must
never be written as one. The exported net is an ordinary 368-filter ResNet, and trunk convolution
work scales with the square of the activation width: (368 / 128)² ≈ **8×** the 8×128 ResNet's — **measured 7.0× on the 3060: 595 vs 85 ms per 4096 evaluations, 1.28× at batch 1** (`runs/plan6/G_timing_3060_gcnn8x46.json`, both cards idle, 2026-09-09 21:00) — not
the ≈ 2.5× a parameter-count intuition suggests (the G timings are compute-linear — resnet10 is
1.24× resnet8 at a 1.25× block ratio, 41.1 vs 33.2 ms per 4096 on the 3090). Measure it first —
`python tools/gtiming.py --device cuda:0 --out runs/plan6/G_timing_wide_3090.json`, batch 4096 and
batch 1, both cards — and **declare the measured number up front in every sentence about this
arm**. Budget the 3060 accordingly: gcnn8x16's 12 480-step point took ≈ 28 min there (sweep 2), so
the wide arm's three points are a large fraction of a 3060-day rather than the ≈ 3 h the width-128
arms cost. If the card is wanted for I1, the 12 480-step point is the one that must exist.

**Settings.** Supervised on `runs/gdata_v1.npz` through `tools/gstudy.py`:
`--arm gcnn8x46 --positions 400000 --passes 8,16,32 --seeds 0 --lr 0.02 --device cuda:1 --out runs/plan6/G_arm_gcnn8x46.json`
— 3 120 / 6 240 / 12 480 steps, the same three step counts the sweeps used, against the points
already on file (dev policy KL vs the teacher):

| steps | 3 120 | 6 240 | 12 480 |
|---|---|---|---|
| resnet8 (2.46 M) | 0.884 | 0.8145 | **0.7630** |
| gcnn8x16 (312 k) | 0.806 | 0.7875 | **0.8298** |

Dev slice only; `endgame_v3_test` stays sealed.

**Pre-registered reading, taken at 12 480 steps** — as KNOWLEDGE 48's restatement now requires: a
supervised gate is read at a step count of the order of the run's, or until the curves have crossed
or clearly will not.

- The wide G-CNN **leads resnet8 at 12 480 steps with a margin that is not closing across the three
  doublings** → the inductive bias is right at equal capacity, H4's result was the 312 k parameters,
  and a self-play run at this width becomes a **proposable science question** — with its *measured*
  inference cost declared up front, and explicitly not a ladder rung: the ladder is read at a fixed
  inference budget and this net costs several times the ResNet's per evaluation.
- It **trails, or its margin closes as gcnn8x16's did** → the bias is wrong for this game at any
  capacity this project can afford. Recorded as a finding in KNOWLEDGE 48 / 50, and **the
  equivariant line closes**.
- Two seeds at the 32-pass point (`--seeds 0,1`) if the margin there is inside 0.005.

### 9c. I1 — the analysis second pass on the strongest net (3060, hours) — **done 2026-09-10 07:23, read in the log (08:10): 15 held, 18 moved, 1 reversed**

**Purpose.** The project's central methodological claim is PLAN5 §1c's: orderings and signs are
stable across strength, magnitudes drift and saturate. It has been tested once, in Phase A at +242,
where every ordering and sign held and two magnitudes moved (PLAN5 §2). The strongest net is now
`runs/deep8_c1_300_e4/net_0300.pt` at **+363** — 120 Elo above the net from which every §1–§8 claim
in `KNOWLEDGE.md` is quoted — and it has never been used to test the claim; the KNOWLEDGE header
says so in as many words ("the game claims of §1–§8 have not been re-run on it, and 'strongest net'
in those sections still means deep10"). I1 closes that gap, and it is the last thing the project
owes its own method.

**What runs.** The net-dependent tools of PLAN5 Phase A at **the same settings as the deep10 pass** —
`runs/plan5_A_3060.sh` and `runs/plan5_A_3090.sh` are the record of those settings, and
`runs/plan5_A.out` and `runs/plan5_B.out` of what they cost — with `deep8_c1_300_e4/net_0300.pt` as
the net under test and held-out positions from **another run's games** as before (PLAN5 §8:
`deep10_c1_300`'s or `deep8_c1_300`'s iterations 280–299, neither of which `_e4` trained on).
Everything runs on the **3060** because the trainer holds the 3090 — including `tools/book.py`,
whose `--device` defaults to `cuda:0` and must be passed `--device cuda:1` explicitly (every other
net-dependent tool below already defaults to `cuda:1`; `corpus_stats.py` and `principles.py` take no
device and are CPU work). The E7 worker shares the card while H1c runs: ≈ 6 min per checkpoint every
≈ 43 min (an `--epochs 8` iteration is ≈ 264 s, checkpoints every 10), so the card is about a
seventh busy.

| tool | claims it re-reads | settings, as in the PLAN5 pass | measured cost on that pass |
|---|---|---|---|
| `tools/atlas.py` | 1–5 | `--nets <net> --budgets 1024,4096,16384 --out runs/plan6/I1_A1_atlas.json` | 16.6 min for **three** nets on the 3090 (`runs/plan5_A.out`, 00:36:04 → 00:52:39); one net on the 3060 is about the same |
| `tools/book.py`, `tools/book_stats.py` | 7, 7a | `--depth 4 --top 3 --sims 16384 --batch 64 --compare runs/book_deep8.json --device cuda:1` | **38 min on the 3060** at 579 nodes (E1; deep10's was 28 min on the 3090) |
| `tools/freemove.py` | 8, 10, 11, 13, 14 | `--corpus runs/deep10_c1_300 --last 20 --sims 256` | 5.0 min (00:43:20 → 00:48:21) |
| `tools/value_decomp.py` | 9, 14–19 | `--data <probe npz> --n 20000 --sims 256 --only <checkpoints>` | 62 min over every checkpoint, 30 min over 11 (`runs/plan5_B.out`); the final checkpoint alone is minutes |
| `tools/decision.py` | 20–22 | `--corpus runs/deep10_c1_300 --last 20 --games 4000 --sims 64` | 6.7–8.7 min per corpus |
| `tools/surprise.py` | 23 | `--buffer runs/deep8_c1_300/latest_full.pt --sims 256 --n 8192 --top 30` | 1.2 min |
| `tools/corpus_stats.py` | 24, 25, 27 | `runs/deep8_c1_300_e4 --last 20` | 38 s, CPU |
| `tools/principles.py` | 26, 33–35 | `--data <probe npz> --corpus runs/deep8_c1_300_e4 --last 20` | minutes, CPU (needs the probe npz below) |
| `tools/puzzles.py` | 32 | `--corpus runs/deep10_c1_300 --last 20 --max_empty 14 --n 6000 --processes 12 --out suites/puzzles_v3_dev.npz` | 42 s |
| `tools/tablebase_grade.py` | 31a | as PLAN5 C5 | minutes; the table is 1 MB and builds in 0.2 s |
| `tools/probe.py build` + `fit --control`, `tools/probe_report.py`, `tools/ownership_grade.py` | 36–40 | `build --corpus runs/deep10_c1_300 --last 20 --net <net>`; `fit --data <npz> --run runs/deep8_c1_300_e4 --control --only <16 checkpoints>` | build 5.1 min; fit **55–61 min on the 3090** over 16 checkpoints → ≈ 2–2.5 h on the 3060, which PLAN5 §7's budget ("under one 3090-day plus two 3060-days" for §2–§4) prices within a few hours — so the probes are **in**, at the same 16-checkpoint grid |

The endgame reads are already done and need no re-run: `runs/deep8_c1_300_e4/analysis.out` carries
endgame_v1 **90.1 / 0.022** and endgame_v2_dev **90.5 / 0.029** (28–31; the log's H1b entry).
`suites/` stays frozen — a new puzzle set is a new name (`puzzles_v3_dev.npz`), never a rewrite of
`puzzles_v2_dev.npz`.

**Pre-registered reading, per claim** — written before the pass, exactly three verdicts:

- **held** — the sign and the ordering agree with the deep10 reading *and* the new magnitude is
  inside the earlier CI. The claim's *held across* list gains "all four strong nets".
- **moved** — the sign and the ordering agree, the magnitude is outside the earlier CI. Report the
  new magnitude; the claim's "grew with strength" clause is updated with the third point, and PLAN5
  §2's closing "the magnitudes saturated between deep8_300 and deep10" is re-read against it.
- **reversed** — a sign or an ordering disagrees. The claim is restated as budget- or
  strength-relative, and the restatement says at which strength it flipped. This is the outcome the
  method says cannot happen; if it does, it is the most important line in the file.

**Outputs.** `runs/plan6/I1_*.out`, one per tool, as PLAN5 did — `runs/plan5_A<row>_*.out` becomes
`runs/plan6/I1_A<row>_*.out` — plus the run's own directory for anything a run owns, and a results
table appended to this section with every row marked held / moved / reversed.

**Write-up.** Each affected claim in `KNOWLEDGE.md` gains "all four strong nets" in its *held
across* list or its new magnitude; the header's "strongest net" sentence is updated (it currently
records the gap this pass closes); RETROSPECTIVE §6 and the explainer's Part 8 are edited only if a
number moves.

### 9d. Order, GPU roles, and what follows

| when | 3090 | 3060 |
|---|---|---|
| from H1c's launch, ≈ 22–23 h | **H1c** (`queue13`), start to `analysis.out` | **G arm (g)** first (hours), then **I1** (hours) — with the E7 worker sharing the card, ≈ 6 min per checkpoint every ≈ 43 min |
| after all three | idle | idle |

The trainer never shares the 3090 (§8); one CUDA device per process; the worker is a `cuda:1`
process by construction.

**Then E11, the backup**, deferred since Phase E for want of a destination. **The owner will create
an empty GitHub repository once these three items are done.** The instance then
`git remote add origin <url>` and `git push -u origin main`, and copies the things git does not
carry off this machine as §2 E11 specifies: `runs/*/games` (≈ 160 MB per 300-iteration run), the
remaining `net_*.pt`, `log.jsonl` and `config*.json`, and `suites/`. `runs/` is ≈ 11 GB.

**Nothing else is proposed.** The chain H1b → H4 → H3 is closed with H3 withdrawn; H5 is not
proposed; the G-CNN is not proposed again at width 128, and a wider one enters self-play only
through 9b's reading and only with its measured cost declared. After H1c, arm (g) and I1 the open
list is the write-up and the backup.
