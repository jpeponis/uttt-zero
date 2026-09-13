"""Statistics over persisted self-play games (runs/<run>/games/games_*.npz from uttt.train2).

    .venv/Scripts/python.exe tools/corpus_stats.py runs/v2a --last 20
    .venv/Scripts/python.exe tools/corpus_stats.py runs/deep8_c1_300_e8 --last 20 --rule draw

Reports: outcome and end-reason shares, length distribution, first-move orbit table
(count, X score), free-move frequency and its outcome correlation, when games are
decided (mean |root value| by ply), and the share of games where the tiebreak rule
decided the result. Games are replayed on the reference engine for the free-move data.

--rule is the rule the corpus is READ under. A count-rule corpus read under "draw" is relabelled
mechanically — a game ends at the same ply under either rule (all boards closed, or a macro line),
so every count-decided game (reason 2) becomes a draw (reason 3, winner 0) and nothing else moves.
That is PLAN7 §5 K1's no-training control, and it claims nothing about how a draw-trained agent
would have played. The reverse direction is not derivable from the stored records and is refused.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import SYM_CELL  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.rules import RULES  # noqa: E402


def corpus_rule(run: str) -> str:
    """The rule the corpus was GENERATED under, from the run's config.json (pre-K1 runs: count)."""
    path = os.path.join(run, "config.json")
    if not os.path.exists(path):
        return "count"
    with open(path) as f:
        return json.load(f).get("rule", "count")


def relabel(win: np.ndarray, reason: np.ndarray, src: str, dst: str):
    """Re-read a corpus's outcomes under rule `dst`. Returns (winners, reasons, number of games changed)."""
    if src == dst:
        return win, reason, 0
    if not (src == "count" and dst == "draw"):
        sys.exit(f"cannot read a {src}-rule corpus under {dst}: the stored records do not carry the board count "
                 "(rebuild the corpus, or read it under its own rule)")
    flip = reason == 2
    return np.where(flip, 0, win).astype(win.dtype), np.where(flip, 3, reason).astype(reason.dtype), int(flip.sum())


def orbits():
    seen, out = set(), []
    for m in range(81):
        if m in seen:
            continue
        orb = sorted({int(SYM_CELL[s, m]) for s in range(8)})
        seen.update(orb)
        out.append(orb)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--last", type=int, default=0, help="use only the last N game files")
    ap.add_argument("--replay", type=int, default=20000, help="max games to replay for free-move statistics")
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule the corpus is READ under (see the module docstring)")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.run, "games", "games_*.npz")))
    if a.last:
        files = files[-a.last :]
    moves, rv, win, reason, length = [], [], [], [], []
    for f in files:
        z = np.load(f)
        moves.append(z["moves"]); rv.append(z["root_values"]); win.append(z["winners"]); reason.append(z["reasons"]); length.append(z["lengths"])
    moves, rv, win, reason, length = map(np.concatenate, (moves, rv, win, reason, length))
    G = len(win)
    src = corpus_rule(a.run)
    print(f"{G} games from {len(files)} files; generated under rule {src}, read under rule {a.rule}")
    if G == 0:
        return
    win, reason, changed = relabel(win, reason, src, a.rule)
    if changed:
        print(f"relabelled {changed} of {G} games ({100 * changed / G:.1f} %) from a count decision to a draw "
              "(mechanical re-reading of the same games, not a re-run)")
    print(f"X wins {100 * (win == 1).mean():.1f}%  O wins {100 * (win == -1).mean():.1f}%  draws {100 * (win == 0).mean():.1f}%")
    print(f"ended by line {100 * (reason == 1).mean():.1f}%  by count {100 * (reason == 2).mean():.1f}%  equal count {100 * (reason == 3).mean():.1f}%")
    print(f"length: mean {length.mean():.1f}  median {np.median(length):.0f}  p10 {np.percentile(length, 10):.0f}  p90 {np.percentile(length, 90):.0f}  max {length.max()}")

    print("\nfirst move by symmetry orbit: games, X score (win=1, draw=0.5)")
    fm = moves[:, 0].astype(np.int64)
    xs = (win == 1) + 0.5 * (win == 0)
    rows = []
    for orb in orbits():
        m = np.isin(fm, orb)
        if m.any():
            rows.append((int(m.sum()), orb, float(xs[m].mean())))
    for cnt, orb, s in sorted(rows, reverse=True):
        print(f"  {str(orb):40s} n={cnt:6d}  X score {100 * s:.1f}%")

    # root value trajectory: mean value for X (sign-corrected) by ply, split by final result
    print("\nmean root value from X's perspective by ply (X wins | O wins | draws):")
    T = min(int(length.max()), 81)
    signs = np.where(np.arange(T) % 2 == 0, 1.0, -1.0)  # ply parity -> side to move
    for p in range(0, T, 6):
        vals = rv[:, p].astype(np.float32) * signs[p]
        has = length > p
        parts = []
        for w in (1, -1, 0):
            m = has & (win == w)
            parts.append(f"{vals[m].mean():+.2f}" if m.any() else "  n/a")
        print(f"  ply {p:2d}: " + " | ".join(parts) + f"   (games alive {int(has.sum())})")

    # replay for free-move statistics
    R = min(G, a.replay)
    free_moves = np.zeros(R, dtype=np.int64)
    free_by_x = np.zeros(R, dtype=np.int64)
    closed_at_end = np.zeros(R, dtype=np.int64)
    for k in range(R):
        g = UTTT(a.rule)
        for t in range(int(length[k])):
            if g.next_board < 0 and t > 0:
                free_moves[k] += 1
                if g.player == 1:
                    free_by_x[k] += 1
            g.play(int(moves[k, t]))
        closed_at_end[k] = int((g.macro != 0).sum())
    w = win[:R]
    print(f"\nfree moves per game (replayed {R}): mean {free_moves.mean():.2f}; games with >=1 free move {100 * (free_moves > 0).mean():.1f}%")
    fx = free_by_x - (free_moves - free_by_x)
    for lo, hi, name in ((-99, -1, "O had more free moves"), (0, 0, "equal"), (1, 99, "X had more free moves")):
        m = (fx >= lo) & (fx <= hi)
        if m.any():
            print(f"  {name:24s}: n={int(m.sum()):6d}  X score {100 * ((w[m] == 1) + 0.5 * (w[m] == 0)).mean():.1f}%")
    print(f"closed boards at game end: mean {closed_at_end.mean():.2f}")


if __name__ == "__main__":
    main()
