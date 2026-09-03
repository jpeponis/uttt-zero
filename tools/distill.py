"""Distil the network's search into a legible linear surrogate (PLAN5 §3 B6) and measure what it misses.

    .venv/Scripts/python.exe tools/distill.py --net runs/deep10_c1_300/net_0300.pt --data runs/probe_data_deep8late.npz --sims 256 --dagger 1 --device cuda:1 --out runs/surrogate_deep10.json
    .venv/Scripts/python.exe tools/openings.py match --a surrogate:runs/surrogate_deep10.json --b runs/v2b/net_0150.pt --sims 64 --device cuda:1

Targets: the net's 256-sim root visit distribution and root value on held-out positions (from tools/probe.py build).
Model: policy = softmax over legal moves of a linear score of uttt.surrogate.MOVE_FEATURES (the position after the
move, from the mover's view); value = tanh of a linear function of POSITION_FEATURES. Fitted by gradient descent on
the train split, scored on the test split (top-1 agreement with the search's move, cross-entropy, value R²). One
DAgger round (--dagger 1): the surrogate plays itself with 64-sim search, the positions it reaches are labelled by
the net's search, and the fit is repeated on the union. The weights are printed as a table — the legible part —
and the surrogate's Elo on the paired suite (a separate match) is the share of the net's play the features miss.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.arena import SearchPlayer  # noqa: E402
from uttt.batch import BatchUTTT, legal_mask  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.surrogate import MOVE_FEATURES, POSITION_FEATURES, SurrogateEvaluator, move_features, position_features  # noqa: E402


@torch.no_grad()
def search_targets(fe, cells, macro, nb, player, sims, device, bs=4096):
    """Root visit distribution (n, 81) and root value (n,) of the net's search on each position."""
    n = cells.shape[0]
    pol = torch.zeros(n, 81, device=device)
    val = torch.zeros(n, device=device)
    for i in range(0, n, bs):
        sl = slice(i, min(i + bs, n))
        k = sl.stop - sl.start
        g = BatchUTTT(k, device)
        g.cells[:], g.macro[:], g.next_board[:], g.player[:] = cells[sl], macro[sl], nb[sl], player[sl]
        s = BatchedSearch(fe, k, SearchConfig(n_sims=sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(sims, 24)), device)
        r = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
        N0 = s.N[:, 0].float()
        pol[sl] = N0 / N0.sum(1, keepdim=True).clamp(min=1)
        val[sl] = r.root_value
    return pol, val


@torch.no_grad()
def features(cells, macro, nb, player, bs=512):
    F, G, L = [], [], []
    for i in range(0, cells.shape[0], bs):
        sl = slice(i, i + bs)
        F.append(move_features(cells[sl], macro[sl], nb[sl], player[sl]))
        G.append(position_features(cells[sl], macro[sl], nb[sl], player[sl]))
        L.append(legal_mask(cells[sl], macro[sl], nb[sl]))
    return torch.cat(F), torch.cat(G), torch.cat(L)


def fit(F, L, pol, G, val, tr, te, steps=600, lr=0.05, l2=1e-4, seed=0):
    """Policy: conditional logit over legal moves with per-move linear scores. Value: tanh-linear on standardised G."""
    torch.manual_seed(seed)
    d = F.device
    w = torch.zeros(F.shape[2], device=d, requires_grad=True)
    opt = torch.optim.Adam([w], lr=lr)
    Ftr, Ltr, Ptr = F[tr], L[tr], pol[tr]
    for _ in range(steps):
        logits = (Ftr @ w).masked_fill(~Ltr, -1e9)
        logp = torch.log_softmax(logits, 1)
        loss = -(Ptr * logp).sum(1).mean() + l2 * (w * w).sum()
        opt.zero_grad()
        loss.backward()
        opt.step()
    mu, sd = G[tr].mean(0), G[tr].std(0) + 1e-6
    Gs = (G - mu) / sd
    wv = torch.zeros(G.shape[1], device=d, requires_grad=True)
    bv = torch.zeros(1, device=d, requires_grad=True)
    opt = torch.optim.Adam([wv, bv], lr=lr)
    for _ in range(steps):
        pred = torch.tanh(Gs[tr] @ wv + bv)
        loss = ((pred - val[tr]) ** 2).mean() + l2 * (wv * wv).sum()
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        res = {}
        for name, idx in (("train", tr), ("test", te)):
            logits = (F[idx] @ w).masked_fill(~L[idx], -1e9)
            logp = torch.log_softmax(logits, 1)
            res[name] = {"policy_ce": float(-(pol[idx] * logp).sum(1).mean()),
                         "top1_agreement": float((logits.argmax(1) == pol[idx].argmax(1)).float().mean()),
                         "prob_on_search_move": float(torch.exp(logp).gather(1, pol[idx].argmax(1, keepdim=True)).mean()),
                         "value_r2": float(1 - ((torch.tanh(Gs[idx] @ wv + bv) - val[idx]) ** 2).mean() / val[idx].var())}
    return w.detach(), wv.detach(), float(bv), mu, sd, res


