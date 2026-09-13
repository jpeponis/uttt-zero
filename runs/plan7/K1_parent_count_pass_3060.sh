#!/bin/bash
# PLAN7 §5 item 1 (K1's count-rule parent, re-read) and J1's cheap re-read. Why: K1's parent is deep8_c1_300_e8, but the
# count-rule game claims in KNOWLEDGE were last read on deep8_c1_300_e4 (the I1 second pass, runs/plan6/I1_*.out); comparing
# a draw-trained _e8 against a count-trained _e4 would mix the rule with +40 Elo of strength (M0 row 11). So the I1 tool
# set runs on deep8_c1_300_e8 UNDER `count`, at the I1 pass's settings exactly (runs/plan6/I1_second_pass_3060.sh is the
# template and holds the rationale for every setting; the deep10 pass before it is runs/plan5_A.out / plan5_B.out), so the
# reading is like for like: same sims, same position counts, same seeds, same flags, the same held-out corpora.
# Differences from the I1 template, all deliberate:
#   * the net is _e8; every output goes to runs/plan7/K1_parent_<tag>.out (the combined log is runs/plan7/K1_parent_pass.out);
#   * `--rule count` is passed EXPLICITLY to every tool that takes it (K1's convention: the evaluation rule is an argument,
#     never inferred; the tools that do not take it -- surprise, decision, probe fit, probe_report, book_stats,
#     ownership_grade, probe_value -- are count by construction and are the five PLAN7 §5 says to thread before the
#     DRAW readings, not before this one);
#   * puzzles writes the NEW name suites/puzzles_v4_dev.npz (v3_dev is _e4's; suites/ is frozen, nothing is rewritten);
#   * the probe dataset is the new name runs/probe_data_deep10late_e8.npz (deep10's late games labelled by THIS net);
#   * book.py's --paired is _e8's primary match against its parent (paired_vs_deep8c1_300e4_64.json), --compare is the
#     parent's book (runs/book_deep8_e4.json), out runs/book_deep8_e8.json; book_stats prints all four books;
#   * ADDED: tools/probe_value.py on _e8 (claims 12, 15, 18 and 35's counterfactual half -- J1's cheap re-read, PLAN7 §4 J1),
#     at the deep10 pass's invocation (runs/plan5_B4.sh: --buffer runs/deep8_c1_300/latest_full.pt, another run's buffer).
# Held-out corpora (PLAN5 §8): runs/deep10_c1_300 iterations 280-299 (_e8 never trained on them; they are already its
# timeline corpus, runs/plan6/H1c_timeline.out); runs/v2a's last 2 files (decision's reference column); the
# deep8_c1_300 buffer (surprise, probe_value); _e8's OWN games only for corpus_stats and principles' draw statistics.
# Device: cuda:1, the 3060, uncontested (nothing on either card; the reviews running beside this are CPU-only reads).
# Cost: the _e4 pass took 4 h 56 min with the E7 worker sharing the card; expect less here.
# Pre-registered reading: HELD / MOVED / REVERSED per claim against the _e4 reading, as I1 read against deep10; the
# outputs are ALSO the count-rule baseline every K1 draw reading is compared with (rule-invariant / rule-dependent /
# unresolved, PLAN7 §5 item 2).
# Launch: bash runs/plan7/K1_parent_count_pass_3060.sh
cd "/c/Users/John Peponis/Desktop/uttt-zero"
P=.venv/Scripts/python.exe
D=cuda:1
RULE=count
R=runs/deep8_c1_300_e8                      # the net under test (K1's parent); its own corpus for the descriptive claims
N=$R/net_0300.pt                            # +363 vs v2b, +40 over _e4; the play agent
HOLD=runs/deep10_c1_300                     # held-out games (PLAN5 §8), this net's timeline corpus already
PZ=runs/probe_data_deep10late_e8.npz        # probe dataset: HOLD's late games labelled by THIS net (a new name)
O=runs/plan7/K1_parent
run() {  # run <out> <header> <cmd...>: header and exit code into the combined log, the tool's output into <out>
  local out=$1 hdr=$2; shift 2
  echo "=== $hdr ($(date +%H:%M))"
  "$@" > "$out" 2>&1
  echo "    -> $out ($?)"
}
{
echo "K1 parent count-rule pass on $N (rule $RULE) started $(date)"

# claims 24, 25, 27 -- X/O/draw shares, the count rule, game length and free moves per game. This net's OWN games.
run ${O}_A6_corpus_stats.out "corpus_stats (claims 24, 25, 27)" \
  $P tools/corpus_stats.py $R --last 20 --rule $RULE

# claim 32 -- what the raw policy still gets wrong late. A new suite name; suites/ is frozen.
run ${O}_A7_puzzles.out "puzzles (claim 32)" \
  $P tools/puzzles.py $N --corpus $HOLD --last 20 --max_empty 14 --n 6000 --processes 12 --device $D --rule $RULE --out suites/puzzles_v4_dev.npz

# claim 23 -- where intuition and search part company. The same buffer the deep10 and _e4 passes used.
run ${O}_B4_surprise.out "surprise (claim 23)" \
  $P tools/surprise.py $N --buffer runs/deep8_c1_300/latest_full.pt --sims 256 --n 8192 --top 30 --device $D

# claims 12, 15, 18, 35 -- the value head probed on held-out positions (J1's cheap re-read; plan5 B4's invocation).
run ${O}_B4b_probe_value.out "probe_value (claims 12, 15, 18, 35)" \
  $P tools/probe_value.py $N --buffer runs/deep8_c1_300/latest_full.pt --device $D

# claims 8, 10, 11, 13, 14 -- the free move, macro-line threats, board ownership; the prespecified regression.
run ${O}_A4_freemove.out "freemove (claims 8, 10, 11, 13, 14)" \
  $P tools/freemove.py $N --corpus $HOLD --last 20 --sims 256 --device $D --rule $RULE

# claims 20-22 -- when games are decided. Both corpora the earlier passes ran.
run ${O}_A3a_decision_on_v2a.out "decision on v2a (claims 20-22)" \
  $P tools/decision.py $N --corpus runs/v2a --last 2 --games 4000 --sims 64 --device $D
run ${O}_A3b_decision_on_deep10late.out "decision on deep10 late games (claims 20-22)" \
  $P tools/decision.py $N --corpus $HOLD --last 20 --games 4000 --sims 64 --device $D

# claims 1-5 -- the opening atlas. One net; the taus against the earlier nets are computed at read time from this JSON
# and runs/plan5_A1_atlas.json / runs/plan6/I1_A1_atlas.json.
run ${O}_A1_atlas.out "atlas (claims 1-5)" \
  $P tools/atlas.py --nets $N --budgets 1024,4096,16384 --device $D --rule $RULE --out ${O}_A1_atlas.json
run ${O}_A1_atlas_orbits.out "atlas --report, reply-orbit gaps (claims 4, 5)" \
  $P tools/atlas.py --report ${O}_A1_atlas.json --rule $RULE

# The probe dataset: held-out positions with concept labels and this net's 256-sim look-ahead labels.
run ${O}_B2_probe_build.out "probe.py build (dataset for principles / tablebase_grade / value_decomp / probes)" \
  $P tools/probe.py build --corpus $HOLD --last 20 --net $N --out $PZ --device $D --rule $RULE

# claims 26, 33-35 -- the folk claims and what drawn games look like. CPU.
run ${O}_C2_principles.out "principles (claims 26, 33-35)" \
  $P tools/principles.py --data $PZ --corpus $R --last 20 --rule $RULE --out ${O}_principles_deep8e8.json

# claim 31a -- the last-board phase against the exact one-open-board tablebase (PLAN5 §4 C5's description, tool defaults).
run ${O}_C5_tablebase_grade.out "tablebase_grade (claim 31a)" \
  $P tools/tablebase_grade.py $N --data $PZ --sims 64 --device $D --rule $RULE

# claims 9, 14-19 -- the value decomposition per checkpoint. Every checkpoint, as the earlier passes ran it.
run ${O}_B3_value_decomp.out "value_decomp (claims 9, 14-19)" \
  $P tools/value_decomp.py $R --data $PZ --n 20000 --sims 256 --device $D --rule $RULE

# claims 7, 7a -- the opening book and the self-send reply rule. --paired: this net's primary match against its parent;
# --compare: the parent's book. book_stats prints all four books.
run ${O}_C1_book.out "book (claims 7, 7a)" \
  $P tools/book.py --net $N --depth 4 --top 3 --sims 16384 --batch 64 --paired $R/paired_vs_deep8c1_300e4_64.json --compare runs/book_deep8_e4.json --device $D --rule $RULE --out runs/book_deep8_e8.json
run ${O}_C1_book_stats.out "book_stats (claim 7a)" \
  $P tools/book_stats.py runs/book_deep8_e8.json runs/book_deep8_e4.json runs/book_deep10.json runs/book_deep8.json

# claims 36-40 -- what the trunk computes, where and when; and the ownership head graded on open boards only. Last,
# because the fit is the expensive one: 16 checkpoints (the grid every earlier fit used), ~2-2.5 h here.
run ${O}_B2_probe_fit.out "probe.py fit --control, 16 checkpoints (claims 36-39)" \
  $P tools/probe.py fit --data $PZ --run $R --control --only 10,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300 --device $D
run ${O}_B2_probe_report.out "probe_report (claims 36-39)" \
  $P tools/probe_report.py $R/probes.json --fig $R/probes.png
run ${O}_E9_ownership_grade.out "ownership_grade --control (claim 40)" \
  $P tools/ownership_grade.py --data $PZ --net $N --control --device $D --out ${O}_E9_ownership.json

echo "K1 PARENT PASS DONE ($(date +%H:%M))"
} >> runs/plan7/K1_parent_pass.out 2>&1
