"""Fixed opening suite for paired evaluation (PLAN2 §5 step 1a; REVIEW-codex finding 3).

A suite is a frozen list of opening move sequences, each tagged with a sub-suite name:

  empty    the empty board (1 opening)
  orbits   one representative of each of the 15 first-move symmetry classes (length 1)
  natural  canonical 4-ply prefixes sampled ∝ frequency from a frozen self-play corpus
  random   uniformly random legal 4-ply sequences (deliberately broad)

Every opening is played twice with colours swapped (A as X, then A as O); the unit of
analysis is the opening *pair*, scored (s_AX + s_AO) / 2 for A, and confidence intervals
are bootstrapped over pairs. Natural and random openings are canonicalised under the D4
symmetry group before de-duplication, so no two openings are symmetric images of each other.

With deterministic players (Gumbel scale 0) every opening yields exactly one game per colour,
so the number of openings is the sample size; the suite file is meant to be built once and
reused for every checkpoint and anchor (its index is the opening id). Results are bit-identical
within a process; across processes cuDNN's fp16 algorithm choice can flip a few games (observed
62.9 % vs 63.3 % on 1032 games), which is well inside the bootstrap CI but not zero.
"""
from __future__ import annotations

import glob
import json
import os
import time
from dataclasses import dataclass

import numpy as np
import torch

from .batch import SYM_CELL, BatchUTTT
from .game import UTTT

SUITES = ("empty", "orbits", "natural", "random")
_SYM = SYM_CELL.numpy()  # (8, 81)


# ---- symmetry canonicalisation ----------------------------------------------------------
def canonical_keys(seqs: np.ndarray) -> np.ndarray:
    """Lexicographically smallest D4 image of each move sequence, encoded as one int64 key.

    seqs: (G, P) engine-order moves, P <= 8 (81**8 < 2**63)."""
    seqs = np.asarray(seqs, dtype=np.int64)
    P = seqs.shape[1]
    weights = 81 ** np.arange(P - 1, -1, -1, dtype=np.int64)
    images = _SYM[:, seqs]  # (8, G, P)
    return (images * weights).sum(-1).min(0)


def decode_key(key: int, plies: int) -> list[int]:
    out = []
    for _ in range(plies):
        key, m = divmod(int(key), 81)
        out.append(m)
    return out[::-1]


def canonical(seq) -> tuple[int, ...]:
    seq = list(seq)
    if not seq:
        return ()
    return tuple(decode_key(canonical_keys(np.array([seq]))[0], len(seq)))


def orbit_representatives() -> list[int]:
    """The 15 first-move symmetry classes, each by its smallest member, in ascending order."""
    reps = sorted({int(_SYM[:, m].min()) for m in range(81)})
    assert len(reps) == 15
    return reps


# ---- the transforms themselves (PLAN6 E1: a canonical key is only half the answer; the frame change that
# produced it must travel with it, or lines assembled from several canonical nodes mix coordinate frames) ----
def _group_tables():
    comp = np.empty((8, 8), dtype=np.int64)
    inv = np.empty(8, dtype=np.int64)
    for a in range(8):
        for b in range(8):
            image = _SYM[a][_SYM[b]]  # apply b, then a
            (comp[a, b],) = [s for s in range(8) if np.array_equal(_SYM[s], image)]
        (inv[a],) = [s for s in range(8) if np.array_equal(_SYM[a][_SYM[s]], np.arange(81))]
    return comp, inv


_COMPOSE, _INVERSE = _group_tables()


def compose(a: int, b: int) -> int:
    """Index of the symmetry "b first, then a": SYM[compose(a, b)][m] == SYM[a][SYM[b][m]]."""
    return int(_COMPOSE[a, b])


def inverse(g: int) -> int:
    return int(_INVERSE[g])


def transform_move(g: int, m: int) -> int:
    """Image of move m under symmetry g (the same table the batched engine uses)."""
    return int(_SYM[g, m])


def canonical_transforms(seqs: np.ndarray):
    """canonical_keys plus, per sequence, the index g of a symmetry that maps it onto its canonical form
    (the smallest such index, so the choice is deterministic; with a non-trivial stabiliser several g work)."""
    seqs = np.asarray(seqs, dtype=np.int64)
    P = seqs.shape[1]
    weights = 81 ** np.arange(P - 1, -1, -1, dtype=np.int64)
    enc = (_SYM[:, seqs] * weights).sum(-1)  # (8, G)
    return enc.min(0), enc.argmin(0)


