"""Frozen exact-label endgame set (PLAN2 §5 step 1c; REVIEW-codex findings 7 and the endgame-evaluation
paragraph): positions with few moves left, taken from a frozen game corpus with provenance, solved
exactly together with every legal child, and balanced over (remaining empties × exact result × side to
move). Evaluators are scored with WDL-argmax accuracy, Brier score, log-loss, action regret and
optimal-move rate, with confidence intervals from a cluster bootstrap over source games.

    uttt.endgame.build_set(...)  -> EndgameSet  (tools/endgame.py build)
    uttt.endgame.evaluate(...)   -> dict        (tools/endgame.py eval)
"""
from __future__ import annotations

import glob
import json
import os
import time
from dataclasses import dataclass
from multiprocessing import Pool

import numpy as np
import torch

from .batch import apply_symmetry, encode
from .game import UTTT
from .solver import ILLEGAL, empties_in_open_boards, solve_children  # noqa: F401  (solve_children re-exported)

BUCKETS = ((6, 9), (10, 12), (13, 14), (15, 16))


def bucket_of(e: int) -> int:
    for k, (lo, hi) in enumerate(BUCKETS):
        if lo <= e <= hi:
            return k
    return -1


# ---- candidate positions with provenance -----------------------------------------------------
def collect_candidates(files: list[str], per_game: int, min_empty: int, max_empty: int, rng: np.random.Generator) -> dict:
    """Replay persisted games; keep up to `per_game` random positions per game whose empties in open boards
    lie in [min_empty, max_empty]. Positions carry (file index, game row, ply) as provenance."""
    cols = {k: [] for k in ("cells", "macro", "next_board", "player", "empties", "file", "game", "ply")}
    seen = set()
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
            if not found:
                continue
            for j in rng.choice(len(found), size=min(per_game, len(found)), replace=False):
                t, c, m, nb, p, e = found[j]
                key = c.tobytes() + m.tobytes() + bytes([nb + 1, p + 1])
                if key in seen:
                    continue
                seen.add(key)
                for name, val in zip(cols, (c, m, nb, p, e, fi, k, t)):
                    cols[name].append(val)
    out = {k: np.array(v) for k, v in cols.items()}
    out["cells"] = out["cells"].astype(np.int8)
    out["macro"] = out["macro"].astype(np.int8)
    return out


# ---- exact labels ------------------------------------------------------------------------------
def _solve_many(cands: dict, idx: np.ndarray, processes: int):
    args = [(cands["cells"][i], cands["macro"][i], int(cands["next_board"][i]), int(cands["player"][i])) for i in idx]
    if processes <= 1:
        return [solve_children(a) for a in args]
    with Pool(processes) as pool:
        return pool.map(solve_children, args, chunksize=8)


@dataclass
class EndgameSet:
    cells: np.ndarray  # (K, 81) int8
    macro: np.ndarray  # (K, 9) int8
    next_board: np.ndarray  # (K,) int8
    player: np.ndarray  # (K,) int8
    exact: np.ndarray  # (K,) int8: +1 / 0 / -1 for the mover
    child: np.ndarray  # (K, 81) int8: exact value after each move, ILLEGAL where illegal
    empties: np.ndarray  # (K,) int64
    game_id: np.ndarray  # (K,) int64: cluster id (source file * 2**20 + game row)
    ply: np.ndarray
    meta: dict

    @property
    def n(self) -> int:
        return int(self.cells.shape[0])

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        np.savez_compressed(path, cells=self.cells, macro=self.macro, next_board=self.next_board, player=self.player,
                            exact=self.exact, child=self.child, empties=self.empties, game_id=self.game_id, ply=self.ply,
                            meta=np.array(json.dumps(self.meta)))

    @staticmethod
    def load(path: str) -> "EndgameSet":
        z = np.load(path, allow_pickle=False)
        meta = json.loads(str(z["meta"]))
        meta["name"] = os.path.splitext(os.path.basename(path))[0]
        return EndgameSet(z["cells"], z["macro"], z["next_board"], z["player"], z["exact"], z["child"], z["empties"],
                          z["game_id"], z["ply"], meta)

    def strata(self) -> np.ndarray:
        """Stratum index = bucket * 6 + result_class * 2 + (player == -1)."""
        b = np.array([bucket_of(int(e)) for e in self.empties])
        r = 1 - self.exact.astype(np.int64)  # win 0 / draw 1 / loss 2
        return b * 6 + r * 2 + (self.player == -1)


