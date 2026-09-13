"""solve_bounded / solve_children_bounded (PLAN7 J4): a node budget that only ever removes results.

On one shared set of 500 random positions with <= 16 empties in open boards:
  1. with a budget the search never reaches, bounded == unbounded exactly — same value, same node count
     (under both terminal rules, and the draw rule must actually change some values);
  2. whenever a bounded search completes, its value equals the unbounded one, at every budget — under
     COUNT and under DRAW (PLAN7 §7e M2 row 18);
  3. a budget of 10 nodes reports incomplete on exactly the positions that need more than 10, and value
     None on every one of them (an aborted search must never hand back a game value);
  4. solve_children_bounded, which is what J4 actually measures (complete legal-action value coverage):
     with a generous budget it reproduces solve_children under both rules; with a budget smaller than the
     enumeration needs it returns (None, None, used, False) with used <= budget — no partial child table
     and no value; and the same call through a multiprocessing pool under "draw" agrees with the
     in-process result, so the rule reaches a worker process (tools/frontier.py runs it that way).
"""
import os
import sys
import time
from functools import partial
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from test_solver import random_endgame  # noqa: E402
from uttt.solver import solve, solve_bounded, solve_children, solve_children_bounded  # noqa: E402

N = 500
MAX_EMPTY = 16
GENEROUS = 10**12
N_CHILDREN = 250  # positions for property 4 (each one solves every legal child, so it costs more per position)
N_POOLED = 100  # of those, the ones re-solved through a pool
POOL_WORKERS = 2


def positions(n=N, max_empty=MAX_EMPTY, seed=0):
    rng = np.random.default_rng(seed)
    return [random_endgame(rng, max_empty) for _ in range(n)]


def test_bounded_matches_unbounded(games=None):
    games = games or positions()
    t = time.perf_counter()
    ref = [solve(g.cells, g.macro, g.next_board, g.player) for g in games]
    t_ref = time.perf_counter() - t
    t = time.perf_counter()
    got = [solve_bounded(g.cells, g.macro, g.next_board, g.player, GENEROUS) for g in games]
    t_bnd = time.perf_counter() - t
    for g, (v, n), (vb, nb, ok) in zip(games, ref, got):
        assert ok, f"a budget of {GENEROUS} was not enough for {n} nodes"
        assert (vb, nb) == (v, n), (v, n, vb, nb, str(g))
    nodes = [n for _, n in ref]
    print(f"{len(games)} positions (<= {MAX_EMPTY} empties): bounded == unbounded in value and node count; "
          f"median {int(np.median(nodes))} nodes, max {max(nodes)}; unbounded {t_ref:.2f}s, bounded {t_bnd:.2f}s "
          f"({100 * (t_bnd / t_ref - 1):+.1f} %)")
    return games, ref


def test_bounded_matches_unbounded_draw(games=None):
    """Property 1 under the draw rule (PLAN7 K1): the bounded kernel carries the same draw_rule flag as _negamax,
    so the two must agree in value and node count under "draw" too — and the rule must actually change something.

    Returns (games, ref) so property 2 can be run against the draw-rule reference."""
    games = games or positions()
    ref = [solve(g.cells, g.macro, g.next_board, g.player, rule="draw") for g in games]
    got = [solve_bounded(g.cells, g.macro, g.next_board, g.player, GENEROUS, rule="draw") for g in games]
    for g, (v, n), (vb, nb, ok) in zip(games, ref, got):
        assert ok and (vb, nb) == (v, n), (v, n, vb, nb, ok, str(g))
    count_vals = [solve(g.cells, g.macro, g.next_board, g.player)[0] for g in games]
    differ = sum(int(a != b[0]) for a, b in zip(count_vals, ref))
    assert differ > 0, "the draw rule changed no value on 500 positions — the flag is not reaching the kernel"
    print(f"draw rule: bounded == unbounded in value and node count on {len(games)} positions; "
          f"{differ} of them have a different value than under the count rule")
    return games, ref


def test_complete_is_always_right(games=None, ref=None, budgets=(10, 1000, 100000), rule="count"):
    """Property 2: a completed bounded search is correct at any budget; nodes never exceed the budget.

    Run under both rules (M2, PLAN7 §7e M2 row 18): a tight budget must not turn the draw rule's terminal
    value into the count rule's, and `ref` is the unbounded reference solved under the same `rule`."""
    if games is None:
        games, ref = test_bounded_matches_unbounded() if rule == "count" else test_bounded_matches_unbounded_draw()
    done = []
    for budget in budgets:
        k = 0
        for g, (v, _) in zip(games, ref):
            vb, nb, ok = solve_bounded(g.cells, g.macro, g.next_board, g.player, budget, rule=rule)
            assert nb <= budget, (nb, budget)
            if ok:
                assert vb == v, (vb, v, budget, rule, str(g))
                k += 1
            else:
                assert vb is None, vb
        done.append((budget, k))
    print(f"rule {rule}: completed and agreed with the unbounded value: "
          + ", ".join(f"{k}/{len(games)} at a budget of {b}" for b, k in done))


