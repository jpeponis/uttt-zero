"""solve_bounded (PLAN7 J4): a node budget that only ever removes results.

Three properties, on the same 500 random positions with <= 16 empties in open boards:
  1. with a budget the search never reaches, bounded == unbounded exactly — same value, same node count;
  2. whenever a bounded search completes, its value equals the unbounded one, at every budget;
  3. a budget of 10 nodes reports incomplete on exactly the positions that need more than 10, and value
     None on every one of them (an aborted search must never hand back a game value).
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from test_solver import random_endgame  # noqa: E402
from uttt.solver import solve, solve_bounded  # noqa: E402

N = 500
MAX_EMPTY = 16
GENEROUS = 10**12


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


def test_complete_is_always_right(games=None, ref=None, budgets=(10, 1000, 100000)):
    """Property 2: a completed bounded search is correct at any budget; nodes never exceed the budget."""
    if games is None:
        games, ref = test_bounded_matches_unbounded()
    done = []
    for budget in budgets:
        k = 0
        for g, (v, _) in zip(games, ref):
            vb, nb, ok = solve_bounded(g.cells, g.macro, g.next_board, g.player, budget)
            assert nb <= budget, (nb, budget)
            if ok:
                assert vb == v, (vb, v, budget, str(g))
                k += 1
            else:
                assert vb is None, vb
        done.append((budget, k))
    print("completed and agreed with the unbounded value: " + ", ".join(f"{k}/{len(games)} at a budget of {b}" for b, k in done))


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


if __name__ == "__main__":
    warm = (np.zeros(81, np.int8), np.array([1, 1, 2, -1, -1, 2, 2, 2, 0], np.int8), -1, 1)  # JIT warm-up, both kernels
    solve(*warm)
    solve_bounded(*warm, 10**6)
    t = time.perf_counter()
    games, ref = test_bounded_matches_unbounded()
    test_complete_is_always_right(games, ref)
    test_budget_10(games, ref)
    print(f"ok [{time.perf_counter() - t:.1f}s]")
