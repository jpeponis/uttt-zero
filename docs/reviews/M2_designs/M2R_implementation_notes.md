# M2's rebuttal round — implementation notes (written 2026-09-13 by the implementing agent after M2's rebuttal round; verbatim)

*M2's rebuttal (`REBUTTAL.md`, sections (c), (d) and (e)) found five gaps left by the M2 merges: the
cross-rule resume refusal keyed on a file that need not exist, a legacy search cache ignored rather than
rejected, `tools/frontier.py`'s recorded move coming from a second search, `games_rule()` letting one
tagged file vouch for a directory of untagged ones, and K1's launcher chain not stopping on failure. They
were closed by an Opus `directed` agent in an isolated worktree (commit `6e15a12`, branched from
`465e764`), which was asked to confirm every line-cited claim in the code before changing anything and to
say so rather than "fix" any that were wrong. None was wrong. K1 has still not been launched and no
training was run. What follows is that agent's own final report, verbatim: the files changed, each of the
five items with its premise and remedy, the design choices it made where the brief left room, the test and
smoke output as it came out, and what it deliberately did not do.*

---

## 1. Files changed

All under `C:\Users\John Peponis\Desktop\uttt-zero\.claude\worktrees\agent-aa4268d70e7b4cd7d\`, commit `6e15a12` on `worktree-agent-aa4268d70e7b4cd7d` (worktree fast-forwarded to `465e764` first, as instructed — it had started at `40b7864`):

- `uttt/train2.py`
- `uttt/endgame.py`
- `tools/frontier.py`
- `tools/corpus_stats.py`
- `runs/queue14.sh`, `runs/eval_run_k1.sh`
- `tests/test_rules_boundaries.py`, `tests/test_endgame.py`

Nothing else touched. No training run. No writes into the main checkout (`runs/`, `suites/` and the net were read by absolute path; all outputs went to the scratchpad).

## 2. The five items

**1. `train2.py` — cross-rule resume. Premise confirmed.** `uttt/train2.py:257` gates on `os.path.exists(cfg_path)`; the restore at `:338-340` is reached regardless. Checkpoints carry the config under the key `"cfg"` (`:419` and `:423`, both `asdict(cfg)`).

Added `_checkpoint_rule()` beside `_atomic_save`, and a gate before `os.makedirs` (so before `config.json`/`config_resume_*.json`): a directory with a checkpoint and no `config.json` is refused under either rule with instructions; otherwise the checkpoint's recorded rule (missing → `count`) must equal `cfg.rule`. A second, free check at the restore site tests the file actually being restored, before `net.load_state_dict`.

**2. `endgame.py` — cache and graded moves. Premise confirmed.** `uttt/endgame.py:291` is `search_cache.get((s, rule))`; an integer key returns `None`, which is indistinguishable from a miss, and the new tuple key is then *added alongside* the stale one. `evaluate` now raises on any key that is not `(int, str)`. `_row` records `per["move"]` **after** the aggregation loop — inside it, `move` would have been averaged and cluster-bootstrapped.

**3. `frontier.py` — the recorded move. Premise confirmed.** `tools/frontier.py:357-364`: `mv = search_moves(...)` was a second search, `bad` was only warned about, and `position_rows(..., mv, per_reg)` paired that move with the first search's regret. Now the move is `r["_per"]["move"]`; `search_moves` and its `uttt.search` import are deleted; `regret == exact_root_value − child_values[move]` is asserted on complete rows inside `position_rows`. `meta["chosen_move_regret_mismatches"]` stays as a constant `0` plus a `_note` key saying it is now by construction.

**4. `corpus_stats.py` — untagged files. Premise confirmed.** `tools/corpus_stats.py:43-52` only ever added to `tags` when `"rule" in z.files`. Now tagged and untagged files are counted separately; a mixed directory exits naming the untagged files unless `config.json` records the same rule as the tag. Shared `_config_rule()` helper; `corpus_rule` uses it instead of re-reading the file.

**5. The launcher. All four sub-claims confirmed.** `runs/queue14.sh:55-56` (no `||`, `bash eval_run_k1.sh` runs unconditionally), `:54` (`&` with no `$!`), `runs/eval_run_k1.sh:18` (`N=$(ls runs/$R/net_*.pt | sort | tail -1)`), and no `pipefail`/status checks anywhere. Also confirmed the worker never exits on its own: `tools/eval_worker.py:144-150` polls until `runs/$R/DONE` exists, so the old bare `wait` would have hung forever after a failed run.

`queue14.sh` now records `WORKER=$!`, and both `run_train` and `eval_run_k1.sh` failures echo, `stop_worker`, and `exit 1`. `eval_run_k1.sh` requires `DONE`, `net_0300.pt` and the parent checkpoint, and each command is followed by `record $? "<what>"`, which writes `!!! FAILED (exit N): …` into `analysis.out` and increments a counter; the script exits 1 if any failed. **Every training flag is byte-identical** — diffed against `HEAD`, the only difference is the appended `\`.

## 3. Design choices

1. **The ambiguity refusal does not read the checkpoint.** A directory with a checkpoint and no `config.json` is refused *before* `torch.load`, under either rule. The complaint is the missing provenance, not a mismatch — the checkpoint records only what the *weights* were trained under, not what the `games/` directory and buffer beside them are — and refusing first avoids `torch.load(weights_only=False)` on a file of unknown origin.
2. **The early probe reads `latest.pt`, not `latest_full.pt`** (measured 19.7 MB vs 568 MB on `deep8_c1_300_e8`). `latest.pt` is written every iteration and `latest_full.pt` every tenth, so it is also the more recent record. The gap this leaves — a foreign `latest_full.pt` beside a native `latest.pt`, when restore prefers the former — is closed by the second check at the restore site, which is free because the file is already in memory. That check fires after `config_resume_*.json` is written; the pathological case did not seem worth a duplicated 568 MB load on every legitimate resume.
3. **`per["move"]` is added after the aggregation loop, not before.** Inside it, `d["move"] = mean(move index)` and a 2000-sample bootstrap of move indices would both have been computed. The test asserts `"move" not in r and "move_ci" not in r`.
4. **`chosen_move_regret_mismatches` kept as `0`** rather than removed, so a reader of the older `J4_frontier.json` files does not see the key appear and vanish; a `_note` key says it is now constant by construction.
5. **`games_rule` reads `config.json` itself** (via `_config_rule`) instead of taking the rule as an argument, so the guarantee holds for any caller, not just `corpus_rule`. `--corpus_rule` deliberately cannot wave a mixed directory through — it is the escape hatch for a directory with *no* evidence, not for one with contradictory evidence.
6. **`record $? "<what>"` rather than `set -e`.** A failed reading should not abort the ones after it — item 3 is independent of item 4 — but it must not look like an absent one either. The failures are named in `analysis.out`, counted, summarised (`=== N of 9 readings failed`), and returned as the script's exit status. The `{ … } > analysis.out` brace group does not fork, so `fail` survives it.
7. **`queue14.sh` also propagates the worker's own exit status** (`exit $ws`), which the reviewer did not ask for. A worker that died at hour 3 of 22 silently truncates the E7 curve.

## 4. Outputs, verbatim

`tests/test_rules_boundaries.py`:

```
relabel: count -> draw turns exactly the count endings into draws; draw -> count is refused as needing a replay
principles.py samples the draws uniformly over the window, seeded and reproducible, and takes all of them unchanged when the window fits the cap
a corpus's rule comes from its game files' tag, else config.json (no key = count); an untagged orphan is refused unless --corpus_rule names it, and a tag contradicting config.json is a fault
a directory mixing tagged and untagged game files is refused by name unless a config.json agreeing with the tag vouches for the untagged ones; a uniformly tagged one still identifies itself
book.py checks a paired match file's rule against its own (a file with no rule key is count)
a surrogate player is refused under draw and only under draw (it is a learned model of the count game)
a cross-rule resume is refused before config_resume_*.json, the games directory or any checkpoint is touched
WARNING: this invocation's config differs from C:\Users\JOHNPE~1\AppData\Local\Temp\tmplabyqpg6\r\config.json; the original is kept, this one is recorded as config_resume_*.json
attempt 1: a resumed run is a perturbed continuation, not a replay (PLAN6 §1 item 13)
a checkpoint is gated on its own recorded rule: an orphan without config.json is refused under either rule, a copied-in checkpoint of the other rule is refused beside an agreeing config.json, a pre-K1 checkpoint counts as count, and an agreeing one passes
evaluate's cache is keyed by (sims, rule); a count search cannot grade a draw set, a cache keyed by sims alone is refused rather than silently ignored, and a set of the wrong rule is refused before any of it is read
evaluate_rollout is given its rule and refuses a set of another one (it used to infer the set's)
  uttt.search count: root value +0.941 after 16 simulations (want +1.0)
  uttt.mcts   count: root value +0.941 after 16 simulations (want +1.0)
  uttt.search draw : root value +0.000 after 16 simulations (want +0.0)
  uttt.mcts   draw : root value +0.000 after 16 simulations (want +0.0)
both searches back the terminal value up under the rule they were given: a count win for the mover, a draw under `draw`, from the same position
WARNING: this invocation's config differs from C:\Users\JOHNPE~1\AppData\Local\Temp\tmp45kcsu4p\r\config.json; the original is kept, this one is recorded as config_resume_*.json
attempt 1: a resumed run is a perturbed continuation, not a replay (PLAN6 §1 item 13)
a config.json with no rule key means count: draw refused, count resumed, and the resolved search configuration (gumbel_scale 1.0 included) is recorded in _provenance
ok
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
build / save / load / evaluate ok; every graded row carries the moves its regret was computed from
ok
```

`tests/test_solver_bounded.py`:

```
500 positions (<= 16 empties): bounded == unbounded in value and node count; median 5516 nodes, max 1882919; unbounded 1.31s, bounded 1.41s (+7.1 %)
draw rule: bounded == unbounded in value and node count on 500 positions; 90 of them have a different value than under the count rule
rule count: completed and agreed with the unbounded value: 23/500 at a budget of 10, 113/500 at a budget of 1000, 457/500 at a budget of 100000
rule draw: completed and agreed with the unbounded value: 23/500 at a budget of 10, 97/500 at a budget of 1000, 447/500 at a budget of 100000
budget 10: incomplete on 477/500 positions — exactly those needing more than 10 nodes, value None on every one of them
solve_children_bounded == solve_children in root value and all 81 child values on 250 positions under both rules (40 differ in root value between the rules); median 12086 nodes, max 6231875
budget = half of what the enumeration needs: incomplete on all 249 positions that need >= 2 nodes, (None, None, used <= budget, False) on every one
pooled (2 workers, rule draw): identical root value, child table and node count to the in-process result on 100 positions
ok [25.4s]
```

Frontier smoke, the specified command (`--plies 60 61 --per_ply 8 --max_nodes 1e6 --sims 64`, `--device cuda:0`, net and run from the main checkout by absolute path, output to the scratchpad):

```
C:/Users/John Peponis/Desktop/uttt-zero/runs/deep8_c1_300_e8: 98581 games in 20 files (games_0280.npz..games_0299.npz); grading C:/Users/John Peponis/Desktop/uttt-zero/runs/deep8_c1_300_e8/net_0300.pt at 64 sims on cuda:0
plies 60-61, 8 positions per ply, budget 1,000,000 nodes per position, 4 solver processes, rule count

 ply   alive sampled          complete coverage   nodes med   nodes p90          optimal %             regret  incompl      s
(complete coverage = every legal child's exact value obtained inside the shared budget — stricter than proving the root's value)
(coverage: conditional on alive, 95 % Wilson | nodes, optimal, regret: conditional on complete; optimal Wilson, regret cluster bootstrap)
  60    7850       8  100.0 % [ 67.6,100.0] (8)           8         899 100.0 [ 67.6,100.0]        0.000 [n/a]        0    5.5
  61    5119       8  100.0 % [ 67.6,100.0] (8)           5         112 100.0 [ 67.6,100.0]        0.000 [n/a]        0    6.9

wrote .../J4_smoke.json and .../J4_smoke_positions.npz (16 positions)
```

That smoke has zero regret everywhere and no incomplete rows, so it exercises the new assertion only degenerately. Three further checks, from the scratchpad:

```
16 positions, 16 complete
regret == exact_root_value - child_values[move] on every complete row: True
every recorded move is legal (child value != ILLEGAL): True
incomplete rows: move -1, optimal -1, regret NaN, child row all -3: True
regret values: [0.0]  non-zero rows: 0
optimal flag agrees with regret == 0: True
meta['chosen_move_regret_mismatches'] = 0
meta note present: True
```

A weaker search at earlier plies, to reach the incomplete-row path (`--plies 44 46 --per_ply 40 --sims 2`):

```
  44   95087      40  37.5 % [ 24.2, 53.0] (15)     118,586     725,765 100.0 [ 79.6,100.0]        0.000 [n/a]       25    3.4
  45   91724      40  50.0 % [ 35.2, 64.8] (20)      16,150     191,992 100.0 [ 83.9,100.0]        0.000 [n/a]       20    3.0
  46   90214      40  47.5 % [ 32.9, 62.5] (19)       2,338     432,884 100.0 [ 83.2,100.0]        0.000 [n/a]       21    3.2
```

And the assertion itself, fed the real 54 graded rows and then the same rows with one move swapped for a legal move of a different exact value:

```
the grader's own moves and regrets, 54 complete rows: accepted
swapping row 1's move 9 -> 13 (both legal; child values 1 and 0)
assertion fired: ply 60: the recorded move and regret are not each other's (1 rows)
```

The stubbed launcher harness (the real `eval_run_k1.sh` with its `cd` retargeted and `$P` stubbed; the guards, `record`, the brace group and the final exit are the file under test verbatim):

```
--- (1) DONE present, net_0300.pt absent
runs/fake/net_0300.pt is missing: K1's readings are of the final checkpoint of a 300-iteration run, not of the latest one present
exit=1
--- (2) DONE and net_0300.pt present, every reading succeeds
wrote runs/fake/analysis.out
exit=0
last line of analysis.out: === 0 of 9 readings failed
--- (3) the same, with two readings failing (the endgame sets are renamed so the stub trips on them)
eval_run_k1: 2 reading(s) FAILED; see runs/fake/analysis.out (grep '!!! FAILED')
exit=1
recorded in analysis.out:
!!! FAILED (exit 3): item 3: the draw net on endgame_v2_dev under count
!!! FAILED (exit 3): item 3: the draw net on endgame_v1 under count
=== 2 of 9 readings failed
--- (4) a run that never finished is refused even with a full set of checkpoints
runs/fake/DONE is missing: the run has not finished, and a partial run is not a K1 reading
exit=1
```

`bash -n`: `queue14.sh: syntax ok` / `eval_run_k1.sh: syntax ok`. Also run as regression cover, both `ok`: `tests/test_hygiene.py`, `tests/test_rng_hygiene.py`; and `tools/endgame.py eval … --set endgame_v2_dev_draw.npz --rule draw --sims 32 --device cuda:0`, which exercises `evaluate` + `breakdown` + both report formatters on the real K1 draw set (raw net 79.0 % WDL, search 32 regret 0.014).

## 5. Not done, and why

- **No premise was refuted.** All five, including the four sub-claims in (d), are as the reviewer described at `465e764`. One thing I checked and found *fine*: `eval_run_k1.sh:31-32` and `:34-35` pass the same `--out` for the count and draw matches, which looks like the draw match overwriting the count one — it does not, because `tools/openings.py:119` runs the path through `tag_path(a.out, a.rule)`, which leaves `count` untagged and appends `_draw`. Left alone.
- **The assertion in item 3 catches a move/regret mismatch only when the two moves have different exact values.** A swap between two equally-valued moves satisfies `regret == exact_root_value − child_values[move]` and is accepted. That is the identity the table claims and the one you asked for; I mention it because my first attempt at breaking the assertion picked an equal-valued move and was correctly accepted.
- **No repo test file was added for `frontier.position_rows`.** Item 6 named the files I may touch and no frontier test file exists; the adversarial check above lives in the scratchpad (`check_assertion.py`, `check_positions.py`, `test_eval_run_k1.sh`) rather than in `tests/`. Say the word and I will add it as `tests/test_frontier.py`.
- **`docs/reviews/M2_designs/J3J4_M2_implementation_notes.md:35` is now stale** — it documents the second search and the mismatch counter as the design. `docs/` was out of scope, so I left it; it will need a line when the M2 notes are next revised.
- **Rebuttal sections (a), (b) and the closing row-12 point are untouched** — decision rules, thresholds and the adjudication's wording are PLAN7/KNOWLEDGE work, explicitly excluded.
- **Nothing pushed; no training run; `cuda:1` never used.**
