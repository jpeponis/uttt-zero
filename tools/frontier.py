"""The exact frontier (PLAN7 J4): how far back into a run's late games the solver reaches under a node
budget, and how the net's search plays where it reaches.

    .venv/Scripts/python.exe tools/frontier.py --run runs/deep8_c1_300_e8 --net runs/deep8_c1_300_e8/net_0300.pt \
        --plies 40 70 --per_ply 500 --max_nodes 1e8 --sims 256 --device cuda:1 --out runs/plan7/J4_frontier.json

For every ply p in [P0, P1]: the population is the games of the run's last --last game files that are
still *alive* at p (length > p, so a position with a move to make exists there); --per_ply of them are
drawn without replacement, each replayed to ply p, and solved exactly under one budget of --max_nodes
nodes shared by the position and all its children (uttt.solver.solve_children_bounded). Where that
completes, the search move at --sims is graded exactly as tools/endgame.py eval grades one — the same
uttt.endgame.evaluate on a per-ply EndgameSet, so the same action regret against the exact child values
and the same optimal-move rate.

THE ORDINATE IS COMPLETE LEGAL-ACTION VALUE COVERAGE WITHIN THE BUDGET, not root solvability (M2, PLAN7
§7e M2 row 16). A position counts *complete* when the exact value of EVERY legal child was obtained
inside the shared budget — what grading a chosen move against all of its alternatives requires. That is
strictly stronger than proving the root's value: the root value alone can follow from a cutoff that never
values the other children. The field names say "complete coverage" for that reason; "solved" is not a
word this measurement earns.

NODE-COUNT CONVENTION. A node is one recursive entry of the budgeted kernel uttt.solver._negamax_bounded.
A child that is already terminal after the move is decided directly in solve_children_bounded and costs
ZERO counted nodes (uttt/solver.py:255-263), so a position whose children are nearly all terminal can
complete at a node count far below its child count. The budget bounds SEARCH WORK, not wall time.

Both conditionings are in the output's field names, because neither may be dropped when the numbers are
quoted (PLAN7 §7e row 22). The coverage fraction is conditional on the game being alive at that ply —
games that ended earlier are not in the denominator, and they are the decided ones. The search numbers
are conditional on the position having had complete coverage inside the budget — a subset that is the
*easy* end of that ply, and more so the harder the budget binds. "Solved from ply N onwards" is not a
statement this measurement can make.

UNCERTAINTY. The two proportions (coverage, optimal-move rate) carry 95 % Wilson intervals, which stay
inside [0, 1] and do not collapse to a point on an all-success sample the way a percentile bootstrap of
[1, 1, ..., 1] does. Mean regret keeps the cluster bootstrap, except that a degenerate sample (every
regret identical) reports no interval at all rather than a zero-width one. Within a ply each game
contributes at most one position; ACROSS plies the same game recurs, so comparing plies needs game-linked
resampling over the per-position table (<out>_positions.npz, which carries game_id for exactly that), not
independent-row inference.

Cost: an incomplete position spends the whole budget, so a ply costs at most per_ply * max_nodes nodes. The
solver runs at ~1.6e7 nodes/s/process on this machine, so the worst case of --per_ply 500 --max_nodes 1e8
over 8 processes is ~6.5 min/ply, ~3.5 h for plies 40-70; the early plies, where almost nothing resolves,
are the expensive ones. The per-ply timing is printed as it goes.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
import time
from functools import partial
from multiprocessing import Pool

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.endgame import EndgameSet, evaluate  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.rules import RULES, check_rule, tag_path  # noqa: E402
from uttt.solver import ILLEGAL, empties_in_open_boards, solve_children_bounded  # noqa: E402

Z95 = 1.959963984540054
NULL_ROW = -3  # per-position child-value row for a position that did not complete (ILLEGAL is -2)


def wilson(k: int, n: int) -> list | None:
    """95 % Wilson score interval for a binomial share: boundary-safe, and never zero-width at k == n.

    Kept local (tools/empty_board.py has its own copy) so each tool stands alone."""
    if n == 0:
        return None
    p, z2 = k / n, Z95 * Z95
    d = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / d
    half = Z95 * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / d
    return [centre - half, centre + half]


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


def positions_at_ply(moves, fidx, row, length, p: int, per_ply: int, rng, rule: str) -> tuple[dict, int]:
    """Up to per_ply positions at ply p, drawn without replacement from the games alive there.

    Alive at p means length > p: the game had not ended before p, so the position at p exists and has a
    move to make. A game of length exactly p is over at p and is not in the population. (Replay is
    rule-independent — the terminal rule decides the winner of a full macro grid, not whether the game is
    over — but the rule is passed anyway so nothing in this tool defaults silently.)"""
    alive = np.flatnonzero(length > p)
    if alive.size == 0:
        return {}, 0
    pick = rng.choice(alive, size=min(per_ply, alive.size), replace=False)
    cols = {k: [] for k in ("cells", "macro", "next_board", "player", "empties", "game_id", "file_index", "game_row")}
    for i in pick:
        g = UTTT(rule)
        seq = moves[fidx[i]][row[i]]
        for t in range(p):
            g.play(int(seq[t]))
        assert not g.done, (fidx[i], row[i], p)
        for name, val in zip(cols, (g.cells.copy(), g.macro.copy(), g.next_board, g.player,
                                    empties_in_open_boards(g.cells, g.macro),
                                    int(fidx[i]) * (1 << 20) + int(row[i]), int(fidx[i]), int(row[i]))):
            cols[name].append(val)
    out = {k: np.array(v) for k, v in cols.items()}
    out["cells"] = out["cells"].astype(np.int8)
    out["macro"] = out["macro"].astype(np.int8)
    return out, int(alive.size)


def solve_all(pos: dict, max_nodes: int, processes: int, rule: str):
    args = [(pos["cells"][i], pos["macro"][i], int(pos["next_board"][i]), int(pos["player"][i]), max_nodes)
            for i in range(len(pos["player"]))]
    fn = partial(solve_children_bounded, rule=rule)
    if processes <= 1:
        return [fn(a) for a in args]
    with Pool(processes) as pool:
        return pool.map(fn, args, chunksize=1)


def graded_set(pos: dict, solved: list, ply: int, meta: dict, rule: str) -> EndgameSet:
    """The complete positions of one ply as an EndgameSet, so tools/endgame.py's grader can score them
    unchanged. The set's own rule is the rule its exact values were solved under: uttt.endgame.evaluate
    refuses to grade it under any other (endgame.py:275-276)."""
    idx = [i for i, (v, child, _, ok) in enumerate(solved) if ok]
    exact = np.array([solved[i][0] for i in idx], dtype=np.int8)
    child = np.stack([solved[i][1] for i in idx]) if idx else np.zeros((0, 81), dtype=np.int8)
    return EndgameSet(pos["cells"][idx], pos["macro"][idx], pos["next_board"][idx].astype(np.int8),
                      pos["player"][idx].astype(np.int8), exact, child, pos["empties"][idx], pos["game_id"][idx],
                      np.full(len(idx), ply, dtype=np.int64),
                      dict(meta, name=f"ply {ply}, complete coverage", rule=rule))


def position_rows(pos: dict, solved: list, ply: int, es: EndgameSet | None, moves: np.ndarray | None,
                  regret: np.ndarray | None) -> dict:
    """One ply of the per-position table: every sampled position, complete or not (M2 §7e M2 row 16).

    complete=False rows carry nodes spent and nothing else: move -1, optimal -1, regret NaN, and a child
    row of NULL_ROW (-3) throughout — distinct from ILLEGAL (-2), which marks an illegal move in a
    complete row.

    `moves` and `regret` are the grader's own, both out of the one uttt.endgame.evaluate call (its
    _per["move"] and _per["regret"]), so the recorded move is by construction the move the recorded
    regret was computed from. The assertion at the end of this function is that identity, checked."""
    n = len(pos["player"])
    ok = np.array([s[3] for s in solved], dtype=bool)
    where = np.full(n, -1, dtype=np.int64)
    where[np.flatnonzero(ok)] = np.arange(int(ok.sum()))  # row of this position in the graded set
    child = np.full((n, 81), NULL_ROW, dtype=np.int8)
    root = np.full(n, NULL_ROW, dtype=np.int8)
    mv = np.full(n, -1, dtype=np.int16)
    opt = np.full(n, -1, dtype=np.int8)
    reg = np.full(n, np.nan, dtype=np.float32)
    for i in range(n):
        if not ok[i]:
            continue
        root[i] = np.int8(solved[i][0])
        child[i] = solved[i][1]
        if moves is not None:
            mv[i] = np.int16(moves[where[i]])
            reg[i] = np.float32(regret[where[i]])
            opt[i] = np.int8(regret[where[i]] == 0)
    assert es is None or int(ok.sum()) == es.n, (int(ok.sum()), None if es is None else es.n)
    assert bool((child[ok] >= ILLEGAL).all()), "a complete position produced a NULL child value"
    if moves is not None and ok.any():  # regret == exact_root_value - child_values[move], on every complete row
        rows_ok = np.flatnonzero(ok)
        want = root[rows_ok].astype(np.int64) - child[rows_ok, mv[rows_ok]].astype(np.int64)
        assert np.array_equal(reg[rows_ok].astype(np.int64), want), \
            f"ply {ply}: the recorded move and regret are not each other's ({int((reg[rows_ok] != want).sum())} rows)"
    return {"ply": np.full(n, ply, dtype=np.int16),
            "file_index": pos["file_index"].astype(np.int32), "game_row": pos["game_row"].astype(np.int64),
            "game_id": pos["game_id"].astype(np.int64), "empties": pos["empties"].astype(np.int64),
            "complete": ok, "nodes": np.array([s[2] for s in solved], dtype=np.int64),
            "exact_root_value": root, "child_values": child, "move": mv, "optimal": opt, "regret": reg}


HEADER = (f"{'ply':>4s} {'alive':>7s} {'sampled':>7s} {'complete coverage':>26s} {'nodes med':>11s} {'nodes p90':>11s} "
          f"{'optimal %':>18s} {'regret':>18s} {'incompl':>8s} {'s':>6s}")
LEGEND = ("(complete coverage = every legal child's exact value obtained inside the shared budget — stricter than "
          "proving the root's value)\n"
          "(coverage: conditional on alive, 95 % Wilson | nodes, optimal, regret: conditional on complete; "
          "optimal Wilson, regret cluster bootstrap)")


def format_row(d: dict) -> str:
    """One ply of the JSON as a table line; the legend says which column is conditional on what."""
    def num(key, fmt, scale=1.0):
        v = d[key]
        return "-" if v is None else format(scale * v, fmt)

    def ci(key, fmt, scale=1.0):
        v, c = d[key], d[key.replace("_conditional_", "_ci_conditional_")]
        if v is None:
            return "-"
        if c is None:
            return f"{scale * v:{fmt}} [n/a]"
        return f"{scale * v:{fmt}} [{scale * c[0]:{fmt}},{scale * c[1]:{fmt}}]"

    f, c = d["fraction_complete_coverage_conditional_on_alive"], d["fraction_complete_coverage_ci_conditional_on_alive"]
    cov = "-" if f is None else f"{100 * f:5.1f} % [{100 * c[0]:5.1f},{100 * c[1]:5.1f}] ({d['n_complete']})"
    return (f"{d['ply']:4d} {d['games_alive_at_ply']:7d} {d['positions_sampled_conditional_on_alive']:7d} {cov:>26s} "
            f"{num('median_nodes_conditional_on_complete', ',.0f'):>11s} "
            f"{num('p90_nodes_conditional_on_complete', ',.0f'):>11s} "
            f"{ci('search_optimal_move_rate_conditional_on_complete', '5.1f', 100):>18s} "
            f"{ci('search_mean_regret_conditional_on_complete', '5.3f'):>18s} "
            f"{d['incomplete_count_conditional_on_alive']:8d} {d['seconds']:6.1f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="run directory; its games/games_*.npz are the population")
    ap.add_argument("--net", required=True, help="checkpoint whose search is graded on the covered positions")
    ap.add_argument("--plies", type=int, nargs=2, default=[40, 70], metavar=("P0", "P1"))
    ap.add_argument("--per_ply", type=int, default=500)
    ap.add_argument("--max_nodes", type=float, default=1e8, help="node budget per position, shared by it and all its children")
    ap.add_argument("--sims", type=int, default=256)
    ap.add_argument("--last", type=int, default=20, help="use the last N game files of the run (0 = all)")
    ap.add_argument("--processes", type=int, default=8)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule the solver and the graded search run under")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", default="runs/plan7/J4_frontier.json")
    a = ap.parse_args()
    rule = check_rule(a.rule)
    max_nodes = int(a.max_nodes)
    device = torch.device(a.device)
    rng = np.random.default_rng(a.seed)
    out = tag_path(a.out, rule)
    pos_out = os.path.splitext(out)[0] + "_positions.npz"

    names, moves, fidx, row, length = load_corpus(a.run, a.last)
    cfg_path = os.path.join(a.run, "config.json")
    corpus_rule = json.load(open(cfg_path)).get("rule", "count") if os.path.exists(cfg_path) else None
    fe = FusedEvaluator(load_checkpoint(a.net, device), device)
    meta = {"run": a.run, "net": a.net, "corpus_files": names, "games": int(len(length)), "plies": a.plies,
            "per_ply": a.per_ply, "max_nodes": max_nodes, "sims": a.sims, "seed": a.seed, "processes": a.processes,
            "boot": a.boot, "device": str(device), "rule": rule, "corpus_rule": corpus_rule,
            "built": time.strftime("%Y-%m-%d %H:%M"), "positions_npz": os.path.basename(pos_out),
            "alive_at_ply": "the game's length exceeds the ply, so a position with a move to make exists there",
            "complete_coverage": "the exact value of the position AND of every legal child was obtained within one "
                                 "shared budget of max_nodes nodes: complete legal-action value coverage within the "
                                 "budget. It is stricter than root solvability — the root's value alone can follow "
                                 "from a cutoff that never values the other children — and it is what grading a "
                                 "chosen move against its alternatives needs (M2, PLAN7 §7e M2 row 16)",
            "node_convention": "a node is one recursive entry of the budgeted kernel (uttt.solver._negamax_bounded); a "
                               "child that is terminal after the move is decided directly in solve_children_bounded and "
                               "costs zero counted nodes (uttt/solver.py:255-263). The budget bounds search work, not "
                               "wall time",
            "grading": "uttt.endgame.evaluate, the grader of tools/endgame.py eval: action regret against the exact "
                       "child values and optimal-move rate, on the plain (not symmetry-averaged) evaluator",
            "intervals": "the coverage fraction and the optimal-move rate carry 95 % Wilson intervals (boundary-safe, "
                         "and not zero-width on an all-success sample the way a percentile bootstrap of [1,...,1] is); "
                         "mean regret keeps the cluster bootstrap over source games, and reports no interval at all "
                         "where the regret sample is degenerate rather than a zero-width one (M2 §7e M2 row 4)",
            "clusters": "within a ply every game contributes at most one position, so that cluster bootstrap is an "
                        "ordinary one and Wilson applies to the two proportions directly; ACROSS plies the same game "
                        "recurs, so the plies are not independent of each other and any across-ply comparison (a "
                        "difference between plies, a fitted curve, a joint interval) needs game-linked resampling over "
                        f"the per-position table {os.path.basename(pos_out)}, which carries game_id for that purpose",
            "positions_table": "every sampled position, complete or not: ply, file_index (into corpus_files), game_row, "
                               "game_id (the cluster id), empties, complete, nodes, exact_root_value, child_values "
                               "(81 int8: the exact value after each legal move, ILLEGAL=-2 where illegal, the whole "
                               "row NULL=-3 where the position did not complete), move (the graded search's own choice, "
                               "taken from the grader's per-position record, -1 where not graded), optimal (1/0, -1 "
                               "where not graded), regret (NaN where not graded). move and regret come out of the SAME "
                               "search: regret == exact_root_value - child_values[move] holds on every complete row by "
                               "construction and is asserted. Saved so that later joint uncertainty calculations need "
                               "no recomputation",
            "warning": "the covered subset is the easy end of a ply and gets easier as the budget binds; every number "
                       "below is conditional as its name says, and 'solved from ply N' does not follow from any of them"}
    print(f"{a.run}: {len(length)} games in {len(names)} files ({names[0]}..{names[-1]}); "
          f"grading {a.net} at {a.sims} sims on {device}", flush=True)
    print(f"plies {a.plies[0]}-{a.plies[1]}, {a.per_ply} positions per ply, budget {max_nodes:,} nodes per position, "
          f"{a.processes} solver processes, rule {rule}"
          + (f" (corpus trained under {corpus_rule})" if corpus_rule and corpus_rule != rule else ""), flush=True)
    print("\n" + HEADER)
    print(LEGEND)
    rows, table = [], []
    for p in range(a.plies[0], a.plies[1] + 1):
        t = time.perf_counter()
        pos, n_alive = positions_at_ply(moves, fidx, row, length, p, a.per_ply, rng, rule)
        n = len(pos.get("player", ()))
        solved = solve_all(pos, max_nodes, a.processes, rule) if n else []
        ok = np.array([s[3] for s in solved], dtype=bool) if n else np.zeros(0, dtype=bool)
        nodes = np.array([s[2] for s in solved], dtype=np.int64) if n else np.zeros(0, dtype=np.int64)
        d = {"ply": p,
             "games_alive_at_ply": n_alive,
             "positions_sampled_conditional_on_alive": n,
             "fraction_complete_coverage_conditional_on_alive": float(ok.mean()) if n else None,
             "fraction_complete_coverage_ci_conditional_on_alive": wilson(int(ok.sum()), n) if n else None,
             "n_complete": int(ok.sum()),
             "incomplete_count_conditional_on_alive": int(n - ok.sum()),
             "finite_population_note": None,
             "median_nodes_conditional_on_complete": float(np.median(nodes[ok])) if ok.any() else None,
             "p90_nodes_conditional_on_complete": float(np.quantile(nodes[ok], 0.9)) if ok.any() else None,
             "nodes_spent_total": int(nodes.sum()),
             "search_optimal_move_rate_conditional_on_complete": None,
             "search_optimal_move_rate_ci_conditional_on_complete": None,
             "search_mean_regret_conditional_on_complete": None,
             "search_mean_regret_ci_conditional_on_complete": None,
             "search_mean_regret_ci_note": None,
             "median_empties_conditional_on_complete": float(np.median(pos["empties"][ok])) if ok.any() else None,
             "seconds": None}
        if n and n == n_alive:
            d["finite_population_note"] = (
                "positions_sampled == games_alive_at_ply: the whole alive set at this ply was measured, so the "
                "coverage fraction is a census of this corpus's alive games at this ply and carries no sampling "
                "error with respect to it. The Wilson interval beside it is the interval for the wider population "
                "of games this checkpoint's self-play could have generated — read it as that or not at all.")
        if ok.any():
            es = graded_set(pos, solved, p, meta, rule)
            res = evaluate(fe, es, device, sims=[a.sims], n_boot=a.boot, symmetrise=False, rule=rule)
            r = res["rows"][-1]
            assert r["name"] == f"search {a.sims} sims", r["name"]
            per_reg = r["_per"]["regret"]
            d["search_optimal_move_rate_conditional_on_complete"] = r["optimal"]
            d["search_optimal_move_rate_ci_conditional_on_complete"] = wilson(int((per_reg == 0).sum()), len(per_reg))
            d["search_mean_regret_conditional_on_complete"] = r["regret"]
            if per_reg.min() == per_reg.max():
                d["search_mean_regret_ci_note"] = (
                    f"every regret in the sample is {per_reg[0]:g}: the percentile bootstrap of a degenerate sample is "
                    "zero-width, which is an artifact of resampling identical values and not population certainty. No "
                    "interval is reported; the optimal-move rate's Wilson interval is the uncertainty statement here.")
            else:
                d["search_mean_regret_ci_conditional_on_complete"] = list(r["regret_ci"])
            # The graded search's own moves, out of the same evaluate() call as the regret above
            # (endgame.py's _per["move"]). This used to be a SECOND search whose move was paired with the
            # first search's regret, with disagreements only warned about (M2 rebuttal (c)).
            table.append(position_rows(pos, solved, p, es, r["_per"]["move"], per_reg))
        elif n:
            table.append(position_rows(pos, solved, p, None, None, None))
        d["seconds"] = round(time.perf_counter() - t, 1)
        rows.append(d)
        print(format_row(d), flush=True)
    meta["chosen_move_regret_mismatches"] = 0  # kept for the JSONs already written under the old scheme
    meta["chosen_move_regret_mismatches_note"] = (
        "0 by construction, not by measurement: the recorded move IS the graded move (endgame.evaluate's "
        "_per[\"move\"]), so there is no second search to disagree with. Earlier files carry a counted value "
        "from when the move came from a second search of the same positions (M2 rebuttal (c))")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as fh:
        json.dump({"meta": meta, "plies": rows}, fh, indent=1)
    if table:
        cat = {k: np.concatenate([t[k] for t in table]) for k in table[0]}
        np.savez_compressed(pos_out, corpus_files=np.array(names), meta=np.array(json.dumps(meta)), **cat)
        print(f"\nwrote {out} and {pos_out} ({len(cat['ply'])} positions)")
    else:
        print(f"\nwrote {out} (no positions sampled: no per-position table)")


if __name__ == "__main__":
    main()
