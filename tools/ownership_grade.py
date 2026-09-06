"""The ownership head, graded properly (PLAN6 E9; REVIEW-astra §6.5). KNOWLEDGE 40 says the auxiliary ownership head
"learns almost nothing beyond the board" from an aggregate accuracy that mixes boards whose owner is already fixed
with boards still open. Here every number is on OPEN boards only (macro status 0 at the position), on the held-out
test split of a probe dataset (tools/probe.py build), by ply bucket, against:

  majority   the majority final class of open boards in the ply bucket (train split) — the deterministic
             current-status baseline: the status of an open board says "open", so this is all it can predict;
  local      a multinomial logistic regression on hand-written per-board features (the board's cells from the
             mover's side, local threats, empties, target / free-move flags, board class, macro threats through
             the board, the count margin, the ply), fitted on the train split;
  head       the net's own ownership head;
  probe      a linear read-out of the final residual block, trained on the train split for open boards only,
             on the trained net and (--control) on a randomly initialised net of the same shape.

    .venv/Scripts/python.exe tools/ownership_grade.py --data runs/probe_data_deep8late.npz --net runs/deep10_c1_300/net_0300.pt --control --device cuda:1 --out runs/plan6_E9_ownership_deep10.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from probe import layer_activations  # noqa: E402
from uttt.batch import LINES, encode  # noqa: E402
from uttt.model import NetConfig, ResNet, load_checkpoint  # noqa: E402

PLY_BUCKETS = ((0, 7), (8, 19), (20, 31), (32, 43), (44, 80))
BOARD_CLASS = torch.tensor([0, 1, 0, 1, 2, 1, 0, 1, 0])  # corner / edge / centre


def local_features(cells, macro, nb, player, ply) -> torch.Tensor:
    """(N, 9, F) per-board features from the mover's perspective."""
    N = cells.shape[0]
    d = cells.device
    lines = LINES.to(d)
    p = player.view(N, 1, 1).float()
    rel = cells.view(N, 9, 9).float() * p  # +1 own, -1 opponent
    own, opp, emp = (rel == 1).float(), (rel == -1).float(), (rel == 0).float()
    cl = rel[:, :, lines]  # (N, 9, 8, 3)
    t_for = ((cl == 1).sum(3) == 2) & ((cl == -1).sum(3) == 0)
    t_against = ((cl == -1).sum(3) == 2) & ((cl == 1).sum(3) == 0)
    mrel = macro.float() * p.view(N, 1)
    mrel = torch.where(macro.abs() == 1, mrel, torch.zeros_like(mrel))  # own +1 / opp -1 / else 0
    ml = mrel[:, lines]  # (N, 8, 3)
    m_for = torch.zeros(N, 9, device=d)
    m_against = torch.zeros(N, 9, device=d)
    for li in range(8):
        for j in range(3):
            b = lines[li, j]
            others = [lines[li, k] for k in range(3) if k != j]
            open_b = macro[:, b] == 0
            m_for[:, b] += (open_b & (mrel[:, others[0]] == 1) & (mrel[:, others[1]] == 1)).float()
            m_against[:, b] += (open_b & (mrel[:, others[0]] == -1) & (mrel[:, others[1]] == -1)).float()
    target = F.one_hot(nb.long().clamp(min=0), 9).float() * (nb >= 0).float().view(N, 1)
    free = (nb < 0).float().view(N, 1).expand(N, 9)
    cls = F.one_hot(BOARD_CLASS.to(d), 3).float().unsqueeze(0).expand(N, 9, 3)
    margin = (mrel == 1).sum(1, keepdim=True).float() - (mrel == -1).sum(1, keepdim=True).float()
    feats = [own, opp, emp, t_for.float(), t_against.float(), emp.sum(2, keepdim=True) / 9,
             target.unsqueeze(2), free.unsqueeze(2), cls, m_for.unsqueeze(2), m_against.unsqueeze(2),
             (margin / 4).unsqueeze(2).expand(N, 9, 1), (ply.float().view(N, 1, 1) / 80).expand(N, 9, 1)]
    return torch.cat(feats, 2)


