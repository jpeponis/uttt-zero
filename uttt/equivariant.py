"""Exactly D4-equivariant network parts (PLAN6 §4, arms (d) and (e); REVIEW-astra §5.3).

The group is the diagonal D4 of uttt.batch: the same rotation / reflection on the board index and the cell index,
which on the 9×9 grid of the encoder is the ordinary rotation / reflection of the image. Two constructions:

* TiedLinear — a dense map between grid-indexed (or board-indexed, or invariant) feature vectors whose weights are
  tied over the orbits of index pairs under the simultaneous action: W[g a, g b] = W[a, b], b[g a] = b[a]. For the
  81 → 81 policy map that is 861 orbits instead of 6561 weights per channel (the review's count). A ResNet whose four
  heads are tied this way (TiedResNet, arm (d)) has equivariant read-outs on an ordinary, non-equivariant trunk.
* GConv2d / GBatchNorm / GResBlock / GResNet — a regular-representation group-convolutional ResNet (Cohen & Welling
  2016): every base filter carries 8 orientation channels that permute with the transformation, the 3×3 kernels are
  one bank per (out, in, orientation) rotated / reflected into place, BatchNorm statistics and affine parameters are
  shared across the 8 orientations, and the heads pool the orientation axis before tied read-outs. Exactly
  equivariant by construction: policy and ownership transform with the board, value and margin are invariant.

Both export() to ordinary modules — plain Conv2d / BatchNorm2d / Linear with the expanded weights — so
uttt.infer.FusedEvaluator (BN folding, fp16, channels_last, CUDA graphs) is untouched and the inference cost is
exactly that of an ordinary ResNet of the expanded width (GResNet with 16 base filters = a 128-filter ResNet in
FLOPs, with 8× fewer trunk parameters). tests/test_equivariant.py checks the laws, the export and the fused path.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .batch import INV_PERM, PERM, SYM_BOARD, SYM_CELL, _D4
from .openings import compose, inverse

# ---- the group on the objects the network indexes ------------------------------------------------------------
GRID = INV_PERM[SYM_CELL[:, PERM]].numpy()  # (8, 81): image of grid position y under s, in grid coordinates
BOARD = SYM_BOARD.numpy()  # (8, 9): image of board b
INVARIANT = np.zeros((8, 1), dtype=np.int64)  # a one-point set: invariant outputs
ORIENT = np.array([[compose(inverse(g), h) for h in range(8)] for g in range(8)], dtype=np.int64)  # g^-1 h


def _kernel_perms(k: int) -> np.ndarray:
    """(8, k*k): the rotated / reflected kernel K_g satisfies K_g.flat[y] = K.flat[KER[g][y]] (K_g(y) = K(g^-1 y))."""
    out = np.zeros((8, k * k), dtype=np.int64)
    for g in range(8):
        f = _D4[inverse(g)]
        for i in range(k):
            for j in range(k):
                if k == 1:
                    out[g, 0] = 0
                else:
                    i2, j2 = f(i, j)
                    out[g, i * k + j] = i2 * k + j2
    return out


def pair_orbits(act_a: np.ndarray, act_b: np.ndarray) -> tuple[np.ndarray, int]:
    """Orbit id of every pair (a, b) under the simultaneous action (act_a[s][a], act_b[s][b]); returns ((A, B) ids, count)."""
    A, B = act_a.shape[1], act_b.shape[1]
    key = np.full((A, B), np.iinfo(np.int64).max, dtype=np.int64)
    for s in range(8):
        img = act_a[s][:, None] * B + act_b[s][None, :]
        key = np.minimum(key, img)
    uniq, ids = np.unique(key, return_inverse=True)
    return ids.reshape(A, B), len(uniq)


class TiedLinear(nn.Module):
    """(N, in_ch * P_in) -> (N, P_out * out_k), weights tied over orbits of (output position, input position).

    act_in / act_out: (8, P) tables of the group action on the input / output index (GRID, BOARD or INVARIANT).
    The input is a flattened (N, in_ch, P_in) tensor (channel-major, as x.flatten(1) of (N, C, 9, 9)); the output is
    position-major (N, P_out, out_k) flattened, so a (9, classes) ownership head reads .view(-1, 9, classes)."""

    def __init__(self, in_ch: int, act_in: np.ndarray, out_k: int, act_out: np.ndarray) -> None:
        super().__init__()
        ids, n_orb = pair_orbits(act_out, act_in)  # (P_out, P_in)
        bias_ids, n_bias = pair_orbits(act_out, INVARIANT)
        self.in_ch, self.out_k = in_ch, out_k
        self.P_out, self.P_in = ids.shape
        self.register_buffer("ids", torch.from_numpy(ids), persistent=False)
        self.register_buffer("bias_ids", torch.from_numpy(bias_ids[:, 0]), persistent=False)
        bound = 1.0 / np.sqrt(in_ch * self.P_in)
        self.bank = nn.Parameter(torch.empty(n_orb, out_k, in_ch).uniform_(-bound, bound))
        self.bias_bank = nn.Parameter(torch.empty(n_bias, out_k).uniform_(-bound, bound))

    def expanded(self):
        W = self.bank[self.ids]  # (P_out, P_in, out_k, in_ch)
        W = W.permute(0, 2, 3, 1).reshape(self.P_out * self.out_k, self.in_ch * self.P_in)
        b = self.bias_bank[self.bias_ids].reshape(self.P_out * self.out_k)
        return W, b

    def forward(self, x):
        W, b = self.expanded()
        return F.linear(x, W, b)

    def export(self) -> nn.Linear:
        lin = nn.Linear(self.in_ch * self.P_in, self.P_out * self.out_k).to(self.bank.device)
        with torch.no_grad():
            W, b = self.expanded()
            lin.weight.copy_(W)
            lin.bias.copy_(b)
        return lin


class GConv2d(nn.Module):
    """Group convolution on the regular representation. lift=True: scalar input planes -> out_base x 8 orientations;
    otherwise (in_base x 8) -> (out_base x 8). Channel index = base * 8 + orientation."""

    def __init__(self, in_base: int, out_base: int, k: int, lift: bool = False) -> None:
        super().__init__()
        self.in_base, self.out_base, self.k, self.lift = in_base, out_base, k, lift
        n_or = 1 if lift else 8
        fan_in = in_base * n_or * k * k
        self.bank = nn.Parameter(torch.randn(out_base, in_base, n_or, k * k) * np.sqrt(2.0 / fan_in))
        self.register_buffer("ker", torch.from_numpy(_kernel_perms(k)), persistent=False)  # (8, k*k)
        self.register_buffer("orient", torch.from_numpy(ORIENT), persistent=False)  # (8, 8)

    def expanded(self):
        O, I, k = self.out_base, self.in_base, self.k
        if self.lift:
            W = self.bank[:, :, 0, :][:, None, :, :].expand(O, 8, I, k * k)  # (O, g, I, kk)
            W = torch.gather(W, 3, self.ker[None, :, None, :].expand(O, 8, I, k * k))
            return W.reshape(O * 8, I, k, k)
        W = self.bank[:, :, self.orient, :]  # (O, I, g, h, kk): bank[o, i, g^-1 h]
        W = W.permute(0, 2, 1, 3, 4)  # (O, g, I, h, kk)
        W = torch.gather(W, 4, self.ker[None, :, None, None, :].expand(O, 8, I, 8, k * k))
        return W.reshape(O * 8, I * 8, k, k)

    def forward(self, x):
        return F.conv2d(x, self.expanded(), padding=self.k // 2)

    def export(self) -> nn.Conv2d:
        conv = nn.Conv2d(self.in_base * (1 if self.lift else 8), self.out_base * 8, self.k, padding=self.k // 2, bias=False).to(self.bank.device)
        with torch.no_grad():
            conv.weight.copy_(self.expanded())
        return conv


class GBatchNorm(nn.Module):
    """BatchNorm over base filters, statistics and affine parameters shared across the 8 orientation channels."""

    def __init__(self, base: int) -> None:
        super().__init__()
        self.base = base
        self.bn = nn.BatchNorm2d(base)

    def forward(self, x):
        N, C, H, W = x.shape
        return self.bn(x.reshape(N, self.base, 8 * H, W)).reshape(N, C, H, W)

    def export(self) -> nn.BatchNorm2d:
        bn = nn.BatchNorm2d(self.base * 8).to(self.bn.weight.device)
        with torch.no_grad():
            for k in ("weight", "bias", "running_mean", "running_var"):
                getattr(bn, k).copy_(getattr(self.bn, k).repeat_interleave(8))
            bn.num_batches_tracked.copy_(self.bn.num_batches_tracked)
        return bn.train(self.training)


class GResBlock(nn.Module):
    def __init__(self, base: int) -> None:
        super().__init__()
        self.c1, self.b1 = GConv2d(base, base, 3), GBatchNorm(base)
        self.c2, self.b2 = GConv2d(base, base, 3), GBatchNorm(base)

    def forward(self, x):
        y = F.relu(self.b1(self.c1(x)))
        y = self.b2(self.c2(y))
        return F.relu(x + y)

    def export(self):
        from .model import ResBlock

        blk = ResBlock(self.c1.out_base * 8)
        blk.c1, blk.b1, blk.c2, blk.b2 = self.c1.export(), self.b1.export(), self.c2.export(), self.b2.export()
        return blk


def orientation_pool(base: int) -> nn.Conv2d:
    """A fixed 1x1 convolution averaging the 8 orientation channels of every base filter (an invariant read-out
    per position; kept as a Conv2d so the exported net is convolutions end to end)."""
    conv = nn.Conv2d(base * 8, base, 1, bias=False)
    with torch.no_grad():
        conv.weight.zero_()
        for b in range(base):
            conv.weight[b, b * 8 : (b + 1) * 8, 0, 0] = 1.0 / 8
    conv.weight.requires_grad_(False)
    return conv


class _HeadsMixin:
    """The forward shared by the equivariant nets and their exports (heads on orientation-pooled scalar fields)."""

    def forward(self, x):
        h = self.blocks(self.stem(x))
        p = self.p_fc(self.p_pool(self.p_conv(h)).flatten(1))
        vh = self.v_pool(self.v_conv(h)).flatten(1)
        v = self.v_fc2(F.relu(self.v_fc1(vh)))
        o = self.o_fc(vh).view(-1, 9, self.cfg.own_classes)
        m = self.m_fc(vh)
        return p, v, o, m


class PlainNet(_HeadsMixin, nn.Module):
    """What GResNet exports to: ordinary modules only, the same forward."""

    def __init__(self, cfg, stem, blocks, p_conv, p_pool, p_fc, v_conv, v_pool, v_fc1, v_fc2, o_fc, m_fc) -> None:
        nn.Module.__init__(self)
        self.cfg = cfg
        self.stem, self.blocks, self.p_conv, self.p_pool, self.p_fc = stem, blocks, p_conv, p_pool, p_fc
        self.v_conv, self.v_pool, self.v_fc1, self.v_fc2, self.o_fc, self.m_fc = v_conv, v_pool, v_fc1, v_fc2, o_fc, m_fc


class GResNet(_HeadsMixin, nn.Module):
    """Arm (e): cfg.gcnn base filters x 8 orientations (activation width 8 * gcnn = cfg.filters), cfg.blocks blocks."""

    def __init__(self, cfg) -> None:
        nn.Module.__init__(self)
        from .model import MARGIN_BINS

        assert cfg.gcnn > 0 and cfg.filters == 8 * cfg.gcnn, "set filters = 8 * gcnn (the activation width)"
        self.cfg = cfg
        B, pc, vc = cfg.gcnn, cfg.policy_channels, cfg.value_channels
        self.stem = nn.Sequential(GConv2d(cfg.n_planes, B, 3, lift=True), GBatchNorm(B), nn.ReLU())
        self.blocks = nn.Sequential(*[GResBlock(B) for _ in range(cfg.blocks)])
        self.p_conv = nn.Sequential(GConv2d(B, pc, 1), GBatchNorm(pc), nn.ReLU())
        self.p_pool = orientation_pool(pc)
        self.p_fc = TiedLinear(pc, GRID, 1, GRID)
        self.v_conv = nn.Sequential(GConv2d(B, vc, 1), GBatchNorm(vc), nn.ReLU())
        self.v_pool = orientation_pool(vc)
        self.v_fc1 = TiedLinear(vc, GRID, cfg.value_hidden, INVARIANT)
        self.v_fc2 = nn.Linear(cfg.value_hidden, 3)
        self.o_fc = TiedLinear(vc, GRID, cfg.own_classes, BOARD)
        self.m_fc = TiedLinear(vc, GRID, MARGIN_BINS, INVARIANT)

    def export(self) -> PlainNet:
        seq = lambda s: nn.Sequential(s[0].export(), s[1].export(), nn.ReLU())  # noqa: E731
        plain = PlainNet(self.cfg, seq(self.stem), nn.Sequential(*[b.export() for b in self.blocks]), seq(self.p_conv), self.p_pool,
                         self.p_fc.export(), seq(self.v_conv), self.v_pool, self.v_fc1.export(), self.v_fc2, self.o_fc.export(),
                         self.m_fc.export())
        return plain.train(self.training)


def tie_heads(net) -> None:
    """Arm (d): replace an ordinary ResNet's four head Linears by tied ones (in place). The trunk stays as it is."""
    from .model import MARGIN_BINS

    cfg = net.cfg
    net.p_fc = TiedLinear(cfg.policy_channels, GRID, 1, GRID)
    net.v_fc1 = TiedLinear(cfg.value_channels, GRID, cfg.value_hidden, INVARIANT)
    net.o_fc = TiedLinear(cfg.value_channels, GRID, cfg.own_classes, BOARD)
    net.m_fc = TiedLinear(cfg.value_channels, GRID, MARGIN_BINS, INVARIANT)


def export_plain(m: nn.Module) -> nn.Module:
    """Replace every module that knows how to export itself (tied heads on an ordinary ResNet) by its plain form."""
    if hasattr(m, "export"):
        return m.export()
    for name, child in list(m.named_children()):
        if hasattr(child, "export"):
            setattr(m, name, child.export())
    return m
