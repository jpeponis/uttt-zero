"""Reply principles read off an opening book (PLAN5 §4 C2): how often the most-visited reply is the "self-send" —
the cell whose index equals the board the mover was sent to, which sends the opponent straight back into that same
board — and what the reply is otherwise. Since PLAN6 E1 a book's replies are orbits; the top reply is the orbit's
representative and its share the orbit's summed visit share. Every statistic here (self-send, cell class, free move,
back-to-previous) is invariant within an orbit, so the representative stands for the orbit.

    .venv/Scripts/python.exe tools/book_stats.py runs/book_deep10.json runs/book_deep8.json
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.game import UTTT  # noqa: E402


def stats(path: str) -> None:
    b = json.load(open(path))
    nodes = b["nodes"]
    tot = avail = chosen = 0
    by_depth = {}
    share_self, share_other = [], []
    other = Counter()
    cell_class = Counter()
    for n in nodes.values():
        if not n["moves"]:
            continue
        g = UTTT()
        for m in n["seq"]:
            g.play(m)
        sent = g.next_board
        if sent < 0 or g.macro[sent] != 0:
            continue
        top = n["moves"][0]
        board, cell = top["move"] // 9, top["move"] % 9
        tot += 1
        free = g.cells[9 * sent + sent] == 0
        avail += int(free)
        d = by_depth.setdefault(n["depth"], [0, 0, 0])
        d[0] += 1
        d[1] += int(free)
        cell_class["centre" if cell == 4 else "corner" if cell in (0, 2, 6, 8) else "edge"] += 1
        if cell == board:
            chosen += 1
            d[2] += 1
            share_self.append(top["share"])
        else:
            share_other.append(top["share"])
            prev = n["seq"][-1] // 9
            other["gives a free move" if g.macro[cell] != 0 else "back to the board they played from" if cell == prev else "elsewhere"] += 1
    m = b["meta"]
    print(f"{path}: {m['net_name']} at {m['sims']} sims, depth {m['depth']}, top-{m['top']}; {len(nodes)} nodes, {tot} with a confined mover")
    print(f"  self-send reply (cell index = board index, opponent sent back into the same board): available in {avail}, chosen in {chosen} "
          f"({100 * chosen / max(avail, 1):.0f} %); by depth [nodes, available, chosen]: {by_depth}")
    if share_self and share_other:
        print(f"  mean visit share of the top reply: self-send {sum(share_self) / len(share_self):.2f} (n={len(share_self)}), "
              f"other {sum(share_other) / len(share_other):.2f} (n={len(share_other)})")
    print(f"  when not the self-send: {dict(other)}")
    print(f"  cell class of the top reply: {dict(cell_class)}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        stats(p)
