"""The rule's boundaries: every place two rules could mix, and the refusal that stops them
(PLAN7 §7e M2 rows 1, 6, 8, 9, 18).

    .venv/Scripts/python.exe tests/test_rules_boundaries.py

tests/test_rules.py checks that the two rules are what they claim to be. This file checks the seams:

1. Resume.        A run whose config.json records one rule cannot be resumed under another, and the refusal
                  lands before config_resume_*.json is written and before any checkpoint or buffer is read.
                  A config.json with no `rule` key is a pre-K1 run, i.e. count. Where config.json cannot
                  speak -- an orphaned run directory, or a checkpoint copied in from another run -- the
                  checkpoint's own recorded rule is the gate, and an ambiguous directory is refused.
2. Search cache.  uttt.endgame.evaluate's cache is keyed by (sims, rule), a cache poisoned with a search of
                  the wrong rule is caught rather than used, and one keyed the old way (by sims alone) is
                  refused rather than silently ignored.
3. Explicit rule. evaluate_rollout takes its rule as an argument and checks it against the set's.
4. relabel.       The count -> draw re-reading is exactly "reason 2 becomes reason 3, winner becomes 0", and
                  the reverse direction is refused with the reason (it needs a replay, not a rebuild).
5. Corpora.       The rule a corpus was generated under is read from the game files' tag, else from
                  config.json; a directory with neither is refused unless --corpus_rule names it, and one
                  mixing tagged and untagged files is refused unless config.json vouches for the untagged.
6. Tools.         A count-only surrogate player is refused under `draw`; a paired match file of one rule
                  cannot be attached to a book of the other.
7. Draw sample.   tools/principles.py samples the draws uniformly over the window, reproducibly, and not at
                  all when the window fits the cap.
8. Terminal backup. A position one move from a count-decided terminal reads as a win for the mover under
                  `count` and a draw under `draw` at the root of BOTH search implementations.
"""
import glob
import json
import os
import sys
import tempfile
from dataclasses import asdict

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
sys.path.insert(0, os.path.dirname(__file__))
from book import paired_stats  # noqa: E402
from corpus_stats import corpus_rule, games_rule, relabel  # noqa: E402
from openings import player as openings_player  # noqa: E402
from principles import sample_draws  # noqa: E402
from test_rules import random_endgame  # noqa: E402
from uttt.endgame import EndgameSet, evaluate, evaluate_rollout  # noqa: E402
from uttt.game import FULL, UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.mcts import BatchedMCTS, MCTSConfig  # noqa: E402
from uttt.model import NetConfig, ResNet, UniformEvaluator  # noqa: E402
from uttt.rollout import RolloutPlayer  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.solver import solve_children  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")
NO_LINE_FILL = [1, -1, 1, 1, -1, -1, -1, 1, 0]  # + one stone on cell 8: the board fills with no local winner


def _expect(exc_types, fn, *args, **kw):
    """Run fn and return the exception message; fail if it did not raise one of exc_types."""
    try:
        fn(*args, **kw)
    except exc_types as e:
        return str(getattr(e, "code", None) or e)
    raise AssertionError(f"{getattr(fn, '__name__', fn)} accepted what it should have refused")


# ---- 1. a cross-rule resume ------------------------------------------------------------------------
def _write_run(run, cfg_dict):
    os.makedirs(run, exist_ok=True)
    with open(os.path.join(run, "config.json"), "w") as f:
        json.dump(cfg_dict, f)


def test_cross_rule_resume_is_refused_before_anything_is_written():
    from uttt.train2 import TrainConfig, main

    with tempfile.TemporaryDirectory() as tmp:
        run = os.path.join(tmp, "r")
        _write_run(run, dict(asdict(TrainConfig(run=run)), _provenance={"rule": "count"}))
        with open(os.path.join(run, "latest.pt"), "wb") as f:
            f.write(b"this is not a checkpoint")  # a late refusal would trip over this first
        msg = _expect(ValueError, main, TrainConfig(run=run, rule="draw", device="cpu"))
        assert "count" in msg and "draw" in msg, msg
        assert sorted(os.listdir(run)) == ["config.json", "latest.pt"], \
            f"the refusal came after something was written: {sorted(os.listdir(run))}"
        assert not glob.glob(os.path.join(run, "config_resume_*.json"))
        assert not os.path.exists(os.path.join(run, "games"))
    print("a cross-rule resume is refused before config_resume_*.json, the games directory or any checkpoint is touched")


