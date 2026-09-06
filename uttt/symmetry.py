"""Exactly equivariant evaluators built on an ordinary net.

SymmetryAveragedEvaluator: evaluate all 8 D4 images of each position and average the mapped-back
policies and values. 8x the inference cost; an ensemble as much as a symmetriser (+35 Elo at equal
sims on deep10, PLAN5 B5).

CanonicalEvaluator (PLAN6 F1, from REVIEW-astra §5.2): evaluate the position ONCE in its canonical
orientation — the lexicographically smallest of its 8 images over (cells, macro, next board) — and
transport the policy back through every symmetry that maps the position onto that canonical image
(more than one when the position has a non-trivial stabiliser: the empty board, [40]), averaging the
transports. Exactly equivariant at ≈ 1.03x the cost of the plain net. It picks one orientation's
errors consistently rather than averaging them away, so it is a symmetry control, not an ensemble.

Both are exactly equivariant: evaluating a transformed position gives the transformed policy.
"""
from __future__ import annotations

import torch

from .batch import SYM_BOARD, SYM_BOARD_INV, SYM_CELL, SYM_CELL_INV


class SymmetryAveragedEvaluator:
    def __init__(self, base) -> None:
        self.base = base
        self.device = base.device
        d = self.device
        self.cell_inv = SYM_CELL_INV.to(d)  # (8, 81)
        self.cell = SYM_CELL.to(d)
        self.board_inv = SYM_BOARD_INV.to(d)  # (8, 9)
        self.board = SYM_BOARD.to(d)

    @torch.no_grad()
    def __call__(self, cells, macro, next_board, player, done):
        n = cells.shape[0]
        # images: for symmetry s, new_cells[SYM_CELL[s][m]] = cells[m]  <=>  new_cells = cells[:, SYM_CELL_INV[s]]
        c8 = cells[:, self.cell_inv].reshape(n * 8, 81)  # (n, 8, 81) -> (n*8, 81)
        m8 = macro[:, self.board_inv].reshape(n * 8, 9)
        nb = next_board.long()
        nb8 = torch.where(nb.unsqueeze(1) >= 0, self.board[:, nb.clamp(min=0)].t(), nb.unsqueeze(1)).reshape(n * 8).to(next_board.dtype)
        p8 = player.repeat_interleave(8)
        d8 = done.repeat_interleave(8)
        probs, value = self.base(c8, m8, nb8, p8, d8)
        probs = probs.view(n, 8, 81)
        # map policies back: original move m corresponds to image move SYM_CELL[s][m]
        back = torch.gather(probs, 2, self.cell.unsqueeze(0).expand(n, 8, 81))
        return back.mean(1), value.view(n, 8).mean(1)


class CanonicalEvaluator:
    def __init__(self, base) -> None:
        self.base = base
        self.device = base.device
        d = self.device
        self.cell_inv = SYM_CELL_INV.to(d)
        self.cell = SYM_CELL.to(d)
        self.board_inv = SYM_BOARD_INV.to(d)
        self.board = SYM_BOARD.to(d)

    @torch.no_grad()
    def __call__(self, cells, macro, next_board, player, done):
        n = cells.shape[0]
        idx = torch.arange(n, device=self.device)
        c8 = cells[:, self.cell_inv]  # (n, 8, 81): image s of every position
        m8 = macro[:, self.board_inv]  # (n, 8, 9)
        nb = next_board.long()
        nb8 = torch.where(nb.unsqueeze(1) >= 0, self.board[:, nb.clamp(min=0)].t(), nb.unsqueeze(1)).to(next_board.dtype)  # (n, 8)
        keys = torch.cat([c8, m8, nb8.unsqueeze(2)], dim=2)  # (n, 8, 91): exact lexicographic comparison, no hashing
        best, pick = keys[:, 0], torch.zeros(n, dtype=torch.long, device=self.device)
        for s in range(1, 8):  # graph-capturable: no host syncs
            cand = keys[:, s]
            first = (cand != best).to(torch.int32).argmax(1)  # first differing column (0 when equal: then not less)
            less = cand[idx, first] < best[idx, first]
            best = torch.where(less.unsqueeze(1), cand, best)
            pick = torch.where(less, torch.full_like(pick, s), pick)
        probs, value = self.base(c8[idx, pick], m8[idx, pick], nb8[idx, pick], player, done)
        # every s with image == canonical image is a valid transport back; average them (the stabiliser coset)
        coset = (keys == best.unsqueeze(1)).all(2).float()  # (n, 8)
        back = probs[:, self.cell]  # (n, 8, 81): back[:, s, m] = probs[:, SYM_CELL[s][m]]
        probs = (back * coset.unsqueeze(2)).sum(1) / coset.sum(1, keepdim=True)
        return probs, value
