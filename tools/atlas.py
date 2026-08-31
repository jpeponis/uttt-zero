"""Opening atlas (PLAN2 §5 step 7): the 15 first-move orbits and their reply orbits evaluated by deep search
with several nets and budgets; reports values, ranks and rank stability (Kendall tau) across nets and budgets.

    .venv/Scripts/python.exe tools/atlas.py --nets runs/dev1/net_0200.pt,runs/v2a/net_0150.pt,runs/v2b/net_0150.pt --budgets 1024,4096,16384 --device cuda:1

Values are from X's perspective (search-relative statements: what net+search prefers, not game-theoretic).
Symmetry-averaged evaluators are used so orbit representatives are exactly representative. Writes --out (JSON).
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.openings import canonical, orbit_representatives  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402


def kendall_tau(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    n = len(a)
    s = 0
    for i, j in itertools.combinations(range(n), 2):
        s += np.sign(a[i] - a[j]) * np.sign(b[i] - b[j])
    return float(s / (n * (n - 1) / 2))


def reply_classes(m: int) -> list[tuple[int, int]]:
    """Canonical (first move, reply) representatives of O's replies to first move m, grouped under D4."""
    g = UTTT()
    g.play(m)
    seen = {}
    for r in g.legal_moves():
        key = canonical([m, r])
        seen.setdefault(key, (m, r))
    # keep the first move fixed to m: canonical form may rotate m; map back via the pair in m's orbit if needed
    out = []
    for key, pair in seen.items():
        out.append(pair)
    return sorted(out, key=lambda p: canonical(list(p)))


def principal_variations(s: BatchedSearch, max_len: int = 10) -> list[list[int]]:
    """Most-visited line from each tree's root (moves), plus the visit share of the second-best root move."""
    N = s.N.cpu().numpy()
    ch = s.children.cpu().numpy()
    out = []
    for i in range(s.n):
        node, pv = 0, []
        while len(pv) < max_len:
            nc = N[i, node]
            if nc.max() <= 0:
                break
            a = int(nc.argmax())
            pv.append(a)
            node = int(ch[i, node, a])
            if node < 0:
                break
        out.append(pv)
    return out


