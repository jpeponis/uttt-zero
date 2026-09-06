"""Symmetry, made checkable (PLAN6 E6; REVIEW-astra §5.5). The D4 group acts on the 9×9 grid — the same rotation or
reflection on the board index and the cell index at once — and everything the pipeline computes must commute with it:

  1. the engine: T(g s, g a) = g T(s, a), through free moves, board closures and count endings;
  2. the encoder: encode(g s) is the grid transform of encode(s); and relabelling X <-> O together with the side to move
     leaves the seven planes unchanged;
  3. the heads of the two exactly equivariant evaluators (8-way average, one-call canonical): the value is invariant,
     the policy transforms with the board, and at positions with a non-trivial stabiliser (the empty board, [40]) the
     policy is constant on orbits — compared as orbit masses, never as argmaxes (§3.3: no equivariant deterministic
     move exists there);
  4. the same after fusion, fp16 and CUDA-graph capture, at one fixed batch shape (CUDA only);
  5. a deterministic search on top of an exact evaluator commutes with the group as a distribution over moves.

Run: .venv/Scripts/python.exe tests/test_symmetry.py   (UTTT_DEV selects the device; the fp16/graph part needs CUDA)"""
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import FULL, INV_PERM, PERM, SYM_BOARD, SYM_CELL, BatchUTTT, apply_symmetry, encode, step_state  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import Evaluator, NetConfig, ResNet  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.symmetry import CanonicalEvaluator, SymmetryAveragedEvaluator  # noqa: E402

DEV = torch.device(os.environ.get("UTTT_DEV", "cuda:0" if torch.cuda.is_available() else "cpu"))


def random_games(n, plies, seed=0):
    torch.manual_seed(seed)
    g = BatchUTTT(n, DEV)
    for _ in range(plies):
        g.step(torch.multinomial(g.legal_mask().float() + 1e-9, 1).squeeze(1))
    return g


def transported(policy, s):
    """policy in the frame of g s, brought back to the frame of s: back[m] = policy[SYM_CELL[s][m]]."""
    return policy[:, SYM_CELL[s].to(policy.device)]


# ---- 1. the engine commutes with D4 -------------------------------------------------------------
def test_engine_commutation(n=512, plies=70):
    torch.manual_seed(1)
    g = BatchUTTT(n, DEV)
    seen = {"free": 0, "closed": 0, "count_end": 0, "line_end": 0}
    for _ in range(plies):
        legal = g.legal_mask()
        a = torch.multinomial(legal.float() + 1e-9, 1).squeeze(1)
        seen["free"] += int(((g.next_board < 0) & ~g.done).sum())
        out = step_state(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, a)
        for s in range(8):
            c, m, nb = apply_symmetry(s, g.cells, g.macro, g.next_board)
            ga = SYM_CELL[s].to(DEV)[a]
            out_s = step_state(c, m, nb, g.player, g.done, g.winner, ga)
            c2, m2, nb2 = apply_symmetry(s, out[0], out[1], out[2])
            assert torch.equal(out_s[0], c2) and torch.equal(out_s[1], m2) and torch.equal(out_s[2], nb2), s
            for k in (3, 4, 5, 6):  # player, done, winner, reason: invariant
                assert torch.equal(out_s[k], out[k]), (s, k)
        g.step(a)
        seen["closed"] += int((g.macro != 0).sum())
        seen["count_end"] += int((g.end_reason == 2).sum() + (g.end_reason == 3).sum())
        seen["line_end"] += int((g.end_reason == 1).sum())
    assert all(v > 0 for v in seen.values()), seen  # the play-outs exercised every rule
    print(f"engine commutes with D4 over {plies} random plies of {n} games (free moves, closures, line and count endings seen)")


# ---- 2. the encoder --------------------------------------------------------------------------------
def test_encoder(n=512):
    g = random_games(n, 58, seed=2)  # random play fills its first unwon boards only after ~50 plies
    obs = encode(g.cells, g.macro, g.next_board, g.player, g.done).view(n, -1, 81)
    grid_map = INV_PERM[SYM_CELL[:, PERM]]  # (8, 81): grid position g -> grid position of the image of its cell
    for s in range(8):
        c, m, nb = apply_symmetry(s, g.cells, g.macro, g.next_board)
        obs_s = encode(c, m, nb, g.player, g.done).view(n, -1, 81)
        assert torch.equal(obs_s[:, :, grid_map[s].to(DEV)], obs), s
    # X <-> O relabelling, side to move included: the relative encoding cannot tell
    flipped = encode(-g.cells, torch.where(g.macro.abs() == 1, -g.macro, g.macro), g.next_board, -g.player, g.done)
    assert torch.equal(flipped.view(n, -1, 81), obs)
    assert int((g.macro == FULL).sum()) > 0  # full boards were present, so the FULL plane was exercised
    print("encoder is D4-equivariant and colour-relabelling invariant")


# ---- 3. the exact evaluators' heads ----------------------------------------------------------------
def orbit_masses(p, position: str):
    """Total policy mass on each orbit of the position's legal moves (empty board: 15 first-move orbits; after [40]: edges, corners)."""
    if position == "empty":
        orbits = {}
        for m in range(81):
            orbits.setdefault(int(SYM_CELL[:, m].min()), []).append(m)
    else:
        orbits = {"edges": [37, 39, 41, 43], "corners": [36, 38, 42, 44]}
    return {k: p[:, v] for k, v in orbits.items()}


