"""Residual policy/value network for UTTT and evaluator wrappers used by the search.

Outputs:
  policy logits (n, 81) in GRID order (the evaluator converts to engine order),
  value logits  (n, 3)  = win / draw / loss from the side-to-move's perspective,
  ownership logits (n, 9, 3) = for each local board (engine order), final status
      self-won / neither / opponent-won  (KataGo-style auxiliary target),
  margin logits (n, MARGIN_BINS) = final won-board difference (self minus opponent),
      bins -9..+9 (the quantity the most-boards tiebreak is decided by).
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

from .batch import INV_PERM, N_PLANES, encode, legal_mask

MARGIN_BINS = 19  # won-board margin -9..+9


@dataclass
class NetConfig:
    blocks: int = 6
    filters: int = 64
    policy_channels: int = 4
    value_channels: int = 4
    value_hidden: int = 128
    n_planes: int = N_PLANES  # 7, or 9 with the first-player and count-difference planes (encode extra=True)
    own_classes: int = 3  # 3: self-won / neither / opponent-won; 4: self-won / opponent-won / drawn-full / open at the end
    mask_closed: int = 0  # 1: the encoder zeroes the stone planes inside closed boards (PLAN6 G arm (c) / H2)

    @property
    def extra_planes(self) -> bool:
        return self.n_planes > N_PLANES


class ResBlock(nn.Module):
    def __init__(self, f: int) -> None:
        super().__init__()
        self.c1 = nn.Conv2d(f, f, 3, padding=1, bias=False)
        self.b1 = nn.BatchNorm2d(f)
        self.c2 = nn.Conv2d(f, f, 3, padding=1, bias=False)
        self.b2 = nn.BatchNorm2d(f)

    def forward(self, x):
        y = F.relu(self.b1(self.c1(x)))
        y = self.b2(self.c2(y))
        return F.relu(x + y)


class ResNet(nn.Module):
    def __init__(self, cfg: NetConfig = NetConfig()) -> None:
        super().__init__()
        self.cfg = cfg
        f = cfg.filters
        self.stem = nn.Sequential(nn.Conv2d(cfg.n_planes, f, 3, padding=1, bias=False), nn.BatchNorm2d(f), nn.ReLU())
        self.blocks = nn.Sequential(*[ResBlock(f) for _ in range(cfg.blocks)])
        pc, vc = cfg.policy_channels, cfg.value_channels
        self.p_conv = nn.Sequential(nn.Conv2d(f, pc, 1, bias=False), nn.BatchNorm2d(pc), nn.ReLU())
        self.p_fc = nn.Linear(pc * 81, 81)
        self.v_conv = nn.Sequential(nn.Conv2d(f, vc, 1, bias=False), nn.BatchNorm2d(vc), nn.ReLU())
        self.v_fc1 = nn.Linear(vc * 81, cfg.value_hidden)
        self.v_fc2 = nn.Linear(cfg.value_hidden, 3)
        self.o_fc = nn.Linear(vc * 81, 9 * cfg.own_classes)
        self.m_fc = nn.Linear(vc * 81, MARGIN_BINS)

    def forward(self, x):
        h = self.blocks(self.stem(x))
        p = self.p_fc(self.p_conv(h).flatten(1))
        vh = self.v_conv(h).flatten(1)
        v = self.v_fc2(F.relu(self.v_fc1(vh)))
        o = self.o_fc(vh).view(-1, 9, self.cfg.own_classes)
        m = self.m_fc(vh)
        return p, v, o, m


def load_checkpoint(path: str, device) -> ResNet:
    """Build the ResNet a checkpoint describes (blocks, filters, n_planes, own_classes from its cfg) and load its weights.

    The construction initialises layers (and so consumes CPU RNG) before the weights are replaced; that is done under
    fork_rng so loading an anchor or a candidate never moves the caller's random stream (PLAN6 E4)."""
    ck = torch.load(path, map_location=device, weights_only=False)
    cfg = ck.get("cfg", {})
    with torch.random.fork_rng(devices=[]):
        net = ResNet(NetConfig(blocks=cfg.get("blocks", 6), filters=cfg.get("filters", 64), n_planes=cfg.get("n_planes", N_PLANES),
                               own_classes=cfg.get("own_classes", 3), mask_closed=cfg.get("mask_closed", 0)))
    net.load_state_dict(ck["net"], strict=False)
    return net.to(device).eval()


class Evaluator:
    """Wraps a network: batched (state) -> (policy probs in engine order, scalar value)."""

    def __init__(self, net: nn.Module, device, amp: bool = True) -> None:
        self.net = net.to(device).eval()
        self.device = torch.device(device)
        self.amp = amp and self.device.type == "cuda"
        self._inv = INV_PERM.to(device)

    @torch.no_grad()
    def __call__(self, cells, macro, next_board, player, done):
        obs = encode(cells, macro, next_board, player, done, extra=self.net.cfg.extra_planes, mask_closed=bool(self.net.cfg.mask_closed))
        legal = legal_mask(cells, macro, next_board, done)
        with torch.autocast("cuda", dtype=torch.float16, enabled=self.amp):
            p_logits, v_logits, *_ = self.net(obs)
        p_logits = p_logits.float()[:, self._inv]  # engine order
        p_logits = p_logits.masked_fill(~legal, float("-inf"))
        probs = torch.softmax(p_logits, dim=1)
        probs = torch.nan_to_num(probs, nan=0.0)  # rows with no legal move (finished games)
        wdl = torch.softmax(v_logits.float(), dim=1)
        value = wdl[:, 0] - wdl[:, 2]
        return probs, value


class UniformEvaluator:
    """Uniform policy over legal moves, value 0 — turns the search into plain UCT for tests."""

    def __init__(self, device) -> None:
        self.device = torch.device(device)

    def __call__(self, cells, macro, next_board, player, done):
        legal = legal_mask(cells, macro, next_board, done).float()
        probs = legal / legal.sum(1, keepdim=True).clamp(min=1)
        return probs, torch.zeros(cells.shape[0], device=cells.device)
