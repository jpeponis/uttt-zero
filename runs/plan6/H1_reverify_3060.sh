#!/bin/bash
# PLAN6 Handover (2): the play-time re-verifications on the new play agent deep8_c1_300_e2 -- the phased schedule
# (PLAN5 A8c), the 8-way symmetry average (PLAN5 B5) and the canonical evaluator (PLAN6 F1), each vs the plain net.
# Launch (hidden console): wscript runs/launch_reverify_hidden.vbs
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe; N=runs/deep8_c1_300_e2/net_0300.pt
{
echo "=== phased 0:128,24:384 vs flat 256 (PLAN5 A8c on e2)"
$P tools/openings.py match --a $N --b $N --a_sims "0:128,24:384" --b_sims 256 --device cuda:1 --out runs/deep8_c1_300_e2/paired_phased_vs_256.json
echo "=== 8-way symmetry-averaged @64 vs plain @64 (PLAN5 B5 on e2)"
$P tools/openings.py match --a $N --b $N --a_sym --sims 64 --device cuda:1 --out runs/deep8_c1_300_e2/paired_sym_vs_plain_64.json
echo "=== canonical @64 vs plain @64 (PLAN6 F1 on e2)"
$P tools/openings.py match --a $N --b $N --a_canon --sims 64 --device cuda:1 --out runs/deep8_c1_300_e2/paired_canon_vs_plain_64.json
echo "reverify done at $(date)"
} > runs/plan6/H1_reverify.out 2>&1
