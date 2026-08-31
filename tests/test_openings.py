"""Opening suite: canonicalisation, suite construction, scripted paired play, pair bootstrap."""
import os
import sys
import tempfile

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.arena import RandomPlayer, SearchPlayer  # noqa: E402
from uttt.batch import SYM_CELL  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.model import UniformEvaluator  # noqa: E402
from uttt.openings import (Suite, bootstrap_mean_ci, build_suite, canonical, canonical_keys, format_report,  # noqa: E402
                           orbit_representatives, play_openings, play_paired, random_openings, summarize)
from uttt.search import SearchConfig  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def test_canonical():
    rng = np.random.default_rng(0)
    seqs = random_openings(50, 4, rng)
    for s in seqs:
        assert canonical(s) == tuple(s)  # random_openings returns canonical forms
        for sym in range(8):
            img = [int(SYM_CELL[sym, m]) for m in s]
            assert canonical(img) == tuple(s), (s, sym, img)
            g = UTTT()
            for m in img:
                g.play(m)  # symmetric images are legal
    assert len({tuple(s) for s in seqs}) == 50
    keys = canonical_keys(np.array(seqs))
    assert len(np.unique(keys)) == 50
    reps = orbit_representatives()
    assert reps[0] == 0 and 40 in reps and len(reps) == 15
    assert all(canonical([m]) == (r,) for r in reps for m in SYM_CELL[:, r].tolist())
    print("canonicalisation ok")


def synthetic_corpus(tmp, n_files=3, games=400, seed=0):
    """Random games in the persisted format (moves padded with -1)."""
    rng = np.random.default_rng(seed)
    os.makedirs(os.path.join(tmp, "games"))
    for k in range(n_files):
        moves = np.full((games, 82), -1, dtype=np.int8)
        lengths = np.zeros(games, dtype=np.int64)
        for i in range(games):
            g = UTTT()
            # bias the first move so the natural suite has a frequency structure
            first = 40 if rng.random() < 0.7 else int(rng.choice(g.legal_moves()))
            g.play(first)
            moves[i, 0] = first
            while not g.done:
                m = int(rng.choice(g.legal_moves()))
                moves[i, g.move_count] = m
                g.play(m)
            lengths[i] = g.move_count
        np.savez_compressed(os.path.join(tmp, "games", f"games_{k:04d}.npz"), moves=moves, lengths=lengths,
                            winners=np.zeros(games, np.int8), reasons=np.zeros(games, np.int8), root_values=np.zeros((games, 82), np.float16))


def test_build_and_io():
    with tempfile.TemporaryDirectory() as tmp:
        synthetic_corpus(tmp)
        suite = build_suite(tmp, n_natural=30, n_random=40, plies=4, last=2, seed=1)
        assert suite.counts() == {"empty": 1, "orbits": 15, "natural": 30, "random": 40}
        assert suite.meta["corpus_games"] == 800 and len(suite.meta["corpus_files"]) == 2
        seqs = suite.sequences()
        assert seqs[0] == [] and [s[0] for s in seqs[1:16]] == orbit_representatives()
        assert len({tuple(s) for s in seqs}) == suite.n  # all distinct
        assert all(canonical(s) == tuple(s) for s in seqs)
        nat = [s for s, nm in zip(seqs, suite.names) if nm == "natural"]
        assert sum(s[0] == 40 for s in nat) >= 15  # frequency-weighted: the common first move dominates
        path = os.path.join(tmp, "s.npz")
        suite.save(path)
        s2 = Suite.load(path)
        assert np.array_equal(s2.moves, suite.moves) and np.array_equal(s2.names, suite.names) and s2.meta["name"] == "s"
        sub = s2.subset(10)
        assert sub.counts() == {"empty": 1, "orbits": 10, "natural": 10, "random": 10}
        assert sub.ids().tolist() == [0] + list(range(1, 11)) + list(range(16, 26)) + list(range(46, 56))
        assert sub.sequences() == [s2.sequences()[i] for i in sub.ids()]
    print("build / save / load / subset ok")


