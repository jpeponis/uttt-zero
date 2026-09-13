"""The empty board (PLAN7 J3): what one checkpoint says about the starting position, and what its own
play from there looks like at a matched search budget.

    .venv/Scripts/python.exe tools/empty_board.py --net runs/deep8_c1_300_e8/net_0300.pt \
        --games 2000 --sims 256 --root_sims 16384 --device cuda:1 --out runs/plan7/J3_empty_board.json

Three measurements:

  (a) the root value of the empty board and its deterministic principal line at --root_sims, through
      tools/atlas.py's deep_values — 8-way symmetry-averaged (uttt.symmetry), as every atlas reading is,
      and a DIFFERENT search from the game arms below (PUCT, c_puct 1.25, m_considered 81, gumbel_scale 0,
      depth_cap 40). A separate measurement, not a matched-budget comparator for (b) or (c).
      Search-relative: this is what net + search prefer, not a game-theoretic value.
  (b) --games self-play games from the empty board at --sims, with the move sampled from the search policy
      for the first --b_sample_moves plies at temperature 1 and the uniform floor OFF, greedy afterwards.
  (c) --games self-play games from the empty board at the SAME --sims, under the run's own self-play
      exploration settings as trained, read from its config.json (sample_moves, temperature, sample_uniform,
      root_prior_floor) with the trainer's Gumbel scale.

(b) and (c) play with the plain FusedEvaluator by default — the agent that generated the run's corpus, so
their splits are comparable with the corpus's (M2 §7e M2 row 15); --sym symmetry-averages them too, which
measures a different (stronger) player. Arm (a) is symmetry-averaged either way.

(b) and (c) share the budget on purpose: their difference is the exploration *package* at a matched budget,
not a budget change (M0's finding on the first design, PLAN7 §7e row 21) — four knobs at once (sampled
plies, sampling floor, root prior floor, Gumbel scale), not attributable singly. Neither arm is greedy in
the sense the first design assumed: with sampling off the search is deterministic and would replay one game
--games times, which is why (b) samples the opening. The games of each arm are independent draws from that
arm's stochastic policy, so the Wilson intervals are the right intervals for its outcome distribution;
distinct_games and the distinct-opening counts report how concentrated the policy is and are not a
correction to them (M2 §7e M2 row 3).

Budget and depth cap are NOT as trained (they are held fixed across the arms on purpose): the meta records
the arms' sims and depth_cap beside the run's trained depth_cap and sims schedule.
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
from uttt.rules import RULES, check_rule, tag_path  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402

MAX_PLY = 82
Z95 = 1.959963984540054
PLAIN_EV = "plain FusedEvaluator (the agent that generated the run's corpus)"
SYM_EV = "8-way symmetry-averaged (uttt.symmetry)"


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
def play_from_empty(ev, n: int, cfg: SearchConfig, device, seed: int, rule: str):
    """n self-play games from the empty board, both sides the same evaluator, in lock-step.

    selfplay=True and the true ply are passed to every search, because that pair is what gates the opening
    sampling (uttt/search.py:308-321) — the Gumbel scale does not (M0). `rule` is the terminal rule the
    games and the search trees run under (uttt.rules). Returns the finished BatchUTTT and the move table
    (padded with -1)."""
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    g = BatchUTTT(n, device, rule)
    s = BatchedSearch(ev, n, cfg, device, generator=gen, rule=rule)
    moves = torch.full((n, MAX_PLY), -1, dtype=torch.int8, device=device)
    ply = 0
    while not bool(g.done.all()):
        r = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=True, ply=ply)
        moves[:, ply] = torch.where(g.done, torch.full_like(r.action, -1), r.action).to(torch.int8)
        g.step(r.action)
        ply += 1
    return g, moves


def arm_stats(label: str, cfg: SearchConfig, games: list, seconds: float, evaluator: str, rule: str) -> dict:
    """One arm's X / O / draw split with Wilson 95 % intervals, length, end reasons, and how concentrated
    the arm's policy is (distinct games and distinct openings — reported, not corrected for)."""
    winner = np.concatenate([g.winner.cpu().numpy() for g, _ in games])
    reason = np.concatenate([g.end_reason.cpu().numpy() for g, _ in games])
    length = np.concatenate([g.move_count.cpu().numpy().astype(np.int64) for g, _ in games])
    mv = np.concatenate([m.cpu().numpy() for _, m in games]).astype(np.int64)
    n = len(winner)
    k = {"x_win": int((winner == 1).sum()), "o_win": int((winner == -1).sum()), "draw": int((winner == 0).sum())}
    out = {"label": label, "games": n, "sims": cfg.n_sims, "evaluator": evaluator, "rule": rule,
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
    out["interval_note"] = (
        "the games are independent draws from this arm's stochastic policy, so the Wilson intervals above are "
        "the correct 95 % intervals for that policy's outcome distribution. Identical games are duplicate "
        "OUTCOMES of independent draws, not dependent draws: distinct_games, distinct_openings_4ply and "
        "distinct_openings_4ply_canonical report how concentrated the policy is, and are NOT a correction to "
        "the intervals (M2, PLAN7 §7e M2 row 3). A bootstrap over distinct lines would reweight them and "
        "estimate a different policy; widening the sampled plies would define a different experiment.")
    return out


def format_arm(d: dict) -> str:
    def pct(name):
        lo, hi = d[f"{name}_ci95"]
        return f"{100 * d[f'{name}_share']:5.1f} % [{100 * lo:5.1f}, {100 * hi:5.1f}]"

    return (f"  {d['label']:34s} {d['games']:5d} games @{d['sims']:5d} sims   X {pct('x_win')}   O {pct('o_win')}   "
            f"draw {pct('draw')}\n"
            f"  {'':34s} mean length {d['mean_length']:5.1f}   end reasons line {100 * d['end_line_share']:5.1f} % / "
            f"count {100 * d['end_count_share']:5.1f} % / equal {100 * d['end_equal_share']:5.1f} %\n"
            f"  {'':34s} policy concentration (not an interval correction): {d['distinct_games']} distinct games, "
            f"{d['distinct_openings_4ply']} 4-ply openings ({d['distinct_openings_4ply_canonical']} up to symmetry)   "
            f"[{d['seconds']:.0f}s]")


def run_arm(label: str, ev, cfg: SearchConfig, total: int, batch: int, device, seed: int, evaluator: str, rule: str) -> dict:
    """Play `total` games in chunks of at most `batch` (one lock-step batch each; they all start from the
    empty board, so chunking changes nothing but the memory and the per-chunk RNG stream)."""
    sizes = [batch] * (total // batch) + ([total % batch] if total % batch else [])
    games, t = [], time.perf_counter()
    for i, k in enumerate(sizes):
        games.append(play_from_empty(ev, k, cfg, device, seed + i, rule))
        print(f"  {label}: {sum(len(g.winner) for g, _ in games)}/{total} games ({time.perf_counter() - t:.0f}s)", flush=True)
    return arm_stats(label, cfg, games, time.perf_counter() - t, evaluator, rule)


def opening_trajectory(run: str) -> tuple[list, str]:
    """The run's own first-move trajectory, from its two records, which are NOT the same statistic:

      timeline.json  first_top_share  — the RAW POLICY's first-move probability: probs.max() of the
                                        checkpoint's policy head on the empty board (tools/timeline.py:129-130);
      log.jsonl      first_move_top_share — the share of that iteration's GENERATED GAMES whose first move
                                        was the modal one (self-play at its training budget, with the
                                        exploration package on).

    They differ by construction (0.982 against 0.835 at the end of deep8_c1_300_e8; M2 §7e M2 row 7) and
    neither substitutes for the other. Pairing: timeline row `iter` = N is checkpoint net_NNNN.pt, written
    after training iteration N-1 (uttt/train2.py:397-399), so the generating log row is `iter` N-1."""
    tl_path, log_path = os.path.join(run, "timeline.json"), os.path.join(run, "log.jsonl")
    by_iter = {}
    if os.path.exists(log_path):
        with open(log_path) as fh:
            for line in fh:
                r = json.loads(line)
                by_iter[int(r["iter"])] = r
    rows = []
    if os.path.exists(tl_path):
        for r in json.load(open(tl_path))["rows"]:
            it = int(r["iter"])
            g = by_iter.get(it - 1)
            rows.append({"iter": it, "log_iter": (it - 1) if g else None,
                         "raw_policy_first_move": r.get("first_top_move"),
                         "raw_policy_first_move_prob": r.get("first_top_share"),
                         "generated_games_first_move": g.get("first_move_top") if g else None,
                         "generated_games_top_move_share": g.get("first_move_top_share") if g else None,
                         "generated_games": g.get("games") if g else None})
    elif by_iter:
        for it in sorted(by_iter):
            g = by_iter[it]
            rows.append({"iter": None, "log_iter": it, "raw_policy_first_move": None,
                         "raw_policy_first_move_prob": None,
                         "generated_games_first_move": g.get("first_move_top"),
                         "generated_games_top_move_share": g.get("first_move_top_share"),
                         "generated_games": g.get("games")})
    src = ("timeline.json + log.jsonl" if rows and os.path.exists(tl_path) and by_iter else
           "timeline.json only" if rows and os.path.exists(tl_path) else
           "log.jsonl only" if rows else "neither timeline.json nor log.jsonl found")
    return rows, src


def format_trajectory(rows: list, src: str) -> str:
    def one(r):
        raw = ("-" if r["raw_policy_first_move_prob"] is None else
               f"[{r['raw_policy_first_move']}] {r['raw_policy_first_move_prob']:.3f}")
        gen = ("-" if r["generated_games_top_move_share"] is None else
               f"[{r['generated_games_first_move']}] {r['generated_games_top_move_share']:.3f}")
        it = f"iter {r['iter']}" if r["iter"] is not None else f"log iter {r['log_iter']}"
        return f"  {it:>10s}:  raw policy {raw:>14s}   generated games {gen:>14s}"

    if not rows:
        return f"\nthe run's own opening trajectory: {src}"
    shown = [rows[0], rows[len(rows) // 2], rows[-1]]
    return ("\nthe run's own opening trajectory (" + src + "). Two different statistics, neither a substitute "
            "for the other:\n  raw policy      = the checkpoint's first-move PROBABILITY on the empty board "
            "(timeline.json first_top_share = probs.max(), tools/timeline.py:129-130)\n  generated games = the share of "
            "that iteration's self-play games whose first move was the modal one (log.jsonl first_move_top_share)\n"
            + "\n".join(one(r) for r in shown))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", required=True)
    ap.add_argument("--run", default="", help="run directory for config.json, timeline.json and log.jsonl (default: the net's)")
    ap.add_argument("--games", type=int, default=2000, help="games in each of arms (b) and (c)")
    ap.add_argument("--sims", type=int, default=256, help="the budget both arms play at")
    ap.add_argument("--root_sims", type=int, default=16384, help="arm (a)'s budget on the empty board")
    ap.add_argument("--batch", type=int, default=250, help="games per lock-step batch")
    ap.add_argument("--b_sample_moves", type=int, default=4, help="arm (b): plies whose move is sampled from the search policy")
    ap.add_argument("--b_temperature", type=float, default=1.0)
    ap.add_argument("--b_gumbel_scale", type=float, default=0.0, help="arm (b): 0 keeps the search itself deterministic")
    ap.add_argument("--b_root_floor", type=float, default=0.0, help="arm (b): the root prior floor, off by default")
    ap.add_argument("--c_gumbel_scale", type=float, default=None,
                    help="arm (c): default is config.json's gumbel_scale if the run recorded one, else MCTSConfig's 1.0")
    ap.add_argument("--sym", action="store_true",
                    help="symmetry-average arms (b) and (c) too (default: the plain evaluator, the corpus-generating agent)")
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule the games and the search trees run under")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", default="runs/plan7/J3_empty_board.json")
    a = ap.parse_args()
    rule = check_rule(a.rule)
    device = torch.device(a.device)
    run = a.run or os.path.dirname(a.net)
    cfg_path = os.path.join(run, "config.json")
    train = json.load(open(cfg_path))
    fe = FusedEvaluator(load_checkpoint(a.net, device), device)
    sym_ev = SymmetryAveragedEvaluator(fe)
    games_ev = sym_ev if a.sym else fe
    games_ev_name = SYM_EV if a.sym else PLAIN_EV
    mode, c_scale = train.get("mode", "gumbel"), float(train.get("c_scale", 0.1))
    train_rule = train.get("rule", "count")  # every run before K1 predates the field and is a count-rule run
    depth_cap = min(a.sims, 24)

    # arm (c)'s Gumbel scale: the trainer is gaining the field, so read it when the run recorded one (M2 row 5)
    if a.c_gumbel_scale is not None:
        c_gs, c_gs_src = float(a.c_gumbel_scale), "--c_gumbel_scale on the command line"
    elif "gumbel_scale" in train:
        c_gs, c_gs_src = float(train["gumbel_scale"]), f"{cfg_path} (the run recorded it)"
    else:
        c_gs, c_gs_src = 1.0, f"MCTSConfig's default 1.0 ({cfg_path} has no gumbel_scale key, so the run trained at it)"

    def cfg(sims, sample_moves, temperature, sample_uniform, gumbel_scale, root_floor):
        return SearchConfig(n_sims=sims, mode=mode, gumbel_scale=gumbel_scale, sample_moves=sample_moves,
                            temperature=temperature, sample_uniform=sample_uniform, root_prior_floor=root_floor,
                            c_scale=c_scale, cuda_graph=device.type == "cuda", depth_cap=depth_cap)

    print(f"{a.net} on {device}; rule {rule} (trained under {train_rule}); arms (b)/(c) play with the {games_ev_name}, "
          f"arm (a) is {SYM_EV}", flush=True)
    if rule != train_rule:
        print(f"NOTE: evaluation rule {rule!r} differs from this checkpoint's training rule {train_rule!r}; "
              "that is a deliberate argument of this tool, never inferred (uttt/rules.py)", flush=True)
    print(f"exploration as trained from {cfg_path}: sample_moves {train['sample_moves']}, temperature {train['temperature']}, "
          f"sample_uniform {train['sample_uniform']}, root_prior_floor {train['root_prior_floor']}, c_scale {c_scale}, "
          f"gumbel_scale {c_gs} <- {c_gs_src}", flush=True)
    print(f"exploration settings as trained; budget and depth cap are not: arms (b)/(c) play at {a.sims} sims and "
          f"depth_cap {depth_cap}, against the run's trained depth_cap {train.get('depth_cap')} and sims "
          f"{train.get('sims')} (schedule {train.get('sims_schedule')!r})", flush=True)

    # ---- (a) the root ------------------------------------------------------------------
    t = time.perf_counter()
    vals, pvs, _ = deep_values(sym_ev, [[]], a.root_sims, device, want_pv=True, rule=rule)
    root = {"sims": a.root_sims, "value_for_x": float(vals[0]), "principal_line": [int(m) for m in pvs[0]],
            "first_move": int(pvs[0][0]) if pvs[0] else None, "symmetry_averaged": True, "evaluator": SYM_EV,
            "rule": rule,
            "search": "tools/atlas.py deep_values: puct, c_puct 1.25, m_considered 81, gumbel_scale 0, depth_cap 40",
            "comparability": ("a DIFFERENT search from the game arms (PUCT at depth cap 40 against their Gumbel search at "
                              f"depth cap {depth_cap}) and a different evaluator (symmetry-averaged): a separate "
                              "measurement, not a matched-budget comparator for (b) or (c) (M2 §7e M2 row 15)"),
            "note": "search-relative: what this net and this budget prefer, not a game-theoretic value",
            "seconds": round(time.perf_counter() - t, 1)}
    print(f"\n(a) empty board @{a.root_sims} sims: value for X {root['value_for_x']:+.4f}; "
          f"principal line {root['principal_line']}  [{root['seconds']:.0f}s]", flush=True)

    # ---- (b) and (c) -------------------------------------------------------------------
    batch = max(1, min(a.batch, a.games))
    b_cfg = cfg(a.sims, a.b_sample_moves, a.b_temperature, 0.0, a.b_gumbel_scale, a.b_root_floor)
    c_cfg = cfg(a.sims, int(train["sample_moves"]), float(train["temperature"]), float(train["sample_uniform"]),
                c_gs, float(train["root_prior_floor"]))
    print(flush=True)
    b = run_arm(f"(b) sampled {a.b_sample_moves} plies, floor off", games_ev, b_cfg, a.games, batch, device,
                a.seed * 1000 + 1, games_ev_name, rule)
    c = run_arm("(c) exploration as trained", games_ev, c_cfg, a.games, batch, device,
                a.seed * 1000 + 501, games_ev_name, rule)
    print("\n" + format_arm(b))
    print(format_arm(c))

    # ---- the run's opening trajectory, for context -------------------------------------
    traj, traj_src = opening_trajectory(run)
    print(format_trajectory(traj, traj_src))

    rec = {"meta": {"net": a.net, "run": run, "device": str(device), "games": a.games, "sims": a.sims,
                    "root_sims": a.root_sims, "batch": batch, "seed": a.seed, "rule": rule, "train_rule": train_rule,
                    "built": time.strftime("%Y-%m-%d %H:%M"),
                    "evaluators": {"a": SYM_EV, "b": games_ev_name, "c": games_ev_name,
                                   "note": "(b) and (c) play with the plain evaluator by default — the agent that "
                                           "generated this run's corpus, so their splits are comparable with it; --sym "
                                           "symmetry-averages them, which measures a different, stronger player. Arm (a) "
                                           "keeps the symmetry averaging every atlas reading uses (M2 §7e M2 row 15)"},
                    "train_exploration": {k: train.get(k) for k in ("sample_moves", "temperature", "sample_uniform",
                                                                    "root_prior_floor", "c_scale", "mode", "sims",
                                                                    "sims_schedule", "depth_cap", "gumbel_scale")},
                    "budget_and_depth": {"arm_sims": a.sims, "arm_depth_cap": depth_cap,
                                         "trained_depth_cap": train.get("depth_cap"), "trained_sims": train.get("sims"),
                                         "trained_sims_schedule": train.get("sims_schedule"),
                                         "note": "exploration settings as trained; budget and depth cap are not"},
                    "gumbel_scale": {"b": a.b_gumbel_scale, "c": c_gs, "c_source": c_gs_src},
                    "matched_budget": "(b) and (c) play at the same n_sims; their difference is the exploration package "
                                      "(sampled plies, sampling floor, root prior floor, Gumbel scale — four knobs at "
                                      "once, not attributable singly), not budget",
                    "first_move_statistics": "run_opening_trajectory pairs two different things: the raw policy's "
                                             "first-move probability (timeline.json first_top_share) and the generated "
                                             "games' top-move share (log.jsonl first_move_top_share); neither "
                                             "substitutes for the other (M2 §7e M2 row 7)"},
           "root": root, "arms": {"b": b, "c": c},
           "run_opening_trajectory": traj, "run_opening_trajectory_source": traj_src}
    out = tag_path(a.out, rule)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as fh:
        json.dump(rec, fh, indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
