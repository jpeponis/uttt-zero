# K1 — M2's findings applied: implementation notes (written 2026-09-12 by the implementing agent after M2; verbatim, lightly formatted)

*PLAN7 §7e's M2 block was adjudicated in eighteen rows, all accepted. Rows 1, 5, 6, 8, 9 and 18 of that
table — the engineering that had to land before K1's launch — together with the five I1 tools PLAN7 §5
lists as a pre-reading item, were implemented by an Opus `directed` agent in an isolated worktree
(commit `603daf8`; rows 3, 4, 7, 15 and 16 were a second agent's, in `tools/empty_board.py`,
`tools/frontier.py` and `tests/test_solver_bounded.py`). These are its notes: the files changed, each row
and where it landed, the fourteen design choices the spec left open, the test and smoke output as it
printed, and what was deliberately not done.*

## 1. Files changed

| file | what |
|---|---|
| `uttt/train2.py` | rows 1, 5; the `rule` tag in every game file |
| `uttt/endgame.py` | rows 1, 9 |
| `tools/endgame.py` | passes the rule to `evaluate_rollout` |
| `tools/eval_worker.py` | row 9 |
| `tools/openings.py` | row 6 (surrogate) |
| `tools/book.py` | row 6 (paired file) |
| `tools/corpus_stats.py` | rows 6, 9 (`corpus_rule`, the replay message) |
| `tools/principles.py` | rows 6, 8, 9 |
| `tools/decision.py`, `tools/surprise.py`, `tools/ownership_grade.py`, `tools/timeline.py`, `tools/probe_value.py` | the five I1 tools |
| `tools/gdata.py`, `tools/annotate.py`, `tools/endgame_accuracy.py` | the three optional ones — all three done |
| `tests/test_rules.py`, `tests/test_tablebase.py` | row 18 |
| `tests/test_rules_boundaries.py` | **new**, 318 lines, row 18 |

## 2. Each row: what was done, where

**Row 5 — `gumbel_scale` and the resolved search configuration.** `uttt/train2.py:57-60` adds
`gumbel_scale: float = 1.0` with the comment that every run so far trained at `SearchConfig`'s own
default of 1.0, which `train2` never set and so never recorded, making it documentation rather than an
intervention. `train2.py:274-278` builds the self-play `SearchConfig` (now with
`gumbel_scale=cfg.gumbel_scale`) **before** `info`, and `train2.py:281` writes `asdict(scfg)` into
`info["_provenance"]["search_config"]`. The old construction site after the buffer allocation is gone;
the sims-schedule rebuild (`replace(scfg, n_sims=…)`) carries the field. `--gumbel_scale` appears
automatically (argparse is generated from the dataclass). Behaviour is bit-identical: 1.0 was already
the inherited value.

**Row 1 — the cross-rule resume.** `uttt/train2.py:255-271`: `config.json` is read at the top of
`main()`, before `os.makedirs`, before `attempt` is counted, before `info` exists, and long before
`torch.load`. A recorded rule differing from `cfg.rule` raises `ValueError` naming both; a missing
`rule` key means `"count"`. The existing config-differs WARNING (`train2.py:285`) is untouched and still
fires for every other key.

**Row 1 — the search cache.** `uttt/endgame.py:291,296` key it `(sims, rule)`; `endgame.py:297`
additionally asserts `bs.rule == rule`, so a cache handed in poisoned (the old `{sims: search}` shape)
fails loudly rather than grading a draw set with a count search. `EvalKit.eg_cache` and the E7 worker's
`eg_cache` pass through unchanged.

**Row 9 — the explicit rollout rule.** `uttt/endgame.py:303-313`:
`evaluate_rollout(player_fn, es, n_boot, rule)`, validated against `es.rule` with `evaluate`'s exact
message and `ValueError` type; the `BatchUTTT` is built from `rule`, not `es.rule`. `tools/endgame.py:68`
passes `rule=a.rule`. The docstring states what it cannot check — that the caller also built `player_fn`
under that rule.

**Row 9 — the E7 worker.** `tools/eval_worker.py:74-76`: the set's rule is compared with `a.rule` in
`Worker.__init__` immediately after `EndgameSet.load`, before the anchors, the players or a single match.

