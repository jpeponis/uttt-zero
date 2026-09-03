"""Concept labels (uttt.concepts) agree with a brute-force reading of the reference engine on random positions."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.concepts import CONCEPTS, concept_labels  # noqa: E402
from uttt.game import FULL, LINES, UTTT, line_winner  # noqa: E402


def random_positions(n, rng):
    rows = []
    while len(rows) < n:
        g = UTTT()
        stop = int(rng.integers(0, 60))
        for _ in range(stop):
            if g.done:
                break
            g.play(int(rng.choice(g.legal_moves())))
        if not g.done:
            rows.append(g)
    return rows


def brute(g: UTTT) -> dict:
    p = g.player
    d = {}
    legal = g.legal_moves()
    d["free_move"] = int(g.next_board < 0 or g.macro[g.next_board] != 0)
    d["target_board"] = 9 if d["free_move"] else int(g.next_board)
    d["open_count"] = float((g.macro == 0).sum())
    d["empties"] = float(sum(1 for m in range(81) if g.cells[m] == 0 and g.macro[m // 9] == 0))
    d["count_margin"] = float((g.macro == p).sum() - (g.macro == -p).sum())
    lw, mw = 0, 0
    for m in legal:
        h = g.clone()
        h.play(m)
        if h.macro[m // 9] == p:
            lw = 1
            if h.done and h.winner == p and h.end_reason == "line":
                mw = 1
    d["local_win_now"], d["macro_win_now"] = lw, mw
    lt = 0
    for bd in range(9):
        if g.macro[bd] != 0:
            continue
        cells = g.cells[9 * bd : 9 * bd + 9]
        for a, b, c in LINES:
            v = [cells[a], cells[b], cells[c]]
            if v.count(-p) == 2 and v.count(0) == 1:
                lt = 1
    d["local_threat_against"] = lt
    dead = []
    for bd in range(9):
        cells = g.cells[9 * bd : 9 * bd + 9]
        ok = g.macro[bd] == 0
        winnable = any(all(cells[i] != -s for i in ln) for s in (1, -1) for ln in LINES)
        dead.append(int(ok and not winnable))
    d["dead_count"] = float(sum(dead))
    for bd in range(9):
        d[f"dead_{bd}"] = dead[bd]
        d[f"status_{bd}"] = 1 if g.macro[bd] == p else 2 if g.macro[bd] == -p else 3 if g.macro[bd] == FULL else 0
    for who, key in ((p, "threats_for"), (-p, "threats_against")):
        t = 0
        for a, b, c in LINES:
            v = [g.macro[a], g.macro[b], g.macro[c]]
            if v.count(who) == 2 and v.count(0) == 1:
                t += 1
        d[key] = float(t)
    return d


def test_labels(n=400, seed=0):
    rng = np.random.default_rng(seed)
    gs = random_positions(n, rng)
    cells = np.stack([g.cells for g in gs])
    macro = np.stack([g.macro for g in gs])
    nb = np.array([g.next_board for g in gs], dtype=np.int8)
    pl = np.array([g.player for g in gs], dtype=np.int8)
    lab = concept_labels(cells, macro, nb, pl)
    assert set(lab) == set(CONCEPTS), set(lab) ^ set(CONCEPTS)
    for name, (kind, _) in CONCEPTS.items():
        assert lab[name].shape == (n,), name
        if kind.startswith("class:"):
            assert lab[name].min() >= 0 and lab[name].max() < int(kind[6:]), name
    hits = {k: 0 for k in lab}
    for i, g in enumerate(gs):
        ref = brute(g)
        for k, v in ref.items():
            assert lab[k][i] == v, (k, i, lab[k][i], v, str(g))
        for k in lab:
            hits[k] += int(lab[k][i] != 0)
    rare = [k for k, h in hits.items() if h == 0]
    print(f"labels agree with brute force on {n} positions; never-positive labels: {rare or 'none'}")


if __name__ == "__main__":
    test_labels()
