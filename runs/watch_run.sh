#!/bin/bash
# bash runs/watch_run.sh <run> [device]: wait for the run to FINISH (train2 writes runs/<run>/DONE),
# then run the standard evaluation chain. Waiting on a checkpoint name broke for non-150-iteration runs.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
R=$1; D=${2:-cuda:1}
while [ ! -f runs/$R/DONE ]; do sleep 120; done
sleep 30
bash runs/eval_run.sh $R $D
echo "evaluated $R at $(date)"
