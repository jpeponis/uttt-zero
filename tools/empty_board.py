"""The empty board (PLAN7 J3): what one checkpoint says about the starting position, and what its own
play from there looks like at a matched search budget.

    .venv/Scripts/python.exe tools/empty_board.py --net runs/deep8_c1_300_e8/net_0300.pt \
        --games 2000 --sims 256 --root_sims 16384 --device cuda:1 --out runs/plan7/J3_empty_board.json

Three measurements, all with the 8-way symmetry-averaged evaluator (uttt.symmetry), so nothing depends on
the orientation the net happens to prefer:

  (a) the root value of the empty board and its deterministic principal line at --root_sims, through
      tools/atlas.py's deep_values (the same PUCT search, m_considered 81, Gumbel scale 0 that searched the
      15 first-move orbits). Search-relative: this is what net + search prefer, not a game-theoretic value.
  (b) --games self-play games from the empty board at --sims, with the move sampled from the search policy
      for the first --b_sample_moves plies at temperature 1 and the uniform floor OFF, greedy afterwards.
  (c) --games self-play games from the empty board at the SAME --sims, under the run's own self-play
      exploration settings as trained, read from its config.json (sample_moves, temperature, sample_uniform,
      root_prior_floor) with the trainer's Gumbel scale.

(b) and (c) share the budget on purpose: their difference is exploration's contribution, not a budget
change (M0's finding on the first design, PLAN7 §7e row 21). Neither is greedy in the sense the first design
assumed — with sampling off the search is deterministic and would replay one game --games times, which is
why (b) samples the opening and why distinct_games is reported beside every split.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from atlas import deep_values  # noqa: E402
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.openings import canonical_keys  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402

MAX_PLY = 82
Z95 = 1.959963984540054


def wilson(k: int, n: int) -> list | None:
    """95 % Wilson score interval for a binomial share (it does not run off the ends at small n)."""
    if n == 0:
        return None
    p, z2 = k / n, Z95 * Z95
    d = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / d
    half = Z95 * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / d
    return [centre - half, centre + half]


@torch.no_grad()
def play_from_empty(ev, n: int, cfg: SearchConfig, device, seed: int):
    """n self-play games from the empty board, both sides the same evaluator, in lock-step.

    selfplay=True and the true ply are passed to every search, because that pair is what gates the opening
    sampling (uttt/search.py:308-321) — the Gumbel scale does not (M0). Returns the finished BatchUTTT and
    the move table (padded with -1)."""
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    g = BatchUTTT(n, device)
    s = BatchedSearch(ev, n, cfg, device, generator=gen)
    moves = torch.full((n, MAX_PLY), -1, dtype=torch.int8, device=device)
    ply = 0
    while not bool(g.done.all()):
        r = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=True, ply=ply)
        moves[:, ply] = torch.where(g.done, torch.full_like(r.action, -1), r.action).to(torch.int8)
        g.step(r.action)
        ply += 1
    return g, moves


def arm_stats(label: str, cfg: SearchConfig, games: list, seconds: float) -> dict:
    """One arm's X / O / draw split with binomial 95 % intervals, length, end reasons, and how much of the
    arm is actually distinct games (a deterministic search repeats itself; the interval below does not know that)."""
    winner = np.concatenate([g.winner.cpu().numpy() for g, _ in games])
    reason = np.concatenate([g.end_reason.cpu().numpy() for g, _ in games])
    length = np.concatenate([g.move_count.cpu().numpy().astype(np.int64) for g, _ in games])
    mv = np.concatenate([m.cpu().numpy() for _, m in games]).astype(np.int64)
    n = len(winner)
    k = {"x_win": int((winner == 1).sum()), "o_win": int((winner == -1).sum()), "draw": int((winner == 0).sum())}
    out = {"label": label, "games": n, "sims": cfg.n_sims,
           "search": {"mode": cfg.mode, "n_sims": cfg.n_sims, "gumbel_scale": cfg.gumbel_scale,
                      "sample_moves": cfg.sample_moves, "temperature": cfg.temperature,
                      "sample_uniform": cfg.sample_uniform, "root_prior_floor": cfg.root_prior_floor,
                      "c_scale": cfg.c_scale, "m_considered": cfg.m_considered, "depth_cap": cfg.depth_cap}}
    for name, count in k.items():
        out[f"{name}_share"] = count / n
        out[f"{name}_ci95"] = wilson(count, n)
        out[f"{name}_n"] = count
    out["mean_length"] = float(length.mean())
    out["sd_length"] = float(length.std(ddof=1)) if n > 1 else None
    for r, name in ((1, "end_line"), (2, "end_count"), (3, "end_equal")):
        out[f"{name}_share"] = float((reason == r).mean())
    out["distinct_games"] = int(len(np.unique(mv, axis=0)))
    out["distinct_openings_4ply"] = int(len(np.unique(mv[:, :4], axis=0)))
    out["distinct_openings_4ply_canonical"] = int(len(np.unique(canonical_keys(mv[:, :4]))))
    out["seconds"] = round(seconds, 1)
    out["interval_note"] = ("binomial intervals treat the games as independent draws; identical games (see "
                            "distinct_games) make them optimistic, so read them with that count beside them")
    return out


def format_arm(d: dict) -> str:
    def pct(name):
        lo, hi = d[f"{name}_ci95"]
        return f"{100 * d[f'{name}_share']:5.1f} % [{100 * lo:5.1f}, {100 * hi:5.1f}]"

    return (f"  {d['label']:34s} {d['games']:5d} games @{d['sims']:5d} sims   X {pct('x_win')}   O {pct('o_win')}   "
            f"draw {pct('draw')}\n"
            f"  {'':34s} mean length {d['mean_length']:5.1f}   end reasons line {100 * d['end_line_share']:5.1f} % / "
            f"count {100 * d['end_count_share']:5.1f} % / equal {100 * d['end_equal_share']:5.1f} %\n"
            f"  {'':34s} distinct: {d['distinct_games']} games, {d['distinct_openings_4ply']} 4-ply openings "
            f"({d['distinct_openings_4ply_canonical']} up to symmetry)   [{d['seconds']:.0f}s]")


def run_arm(label: str, ev, cfg: SearchConfig, total: int, batch: int, device, seed: int) -> dict:
    """Play `total` games in chunks of at most `batch` (one lock-step batch each; they all start from the
    empty board, so chunking changes nothing but the memory and the per-chunk RNG stream)."""
    sizes = [batch] * (total // batch) + ([total % batch] if total % batch else [])
    games, t = [], time.perf_counter()
    for i, k in enumerate(sizes):
        games.append(play_from_empty(ev, k, cfg, device, seed + i))
        print(f"  {label}: {sum(len(g.winner) for g, _ in games)}/{total} games ({time.perf_counter() - t:.0f}s)", flush=True)
    return arm_stats(label, cfg, games, time.perf_counter() - t)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", required=True)
    ap.add_argument("--run", default="", help="run directory for config.json and timeline.json (default: the net's)")
    ap.add_argument("--games", type=int, default=2000, help="games in each of arms (b) and (c)")
    ap.add_argument("--sims", type=int, default=256, help="the budget both arms play at")
    ap.add_argument("--root_sims", type=int, default=16384, help="arm (a)'s budget on the empty board")
    ap.add_argument("--batch", type=int, default=250, help="games per lock-step batch")
    ap.add_argument("--b_sample_moves", type=int, default=4, help="arm (b): plies whose move is sampled from the search policy")
    ap.add_argument("--b_temperature", type=float, default=1.0)
    ap.add_argument("--b_gumbel_scale", type=float, default=0.0, help="arm (b): 0 keeps the search itself deterministic")
    ap.add_argument("--b_root_floor", type=float, default=0.0, help="arm (b): the root prior floor, off by default")
    ap.add_argument("--c_gumbel_scale", type=float, default=1.0, help="arm (c): the trainer's default (not in config.json)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", default="runs/plan7/J3_empty_board.json")
    a = ap.parse_args()
    device = torch.device(a.device)
    run = a.run or os.path.dirname(a.net)
    cfg_path, tl_path = os.path.join(run, "config.json"), os.path.join(run, "timeline.json")
    train = json.load(open(cfg_path))
    fe = FusedEvaluator(load_checkpoint(a.net, device), device)
    ev = SymmetryAveragedEvaluator(fe)
    mode, c_scale = train.get("mode", "gumbel"), float(train.get("c_scale", 0.1))

    def cfg(sims, sample_moves, temperature, sample_uniform, gumbel_scale, root_floor):
        return SearchConfig(n_sims=sims, mode=mode, gumbel_scale=gumbel_scale, sample_moves=sample_moves,
                            temperature=temperature, sample_uniform=sample_uniform, root_prior_floor=root_floor,
                            c_scale=c_scale, cuda_graph=device.type == "cuda", depth_cap=min(sims, 24))

    print(f"{a.net} (symmetry-averaged) on {device}; exploration as trained from {cfg_path}: "
          f"sample_moves {train['sample_moves']}, temperature {train['temperature']}, sample_uniform {train['sample_uniform']}, "
          f"root_prior_floor {train['root_prior_floor']}, c_scale {c_scale}", flush=True)

    # ---- (a) the root ------------------------------------------------------------------
    t = time.perf_counter()
    vals, pvs, _ = deep_values(ev, [[]], a.root_sims, device, want_pv=True)
    root = {"sims": a.root_sims, "value_for_x": float(vals[0]), "principal_line": [int(m) for m in pvs[0]],
            "first_move": int(pvs[0][0]) if pvs[0] else None, "symmetry_averaged": True,
            "search": "tools/atlas.py deep_values: puct, c_puct 1.25, m_considered 81, gumbel_scale 0, depth_cap 40",
            "note": "search-relative: what this net and this budget prefer, not a game-theoretic value",
            "seconds": round(time.perf_counter() - t, 1)}
    print(f"\n(a) empty board @{a.root_sims} sims: value for X {root['value_for_x']:+.4f}; "
          f"principal line {root['principal_line']}  [{root['seconds']:.0f}s]", flush=True)

    # ---- (b) and (c) -------------------------------------------------------------------
    batch = max(1, min(a.batch, a.games))
    b_cfg = cfg(a.sims, a.b_sample_moves, a.b_temperature, 0.0, a.b_gumbel_scale, a.b_root_floor)
    c_cfg = cfg(a.sims, int(train["sample_moves"]), float(train["temperature"]), float(train["sample_uniform"]),
                a.c_gumbel_scale, float(train["root_prior_floor"]))
    print(flush=True)
    b = run_arm(f"(b) sampled {a.b_sample_moves} plies, floor off", ev, b_cfg, a.games, batch, device, a.seed * 1000 + 1)
    c = run_arm("(c) exploration as trained", ev, c_cfg, a.games, batch, device, a.seed * 1000 + 501)
    print("\n" + format_arm(b))
    print(format_arm(c))

    # ---- the run's opening trajectory, for context -------------------------------------
    first_top = []
    if os.path.exists(tl_path):
        first_top = [{"iter": r["iter"], "first_top_share": r.get("first_top_share"), "first_top_move": r.get("first_top_move")}
                     for r in json.load(open(tl_path))["rows"]]
        shown = [r for r in first_top if r["iter"] in (first_top[0]["iter"], first_top[len(first_top) // 2]["iter"], first_top[-1]["iter"])]
        print("\nthe run's own opening trajectory (timeline.json, self-play at its training budget): "
              + ", ".join(f"iter {r['iter']}: [{r['first_top_move']}] {r['first_top_share']:.3f}" for r in shown))
    else:
        print(f"\n{tl_path} not found: first_top_share trajectory omitted")

    rec = {"meta": {"net": a.net, "run": run, "device": str(device), "games": a.games, "sims": a.sims,
                    "root_sims": a.root_sims, "batch": batch, "seed": a.seed, "symmetry_averaged": True,
                    "built": time.strftime("%Y-%m-%d %H:%M"),
                    "train_exploration": {k: train.get(k) for k in ("sample_moves", "temperature", "sample_uniform",
                                                                    "root_prior_floor", "c_scale", "mode", "sims", "sims_schedule")},
                    "matched_budget": "(b) and (c) play at the same n_sims; their difference is exploration, not budget",
                    "gumbel_scale_note": "config.json does not record it; the trainer leaves MCTSConfig's 1.0, which arm (c) "
                                         "uses and arm (b) sets to 0 so that 'greedy after the sampled plies' is true"},
           "root": root, "arms": {"b": b, "c": c}, "run_first_top_share": first_top}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(rec, fh, indent=1)
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