def test_budget_10(games=None, ref=None):
    """Property 3: at a budget of 10, incomplete on exactly the positions whose unbounded search needs more."""
    if games is None:
        games, ref = test_bounded_matches_unbounded()
    incomplete = 0
    for g, (v, n) in zip(games, ref):
        vb, nb, ok = solve_bounded(g.cells, g.macro, g.next_board, g.player, 10)
        assert ok == (n <= 10), (ok, n, str(g))
        if ok:
            assert (vb, nb) == (v, n), (v, n, vb, nb)
        else:
            assert vb is None and nb == 10, (vb, nb)
            incomplete += 1
    print(f"budget 10: incomplete on {incomplete}/{len(games)} positions — exactly those needing more than 10 nodes, "
          f"value None on every one of them")


def test_children_bounded(games=None, n=N_CHILDREN, pooled=N_POOLED, workers=POOL_WORKERS):
    """Property 4: the bounded child enumeration — what J4 measures — under both rules, tight budgets and a pool.

    (i) generous budget: (root value, child table) identical to solve_children() under "count" and "draw";
    (ii) budget = used // 2 on every position that needs at least 2 nodes: the enumeration must fail, and
         failing means (None, None, used, False) with used <= budget — no partial child table, no value;
    (iii) the same generous call through a Pool under "draw" (functools.partial, as tools/frontier.py does
          it) returns exactly the in-process result, so the rule reaches the worker processes."""
    games = (games or positions())[:n]
    out = {}
    for rule in ("count", "draw"):
        ref = [solve_children((g.cells, g.macro, g.next_board, g.player), rule) for g in games]
        got = [solve_children_bounded((g.cells, g.macro, g.next_board, g.player, GENEROUS), rule) for g in games]
        for g, (v, child), (vb, childb, used, ok) in zip(games, ref, got):
            assert ok, f"a budget of {GENEROUS} did not finish the enumeration ({used} nodes)"
            assert vb == v and np.array_equal(childb, child), (v, vb, rule, str(g))
            assert used <= GENEROUS
        out[rule] = (ref, got)
    differ = sum(int(a[0] != b[0]) for a, b in zip(out["count"][0], out["draw"][0]))
    assert differ > 0, f"the draw rule changed no root value on {len(games)} enumerations — it is not reaching them"
    used_all = [u for _, _, u, _ in out["count"][1]]
    print(f"solve_children_bounded == solve_children in root value and all 81 child values on {len(games)} positions "
          f"under both rules ({differ} differ in root value between the rules); median {int(np.median(used_all))} "
          f"nodes, max {max(used_all)}")

    tight = 0
    for g, (_, _, used, _) in zip(games, out["draw"][1]):
        if used < 2:
            continue
        budget = used // 2
        vb, childb, u, ok = solve_children_bounded((g.cells, g.macro, g.next_board, g.player, budget), "draw")
        assert not ok, (used, budget, str(g))
        assert vb is None and childb is None, (vb, childb)
        assert u <= budget, (u, budget)
        tight += 1
    assert tight > 0, "no position needed 2 nodes: the tight-budget property tested nothing"
    print(f"budget = half of what the enumeration needs: incomplete on all {tight} positions that need >= 2 nodes, "
          "(None, None, used <= budget, False) on every one")

    sub = games[:pooled]
    args = [(g.cells, g.macro, g.next_board, g.player, GENEROUS) for g in sub]
    with Pool(workers) as pool:
        got = pool.map(partial(solve_children_bounded, rule="draw"), args, chunksize=1)
    for (v, child, used, ok), (vr, childr, usedr, okr) in zip(got, out["draw"][1][:pooled]):
        assert (v, used, ok) == (vr, usedr, okr) and np.array_equal(child, childr), (v, vr, used, usedr)
    print(f"pooled ({workers} workers, rule draw): identical root value, child table and node count to the "
          f"in-process result on {len(sub)} positions")


if __name__ == "__main__":
    warm = (np.zeros(81, np.int8), np.array([1, 1, 2, -1, -1, 2, 2, 2, 0], np.int8), -1, 1)  # JIT warm-up, both kernels
    solve(*warm)
    solve_bounded(*warm, 10**6)
    solve(*warm, rule="draw")
    solve_bounded(*warm, 10**6, rule="draw")
    t = time.perf_counter()
    games, ref = test_bounded_matches_unbounded()
    games, ref_draw = test_bounded_matches_unbounded_draw(games)
    test_complete_is_always_right(games, ref)
    test_complete_is_always_right(games, ref_draw, rule="draw")
    test_budget_10(games, ref)
    test_children_bounded(games)
    print(f"ok [{time.perf_counter() - t:.1f}s]")
