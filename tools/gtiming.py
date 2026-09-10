"""Inference cost of every G arm (PLAN6 §4 metrics), measured in isolation: the numbers tools/gstudy.py records while
the E7 worker shares the card are contaminated. Run when both cards are idle.

    .venv/Scripts/python.exe tools/gtiming.py --device cuda:0 --out runs/plan6/G_timing_3090.json
    .venv/Scripts/python.exe tools/gtiming.py --device cuda:1 --out runs/plan6/G_timing_3060.json
    .venv/Scripts/python.exe tools/gtiming.py --device cuda:1 --arms resnet8,gcnn8x46 --out runs/plan6/G_timing_3060_gcnn8x46.json  # one arm and its reference

Per arm: graph-replayed fused-evaluator time per call at batch 4096 and batch 1 (ms), parameters, and the parameter
count of the exported plain net. Random weights: cost does not depend on them.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from gstudy import ARMS, inference_ms  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import build_net  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--arms", default="", help="comma-separated subset of ARMS (default: all, in ARMS order)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    device = torch.device(a.device)
    torch.backends.cudnn.benchmark = True
    rows = []
    print(f"{torch.cuda.get_device_name(device)}: fused fp16 evaluator, CUDA-graph replay, median of {a.repeats} x 20 calls")
    want = [x for x in a.arms.split(",") if x] or list(ARMS)
    for name in want:
        make = ARMS[name]
        torch.manual_seed(0)
        net = build_net(make()).to(device).eval()
        fe = FusedEvaluator(net, device)
        ms4096 = sorted(inference_ms(fe, device, 4096) for _ in range(a.repeats))[a.repeats // 2]
        ms1 = sorted(inference_ms(fe, device, 1) for _ in range(a.repeats))[a.repeats // 2]
        rows.append({"arm": name, "params": sum(p.numel() for p in net.parameters() if p.requires_grad),
                     "params_exported": sum(p.numel() for p in fe.net.parameters()), "ms_batch4096": ms4096, "ms_batch1": ms1})
        print(f"  {name:14s} params {rows[-1]['params']:9d} (exported {rows[-1]['params_exported']:9d})  {ms4096:7.2f} ms @4096  {ms1:6.3f} ms @1")
        del net, fe
        torch.cuda.empty_cache()
    if a.out:
        with open(a.out, "w") as f:
            json.dump({"device": torch.cuda.get_device_name(device), "rows": rows}, f, indent=1)
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
