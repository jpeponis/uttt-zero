"""Data hygiene (PLAN2 §5 step 4): symmetric dedup hash, extra input planes, 4-class ownership, checkpoint loader."""
import os
import sys
import tempfile

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import FULL, N_PLANES, BatchUTTT, apply_symmetry, encode  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import NetConfig, ResNet, load_checkpoint  # noqa: E402
from uttt.model import Evaluator  # noqa: E402
from uttt.selfplay_cont import GPUReplayBuffer, position_hash, position_hash_sym  # noqa: E402
from uttt.train2 import OWN_CLASS  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def positions(n, plies, seed=0):
    torch.manual_seed(seed)
    g = BatchUTTT(n, DEV)
    for _ in range(plies):
        m = g.legal_mask().float() + 1e-9
        g.step(torch.multinomial(m, 1).squeeze(1))
    return g


def test_sym_hash(n=512):
    g = positions(n, 20)
    h = position_hash_sym(g.cells, g.next_board, g.player)
    for s in range(8):
        c, m, nb = apply_symmetry(s, g.cells, g.macro, g.next_board)
        assert torch.equal(position_hash_sym(c, nb, g.player), h), s
    # plain hashes of the images differ (unless the position is itself symmetric), the symmetric one does not
    c, m, nb = apply_symmetry(1, g.cells, g.macro, g.next_board)
    assert float((position_hash(c, nb, g.player) != position_hash(g.cells, g.next_board, g.player)).float().mean()) > 0.9
    assert len(torch.unique(h)) > 0.9 * n  # different positions still hash apart
    print("symmetric hash ok")


def test_extra_planes(n=256):
    g = positions(n, 30)
    obs = encode(g.cells, g.macro, g.next_board, g.player, g.done, extra=True)
    base = encode(g.cells, g.macro, g.next_board, g.player, g.done)
    assert obs.shape == (n, 9, 9, 9) and torch.equal(obs[:, :N_PLANES], base)
    is_x = (g.player == 1).float()
    assert torch.equal(obs[:, 7].flatten(1).mean(1), is_x)
    p = g.player.view(n, 1)
    diff = ((g.macro == p).sum(1) - (g.macro == -p).sum(1)).float() / 4
    assert torch.allclose(obs[:, 8].flatten(1).mean(1), diff)
    assert float((obs[:, 8, 0, 0] != 0).float().mean()) > 0.2  # some boards are won by ply 30
    print("extra planes ok")


def test_own_classes():
    m3 = torch.tensor(OWN_CLASS[3])
    m4 = torch.tensor(OWN_CLASS[4])
    own = torch.tensor([-1, 0, 1, 2])  # opponent / open / self / full-drawn
    assert m3[own + 1].tolist() == [2, 1, 0, 1]  # old 3-way: opponent-won 2, neither 1, self-won 0
    old = (1 - own[:3]).clamp(0, 2)
    assert torch.equal(m3[own[:3] + 1], old)  # identical to the previous mapping on {-1, 0, 1}
    assert m4[own + 1].tolist() == [1, 3, 0, 2] and len(set(m4.tolist())) == 4
    print("ownership class maps ok")


def test_nets_and_loader(n=64):
    g = positions(n, 12)
    with tempfile.TemporaryDirectory() as tmp:
        for cfg in (NetConfig(blocks=2, filters=16), NetConfig(blocks=2, filters=16, n_planes=9, own_classes=4)):
            net = ResNet(cfg).to(DEV).eval()
            obs = encode(g.cells, g.macro, g.next_board, g.player, g.done, extra=cfg.extra_planes)
            p, v, o, m = net(obs)
            assert p.shape == (n, 81) and v.shape == (n, 3) and o.shape == (n, 9, cfg.own_classes)
            path = os.path.join(tmp, f"net{cfg.n_planes}.pt")
            torch.save({"net": net.state_dict(), "cfg": {"blocks": 2, "filters": 16, "n_planes": cfg.n_planes, "own_classes": cfg.own_classes}}, path)
            net2 = load_checkpoint(path, DEV)
            assert net2.cfg == cfg
            probs, val = FusedEvaluator(net2, DEV)(g.cells, g.macro, g.next_board, g.player, g.done)
            probs_ref, val_ref = Evaluator(net, DEV, amp=False)(g.cells, g.macro, g.next_board, g.player, g.done)
            assert torch.allclose(val, val_ref, atol=2e-2) and torch.allclose(probs, probs_ref, atol=2e-2)
        # an old-style checkpoint without the new cfg keys loads as a 7-plane / 3-class net
        torch.save({"net": ResNet(NetConfig(blocks=2, filters=16)).state_dict(), "cfg": {"blocks": 2, "filters": 16}}, os.path.join(tmp, "old.pt"))
        old = load_checkpoint(os.path.join(tmp, "old.pt"), DEV)
        assert old.cfg.n_planes == 7 and old.cfg.own_classes == 3
    print("net configs / fused inference / loader ok")


def test_alpha_early():
    buf = GPUReplayBuffer(1000, DEV)
    n = 400
    pos = {"cells": torch.zeros(n, 81, dtype=torch.int8, device=DEV), "macro": torch.zeros(n, 9, dtype=torch.int8, device=DEV),
           "next_board": torch.full((n,), -1, dtype=torch.int8, device=DEV), "player": torch.ones(n, dtype=torch.int8, device=DEV),
           "policy": torch.zeros(n, 81, dtype=torch.float16, device=DEV), "value": torch.zeros(n, dtype=torch.int8, device=DEV),
           "ownership": torch.zeros(n, 9, dtype=torch.int8, device=DEV), "margin": torch.zeros(n, dtype=torch.int8, device=DEV),
           "root_value": torch.zeros(n, dtype=torch.float16, device=DEV), "ply": torch.arange(n, device=DEV).to(torch.int16) % 16,
           "hash": (torch.arange(n, device=DEV) % 4),  # 4 identical groups of 100
           "game": torch.arange(n, device=DEV), "iter": torch.zeros(n, dtype=torch.int16, device=DEV)}
    buf.add(pos)
    buf.update_weights(0.5, alpha_early=1.0, early_plies=8)
    w = buf.weights[:n]
    early = pos["ply"] < 8
    assert torch.allclose(w[early], torch.full_like(w[early], 100 ** -1.0)) and torch.allclose(w[~early], torch.full_like(w[~early], 100 ** -0.5))
    print("early-ply alpha ok")


if __name__ == "__main__":
    test_sym_hash()
    test_extra_planes()
    test_own_classes()
    test_nets_and_loader()
    test_alpha_early()
    print("ok")
