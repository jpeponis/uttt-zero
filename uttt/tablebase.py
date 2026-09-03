"""Exact tablebase for positions with at most one open local board (PLAN5 §4 C5).

With one board open, every legal move is in that board, so the game is a single tic-tac-toe whose three outcomes
(X wins the board / O wins it / it fills) are each mapped by the macro board to a game result: a macro line for the
winner, else the board count (the most-boards rule; equal is a draw). The tablebase therefore needs only the open
board's cells (3^9 states), the side to move and the outcome-to-result map (3^3 triples): 19 683 x 2 x 27 = 1.06 M
entries, one byte each — knowledge/06's 1.2 x 10^10 counted the closed boards' identities and the send, neither of
which changes the value. Built by backward induction in a second; exact for every position with <= 1 open board
(the solver already covers these, but the table answers a GPU batch in one gather, which is what a terminal lookup
inside the search needs).

    tb = K1Table()                              # builds (or loads) the table
    v, best = tb.lookup(cells, macro, player)   # exact value for the mover and an optimal move, for K=1 rows
    ev = TablebaseEvaluator(base_evaluator)     # any evaluator: K=1 positions get the exact value and an optimal policy
"""
from __future__ import annotations

import numpy as np
import torch

from .batch import FULL, consts, legal_mask

POW3 = 3 ** np.arange(9)
LINES_NP = np.array([(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)])


def _build() -> tuple[np.ndarray, np.ndarray]:
    """V[state, side, payoff] in {-1, 0, +1} from the side to move's view; M[state, side, payoff] an optimal cell (or -1).
    state = sum (cell + 1) * 3^c; side 0 = X (+1), 1 = O (-1); payoff = (rX+1)*9 + (rO+1)*3 + (rF+1), results for X."""
    S = 19683
    digits = (np.arange(S)[:, None] // POW3[None, :]) % 3  # (S, 9) in {0, 1, 2}
    cells = digits - 1  # -1 / 0 / +1
    x_win = (cells[:, LINES_NP] == 1).all(-1).any(-1)
    o_win = (cells[:, LINES_NP] == -1).all(-1).any(-1)
    full = (cells != 0).all(-1)
    stones = (cells != 0).sum(-1)
    pay = np.arange(27)
    rX, rO, rF = pay // 9 - 1, (pay // 3) % 3 - 1, pay % 3 - 1  # (27,) results for X
    V = np.zeros((S, 2, 27), dtype=np.int8)
    M = np.full((S, 2, 27), -1, dtype=np.int8)
    side_sign = np.array([1, -1])
    # terminal states: result for X times the mover's sign
    term = x_win | o_win | full
    res_x = np.where(x_win[:, None], rX[None, :], np.where(o_win[:, None], rO[None, :], rF[None, :]))  # (S, 27)
    for s in range(2):
        V[term, s, :] = (res_x[term] * side_sign[s]).astype(np.int8)
    # backward induction over stone count
    for k in range(8, -1, -1):
        idx = np.flatnonzero((stones == k) & ~term)
        for s in range(2):
            sign = side_sign[s]
            best = np.full((len(idx), 27), -2, dtype=np.int8)
            bestm = np.full((len(idx), 27), -1, dtype=np.int8)
            for c in range(9):
                empty = cells[idx, c] == 0
                child = np.where(empty, idx + sign * POW3[c], idx)  # placing +1 raises the digit, -1 lowers it
                cv = -V[child, 1 - s, :]  # child value from the opponent's view, negated (ignored where not empty)
                better = empty[:, None] & (cv > best)
                best = np.where(better, cv, best)
                bestm = np.where(better, c, bestm)
            V[idx, s, :] = best
            M[idx, s, :] = bestm
    return V, M


class K1Table:
    def __init__(self, device=None) -> None:
        self.V, self.M = _build()
        self.device = torch.device(device) if device is not None else None
        if self.device is not None:
            self.Vt = torch.from_numpy(self.V).to(self.device)
            self.Mt = torch.from_numpy(self.M).to(self.device)
            self.pow3 = torch.from_numpy(POW3).to(self.device)

    @torch.no_grad()
    def payoffs(self, macro: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """Result for X (-1/0/+1) if board b ends X-won, O-won, full: (n, 3)."""
        n = macro.shape[0]
        lines = consts(macro.device)["LINES"]
        out = []
        for outcome in (1, -1, FULL):  # no Python scalars reach the device tensors: CUDA-graph capture safe
            fill = torch.full((n, 1), outcome, dtype=macro.dtype, device=macro.device)
            m = macro.scatter(1, b.view(n, 1), fill)
            won_only = m * (m.abs() == 1)
            xl = (won_only[:, lines] == 1).all(-1).any(-1)
            ol = (won_only[:, lines] == -1).all(-1).any(-1)
            count = torch.sign((m == 1).sum(1) - (m == -1).sum(1)).long()
            ones = torch.ones_like(count)
            out.append(torch.where(xl, ones, torch.where(ol, -ones, count)))
        return torch.stack(out, 1)

    @torch.no_grad()
    def lookup(self, cells: torch.Tensor, macro: torch.Tensor, player: torch.Tensor):
        """For rows with exactly one open board: (value for the mover, optimal move in engine order); other rows get
        value 0 and move -1, plus the mask of K=1 rows. Terminal rows (game over) are not K=1 by construction."""
        n = cells.shape[0]
        idx = torch.arange(n, device=cells.device)
        open_b = macro == 0
        k1 = open_b.sum(1) == 1
        b = open_b.float().argmax(1)
        local = cells.view(n, 9, 9)[idx, b].long()
        state = ((local + 1) * self.pow3).sum(1)
        side = (player.long() == -1).long()
        pay = self.payoffs(macro, b)
        pidx = (pay[:, 0] + 1) * 9 + (pay[:, 1] + 1) * 3 + (pay[:, 2] + 1)
        v = self.Vt[state, side, pidx].float()
        m = self.Mt[state, side, pidx].long()
        move = torch.where(k1 & (m >= 0), 9 * b + m, torch.full_like(m, -1))
        return torch.where(k1, v, torch.zeros_like(v)), move, k1


class TablebaseEvaluator:
    """Wraps an evaluator: positions with one open board get the exact value and a one-hot policy on an optimal move."""

    def __init__(self, base, table: K1Table | None = None) -> None:
        self.base = base
        self.device = base.device
        self.tb = table or K1Table(self.device)
        self._calls = torch.zeros((), dtype=torch.long, device=self.device)  # device-side counters: no host sync
        self._hits = torch.zeros((), dtype=torch.long, device=self.device)   # inside a CUDA-graph capture

    @property
    def calls(self) -> int:
        return int(self._calls)

    @property
    def k1_hits(self) -> int:
        return int(self._hits)

    @torch.no_grad()
    def __call__(self, cells, macro, next_board, player, done):
        probs, value = self.base(cells, macro, next_board, player, done)
        v, move, k1 = self.tb.lookup(cells, macro, player)
        k1 = k1 & ~done & (move >= 0)
        self._calls += cells.shape[0]
        self._hits += k1.sum()
        onehot = torch.zeros_like(probs).scatter(1, move.clamp(min=0).view(-1, 1), 1.0)
        onehot = onehot * legal_mask(cells, macro, next_board, done)
        probs = torch.where(k1.unsqueeze(1), onehot, probs)
        value = torch.where(k1, v, value)
        return probs, value
