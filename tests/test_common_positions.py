"""The two K1 reading instruments that do their own inference: tools/common_positions.py's paired
regression (PLAN7 §5 items 2 and 3) and tools/paired_contrast.py's joint pair bootstrap (§5 item 4).

    .venv/Scripts/python.exe tests/test_common_positions.py

Neither tool can be checked against K1's outputs -- they are frozen before the run exists (§7e M2-R R9) --
so what is checked here is that each estimator recovers a quantity that was put in by hand:

1. design.        The design matrix is freemove.py's, column for column, on real positions from random play:
                  the free-move indicator, the count margin and the empty count are recomputed independently.
2. paired Delta.  Two synthetic responses differing by a known Delta on a known set of regressors, with a
                  large game-level random effect in BOTH: the paired regression recovers Delta, its 95 %
                  interval covers it, and the game effect -- which would swamp an unpaired comparison --
                  cancels. The three verdicts of §5 item 2 fall out of the one fit, one each.
3. verdicts.      The decision rules on hand-made intervals, including the boundaries.
4. degeneracy.    An identically zero paired difference (the raw value head, which never sees the rule) is
                  reported as vacuous, not as "invariant".
5. contrast.      1 - s_D - s_C on a hand-made pair of match records, and the proof that the bootstrap is
                  JOINT: with the draw file's per-opening scores set to 1 - the count file's, the contrast is
                  identically zero for every resample, so a joint bootstrap gives a zero-width interval while
                  two independent ones could not.
"""
import json
import os
import sys
import tempfile
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from common_positions import (NAMES, design, features, fit, paired_verdicts,  # noqa: E402
                              verdict_band, verdict_decrease, verdict_equivalence)
from paired_contrast import check_pair, joint_bootstrap, load_match, verdict  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.solver import empties_in_open_boards  # noqa: E402


def random_positions(n_games: int, seed: int = 0) -> list:
    """Rows in tools/freemove.py's sample_positions format, from random legal play."""
    rng = np.random.default_rng(seed)
    rows = []
    for g_id in range(n_games):
        g = UTTT()
        t = 0
        while not g.done:
            moves = g.legal_moves()
            g.play(int(moves[rng.integers(len(moves))]))
            t += 1
            if 6 <= t <= 60 and not g.done and rng.random() < 0.25:
                rows.append((g_id, t, g.cells.copy(), g.macro.copy(), g.next_board, g.player))
    return rows