**Row 6 — the surrogate.** `tools/openings.py:51-56`: `player()` refuses a `surrogate:` spec under any
rule but `count`, at the top, before the file is opened. The reason is in the comment: the surrogate is a
learned model of the count-rule game with no terminal logic of its own.

**Row 6 — the paired file.** `tools/book.py:151-162`: `paired_stats(path, rule)` reads the JSON's
`"rule"` (missing → `"count"`) and refuses a mismatch. Called at `book.py:236`, i.e. **before** the book
is built — the check used to be reachable only after hours of search and after the book JSON was already
written.

**Row 6 / 9 — the corpus rule.** `tools/corpus_stats.py:39-52` adds `games_rule(run)`, reading the `rule`
entry of every `games_*.npz` (only the zip directory is read; ~2 s cold over 300 files, 0.05 s warm) and
refusing a directory whose files carry more than one tag. `corpus_stats.py:55-80`'s
`corpus_rule(run, override="")` prefers that tag, then `config.json` (a missing `rule` key there = count),
refuses a tag that contradicts `config.json`, and refuses a directory with neither unless `--corpus_rule`
names it. `--corpus_rule` was added to `corpus_stats`, `principles`, `decision`, `timeline`, `gdata` and
(as the buffer's run rule) `probe_value`, `surprise`, `endgame_accuracy`. `corpus_stats.py:88-92`: the
reverse-relabel refusal now says the information is not lost — every move is stored — but recovering it
*requires replaying the saved moves (not implemented)*.

**The `rule` tag in game files.** `uttt/train2.py:378-380`:
`np.savez_compressed(…, rule=np.array(cfg.rule), **games)` — a 0-d string array, added at the save site
rather than inside `ContinuousSelfPlay.run`, whose per-key `np.concatenate` would have had to
special-case it. Pre-K1 files carry no such entry and keep reading as count through `config.json`.

**Row 8 — the draw sample.** `tools/principles.py:95-107` adds `sample_draws(winners, max_games, seed)`:
all draws in file order when the window holds at most `max_games` — so `_e4`'s 16 471-draw reading is
reproduced exactly, element for element — otherwise
`np.sort(default_rng(seed).choice(idx, max_games, replace=False))`. `--seed` (default 0) and
`--max_draws` at `principles.py:159-164`. `principles.py:140-146` records `"draws total"`,
`"draws sampled"`, `"draw sample seed"`, `"draw sample cap"`, and replaces `"mean boards each side"` with
`"mean boards X"` and `"mean boards O"`.

**The five I1 tools.** All get `--rule` (default `count`), threading, a rule in the output and a refusal:

- `tools/decision.py:47` — `BatchUTTT(G, device, a.rule)` and `BatchedSearch(…, rule=a.rule)`; the
  corpus's outcomes are relabelled to the evaluation rule through `corpus_stats.relabel`, so a draw
  corpus read under count is refused; the rule and the relabel count are printed.
- `tools/surprise.py:54` — `BatchedSearch(…, rule=a.rule)`, the printed board's `UTTT(rule)`, the rule in
  the header line, and the buffer's run rule checked.
- `tools/probe_value.py:106` — no search or terminal here, so the rule changes no arithmetic; it labels
  the reading and, via the new `check_buffer_rule` (`probe_value.py:39-48`, shared with `surprise` and
  `endgame_accuracy`), refuses a buffer from a run of another rule.
- `tools/timeline.py:101` — `evaluate(…, rule=a.rule)`, `BatchUTTT(1, device, a.rule)`,
  `sample_positions(…, a.rule)`; the endgame set's rule checked at load and the held-out corpus's rule
  checked against `--rule`; `rule`, `run_rule` and `corpus_rule` in `meta`; `timeline.json`,
  `timeline.png` and the `eval_full.jsonl` read all `tag_path`-ed.
- `tools/ownership_grade.py:137` — the probe dataset's `meta["rule"]` checked, `"rule"` in the JSON,
  `tag_path` on `--out`.

**The three optional ones — all done, all small.** `tools/gdata.py:132` (replay, teacher search and
`partial(solve_batch, rule=…)` through the pool; `rule` and `corpus_rule` in `meta`; `tag_path` on
`--out`; the corpus's rule checked). `tools/annotate.py:74` (`as_game`, `pv_and_end`, `solve_children`;
the puzzle file's `meta["rule"]` checked; `tag_path` on `--out`; the rule in the document header).
`tools/endgame_accuracy.py:43` (`solve`, `step_state`, `BatchedSearch`; the buffer's rule checked; a
`rule` array in the `--out` npz).

**Row 18 — tests.** `tests/test_rules.py:80-96` adds `compare_states`, called at `:120` after **every**
ply: `done`, `next_board`, `player`, `move_count` for every row including finished ones, and `cells` /
`macro` every 8 plies (`state_every`) and again at the end. A second check (`:110`) asserts the batch
engine offers no legal move in a finished game. Cost: 355 s + 320 s against the previous 305 s + 309 s.
`tests/test_tablebase.py` runs the 300-position solver comparison under both rules and asserts the two
disagree somewhere (119 of 300 do), runs the evaluator test under both, and adds the table/evaluator
mismatch refusal. `tests/test_rules_boundaries.py` (new) covers the cross-rule resume (`:72`) and the
legacy-config positive control (`:89`), the search cache (`:131`), `evaluate_rollout` (`:155`),
`relabel` (`:165`), `corpus_rule`'s four sources (`:191`), the surrogate (`:221`), the paired file
(`:231`), the draw sample (`:250`) and terminal-value backup in both searches (`:276`).

## 3. Design choices the spec left open

1. **The resume check is placed before `os.makedirs`, not merely before `config_resume_*.json`.** The
   spec said "before `config_resume_*.json` is written"; putting it at the very top means a refused
   invocation leaves the run directory byte-identical. The test asserts
   `sorted(os.listdir(run)) == ["config.json", "latest.pt"]` after the refusal, with `latest.pt`
   deliberately holding non-checkpoint bytes so a late refusal would fail with a torch error instead.

2. **`ValueError`, not `sys.exit`, for the resume.** `uttt/train2.py` is a library module called by tests
   and by `main(cfg)`; raising keeps it testable. Tools that are only ever entry points (`eval_worker`,
   `corpus_stats`, `book`, the I1 tools) use `sys.exit` with a message, matching the file they live in.

3. **Both remedies for the cache, not one.** The spec allowed `(sims, rule)` keying *or* asserting the
   cached object's rule. I did both: the key prevents the collision and the assert catches a caller who
   builds the dict themselves. The test poisons a `(4, "draw")` key with a count search and checks the
   assert fires.

4. **`corpus_rule`'s precedence and the scope of `--corpus_rule`.** Order is: game-file tag →
   `config.json` → `--corpus_rule` → refuse. The override is a last resort only, so it cannot silently
   contradict a run that *does* record its rule (the test asserts `corpus_rule(run, "draw") == "count"`
   when a legacy `config.json` is present). A tag that contradicts `config.json` is treated as a corrupt
   run and refused rather than resolved by preference.

5. **`games_rule` scans every game file, not just the newest.** Cheaper would be to stop at the first
   tagged file. Scanning all of them catches a directory holding two rules' files — which the resume
   refusal now makes impossible for a single run, but not for a hand-assembled directory. ~2 s cold on
   the 300-file `_e8` corpus, once per invocation, against tools that run for minutes.

6. **The buffer's rule is read from the run directory, not from the checkpoint.** `check_buffer_rule`
   (`probe_value.py:39-48`) calls `corpus_rule(os.path.dirname(buffer_path))`. The checkpoint does carry
   `cfg`, but `latest_full.pt` is multi-gigabyte and would have to be loaded twice. The two cannot
   disagree now that a cross-rule resume is refused; the docstring says so.

7. **`sample_draws` was factored out of `claim_draws`.** The sampling is the thing row 8 asks to change,
   and testing it through `claim_draws` would have required a synthetic corpus and inferences from
   summary statistics. As a function of `winners` it is tested directly: no-op at and below the cap,
   sorted and unique above it, reproducible under a seed, different under another seed, and never the
   earliest `max_games` (the test puts all 600 draws in the tail of a 1000-game window).

8. **`"draws"` was replaced, not supplemented.** The key becomes `"draws total"` + `"draws sampled"`. A
   single `"draws"` that sometimes means the total and sometimes the sample is the ambiguity row 8 is
   about. Consequence for the K1 parent pass now running on the 3060: its
   `runs/plan7/K1_parent_principles_deep8e8.json` has 16 369 draws, below the 20 000 cap, so **every
   number in it is unchanged** by this work — only the key names differ (`draws` →
   `draws total`/`draws sampled`, `mean boards each side` → `mean boards X`/`mean boards O`). Anything
   quoting that file by key needs the new names after a re-run.

9. **`timeline.json`'s field names were left alone.** M2 row 7 (the raw-policy-vs-generated-play
   mislabel) is the other agent's row and its remedy lands in `tools/empty_board.py`, which reads
   `first_top_share` / `first_top_move` out of existing `timeline.json` files. Renaming them would break
   that reader and pre-date nothing. I added a comment at the computation site and a `first_move_note` in
   `meta` saying which statistic it is, and nothing else.

10. **`ownership_grade` refuses a dataset of another rule although its labels are rule-independent.**
    Final board ownership is a property of the final macro grid, which both rules share. The refusal is
    nonetheless kept, for the reason M2 row 9 gave for `value_decomp` and `tablebase_grade`: rebuilding
    costs minutes and a refusal costs nothing, and a reading labelled `rule: count` should not be
    computed from a draw-rule dataset's sampled positions.

11. **`tag_path` was applied to `--out` for `timeline`, `ownership_grade`, `gdata`, `annotate` and
    `endgame_accuracy`,** following K1 design note 3 — including `timeline.py`'s `<run>/timeline.json`
    and `<run>/timeline.png`, which are per-run paths a second rule's reading would otherwise clobber.

12. **`timeline` and `book` check their inputs' rules up front.** Both originally refused only when the
    expensive work reached the mismatched object (timeline on the first checkpoint's `evaluate`, book
    after the whole build and after writing its JSON). Both checks moved to argument-handling time; the
    smoke shows `book3.json written: False`.

13. **The cross-check compares `cells` / `macro` every 8 plies rather than every ply.** The spec set the
    interval; I made it the `state_every` parameter of `cross_check` (default 8) and put it in the
    printed line, so the test states what it actually checked rather than leaving the reader to assume
    every ply.

14. **`decision.py` relabels the corpus rather than refusing a count corpus under draw.** Its targets are
    the stored winners, and `corpus_stats.relabel` is the established, exact count→draw re-reading; the
    impossible direction is refused. It prints the relabel count over the window before sampling.

## 4. Outputs, verbatim

### `tests/test_rules.py` (`UTTT_DEV=cuda:0`, exit 0, 690 s)

```
rule validation rejects typos; 'count' never renames a file, 'draw' always does
count rule reproduces 2000 pre-K1 games bit for bit (ended by line 1571, count 280, draw 149)
draw rule: 280 of 2000 games (14.0 %) turn from a count decision into a draw; the other 1720 are untouched
4-4 with one drawn board: a draw under both rules
5-3 with no macro line: an X count win under 'count', a draw under 'draw'
a macro line wins under both rules, 2-5 down on boards before the move
  count: solver agrees with brute force on 200 positions (<= 8 empties); 43 of them have a different value under the other rule  [3s]
  draw : solver agrees with brute force on 200 positions (<= 8 empties); 43 of them have a different value under the other rule  [9s]
  count: solve_children / solve_batch match the solver on 64 positions, in process and in a pool
  draw : solve_children / solve_batch match the solver on 64 positions, in process and in a pool
cross-engine check, 100000 games per rule:
  count: 100000 random games, both engines agree on the legal mask and, after every ply, on done / next_board / player / move_count (cells and macro every 8 plies and at the end), plus winner and end reason (line 77913, count 14800, draw 7287)  [355s]
  draw : 100000 random games, both engines agree on the legal mask and, after every ply, on done / next_board / player / move_count (cells and macro every 8 plies and at the end), plus winner and end reason (line 77913, count 0, draw 22087)  [320s]
ok
```

The line counts (77 913 line endings, 14 800 → 0 count endings) are identical to the pre-change run
recorded in `K1_design_notes.md`.

### `tests/test_rules_boundaries.py` (new, exit 0)

```
relabel: count -> draw turns exactly the count endings into draws; draw -> count is refused as needing a replay
principles.py samples the draws uniformly over the window, seeded and reproducible, and takes all of them unchanged when the window fits the cap
a corpus's rule comes from its game files' tag, else config.json (no key = count); an untagged orphan is refused unless --corpus_rule names it, and a tag contradicting config.json is a fault
book.py checks a paired match file's rule against its own (a file with no rule key is count)
a surrogate player is refused under draw and only under draw (it is a learned model of the count game)
a cross-rule resume is refused before config_resume_*.json, the games directory or any checkpoint is touched
evaluate's cache is keyed by (sims, rule); a count search cannot grade a draw set, and a set of the wrong rule is refused before any of it is read
evaluate_rollout is given its rule and refuses a set of another one (it used to infer the set's)
  uttt.search count: root value +0.941 after 16 simulations (want +1.0)
  uttt.mcts   count: root value +0.941 after 16 simulations (want +1.0)
  uttt.search draw : root value +0.000 after 16 simulations (want +0.0)
  uttt.mcts   draw : root value +0.000 after 16 simulations (want +0.0)
both searches back the terminal value up under the rule they were given: a count win for the mover, a draw under `draw`, from the same position
WARNING: this invocation's config differs from C:\Users\JOHNPE~1\AppData\Local\Temp\tmp8pwrorvr\r\config.json; the original is kept, this one is recorded as config_resume_*.json
attempt 1: a resumed run is a perturbed continuation, not a replay (PLAN6 §1 item 13)
a config.json with no rule key means count: draw refused, count resumed, and the resolved search configuration (gumbel_scale 1.0 included) is recorded in _provenance
ok
```

`0.941` is `n_sims / (n_sims + 1)` = 16/17 — the root's own raw value (0, from `UniformEvaluator`) mixed
with 16 terminal backups of +1.

### `tests/test_tablebase.py` (exit 0)

```
tables built in 0.2s: V (19683, 2, 27) 1.1 MB (the table is shared; only payoffs() reads the rule)
  count: values and optimal moves agree with the solver on 300 one-open-board positions (W/D/L for the mover 0.56/0.20/0.24)  [3s]
  draw : values and optimal moves agree with the solver on 300 one-open-board positions (W/D/L for the mover 0.35/0.60/0.05)  [3s]
119 of the 300 positions have a different exact value under the two rules
  count: evaluator wrapper overrides exactly the K=1 rows
  draw : evaluator wrapper overrides exactly the K=1 rows
a draw-rule evaluator refuses a count-rule table
ok
```

### `tests/test_endgame.py` (exit 0)

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

### `tests/test_exact.py`, `tests/test_rollout.py` (exit 0)

```
300 of 25113 positions labelled in 2.6s (115/s with 4 workers); exact value differs from z in 17.7% of them; exact W/D/L [np.float64(0.583), np.float64(0.143), np.float64(0.273)]
ok
```

```
bitboard rules agree with the reference engine under rule count over 300 random games (17765 plies)
bitboard rules agree with the reference engine under rule draw over 300 random games (17765 plies)
UCT 20000 playouts keeps the exact value on 40/40 solved endgames (<= 9 empties, 36 decisive)
reproducible for a seed; different seed differs: True
  suite    pairs  score   95% CI (pairs)    Elo  95% CI          as X   as O   | X share  draws |  pairs won/split/lost
  random      48  100.0%  [100.0, 100.0]  +1200 [+1200, +1200] 100.0% 100.0%    50.0%    0.0%     48 /   0 /   0
  all         48  100.0%  [100.0, 100.0]  +1200 [+1200, +1200] 100.0% 100.0%    50.0%    0.0%     48 /   0 /   0
  end reasons: line 96.9%  count 3.1%  equal 0.0%  |  mean length 41.2  |  rule count
[2s]
  1 games x 100000 playouts: 0.51s = 0.20 M playouts/s
 24 games x 100000 playouts: 0.81s = 2.96 M playouts/s
 96 games x 100000 playouts: 3.41s = 2.81 M playouts/s
ok
```

### `tests/test_openings.py`, `tests/test_selfplay_cont.py` (exit 0)

```
canonicalisation ok
build / save / load / subset ok
scripted openings ok
  suite    pairs  score   95% CI (pairs)    Elo  95% CI          as X   as O   | X share  draws |  pairs won/split/lost
  empty        1   50.0%       n/a        n/a                   0.0% 100.0%     0.0%    0.0%      0 /   1 /   0
  random      31   50.0%  [ 50.0,  50.0]     +0 [  +0,   +0]   45.2%  54.8%    45.2%    0.0%      0 /  31 /   0
  all         32   50.0%  [ 50.0,  50.0]     +0 [  +0,   +0]   43.8%  56.2%    43.8%    0.0%      0 /  32 /   0
  end reasons: line 100.0%  count 0.0%  equal 0.0%  |  mean length 46.6  |  rule count
same-player pairing ok
  suite    pairs  score   95% CI (pairs)    Elo  95% CI          as X   as O   | X share  draws |  pairs won/split/lost
  random      64   89.8%  [ 85.2,  94.5]   +379 [+303, +495]   87.5%  92.2%    47.7%    1.6%     52 /  12 /   0
  all         64   89.8%  [ 85.2,  94.5]   +379 [+303, +495]   87.5%  92.2%    47.7%    1.6%     52 /  12 /   0
  end reasons: line 92.2%  count 6.2%  equal 1.6%  |  mean length 45.1  |  rule count
bootstrap coverage 0.97
ok
```

```
finished games: {'games': 455, 'x_win': 0.499, 'o_win': 0.464, 'draw': 0.037, 'end_line': 0.895, 'end_count': 0.068, 'mean_len': 55.2, 'surprise': 0.008, 'cap_hit': 0.0, 'raw_kl': 0.0258, 'q_range': 0.0193, 'target_entropy': 2.8163, 'first_move_top': 23, 'first_move_top_share': 0.024, 'first_move_distinct': 81}
consistency ok: 455 games, 25113 positions, mean length 55.2
dup stats: {'distinct_frac': 0.962, 'exact_frac': 0.0, 'dup_mean_ply0': 455.0, 'dup_mean_ply2': 1.6, 'dup_mean_ply4': 1.0, 'dup_mean_ply8': 1.0, 'dup_mean_ply12': 1.0}
continuous self-play (uniform net): 4096 games x 64 steps in 80.3s -> 3266 positions/s, 50.7 finished games/s, 39.2 ms/sim
ok
```

### `tests/test_search_v2.py`, `tests/test_mcts.py`, `tests/test_hygiene.py` (exit 0)

```
puct   sims=  32 net=False selfplay=False: visits True  policy True  value True  action True
puct   sims= 200 net=False selfplay=False: visits True  policy True  value True  action True
puct   sims=  32 net=True  selfplay=False: visits True  policy True  value True  action True
puct   sims=  64 net=True  selfplay=True : visits True  policy True  value True  action True
gumbel sims=  32 net=False selfplay=False: visits True  policy True  value True  action True
gumbel sims= 200 net=False selfplay=False: visits True  policy True  value True  action True
gumbel sims=  32 net=True  selfplay=False: visits True  policy True  value True  action True
gumbel sims=  64 net=True  selfplay=True : visits True  policy True  value True  action True
v2 syncs per simulation: 1.0
v1 uniform: 4096 trees x 32 sims: 0.95s = 29.6 ms/sim
v2 uniform: 4096 trees x 32 sims: 0.90s = 28.1 ms/sim
v1 net: 4096 trees x 32 sims: 1.20s = 37.5 ms/sim
v2 net: 4096 trees x 32 sims: 1.06s = 33.2 ms/sim
ok
```

```
puct   win  : root value +0.94, target p(best) 0.95
puct   block: root value -0.18, target p(best) 0.90
gumbel win  : root value +0.46, target p(best) 1.00
gumbel block: root value -0.63, target p(best) 1.00
puct   UCT(32) as X vs random: +234 =0 -22 (91.4%) in 18.9s
gumbel UCT(32) as X vs random: +233 =1 -22 (91.2%) in 23.9s
puct   search: 4096 trees x 32 sims in 1.01s -> 31.6 ms/sim (uniform evaluator)
gumbel search: 4096 trees x 32 sims in 0.99s -> 31.0 ms/sim (uniform evaluator)
ok
```

```
symmetric hash ok / extra planes ok / ownership class maps ok / net configs / fused inference / loader ok / early-ply alpha ok / ok
```

### Tool smoke, `--rule count` on `runs/deep8_c1_300_e8/net_0300.pt` (cuda:0)

Full logs: `…/scratchpad/smoke/smoke.out` (849 lines) and `smoke2.out`. Everything read from the main
checkout by absolute path; everything written went to the scratchpad — the main checkout was verified
untouched. Mismatch fixtures: a hand-made 60-game **draw-tagged** corpus (`rule` array + `config.json`),
an **untagged orphan** copy of it, and a `"rule": "draw"` paired match file.

The `rule` field in every output written:

```
======== the rule field in every output written above ========
book.json              rule = 'count'
gdata.npz              rule = 'count'
ownership.json         rule = 'count'
paired.json            rule = 'count'
principles.json        rule = 'count'
timeline.json          rule = 'count'  run_rule = 'count'  corpus_rule = 'count'
eval_full.jsonl        rule = 'count'
ea.npz                 rule = 'count'
```

Per-tool rule lines:

```
corpus_stats  4980 games from 1 files; generated under rule count, read under rule count
decision      rule count (corpus generated under count; 0 of the window's 4980 outcomes relabelled from a count decision to a draw before sampling)
surprise      251 positions, 16 sims, rule count. Search move != raw argmax in 18.3% of positions; mean |search value - raw value| = 0.192
probe_value   3894 distinct positions, plies 6-60, from .../latest_full.pt; rule count
ownership     .../probe_data_deep8late.npz: 60000 positions, test split 10000; open boards in test: 73330 of 90000; rule count
timeline      .../run_e8: 1 checkpoints; 2000 held-out positions from 1 files of .../deep8_c1_300_e8; endgame set endgame_v2_dev (3000); read under rule count (the run trained under count)
endgame_acc   40 distinct positions with 6-10 empties in open boards; rule count
eval_worker   evaluator: suite openings_v1.npz (7 openings), anchors ['deep8_c1_300_e8_net_0300'], 8 sims, endgame set endgame_v2_dev.npz, rule count (run trains under count), device NVIDIA GeForce RTX 3090
openings      paired suite openings_v1 (7 openings, 14 games) under rule count: ... end reasons: line 100.0%  count 0.0%  equal 0.0%  |  rule count
book          # Opening book: .../net_0300.pt at 8 sims, depth 1, top-1 replies per node, rule count
endgame eval  .../net_0300.pt on endgame_v2_dev under rule count  [2s]   (raw net 91.7 WDL, rollout UCT 200 playouts 89.5 optimal — evaluate_rollout with the explicit rule)
principles    "rule": "count", "corpus rule": "count", "draws total": 867, "draws sampled": 40, "mean boards X"/"mean boards O" present
annotate      # Puzzle positions from `suites/puzzles_v2_dev.npz` (hard: 5; net runs/deep10_c1_300/net_0300.pt, search 64 sims)
gdata         wrote .../gdata.npz: 200 positions  [4s]
```

Every refusal, verbatim:

```
corpus_stats (draw corpus under count)
  cannot read a draw-rule corpus under count: the stored outcome fields do not carry the board count, so
  the count-decided games cannot be picked out of the draws. The information is not lost — every move is stored — but
  recovering it requires replaying the saved moves (not implemented); read the corpus under its own rule instead

corpus_stats (orphan with no config.json and no tag)
  .../orphan_corpus has no config.json and none of its game files carries a rule tag, so the rule it was
  generated under cannot be established: pass --corpus_rule count|draw to say what it is (pre-K1 corpora are
  count, but an orphaned directory is not evidence of that)
  -> with --corpus_rule draw it reads: "60 games from 1 files; generated under rule draw, read under rule draw"
  -> the tagged copy needs no config.json at all: "generated under rule draw, read under rule draw"

decision (draw corpus under count)
  cannot read a draw-rule corpus under count: ... requires replaying the saved moves (not implemented); ...

probe_value / surprise / endgame_accuracy (count buffer under draw)
  .../latest_full.pt holds positions from a count-rule run and --rule is draw: its values, ownership and
  margin targets were decided under count. Read it under --rule count, or point --buffer at a draw-rule run.

timeline (--rule draw, count set)
  endgame set .../endgame_v2_dev.npz was solved under rule 'count' and --rule is 'draw': build a draw-rule
  set with tools/endgame.py build --rule draw.

timeline (--rule count, draw corpus)
  .../draw_corpus was generated under rule 'draw' and --rule is 'count': the held-out policy statistics
  would then be read off another rule's positions. Point --corpus at a count-rule run.

endgame.py eval (--rule draw, count set)
  ValueError: endgame set endgame_v2_dev was solved under rule 'count'; cannot evaluate under 'draw'

eval_worker (--rule draw, count set) — raised in __init__, before any match
  endgame set .../endgame_v2_dev.npz was solved under rule 'count' and --rule is 'draw': its exact labels
  would be wrong. Build a draw-rule set with tools/endgame.py build --rule draw, or pass --set ''.

openings.py match (surrogate under --rule draw)
  ValueError: a surrogate player is a learned model of the count-rule game and cannot be played under
  rule 'draw': distil a draw-rule surrogate first, or play it under --rule count

book.py (draw paired file, count book)
  .../paired_draw.json holds games played under rule 'draw' and this book is built under 'count':
  rerun tools/openings.py match --rule count, or build the book under draw
  book3.json written: False (False = the refusal came before the build)

gdata.py (draw corpus under --rule count)
  .../draw_corpus was generated under rule 'draw' and --rule is 'count': the teacher would label another
  rule's positions. Point --corpus at a draw-rule run.

annotate.py (--rule draw, count puzzle file)
  .../puzzles_v2_dev.npz was built under rule 'count' and --rule is 'draw': its exact values and child
  tables are count-rule. Read it under --rule count, or rebuild it with tools/puzzles.py --rule draw.
```

## 5. Not done, and why

- **No training run** — as instructed. The one `train2.main` call in the new test is `--iters 0` on a
  1-block/8-filter net: it exercises the resume gate, the `_provenance` write and the DONE file, and
  takes seconds.
- **`timeline.json`'s field names and the generated-share line are untouched** — M2 row 7 is the other
  agent's row, and renaming would break `empty_board.py`'s reader and every existing `timeline.json`.
  See choice 9.
- **Rows 3, 4, 7, 15, 16 and their three files** — the other agent's.
- **`uttt/surrogate.py`, `tools/distill.py`, `match.py`, `ladder.py`, `calibrate.py`, `gstudy.py`,
  `analyze_opening.py`, `play.py`, `web/server.py`, `uttt/train.py`** stay count-only, as K1 design
  note 6 records. Only `openings.py` needed the new closure, because it was the one path that could put
  a count-only surrogate inside a draw-rule game.
- **`book.py`'s `audit()` still builds `UTTT()` at the default rule.** It replays opening lines and
  checks legality and frame consistency, both rule-independent, and never reaches a terminal. Left as
  found rather than widened outside my rows.
- **The `assert` in `evaluate` is an `assert`**, so `python -O` would strip it. The `(sims, rule)` key is
  the load-bearing fix; the assert is the belt. Nothing in this repository runs under `-O`.
- **`corpus_rule` is uncached.** Every caller invokes it once per process, so the ~2 s cold scan is paid
  once; an `lru_cache` would add a staleness mode for no measured gain.