def test_a_config_without_a_rule_key_is_a_count_run():
    from uttt.train2 import TrainConfig, main

    with tempfile.TemporaryDirectory() as tmp:
        run = os.path.join(tmp, "r")
        legacy = {k: v for k, v in asdict(TrainConfig(run=run)).items() if k != "rule"}  # a pre-K1 config.json
        _write_run(run, legacy)
        msg = _expect(ValueError, main, TrainConfig(run=run, rule="draw", device="cpu"))
        assert "count" in msg, msg
        # and the same run resumes under count: the gate is the rule, not the presence of a config
        cfg = TrainConfig(run=run, rule="count", device=DEV, iters=0, games=4, steps=1, sims=2, buffer=1000,
                          blocks=1, filters=8, eval_every=0, suite="", endgame_set="", anchors="", save_buffer_every=0)
        main(cfg)
        assert os.path.exists(os.path.join(run, "DONE"))
        resumes = glob.glob(os.path.join(run, "config_resume_*.json"))
        assert len(resumes) == 1, resumes
        with open(resumes[0]) as f:
            info = json.load(f)
        assert info["rule"] == "count" and info["_provenance"]["rule"] == "count"
        assert info["_provenance"]["search_config"]["gumbel_scale"] == 1.0, info["_provenance"]["search_config"]
        assert info["_provenance"]["search_config"]["n_sims"] == 2
        with open(os.path.join(run, "config.json")) as f:
            assert {k: v for k, v in json.load(f).items() if not k.startswith("_")} == legacy, "the original config was clobbered"
    print("a config.json with no rule key means count: draw refused, count resumed, and the resolved search "
          "configuration (gumbel_scale 1.0 included) is recorded in _provenance")


def _tiny(run, **kw):
    """A TrainConfig small enough that main() can build its net, buffer and self-play on the CPU."""
    from uttt.train2 import TrainConfig

    return TrainConfig(run=run, device="cpu", iters=0, games=4, steps=1, sims=2, buffer=1000, blocks=1, filters=8,
                       eval_every=0, suite="", endgame_set="", anchors="", save_buffer_every=0, **kw)


def _stub_ckpt(run, name="latest.pt", rule="count", drop_rule=False):
    """A checkpoint carrying only what the rule gate reads: train2 saves the TrainConfig as "cfg"."""
    from uttt.train2 import TrainConfig

    cfg = asdict(TrainConfig(run=run, rule=rule))
    if drop_rule:  # a pre-K1 checkpoint, written before TrainConfig had the field
        cfg.pop("rule")
    torch.save({"net": {}, "cfg": cfg, "iter": 7}, os.path.join(run, name))


def test_a_checkpoint_is_gated_even_when_config_json_cannot_speak():
    """The refusal above is keyed on config.json; these three directories have a checkpoint it does not
    cover, and each one would have resumed one rule's weights under the other (M2 rebuttal (c))."""
    from uttt.train2 import TrainConfig, main

    with tempfile.TemporaryDirectory() as tmp:
        run = os.path.join(tmp, "r")
        os.makedirs(run)
        # (a) a checkpoint and no config.json: nothing in the directory records the rule it was made under,
        #     so the directory is ambiguous and is refused under BOTH rules -- the complaint is the missing
        #     config, not a mismatch -- before anything at all is written
        _stub_ckpt(run, rule="draw")
        for rule in ("count", "draw"):
            msg = _expect(ValueError, main, _tiny(run, rule=rule))
            assert "config.json" in msg and "latest.pt" in msg, msg
        assert sorted(os.listdir(run)) == ["latest.pt"], sorted(os.listdir(run))
        # latest_full.pt alone is the same directory, and the message names it
        os.replace(os.path.join(run, "latest.pt"), os.path.join(run, "latest_full.pt"))
        msg = _expect(ValueError, main, _tiny(run, rule="draw"))
        assert "latest_full.pt" in msg, msg
        os.replace(os.path.join(run, "latest_full.pt"), os.path.join(run, "latest.pt"))
        # (b) a draw checkpoint copied into a count run, whose config.json AGREES with the invocation: the
        #     config gate cannot see this one at all
        _write_run(run, dict(asdict(TrainConfig(run=run, rule="count")), _provenance={"rule": "count"}))
        msg = _expect(ValueError, main, _tiny(run, rule="count"))
        assert "'draw'" in msg and "'count'" in msg and "latest.pt" in msg, msg
        assert sorted(os.listdir(run)) == ["config.json", "latest.pt"], sorted(os.listdir(run))
        assert not glob.glob(os.path.join(run, "config_resume_*.json"))
        assert not os.path.exists(os.path.join(run, "games"))
        # (c) a pre-K1 checkpoint carries no rule in its cfg: it is count, exactly as a config.json without
        #     one is, and a draw run refuses it
        _write_run(run, dict(asdict(TrainConfig(run=run, rule="draw")), _provenance={"rule": "draw"}))
        _stub_ckpt(run, drop_rule=True)
        msg = _expect(ValueError, main, _tiny(run, rule="draw"))
        assert "'count'" in msg and "latest.pt" in msg, msg
        # (d) and when the checkpoint, the config and the invocation all agree the gate passes: what stops
        #     this run is the stub checkpoint's missing tensors, after the provenance was written
        _write_run(run, dict(asdict(TrainConfig(run=run, rule="count")), _provenance={"rule": "count"}))
        _stub_ckpt(run, rule="count")
        msg = _expect(Exception, main, _tiny(run, rule="count"))
        assert "rule" not in msg, msg
        assert len(glob.glob(os.path.join(run, "config_resume_*.json"))) == 1, "the gate did not pass"
    print("a checkpoint is gated on its own recorded rule: an orphan without config.json is refused under "
          "either rule, a copied-in checkpoint of the other rule is refused beside an agreeing config.json, "
          "a pre-K1 checkpoint counts as count, and an agreeing one passes")


