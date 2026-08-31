"""Exact-label pipeline: labels agree with the solver and reach the right buffer rows; weights and checkpoints carry them."""
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.exact import ExactLabeler, empties_in_open_boards_t  # noqa: E402
from uttt.model import UniformEvaluator  # noqa: E402
from uttt.search import SearchConfig  # noqa: E402
from uttt.selfplay_cont import ContinuousSelfPlay, GPUReplayBuffer  # noqa: E402
from uttt.solver import empties_in_open_boards, solve  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def main(n=256, steps=120, max_empty=10, per_iter=300):
    torch.manual_seed(0)
    sp = ContinuousSelfPlay(UniformEvaluator(DEV), n, SearchConfig(n_sims=8, mode="gumbel", sample_moves=6), DEV)
    pos, games, stats = sp.run(steps)
    P = int(pos["cells"].shape[0])
    e = empties_in_open_boards_t(pos["cells"], pos["macro"]).cpu().numpy()
    e_ref = np.array([empties_in_open_boards(pos["cells"][i].cpu().numpy(), pos["macro"][i].cpu().numpy()) for i in range(0, P, 97)])
    assert np.array_equal(e[::97], e_ref)

    buf = GPUReplayBuffer(50_000, DEV)
    buf.add(pos)
    assert buf.last_slots is not None and buf.last_slots.numel() == P
    lab = ExactLabeler(processes=4, max_empty=max_empty, per_iter=per_iter, chunk=16, seed=0)
    t = time.perf_counter()
    k = lab.submit(pos, buf.last_slots)
    assert 0 < k <= per_iter, k
    slots, vals, pols = lab.collect()
    dt = time.perf_counter() - t
    lab.close()
    assert len(vals) == k == slots.numel()
    # every label matches the solver on the position stored in that buffer row
    for j in range(0, k, max(1, k // 25)):
        s = int(slots[j])
        c, m = buf.buf["cells"][s].cpu().numpy(), buf.buf["macro"][s].cpu().numpy()
        nb, p = int(buf.buf["next_board"][s]), int(buf.buf["player"][s])
        assert empties_in_open_boards(c, m) <= max_empty
        assert int(vals[j]) == solve(c, m, nb, p)[0]
        assert abs(float(pols[j].astype(np.float32).sum()) - 1) < 1e-2
    z_before = buf.buf["value"][slots.to(DEV)].clone()
    buf.apply_exact(slots, vals, pols)
    assert torch.equal(buf.buf["value"][slots.to(DEV)].cpu(), torch.from_numpy(vals))
    assert int(buf.buf["exact"][: buf.size].sum()) == k
    changed = float((z_before.cpu() != torch.from_numpy(vals)).float().mean())
    st = buf.update_weights(0.5, exact_weight=3.0)
    assert abs(st["exact_frac"] - k / P) < 1e-3
    w_exact = buf.weights[slots.to(DEV)]
    w_other = buf.weights[: buf.size][buf.buf["exact"][: buf.size] == 0]
    assert float(w_exact.min()) >= 3.0 * float(w_other.min()) - 1e-6  # exact rows carry the multiplier (dedup counts differ)
    b = buf.sample(64)
    assert "exact" in b
    sd = buf.state_dict()
    buf2 = GPUReplayBuffer(50_000, DEV)
    buf2.load_state_dict(sd)
    assert torch.equal(buf2.buf["exact"][: buf2.size], buf.buf["exact"][: buf.size])
    print(f"{k} of {P} positions labelled in {dt:.1f}s ({k / dt:.0f}/s with 4 workers); exact value differs from z in "
          f"{100 * changed:.1f}% of them; exact W/D/L {[(vals == v).mean().round(3) for v in (1, 0, -1)]}")
    print("ok")


if __name__ == "__main__":
    main()
