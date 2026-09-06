"""The equivariant parts (PLAN6 G arms (d), (e); uttt.equivariant) obey the transformation laws of REVIEW-astra §3.2 —
policy and ownership transform with the board, value and margin are invariant — exactly in fp32, at initialisation
and after optimizer steps; their export() reproduces them; and the exported, fused fp16 net still does within fp16
tolerance. Also the orbit counts the review derived (15 cells, 861 ordered pairs).

Run: .venv/Scripts/python.exe tests/test_equivariant.py   (UTTT_DEV selects the device; the fp16 part needs CUDA)"""
import os
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT, SYM_BOARD, apply_symmetry, encode  # noqa: E402
from uttt.equivariant import BOARD, GRID, INVARIANT, GResNet, TiedLinear, pair_orbits, tie_heads  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import Evaluator, NetConfig, ResNet, build_net  # noqa: E402

DEV = torch.device(os.environ.get("UTTT_DEV", "cuda:0" if torch.cuda.is_available() else "cpu"))
GRID_T = torch.from_numpy(GRID)
torch.backends.cudnn.allow_tf32 = False  # the exact checks are fp32 checks; Ampere's TF32 convolutions are ~1e-3 accurate
torch.backends.cuda.matmul.allow_tf32 = False


def random_games(n, plies, seed=0):
    torch.manual_seed(seed)
    g = BatchUTTT(n, DEV)
    for _ in range(plies):
        g.step(torch.multinomial(g.legal_mask().float() + 1e-9, 1).squeeze(1))
    return g


def test_orbit_counts():
    assert pair_orbits(GRID, INVARIANT)[1] == 15
    assert pair_orbits(GRID, GRID)[1] == 861  # (9^4 + 3 + 4 * 3^4) / 8
    assert pair_orbits(BOARD, INVARIANT)[1] == 3  # corner / edge / centre boards
    print("orbit counts: 15 cells, 861 ordered cell pairs, 3 board classes")


def transported_grid(field, s):
    """field (N, C, 81) in grid order, the image under s brought back: back[:, :, y] = field[:, :, GRID[s][y]]."""
    return field[:, :, GRID_T[s].to(field.device)]


def test_tied_linear(n=64, ch=4):
    torch.manual_seed(1)
    x = torch.randn(n, ch, 81, device=DEV)
    heads = {"policy": TiedLinear(ch, GRID, 1, GRID), "value": TiedLinear(ch, GRID, 16, INVARIANT), "own": TiedLinear(ch, GRID, 3, BOARD)}
    for k, h in heads.items():
        h.to(DEV)
        y0 = h(x.flatten(1))
        for s in range(8):
            xs = torch.zeros_like(x)
            xs[:, :, GRID_T[s].to(DEV)] = x  # the transformed field: value at the image position
            ys = h(xs.flatten(1))
            if k == "policy":
                assert torch.allclose(ys[:, GRID_T[s].to(DEV)], y0, atol=1e-5), (k, s)
            elif k == "value":
                assert torch.allclose(ys, y0, atol=1e-5), (k, s)
            else:
                assert torch.allclose(ys.view(n, 9, 3)[:, SYM_BOARD[s].to(DEV)], y0.view(n, 9, 3), atol=1e-5), (k, s)
        lin = h.export()
        assert torch.allclose(lin(x.flatten(1)), y0, atol=1e-6)
    print("TiedLinear: policy equivariant, value invariant, ownership equivariant; export reproduces it")


def check_laws(net, name, tol, n=128):
    """Raw net outputs on random positions and on every image; policy / ownership transported, value / margin equal."""
    g = random_games(n, 20, seed=2)
    net.eval()
    with torch.no_grad():
        p0, v0, o0, m0 = net(encode(g.cells, g.macro, g.next_board, g.player, g.done))
        for s in range(8):
            c, m, nb = apply_symmetry(s, g.cells, g.macro, g.next_board)
            ps, vs, os_, ms = net(encode(c, m, nb, g.player, g.done))
            assert float((ps[:, GRID_T[s].to(DEV)] - p0).abs().max()) < tol, (name, "policy", s)
            assert float((vs - v0).abs().max()) < tol, (name, "value", s)
            assert float((os_[:, SYM_BOARD[s].to(DEV)] - o0).abs().max()) < tol, (name, "ownership", s)
            assert float((ms - m0).abs().max()) < tol, (name, "margin", s)


