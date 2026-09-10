#!/bin/bash
# PLAN6 §9c, I1: the analysis SECOND PASS, on the strongest net. Why: the project's central methodological claim is
# PLAN5 §1c's -- orderings and signs are stable across strength, magnitudes drift and saturate -- and it has been
# tested once, in Phase A at +242 Elo. The strongest net is now runs/deep8_c1_300_e4/net_0300.pt at +363, 120 Elo
# above the net every §1-§8 claim in KNOWLEDGE.md is quoted from, and KNOWLEDGE's header says in as many words that
# those claims have not been re-run on it. This closes that gap, and it is the last thing the project owes its own
# method. Every net-dependent Phase A/B/C tool below runs at THE SAME SETTINGS the deep10 pass used (runs/plan5_A.out
# and runs/plan5_B.out are the record of the invocations; runs/plan5_A_3060.sh, plan5_A_3090.sh, plan5_B.sh,
# plan5_B4.sh and plan5_C1.sh of the scripts), so the comparison is like for like: same sims, same position counts,
# same seeds, same flags.
#
# Held-out corpora (PLAN5 §8: a net is probed on ANOTHER run's games, never its own):
#   runs/deep10_c1_300, iterations 280-299  -- puzzles, freemove, decision's strong-play column, the probe dataset.
#     deep8_c1_300_e4 never trained on them, and they are already this net's timeline corpus
#     (runs/plan6/H1b_timeline.out), so nothing about the held-out convention changes for it.
#   runs/v2a, last 2 files -- decision's second column, exactly as the deep10 pass ran it (the corpus every net's
#     "settled by ply" number in claim 20 is quoted on).
#   runs/deep8_c1_300/latest_full.pt -- surprise's buffer, as §9c's table specifies: another run's buffer, held out
#     for _e4, and the same buffer the deep10 pass used, so claim 23's numbers are on identical positions.
#   runs/deep8_c1_300_e4 itself -- corpus_stats, and principles' draw statistics only, which are descriptive of THIS
#     net's own games (claims 24-27) and must come from its own corpus, as they did for deep10.
# Devices: everything on cuda:1, the 3060, because H1c holds the 3090 (§8: the trainer never shares it). book.py
# defaults to cuda:0 and is passed --device cuda:1 explicitly; corpus_stats.py and principles.py take no device and
# are CPU work. The E7 worker of H1c shares the card throughout (~6 min per checkpoint every ~43 min, so the card is
# about a seventh busy) -- expected, and the reason every wall-clock below will read longer than the deep10 pass's.
# Order: cheapest first, probes last. Rough cost, scaled from the deep10 pass: corpus_stats 40 s, puzzles 1 min,
# surprise 1 min, freemove 5 min, decision 2 x 7-9 min, atlas ~17 min, probe build 5 min, principles minutes,
# tablebase_grade minutes, value_decomp ~60 min (30 checkpoints), book ~38 min, probe fit ~2-2.5 h, ownership_grade
# ~1 min: ~5 h in all.
#
# Pre-registered reading, per claim (§9c), exactly three verdicts: HELD (the sign and the ordering agree with the
# deep10 reading AND the new magnitude is inside the earlier CI -- the claim's "held across" list gains "all four
# strong nets"); MOVED (sign and ordering agree, magnitude outside the earlier CI -- report it, update the "grew
# with strength" clause with the third point, and re-read PLAN5 §2's "the magnitudes saturated between deep8_300 and
# deep10" against it); REVERSED (a sign or an ordering disagrees -- restate the claim as budget- or strength-
# relative and say at which strength it flipped; this is the outcome the method says cannot happen, and if it does
# it is the most important line in the file).
#
# What is NOT here, and why: the endgame reads (claims 28-31) are already done for this net, in
# runs/deep8_c1_300_e4/analysis.out (endgame_v1 90.1 / 0.022, endgame_v2_dev 90.5 / 0.029); suites/ stays frozen, so
# puzzles writes the NEW name suites/puzzles_v3_dev.npz and never rewrites puzzles_v2_dev.npz; and §9c's table does
# not list tools/probe_value.py (claims 12, 15, 18), tools/timeline.py (6, 31, 41 -- already run for this net) or the
# --hidden 256 MLP probe (38a, a deep10-only claim), so they are not run here.
# Two settings could NOT be reconstructed from a recorded log and are reasoned from the plan instead (each flagged
# again at its tool below): tablebase_grade.py has no .out on file from the deep10 pass, so its invocation is taken
# from PLAN5 §4 C5's description (the 701 one-open-board positions among the 60 000 held-out B2 positions, i.e. the
# probe dataset) plus the tool's defaults --sims 64 / --device cuda:1; and book.py's --paired file for deep10 was its
# own self-match (paired_phased_vs_256.json), which deep8_c1_300_e4 does not have, so its primary paired match
# against the parent is used instead (the deep8 book used a cross-net match file the same way).
# Launch (3060, beside H1c on the 3090): bash runs/plan6/I1_second_pass_3060.sh  (or via runs/plan6/closing_3060.sh)
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
D=cuda:1
R=runs/deep8_c1_300_e4                      # the net under test; its own corpus for the descriptive claims
N=$R/net_0300.pt                            # +363 vs v2b; the play agent
HOLD=runs/deep10_c1_300                     # held-out games (PLAN5 §8), this net's timeline corpus already
PZ=runs/probe_data_deep10late_e4.npz        # probe dataset: HOLD's late games labelled by THIS net (a new name --
                                            # runs/probe_data_deep10late.npz is the same games labelled by deep8_c1_300)
