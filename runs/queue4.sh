#!/bin/bash
# PLAN4 queue for the 3090: (A) depth 6->8 blocks at 128 filters, then (B) self-play sims 64->96
# in the final phase. One change per run vs wide128_c1; each followed by the standard eval chain.
# wide128_c1 joins the in-run anchors (its net_0150 is the new co-reference next to v2b).
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
BASE="--iters 150 --games 4096 --steps 64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --lr 0.02 --lr_drops 100,140 --eval_every 10 --eval_sims 64 --anchors runs/dev1/net_0200.pt,runs/v2b/net_0150.pt,runs/wide128_c1/net_0150.pt --save_buffer_every 10 --cuda_graph 1 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --c_scale 1.0 --filters 128 --device cuda:0"
$P -u -m uttt.train2 --run runs/deep8_c1 --blocks 8 --sims 32 --sims_schedule 60:48,100:64 --depth_cap 12 $BASE > runs/deep8_c1.out 2>&1        # A: ~6.1 h (probe_b8: 1630 pos/s)
bash runs/eval_run.sh deep8_c1 cuda:1 &
$P -u -m uttt.train2 --run runs/wide128_c1_s96 --sims 32 --sims_schedule 60:48,100:96 --depth_cap 16 $BASE > runs/wide128_c1_s96.out 2>&1      # B: ~5.3 h (final phase 1.5x)
wait
bash runs/eval_run.sh wide128_c1_s96 cuda:0
echo "queue4 done at $(date)"