def check_heads(ev, name, tol=1e-4, n=256):
    g = random_games(n, 18, seed=3)
    p0, v0 = ev(g.cells, g.macro, g.next_board, g.player, g.done)
    for s in range(8):
        c, m, nb = apply_symmetry(s, g.cells, g.macro, g.next_board)
        ps, vs = ev(c, m, nb, g.player, g.done)
        assert float((transported(ps, s) - p0).abs().max()) < tol, (name, s)
        assert float((vs - v0).abs().max()) < tol, (name, s)
    # stabiliser positions: the policy must be constant on every orbit of legal moves
    empty = BatchUTTT(n, DEV)
    after40 = BatchUTTT(n, DEV)
    after40.step(torch.full((n,), 40, device=DEV))
    for pos, name_pos in ((empty, "empty"), (after40, "after40")):
        p, _ = ev(pos.cells, pos.macro, pos.next_board, pos.player, pos.done)
        for k, block in orbit_masses(p, name_pos).items():
            assert float((block.max(1).values - block.min(1).values).max()) < tol, (name, name_pos, k)
    print(f"{name}: value invariant, policy equivariant, constant on orbits at the empty board and after [40]")


def test_exact_evaluators():
    torch.manual_seed(4)
    base = Evaluator(ResNet(NetConfig(blocks=2, filters=32)).to(DEV), DEV, amp=False)
    check_heads(SymmetryAveragedEvaluator(base), "8-way average")
    check_heads(CanonicalEvaluator(base), "one-call canonical")
    p_base, _ = base(*random_games(64, 18, seed=3).state_tuple())
    # the plain net is NOT equivariant (so the checks above have teeth)
    g = random_games(64, 18, seed=3)
    c, m, nb = apply_symmetry(1, g.cells, g.macro, g.next_board)
    p1, _ = base(c, m, nb, g.player, g.done)
    assert float((transported(p1, 1) - p_base).abs().max()) > 1e-3
    print("the plain net is not equivariant; the wrappers are")


# ---- 4. after fusion, fp16 and graph capture (fixed batch shape) -----------------------------------
def test_fused_fp16_graph(n=256):
    if DEV.type != "cuda":
        print("fused/fp16/graph check skipped (no CUDA)")
        return
    torch.manual_seed(5)
    net = ResNet(NetConfig(blocks=2, filters=32)).to(DEV)
    fe = FusedEvaluator(net, DEV)  # BN folded, fp16, channels_last
    canon = CanonicalEvaluator(fe)
    g = random_games(n, 18, seed=6)
    static = [t.clone() for t in g.state_tuple()]
    stream = torch.cuda.Stream(device=DEV)
    stream.wait_stream(torch.cuda.current_stream(DEV))
    with torch.cuda.stream(stream):
        for _ in range(3):
            canon(*static)
    torch.cuda.current_stream(DEV).wait_stream(stream)
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph):
        out_p, out_v = canon(*static)
    ref_p, ref_v = None, None
    for s in range(8):
        c, m, nb = apply_symmetry(s, g.cells, g.macro, g.next_board)
        for dst, src in zip(static, (c, m, nb, g.player, g.done)):
            dst.copy_(src)
        graph.replay()
        p, v = transported(out_p.clone(), s), out_v.clone()
        if ref_p is None:
            ref_p, ref_v = p, v
        else:  # one canonical state per input, whatever its orientation: identical fp16 arithmetic, identical answer
            assert torch.equal(p, ref_p) and torch.equal(v, ref_v), s
    print("canonical evaluator on the fused fp16 net under CUDA-graph replay: bitwise identical across the 8 orientations")


# ---- 5. search on an exact evaluator commutes with the group (as a distribution) --------------------
def test_search_commutes(n=128, sims=24):
    torch.manual_seed(7)
    base = Evaluator(ResNet(NetConfig(blocks=2, filters=32)).to(DEV), DEV, amp=False)
    ev = SymmetryAveragedEvaluator(base)
    g = random_games(n, 14, seed=8)
    cfg = SearchConfig(n_sims=sims, mode="gumbel", gumbel_scale=0.0)  # deterministic: the (zero) noise is trivially transported
    s0 = BatchedSearch(ev, n, cfg, DEV)
    r0 = s0.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
    agree, total = 0, 0
    for s in range(1, 8):
        c, m, nb = apply_symmetry(s, g.cells, g.macro, g.next_board)
        rs = BatchedSearch(ev, n, cfg, DEV).search(c, m, nb, g.player, g.done, g.winner, selfplay=False)
        pol = transported(rs.policy, s)
        assert float((rs.root_value - r0.root_value).abs().max()) < 1e-3, s
        close = (pol - r0.policy).abs().max(1).values < 1e-3
        agree += int(close.sum())
        total += n
    # ties broken by index can differ between frames (REVIEW-astra §3.3); they are rare on random positions
    assert agree / total > 0.97, agree / total
    print(f"deterministic search on the exact evaluator: transported policies agree on {100 * agree / total:.1f} % of positions, root values everywhere")


if __name__ == "__main__":
    test_engine_commutation()
    test_encoder()
    test_exact_evaluators()
    test_fused_fp16_graph()
    test_search_commutes()
    print("ok")
