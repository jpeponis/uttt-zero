# J3 / J4 — implementation notes after M2 (written 2026-09-12 by the implementing agent; verbatim)

*M2's adjudicated rows for the two analysis tools (PLAN7 §7e M2 rows 3, 4, 7, 15, 16 and the J3 / J4 half
of row 9, plus row 18's bounded-solver tests) were implemented by an Opus `directed` agent in an isolated
worktree, against the amended §4 J3 / J4, `REVIEW.md` findings 3, 4, 7 and answers 3, 4, and the
implementer's own `J3J4_design_notes.md`. Neither J3 nor J4 has been run for real: what follows is the
agent's own note on what changed and where, every choice the adjudication left open with its reasoning,
the tests and smoke runs verbatim, and what was deliberately not done. `uttt/solver.py` and the files
belonging to the concurrent K1 worktree were not touched.*

## 1. Files changed

- `C:/Users/John Peponis/Desktop/uttt-zero/.claude/worktrees/agent-a1289da40ea51e45b/tools/empty_board.py` (J3)
- `C:/Users/John Peponis/Desktop/uttt-zero/.claude/worktrees/agent-a1289da40ea51e45b/tools/frontier.py` (J4)
- `C:/Users/John Peponis/Desktop/uttt-zero/.claude/worktrees/agent-a1289da40ea51e45b/tests/test_solver_bounded.py` (row 18's J4 half)

492 insertions, 129 deletions, one commit, not pushed. No new test file was needed — the bounded-solver properties belong beside the three that exist. Nothing outside these three files was touched; every run output went to the session scratchpad, nothing was written into the main checkout.

**One thing the parent must know before merging:** this worktree was created from `40b7864`, one commit *before* the M2 adjudication `09c687c`. `git diff 40b7864 09c687c` touches only `PLAN7.md`, `KNOWLEDGE.md`, `README.md`, `RETROSPECTIVE.md`, `docs/**` and `runs/plan7/K1_parent_count_pass_3060.sh` — no code file — so the merge is clean, but I read the spec out of `git show 09c687c:PLAN7.md` and `C:/Users/John Peponis/Desktop/uttt-zero/docs/reviews/M2_designs/REVIEW.md` (the worktree has neither).

## 2. The rows, what was done, where

**Row 3 — J3's interval note.** `tools/empty_board.py:124-131`. `interval_note` now says the games are independent draws from the arm's stochastic policy, so the Wilson intervals are the correct 95 % intervals for that policy's outcome distribution; identical games are duplicate *outcomes* of independent draws, and `distinct_games` / `distinct_openings_4ply` / `distinct_openings_4ply_canonical` report the concentration and are **not** a correction to them. It names both refusals explicitly: a bootstrap over distinct lines would reweight them and estimate a different policy, and widening the sampled plies would define a different experiment. The docstring (`:26-31`) and `arm_stats`'s own docstring (`:98-100`) carry the same statement, and the printed line is relabelled "policy concentration (not an interval correction)" (`:143-145`).

**Row 15 — evaluators, and (a)'s status.** `tools/empty_board.py:236-237, 250-251, 302-305`. Arms (b) and (c) take the plain `FusedEvaluator`; `--sym` substitutes `SymmetryAveragedEvaluator` for them. Arm (a) takes the symmetry-averaged evaluator unconditionally (`:249, 279`) — `--sym` does not touch it, because its precedent (`atlas.deep_values`) is unconditional. Each arm records its evaluator (`arm_stats`, `:106`), and the meta records all three plus the reason (`:316-321`). Arm (a)'s record gained a `comparability` field (`:288-291`) saying it is a different search (PUCT at depth cap 40 against the game arms' Gumbel search at depth cap 24) and a different evaluator — a separate measurement, not a matched-budget comparator.

**Row 15 — budget, depth cap, `gumbel_scale`.** `tools/empty_board.py:324-328`. `meta["budget_and_depth"]` holds `arm_sims`, `arm_depth_cap` (24), `trained_depth_cap` (12), `trained_sims` (32), `trained_sims_schedule` (`60:48,100:64`) and the sentence *"exploration settings as trained; budget and depth cap are not"*; the same sentence is printed (`:275-277`). `meta["gumbel_scale"]` holds (b)'s, (c)'s and `c_source`, resolved at `:256-262`: `--c_gumbel_scale` if given, else `config.json`'s `gumbel_scale` if the key exists, else 1.0 with the text "MCTSConfig's default 1.0 (…config.json has no gumbel_scale key, so the run trained at it)". `_e8` has no such key, so the smoke prints the third branch.

**Row 7 — the two first-move statistics.** `tools/empty_board.py:159-217`. New `opening_trajectory()` reads both records; `timeline.json`'s `first_top_share` is labelled *the raw policy's first-move probability* (`probs.max()` on the empty board, `tools/timeline.py:129-130`) and the generated games' `first_move_top` / `first_move_top_share` from `<run>/log.jsonl` is printed beside it at the same iterations. Pairing rule, documented in the function docstring: timeline row `iter` = N is checkpoint `net_NNNN.pt`, written after training iteration N−1 (`uttt/train2.py:397-399`), so the generating log row is N−1. Every row goes into the JSON as `run_opening_trajectory` with `log_iter`, both moves, both shares and the generating iteration's game count; `meta["first_move_statistics"]` (`:332-335`) says neither substitutes for the other. On `_e8` this prints 0.982 against 0.835 at iteration 300 — and, at iteration 10, two *different moves* (raw [44] 0.215, generated [42] 0.528).

**Row 16 — the ordinate.** `tools/frontier.py`. Field names: `fraction_complete_coverage_conditional_on_alive`, `fraction_complete_coverage_ci_conditional_on_alive`, `n_complete`, `incomplete_count_conditional_on_alive`, `median_nodes_conditional_on_complete`, `p90_nodes_conditional_on_complete`, `search_optimal_move_rate_conditional_on_complete`, `search_mean_regret_conditional_on_complete`, `median_empties_conditional_on_complete` (`:318-335`). The header docstring says it in capitals (`:16-22`), `meta["complete_coverage"]` (`:274-278`) gives the definition and why it is stricter than root solvability, the printed column is "complete coverage" and the legend line states it (`:210-216`). The graded `EndgameSet` is named "ply N, complete coverage" (`:154`).

**Row 4 — intervals.** `tools/frontier.py:75-85` implements Wilson locally. The coverage fraction gets one (`:321`); the optimal-move rate gets one computed from the per-position regret vector (`:348`), replacing the bootstrap CI. Mean regret keeps the cluster bootstrap (`:354`) except when the regret sample is degenerate, where no interval is emitted and `search_mean_regret_ci_note` (`:351-353`) says the zero-width percentile interval is an artifact of resampling identical values, not population certainty, and points at the optimal-rate Wilson interval instead; the table prints `[n/a]`. `finite_population_note` (`:336-341`) is set on rows where `positions_sampled == games_alive_at_ply`, and says the coverage fraction is then a census of this corpus's alive games at that ply while the Wilson interval refers to the wider population of games the checkpoint's self-play could generate. `meta["intervals"]` (`:285-288`) states the scheme.

**Row 16 — the per-position table.** `tools/frontier.py:176-207, 374-377`. `<out>_positions.npz` (named in `meta["positions_npz"]`, described in `meta["positions_table"]`) carries every sampled position, complete or not: `ply`, `file_index` (into the saved `corpus_files` array), `game_row`, `game_id` (the cluster id), `empties`, `complete`, `nodes`, `exact_root_value`, `child_values` (81 int8), `move`, `optimal`, `regret`, plus the full `meta` as a JSON string. The search's chosen move comes from `search_moves()` (`:161-174`), one extra search under exactly the `SearchConfig` `uttt.endgame.evaluate` builds (`endgame.py:291-292`) — `evaluate` returns the regret but not the move, and `uttt/endgame.py` is another agent's file. Each position's recorded move is cross-checked against the grader's per-position regret; disagreements are counted into `meta["chosen_move_regret_mismatches"]` and printed as a warning (`:357-363`). Zero on every run below, including one with four non-optimal moves. [Superseded 2026-09-13 after M2's rebuttal (R6): the recorded move is now the graded move from `evaluate`'s per-position record and the second search is gone — see M2R_implementation_notes.md.]

**Row 16 — the node convention and the resampling warning.** Header docstring `:24-29` and `meta["node_convention"]` (`:279-282`): a node is one recursive entry of `uttt.solver._negamax_bounded`; a child already terminal after the move is decided directly in `solve_children_bounded` and costs zero counted nodes (`uttt/solver.py:255-263`); the budget bounds search work, not wall time. `meta["clusters"]` (`:289-293`) and the header (`:38-41`) say games recur across plies, so across-ply comparisons need game-linked resampling over the per-position table, which carries `game_id` for that purpose. The convention is visible in the smoke: plies 73–75 report median 0 nodes, because every legal child there is terminal.

**Row 9 (J3/J4 half).** `--rule` (`choices=RULES`, default `count`, validated by `check_rule`) in both tools: `tools/empty_board.py:238, 243` threaded to `BatchUTTT` and `BatchedSearch` (`:88-89`) and to `atlas.deep_values(..., rule=rule)` (`:280`, whose signature already took it); `tools/frontier.py:253, 256` threaded to `solve_children_bounded` via `functools.partial` so it survives the pool (`:140`), to `UTTT(rule)` during replay (`:123`), to `graded_set`'s `EndgameSet` meta (`:154`) and to `evaluate(..., rule=rule)` (`:344`). Both metas carry `"rule"`; `empty_board` also carries `train_rule`, `frontier` `corpus_rule`. Both outputs are rule-tagged through `uttt.rules.tag_path` (`empty_board.py:338`, `frontier.py:262`), as `tools/atlas.py:216` does.

**Row 18 (my half).** `tests/test_solver_bounded.py`. `test_complete_is_always_right` gained a `rule` parameter (`:78-99`) and runs under both rules against a reference solved under the same rule (`test_bounded_matches_unbounded_draw` now returns `(games, ref)`). New `test_children_bounded` (`:118-163`): (i) a generous budget makes `solve_children_bounded` reproduce `solve_children` in root value and all 81 child values on 250 positions under both rules, with a guard that the draw rule actually changes some root values; (ii) a budget of half what the enumeration needs returns `(None, None, used, False)` with `used <= budget` on every position needing ≥ 2 nodes; (iii) the same call through a `multiprocessing.Pool` of 2 workers under `draw` returns exactly the in-process root value, child table and node count.

## 3. Design choices the spec left open

1. **`--sym` is a flag, not a mode selector, and does not reach arm (a).** The plain evaluator is the default for (b)/(c) because it is the corpus-generating agent; `--sym` restores the previous behaviour for those two arms only. Arm (a) reuses `atlas.deep_values`, whose symmetry averaging is the atlas precedent M2 accepted, so making it switchable would invite a reading no precedent covers.
2. **`--c_gumbel_scale` default changed from `1.0` to `None`.** Resolution order is CLI → `config.json["gumbel_scale"]` → `MCTSConfig`'s 1.0, and the resolved value's *source string* is recorded verbatim in `meta["gumbel_scale"]["c_source"]` and printed. A hardcoded 1.0 would silently keep lying once the trainer gains the field, which is exactly what row 5 is fixing.
3. **Timeline↔log pairing by `iter − 1`, justified in code.** `uttt/train2.py:397-399` writes `net_{it+1:04d}.pt`, so a timeline row for `net_0300` was evaluated on the checkpoint produced by log iteration 299. I record `log_iter` in every JSON row rather than leave the offset implicit, and fall back to `None` when no log row exists.
4. **A rule mismatch against a *checkpoint* or a *corpus* is noted, not refused.** `uttt/rules.py` states that a tool's evaluation rule is always an argument and is never conflated with a run's training rule; grading a count-trained net under `draw` is a legitimate measurement (K1's own 2 × 2 cross-play needs it). So both tools print a NOTE and record `train_rule` / `corpus_rule` in the meta. The refusals that do bite are unchanged and unbypassed: `uttt.endgame.evaluate` still refuses an `EndgameSet` whose exact labels were solved under another rule, and `graded_set` now stamps the set's rule explicitly so that check is real rather than inherited by accident.
5. **Both outputs are rule-tagged** (`tag_path`), so a `--rule draw` re-read cannot overwrite or be mistaken for the count reading; `<out>_positions.npz` derives from the tagged path, so the JSON and its table always agree. Verified: `J4_frontier_draw.json` + `J4_frontier_draw_positions.npz`.
6. **The chosen move comes from one extra search, and is cross-checked rather than trusted.** `uttt/endgame.py` is another agent's file this round, so I could not have `evaluate` return the moves; reconstructing them from root visit counts would be fragile. The extra search costs seconds per ply against minutes of solving. Because two searches could in principle disagree, I recompute each position's regret from my move and the exact child values and compare it to the grader's per-position regret; mismatches are counted in the meta and warned about **but do not abort** — a hard assert would throw away hours of a 3.5 h run over a reporting detail. The check has found 0 mismatches on 177 graded positions, 4 of them non-optimal.
7. **A degenerate regret sample reports no interval at all.** The alternative — keeping `[0.000, 0.000]` with a caveat — is the thing finding 4 objects to. The note names the substitute (the optimal-rate Wilson interval), so the row is not left silently uncertain.
8. **The optimal-rate Wilson interval is computed from integer counts** (`(per_regret == 0).sum()`), not from the float rate, so it is exact at the boundaries.
9. **Wilson is implemented twice, once per tool.** `frontier.py` does not put `tools/` on `sys.path` and neither tool should acquire a dependency on the other; the duplication is eight lines and is flagged in both docstrings.
10. **npz sentinels.** `complete=False` rows carry `move = -1`, `optimal = -1`, `regret = NaN` and a child row of `NULL_ROW = -3` throughout — distinct from `ILLEGAL = -2`, so "illegal move in a complete row" and "nothing known about this position" never collide. An assert in `position_rows` (`:208`) pins that complete rows contain nothing below `ILLEGAL`. I also stored `exact_root_value` (not on the spec's list): it is one int8 column, it makes `regret == root − child[move]` checkable from the table alone, and I used it to verify exactly that.
11. **The rename was applied to every name carrying "solved"**, not only the three the row named — including `unsolved_count → incomplete_count_conditional_on_alive` and `median_empties_conditional_on_complete`. A file mixing the two vocabularies is worse than either.
12. **`finite_population_note` is per-row and phrased about the superpopulation**, not as a finite-population *correction* to the interval. Applying an FPC would assert that the alive set of this corpus is the target population; the honest statement is that the fraction is a census of that set and the Wilson interval belongs to the wider population of games the policy could generate. Read one way or the other, not both.
13. **Test sizes**: 250 positions for property 4 (each solves every legal child, so it is ~5× the per-position cost of property 1), 100 of them through the pool, 2 workers — enough to prove rule propagation across a process boundary without paying for eight spawns. The tight budget is `used // 2` restricted to positions needing ≥ 2 nodes, which is guaranteed to fail (the enumeration is deterministic and budget-independent in its per-child costs) and fails *mid*-enumeration rather than on the last child.
14. **`positions_at_ply` takes the rule** even though replay is rule-independent (the terminal rule decides the winner of a full macro grid, not whether the game is over). Stated in its docstring. Nothing in either tool now constructs a game object without an explicit rule.

## 4. Test and smoke outputs, verbatim

`tests/test_solver_bounded.py`:

```
500 positions (<= 16 empties): bounded == unbounded in value and node count; median 5516 nodes, max 1882919; unbounded 1.51s, bounded 1.65s (+9.1 %)
draw rule: bounded == unbounded in value and node count on 500 positions; 90 of them have a different value than under the count rule
rule count: completed and agreed with the unbounded value: 23/500 at a budget of 10, 113/500 at a budget of 1000, 457/500 at a budget of 100000
rule draw: completed and agreed with the unbounded value: 23/500 at a budget of 10, 97/500 at a budget of 1000, 447/500 at a budget of 100000
budget 10: incomplete on 477/500 positions — exactly those needing more than 10 nodes, value None on every one of them
solve_children_bounded == solve_children in root value and all 81 child values on 250 positions under both rules (40 differ in root value between the rules); median 12086 nodes, max 6231875
budget = half of what the enumeration needs: incomplete on all 249 positions that need >= 2 nodes, (None, None, used <= budget, False) on every one
pooled (2 workers, rule draw): identical root value, child table and node count to the in-process result on 100 positions
ok [30.0s]
```

`tests/test_endgame.py`:

```
child labels agree with the solver
cluster bootstrap ok
evaluator                                       WDL acc %    Brier  logloss            3-way %  |err|             regret          optimal %
raw net (value head + policy argmax)     33.3 [16.7,54.2]    0.667    1.099   33.3 [16.7,50.0]  0.677 0.292 [0.042,0.458]   75.0 [58.3,95.8]
raw net, symmetry-averaged WDL           33.3 [16.7,54.2]    0.667    1.099   33.3 [16.7,50.0]  0.676
search 8 sims                                                                 41.7 [25.0,58.4]  0.589 0.292 [0.125,0.501]   75.0 [58.3,87.5]
search 16 sims                                                                58.3 [41.7,70.9]  0.506 0.208 [0.083,0.376]   79.2 [62.4,91.7]
rollout                                                                                               0.042 [0.000,0.125]  95.8 [87.5,100.0]
build / save / load / evaluate ok
ok
```

J3, `tools/empty_board.py --net runs/deep8_c1_300_e8/net_0300.pt --games 16 --sims 32 --root_sims 256 --device cuda:0` (`--out` to the scratchpad; the worktree's own `net_0300.pt`, `config.json`, `timeline.json` and `log.jsonl` are tracked and identical to the main checkout's):

```
runs/deep8_c1_300_e8/net_0300.pt on cuda:0; rule count (trained under count); arms (b)/(c) play with the plain FusedEvaluator (the agent that generated the run's corpus), arm (a) is 8-way symmetry-averaged (uttt.symmetry)
exploration as trained from runs/deep8_c1_300_e8\config.json: sample_moves 8, temperature 1.0, sample_uniform 0.15, root_prior_floor 0.03, c_scale 1.0, gumbel_scale 1.0 <- MCTSConfig's default 1.0 (runs/deep8_c1_300_e8\config.json has no gumbel_scale key, so the run trained at it)
exploration settings as trained; budget and depth cap are not: arms (b)/(c) play at 32 sims and depth_cap 24, against the run's trained depth_cap 12 and sims 32 (schedule '60:48,100:64')

(a) empty board @256 sims: value for X +0.5087; principal line [40, 36, 0, 8, 80, 77, 50, 48, 34, 66]  [5s]

  (b) sampled 4 plies, floor off: 16/16 games (8s)
  (c) exploration as trained: 16/16 games (9s)

  (b) sampled 4 plies, floor off        16 games @   32 sims   X   0.0 % [  0.0,  19.4]   O 100.0 % [ 80.6, 100.0]   draw   0.0 % [  0.0,  19.4]
                                     mean length  50.0   end reasons line 100.0 % / count   0.0 % / equal   0.0 %
                                     policy concentration (not an interval correction): 1 distinct games, 1 4-ply openings (1 up to symmetry)   [8s]
  (c) exploration as trained            16 games @   32 sims   X  68.8 % [ 44.4,  85.8]   O  25.0 % [ 10.2,  49.5]   draw   6.2 % [  1.1,  28.3]
                                     mean length  51.7   end reasons line  87.5 % / count   6.2 % / equal   6.2 %
                                     policy concentration (not an interval correction): 16 distinct games, 10 4-ply openings (9 up to symmetry)   [9s]

the run's own opening trajectory (timeline.json + log.jsonl). Two different statistics, neither a substitute for the other:
  raw policy      = the checkpoint's first-move PROBABILITY on the empty board (timeline.json first_top_share = probs.max(), tools/timeline.py:129-130)
  generated games = the share of that iteration's self-play games whose first move was the modal one (log.jsonl first_move_top_share)
     iter 10:  raw policy     [44] 0.215   generated games     [42] 0.528
    iter 160:  raw policy     [40] 0.976   generated games     [40] 0.832
    iter 300:  raw policy     [40] 0.982   generated games     [40] 0.835
```

The same command with `--sym`:

```
runs/deep8_c1_300_e8/net_0300.pt on cuda:0; rule count (trained under count); arms (b)/(c) play with the 8-way symmetry-averaged (uttt.symmetry), arm (a) is 8-way symmetry-averaged (uttt.symmetry)
exploration as trained from runs/deep8_c1_300_e8\config.json: sample_moves 8, temperature 1.0, sample_uniform 0.15, root_prior_floor 0.03, c_scale 1.0, gumbel_scale 1.0 <- MCTSConfig's default 1.0 (runs/deep8_c1_300_e8\config.json has no gumbel_scale key, so the run trained at it)
exploration settings as trained; budget and depth cap are not: arms (b)/(c) play at 32 sims and depth_cap 24, against the run's trained depth_cap 12 and sims 32 (schedule '60:48,100:64')

(a) empty board @256 sims: value for X +0.5087; principal line [40, 36, 0, 8, 80, 77, 50, 48, 34, 66]  [6s]

  (b) sampled 4 plies, floor off: 16/16 games (10s)
  (c) exploration as trained: 16/16 games (11s)

  (b) sampled 4 plies, floor off        16 games @   32 sims   X  81.2 % [ 57.0,  93.4]   O   0.0 % [  0.0,  19.4]   draw  18.8 % [  6.6,  43.0]
                                     mean length  51.6   end reasons line  81.2 % / count   0.0 % / equal  18.8 %
                                     policy concentration (not an interval correction): 4 distinct games, 4 4-ply openings (2 up to symmetry)   [10s]
  (c) exploration as trained            16 games @   32 sims   X  37.5 % [ 18.5,  61.4]   O  37.5 % [ 18.5,  61.4]   draw  25.0 % [ 10.2,  49.5]
                                     mean length  52.7   end reasons line  62.5 % / count  12.5 % / equal  25.0 %
                                     policy concentration (not an interval correction): 16 distinct games, 12 4-ply openings (7 up to symmetry)   [11s]

the run's own opening trajectory (timeline.json + log.jsonl). Two different statistics, neither a substitute for the other:
  raw policy      = the checkpoint's first-move PROBABILITY on the empty board (timeline.json first_top_share = probs.max(), tools/timeline.py:129-130)
  generated games = the share of that iteration's self-play games whose first move was the modal one (log.jsonl first_move_top_share)
     iter 10:  raw policy     [44] 0.215   generated games     [42] 0.528
    iter 160:  raw policy     [40] 0.976   generated games     [40] 0.832
    iter 300:  raw policy     [40] 0.982   generated games     [40] 0.835
```

Two things in that pair are worth carrying into the J3 reading. First, `--sym` reproduces the predecessor's smoke for arm (b) **exactly** (X 81.2 / O 0.0 / draw 18.8, 4 distinct games, 2 up to symmetry), so the only thing the evaluator change moves is the evaluator. Second, with the plain evaluator arm (b) collapses to **one distinct game out of 16** and gives X 0 % / O 100 %: at 16 games and 32 sims the corpus-generating agent's near-greedy play is a single line, and it is an O win. That is the concentration row 3 says to report rather than correct; whether it survives 2 000 games at 256 sims is the real run's business. Arm (c) differs between the two runs in the third decimal-place sense (43.8/37.5/18.8 on the predecessor's cuda:1 pass versus 37.5/37.5/25.0 here) — I re-ran the `--sym` command on cuda:0 and it reproduced itself exactly, and arm (b) matched the predecessor across devices, so the divergence is GPU-dependent floating point in the noisier Gumbel path (3060 versus 3090), not the code. I did not verify that on the 3060, which is busy.

J4, `tools/frontier.py --run <main checkout>/runs/deep8_c1_300_e8 --net <…>/net_0300.pt --plies 60 62 --per_ply 20 --max_nodes 1e6 --sims 256 --device cuda:0`:

```
C:/Users/John Peponis/Desktop/uttt-zero/runs/deep8_c1_300_e8: 98581 games in 20 files (games_0280.npz..games_0299.npz); grading C:/Users/John Peponis/Desktop/uttt-zero/runs/deep8_c1_300_e8/net_0300.pt at 256 sims on cuda:0
plies 60-62, 20 positions per ply, budget 1,000,000 nodes per position, 8 solver processes, rule count

 ply   alive sampled          complete coverage   nodes med   nodes p90          optimal %             regret  incompl      s
(complete coverage = every legal child's exact value obtained inside the shared budget — stricter than proving the root's value)
(coverage: conditional on alive, 95 % Wilson | nodes, optimal, regret: conditional on complete; optimal Wilson, regret cluster bootstrap)
  60    7850      20 100.0 % [ 83.9,100.0] (20)          23       1,072 100.0 [ 83.9,100.0]        0.000 [n/a]        0   11.0
  61    5119      20 100.0 % [ 83.9,100.0] (20)          10          48 100.0 [ 83.9,100.0]        0.000 [n/a]        0   15.0
  62    3640      20 100.0 % [ 83.9,100.0] (20)           6         221 100.0 [ 83.9,100.0]        0.000 [n/a]        0   26.5

wrote …\J4_frontier.json and …\J4_frontier_positions.npz (60 positions)
```

Median and p90 node counts are identical to the predecessor's smoke (23/10/6, 1 072/48/221): the measurement did not move, only its reporting. `100.0 [100.0,100.0]` is now `100.0 [83.9,100.0]`.

Four branch checks beyond the required smoke, all on the same corpus and `cuda:0`:

```
# --plies 40 42 --per_ply 12 --max_nodes 2e5  (incomplete positions; reproduces the predecessor's 8.3/16.7/50 %)
  40   98181      12    8.3 % [  1.5, 35.4] (1)     135,125     135,125 100.0 [ 20.7,100.0]        0.000 [n/a]       11   10.1
  41   97542      12   16.7 % [  4.7, 44.8] (2)       1,086       1,917 100.0 [ 34.2,100.0]        0.000 [n/a]       10   12.1
  42   97285      12   50.0 % [ 25.4, 74.6] (6)      35,252     101,396 100.0 [ 61.0,100.0]        0.000 [n/a]        6   11.8

# --plies 72 76 --per_ply 500  (the whole alive set; finite_population_note on 72-75, none at 76)
  72       6       6  100.0 % [ 61.0,100.0] (6)           4           6 100.0 [ 61.0,100.0]        0.000 [n/a]        0   10.3
  73       5       5  100.0 % [ 56.6,100.0] (5)           0           4 100.0 [ 56.6,100.0]        0.000 [n/a]        0   12.4
  74       2       2  100.0 % [ 34.2,100.0] (2)           0           1 100.0 [ 34.2,100.0]        0.000 [n/a]        0   11.5
  75       1       1  100.0 % [ 20.7,100.0] (1)           0           0 100.0 [ 20.7,100.0]        0.000 [n/a]        0   11.4
  76       0       0                          -           -           -                  -                  -        0    0.0

# --plies 40 40 --per_ply 6 --max_nodes 10  (zero coverage)
  40   98181       6    0.0 % [  0.0, 39.0] (0)           -           -                  -                  -        6    3.6

# --net net_0010.pt --plies 50 52 --per_ply 40 --max_nodes 1e7 --sims 32  (non-degenerate regret)
  50   70386      40  92.5 % [ 80.1, 97.4] (37)       1,989     794,458 100.0 [ 90.6,100.0]        0.000 [n/a]        3   10.3
  51   60700      40 100.0 % [ 91.2,100.0] (40)       2,254     175,922  92.5 [ 80.1, 97.4] 0.150 [0.000,0.350]        0   10.6
  52   55956      40 100.0 % [ 91.2,100.0] (40)         314     102,875  97.5 [ 87.1, 99.6] 0.025 [0.000,0.075]        0   12.0

# --rule draw --plies 60 62 --per_ply 20 --max_nodes 1e6  (rule threading; wrote J4_frontier_draw{,_positions}.*)
plies 60-62, 20 positions per ply, budget 1,000,000 nodes per position, 8 solver processes, rule draw (corpus trained under count)
  60    7850      20 100.0 % [ 83.9,100.0] (20)          24         949 100.0 [ 83.9,100.0]        0.000 [n/a]        0   13.1
  61    5119      20 100.0 % [ 83.9,100.0] (20)          12         118 100.0 [ 83.9,100.0]        0.000 [n/a]        0   23.5
  62    3640      20 100.0 % [ 83.9,100.0] (20)           7         264 100.0 [ 83.9,100.0]        0.000 [n/a]        0   21.8
```

The draw run's node counts (24/12/7) differ from the count run's (23/10/6), which is the evidence that `--rule` reaches the pooled solver. `tools/empty_board.py … --rule draw` likewise prints `rule draw (trained under count)` plus the NOTE line and writes a `_draw`-tagged file.

Per-position table, read back from the npz (the required smoke's, the tight run's and the weak-net run's):

```
keys: ['child_values', 'complete', 'corpus_files', 'empties', 'exact_root_value', 'file_index', 'game_id', 'game_row', 'meta', 'move', 'nodes', 'optimal', 'ply', 'regret']
  ply               int16    (60,)      first5=[60, 60, 60, 60, 60]
  file_index        int32    (60,)      first5=[18, 5, 5, 18, 10]
  game_row          int64    (60,)      first5=[471, 4877, 737, 2516, 185]
  game_id           int64    (60,)      first5=[18874839, 5247757, 5243617, 18876884, 10485945]
  empties           int64    (60,)      first5=[6, 11, 2, 9, 4]
  complete          bool     (60,)      first5=[True, True, True, True, True]
  nodes             int64    (60,)      first5=[74, 2191, 2, 1412, 16]
  exact_root_value  int8     (60,)      first5=[1, 0, 0, 1, 0]
  move              int16    (60,)      first5=[78, 63, 75, 34, 17]
  optimal           int8     (60,)      first5=[1, 1, 1, 1, 1]
  regret            float32  (60,)      first5=[0.0, 0.0, 0.0, 0.0, 0.0]
  child_values       int8 (60, 81) row0 legal entries: {17: -1, 57: -1, 58: -1, 68: -1, 76: 1, 78: 1}
  corpus_files       (20,) games_0280.npz .. games_0299.npz
  meta rule/corpus_rule/mismatches: count count 0 | positions_npz: J4_frontier_positions.npz

tight npz: 36 rows, 27 incomplete
 incomplete row0: move -1 optimal -1 regret nan nodes 200000 child_values unique [-3]
 complete rows: 9 | child_values unique on complete: [-2, -1, 0, 1]

weak-net run: mismatches: 0
graded rows: 117 non-optimal: 4 regret values: [0.0, 1.0, 2.0]
regret == root - child[move] everywhere: True
```

And one JSON row verbatim, so the new field names are on the record:

```json
{"ply": 60, "games_alive_at_ply": 7850, "positions_sampled_conditional_on_alive": 20,
 "fraction_complete_coverage_conditional_on_alive": 1.0,
 "fraction_complete_coverage_ci_conditional_on_alive": [0.8388748419471806, 1.0],
 "n_complete": 20, "incomplete_count_conditional_on_alive": 0, "finite_population_note": null,
 "median_nodes_conditional_on_complete": 23.0, "p90_nodes_conditional_on_complete": 1071.8000000000006,
 "nodes_spent_total": 5785,
 "search_optimal_move_rate_conditional_on_complete": 1.0,
 "search_optimal_move_rate_ci_conditional_on_complete": [0.8388748419471806, 1.0],
 "search_mean_regret_conditional_on_complete": 0.0,
 "search_mean_regret_ci_conditional_on_complete": null,
 "search_mean_regret_ci_note": "every regret in the sample is 0: the percentile bootstrap of a degenerate sample is zero-width, which is an artifact of resampling identical values and not population certainty. No interval is reported; the optimal-move rate's Wilson interval is the uncertainty statement here.",
 "median_empties_conditional_on_complete": 5.5, "seconds": 10.6}
```

## 5. Not done, and why

- **The real J3 and J4 runs.** Smoke only, as instructed; J4's real pass also wants the 3060, which is occupied.
- **Memoizing arm (b)'s repeated deterministic suffixes** (REVIEW answer 3 offers it as an optimization). Not in my rows; it is a correctness-conditional speed-up — the review itself says the deterministic continuation must be validated across batches and seeds first, and index-based tie-breaking survives symmetry averaging. Arm (b) at 2 000 games is not the expensive arm.
- **No linter was run**: the venv has neither `flake8` nor `pyflakes` and I did not install one. `py_compile` passes on all three files, imports were checked by hand, and every code path above was executed at least once.
- **`tools/frontier.py` always writes the per-position table** — no flag to suppress it. At the real size (31 plies × 500 positions) it is well under a megabyte compressed.
- **The worktree branch was not rebased onto `09c687c`.** See §1: no code file differs between the two commits, so this is a note for whoever merges, not a problem I could fix without touching `PLAN7.md`.
- **`uttt/solver.py`, `uttt/endgame.py`, `uttt/train2.py`, `tests/test_rules.py` and the other agent's files are untouched**, including the search cache keying and the `gumbel_scale` field that rows 1 and 5 add — `tools/empty_board.py` already reads that field when it appears and falls back with an explicit source string until then.
