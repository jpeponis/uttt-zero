"""Value decomposition (PLAN5 §3 B3): regress the raw value head and the 256-sim search value on the hand-written
concept set, per checkpoint, to see which concepts the value weighs, when the weights appear over training, and
where the search still corrects the head (the raw-minus-search coefficient gap).

    .venv/Scripts/python.exe tools/value_decomp.py runs/deep10_c1_300 --data runs/probe_data_deep8late.npz --n 20000 --sims 256 --device cuda:1

Positions and labels come from tools/probe.py build (held-out games, provenance kept for cluster-robust SEs). The
model is tools/freemove.py's prespecified regression extended with the B2 concepts: free move, ply, count margin,
open boards, empties, side, macro threats for / against, dead boards, immediate local win / threat, macro win now,
and board ownership by class. Values are from the mover's perspective. Writes <run>/value_decomp.json and .png.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from freemove import ols_cluster  # noqa: E402
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402

CENTRE, CORNERS, EDGES = [4], [0, 2, 6, 8], [1, 3, 5, 7]


def design(z, idx, ownership: bool = False) -> tuple[np.ndarray, list[str]]:
    """Regressors. ownership=True swaps count_margin for boards owned by class (self / opponent x centre / corner / edge);
    the two cannot be in one model — the six class counts sum exactly to count_margin's two terms."""
    L = lambda k: z["label_" + k][idx].astype(np.float64)  # noqa: E731
    ply = z["ply"][idx].astype(np.float64)
    status = np.stack([z[f"label_status_{b}"][idx] for b in range(9)], 1)  # 0 open / 1 mine / 2 theirs / 3 full
    own = lambda cls, who: (status[:, cls] == who).sum(1).astype(np.float64)  # noqa: E731
    cols = [
        ("intercept", np.ones(len(idx))), ("free_move", L("free_move")), ("ply/10", ply / 10), ("(ply/10)^2", (ply / 10) ** 2),
        ("count_margin", L("count_margin")), ("open_boards", L("open_count")), ("empties/10", L("empties") / 10), ("is_X", L("side_to_move_x")),
        ("threats_for", L("threats_for")), ("threats_against", L("threats_against")), ("dead_boards", L("dead_count")),
        ("local_win_now", L("local_win_now")), ("local_threat_against", L("local_threat_against")), ("macro_win_now", L("macro_win_now")),
        ("full_boards", L("boards_full")),
    ]
    if ownership:  # open + full + self-owned + opponent-owned boards = 9, so open_boards must go too
        cols = [c for c in cols if c[0] not in ("count_margin", "open_boards")] + [
            ("centre_self", own(CENTRE, 1)), ("centre_opp", own(CENTRE, 2)), ("corners_self", own(CORNERS, 1)), ("corners_opp", own(CORNERS, 2)),
            ("edges_self", own(EDGES, 1)), ("edges_opp", own(EDGES, 2))]
    X = np.column_stack([c for _, c in cols])
    names = [n for n, _ in cols]
    keep = [i for i in range(X.shape[1]) if i == 0 or X[:, i].std() > 0]  # a regressor constant on this sample carries nothing
    if len(keep) < len(names):
        print("dropped constant regressors:", [names[i] for i in range(len(names)) if i not in keep])
    return X[:, keep], [names[i] for i in keep]


