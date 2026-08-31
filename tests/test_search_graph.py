"""CUDA-graph mode of the v2 search must reproduce eager mode exactly, and be faster."""
import os
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import NetConfig, ResNet, UniformEvaluator  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def positions(n, plies, seed=0):
    torch.manual_seed(seed)
    g = BatchUTTT(n, DEV)
    for _ in range(plies):
        m = g.legal_mask().float() + 1e-9
        g.step(torch.multinomial(m, 1).squeeze(1))
    return g


def compare(mode, sims, n=1024, net=False, selfplay=True, depth_cap=32):
    g = positions(n, 10)
    ev = FusedEvaluator(ResNet(NetConfig()).to(DEV), DEV) if net else UniformEvaluator(DEV)
    eager = BatchedSearch(ev, n, SearchConfig(n_sims=sims, mode=mode, depth_cap=depth_cap), DEV)
    graphed = BatchedSearch(ev, n, SearchConfig(n_sims=sims, mode=mode, depth_cap=depth_cap, cuda_graph=True), DEV)
    args = (g.cells, g.macro, g.next_board, g.player, g.done, g.winner)
    outs = []
    for s in (eager, graphed, graphed):  # graphed twice: capture pass, then pure replay
        torch.manual_seed(1)
        outs.append(s.search(*args, selfplay=selfplay))
    for k, r in enumerate(outs[1:]):
        ok = (torch.equal(outs[0].visits, r.visits), torch.allclose(outs[0].policy, r.policy, atol=1e-5),
              torch.allclose(outs[0].root_value, r.root_value, atol=1e-5), torch.equal(outs[0].action, r.action))
        print(f"{mode:6s} sims={sims:3d} net={net!s:5s} pass {k + 1}: visits {ok[0]} policy {ok[1]} value {ok[2]} action {ok[3]}")
        assert all(ok)


def test_refresh_in_place(n=256):
    g = positions(n, 8)
    net = ResNet(NetConfig()).to(DEV)
    fe = FusedEvaluator(net, DEV)
    s = BatchedSearch(fe, n, SearchConfig(n_sims=16, mode="gumbel", cuda_graph=True), DEV)
    args = (g.cells, g.macro, g.next_board, g.player, g.done, g.winner)
    torch.manual_seed(1)
    r1 = s.search(*args, selfplay=False)
    with torch.no_grad():
        for p in net.parameters():
            p.add_(torch.randn_like(p) * 0.05)
    fe.refresh(net)
    torch.manual_seed(1)
    r2 = s.search(*args, selfplay=False)
    ref = BatchedSearch(FusedEvaluator(net, DEV), n, SearchConfig(n_sims=16, mode="gumbel"), DEV)
    torch.manual_seed(1)
    r3 = ref.search(*args, selfplay=False)
    assert not torch.allclose(r1.raw_value, r2.raw_value), "refresh had no effect"
    assert torch.equal(r2.visits, r3.visits) and torch.allclose(r2.raw_value, r3.raw_value, atol=1e-5)
    print("in-place weight refresh is seen by captured graphs")


def bench(n=4096, sims=32, net=True):
    g = positions(n, 6)
    ev = FusedEvaluator(ResNet(NetConfig()).to(DEV), DEV) if net else UniformEvaluator(DEV)
    args = (g.cells, g.macro, g.next_board, g.player, g.done, g.winner)
    for name, cfg in (("eager", SearchConfig(n_sims=sims, mode="gumbel")),
                      ("graph", SearchConfig(n_sims=sims, mode="gumbel", cuda_graph=True, depth_cap=12))):
        s = BatchedSearch(ev, n, cfg, DEV)
        s.search(*args, selfplay=True)
        torch.cuda.synchronize(DEV)
        t = time.perf_counter()
        for _ in range(3):
            s.search(*args, selfplay=True)
        torch.cuda.synchronize(DEV)
        dt = (time.perf_counter() - t) / 3
        print(f"{name} {'fused net' if net else 'uniform'}: {n} trees x {sims} sims: {dt:.2f}s = {dt / sims * 1000:.1f} ms/sim")


if __name__ == "__main__":
    compare("gumbel", 32)
    compare("puct", 32)
    compare("gumbel", 32, net=True)
    compare("gumbel", 64, net=True, selfplay=False)
    test_refresh_in_place()
    bench(net=False)
    bench(net=True)
    print("ok")
