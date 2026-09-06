"""Canonical-position overlap between (and within) frozen position sets (PLAN6 E10; REVIEW-astra §5.5: a game-level
split is only a split if symmetric copies of one position do not sit on both sides of it).

    .venv/Scripts/python.exe tools/suite_overlap.py suites/endgame_v3_dev.npz suites/endgame_v3_test.npz

A position's key is the lexicographically smallest D4 image of (cells, macro, next board), with the side to move;
two positions with the same key are the same position up to a symmetry. Reports, per set, distinct keys and
duplicates, and the number of keys the sets share.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import SYM_BOARD, SYM_BOARD_INV, SYM_CELL_INV  # noqa: E402
from uttt.endgame import EndgameSet  # noqa: E402


def canonical_keys(cells, macro, next_board, player) -> list[bytes]:
    """Exact canonical key per position (bytes of the smallest image), no hashing."""
    c = torch.from_numpy(np.asarray(cells, dtype=np.int8))
    m = torch.from_numpy(np.asarray(macro, dtype=np.int8))
    nb = torch.from_numpy(np.asarray(next_board, dtype=np.int8)).long()
    n = c.shape[0]
    c8 = c[:, SYM_CELL_INV]  # (n, 8, 81)
    m8 = m[:, SYM_BOARD_INV]
    nb8 = torch.where(nb.unsqueeze(1) >= 0, SYM_BOARD[:, nb.clamp(min=0)].t(), nb.unsqueeze(1)).to(torch.int8)
    keys = torch.cat([c8, m8, nb8.unsqueeze(2)], 2).numpy()  # (n, 8, 91)
    out = []
    p = np.asarray(player, dtype=np.int8)
    for i in range(n):
        imgs = [keys[i, s].tobytes() for s in range(8)]
        out.append(min(imgs) + bytes([p[i] + 2]))
    return out


def main() -> None:
    sets = {path: EndgameSet.load(path) for path in sys.argv[1:]}
    keys = {}
    for path, es in sets.items():
        k = canonical_keys(es.cells, es.macro, es.next_board, es.player)
        keys[path] = k
        distinct = len(set(k))
        print(f"{path}: {es.n} positions from {len(np.unique(es.game_id))} games; {distinct} distinct canonical positions "
              f"({es.n - distinct} symmetric or literal duplicates within the set)")
    paths = list(sets)
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            shared = set(keys[paths[i]]) & set(keys[paths[j]])
            print(f"{os.path.basename(paths[i])} and {os.path.basename(paths[j])}: {len(shared)} shared canonical positions")


if __name__ == "__main__":
    main()
