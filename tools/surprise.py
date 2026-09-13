"""Surprise mining (Phase E, item 4): positions where the raw net and a deep search disagree most.

    .venv/Scripts/python.exe tools/surprise.py runs/v2a/net_0150.pt --buffer runs/v2a/latest.pt --sims 256 --device cuda:1

For each sampled position: raw policy vs search policy (probability the raw policy gives the search's
chosen move), raw value vs search value. Reports aggregate disagreement by ply and prints the top-k
positions, ranked by value surprise and by policy surprise, as boards.

--rule count|draw is the rule the search trees expand under; the buffer must belong to a run trained under it
(a count-rule buffer read under draw would be a draw-rule search over count-rule positions labelled as if
they were the run's own; refused, never inferred — PLAN7 §5 K1).
"""
from __future__ import annotations

import argparse
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.game import UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.rules import RULES  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from probe_value import check_buffer_rule, load_positions  # noqa: E402


def board_str(cells, macro, nb, player, rule="count"):
    g = UTTT(rule)
    g.cells[:] = cells.cpu().numpy()
    g.macro[:] = macro.cpu().numpy()
    g.next_board = int(nb)
    g.player = int(player)
    g.move_count = int((g.cells != 0).sum())
    return str(g)


def mv(m: int) -> str:
    return f"{m} (board {m // 9 + 1} cell {m % 9 + 1})"


@torch.no_grad()
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--buffer", default="runs/v2a/latest.pt")
    ap.add_argument("--n", type=int, default=8192)
    ap.add_argument("--sims", type=int, default=256)
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule the search trees expand under")
    ap.add_argument("--corpus_rule", choices=RULES, default="", help="the buffer's run rule, when its run directory records none")
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    device = torch.device(a.device)
    check_buffer_rule(a.buffer, a.rule, a.corpus_rule)
    ev = FusedEvaluator(load_checkpoint(a.checkpoint, device), device)
    P = load_positions(a.buffer, device, a.n, 2, 70)
    n = P["cells"].shape[0]
    cells, macro, nb, player, ply = P["cells"], P["macro"], P["next_board"], P["player"], P["ply"].long()
    done = torch.zeros(n, dtype=torch.bool, device=device)
    winner = torch.zeros(n, dtype=torch.int8, device=device)
    raw_p, raw_v = ev(cells, macro, nb, player, done)
    scfg = SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, m_considered=16, cuda_graph=device.type == "cuda", depth_cap=min(a.sims, 24))
    r = BatchedSearch(ev, n, scfg, device, rule=a.rule).search(cells, macro, nb, player, done, winner, selfplay=False)
    best = r.action
    p_of_best = raw_p.gather(1, best.unsqueeze(1)).squeeze(1)
    raw_best = raw_p.argmax(1)
    disagree = raw_best != best
    dv = r.root_value - raw_v
    print(f"{n} positions, {a.sims} sims, rule {a.rule}. Search move != raw argmax in {100 * float(disagree.float().mean()):.1f}% of positions; "
          f"mean |search value - raw value| = {float(dv.abs().mean()):.3f}")
    print("by ply:  disagreement %   mean|dv|   mean p_raw(search move)")
    for lo, hi in ((2, 9), (10, 19), (20, 29), (30, 39), (40, 49), (50, 70)):
        m = (ply >= lo) & (ply <= hi)
        if m.sum() > 30:
            print(f"  {lo:2d}-{hi:2d}: {100 * float(disagree[m].float().mean()):5.1f}%        {float(dv[m].abs().mean()):.3f}       {float(p_of_best[m].mean()):.3f}   (n={int(m.sum())})")

    def show(idx, why):
        i = int(idx)
        print("=" * 72)
        print(f"{why}   ply {int(ply[i])}")
        print(board_str(cells[i], macro[i], nb[i], player[i], a.rule))
        print(f"raw: value {float(raw_v[i]):+.2f}, top move {mv(int(raw_best[i]))} p={float(raw_p[i].max()):.2f};   "
              f"search: value {float(r.root_value[i]):+.2f}, move {mv(int(best[i]))} (raw p={float(p_of_best[i]):.3f}, visits {int(r.visits[i, best[i]])}/{a.sims})")

    print("\n### largest value surprises (search much better for the mover than the net thought)")
    for i in torch.topk(dv, a.top).indices:
        show(i, f"value surprise {float(dv[i]):+.2f}")
    print("\n### largest negative value surprises (net too optimistic)")
    for i in torch.topk(-dv, a.top).indices:
        show(i, f"value surprise {float(dv[i]):+.2f}")
    print("\n### largest policy surprises (search chooses a move the net almost never considers)")
    for i in torch.topk(-p_of_best, a.top).indices:
        show(i, f"policy surprise: raw p(search move) = {float(p_of_best[i]):.4f}")


if __name__ == "__main__":
    main()