def build_set(corpus: str, last: int = 5, per_stratum: int = 125, per_game: int = 2, min_empty: int = 6, max_empty: int = 16,
              max_solve: int = 15000, processes: int = 8, seed: int = 0, log=print) -> EndgameSet:
    """Balanced over BUCKETS × {win, draw, loss} × {X, O to move}: up to per_stratum positions each. Candidates are
    solved in random order until every stratum is full or max_solve positions have been solved."""
    files = sorted(glob.glob(os.path.join(corpus, "games", "games_*.npz")))
    if last:
        files = files[-last:]
    rng = np.random.default_rng(seed)
    t = time.perf_counter()
    cands = collect_candidates(files, per_game, min_empty, max_empty, rng)
    K = len(cands["empties"])
    log(f"{K} candidate positions from {len(files)} files ({time.perf_counter() - t:.0f}s)")
    order = rng.permutation(K)
    n_strata = len(BUCKETS) * 6
    chosen = {s: [] for s in range(n_strata)}
    labels = {}
    solved = 0
    t = time.perf_counter()
    for start in range(0, min(K, max_solve), 1000):
        idx = order[start : start + 1000]
        idx = idx[[bucket_of(int(cands["empties"][i])) >= 0 for i in idx]]
        for i, (v, child) in zip(idx, _solve_many(cands, idx, processes)):
            labels[i] = (v, child)
            s = bucket_of(int(cands["empties"][i])) * 6 + (1 - v) * 2 + int(cands["player"][i] == -1)
            if len(chosen[s]) < per_stratum:
                chosen[s].append(i)
        solved += len(idx)
        fill = sum(len(v) for v in chosen.values())
        log(f"  solved {solved}: {fill}/{n_strata * per_stratum} slots filled ({time.perf_counter() - t:.0f}s)")
        if all(len(v) >= per_stratum for v in chosen.values()):
            break
    sel = np.array(sorted(i for v in chosen.values() for i in v))
    exact = np.array([labels[i][0] for i in sel], dtype=np.int8)
    child = np.stack([labels[i][1] for i in sel])
    game_id = cands["file"][sel].astype(np.int64) * (1 << 20) + cands["game"][sel].astype(np.int64)
    counts = {f"{BUCKETS[b][0]}-{BUCKETS[b][1]}": [len(chosen[b * 6 + r * 2 + p]) for r in range(3) for p in range(2)] for b in range(len(BUCKETS))}
    meta = {"corpus": corpus, "corpus_files": [os.path.basename(f) for f in files], "per_stratum": per_stratum, "per_game": per_game,
            "min_empty": min_empty, "max_empty": max_empty, "seed": seed, "solved": solved, "built": time.strftime("%Y-%m-%d %H:%M"),
            "strata_counts (bucket -> [W_X, W_O, D_X, D_O, L_X, L_O])": counts}
    return EndgameSet(cands["cells"][sel], cands["macro"][sel], cands["next_board"][sel], cands["player"][sel], exact, child,
                      cands["empties"][sel], game_id, cands["ply"][sel], meta)


