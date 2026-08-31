"""Stochastic weight averaging over the last checkpoints of a run (PLAN2 §2g: consecutive checkpoints differ
by up to 4 points; averaging is the cheap fix).

    .venv/Scripts/python.exe tools/swa.py runs/v2b --ckpts 0130,0140,0150 --out runs/v2b/net_swa.pt

Parameters and BatchNorm buffers are averaged uniformly; BatchNorm running statistics are then recomputed
with a forward pass over positions from the run's replay buffer (latest.pt), which matters after averaging.
"""
from __future__ import annotations

import argparse
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import encode  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402


@torch.no_grad()
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--ckpts", default="0130,0140,0150")
    ap.add_argument("--out", default="")
    ap.add_argument("--bn_positions", type=int, default=65536)
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    device = torch.device(a.device)
    paths = [os.path.join(a.run, f"net_{c}.pt") for c in a.ckpts.split(",")]
    nets = [load_checkpoint(p, device) for p in paths]
    avg = nets[-1]
    sd = avg.state_dict()
    for k in sd:
        if sd[k].dtype.is_floating_point:
            sd[k] = torch.stack([n.state_dict()[k].float() for n in nets]).mean(0).to(sd[k].dtype)
    avg.load_state_dict(sd)
    # recompute BatchNorm statistics on real positions
    ck = torch.load(os.path.join(a.run, "latest.pt"), map_location="cpu", weights_only=False)
    if "buffer" in ck:
        b = ck["buffer"]["buf"]
        n = min(a.bn_positions, b["cells"].shape[0])
        idx = torch.randperm(b["cells"].shape[0])[:n]
        for m in avg.modules():
            if isinstance(m, torch.nn.BatchNorm2d):
                m.reset_running_stats()
                m.momentum = None  # cumulative average
        avg.train()
        for i in range(0, n, 4096):
            sl = idx[i : i + 4096]
            obs = encode(b["cells"][sl].to(device), b["macro"][sl].to(device), b["next_board"][sl].to(device), b["player"][sl].to(device),
                         extra=avg.cfg.extra_planes)
            avg(obs)
        avg.eval()
        print(f"averaged {len(paths)} checkpoints; BN statistics recomputed on {n} buffer positions")
    else:
        print(f"averaged {len(paths)} checkpoints; no buffer in latest.pt, BN statistics averaged")
    cfg = torch.load(paths[-1], map_location="cpu", weights_only=False).get("cfg", {})
    out = a.out or os.path.join(a.run, "net_swa.pt")
    torch.save({"net": avg.state_dict(), "cfg": cfg, "swa_of": paths}, out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
