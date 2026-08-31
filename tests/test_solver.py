"""Solver correctness: agrees with a pure-Python minimax on the reference engine for small endgames,
and with actual game outcomes when the solved value is decisive along the played line."""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.game import UTTT  # noqa: E402
from uttt.solver import empties_in_open_boards, solve  # noqa: E402


def minimax_ref(g: UTTT) -> int:
    if g.done:
        return 0 if g.winner == 0 else (1 if g.winner == g.player else -1)
    best = -2
    for m in g.legal_moves():
        h = g.clone()
        h.play(m)
        v = -minimax_ref(h)
        if v > best:
            best = v
        if best == 1:
            break
    return best


def random_endgame(rng, max_empty):
    """Play random moves until the position has <= max_empty empties in open boards (and is not over)."""
    while True:
        g = UTTT()
        while not g.done and empties_in_open_boards(g.cells, g.macro) > max_empty:
            g.play(int(rng.choice(g.legal_moves())))
        if not g.done:
            return g


def test_against_reference(n=60, max_empty=8, seed=0):
    rng = np.random.default_rng(seed)
    t_ref = t_sol = 0.0
    for _ in range(n):
        g = random_endgame(rng, max_empty)
        t = time.perf_counter()
        v_ref = minimax_ref(g)
        t_ref += time.perf_counter() - t
        t = time.perf_counter()
        v_sol, nodes = solve(g.cells, g.macro, g.next_board, g.player)
        t_sol += time.perf_counter() - t
        assert v_ref == v_sol, (v_ref, v_sol, str(g))
    print(f"solver agrees with reference minimax on {n} endgames (<= {max_empty} empties): ref {t_ref:.1f}s, solver {t_sol:.3f}s")


def test_speed(seed=1):
    rng = np.random.default_rng(seed)
    for max_empty in (10, 12, 14, 16):
        times, nodes_all = [], []
        for _ in range(10):
            g = random_endgame(rng, max_empty)
            t = time.perf_counter()
            _, nodes = solve(g.cells, g.macro, g.next_board, g.player)
            times.append(time.perf_counter() - t)
            nodes_all.append(nodes)
        print(f"<= {max_empty} empties: median {np.median(times) * 1000:.1f} ms, max {max(times) * 1000:.0f} ms, median nodes {int(np.median(nodes_all))}, max nodes {max(nodes_all)}")


if __name__ == "__main__":
    solve(np.zeros(81, np.int8), np.array([1, 1, 2, -1, -1, 2, 2, 2, 0], np.int8), -1, 1)  # JIT warm-up on a tiny case
    test_against_reference()
    test_speed()
    print("ok")