# ---- 2 and 3. the endgame search cache and the explicit rollout rule ----------------------------------
def tiny_set(rule, n=12, max_empty=6, seed=5) -> EndgameSet:
    """A hand-built EndgameSet: the same positions under both rules (the walk down is rule-free), solved
    under `rule`, so the two differ only in their labels — exactly the pair that must not be mixed."""
    rng = np.random.default_rng(seed)
    gs = [random_endgame(rng, max_empty, rule) for _ in range(n)]
    solved = [solve_children((g.cells, g.macro, g.next_board, g.player), rule) for g in gs]
    return EndgameSet(cells=np.stack([g.cells for g in gs]), macro=np.stack([g.macro for g in gs]),
                      next_board=np.array([g.next_board for g in gs], np.int8),
                      player=np.array([g.player for g in gs], np.int8),
                      exact=np.array([v for v, _ in solved], np.int8), child=np.stack([c for _, c in solved]),
                      empties=np.zeros(n, np.int64), game_id=np.arange(n), ply=np.zeros(n, np.int64),
                      meta={"name": f"tiny_{rule}", "rule": rule})


def test_evaluate_cache_is_keyed_by_rule():
    device = torch.device(DEV)
    torch.manual_seed(0)
    fe = FusedEvaluator(ResNet(NetConfig(blocks=1, filters=8)).to(device), device)
    es_c, es_d = tiny_set("count"), tiny_set("draw")
    assert not np.array_equal(es_c.exact, es_d.exact), "the two sets must disagree somewhere for this test to bite"
    cache: dict = {}
    kw = dict(sims=(4,), n_boot=10, symmetrise=False, graph=False, search_cache=cache)
    evaluate(fe, es_c, device, rule="count", **kw)
    assert list(cache) == [(4, "count")], list(cache)
    evaluate(fe, es_d, device, rule="draw", **kw)
    assert sorted(cache) == [(4, "count"), (4, "draw")], sorted(cache)
    assert cache[(4, "count")].rule == "count" and cache[(4, "draw")].rule == "draw"
    # keyed by sims alone, the count-rule search would have been handed the draw-rule set:
    poisoned = {(4, "draw"): cache[(4, "count")]}
    _expect(AssertionError, evaluate, fe, es_d, device, sims=(4,), n_boot=10, symmetrise=False, graph=False,
            search_cache=poisoned, rule="draw")
    # a cache keyed the old way -- by sims alone -- is REFUSED, not ignored: ignoring it reads as a miss, so
    # the wrong-rule searches stay in the caller's dict unexamined beside the new ones (M2 rebuttal (c))
    legacy = {4: cache[(4, "count")]}
    msg = _expect(ValueError, evaluate, fe, es_c, device, sims=(4,), n_boot=10, symmetrise=False, graph=False,
                  search_cache=legacy, rule="count")
    assert "(sims, rule)" in msg, msg
    assert list(legacy) == [4], "the refused cache was written to anyway"
    # and a set solved under another rule is refused outright, with or without a search
    msg = _expect(ValueError, evaluate, fe, es_c, device, sims=(), n_boot=10, symmetrise=False, rule="draw")
    assert "solved under rule" in msg, msg
    print("evaluate's cache is keyed by (sims, rule); a count search cannot grade a draw set, a cache keyed by "
          "sims alone is refused rather than silently ignored, and a set of the wrong rule is refused before "
          "any of it is read")


