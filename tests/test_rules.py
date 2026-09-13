"""The `rule` switch (PLAN7 §5 K1): "count" must be exactly what it always was, "draw" must be the
Wikipedia / uttt.ai / SaltZero / OpenSpiel variant, and the engines must agree on both.

    .venv/Scripts/python.exe tests/test_rules.py

1. Regression. The batch engine reproduces tests/fixtures/count_engine_2000.npz — winners, end reasons,
   final macro and lengths of 2 000 seeded random games, recorded from the pre-K1 code — bit for bit
   under rule="count". Nothing below can pass by quietly changing what "count" means.
2. Cross-engine. Reference and batch engines agree over 100 000 random games under each rule: the legal mask
   of every live game before every move, and — after EVERY ply, for every row including the ones already
   finished — done, next_board, player and move_count; cells and macro every 8 plies and again at the end
   (M2 row 18: terminal agreement alone can miss a divergence that a later move erases, and a finished row
   whose state kept moving would be a real fault). The same seed gives the same moves under both rules — a
   game ends at the same ply either way — so the two runs differ only in the verdict.
3. Hand-made terminals. A 4-4 board count with one drawn board is a draw under both rules; a 5-3 count
   with no macro line is an X win under "count" and a draw under "draw"; a macro line wins under both,
   even when the line's owner is 2-5 down on boards.
4. Solver. Agreement with a brute-force negamax on 200 tiny positions (<= 8 empties) under both rules,
   and the same answers through a process pool (the path uttt.exact and every label builder take, which
   on Windows means the rule must survive a spawn).
"""
import os
import sys
import time
from functools import partial
from multiprocessing import Pool

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.game import FULL, UTTT  # noqa: E402
from uttt.rules import RULES, check_rule, tag_path  # noqa: E402
from uttt.solver import empties_in_open_boards, solve, solve_batch, solve_children  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "count_engine_2000.npz")
REASON = {"line": 1, "count": 2, "draw": 3}


def random_games(n, seed, device="cpu", rule="count"):
    """n random games in lock-step on the batch engine. The moves depend only on (n, seed): the legal
    mask and the number of steps are rule-independent, so both rules play exactly the same games."""
    rng = np.random.default_rng(seed)
    g = BatchUTTT(n, device, rule)
    while not bool(g.done.all()):
        legal = g.legal_mask().cpu().numpy()
        u = rng.random((n, 81))
        moves = np.where(legal, u, -1.0).argmax(1)
        g.step(torch.from_numpy(moves).to(device))
    return g


# ---- 1. regression against the pre-change engine --------------------------------------------------
def test_count_is_unchanged():
    z = np.load(FIXTURE)
    g = random_games(int(z["n"]), int(z["seed"]), rule="count")
    for k in ("winner", "end_reason", "macro", "move_count"):
        assert np.array_equal(getattr(g, k).cpu().numpy(), z[k]), f"{k} differs from the pre-K1 fixture"
    r = z["end_reason"]
    print(f"count rule reproduces {int(z['n'])} pre-K1 games bit for bit "
          f"(ended by line {int((r == 1).sum())}, count {int((r == 2).sum())}, draw {int((r == 3).sum())})")


def test_draw_relabels_exactly_the_count_endings():
    """The draw rule changes the verdict of every count-decided game and nothing else — the mechanical
    relabel tools/corpus_stats.py --rule draw performs, checked against a real re-run of the engine."""
    z = np.load(FIXTURE)
    g = random_games(int(z["n"]), int(z["seed"]), rule="draw")
    flip = z["end_reason"] == 2
    assert np.array_equal(g.macro.cpu().numpy(), z["macro"]), "the rule must not change the games themselves"
    assert np.array_equal(g.move_count.cpu().numpy(), z["move_count"])
    assert np.array_equal(g.end_reason.cpu().numpy(), np.where(flip, 3, z["end_reason"]))
    assert np.array_equal(g.winner.cpu().numpy(), np.where(flip, 0, z["winner"]))
    print(f"draw rule: {int(flip.sum())} of {len(flip)} games ({100 * flip.mean():.1f} %) turn from a count "
          f"decision into a draw; the other {int((~flip).sum())} are untouched")


