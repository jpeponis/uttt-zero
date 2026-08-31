"""Lock-step self-play of n games with batched MCTS, producing training examples."""
from __future__ import annotations

from dataclasses import dataclass

import torch

from .batch import BatchUTTT
from .mcts import BatchedMCTS, MCTSConfig


@dataclass
class SelfPlayBatch:
    cells: torch.Tensor  # (P, 81) int8
    macro: torch.Tensor  # (P, 9) int8
    next_board: torch.Tensor  # (P,) int8
    player: torch.Tensor  # (P,) int8
    policy: torch.Tensor  # (P, 81) float16
    value: torch.Tensor  # (P,) int8   +1 win / 0 draw / -1 loss for side to move
    ownership: torch.Tensor  # (P, 9) int8  final local-board status relative to side to move
    ply: torch.Tensor  # (P,) int16
    game_id: torch.Tensor  # (P,) int32  index of the game within this batch
    # per-game statistics
    winners: torch.Tensor  # (n,) int8
    reasons: torch.Tensor  # (n,) int8
    lengths: torch.Tensor  # (n,) int16
    first_moves: torch.Tensor  # (n,) int64
    surprise: float  # mean |root_value - raw_value|

    def __len__(self) -> int:
        return self.cells.shape[0]


@torch.no_grad()
def selfplay(evaluator, n: int, cfg: MCTSConfig, device, mcts: BatchedMCTS | None = None) -> SelfPlayBatch:
    d = torch.device(device)
    g = BatchUTTT(n, d)
    mcts = mcts or BatchedMCTS(evaluator, n, cfg, d)
    rec = {k: [] for k in ("cells", "macro", "next_board", "player", "policy", "ply", "game_id")}
    surprise, steps = 0.0, 0
    first_moves = None
    ply = 0
    while not bool(g.done.all()):
        active = ~g.done
        res = mcts.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=True, ply=ply)
        rec["cells"].append(g.cells[active])
        rec["macro"].append(g.macro[active])
        rec["next_board"].append(g.next_board[active])
        rec["player"].append(g.player[active])
        rec["policy"].append(res.policy[active].half())
        rec["ply"].append(torch.full((int(active.sum()),), ply, dtype=torch.int16, device=d))
        rec["game_id"].append(torch.nonzero(active).squeeze(1).to(torch.int32))
        surprise += float((res.root_value - res.raw_value).abs()[active].mean())
        steps += 1
        if first_moves is None:
            first_moves = res.action.clone()
        g.step(res.action)
        ply += 1
    out = {k: torch.cat(v) for k, v in rec.items()}
    gid = out["game_id"].long()
    z = (g.winner[gid] * out["player"]).to(torch.int8)
    final_macro = g.macro[gid]  # (P, 9)
    p = out["player"].unsqueeze(1)
    own = torch.where(final_macro == p, 1, torch.where(final_macro == -p, -1, 0)).to(torch.int8)
    return SelfPlayBatch(
        cells=out["cells"], macro=out["macro"], next_board=out["next_board"], player=out["player"],
        policy=out["policy"], value=z, ownership=own, ply=out["ply"], game_id=out["game_id"],
        winners=g.winner.clone(), reasons=g.end_reason.clone(), lengths=g.move_count.clone(),
        first_moves=first_moves, surprise=surprise / max(steps, 1),
    )


class ReplayBuffer:
    """Ring buffer of positions held on the CPU (pinned) with a fixed capacity."""

    FIELDS = ("cells", "macro", "next_board", "player", "policy", "value", "ownership", "ply")

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.size = 0
        self.pos = 0
        self.buf = {
            "cells": torch.zeros(capacity, 81, dtype=torch.int8),
            "macro": torch.zeros(capacity, 9, dtype=torch.int8),
            "next_board": torch.zeros(capacity, dtype=torch.int8),
            "player": torch.zeros(capacity, dtype=torch.int8),
            "policy": torch.zeros(capacity, 81, dtype=torch.float16),
            "value": torch.zeros(capacity, dtype=torch.int8),
            "ownership": torch.zeros(capacity, 9, dtype=torch.int8),
            "ply": torch.zeros(capacity, dtype=torch.int16),
        }

    def add(self, b: SelfPlayBatch) -> None:
        m = len(b)
        idx = (torch.arange(m) + self.pos) % self.capacity
        for k in self.FIELDS:
            self.buf[k][idx] = getattr(b, k).cpu()
        self.pos = (self.pos + m) % self.capacity
        self.size = min(self.size + m, self.capacity)

    def sample(self, batch_size: int, device):
        idx = torch.randint(0, self.size, (batch_size,))
        return {k: self.buf[k][idx].to(device, non_blocking=True) for k in self.FIELDS}

    def state_dict(self):
        return {"size": self.size, "pos": self.pos, "buf": {k: v[: self.size] for k, v in self.buf.items()}}

    def load_state_dict(self, sd) -> None:
        n = sd["size"]
        for k in self.FIELDS:
            self.buf[k][:n] = sd["buf"][k]
        self.size, self.pos = n, sd["pos"] % self.capacity