def test_evaluate_rollout_takes_its_rule_and_checks_it():
    es = tiny_set("count", n=8)
    row = evaluate_rollout(RolloutPlayer(200, rule="count").act, es, 10, rule="count")
    assert 0.0 <= row["optimal"] <= 1.0
    msg = _expect(ValueError, evaluate_rollout, RolloutPlayer(200, rule="draw").act, es, 10, rule="draw")
    assert "solved under rule" in msg, msg
    print("evaluate_rollout is given its rule and refuses a set of another one (it used to infer the set's)")


# ---- 4. relabel ---------------------------------------------------------------------------------------
def test_relabel():
    win = np.array([1, -1, 0, 1, -1], np.int8)
    reason = np.array([1, 2, 3, 2, 1], np.int8)  # line, count, draw, count, line
    w, r, n = relabel(win.copy(), reason.copy(), "count", "draw")
    assert n == 2
    assert w.tolist() == [1, 0, 0, 0, -1], w.tolist()
    assert r.tolist() == [1, 3, 3, 3, 1], r.tolist()
    assert w.dtype == win.dtype and r.dtype == reason.dtype
    for rule in ("count", "draw"):
        w2, r2, n2 = relabel(win, reason, rule, rule)
        assert n2 == 0 and w2 is win and r2 is reason
    msg = _expect(SystemExit, relabel, win, reason, "draw", "count")
    assert "replaying the saved moves" in msg and "not implemented" in msg, msg
    print("relabel: count -> draw turns exactly the count endings into draws; draw -> count is refused as needing a replay")


# ---- 5. what rule a corpus was generated under ---------------------------------------------------------
def _corpus(run, rule_tag=None, n=6, name="games_0000.npz"):
    os.makedirs(os.path.join(run, "games"), exist_ok=True)
    cols = dict(moves=np.zeros((n, 82), np.int8), winners=np.zeros(n, np.int8), reasons=np.full(n, 3, np.int8),
                lengths=np.full(n, 81, np.int64), root_values=np.zeros((n, 82), np.float32))
    if rule_tag is not None:
        cols["rule"] = np.array(rule_tag)
    np.savez_compressed(os.path.join(run, "games", name), **cols)


def test_corpus_rule_is_read_never_guessed():
    with tempfile.TemporaryDirectory() as tmp:
        # (a) no config.json, no tag: refused, and --corpus_rule is the way out
        run = os.path.join(tmp, "orphan")
        _corpus(run)
        assert games_rule(run) is None
        msg = _expect(SystemExit, corpus_rule, run)
        assert "--corpus_rule" in msg, msg
        assert corpus_rule(run, "draw") == "draw" and corpus_rule(run, "count") == "count"
        # (b) a pre-K1 config.json (no rule key) is a count corpus, and the override does not override it
        with open(os.path.join(run, "config.json"), "w") as f:
            json.dump({"run": run, "sims": 32}, f)
        assert corpus_rule(run) == "count" and corpus_rule(run, "draw") == "count"
        # (c) a tagged corpus identifies itself, config.json or not
        run2 = os.path.join(tmp, "tagged")
        _corpus(run2, "draw")
        assert games_rule(run2) == "draw" and corpus_rule(run2) == "draw"
        with open(os.path.join(run2, "config.json"), "w") as f:
            json.dump({"run": run2, "rule": "draw"}, f)
        assert corpus_rule(run2) == "draw"
        # (d) a tag that contradicts config.json is a corrupt run, not a preference
        with open(os.path.join(run2, "config.json"), "w") as f:
            json.dump({"run": run2, "rule": "count"}, f)
        msg = _expect(SystemExit, corpus_rule, run2)
        assert "game files are tagged" in msg, msg
    print("a corpus's rule comes from its game files' tag, else config.json (no key = count); an untagged "
          "orphan is refused unless --corpus_rule names it, and a tag contradicting config.json is a fault")