# ---- 2. the two engines agree, under each rule ----------------------------------------------------
def compare_states(b, refs, rule, seed, ply, with_cells):
    """Every row of the batch engine against the reference games after one ply, FINISHED ROWS INCLUDED: a
    finished game whose state kept moving on one engine and not the other is a fault the end-of-game
    comparison cannot see (M2 row 18). cells and macro only on the sampled plies, to bound the cost."""
    n = len(refs)
    fields = [("done", b.done.cpu().numpy(), np.fromiter((g.done for g in refs), bool, n)),
              ("next_board", b.next_board.cpu().numpy(), np.fromiter((g.next_board for g in refs), np.int64, n)),
              ("player", b.player.cpu().numpy(), np.fromiter((g.player for g in refs), np.int64, n)),
              ("move_count", b.move_count.cpu().numpy(), np.fromiter((g.move_count for g in refs), np.int64, n))]
    if with_cells:
        fields += [("cells", b.cells.cpu().numpy(), np.stack([g.cells for g in refs])),
                   ("macro", b.macro.cpu().numpy(), np.stack([g.macro for g in refs]))]
    for name, got, want in fields:
        bad = np.flatnonzero((got != want).reshape(n, -1).any(1))
        assert bad.size == 0, (f"{name} mismatch ({rule}, seed {seed}, ply {ply}, {bad.size} games, first {int(bad[0])}: "
                               f"batch {got[int(bad[0])]} vs reference {want[int(bad[0])]})\n{refs[int(bad[0])]}")


def cross_check(rule, games, seeds, device="cpu", state_every=8):
    """games x seeds random games: batch engine against the reference engine, move by move."""
    t0 = time.perf_counter()
    counts = {1: 0, 2: 0, 3: 0}
    for seed in range(seeds):
        rng = np.random.default_rng(1000 + seed)
        b = BatchUTTT(games, device, rule)
        refs = [UTTT(rule) for _ in range(games)]
        ply = 0
        while not bool(b.done.all()):
            legal = b.legal_mask().cpu().numpy()
            done_b = b.done.cpu().numpy()
            assert not legal[done_b].any(), f"the batch engine offers legal moves in a finished game ({rule}, seed {seed}, ply {ply})"
            u = rng.random((games, 81))
            moves = np.where(legal, u, -1.0).argmax(1)
            for i, g in enumerate(refs):
                if not g.done:
                    assert np.array_equal(legal[i], g.legal_mask()), f"legal mask mismatch ({rule}, seed {seed}, game {i})"
                    g.play(int(moves[i]))
            b.step(torch.from_numpy(moves).to(device))
            ply += 1
            finished = bool(b.done.all())
            compare_states(b, refs, rule, seed, ply, with_cells=finished or ply % state_every == 0)
        win, reason, macro = b.winner.cpu().numpy(), b.end_reason.cpu().numpy(), b.macro.cpu().numpy()
        for i, g in enumerate(refs):
            assert g.done and bool(b.done[i])
            assert win[i] == g.winner, f"winner mismatch ({rule}, seed {seed}, game {i})\n{g}"
            assert reason[i] == REASON[g.end_reason], f"end reason mismatch ({rule}, seed {seed}, game {i})\n{g}"
            assert np.array_equal(macro[i], g.macro)
            counts[int(reason[i])] += 1
    assert (counts[2] == 0) == (rule == "draw"), f"rule {rule} produced {counts[2]} count endings"
    print(f"  {rule:5s}: {games * seeds} random games, both engines agree on the legal mask and, after every ply, on "
          f"done / next_board / player / move_count (cells and macro every {state_every} plies and at the end), plus "
          f"winner and end reason (line {counts[1]}, count {counts[2]}, draw {counts[3]})  [{time.perf_counter() - t0:.0f}s]")
    return counts


