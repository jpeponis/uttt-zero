"""Post-hoc WDL calibration (PLAN2 §2d: the value head under-predicts draws). Fits a bias vector on the
(win, draw, loss) logits by maximum likelihood on half of the exact endgame set (split by source game),
reports accuracy / Brier / log-loss on the other half, then plays the calibrated evaluator against the
uncalibrated one on the paired opening suite (the search uses win - loss as its scalar value, so a draw
bias changes play, not only classification).

    .venv/Scripts/python.exe tools/calibrate.py runs/v2b/net_0150.pt --device cuda:1 [--cap 100]
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.arena import SearchPlayer  # noqa: E402
from uttt.endgame import EndgameSet, evaluate, format_report, wdl_probs  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.openings import Suite, format_report as fmt_match, play_paired, summarize  # noqa: E402
from uttt.search import SearchConfig  # noqa: E402


def fit_bias(logits: torch.Tensor, y: torch.Tensor, steps: int = 500) -> torch.Tensor:
    b = torch.zeros(3, device=logits.device, requires_grad=True)
    opt = torch.optim.LBFGS([b], max_iter=steps, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        loss = torch.nn.functional.cross_entropy(logits + b, y)
        loss.backward()
        return loss

    opt.step(closure)
    return b.detach() - b.detach().mean()  # softmax is shift-invariant; centre for readability


@torch.no_grad()
def raw_logits(fe, es, idx, device):
    from uttt.batch import encode

    t = lambda a: torch.from_numpy(a[idx]).to(device)  # noqa: E731
    obs = encode(t(es.cells), t(es.macro), t(es.next_board), t(es.player), None, extra=fe.extra)
    if fe.half:
        obs = obs.half()
    if fe.channels_last:
        obs = obs.contiguous(memory_format=torch.channels_last)
    _, v, *_ = fe.net(obs)
    return v.float()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--set", default="suites/endgame_v1.npz")
    ap.add_argument("--suite", default="suites/openings_v1.npz")
    ap.add_argument("--cap", type=int, default=0)
    ap.add_argument("--sims", type=int, default=64)
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    device = torch.device(a.device)
    es = EndgameSet.load(a.set)
    net = load_checkpoint(a.checkpoint, device)
    fe = FusedEvaluator(net, device)
    games = np.unique(es.game_id)
    rng = np.random.default_rng(0)
    fit_games = set(rng.choice(games, size=len(games) // 2, replace=False).tolist())
    fit = np.array([g in fit_games for g in es.game_id])
    y = torch.from_numpy(1 - es.exact.astype(np.int64)).to(device)
    lg_fit = raw_logits(fe, es, np.flatnonzero(fit), device)
    b = fit_bias(lg_fit, y[torch.from_numpy(fit).to(device)])
    print(f"fitted WDL logit bias on {int(fit.sum())} positions ({len(fit_games)} games): win {b[0]:+.3f} draw {b[1]:+.3f} loss {b[2]:+.3f}")
    hold = np.flatnonzero(~fit)
    lg_hold = raw_logits(fe, es, hold, device)
    yh = y[torch.from_numpy(~fit).to(device)]
    for name, lg in (("uncalibrated", lg_hold), ("calibrated", lg_hold + b)):
        p = torch.softmax(lg, 1)
        acc = float((p.argmax(1) == yh).float().mean())
        brier = float(((p - torch.nn.functional.one_hot(yh, 3)) ** 2).sum(1).mean())
        ll = float(torch.nn.functional.cross_entropy(lg, yh))
        draws = float((p.argmax(1)[yh == 1] == 1).float().mean())
        print(f"  held-out half ({len(hold)} positions) {name:13s}: WDL acc {100 * acc:.1f}%  draws {100 * draws:.1f}%  Brier {brier:.3f}  log-loss {ll:.3f}")
    # play: calibrated vs uncalibrated on the paired suite
    fe_cal = FusedEvaluator(net, device, wdl_bias=b)
    suite = Suite.load(a.suite)
    if a.cap:
        suite = suite.subset(a.cap)
    cfg = SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(a.sims, 24))
    t = time.perf_counter()
    r = play_paired(SearchPlayer(fe_cal, suite.n, cfg, device), SearchPlayer(fe, suite.n, cfg, device), suite, device)
    print(f"\ncalibrated vs uncalibrated, {suite.n} openings x 2 at {a.sims} sims [{time.perf_counter() - t:.0f}s]")
    print(fmt_match(summarize(r)))
    res = evaluate(fe_cal, es, device, sims=(a.sims,), n_boot=500, symmetrise=False)
    print("\ncalibrated evaluator on the full endgame set (fit half included):")
    print(format_report(es, res))


if __name__ == "__main__":
    main()
