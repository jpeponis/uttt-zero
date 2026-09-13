# K1 — the rule switch: design notes for M2 (written 2026-09-12 by the implementing agent; verbatim, lightly formatted)

*PLAN7 §5's engineering — `rule ∈ {count, draw}` threaded through the engine and tools — was
implemented by an Opus `directed` agent in an isolated worktree and merged to `main`. These are its
notes: what changed, the tests as they printed, the end-to-end smoke under `--rule draw`, and the
eight design choices it made where PLAN7 §5 left the choice open. The numbered items and the
"not threaded" list are what M2 is asked to adjudicate before K1 launches.*

## Files changed

**New:** `uttt/rules.py` (37 lines: `RULES = ("count", "draw")`, `check_rule()` — a typo must not
silently mean count — and `tag_path()`: `x.npz` → `x_draw.npz`, `count` never renames);
`tests/test_rules.py` (255 lines); `tests/fixtures/count_engine_2000.npz` (8.7 kB: winners, end
reasons, final macro and lengths of 2 000 seeded random games, recorded from the **pre-edit** engine).

**Engine:** `uttt/game.py` (`UTTT(rule="count")`, `rule` in `__slots__` and `clone()`; the terminal
branch gains `and self.rule == "count"`); `uttt/batch.py` (`BatchUTTT(n, device, rule)`,
`step_state(..., rule)`; `count_winner` becomes zeros under draw, so `reason` falls through to 3);
`uttt/solver.py` (`solve / solve_children / solve_batch(..., rule)`; the njit `_negamax` takes a
`draw_rule` boolean — one Numba specialisation per rule); `uttt/exact.py` (`ExactLabeler(..., rule)`;
the pool call is `partial(solve_batch, rule=...)`); `uttt/tablebase.py` (`K1Table(device, rule)`,
`TablebaseEvaluator(base, table, rule)`; the rule enters **only** through `payoffs()`'s outcome map, so
the 1.06 M-entry table is shared and `_build()` is untouched; a table / evaluator mismatch raises);
`uttt/search.py`, `uttt/mcts.py` (the rule stored on the object and passed to `step_state`: the tree
expands under the rule); `uttt/arena.py`, `uttt/openings.py` (`PairedResult.rule`; `summarize()` emits
`"rule"`; `build_suite` untouched — the suite is opening positions); `uttt/selfplay.py`,
`uttt/selfplay_cont.py` (**lines 158–169, the margin / ownership labels, left exactly as they were**);
`uttt/rollout.py` (the independent Numba UCT anchor: `draw_rule` through `_apply` / `_uct_search` /
`_search_batch`); `uttt/endgame.py` (`build_set` records `meta["rule"]`; pre-K1 sets read back as
`count`; `evaluate` **refuses** a rule the set was not solved under); `uttt/train2.py`
(`TrainConfig.rule` → `--rule`; threaded to self-play, the sims-schedule rebuild, `ExactLabeler`,
`EvalKit`; recorded in `config.json` as `rule` and in `_provenance.rule`; refuses an endgame set of the
wrong rule; prints a one-line warning that the anchors are count-trained).

**Tools** (each gains `--rule`, default `count`; every JSON / npz written gains a `"rule"` field;
cached datasets get the `_draw` name tag): `openings.py` (`match`, incl. the tablebase wrapper and the
rollout anchor), `eval_worker.py` (prints the run's *training* rule from `config.json` beside the
evaluation rule; writes `eval_full_draw.jsonl`), `endgame.py` (`build`, `eval`), `corpus_stats.py`,
`principles.py`, `atlas.py`, `book.py`, `freemove.py`, `value_decomp.py`, `probe.py`, `puzzles.py`,
`tablebase_grade.py`. Also `.gitignore` (`probes*.json`, `value_decomp*.{json,png}`,
`eval_full_*.jsonl`, so rule-tagged outputs stay tracked) and `tests/test_rollout.py` (one white-box
call to the private `_apply` that the njit signature change broke — now parametrised, runs under both
rules).

## Tests, verbatim

`tests/test_rules.py` — exit 0, ≈ 630 s:

```
rule validation rejects typos; 'count' never renames a file, 'draw' always does
count rule reproduces 2000 pre-K1 games bit for bit (ended by line 1571, count 280, draw 149)
draw rule: 280 of 2000 games (14.0 %) turn from a count decision into a draw; the other 1720 are untouched
4-4 with one drawn board: a draw under both rules
5-3 with no macro line: an X count win under 'count', a draw under 'draw'
a macro line wins under both rules, 2-5 down on boards before the move
  count: solver agrees with brute force on 200 positions (<= 8 empties); 43 of them have a different value under the other rule  [3s]
  draw : solver agrees with brute force on 200 positions (<= 8 empties); 43 of them have a different value under the other rule  [7s]
  count: solve_children / solve_batch match the solver on 64 positions, in process and in a pool
  draw : solve_children / solve_batch match the solver on 64 positions, in process and in a pool
cross-engine check, 100000 games per rule:
  count: 100000 random games, both engines agree on the legal mask, winner, end reason and final macro (line 77913, count 14800, draw 7287)  [305s]
  draw : 100000 random games, both engines agree on the legal mask, winner, end reason and final macro (line 77913, count 0, draw 22087)  [309s]
ok
```

The identical `line 77913` in both rows is the point: the same seed plays the same 100 000 games under
either rule (a game ends at the same ply either way), so the two runs differ *only* in the verdict —
all 14 800 count endings become draws and nothing else moves.