run() {  # run <out> <header> <cmd...>: header and exit code into the combined log, the tool's output into <out>
  local out=$1 hdr=$2; shift 2
  echo "=== $hdr ($(date +%H:%M))"
  "$@" > "$out" 2>&1
  echo "    -> $out ($?)"
}
{
echo "I1 second pass on $N started $(date)"

# claims 24, 25, 27 -- X/O/draw shares, the count rule, game length and free moves per game. This net's OWN games.
run runs/plan6/I1_A6_corpus_stats.out "corpus_stats (claims 24, 25, 27)" \
  $P tools/corpus_stats.py $R --last 20

# claim 32 -- what the raw policy still gets wrong late. A new suite name; suites/ is frozen.
run runs/plan6/I1_A7_puzzles.out "puzzles (claim 32)" \
  $P tools/puzzles.py $N --corpus $HOLD --last 20 --max_empty 14 --n 6000 --processes 12 --device $D --out suites/puzzles_v3_dev.npz

# claim 23 -- where intuition and search part company. The same buffer the deep10 pass used.
run runs/plan6/I1_B4_surprise.out "surprise (claim 23)" \
  $P tools/surprise.py $N --buffer runs/deep8_c1_300/latest_full.pt --sims 256 --n 8192 --top 30 --device $D

# claims 8, 10, 11, 13, 14 -- the free move, macro-line threats, board ownership; the prespecified regression.
run runs/plan6/I1_A4_freemove.out "freemove (claims 8, 10, 11, 13, 14)" \
  $P tools/freemove.py $N --corpus $HOLD --last 20 --sims 256 --device $D

# claims 20-22 -- when games are decided. Both corpora the deep10 pass ran: v2a (the reference column every net's
# number is quoted on) and the strong-play late games.
run runs/plan6/I1_A3a_decision_on_v2a.out "decision on v2a (claims 20-22)" \
  $P tools/decision.py $N --corpus runs/v2a --last 2 --games 4000 --sims 64 --device $D
run runs/plan6/I1_A3b_decision_on_deep10late.out "decision on deep10 late games (claims 20-22)" \
  $P tools/decision.py $N --corpus $HOLD --last 20 --games 4000 --sims 64 --device $D

# claims 1-5 -- the opening atlas. One net (§9c): the Kendall taus against v2b / deep8_300 / deep10 are computed at
# read time from this JSON and the saved runs/plan5_A1_atlas.json, which holds those three columns already.
run runs/plan6/I1_A1_atlas.out "atlas (claims 1-5)" \
  $P tools/atlas.py --nets $N --budgets 1024,4096,16384 --device $D --out runs/plan6/I1_A1_atlas.json
run runs/plan6/I1_A1_atlas_orbits.out "atlas --report, reply-orbit gaps (claims 4, 5)" \
  $P tools/atlas.py --report runs/plan6/I1_A1_atlas.json

# The probe dataset: held-out positions with concept labels and this net's 256-sim look-ahead labels. It is the
# probes' first step, and also the input of principles, tablebase_grade and value_decomp, so it runs here.
run runs/plan6/I1_B2_probe_build.out "probe.py build (dataset for principles / tablebase_grade / value_decomp / probes)" \
  $P tools/probe.py build --corpus $HOLD --last 20 --net $N --out $PZ --device $D

# claims 26, 33-35 -- the folk claims and what drawn games look like. CPU. --corpus is this net's own games (the
# draw statistics are descriptive of them); --data the held-out probe dataset (the sending rule).
run runs/plan6/I1_C2_principles.out "principles (claims 26, 33-35)" \
  $P tools/principles.py --data $PZ --corpus $R --last 20 --out runs/plan6/I1_principles_deep8e4.json

# claim 31a -- the last-board phase against the exact one-open-board tablebase. NOT reconstructible from a log: the
# deep10 pass left no .out for this tool, so the settings are PLAN5 §4 C5's description (the one-open-board
# positions among the 60 000 held-out B2 positions, i.e. the probe dataset) at the tool's defaults.
run runs/plan6/I1_C5_tablebase_grade.out "tablebase_grade (claim 31a)" \
  $P tools/tablebase_grade.py $N --data $PZ --sims 64 --device $D

# claims 9, 14-19 -- the value decomposition per checkpoint: which concepts the value weighs, when the weights
# appear over training, where the search still corrects the head. Every checkpoint, as the deep10 pass ran it.
run runs/plan6/I1_B3_value_decomp.out "value_decomp (claims 9, 14-19)" \
  $P tools/value_decomp.py $R --data $PZ --n 20000 --sims 256 --device $D

# claims 7, 7a -- the opening book and the self-send reply rule. --paired: deep10's book used its own self-match,
# which this net does not have, so its primary paired match against the parent is used (the deep8 book used a
# cross-net match file the same way); --compare deep8's book, as §9c specifies. book_stats prints all three books.
run runs/plan6/I1_C1_book.out "book (claims 7, 7a)" \
  $P tools/book.py --net $N --depth 4 --top 3 --sims 16384 --batch 64 --paired $R/paired_vs_deep8c1_300e2_64.json --compare runs/book_deep8.json --device $D --out runs/book_deep8_e4.json
run runs/plan6/I1_C1_book_stats.out "book_stats (claim 7a)" \
  $P tools/book_stats.py runs/book_deep8_e4.json runs/book_deep10.json runs/book_deep8.json

# claims 36-40 -- what the trunk computes, where and when; and the ownership head graded on open boards only.
# Last, because the fit is the expensive one: 16 checkpoints (§9c's grid, the one the deep8_c1_300 fit used),
# 55-61 min on the 3090 -> ~2-2.5 h here.
run runs/plan6/I1_B2_probe_fit.out "probe.py fit --control, 16 checkpoints (claims 36-39)" \
  $P tools/probe.py fit --data $PZ --run $R --control --only 10,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300 --device $D
run runs/plan6/I1_B2_probe_report.out "probe_report (claims 36-39)" \
  $P tools/probe_report.py $R/probes.json --fig $R/probes.png
run runs/plan6/I1_E9_ownership_grade.out "ownership_grade --control (claim 40)" \
  $P tools/ownership_grade.py --data $PZ --net $N --control --device $D --out runs/plan6/I1_E9_ownership.json

echo "I1 DONE ($(date +%H:%M))"
} >> runs/plan6/I1_second_pass.out 2>&1
