#!/bin/bash
# PLAN6 §9d, the 3060 half of the closing programme, in the owner's order: G arm (g) first (§9b, ~9-10 h for the
# three points, the decisive 32-pass one first), then I1 (§9c, ~5 h). One card, one process at a time -- the two
# studies never overlap, so neither is timed against a contended card more than the E7 worker already makes it.
# Started as soon as H1c (queue13, the 3090) is launched and running beside it: the E7 worker of H1c shares this
# card throughout, ~6 min per checkpoint every ~43 min (about a seventh busy). That is expected and is why every
# wall-clock here reads longer than the same tool's cost in PLAN5's pass.
# Each script keeps its own log -- runs/plan6/G_arm_g.out and runs/plan6/I1_second_pass.out (plus one .out per I1
# tool); this file only records which step started when, so "where did it get to" is one tail away.
# Launch (detached, from the repo root):  nohup bash runs/plan6/closing_3060.sh >/dev/null 2>&1 &
# It is a plain bash wrapper, so it dies with its terminal session (the log's 08:25 entry). Both halves are
# restartable: gstudy rewrites its JSON after every point, and I1's steps are independent -- re-run the wrapper and
# comment out what the logs show already finished.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
{
echo "=== closing 3060 queue started $(date)"
echo "=== G arm (g) gcnn8x46 ($(date +%H:%M)) -> runs/plan6/G_arm_g.out"
bash runs/plan6/G_arm_g_3060.sh
echo "=== I1 second pass on deep8_c1_300_e4 ($(date +%H:%M)) -> runs/plan6/I1_second_pass.out"
bash runs/plan6/I1_second_pass_3060.sh
echo "closing 3060 queue DONE $(date)"
} >> runs/plan6/closing_3060.out 2>&1
