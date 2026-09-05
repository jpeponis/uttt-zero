#!/bin/bash
# PLAN5 Handover step 3 (+4): the Phase B control on the D1 seed replicate, mirroring runs/plan5_B.sh. Held-out
# positions are deep8_c1_300's late games (runs/probe_data_deep8late.npz), as for deep10_c1_300 (PLAN5 §8).
# 3060 chain: B1 timeline, B3 value decomposition. 3090 chain (after eval_run.sh has finished, i.e. queue7.out says
# "queue7 done"): B2 linear probes with the random-init control, the probe report, then the ONE reading of the sealed
# suites/endgame_v2_test.npz for deep10_c1_300, deep8_c1_300 and the replicate (owner-approved 2026-09-04).
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
S1=runs/deep10_c1_300_s1; D10=runs/deep10_c1_300/net_0300.pt; D8=runs/deep8_c1_300/net_0300.pt
run() { local out=$1; shift; echo "=== $(date '+%F %T') $*"; "$@" > "$out" 2>&1; echo "    -> $out ($?)"; }
{
echo "plan5 D1 control (3060 chain) started $(date)"
run runs/plan5_B1_timeline_s1.out   $P tools/timeline.py $S1 --corpus runs/deep8_c1_300 --last 20 --device cuda:1
run runs/plan5_B3_value_s1.out      $P tools/value_decomp.py $S1 --data runs/probe_data_deep8late.npz --n 20000 --sims 256 --device cuda:1
echo "plan5 D1 control (3060 chain) done $(date)"
} >> runs/plan5_D1_control.out 2>&1 &
{
echo "plan5 D1 control (3090 chain) waiting for eval_run.sh $(date)"
while ! grep -q "queue7 done" runs/queue7.out 2>/dev/null; do sleep 60; done
echo "plan5 D1 control (3090 chain) started $(date)"
run runs/plan5_B2_fit_s1.out        $P tools/probe.py fit --data runs/probe_data_deep8late.npz --run $S1 --control --device cuda:0
run runs/plan5_B2_report_s1.out     $P tools/probe_report.py $S1/probes.json --fig $S1/probes.png
run runs/plan5_A9_test_deep10.out   $P tools/endgame.py eval $D10 --set suites/endgame_v2_test.npz --device cuda:0
run runs/plan5_A9_test_deep8.out    $P tools/endgame.py eval $D8 --set suites/endgame_v2_test.npz --device cuda:0
run runs/plan5_A9_test_s1.out       $P tools/endgame.py eval $S1/net_0300.pt --set suites/endgame_v2_test.npz --device cuda:0
echo "plan5 D1 control (3090 chain) done $(date)"
} >> runs/plan5_D1_control.out 2>&1 &
wait
echo "plan5 D1 control all done $(date)" >> runs/plan5_D1_control.out
