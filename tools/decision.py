"""Decision time (PLAN2 §5 step 7): when does the outcome of a game become predictable?

    .venv/Scripts/python.exe tools/decision.py runs/v2b/net_0150.pt --corpus runs/v2a --last 2 --games 4000 --sims 64 --device cuda:1

Held-out corpus games (another run's self-play) are replayed; at every ply the net's WDL head (raw) and the
search's root value predict the final result. Reported by ply: log-loss and accuracy of the raw WDL head,
sign accuracy of raw and search values, and the share of games already "settled" (the 3-way prediction is
correct at this ply and at every later ply). Also the distribution of each game's settling ply.
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
from uttt.endgame import wdl_probs  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402


def three_way(v: np.ndarray) -> np.ndarray:
    return np.where(v > 0.33, 1, np.where(v < -0.33, -1, 0))


@torch.no_grad()
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--corpus", default="runs/v2a")
    ap.add_argument("--last", type=int, default=2)
    ap.add_argument("--games", type=int, default=4000)
    ap.add_argument("--sims", type=int, default=64)
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    device = torch.device(a.device)
    files = sorted(glob.glob(os.path.join(a.corpus, "games", "games_*.npz")))[-a.last :]
    moves = np.concatenate([np.load(f)["moves"] for f in files])
    winners = np.concatenate([np.load(f)["winners"] for f in files])
    lengths = np.concatenate([np.load(f)["lengths"] for f in files])
    rng = np.random.default_rng(0)
    sel = rng.choice(len(winners), size=min(a.games, len(winners)), replace=False)
    moves, winners, lengths = moves[sel], winners[sel], lengths[sel]
    G, T = len(sel), int(lengths.max())
    fe = FusedEvaluator(load_checkpoint(a.checkpoint, device), device)
    srch = BatchedSearch(fe, G, SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(a.sims, 24)), device)
    g = BatchUTTT(G, device)
    mv = torch.from_numpy(moves.astype(np.int64)).to(device)
    final = torch.from_numpy(winners.astype(np.int64)).to(device)
    y = (1 - final)  # X's class: win 0 / draw 1 / loss 2
    raw_v = np.full((G, T), np.nan)
    srch_v = np.full((G, T), np.nan)
    q_v = np.full((G, T), np.nan)  # Q of the search's chosen move (best child), a sharper predictor than the mixed root value
    ll = np.full((G, T), np.nan)
    acc_wdl = np.full((G, T), np.nan)
    for t in range(T):
        alive = ~g.done
        sign = torch.where(g.player == 1, 1.0, -1.0)
        wdl = wdl_probs(fe, g.cells, g.macro, g.next_board, g.player)  # mover's perspective
        wdl_x = torch.where(g.player.unsqueeze(1) == 1, wdl, wdl.flip(1))  # X's perspective
        r = srch.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
        ar = torch.arange(G, device=device)
        q_best = srch.W[ar, 0, r.action] / srch.N[ar, 0, r.action].clamp(min=1)
        al = alive.cpu().numpy()
        raw_v[al, t] = ((wdl_x[:, 0] - wdl_x[:, 2])).cpu().numpy()[al]
        srch_v[al, t] = (r.root_value * sign).cpu().numpy()[al]
        q_v[al, t] = (q_best * sign).cpu().numpy()[al]
        ll[al, t] = (-torch.log(wdl_x[torch.arange(G, device=device), y].clamp(min=1e-9))).cpu().numpy()[al]
        acc_wdl[al, t] = (wdl_x.argmax(1) == y).float().cpu().numpy()[al]
        g.step(torch.where(alive, mv[:, t].clamp(min=0), torch.zeros_like(mv[:, t])))
    fin = winners.astype(np.int64)
    # settled: 3-way prediction equals the final result at this ply and all later plies of the game
    def settled_from(v):
        pred = three_way(np.nan_to_num(v, nan=99.0))
        ok = (pred == fin[:, None]) | np.isnan(v)
        # suffix-and over plies (only real plies count; padded plies are True)
        suf = np.flip(np.cumprod(np.flip(ok, 1), 1), 1).astype(bool)
        return suf & ~np.isnan(v)

    set_raw, set_srch, set_q = settled_from(raw_v), settled_from(srch_v), settled_from(q_v)
    print(f"{G} held-out games from {[os.path.basename(f) for f in files]} ({a.corpus}); net {a.checkpoint}; search {a.sims} sims")
    print(f"result X/O/draw: {(fin == 1).mean():.3f}/{(fin == -1).mean():.3f}/{(fin == 0).mean():.3f}; mean length {lengths.mean():.1f}")
    print(f"\n{'ply':>4s} {'alive':>6s} {'WDL logloss':>12s} {'WDL acc':>8s} {'raw sign':>9s} {'srch sign':>10s} {'Q sign':>7s} {'settled raw':>12s} {'settled srch':>13s} {'settled Q':>10s}")
    for t in range(0, T, 4):
        al = ~np.isnan(raw_v[:, t])
        if al.sum() < 30:
            break
        sr = (np.sign(raw_v[al, t]) == np.sign(fin[al])).mean()
        ss = (np.sign(srch_v[al, t]) == np.sign(fin[al])).mean()
        sq = (np.sign(q_v[al, t]) == np.sign(fin[al])).mean()
        print(f"{t:4d} {int(al.sum()):6d} {np.nanmean(ll[al, t]):12.3f} {np.nanmean(acc_wdl[al, t]):8.3f} {sr:9.3f} {ss:10.3f} {sq:7.3f} "
              f"{set_raw[al, t].mean():12.3f} {set_srch[al, t].mean():13.3f} {set_q[al, t].mean():10.3f}")
    for name, s in (("raw value", set_raw), ("search root value", set_srch), ("best-child Q", set_q)):
        first = np.array([np.argmax(s[i]) if s[i].any() else lengths[i] for i in range(G)])
        frac = first / lengths
        print(f"\nsettling ply ({name}): median {np.median(first):.0f}, quartiles {np.percentile(first, 25):.0f}-{np.percentile(first, 75):.0f}; "
              f"as a fraction of game length: median {np.median(frac):.2f}, p10 {np.percentile(frac, 10):.2f}, p90 {np.percentile(frac, 90):.2f}; "
              f"never settled before the last ply: {(first >= lengths - 1).mean():.3f}")
        for w, nm in ((1, "X wins"), (-1, "O wins"), (0, "draws")):
            m = fin == w
            print(f"  {nm:7s}: median settling ply {np.median(first[m]):.0f}, fraction {np.median(frac[m]):.2f} (n={int(m.sum())})")


if __name__ == "__main__":
    main()
