"""Play against a trained network in the terminal.

    .venv/Scripts/python.exe play.py runs/v2a/net_0150.pt --sims 800 --human O

Moves are entered as "board cell" (each 1-9, row-major like a keypad read top-to-bottom:
1 2 3 / 4 5 6 / 7 8 9) or as a single 0-80 engine index. Type "hint" for the agent's suggestion.
"""
from __future__ import annotations

import argparse
import sys

import torch

from uttt.batch import BatchUTTT
from uttt.game import UTTT
from uttt.infer import FusedEvaluator
from uttt.model import load_checkpoint
from uttt.search import BatchedSearch, SearchConfig


def load(path: str, device):
    return FusedEvaluator(load_checkpoint(path, device), device)


def parse_move(s: str) -> int:
    parts = s.replace(",", " ").split()
    if len(parts) == 2:
        b, c = int(parts[0]) - 1, int(parts[1]) - 1
        return 9 * b + c
    return int(parts[0])


def fmt(m: int) -> str:
    return f"board {m // 9 + 1} cell {m % 9 + 1}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--sims", type=int, default=800)
    ap.add_argument("--human", default="X", choices=["X", "O"])
    ap.add_argument("--device", default="cuda:0")
    a = ap.parse_args()
    device = torch.device(a.device)
    ev = load(a.checkpoint, device)
    cfg = SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, m_considered=81, root_prior_floor=0.03,
                       cuda_graph=device.type == "cuda", depth_cap=min(a.sims, 40))
    mcts = BatchedSearch(ev, 1, cfg, device)
    human = 1 if a.human == "X" else -1
    ref = UTTT()
    b = BatchUTTT(1, device)

    def think():
        r = mcts.search(b.cells, b.macro, b.next_board, b.player, b.done, b.winner, selfplay=False)
        top = torch.topk(r.visits[0], 3)
        alts = ", ".join(f"{fmt(int(i))} ({int(n)} visits)" for n, i in zip(top.values, top.indices) if n > 0)
        return int(r.action[0]), float(r.root_value[0]), alts

    while not ref.done:
        print("\n" + str(ref))
        if ref.player == human:
            while True:
                try:
                    s = input("your move (board cell | index | hint): ").strip()
                except EOFError:
                    print("\n(input closed)")
                    return
                if s.lower().startswith("h"):
                    mv, v, alts = think()
                    print(f"hint: {fmt(mv)}; eval for you {v:+.2f}; candidates: {alts}")
                    continue
                try:
                    mv = parse_move(s)
                    if ref.legal_mask()[mv]:
                        break
                except (ValueError, IndexError):
                    pass
                print("illegal")
        else:
            mv, v, alts = think()
            print(f"agent plays {fmt(mv)} [{mv}]; eval for agent {v:+.2f}; candidates: {alts}")
        ref.play(mv)
        b.step(torch.tensor([mv], device=device))
    print("\n" + str(ref))


if __name__ == "__main__":
    main()
