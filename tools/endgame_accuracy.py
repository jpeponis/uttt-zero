"""Exact-label endgame test (NOTES-v2 §5.3): solve buffer positions with few remaining moves and score
the raw net and the search against the exact game value.

    .venv/Scripts/python.exe tools/endgame_accuracy.py runs/v2a/net_0150.pt --buffer runs/v2a/latest.pt --max_empty 16 --n 3000

Metrics: raw WDL-argmax accuracy and mean |value error|; for each search budget, root-value sign
accuracy and the move-error rate (the chosen move loses exact value: -solve(child) < solve(parent)).

--rule count|draw is the rule the solver, the search trees and the child step all use; the buffer must belong
to a run trained under it. Every number here is an exact terminal value, so the rule is not cosmetic: 43 of
200 random <= 8-empty positions have a different value under the other rule (tests/test_rules.py).
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from probe_value import check_buffer_rule  # noqa: E402
from uttt.batch import step_state  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.rules import RULES, tag_path  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.solver import empties_in_open_boards, solve  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--buffer", default="runs/v2a/latest.pt")
    ap.add_argument("--max_empty", type=int, default=16)
    ap.add_argument("--min_empty", type=int, default=6)
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--sims", default="32,64,256")
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule the solver and the searches use")
    ap.add_argument("--corpus_rule", choices=RULES, default="", help="the buffer run rule, when its directory records none")
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    device = torch.device(a.device)
    check_buffer_rule(a.buffer, a.rule, a.corpus_rule)

    ck = torch.load(a.buffer, map_location="cpu", weights_only=False)["buffer"]["buf"]
    cells_all, macro_all = ck["cells"].numpy(), ck["macro"].numpy()
    nb_all, pl_all, ply_all = ck["next_board"].numpy(), ck["player"].numpy(), ck["ply"].numpy()
    emp = ((cells_all.reshape(-1, 9, 9) == 0) & (macro_all == 0)[:, :, None]).sum((1, 2))
    cand = np.nonzero((emp >= a.min_empty) & (emp <= a.max_empty))[0]
    rng = np.random.default_rng(0)
    cand = rng.permutation(cand)
    seen, idx = set(), []
    for i in cand:
        key = cells_all[i].tobytes() + macro_all[i].tobytes() + bytes([nb_all[i] + 1, pl_all[i] + 1])
        if key not in seen:
            seen.add(key)
            idx.append(i)
        if len(idx) >= a.n:
            break
    idx = np.array(idx)
    print(f"{len(idx)} distinct positions with {a.min_empty}-{a.max_empty} empties in open boards; rule {a.rule}")

    t = time.perf_counter()
    exact = np.array([solve(cells_all[i], macro_all[i], int(nb_all[i]), int(pl_all[i]), a.rule)[0] for i in idx])
    print(f"solved in {time.perf_counter() - t:.1f}s: exact win/draw/loss for the mover = "
          f"{(exact == 1).mean():.3f}/{(exact == 0).mean():.3f}/{(exact == -1).mean():.3f}")

    fe = FusedEvaluator(load_checkpoint(a.checkpoint, device), device)
    sym = SymmetryAveragedEvaluator(fe)
    cells = torch.from_numpy(cells_all[idx]).to(device)
    macro = torch.from_numpy(macro_all[idx]).to(device)
    nb = torch.from_numpy(nb_all[idx]).to(device)
    player = torch.from_numpy(pl_all[idx]).to(device)
    n = len(idx)
    done = torch.zeros(n, dtype=torch.bool, device=device)
    winner = torch.zeros(n, dtype=torch.int8, device=device)
    ex = torch.from_numpy(exact).to(device).float()

    def sign_acc(v):
        s = torch.where(v > 0.33, 1.0, torch.where(v < -0.33, -1.0, 0.0))
        return float((s == ex).float().mean()), float((torch.sign(v) == torch.sign(ex)).float().mean())

    rows = []
    for name, evl in (("raw net", fe), ("raw net, symmetry-averaged", sym)):
        with torch.no_grad():
            _, v = evl(cells, macro, nb, player, done)
        acc3, accs = sign_acc(v)
        rows.append((name, acc3, accs, float((v - ex).abs().mean()), None))
    for s in [int(x) for x in a.sims.split(",")]:
        scfg = SearchConfig(n_sims=s, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(s, 24))
        r = BatchedSearch(fe, n, scfg, device, rule=a.rule).search(cells, macro, nb, player, done, winner, selfplay=False)
        acc3, accs = sign_acc(r.root_value)
        # move error: exact value after the chosen move
        c2, m2, nb2, p2, d2, w2, _ = step_state(cells, macro, nb, player, done, winner, r.action, a.rule)
        child_val = np.empty(n)
        c2n, m2n, nb2n, p2n, d2n, w2n = c2.cpu().numpy(), m2.cpu().numpy(), nb2.cpu().numpy(), p2.cpu().numpy(), d2.cpu().numpy(), w2.cpu().numpy()
        for i in range(n):
            if d2n[i]:
                child_val[i] = 0 if w2n[i] == 0 else (1 if w2n[i] == p2n[i] else -1)
            else:
                child_val[i] = solve(c2n[i], m2n[i], int(nb2n[i]), int(p2n[i]), a.rule)[0]
        move_err = float((-child_val < exact).mean())
        rows.append((f"search {s} sims", acc3, accs, float((r.root_value - ex).abs().mean()), move_err))
    print(f"\n{'evaluator':30s} {'3-way acc':>10s} {'sign acc':>9s} {'mean|err|':>10s} {'move error':>11s}")
    for name, acc3, accs, err, me in rows:
        print(f"{name:30s} {acc3:10.3f} {accs:9.3f} {err:10.3f} {'' if me is None else f'{me:11.3f}'}")
    # by empties bucket for the raw net and the largest search budget
    e = emp[idx]
    print("\nby remaining empties (raw 3-way acc | last search: 3-way acc, move error):")
    with torch.no_grad():
        _, v_raw = fe(cells, macro, nb, player, done)
    s_raw = torch.where(v_raw > 0.33, 1.0, torch.where(v_raw < -0.33, -1.0, 0.0)).cpu().numpy()
    s_srch = torch.where(r.root_value > 0.33, 1.0, torch.where(r.root_value < -0.33, -1.0, 0.0)).cpu().numpy()
    for lo, hi in ((a.min_empty, 9), (10, 12), (13, 14), (15, a.max_empty)):
        m = (e >= lo) & (e <= hi)
        if m.sum() > 20:
            print(f"  {lo:2d}-{hi:2d} empties (n={int(m.sum()):4d}): {float((s_raw[m] == exact[m]).mean()):.3f} | {float((s_srch[m] == exact[m]).mean()):.3f}, {float((-child_val[m] < exact[m]).mean()):.3f}")
    if a.out:
        out = tag_path(a.out, a.rule)
        np.savez_compressed(out, rule=np.array(a.rule), idx=idx, exact=exact, empties=e)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