# ---- evaluation ---------------------------------------------------------------------------------
def cluster_bootstrap(x: np.ndarray, groups: np.ndarray, n_boot: int = 2000, seed: int = 0):
    """95 % percentile CI of mean(x) resampling whole groups (source games) with replacement."""
    _, inv = np.unique(groups, return_inverse=True)
    G = inv.max() + 1
    sums = np.bincount(inv, weights=x, minlength=G)
    cnts = np.bincount(inv, minlength=G).astype(np.float64)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, G, size=(n_boot, G))
    means = sums[pick].sum(1) / cnts[pick].sum(1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


@torch.no_grad()
def wdl_probs(fe, cells, macro, nb, player, symmetrise: bool = False) -> torch.Tensor:
    """(n, 3) win/draw/loss probabilities of a FusedEvaluator's net for the side to move."""
    n = cells.shape[0]
    done = torch.zeros(n, dtype=torch.bool, device=cells.device)
    syms = range(8) if symmetrise else (0,)
    acc = torch.zeros(n, 3, device=cells.device)
    for s in syms:
        c, m, b = apply_symmetry(s, cells, macro, nb)
        obs = encode(c, m, b, player, done, extra=getattr(fe, "extra", False))
        if fe.half:
            obs = obs.half()
        if fe.channels_last:
            obs = obs.contiguous(memory_format=torch.channels_last)
        _, v_logits, *_ = fe.net(obs)
        v_logits = v_logits.float()
        if getattr(fe, "wdl_bias", None) is not None:
            v_logits = v_logits + fe.wdl_bias
        acc += torch.softmax(v_logits, dim=1)
    return acc / len(syms)


def _tensors(es: EndgameSet, device):
    t = lambda a: torch.from_numpy(a).to(device)  # noqa: E731
    return t(es.cells), t(es.macro), t(es.next_board), t(es.player)


def _regret(es: EndgameSet, moves: np.ndarray) -> np.ndarray:
    after = es.child[np.arange(es.n), moves]
    assert (after != ILLEGAL).all(), "an evaluator chose an illegal move"
    return (es.exact.astype(np.int64) - after.astype(np.int64)).astype(np.float64)


def _row(es: EndgameSet, name: str, wdl: np.ndarray | None, scalar: np.ndarray | None, moves: np.ndarray | None, n_boot: int) -> dict:
    """Per-position metric arrays -> means with cluster CIs. wdl: (n, 3) probabilities; scalar: value in [-1, 1]."""
    y = 1 - es.exact.astype(np.int64)  # win 0 / draw 1 / loss 2
    d = {"name": name, "n": es.n}
    per = {}
    if wdl is not None:
        per["wdl_acc"] = (wdl.argmax(1) == y).astype(np.float64)
        onehot = np.eye(3)[y]
        per["brier"] = ((wdl - onehot) ** 2).sum(1)
        per["logloss"] = -np.log(np.clip(wdl[np.arange(es.n), y], 1e-9, 1))
        scalar = wdl[:, 0] - wdl[:, 2]
    if scalar is not None:
        s3 = np.where(scalar > 0.33, 1, np.where(scalar < -0.33, -1, 0))
        per["acc3"] = (s3 == es.exact).astype(np.float64)
        per["abs_err"] = np.abs(scalar - es.exact)
    if moves is not None:
        reg = _regret(es, moves)
        per["regret"] = reg
        per["optimal"] = (reg == 0).astype(np.float64)
    for k, v in per.items():
        d[k] = float(v.mean())
        d[k + "_ci"] = cluster_bootstrap(v, es.game_id, n_boot)
    d["_per"] = per
    return d


@torch.no_grad()
def evaluate(fe, es: EndgameSet, device, sims=(32, 64, 256), n_boot: int = 2000, symmetrise: bool = True,
             graph: bool = True, search_cache: dict | None = None) -> dict:
    """Score a FusedEvaluator (raw heads) and the v2 search at the given budgets on the set.

    search_cache: optional {sims: BatchedSearch} dict a repeated caller (train2.EvalKit) owns, so the
    search objects and their CUDA graphs are built once and reused instead of churned per call."""
    from .search import BatchedSearch, SearchConfig

    cells, macro, nb, player = _tensors(es, device)
    n = es.n
    done = torch.zeros(n, dtype=torch.bool, device=device)
    winner = torch.zeros(n, dtype=torch.int8, device=device)
    rows = []
    probs, _ = fe(cells, macro, nb, player, done)
    wdl = wdl_probs(fe, cells, macro, nb, player).cpu().numpy()
    rows.append(_row(es, "raw net (value head + policy argmax)", wdl, None, probs.argmax(1).cpu().numpy(), n_boot))
    if symmetrise:
        wdl_s = wdl_probs(fe, cells, macro, nb, player, symmetrise=True).cpu().numpy()
        rows.append(_row(es, "raw net, symmetry-averaged WDL", wdl_s, None, None, n_boot))
    for s in sims:
        bs = search_cache.get(s) if search_cache is not None else None
        if bs is None:
            scfg = SearchConfig(n_sims=s, mode="gumbel", gumbel_scale=0.0, cuda_graph=graph and device.type == "cuda", depth_cap=min(s, 24))
            bs = BatchedSearch(fe, n, scfg, device)
            if search_cache is not None:
                search_cache[s] = bs
        r = bs.search(cells, macro, nb, player, done, winner, selfplay=False)
        rows.append(_row(es, f"search {s} sims", None, r.root_value.cpu().numpy(), r.action.cpu().numpy(), n_boot))
    return {"rows": rows, "n": n}


def evaluate_rollout(player_fn, es: EndgameSet, n_boot: int = 2000) -> dict:
    """Score an arbitrary batch player (e.g. RolloutPlayer) on action regret; player_fn(BatchUTTT) -> moves."""
    from .batch import BatchUTTT

    g = BatchUTTT(es.n, "cpu")
    g.cells[:] = torch.from_numpy(es.cells)
    g.macro[:] = torch.from_numpy(es.macro)
    g.next_board[:] = torch.from_numpy(es.next_board)
    g.player[:] = torch.from_numpy(es.player)
    moves = player_fn(g).cpu().numpy()
    return _row(es, "rollout", None, None, moves, n_boot)


def breakdown(es: EndgameSet, row: dict, key: str) -> dict:
    """Metric `key` of one evaluator row by empties bucket, exact result, side and free-move status."""
    per = row["_per"][key]
    out = {}
    b = np.array([bucket_of(int(e)) for e in es.empties])
    for k, (lo, hi) in enumerate(BUCKETS):
        m = b == k
        if m.any():
            out[f"empties {lo}-{hi}"] = (float(per[m].mean()), int(m.sum()))
    for v, nm in ((1, "mover wins"), (0, "draw"), (-1, "mover loses")):
        m = es.exact == v
        if m.any():
            out[nm] = (float(per[m].mean()), int(m.sum()))
    for p, nm in ((1, "X to move"), (-1, "O to move")):
        m = es.player == p
        out[nm] = (float(per[m].mean()), int(m.sum()))
    for f, nm in ((True, "free move"), (False, "sent to a board")):
        m = (es.next_board < 0) == f
        if m.any():
            out[nm] = (float(per[m].mean()), int(m.sum()))
    return out


def format_report(es: EndgameSet, res: dict, extra_rows: list | None = None) -> str:
    def ci(d, k):
        return f"{100 * d[k]:5.1f} [{100 * d[k + '_ci'][0]:4.1f},{100 * d[k + '_ci'][1]:4.1f}]" if k in d else " " * 18

    lines = [f"{'evaluator':38s} {'WDL acc %':>18s} {'Brier':>8s} {'logloss':>8s} {'3-way %':>18s} {'|err|':>6s} {'regret':>18s} {'optimal %':>18s}"]
    for d in res["rows"] + (extra_rows or []):
        br = f"{d['brier']:8.3f}" if "brier" in d else " " * 8
        ll = f"{d['logloss']:8.3f}" if "logloss" in d else " " * 8
        ae = f"{d['abs_err']:6.3f}" if "abs_err" in d else " " * 6
        rg = f"{d['regret']:5.3f} [{d['regret_ci'][0]:4.3f},{d['regret_ci'][1]:4.3f}]" if "regret" in d else " " * 18
        lines.append(f"{d['name']:38s} {ci(d, 'wdl_acc'):>18s} {br} {ll} {ci(d, 'acc3'):>18s} {ae} {rg:>18s} {ci(d, 'optimal'):>18s}")
    return "\n".join(lines)


def format_breakdown(es: EndgameSet, rows: list, key: str, title: str) -> str:
    names = [r["name"] for r in rows]
    bds = [breakdown(es, r, key) for r in rows]
    lines = [f"{title} by stratum: " + " | ".join(names)]
    for k in bds[0]:
        n = bds[0][k][1]
        lines.append(f"  {k:16s} (n={n:4d}): " + "  ".join(f"{100 * b[k][0]:5.1f}" if key != "regret" else f"{b[k][0]:5.3f}" for b in bds))
    return "\n".join(lines)
