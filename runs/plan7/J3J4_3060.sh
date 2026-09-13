#!/bin/bash
# PLAN7 §4 J3 and J4, as amended after M2 and its rebuttal (§7e M2 rows 3, 4, 7, 15, 16; M2-R R5–R7) — the real runs,
# on the 3060 once the _e8 count pass freed it (02:40, 2026-09-13). K1 trains on the 3090 beside this; its E7 worker
# shares the 3060 for ~6 min every ~40 min, as the I1 pass shared it with H1c's worker.
#   J3  tools/empty_board.py on deep8_c1_300_e8 and deep8_c1_300_e4: (a) the empty board's root value and principal
#       line at 16 384 sims, symmetry-averaged; (b) 2 000 games at 256 sims, the search policy sampled for the first
#       4 plies with both floors off and the Gumbel scale 0, the PLAIN evaluator (the corpus-generating agent);
#       (c) 2 000 games at 256 sims under the exploration settings as trained, plain evaluator. The Wilson intervals
#       are the policy's; the concentration (distinct games / openings) is reported beside them, not corrected for;
#       (b) − (c) is the exploration package at a matched budget; (b)'s split is COMPARED with claim 24's, not a
#       test of it. ≈ 45 min per net.
#   J4  tools/frontier.py on deep8_c1_300_e8's late games: 500 positions per ply from 40 to 70, a shared budget of
#       1e8 counted nodes per position for the complete legal-action value coverage, the 256-sim plain-evaluator
#       search graded on the complete subset; Wilson intervals, the per-position table beside the aggregates.
#       CPU-bound (8 solver processes; K1's 12 exact-label workers share the 24 cores), ≈ 3.5 h.
# Outputs: runs/plan7/J3_empty_board_e8.json, J3_empty_board_e4.json, J4_frontier.json + J4_frontier_positions.npz,
# and the .out files beside them; the combined log runs/plan7/J3J4.out. The readings become KNOWLEDGE lines in the
# forms §4 J3 / J4 fix (the J4 sentence is written out there).
# Launch: bash runs/plan7/J3J4_3060.sh
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
D=cuda:1
run() {  # run <out> <header> <cmd...>
  local out=$1 hdr=$2; shift 2
  echo "=== $hdr ($(date +%H:%M))"
  "$@" > "$out" 2>&1
  echo "    -> $out ($?)"
}
{
echo "J3 / J4 started $(date)"
run runs/plan7/J3_empty_board_e8.out "J3 empty board, deep8_c1_300_e8" \
  $P tools/empty_board.py --net runs/deep8_c1_300_e8/net_0300.pt --games 2000 --sims 256 --root_sims 16384 --device $D --rule count --out runs/plan7/J3_empty_board_e8.json
run runs/plan7/J3_empty_board_e4.out "J3 empty board, deep8_c1_300_e4" \
  $P tools/empty_board.py --net runs/deep8_c1_300_e4/net_0300.pt --games 2000 --sims 256 --root_sims 16384 --device $D --rule count --out runs/plan7/J3_empty_board_e4.json
run runs/plan7/J4_frontier.out "J4 exact frontier, deep8_c1_300_e8 late games, plies 40-70" \
  $P tools/frontier.py --run runs/deep8_c1_300_e8 --net runs/deep8_c1_300_e8/net_0300.pt --plies 40 70 --per_ply 500 --max_nodes 1e8 --sims 256 --processes 8 --device $D --rule count --out runs/plan7/J4_frontier.json
echo "J3 / J4 DONE ($(date +%H:%M))"
} >> runs/plan7/J3J4.out 2>&1
