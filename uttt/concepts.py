"""Concept labels computed from the board state (PLAN5 §3 B2): the hand-written features a probe is trained to read
off the network's activations. Everything is vectorised over a batch of positions and expressed from the side to
move's perspective ("mine" / "theirs"), matching the input encoding (uttt.batch.encode).

    labels = concept_labels(cells, macro, next_board, player)   # dict name -> (N,) array
    CONCEPTS[name] = ("binary" | "class:K" | "reg", description)

Positions: cells (N, 81) int8 in engine order (m = 9*board + cell), macro (N, 9) int8 (0 open, ±1 won, 2 full),
next_board (N,) int8 (-1 = free), player (N,) int8 (+1 X / -1 O).
"""
from __future__ import annotations

import numpy as np

from .game import FULL, LINES

CONCEPTS = {
    "side_to_move_x": ("binary", "side to move is X"),
    "free_move": ("binary", "the mover may play on any open board"),
    "target_board": ("class:10", "board the mover is sent to (0-8), 9 = free"),
    "open_count": ("reg", "number of open boards"),
    "empties": ("reg", "empty cells in open boards"),
    "count_margin": ("reg", "boards won by the mover minus boards won by the opponent"),
    "count_sign": ("class:3", "sign of count_margin: behind / equal / ahead"),
    "boards_full": ("reg", "boards closed as full without a winner"),
    "threats_for": ("reg", "macro lines with two mover boards and the third open"),
    "threats_against": ("reg", "macro lines with two opponent boards and the third open"),
    "threat_for_any": ("binary", "threats_for > 0"),
    "threat_against_any": ("binary", "threats_against > 0"),
    "dead_count": ("reg", "open boards that neither side can still win"),
    "local_win_now": ("binary", "the mover can win a board with this move"),
    "local_threat_against": ("binary", "the opponent has a two-in-a-line with the third cell empty in some open board"),
    "macro_win_now": ("binary", "the mover can win the game with this move"),
}
for _b in range(9):
    CONCEPTS[f"status_{_b}"] = ("class:4", f"board {_b}: open / mine / theirs / full")
    CONCEPTS[f"dead_{_b}"] = ("binary", f"board {_b} is open but unwinnable by either side")


def concept_labels(cells: np.ndarray, macro: np.ndarray, next_board: np.ndarray, player: np.ndarray) -> dict:
    N = cells.shape[0]
    p = player.astype(np.int8).reshape(N, 1)
    macro = macro.astype(np.int8)
    b = cells.astype(np.int8).reshape(N, 9, 9)
    lines = b[:, :, LINES]  # (N, 9 boards, 8 lines, 3 cells)
    pl = p[:, :, None, None]
    c_me, c_op, c_e = (lines == pl).sum(-1), (lines == -pl).sum(-1), (lines == 0).sum(-1)  # (N, 9, 8)
    open_b = macro == 0
    board_me_win = ((c_me == 2) & (c_e == 1)).any(-1) & open_b  # I could complete a line here, if allowed to play here
    board_op_win = ((c_op == 2) & (c_e == 1)).any(-1) & open_b
    dead = open_b & ((c_me > 0) & (c_op > 0)).all(-1)
    nb = next_board.astype(np.int64)
    nb0 = np.clip(nb, 0, 8)
    sent_open = (nb >= 0) & open_b[np.arange(N), nb0]
    allowed = np.where(sent_open[:, None], np.eye(9, dtype=bool)[nb0], open_b)
    mine, theirs, full = macro == p, macro == -p, macro == FULL
    ml = macro[:, LINES]  # (N, 8, 3)
    m_me, m_op, m_open = (ml == p[:, :, None]).sum(-1), (ml == -p[:, :, None]).sum(-1), (ml == 0).sum(-1)
    thr_for = ((m_me == 2) & (m_open == 1)).sum(1)
    thr_against = ((m_op == 2) & (m_open == 1)).sum(1)
    completes = np.zeros((N, 9), dtype=bool)  # winning board j now would complete a macro line
    for a, c, d in LINES:
        for j, (x, y) in ((a, (c, d)), (c, (a, d)), (d, (a, c))):
            completes[:, j] |= mine[:, x] & mine[:, y]
    margin = mine.sum(1).astype(np.int64) - theirs.sum(1).astype(np.int64)
    empties = ((b == 0) & open_b[:, :, None]).sum((1, 2))
    out = {
        "side_to_move_x": (player == 1).astype(np.int64),
        "free_move": (~sent_open).astype(np.int64),
        "target_board": np.where(sent_open, nb0, 9).astype(np.int64),
        "open_count": open_b.sum(1).astype(np.float64),
        "empties": empties.astype(np.float64),
        "count_margin": margin.astype(np.float64),
        "count_sign": (np.sign(margin) + 1).astype(np.int64),
        "boards_full": full.sum(1).astype(np.float64),
        "threats_for": thr_for.astype(np.float64),
        "threats_against": thr_against.astype(np.float64),
        "threat_for_any": (thr_for > 0).astype(np.int64),
        "threat_against_any": (thr_against > 0).astype(np.int64),
        "dead_count": dead.sum(1).astype(np.float64),
        "local_win_now": (board_me_win & allowed).any(1).astype(np.int64),
        "local_threat_against": board_op_win.any(1).astype(np.int64),
        "macro_win_now": (board_me_win & allowed & completes).any(1).astype(np.int64),
    }
    status = np.where(mine, 1, np.where(theirs, 2, np.where(full, 3, 0))).astype(np.int64)
    for j in range(9):
        out[f"status_{j}"] = status[:, j]
        out[f"dead_{j}"] = dead[:, j].astype(np.int64)
    return out
