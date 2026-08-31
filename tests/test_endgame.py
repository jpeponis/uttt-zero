"""Endgame set: exact child labels agree with the solver, cluster bootstrap, WDL probabilities, end-to-end eval."""
import os
import sys
import tempfile

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.endgame import (ILLEGAL, EndgameSet, build_set, cluster_bootstrap, evaluate, evaluate_rollout, format_report,  # noqa: E402
                          solve_children, wdl_probs)
from uttt.game import UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import NetConfig, ResNet  # noqa: E402
from uttt.rollout import RolloutPlayer  # noqa: E402
from uttt.solver import empties_in_open_boards, solve  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def random_endgame(rng, max_empty):
    while True:
        g = UTTT()
        while not g.done and empties_in_open_boards(g.cells, g.macro) > max_empty:
            g.play(int(rng.choice(g.legal_moves())))
        if not g.done:
            return g


def test_children(n=30, seed=0):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        g = random_endgame(rng, 10)
        v, child = solve_children((g.cells, g.macro, g.next_board, g.player))
        assert v == solve(g.cells, g.macro, g.next_board, g.player)[0]
        legal = g.legal_mask()
        assert ((child != ILLEGAL) == legal).all()
        assert child[legal].max() == v
    print("child labels agree with the solver")


def test_cluster_bootstrap():
    rng = np.random.default_rng(1)
    groups = np.repeat(np.arange(200), 3)
    x = (rng.random(600) < 0.6).astype(float)
    lo, hi = cluster_bootstrap(x, groups, 1000)
    assert lo < x.mean() < hi and hi - lo < 0.2
    # perfectly correlated clusters widen the interval relative to i.i.d. positions
    x2 = np.repeat((rng.random(200) < 0.6).astype(float), 3)
    lo2, hi2 = cluster_bootstrap(x2, groups, 1000)
    lo3, hi3 = cluster_bootstrap(x2, np.arange(600), 1000)
    assert (hi2 - lo2) > 1.5 * (hi3 - lo3), (hi2 - lo2, hi3 - lo3)
    print("cluster bootstrap ok")


def test_build_eval():
    torch.manual_seed(0)
    with tempfile.TemporaryDirectory() as tmp:
        # tiny corpus of random games in the persisted format
        rng = np.random.default_rng(2)
        os.makedirs(os.path.join(tmp, "games"))
        G = 150
        moves = np.full((G, 82), -1, dtype=np.int8)
        lengths = np.zeros(G, dtype=np.int64)
        for i in range(G):
            g = UTTT()
            while not g.done:
                m = int(rng.choice(g.legal_moves()))
                moves[i, g.move_count] = m
                g.play(m)
            lengths[i] = g.move_count
        np.savez_compressed(os.path.join(tmp, "games", "games_0000.npz"), moves=moves, lengths=lengths)
        es = build_set(tmp, last=1, per_stratum=2, per_game=2, min_empty=6, max_empty=12, max_solve=400, processes=1, seed=0, log=lambda *a: None)
        assert 0 < es.n <= 2 * 24 and (es.exact == es.child.max(1)).all()
        path = os.path.join(tmp, "e.npz")
        es.save(path)
        es2 = EndgameSet.load(path)
        assert np.array_equal(es2.child, es.child) and es2.meta["name"] == "e"
        fe = FusedEvaluator(ResNet(NetConfig(blocks=2, filters=16)).to(DEV), DEV)
        cells = torch.from_numpy(es.cells).to(DEV)
        macro = torch.from_numpy(es.macro).to(DEV)
        nb = torch.from_numpy(es.next_board).to(DEV)
        player = torch.from_numpy(es.player).to(DEV)
        wdl = wdl_probs(fe, cells, macro, nb, player)
        _, v = fe(cells, macro, nb, player, torch.zeros(es.n, dtype=torch.bool, device=DEV))
        assert torch.allclose(wdl[:, 0] - wdl[:, 2], v, atol=1e-3)
        res = evaluate(fe, es, torch.device(DEV), sims=(8, 16), n_boot=200)
        row = evaluate_rollout(RolloutPlayer(2000).act, es, 200)
        print(format_report(es, res, [row]))
        assert row["regret"] < res["rows"][0]["regret"] + 0.5  # rollout UCT is far better than an untrained net
        for r in res["rows"] + [row]:
            for k in ("regret", "optimal"):
                if k in r:
                    assert r[k + "_ci"][0] <= r[k] <= r[k + "_ci"][1]
    print("build / save / load / evaluate ok")


if __name__ == "__main__":
    test_children()
    test_cluster_bootstrap()
    test_build_eval()
    print("ok")