def test_engines_agree_under_both_rules(games=500, seeds=200):
    print(f"cross-engine check, {games * seeds} games per rule:")
    for rule in RULES:
        cross_check(rule, games, seeds)


# ---- 3. hand-made terminal positions --------------------------------------------------------------
NO_LINE_FILL = [1, -1, 1, 1, -1, -1, -1, 1, 0]  # + O on cell 8: the board fills with no local winner


def _close_last_board(macro, board, cells9, mover, cell, rule):
    """A position whose next move closes `board`; play it and return the finished game."""
    g = UTTT(rule)
    g.macro[:] = macro
    g.cells[:] = 1  # the other boards are closed: their contents can no longer matter
    g.cells[9 * board : 9 * board + 9] = cells9
    g.next_board, g.player = -1, mover
    g.play(9 * board + cell)
    assert g.done, "the hand-made position did not finish"
    return g


def test_four_four_is_a_draw_under_both_rules():
    # X owns 0, 1, 5, 6; O owns 2, 3, 4, 8; board 7 fills without a winner. Neither side has a macro line.
    macro = [1, 1, -1, -1, -1, 1, 1, 0, -1]
    for rule in RULES:
        g = _close_last_board(macro, 7, NO_LINE_FILL, -1, 8, rule)
        assert int((g.macro == 1).sum()) == 4 and int((g.macro == -1).sum()) == 4
        assert (g.winner, g.end_reason) == (0, "draw"), (rule, g.winner, g.end_reason, str(g))
    print("4-4 with one drawn board: a draw under both rules")


def test_five_three_splits_on_the_rule():
    # X owns 1, 2, 3, 5, 6; O owns 0, 4, 7; board 8 fills without a winner. Neither side has a macro line.
    macro = [-1, 1, 1, 1, -1, 1, 1, -1, 0]
    g = _close_last_board(macro, 8, NO_LINE_FILL, -1, 8, "count")
    assert int((g.macro == 1).sum()) == 5 and int((g.macro == -1).sum()) == 3
    assert (g.winner, g.end_reason) == (1, "count"), (g.winner, g.end_reason, str(g))
    g = _close_last_board(macro, 8, NO_LINE_FILL, -1, 8, "draw")
    assert (g.winner, g.end_reason) == (0, "draw"), (g.winner, g.end_reason, str(g))
    print("5-3 with no macro line: an X count win under 'count', a draw under 'draw'")


def test_macro_line_wins_under_both_rules():
    # O leads 5-2 on boards; X wins board 8 and with it the macro line 0-4-8. The line must still win.
    macro = [1, -1, -1, -1, 1, -1, FULL, -1, 0]
    for rule in RULES:
        g = _close_last_board(macro, 8, [1, 0, 0, 0, 1, 0, 0, 0, 0], 1, 8, rule)
        assert g.macro[8] == 1
        assert int((g.macro == -1).sum()) == 5 and int((g.macro == 1).sum()) == 3
        assert (g.winner, g.end_reason) == (1, "line"), (rule, g.winner, g.end_reason, str(g))
    print("a macro line wins under both rules, 2-5 down on boards before the move")


# ---- 4. solver against brute force ----------------------------------------------------------------
def brute_force(g: UTTT) -> int:
    """Plain negamax on the reference engine: the value for the side to move."""
    if g.done:
        return 0 if g.winner == 0 else (1 if g.winner == g.player else -1)
    best = -2
    for m in g.legal_moves():
        h = g.clone()
        h.play(m)
        v = -brute_force(h)
        if v > best:
            best = v
        if best == 1:
            break
    return best


