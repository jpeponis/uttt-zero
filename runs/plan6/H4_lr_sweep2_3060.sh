#!/bin/bash
# PLAN6 H4 follow-up, second sweep (2026-09-09; the first is H4_lr_sweep_3060.sh, read in the log's 2026-09-09 entry):
# at lr 0.02 the G-CNN's supervised advantage over the ResNet shrank from 0.078 (8 passes) to 0.027 (16 passes) --
# the ResNet gains 4x more per doubling of the steps -- and the lr-0.005 arm at one step count could not separate
# "the G-CNN sits at an LR-set floor" from "312 k parameters saturate". Two questions, three arms, ~1.4 h on the 3060:
# (1) both nets at lr 0.02 x 32 passes (12 480 steps): does the ResNet overtake? (2) the G-CNN at lr 0.005 x 32: does
# it beat its own lr-0.02 x 32 number at equal steps (an LR floor -> propose the G-CNN at a lower LR) or not
# (capacity -> the wider G-CNN or --head_tying 1)?
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
for JOB in "gcnn8x16 0.02" "resnet8 0.02" "gcnn8x16 0.005"; do
  set -- $JOB; ARM=$1; LR=$2
  echo "=== $ARM lr $LR, 400k x 32 ($(date +%H:%M))"
  $P -u tools/gstudy.py --data runs/gdata_v1.npz --arm $ARM --positions 400000 --passes 32 --seeds 0 --lr $LR --device cuda:1 --out runs/plan6/H4_lr2_${ARM}_lr${LR}_x32.json
done
echo "H4 LR sweep 2 DONE ($(date +%H:%M))"
} >> runs/plan6/H4_lr_sweep2.out 2>&1
