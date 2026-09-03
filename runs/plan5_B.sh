#!/bin/bash
# PLAN5 §3 Phase B, first pass: B1 checkpoint timelines (both 300-iteration runs), B2 probe datasets + linear probes
# over every checkpoint (random-init control included), B3 value decomposition per checkpoint. Two chains: the 3090
# builds the probe datasets (256-sim look-ahead labels) and fits the probes; the 3060 runs the timelines and B3.
# Held-out convention (PLAN5 §8): deep10 is probed on deep8_c1_300's iteration-280+ games and vice versa.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
D10=runs/deep10_c1_300/net_0300.pt; D8=runs/deep8_c1_300/net_0300.pt
run() { local out=$1; shift; echo "=== $(date '+%F %T') $*"; "$@" > "$out" 2>&1; echo "    -> $out ($?)"; }
{
echo "plan5 Phase B (3090 chain) started $(date)"
run runs/plan5_B2_build_deep8late.out   $P tools/probe.py build --corpus runs/deep8_c1_300 --last 20 --net $D10 --out runs/probe_data_deep8late.npz --device cuda:0
run runs/plan5_B2_build_deep10late.out  $P tools/probe.py build --corpus runs/deep10_c1_300 --last 20 --net $D8 --out runs/probe_data_deep10late.npz --device cuda:0
run runs/plan5_B2_fit_deep10.out        $P tools/probe.py fit --data runs/probe_data_deep8late.npz --run runs/deep10_c1_300 --control --device cuda:0
run runs/plan5_B2_fit_deep8.out         $P tools/probe.py fit --data runs/probe_data_deep10late.npz --run runs/deep8_c1_300 --control --only 10,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300 --device cuda:0
run runs/plan5_B2_fit_deep10_mlp.out    $P tools/probe.py fit --data runs/probe_data_deep8late.npz --run runs/deep10_c1_300 --control --hidden 256 --only 20,100,200,220,280,300 --device cuda:0
echo "plan5 Phase B (3090 chain) done $(date)"
} >> runs/plan5_B.out 2>&1 &
{
echo "plan5 Phase B (3060 chain) started $(date)"
run runs/plan5_B1_timeline_deep10.out   $P tools/timeline.py runs/deep10_c1_300 --corpus runs/deep8_c1_300 --last 20 --device cuda:1
run runs/plan5_B1_timeline_deep8.out    $P tools/timeline.py runs/deep8_c1_300 --corpus runs/deep10_c1_300 --last 20 --device cuda:1
while [ ! -f runs/probe_data_deep10late.npz ]; do sleep 60; done
run runs/plan5_B3_value_deep10.out      $P tools/value_decomp.py runs/deep10_c1_300 --data runs/probe_data_deep8late.npz --n 20000 --sims 256 --device cuda:1
run runs/plan5_B3_value_deep8.out       $P tools/value_decomp.py runs/deep8_c1_300 --data runs/probe_data_deep10late.npz --n 20000 --sims 256 --only 20,60,100,140,180,200,220,240,260,280,300 --device cuda:1
echo "plan5 Phase B (3060 chain) done $(date)"
} >> runs/plan5_B.out 2>&1 &
wait
