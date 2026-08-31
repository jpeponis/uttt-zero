#!/bin/bash
# After the ablation queue: c_scale 1.0 combined with wider nets, each evaluated after training.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
while [ ! -f runs/abl_noheads/net_0150.pt ]; do sleep 180; done
sleep 60
BASE="--iters 150 --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --lr 0.02 --lr_drops 100,140 --eval_every 10 --eval_sims 64 --anchors runs/dev1/net_0200.pt,runs/v2b/net_0150.pt --save_buffer_every 10 --cuda_graph 1 --depth_cap 12 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --c_scale 1.0 --device cuda:0"
$P -u -m uttt.train2 --run runs/wide96_c1 --filters 96 $BASE > runs/wide96_c1.out 2>&1
bash runs/eval_run.sh wide96_c1 cuda:1 &
$P -u -m uttt.train2 --run runs/wide128_c1 --filters 128 $BASE > runs/wide128_c1.out 2>&1
wait
bash runs/eval_run.sh wide128_c1 cuda:0
echo "after-queue2 done at $(date)"
