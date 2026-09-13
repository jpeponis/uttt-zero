"""Free-move tempo effect from natural positions with a prespecified model (PLAN2 §5 step 7; replaces the
tensor-edit probe of tools/probe_value.py, REVIEW-codex finding 2).

    .venv/Scripts/python.exe tools/freemove.py runs/v2b/net_0150.pt --corpus runs/v2a --last 3 --sims 256 --device cuda:1

Positions are sampled from held-out corpus games (≤ 5 per game, plies 8-50, game not over), the search value
for the side to move is regressed on the free-move indicator with controls (ply, ply², macro score, open
boards, empties in open boards, side to move, macro threats for and against), OLS with cluster-robust
standard errors by source game. A stratified comparison (ply bucket × macro score) is printed as a check.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.game import LINES, UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.rules import RULES  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402


def macro_threats(macro: np.ndarray, p: int) -> int:
    """Macro lines where p owns two boards and the third is still open."""
    t = 0
    for a, b, c in LINES:
        v = [macro[a], macro[b], macro[c]]
        if v.count(p) == 2 and v.count(0) == 1:
            t += 1
    return t


def sample_positions(files, per_game, ply_lo, ply_hi, n_max, rng, rule="count"):
    rows = []
    gid = 0
    for f in files:
        z = np.load(f)
        moves, lengths = z["moves"], z["lengths"]
        for k in range(len(lengths)):
            L = int(lengths[k])
            plies = [t for t in range(ply_lo, min(ply_hi, L - 1) + 1)]
            if not plies:
                gid += 1
                continue
            want = set(rng.choice(plies, size=min(per_game, len(plies)), replace=False).tolist())
            g = UTTT(rule)
            for t in range(L):
                if t in want:
                    rows.append((gid, t, g.cells.copy(), g.macro.copy(), g.next_board, g.player))
                g.play(int(moves[k, t]))
            gid += 1
            if len(rows) >= n_max:
                return rows
    return rows


def ols_cluster(X, y, groups):
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    e = y - X @ beta
    meat = np.zeros((X.shape[1], X.shape[1]))
    for gval in np.unique(groups):
        m = groups == gval
        s = X[m].T @ e[m]
        meat += np.outer(s, s)
    V = XtX_inv @ meat @ XtX_inv
    return beta, np.sqrt(np.diag(V)), e


@torch.no_grad()
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--corpus", default="runs/v2a")
    ap.add_argument("--last", type=int, default=3)
    ap.add_argument("--per_game", type=int, default=5)
    ap.add_argument("--n", type=int, default=30000)
    ap.add_argument("--sims", type=int, default=256)
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule the search values are read under")
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    device = torch.device(a.device)
    files = sorted(glob.glob(os.path.join(a.corpus, "games", "games_*.npz")))[-a.last :]
    rows = sample_positions(files, a.per_game, 8, 50, a.n, np.random.default_rng(0), a.rule)
    N = len(rows)
    gid = np.array([r[0] for r in rows])
    ply = np.array([r[1] for r in rows], dtype=np.float64)
    cells = np.stack([r[2] for r in rows]).astype(np.int8)
    macro = np.stack([r[3] for r in rows]).astype(np.int8)
    nb = np.array([r[4] for r in rows], dtype=np.int8)
    player = np.array([r[5] for r in rows], dtype=np.int8)
    free = (nb < 0).astype(np.float64)
    p = player.astype(np.int64)[:, None]
    score = ((macro == p).sum(1) - (macro == -p).sum(1)).astype(np.float64)
    open_b = (macro == 0).sum(1).astype(np.float64)
    empties = ((cells.reshape(N, 9, 9) == 0) & (macro == 0)[:, :, None]).sum((1, 2)).astype(np.float64)
    is_x = (player == 1).astype(np.float64)
    thr_for = np.array([macro_threats(macro[i], int(player[i])) for i in range(N)], dtype=np.float64)
    thr_against = np.array([macro_threats(macro[i], -int(player[i])) for i in range(N)], dtype=np.float64)

    fe = FusedEvaluator(load_checkpoint(a.checkpoint, device), device)
    vals = np.zeros(N)
    raw = np.zeros(N)
    bs = 4096
    for i in range(0, N, bs):
        sl = slice(i, min(i + bs, N))
        n = sl.stop - sl.start
        g = BatchUTTT(n, device, a.rule)
        g.cells[:] = torch.from_numpy(cells[sl]).to(device)
        g.macro[:] = torch.from_numpy(macro[sl]).to(device)
        g.next_board[:] = torch.from_numpy(nb[sl]).to(device)
        g.player[:] = torch.from_numpy(player[sl]).to(device)
        s = BatchedSearch(fe, n, SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(a.sims, 24)), device, rule=a.rule)
        r = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
        vals[sl] = r.root_value.cpu().numpy()
        raw[sl] = r.raw_value.cpu().numpy()
    print(f"{N} positions from {len(np.unique(gid))} held-out games ({[os.path.basename(f) for f in files]}), net {a.checkpoint}, "
          f"{a.sims}-sim search values under rule {a.rule}")
    print(f"free-move positions: {free.mean():.3f}; mean value free {vals[free == 1].mean():+.3f} vs confined {vals[free == 0].mean():+.3f} (raw difference {vals[free == 1].mean() - vals[free == 0].mean():+.3f})")
    names = ["intercept", "free_move", "ply/10", "(ply/10)^2", "macro_score", "open_boards", "empties/10", "is_X", "threats_for", "threats_against"]
    X = np.column_stack([np.ones(N), free, ply / 10, (ply / 10) ** 2, score, open_b, empties / 10, is_x, thr_for, thr_against])
    for label, yv in (("search value", vals), ("raw value", raw)):
        beta, se, e = ols_cluster(X, yv, gid)
        r2 = 1 - e.var() / yv.var()
        print(f"\nOLS of the {label} (mover's perspective), cluster-robust SE by game, R^2 = {r2:.3f}:")
        for nm, b, s in zip(names, beta, se):
            flag = " *" if abs(b) > 1.96 * s and nm != "intercept" else ""
            print(f"  {nm:16s} {b:+.4f} +- {1.96 * s:.4f}{flag}")
    # board-ownership model: which boards are worth owning (replaces the tensor-flip probe of probe_value.py)
    centre, corners, edges = [4], [0, 2, 6, 8], [1, 3, 5, 7]
    own = lambda cls, who: (macro[:, cls] == who * p).sum(1).astype(np.float64)  # noqa: E731
    full = (macro == 2).sum(1).astype(np.float64)
    names2 = ["intercept", "free_move", "ply/10", "(ply/10)^2", "empties/10", "is_X", "threats_for", "threats_against", "full_boards",
              "centre_self", "centre_opp", "corners_self", "corners_opp", "edges_self", "edges_opp"]
    X2 = np.column_stack([np.ones(N), free, ply / 10, (ply / 10) ** 2, empties / 10, is_x, thr_for, thr_against, full,
                          own(centre, 1), own(centre, -1), own(corners, 1), own(corners, -1), own(edges, 1), own(edges, -1)])
    beta, se, e = ols_cluster(X2, vals, gid)
    print(f"\nOLS of the search value on board ownership by class (per board owned), cluster-robust SE by game, R^2 = {1 - e.var() / vals.var():.3f}:")
    for nm, b, s in zip(names2, beta, se):
        flag = " *" if abs(b) > 1.96 * s and nm != "intercept" else ""
        print(f"  {nm:16s} {b:+.4f} +- {1.96 * s:.4f}{flag}")
    d = dict(zip(names2, beta))
    print(f"  net worth of owning (self - opp coefficient): centre {d['centre_self'] - d['centre_opp']:+.3f}, corner {d['corners_self'] - d['corners_opp']:+.3f}, "
          f"edge {d['edges_self'] - d['edges_opp']:+.3f}")
    # stratified check: free vs confined within (ply bucket x macro score) cells, weighted by cell size
    print("\nstratified free - confined difference in search value (cells with >= 30 positions of each kind):")
    tot_w, tot_d = 0.0, 0.0
    for lo, hi in ((8, 19), (20, 31), (32, 43), (44, 50)):
        for sc in (-2, -1, 0, 1, 2):
            m = (ply >= lo) & (ply <= hi) & (score == sc)
            mf, mc = m & (free == 1), m & (free == 0)
            if mf.sum() >= 30 and mc.sum() >= 30:
                d = vals[mf].mean() - vals[mc].mean()
                w = min(mf.sum(), mc.sum())
                tot_w += w
                tot_d += w * d
                print(f"  ply {lo:2d}-{hi:2d}, macro score {sc:+d}: free {vals[mf].mean():+.3f} (n={int(mf.sum()):5d})  confined {vals[mc].mean():+.3f} (n={int(mc.sum()):5d})  diff {d:+.3f}")
    print(f"weighted mean difference: {tot_d / max(tot_w, 1):+.3f}")


if __name__ == "__main__":
    main()
