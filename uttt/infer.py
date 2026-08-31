"""Inference-only network copy for the search: BatchNorm folded into the convolutions,
fp16 weights (no autocast casts), channels_last memory format.

    fe = FusedEvaluator(net, device)      # snapshot of the training net
    fe.refresh(net)                       # re-snapshot after training steps
"""
from __future__ import annotations

import copy

import torch
import torch.nn as nn
from torch.nn.utils.fusion import fuse_conv_bn_eval

from .batch import INV_PERM, encode, legal_mask
from .model import ResBlock


def _fuse(model: nn.Module) -> nn.Module:
    m = copy.deepcopy(model).eval()
    for mod in m.modules():
        if isinstance(mod, ResBlock):
            mod.c1 = fuse_conv_bn_eval(mod.c1, mod.b1)
            mod.b1 = nn.Identity()
            mod.c2 = fuse_conv_bn_eval(mod.c2, mod.b2)
            mod.b2 = nn.Identity()
        elif isinstance(mod, nn.Sequential) and len(mod) >= 2 and isinstance(mod[0], nn.Conv2d) and isinstance(mod[1], nn.BatchNorm2d):
            mod[0] = fuse_conv_bn_eval(mod[0], mod[1])
            mod[1] = nn.Identity()
    return m


class FusedEvaluator:
    def __init__(self, net: nn.Module, device, half: bool = True, channels_last: bool = True, wdl_bias=None) -> None:
        self.device = torch.device(device)
        self.half = half and self.device.type == "cuda"
        self.channels_last = channels_last
        self._inv = INV_PERM.to(self.device)
        # optional post-hoc calibration: added to the (win, draw, loss) logits before the softmax (tools/calibrate.py)
        self.wdl_bias = None if wdl_bias is None else torch.as_tensor(wdl_bias, dtype=torch.float32, device=self.device).view(1, 3)
        self.refresh(net)

    def refresh(self, net: nn.Module) -> None:
        """Re-snapshot the training net. Weights are copied IN PLACE once the module exists,
        so CUDA graphs that captured this evaluator keep seeing the current weights."""
        m = _fuse(net).to(self.device)
        self.extra = net.cfg.extra_planes
        if self.half:
            m = m.half()
        if self.channels_last:
            m = m.to(memory_format=torch.channels_last)
        if getattr(self, "net", None) is None:
            self.net = m
        else:
            with torch.no_grad():
                for dst, src in zip(self.net.parameters(), m.parameters()):
                    dst.copy_(src)
                for dst, src in zip(self.net.buffers(), m.buffers()):
                    dst.copy_(src)

    @torch.no_grad()
    def __call__(self, cells, macro, next_board, player, done):
        legal = legal_mask(cells, macro, next_board, done)
        obs = encode(cells, macro, next_board, player, done, extra=self.extra)
        if self.half:
            obs = obs.half()
        if self.channels_last:
            obs = obs.contiguous(memory_format=torch.channels_last)
        p_logits, v_logits, *_ = self.net(obs)
        p_logits = p_logits.float()[:, self._inv].masked_fill(~legal, float("-inf"))
        probs = torch.nan_to_num(torch.softmax(p_logits, dim=1), nan=0.0)
        v_logits = v_logits.float()
        if self.wdl_bias is not None:
            v_logits = v_logits + self.wdl_bias
        wdl = torch.softmax(v_logits, dim=1)
        return probs, wdl[:, 0] - wdl[:, 2]
