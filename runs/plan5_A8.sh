#!/bin/bash
# PLAN5 §2 A8: equal-compute matches for the 10-block net (per-sim cost ~ blocks x filters^2:
# deep10 = 6.7x v2b, 1.25x deep8_c1_300) and the phased-schedule re-verify on deep10.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe; D=${1:-cuda:0}
{
echo "=== A8a: deep10@64 vs v2b@427 (FLOP-matched)"
$P tools/openings.py match --a runs/deep10_c1_300/net_0300.pt --b runs/v2b/net_0150.pt --a_sims 64 --b_sims 427 --device $D --out runs/deep10_c1_300/paired_vs_v2b_flopmatched.json
echo "=== A8b: deep10@64 vs deep8_c1_300@80 (FLOP-matched)"
$P tools/openings.py match --a runs/deep10_c1_300/net_0300.pt --b runs/deep8_c1_300/net_0300.pt --a_sims 64 --b_sims 80 --device $D --out runs/deep10_c1_300/paired_vs_deep8c1_300_flopmatched.json
echo "=== A8c: deep10 phased 0:128,24:384 vs uniform 256"
$P tools/openings.py match --a runs/deep10_c1_300/net_0300.pt --b runs/deep10_c1_300/net_0300.pt --a_sims "0:128,24:384" --b_sims 256 --device $D --out runs/deep10_c1_300/paired_phased_vs_256.json
echo "A8 done at $(date)"
} > runs/plan5_A8.out 2>&1
