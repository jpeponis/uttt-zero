#!/bin/bash
# PLAN6 §9a H1c (owner-approved 2026-09-09; the chain's replacement third link, after H3 was withdrawn):
# deep8_c1_300_e8 -- the THIRD doubling of the optimizer steps. deep8_c1_300_e4's recipe (H1b: 8x128 ResNet) with
# --epochs 8 and nothing else changed: 2048 optimizer steps of batch 1024 per iteration (8 x 4096 x 64 / 1024,
# train2.py:356), 614 400 in the run against H1b's 307 200; the same 4096 x 64 new positions per iteration, the same
# 2 M-row buffer, LR drops at 200 / 280, seed 0. Parent: deep8_c1_300_e4 (the play agent, +363 vs v2b).
# Why: the dose-response curve of KNOWLEDGE 46 / 49 -- +100 Elo for the first doubling of the update count, +64 for
# the second, then what -- read to its asymptote or its plateau (either is a finding, and this is the last cheap
# point on the axis); and the first direct test of the over-fitting branch H1's reading wrote and never fired -- at
# eight passes each generated position is sampled eight times in expectation from a buffer window of 7.6 iterations.
# Reading (PLAN6 §9a), pre-registered before the launch:
#   PRIMARY   net_0300 vs deep8_c1_300_e4 on the FULL paired suite @64 -- >= 53 % helped, <= 47 % hurt, else null --
#             with the seed band (~3 points) stated beside it (eval_run.sh writes paired_vs_deep8c1_300e4_64.json).
#   SECONDARY vs deep8_c1_300_e2 and deep8_c1_300, so the dose-response is read as a curve across 1x / 2x / 4x / 8x
#             the updates and not as one more pairwise step (eval_run.sh writes both matches); the E7 full-suite
#             curve against H1b's at matched iterations (does the constant-LR phase lift again, and by how much
#             less); and the budget axes for over-fitting the buffer window (E8's per-iteration fields): the sampled
#             distinct-position fraction (H1 0.81 -> 0.75, H1b 0.67 -> 0.62; eight passes should read lower again),
#             the skipped-step count (H1 70 of 153 600, H1b 133 of 307 200 -- the same rate) and the policy loss's
#             late trend.
#   TERTIARY  the endgame reads on endgame_v1 and endgame_v2_dev against H1b's 90.1 % raw WDL / 79.0 % draw
#             recognition / 0.022 regret.
#   Helped -> the learner is still update-limited at eight passes; state the curve (+100, +64, +X) and where it puts
#   the plateau. Null -> the plateau lies between four and eight passes at this data rate and the +164 of the first
#   two doublings stands as the axis's total. Hurt -> the buffer window is over-fitted at eight passes, which is
#   itself the finding: the buffer, not the update count, is the knob. The play agent changes only if it helps.
# Cost ~22-23 h against H1b's 16.9 (t_train ~10 h against 4.98 -- training is the only term that doubles; self-play
# unchanged at ~12 h, the same 8x128 ResNet at the same sims). Inside the update pause (2026-10-14).
# The E7 worker's anchors are §9a's: v2b, the parent deep8_c1_300_e4 and deep8_c1_300 -- the standing convention
# (queue10 / queue11 / queue12), and deep8_c1_300 is the 1x point every earlier run's curve shares, so H1b's curve
# and this one are comparable at matched iterations. deep8_c1_300_e2 (the 2x point) is NOT a worker anchor: the
# secondary reading needs it only at the final checkpoint, and eval_run.sh already runs that match.
# Launch (hidden console, survives any terminal): wscript runs/launch_queue13_hidden.vbs
# Status: python tools/run_status.py runs/deep8_c1_300_e8 --ref runs/deep8_c1_300_e4
# Reboot (the one failure the retry wrapper cannot cover -- the bash wrapper dies with the session): relaunch the
# same .vbs; train2 prefers latest_full.pt and continues as attempt N (de-duplicate log.jsonl by iteration when
# reading it), and the worker skips what eval_full.jsonl already holds.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
PARENT=deep8_c1_300_e4
R=deep8_c1_300_e8

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

[ -f runs/$PARENT/net_0300.pt ] || { echo "parent runs/$PARENT/net_0300.pt missing" >> runs/queue13.out; exit 1; }
mkdir -p runs/$R
$P -u tools/eval_worker.py --run runs/$R --anchors runs/v2b/net_0150.pt,runs/$PARENT/net_0300.pt,runs/deep8_c1_300/net_0300.pt --sims 64 --set suites/endgame_v2_dev.npz --poll 60 --device cuda:1 >> runs/${R}_worker.out 2>&1 &
run_train $R --iters 300 --games 4096 --steps 64 --sims 32 --sims_schedule 60:48,100:64 --sample_moves 8 --sample_uniform 0.15 --root_prior_floor 0.03 --dedup_alpha 0.5 --c_scale 1.0 --filters 128 --blocks 8 --depth_cap 12 --lr 0.02 --lr_drops 200,280 --epochs 8 --eval_every 0 --ckpt_every 10 --anchors "" --save_buffer_every 10 --cuda_graph 1 --exact_max_empty 14 --exact_per_iter 8192 --exact_processes 12 --device cuda:0
bash runs/eval_run.sh $R cuda:0
$P tools/endgame.py eval runs/$R/net_0300.pt --set suites/endgame_v2_dev.npz --device cuda:0 >> runs/$R/analysis.out 2>&1
wait
echo "queue13 done at $(date)"
