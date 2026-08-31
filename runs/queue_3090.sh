#!/bin/bash
# Queue for the 3090 after v2d (PLAN2 §5 steps 5-6). Base = the v2c recipe (v2b + exact labels, a no-op but free).
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
BASE="--iters 150 --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --lr 0.02 --lr_drops 100,140 --eval_every 10 --eval_sims 64 --anchors runs/dev1/net_0200.pt,runs/v2b/net_0150.pt --save_buffer_every 10 --cuda_graph 1 --depth_cap 12 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --device cuda:0"
$P -u -m uttt.train2 --run runs/wide96 --filters 96 $BASE > runs/wide96.out 2>&1                      # step 5: 6x96 net (capacity is the endgame lever, §2f)
$P -u -m uttt.train2 --run runs/abl_cscale1 --c_scale 1.0 $BASE > runs/abl_cscale1.out 2>&1          # step 6: Gumbel c_scale 0.1 -> 1.0
$P -u -m uttt.train2 --run runs/abl_noheads --own_weight 0 --margin_weight 0 $BASE > runs/abl_noheads.out 2>&1  # step 6: auxiliary heads off
echo queue done