def test_gresnet(n=128):
    torch.manual_seed(3)
    cfg = NetConfig(blocks=2, filters=32, gcnn=4)
    net = build_net(cfg).to(DEV)
    assert isinstance(net, GResNet)
    check_laws(net, "GResNet at init", 1e-4)
    # after optimizer steps (BatchNorm statistics included): train on random targets for a few steps
    opt = torch.optim.SGD(net.parameters(), lr=0.01, momentum=0.9)
    g = random_games(256, 15, seed=4)
    x = encode(g.cells, g.macro, g.next_board, g.player, g.done)
    net.train()
    for _ in range(5):
        p, v, o, m = net(x)
        loss = p.logsumexp(1).mean() + v.pow(2).mean() + o.pow(2).mean() + m.pow(2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    check_laws(net, "GResNet after training", 1e-4)
    # export reproduces the net exactly, and is made of ordinary modules
    net.eval()
    plain = net.export().to(DEV).eval()
    with torch.no_grad():
        a, b = net(x[:64]), plain(x[:64])
    assert all(torch.allclose(u, w, atol=1e-4) for u, w in zip(a, b))
    assert all(type(mod).__module__.startswith("torch.nn") for mod in plain.modules() if len(list(mod.children())) == 0)
    n_g = sum(p.numel() for p in net.parameters() if p.requires_grad)
    n_p = sum(p.numel() for p in plain.parameters() if p.requires_grad)
    print(f"GResNet: exact laws at init and after training; export exact; {n_g} parameters expand to {n_p} ({n_p / n_g:.1f}x)")
    return net


def test_tied_heads_resnet():
    torch.manual_seed(5)
    net = build_net(NetConfig(blocks=2, filters=32, head_tying=1)).to(DEV)
    assert isinstance(net, ResNet) and isinstance(net.p_fc, TiedLinear)
    g = random_games(64, 15, seed=6)
    x = encode(g.cells, g.macro, g.next_board, g.player, g.done)
    net.eval()
    with torch.no_grad():
        a = net(x)
        fe = FusedEvaluator(net, DEV, half=False)  # export_plain inside _fuse
    plain_types = {type(m).__name__ for m in fe.net.modules()}
    assert "TiedLinear" not in plain_types
    with torch.no_grad():
        p, v = fe(g.cells, g.macro, g.next_board, g.player, g.done)
    assert p.shape == (64, 81) and torch.isfinite(v).all()
    print("TiedResNet (arm d): tied heads on the ordinary trunk; fused evaluator exports them to Linear")


def test_fused_fp16(net):
    if DEV.type != "cuda":
        print("fused fp16 check skipped (no CUDA)")
        return
    fe = FusedEvaluator(net, DEV)  # exported, BN folded, fp16, channels_last
    g = random_games(256, 18, seed=7)
    p0, v0 = fe(g.cells, g.macro, g.next_board, g.player, g.done)
    from uttt.batch import SYM_CELL
    worst_p = worst_v = 0.0
    for s in range(8):
        c, m, nb = apply_symmetry(s, g.cells, g.macro, g.next_board)
        ps, vs = fe(c, m, nb, g.player, g.done)
        worst_p = max(worst_p, float((ps[:, SYM_CELL[s].to(DEV)] - p0).abs().max()))
        worst_v = max(worst_v, float((vs - v0).abs().max()))
    assert worst_p < 2e-2 and worst_v < 2e-2, (worst_p, worst_v)
    print(f"GResNet fused fp16: equivariance holds to fp16 precision (max |dp| {worst_p:.1e}, |dv| {worst_v:.1e})")


if __name__ == "__main__":
    test_orbit_counts()
    test_tied_linear()
    net = test_gresnet()
    test_tied_heads_resnet()
    test_fused_fp16(net)
    print("ok")
