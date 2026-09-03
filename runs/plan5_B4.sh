#!/bin/bash
# PLAN5 §3 B4: counterfactual value probes (raw, symmetry-averaged) and surprise mining on deep10, positions from
# deep8_c1_300's replay buffer (held-out for deep10; PLAN5 §8). 3060 while the B chains use the 3090.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
run() { local out=$1; shift; echo "=== $(date '+%F %T') $*"; "$@" > "$out" 2>&1; echo "    -> $out ($?)"; }
{
run runs/plan5_B4_probe_value_deep10.out $P tools/probe_value.py runs/deep10_c1_300/net_0300.pt --buffer runs/deep8_c1_300/latest_full.pt --device cuda:1
run runs/plan5_B4_surprise_deep10.out    $P tools/surprise.py runs/deep10_c1_300/net_0300.pt --buffer runs/deep8_c1_300/latest_full.pt --sims 256 --n 8192 --top 30 --device cuda:1
echo "plan5 B4 done $(date)"
} >> runs/plan5_B.out 2>&1
