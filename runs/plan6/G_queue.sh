#!/bin/bash
# PLAN6 §4: G0 (passes vs data, plain 8x128) and arms (a) resnet10, (b) resnet8, (c) resnet8 + closed-board mask,
# two seeds each at 400k positions x 8 passes, on the 3060 (shared with H1's E7 worker). Dev slice only; the test
# slice stays sealed. Arms (d) tied heads and (e) D4 G-CNN are not implemented yet (tools/gstudy.py ARMS).
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
{
echo "=== G0 ($(date +%H:%M))"
$P -u tools/gstudy.py --data runs/gdata_v1.npz --arm resnet8 --positions 50000,100000,200000,400000 --passes 1,2,4,8 --seeds 0 --device cuda:1 --out runs/plan6/G0_resnet8.json
for ARM in resnet8 resnet10 resnet8_mask; do
  echo "=== arm $ARM ($(date +%H:%M))"
  $P -u tools/gstudy.py --data runs/gdata_v1.npz --arm $ARM --positions 400000 --passes 8 --seeds 0,1 --device cuda:1 --out runs/plan6/G_arm_$ARM.json
done
echo "G queue DONE ($(date +%H:%M))"
} > runs/plan6/G_queue.out 2>&1
