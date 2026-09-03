#!/bin/bash
# PLAN5 §2 Phase A, 3060 chain: A3 (decision time), A4/A5 (free-move and ownership regression), A7 (puzzles v2 dev).
# Net under test: deep10_c1_300/net_0300.pt; second column deep8_c1_300 where cheap. Held-out corpora per PLAN5 §8:
# deep10 is probed on deep8_c1_300's iteration-280+ games (and on v2a's, the games the earlier beliefs used), and vice versa.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe; D=${1:-cuda:1}
D10=runs/deep10_c1_300/net_0300.pt; D8=runs/deep8_c1_300/net_0300.pt
run() { local out=$1; shift; echo "=== $(date '+%F %T') $*"; "$@" > "$out" 2>&1; echo "    -> $out ($?)"; }
{
echo "plan5 Phase A (3060 chain) started $(date)"
run runs/plan5_A3a_decision_deep10_on_v2a.out       $P tools/decision.py $D10 --corpus runs/v2a --last 2 --games 4000 --sims 64 --device $D
run runs/plan5_A3b_decision_deep10_on_deep8late.out  $P tools/decision.py $D10 --corpus runs/deep8_c1_300 --last 20 --games 4000 --sims 64 --device $D
run runs/plan5_A3c_decision_deep8_on_v2a.out         $P tools/decision.py $D8  --corpus runs/v2a --last 2 --games 4000 --sims 64 --device $D
run runs/plan5_A4_freemove_deep10_on_deep8late.out   $P tools/freemove.py $D10 --corpus runs/deep8_c1_300 --last 20 --sims 256 --device $D
run runs/plan5_A7_puzzles_deep10_on_deep8late.out    $P tools/puzzles.py  $D10 --corpus runs/deep8_c1_300 --last 20 --max_empty 14 --n 6000 --processes 12 --device $D --out suites/puzzles_v2_dev.npz
run runs/plan5_A4b_freemove_deep8_on_deep10late.out  $P tools/freemove.py $D8  --corpus runs/deep10_c1_300 --last 20 --sims 256 --device $D
echo "plan5 Phase A (3060 chain) done $(date)"
} >> runs/plan5_A.out 2>&1
