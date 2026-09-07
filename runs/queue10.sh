#!/bin/bash
# PLAN6 Handover H1b (owner-approved 2026-09-07): deep8_c1_300_e4 -- dose-response on the update count. Identical to
# deep8_c1_300_e2's recipe (queue9) except --epochs 4 (1024 optimizer steps per iteration instead of 512), with the
# PLAN6 operational settings: no evaluation in the trainer (--eval_every 0), numbered checkpoints every 10 iterations
# (--ckpt_every 10), the E7 worker scoring every checkpoint on the FULL paired suite on the 3060 (anchors v2b,
# deep8_c1_300_e2 (the parent), deep8_c1_300; endgame_v2_dev). Pre-registered reading (PLAN6 Handover): primary vs
# deep8_c1_300_e2 at 64 sims -- helped >= 53 % (still update-limited), 47-53 null (epochs 2 is the plateau),
# hurt <= 47 % (over-fitting the buffer window); the seed band is ~3 points.
# Launch (hidden console, survives any terminal): wscript runs/launch_queue10_hidden.vbs
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
R=deep8_c1_300_e4

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

mkdir -p runs/$R
$P -u tools/eval_worker.py --run runs/$R --anchors runs/v2b/net_0150.pt,runs/deep8_c1_300_e2/net_0300.pt,runs/deep8_c1_300/net_0300.pt --sims 64 --set suites/endgame_v2_dev.npz --poll 60 --device cuda:1 >> runs/${R}_worker.out 2>&1 &
run_train $R --iters 300 --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --c_scale 1.0 --filters 128 --blocks 8 --depth_cap 12 --lr 0.02 --lr_drops 200,280 --epochs 4 --eval_every 0 --ckpt_every 10 --anchors "" --save_buffer_every 10 --cuda_graph 1 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --device cuda:0
bash runs/eval_run.sh $R cuda:0
$P tools/endgame.py eval runs/$R/net_0300.pt --set suites/endgame_v2_dev.npz --device cuda:0 >> runs/$R/analysis.out 2>&1
wait
echo "queue10 done at $(date)"
