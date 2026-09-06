#!/bin/bash
# PLAN6 §4 arms (d) resnet8_tied and (e) gcnn8x16 (uttt.equivariant), two seeds each at 400k x 8 passes, after the
# first queue (G0 + arms a-c) has finished on the 3060. Appends to runs/plan6/G_queue.out.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
until grep -q "G queue DONE" runs/plan6/G_queue.out 2>/dev/null; do sleep 60; done
{
for ARM in resnet8_tied gcnn8x16; do
  echo "=== arm $ARM ($(date +%H:%M))"
  $P -u tools/gstudy.py --data runs/gdata_v1.npz --arm $ARM --positions 400000 --passes 8 --seeds 0,1 --device cuda:1 --out runs/plan6/G_arm_$ARM.json
done
echo "G queue 2 DONE ($(date +%H:%M))"
} >> runs/plan6/G_queue.out 2>&1
