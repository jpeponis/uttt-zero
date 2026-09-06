#!/bin/bash
# PLAN6 F2: the second LR drop at ±2.8 instead of ±6. Full-suite scores vs v2b @64 for the checkpoints around both
# drops of the four 300-iteration runs, through the E7 worker (--once: score what is listed and exit). Writes
# runs/<run>/eval_full.jsonl. Pre-registered reading: the 280 drop "does something" only if 0300 - 0260 >= 3 points
# on at least three of the four runs. ~24 matches x 2-3 min on the 3090.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
D=${1:-cuda:0}
{
for R in deep8_c1_300 deep10_c1_300 deep10_c1_300_s1; do
  $P tools/eval_worker.py --run runs/$R --once --only 200,220,260,280,300 --anchors runs/v2b/net_0150.pt --sims 64 --set "" --device $D
done
$P tools/eval_worker.py --run runs/deep10_c1_300_lr150 --once --only 150,160,240,250,260,300 --anchors runs/v2b/net_0150.pt --sims 64 --set "" --device $D
echo "=== F2 summary: full-suite score vs v2b @64 per checkpoint"
$P - <<'PY'
import json
for r in ("deep8_c1_300", "deep10_c1_300", "deep10_c1_300_s1", "deep10_c1_300_lr150"):
    rows = sorted((json.loads(l) for l in open(f"runs/{r}/eval_full.jsonl")), key=lambda x: x["iter"])
    s = {x["iter"]: x["anchors"]["v2b_net_0150"] for x in rows}
    print(r, "  ".join(f"{it}: {100 * v['score']:.1f} [{100 * v['ci'][0]:.1f}, {100 * v['ci'][1]:.1f}]" for it, v in s.items()))
    last, prev = max(s), sorted(s)[-2]
    print(f"  {last} - {prev}: {100 * (s[last]['score'] - s[prev]['score']):+.1f} points")
PY
echo DONE
} > runs/plan6/F2_second_drop.out 2>&1