def fit_linear(x_tr, y_tr, x_te, n_out, device, epochs=8, bs=2048, lr=2e-3, seed=0):
    """Multinomial logistic regression (one linear layer) with standardised inputs; returns test predictions."""
    torch.manual_seed(seed)
    mu, sd = x_tr.float().mean(0, keepdim=True), x_tr.float().std(0, keepdim=True) + 1e-3
    lin = torch.nn.Linear(x_tr.shape[1], n_out).to(device)
    opt = torch.optim.AdamW(lin.parameters(), lr=lr, weight_decay=1e-4)
    g = torch.Generator(device=device).manual_seed(seed)
    for _ in range(epochs):
        perm = torch.randperm(x_tr.shape[0], device=device, generator=g)
        for i in range(0, len(perm), bs):
            idx = perm[i : i + bs]
            loss = F.cross_entropy(lin((x_tr[idx].float() - mu) / sd), y_tr[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
    with torch.no_grad():
        return torch.cat([lin((x_te[i : i + 4096].float() - mu) / sd).argmax(1) for i in range(0, x_te.shape[0], 4096)])


@torch.no_grad()
def head_predictions(net, cells, macro, nb, player, device, bs=2048):
    out = []
    for i in range(0, cells.shape[0], bs):
        sl = slice(i, i + bs)
        done = torch.zeros(cells[sl].shape[0], dtype=torch.bool, device=device)
        _, _, o, _ = net(encode(cells[sl], macro[sl], nb[sl], player[sl], done, extra=net.cfg.extra_planes))
        pred = o.argmax(2)
        if net.cfg.own_classes == 4:  # self 0 / opponent 1 / full 2 / open 3 -> self 0 / neither 1 / opponent 2
            pred = torch.where(pred == 0, 0, torch.where(pred == 1, 2, 1))
        out.append(pred)
    return torch.cat(out)


def trunk_probe(net, cells, macro, nb, player, y, open_mask, tr, te, device):
    """Linear read-out of the last block -> 9 x 3 classes, trained on open boards of the train split."""
    acts = layer_activations(net, cells, macro, nb, player, f"block{net.cfg.blocks:02d}", device)
    mu, sd = acts[tr].float().mean(0, keepdim=True), acts[tr].float().std(0, keepdim=True) + 1e-3
    lin = torch.nn.Linear(acts.shape[1], 27).to(device)
    opt = torch.optim.AdamW(lin.parameters(), lr=1e-3, weight_decay=1e-4)
    g = torch.Generator(device=device).manual_seed(0)
    for _ in range(8):
        perm = tr[torch.randperm(len(tr), device=device, generator=g)]
        for i in range(0, len(perm), 1024):
            idx = perm[i : i + 1024]
            logits = lin((acts[idx].float() - mu) / sd).view(-1, 9, 3)
            m = open_mask[idx]
            loss = F.cross_entropy(logits[m], y[idx][m])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
    with torch.no_grad():
        return torch.cat([lin((acts[te[i : i + 4096]].float() - mu) / sd).view(-1, 9, 3).argmax(2) for i in range(0, len(te), 4096)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="runs/probe_data_deep8late.npz")
    ap.add_argument("--net", default="runs/deep10_c1_300/net_0300.pt")
    ap.add_argument("--control", action="store_true", help="also probe a randomly initialised net of the same shape")
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    device = torch.device(a.device)
    t0 = time.perf_counter()
    z = np.load(a.data, allow_pickle=True)
    t = lambda k, dt: torch.from_numpy(np.asarray(z[k], dtype=dt)).to(device)  # noqa: E731
    cells, macro, nb, player = t("cells", np.int8), t("macro", np.int8), t("next_board", np.int8), t("player", np.int8)
    ply = t("ply", np.int64)
    split = np.asarray(z["split"])
    y = torch.stack([t(f"label_final_own_{b}", np.int64) for b in range(9)], 1)  # (N, 9): 0 self / 1 neither / 2 opponent
    open_mask = macro == 0
    tr = torch.from_numpy(np.flatnonzero(split == 0)).to(device)
    te = torch.from_numpy(np.flatnonzero(split == 1)).to(device)
    N = cells.shape[0]
    print(f"{a.data}: {N} positions, test split {len(te)}; open boards in test: {int(open_mask[te].sum())} of {9 * len(te)}", flush=True)

    net = load_checkpoint(a.net, device)
    preds = {"head": head_predictions(net, cells, macro, nb, player, device)}
    feats = local_features(cells, macro, nb, player, ply)  # (N, 9, F)
    x_tr, y_tr = feats[tr][open_mask[tr]], y[tr][open_mask[tr]]
    x_te = feats[te].reshape(-1, feats.shape[2])
    preds["local"] = fit_linear(x_tr, y_tr, x_te, 3, device).view(len(te), 9)
    preds["probe"] = trunk_probe(net, cells, macro, nb, player, y, open_mask, tr, te, device)
    if a.control:
        torch.manual_seed(1)
        ctrl = ResNet(net.cfg).to(device).eval()
        preds["probe_random"] = trunk_probe(ctrl, cells, macro, nb, player, y, open_mask, tr, te, device)
        preds["head_random"] = head_predictions(ctrl, cells, macro, nb, player, device)
    # majority baseline per bucket, from the train split's open boards
    ply_tr, ply_te = ply[tr], ply[te]
    rows = []
    for lo, hi in list(PLY_BUCKETS) + [(0, 80)]:
        m_tr = open_mask[tr] & ((ply_tr >= lo) & (ply_tr <= hi)).view(-1, 1)
        m_te = open_mask[te] & ((ply_te >= lo) & (ply_te <= hi)).view(-1, 1)
        n = int(m_te.sum())
        if n == 0:
            continue
        counts = torch.bincount(y[tr][m_tr], minlength=3).float()
        maj = int(counts.argmax())
        truth = y[te][m_te]
        row = {"ply": f"{lo}-{hi}", "n_open_boards": n, "class_shares_test": [round(float((truth == k).float().mean()), 3) for k in range(3)],
               "majority": round(float((truth == maj).float().mean()), 4)}
        for k, p in preds.items():
            pk = p[:, :] if p.shape[0] == len(te) else p[te]
            row[k] = round(float((pk[m_te] == truth).float().mean()), 4)
        rows.append(row)
    cols = ["majority", "local", "head", "probe"] + (["probe_random", "head_random"] if a.control else [])
    print(f"\nOwnership on OPEN boards, test split, accuracy by ply bucket (net {a.net}; classes self / neither / opponent):")
    print("  ply     n_open   shares(s/n/o)        " + "  ".join(f"{c:>12s}" for c in cols))
    for r in rows:
        print(f"  {r['ply']:6s} {r['n_open_boards']:7d}   {str(r['class_shares_test']):22s} " + "  ".join(f"{100 * r[c]:12.1f}" for c in cols))
    print(f"  ({time.perf_counter() - t0:.0f}s)")
    if a.out:
        with open(a.out, "w") as f:
            json.dump({"data": a.data, "net": a.net, "rows": rows, "columns": cols}, f, indent=1)
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
