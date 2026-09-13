"""One frozen set of natural positions, both nets under both rules (PLAN7 §5 item 3, and the paired half
of item 2). Written and frozen before K1's final checkpoint exists (§7e M2-R row R9).

    .venv/Scripts/python.exe tools/common_positions.py \
      --corpus_a runs/deep8_c1_300_e8_draw --corpus_b runs/deep10_c1_300 \
      --net_a runs/deep8_c1_300_e8_draw/net_0300.pt --net_b runs/deep8_c1_300_e8/net_0300.pt \
      --n 15000 --sims 256 --device cuda:1 --out runs/plan7/K1_common_positions.json

The rule's effect on the *value* has to be read on identical inputs, or it is confounded with the
positions each net's own play produces. So: one set of natural positions (15 000 from each of two
corpora, 30 000 in all -- M2 rebuttal R1's size, below which claims 8 and 13 are unresolved by
construction), and a 2 x 2 matrix of cells -- each net, under each rule -- evaluated on all of them.
Every cell's rule is an explicit argument; nothing is inferred from a checkpoint. The corpora's own
generating rule is read (tools/corpus_stats.py's corpus_rule) and recorded beside their positions, but
it refuses nothing: a position is a position, and reading count-play positions under `draw` is exactly
the comparison item 3 asks for.

What is computed, per cell (net x rule):
  * the raw value head and the 256-sim search value, mover's perspective (tools/value_decomp.py's
    `values`: one BatchedSearch per batch, gumbel_scale 0, depth_cap min(sims, 24));
  * tools/freemove.py's prespecified regression of each on the design matrix (free move, ply, ply^2,
    macro score = the count margin, open boards, empties, is_X, macro threats for / against) and its
    ownership-by-class model, OLS with cluster-robust standard errors by source game.
And, across cells:
  * the PAIRED differences. For each net, Delta = beta_draw - beta_count, estimated as the regression of
    (v_draw - v_count) on the same design matrix, clustered by game. One regression, not a difference of
    two: the two cells share every regressor and every cluster, so the paired residual is what carries
    the rule's effect, and its interval is the paired one (M2 rows 2, 12; rebuttal R1, R13).
  * the ACROSS-NET paired differences, Delta = beta(net A) - beta(net B) under each rule, on the same
    positions and the same clusters. These exist because the raw value head cannot see the rule: an
    evaluator is a function of the position alone, so for ONE net the raw draw-minus-count difference is
    identically zero and its interval is zero-wide -- a tautology, not evidence of invariance. Claim 16's
    "raw head" half is therefore only readable as a difference between the two NETS, and that is what this
    block is. The tool says so in place of a verdict wherever a paired difference is identically zero.
  * the DIFFERENCE IN DIFFERENCES, net A's paired Delta minus net B's -- NOT a pre-registered reading, and
    printed as a control, not as a verdict. Smoke-tested on two COUNT-trained nets (2 000 positions from each
    of two count corpora, 64 sims), each net's paired count-margin Delta came out at -0.0196 with a 95 %
    interval of [-0.0271, -0.0122]: the rule change alone moves that coefficient, because under `draw` a
    count-decided terminal backs up 0 instead of +-1 and every position with a positive count margin is pulled
    towards zero. A count-trained control therefore ALREADY satisfies the registered "established decrease"
    (upper endpoint <= -0.005) by a factor of four. The registered verdict is still printed, unchanged; this
    block is what separates the draw net's training from the search's arithmetic.
  * the exact minimax value of every position with <= 14 empties in open boards, under both rules
    (uttt.solver.solve_batch in a process pool), and the fraction whose exact value changes -- the rule's
    effect on the game itself, with no net in it at all. Reported by source corpus and pooled; every
    position of the subset is solved completely under both rules, so the "intersection solved under both"
    (M2 row 17) is the whole subset, and that is stated rather than assumed.

Verdicts are §5 item 2's, applied to the paired interval and printed for every subset:
  claims 8 (free move) and 13 (macro threats): invariant if the whole 95 % interval lies inside
    (-0.03, +0.03), dependent if it lies wholly beyond either bound, unresolved otherwise;
  claim 16 (the count margin): an established decrease if the upper endpoint <= -0.005, contradicted if
    the interval lies wholly above -0.005, unresolved otherwise. The secondary form -- the draw cell's own
    coefficient against [-0.015, +0.015] -- is printed beside it, marked as the secondary.
Unresolved means insufficient precision, never an inconvenient result.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from functools import partial
from multiprocessing import Pool

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from corpus_stats import corpus_rule  # noqa: E402
from freemove import macro_threats, ols_cluster, sample_positions  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.rules import RULES  # noqa: E402
from uttt.solver import empties_in_open_boards, solve_batch  # noqa: E402
from value_decomp import values as cell_values  # noqa: E402

CENTRE, CORNERS, EDGES = [4], [0, 2, 6, 8], [1, 3, 5, 7]
# tools/freemove.py:127 and :140-141, verbatim and in their order: this file fits freemove's model, so its
# column list is freemove's. freemove builds both matrices inline inside main(), so there is no design
# function to import; macro_threats(), ols_cluster() and sample_positions() are imported from it.
NAMES = ["intercept", "free_move", "ply/10", "(ply/10)^2", "macro_score", "open_boards", "empties/10", "is_X",
         "threats_for", "threats_against"]
OWN_NAMES = ["intercept", "free_move", "ply/10", "(ply/10)^2", "empties/10", "is_X", "threats_for", "threats_against",
             "full_boards", "centre_self", "centre_opp", "corners_self", "corners_opp", "edges_self", "edges_opp"]
# The four coefficients the paired differences are read on, and the claim each belongs to (PLAN7 §5 item 2).
PAIRED_KEYS = {"free_move": 8, "threats_for": 13, "threats_against": 13, "macro_score": 16}


# ---------------------------------------------------------------- sampling and design

def sample_corpus(run: str, last: int, per_game: int, ply_lo: int, ply_hi: int, n: int, seed: int,
                  override: str = "") -> tuple[list, str, list[str]]:
    """freemove.sample_positions over a run's last `last` game files: <= per_game positions per game from
    plies [ply_lo, ply_hi], the game not over, the source game kept for clustering. The corpus's own
    generating rule is established, never guessed (corpus_stats.corpus_rule), and is what the replay uses;
    it decides no terminal value here, since every sampled position is short of the end."""
    src = corpus_rule(run, override)
    files = sorted(glob.glob(os.path.join(run, "games", "games_*.npz")))[-last:]
    if not files:
        sys.exit(f"{run}/games holds no games_*.npz")
    rows = sample_positions(files, per_game, ply_lo, ply_hi, n, np.random.default_rng(seed), src)
    return rows[:n], src, [os.path.basename(f) for f in files]


def features(rows: list, gid_offset: int) -> dict:
    """The sampled rows as arrays. gid_offset keeps two corpora's game ids from colliding in one cluster
    variable (freemove numbers games from 0 within a corpus)."""
    return {"gid": np.array([r[0] for r in rows], dtype=np.int64) + gid_offset,
            "ply": np.array([r[1] for r in rows], dtype=np.float64),
            "cells": np.stack([r[2] for r in rows]).astype(np.int8),
            "macro": np.stack([r[3] for r in rows]).astype(np.int8),
            "next_board": np.array([r[4] for r in rows], dtype=np.int8),
            "player": np.array([r[5] for r in rows], dtype=np.int8)}


def design(F: dict) -> tuple[np.ndarray, np.ndarray, dict]:
    """(X, Xo, parts): freemove.py's two prespecified design matrices for these positions."""
    cells, macro, player, ply = F["cells"], F["macro"], F["player"], F["ply"]
    N = len(player)
    p = player.astype(np.int64)[:, None]
    free = (F["next_board"] < 0).astype(np.float64)
    score = ((macro == p).sum(1) - (macro == -p).sum(1)).astype(np.float64)
    open_b = (macro == 0).sum(1).astype(np.float64)
    empties = ((cells.reshape(N, 9, 9) == 0) & (macro == 0)[:, :, None]).sum((1, 2)).astype(np.float64)
    is_x = (player == 1).astype(np.float64)
    thr_for = np.array([macro_threats(macro[i], int(player[i])) for i in range(N)], dtype=np.float64)
    thr_against = np.array([macro_threats(macro[i], -int(player[i])) for i in range(N)], dtype=np.float64)
    X = np.column_stack([np.ones(N), free, ply / 10, (ply / 10) ** 2, score, open_b, empties / 10, is_x, thr_for, thr_against])
    own = lambda cls, who: (macro[:, cls] == who * p).sum(1).astype(np.float64)  # noqa: E731
    full = (macro == 2).sum(1).astype(np.float64)
    Xo = np.column_stack([np.ones(N), free, ply / 10, (ply / 10) ** 2, empties / 10, is_x, thr_for, thr_against, full,
                          own(CENTRE, 1), own(CENTRE, -1), own(CORNERS, 1), own(CORNERS, -1), own(EDGES, 1), own(EDGES, -1)])
    return X, Xo, {"free": free, "score": score, "empties": empties}


