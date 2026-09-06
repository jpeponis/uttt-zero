#!/bin/bash
# PLAN6 E1: rebuild both opening books with orbit-ranked replies and frame-consistent lines (tools/book.py after E1).
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
$P tools/book.py --net runs/deep8_c1_300/net_0300.pt --depth 4 --top 3 --sims 16384 --batch 64 --paired runs/deep10_c1_300/paired_vs_deep8c1_300_64.json --device cuda:1 --out runs/book_deep8.json > runs/plan6/E1_book_deep8.out 2>&1 &
$P tools/book.py --net runs/deep10_c1_300/net_0300.pt --depth 4 --top 3 --sims 16384 --batch 128 --paired runs/deep10_c1_300/paired_phased_vs_256.json --device cuda:0 --out runs/book_deep10.json > runs/plan6/E1_book_deep10.out 2>&1 &
wait
# the comparison column needs both books: regenerate deep10's markdown against deep8's (no search)
$P - <<'PY' > runs/plan6/E1_book_compare.out 2>&1
import json, sys
sys.path.insert(0, "tools"); sys.path.insert(0, ".")
from book import markdown, paired_stats
d10 = json.load(open("runs/book_deep10.json")); d8 = json.load(open("runs/book_deep8.json"))
md = markdown(d10["nodes"], d10["meta"], paired_stats("runs/deep10_c1_300/paired_phased_vs_256.json"), d8)
open("runs/book_deep10.md", "w", encoding="utf-8").write(md + "\n")
print(md)
PY
$P tools/book_stats.py runs/book_deep10.json runs/book_deep8.json > runs/plan6/E1_book_stats.out 2>&1
echo DONE >> runs/plan6/E1_book_compare.out
