"""Folk claims about Ultimate Tic-Tac-Toe checked against the agent (PLAN5 §4 C2).

    .venv/Scripts/python.exe tools/principles.py --data runs/probe_data_deep8late.npz --corpus runs/deep10_c1_300 --last 20

1. "Never send the opponent to a board where one move wins it" (minimax.dev's pruning rule). On the probe dataset
   (positions from held-out games with the source net's 256-sim best move as a label): how often the search's move
   sends the opponent to a board they can win at once, against the base rate over all legal moves; and, when it
   does, what the position looks like (is the board already decided, does the opponent's local win create a macro
   threat, is the game already decided).
2. "The Orlin gambit" (conceding the centre board early): is answered by B3's ownership model — not repeated here.
3. What drawn games look like: from a corpus's last N files, the final macro of every game that ended by equal
   count: boards won by each side, boards full, and how many draws had the count settled (no open board could
   change it) some plies before the end.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.concepts import concept_labels  # noqa: E402
from uttt.game import FULL, LINES, UTTT  # noqa: E402


def play_all(cells, macro, nb, player, moves):
    """Play one move per position on the reference engine; returns the child state arrays."""
    N = len(moves)
    out = [np.zeros((N, 81), np.int8), np.zeros((N, 9), np.int8), np.zeros(N, np.int8), np.zeros(N, np.int8), np.zeros(N, bool), np.zeros(N, np.int8)]
    for i in range(N):
        g = UTTT()
        g.cells[:], g.macro[:], g.next_board, g.player = cells[i], macro[i], int(nb[i]), int(player[i])
        g.move_count = int((g.cells != 0).sum())
        g.play(int(moves[i]))
        out[0][i], out[1][i], out[2][i], out[3][i], out[4][i], out[5][i] = g.cells, g.macro, g.next_board, g.player, g.done, g.winner
    return out


def claim_sending(z) -> dict:
    cells, macro, nb, player = z["cells"], z["macro"], z["next_board"], z["player"]
    best = z["label_best_move_now"]
    N = len(best)
    c_cells, c_macro, c_nb, c_player, c_done, c_winner = play_all(cells, macro, nb, player, best)
    alive = ~c_done
    lab = concept_labels(c_cells[alive], c_macro[alive], c_nb[alive], c_player[alive])  # from the opponent's (new mover's) view
    sent_winnable = lab["local_win_now"].astype(bool)  # the opponent can win a board at once
    confined = lab["free_move"] == 0
    # base rate: a random legal move from the same positions
    rng = np.random.default_rng(0)
    rand = np.zeros(N, np.int64)
    for i in range(N):
        g = UTTT()
        g.cells[:], g.macro[:], g.next_board, g.player = cells[i], macro[i], int(nb[i]), int(player[i])
        g.move_count = int((g.cells != 0).sum())
        rand[i] = int(rng.choice(g.legal_moves()))
    r_cells, r_macro, r_nb, r_player, r_done, _ = play_all(cells, macro, nb, player, rand)
    r_alive = ~r_done
    r_lab = concept_labels(r_cells[r_alive], r_macro[r_alive], r_nb[r_alive], r_player[r_alive])
    r_sent = r_lab["local_win_now"].astype(bool)
    # the label is the solver's optimal move where the position is solved (exact >= 0) and the search's move elsewhere
    exact = z["label_exact_value"][alive]
    ply = z["ply"][alive]
    solved, searched = exact >= 0, exact < 0
    macro_win_after = lab["macro_win_now"].astype(bool)  # the opponent can win the game at once
    macro_threat_after = lab["threat_for_any"].astype(bool)
    rate = lambda m: float(sent_winnable[m].mean()) if m.any() else float("nan")  # noqa: E731
    return {"positions": int(N),
            "search move (unsolved positions) sends the opponent to a board they can win at once": rate(searched),
            "  of which confined (not a free move)": float((sent_winnable & confined & searched).sum() / max((sent_winnable & searched).sum(), 1)),
            "  by ply": {f"{lo}-{hi}": rate(searched & (ply >= lo) & (ply <= hi)) for lo, hi in ((0, 19), (20, 31), (32, 43), (44, 80))},
            "  and the opponent can then win the game at once": float((sent_winnable & searched & macro_win_after).sum() / max(searched.sum(), 1)),
            "  and the opponent has a macro threat": float((sent_winnable & searched & macro_threat_after).sum() / max(searched.sum(), 1)),
            "random legal move sends the opponent to a board they can win at once": float(r_sent.mean()),
            "OPTIMAL move (solved positions, <= 14 empties) sends the opponent to a board they can win at once": rate(solved),
            "  when the mover is winning": rate(solved & (exact == 2)),
            "  when the position is drawn": rate(solved & (exact == 1)),
            "  when the mover is lost": rate(solved & (exact == 0)),
            "  and the opponent can then win the game at once, mover not lost": float((sent_winnable & solved & (exact >= 1) & macro_win_after).sum() / max((solved & (exact >= 1)).sum(), 1)),
            "solved positions": int(solved.sum())}


def claim_draws(corpus: str, last: int, max_games: int = 20000) -> dict:
    files = sorted(glob.glob(os.path.join(corpus, "games", "games_*.npz")))[-last:]
    moves, winners, lengths, reasons = [], [], [], []
    for f in files:
        zz = np.load(f)
        moves.append(zz["moves"]); winners.append(zz["winners"]); lengths.append(zz["lengths"]); reasons.append(zz["reasons"])
    moves, winners, lengths, reasons = map(np.concatenate, (moves, winners, lengths, reasons))
    draws = np.flatnonzero(winners == 0)[:max_games]
    finals, lead_changes = [], []
    for k in draws:
        g = UTTT()
        L = int(lengths[k])
        lead, changes = 0, 0
        for t in range(L):
            g.play(int(moves[k, t]))
            d = int((g.macro == 1).sum()) - int((g.macro == -1).sum())
            if d != 0 and np.sign(d) != lead and lead != 0:
                changes += 1
            if d != 0:
                lead = int(np.sign(d))
        finals.append((int((g.macro == 1).sum()), int((g.macro == -1).sum()), int((g.macro == FULL).sum())))
        lead_changes.append(changes)
    finals = np.array(finals)
    combos = {}
    for x, o, f in finals:
        combos[f"X{x}-O{o}-full{f}"] = combos.get(f"X{x}-O{o}-full{f}", 0) + 1
    top = sorted(combos.items(), key=lambda kv: -kv[1])[:6]
    return {"games": int(len(winners)), "draws": int(len(draws)), "draw share": float((winners == 0).mean()),
            "mean boards each side": float(finals[:, 0].mean()), "mean full boards": float(finals[:, 2].mean()),
            "most common final counts (X boards - O boards - full)": {k: v / len(draws) for k, v in top},
            "board-count lead changed hands during the game (share of draws)": float(np.mean(np.array(lead_changes) > 0)),
            "mean lead changes per draw": float(np.mean(lead_changes)),
            "mean draw length": float(lengths[draws].mean()), "mean length all games": float(lengths.mean())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="runs/probe_data_deep8late.npz")
    ap.add_argument("--corpus", default="runs/deep10_c1_300")
    ap.add_argument("--last", type=int, default=20)
    ap.add_argument("--out", default="runs/principles.json")
    a = ap.parse_args()
    z = np.load(a.data)
    meta = json.loads(str(z["meta"]))
    res = {"data": a.data, "search_net": meta["net"], "sending": claim_sending(z), "draws": claim_draws(a.corpus, a.last)}
    print(json.dumps(res, indent=1))
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
