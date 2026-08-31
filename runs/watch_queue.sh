#!/bin/bash
# Evaluate each queued run on the 3060 as soon as its final checkpoint appears.
cd "/c/Users/John Peponis/Desktop/uttt-zero"
for R in wide96 abl_cscale1 abl_noheads; do
  while [ ! -f runs/$R/net_0150.pt ]; do sleep 120; done
  sleep 30
  bash runs/eval_run.sh $R cuda:1
  echo "evaluated $R at $(date)"
done
