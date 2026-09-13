# J3 / J4 — design notes for M2 (written 2026-09-12 by the implementing agent; verbatim, lightly formatted)

*PLAN7 §4 J3 and J4 were implemented by an Opus `directed` agent in an isolated worktree and merged to
`main` after the solver change was read. Neither J3 nor J4 has been run for real; they are designs for
M2 to review before execution. These are the agent's own notes on every choice PLAN7 §4 left open,
followed by the smoke-test outputs. The numbered items are what M2 is asked to adjudicate.*

## Files

- `uttt/solver.py` — `ABORT = -3`, `_negamax_bounded` (a copy of `_negamax` with a budget check and an
  unwinding abort), `solve_bounded(cells, macro, next_board, player, max_nodes) -> (value, nodes,
  complete)`, `solve_children_bounded(args)` (the bounded twin of `solve_children`, sited here so pool
  workers import it by name). `solve()` and `solve_children()` are byte-identical to before.
- `tests/test_solver_bounded.py` — three properties on one shared set of 500 random positions with
  ≤ 16 empties.
- `tools/frontier.py` — J4.
- `tools/empty_board.py` — J3.

## Test results (verbatim)

```
500 positions (<= 16 empties): bounded == unbounded in value and node count; median 5516 nodes, max 1882919; unbounded 1.33s, bounded 1.36s (+2.5 %)
completed and agreed with the unbounded value: 23/500 at a budget of 10, 113/500 at a budget of 1000, 457/500 at a budget of 100000
budget 10: incomplete on 477/500 positions — exactly those needing more than 10 nodes, value None on every one of them
ok [5.2s]
```

The budget-10 assertion is two-sided: `ok == (unbounded_nodes <= 10)` on every position, `value is
None` and `nodes == 10` on every incomplete one. The middle line is the property that matters most — a
*completed* bounded search is correct at every budget, not only at a generous one. `tests/test_solver.py`
and `tests/test_endgame.py` still pass.

## J4 smoke test (verbatim)

```
tools/frontier.py --run runs/deep8_c1_300_e8 --net runs/deep8_c1_300_e8/net_0300.pt --plies 60 62 --per_ply 20 --max_nodes 1e6 --sims 256 --device cuda:1
runs/deep8_c1_300_e8: 98581 games in 20 files (games_0280.npz..games_0299.npz); grading net_0300.pt at 256 sims on cuda:1
plies 60-62, 20 positions per ply, budget 1,000,000 nodes per position, 8 solver processes

 ply   alive sampled         solved   nodes med   nodes p90          optimal %             regret unsolved      s
(solved: conditional on alive | nodes, optimal, regret: conditional on solved)
  60    7850      20   100.0 % (20)          23       1,072 100.0 [100.0,100.0] 0.000 [0.000,0.000]        0    6.9
  61    5119      20   100.0 % (20)          10          48 100.0 [100.0,100.0] 0.000 [0.000,0.000]        0    9.1
  62    3640      20   100.0 % (20)           6         221 100.0 [100.0,100.0] 0.000 [0.000,0.000]        0    8.4
```

A second check at the interesting end (`--plies 40 42 --per_ply 12 --max_nodes 2e5`): ply 40 solved
8.3 % (1/12), ply 41 16.7 %, ply 42 50.0 % — the selection effect the field names exist to prevent
being read away. One JSON row, so the field names are on the record:

```
{"ply": 60, "games_alive_at_ply": 7850, "positions_sampled_conditional_on_alive": 20,
 "fraction_solved_conditional_on_alive": 1.0, "n_solved": 20, "unsolved_count_conditional_on_alive": 0,
 "median_nodes_conditional_on_solved": 23.0, "p90_nodes_conditional_on_solved": 1071.8, "nodes_spent_total": 5785,
 "search_optimal_move_rate_conditional_on_solved": 1.0, "search_optimal_move_rate_ci_conditional_on_solved": [1.0, 1.0],
 "search_mean_regret_conditional_on_solved": 0.0, "search_mean_regret_ci_conditional_on_solved": [0.0, 0.0],
 "median_empties_conditional_on_solved": 5.5, "seconds": 7.4}
```

Measured throughput 1.6 × 10⁷ nodes/s/process, so the real run (`--per_ply 500 --max_nodes 1e8`,
8 processes) is bounded by ≈ 6.5 min/ply, ≈ 3.5 h for plies 40–70, front-loaded on the early plies.

## J3 smoke test (verbatim)

```
tools/empty_board.py --net runs/deep8_c1_300_e8/net_0300.pt --games 16 --sims 32 --root_sims 256 --device cuda:1
runs/deep8_c1_300_e8/net_0300.pt (symmetry-averaged) on cuda:1; exploration as trained from config.json: sample_moves 8, temperature 1.0, sample_uniform 0.15, root_prior_floor 0.03, c_scale 1.0

(a) empty board @256 sims: value for X +0.5087; principal line [40, 36, 0, 8, 80, 77, 50, 48, 34, 66]  [7s]

  (b) sampled 4 plies, floor off        16 games @   32 sims   X  81.2 % [ 57.0,  93.4]   O   0.0 % [  0.0,  19.4]   draw  18.8 % [  6.6,  43.0]
                                     mean length  51.6   end reasons line  81.2 % / count   0.0 % / equal  18.8 %
                                     distinct: 4 games, 4 4-ply openings (2 up to symmetry)   [24s]
  (c) exploration as trained            16 games @   32 sims   X  43.8 % [ 23.1,  66.8]   O  37.5 % [ 18.5,  61.4]   draw  18.8 % [  6.6,  43.0]
                                     mean length  52.4   end reasons line  62.5 % / count  18.8 % / equal  18.8 %
                                     distinct: 16 games, 12 4-ply openings (7 up to symmetry)   [36s]

the run's own opening trajectory (timeline.json): iter 10: [44] 0.215, iter 160: [40] 0.976, iter 300: [40] 0.982
```

