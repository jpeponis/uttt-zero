"""Opening analysis with a trained net: symmetry-averaged raw policy and value, and a deep search whose
root cannot be locked by a one-hot prior (uniform floor mixed into the root prior).

    .venv/Scripts/python.exe tools/analyze_opening.py runs/v2a/latest.pt --sims 8192 --floor 0.25

All 9x9 grids are printed in board layout (row = 3*macro_row + micro_row). Values are from X's
(the first player's) perspective. The orbit table groups the 81 first moves by the 15 symmetry classes.
"""
from __future__ import annotations

import argparse
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import PERM, SYM_CELL, BatchUTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402


def load(path, device, sym=True):
    net = load_checkpoint(path, device)
    ev = FusedEvaluator(net, device)
    return SymmetryAveragedEvaluator(ev) if sym else ev


def grid(vals, fmt="{:6.3f}"):
    v = vals.detach().float().cpu()[PERM].view(9, 9)
    lines = []
    for r in range(9):
        row = "  ".join(" ".join(fmt.format(float(v[r, c])) for c in range(3 * b, 3 * b + 3)) for b in range(3))
        lines.append(row)
        if r in (2, 5):
            lines.append("")
    return "\n".join(lines)


def orbits():
    seen, out = set(), []
    for m in range(81):
        if m in seen:
            continue
        orb = sorted({int(SYM_CELL[s, m]) for s in range(8)})
        seen.update(orb)
        out.append(orb)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--sims", type=int, default=8192)
    ap.add_argument("--floor", type=float, default=0.25, help="uniform fraction mixed into the root prior for the deep search")
    ap.add_argument("--mode", default="puct")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--no_sym", action="store_true")
    a = ap.parse_args()
    device = torch.device(a.device)
    ev = load(a.checkpoint, device, sym=not a.no_sym)

    g = BatchUTTT(1, device)
    probs, value = ev(g.cells, g.macro, g.next_board, g.player, g.done)
    print(f"raw net value of the empty board for X: {float(value[0]):+.3f}\n")
    print("raw policy at the empty board (%):")
    print(grid(100 * probs[0], "{:5.1f}"), "\n")

    b = BatchUTTT(81, device)
    b.step(torch.arange(81, device=device))
    _, v_after = ev(b.cells, b.macro, b.next_board, b.player, b.done)
    v_x = -v_after  # side to move is O after X's first move
    print("raw net value after each first move (X's perspective):")
    print(grid(v_x), "\n")

    cfg = SearchConfig(n_sims=a.sims, mode=a.mode, c_puct=1.25, root_prior_floor=a.floor, gumbel_scale=0.0,
                       m_considered=81, cuda_graph=device.type == "cuda", depth_cap=40)
    mcts = BatchedSearch(ev, 1, cfg, device)
    r = mcts.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
    Nc = mcts.N[0, 0]
    Qc = mcts.W[0, 0] / Nc.clamp(min=1)
    print(f"{a.mode} search, {a.sims} sims, root prior floor {a.floor}: root value {float(r.root_value[0]):+.3f}; visits per first move:")
    print(grid(Nc, "{:6.0f}"), "\n")
    print("search Q per first move (X's perspective, unvisited = 0):")
    print(grid(Qc), "\n")

    # deep search from each orbit representative (O to move after X's first move): value for X = -root value
    orbs = orbits()
    reps = torch.tensor([o[0] for o in orbs], device=device)
    b15 = BatchUTTT(len(orbs), device)
    b15.step(reps)
    deep_sims = max(a.sims // 2, 1024)
    dcfg = SearchConfig(n_sims=deep_sims, mode=a.mode, c_puct=1.25, root_prior_floor=0.0, gumbel_scale=0.0,
                        m_considered=81, cuda_graph=device.type == "cuda", depth_cap=40)
    r15 = BatchedSearch(ev, len(orbs), dcfg, device).search(b15.cells, b15.macro, b15.next_board, b15.player, b15.done, b15.winner, selfplay=False)
    deep_v = (-r15.root_value).tolist()

    print(f"orbit table (15 symmetry classes): members | raw policy % | raw value | root-search visits/Q | deep value ({deep_sims} sims after the move)")
    rows = []
    for k, orb in enumerate(orbs):
        idx = torch.tensor(orb, device=device)
        q = float((Qc[idx] * Nc[idx]).sum() / Nc[idx].sum().clamp(min=1))
        rows.append((deep_v[k], orb, float(100 * probs[0, idx].sum()), float(v_x[idx].mean()), float(Nc[idx].sum()), q))
    for dv, orb, p, v, n_vis, q in sorted(rows, reverse=True):
        print(f"  {str(orb):40s} p={p:5.1f}  v={v:+.3f}  N={n_vis:6.0f}  Q={q:+.3f}  deep={dv:+.3f}")


if __name__ == "__main__":
    main()
