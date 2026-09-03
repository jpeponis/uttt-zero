#!/bin/bash
# PLAN5 §3 B5, behavioural half: what symmetry averaging still adds at play time on the annealed net.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
echo "=== B5: deep10 symmetry-averaged @64 vs deep10 plain @64 (paired suite)"
$P tools/openings.py match --a runs/deep10_c1_300/net_0300.pt --b runs/deep10_c1_300/net_0300.pt --a_sym --sims 64 --device cuda:1 --out runs/deep10_c1_300/paired_sym_vs_plain_64.json
echo "B5 done at $(date)"
} > runs/plan5_B5_sym_vs_plain.out 2>&1
