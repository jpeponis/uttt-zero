"""The exact frontier (PLAN7 J4): how far back into a run's late games the solver reaches under a node
budget, and how the net's search plays where it reaches.

    .venv/Scripts/python.exe tools/frontier.py --run runs/deep8_c1_300_e8 --net runs/deep8_c1_300_e8/net_0300.pt \
        --plies 40 70 --per_ply 500 --max_nodes 1e8 --sims 256 --device cuda:1 --out runs/plan7/J4_frontier.json

For every ply p in [P0, P1]: the population is the games of the run's last --last game files that are
still *alive* at p (length > p, so a position with a move to make exists there); --per_ply of them are
drawn without replacement, each replayed to ply p, and solved exactly under one budget of --max_nodes
nodes shared by the position and all its children (uttt.solver.solve_children_bounded). Where that
completes, the search move at --sims is graded exactly as tools/endgame.py eval grades one — the same
uttt.endgame.evaluate on a per-ply EndgameSet, so the same action regret against the exact child values,
the same optimal-move rate, the same cluster bootstrap.

Both conditionings are in the output's field names, because neither may be dropped when the numbers are
quoted (PLAN7 §7e row 22). The solved fraction is conditional on the game being alive at that ply —
games that ended earlier are not in the denominator, and they are the decided ones. The search numbers
are conditional on the position having been solved inside the budget — a subset that is the *easy* end
of that ply, and more so the harder the budget binds. "Solved from ply N onwards" is not a statement
this measurement can make.

Cost: an unsolved position spends the whole budget, so a ply costs at most per_ply * max_nodes nodes. The
solver runs at ~1.6e7 nodes/s/process on this machine, so the worst case of --per_ply 500 --max_nodes 1e8
over 8 processes is ~6.5 min/ply, ~3.5 h for plies 40-70; the early plies, where almost nothing resolves,
are the expensive ones. The per-ply timing is printed as it goes.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.endgame import EndgameSet, evaluate  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.solver import empties_in_open_boards, solve_children_bounded  # noqa: E402


def load_corpus(run: str, last: int):
    """The last `last` game files of <run>/games as (file names, per-file moves, one flat game table).

    The flat table is (file index, row, length) for every game, so "alive at ply p" is one comparison."""
    files = sorted(glob.glob(os.path.join(run, "games", "games_*.npz")))
    if not files:
        sys.exit(f"no game files in {os.path.join(run, 'games')}")
    if last:
        files = files[-last:]
    moves, fidx, row, length = [], [], [], []
    for i, f in enumerate(files):
        z = np.load(f)
        moves.append(z["moves"])
        n = len(z["lengths"])
        fidx.append(np.full(n, i, dtype=np.int64))
        row.append(np.arange(n, dtype=np.int64))
        length.append(z["lengths"].astype(np.int64))
    return ([os.path.basename(f) for f in files], moves,
            np.concatenate(fidx), np.concatenate(row), np.concatenate(length))


def positions_at_ply(moves, fidx, row, length, p: int, per_ply: int, rng) -> tuple[dict, int]:
    """Up to per_ply positions at ply p, drawn without replacement from the games alive there.

    Alive at p means length > p: the game had not ended before p, so the position at p exists and has a
    move to make. A game of length exactly p is over at p and is not in the population."""
    alive = np.flatnonzero(length > p)
    if alive.size == 0:
        return {}, 0
    pick = rng.choice(alive, size=min(per_ply, alive.size), replace=False)
    cols = {k: [] for k in ("cells", "macro", "next_board", "player", "empties", "game_id")}
    for i in pick:
        g = UTTT()
        seq = moves[fidx[i]][row[i]]
        for t in range(p):
            g.play(int(seq[t]))
        assert not g.done, (fidx[i], row[i], p)
        for name, val in zip(cols, (g.cells.copy(), g.macro.copy(), g.next_board, g.player,
                                    empties_in_open_boards(g.cells, g.macro), int(fidx[i]) * (1 << 20) + int(row[i]))):
            cols[name].append(val)
    out = {k: np.array(v) for k, v in cols.items()}
    out["cells"] = out["cells"].astype(np.int8)
    out["macro"] = out["macro"].astype(np.int8)
    return out, int(alive.size)


def solve_all(pos: dict, max_nodes: int, processes: int):
    args = [(pos["cells"][i], pos["macro"][i], int(pos["next_board"][i]), int(pos["player"][i]), max_nodes)
            for i in range(len(pos["player"]))]
    if processes <= 1:
        return [solve_children_bounded(a) for a in args]
    with Pool(processes) as pool:
        return pool.map(solve_children_bounded, args, chunksize=1)


def graded_set(pos: dict, solved: list, ply: int, meta: dict) -> EndgameSet:
    """The solved positions of one ply as an EndgameSet, so tools/endgame.py's grader can score them unchanged."""
    idx = [i for i, (v, child, _, ok) in enumerate(solved) if ok]
    exact = np.array([solved[i][0] for i in idx], dtype=np.int8)
    child = np.stack([solved[i][1] for i in idx]) if idx else np.zeros((0, 81), dtype=np.int8)
    return EndgameSet(pos["cells"][idx], pos["macro"][idx], pos["next_board"][idx].astype(np.int8),
                      pos["player"][idx].astype(np.int8), exact, child, pos["empties"][idx], pos["game_id"][idx],
                      np.full(len(idx), ply, dtype=np.int64), dict(meta, name=f"ply {ply}, solved"))