def test_a_directory_mixing_tagged_and_untagged_game_files_is_refused():
    """A tag vouches for its own file. Every run's files are all tagged (K1 on) or all untagged (pre-K1), so
    a directory holding both was assembled from two corpora; reading the tagged ones and ignoring the rest
    let one draw-tagged file speak for a directory of count games (M2 rebuttal (e))."""
    with tempfile.TemporaryDirectory() as tmp:
        run = os.path.join(tmp, "mixed")
        _corpus(run, "draw", name="games_0000.npz")
        _corpus(run, None, name="games_0001.npz")
        _corpus(run, None, name="games_0002.npz")
        msg = _expect(SystemExit, games_rule, run)
        assert "games_0001.npz" in msg and "games_0002.npz" in msg, msg
        assert "1 tagged 'draw'" in msg and "2 carrying no tag" in msg, msg
        _expect(SystemExit, corpus_rule, run)  # and the caller that asks for the corpus's rule sees it too
        _expect(SystemExit, corpus_rule, run, "draw")  # --corpus_rule cannot wave it through either
        # a config.json agreeing with the tag vouches for the untagged files; one that disagrees does not
        cfg_path = os.path.join(run, "config.json")
        with open(cfg_path, "w") as f:
            json.dump({"run": run, "rule": "draw"}, f)
        assert games_rule(run) == "draw" and corpus_rule(run) == "draw"
        with open(cfg_path, "w") as f:
            json.dump({"run": run, "rule": "count"}, f)
        msg = _expect(SystemExit, games_rule, run)
        assert "config.json records rule 'count'" in msg, msg
        with open(cfg_path, "w") as f:  # a pre-K1 config.json has no rule key, i.e. count: it vouches for count
            json.dump({"run": run, "sims": 32}, f)
        msg = _expect(SystemExit, games_rule, run)
        assert "config.json records rule 'count'" in msg, msg
        # and a uniformly tagged directory is untouched by any of this
        os.remove(os.path.join(run, "games", "games_0001.npz"))
        os.remove(os.path.join(run, "games", "games_0002.npz"))
        os.remove(cfg_path)
        assert games_rule(run) == "draw"
    print("a directory mixing tagged and untagged game files is refused by name unless a config.json agreeing "
          "with the tag vouches for the untagged ones; a uniformly tagged one still identifies itself")


# ---- 6. the two tool closures ---------------------------------------------------------------------------
def test_surrogate_is_refused_under_a_non_count_rule():
    device = torch.device("cpu")
    msg = _expect(ValueError, openings_player, "surrogate:/no/such/file.pt", 8, 2, device, rule="draw")
    assert "count-rule game" in msg, msg
    # under count the rule gate does not fire: the failure is the missing file, not the rule
    other = _expect(Exception, openings_player, "surrogate:/no/such/file.pt", 8, 2, device, rule="count")
    assert "count-rule game" not in other, other
    print("a surrogate player is refused under draw and only under draw (it is a learned model of the count game)")


def test_book_refuses_a_paired_file_of_another_rule():
    opening = {"moves": [40], "a_as_x": 1.0, "a_as_o": 0.0}
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "paired.json")
        for rule in ("count", "draw"):
            with open(p, "w") as f:
                json.dump({"rule": rule, "openings": [opening]}, f)
            assert paired_stats(p, rule)  # its own rule is fine
            other = "draw" if rule == "count" else "count"
            msg = _expect(SystemExit, paired_stats, p, other)
            assert "played under rule" in msg, msg
        with open(p, "w") as f:  # a pre-K1 paired file carries no rule: it is count
            json.dump({"openings": [opening]}, f)
        assert paired_stats(p, "count")
        _expect(SystemExit, paired_stats, p, "draw")
    print("book.py checks a paired match file's rule against its own (a file with no rule key is count)")


