#!/bin/bash
# Standard post-run chain: bash runs/eval_run.sh <run> [device]  -> runs/<run>/analysis.out
# The final checkpoint is discovered (last net_*.pt), not hardcoded, so 150- and 300-iteration runs both work.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
R=$1; D=${2:-cuda:0}; P=.venv/Scripts/python.exe
N=$(ls runs/$R/net_*.pt | sort | tail -1)
{
echo "=== $R final in-run evals (checkpoint: $N)"
$P - "$R" <<'PY'
import json, sys
rows=[json.loads(l) for l in open(f'runs/{sys.argv[1]}/log.jsonl')]
last=max(r['iter'] for r in rows)
for x in rows:
    if any(k.startswith('vs_') for k in x) and x['iter'] >= last-30:
        print({k:x[k] for k in x if k.startswith(('vs_','ci_','eg_')) or k=='iter'})
print('wall-clock (h):', round(sum(r.get('t_iter', r['t_selfplay']+r['t_train']+r.get('t_eval',0)+r.get('t_exact_wait',0)) for r in rows)/3600, 2))
PY
echo "=== paired matches"
$P tools/openings.py match --a $N --b runs/v2b/net_0150.pt --sims 64 --device $D --out runs/$R/paired_vs_v2b_64.json
[ "$R" != "wide128_c1" ] && $P tools/openings.py match --a $N --b runs/wide128_c1/net_0150.pt --sims 64 --device $D --out runs/$R/paired_vs_wide128c1_64.json
[ "$R" != "deep8_c1" ] && [ -f runs/deep8_c1/net_0150.pt ] && $P tools/openings.py match --a $N --b runs/deep8_c1/net_0150.pt --sims 64 --device $D --out runs/$R/paired_vs_deep8c1_64.json
[ "$R" != "deep8_c1_300" ] && [ -f runs/deep8_c1_300/net_0300.pt ] && $P tools/openings.py match --a $N --b runs/deep8_c1_300/net_0300.pt --sims 64 --device $D --out runs/$R/paired_vs_deep8c1_300_64.json
[ "$R" != "deep10_c1_300" ] && [ -f runs/deep10_c1_300/net_0300.pt ] && $P tools/openings.py match --a $N --b runs/deep10_c1_300/net_0300.pt --sims 64 --device $D --out runs/$R/paired_vs_deep10c1_300_64.json
[ "$R" != "deep10_c1_300_s1" ] && [ -f runs/deep10_c1_300_s1/net_0300.pt ] && $P tools/openings.py match --a $N --b runs/deep10_c1_300_s1/net_0300.pt --sims 64 --device $D --out runs/$R/paired_vs_deep10c1_300s1_64.json
$P tools/openings.py match --a $N --b runs/dev1/net_0200.pt --sims 64 --device $D --out runs/$R/paired_vs_dev1_64.json
echo "=== endgame set"
$P tools/endgame.py eval $N --device $D
} > runs/$R/analysis.out 2>&1
echo "wrote runs/$R/analysis.out"
