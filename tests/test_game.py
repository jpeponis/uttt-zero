import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.game import FULL, UTTT  # noqa: E402


def test_invariants():
    rng = np.random.default_rng(0)
    lengths, outcomes, reasons = [], [], []
    for _ in range(2000):
        g = UTTT()
        while not g.done:
            m = g.legal_mask()
            n = int(m.sum())
            assert 1 <= n <= 81
            if g.next_board >= 0:
                assert n <= 9
                assert all(mv // 9 == g.next_board for mv in np.flatnonzero(m))
            # never legal in a closed board
            assert not np.any(m & np.repeat(g.macro != 0, 9))
            g.play(int(rng.choice(np.flatnonzero(m))))
        assert g.move_count <= 81
        if g.end_reason == "line":
            assert g.winner != 0
        else:
            assert np.all(g.macro != 0)
        lengths.append(g.move_count)
        outcomes.append(g.winner)
        reasons.append(g.end_reason)
    print(
        "random play: mean length %.1f, X/O/draw = %d/%d/%d, end by line/count/draw = %d/%d/%d"
        % (
            np.mean(lengths),
            outcomes.count(1),
            outcomes.count(-1),
            outcomes.count(0),
            reasons.count("line"),
            reasons.count("count"),
            reasons.count("draw"),
        )
    )


def test_free_move_after_closed_board():
    g = UTTT()
    g.play(9 * 4 + 0)  # X in board 4 cell 0 -> O to board 0
    assert g.next_board == 0 and g.player == -1
    g.play(9 * 0 + 4)  # O -> X to board 4
    assert g.next_board == 4
    g.play(9 * 4 + 1)  # X -> O to board 1
    g.play(9 * 1 + 4)  # O -> X to board 4
    g.play(9 * 4 + 2)  # X wins board 4 (cells 0,1,2); O sent to board 2
    assert g.macro[4] == 1
    assert g.next_board == 2
    g.play(9 * 2 + 4)  # O -> X to board 4, which is closed -> free move
    assert g.next_board == -1
    m = g.legal_mask()
    assert not m[9 * 4 : 9 * 4 + 9].any()
    assert m.sum() == 81 - 9 - 3  # eight open boards minus O's three stones


def test_count_tiebreak():
    # Synthetic terminal macro state: no macro line, board 8 about to close as full.
    g = UTTT()
    g.macro[:] = [1, -1, FULL, -1, 1, FULL, FULL, 1, 0]
    g.cells[:] = 1
    g.cells[9 * 8 : 9 * 8 + 9] = [1, -1, 1, 1, -1, -1, -1, 1, 0]  # no line for either yet
    g.next_board = -1
    g.player = -1
    g.play(80)  # O fills board 8: cells 80 (idx 8) with O -> (2,5,8) = 1,-1,-1 no; (6,7,8) = -1,1,-1 no; (0,4,8) = 1,-1,-1 no
    assert g.done and g.macro[8] == FULL
    assert g.winner == 1 and g.end_reason == "count"  # X 3 boards vs O 2


def test_count_draw():
    g = UTTT()
    g.macro[:] = [1, -1, FULL, -1, 1, FULL, FULL, 0, FULL]  # X: 0,4 (2)  O: 1,3 (2)
    g.cells[:] = 1
    g.cells[9 * 7 : 9 * 7 + 9] = [1, -1, 1, 1, -1, -1, -1, 1, 0]
    g.next_board = -1
    g.player = -1
    g.play(9 * 7 + 8)
    assert g.done and g.winner == 0 and g.end_reason == "draw"


if __name__ == "__main__":
    test_invariants()
    test_free_move_after_closed_board()
    test_count_tiebreak()
    test_count_draw()
    print("ok")
