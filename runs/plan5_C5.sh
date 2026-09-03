#!/bin/bash
# PLAN5 §4 C5: the one-open-board tablebase spliced into the search as a terminal lookup - with vs without, both
# @64 on the paired suite (3060). A null is expected for deep10 (its search is already 100 % optimal there);
# v2b is the weaker-net check. Waits for the B6 chain to release the 3060.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
while ! grep -q "B6 done" runs/plan5_B6_distill.out 2>/dev/null; do sleep 60; done
{
echo "=== C5: deep10 @64 with the K=1 tablebase vs deep10 @64 plain"
$P tools/openings.py match --a runs/deep10_c1_300/net_0300.pt --b runs/deep10_c1_300/net_0300.pt --a_tb --sims 64 --device cuda:1 --out runs/deep10_c1_300/paired_tb_vs_plain_64.json
echo "=== C5: v2b @64 with the K=1 tablebase vs v2b @64 plain"
$P tools/openings.py match --a runs/v2b/net_0150.pt --b runs/v2b/net_0150.pt --a_tb --sims 64 --device cuda:1 --out runs/v2b/paired_tb_vs_plain_64.json
echo "C5 done at $(date)"
} > runs/plan5_C5_tablebase.out 2>&1