def test_design_is_freemoves_design():
    rows = random_positions(220, seed=3)
    F = features(rows, gid_offset=0)
    X, Xo, parts = design(F)
    N = len(rows)
    assert X.shape == (N, len(NAMES)), X.shape
    assert np.all(X[:, 0] == 1.0)
    assert np.array_equal(X[:, NAMES.index("free_move")], (F["next_board"] < 0).astype(float))
    for i in (0, N // 3, N // 2, N - 1):  # the count margin and the empty count, recomputed by hand
        macro, p = F["macro"][i], int(F["player"][i])
        want = int((macro == p).sum() - (macro == -p).sum())
        assert X[i, NAMES.index("macro_score")] == want, (i, X[i, NAMES.index("macro_score")], want)
        assert 10 * X[i, NAMES.index("empties/10")] == empties_in_open_boards(F["cells"][i], F["macro"][i])
    assert Xo.shape[0] == N and np.linalg.matrix_rank(X) == X.shape[1], "the design must not be singular"
    print(f"design: {N} positions from {len(np.unique(F['gid']))} random games, {X.shape[1]} columns, full rank; "
          f"free move {X[:, 1].mean():.3f}; the count margin and the empty count agree with a hand computation")


def test_paired_regression_recovers_a_known_delta():
    rows = random_positions(600, seed=1)
    F = features(rows, gid_offset=0)
    X, _, _ = design(F)
    gid, N = F["gid"], len(rows)
    rng = np.random.default_rng(7)
    beta = rng.normal(scale=0.2, size=X.shape[1])
    delta = np.zeros(X.shape[1])
    delta[NAMES.index("macro_score")] = -0.020   # claim 16: an established decrease
    delta[NAMES.index("free_move")] = +0.050     # claim  8: dependent
    delta[NAMES.index("threats_against")] = +0.010  # claim 13: invariant
    game_effect = rng.normal(scale=1.0, size=gid.max() + 1)[gid]  # in BOTH responses: pairing must cancel it
    y_count = X @ beta + game_effect + rng.normal(scale=0.01, size=N)
    y_draw = X @ (beta + delta) + game_effect + rng.normal(scale=0.01, size=N)
    rec = fit(X, y_draw - y_count, gid, NAMES)
    v = paired_verdicts(rec)
    for name in ("macro_score", "free_move", "threats_for", "threats_against"):
        got, (lo, hi) = rec["coef"][name], rec["interval"][name]
        want = delta[NAMES.index(name)]
        assert abs(got - want) < 0.01, f"{name}: recovered {got:+.4f}, put in {want:+.4f}"
        assert lo <= want <= hi, f"{name}: the 95 % interval [{lo:+.4f}, {hi:+.4f}] misses {want:+.4f}"
        print(f"  {name:16s} put in {want:+.4f}  recovered {got:+.4f}  95 % [{lo:+.4f}, {hi:+.4f}]  "
              f"{v[name]['verdict']}")
    assert v["macro_score"]["verdict"] == "established decrease", v["macro_score"]
    assert v["free_move"]["verdict"] == "dependent", v["free_move"]
    assert v["threats_against"]["verdict"] == "invariant", v["threats_against"]
    # the game effect is ~5x every coefficient and cancels exactly: an unpaired difference of means would not
    unpaired = float(y_draw.mean() - y_count.mean())
    print(f"  the game-level random effect (sd 1.0, in both responses) cancels: the paired intercept is "
          f"{rec['coef']['intercept']:+.4f} and the raw difference of means {unpaired:+.4f}")


def test_an_identically_zero_difference_is_vacuous_not_invariant():
    rows = random_positions(120, seed=5)
    F = features(rows, gid_offset=0)
    X, _, _ = design(F)
    y = np.random.default_rng(0).normal(size=len(rows))
    rec = fit(X, y - y, F["gid"], NAMES)  # what the raw value head gives: it never sees the rule
    assert rec["degenerate"] is True
    for name, d in paired_verdicts(rec).items():
        assert d["verdict"].startswith("vacuous"), (name, d)
        assert d["interval"] == [0.0, 0.0], (name, d)
    print("an identically zero paired difference is reported as vacuous, not as an invariance finding")


def test_verdict_rules():
    # claims 8 / 13: inside (-0.03, +0.03) invariant, wholly beyond dependent, else unresolved
    assert verdict_equivalence(-0.010, +0.020) == "invariant"
    assert verdict_equivalence(-0.029, +0.029) == "invariant"
    assert verdict_equivalence(+0.031, +0.050) == "dependent"
    assert verdict_equivalence(-0.090, -0.031) == "dependent"
    assert verdict_equivalence(-0.031, +0.010) == "unresolved"   # straddles a bound
    assert verdict_equivalence(-0.030, +0.010) == "unresolved"   # touching is not inside
    assert verdict_equivalence(+0.030, +0.060) == "dependent"    # touching from outside is beyond
    assert verdict_equivalence(-0.500, +0.500) == "unresolved"   # no precision
    # claim 16, primary: an established decrease needs the upper endpoint <= -0.005
    assert verdict_decrease(-0.040, -0.006) == "established decrease"
    assert verdict_decrease(-0.040, -0.005) == "established decrease"
    assert verdict_decrease(-0.004, +0.030) == "contradicted"
    assert verdict_decrease(-0.020, +0.002) == "unresolved"
    assert verdict_decrease(-0.005, +0.001) == "unresolved"
    # claim 16, secondary: the net's own coefficient against [-0.015, +0.015]
    assert verdict_band(-0.010, +0.012) == "supported"
    assert verdict_band(+0.020, +0.040) == "contradicted"
    assert verdict_band(-0.010, +0.030) == "unresolved"
    print("the three verdict rules of §5 item 2 behave at their boundaries")


def _match_file(path, rule, pairs, ids=None, suite=None, a="netA.pt", b="netB.pt"):
    """A minimal tools/openings.py match JSON: per-opening records whose mean is summary.overall.score."""
    ids = list(range(len(pairs))) if ids is None else ids
    openings = []
    for i, p in zip(ids, pairs):  # split a pair score into the two colour scores it averages
        ax = min(1.0, 2 * p) if p <= 0.5 else 1.0
        ao = 2 * p - ax
        openings.append({"id": int(i), "suite": "empty", "moves": [], "a_as_x": float(ax), "a_as_o": float(ao)})
    rec = {"rule": rule, "a": a, "b": b, "a_sims": 64, "b_sims": 64,
           "suite": suite or {"name": "openings_v1", "corpus": "runs/v2a", "corpus_games": 1, "plies": 4,
                              "seed": 0, "built": "2026-01-01 00:00"},
           "summary": {"overall": {"score": float(np.mean(pairs)), "ci": [0.0, 1.0], "draws": 0.2,
                                   "end_count": 0.1, "end_equal": 0.2}},
           "openings": openings}
    with open(path, "w") as f:
        json.dump(rec, f)
    return path


def test_contrast_and_the_joint_bootstrap():
    rng = np.random.default_rng(11)
    pc = rng.choice([0.0, 0.5, 1.0], size=400, p=[0.3, 0.2, 0.5])
    pd_free = rng.choice([0.0, 0.5, 1.0], size=400, p=[0.4, 0.2, 0.4])
    with tempfile.TemporaryDirectory() as td:
        fc = _match_file(os.path.join(td, "c.json"), "count", pc)
        fd = _match_file(os.path.join(td, "d.json"), "draw", pd_free)
        c, d = load_match(fc), load_match(fd)
        assert check_pair(c, d) == [], "a well-formed count / draw pair should raise no note"
        b = joint_bootstrap(c["pair"], d["pair"], 2000, 0)
        want = 1.0 - float(pd_free.mean()) - float(pc.mean())
        got = 1.0 - d["score"] - c["score"]
        assert abs(got - want) < 1e-12, (got, want)
        assert b["contrast"][0] < want < b["contrast"][1], (b["contrast"], want)
        print(f"contrast: s_C {c['score']:.4f}, s_D {d['score']:.4f}, 1 - s_D - s_C = {got:+.4f} "
              f"(put in {want:+.4f}), 95 % [{b['contrast'][0]:+.4f}, {b['contrast'][1]:+.4f}], "
              f"verdict {verdict(*b['contrast'])}")

        # the joint half: make the draw file's per-opening scores 1 - the count file's. Then
        # 1 - s_D - s_C = 1 - (1 - s_C) - s_C = 0 for EVERY resample -- but only if both scores are
        # recomputed from the SAME resampled openings. Two independent bootstraps could not give a
        # zero-width interval here, because each marginal is wide.
        fd2 = _match_file(os.path.join(td, "d2.json"), "draw", 1.0 - pc)
        d2 = load_match(fd2)
        b2 = joint_bootstrap(c["pair"], d2["pair"], 2000, 0)
        assert abs(b2["contrast"][0]) < 1e-12 and abs(b2["contrast"][1]) < 1e-12, b2["contrast"]
        width = b2["s_count"][1] - b2["s_count"][0]
        assert width > 0.02, width
        print(f"joint bootstrap: with s_D's openings set to 1 - s_C's, the contrast interval is "
              f"[{b2['contrast'][0]:+.1e}, {b2['contrast'][1]:+.1e}] while each score's own interval is "
              f"{100 * width:.1f} points wide -- the same resample was used for both")

        # the +- 3 point rule, and the guards
        assert verdict(+0.031, +0.090) == "positive"
        assert verdict(-0.200, -0.031) == "negative"
        assert verdict(+0.010, +0.090) == "unresolved"
        assert verdict(-0.010, +0.010) == "unresolved"
        same = load_match(_match_file(os.path.join(td, "c2.json"), "count", pc))
        notes = check_pair(c, same)
        assert notes and "BOTH FILES WERE PLAYED UNDER RULE" in notes[0], notes
        other = load_match(_match_file(os.path.join(td, "e.json"), "draw", pc,
                                       suite={"name": "openings_v2", "corpus": "runs/v2a", "corpus_games": 1,
                                              "plies": 4, "seed": 0, "built": "2026-01-01 00:00"}))
        try:
            check_pair(c, other)
            raise AssertionError("two different suites must be refused")
        except SystemExit as e:
            assert "different suites" in str(e), e
        print("a shared rule is flagged, a different suite is refused, and the +- 3 point rule reads as "
              "positive / negative / unresolved")


if __name__ == "__main__":
    t0 = time.perf_counter()
    test_design_is_freemoves_design()
    test_paired_regression_recovers_a_known_delta()
    test_an_identically_zero_difference_is_vacuous_not_invariant()
    test_verdict_rules()
    test_contrast_and_the_joint_bootstrap()
    print(f"ok [{time.perf_counter() - t0:.1f}s]")
