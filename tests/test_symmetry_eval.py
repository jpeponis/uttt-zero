"""Symmetry-averaged evaluator: exact equivariance and agreement with the base evaluator on average."""
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT, apply_symmetry  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import NetConfig, ResNet  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def main(n=512):
    torch.manual_seed(0)
    g = BatchUTTT(n, DEV)
    for _ in range(14):
        g.step(torch.multinomial(g.legal_mask().float() + 1e-9, 1).squeeze(1))
    net = ResNet(NetConfig())
    ck = "runs/dev1/net_0200.pt"
    if os.path.exists(ck):
        net.load_state_dict(torch.load(ck, map_location="cpu", weights_only=False)["net"], strict=False)
    base = FusedEvaluator(net, DEV, half=False)  # fp32 so equivariance can be checked tightly
    sym = SymmetryAveragedEvaluator(base)
    p0, v0 = sym(g.cells, g.macro, g.next_board, g.player, g.done)
    worst_p, worst_v = 0.0, 0.0
    for s in range(8):
        c2, m2, nb2, p2 = apply_symmetry(s, g.cells, g.macro, g.next_board, p0)
        ps, vs = sym(c2, m2, nb2, g.player, g.done)
        worst_p = max(worst_p, float((ps - p2).abs().max()))
        worst_v = max(worst_v, float((vs - v0).abs().max()))
    print(f"equivariance: max |dp| = {worst_p:.2e}, max |dv| = {worst_v:.2e}")
    assert worst_p < 1e-4 and worst_v < 1e-4
    pb, vb = base(g.cells, g.macro, g.next_board, g.player, g.done)
    print(f"base vs averaged: mean |dv| = {float((vb - v0).abs().mean()):.4f}, max |dv| = {float((vb - v0).abs().max()):.4f}, "
          f"argmax agreement = {float((pb.argmax(1) == p0.argmax(1)).float().mean()):.3f}")
    print("ok")


if __name__ == "__main__":
    main()
