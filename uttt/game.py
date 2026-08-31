"""Reference (single-game, pure Python/numpy) implementation of Ultimate Tic-Tac-Toe.

Rule set (the "closed board" variant with most-boards tiebreak, as on CodinGame):

* Nine local 3x3 boards sit in a 3x3 macro grid. Move index m = 9*board + cell,
  board = 3*R + C and cell = 3*r + c, both row-major.
* Playing cell k of any board sends the opponent to board k.
* A local board is CLOSED once it is won or full; no move may be played in it.
* If the designated board is closed, the player may play in ANY open board.
* Three won local boards in a macro line win the game immediately.
* If no legal move remains (every board closed) with no macro line, the player
  with MORE won local boards wins; equal counts is a draw.

Players are +1 (X, moves first) and -1 (O). A local board's macro status is
0 open, +1/-1 won, 2 closed-as-full-without-winner.
"""
from __future__ import annotations

import numpy as np

LINES = np.array(
    [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)],
    dtype=np.int64,
)
FULL = 2  # macro marker for a drawn (full, unwon) local board


def line_winner(cells9: np.ndarray) -> int:
    """Winner (+1/-1) of a length-9 array under standard tic-tac-toe lines, else 0."""
    for a, b, c in LINES:
        v = cells9[a]
        if v != 0 and v == cells9[b] == cells9[c]:
            return int(v)
    return 0


class UTTT:
    __slots__ = ("cells", "macro", "next_board", "player", "move_count", "done", "winner", "end_reason")

    def __init__(self) -> None:
        self.cells = np.zeros(81, dtype=np.int8)
        self.macro = np.zeros(9, dtype=np.int8)
        self.next_board = -1  # -1 = free move
        self.player = 1
        self.move_count = 0
        self.done = False
        self.winner = 0  # +1 / -1, or 0 for draw / ongoing
        self.end_reason = ""  # "line" | "count" | "draw" once done

    def clone(self) -> "UTTT":
        g = UTTT.__new__(UTTT)
        g.cells = self.cells.copy()
        g.macro = self.macro.copy()
        g.next_board = self.next_board
        g.player = self.player
        g.move_count = self.move_count
        g.done = self.done
        g.winner = self.winner
        g.end_reason = self.end_reason
        return g

    # ---- rules -----------------------------------------------------------
    def legal_mask(self) -> np.ndarray:
        if self.done:
            return np.zeros(81, dtype=bool)
        open_board = self.macro == 0
        if self.next_board >= 0 and open_board[self.next_board]:
            allowed = np.zeros(9, dtype=bool)
            allowed[self.next_board] = True
        else:
            allowed = open_board
        return (self.cells == 0) & np.repeat(allowed, 9)

    def legal_moves(self) -> list[int]:
        return np.flatnonzero(self.legal_mask()).tolist()

    def play(self, move: int) -> None:
        if self.done:
            raise ValueError("game is over")
        if not self.legal_mask()[move]:
            raise ValueError(f"illegal move {move}")
        b, c = divmod(move, 9)
        p = self.player
        self.cells[move] = p
        self.move_count += 1

        local = self.cells[9 * b : 9 * b + 9]
        if line_winner(local) == p:
            self.macro[b] = p
        elif np.all(local != 0):
            self.macro[b] = FULL

        if line_winner(np.where(np.abs(self.macro) == 1, self.macro, 0)) == p:
            self.done, self.winner, self.end_reason = True, p, "line"
        elif np.all(self.macro != 0):
            x, o = int(np.sum(self.macro == 1)), int(np.sum(self.macro == -1))
            self.done = True
            if x != o:
                self.winner, self.end_reason = (1 if x > o else -1), "count"
            else:
                self.winner, self.end_reason = 0, "draw"

        self.next_board = c if self.macro[c] == 0 else -1
        self.player = -p

    # ---- display ---------------------------------------------------------
    def __str__(self) -> str:
        sym = {0: ".", 1: "X", -1: "O"}
        rows = []
        for row in range(9):
            R, r = divmod(row, 3)
            s = ""
            for col in range(9):
                C, c = divmod(col, 3)
                s += sym[int(self.cells[9 * (3 * R + C) + 3 * r + c])]
                s += " " if col % 3 != 2 else ("  " if col < 8 else "")
            rows.append(s)
            if row in (2, 5):
                rows.append("")
        msym = {0: ".", 1: "X", -1: "O", 2: "#"}
        macro = "\n".join("".join(msym[int(self.macro[3 * R + C])] for C in range(3)) for R in range(3))
        nb = self.next_board if self.next_board >= 0 else "any"
        head = f"to move: {sym[self.player]}   next board: {nb}   moves: {self.move_count}"
        if self.done:
            res = "draw" if self.winner == 0 else sym[self.winner] + " wins"
            head += f"   RESULT: {res} ({self.end_reason})"
        return head + "\n" + "\n".join(rows) + "\nmacro:\n" + macro
