import os
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import FULL, BatchUTTT  # noqa: E402
from uttt.mcts import BatchedMCTS, MCTSConfig, table_of_considered_visits  # noqa: E402
from uttt.model import UniformEvaluator  # noqa: E402

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
MODES = [MCTSConfig(n_sims=200, mode="puct"), MCTSConfig(n_sims=200, mode="gumbel", m_considered=16)]


def test_schedule():
    t = table_of_considered_visits(16, 32)
    assert t.shape == (17, 32)
    assert t[16].tolist()[:16] == [0] * 16  # first phase visits all 16 once
    assert t[2].tolist() == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15]


def _win_position(n=8):
    """X has boards 0 and 1; sent to board 2 where cells 0,1 are X -> move 9*2+2 wins the game."""
    g = BatchUTTT(n, DEV)
    g.macro[:, 0] = 1
    g.macro[:, 1] = 1
    g.cells[:, 9 * 2 + 0] = 1
    g.cells[:, 9 * 2 + 1] = 1
    g.cells[:, 9 * 2 + 3] = -1
    g.cells[:, 9 * 2 + 4] = -1
    g.next_board[:] = 2
    return g


def _block_position(n=8):
    """O to move, sent to board 2; X threatens 9*2+2. Boards 4,5,7,8 closed, so every other O
    move hands X a free move and an immediate win: the block is forced."""
    g = BatchUTTT(n, DEV)
    g.macro[:, 0] = 1
    g.macro[:, 1] = 1
    g.macro[:, 6] = -1
    for b in (4, 5, 7, 8):
        g.macro[:, b] = FULL
    g.cells[:, 9 * 2 + 0] = 1
    g.cells[:, 9 * 2 + 1] = 1
    g.cells[:, 9 * 2 + 3] = -1
    g.cells[:, 9 * 2 + 6] = -1
    g.next_board[:] = 2
    g.player[:] = -1
    return g


def test_tactics():
    for cfg in MODES:
        for name, g, expect_sign in (("win", _win_position(), 1), ("block", _block_position(), -1)):
            mcts = BatchedMCTS(UniformEvaluator(DEV), g.n, cfg, DEV)
            for selfplay in (False, True):
                r = mcts.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=selfplay)
                assert bool((r.policy.argmax(1) == 20).all()), (cfg.mode, name, selfplay, r.visits[0].tolist())
                if not (selfplay and cfg.mode == "puct"):  # puct self-play samples the early moves
                    assert bool((r.action == 20).all()), (cfg.mode, name, selfplay)
            print(f"{cfg.mode:6s} {name:5s}: root value {float(r.root_value.mean()):+.2f}, target p(best) {float(r.policy[0, 20]):.2f}")


def test_search_beats_random(n=256, sims=32):
    from uttt.arena import RandomPlayer, SearchPlayer, play_games
    for mode in ("puct", "gumbel"):
        cfg = MCTSConfig(n_sims=sims, mode=mode)
        torch.manual_seed(0)
        t = time.perf_counter()
        r = play_games(SearchPlayer(UniformEvaluator(DEV), n, cfg, DEV), RandomPlayer(DEV), n, DEV)
        dt = time.perf_counter() - t
        print(f"{mode:6s} UCT({sims}) as X vs random: {r} in {dt:.1f}s")
        assert r.score > 0.85


def bench_search(n=4096, sims=32):
    for mode in ("puct", "gumbel"):
        g = BatchUTTT(n, DEV)
        mcts = BatchedMCTS(UniformEvaluator(DEV), n, MCTSConfig(n_sims=sims, mode=mode), DEV)
        for _ in range(5):
            m = g.legal_mask().float() + 1e-9
            g.step(torch.multinomial(m, 1).squeeze(1))
        torch.cuda.synchronize()
        t = time.perf_counter()
        mcts.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=True)
        torch.cuda.synchronize()
        dt = time.perf_counter() - t
        print(f"{mode:6s} search: {n} trees x {sims} sims in {dt:.2f}s -> {dt / sims * 1000:.1f} ms/sim (uniform evaluator)")


if __name__ == "__main__":
    test_schedule()
    test_tactics()
    test_search_beats_random()
    bench_search()
    print("ok")
