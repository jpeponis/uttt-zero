#!/bin/bash
# PLAN6 Handover H4 (pre-approved by the owner 2026-09-07 as the second link of the chain H1b -> H4 -> H3):
# gcnn8_c1_300_e<E> -- the D4 group-convolutional net (uttt/equivariant.py, 16 base filters x 8 orientations =
# activation width 128, exact equivariance by construction, the same inference cost as the 8x128 ResNet because it
# exports to ordinary convolutions) in self-play. Everything else is H1's recipe at the chain's epochs E, so the parent
# is the 8-block ResNet at the same E: deep8_c1_300_e4 if H1b helped (>= 53 % vs e2), else deep8_c1_300_e2.
# SET E AND PARENT BELOW FROM H1b's PRE-REGISTERED READING BEFORE LAUNCHING. Reading (PLAN6 Handover): primary vs the
# parent at 64 sims (equal cost by construction) -- helped >= 53 %, hurt <= 47 %, else null; secondary the D4 residual
# (timeline.py's D4 JS column must read 0.000) and the endgame reads. Fallback if the G-CNN misbehaves in RL
# (diverging losses, many skipped steps): --head_tying 1 on the plain trunk instead of --gcnn 16.
# Launch (hidden console, survives any terminal): wscript runs/launch_queue11_hidden.vbs
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
E=4                       # <-- H1b's reading: 4 if it helped, else 2
PARENT=deep8_c1_300_e4    # <-- deep8_c1_300_e4 if E=4, deep8_c1_300_e2 if E=2
R=gcnn8_c1_300_e$E

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

[ -f runs/$PARENT/net_0300.pt ] || { echo "parent runs/$PARENT/net_0300.pt missing" >> runs/queue11.out; exit 1; }
mkdir -p runs/$R
$P -u tools/eval_worker.py --run runs/$R --anchors runs/v2b/net_0150.pt,runs/$PARENT/net_0300.pt,runs/deep8_c1_300/net_0300.pt --sims 64 --set suites/endgame_v2_dev.npz --poll 60 --device cuda:1 >> runs/${R}_worker.out 2>&1 &
run_train $R --iters 300 --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --c_scale 1.0 --filters 128 --blocks 8 --gcnn 16 --depth_cap 12 --lr 0.02 --lr_drops 200,280 --epochs $E --eval_every 0 --ckpt_every 10 --anchors "" --save_buffer_every 10 --cuda_graph 1 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --device cuda:0
bash runs/eval_run.sh $R cuda:0
$P tools/endgame.py eval runs/$R/net_0300.pt --set suites/endgame_v2_dev.npz --device cuda:0 >> runs/$R/analysis.out 2>&1
wait
echo "queue11 done at $(date)"
