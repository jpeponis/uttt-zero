"""Surprise mining -> validated tactical puzzles (PLAN2 §5 step 7; REVIEW-codex: "surprise mining should become a
tactical-puzzle pipeline").

    .venv/Scripts/python.exe tools/puzzles.py runs/v2b/net_0150.pt --corpus runs/v2a --last 3 --max_empty 14 --n 6000 --device cuda:1

Candidates: natural positions from held-out corpus games (≤ 2 per game, provenance kept) with ≤ max_empty empties
in open boards. Every candidate is solved with all its children (exact values), so a puzzle is a position where
the raw policy's argmax move loses exact value; "hard" puzzles are those where the 64-sim search also fails.
Each puzzle records the optimal-move set, a greedy principal variation, the regret and heuristic motif labels
(local_win, macro_win, closes_board, gives_free_move, denies_free_move, tiebreak_conversion, draw_hold).
Writes suites/puzzles_v1.npz (+ .json with readable boards of the first 20 hard puzzles).
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
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.game import FULL, UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.solver import ILLEGAL, empties_in_open_boards, solve_children  # noqa: E402


def collect(files, per_game, min_empty, max_empty, n_max, rng):
    rows = []
    for fi, f in enumerate(files):
        z = np.load(f)
        moves, lengths = z["moves"], z["lengths"]
        for k in range(len(lengths)):
            g = UTTT()
            found = []
            for t in range(int(lengths[k])):
                e = empties_in_open_boards(g.cells, g.macro)
                if e < min_empty:
                    break
                if e <= max_empty:
                    found.append((t, g.cells.copy(), g.macro.copy(), g.next_board, g.player, e))
                g.play(int(moves[k, t]))
            for j in rng.choice(len(found), size=min(per_game, len(found)), replace=False) if found else []:
                rows.append((fi * (1 << 20) + k,) + found[j])
            if len(rows) >= n_max:
                return rows
    return rows


def as_game(cells, macro, nb, player) -> UTTT:
    g = UTTT()
    g.cells[:] = cells
    g.macro[:] = macro
    g.next_board, g.player = int(nb), int(player)
    g.move_count = int((g.cells != 0).sum())
    return g


def pv_and_end(cells, macro, nb, player, child, max_len=8):
    """Greedy principal variation (an optimal move at every step) and how the game ends under it."""
    g = as_game(cells, macro, nb, player)
    pv = []
    ch = child
    while not g.done and len(pv) < max_len:
        v = int(ch.max())
        m = int(np.flatnonzero(ch == v)[0])
        pv.append(m)
        g.play(m)
        if g.done:
            break
        _, ch = solve_children((g.cells, g.macro, g.next_board, g.player))
    # finish greedily without storing more of the PV
    while not g.done:
        _, ch = solve_children((g.cells, g.macro, g.next_board, g.player))
        g.play(int(np.flatnonzero(ch == ch.max())[0]))
    return pv, g.end_reason


def motifs(cells, macro, nb, player, best, raw_move, exact, end_reason) -> list[str]:
    g = as_game(cells, macro, nb, player)
    h = g.clone()
    h.play(best)
    tags = []
    b = best // 9
    if h.macro[b] == player:
        tags.append("local_win")
    if h.done and h.winner == player and h.end_reason == "line":
        tags.append("macro_win")
    if h.macro[b] == FULL:
        tags.append("closes_board")
    if h.next_board < 0 and not h.done:
        tags.append("gives_free_move")
    r = g.clone()
    r.play(raw_move)
    if r.next_board < 0 and not r.done and h.next_board >= 0:
        tags.append("denies_free_move")
    if end_reason in ("count", "draw"):
        tags.append("tiebreak_conversion")
    if exact == 0:
        tags.append("draw_hold")
    return tags


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("--corpus", default="runs/v2a")
    ap.add_argument("--last", type=int, default=3)
    ap.add_argument("--min_empty", type=int, default=6)
    ap.add_argument("--max_empty", type=int, default=14)
    ap.add_argument("--n", type=int, default=6000)
    ap.add_argument("--sims", type=int, default=64)
    ap.add_argument("--processes", type=int, default=8)
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", required=True, help="output .npz; NEVER an existing suites/ yardstick (a rebuilt suite is a new, incomparable one)")
    a = ap.parse_args()
    device = torch.device(a.device)
    files = sorted(glob.glob(os.path.join(a.corpus, "games", "games_*.npz")))[-a.last :]
    t0 = time.perf_counter()
    rows = collect(files, 2, a.min_empty, a.max_empty, a.n, np.random.default_rng(0))
    N = len(rows)
    gid = np.array([r[0] for r in rows])
    ply = np.array([r[1] for r in rows])
    cells = np.stack([r[2] for r in rows]).astype(np.int8)
    macro = np.stack([r[3] for r in rows]).astype(np.int8)
    nb = np.array([r[4] for r in rows], dtype=np.int8)
    player = np.array([r[5] for r in rows], dtype=np.int8)
    empties = np.array([r[6] for r in rows])
    print(f"{N} candidate positions from {len(np.unique(gid))} games ({time.perf_counter() - t0:.0f}s)", flush=True)
    with Pool(a.processes) as pool:
        solved = pool.map(solve_children, [(cells[i], macro[i], int(nb[i]), int(player[i])) for i in range(N)], chunksize=16)
    exact = np.array([s[0] for s in solved], dtype=np.int8)
    child = np.stack([s[1] for s in solved])
    print(f"solved with children in {time.perf_counter() - t0:.0f}s; exact W/D/L for the mover {(exact == 1).mean():.3f}/{(exact == 0).mean():.3f}/{(exact == -1).mean():.3f}", flush=True)

    fe = FusedEvaluator(load_checkpoint(a.checkpoint, device), device)
    g = BatchUTTT(N, device)
    g.cells[:] = torch.from_numpy(cells).to(device)
    g.macro[:] = torch.from_numpy(macro).to(device)
    g.next_board[:] = torch.from_numpy(nb).to(device)
    g.player[:] = torch.from_numpy(player).to(device)
    with torch.no_grad():
        probs, _ = fe(g.cells, g.macro, g.next_board, g.player, g.done)
        raw_move = probs.argmax(1).cpu().numpy()
        s = BatchedSearch(fe, N, SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(a.sims, 24)), device)
        srch_move = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False).action.cpu().numpy()
    ar = np.arange(N)
    reg_raw = exact.astype(np.int64) - child[ar, raw_move].astype(np.int64)
    reg_srch = exact.astype(np.int64) - child[ar, srch_move].astype(np.int64)
    assert (child[ar, raw_move] != ILLEGAL).all() and (child[ar, srch_move] != ILLEGAL).all()
    is_puzzle = reg_raw > 0
    is_hard = reg_srch > 0
    print(f"raw-policy failures (puzzles): {is_puzzle.sum()} ({100 * is_puzzle.mean():.1f}%); search-{a.sims} failures (hard): {is_hard.sum()} ({100 * is_hard.mean():.2f}%)")
    print("puzzle rate by empties: " + ", ".join(f"{e}: {100 * is_puzzle[empties == e].mean():.1f}%" for e in sorted(np.unique(empties))))
    idx = np.flatnonzero(is_puzzle)
    pvs, ends, tags, best = [], [], [], []
    for i in idx:
        pv, end = pv_and_end(cells[i], macro[i], nb[i], player[i], child[i])
        pvs.append(pv)
        ends.append(end)
        best.append(int(pv[0]))
        tags.append(motifs(cells[i], macro[i], nb[i], player[i], int(pv[0]), int(raw_move[i]), int(exact[i]), end))
    all_tags = sorted({t for tg in tags for t in tg})
    print("motifs among puzzles: " + ", ".join(f"{t} {sum(t in tg for tg in tags)}" for t in all_tags))
    print(f"regret of the raw move among puzzles: 1 (win->draw or draw->loss) {100 * (reg_raw[idx] == 1).mean():.1f}%, 2 (win->loss) {100 * (reg_raw[idx] == 2).mean():.1f}%")
    pv_arr = np.full((len(idx), 8), -1, dtype=np.int8)
    for j, pv in enumerate(pvs):
        pv_arr[j, : len(pv)] = pv
    tag_str = np.array([",".join(t) for t in tags], dtype=str)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    np.savez_compressed(a.out, cells=cells[idx], macro=macro[idx], next_board=nb[idx], player=player[idx], exact=exact[idx], child=child[idx],
                        empties=empties[idx], game_id=gid[idx], ply=ply[idx], raw_move=raw_move[idx], search_move=srch_move[idx],
                        regret_raw=reg_raw[idx], regret_search=reg_srch[idx], hard=is_hard[idx], pv=pv_arr, motifs=tag_str,
                        meta=np.array(json.dumps({"corpus": a.corpus, "files": [os.path.basename(f) for f in files], "net": a.checkpoint,
                                                  "sims": a.sims, "candidates": int(N), "max_empty": a.max_empty})))
    hard_idx = [j for j, i in enumerate(idx) if is_hard[i]][:20]
    readable = []
    for j in hard_idx:
        i = idx[j]
        gg = as_game(cells[i], macro[i], nb[i], player[i])
        readable.append({"id": int(i), "game_id": int(gid[i]), "ply": int(ply[i]), "exact": int(exact[i]), "best": best[j], "pv": pvs[j],
                         "raw_move": int(raw_move[i]), "search_move": int(srch_move[i]), "motifs": tags[j], "board": str(gg)})
    with open(os.path.splitext(a.out)[0] + ".json", "w") as f:
        json.dump(readable, f, indent=1)
    print(f"wrote {a.out} ({len(idx)} puzzles, {int(is_hard[idx].sum())} hard) and {len(readable)} readable hard puzzles  [{time.perf_counter() - t0:.0f}s]")
    for r in readable[:3]:
        print(f"\nhard puzzle id {r['id']} (game {r['game_id']}, ply {r['ply']}): exact {r['exact']:+d}, best {r['best']}, PV {r['pv']}, raw {r['raw_move']}, search {r['search_move']}, motifs {r['motifs']}")
        print(r["board"])


if __name__ == "__main__":
    main()