# ---------------------------------------------------------------- estimation and verdicts

def fit(X: np.ndarray, y: np.ndarray, gid: np.ndarray, names: list[str]) -> dict:
    """freemove.ols_cluster, packaged: coefficients, 95 % half-widths, interval endpoints, R^2."""
    beta, se, e = ols_cluster(X, y, gid)
    hw = 1.96 * se
    return {"r2": float(1 - e.var() / y.var()) if y.var() > 0 else 0.0,
            "degenerate": bool(np.all(y == 0)),  # an identically zero response: every interval is zero-wide
            "coef": dict(zip(names, beta.tolist())), "ci95": dict(zip(names, hw.tolist())),
            "interval": {n: [float(b - h), float(b + h)] for n, b, h in zip(names, beta, hw)}}


def verdict_equivalence(lo: float, hi: float, margin: float = 0.03) -> str:
    """Claims 8 and 13 (PLAN7 §5 item 2, as amended by M2-R R1 / R13)."""
    if lo > -margin and hi < margin:
        return "invariant"
    if hi <= -margin or lo >= margin:
        return "dependent"
    return "unresolved"


def verdict_decrease(lo: float, hi: float, margin: float = -0.005) -> str:
    """Claim 16, primary: the paired count-margin difference."""
    if hi <= margin:
        return "established decrease"
    if lo > margin:
        return "contradicted"
    return "unresolved"


