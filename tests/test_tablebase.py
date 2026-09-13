"""K=1 tablebase (uttt.tablebase) agrees with the exact solver on random one-open-board positions, and the
evaluator wrapper overrides value and policy only there.

Both are checked under BOTH terminal rules (PLAN7 §7e M2 row 18). The table itself is rule-free — the rule
enters only through K1Table.payoffs's outcome map — so the pair of runs is the test of that map: the same
positions, solved by the same solver under each rule, and the payoffs must follow."""
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.model import UniformEvaluator  # noqa: E402
from uttt.rules import RULES  # noqa: E402
from uttt.solver import solve, solve_children  # noqa: E402
from uttt.tablebase import K1Table, TablebaseEvaluator  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def random_k1(rng, n, rule="count"):
    out = []
    while len(out) < n:
        g = UTTT(rule)
        while not g.done and (g.macro == 0).sum() > 1:
            g.play(int(rng.choice(g.legal_moves())))
        if not g.done and (g.macro == 0).sum() == 1:
            out.append(g)
    return out


def test_table(n=300, seed=0):
    t = time.perf_counter()
    tables = {r: K1Table(DEV, r) for r in RULES}
    print(f"tables built in {time.perf_counter() - t:.1f}s: V {tables['count'].V.shape} "
          f"{tables['count'].V.nbytes / 1e6:.1f} MB (the table is shared; only payoffs() reads the rule)")
    values = {}
    for rule in RULES:
        t0 = time.perf_counter()
        tb = tables[rule]
        rng = np.random.default_rng(seed)
        gs = random_k1(rng, n, rule)  # the walk down is rule-free: the same n positions under both rules
        cells = torch.tensor(np.stack([g.cells for g in gs]), device=DEV)
        macro = torch.tensor(np.stack([g.macro for g in gs]), device=DEV)
        player = torch.tensor([g.player for g in gs], dtype=torch.int8, device=DEV)
        v, move, k1 = tb.lookup(cells, macro, player)
        assert bool(k1.all())
        v, move = v.cpu().numpy(), move.cpu().numpy()
        for i, g in enumerate(gs):
            ex, ch = solve_children((g.cells, g.macro, g.next_board, g.player), rule)
            assert v[i] == ex, (rule, i, v[i], ex, str(g))
            assert g.legal_mask()[move[i]] and ch[move[i]] == ex, (rule, i, move[i], ch[move[i]], ex)
        values[rule] = v
        print(f"  {rule:5s}: values and optimal moves agree with the solver on {n} one-open-board positions "
              f"(W/D/L for the mover {np.mean(v == 1):.2f}/{np.mean(v == 0):.2f}/{np.mean(v == -1):.2f})"
              f"  [{time.perf_counter() - t0:.0f}s]")
    differs = int((values["count"] != values["draw"]).sum())
    assert differs > 0, "the two rules gave the same value on every position: the payoff map is not being read"
    print(f"{differs} of the {n} positions have a different exact value under the two rules")


def test_evaluator(seed=1, rule="count"):
    tb = K1Table(DEV, rule)
    ev = TablebaseEvaluator(UniformEvaluator(DEV), tb, rule)
    rng = np.random.default_rng(seed)
    gs = random_k1(rng, 8, rule)
    g = BatchUTTT(16, DEV, rule)  # 8 K=1 positions + 8 fresh boards
    for i, h in enumerate(gs):
        g.cells[i] = torch.tensor(h.cells, device=DEV)
        g.macro[i] = torch.tensor(h.macro, device=DEV)
        g.next_board[i] = h.next_board
        g.player[i] = h.player
    probs, value = ev(g.cells, g.macro, g.next_board, g.player, g.done)
    assert ev.k1_hits == 8 and ev.calls == 16
    assert torch.all(value[8:] == 0) and torch.allclose(probs[8:].sum(1), torch.ones(8, device=DEV))
    for i, h in enumerate(gs):
        assert float(value[i]) == solve(h.cells, h.macro, h.next_board, h.player, rule)[0]
        m = int(probs[i].argmax())
        assert float(probs[i, m]) == 1.0 and h.legal_mask()[m]
    print(f"  {rule:5s}: evaluator wrapper overrides exactly the K=1 rows")


def test_table_evaluator_rule_mismatch():
    tb = K1Table(DEV, "count")
    try:
        TablebaseEvaluator(UniformEvaluator(DEV), tb, "draw")
    except ValueError:
        print("a draw-rule evaluator refuses a count-rule table")
        return
    raise AssertionError("a count-rule table was wrapped in a draw-rule evaluator")


if __name__ == "__main__":
    test_table()
    for _r in RULES:
        test_evaluator(rule=_r)
    test_table_evaluator_rule_mismatch()
    print("ok")
