"""Symmetry-averaged evaluation: evaluate all 8 D4 images of each position and average the
mapped-back policies and values. 8x the inference cost; for analysis and evaluation only.

The result is exactly equivariant: evaluating a transformed position gives the transformed policy.
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
