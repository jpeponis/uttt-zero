"""The frozen-teacher dataset for the architecture study (PLAN6 §4 G-data).

    .venv/Scripts/python.exe tools/gdata.py --corpus runs/deep10_c1_300_s1 --last 20 --n 500000 --teacher runs/deep10_c1_300/net_0300.pt --sims 256 --device cuda:0 --out runs/gdata_v1.npz

Positions are drawn from the corpus's last --last game files with a prespecified ply mixture — the replay audit's
*sampling* fractions (3 / 18 / 25 / 29 / 25 % for plies 0–7 / 8–19 / 20–31 / 32–43 / 44+), so the study sees what the
learner sees — without replacement, then split by source game 80 / 10 / 10 into train / dev / test (split 0 / 1 / 2;
the test slice is sealed until the end of Phase G: G tools take --split dev). Teacher: --teacher evaluated with the
8-way symmetry average (exactly equivariant, so a student's D4 residual is measured against a symmetric target) at
--sims simulations: search policy (visit distribution), search value, plus the raw policy and value, plus the exact
value and the uniform-over-optimal-moves policy where the position has <= --max_exact empties in open boards
(uttt.solver). Reports the canonical-position overlap between the splits (64-bit symmetric hash; collisions
negligible at this size). Everything is stored from the side to move's perspective, as the replay buffer does.

--rule count|draw is the rule the games are replayed under, the teacher's trees expand under and the exact
labels are solved under; the corpus must have been generated under it, the dataset records it and a non-count
rule tags the output name. Three of the four label kinds here decide a terminal value, so a rule mismatch
would be a silent mixture rather than a cosmetic one (PLAN7 §5 K1).
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
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.exact import empties_in_open_boards_t  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.rules import RULES, tag_path  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.selfplay_cont import position_hash_sym  # noqa: E402
from uttt.solver import solve_batch  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402

PLY_BUCKETS = ((0, 7), (8, 19), (20, 31), (32, 43), (44, 81))
MIXTURE = (0.03, 0.18, 0.25, 0.29, 0.25)  # docs/history/review_astra/replay_audit.json: sampling fraction by ply bucket


def sample_pairs(lengths: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """(game, ply) pairs: per bucket, MIXTURE[b] * n plies drawn without replacement from every position in that bucket."""
    G = len(lengths)
    ply = np.arange(82)
    valid = ply[None, :] < (lengths[:, None] - 0)  # positions 0 .. L-1 (the position before each move)
    out = []
    for (lo, hi), frac in zip(PLY_BUCKETS, MIXTURE):
        cand = np.argwhere(valid & (ply[None, :] >= lo) & (ply[None, :] <= hi))  # (K, 2): game, ply
        k = min(int(round(frac * n)), len(cand))
        out.append(cand[rng.choice(len(cand), size=k, replace=False)])
    pairs = np.concatenate(out)
    return pairs[np.lexsort((pairs[:, 1], pairs[:, 0]))]


@torch.no_grad()
def replay_positions(moves: np.ndarray, pairs: np.ndarray, device, chunk: int = 20000, rule: str = "count"):
    """Reconstruct the sampled positions by stepping the games in lockstep on the batched engine."""
    out = {k: [] for k in ("cells", "macro", "next_board", "player")}
    order = []
    for g0 in range(0, moves.shape[0], chunk):
        mv = torch.from_numpy(moves[g0 : g0 + chunk].astype(np.int64)).to(device)
        n = mv.shape[0]
        sel = pairs[(pairs[:, 0] >= g0) & (pairs[:, 0] < g0 + n)]
        want = torch.zeros(n, 82, dtype=torch.bool, device=device)
        want[torch.from_numpy(sel[:, 0] - g0).to(device), torch.from_numpy(sel[:, 1]).to(device)] = True
        g = BatchUTTT(n, device, rule)
        for t in range(82):
            m = want[:, t]
            if bool(m.any()):
                idx = torch.nonzero(m).squeeze(1)
                out["cells"].append(g.cells[idx])
                out["macro"].append(g.macro[idx])
                out["next_board"].append(g.next_board[idx])
                out["player"].append(g.player[idx])
                order.append(np.stack([idx.cpu().numpy() + g0, np.full(len(idx), t)], 1))
            if t < 81:
                g.step(mv[:, t].clamp(min=0))
    order = np.concatenate(order)
    return {k: torch.cat(v) for k, v in out.items()}, order


@torch.no_grad()
def teach(ev, pos: dict, sims: int, device, batch: int = 4096, log=print, rule: str = "count"):
    """Search policy / value and raw policy / value for every position, in fixed-shape batches (graphs captured once)."""
    N = pos["cells"].shape[0]
    cfg = SearchConfig(n_sims=sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(sims, 24))
    s = BatchedSearch(ev, batch, cfg, device, rule=rule)
    pol = torch.zeros(N, 81, dtype=torch.float16, device=device)
    val = torch.zeros(N, device=device)
    raw_p = torch.zeros(N, 81, dtype=torch.float16, device=device)
    raw_v = torch.zeros(N, device=device)
    t0 = time.perf_counter()
    for i in range(0, N, batch):
        sl = slice(i, min(i + batch, N))
        n = sl.stop - sl.start
        g = BatchUTTT(batch, device, rule)
        for k in ("cells", "macro", "next_board", "player"):
            getattr(g, k)[:n] = pos[k][sl]
        rp, rv = ev(g.cells, g.macro, g.next_board, g.player, g.done)
        r = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
        pol[sl], val[sl] = r.policy[:n].half(), r.root_value[:n]
        raw_p[sl], raw_v[sl] = rp[:n].half(), rv[:n]
        if (i // batch) % 10 == 0:
            done = sl.stop
            el = time.perf_counter() - t0
            log(f"  teacher: {done}/{N} ({el:.0f}s, {el / done * (N - done):.0f}s left)")
    return pol, val, raw_p, raw_v


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="runs/deep10_c1_300_s1")
    ap.add_argument("--last", type=int, default=20)
    ap.add_argument("--n", type=int, default=500_000)
    ap.add_argument("--teacher", default="runs/deep10_c1_300/net_0300.pt")
    ap.add_argument("--sims", type=int, default=256)
    ap.add_argument("--no_sym", action="store_true", help="plain teacher instead of the 8-way symmetry average (8x faster)")
    ap.add_argument("--max_exact", type=int, default=14)
    ap.add_argument("--processes", type=int, default=8)
    ap.add_argument("--batch", type=int, default=4096)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule the replay, the teacher search and the exact labels use")
    ap.add_argument("--corpus_rule", choices=RULES, default="", help="the corpus rule, when its directory records none")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out_path = tag_path(a.out, a.rule)  # a second rule writes beside the first, never over it
    if os.path.exists(out_path):
        sys.exit(f"refusing to overwrite {out_path}: a rebuilt dataset is a different one; pick a new name")
    corpus_src = corpus_rule(a.corpus, a.corpus_rule)
    if corpus_src != a.rule:
        sys.exit(f"{a.corpus} was generated under rule {corpus_src!r} and --rule is {a.rule!r}: the teacher would "
                 f"label another rule's positions. Point --corpus at a {a.rule}-rule run.")
    device = torch.device(a.device)
    torch.manual_seed(a.seed)
    rng = np.random.default_rng(a.seed)
    t0 = time.perf_counter()
    files = sorted(glob.glob(os.path.join(a.corpus, "games", "games_*.npz")))[-a.last :]
    moves = np.concatenate([np.load(f)["moves"] for f in files])
    lengths = np.concatenate([np.load(f)["lengths"] for f in files]).astype(np.int64)
    pairs = sample_pairs(lengths, a.n, rng)
    print(f"{len(lengths)} games in {len(files)} files of {a.corpus}; {len(pairs)} positions sampled by the ply mixture {MIXTURE}", flush=True)
    pos, order = replay_positions(moves, pairs, device, rule=a.rule)
    N = pos["cells"].shape[0]
    game_id, ply = order[:, 0], order[:, 1]
    # split by game, 80 / 10 / 10
    games = np.unique(game_id)
    u = rng.random(len(games))
    split_of_game = np.where(u < 0.8, 0, np.where(u < 0.9, 1, 2)).astype(np.int8)
    split = split_of_game[np.searchsorted(games, game_id)]
    print(f"replayed {N} positions from {len(games)} games ({time.perf_counter() - t0:.0f}s); split sizes "
          f"{[int((split == k).sum()) for k in range(3)]}", flush=True)
    # overlap between splits, by canonical (symmetric) position
    h = position_hash_sym(pos["cells"], pos["next_board"], pos["player"]).cpu().numpy()
    keys = [set(h[split == k].tolist()) for k in range(3)]
    overlap = {"train_dev": len(keys[0] & keys[1]), "train_test": len(keys[0] & keys[2]), "dev_test": len(keys[1] & keys[2]),
               "distinct": [len(k) for k in keys]}
    print(f"canonical-position overlap between splits: {overlap}", flush=True)
    # teacher
    fe = FusedEvaluator(load_checkpoint(a.teacher, device), device)
    ev = fe if a.no_sym else SymmetryAveragedEvaluator(fe)
    pol, val, raw_p, raw_v = teach(ev, pos, a.sims, device, a.batch, rule=a.rule)
    print(f"teacher labels done ({time.perf_counter() - t0:.0f}s)", flush=True)
    # exact labels
    empt = empties_in_open_boards_t(pos["cells"], pos["macro"]).cpu().numpy()
    ex = np.flatnonzero(empt <= a.max_exact)
    exact_v = np.full(N, -2, dtype=np.int8)
    exact_p = np.zeros((N, 81), dtype=np.float16)
    if len(ex):
        c, m, nb, p = (pos[k].cpu().numpy() for k in ("cells", "macro", "next_board", "player"))
        chunks = [(c[ex[i : i + 64]], m[ex[i : i + 64]], nb[ex[i : i + 64]], p[ex[i : i + 64]]) for i in range(0, len(ex), 64)]
        with Pool(a.processes) as pool:
            for j, (v, pp) in enumerate(pool.imap(partial(solve_batch, rule=a.rule), chunks, chunksize=4)):
                sl = ex[j * 64 : j * 64 + len(v)]
                exact_v[sl], exact_p[sl] = v, pp
    print(f"exact labels for {len(ex)} positions with <= {a.max_exact} empties ({time.perf_counter() - t0:.0f}s)", flush=True)
    meta = {"rule": a.rule, "corpus": a.corpus, "corpus_rule": corpus_src, "files": [os.path.basename(f) for f in files], "n": N, "mixture": MIXTURE, "ply_buckets": PLY_BUCKETS,
            "teacher": a.teacher, "sims": a.sims, "symmetry_averaged": not a.no_sym, "max_exact": a.max_exact, "seed": a.seed,
            "split": "0 train / 1 dev / 2 test (by source game; test sealed until the end of PLAN6 Phase G)",
            "overlap": overlap, "built": time.strftime("%Y-%m-%d %H:%M"), "seconds": round(time.perf_counter() - t0)}
    np.savez_compressed(out_path, cells=pos["cells"].cpu().numpy(), macro=pos["macro"].cpu().numpy(), next_board=pos["next_board"].cpu().numpy(),
                        player=pos["player"].cpu().numpy(), ply=ply.astype(np.int16), game_id=game_id.astype(np.int64), split=split,
                        empties=empt.astype(np.int16), teacher_policy=pol.cpu().numpy(), teacher_value=val.cpu().numpy(),
                        raw_policy=raw_p.cpu().numpy(), raw_value=raw_v.cpu().numpy(), exact_value=exact_v, exact_policy=exact_p,
                        meta=np.array(json.dumps(meta)))
    print(f"wrote {out_path}: {N} positions  [{time.perf_counter() - t0:.0f}s]")


if __name__ == "__main__":
    main()