@torch.no_grad()
def values(fe, z, idx, sims, device, bs=4096):
    raw, srch = np.zeros(len(idx)), np.zeros(len(idx))
    for i in range(0, len(idx), bs):
        sl = idx[i : i + bs]
        n = len(sl)
        g = BatchUTTT(n, device)
        g.cells[:] = torch.from_numpy(z["cells"][sl]).to(device)
        g.macro[:] = torch.from_numpy(z["macro"][sl]).to(device)
        g.next_board[:] = torch.from_numpy(z["next_board"][sl]).to(device)
        g.player[:] = torch.from_numpy(z["player"][sl]).to(device)
        s = BatchedSearch(fe, n, SearchConfig(n_sims=sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(sims, 24)), device)
        r = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
        raw[i : i + n] = r.raw_value.cpu().numpy()
        srch[i : i + n] = r.root_value.cpu().numpy()
    return raw, srch


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--data", default="runs/probe_data_deep8late.npz")
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--sims", type=int, default=256)
    ap.add_argument("--only", default="")
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    device = torch.device(a.device)
    t0 = time.perf_counter()
    z = np.load(a.data)
    rng = np.random.default_rng(0)
    idx = np.sort(rng.choice(len(z["ply"]), size=min(a.n, len(z["ply"])), replace=False))
    X, names = design(z, idx)
    Xo, names_o = design(z, idx, ownership=True)
    gid = z["game_id"][idx]
    ckpts = sorted(glob.glob(os.path.join(a.run, "net_[0-9][0-9][0-9][0-9].pt")))
    if a.only:
        keep = {int(x) for x in a.only.split(",")}
        ckpts = [p for p in ckpts if int(os.path.basename(p)[4:8]) in keep]
    print(f"{len(idx)} positions from {len(np.unique(gid))} games ({a.data}); {len(ckpts)} checkpoints of {a.run}; {len(names) - 1} regressors")
    out = []
    for p in ckpts:
        it = int(os.path.basename(p)[4:8])
        fe = FusedEvaluator(load_checkpoint(p, device), device)
        raw, srch = values(fe, z, idx, a.sims, device)
        rec = {"iter": it}
        for label, yv in (("raw", raw), ("search", srch)):
            beta, se, e = ols_cluster(X, yv, gid)
            rec[label] = {"r2": float(1 - e.var() / yv.var()), "coef": dict(zip(names, beta.tolist())), "ci95": dict(zip(names, (1.96 * se).tolist()))}
        rec["gap"] = {k: rec["raw"]["coef"][k] - rec["search"]["coef"][k] for k in names}
        for label, yv in (("own_raw", raw), ("own_search", srch)):  # ownership-by-class model (freemove.py's second regression)
            beta, se, e = ols_cluster(Xo, yv, gid)
            rec[label] = {"r2": float(1 - e.var() / yv.var()), "coef": dict(zip(names_o, beta.tolist())), "ci95": dict(zip(names_o, (1.96 * se).tolist()))}
        out.append(rec)
        show = ("free_move", "count_margin", "threats_for", "threats_against", "local_win_now", "macro_win_now")
        print(f"  net_{it:04d}: R2 raw {rec['raw']['r2']:.3f} search {rec['search']['r2']:.3f} | " +
              "  ".join(f"{k} {rec['raw']['coef'][k]:+.3f}/{rec['search']['coef'][k]:+.3f}" for k in show) + f"  ({time.perf_counter() - t0:.0f}s)", flush=True)
    final = out[-1]
    print(f"\nfinal checkpoint net_{final['iter']:04d}: coefficient (95 % CI) of the raw value | the {a.sims}-sim search value | gap raw-search")
    for k in names:
        r, s = final["raw"], final["search"]
        print(f"  {k:22s} {r['coef'][k]:+.4f} +- {r['ci95'][k]:.4f} | {s['coef'][k]:+.4f} +- {s['ci95'][k]:.4f} | {final['gap'][k]:+.4f}")
    print("\nownership-by-class model (count_margin replaced by boards owned per class), final checkpoint: raw | search")
    for k in names_o[-6:]:
        r, s = final["own_raw"], final["own_search"]
        print(f"  {k:22s} {r['coef'][k]:+.4f} +- {r['ci95'][k]:.4f} | {s['coef'][k]:+.4f} +- {s['ci95'][k]:.4f}")
    for label in ("own_raw", "own_search"):
        d = final[label]["coef"]
        if all(k in d for k in ("centre_self", "centre_opp", "corners_self", "corners_opp", "edges_self", "edges_opp")):
            print(f"  net worth of owning (self - opp, {label[4:]} value): centre {d['centre_self'] - d['centre_opp']:+.3f}, "
                  f"corner {d['corners_self'] - d['corners_opp']:+.3f}, edge {d['edges_self'] - d['edges_opp']:+.3f}")
    meta = {"run": a.run, "data": a.data, "n": int(len(idx)), "sims": a.sims, "regressors": names, "regressors_ownership": names_o}
    path = os.path.join(a.run, "value_decomp.json")
    with open(path, "w") as f:
        json.dump({"meta": meta, "rows": out}, f, indent=1)
    print(f"wrote {path}  [{time.perf_counter() - t0:.0f}s]")
    if len(out) > 1:
        plot(out, meta, os.path.join(a.run, "value_decomp.png"))


def plot(rows, meta, path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from plot_run import BLUE, GRID, INK, MUTED, ORANGE, style

    keys = ["free_move", "count_margin", "threats_for", "threats_against", "local_win_now", "macro_win_now"]
    it = [r["iter"] for r in rows]
    fig, axes = plt.subplots(2, 3, figsize=(14, 7), facecolor="#fcfcfb")
    fig.subplots_adjust(hspace=0.5, wspace=0.3, left=0.06, right=0.98, top=0.86, bottom=0.09)
    for ax, k in zip(axes.flat, keys):
        for src, c in (("raw", ORANGE), ("search", BLUE)):
            y = [r[src]["coef"][k] for r in rows]
            e = [r[src]["ci95"][k] for r in rows]
            ax.plot(it, y, color=c, linewidth=2, marker="o", markersize=4, label=f"{src} value")
            ax.fill_between(it, [a - b for a, b in zip(y, e)], [a + b for a, b in zip(y, e)], color=c, alpha=0.12, linewidth=0)
        ax.axhline(0, color=GRID, linewidth=1)
        style(ax, f"coefficient of {k}", "expected score per unit")
        ax.set_xlabel("iteration", fontsize=8, color=MUTED)
    axes[0, 0].legend(frameon=False, fontsize=8, loc="best")
    fig.suptitle(f"{meta['run']}: value regressed on concepts, by checkpoint (R² final: raw {rows[-1]['raw']['r2']:.2f}, search {rows[-1]['search']['r2']:.2f}; "
                 f"{meta['n']} held-out positions, {meta['sims']}-sim search; bands = 95 % CI, cluster-robust by game)", x=0.06, ha="left", fontsize=10, color=INK)
    fig.savefig(path, dpi=130)
    print("wrote", path)


if __name__ == "__main__":
    main()
