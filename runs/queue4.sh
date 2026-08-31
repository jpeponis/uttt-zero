#!/bin/bash
# PLAN4 queue for the 3090: (A) depth 6->8 blocks at 128 filters, then (B) self-play sims 64->96
# in the final phase. One change per run vs wide128_c1; each followed by the standard eval chain.
# run_train auto-resumes after a crash (2026-08-30: two nvlddmkm GPU faults during in-run eval killed
# both runs; train2 now checkpoints full state to latest_full.pt and resumes from it, and a fresh
# process gets a clean CUDA context). If eval faults persist, add --eval_graph 0 to BASE.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
BASE="--iters 150 --games 4096 --steps 64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --lr 0.02 --lr_drops 100,140 --eval_every 10 --eval_sims 64 --anchors runs/dev1/net_0200.pt,runs/v2b/net_0150.pt,runs/wide128_c1/net_0150.pt --save_buffer_every 10 --cuda_graph 1 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --c_scale 1.0 --filters 128 --device cuda:0"

run_train() {  # run_train <name> <extra args...>: train with auto-resume on crash, max 6 attempts
  local name=$1; shift
  for i in 1 2 3 4 5 6; do
    $P -u -m uttt.train2 --run runs/$name "$@" $BASE >> runs/$name.out 2>&1
    [ -f runs/$name/DONE ] && return 0
    echo "=== $name attempt $i died at $(date); resuming in 60s" >> runs/$name.out
    sleep 60
  done
  echo "=== $name FAILED after 6 attempts" >> runs/$name.out
  return 1
}

run_train deep8_c1 --blocks 8 --sims 32 --sims_schedule 60:48,100:64 --depth_cap 12          # A: ~6.1 h (probe_b8: 1630 pos/s)
bash runs/eval_run.sh deep8_c1 cuda:1 &
run_train wide128_c1_s96 --sims 32 --sims_schedule 60:48,100:96 --depth_cap 16               # B: ~5.3 h (final phase 1.5x)
wait
bash runs/eval_run.sh wide128_c1_s96 cuda:0
echo "queue4 done at $(date)"