def test_scripted_openings():
    torch.manual_seed(0)
    rng = np.random.default_rng(2)
    seqs = [[]] + [[m] for m in orbit_representatives()] + random_openings(20, 4, rng) + random_openings(5, 6, rng)
    names = ["empty"] + ["orbits"] * 15 + ["random"] * 25
    suite = Suite.from_sequences(seqs, names)
    assert suite.max_len == 6
    # a player that records the states it saw at each ply lets us check the openings were forced
    seen = []

    class Recorder(RandomPlayer):
        def act(self, g):
            seen.append(g.cells.clone())
            return super().act(g)

    g = play_openings(Recorder(DEV), Recorder(DEV), suite, DEV)
    assert bool(g.done.all())
    for i, s in enumerate(seqs):
        ref = UTTT()
        for m in s:
            ref.play(m)
        cells_after_opening = seen[len(s)][i].cpu().numpy()
        assert np.array_equal(cells_after_opening, ref.cells), i
    print("scripted openings ok")


def test_paired_same_player():
    """The same deterministic player on both sides scores exactly 0.5 on every pair (games are identical)."""
    torch.manual_seed(0)
    rng = np.random.default_rng(3)
    suite = Suite.from_sequences([[]] + random_openings(31, 4, rng), ["empty"] + ["random"] * 31)
    cfg = SearchConfig(n_sims=8, mode="gumbel", gumbel_scale=0.0, cuda_graph=DEV.startswith("cuda"), depth_cap=8)
    ev = UniformEvaluator(DEV)
    pa, pb = SearchPlayer(ev, suite.n, cfg, DEV), SearchPlayer(ev, suite.n, cfg, DEV)
    r = play_paired(pa, pb, suite, DEV)
    assert np.array_equal(r.score_ax, 1 - r.score_ao)
    assert np.all(r.pair_score == 0.5)
    s = summarize(r)
    assert s["overall"]["score"] == 0.5 and s["overall"]["ci"] == (0.5, 0.5)
    assert s["suites"]["empty"]["ci"] is None and s["suites"]["empty"]["pairs"] == 1
    assert s["overall"]["pairs_split"] == 32
    print(format_report(s))
    print("same-player pairing ok")


def test_search_beats_random():
    torch.manual_seed(0)
    rng = np.random.default_rng(4)
    suite = Suite.from_sequences(random_openings(64, 4, rng), ["random"] * 64)
    cfg = SearchConfig(n_sims=32, mode="gumbel", gumbel_scale=0.0, cuda_graph=DEV.startswith("cuda"), depth_cap=12)
    r = play_paired(SearchPlayer(UniformEvaluator(DEV), suite.n, cfg, DEV), RandomPlayer(DEV), suite, DEV)
    s = summarize(r)
    print(format_report(s))
    assert s["overall"]["ci"][0] > 0.6, s["overall"]
    assert 0 <= s["overall"]["x_share"] <= 1 and s["overall"]["games"] == 128


def test_bootstrap():
    rng = np.random.default_rng(5)
    cover = 0
    for _ in range(200):
        x = rng.choice([0.0, 0.5, 1.0], size=100, p=[0.3, 0.2, 0.5])
        lo, hi = bootstrap_mean_ci(x, n_boot=1000, seed=int(rng.integers(1 << 30)))
        cover += lo <= 0.6 <= hi
    assert 170 <= cover <= 200, cover  # nominal 95 %
    assert bootstrap_mean_ci(np.array([1.0])) is None
    print(f"bootstrap coverage {cover / 200:.2f}")


if __name__ == "__main__":
    test_canonical()
    test_build_and_io()
    test_scripted_openings()
    test_paired_same_player()
    test_search_beats_random()
    test_bootstrap()
    print("ok")