# ---- 7. the uniform draw sample ---------------------------------------------------------------------------
def test_draw_sample_is_uniform_seeded_and_a_no_op_under_the_cap():
    winners = np.ones(1000, np.int8)
    winners[400:] = 0  # 600 draws, all in the tail of the window
    idx = np.flatnonzero(winners == 0)
    assert np.array_equal(sample_draws(winners, 600), idx), "a window at the cap must be read whole, in order"
    assert np.array_equal(sample_draws(winners, 10_000), idx)
    s0 = sample_draws(winners, 200, seed=0)
    assert len(s0) == 200 and np.array_equal(s0, np.sort(s0)) and len(set(s0.tolist())) == 200
    assert np.array_equal(s0, sample_draws(winners, 200, seed=0)), "the sample must be reproducible"
    assert not np.array_equal(s0, sample_draws(winners, 200, seed=1)), "the seed must move the sample"
    assert not np.array_equal(s0, idx[:200]), "the sample must not be the earliest 200 draws"
    assert s0.max() > idx[-50], "a uniform sample of the window must reach its end"
    print("principles.py samples the draws uniformly over the window, seeded and reproducible, and takes all "
          "of them unchanged when the window fits the cap")


# ---- 8. terminal-value backup in both searches --------------------------------------------------------------
def count_decided_in_one_move():
    """X to move, sent to board 8, whose only empty cell fills it without a local winner. Closing it ends the
    game with X on 5 boards and O on 3 and no macro line: an X win under `count`, a draw under `draw`."""
    macro = np.array([-1, 1, 1, 1, -1, 1, 1, -1, 0], np.int8)
    cells = np.ones(81, np.int8)  # the eight closed boards' contents can no longer matter
    cells[72:81] = np.array(NO_LINE_FILL, np.int8)
    return cells, macro, 8, 1


def test_terminal_backup_in_both_searches():
    cells, macro, nb, player = count_decided_in_one_move()
    # the position is what it claims to be, on the reference engine
    for rule, want in (("count", (1, "count")), ("draw", (0, "draw"))):
        g = UTTT(rule)
        g.cells[:], g.macro[:] = cells, macro
        g.next_board, g.player = nb, player
        g.move_count = int((g.cells != 0).sum())
        assert g.legal_moves() == [80], g.legal_moves()
        g.play(80)
        assert (g.winner, g.end_reason) == want, (rule, g.winner, g.end_reason)
        assert int((g.macro == 1).sum()) == 5 and int((g.macro == -1).sum()) == 3 and g.macro[8] == FULL
    device = torch.device(DEV)
    t = lambda a, dt: torch.tensor(np.asarray(a)[None], dtype=dt, device=device)  # noqa: E731
    args = (t(cells, torch.int8), t(macro, torch.int8), t(nb, torch.int8), t(player, torch.int8),
            torch.zeros(1, dtype=torch.bool, device=device), torch.zeros(1, dtype=torch.int8, device=device))
    ev = UniformEvaluator(device)
    for rule, want in (("count", 1.0), ("draw", 0.0)):
        v2 = BatchedSearch(ev, 1, SearchConfig(n_sims=16, mode="gumbel", gumbel_scale=0.0, cuda_graph=False, depth_cap=8),
                           device, rule=rule).search(*args, selfplay=False)
        v1 = BatchedMCTS(ev, 1, MCTSConfig(n_sims=16, mode="gumbel", gumbel_scale=0.0), device,
                         rule=rule).search(*args, selfplay=False)
        for name, r in (("uttt.search", v2), ("uttt.mcts", v1)):
            assert int(r.action[0]) == 80, (name, rule, int(r.action[0]))
            got = float(r.root_value[0])
            assert abs(got - want) < 0.07, f"{name} under {rule}: root value {got:+.3f}, expected {want:+.1f}"
            print(f"  {name:11s} {rule:5s}: root value {got:+.3f} after 16 simulations (want {want:+.1f})")
    print("both searches back the terminal value up under the rule they were given: a count win for the mover, "
          "a draw under `draw`, from the same position")


if __name__ == "__main__":
    test_relabel()
    test_draw_sample_is_uniform_seeded_and_a_no_op_under_the_cap()
    test_corpus_rule_is_read_never_guessed()
    test_a_directory_mixing_tagged_and_untagged_game_files_is_refused()
    test_book_refuses_a_paired_file_of_another_rule()
    test_surrogate_is_refused_under_a_non_count_rule()
    test_cross_rule_resume_is_refused_before_anything_is_written()
    test_a_checkpoint_is_gated_even_when_config_json_cannot_speak()
    test_evaluate_cache_is_keyed_by_rule()
    test_evaluate_rollout_takes_its_rule_and_checks_it()
    test_terminal_backup_in_both_searches()
    test_a_config_without_a_rule_key_is_a_count_run()
    print("ok")
