#!/bin/bash
# PLAN6 H4 follow-up (2026-09-09): why did the G-CNN, the best supervised student (KNOWLEDGE 48), lose ~250 Elo to
# its ResNet parent in self-play? The in-run signature is a too-high constant LR, not instability: the policy loss is
# flat over iterations 100-190 and falls 15 % at the first drop (the parent: 8 %); the drop is worth +223 Elo to it
# against the parent's +70; the opening prior flips between orbits across adjacent checkpoints (p(40) 0.24 / 0.69 /
# 0.15 at 180 / 190 / 200) and its Hessian top eigenvalue is 2.3x the ResNet's at the same point. The supervised
# study used the same SGD 0.02 but only 2080 top-LR steps against 204 800 in the run. This sweep doubles the
# supervised step count (400k x 16 passes = 6250 steps, ~14 min per arm on the 3060) at the run's LR and at a
# quarter of it, for both nets. Reading: if the G-CNN's dev-KL advantage over the ResNet shrinks at 0.02 as steps
# grow but holds at 0.005, the LR is the cause; if it shrinks at both, capacity (312 k parameters); the 8-pass points
# already on file (G_arm_gcnn8x16.json 0.806, G_arm_resnet8.json 0.884, lr 0.02) are the comparison.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
for LR in 0.02 0.005; do
  for ARM in gcnn8x16 resnet8; do
    echo "=== $ARM lr $LR, 400k x 16 ($(date +%H:%M))"
    $P -u tools/gstudy.py --data runs/gdata_v1.npz --arm $ARM --positions 400000 --passes 16 --seeds 0 --lr $LR --device cuda:1 --out runs/plan6/H4_lr_${ARM}_lr${LR}.json
  done
done
echo "H4 LR sweep DONE ($(date +%H:%M))"
} >> runs/plan6/H4_lr_sweep.out 2>&1
