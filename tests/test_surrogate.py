"""Surrogate features (uttt.surrogate) agree with uttt.concepts on random positions, and the per-move features
agree with replaying each move on the reference engine."""
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.concepts import concept_labels  # noqa: E402
from uttt.game import FULL, UTTT  # noqa: E402
from uttt.surrogate import MOVE_FEATURES, POSITION_FEATURES, SurrogateEvaluator, move_features, position_features  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def random_positions(n, rng):
    out = []
    while len(out) < n:
        g = UTTT()
        for _ in range(int(rng.integers(0, 60))):
            if g.done:
                break
            g.play(int(rng.choice(g.legal_moves())))
        if not g.done:
            out.append(g)
    return out


def tensors(gs):
    t = lambda a, dt: torch.tensor(np.asarray(a, dtype=dt), device=DEV)  # noqa: E731
    return (t(np.stack([g.cells for g in gs]), np.int8), t(np.stack([g.macro for g in gs]), np.int8),
            t([g.next_board for g in gs], np.int8), t([g.player for g in gs], np.int8))


def test_position_features(n=300, seed=0):
    gs = random_positions(n, np.random.default_rng(seed))
    cells, macro, nb, player = tensors(gs)
    G = position_features(cells, macro, nb, player).cpu().numpy()
    lab = concept_labels(cells.cpu().numpy(), macro.cpu().numpy(), nb.cpu().numpy(), player.cpu().numpy())
    pairs = {"free_move": "free_move", "count_margin": "count_margin", "open_boards": "open_count", "is_X": "side_to_move_x",
             "threats_for": "threats_for", "threats_against": "threats_against", "dead_boards": "dead_count",
             "local_win_now": "local_win_now", "local_threat_against": "local_threat_against", "macro_win_now": "macro_win_now",
             "full_boards": "boards_full"}
    for f, c in pairs.items():
        j = POSITION_FEATURES.index(f)
        assert np.allclose(G[:, j], lab[c]), (f, G[:5, j], lab[c][:5])
    assert np.allclose(G[:, POSITION_FEATURES.index("empties")] * 10, lab["empties"])
    print(f"position features agree with uttt.concepts on {n} positions")


def test_move_features(n=120, seed=1):
    gs = random_positions(n, np.random.default_rng(seed))
    cells, macro, nb, player = tensors(gs)
    F = move_features(cells, macro, nb, player).cpu().numpy()
    fi = {k: i for i, k in enumerate(MOVE_FEATURES)}
    checked = 0
    for i, g in enumerate(gs):
        legal = g.legal_mask()
        assert np.all(F[i][~legal] == 0)
        for m in np.flatnonzero(legal):
            h = g.clone()
            h.play(int(m))
            p = g.player
            assert F[i, m, fi["wins_board"]] == float(h.macro[m // 9] == p)
            assert F[i, m, fi["fills_board"]] == float(h.macro[m // 9] == FULL)
            assert F[i, m, fi["wins_game"]] == float(h.done and h.winner == p)
            assert F[i, m, fi["gives_free_move"]] == float((h.next_board < 0) and not h.done)
            assert F[i, m, fi["count_margin_after"]] == float((h.macro == p).sum() - (h.macro == -p).sum())
            assert F[i, m, fi["self_send"]] == float(m % 9 == m // 9)
            if not h.done:
                lab = concept_labels(h.cells[None], h.macro[None], np.array([h.next_board], np.int8), np.array([h.player], np.int8))
                assert F[i, m, fi["opp_local_win_next"]] == float(lab["local_win_now"][0])
                assert F[i, m, fi["opp_macro_win_next"]] == float(lab["macro_win_now"][0])
                assert F[i, m, fi["opp_threats_after"]] == float(lab["threats_for"][0])  # the opponent is now the mover
                assert F[i, m, fi["my_threats_after"]] == float(lab["threats_against"][0])
                assert F[i, m, fi["dead_boards_after"]] == float(lab["dead_count"][0])
            checked += 1
    print(f"move features agree with the engine on {checked} (position, move) pairs")


def test_evaluator(seed=2):
    gs = random_positions(16, np.random.default_rng(seed))
    cells, macro, nb, player = tensors(gs)
    ev = SurrogateEvaluator(np.zeros(len(MOVE_FEATURES)), np.zeros(len(POSITION_FEATURES)), 0.0, DEV)
    probs, value = ev(cells, macro, nb, player, torch.zeros(16, dtype=torch.bool, device=DEV))
    assert torch.allclose(probs.sum(1), torch.ones(16, device=DEV)) and torch.all(value == 0)
    for i, g in enumerate(gs):
        legal = torch.tensor(g.legal_mask(), device=DEV)
        assert torch.all(probs[i][~legal] == 0) and torch.allclose(probs[i][legal], probs[i][legal][0])
    print("zero-weight surrogate is uniform over legal moves with value 0")


if __name__ == "__main__":
    test_position_features()
    test_move_features()
    test_evaluator()
    print("ok")
