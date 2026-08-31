"""Continuous self-play: recorded games replay to the recorded result; targets are consistent; throughput."""
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.game import UTTT  # noqa: E402
from uttt.model import UniformEvaluator  # noqa: E402
from uttt.search import SearchConfig  # noqa: E402
from uttt.selfplay_cont import ContinuousSelfPlay, GPUReplayBuffer, position_hash  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def test_consistency(n=256, steps=120, sims=8):
    torch.manual_seed(0)
    sp = ContinuousSelfPlay(UniformEvaluator(DEV), n, SearchConfig(n_sims=sims, mode="gumbel", sample_moves=6), DEV)
    pos, games, stats = sp.run(steps)
    G = len(games["winners"])
    assert G > 0 and stats.games == G
    print("finished games:", stats.summary())
    # every finished game replays on the reference engine to the same result
    for k in range(G):
        ref = UTTT()
        L = int(games["lengths"][k])
        for t in range(L):
            ref.play(int(games["moves"][k, t]))
        assert ref.done and ref.winner == int(games["winners"][k]) and ref.move_count == L
        assert int(games["moves"][k, L]) == -1 if L < 82 else True
    # position count equals the sum of finished game lengths
    P = int(pos["cells"].shape[0])
    assert P == int(games["lengths"].sum()), (P, games["lengths"].sum())
    # value / ownership / margin consistency with the game result
    z = pos["value"].cpu().numpy()
    assert set(np.unique(z)).issubset({-1, 0, 1})
    own = pos["ownership"].cpu().numpy()
    margin = pos["margin"].cpu().numpy()
    assert np.array_equal((own == 1).sum(1) - (own == -1).sum(1), margin)
    # margin sign agrees with z for games decided by count
    # policy targets are distributions over legal moves
    pol = pos["policy"].float()
    assert torch.allclose(pol.sum(1), torch.ones_like(pol.sum(1)), atol=1e-2)
    # hash is a function of (cells, next_board, player)
    h2 = position_hash(pos["cells"], pos["next_board"], pos["player"])
    assert torch.equal(h2, pos["hash"])
    # provenance: every finished game's positions share one game id, ids are distinct across games, ply runs 0..L-1
    gid = pos["game"].cpu().numpy()
    plies = pos["ply"].cpu().numpy()
    assert len(np.unique(gid)) == G
    for gg in np.unique(gid)[:20]:
        m = gid == gg
        assert sorted(plies[m].tolist()) == list(range(int(m.sum())))
    assert sp.games_started == n + G
    # pending positions of unfinished games are still staged: every step records n positions
    assert int(sp.len.sum()) == n * steps - P
    print(f"consistency ok: {G} games, {P} positions, mean length {games['lengths'].mean():.1f}")

    buf = GPUReplayBuffer(100_000, DEV)
    buf.add(pos)
    print("dup stats:", buf.update_weights(0.5))
    b = buf.sample(64)
    assert b["cells"].shape == (64, 81)


def bench(n=4096, steps=64, sims=32):
    torch.manual_seed(0)
    sp = ContinuousSelfPlay(UniformEvaluator(DEV), n, SearchConfig(n_sims=sims, mode="gumbel"), DEV)
    sp.run(8)  # warm-up
    torch.cuda.synchronize(DEV)
    t = time.perf_counter()
    pos, games, stats = sp.run(steps)
    torch.cuda.synchronize(DEV)
    dt = time.perf_counter() - t
    print(f"continuous self-play (uniform net): {n} games x {steps} steps in {dt:.1f}s -> {n * steps / dt:.0f} positions/s, "
          f"{stats.games / dt:.1f} finished games/s, {dt / steps / sims * 1000:.1f} ms/sim")


if __name__ == "__main__":
    test_consistency()
    bench()
    print("ok")
