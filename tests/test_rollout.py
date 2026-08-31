"""Rollout anchor: bitboard rules agree with uttt.game move by move; UCT finds exact-solver moves; throughput."""
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.arena import RandomPlayer  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.openings import Suite, format_report, play_paired, random_openings, summarize  # noqa: E402
from uttt.rollout import DN, LEN, NB, PL, WN, RolloutPlayer, _apply, _legal, encode_states, search_position  # noqa: E402
from uttt.solver import empties_in_open_boards, solve  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def test_rules(n_games=300, seed=0):
    rng = np.random.default_rng(seed)
    buf = np.zeros(81, dtype=np.int64)
    plies = 0
    for _ in range(n_games):
        ref = UTTT()
        st = np.zeros(LEN, dtype=np.int64)
        st[PL] = 1
        st[NB] = -1
        while True:
            n = _legal(st, buf)
            assert sorted(buf[:n].tolist()) == ref.legal_moves(), (ref, buf[:n])
            enc = encode_states(ref.cells[None], ref.macro[None], np.array([ref.next_board]), np.array([ref.player]))[0]
            assert np.array_equal(enc[:PL + 1], st[:PL + 1]), (enc, st)
            assert bool(st[DN]) == ref.done and int(st[WN]) == ref.winner
            if ref.done:
                break
            m = int(rng.choice(ref.legal_moves()))
            ref.play(m)
            _apply(st, m)
            plies += 1
    print(f"bitboard rules agree with the reference engine over {n_games} random games ({plies} plies)")


def random_endgame(rng, max_empty):
    while True:
        g = UTTT()
        while not g.done and empties_in_open_boards(g.cells, g.macro) > max_empty:
            g.play(int(rng.choice(g.legal_moves())))
        if not g.done:
            return g


def test_uct_vs_solver(n=40, max_empty=9, playouts=20_000, seed=1):
    """On solved endgames the chosen move must keep the exact value (no regret) in nearly every case."""
    rng = np.random.default_rng(seed)
    ok = 0
    decisive = 0
    for _ in range(n):
        g = random_endgame(rng, max_empty)
        v_root, _ = solve(g.cells, g.macro, g.next_board, g.player)
        m, wr, visits = search_position(g.cells, g.macro, g.next_board, g.player, playouts, seed=int(rng.integers(1 << 30)))
        assert g.legal_mask()[m]
        h = g.clone()
        h.play(m)
        v_after = 0 if h.winner == 0 and h.done else ((1 if h.winner == g.player else -1) if h.done else -solve(h.cells, h.macro, h.next_board, h.player)[0])
        ok += v_after == v_root
        decisive += v_root != 0
    print(f"UCT {playouts} playouts keeps the exact value on {ok}/{n} solved endgames (<= {max_empty} empties, {decisive} decisive)")
    assert ok >= 0.9 * n


def test_beats_random(k=48):
    torch.manual_seed(0)
    rng = np.random.default_rng(2)
    suite = Suite.from_sequences(random_openings(k, 4, rng), ["random"] * k)
    t = time.perf_counter()
    r = play_paired(RolloutPlayer(2000, seed=0), RandomPlayer(DEV), suite, DEV)
    s = summarize(r)
    print(format_report(s), f"\n[{time.perf_counter() - t:.0f}s]")
    assert s["overall"]["ci"][0] > 0.85, s["overall"]


def test_reproducible():
    from uttt.batch import BatchUTTT
    g = BatchUTTT(8, DEV)
    a = RolloutPlayer(3000, seed=5).act(g)
    b = RolloutPlayer(3000, seed=5).act(g)
    c = RolloutPlayer(3000, seed=6).act(g)
    assert torch.equal(a, b)
    print("reproducible for a seed; different seed differs:", not torch.equal(a, c))


def bench(playouts=100_000):
    from uttt.batch import BatchUTTT
    for G in (1, 24, 96):
        g = BatchUTTT(G, DEV)
        p = RolloutPlayer(playouts)
        p.act(g)  # JIT warm-up on the first call
        t = time.perf_counter()
        p.act(g)
        dt = time.perf_counter() - t
        print(f"{G:3d} games x {playouts} playouts: {dt:.2f}s = {G * playouts / dt / 1e6:.2f} M playouts/s")


if __name__ == "__main__":
    test_rules()
    test_uct_vs_solver()
    test_reproducible()
    test_beats_random()
    bench()
    print("ok")
