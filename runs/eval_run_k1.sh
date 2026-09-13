#!/bin/bash
# K1's post-run chain (PLAN7 §5 items 4 and 3, the parts a final checkpoint can give at once):
#   bash runs/eval_run_k1.sh deep8_c1_300_e8_draw [device]  -> runs/deep8_c1_300_e8_draw/analysis.out
# Not eval_run.sh: that chain plays the whole ladder under count, which is not a pre-registered K1 reading (a draw net's
# count-rule score against the ladder is not comparable with anything). What is pre-registered:
#   item 4  cross-play -- the draw net against its count-trained parent on the paired suite at 64 sims, once under count
#           and once under draw: two independent scores, the contrast 1 - s_D - s_C read by the +-3 rule with a joint
#           pair bootstrap by opening (tools/openings.py writes the per-opening records both bootstraps need); and v2b
#           under both rules, for shape only.
#   item 3  both nets under both rules on the two dev endgame sets: the draw net on the draw set under draw and on the
#           count set under count; the parent on the draw set under draw (its count reading is in its own analysis.out).
#           The common natural-position set and the exact-minimax change on its solved subset are a separate tool run.
# The evaluation rule is an explicit argument everywhere (never inferred from a checkpoint); a non-count rule tags the
# output file name (paired_vs_..._64_draw.json), so the two rules' matches cannot be mistaken for each other.
# The checkpoint is named, not discovered (M2 rebuttal (d)): `ls net_*.pt | tail -1` graded whatever the run had
# reached, so an interrupted run would have been written up as if it were the finished one. This script now runs
# only on a run that reached DONE and produced net_0300.pt, and every command's exit status is recorded in
# analysis.out and summed into the script's own: a failed reading can no longer look like an absent one.
set -o pipefail
cd "/c/Users/John Peponis/Desktop/uttt-zero" || { echo "eval_run_k1: cannot cd to the repository" >&2; exit 2; }
R=$1; D=${2:-cuda:0}; P=.venv/Scripts/python.exe
PARENT=runs/deep8_c1_300_e8/net_0300.pt
[ -n "$R" ] || { echo "usage: bash runs/eval_run_k1.sh <run> [device]" >&2; exit 2; }
[ -f runs/$R/DONE ] || { echo "runs/$R/DONE is missing: the run has not finished, and a partial run is not a K1 reading" >&2; exit 1; }
N=runs/$R/net_0300.pt
[ -f $N ] || { echo "$N is missing: K1's readings are of the final checkpoint of a 300-iteration run, not of the latest one present" >&2; exit 1; }
[ -f $PARENT ] || { echo "$PARENT is missing: every reading below is against the count-trained parent" >&2; exit 1; }
fail=0
record() {  # record() <status> <what>: name the failure in analysis.out and keep going to the next reading
  [ "$1" -eq 0 ] || { echo "!!! FAILED (exit $1): $2"; fail=$((fail + 1)); }
}
{
echo "=== $R final in-run evals (checkpoint: $N; the run trained under draw)"
$P - "$R" <<'PY'
import json, sys
rows=[json.loads(l) for l in open(f'runs/{sys.argv[1]}/log.jsonl')]
last=max(r['iter'] for r in rows)
for x in rows:
    if any(k.startswith('vs_') for k in x) and x['iter'] >= last-30:
        print({k:x[k] for k in x if k.startswith(('vs_','ci_','eg_')) or k=='iter'})
print('wall-clock (h):', round(sum(r.get('t_iter', r['t_selfplay']+r['t_train']+r.get('t_eval',0)+r.get('t_exact_wait',0)) for r in rows)/3600, 2))
PY
record $? "the final in-run evaluation table (runs/$R/log.jsonl)"
echo "=== item 4: cross-play against the count-trained parent, one match per rule"
$P tools/openings.py match --a $N --b $PARENT --sims 64 --rule count --device $D --out runs/$R/paired_vs_deep8c1_300e8_64.json
record $? "item 4: vs the parent under count"
$P tools/openings.py match --a $N --b $PARENT --sims 64 --rule draw  --device $D --out runs/$R/paired_vs_deep8c1_300e8_64.json
record $? "item 4: vs the parent under draw"
echo "=== v2b under both rules (shape only; v2b is count-trained)"
$P tools/openings.py match --a $N --b runs/v2b/net_0150.pt --sims 64 --rule count --device $D --out runs/$R/paired_vs_v2b_64.json
record $? "vs v2b under count"
$P tools/openings.py match --a $N --b runs/v2b/net_0150.pt --sims 64 --rule draw  --device $D --out runs/$R/paired_vs_v2b_64.json
record $? "vs v2b under draw"
echo "=== item 3: the endgame sets, each under its own rule"
echo "--- the draw net on endgame_v2_dev_draw under draw"
$P tools/endgame.py eval $N --set suites/endgame_v2_dev_draw.npz --rule draw --device $D
record $? "item 3: the draw net on endgame_v2_dev_draw under draw"
echo "--- the draw net on endgame_v2_dev under count"
$P tools/endgame.py eval $N --set suites/endgame_v2_dev.npz --rule count --device $D
record $? "item 3: the draw net on endgame_v2_dev under count"
echo "--- the draw net on endgame_v1 under count (the ladder's column)"
$P tools/endgame.py eval $N --set suites/endgame_v1.npz --rule count --device $D
record $? "item 3: the draw net on endgame_v1 under count"
echo "--- the parent deep8_c1_300_e8 on endgame_v2_dev_draw under draw"
$P tools/endgame.py eval $PARENT --set suites/endgame_v2_dev_draw.npz --rule draw --device $D
record $? "item 3: the parent on endgame_v2_dev_draw under draw"
echo "=== $fail of 9 readings failed"
} > runs/$R/analysis.out 2>&1
if [ $fail -ne 0 ]; then
  echo "eval_run_k1: $fail reading(s) FAILED; see runs/$R/analysis.out (grep '!!! FAILED')" >&2
  exit 1
fi
echo "wrote runs/$R/analysis.out"
