#!/bin/bash
# PLAN6 H4 follow-up, third sweep (2026-09-09): sweeps 1 and 2 (H4_lr_sweep_3060.sh, H4_lr_sweep2_3060.sh; the log's
# 2026-09-09 entry) showed the G-CNN's supervised advantage is a small-step advantage -- at 12 480 steps the plain
# ResNet overtakes it (dev KL 0.763 vs 0.830) and a lower LR does not help. Phase G's gate was read at 3 120 steps.
# Before --head_tying 1 (the pre-registered hedge; KL 0.848 at 3 120 steps against the ResNet's 0.884) can be proposed,
# the same test: resnet8_tied at lr 0.02 for 16 and 32 passes (6 240 and 12 480 steps), against the resnet8 points
# already on file (0.8145 / 0.7630). ~36 min on the 3060.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
echo "=== resnet8_tied lr 0.02, 400k x 16,32 ($(date +%H:%M))"
$P -u tools/gstudy.py --data runs/gdata_v1.npz --arm resnet8_tied --positions 400000 --passes 16,32 --seeds 0 --lr 0.02 --device cuda:1 --out runs/plan6/H4_lr3_resnet8_tied_lr0.02.json
echo "H4 LR sweep 3 DONE ($(date +%H:%M))"
} >> runs/plan6/H4_lr_sweep3.out 2>&1
