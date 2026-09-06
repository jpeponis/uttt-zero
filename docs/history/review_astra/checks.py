"""Read-only project audit. Outputs live only in review_astra/; no training runs.

Run with .venv/Scripts/python.exe -B docs/history/review_astra/checks.py.
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]  # moved to docs/history/review_astra by PLAN6
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["NUMBA_CACHE_DIR"] = str(OUT / "numba_cache")
os.environ["UTTT_DEV"] = "cuda:1"

import numpy as np
import torch

from uttt.batch import BatchUTTT, LINES, SYM_BOARD, SYM_CELL, apply_symmetry, encode
from uttt.infer import FusedEvaluator
from uttt.model import UniformEvaluator, load_checkpoint
from uttt.search import BatchedSearch, SearchConfig
from uttt.selfplay_cont import ContinuousSelfPlay


def emit(name, value):
    print(name, json.dumps(value), flush=True)
    return value


def test_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def existing_checks():
    cases = [
        ("test_game", "test_invariants", {}),
        ("test_game", "test_free_move_after_closed_board", {}),
        ("test_game", "test_count_tiebreak", {}),
        ("test_game", "test_count_draw", {}),
        ("test_batch", "test_encode_shapes", {}),
        ("test_batch", "test_batch_matches_reference", {"n": 32, "device": "cuda:1"}),
        ("test_batch", "test_symmetries_preserve_game", {"n": 32}),
        ("test_hygiene", "test_sym_hash", {"n": 64}),
        ("test_hygiene", "test_extra_planes", {"n": 64}),
        ("test_hygiene", "test_own_classes", {}),
        ("test_hygiene", "test_alpha_early", {}),
        ("test_mcts", "test_schedule", {}),
        ("test_mcts", "test_tactics", {}),
        ("test_search_v2", "compare", {"mode": "gumbel", "sims": 16, "n": 32}),
        ("test_search_v2", "compare", {"mode": "puct", "sims": 16, "n": 32}),
        ("test_search_graph", "compare", {"mode": "gumbel", "sims": 16, "n": 32, "depth_cap": 8}),
        ("test_search_graph", "compare", {"mode": "gumbel", "sims": 16, "n": 32, "depth_cap": 8, "net": True}),
        ("test_search_graph", "test_refresh_in_place", {"n": 32}),
        ("test_selfplay_cont", "test_consistency", {"n": 32, "steps": 80, "sims": 4}),
        ("test_solver", "test_against_reference", {"n": 20, "max_empty": 7}),
        ("test_symmetry_eval", "main", {"n": 64}),
        ("test_concepts", "test_labels", {"n": 100}),
        ("test_tablebase", "test_table", {"n": 30}),
    ]
    results = []
    for module, fn, kwargs in cases:
        start = time.perf_counter()
        try:
            getattr(test_module(module), fn)(**kwargs)
            result = {"module": module, "function": fn, "kwargs": kwargs, "pass": True}
        except Exception as exc:
            result = {"module": module, "function": fn, "kwargs": kwargs, "pass": False,
                      "error": repr(exc)}
        result["seconds"] = round(time.perf_counter() - start, 3)
        results.append(emit("existing_check", result))
    return results


def group_checks():
    # Exhaustive automorphism group of the 9-point, 8-winning-line hypergraph.
    lines = {tuple(sorted(line)) for line in LINES.tolist()}
    degrees = [sum(i in line for line in lines) for i in range(9)]
    autos = []
    for p in itertools.permutations(range(9)):
        if any(degrees[i] != degrees[p[i]] for i in range(9)):
            continue
        if {tuple(sorted(p[i] for i in line)) for line in lines} == lines:
            autos.append(p)
    assert set(autos) == {tuple(p) for p in SYM_BOARD.tolist()}
    fixed = [(p == torch.arange(9)).sum().item() for p in SYM_BOARD]
    cell_fixed = [(p == torch.arange(81)).sum().item() for p in SYM_CELL]
    return emit("group", {"line_hypergraph_automorphisms": len(autos), "fixed_board_counts": fixed,
                          "first_move_orbits": sum(cell_fixed) // 8,
                          "ordered_action_pair_orbits": sum(x*x for x in cell_fixed) // 8})


def rng_checks():
    out = {}
    for dev in ("cpu", "cuda:1"):
        g = BatchUTTT(4, dev)
        s = BatchedSearch(UniformEvaluator(dev), 4, SearchConfig(n_sims=2, depth_cap=2), dev)
        torch.manual_seed(987)
        before = torch.get_rng_state().clone() if dev == "cpu" else torch.cuda.get_rng_state(dev).clone()
        s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
        after = torch.get_rng_state() if dev == "cpu" else torch.cuda.get_rng_state(dev)
        out[dev] = {"deterministic_eval_advances_rng": not torch.equal(before, after)}
        assert out[dev]["deterministic_eval_advances_rng"]
    # In particular, loading an anchor instantiates randomly initialized layers first.
    torch.manual_seed(123)
    before = torch.get_rng_state().clone()
    load_checkpoint(str(ROOT / "runs/v2b/net_0150.pt"), "cpu")
    out["checkpoint_load_advances_cpu_rng"] = not torch.equal(before, torch.get_rng_state())
    return emit("rng", out)


def logs():
    out = {}
    for name in ("deep10_c1_300", "deep10_c1_300_s1", "deep10_c1_300_lr150", "deep8_c1_300"):
        folder = ROOT / "runs" / name
        raw = [json.loads(x) for x in (folder / "log.jsonl").read_text().splitlines()]
        rows = list({r["iter"]: r for r in raw}.values())
        totals = {k: round(sum(r.get(k, 0) for r in rows), 2)
                  for k in ("t_selfplay", "t_train", "t_eval", "t_ckpt", "t_exact_wait", "t_iter")}
        tail = [r for r in rows if r["iter"] >= 280]
        totals["unattributed_s"] = round(totals["t_iter"] - sum(totals[k] for k in
                                      ("t_selfplay", "t_train", "t_eval", "t_ckpt", "t_exact_wait")), 2)
        stats = {"unique_iters": len(rows), "duplicate_rows": len(raw)-len(rows), "totals_seconds": totals,
                 "positions_total": sum(r["positions_new"] for r in rows),
                 "sampled_total": sum(r["steps"] * 1024 for r in rows),
                 "tail_mean": {k: float(np.mean([r[k] for r in tail])) for k in
                               ("positions_new", "games", "t_selfplay", "t_train", "cap_hit", "distinct_frac")}}
        out[name] = stats
    a = {r["iter"]: r for r in [json.loads(x) for x in (ROOT / "runs/deep10_c1_300/log.jsonl").read_text().splitlines()]}
    b = {r["iter"]: r for r in [json.loads(x) for x in (ROOT / "runs/deep10_c1_300_lr150/log.jsonl").read_text().splitlines()]}
    fields = ("positions_new", "games", "loss_policy", "loss_value", "x_win", "first_move_top_share")
    diffs = [{"iter": i, "differences": {k: [a[i][k], b[i][k]] for k in fields if a[i][k] != b[i][k]}}
             for i in sorted(a.keys() & b.keys()) if i < 150]
    out["d3_before_treatment"] = [d for d in diffs if d["differences"]][:4]
    return emit("logs", out)


@torch.no_grad()
def symmetry_diagnostics():
    dev = "cuda:1"
    ckpt = ROOT / "runs/deep10_c1_300/net_0300.pt"
    net = load_checkpoint(str(ckpt), dev)
    fe = FusedEvaluator(net, dev)
    # Reconstruct a small deterministic sample of archived games from another run.
    from uttt.game import UTTT
    with np.load(ROOT / "runs/deep8_c1_300/games/games_0299.npz") as z:
        gs = []
        for seq, length in zip(z["moves"][:128], z["lengths"][:128]):
            g = UTTT()
            for ply, move in enumerate(seq[:int(length)]):
                if ply in (16, 28, 40, 48):
                    gs.append(g.clone())
                g.play(int(move))
    c = torch.tensor(np.stack([g.cells for g in gs]), device=dev)
    m = torch.tensor(np.stack([g.macro for g in gs]), device=dev)
    nb = torch.tensor([g.next_board for g in gs], dtype=torch.int8, device=dev)
    p = torch.tensor([g.player for g in gs], dtype=torch.int8, device=dev)
    done = torch.zeros(len(gs), dtype=torch.bool, device=dev)
    probs, vals = [], []
    for s in range(8):
        cs, ms, ns = apply_symmetry(s, c, m, nb)
        ps, vs = fe(cs, ms, ns, p, done)
        probs.append(ps[:, SYM_CELL[s].to(dev)])
        vals.append(vs)
    ps, vs = torch.stack(probs, 1), torch.stack(vals, 1)
    avg = ps.mean(1)
    js = (ps * (ps.clamp_min(1e-30).log2() - avg[:, None].clamp_min(1e-30).log2())).sum(-1).mean(1)
    # Color relabeling, including the mover, should be exactly removed by base encoding.
    relabel_macro = torch.where(m.abs() == 1, -m, m)
    obs = encode(c, m, nb, p, done)
    obs2 = encode(-c, relabel_macro, nb, -p, done)
    assert torch.equal(obs, obs2)
    # Semantically equivalent continuation states: erase irrelevant cells of CLOSED boards only.
    closed_cells = (m != 0).repeat_interleave(9, 1)
    cc = torch.where(closed_cells, torch.zeros_like(c), c)
    p0, v0 = fe(c, m, nb, p, done)
    pe, ve = fe(cc, m, nb, p, done)
    q = (m != 0).any(1)
    result = {"n": len(gs), "corpus": "deep8_c1_300 games_0299 first 128 games, plies 16/28/40/48",
              "mean_policy_js_bits": js.mean().item(), "mean_value_orbit_range": (vs.max(1).values-vs.min(1).values).mean().item(),
              "mean_value_orbit_std": vs.std(1, correction=0).mean().item(),
              "fraction_all_eight_argmax_agree": (ps.argmax(2) == ps.argmax(2)[:, :1]).all(1).float().mean().item(),
              "base_encoding_exact_color_relabel_invariance": True,
              "erased_closed_board_cells": {"n": int(q.sum()), "mean_abs_value_change": (v0[q]-ve[q]).abs().mean().item(),
                                             "policy_argmax_changed": (p0[q].argmax(1)!=pe[q].argmax(1)).float().mean().item(),
                                             "warning": "Out-of-training-distribution input, not a performance comparison; keep engine macro state."}}
    return emit("symmetry_diagnostics", result)


def main():
    torch.set_num_threads(4)
    out = {"torch": torch.__version__, "cuda": torch.version.cuda,
           "devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]}
    out["group"] = group_checks()
    out["rng"] = rng_checks()
    out["logs"] = logs()
    out["symmetry"] = symmetry_diagnostics()
    out["existing_tests"] = existing_checks()
    (OUT / "checks.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
