"""K=1 tablebase (uttt.tablebase) agrees with the exact solver on random one-open-board positions, and the
evaluator wrapper overrides value and policy only there."""
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.model import UniformEvaluator  # noqa: E402
from uttt.solver import solve, solve_children  # noqa: E402
from uttt.tablebase import K1Table, TablebaseEvaluator  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def random_k1(rng, n):
    out = []
    while len(out) < n:
        g = UTTT()
        while not g.done and (g.macro == 0).sum() > 1:
            g.play(int(rng.choice(g.legal_moves())))
        if not g.done and (g.macro == 0).sum() == 1:
            out.append(g)
    return out


def test_table(n=300, seed=0):
    t = time.perf_counter()
    tb = K1Table(DEV)
    print(f"table built in {time.perf_counter() - t:.1f}s: V {tb.V.shape} {tb.V.nbytes / 1e6:.1f} MB")
    rng = np.random.default_rng(seed)
    gs = random_k1(rng, n)
    cells = torch.tensor(np.stack([g.cells for g in gs]), device=DEV)
    macro = torch.tensor(np.stack([g.macro for g in gs]), device=DEV)
    player = torch.tensor([g.player for g in gs], dtype=torch.int8, device=DEV)
    v, move, k1 = tb.lookup(cells, macro, player)
    assert bool(k1.all())
    v, move = v.cpu().numpy(), move.cpu().numpy()
    for i, g in enumerate(gs):
        ex, ch = solve_children((g.cells, g.macro, g.next_board, g.player))
        assert v[i] == ex, (i, v[i], ex, str(g))
        assert g.legal_mask()[move[i]] and ch[move[i]] == ex, (i, move[i], ch[move[i]], ex)
    print(f"values and optimal moves agree with the solver on {n} one-open-board positions "
          f"(W/D/L for the mover {np.mean(v == 1):.2f}/{np.mean(v == 0):.2f}/{np.mean(v == -1):.2f})")


def test_evaluator(seed=1):
    tb = K1Table(DEV)
    ev = TablebaseEvaluator(UniformEvaluator(DEV), tb)
    rng = np.random.default_rng(seed)
    gs = random_k1(rng, 8)
    g = BatchUTTT(16, DEV)  # 8 K=1 positions + 8 fresh boards
    for i, h in enumerate(gs):
        g.cells[i] = torch.tensor(h.cells, device=DEV)
        g.macro[i] = torch.tensor(h.macro, device=DEV)
        g.next_board[i] = h.next_board
        g.player[i] = h.player
    probs, value = ev(g.cells, g.macro, g.next_board, g.player, g.done)
    assert ev.k1_hits == 8 and ev.calls == 16
    assert torch.all(value[8:] == 0) and torch.allclose(probs[8:].sum(1), torch.ones(8, device=DEV))
    for i, h in enumerate(gs):
        assert float(value[i]) == solve(h.cells, h.macro, h.next_board, h.player)[0]
        m = int(probs[i].argmax())
        assert float(probs[i, m]) == 1.0 and h.legal_mask()[m]
    print("evaluator wrapper overrides exactly the K=1 rows")


if __name__ == "__main__":
    test_table()
    test_evaluator()
    print("ok")
