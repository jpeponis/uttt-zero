#!/bin/bash
# PLAN6 §9b, G arm (g) gcnn8x46: the D4 group-convolutional net (uttt/equivariant.py) at the ResNet's parameter
# count, on frozen data. Why: H4 read as capacity, not equivariance (KNOWLEDGE 50) -- but the only equivariant net
# this project has ever trained carries 312 k parameters against resnet8's 2.46 M, so "is the inductive bias wrong
# for this game, or was the net simply too small?" is still open, and Phase G answers exactly this kind of question
# on frozen data for no GPU-day. The arm: 8 blocks at 46 base filters x 8 orientations = activation width 368,
# 2 459 392 parameters against resnet8's 2 456 014 (0.1 % apart) -- tools/gstudy.py ARMS["gcnn8x46"].
#
# COST, MEASURED FIRST AND DECLARED UP FRONT (§9b requires this in every sentence about the arm; runs/plan6/
# G_timing_3060_gcnn8x46.json, 2026-09-09, both cards idle): on the 3060 the exported net costs 595.5 ms per 4096
# evaluations against resnet8's 84.8 ms in the same session -- 7.0x, not the ~2.5x a parameter-count intuition
# suggests, because the exported net is an ordinary 368-filter ResNet (19.6 M exported parameters) and trunk
# convolution work scales with the square of the activation width. At batch 1 it is 0.503 ms against 0.392 ms
# (1.28x; batch 1 is launch-latency bound). This is NOT an equal-cost arm and must never be written as one.
# Budget here, scaled from gcnn8x16's 2250 s at 12 480 steps by (46/16)^2: ~5 h for the 32-pass point and ~9-10 h
# for all three, with the E7 worker of H1c sharing the card (~a seventh busy).
#
# --passes 32,8,16 -- gstudy iterates the list in the order given (tools/gstudy.py main: a plain generator over
# --passes.split(","), no sort), and every student is trained from scratch under torch.manual_seed(--seeds), so the
# order changes nothing but which point exists first. 32 is first deliberately: §9b's reading is taken at 12 480
# steps and "if the card is wanted for I1, the 12 480-step point is the one that must exist". The JSON is rewritten
# after every point, so an interrupted run keeps what it finished.
#
# Pre-registered reading (§9b), at the 32-pass / 12 480-step point, dev slice only (endgame_v3_test stays sealed),
# against the points already on file (dev policy KL vs the teacher):
#     steps        3 120    6 240   12 480
#     resnet8      0.884    0.8145  0.7630
#     gcnn8x16     0.806    0.7875  0.8298
#   - leads resnet8 at 12 480 with a margin that is NOT closing across the three doublings -> the inductive bias is
#     right at equal capacity, H4's result was the 312 k parameters, and a self-play run at this width becomes a
#     proposable science question -- with the 7.0x inference cost above declared up front, and explicitly not a
#     ladder rung (the ladder is read at a fixed inference budget).
#   - trails, or its margin closes as gcnn8x16's did -> the bias is wrong for this game at any capacity this project
#     can afford; recorded in KNOWLEDGE 48 / 50 and the equivariant line closes.
# Launch (3060, beside H1c on the 3090): bash runs/plan6/G_arm_g_3060.sh   (or through runs/plan6/closing_3060.sh)
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
echo "=== G arm (g) gcnn8x46, 400k positions x 32,8,16 passes, lr 0.02, seed 0, dev slice ($(date +%H:%M))"
$P -u tools/gstudy.py --data runs/gdata_v1.npz --arm gcnn8x46 --positions 400000 --passes 32,8,16 --seeds 0 --lr 0.02 --device cuda:1 --out runs/plan6/G_arm_gcnn8x46.json
# NOT automatic (§9b's tie rule): only if the 32-pass dev policy KL lands within 0.005 of resnet8's 0.7630, run a
# second seed at that point by hand and read the two together -- ~5 h more on the 3060:
# $P -u tools/gstudy.py --data runs/gdata_v1.npz --arm gcnn8x46 --positions 400000 --passes 32 --seeds 1 --lr 0.02 --device cuda:1 --out runs/plan6/G_arm_gcnn8x46_s1.json
echo "G arm (g) DONE ($(date +%H:%M))"
} >> runs/plan6/G_arm_g.out 2>&1
