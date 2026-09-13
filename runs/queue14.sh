#!/bin/bash
# PLAN7 §5 K1 -- deep8_c1_300_e8_draw: the most-boards tiebreak as a controlled variable. NOT LAUNCHED UNTIL THE OWNER
# APPROVES IT (PLAN7 §5; the ladder moves only by owner approval, PLAN4 §3c / PLAN5 §5) and only under the 50 % line.
# The parent deep8_c1_300_e8's recipe (queue13.sh: 8x128 ResNet, 300 iterations, 4096 x 64 new positions per
# iteration, --epochs 8 = 2048 optimizer steps of batch 1024 per iteration, LR drops at 200 / 280, seed 0) with ONE
# change: --rule draw -- when all nine boards close with no macro line the game is a draw (the Wikipedia / uttt.ai /
# SaltZero / OpenSpiel rule) instead of going to the board count. Everything else identical, including the margin and
# ownership auxiliary targets (PLAN7 §5, M2 row 16 of M0: deliberately count-flavoured and unchanged).
# Provenance (M2 row 5): --gumbel_scale 1.0 is passed EXPLICITLY -- it is the value every run so far trained at
# (SearchConfig's default, never recorded before); the trainer now writes the resolved search configuration into
# config.json's _provenance. The in-run endgame set is the draw-rule twin of the parent's (suites/endgame_v2_dev_draw.npz,
# built 2026-09-12 by tools/endgame.py build --rule draw from the same corpus, split and seed as endgame_v2_dev; the
# trainer and the E7 worker refuse a count-solved set under draw). The E7 worker's anchors are the standing convention
# (v2b, the parent deep8_c1_300_e8, deep8_c1_300), all count-trained, PLAYED UNDER DRAW: PLAN7 §5 item 6, shape only --
# there is no draw-trained reference and none is proposed; scores against them are not comparable with a count run's.
# Why: every game claim in KNOWLEDGE §1-§8 is read under the count rule; K1 re-reads each under draw and marks it
# rule-invariant / rule-dependent / unresolved (PLAN7 §5 item 2, thresholds pre-registered there after M2). Readings:
#   0. the no-training relabel control -- done on the parent (15.7 % of outcomes change, 32.3 % reach the no-line terminal;
#      runs/plan7/K1_parent_A6_corpus_stats.out);
#   1. the count-rule parent re-read -- the I1 tool set on _e8 under count (runs/plan7/K1_parent_*.out, 2026-09-12);
#   2. the I1 tool set on THIS net under draw (runs/plan7/K1_*.out; a separate script after the run) -- primary;
#   3. both nets under both rules on one frozen position set; the exact minimax change on the solved subset;
#   4. cross-play: two scores (this net vs _e8 under count and under draw), the contrast 1 - s_D - s_C, a joint pair
#      bootstrap by opening, no mechanism attributed (eval_run_k1.sh writes both matches);
#   5. corpus statistics over the last 20 iterations; 6. the E7 curve against the count anchors under draw, shape only.
# What K1 cannot say (PLAN7 §5): anything absolute about strength between the two nets (different games); anything
# about the open-board variant; one seed -- every reading is "observed in this pair of runs".
# Cost ~22 h on the 3090 (the parent took 21.96 h) + ~6 h on the 3060 for the readings. Inside the update pause.
# Launch (hidden console, survives any terminal): wscript runs/launch_queue14_hidden.vbs
# Status: python tools/run_status.py runs/deep8_c1_300_e8_draw --ref runs/deep8_c1_300_e8
# Reboot: relaunch the same .vbs; train2 prefers latest_full.pt and continues as attempt N (a cross-RULE resume is
# refused, M2 row 1); the worker skips what eval_full_draw.jsonl already holds.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
PARENT=deep8_c1_300_e8
R=deep8_c1_300_e8_draw
SET=suites/endgame_v2_dev_draw.npz

run_train() {  # auto-resume on crash (train2 resumes from latest_full.pt), max 6 attempts
  local name=$1; shift
  for i in 1 2 3 4 5 6; do
    $P -u -m uttt.train2 --run runs/$name "$@" >> runs/$name.out 2>&1
    [ -f runs/$name/DONE ] && return 0
    echo "=== $name attempt $i died at $(date); resuming in 60s" >> runs/$name.out
    sleep 60
  done
  echo "=== $name FAILED after 6 attempts" >> runs/$name.out
  return 1
}

[ -f runs/$PARENT/net_0300.pt ] || { echo "parent runs/$PARENT/net_0300.pt missing" >> runs/queue14.out; exit 1; }
[ -f $SET ] || { echo "draw-rule endgame set $SET missing: tools/endgame.py build --rule draw first" >> runs/queue14.out; exit 1; }
mkdir -p runs/$R
$P -u tools/eval_worker.py --run runs/$R --rule draw --anchors runs/v2b/net_0150.pt,runs/$PARENT/net_0300.pt,runs/deep8_c1_300/net_0300.pt --sims 64 --set $SET --poll 60 --device cuda:1 >> runs/${R}_worker.out 2>&1 &
run_train $R --rule draw --gumbel_scale 1.0 --endgame_set $SET --iters 300 --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --c_scale 1.0 --filters 128 --blocks 8 --depth_cap 12 --lr 0.02 --lr_drops 200,280 --epochs 8 --eval_every 0 --ckpt_every 10 --anchors "" --save_buffer_every 10 --cuda_graph 1 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --device cuda:0
bash runs/eval_run_k1.sh $R cuda:0
wait
echo "queue14 done at $(date)"
