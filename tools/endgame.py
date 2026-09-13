"""Frozen exact-label endgame set: build it once from a game corpus, then score checkpoints on it.

    .venv/Scripts/python.exe tools/endgame.py build --corpus runs/v2a --last 5 --per_stratum 125 --out suites/endgame_v1.npz
    .venv/Scripts/python.exe tools/endgame.py build --corpus runs/deep8_c1_300 --last 20 --split dev,test --out suites/endgame_v2
    .venv/Scripts/python.exe tools/endgame.py eval runs/v2b/net_0150.pt [--sims 32,64,256] [--rollout 100000] [--device cuda:1]

Metrics (uttt.endgame): WDL-argmax accuracy, Brier, log-loss of the value head; 3-way accuracy of scalar
values (for continuity with tools/endgame_accuracy.py); action regret (exact value lost by the chosen
move, in game-value units) and optimal-move rate; 95 % CIs from a cluster bootstrap over source games.

--rule count|draw: a set is SOLVED under one rule, records it, and takes a "_draw" tag in its file name;
eval refuses a rule the set was not solved for, because the exact labels would then be wrong (PLAN7 §5 K1).
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.endgame import EndgameSet, build_set, evaluate, evaluate_rollout, format_breakdown, format_report  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.rules import RULES, tag_path  # noqa: E402

DEFAULT_SET = "suites/endgame_v1.npz"


def load(path, device):
    net = load_checkpoint(path, device)
    return FusedEvaluator(net, device)


def cmd_build(a) -> None:
    parts = [p for p in a.split.split(",") if p]
    stem = os.path.splitext(a.out)[0]
    outs = {p: tag_path(f"{stem}_{p}.npz", a.rule) for p in parts} if parts else {"": tag_path(a.out, a.rule)}
    for out in outs.values():  # suites are frozen: a build never overwrites an existing yardstick
        if os.path.exists(out):
            sys.exit(f"refusing to overwrite {out} (a rebuilt suite is a new, incomparable one; pick a new name)")
    for part, out in outs.items():
        es = build_set(a.corpus, a.last, a.per_stratum, a.per_game, a.min_empty, a.max_empty, a.max_solve, a.processes, a.seed,
                       split=part, split_seed=a.split_seed, rule=a.rule)
        es.save(out)
        print(f"wrote {out}: {es.n} positions solved under rule {es.rule}; exact W/D/L for the mover "
              f"{(es.exact == 1).mean():.3f}/{(es.exact == 0).mean():.3f}/"
              f"{(es.exact == -1).mean():.3f}; {len(set(es.game_id.tolist()))} source games")
        for k, v in es.meta["strata_counts (bucket -> [W_X, W_O, D_X, D_O, L_X, L_O])"].items():
            print(f"  empties {k}: {v}")


def cmd_eval(a) -> None:
    device = torch.device(a.device)
    es = EndgameSet.load(a.set)
    print(f"{a.set}: {es.n} positions solved under rule {es.rule}, {len(set(es.game_id.tolist()))} source games, W/D/L {(es.exact == 1).mean():.3f}/"
          f"{(es.exact == 0).mean():.3f}/{(es.exact == -1).mean():.3f}; free-move positions {(es.next_board < 0).mean():.3f}")
    fe = load(a.checkpoint, device)
    t = time.perf_counter()
    res = evaluate(fe, es, device, sims=[int(s) for s in a.sims.split(",") if s], n_boot=a.boot, rule=a.rule)
    extra = []
    if a.rollout:
        from uttt.rollout import RolloutPlayer

        t2 = time.perf_counter()
        row = evaluate_rollout(RolloutPlayer(a.rollout, rule=a.rule).act, es, a.boot, rule=a.rule)
        row["name"] = f"rollout UCT {a.rollout} playouts"
        extra.append(row)
        print(f"rollout anchor scored in {time.perf_counter() - t2:.0f}s")
    print(f"\n{a.checkpoint} on {es.meta['name']} under rule {a.rule}  [{time.perf_counter() - t:.0f}s]")
    print(format_report(es, res, extra))
    rows = [res["rows"][0], res["rows"][-1]] + extra
    print()
    print(format_breakdown(es, [res["rows"][0]] + ([res["rows"][1]] if len(res["rows"]) > 1 and "wdl_acc" in res["rows"][1] else []), "wdl_acc", "WDL accuracy %"))
    print()
    print(format_breakdown(es, rows, "regret", "action regret"))
    print()
    print(format_breakdown(es, rows, "optimal", "optimal-move %"))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--corpus", default="runs/v2a")
    b.add_argument("--last", type=int, default=5)
    b.add_argument("--per_stratum", type=int, default=125)
    b.add_argument("--per_game", type=int, default=2)
    b.add_argument("--min_empty", type=int, default=6)
    b.add_argument("--max_empty", type=int, default=16)
    b.add_argument("--max_solve", type=int, default=15000)
    b.add_argument("--processes", type=int, default=8)
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--out", default=DEFAULT_SET)
    b.add_argument("--split", default="", help='"dev,test": build one set per half of the source games (split before solving); '
                   "--out is then a stem, e.g. suites/endgame_v2 -> suites/endgame_v2_dev.npz + _test.npz")
    b.add_argument("--split_seed", type=int, default=0)
    b.add_argument("--rule", choices=RULES, default="count", help="terminal rule the set is solved under; a non-count rule tags the file name")
    e = sub.add_parser("eval")
    e.add_argument("checkpoint")
    e.add_argument("--set", default=DEFAULT_SET)
    e.add_argument("--sims", default="32,64,256")
    e.add_argument("--rollout", type=int, default=0, help="also score the rollout anchor with this many playouts per move")
    e.add_argument("--boot", type=int, default=2000)
    e.add_argument("--rule", choices=RULES, default="count", help="terminal rule to evaluate under; must be the rule the set was solved under")
    e.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    {"build": cmd_build, "eval": cmd_eval}[a.cmd](a)


if __name__ == "__main__":
    main()