HEADER = (f"{'ply':>4s} {'alive':>7s} {'sampled':>7s} {'solved':>14s} {'nodes med':>11s} {'nodes p90':>11s} "
          f"{'optimal %':>18s} {'regret':>18s} {'unsolved':>8s} {'s':>6s}")


def format_row(d: dict) -> str:
    """One ply of the JSON as a table line; the header says which column is conditional on what."""
    def num(key, fmt, scale=1.0):
        v = d[key]
        return "-" if v is None else format(scale * v, fmt)

    def ci(key, fmt, scale=1.0):
        v, c = d[key], d[key.replace("_conditional_", "_ci_conditional_")]
        return "-" if v is None else f"{scale * v:{fmt}} [{scale * c[0]:{fmt}},{scale * c[1]:{fmt}}]"

    solved = "-" if d["fraction_solved_conditional_on_alive"] is None else \
        f"{100 * d['fraction_solved_conditional_on_alive']:5.1f} % ({d['n_solved']})"
    return (f"{d['ply']:4d} {d['games_alive_at_ply']:7d} {d['positions_sampled_conditional_on_alive']:7d} {solved:>14s} "
            f"{num('median_nodes_conditional_on_solved', ',.0f'):>11s} {num('p90_nodes_conditional_on_solved', ',.0f'):>11s} "
            f"{ci('search_optimal_move_rate_conditional_on_solved', '5.1f', 100):>18s} "
            f"{ci('search_mean_regret_conditional_on_solved', '5.3f'):>18s} "
            f"{d['unsolved_count_conditional_on_alive']:8d} {d['seconds']:6.1f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="run directory; its games/games_*.npz are the population")
    ap.add_argument("--net", required=True, help="checkpoint whose search is graded on the solved positions")
    ap.add_argument("--plies", type=int, nargs=2, default=[40, 70], metavar=("P0", "P1"))
    ap.add_argument("--per_ply", type=int, default=500)
    ap.add_argument("--max_nodes", type=float, default=1e8, help="node budget per position, shared by it and all its children")
    ap.add_argument("--sims", type=int, default=256)
    ap.add_argument("--last", type=int, default=20, help="use the last N game files of the run (0 = all)")
    ap.add_argument("--processes", type=int, default=8)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", default="runs/plan7/J4_frontier.json")
    a = ap.parse_args()
    max_nodes = int(a.max_nodes)
    device = torch.device(a.device)
    rng = np.random.default_rng(a.seed)

    names, moves, fidx, row, length = load_corpus(a.run, a.last)
    fe = FusedEvaluator(load_checkpoint(a.net, device), device)
    meta = {"run": a.run, "net": a.net, "corpus_files": names, "games": int(len(length)), "plies": a.plies,
            "per_ply": a.per_ply, "max_nodes": max_nodes, "sims": a.sims, "seed": a.seed, "processes": a.processes,
            "boot": a.boot, "device": str(device), "built": time.strftime("%Y-%m-%d %H:%M"),
            "alive_at_ply": "the game's length exceeds the ply, so a position with a move to make exists there",
            "solved": "the position and every legal child resolved within one shared budget of max_nodes nodes",
            "grading": "uttt.endgame.evaluate, the grader of tools/endgame.py eval: action regret against the exact "
                       "child values and optimal-move rate, cluster-bootstrap 95 % CIs over source games",
            "clusters": "within a ply every game contributes at most one position, so that cluster bootstrap is an "
                        "ordinary one; across plies the same game recurs, so the plies are not independent of each other",
            "warning": "the solved subset is the easy end of a ply and gets easier as the budget binds; every number "
                       "below is conditional as its name says, and 'solved from ply N' does not follow from any of them"}
    print(f"{a.run}: {len(length)} games in {len(names)} files ({names[0]}..{names[-1]}); "
          f"grading {a.net} at {a.sims} sims on {device}", flush=True)
    print(f"plies {a.plies[0]}-{a.plies[1]}, {a.per_ply} positions per ply, budget {max_nodes:,} nodes per position, "
          f"{a.processes} solver processes", flush=True)
    print("\n" + HEADER)
    print("(solved: conditional on alive | nodes, optimal, regret: conditional on solved)")
    rows = []
    for p in range(a.plies[0], a.plies[1] + 1):
        t = time.perf_counter()
        pos, n_alive = positions_at_ply(moves, fidx, row, length, p, a.per_ply, rng)
        n = len(pos.get("player", ()))
        solved = solve_all(pos, max_nodes, a.processes) if n else []
        ok = np.array([s[3] for s in solved], dtype=bool) if n else np.zeros(0, dtype=bool)
        nodes = np.array([s[2] for s in solved], dtype=np.int64) if n else np.zeros(0, dtype=np.int64)
        d = {"ply": p,
             "games_alive_at_ply": n_alive,
             "positions_sampled_conditional_on_alive": n,
             "fraction_solved_conditional_on_alive": float(ok.mean()) if n else None,
             "n_solved": int(ok.sum()),
             "unsolved_count_conditional_on_alive": int(n - ok.sum()),
             "median_nodes_conditional_on_solved": float(np.median(nodes[ok])) if ok.any() else None,
             "p90_nodes_conditional_on_solved": float(np.quantile(nodes[ok], 0.9)) if ok.any() else None,
             "nodes_spent_total": int(nodes.sum()),
             "search_optimal_move_rate_conditional_on_solved": None,
             "search_optimal_move_rate_ci_conditional_on_solved": None,
             "search_mean_regret_conditional_on_solved": None,
             "search_mean_regret_ci_conditional_on_solved": None,
             "median_empties_conditional_on_solved": float(np.median(pos["empties"][ok])) if ok.any() else None,
             "seconds": None}
        if ok.any():
            es = graded_set(pos, solved, p, meta)
            res = evaluate(fe, es, device, sims=[a.sims], n_boot=a.boot, symmetrise=False)
            r = res["rows"][-1]
            assert r["name"] == f"search {a.sims} sims", r["name"]
            d["search_optimal_move_rate_conditional_on_solved"] = r["optimal"]
            d["search_optimal_move_rate_ci_conditional_on_solved"] = list(r["optimal_ci"])
            d["search_mean_regret_conditional_on_solved"] = r["regret"]
            d["search_mean_regret_ci_conditional_on_solved"] = list(r["regret_ci"])
        d["seconds"] = round(time.perf_counter() - t, 1)
        rows.append(d)
        print(format_row(d), flush=True)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump({"meta": meta, "plies": rows}, fh, indent=1)
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
