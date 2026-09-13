#!/bin/bash
# PLAN7 §5 item 2 (K1's DRAW readings) -- the I1 tool set on the draw net UNDER `draw`, plus items 3 and 4's tools.
# Frozen before runs/deep8_c1_300_e8_draw/net_0300.pt exists (§7e M2-R row R9): the commands, the sampling and the
# estimators below are the pre-registration, not a script written after an outcome was seen.
#
# The template is runs/plan7/K1_parent_count_pass_3060.sh -- the SAME tool set, the same sims, the same position
# counts, the same seeds, the same flags, on runs/deep8_c1_300_e8 under `count`. That pass is the baseline every
# reading here is compared with (rule-invariant / rule-dependent / unresolved). Read the two side by side: a
# difference between them that is not listed below is a bug, not a finding.
#
# Differences from the count pass, all deliberate:
#   * the net is runs/deep8_c1_300_e8_draw/net_0300.pt and `--rule draw` is passed EXPLICITLY to every tool that
#     takes it (the evaluation rule is an argument, never inferred from a checkpoint -- K1's convention);
#   * every output goes to runs/plan7/K1_<tag>.out; the combined log is runs/plan7/K1_readings.out;
#   * new dataset / suite / book names, so nothing of the count pass is overwritten. tools that write through
#     uttt.rules.tag_path add `_draw` to the name they are given, so the names on disk will be:
#         probe dataset  runs/probe_data_deep10late_e8draw.npz  -> runs/probe_data_deep10late_e8draw_draw.npz
#         puzzle suite   suites/puzzles_v5_dev.npz              -> suites/puzzles_v5_dev_draw.npz  (+ _draw.json)
#         book           runs/book_deep8_e8draw.json            -> runs/book_deep8_e8draw_draw.json (+ .md)
#         atlas          runs/plan7/K1_A1_atlas.json            -> runs/plan7/K1_A1_atlas_draw.json
#         principles     runs/plan7/K1_principles_deep8e8draw.json -> ..._draw.json
#         ownership      runs/plan7/K1_E9_ownership.json        -> runs/plan7/K1_E9_ownership_draw.json
#         value_decomp   runs/deep8_c1_300_e8_draw/value_decomp_draw.json
#         probes         runs/deep8_c1_300_e8_draw/probes_draw.json (probe.py fit takes the rule from the dataset)
#     Every downstream --data / --report / --fig below therefore names the TAGGED file, not the one passed to --out;
#   * wherever an endgame set is read it is the draw set, suites/endgame_v2_dev_draw.npz. No reading in THIS script
#     reads one -- the endgame reads are runs/eval_run_k1.sh's, and they are diagnostic, never item 3 (rebuttal R10);
#   * book.py's --paired is the draw-rule paired match runs/eval_run_k1.sh writes
#     (paired_vs_deep8c1_300e8_64_draw.json; book.py refuses a paired file of another rule, M2 row 6) and --compare
#     is the count parent's book runs/book_deep8_e8.json. That comparison is deliberately CROSS-RULE -- it is the
#     count-rule baseline for claims 7 / 7a -- and book.py does not check --compare's rule, only --paired's;
#   * items 3 and 4's tools run at the end, so one command produces the whole pre-registered reading.
#
# THE CORPUS QUESTION -- the choice M3 should judge.
#   The template probes a net on ANOTHER run's games (PLAN5 §8): runs/deep10_c1_300's last 20 files, which are
#   count-rule self-play, and which runs/deep8_c1_300_e8 was never trained on. No draw-play held-out corpus exists
#   and none can before this run, so there are only two options, and this script takes the first:
#     (a) keep the template's corpora and read them under `draw`. The search-based tools (freemove, puzzles,
#         probe build, tablebase_grade, value_decomp, atlas, book) then evaluate the SAME natural positions the
#         count pass read, under the other rule, and decision.py relabels those games' outcomes (count -> draw is
#         exact: a game ends at the same ply either way, so reason 2 becomes reason 3 and the winner becomes 0).
#         Identical inputs are what a rule-invariance comparison wants: any difference from the count pass is the
#         rule and the net, with the position distribution held fixed.
#     (b) read the draw net on its own games. That changes the positions and the rule at once, so a difference
#         would be unattributable.
#   The cost of (a), stated plainly: these are positions a COUNT-rule policy produced. If the draw rule changes
#   which positions arise -- which is item 5's question and quite likely -- then these readings describe the draw
#   net's judgement of count-play positions, not of the positions it actually meets. They are a controlled
#   comparison, not a description of the draw net's own game. The draw net's OWN games are used only where the
#   claim is descriptive and the corpus IS the object -- corpus_stats (claims 24, 25, 27) and principles' draw
#   statistics (claims 26, 33-35) -- exactly as the template does. tools/common_positions.py (item 3) samples from
#   BOTH corpora and reports every number by source corpus as well as pooled, which is the check on this choice.
#
# THE BUFFER, the second choice M3 should judge.
#   surprise.py and probe_value.py take positions from a replay buffer, and both call probe_value.check_buffer_rule,
#   which REFUSES a buffer whose run was trained under another rule (M2 row 9's pattern). The count pass used
#   runs/deep8_c1_300/latest_full.pt -- a count run, so under `--rule draw` that refusal fires. The only draw-rule
#   buffer that will exist is the draw run's OWN, so these two readings -- and only these two -- use it. They are
#   therefore NOT held out: the positions are the net's own recent self-play. The alternative would be to change
#   check_buffer_rule so that a buffer supplies positions while the search runs under an explicitly given rule
#   (the positions are rule-free; only the buffer's stored value / margin / ownership targets are not, and neither
#   tool reads those). That is a tool change, not a reading, and was not made here.
#
# Rule bookkeeping, checked against the code before this script was written: every corpus this script names has a
# config.json or rule-tagged game files, so corpus_stats.corpus_rule establishes each one and no --corpus_rule
# override is needed anywhere (runs/v2a, runs/deep10_c1_300, runs/deep8_c1_300 and runs/deep8_c1_300_e8 all carry a
# config.json with no `rule` key = pre-K1 = count; runs/deep8_c1_300_e8_draw's files carry a `draw` tag and its
# config.json agrees). The count corpora are read under `draw` by relabelling, which is exact in that direction and
# refused in the other; the draw run's own files are read under `draw` directly.
#
# Device: cuda:1, the 3060 (the 3090 is K1's training card). Cost: the count pass took ~5 h on the same card;
# items 3 and 4 add ~30 min (30 000 positions x 4 cells at 256 sims, plus the exact solve on 8 CPU processes).
# Launch: bash runs/plan7/K1_readings_3060.sh
# Dry run (prove every invocation parses, run nothing): DRY=1 bash runs/plan7/K1_readings_3060.sh
# REPO overrides the repository root; it exists only so the dry run can be made from a worktree.
cd "${REPO:-/c/Users/John Peponis/Desktop/uttt-zero}" || { echo "K1_readings: cannot cd to the repository" >&2; exit 2; }
P=.venv/Scripts/python.exe
D=cuda:1
RULE=draw
R=runs/deep8_c1_300_e8_draw                 # the net under test; its own corpus for the descriptive claims only
N=$R/net_0300.pt                            # K1's final checkpoint -- named, never discovered (M2 rebuttal (d))
PARENT=runs/deep8_c1_300_e8/net_0300.pt     # the count-trained parent: same recipe, same strength, the other rule
HOLD=runs/deep10_c1_300                     # held-out games (PLAN5 §8): count-rule play, read here under `draw`
PZ_OUT=runs/probe_data_deep10late_e8draw.npz          # what probe.py build is given ...
PZ=runs/probe_data_deep10late_e8draw_draw.npz         # ... and what tag_path makes of it: every --data below
BOOK_OUT=runs/book_deep8_e8draw.json
BOOK=runs/book_deep8_e8draw_draw.json
ATLAS_OUT=runs/plan7/K1_A1_atlas.json
ATLAS=runs/plan7/K1_A1_atlas_draw.json
PAIRED_C=$R/paired_vs_deep8c1_300e8_64.json           # written by runs/eval_run_k1.sh, item 4's two matches
PAIRED_D=$R/paired_vs_deep8c1_300e8_64_draw.json
O=runs/plan7/K1

