"""Grade a net on every one-open-board position of a corpus with the exact tablebase (PLAN5 §4 C5).

    .venv/Scripts/python.exe tools/tablebase_grade.py runs/deep10_c1_300/net_0300.pt --data runs/probe_data_deep8late.npz --device cuda:1

Reports the share of positions with one open board, the raw value head's 3-way accuracy on them (and its draw
recognition), the raw policy's optimal-move rate, and the 64-sim search's optimal-move rate, all against the
tablebase; per-move exactness uses the solver (these positions have <= 9 empties, so it is instant).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.endgame import wdl_probs  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.solver import solve_children  # noqa: E402
from uttt.tablebase import K1Table  # noqa: E402


@torch.no_grad()
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--data", default="runs/probe_data_deep8late.npz")
    ap.add_argument("--sims", type=int, default=64)
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    device = torch.device(a.device)
    z = np.load(a.data)
    t = lambda k: torch.from_numpy(z[k]).to(device)  # noqa: E731
    cells, macro, nb, player = t("cells"), t("macro"), t("next_board"), t("player")
    tb = K1Table(device)
    v, best, k1 = tb.lookup(cells, macro, player)
    idx = k1.nonzero(as_tuple=True)[0]
    n = len(idx)
    print(f"{a.data}: {len(k1)} positions, {n} with exactly one open board ({100 * n / len(k1):.1f} %); "
          f"exact W/D/L for the mover {float((v[idx] == 1).float().mean()):.2f}/{float((v[idx] == 0).float().mean()):.2f}/{float((v[idx] == -1).float().mean()):.2f}")
    fe = FusedEvaluator(load_checkpoint(a.checkpoint, device), device)
    c, m, b, p = cells[idx], macro[idx], nb[idx], player[idx]
    done = torch.zeros(n, dtype=torch.bool, device=device)
    probs, _ = fe(c, m, b, p, done)
    wdl = wdl_probs(fe, c, m, b, p)
    pred = 1 - wdl.argmax(1)  # win 0 / draw 1 / loss 2 -> +1 / 0 / -1
    ex = v[idx]
    acc = float((pred == ex).float().mean())
    draw_rec = float((pred[ex == 0] == 0).float().mean()) if (ex == 0).any() else float("nan")
    g = BatchUTTT(n, device)
    g.cells[:], g.macro[:], g.next_board[:], g.player[:] = c, m, b, p
    s = BatchedSearch(fe, n, SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(a.sims, 24)), device)
    smove = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False).action.cpu().numpy()
    rmove = probs.argmax(1).cpu().numpy()
    cn, mn, bn, pn = c.cpu().numpy(), m.cpu().numpy(), b.cpu().numpy(), p.cpu().numpy()
    exn = ex.cpu().numpy()
    opt_raw = opt_search = 0
    reg_raw = reg_search = 0.0
    for i in range(n):
        _, ch = solve_children((cn[i], mn[i], int(bn[i]), int(pn[i])))
        opt_raw += int(ch[rmove[i]] == exn[i])
        opt_search += int(ch[smove[i]] == exn[i])
        reg_raw += float(exn[i] - ch[rmove[i]])
        reg_search += float(exn[i] - ch[smove[i]])
    print(f"{a.checkpoint} on the {n} one-open-board positions:")
    print(f"  raw value head: 3-way accuracy {100 * acc:.1f} %, draw recognition {100 * draw_rec:.1f} %")
    print(f"  raw policy: optimal move {100 * opt_raw / n:.1f} %, regret {reg_raw / n:.3f}")
    print(f"  search {a.sims} sims: optimal move {100 * opt_search / n:.1f} %, regret {reg_search / n:.3f}")


if __name__ == "__main__":
    main()
