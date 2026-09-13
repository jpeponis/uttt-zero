"""Annotated puzzle positions (PLAN5 §4 C3): for every hard puzzle in a puzzle file, the board, the exact value of
each legal move, and the solver's line after the best move and after the net's move — the raw material for a
hand-written commentary.

    .venv/Scripts/python.exe tools/annotate.py suites/puzzles_v2_dev.npz [--all] [--out docs/positions_raw.md]

--rule count|draw is the rule the solver lines are computed under; it must be the rule the puzzle file was
built under (its stored exact values and child tables are that rule's), so it is checked and never inferred
from the file (PLAN7 §5 K1).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from puzzles import as_game, pv_and_end  # noqa: E402
from uttt.rules import RULES, tag_path  # noqa: E402
from uttt.solver import ILLEGAL  # noqa: E402

SYM = {1: "X", -1: "O", 0: "."}


def value_map(child: np.ndarray, player: int) -> str:
    """The exact value after each legal move, drawn on the 9x9 board from the mover's view: + win, = draw, - loss."""
    rows = []
    for R in range(3):
        for r in range(3):
            cells = []
            for C in range(3):
                b = 3 * R + C
                cells.append(" ".join({1: "+", 0: "=", -1: "-"}.get(int(child[9 * b + 3 * r + c]), ".") if child[9 * b + 3 * r + c] != ILLEGAL else "."
                                      for c in range(3)))
            rows.append("  ".join(cells))
        if R < 2:
            rows.append("")
    return "\n".join(rows)


def line_after(cells, macro, nb, player, first_move, max_len=8, rule="count"):
    """Play `first_move`, then the solver's greedy line; returns the moves and how the game ends."""
    g = as_game(cells, macro, nb, player, rule)
    g.play(int(first_move))
    if g.done:
        return [int(first_move)], g.end_reason, g.winner
    from uttt.solver import solve_children

    _, ch = solve_children((g.cells, g.macro, g.next_board, g.player), rule)
    pv, end = pv_and_end(g.cells, g.macro, g.next_board, g.player, ch, max_len=max_len - 1, rule=rule)
    h = as_game(cells, macro, nb, player, rule)
    for m in [int(first_move)] + pv:
        h.play(m)
        if h.done:
            break
    while not h.done:
        _, ch2 = solve_children((h.cells, h.macro, h.next_board, h.player), rule)
        h.play(int(np.flatnonzero(ch2 == ch2.max())[0]))
    return [int(first_move)] + pv, h.end_reason, h.winner


def mv(m: int) -> str:
    return f"{m} (board {m // 9}, cell {m % 9})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("puzzles")
    ap.add_argument("--all", action="store_true", help="every puzzle, not only the hard ones")
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule the lines are solved under; must be the puzzle file's")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    z = np.load(a.puzzles)
    meta = json.loads(str(z["meta"]))
    file_rule = meta.get("rule", "count")  # pre-K1 puzzle files: count
    if file_rule != a.rule:
        sys.exit(f"{a.puzzles} was built under rule {file_rule!r} and --rule is {a.rule!r}: its exact values and "
                 f"child tables are {file_rule}-rule. Read it under --rule {file_rule}, or rebuild it with "
                 f"tools/puzzles.py --rule {a.rule}.")
    idx = np.flatnonzero(z["hard"]) if not a.all else np.arange(len(z["hard"]))
    out = [f"# Puzzle positions from `{a.puzzles}` ({'hard' if not a.all else 'all'}: {len(idx)}; net {meta['net']}, search {meta['sims']} sims)", ""]
    for i in idx:
        cells, macro, nb, player = z["cells"][i], z["macro"][i], int(z["next_board"][i]), int(z["player"][i])
        g = as_game(cells, macro, nb, player, a.rule)
        exact, child, raw, srch = int(z["exact"][i]), z["child"][i], int(z["raw_move"][i]), int(z["search_move"][i])
        best_line, best_end, best_w = line_after(cells, macro, nb, player, int(z["pv"][i][0]), rule=a.rule)
        raw_line, raw_end, raw_w = line_after(cells, macro, nb, player, raw, rule=a.rule)
        out += [f"## Puzzle {int(i)} — game {int(z['game_id'][i])}, ply {int(z['ply'][i])}, {SYM[player]} to move, "
                f"{'free move' if nb < 0 or macro[nb] != 0 else f'sent to board {nb}'}; exact value for the mover {exact:+d}; motifs: {z['motifs'][i] or '-'}", "",
                "```", str(g), "```", "",
                "Exact value after each legal move (mover's view: `+` win, `=` draw, `-` loss):", "", "```", value_map(child, player), "```", "",
                f"- best move {mv(int(z['pv'][i][0]))}: line {best_line} → {best_end}, winner {SYM[best_w]}",
                f"- the net's move {mv(raw)} (search {mv(srch)}), value {int(child[raw]):+d}: line {raw_line} → {raw_end}, winner {SYM[raw_w]}", ""]
    text = "\n".join(out)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("wrote", a.out)


if __name__ == "__main__":
    main()
