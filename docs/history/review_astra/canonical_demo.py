"""Experimental exact-D4 evaluator: one NN call, including stabilizer handling.

This is a review experiment, NOT a proposed drop-in production change. It
chooses one orientation's predictions rather than ensembling all orientations.
Run: .venv/Scripts/python.exe -B docs/history/review_astra/canonical_demo.py
"""
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[3]  # moved to docs/history/review_astra by PLAN6
sys.path.insert(0, str(ROOT))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import numpy as np
import torch

from uttt.batch import SYM_CELL, SYM_CELL_INV, SYM_BOARD, SYM_BOARD_INV, apply_symmetry
from uttt.infer import FusedEvaluator
from uttt.model import load_checkpoint
from uttt.symmetry import SymmetryAveragedEvaluator
from bench import timed


class D4CanonicalEvaluator:
    def __init__(self, base):
        self.base, self.device = base, base.device
        self.cp = SYM_CELL.to(self.device)
        self.ci = SYM_CELL_INV.to(self.device)
        self.bp = SYM_BOARD.to(self.device)
        self.bi = SYM_BOARD_INV.to(self.device)

    @torch.no_grad()
    def __call__(self, cells, macro, next_board, player, done):
        n = cells.shape[0]
        idx = torch.arange(n, device=self.device)
        c8, m8 = cells[:, self.ci], macro[:, self.bi]
        nb = next_board.long()
        nb8 = torch.where(nb[:, None] >= 0, self.bp[:, nb.clamp_min(0)].T, nb[:, None]).to(next_board.dtype)
        # Exact lexicographic comparison, not a collision-prone hash. Side,
        # done and terminal value are unchanged by every spatial transform.
        keys = torch.cat([c8, m8, nb8[:, :, None]], dim=2)
        best, pick = keys[:, 0], torch.zeros(n, dtype=torch.long, device=self.device)
        for j in range(1, 8):
            candidate = keys[:, j]
            first_difference = (candidate != best).to(torch.int32).argmax(1)
            less = candidate[idx, first_difference] < best[idx, first_difference]
            best = torch.where(less[:, None], candidate, best)
            pick = torch.where(less, j, pick)
        prob, value = self.base(c8[idx, pick], m8[idx, pick], nb8[idx, pick], player, done)
        # All maps taking this state to the canonical state form a stabilizer
        # coset. Average their output transports, WITHOUT another NN call.
        same_canonical = (keys == best[:, None]).all(2).float()
        back = prob[:, self.cp]
        prob = (back * same_canonical[:, :, None]).sum(1) / same_canonical.sum(1, keepdim=True)
        return prob, value


@torch.no_grad()
def main():
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = True
    device = torch.device("cuda:1")
    torch.cuda.set_device(device)
    fe = FusedEvaluator(load_checkpoint(str(ROOT / "runs/deep10_c1_300/net_0300.pt"), device), device)
    canonical = D4CanonicalEvaluator(fe)
    averaged = SymmetryAveragedEvaluator(fe)
    with np.load(ROOT / "suites/endgame_v1.npz") as z:
        print("endgame keys", z.files, flush=True)
        c = torch.from_numpy(z["cells"].copy()).to(device)
        m = torch.from_numpy(z["macro"].copy()).to(device)
        nb = torch.from_numpy(z["next_board"].copy()).to(device)
        p = torch.from_numpy(z["player"].copy()).to(device)
        exact = torch.from_numpy(z["exact"].copy()).to(device)
        child = torch.from_numpy(z["child"].copy()).to(device)
    done = torch.zeros(c.shape[0], dtype=torch.bool, device=device)
    args = c, m, nb, p, done
    # Compare equal batch shapes, so cuDNN selects the same fp16 algorithm.
    pc, vc = canonical(*(x[:256] for x in args))
    worst_p = worst_v = 0.0
    for s in range(8):
        cs, ms, ns = apply_symmetry(s, c[:256], m[:256], nb[:256])
        ps, vs = canonical(cs, ms, ns, p[:256], done[:256])
        worst_p = max(worst_p, float((ps[:, SYM_CELL[s].to(device)] - pc[:256]).abs().max()))
        worst_v = max(worst_v, float((vs - vc[:256]).abs().max()))
    print("equivariance errors", worst_p, worst_v, flush=True)
    assert worst_p < 1e-4 and worst_v < 1e-4
    # Stabilizer case: after [40], policy must be constant on the four corners
    # and on the four edges of board 4. No legal deterministic action is fixed.
    from uttt.batch import BatchUTTT
    g = BatchUTTT(1, device)
    g.step(torch.tensor([40], device=device))
    pp, vv = canonical(g.cells, g.macro, g.next_board, g.player, g.done)
    corners, edges = pp[0, [36,38,42,44]], pp[0, [37,39,41,43]]
    assert float(corners.max()-corners.min()) < 1e-6 and float(edges.max()-edges.min()) < 1e-6
    result = {"equivariance_max_policy_error": worst_p, "equivariance_max_value_error": worst_v,
              "after40_corners": corners.tolist(), "after40_edges": edges.tolist(), "raw_endgame_v1": {}, "timings": {}}
    idx = torch.arange(c.shape[0], device=device)
    for name, ev in (("plain", fe), ("canonical", canonical), ("eight_way", averaged)):
        prob, value = ev(*args)
        move = prob.argmax(1)
        reg = exact.float()-child[idx, move].float()
        result["raw_endgame_v1"][name] = {"optimal": (reg == 0).float().mean().item(),
                                         "regret": reg.mean().item(),
                                         "scalar_mae": (exact-value).abs().mean().item()}
        small = tuple(x[:256] for x in args)
        s = torch.cuda.Stream(device=device)
        s.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(s):
            for _ in range(3):
                ev(*small)
        torch.cuda.current_stream().wait_stream(s)
        graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(graph, stream=s):
            output = ev(*small)
        result["timings"][name] = timed(graph.replay, device, repeats=5, groups=3)
        del graph, output
    (Path(__file__).resolve().parent / "canonical_demo.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