@torch.no_grad()
def dagger_positions(surr, n_games, device, sims=64, per_game=4, seed=0):
    """Self-play the surrogate (both sides, 64-sim search) and sample positions it reaches."""
    torch.manual_seed(seed)
    g = BatchUTTT(n_games, device)
    player = SearchPlayer(surr, n_games, SearchConfig(n_sims=sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(sims, 24)), device)
    snaps = []
    ply = 0
    while not bool(g.done.all()) and ply < 81:
        keep = (~g.done) & (torch.rand(n_games, device=device) < per_game / 50)
        if keep.any():
            snaps.append((g.cells[keep].clone(), g.macro[keep].clone(), g.next_board[keep].clone(), g.player[keep].clone()))
        g.step(player.act(g))
        ply += 1
    return [torch.cat(x) for x in zip(*snaps)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default="runs/deep10_c1_300/net_0300.pt")
    ap.add_argument("--data", default="runs/probe_data_deep8late.npz")
    ap.add_argument("--n", type=int, default=60000)
    ap.add_argument("--sims", type=int, default=256)
    ap.add_argument("--dagger", type=int, default=1, help="DAgger rounds (0 = none)")
    ap.add_argument("--dagger_games", type=int, default=2048)
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = torch.device(a.device)
    t0 = time.perf_counter()
    z = np.load(a.data)
    n = min(a.n, len(z["ply"]))
    t = lambda k: torch.from_numpy(z[k][:n]).to(device)  # noqa: E731
    cells, macro, nb, player = t("cells"), t("macro"), t("next_board"), t("player")
    split = z["split"][:n]
    tr = torch.from_numpy(np.flatnonzero(split == 0)).to(device)
    te = torch.from_numpy(np.flatnonzero(split == 1)).to(device)
    fe = FusedEvaluator(load_checkpoint(a.net, device), device)
    pol, val = search_targets(fe, cells, macro, nb, player, a.sims, device)
    print(f"{n} positions ({len(tr)} train / {len(te)} test); {a.sims}-sim targets from {a.net}  [{time.perf_counter() - t0:.0f}s]", flush=True)
    F, G, L = features(cells, macro, nb, player)
    w, wv, bv, mu, sd, res = fit(F, L, pol, G, val, tr, te, a.steps)
    print(f"round 0: test top-1 agreement {res['test']['top1_agreement']:.3f}, prob on the search move {res['test']['prob_on_search_move']:.3f}, "
          f"policy CE {res['test']['policy_ce']:.3f}, value R2 {res['test']['value_r2']:.3f}  [{time.perf_counter() - t0:.0f}s]", flush=True)
    rounds = [res]
    surr = SurrogateEvaluator(w, wv, bv, device, mu, sd)
    for r in range(a.dagger):
        dc, dm, dn, dp = dagger_positions(surr, a.dagger_games, device, seed=r)
        dpol, dval = search_targets(fe, dc, dm, dn, dp, a.sims, device)
        dF, dG, dL = features(dc, dm, dn, dp)
        with torch.no_grad():
            agree = float(((dF @ w).masked_fill(~dL, -1e9).argmax(1) == dpol.argmax(1)).float().mean())
        print(f"DAgger round {r + 1}: {len(dc)} positions from {a.dagger_games} surrogate self-play games; the old surrogate agreed with the net on {agree:.3f} of them", flush=True)
        F2, G2, L2, pol2, val2 = torch.cat([F, dF]), torch.cat([G, dG]), torch.cat([L, dL]), torch.cat([pol, dpol]), torch.cat([val, dval])
        tr2 = torch.cat([tr, torch.arange(len(F), len(F2), device=device)])
        w, wv, bv, mu, sd, res = fit(F2, L2, pol2, G2, val2, tr2, te, a.steps, seed=r + 1)
        print(f"round {r + 1}: test top-1 agreement {res['test']['top1_agreement']:.3f}, prob on the search move {res['test']['prob_on_search_move']:.3f}, "
              f"policy CE {res['test']['policy_ce']:.3f}, value R2 {res['test']['value_r2']:.3f}  [{time.perf_counter() - t0:.0f}s]", flush=True)
        rounds.append(res)
        surr = SurrogateEvaluator(w, wv, bv, device, mu, sd)
    print("\npolicy weights (score of a move = sum of feature x weight; softmax over legal moves):")
    for name, x in sorted(zip(MOVE_FEATURES, w.tolist()), key=lambda kv: -abs(kv[1])):
        print(f"  {name:24s} {x:+.3f}")
    print("value weights (standardised features; value = tanh(sum + bias)):")
    for name, x in sorted(zip(POSITION_FEATURES, wv.tolist()), key=lambda kv: -abs(kv[1])):
        print(f"  {name:24s} {x:+.3f}")
    print(f"  bias                     {bv:+.3f}")
    surr.save(a.out, {"net": a.net, "data": a.data, "n": n, "sims": a.sims, "dagger": a.dagger, "rounds": rounds, "built": time.strftime("%Y-%m-%d %H:%M")})
    print(f"wrote {a.out}  [{time.perf_counter() - t0:.0f}s]")


if __name__ == "__main__":
    main()
