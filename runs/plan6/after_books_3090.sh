#!/bin/bash
# PLAN6, once the book rebuilds have released the 3090: (1) the GPU test suite on the E4/E5/E6/F1 changes;
# (2) F1 — does exact equivariance alone buy anything at play? deep10 canonical @64 vs deep10 plain @64 on the
# full paired suite (pre-registered: >= 53 % adopt; 47-53 null; <= 47 hurts); (3) F2 — the second LR drop at ±2.8.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
echo "=== tests on cuda:0 ($(date +%H:%M))"
for t in test_rng_hygiene test_symmetry test_search_v2 test_search_graph test_selfplay_cont test_hygiene test_symmetry_eval test_book; do
  echo "--- $t"
  UTTT_DEV=cuda:0 $P tests/$t.py 2>&1 | tail -n 8
done
echo "=== F1: canonical vs plain, deep10 @64 ($(date +%H:%M))"
$P tools/openings.py match --a runs/deep10_c1_300/net_0300.pt --a_canon --b runs/deep10_c1_300/net_0300.pt --sims 64 --device cuda:0 --out runs/deep10_c1_300/paired_canon_vs_plain_64.json
echo "=== F1 done ($(date +%H:%M))"
} > runs/plan6/after_books_3090.out 2>&1
bash runs/plan6/F2_second_drop.sh cuda:0
echo DONE >> runs/plan6/after_books_3090.out
