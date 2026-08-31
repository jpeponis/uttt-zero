"""Depth-cap diagnostic: fraction of simulations truncated by depth_cap under self-play settings, by ply and budget."""
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from openings import load  # noqa: E402
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def main(ckpt="runs/v2b/net_0150.pt", n=2048, cap=12, budgets=(32, 48, 64)):
    dev = torch.device(DEV)
    ev = load(ckpt, dev)
    torch.manual_seed(0)
    g = BatchUTTT(n, dev)
    searches = {s: BatchedSearch(ev, n, SearchConfig(n_sims=s, mode="gumbel", sample_moves=8, sample_uniform=0.15, root_prior_floor=0.03,
                                                     cuda_graph=dev.type == "cuda", depth_cap=cap), dev) for s in budgets}
    print(f"fraction of simulations truncated by depth_cap={cap} (self-play settings, {n} games, {ckpt}), by ply:")
    for ply in range(0, 66):
        args = (g.cells, g.macro, g.next_board, g.player, g.done, g.winner)
        r = searches[budgets[-1]].search(*args, selfplay=True, ply=ply)
        if ply % 6 == 0 and int((~g.done).sum()) > 50:
            alive = ~g.done
            parts = [f"{s} sims: {float(srch.search(*args, selfplay=True, ply=ply).cap_hits[alive].mean()) / s * 100:5.2f}%" for s, srch in searches.items()]
            print(f"  ply {ply:2d} (alive {int(alive.sum()):4d}): " + "  ".join(parts))
        g.step(r.action)


if __name__ == "__main__":
    main()
