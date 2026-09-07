#!/bin/bash
# PLAN6 §4 follow-ups after the first read of the arms: (1) arm (c) again -- its endgame WDL number was an
# evaluation artefact (uttt.endgame.wdl_probs encoded the position without the net's closed-board mask; fixed
# 2026-09-07); (2) the sample-efficiency points of §4's gate (ii) for the two arms that beat the ResNet -- gcnn8x16
# and resnet8_tied at 100k x 8, 200k x 8, 400k x 4 (the G0 grid showed the ResNet's fit is a function of optimizer
# steps, so these are the ResNet's own G0 points to compare with). Students saved under runs/plan6/students/.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
until [ -f runs/deep8_c1_300_e2/timeline.png ]; do sleep 30; done
{
echo "=== arm resnet8_mask, rerun with the WDL fix ($(date +%H:%M))"
$P -u tools/gstudy.py --data runs/gdata_v1.npz --arm resnet8_mask --positions 400000 --passes 8 --seeds 0,1 --device cuda:1 --save runs/plan6/students --out runs/plan6/G_arm_resnet8_mask.json
for ARM in gcnn8x16 resnet8_tied; do
  echo "=== $ARM sample-efficiency points ($(date +%H:%M))"
  $P -u tools/gstudy.py --data runs/gdata_v1.npz --arm $ARM --positions 100000,200000 --passes 8 --seeds 0 --device cuda:1 --save runs/plan6/students --out runs/plan6/G0_$ARM.json
  $P -u tools/gstudy.py --data runs/gdata_v1.npz --arm $ARM --positions 400000 --passes 4 --seeds 0 --device cuda:1 --save runs/plan6/students --out runs/plan6/G0b_$ARM.json
done
echo "G queue 3 DONE ($(date +%H:%M))"
} >> runs/plan6/G_queue.out 2>&1
