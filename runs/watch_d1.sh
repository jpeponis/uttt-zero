#!/bin/bash
# Event stream for the D1 seed replicate (PLAN5 §5 D1), for a session Monitor: one line per event.
# Emits: every in-run eval row (tools/run_status.py: progress, ETA, scores vs anchors, ref-run comparison),
# every crash/restart of the retry wrapper, FAILED after 6 attempts, a stall (no new iteration in 45 min),
# the 3090 at >= 92C (max operating 93, slowdown 95), training DONE, and the final analysis.out (then exits).
cd "/c/Users/John Peponis/Desktop/uttt-zero"
R=${1:-deep10_c1_300_s1}; P=.venv/Scripts/python.exe
LOG=runs/$R/log.jsonl; OUT=runs/$R.out; Q=runs/queue7.out
status() { $P tools/run_status.py runs/$R 2>&1; }
count() { grep -c "$1" "$2" 2>/dev/null || echo 0; }
evals=$(count '"vs_' $LOG); died=$(count 'attempt .* died' $OUT); stalled=0; hot=0; donesaid=0
while true; do
  sleep 60
  e=$(count '"vs_' $LOG)
  if [ "$e" != "$evals" ]; then evals=$e; status; fi
  d=$(count 'attempt .* died' $OUT)
  if [ "$d" != "$died" ]; then
    died=$d; echo "RESTART: $(grep 'attempt .* died' $OUT | tail -1)"
    grep -v '^{"iter"' $OUT | grep -B6 'attempt .* died' | tail -7 | cut -c1-300
  fi
  if grep -q 'FAILED after' $OUT; then echo "FAILED: $(grep 'FAILED after' $OUT)"; status; exit 1; fi
  if [ ! -f runs/$R/DONE ]; then
    age=$(( $(date +%s) - $(stat -c %Y $LOG 2>/dev/null || date +%s) ))
    if [ $age -gt 2700 ] && [ $stalled = 0 ]; then stalled=1; echo "STALL? no new iteration for $((age/60)) min"; status; tail -3 $OUT | cut -c1-300; fi
    [ $age -le 2700 ] && stalled=0
  elif [ $donesaid = 0 ]; then
    donesaid=1; echo "TRAINING DONE at $(date '+%F %T'); eval_run.sh running on cuda:0 (~10 min)"; status
  fi
  t=$(nvidia-smi --query-gpu=name,temperature.gpu --format=csv,noheader 2>/dev/null | grep 3090 | awk -F', ' '{print $2}')
  if [ -n "$t" ] && [ "$t" -ge 92 ] && [ $hot = 0 ]; then hot=1; echo "HOT: 3090 at ${t}C (max operating 93C, slowdown 95C)"; fi
  [ -n "$t" ] && [ "$t" -lt 88 ] && hot=0
  if grep -q 'queue7 done' $Q 2>/dev/null; then
    echo "QUEUE7 DONE: $(tail -1 $Q)"; status
    echo "--- runs/$R/analysis.out: final checkpoint on the paired suite (all rows) and the endgame set"
    grep -E '^paired suite|^  all |^=== endgame' -A0 runs/$R/analysis.out | sed 's/paired suite openings_v1 (516 openings, 1032 games): //' | cut -c1-160
    sed -n '/=== endgame set/,$p' runs/$R/analysis.out | grep -E '^evaluator|^raw net (value|^search' | cut -c1-200
    exit 0
  fi
done