def canonicalise(seq) -> tuple[tuple[int, ...], int]:
    """(canonical sequence, g) with canonical[i] == transform_move(g, seq[i]) for every i."""
    seq = list(seq)
    if not seq:
        return (), 0
    keys, gs = canonical_transforms(np.array([seq]))
    return tuple(decode_key(keys[0], len(seq))), int(gs[0])


def reply_orbits(seq, legal: np.ndarray, share: np.ndarray, q: np.ndarray) -> list[dict]:
    """Group the legal replies to `seq` by the D4 orbit of the sequence they produce. Per orbit: the representative,
    every member, the summed visit share, the visit-weighted Q, the child's canonical key and the transform that
    maps `seq + [representative]` onto that child. Sorted by share, descending. Members of one orbit are the same
    reply up to a symmetry that fixes `seq`, so ranking replies without this grouping can list one alternative
    several times (PLAN6 §1 item 2).

    The representative is the orbit's smallest member. For a canonical `seq` that is exactly the member whose
    sequence is the child's canonical form (the minimising symmetry must fix `seq`, whose encoding dominates, so
    canonical(seq + [a]) = seq + [min over the stabiliser of g(a)]): the child key literally extends the parent's,
    the stored transform is the identity, and a line read off successive nodes stays in one frame. Choosing the
    most-visited member instead (the pre-PLAN6 book) put the displayed move and the child's frame at odds."""
    seq = list(seq)
    moves = np.flatnonzero(np.asarray(legal))
    if moves.size == 0:
        return []
    keys, gs = canonical_transforms(np.array([seq + [int(a)] for a in moves]))
    out = []
    for key in np.unique(keys):
        members = moves[keys == key]  # ascending
        sh = np.asarray(share)[members]
        rep = int(members[0])
        tot = float(sh.sum())
        qw = float((np.asarray(q)[members] * sh).sum() / tot) if tot > 0 else float(np.asarray(q)[members].mean())
        out.append({"move": rep, "members": [int(m) for m in members], "share": tot, "q": qw,
                    "child": " ".join(map(str, decode_key(key, len(seq) + 1))), "g": int(gs[list(moves).index(rep)])})
    out.sort(key=lambda o: (-o["share"], o["move"]))
    return out


# ---- suite construction --------------------------------------------------------------------
def natural_openings(corpus_files: list[str], k: int, plies: int, rng: np.random.Generator):
    """k distinct canonical `plies`-move prefixes drawn without replacement ∝ corpus frequency.

    Returns (sequences, number of corpus games used)."""
    pre = np.concatenate([np.load(f)["moves"][:, :plies] for f in corpus_files]).astype(np.int64)
    pre = pre[(pre >= 0).all(1)]
    keys, counts = np.unique(canonical_keys(pre), return_counts=True)
    if len(keys) < k:
        raise ValueError(f"corpus has only {len(keys)} distinct canonical {plies}-ply openings, {k} requested")
    pick = rng.choice(len(keys), size=k, replace=False, p=counts / counts.sum())
    return [decode_key(keys[i], plies) for i in pick], int(counts.sum())


def random_openings(k: int, plies: int, rng: np.random.Generator, exclude=()) -> list[list[int]]:
    """k distinct canonical sequences of `plies` uniformly random legal moves, none of them in `exclude`."""
    seen, out = {tuple(e) for e in exclude}, []
    while len(out) < k:
        g = UTTT()
        seq = []
        for _ in range(plies):
            m = int(rng.choice(g.legal_moves()))
            g.play(m)
            seq.append(m)
        c = canonical(seq)
        if c not in seen:
            seen.add(c)
            out.append(list(c))
    return out