def random_endgame(rng, max_empty, rule):
    """A live position with <= max_empty empties in open boards. The walk down is rule-free, so the
    same seed reaches the same positions under both rules and the values are directly comparable."""
    while True:
        g = UTTT(rule)
        while not g.done and empties_in_open_boards(g.cells, g.macro) > max_empty:
            g.play(int(rng.choice(g.legal_moves())))
        if not g.done:
            return g


def test_solver_against_brute_force(n=200, max_empty=8):
    for rule in RULES:
        rng = np.random.default_rng(7)
        t0 = time.perf_counter()
        differs = 0
        for _ in range(n):
            g = random_endgame(rng, max_empty, rule)
            v_ref = brute_force(g)
            v_sol, _ = solve(g.cells, g.macro, g.next_board, g.player, rule)
            assert v_ref == v_sol, (rule, v_ref, v_sol, str(g))
            v_other, _ = solve(g.cells, g.macro, g.next_board, g.player, "count" if rule == "draw" else "draw")
            differs += int(v_other != v_sol)
        print(f"  {rule:5s}: solver agrees with brute force on {n} positions (<= {max_empty} empties); "
              f"{differs} of them have a different value under the other rule  [{time.perf_counter() - t0:.0f}s]")


def test_solve_children_and_pool(n=64, max_empty=6, processes=4):
    """solve_children / solve_batch must give the solver's answer, and must carry the rule across the
    process boundary a pool puts between the caller and the worker (uttt.exact's path)."""
    for rule in RULES:
        rng = np.random.default_rng(23)
        games = [random_endgame(rng, max_empty, rule) for _ in range(n)]
        args = [(g.cells.copy(), g.macro.copy(), int(g.next_board), int(g.player)) for g in games]
        want = [solve(g.cells, g.macro, g.next_board, g.player, rule)[0] for g in games]
        for a, w in zip(args, want):
            assert solve_children(a, rule)[0] == w
        with Pool(processes) as pool:
            got = pool.map(partial(solve_children, rule=rule), args, chunksize=8)
        assert [v for v, _ in got] == want, f"pool workers lost the {rule} rule"
        cells = np.stack([a[0] for a in args])
        macro = np.stack([a[1] for a in args])
        nb = np.array([a[2] for a in args])
        pl = np.array([a[3] for a in args])
        vals, pol = solve_batch((cells, macro, nb, pl), rule)
        assert [int(v) for v in vals] == want
        assert np.allclose(pol.astype(np.float32).sum(1), 1.0, atol=2e-3)  # float16 targets over the optimal moves
        print(f"  {rule:5s}: solve_children / solve_batch match the solver on {n} positions, in process and in a pool")


# ---- 5. the plumbing itself -----------------------------------------------------------------------
def test_rule_validation_and_tags():
    for bad in ("Draw", "counts", "", None):
        try:
            check_rule(bad)
        except ValueError:
            continue
        raise AssertionError(f"check_rule accepted {bad!r}")
    assert tag_path("runs/x/probes.json", "count") == "runs/x/probes.json"
    assert tag_path("runs/x/probes.json", "draw") == "runs/x/probes_draw.json"
    assert UTTT("draw").clone().rule == "draw" and BatchUTTT(2, "cpu", "draw").clone().rule == "draw"
    print("rule validation rejects typos; 'count' never renames a file, 'draw' always does")


if __name__ == "__main__":
    for _r in RULES:  # JIT warm-up on a tiny case, once per rule specialisation
        solve(np.zeros(81, np.int8), np.array([1, 1, 2, -1, -1, 2, 2, 2, 0], np.int8), -1, 1, _r)
    test_rule_validation_and_tags()
    test_count_is_unchanged()
    test_draw_relabels_exactly_the_count_endings()
    test_four_four_is_a_draw_under_both_rules()
    test_five_three_splits_on_the_rule()
    test_macro_line_wins_under_both_rules()
    test_solver_against_brute_force()
    test_solve_children_and_pool()
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 200  # x 500 games = 100 000 per rule (~4.5 min each)
    test_engines_agree_under_both_rules(seeds=seeds)
    print("ok")
