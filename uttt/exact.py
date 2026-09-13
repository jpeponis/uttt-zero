"""Exact endgame labels during training (PLAN2 §5 step 2). A process pool solves a sample of each
iteration's late positions (few empties in open boards) while the trainer runs; the results — exact
game value and the set of exactly optimal moves — overwrite those rows' value target (and optionally
policy target) in the replay buffer, which can also up-weight them at sampling time.

    labeler = ExactLabeler(processes=8, max_empty=12, per_iter=8192)
    labeler.submit(positions, buffer_slots)     # right after buf.add(positions)
    ...train...
    got = labeler.collect()                     # (slots, values, policies) or None
    buf.apply_exact(*got, replace_policy=True)
"""
from __future__ import annotations

import time
from functools import partial
from multiprocessing import Pool

import numpy as np
import torch

from .rules import check_rule
from .solver import solve_batch


def empties_in_open_boards_t(cells: torch.Tensor, macro: torch.Tensor) -> torch.Tensor:
    """(n,) count of empty cells in open boards, batched."""
    return ((cells.view(-1, 9, 9) == 0) & (macro == 0).unsqueeze(2)).sum((1, 2))


class ExactLabeler:
    def __init__(self, processes: int = 8, max_empty: int = 12, per_iter: int = 8192, chunk: int = 64, seed: int = 0,
                 rule: str = "count") -> None:
        self.pool = Pool(processes)
        self.rule = check_rule(rule)  # the rule the run trains under: the exact labels must agree with its engine
        self.max_empty = max_empty
        self.per_iter = per_iter
        self.chunk = chunk
        self.gen = torch.Generator().manual_seed(seed)
        self.pending = None
        self.t_submit = 0.0
        self.total = 0

    def submit(self, pos: dict, slots: torch.Tensor) -> int:
        """Sample up to per_iter positions with <= max_empty empties in open boards and solve them asynchronously."""
        e = empties_in_open_boards_t(pos["cells"], pos["macro"])
        cand = torch.nonzero(e <= self.max_empty).squeeze(1).cpu()
        if cand.numel() > self.per_iter:
            cand = cand[torch.randperm(cand.numel(), generator=self.gen)[: self.per_iter]]
        if cand.numel() == 0:
            return 0
        cand_d = cand.to(pos["cells"].device)
        cells = pos["cells"][cand_d].cpu().numpy()
        macro = pos["macro"][cand_d].cpu().numpy()
        nb = pos["next_board"][cand_d].cpu().numpy()
        player = pos["player"][cand_d].cpu().numpy()
        k = len(cand)
        chunks = [(cells[i : i + self.chunk], macro[i : i + self.chunk], nb[i : i + self.chunk], player[i : i + self.chunk])
                  for i in range(0, k, self.chunk)]
        self.pending = (slots[cand_d].cpu(), self.pool.map_async(partial(solve_batch, rule=self.rule), chunks))
        self.t_submit = time.perf_counter()
        return k

    def collect(self):
        """Wait for the pending batch; returns (slots (k,) cpu long, values (k,) int8 numpy, policies (k,81) f16 numpy)."""
        if self.pending is None:
            return None
        slots, res = self.pending
        self.pending = None
        parts = res.get()
        vals = np.concatenate([p[0] for p in parts])
        pol = np.concatenate([p[1] for p in parts])
        self.total += len(vals)
        return slots, vals, pol

    def close(self) -> None:
        self.pool.close()
        self.pool.join()
