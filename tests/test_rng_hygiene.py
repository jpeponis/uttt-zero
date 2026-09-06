"""RNG hygiene (PLAN6 E4): an evaluation inserted between two training iterations must not change what the trainer
draws next — the replay sample, the augmentation symmetries, the self-play noise and sampled moves.

What this establishes is *observational neutrality*: with self-play, replay and augmentation on their own generators,
and a deterministic search drawing nothing, evaluation cadence cannot perturb training. It does NOT make training
trajectories reproducible: the pipeline is not bitwise deterministic (cudnn.benchmark, fp16 autocast), and a
4096-game self-play loop amplifies a last-bit difference within one iteration — two runs with the same seed have
been observed to differ in their self-play from iteration 1 (PLAN6 §1 item 13). "Same seed" means the same start.

Run: .venv/Scripts/python.exe tests/test_rng_hygiene.py   (UTTT_DEV selects the device)"""
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import NetConfig, ResNet, load_checkpoint  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.selfplay_cont import ContinuousSelfPlay, GPUReplayBuffer  # noqa: E402
from uttt.train2 import make_generators, symmetrise  # noqa: E402

DEV = torch.device(os.environ.get("UTTT_DEV", "cuda:0" if torch.cuda.is_available() else "cpu"))
ANCHOR = "runs/dev1/net_0200.pt"


def rng_snapshot():
    s = [torch.get_rng_state()]
    if DEV.type == "cuda":
        s.append(torch.cuda.get_rng_state(DEV))
    return s


def same_rng(a, b) -> bool:
    return all(torch.equal(x, y) for x, y in zip(a, b))


def evaluation(n=64, legacy_draw=False):
    """What an in-run evaluation does: load an anchor from disk, build a fresh evaluator, run deterministic searches.
    legacy_draw emulates the pre-E4 search, which drew Gumbel noise from the global RNG and multiplied it by zero."""
    if os.path.exists(ANCHOR):
        anchor = load_checkpoint(ANCHOR, DEV)
    else:
        with torch.random.fork_rng(devices=[]):
            anchor = ResNet(NetConfig()).to(DEV)
    ev = FusedEvaluator(anchor, DEV)
    s = BatchedSearch(ev, n, SearchConfig(n_sims=8, mode="gumbel", gumbel_scale=0.0), DEV)
    g = BatchUTTT(n, DEV)
    for _ in range(12):
        if legacy_draw:
            torch.rand(n, 81, device=DEV)
        g.step(s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False).action)


def training_draws(dedicated: bool, evaluate: bool, legacy_draw: bool = False, n=64):
    """One self-play burst, an optional evaluation, then the next draws of every training stream."""
    torch.manual_seed(0)
    gens = make_generators(0, DEV) if dedicated else {"selfplay": None, "buffer": None, "aug": None}
    fe = FusedEvaluator(ResNet(NetConfig(blocks=1, filters=16)).to(DEV), DEV)
    sp = ContinuousSelfPlay(fe, n, SearchConfig(n_sims=8, mode="gumbel", sample_moves=6), DEV, generator=gens["selfplay"])
    buf = GPUReplayBuffer(50_000, DEV, generator=gens["buffer"])
    pos, _, _ = sp.run(40)
    buf.add(pos)
    buf.update_weights()
    if evaluate:
        evaluation(n, legacy_draw)
    b = next(buf.sample_batches(256, 2))
    idx = buf.last_sample.clone()
    sym = symmetrise(b, DEV, gens["aug"])[0].clone()
    res = sp.search.search(sp.g.cells, sp.g.macro, sp.g.next_board, sp.g.player, sp.g.done, sp.g.winner, selfplay=True, ply=sp.len)
    return idx, sym, res.action.clone(), res.policy.clone()


def test_deterministic_search_draws_nothing(n=128):
    ev = FusedEvaluator(ResNet(NetConfig(blocks=1, filters=16)).to(DEV), DEV)
    g = BatchUTTT(n, DEV)
    for mode in ("gumbel", "puct"):
        s = BatchedSearch(ev, n, SearchConfig(n_sims=8, mode=mode, gumbel_scale=0.0), DEV)
        before = rng_snapshot()
        s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
        assert same_rng(before, rng_snapshot()), mode
    before = rng_snapshot()
    if os.path.exists(ANCHOR):
        load_checkpoint(ANCHOR, DEV)
    assert same_rng(before, rng_snapshot())
    print("deterministic search and checkpoint loading leave the global RNG untouched")


def test_generator_isolation():
    ref = training_draws(dedicated=True, evaluate=False)
    for legacy in (False, True):
        got = training_draws(dedicated=True, evaluate=True, legacy_draw=legacy)
        for name, a, b in zip(("replay indices", "symmetries", "self-play actions", "self-play policy"), ref, got):
            assert torch.equal(a, b), (name, legacy)
    print("with dedicated generators an evaluation (even one that draws from the global RNG) changes no training draw")
    # teeth: the same evaluation with the pre-E4 draw, on the global generator, DOES change the next replay sample
    ref = training_draws(dedicated=False, evaluate=False)
    got = training_draws(dedicated=False, evaluate=True, legacy_draw=True)
    assert not torch.equal(ref[0], got[0])
    # and after E4 the global-generator path is neutral too, because nothing in an evaluation draws any more
    got = training_draws(dedicated=False, evaluate=True, legacy_draw=False)
    assert all(torch.equal(a, b) for a, b in zip(ref, got))
    print("without them the legacy idle draw would have moved the replay sample; the E4 evaluation path draws nothing")


def test_generator_state_round_trip():
    gens = make_generators(3, DEV)
    states = {k: g.get_state() for k, g in gens.items()}
    a = [torch.rand(4, device=DEV, generator=g) for g in gens.values()]
    for k, g in gens.items():
        g.set_state(states[k])
    b = [torch.rand(4, device=DEV, generator=g) for g in gens.values()]
    assert all(torch.equal(x, y) for x, y in zip(a, b))
    print("generator states round-trip through get_state/set_state (what the checkpoints carry, E5)")


if __name__ == "__main__":
    test_deterministic_search_draws_nothing()
    test_generator_isolation()
    test_generator_state_round_trip()
    print("ok")