The seven required suites (`UTTT_DEV=cuda:1`), all exit 0: `test_game` 8.6 s, `test_batch` 18.7 s,
`test_solver` 1.6 s, `test_exact` 23.4 s, `test_tablebase` 6.0 s, `test_endgame` 13.6 s, `test_openings`
14.6 s (its report line now ends `| rule count`). Also exit 0: `test_rollout` 19.1 s (both rules),
`test_selfplay_cont` 75.2 s, `test_mcts` 89.1 s, `test_search_v2` 49.3 s, `test_search_graph` 44.0 s,
`test_hygiene` 3.8 s, `test_rng_hygiene` 58.8 s, `test_concepts`, `test_infer`, `test_symmetry_eval`,
`test_book`, `test_surrogate`.

**One failure, pre-existing:** `tests/test_symmetry.py::test_fused_fp16_graph` dies with
`cudaErrorStreamCaptureUnsupported` inside `torch.cuda.graph` capture (`batch.py:239`, `torch.stack` in
`encode`). The pristine `HEAD` tree, exported with `git archive` and run in the scratchpad, **fails
identically on unmodified code** — a torch 2.13 / driver issue on this machine, not a K1 regression. Its
first five checks (including "engine commutes with D4 … line and count endings seen") pass.

## End-to-end smoke under `--rule draw` (3060, synthetic 1 200-game count corpus in the scratchpad)

`corpus_stats` (relabelled 192 / 1200 = 16.0 %); `endgame build` → `eg_draw.npz` beside `eg.npz`, and
`eval` (the mismatch correctly refused); `openings match --rule draw --a_tb` → `paired_draw.json`;
`probe build` → `probe_draw.npz`; `tablebase_grade`; `principles` → `principles_draw.json` (a count read
of a draw dataset correctly refused); `value_decomp`; `puzzles`; `freemove`; `atlas` → `atlas_draw.json`;
`book` → `book_draw.{json,md}`. One 82-step `train2 --rule draw` iteration (128 games, 8 sims, 33 s):
`end_count 0.0`, 64 exact labels through the pool, `config.json` carrying `rule: draw` in both places;
`--rule Draw` rejected; a count-rule endgame set rejected.

## Design choices M2 is asked to adjudicate

1. **`corpus_stats` / `principles` relabel rather than replay.** A stored corpus has no final macro, so
   re-reading it under another rule cannot be done by replaying cheaply at scale. It does not need to be:
   `done` is rule-independent, so a count-rule game read under `draw` is exactly "reason 2 → reason 3,
   winner → 0". That is PLAN7 §5 reading 0, it is exact, and
   `test_draw_relabels_exactly_the_count_endings` checks the arithmetic against a real re-run of the
   engine. The reverse (a draw corpus read under `count`) is *not* derivable and the tool exits with
   that message rather than guessing.
2. **Where the training rule may be read.** `corpus_stats` / `principles` read `<run>/config.json`'s
   `rule` to know what the corpus *is*; `eval_worker` reads it only to print beside `--rule`. The
   evaluation rule is never taken from it. A missing key ⇒ `"count"`, true of every pre-K1 run.
3. **The file-name tag fires only for non-count rules.** `tag_path("x.npz", "count") == "x.npz"`, so no
   existing path, suite name or tracked artifact moves; a draw run writes beside it. Applied to a
   user-given `--out` too (and printed) — mildly surprising, but the only way "caches cannot be mixed"
   actually holds.
4. **`uttt/rollout.py` was threaded though not on the list** — six mechanical njit edits. Without them
   `openings.py match --rule draw --b rollout` would run a count-rule anchor inside a draw-rule game,
   exactly the silent inference PLAN7 §7e row 34 forbids.
5. **`step_state` validates its `rule` on every call.** It is a public pure function called directly by
   `search.py`, `mcts.py` and `surrogate.py`, so it defends itself; one tuple-membership test per
   batched step against ≈ 30 ms of GPU work. The count path is otherwise untouched — the fixture proves
   it.
6. **Not threaded, and why.** `uttt/surrogate.py` (and so `tools/distill.py`) still calls `step_state`
   with the default — the surrogate is a learned model of the count-rule game. Same for `tools/match.py`,
   `ladder.py`, `calibrate.py`, `decision.py`, `surprise.py`, `gdata.py`, `gstudy.py`,
   `analyze_opening.py`, `endgame_accuracy.py`, `annotate.py`, `ownership_grade.py`, `probe_value.py`,
   `timeline.py`, `play.py`, `web/server.py` and the v1 `uttt/train.py`: all keep count by default and
   behave exactly as before. If the K1 readings need any of them, `gdata.py` (it calls `solve_batch`),
   `annotate.py` and `endgame_accuracy.py` are the three that decide a terminal value and would need the
   same two-line treatment. **[Adjudicator's note: PLAN7 §5 item 2 runs "the I1 tool set" on the draw
   net under the draw rule, and that set includes `decision.py`, `surprise.py`, `ownership_grade.py`,
   `timeline.py` and `probe_value.py` — these must be threaded before K1's readings, not before its
   launch. Listed in PLAN7 §5 as a pre-reading item.]**
7. **`TrainConfig` gained a key**, so resuming a pre-K1 run prints the "config differs" WARNING and
   writes a `config_resume_*.json` beside the original — the existing mechanism, non-destructive, once
   per resumed legacy run.
8. **`puzzles.py`'s `tiebreak_conversion` motif is unchanged** (`end_reason in ("count", "draw")`). Its
   meaning is "the game ended on the line-free terminal", well defined under both rules; under `draw` it
   fires on every such ending rather than on the count-decided subset. A comment was added rather than
   renaming a label that appears in existing suites.
