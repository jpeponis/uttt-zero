#!/bin/bash
# PLAN5 §4 C1: opening book to depth 4, top-3 replies per node, 16k sims, symmetry-averaged evaluators.
# deep8_c1_300's book runs on the idle 3060 now; deep10's waits for the Phase B 3090 chain, then compares with deep8's.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
echo "=== C1 book deep8_c1_300 started $(date) (3060)"
$P tools/book.py --net runs/deep8_c1_300/net_0300.pt --depth 4 --top 3 --sims 16384 --batch 64 --paired runs/deep10_c1_300/paired_vs_deep8c1_300_64.json --device cuda:1 --out runs/book_deep8.json
echo "=== C1 book deep8 done $(date)"
} > runs/plan5_C1_deep8.out 2>&1 &
{
while ! grep -q "3090 chain) done" runs/plan5_B.out; do sleep 120; done
while [ ! -f runs/book_deep8.json ]; do sleep 120; done
echo "=== C1 book deep10 started $(date) (3090)"
$P tools/book.py --net runs/deep10_c1_300/net_0300.pt --depth 4 --top 3 --sims 16384 --batch 128 --paired runs/deep10_c1_300/paired_phased_vs_256.json --compare runs/book_deep8.json --device cuda:0 --out runs/book_deep10.json
echo "C1 done at $(date)"
} > runs/plan5_C1.out 2>&1 &
wait