## Design choices M2 is asked to adjudicate

### J3 — sampling semantics PLAN7 §4 left open

1. **"The uniform floor off" is ambiguous — there are two floors.** `sample_uniform` (0.15 as trained)
   is the exploration floor mixed into the *sampling* distribution; `root_prior_floor` (0.03 as trained)
   is mixed into the *root prior* and so changes the tree, not just the move drawn. The brief named only
   `sample_uniform = 0`. Arm (b) turns **both** off; `--b_root_floor 0.03` restores the prior floor if
   M2 wants only the sampling floor removed. Arm (c) keeps both as trained.
2. **The Gumbel scale is exploration too, and `config.json` does not record it.** `train2.py` never
   sets it, so self-play trained at `MCTSConfig`'s default `gumbel_scale = 1.0` — the as-trained search
   is noisy at the root at *every* ply, not just the sampled ones. "Greedy after the sampled plies" in
   (b) is therefore only true at scale 0, which is what arm (b) uses; arm (c) uses 1.0. Consequence,
   stated in the JSON meta: (b) − (c) differs in four exploration knobs (sampled plies 4 vs 8, sampling
   floor 0 vs 0.15, prior floor 0 vs 0.03, Gumbel 0 vs 1) and in nothing else. `--b_gumbel_scale` /
   `--c_gumbel_scale` expose both.
3. **"Sampled proportionally" is proportional to the improved policy, not to visits.** In Gumbel mode
   `search.py:301` builds the policy as `softmax(root_logits + sigma)` and line 313 raises *that* to
   1/T. Easy to misread as visit-proportional; it is in the docstring.
4. **"The first 4 plies" = `ply < 4`** with ply the 0-based move count, i.e. X, O, X, O. The true ply is
   passed to every search rather than left at the default 0 (which would sample every move forever).
5. **What is matched and what is read from the run.** Both arms take `mode` and `c_scale` from
   `config.json` (this run trained at `c_scale = 1.0`, not the 0.1 default most tools assume) and both
   use `depth_cap = min(sims, 24)`, `m_considered = 16` — the tools convention. The run's trained
   `depth_cap = 12` and its 32 → 48 → 64 sims schedule were deliberately *not* imported: those are
   budget, and the design's point is that budget is held fixed.
6. **Duplication is measured, not hidden.** With the search deterministic after ply 4, arm (b) replays
   a handful of lines: the smoke run gave 4 distinct games out of 16 — **1 up to symmetry** in a second
   check. Every arm reports `distinct_games`, `distinct_openings_4ply` and
   `distinct_openings_4ply_canonical`, and each carries an `interval_note` saying the binomial (Wilson)
   interval treats games as independent and is optimistic by exactly that much. **M2 may well conclude
   arm (b) needs more sampled plies or a bootstrap over distinct lines; the tool makes that visible
   instead of assuming it away.**
7. **Wilson rather than normal-approximation intervals**, so a 0-count cell does not report [0, 0].
8. Games run in lock-step chunks of `--batch` (default 250) because the symmetry-averaged evaluator
   multiplies the batch by 8; chunking is behaviour-neutral since every game starts from the same empty
   board. Arm (a) reuses `atlas.deep_values` unchanged, so its PV length is atlas's `max_len = 10`.
9. All three arms are symmetry-averaged per the brief — the agent playing (b) and (c) is therefore
   *not* the agent that generated the run's corpus.

### J4

10. **"Alive at ply p" = `length > p`**: the game had not ended before p, so a position with a move to
    make exists there. A game of length exactly p is over at p and is out of the population.
11. **Budget semantics: one `max_nodes` shared by the position and its whole child enumeration.**
    Grading the search move the way `endgame.py eval` does needs every child's exact value, not just the
    root's, so "solve the position" is `solve_children`, and the budget is applied to that whole job; the
    first child that does not resolve ends it and the position counts unsolved.
12. **Grading is the plain `FusedEvaluator`, not symmetry-averaged**, `gumbel_scale = 0`,
    `depth_cap = min(sims, 24)` — because it calls `uttt.endgame.evaluate`, which is what
    `tools/endgame.py eval` calls. So J3 symmetrises and J4 does not, each following its own precedent;
    the asymmetry is deliberate and in both docstrings.
13. **`--last 20` game files by default** as the operational meaning of "late games" (`endgame.py
    build`'s convention).
14. **Cluster structure.** Within a ply each game contributes at most one position, so
    `cluster_bootstrap` degenerates to an ordinary bootstrap there; across plies the same game recurs,
    so the plies are *not* independent of one another. Both facts are in the JSON meta, with a `warning`
    field stating that the solved subset is the easy end of a ply and gets easier as the budget binds.

### Solver

`_negamax_bounded` is a copy of `_negamax`, not a parameterisation of it: a single budgeted kernel with
`solve()` passing a huge budget would have been less duplication, but it changes the code (and the
per-node cost) of a verified component for no gain to it; the risk of the copy drifting is what
`test_solver_bounded.py`'s first property exists to catch. Measured cost of the budget check: +2.5 %.
The abort marker is `-3`, outside `{−1, 0, +1}` and distinct from the `-2` "no move yet" sentinel, and it
never escapes to Python: `solve_bounded` returns `value = None` when `complete is False`.
