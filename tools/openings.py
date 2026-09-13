"""Fixed opening suite: build it once, inspect it, and run paired (colour-swapped) matches on it.

    .venv/Scripts/python.exe tools/openings.py build --corpus runs/v2a --natural 250 --random 250 --out suites/openings_v1.npz
    .venv/Scripts/python.exe tools/openings.py show suites/openings_v1.npz
    .venv/Scripts/python.exe tools/openings.py match --a runs/v2b/net_0150.pt --b runs/dev1/net_0200.pt --sims 64 [--cap 100] [--out x.json]

--a / --b may also be "uct" (uniform prior, our search), "rollout" (independent Numba UCT with random
playouts; --x_sims = playouts per move, e.g. 100000) or "random". --cap N keeps the first N openings
of every sub-suite (train2 evaluates on such a subset). Scores are A's; CIs are bootstrapped over opening pairs.
--a_sym / --a_canon wrap A's net in the 8-way symmetry average / the one-call canonical evaluator (uttt.symmetry).
--rule count|draw is the rule the match is PLAYED under (both players' trees and the games); it is never
read off a checkpoint, so a count-trained net can be played under draw with that stated (PLAN7 §5 K1).
The suite itself is opening positions and is rule-free.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.arena import PhasedSearchPlayer, RandomPlayer, SearchPlayer  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import UniformEvaluator, load_checkpoint  # noqa: E402
from uttt.openings import Suite, build_suite, format_report, per_opening_records, play_paired, summarize  # noqa: E402
from uttt.rollout import RolloutPlayer  # noqa: E402
from uttt.rules import RULES, tag_path  # noqa: E402
from uttt.search import SearchConfig  # noqa: E402
from uttt.symmetry import CanonicalEvaluator, SymmetryAveragedEvaluator  # noqa: E402
from uttt.tablebase import TablebaseEvaluator  # noqa: E402

DEFAULT_SUITE = "suites/openings_v1.npz"


def load(path, device):
    if path == "uct":
        return UniformEvaluator(device)
    net = load_checkpoint(path, device)
    return FusedEvaluator(net, device)


def player(spec, sims, n, device, mode="gumbel", graph=True, c_scale=0.1, sym=False, tb=False, canon=False, rule="count"):
    """spec: checkpoint path | "uct" | "rollout" | "random" | "surrogate:<file>". sims: int, or a phase schedule
    "0:32,24:96" (sims from ply). sym: evaluate all 8 D4 images and average (uttt.symmetry; 8x the inference cost).
    canon: one-call canonical evaluator (exactly equivariant at ~1.03x the cost; PLAN6 F1).
    tb: wrap the evaluator in the one-open-board tablebase (exact value and move where one board is open)."""
    if spec.startswith("surrogate:") and rule != "count":
        # uttt.surrogate is a learned model OF THE COUNT-RULE GAME, distilled from count-rule search; it has
        # no terminal logic of its own to re-rule and would answer count-rule questions inside a draw-rule
        # game. Refused rather than silently mixed (M2 row 6).
        raise ValueError(f"a surrogate player is a learned model of the count-rule game and cannot be played under "
                         f"rule {rule!r}: distil a {rule}-rule surrogate first, or play it under --rule count")
    if spec == "random":
        return RandomPlayer(device)

    def ev():
        if spec.startswith("surrogate:"):
            from uttt.surrogate import SurrogateEvaluator

            e = SurrogateEvaluator.load(spec[len("surrogate:"):], device)
        else:
            e = load(spec, device)
            e = SymmetryAveragedEvaluator(e) if sym else CanonicalEvaluator(e) if canon else e
        return TablebaseEvaluator(e, rule=rule) if tb else e
    if isinstance(sims, str) and ":" in sims:
        sched = {int(k): int(v) for k, v in (x.split(":") for x in sims.split(","))}
        cfg = SearchConfig(n_sims=max(sched.values()), mode=mode, gumbel_scale=0.0, c_scale=c_scale, cuda_graph=graph and device.type == "cuda", depth_cap=24)
        return PhasedSearchPlayer(ev(), n, cfg, sched, device, rule=rule)
    sims = int(sims)
    if spec == "rollout":  # independent UCT + random-playout anchor; sims = playouts per move
        return RolloutPlayer(playouts=sims, rule=rule)
    cfg = SearchConfig(n_sims=sims, mode=mode, gumbel_scale=0.0, c_scale=c_scale, cuda_graph=graph and device.type == "cuda", depth_cap=min(sims, 24))
    return SearchPlayer(ev(), n, cfg, device, rule=rule)


def cmd_build(a) -> None:
    suite = build_suite(a.corpus, a.natural, a.random, a.plies, a.last, a.seed)
    suite.save(a.out)
    print(f"wrote {a.out}: {suite.counts()} ({suite.n} openings); natural ones from {suite.meta['corpus_games']} games of {a.corpus}")


def cmd_show(a) -> None:
    suite = Suite.load(a.suite)
    print(f"{a.suite}: {suite.counts()} ({suite.n} openings); meta: {json.dumps({k: v for k, v in suite.meta.items() if k != 'corpus_files'})}")
    for i, (name, seq) in enumerate(zip(suite.names, suite.sequences())):
        print(f"  {i:4d} {name:8s} {seq}")


def cmd_match(a) -> None:
    device = torch.device(a.device)
    torch.manual_seed(a.seed)
    suite = Suite.load(a.suite)
    if a.cap:
        suite = suite.subset(a.cap)
    a_sims, b_sims = a.a_sims or a.sims, a.b_sims or a.sims
    t = time.perf_counter()
    pa = player(a.a, a_sims, suite.n, device, a.mode, bool(a.graph), a.a_cscale, a.a_sym, a.a_tb, a.a_canon, a.rule)
    pb = player(a.b, b_sims, suite.n, device, a.mode, bool(a.graph), a.b_cscale, a.b_sym, a.b_tb, a.b_canon, a.rule)
    r = play_paired(pa, pb, suite, device, a.rule)
    s = summarize(r)
    tag = lambda sym, canon, tb: f"{' sym' if sym else ''}{' canon' if canon else ''}{' tb' if tb else ''}"  # noqa: E731
    print(f"paired suite {suite.meta['name']} ({suite.n} openings, {2 * suite.n} games) under rule {a.rule}: "
          f"A={a.a}@{a_sims}{tag(a.a_sym, a.a_canon, a.a_tb)} vs "
          f"B={a.b}@{b_sims}{tag(a.b_sym, a.b_canon, a.b_tb)}  "
          f"[{time.perf_counter() - t:.0f}s]")
    print(format_report(s))
    for name, p in (("A", pa), ("B", pb)):
        e = getattr(getattr(p, "mcts", None), "eval", None)
        if isinstance(e, TablebaseEvaluator):
            print(f"  {name}: tablebase hit {e.k1_hits} of {e.calls} evaluated positions ({100 * e.k1_hits / max(e.calls, 1):.1f} %)")
    if a.out:
        rec = {"rule": a.rule, "suite": {k: v for k, v in suite.meta.items() if k != "ids"}, "a": a.a, "a_sims": a_sims, "b": a.b, "b_sims": b_sims,
               "a_sym": a.a_sym, "b_sym": a.b_sym, "a_canon": a.a_canon, "b_canon": a.b_canon, "a_tb": a.a_tb, "b_tb": a.b_tb,
               "mode": a.mode, "summary": s, "openings": per_opening_records(r)}
        out = tag_path(a.out, a.rule)
        with open(out, "w") as f:
            json.dump(rec, f, indent=1)
        print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--corpus", default="runs/v2a")
    b.add_argument("--last", type=int, default=20, help="use the last N game files of the corpus")
    b.add_argument("--natural", type=int, default=250)
    b.add_argument("--random", type=int, default=250)
    b.add_argument("--plies", type=int, default=4)
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--out", default=DEFAULT_SUITE)
    s = sub.add_parser("show")
    s.add_argument("suite", nargs="?", default=DEFAULT_SUITE)
    m = sub.add_parser("match")
    m.add_argument("--suite", default=DEFAULT_SUITE)
    m.add_argument("--cap", type=int, default=0, help="keep the first N openings of each sub-suite (0 = all)")
    m.add_argument("--a", required=True)
    m.add_argument("--b", required=True)
    m.add_argument("--sims", default="64")
    m.add_argument("--a_sims", default="", help='int, or a phase schedule like "0:32,24:96" (sims from ply)')
    m.add_argument("--b_sims", default="")
    m.add_argument("--mode", default="gumbel")
    m.add_argument("--a_cscale", type=float, default=0.1, help="Gumbel c_scale of A's play-time search (training default 0.1)")
    m.add_argument("--b_cscale", type=float, default=0.1)
    m.add_argument("--a_sym", action="store_true", help="A evaluates with symmetry averaging over the 8 D4 images (8x cost)")
    m.add_argument("--b_sym", action="store_true")
    m.add_argument("--a_canon", action="store_true", help="A evaluates with the one-call canonical (exactly equivariant) evaluator")
    m.add_argument("--b_canon", action="store_true")
    m.add_argument("--a_tb", action="store_true", help="A uses the one-open-board tablebase as a terminal lookup")
    m.add_argument("--b_tb", action="store_true")
    m.add_argument("--rule", choices=RULES, default="count", help="terminal rule the match is PLAYED under (never inferred from a checkpoint)")
    m.add_argument("--device", default="cuda:0")
    m.add_argument("--graph", type=int, default=1)
    m.add_argument("--seed", type=int, default=0)
    m.add_argument("--out", default="")
    a = ap.parse_args()
    {"build": cmd_build, "show": cmd_show, "match": cmd_match}[a.cmd](a)


if __name__ == "__main__":
    main()
