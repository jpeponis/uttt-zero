"""Diagnostics for the search loop: CPU->GPU synchronisations and kernel launches per simulation.

Runs on cuda:1 (the 3060) with a small batch so it does not disturb a training run on cuda:0.
"""
import os
import sys
import warnings

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.mcts import BatchedMCTS, MCTSConfig  # noqa: E402
from uttt.model import Evaluator, NetConfig, ResNet, UniformEvaluator  # noqa: E402

DEV = "cuda:1" if torch.cuda.device_count() > 1 else "cuda:0"


def make(n, sims, net):
    g = BatchUTTT(n, DEV)
    for _ in range(6):
        m = g.legal_mask().float() + 1e-9
        g.step(torch.multinomial(m, 1).squeeze(1))
    ev = Evaluator(ResNet(NetConfig()), DEV) if net else UniformEvaluator(DEV)
    return g, BatchedMCTS(ev, n, MCTSConfig(n_sims=sims, mode="gumbel"), DEV)


def count_syncs(n=256, sims=8):
    g, mcts = make(n, sims, net=False)
    mcts.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=True)  # warm-up
    torch.cuda.set_sync_debug_mode("warn")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        mcts.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=True)
    torch.cuda.set_sync_debug_mode("default")
    msgs = [str(x.message) for x in w if "synchroniz" in str(x.message).lower()]
    print(f"syncs per search of {sims} sims: {len(msgs)}  -> {len(msgs) / sims:.1f} per simulation")
    kinds = {}
    for m in msgs:
        k = m.split("called a synchronizing operation")[0].strip()[-60:] if "called" in m else m[:60]
        kinds[k] = kinds.get(k, 0) + 1
    for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {v:4d}  {k}")


def count_kernels(n=1024, sims=8, net=True):
    from torch.profiler import ProfilerActivity, profile
    g, mcts = make(n, sims, net=net)
    mcts.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=True)
    torch.cuda.synchronize(DEV)
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        mcts.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=True)
        torch.cuda.synchronize(DEV)
    evs = prof.key_averages()
    n_kernels = sum(e.count for e in evs if e.device_type == torch.autograd.DeviceType.CUDA)
    cuda_us = sum(e.self_device_time_total for e in evs if e.device_type == torch.autograd.DeviceType.CUDA)
    cpu_us = sum(e.self_cpu_time_total for e in evs)
    print(f"{'net' if net else 'uniform'} n={n} sims={sims}: {n_kernels} CUDA kernels ({n_kernels / sims:.0f}/sim), "
          f"GPU busy {cuda_us / 1e3:.1f} ms ({cuda_us / 1e3 / sims:.1f}/sim), CPU time {cpu_us / 1e3:.1f} ms ({cpu_us / 1e3 / sims:.1f}/sim)")
    top = sorted([e for e in evs if e.device_type == torch.autograd.DeviceType.CUDA], key=lambda e: -e.self_device_time_total)[:6]
    for e in top:
        print(f"    {e.self_device_time_total / 1e3:7.1f} ms  x{e.count:5d}  {e.key[:70]}")


if __name__ == "__main__":
    count_syncs()
    count_kernels(net=False)
    count_kernels(net=True)
