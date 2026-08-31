import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import SYM_CELL, BatchUTTT, apply_symmetry, encode, legal_mask  # noqa: E402
from uttt.game import UTTT  # noqa: E402


def test_batch_matches_reference(n=512, device="cpu", seed=1):
    rng = np.random.default_rng(seed)
    batch = BatchUTTT(n, device)
    refs = [UTTT() for _ in range(n)]
    step = 0
    while not bool(batch.done.all()):
        bm = batch.legal_mask().cpu().numpy()
        moves = np.zeros(n, dtype=np.int64)
        for i, g in enumerate(refs):
            rm = g.legal_mask()
            assert np.array_equal(bm[i], rm), f"legal mask mismatch game {i} step {step}"
            if not g.done:
                mv = int(rng.choice(np.flatnonzero(rm)))
                moves[i] = mv
                g.play(mv)
        batch.step(torch.from_numpy(moves).to(device))
        for i, g in enumerate(refs):
            assert bool(batch.done[i]) == g.done
            if g.done:
                assert int(batch.winner[i]) == g.winner, f"winner mismatch game {i}"
                reason = {"line": 1, "count": 2, "draw": 3}[g.end_reason]
                assert int(batch.end_reason[i]) == reason
            assert int(batch.next_board[i]) == g.next_board
            assert int(batch.player[i]) == g.player
            assert np.array_equal(batch.cells[i].cpu().numpy(), g.cells)
            assert np.array_equal(batch.macro[i].cpu().numpy(), g.macro)
        step += 1
    print(f"batch engine matches reference on {n} random games ({step} steps)")


def test_symmetries_preserve_game(n=256, seed=2):
    """Playing the transformed move sequence must give the transformed final state and same result."""
    rng = np.random.default_rng(seed)
    # generate random games on the reference engine
    seqs = []
    for _ in range(n):
        g, seq = UTTT(), []
        while not g.done:
            mv = int(rng.choice(g.legal_moves()))
            seq.append(mv)
            g.play(mv)
        seqs.append((seq, g))
    for s in range(8):
        perm = SYM_CELL[s].numpy()
        for seq, g in seqs:
            h = UTTT()
            for mv in seq:
                h.play(int(perm[mv]))  # raises if illegal -> symmetry broken
            assert h.done and h.winner == g.winner and h.end_reason == g.end_reason
            cells = torch.from_numpy(g.cells).unsqueeze(0)
            macro = torch.from_numpy(g.macro).unsqueeze(0)
            nb = torch.tensor([g.next_board], dtype=torch.int8)
            c2, m2, nb2 = apply_symmetry(s, cells, macro, nb)
            assert np.array_equal(c2[0].numpy(), h.cells)
            assert np.array_equal(m2[0].numpy(), h.macro)
            assert int(nb2[0]) == h.next_board
    print("all 8 symmetries preserve legality, outcome and state mapping")


def test_encode_shapes():
    b = BatchUTTT(4)
    obs = b.observation()
    assert obs.shape == (4, 7, 9, 9)
    assert obs[:, 5].sum() == 4 * 81  # all legal at start
    b.step(torch.tensor([40, 40, 40, 40]))  # centre of centre
    obs = b.observation()
    assert obs[:, 1].sum() == 4 and obs[:, 0].sum() == 0  # from O's perspective X's stone is 'opponent'
    assert obs[:, 5].sum() == 4 * 8  # sent to centre board, 8 empties
    assert bool(obs[0, 1, 4, 4] == 1)


def bench(device, n=4096, iters=60):
    b = BatchUTTT(n, device)
    torch.manual_seed(0)
    if device != "cpu":
        torch.cuda.synchronize()
    t = time.perf_counter()
    for _ in range(iters):
        m = b.legal_mask()
        probs = m.float() + 1e-9
        moves = torch.multinomial(probs, 1).squeeze(1)
        b.step(moves)
        b.observation()
        b.reset_where(b.done)
    if device != "cpu":
        torch.cuda.synchronize()
    dt = time.perf_counter() - t
    print(f"{device}: {n} games x {iters} steps in {dt:.2f}s -> {n * iters / dt / 1e6:.2f} M steps/s (legal+step+encode)")


if __name__ == "__main__":
    test_encode_shapes()
    test_batch_matches_reference()
    test_symmetries_preserve_game()
    bench("cpu")
    if torch.cuda.is_available():
        test_batch_matches_reference(n=256, device="cuda:0", seed=3)
        bench("cuda:0")
        bench("cuda:0", n=32768, iters=60)
    print("ok")
