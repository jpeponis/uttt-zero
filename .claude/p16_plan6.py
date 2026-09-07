import pathlib, sys

Q3 = sys.argv[1] if len(sys.argv) > 1 else "(pending)"
Q4 = sys.argv[2] if len(sys.argv) > 2 else "(pending)"


def sub(path, pairs):
    p = pathlib.Path(path)
    s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:80], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")


LOG = """- **2026-09-07, H1 — `deep8_c1_300_e2` (owner-approved 2026-09-06, launched 18:51, finished 09:39 after
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
  Result: Q3_RESULT
- **G queue 4 — the sealed test read, once:** every arm at 400k × 8 seed 0 on `--split test`. Result:
  Q4_RESULT
"""

sub("PLAN6.md", [
    ("""- **F3.** Recorded in KNOWLEDGE §10.
""", """- **F3.** Recorded in KNOWLEDGE §10.
""" + LOG),
    ("""**State (2026-09-06, 19:00 — hand-off).** Two things are running, both launched with the owner's
approval:""",
     """**State (2026-09-07, hand-off).** Nothing is training. The play agent is now
**`runs/deep8_c1_300_e2/net_0300.pt`** (+291 vs v2b; the log's H1 entry). The 3060 may still be finishing
the G follow-up queues (`runs/plan6/G_queue.out` — queue 3: the mask rerun and the sample-efficiency points;
queue 4: the one sealed test read); their results are pasted into the log entries marked Q3 / Q4 when they
land. What was running during 2026-09-06/07, both owner-approved:"""),
    ("""**What the next instance does, in order.** (1) Read G0 and the three arms when `G_queue.out` says DONE
(each record: policy KL / top-1 vs the teacher, value Brier, 3-way accuracy vs exact labels, the same on
the subset with no canonical twin in train, endgame_v2_dev regret, D4 JS, ms per evaluation at batch 4096
and 1): G0 says whether fitting a fixed teacher is data- or update-limited; the arms give the ResNet's
two-seed spread that §4's gate is measured against, and whether the closed-board mask costs anything
supervised (the licence for H2). Write them into the log below and KNOWLEDGE §8. (2) Implement arms (d)
and (e) (`tools/gstudy.py`), run them, then the test slice once. (3) When H1 finishes (≈ 07:00
2026-09-07), read it by the rule above, write it up (KNOWLEDGE 42/43, RETROSPECTIVE §3, README ladder),
and propose H3's shape to the owner. Nothing else starts without the owner's word.""",
     """**What the next instance does, in order.** (1) If the Q3 / Q4 lines in the log still say pending, read
`runs/plan6/G_queue.out` and the JSONs (`G_arm_resnet8_mask.json`, `G0_gcnn8x16.json`, `G0b_gcnn8x16.json`,
`G0_resnet8_tied.json`, `G0b_resnet8_tied.json`, `G_test_*.json`) and fill them in; the gate-(ii) reading is
"reaches the ResNet's 3120-step KL (0.884 dev) with ≤ 1560 steps", since G0 showed steps are the currency.
(2) Put the three proposals below to the owner; launch the approved one through a hidden-console
`runs/launch_queue<N>_hidden.vbs` (copy queue9's: retry wrapper, `--eval_every 0 --ckpt_every 10`, the E7
worker on the 3060, `eval_run.sh` + the endgame_v2_dev read at the end) and monitor it. (3) Optional, an
hour of the 3090: the phased schedule and the 8-way / canonical evaluators re-verified on the new play agent
(PLAN5 A8c / PLAN6 F1 on `deep8_c1_300_e2`); the game claims of KNOWLEDGE §1–§8 on it are a bigger job
(Phase A's tools, ≈ a day of the 3060) and only worth it if a magnitude is suspected to have moved.

**Proposals for the owner (each one change against a named parent; ±3 rule; final checkpoint on the full
suite; the E7 worker gives the curve at ±2.8).**
- **H1b — dose–response: `deep8_c1_300_e4`, `--epochs 4` (1024 steps per iteration), everything else as
  H1.** ≈ 17 h (training 5 h of it). Parent: `deep8_c1_300_e2`. Pre-registered: ≥ 53 % → still
  update-limited, and the next run doubles again (or H3 runs at epochs 4); 47–53 → epochs 2 is the plateau,
  H3 at epochs 2; ≤ 47 → over-fitting the 7.6-iteration buffer window, and the buffer (not the update count)
  is the next knob. The cheapest test of the largest effect the project has found; **first**.
- **H4 — the gated architecture in self-play: `gcnn8_c1_300_e2`, `--gcnn 16 --filters 128 --blocks 8
  --epochs 2`, everything else as H1.** ≈ 15 h (the group convolution's expansion is a gather per forward;
  the self-play path uses the exported plain net at identical cost). Parent: H1. Primary vs H1 at 64 sims
  (equal cost by construction, so one comparison serves both of §5 H4's requirements); secondary the D4
  residual (0 by construction — the first play agent with exact symmetry) and the endgame reads. Reading by
  the rule. **Second**, or first if the owner prefers the architecture question. `resnet8_tied` (arm d,
  `--head_tying 1`) is the cheaper half of the same question and a fallback if the G-CNN misbehaves in RL.
- **H3 — duration at the right update count: `deep8_c1_600_e2`, 600 iterations, `--lr_drops 500`,
  `--epochs 2` (or H1b's epochs if it helped).** ≈ 29 h. Parent: H1. Reading: the full-suite curve from
  300 to 500 — flat means duration is exhausted at this data rate, climbing means it is not.
- Not proposed: H2 (the closed-board mask; its supervised gain is real but small — 0.008 in KL — and the
  licence it buys, a smaller state key for caches, has no consumer yet); a 10-block anything (46, 48).

**Nothing starts without the owner's word.** E11 (backup / GitHub) is deferred by the owner to the write-up."""),
    ("Result: Q3_RESULT", "Result: " + Q3),
    ("Result:\n  Q4_RESULT", "Result:\n  " + Q4),
])
print("ok")