if [ "${DRY:-0}" != 1 ]; then
  [ -f $R/DONE ] || { echo "$R/DONE is missing: the readings are of a finished 300-iteration run" >&2; exit 1; }
  [ -f $N ] || { echo "$N is missing: K1's readings are of the final checkpoint, not of the latest one present" >&2; exit 1; }
fi

run() {  # run <out> <header> <cmd...>: header and exit code into the combined log, the tool's output into <out>
  local out=$1 hdr=$2; shift 2
  if [ "${DRY:-0}" = 1 ]; then
    echo "DRY $hdr"
    echo "    $*"
    case " $* " in
      *book_stats.py*) echo "    (tools/book_stats.py takes no options: it reads book paths from argv)";;
      *) "$@" --help > /dev/null 2>&1; echo "    argparse exit $?";;
    esac
    return
  fi
  echo "=== $hdr ($(date +%H:%M))"
  "$@" > "$out" 2>&1
  echo "    -> $out ($?)"
}
{
echo "K1 draw-rule readings on $N (rule $RULE) started $(date)"

# claims 24, 25, 27 -- X/O/draw shares, the end reasons under a rule with no count ending, game length and free
# moves per game. This net's OWN games: the corpus is the object of these claims. Claim 24's draw share is read
# against the mechanical relabel baseline of 32.3 % with a 2-point margin (§5 items 0 and 2), not against 16.6 %.
run ${O}_A6_corpus_stats.out "corpus_stats (claims 24, 25, 27)" \
  $P tools/corpus_stats.py $R --last 20 --rule $RULE

# claim 32 -- what the raw policy still gets wrong late. A new suite name; suites/ is frozen.
run ${O}_A7_puzzles.out "puzzles (claim 32)" \
  $P tools/puzzles.py $N --corpus $HOLD --last 20 --max_empty 14 --n 6000 --processes 12 --device $D --rule $RULE --out suites/puzzles_v5_dev.npz

# claim 23 -- where intuition and search part company. The draw run's OWN buffer: see THE BUFFER above.
run ${O}_B4_surprise.out "surprise (claim 23)" \
  $P tools/surprise.py $N --buffer $R/latest_full.pt --sims 256 --n 8192 --top 30 --device $D --rule $RULE

# claims 12, 15, 18, 35 -- the value head probed on buffer positions. Same buffer, same reason.
run ${O}_B4b_probe_value.out "probe_value (claims 12, 15, 18, 35)" \
  $P tools/probe_value.py $N --buffer $R/latest_full.pt --device $D --rule $RULE

# claims 8, 10, 11, 13, 14 -- the free move, macro-line threats, board ownership; the prespecified regression.
# The count pass's corpus, read under `draw`: identical positions, the other rule. The PAIRED form of claims 8
# and 13 -- the one §5 item 2 gives a verdict rule for -- is tools/common_positions.py's, below.
run ${O}_A4_freemove.out "freemove (claims 8, 10, 11, 13, 14)" \
  $P tools/freemove.py $N --corpus $HOLD --last 20 --sims 256 --device $D --rule $RULE

# claims 20-22 -- when games are decided. Both corpora the earlier passes ran; their outcomes are relabelled
# count -> draw, which is exact (corpus_stats.relabel).
run ${O}_A3a_decision_on_v2a.out "decision on v2a (claims 20-22)" \
  $P tools/decision.py $N --corpus runs/v2a --last 2 --games 4000 --sims 64 --device $D --rule $RULE
run ${O}_A3b_decision_on_deep10late.out "decision on deep10 late games (claims 20-22)" \
  $P tools/decision.py $N --corpus $HOLD --last 20 --games 4000 --sims 64 --device $D --rule $RULE

# claims 1-5 -- the opening atlas. Claim 1's test is [40] ranked first at all three budgets by search value, a gap
# <= 0.01 to the runner-up counting as a tie (§5 item 2); the taus against the count reading are computed at read
# time from this JSON and runs/plan7/K1_parent_A1_atlas.json.
run ${O}_A1_atlas.out "atlas (claims 1-5)" \
  $P tools/atlas.py --nets $N --budgets 1024,4096,16384 --device $D --rule $RULE --out $ATLAS_OUT
run ${O}_A1_atlas_orbits.out "atlas --report, reply-orbit gaps (claims 4, 5)" \
  $P tools/atlas.py --report $ATLAS --rule $RULE

# The probe dataset: held-out positions with concept labels, this net's 256-sim look-ahead labels and draw-rule
# exact labels. Everything below that takes --data takes the TAGGED name $PZ.
run ${O}_B2_probe_build.out "probe.py build (dataset for principles / tablebase_grade / value_decomp / probes)" \
  $P tools/probe.py build --corpus $HOLD --last 20 --net $N --out $PZ_OUT --device $D --rule $RULE

# claims 26, 33-35 -- the folk claims and what drawn games look like under a rule where 5-3 is a draw. The draw
# statistics are of this net's OWN games (a seeded uniform sample over the window, X and O separately; M2 row 8).
run ${O}_C2_principles.out "principles (claims 26, 33-35)" \
  $P tools/principles.py --data $PZ --corpus $R --last 20 --rule $RULE --out ${O}_principles_deep8e8draw.json

# claim 31a -- the last-board phase against the exact one-open-board tablebase, whose outcome map is rule-dependent.
run ${O}_C5_tablebase_grade.out "tablebase_grade (claim 31a)" \
  $P tools/tablebase_grade.py $N --data $PZ --sims 64 --device $D --rule $RULE

# claims 9, 14-19 -- the value decomposition per checkpoint. Claim 16's PRIMARY form is the paired difference in
# tools/common_positions.py below; this is the per-checkpoint trajectory and the secondary interval.
run ${O}_B3_value_decomp.out "value_decomp (claims 9, 14-19)" \
  $P tools/value_decomp.py $R --data $PZ --n 20000 --sims 256 --device $D --rule $RULE

# claims 7, 7a -- the opening book and the self-send reply rule. Claim 7's reply after [40] is read as an aggregated
# reply-orbit VISIT share at 16 384 sims with a 0.02 tie tolerance, visits and Q both saved (M2 row 12).
run ${O}_C1_book.out "book (claims 7, 7a)" \
  $P tools/book.py --net $N --depth 4 --top 3 --sims 16384 --batch 64 --paired $PAIRED_D --compare runs/book_deep8_e8.json --device $D --rule $RULE --out $BOOK_OUT
run ${O}_C1_book_stats.out "book_stats (claim 7a)" \
  $P tools/book_stats.py $BOOK runs/book_deep8_e8.json runs/book_deep8_e4.json runs/book_deep10.json runs/book_deep8.json

# claims 36-40 -- what the trunk computes, where and when; and the ownership head graded on open boards only. Last,
# because the fit is the expensive one: 16 checkpoints, the grid every earlier fit used. probe.py fit runs no search
# and decides no terminal value, so it takes its rule from the dataset and writes $R/probes_draw.json.
run ${O}_B2_probe_fit.out "probe.py fit --control, 16 checkpoints (claims 36-39)" \
  $P tools/probe.py fit --data $PZ --run $R --control --only 10,20,40,60,80,100,120,140,160,180,200,220,240,260,280,300 --device $D
run ${O}_B2_probe_report.out "probe_report (claims 36-39)" \
  $P tools/probe_report.py $R/probes_draw.json --fig $R/probes_draw.png
run ${O}_E9_ownership_grade.out "ownership_grade --control (claim 40)" \
  $P tools/ownership_grade.py --data $PZ --net $N --control --device $D --rule $RULE --out ${O}_E9_ownership.json

# ---- item 3, and the paired half of item 2: one frozen position set, both nets under both rules.
# 15 000 positions from each of the two nets' own corpora (M2 rebuttal R1's size), every number reported by source
# corpus as well as pooled (M2 row 17). This is where claims 8, 13 and 16 get the verdicts §5 item 2 pre-registers;
# the freemove and value_decomp readings above are the unpaired, per-cell view of the same positions' cousins.
# KNOWN BEFORE THE RUN, from the tool's smoke on two COUNT-trained nets (deep8_c1_300_e8 and _e4, 2 000 positions
# per corpus, 64 sims): each count-trained net's own paired count-margin Delta is -0.0196, 95 % [-0.0271, -0.0122].
# The rule change ALONE moves that coefficient -- under `draw` a count-decided terminal backs up 0 instead of +-1,
# so every position with a positive count margin is pulled towards zero -- and a count-trained control therefore
# already satisfies §5 item 2's registered "established decrease" (upper endpoint <= -0.005) by a factor of four.
# The registered verdict is printed unchanged; the count parent runs as net B in the same call, so its Delta is the
# control beside the draw net's, and the tool also prints the difference in differences (labelled NOT registered).
# This is the same defect M2 row 2 found in the previous formulation of claim 16, in the other direction, and it is
# for M3 / the owner to decide before the readings are written up -- not for this script to decide by itself.
run ${O}_D1_common_positions.out "common_positions (§5 item 3; claims 8, 13, 16 paired)" \
  $P tools/common_positions.py --corpus_a $R --corpus_b runs/deep8_c1_300_e8 --net_a $N --net_b $PARENT \
     --n 15000 --sims 256 --processes 8 --device $D --out ${O}_D1_common_positions.json

# ---- item 4: the cross-play contrast, from the two matches runs/eval_run_k1.sh plays. Skipped with a message if
# that chain has not run: this script must not silently produce a partial reading.
if [ "${DRY:-0}" = 1 ] || { [ -f $PAIRED_C ] && [ -f $PAIRED_D ]; }; then
run ${O}_D2_paired_contrast.out "paired_contrast (§5 item 4: 1 - s_D - s_C, joint pair bootstrap)" \
  $P tools/paired_contrast.py --count $PAIRED_C --draw $PAIRED_D --boot 2000 --seed 0 --out ${O}_D2_paired_contrast.json
else
echo "=== paired_contrast SKIPPED: $PAIRED_C and/or $PAIRED_D is missing -- run bash runs/eval_run_k1.sh deep8_c1_300_e8_draw first"
fi

echo "K1 DRAW READINGS DONE ($(date +%H:%M))"
} >> runs/plan7/K1_readings.out 2>&1