def verdict_band(lo: float, hi: float, band: float = 0.015) -> str:
    """Claim 16, secondary: a net's own count-margin coefficient against [-band, +band]."""
    if lo >= -band and hi <= band:
        return "supported"
    if lo > band or hi < -band:
        return "contradicted"
    return "unresolved"


def paired_verdicts(rec: dict) -> dict:
    """Every paired coefficient of interest, with the verdict its claim's rule gives. A response that is
    identically zero gets no verdict: the interval is zero-wide for an arithmetic reason, and calling that
    "invariant" would dress a tautology as a finding."""
    out = {}
    for key, claim in PAIRED_KEYS.items():
        lo, hi = rec["interval"][key]
        if rec.get("degenerate"):
            v = "vacuous (the difference is identically zero)"
        else:
            v = verdict_decrease(lo, hi) if claim == 16 else verdict_equivalence(lo, hi)
        out[key] = {"claim": claim, "delta": rec["coef"][key], "interval": [lo, hi], "verdict": v}
    return out


# ---------------------------------------------------------------- the exact-value subset

def solve_subset(F: dict, keep: np.ndarray, processes: int, chunk: int = 64) -> dict:
    """Exact minimax values of the kept positions under both rules (uttt.solver.solve_batch in a pool).
    solve_children is complete, not bounded, so every kept position resolves under both rules and the
    intersection solved under both is the whole subset (M2 row 17)."""
    idx = np.flatnonzero(keep)
    if len(idx) == 0:
        return {r: np.zeros(0, dtype=np.int8) for r in RULES}
    args = [(F["cells"][idx[i:i + chunk]], F["macro"][idx[i:i + chunk]],
             F["next_board"][idx[i:i + chunk]], F["player"][idx[i:i + chunk]]) for i in range(0, len(idx), chunk)]
    out = {}
    with Pool(processes) as pool:
        for rule in RULES:
            res = pool.map(partial(solve_batch, rule=rule), args, chunksize=1)
            out[rule] = np.concatenate([v for v, _ in res])
    return out