@dataclass
class Suite:
    moves: np.ndarray  # (K, L) int8, padded with -1
    lengths: np.ndarray  # (K,) int64
    names: np.ndarray  # (K,) str: sub-suite of each opening
    meta: dict

    @property
    def n(self) -> int:
        return int(self.moves.shape[0])

    @property
    def max_len(self) -> int:
        return int(self.moves.shape[1])

    def ids(self) -> np.ndarray:
        return self.meta.get("ids", np.arange(self.n))

    def subset(self, cap: int) -> "Suite":
        """Keep at most `cap` openings of every sub-suite (the first ones, i.e. a fixed random sample)."""
        keep = np.concatenate([np.flatnonzero(self.names == s)[:cap] for s in SUITES if (self.names == s).any()])
        keep.sort()
        meta = dict(self.meta, ids=self.ids()[keep], subset_cap=cap)
        return Suite(self.moves[keep], self.lengths[keep], self.names[keep], meta)

    def sequences(self) -> list[list[int]]:
        return [[int(m) for m in self.moves[i, : self.lengths[i]]] for i in range(self.n)]

    def counts(self) -> dict:
        return {s: int((self.names == s).sum()) for s in SUITES if (self.names == s).any()}

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        meta = {k: v for k, v in self.meta.items() if k != "ids"}
        np.savez(path, moves=self.moves, lengths=self.lengths, names=self.names, meta=np.array(json.dumps(meta)))

    @staticmethod
    def load(path: str) -> "Suite":
        z = np.load(path, allow_pickle=False)
        meta = json.loads(str(z["meta"]))
        meta["name"] = os.path.splitext(os.path.basename(path))[0]
        return Suite(z["moves"], z["lengths"], z["names"].astype(str), meta)

    @staticmethod
    def from_sequences(seqs: list[list[int]], names: list[str], meta: dict | None = None) -> "Suite":
        L = max([len(s) for s in seqs] + [1])
        moves = np.full((len(seqs), L), -1, dtype=np.int8)
        for i, s in enumerate(seqs):
            moves[i, : len(s)] = s
        return Suite(moves, np.array([len(s) for s in seqs], dtype=np.int64), np.array(names, dtype=str), meta or {})


def build_suite(corpus: str, n_natural: int = 250, n_random: int = 250, plies: int = 4, last: int = 20, seed: int = 0) -> Suite:
    """empty + 15 orbits + n_natural natural + n_random random openings; natural ones from the last
    `last` game files of <corpus>/games (the frozen source distribution)."""
    files = sorted(glob.glob(os.path.join(corpus, "games", "games_*.npz")))
    if last:
        files = files[-last:]
    rng = np.random.default_rng(seed)
    seqs, names = [[]], ["empty"]
    for m in orbit_representatives():
        seqs.append([m])
        names.append("orbits")
    nat, n_games = natural_openings(files, n_natural, plies, rng)
    seqs += nat
    names += ["natural"] * len(nat)
    rnd = random_openings(n_random, plies, rng, exclude=nat)
    seqs += rnd
    names += ["random"] * len(rnd)
    for s in seqs:  # every opening must be a legal, unfinished sequence
        g = UTTT()
        for m in s:
            g.play(m)
        assert not g.done
    meta = {"corpus": corpus, "corpus_files": [os.path.basename(f) for f in files], "corpus_games": n_games,
            "plies": plies, "seed": seed, "built": time.strftime("%Y-%m-%d %H:%M")}
    return Suite.from_sequences(seqs, names, meta)


# ---- paired play --------------------------------------------------------------------------
@torch.no_grad()
def play_openings(px, po, suite: Suite, device, rule: str = "count") -> BatchUTTT:
    """One game per opening, px as X and po as O; the opening moves are scripted, then the players move."""
    g = BatchUTTT(suite.n, device, rule)
    scripted = torch.from_numpy(suite.moves.astype(np.int64)).to(device)
    lens = torch.from_numpy(suite.lengths).to(device)
    ply = 0
    while not bool(g.done.all()):
        m = (px if ply % 2 == 0 else po).act(g)
        if ply < suite.max_len:
            m = torch.where(ply < lens, scripted[:, ply], m)
        g.step(m)
        ply += 1
    return g


@dataclass
class PairedResult:
    """Per-opening outcomes of a colour-swapped match; A's score in {1, 0.5, 0} per game."""
    suite: Suite
    score_ax: np.ndarray  # A's score with A as X
    score_ao: np.ndarray  # A's score with A as O
    reason_ax: np.ndarray  # end reason (1 line, 2 count, 3 equal) per game
    reason_ao: np.ndarray
    len_ax: np.ndarray
    len_ao: np.ndarray
    rule: str = "count"  # the rule these games were played under

    @property
    def pair_score(self) -> np.ndarray:
        return 0.5 * (self.score_ax + self.score_ao)


def play_paired(pa, pb, suite: Suite, device, rule: str = "count") -> PairedResult:
    """pa / pb: players (objects with .act(BatchUTTT)) built for batch size suite.n."""
    g1 = play_openings(pa, pb, suite, device, rule)
    g2 = play_openings(pb, pa, suite, device, rule)
    w1 = g1.winner.cpu().numpy().astype(np.float64)
    w2 = g2.winner.cpu().numpy().astype(np.float64)
    return PairedResult(suite, (1 + w1) / 2, (1 - w2) / 2, g1.end_reason.cpu().numpy(), g2.end_reason.cpu().numpy(),
                        g1.move_count.cpu().numpy(), g2.move_count.cpu().numpy(), rule)


