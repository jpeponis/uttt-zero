#!/bin/bash
# PLAN5 §3 B6: distil deep10's 256-sim search into a linear surrogate over hand-written features (one DAgger round),
# then play the surrogate on the paired suite at 64 sims against v2b and deep10 (3060).
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
echo "=== B6 distil"
$P tools/distill.py --net runs/deep10_c1_300/net_0300.pt --data runs/probe_data_deep8late.npz --sims 256 --dagger 1 --dagger_games 2048 --steps 600 --device cuda:1 --out runs/surrogate_deep10.json
echo "=== B6 match: surrogate @64 vs v2b @64"
$P tools/openings.py match --a surrogate:runs/surrogate_deep10.json --b runs/v2b/net_0150.pt --sims 64 --device cuda:1 --out runs/paired_surrogate_vs_v2b_64.json
echo "=== B6 match: surrogate @64 vs deep10 @64"
$P tools/openings.py match --a surrogate:runs/surrogate_deep10.json --b runs/deep10_c1_300/net_0300.pt --sims 64 --device cuda:1 --out runs/paired_surrogate_vs_deep10_64.json
echo "=== B6 match: surrogate @64 vs rollout UCT 10k playouts (an absolute anchor)"
$P tools/openings.py match --a surrogate:runs/surrogate_deep10.json --b rollout --a_sims 64 --b_sims 10000 --device cuda:1 --out runs/paired_surrogate_vs_rollout10k.json
echo "B6 done at $(date)"
} > runs/plan5_B6_distill.out 2>&1
