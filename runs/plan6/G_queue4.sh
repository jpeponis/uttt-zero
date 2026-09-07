#!/bin/bash
# PLAN6 §4: the ONE read of the sealed test slice, after every arm is in (queue 3). Each arm retrained at 400k x 8,
# seed 0, evaluated on --split test; students saved. Read once; the numbers go into KNOWLEDGE 48 and PLAN6's log.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
until grep -q "G queue 3 DONE" runs/plan6/G_queue.out 2>/dev/null; do sleep 60; done
{
echo "=== SEALED TEST READ ($(date +%H:%M)) -- once"
for ARM in resnet8 resnet10 resnet8_mask resnet8_tied gcnn8x16; do
  $P -u tools/gstudy.py --data runs/gdata_v1.npz --arm $ARM --positions 400000 --passes 8 --seeds 0 --split test --device cuda:1 --save runs/plan6/students_test --out runs/plan6/G_test_$ARM.json
done
echo "G queue 4 DONE ($(date +%H:%M))"
} >> runs/plan6/G_queue.out 2>&1
