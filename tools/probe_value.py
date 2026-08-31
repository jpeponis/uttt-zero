"""Counterfactual value probes (Phase E, item 3): perturb real positions and read the symmetry-averaged
value-head delta from the side-to-move's perspective.

    .venv/Scripts/python.exe tools/probe_value.py runs/v2a/net_0150.pt --buffer runs/v2a/latest.pt --device cuda:1

Probes:
  free-move   : positions where the mover is confined to one board -> give a free move instead.
  own-board B : positions where local board B is already won -> flip its owner (macro sign and the
                stones inside it), i.e. "I own it" vs "opponent owns it"; reported per board class
                (centre / corner / edge) and as a difference between classes.
  close-board : positions where board B is open and the mover is NOT sent there -> mark it drawn/full
                (removes it from play for both), measuring how much an open board is worth to the mover.
Values are raw (no search); the caveat from knowledge/05 applies: this measures what the net believes.
"""
from __future__ import annotations

import argparse
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import FULL  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402

CENTRE, CORNERS, EDGES = [4], [0, 2, 6, 8], [1, 3, 5, 7]


def load_eval(path, device):
    net = load_checkpoint(path, device)
    return SymmetryAveragedEvaluator(FusedEvaluator(net, device))


def load_positions(buffer_path, device, n_max, ply_lo, ply_hi, seed=0):
    ck = torch.load(buffer_path, map_location="cpu", weights_only=False)
    b = ck["buffer"]["buf"]
    ply = b["ply"].long()
    keep = torch.nonzero((ply >= ply_lo) & (ply <= ply_hi)).squeeze(1)
    g = torch.Generator().manual_seed(seed)
    keep = keep[torch.randperm(len(keep), generator=g)[:n_max]]
    out = {k: b[k][keep].to(device) for k in ("cells", "macro", "next_board", "player", "ply")}
    # deduplicate identical positions: keep the first row of every equivalence class
    key = torch.cat([out["cells"], out["macro"], out["next_board"].unsqueeze(1), out["player"].unsqueeze(1)], 1).long()
    uniq, inv = torch.unique(key, dim=0, return_inverse=True)
    first = torch.full((uniq.shape[0],), key.shape[0], dtype=torch.long, device=key.device)
    first.scatter_reduce_(0, inv, torch.arange(key.shape[0], device=key.device), reduce="amin")
    sel = first
    assert torch.unique(key[sel], dim=0).shape[0] == sel.numel()
    return {k: v[sel] for k, v in out.items()}


def value(ev, cells, macro, nb, player, bs=4096):
    vals = []
    for i in range(0, cells.shape[0], bs):
        sl = slice(i, i + bs)
        done = torch.zeros(cells[sl].shape[0], dtype=torch.bool, device=cells.device)
        vals.append(ev(cells[sl], macro[sl], nb[sl], player[sl], done)[1])
    return torch.cat(vals)


def describe(name, dv, ply=None):
    q = torch.quantile(dv, torch.tensor([0.1, 0.5, 0.9], device=dv.device))
    s = f"{name:44s} n={dv.numel():6d}  mean {float(dv.mean()):+.3f}  p10 {float(q[0]):+.3f}  median {float(q[1]):+.3f}  p90 {float(q[2]):+.3f}"
    if ply is not None:
        parts = []
        for lo, hi in ((0, 19), (20, 34), (35, 81)):
            m = (ply >= lo) & (ply <= hi)
            if m.sum() > 20:
                parts.append(f"ply {lo}-{hi}: {float(dv[m].mean()):+.3f}")
        s += "   [" + ", ".join(parts) + "]"
    print(s)


@torch.no_grad()
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--buffer", default="runs/v2a/latest.pt")
    ap.add_argument("--n", type=int, default=60000)
    ap.add_argument("--ply_lo", type=int, default=6)
    ap.add_argument("--ply_hi", type=int, default=60)
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    device = torch.device(a.device)
    ev = load_eval(a.checkpoint, device)
    P = load_positions(a.buffer, device, a.n, a.ply_lo, a.ply_hi)
    cells, macro, nb, player, ply = P["cells"], P["macro"], P["next_board"], P["player"], P["ply"].long()
    print(f"{cells.shape[0]} distinct positions, plies {a.ply_lo}-{a.ply_hi}, from {a.buffer}")
    base = value(ev, cells, macro, nb, player)
    print(f"baseline value (side to move): mean {float(base.mean()):+.3f}\n")

    # ---- free move -------------------------------------------------------
    m = nb >= 0
    dv = value(ev, cells[m], macro[m], torch.full_like(nb[m], -1), player[m]) - base[m]
    describe("free move instead of being confined", dv, ply[m])
    open_count = (macro[m] == 0).sum(1)
    for k in (2, 3, 4, 5, 6, 7, 8, 9):
        mm = open_count == k
        if mm.sum() > 50:
            print(f"    with {k} open boards: {float(dv[mm].mean()):+.3f} (n={int(mm.sum())})")
    print()

    # ---- ownership flips ---------------------------------------------------
    def flip_board(bidx):
        won = (macro[:, bidx] == 1) | (macro[:, bidx] == -1)
        if won.sum() == 0:
            return None
        c2 = cells[won].clone()
        m2 = macro[won].clone()
        c2[:, 9 * bidx : 9 * bidx + 9] *= -1
        m2[:, bidx] *= -1
        v2 = value(ev, c2, m2, nb[won], player[won])
        # sign so that dv = value(I own it) - value(opponent owns it)
        mine = macro[won, bidx] == player[won]
        return torch.where(mine, base[won] - v2, v2 - base[won]), ply[won]

    res = {}
    for name, boards in (("centre", CENTRE), ("corner", CORNERS), ("edge", EDGES)):
        dvs, plys = [], []
        for bidx in boards:
            r = flip_board(bidx)
            if r is not None:
                dvs.append(r[0])
                plys.append(r[1])
        if dvs:
            dv, pl = torch.cat(dvs), torch.cat(plys)
            res[name] = float(dv.mean())
            describe(f"owning a {name} board vs opponent owning it", dv, pl)
    if res:
        print(f"    centre - corner: {res.get('centre', 0) - res.get('corner', 0):+.3f}   corner - edge: {res.get('corner', 0) - res.get('edge', 0):+.3f}\n")

    # ---- closing an open board ---------------------------------------------
    for name, boards in (("centre", CENTRE), ("corner", CORNERS), ("edge", EDGES)):
        dvs, plys = [], []
        for bidx in boards:
            m = (macro[:, bidx] == 0) & (nb != bidx)
            if m.sum() == 0:
                continue
            m2 = macro[m].clone()
            m2[:, bidx] = FULL
            c2 = cells[m].clone()
            c2[:, 9 * bidx : 9 * bidx + 9] = torch.where(c2[:, 9 * bidx : 9 * bidx + 9] == 0, torch.full_like(c2[:, :9], 1), c2[:, 9 * bidx : 9 * bidx + 9])
            dvs.append(value(ev, c2, m2, nb[m], player[m]) - base[m])
            plys.append(ply[m])
        if dvs:
            describe(f"open {name} board removed (drawn) for both", torch.cat(dvs), torch.cat(plys))


if __name__ == "__main__":
    main()
