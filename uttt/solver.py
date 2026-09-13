"""Exact endgame solver (Numba negamax with alpha-beta) under the same rules as uttt.game.

solve(cells, macro, next_board, player, rule) -> +1 / 0 / -1 from the side-to-move's perspective.
Practical for positions with up to ~14 empty cells in open boards (the remaining-move count
bounds the depth; boards closing prunes the tree quickly). Used to label endgame positions
exactly, so the value head and the search can be scored against ground truth.

`rule` is "count" (default) or "draw" (uttt.rules); the Numba kernel takes it as a boolean flag,
so each rule gets its own specialisation and neither pays for the other.
"""
from __future__ import annotations

import numpy as np
from numba import njit

from .rules import check_rule

LINES = np.array([(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)], dtype=np.int64)
FULL = 2


@njit(cache=True)
def _line_winner(arr, off):
    for k in range(8):
        a = arr[off + LINES[k, 0]]
        if a != 0 and a != FULL and a == arr[off + LINES[k, 1]] and a == arr[off + LINES[k, 2]]:
            return a
    return 0


@njit(cache=True)
def _negamax(cells, macro, next_board, player, alpha, beta, nodes, draw_rule):
    nodes[0] += 1
    # legal boards
    best = -2
    target_open = next_board >= 0 and macro[next_board] == 0
    for b in range(9):
        if macro[b] != 0:
            continue
        if target_open and b != next_board:
            continue
        for c in range(9):
            m = 9 * b + c
            if cells[m] != 0:
                continue
            # apply
            cells[m] = player
            old_macro = macro[b]
            won = _line_winner(cells, 9 * b) == player
            full = True
            if not won:
                for k in range(9):
                    if cells[9 * b + k] == 0:
                        full = False
                        break
            if won:
                macro[b] = player
            elif full:
                macro[b] = FULL
            # terminal?
            v = -2
            if won and _line_winner(macro, 0) == player:
                v = 1
            else:
                all_closed = True
                for k in range(9):
                    if macro[k] == 0:
                        all_closed = False
                        break
                if all_closed:
                    v = 0  # the "draw" rule stops here; the count decides only under "count"
                    if not draw_rule:
                        x = 0
                        o = 0
                        for k in range(9):
                            if macro[k] == 1:
                                x += 1
                            elif macro[k] == -1:
                                o += 1
                        diff = (x - o) * player
                        v = 1 if diff > 0 else (-1 if diff < 0 else 0)
            if v == -2:
                nb = c if macro[c] == 0 else -1
                v = -_negamax(cells, macro, nb, -player, -beta, -alpha, nodes, draw_rule)
            # undo
            cells[m] = 0
            macro[b] = old_macro
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta or best == 1:
                return best
    return best


def solve(cells, macro, next_board, player, rule: str = "count"):
    """Exact game value from the side-to-move's perspective (+1 win, 0 draw, -1 loss). Returns (value, nodes).

    No node budget: keep callers to positions with <= ~18 moves left (see tests/test_solver.py timings)."""
    c = np.array(cells, dtype=np.int8).copy()
    m = np.array(macro, dtype=np.int8).copy()
    nodes = np.zeros(1, dtype=np.int64)
    v = _negamax(c, m, int(next_board), int(player), -1, 1, nodes, check_rule(rule) == "draw")
    return int(v), int(nodes[0])


def empties_in_open_boards(cells, macro) -> int:
    c = np.asarray(cells).reshape(9, 9)
    m = np.asarray(macro)
    return int(((c == 0) & (m == 0)[:, None]).sum())


ILLEGAL = -2  # child-value marker for illegal moves


def solve_children(args, rule: str = "count"):
    """(cells, macro, next_board, player) -> (exact root value, (81,) exact value after each legal move from the
    mover's perspective, ILLEGAL elsewhere). The root value is the max over children. Picklable for pools
    (with functools.partial for a non-default rule); this module imports only numpy/numba, so worker
    processes stay light."""
    from .game import UTTT

    cells, macro, nb, player = args
    g = UTTT(rule)
    g.cells[:] = cells
    g.macro[:] = macro
    g.next_board, g.player = int(nb), int(player)
    g.move_count = int((g.cells != 0).sum())
    child = np.full(81, ILLEGAL, dtype=np.int8)
    for m in g.legal_moves():
        h = g.clone()
        h.play(m)
        if h.done:
            child[m] = 0 if h.winner == 0 else (1 if h.winner == g.player else -1)
        else:
            child[m] = -solve(h.cells, h.macro, h.next_board, h.player, rule)[0]
    return int(child.max()), child


def solve_batch(args, rule: str = "count"):
    """Pool worker: (cells (k,81), macro (k,9), next_board (k,), player (k,)) -> (exact values (k,) int8,
    policy targets (k,81) float16 = uniform over the exactly optimal moves)."""
    cells, macro, nb, player = args
    k = len(nb)
    vals = np.zeros(k, dtype=np.int8)
    pol = np.zeros((k, 81), dtype=np.float16)
    for i in range(k):
        v, child = solve_children((cells[i], macro[i], int(nb[i]), int(player[i])), rule)
        vals[i] = v
        opt = (child == v).astype(np.float32)
        pol[i] = opt / opt.sum()
    return vals, pol
