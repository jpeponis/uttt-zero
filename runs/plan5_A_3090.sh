#!/bin/bash
# PLAN5 §2 Phase A, 3090/CPU chain: A6 (corpus statistics), A9 (endgame_v2 dev/test build + evals), A1/A2 (opening atlas).
# The 3090 is idle (training paused, PLAN5 §5); using it for analysis is within the plan's budget (§7).
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe; D=${1:-cuda:0}
D10=runs/deep10_c1_300/net_0300.pt; D8=runs/deep8_c1_300/net_0300.pt
run() { local out=$1; shift; echo "=== $(date '+%F %T') $*"; "$@" > "$out" 2>&1; echo "    -> $out ($?)"; }
{
echo "plan5 Phase A (3090 chain) started $(date)"
run runs/plan5_A6_corpus_deep10_last20.out  $P tools/corpus_stats.py runs/deep10_c1_300 --last 20
run runs/plan5_A6_corpus_deep8_300_last20.out $P tools/corpus_stats.py runs/deep8_c1_300 --last 20
run runs/plan5_A6_corpus_v2a_last20.out     $P tools/corpus_stats.py runs/v2a --last 20
run runs/plan5_A9_build_endgame_v2.out      $P tools/endgame.py build --corpus runs/deep8_c1_300 --last 20 --per_stratum 125 --split dev,test --processes 12 --out suites/endgame_v2
run runs/plan5_A9_eval_deep10_v2dev.out     $P tools/endgame.py eval $D10 --set suites/endgame_v2_dev.npz --device $D
run runs/plan5_A9_eval_deep8_v2dev.out      $P tools/endgame.py eval $D8  --set suites/endgame_v2_dev.npz --device $D
run runs/plan5_A9_eval_deep10_v1.out        $P tools/endgame.py eval $D10 --set suites/endgame_v1.npz --device $D
run runs/plan5_A9_eval_deep8_v1.out         $P tools/endgame.py eval $D8  --set suites/endgame_v1.npz --device $D
run runs/plan5_A1_atlas.out                 $P tools/atlas.py --nets runs/v2b/net_0150.pt,$D8,$D10 --budgets 1024,4096,16384 --device $D --out runs/plan5_A1_atlas.json
echo "plan5 Phase A (3090 chain) done $(date)"
} >> runs/plan5_A.out 2>&1
