"""Checkpoint ladder: every net_*.pt in a run plays a side-swapped match against a reference net.

    .venv/Scripts/python.exe tools/ladder.py --run runs/dev1 --ref net_0150.pt --device cuda:1

Writes/updates <run>/ladder.json incrementally: {checkpoint: {"score", "w", "d", "l", "sims", "games"}}.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.arena import SearchPlayer, match  # noqa: E402
from uttt.mcts import MCTSConfig  # noqa: E402
from uttt.search import SearchConfig  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402


def load(path, device):
    net = load_checkpoint(path, device)
    return FusedEvaluator(net, device)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--ref", required=True, help="reference checkpoint file name inside the run")
    ap.add_argument("--games", type=int, default=256, help="games per side")
    ap.add_argument("--sims", type=int, default=64)
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--graph", type=int, default=1, help="1: CUDA-graph search")
    ap.add_argument("--only", default="", help="comma-separated checkpoint names to (re)run")
    a = ap.parse_args()
    device = torch.device(a.device)
    torch.manual_seed(0)
    out_path = os.path.join(a.run, "ladder.json")
    results = json.load(open(out_path)) if os.path.exists(out_path) else {}
    ref = load(os.path.join(a.run, a.ref), device)
    cfg = SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=bool(a.graph) and device.type == "cuda", depth_cap=min(a.sims, 24))
    ckpts = sorted(glob.glob(os.path.join(a.run, "net_*.pt")))
    only = set(a.only.split(",")) if a.only else None
    for path in ckpts:
        name = os.path.basename(path)
        key = f"{name} vs {a.ref} @{a.sims}"
        if key in results and not (only and name in only):
            continue
        if only and name not in only:
            continue
        ev = load(path, device)
        r = match(lambda: SearchPlayer(ev, a.games, cfg, device), lambda: SearchPlayer(ref, a.games, cfg, device), a.games, device)
        results[key] = {"score": r.score, "w": r.wins, "d": r.draws, "l": r.losses, "sims": a.sims, "games": 2 * a.games}
        print(f"{key}: {r}", flush=True)
        json.dump(results, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()
