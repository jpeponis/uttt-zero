#!/bin/bash
# PLAN5 §3 B5, equal-compute half: symmetry-averaged deep10 @64 (8 evaluations per sim) vs plain deep10 @512.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
echo "=== B5b: deep10 symmetry-averaged @64 vs deep10 plain @512 (equal inference compute)"
$P tools/openings.py match --a runs/deep10_c1_300/net_0300.pt --b runs/deep10_c1_300/net_0300.pt --a_sym --a_sims 64 --b_sims 512 --device cuda:1 --out runs/deep10_c1_300/paired_sym64_vs_plain512.json
echo "B5b done at $(date)"
} > runs/plan5_B5b_sym_equal_compute.out 2>&1
