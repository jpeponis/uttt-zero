#!/bin/bash
# PLAN5 §5 D3 (owner-approved 2026-09-05): the earlier-LR-drop experiment. Identical to queue6's deep10_c1_300
# (seed 0) except --lr_drops 150,250 (was 200,280), plus D1's operational settings: graph eval on with the retry
# wrapper, --eval_every 10 for a dense timeline, deep10_c1_300 added to the anchors. Pre-registered reading in
# PLAN5 §5 D3. Not a rung of the ladder unless it clears the ±3 rule against BOTH 10-block seeds.
# Launch (hidden console, survives any terminal): schtasks /Run /TN uttt-queue8, or wscript runs/launch_queue8_hidden.vbs
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe

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

run_train deep10_c1_300_lr150 --iters 300 --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --c_scale 1.0 --filters 128 --blocks 10 --depth_cap 12 --lr 0.02 --lr_drops 150,250 --eval_every 10 --eval_sims 64 --eval_graph 1 --anchors runs/v2b/net_0150.pt,runs/deep8_c1_300/net_0300.pt,runs/deep10_c1_300/net_0300.pt --save_buffer_every 10 --cuda_graph 1 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --device cuda:0
bash runs/eval_run.sh deep10_c1_300_lr150 cuda:0
echo "queue8 done at $(date)"