# ---- statistics ---------------------------------------------------------------------------
def bootstrap_mean_ci(x: np.ndarray, n_boot: int = 4000, seed: int = 0, level: float = 0.95):
    """Percentile bootstrap CI of the mean of x (resampling its elements, i.e. opening pairs)."""
    x = np.asarray(x, dtype=np.float64)
    if x.size < 2:
        return None
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, x.size, size=(n_boot, x.size))].mean(1)
    a = (1 - level) / 2
    return float(np.quantile(means, a)), float(np.quantile(means, 1 - a))


def elo(score: float) -> float:
    s = min(max(score, 1e-3), 1 - 1e-3)
    return float(400 * np.log10(s / (1 - s)))


def _stats(r: PairedResult, m: np.ndarray, n_boot: int) -> dict:
    ps = r.pair_score[m]
    ci = bootstrap_mean_ci(ps, n_boot)
    sc = float(ps.mean())
    sx, so = r.score_ax[m], r.score_ao[m]
    reasons = np.concatenate([r.reason_ax[m], r.reason_ao[m]])
    return {"pairs": int(m.sum()), "games": int(2 * m.sum()), "score": sc, "ci": ci, "elo": elo(sc),
            "elo_ci": (elo(ci[0]), elo(ci[1])) if ci else None,
            "as_x": float(sx.mean()), "as_o": float(so.mean()),
            "x_share": float(np.concatenate([sx, 1 - so]).mean()),  # first player's score over all games
            "draws": float(np.concatenate([sx == 0.5, so == 0.5]).mean()),
            "pairs_won": int((ps > 0.5).sum()), "pairs_split": int((ps == 0.5).sum()), "pairs_lost": int((ps < 0.5).sum()),
            "end_line": float((reasons == 1).mean()), "end_count": float((reasons == 2).mean()), "end_equal": float((reasons == 3).mean()),
            "mean_len": float(np.concatenate([r.len_ax[m], r.len_ao[m]]).mean())}


def summarize(r: PairedResult, n_boot: int = 4000) -> dict:
    out = {"rule": r.rule, "overall": _stats(r, np.ones(r.suite.n, dtype=bool), n_boot), "suites": {}}
    for s in SUITES:
        m = r.suite.names == s
        if m.any():
            out["suites"][s] = _stats(r, m, n_boot)
    return out


def format_report(summary: dict) -> str:
    def row(name, d):
        ci = f"[{100 * d['ci'][0]:5.1f}, {100 * d['ci'][1]:5.1f}]" if d["ci"] else "     n/a      "
        el = f"{d['elo']:+5.0f} [{d['elo_ci'][0]:+4.0f}, {d['elo_ci'][1]:+4.0f}]" if d["ci"] else "n/a"
        return (f"  {name:8s} {d['pairs']:5d}  {100 * d['score']:5.1f}%  {ci}  {el:19s} "
                f"{100 * d['as_x']:5.1f}% {100 * d['as_o']:5.1f}%   {100 * d['x_share']:5.1f}%  {100 * d['draws']:5.1f}%   "
                f"{d['pairs_won']:4d} /{d['pairs_split']:4d} /{d['pairs_lost']:4d}")

    lines = ["  suite    pairs  score   95% CI (pairs)    Elo  95% CI          as X   as O   | X share  draws |  pairs won/split/lost"]
    for s, d in summary["suites"].items():
        lines.append(row(s, d))
    o = summary["overall"]
    lines.append(row("all", o))
    lines.append(f"  end reasons: line {100 * o['end_line']:.1f}%  count {100 * o['end_count']:.1f}%  equal {100 * o['end_equal']:.1f}%  |  "
                 f"mean length {o['mean_len']:.1f}  |  rule {summary.get('rule', 'count')}")
    return "\n".join(lines)


def per_opening_records(r: PairedResult) -> list[dict]:
    ids = r.suite.ids()
    return [{"id": int(ids[i]), "suite": str(r.suite.names[i]), "moves": [int(m) for m in r.suite.moves[i, : r.suite.lengths[i]]],
             "a_as_x": float(r.score_ax[i]), "a_as_o": float(r.score_ao[i])} for i in range(r.suite.n)]