# ---------------------------------------------------------------- reporting

def show_fit(label: str, rec: dict, names: list[str]) -> None:
    print(f"\n  {label} (R2 = {rec['r2']:.3f}):")
    for n in names:
        b, h = rec["coef"][n], rec["ci95"][n]
        star = " *" if abs(b) > h and n != "intercept" else ""
        print(f"    {n:16s} {b:+.4f} +- {h:.4f}{star}")


def show_paired(label: str, v: dict, what: str = "Delta = beta_draw - beta_count") -> None:
    print(f"  paired difference, {label} ({what}, cluster-robust by game):")
    for key, d in v.items():
        lo, hi = d["interval"]
        print(f"    claim {d['claim']:2d}  {key:16s} {d['delta']:+.4f}  95 % [{lo:+.4f}, {hi:+.4f}]   {d['verdict'].upper()}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus_a", required=True, help="run directory; its last --last game files")
    ap.add_argument("--corpus_b", required=True)
    ap.add_argument("--corpus_a_rule", choices=RULES, default="",
                    help="the rule corpus A was GENERATED under, when its directory records none")
    ap.add_argument("--corpus_b_rule", choices=RULES, default="")
    ap.add_argument("--net_a", required=True)
    ap.add_argument("--net_b", required=True)
    ap.add_argument("--last", type=int, default=20)
    ap.add_argument("--n", type=int, default=15000,
                    help="positions sampled from EACH corpus (M2-R R1: 15 000, i.e. 30 000 in all)")
    ap.add_argument("--per_game", type=int, default=5)
    ap.add_argument("--ply_lo", type=int, default=6)
    ap.add_argument("--ply_hi", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sims", type=int, default=256)
    ap.add_argument("--max_empty", type=int, default=14,
                    help="solve exactly every position with at most this many empties in open boards")
    ap.add_argument("--processes", type=int, default=8)
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", default="runs/plan7/K1_common_positions.json")
    a = ap.parse_args()
    t0 = time.perf_counter()

    # ---- the frozen position set
    corpora, Fs = {}, {}
    order = ["a", "b"]
    for k, run, override in (("a", a.corpus_a, a.corpus_a_rule), ("b", a.corpus_b, a.corpus_b_rule)):
        rows, src, files = sample_corpus(run, a.last, a.per_game, a.ply_lo, a.ply_hi, a.n, a.seed, override)
        Fs[k] = features(rows, gid_offset=order.index(k) * 10_000_000)
        corpora[k] = {"run": run, "generating_rule": src, "files": files, "positions": len(rows),
                      "games": int(len(np.unique(Fs[k]["gid"])))}
        print(f"corpus {k.upper()}: {len(rows)} positions from {corpora[k]['games']} games of {run} "
              f"(generated under {src}; {len(files)} game files, plies {a.ply_lo}-{a.ply_hi}, "
              f"<= {a.per_game} per game, seed {a.seed})", flush=True)
    F = {key: np.concatenate([Fs["a"][key], Fs["b"][key]]) for key in Fs["a"]}
    N = len(F["player"])
    src_of = np.concatenate([np.zeros(len(Fs["a"]["player"]), dtype=np.int8),
                             np.ones(len(Fs["b"]["player"]), dtype=np.int8)])
    X, Xo, parts = design(F)
    gid = F["gid"]
    # the design's `empties` column is uttt.solver.empties_in_open_boards, vectorised; check, do not assume
    for i in range(0, N, max(N // 50, 1)):
        assert int(parts["empties"][i]) == empties_in_open_boards(F["cells"][i], F["macro"][i]), i
    subsets = {"pooled": np.ones(N, dtype=bool), "corpus_a": src_of == 0, "corpus_b": src_of == 1}
    print(f"{N} positions in all; {len(np.unique(gid))} source games; free move {parts['free'].mean():.3f}; "
          f"design {len(NAMES) - 1} regressors + the ownership model's {len(OWN_NAMES) - 1}  "
          f"[{time.perf_counter() - t0:.0f}s]", flush=True)

    # ---- the exact-value subset (no net in it at all), before any CUDA context exists
    keep = parts["empties"] <= a.max_empty
    print(f"\nsolving the {int(keep.sum())} positions with <= {a.max_empty} empties in open boards under both rules "
          f"({a.processes} processes) ...", flush=True)
    exact = solve_subset(F, keep, a.processes)
    ki = np.flatnonzero(keep)
    changed = exact["count"] != exact["draw"]
    solved = {"max_empty": a.max_empty, "n": int(keep.sum()), "share_of_set": float(keep.mean()),
              "complete_under_both_rules": True, "by_subset": {}}
    print(f"solved in {time.perf_counter() - t0:.0f}s. Exact value for the mover (W/D/L) and the rule's effect:")
    for name, m in subsets.items():
        mk = m[ki]
        if not mk.any():
            continue
        ec, ed = exact["count"][mk], exact["draw"][mk]
        d = {"n": int(mk.sum()),
             "count": {"win": float((ec == 1).mean()), "draw": float((ec == 0).mean()), "loss": float((ec == -1).mean())},
             "draw": {"win": float((ed == 1).mean()), "draw": float((ed == 0).mean()), "loss": float((ed == -1).mean())},
             "changed": float(changed[mk].mean()),
             "win_to_draw": float(((ec == 1) & (ed == 0)).mean()),
             "loss_to_draw": float(((ec == -1) & (ed == 0)).mean()),
             "mean_value_count": float(ec.mean()), "mean_value_draw": float(ed.mean())}
        solved["by_subset"][name] = d
        print(f"  {name:9s} n={d['n']:6d}  count {d['count']['win']:.3f}/{d['count']['draw']:.3f}/{d['count']['loss']:.3f}"
              f"   draw {d['draw']['win']:.3f}/{d['draw']['draw']:.3f}/{d['draw']['loss']:.3f}"
              f"   changed {d['changed']:.3f}  (win->draw {d['win_to_draw']:.3f}, loss->draw {d['loss_to_draw']:.3f})")

    # ---- the 2 x 2 matrix of cells
    device = torch.device(a.device)
    z = {"cells": F["cells"], "macro": F["macro"], "next_board": F["next_board"], "player": F["player"]}
    idx = np.arange(N)
    nets = {"a": a.net_a, "b": a.net_b}
    vals: dict[tuple[str, str], dict] = {}
    print()
    for nk in order:
        fe = FusedEvaluator(load_checkpoint(nets[nk], device), device)
        for rule in RULES:
            raw, srch = cell_values(fe, z, idx, a.sims, device, rule=rule)
            vals[(nk, rule)] = {"raw": raw, "search": srch}
            print(f"  net {nk.upper()} under {rule:5s}: mean {a.sims}-sim search value {srch.mean():+.4f}, "
                  f"raw {raw.mean():+.4f}  [{time.perf_counter() - t0:.0f}s]", flush=True)
        del fe
    print("\nmean search value by cell (mover's perspective), and the draw - count difference per net:")
    for nk in order:
        c, d = vals[(nk, "count")]["search"].mean(), vals[(nk, "draw")]["search"].mean()
        print(f"  net {nk.upper()} ({nets[nk]}): count {c:+.4f}  draw {d:+.4f}  difference {d - c:+.4f}")

    # ---- the per-cell regressions
    cells_out: dict[str, dict] = {}
    for nk in order:
        for rule in RULES:
            rec = {}
            for label in ("search", "raw"):
                rec[label] = fit(X, vals[(nk, rule)][label], gid, NAMES)
                rec["own_" + label] = fit(Xo, vals[(nk, rule)][label], gid, OWN_NAMES)
            cells_out[f"{nk}|{rule}"] = rec
            print(f"\n=== net {nk.upper()} ({nets[nk]}) evaluated under rule {rule} -- {a.sims}-sim search, pooled set")
            show_fit("OLS of the search value, cluster-robust SE by game", rec["search"], NAMES)
            show_fit("OLS of the raw value, cluster-robust SE by game", rec["raw"], NAMES)
            show_fit("ownership-by-class model, search value", rec["own_search"], OWN_NAMES)

    # ---- the paired differences
    paired_out: dict[str, dict] = {}
    print("\n" + "=" * 104)
    print("PAIRED DIFFERENCES (PLAN7 sec. 5 item 2): Delta = beta_draw - beta_count, one regression of (v_draw - v_count)")
    print("on the same design matrix, cluster-robust by source game. Verdicts by sec. 5 item 2 rules:")
    print("  claims 8 / 13: invariant if the 95 % interval lies inside (-0.03, +0.03), dependent if wholly beyond, else unresolved")
    print("  claim 16     : established decrease if the upper endpoint <= -0.005, contradicted if wholly above it, else unresolved")
    for nk in order:
        paired_out[nk] = {"net": nets[nk]}
        for sub, m in subsets.items():
            paired_out[nk][sub] = {}
            for label in ("search", "raw"):
                dy = vals[(nk, "draw")][label] - vals[(nk, "count")][label]
                rec = fit(X[m], dy[m], gid[m], NAMES)
                rec["verdicts"] = paired_verdicts(rec)
                paired_out[nk][sub][label] = rec
            print(f"\n--- net {nk.upper()} ({nets[nk]}), {sub} (n = {int(m.sum())}, {len(np.unique(gid[m]))} games)")
            for label in ("search", "raw"):
                rec = paired_out[nk][sub][label]
                if rec["degenerate"]:
                    print(f"  {label} value: the difference is identically zero -- the raw value head is a function of "
                          f"the position alone and never sees the rule, so this contrast is vacuous for one net. "
                          f"Claim 16's raw-head reading is the across-net block below.")
                    continue
                show_paired(f"{label} value", rec["verdicts"])

    # ---- the across-net differences (the only form in which the raw head can be read at all)
    across_out: dict[str, dict] = {}
    print("\n" + "=" * 104)
    print("ACROSS-NET DIFFERENCES: Delta = beta(net A) - beta(net B) on the same positions and the same clusters,")
    print(f"  A = {nets['a']}")
    print(f"  B = {nets['b']}")
    print("The search value is read under each rule separately; the raw value is rule-free, so it is read once.")
    print("Sec. 5 item 2 verdict rules are stated for the rule contrast; they are applied here in the same form and")
    print("every line names the contrast, so the two readings are not confused.")
    for label, rule in (("search", "count"), ("search", "draw"), ("raw", "count")):
        key = f"{label}|{rule}" if label == "search" else "raw (rule-free)"
        across_out[key] = {}
        for sub, m in subsets.items():
            dy = vals[("a", rule)][label] - vals[("b", rule)][label]
            rec = fit(X[m], dy[m], gid[m], NAMES)
            rec["verdicts"] = paired_verdicts(rec)
            across_out[key][sub] = rec
            print(f"\n--- {key}, {sub} (n = {int(m.sum())}, {len(np.unique(gid[m]))} games)")
            show_paired(f"{label} value, net A - net B", rec["verdicts"], "Delta = beta(A) - beta(B)")

    # ---- difference in differences: NOT a pre-registered reading, printed because the control demands it.
    # A net's search value changes when the rule changes for a purely mechanical reason -- under `draw` the
    # count-decided terminals back up 0 instead of +-1 -- so a COUNT-trained net already shows a large paired
    # Delta. The part of the draw net's Delta that its training explains is the excess over the control's:
    #   DiD = [beta_draw - beta_count](net A) - [beta_draw - beta_count](net B),
    # one regression of ((vA_draw - vA_count) - (vB_draw - vB_count)) on the same X, clustered by game.
    did_out: dict[str, dict] = {}
    print("\n" + "=" * 104)
    print("DIFFERENCE IN DIFFERENCES -- NOT a pre-registered reading; the verdicts above are the registered ones.")
    print("DiD = net A's paired Delta minus net B's, i.e. the part of A's rule effect that B's does not explain.")
    print("Printed because a net's paired Delta is not zero under the rule change alone: the search backs up a")
    print("different terminal value, so a count-trained control moves too. Read A's registered Delta beside B's.")
    for sub, m in subsets.items():
        did_out[sub] = {}
        for label in ("search", "raw"):
            dy = ((vals[("a", "draw")][label] - vals[("a", "count")][label])
                  - (vals[("b", "draw")][label] - vals[("b", "count")][label]))
            rec = fit(X[m], dy[m], gid[m], NAMES)
            rec["verdicts"] = paired_verdicts(rec)
            did_out[sub][label] = rec
        print(f"\n--- {sub} (n = {int(m.sum())}, {len(np.unique(gid[m]))} games)")
        for label in ("search", "raw"):
            rec = did_out[sub][label]
            if rec["degenerate"]:
                print(f"  {label} value: identically zero (neither net's raw head sees the rule)")
                continue
            show_paired(f"{label} value, DiD", rec["verdicts"], "Delta_A - Delta_B")

    # ---- claim 16's secondary form: each cell's own count-margin coefficient against [-0.015, +0.015]
    secondary = {}
    print("\nclaim 16, SECONDARY (each cell's own count-margin coefficient against [-0.015, +0.015]):")
    for nk in order:
        for rule in RULES:
            for label in ("search", "raw"):
                rec = cells_out[f"{nk}|{rule}"][label]
                lo, hi = rec["interval"]["macro_score"]
                v = verdict_band(lo, hi)
                secondary[f"{nk}|{rule}|{label}"] = {"interval": [lo, hi], "verdict": v}
                print(f"  net {nk.upper()} under {rule:5s}, {label:6s} value: {rec['coef']['macro_score']:+.4f} "
                      f"95 % [{lo:+.4f}, {hi:+.4f}]   {v.upper()}")

    meta = {"rules": list(RULES), "nets": nets, "corpora": corpora, "n_per_corpus": a.n, "positions": int(N),
            "games": int(len(np.unique(gid))), "sims": a.sims, "per_game": a.per_game, "ply_lo": a.ply_lo,
            "ply_hi": a.ply_hi, "seed": a.seed, "device": str(device), "max_empty": a.max_empty,
            "processes": a.processes, "design": NAMES, "design_ownership": OWN_NAMES,
            "margins": {"claims_8_13": 0.03, "claim_16_primary": -0.005, "claim_16_secondary": 0.015}}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"meta": meta, "cells": cells_out, "paired": paired_out, "across_net": across_out,
                   "did": did_out, "secondary": secondary, "solved": solved}, f, indent=1)
    print(f"\nwrote {a.out}  [{time.perf_counter() - t0:.0f}s]")


if __name__ == "__main__":
    main()
