"""Golden test: the v2 search (uttt.search) must reproduce v1 (uttt.mcts) trees exactly, then be faster."""
import os
import sys
import time
import warnings

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.mcts import BatchedMCTS, MCTSConfig  # noqa: E402
from uttt.model import Evaluator, NetConfig, ResNet, UniformEvaluator  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0" if torch.cuda.is_available() else "cpu")


def positions(n, plies, seed=0):
    torch.manual_seed(seed)
    g = BatchUTTT(n, DEV)
    for _ in range(plies):
        m = g.legal_mask().float() + 1e-9
        g.step(torch.multinomial(m, 1).squeeze(1))
    return g


def compare(mode, sims, n=512, plies=12, net=False, selfplay=False, **v2kw):
    g = positions(n, plies)
    ev = Evaluator(ResNet(NetConfig()).to(DEV), DEV) if net else UniformEvaluator(DEV)
    v1 = BatchedMCTS(ev, n, MCTSConfig(n_sims=sims, mode=mode), DEV)
    v2 = BatchedSearch(ev, n, SearchConfig(n_sims=sims, mode=mode, **v2kw), DEV)
    args = (g.cells, g.macro, g.next_board, g.player, g.done, g.winner)
    torch.manual_seed(1)
    r1 = v1.search(*args, selfplay=selfplay)
    torch.manual_seed(1)
    r2 = v2.search(*args, selfplay=selfplay)
    same_visits = torch.equal(r1.visits, r2.visits)
    same_policy = torch.allclose(r1.policy, r2.policy, atol=1e-5)
    same_value = torch.allclose(r1.root_value, r2.root_value, atol=1e-5)
    same_action = torch.equal(r1.action, r2.action)
    print(f"{mode:6s} sims={sims:4d} net={net!s:5s} selfplay={selfplay!s:5s}: visits {same_visits}  policy {same_policy}  value {same_value}  action {same_action}")
    assert same_visits and same_policy and same_value and same_action


def count_syncs(n=256, sims=8):
    g = positions(n, 6)
    v2 = BatchedSearch(UniformEvaluator(DEV), n, SearchConfig(n_sims=sims, mode="gumbel"), DEV)
    args = (g.cells, g.macro, g.next_board, g.player, g.done, g.winner)
    v2.search(*args, selfplay=True)
    torch.cuda.set_sync_debug_mode("warn")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        v2.search(*args, selfplay=True)
    torch.cuda.set_sync_debug_mode("default")
    k = sum("synchroniz" in str(x.message).lower() for x in w)
    print(f"v2 syncs per simulation: {k / sims:.1f}")


def bench(n=4096, sims=32, net=False):
    g = positions(n, 6)
    ev = Evaluator(ResNet(NetConfig()).to(DEV), DEV) if net else UniformEvaluator(DEV)
    args = (g.cells, g.macro, g.next_board, g.player, g.done, g.winner)
    for name, s in (("v1", BatchedMCTS(ev, n, MCTSConfig(n_sims=sims, mode="gumbel"), DEV)),
                    ("v2", BatchedSearch(ev, n, SearchConfig(n_sims=sims, mode="gumbel"), DEV))):
        s.search(*args, selfplay=True)
        torch.cuda.synchronize()
        t = time.perf_counter()
        s.search(*args, selfplay=True)
        torch.cuda.synchronize()
        dt = time.perf_counter() - t
        print(f"{name} {'net' if net else 'uniform'}: {n} trees x {sims} sims: {dt:.2f}s = {dt / sims * 1000:.1f} ms/sim")


if __name__ == "__main__":
    for mode in ("puct", "gumbel"):
        compare(mode, 32)
        compare(mode, 200)
        compare(mode, 32, net=True)
        compare(mode, 64, net=True, selfplay=True, **({'sample_moves': 10} if mode == 'puct' else {}))
    count_syncs()
    bench()
    bench(net=True)
    print("ok")
