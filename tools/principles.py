"""Folk claims about Ultimate Tic-Tac-Toe checked against the agent (PLAN5 §4 C2).

    .venv/Scripts/python.exe tools/principles.py --data runs/probe_data_deep8late.npz --corpus runs/deep10_c1_300 --last 20

1. "Never send the opponent to a board where one move wins it" (minimax.dev's pruning rule). On the probe dataset
   (positions from held-out games with the source net's 256-sim best move as a label): how often the search's move
   sends the opponent to a board they can win at once, against the base rate over all legal moves; and, when it
   does, what the position looks like (is the board already decided, does the opponent's local win create a macro
   threat, is the game already decided).
2. "The Orlin gambit" (conceding the centre board early): is answered by B3's ownership model — not repeated here.
3. What drawn games look like: from a corpus's last N files, the final macro of the drawn games: boards won by X
   and by O separately, boards full, and how many draws had the board-count lead change hands during the game.
   At most --max_draws games are replayed; when the window holds more, they are a uniform sample of it drawn with
   --seed (not its earliest --max_draws, which would truncate the anatomy chronologically), and the total and
   sampled counts are both recorded.

--rule count|draw is the rule everything here is read under. The probe dataset's own rule (its exact labels)
must match it; the corpus is relabelled mechanically the way tools/corpus_stats.py does (PLAN7 §5 K1), so
under "draw" the draw anatomy is the anatomy of every no-line ending, 5-3 counts included.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from corpus_stats import corpus_rule, relabel  # noqa: E402
from uttt.concepts import concept_labels  # noqa: E402
from uttt.game import FULL, LINES, UTTT  # noqa: E402
from uttt.rules import RULES, tag_path  # noqa: E402


def play_all(cells, macro, nb, player, moves, rule="count"):
    """Play one move per position on the reference engine; returns the child state arrays."""
    N = len(moves)
    out = [np.zeros((N, 81), np.int8), np.zeros((N, 9), np.int8), np.zeros(N, np.int8), np.zeros(N, np.int8), np.zeros(N, bool), np.zeros(N, np.int8)]
    for i in range(N):
        g = UTTT(rule)
        g.cells[:], g.macro[:], g.next_board, g.player = cells[i], macro[i], int(nb[i]), int(player[i])
        g.move_count = int((g.cells != 0).sum())
        g.play(int(moves[i]))
        out[0][i], out[1][i], out[2][i], out[3][i], out[4][i], out[5][i] = g.cells, g.macro, g.next_board, g.player, g.done, g.winner
    return out


def claim_sending(z, rule: str = "count") -> dict:
    cells, macro, nb, player = z["cells"], z["macro"], z["next_board"], z["player"]
    best = z["label_best_move_now"]
    N = len(best)
    c_cells, c_macro, c_nb, c_player, c_done, c_winner = play_all(cells, macro, nb, player, best, rule)
    alive = ~c_done
    lab = concept_labels(c_cells[alive], c_macro[alive], c_nb[alive], c_player[alive])  # from the opponent's (new mover's) view
    sent_winnable = lab["local_win_now"].astype(bool)  # the opponent can win a board at once
    confined = lab["free_move"] == 0
    # base rate: a random legal move from the same positions
    rng = np.random.default_rng(0)
    rand = np.zeros(N, np.int64)
    for i in range(N):
        g = UTTT(rule)
        g.cells[:], g.macro[:], g.next_board, g.player = cells[i], macro[i], int(nb[i]), int(player[i])
        g.move_count = int((g.cells != 0).sum())
        rand[i] = int(rng.choice(g.legal_moves()))
    r_cells, r_macro, r_nb, r_player, r_done, _ = play_all(cells, macro, nb, player, rand, rule)
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


def sample_draws(winners: np.ndarray, max_games: int, seed: int = 0) -> np.ndarray:
    """Indices of the drawn games to replay for the anatomy.

    All of them, in file order, when the window holds at most max_games — so a window that fits the cap is
    read exactly as it always was. Otherwise a UNIFORM sample of the whole window with a seeded RNG, not its
    earliest max_games (M2 row 8): under `draw` a late corpus can hold far more draws than the cap, and the
    first max_games of a file-ordered window are its earliest games, which makes the anatomy a statement
    about the start of the window rather than about the window."""
    idx = np.flatnonzero(winners == 0)
    if len(idx) <= max_games:
        return idx
    return np.sort(np.random.default_rng(seed).choice(idx, size=max_games, replace=False))


def claim_draws(corpus: str, last: int, max_games: int = 20000, rule: str = "count", seed: int = 0,
                corpus_rule_override: str = "") -> dict:
    files = sorted(glob.glob(os.path.join(corpus, "games", "games_*.npz")))[-last:]
    moves, winners, lengths, reasons = [], [], [], []
    for f in files:
        zz = np.load(f)
        moves.append(zz["moves"]); winners.append(zz["winners"]); lengths.append(zz["lengths"]); reasons.append(zz["reasons"])
    moves, winners, lengths, reasons = map(np.concatenate, (moves, winners, lengths, reasons))
    src = corpus_rule(corpus, corpus_rule_override)
    winners, reasons, relabelled = relabel(winners, reasons, src, rule)
    all_draws = np.flatnonzero(winners == 0)
    draws = sample_draws(winners, max_games, seed)
    finals, lead_changes = [], []
    for k in draws:
        g = UTTT(rule)
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
    return {"games": int(len(winners)), "draws total": int(len(all_draws)), "draws sampled": int(len(draws)),
            "draw sample seed": seed, "draw sample cap": max_games, "draw share": float((winners == 0).mean()),
            "rule": rule, "corpus rule": src, "games relabelled from a count decision": relabelled,
            # X and O separately: under "draw" a no-line ending no longer implies equal board counts,
            # so one "each side" mean is X's alone and says nothing about O's (M2 row 8).
            "mean boards X": float(finals[:, 0].mean()), "mean boards O": float(finals[:, 1].mean()),
            "mean full boards": float(finals[:, 2].mean()),
            "most common final counts (X boards - O boards - full)": {k: v / len(draws) for k, v in top},
            "board-count lead changed hands during the game (share of draws)": float(np.mean(np.array(lead_changes) > 0)),
            "mean lead changes per draw": float(np.mean(lead_changes)),
            "mean draw length": float(lengths[draws].mean()), "mean length all games": float(lengths.mean())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="runs/probe_data_deep8late.npz")
    ap.add_argument("--corpus", default="runs/deep10_c1_300")
    ap.add_argument("--last", type=int, default=20)
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule everything is read under")
    ap.add_argument("--corpus_rule", choices=RULES, default="", help="the rule the corpus was GENERATED under, for a "
                    "directory with no config.json and no rule tag in its game files (tools/corpus_stats.py)")
    ap.add_argument("--max_draws", type=int, default=20000, help="draws replayed for the anatomy; more than this are "
                    "sampled uniformly over the window with --seed")
    ap.add_argument("--seed", type=int, default=0, help="seed of the uniform draw sample (a no-op when the "
                    "window holds no more draws than --max_draws)")
    ap.add_argument("--out", default="runs/principles.json")
    a = ap.parse_args()
    z = np.load(a.data)
    meta = json.loads(str(z["meta"]))
    data_rule = meta.get("rule", "count")  # pre-K1 probe datasets were built under count
    if data_rule != a.rule:
        sys.exit(f"{a.data} carries {data_rule}-rule exact labels; rebuild it with tools/probe.py build --rule {a.rule}")
    res = {"rule": a.rule, "data": a.data, "search_net": meta["net"],
           "sending": claim_sending(z, a.rule),
           "draws": claim_draws(a.corpus, a.last, a.max_draws, a.rule, a.seed, a.corpus_rule)}
    print(json.dumps(res, indent=1))
    out = tag_path(a.out, a.rule)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
