#!/bin/bash
# PLAN6 E7/F2: regenerate the four checkpoint timelines so they carry the full-suite (±2.8) points from eval_full.jsonl
# beside the in-run (±6) curve. Same held-out corpus per run as the PLAN5 B1 build (read from the existing timeline.json).
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
for R in deep8_c1_300 deep10_c1_300 deep10_c1_300_s1 deep10_c1_300_lr150; do
  C=$($P -c "import json; print(json.load(open('runs/$R/timeline.json'))['meta']['corpus'])")
  echo "=== $R (held-out corpus $C)"
  $P tools/timeline.py runs/$R --corpus $C --device cuda:1
done
echo DONE
} > runs/plan6/E7_timelines.out 2>&1
