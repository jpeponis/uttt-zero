#!/bin/bash
# After the ablation queue: 6x128 net with the same recipe, then its evaluation.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
while [ ! -f runs/abl_noheads/net_0150.pt ]; do sleep 180; done
sleep 60
BASE="--iters 150 --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --lr 0.02 --lr_drops 100,140 --eval_every 10 --eval_sims 64 --anchors runs/dev1/net_0200.pt,runs/v2b/net_0150.pt --save_buffer_every 10 --cuda_graph 1 --depth_cap 12 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --device cuda:0"
$P -u -m uttt.train2 --run runs/wide128 --filters 128 $BASE > runs/wide128.out 2>&1
bash runs/eval_run.sh wide128 cuda:0
echo "wide128 trained and evaluated at $(date)"
