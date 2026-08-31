"""Play a side-swapped match between two (checkpoint, sims) players and report result + end reasons.

    .venv/Scripts/python.exe tools/match.py --a runs/dev1/net_0200.pt --a_sims 256 --b runs/dev1/net_0200.pt --b_sims 64

--a / --b may also be "uct" (uniform prior, plain search) or "random".
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.arena import RandomPlayer, SearchPlayer  # noqa: E402
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.mcts import MCTSConfig  # noqa: E402
from uttt.search import SearchConfig  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import UniformEvaluator, load_checkpoint  # noqa: E402


def load(path, device):
    if path == "uct":
        return UniformEvaluator(device)
    net = load_checkpoint(path, device)
    return FusedEvaluator(net, device)


def player(spec, sims, n, device, mode, graph=True):
    if spec == "random":
        return RandomPlayer(device)
    cfg = SearchConfig(n_sims=sims, mode=mode, gumbel_scale=0.0, cuda_graph=graph and device.type == "cuda", depth_cap=min(sims, 24))
    return SearchPlayer(load(spec, device), n, cfg, device)


@torch.no_grad()
def play(px, po, n, device, random_plies):
    g = BatchUTTT(n, device)
    rnd = RandomPlayer(device)
    ply = 0
    while not bool(g.done.all()):
        moves = rnd.act(g) if ply < random_plies else (px if ply % 2 == 0 else po).act(g)
        g.step(moves)
        ply += 1
    return g


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--a_sims", type=int, default=64)
    ap.add_argument("--b_sims", type=int, default=64)
    ap.add_argument("--games", type=int, default=256, help="games per side")
    ap.add_argument("--random_plies", type=int, default=2)
    ap.add_argument("--mode", default="gumbel")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--graph", type=int, default=1, help="1: CUDA-graph search")
    a = ap.parse_args()
    device = torch.device(a.device)
    torch.manual_seed(0)
    t = time.perf_counter()
    n = a.games
    g1 = play(player(a.a, a.a_sims, n, device, a.mode, bool(a.graph)), player(a.b, a.b_sims, n, device, a.mode, bool(a.graph)), n, device, a.random_plies)
    g2 = play(player(a.b, a.b_sims, n, device, a.mode, bool(a.graph)), player(a.a, a.a_sims, n, device, a.mode, bool(a.graph)), n, device, a.random_plies)
    w = int((g1.winner == 1).sum()) + int((g2.winner == -1).sum())
    l = int((g1.winner == -1).sum()) + int((g2.winner == 1).sum())
    d = 2 * n - w - l
    reasons = torch.cat([g1.end_reason, g2.end_reason])
    lens = torch.cat([g1.move_count, g2.move_count]).float()
    xw = (int((g1.winner == 1).sum()) + int((g2.winner == 1).sum())) / (2 * n)
    ow = (int((g1.winner == -1).sum()) + int((g2.winner == -1).sum())) / (2 * n)
    print(f"A={a.a}@{a.a_sims} vs B={a.b}@{a.b_sims}: A scores +{w} ={d} -{l} ({100 * (w + 0.5 * d) / (2 * n):.1f}%)  "
          f"[{time.perf_counter() - t:.0f}s]")
    print(f"  X wins {100 * xw:.1f}%  O wins {100 * ow:.1f}%  draws {100 * (1 - xw - ow):.1f}%  | "
          f"ended by line {100 * float((reasons == 1).float().mean()):.1f}%  by count {100 * float((reasons == 2).float().mean()):.1f}%  "
          f"drawn {100 * float((reasons == 3).float().mean()):.1f}%  | mean length {float(lens.mean()):.1f}")


if __name__ == "__main__":
    main()