def deep_values(ev, seqs: list[list[int]], sims: int, device, want_pv: bool = False):
    """Search value for X after each move sequence (X's perspective); optionally the PV and the root's
    action-value gap (Q of the best move minus Q of the second most visited, mover's perspective)."""
    n = len(seqs)
    assert len({len(s) for s in seqs}) == 1, "one call = sequences of equal length"
    g = BatchUTTT(n, device)
    for t in range(len(seqs[0])):
        g.step(torch.tensor([s[t] for s in seqs], device=device))
    cfg = SearchConfig(n_sims=sims, mode="puct", c_puct=1.25, root_prior_floor=0.0, gumbel_scale=0.0, m_considered=81,
                       cuda_graph=device.type == "cuda", depth_cap=40)
    s = BatchedSearch(ev, n, cfg, device)
    r = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
    sign = torch.where(g.player == 1, 1.0, -1.0)
    vals = (r.root_value * sign).cpu().numpy()
    if not want_pv:
        return vals
    N0 = s.N[:, 0]
    Q0 = s.W[:, 0] / N0.clamp(min=1)
    top2 = N0.topk(2, dim=1).indices
    gap = (Q0.gather(1, top2[:, :1]) - Q0.gather(1, top2[:, 1:2])).squeeze(1).cpu().numpy()
    return vals, principal_variations(s), gap


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nets", default="runs/dev1/net_0200.pt,runs/v2a/net_0150.pt,runs/v2b/net_0150.pt")
    ap.add_argument("--budgets", default="1024,4096,16384")
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--no_sym", action="store_true")
    ap.add_argument("--out", default="runs/atlas.json")
    a = ap.parse_args()
    device = torch.device(a.device)
    nets = [p for p in a.nets.split(",") if p]
    budgets = [int(b) for b in a.budgets.split(",")]
    names = [f"{os.path.basename(os.path.dirname(p))}" for p in nets]
    reps = orbit_representatives()
    first = [[m] for m in reps]
    replies = {m: reply_classes(m) for m in reps}
    reply_seqs = [list(p) for m in reps for p in replies[m]]
    t0 = time.perf_counter()
    V1, V2 = {}, {}  # (net, budget) -> values
    pvs, gaps = {}, {}
    for p, nm in zip(nets, names):
        fe = FusedEvaluator(load_checkpoint(p, device), device)
        ev = fe if a.no_sym else SymmetryAveragedEvaluator(fe)
        for b in budgets:
            if b == budgets[-1]:
                V1[(nm, b)], pvs[nm], gaps[nm] = deep_values(ev, first, b, device, want_pv=True)
            else:
                V1[(nm, b)] = deep_values(ev, first, b, device)
            V2[(nm, b)] = deep_values(ev, reply_seqs, b, device)
            print(f"{nm} @{b}: done ({time.perf_counter() - t0:.0f}s)", flush=True)
    cols = list(V1)
    print(f"\nPrincipal variations after each first move at {budgets[-1]} sims (O's reply first) and the root action-value gap (Q best - Q second):")
    for i, m in enumerate(reps):
        print(f"  [{m:2d}] " + "  |  ".join(f"{nm}: {pvs[nm][i]} gap {gaps[nm][i]:+.3f}" for nm in names))
    # ---- table 1: first moves ----
    print("\nFirst-move orbits: deep-search value for X after the move, by net @ budget (rank in brackets)")
    header = f"{'orbit':6s} " + " ".join(f"{nm}@{b:<6d}" for nm, b in cols) + "   mean rank"
    print(header)
    ranks = {c: (-V1[c]).argsort().argsort() + 1 for c in cols}
    mean_rank = np.mean([ranks[c] for c in cols], axis=0)
    for i in np.argsort(mean_rank):
        row = " ".join(f"{V1[c][i]:+.3f}({ranks[c][i]:2d})" for c in cols)
        print(f"  [{reps[i]:2d}]  {row}   {mean_rank[i]:5.1f}")
    print("\nKendall tau between columns (first-move ranking):")
    print(" " * 14 + " ".join(f"{nm[:4]}@{b // 1024}k".rjust(9) for nm, b in cols))
    for c1 in cols:
        print(f"  {c1[0][:4]}@{c1[1] // 1024}k".ljust(14) + " ".join(f"{kendall_tau(V1[c1], V1[c2]):9.2f}" for c2 in cols))
    top = [reps[int(np.argmax(V1[c]))] for c in cols]
    print(f"\nbest first move per column: {top}  (stable: {len(set(top)) == 1})")
    # ---- table 2: replies ----
    print("\nReplies: best reply class (X's value after it, lower = better for O) per first move and column;")
    print("agreement = share of columns choosing the same best reply as the strongest net at the largest budget")
    ref = cols[-1]
    off = 0
    agree_all = []
    for m in reps:
        k = len(replies[m])
        vals = {c: V2[c][off : off + k] for c in cols}
        best = {c: int(np.argmin(vals[c])) for c in cols}
        agree = np.mean([best[c] == best[ref] for c in cols])
        agree_all.append(agree)
        pairs = replies[m]
        print(f"  after [{m:2d}] ({k} reply classes): " + "  ".join(f"{c[0][:4]}@{c[1] // 1024}k:{pairs[best[c]][1]:2d}({vals[c][best[c]]:+.2f})" for c in cols)
              + f"   agreement {agree:.2f}")
        off += k
    print(f"mean best-reply agreement with {ref[0]}@{ref[1]}: {np.mean(agree_all):.2f}")
    rec = {"nets": nets, "budgets": budgets, "first_moves": reps, "values_first": {f"{nm}@{b}": V1[(nm, b)].tolist() for nm, b in cols},
           "replies": {str(m): replies[m] for m in reps}, "values_replies": {f"{nm}@{b}": V2[(nm, b)].tolist() for nm, b in cols},
           "kendall_first": {f"{c1[0]}@{c1[1]}|{c2[0]}@{c2[1]}": kendall_tau(V1[c1], V1[c2]) for c1 in cols for c2 in cols}}
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print(f"wrote {a.out}  [{time.perf_counter() - t0:.0f}s]")


if __name__ == "__main__":
    main()
