#!/bin/bash
# PLAN6 Handover H3 (pre-approved by the owner 2026-09-07 as the third link of the chain H1b -> H4 -> H3):
# deep8_c1_600_e4 -- duration at the right update count. deep8_c1_300_e4's recipe (H1b: 8x128, --epochs 4 = 1024 steps
# per iteration) run for 600 iterations with ONE LR drop at 500 (PLAN6 F2: the second drop does nothing resolvable;
# D3: the drop is a fixed step on whatever the constant-LR phase has built, settling in ~20 iterations), so this is in
# effect "300 more constant-LR iterations" on the H1b recipe. Parent: deep8_c1_300_e4. Reading (PLAN6 Handover):
# the E7 full-suite curve from 300 to 500 (flat = duration exhausted at this data rate, climbing = not), and the final
# net (net_0600) vs the parent at 64 sims -- helped >= 53 %, hurt <= 47 %, else null; seed band ~3 points.
# ~34-36 h. Launch (hidden console, survives any terminal): wscript runs/launch_queue12_hidden.vbs
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
PARENT=deep8_c1_300_e4
R=deep8_c1_600_e4

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

[ -f runs/$PARENT/net_0300.pt ] || { echo "parent runs/$PARENT/net_0300.pt missing" >> runs/queue12.out; exit 1; }
mkdir -p runs/$R
$P -u tools/eval_worker.py --run runs/$R --anchors runs/v2b/net_0150.pt,runs/$PARENT/net_0300.pt,runs/deep8_c1_300/net_0300.pt --sims 64 --set suites/endgame_v2_dev.npz --poll 60 --device cuda:1 >> runs/${R}_worker.out 2>&1 &
run_train $R --iters 600 --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --c_scale 1.0 --filters 128 --blocks 8 --depth_cap 12 --lr 0.02 --lr_drops 500 --epochs 4 --eval_every 0 --ckpt_every 10 --anchors "" --save_buffer_every 10 --cuda_graph 1 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --device cuda:0
bash runs/eval_run.sh $R cuda:0
$P tools/endgame.py eval runs/$R/net_0600.pt --set suites/endgame_v2_dev.npz --device cuda:0 >> runs/$R/analysis.out 2>&1
wait
echo "queue12 done at $(date)"
