"""Short, in-memory GPU microbenchmarks; never starts a training run or saves weights.

Run AFTER checks.py, to avoid timing another workload on the 3060.
"""
from __future__ import annotations

import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]  # moved to docs/history/review_astra by PLAN6
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import numpy as np
import torch
import torch.nn.functional as F

from uttt.batch import BatchUTTT
from uttt.infer import FusedEvaluator
from uttt.model import load_checkpoint


def timed(fn, device, repeats=12, groups=5):
    for _ in range(3):
        fn()
    torch.cuda.synchronize(device)
    wall, gpu = [], []
    for _ in range(groups):
        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        begin = time.perf_counter()
        start.record()
        for _ in range(repeats):
            fn()
        end.record()
        end.synchronize()
        wall.append((time.perf_counter()-begin)*1000/repeats)
        gpu.append(start.elapsed_time(end)/repeats)
    return {"wall_ms_median": float(np.median(wall)), "wall_ms_min": min(wall),
            "wall_ms_max": max(wall), "gpu_ms_median": float(np.median(gpu))}


def record(rows, **row):
    rows.append(row)
    print(json.dumps(row), flush=True)


def inference(device, rows):
    torch.cuda.set_device(device)
    net = load_checkpoint(str(ROOT / "runs/deep10_c1_300/net_0300.pt"), device)
    fe = FusedEvaluator(net, device)
    for n in (1, 64, 256, 1024, 4096):
        g = BatchUTTT(n, device)
        args = (g.cells, g.macro, g.next_board, g.player, g.done)
        with torch.no_grad():
            record(rows, kind="fused_inference", device=device, batch=n, graph=False,
                   **timed(lambda: fe(*args), device))
            s = torch.cuda.Stream(device=device)
            s.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(s):
                for _ in range(3):
                    fe(*args)
            torch.cuda.current_stream().wait_stream(s)
            graph = torch.cuda.CUDAGraph()
            # The torch.cuda.graph default capture stream is cached globally in
            # this installed version. Explicit stream is essential across devices.
            with torch.cuda.device(device), torch.cuda.graph(graph, stream=s):
                output = fe(*args)
            g.next_board.fill_(4)
            graph.replay()
            torch.cuda.synchronize(device)
            ref = fe(*args)
            assert torch.allclose(output[0], ref[0], atol=1e-5)
            assert torch.allclose(output[1], ref[1], atol=1e-5)
            g.next_board.fill_(-1)
            record(rows, kind="fused_inference", device=device, batch=n, graph=True,
                   **timed(graph.replay, device),
                   allocated_mib=torch.cuda.memory_allocated(device)/2**20,
                   reserved_mib=torch.cuda.memory_reserved(device)/2**20)
            del graph, output
        del g
    record(rows, kind="hardware_after_load", device=device,
           smi=subprocess.run(["nvidia-smi", "--query-gpu=name,pcie.link.gen.current,pcie.link.width.current,power.draw,temperature.gpu",
                               "--format=csv"], capture_output=True, text=True).stdout)
    del fe, net
    gc.collect()
    torch.cuda.empty_cache()


def training_layout(device, rows):
    torch.cuda.set_device(device)
    # Dummy minibatches only: test the current architecture's kernel throughput,
    # not learning/strength. Both copies start from the existing checkpoint.
    for channels_last in (False, True):
        net = load_checkpoint(str(ROOT / "runs/deep10_c1_300/net_0300.pt"), device).train()
        if channels_last:
            net.to(memory_format=torch.channels_last)
        x = torch.randn(1024, 7, 9, 9, device=device)
        if channels_last:
            x = x.contiguous(memory_format=torch.channels_last)
        p = torch.randint(81, (1024,), device=device)
        v = torch.randint(3, (1024,), device=device)
        o = torch.randint(3, (1024*9,), device=device)
        m = torch.randint(19, (1024,), device=device)
        opt = torch.optim.SGD(net.parameters(), lr=0.02, momentum=0.9, weight_decay=1e-4, nesterov=True)
        scaler = torch.amp.GradScaler("cuda")

        def step():
            opt.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.float16):
                pl, vl, ol, ml = net(x)
            loss = F.cross_entropy(pl.float(), p) + F.cross_entropy(vl.float(), v)
            loss = loss + 0.5 * F.cross_entropy(ol.float().reshape(-1, 3), o) + 0.25 * F.cross_entropy(ml.float(), m)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()

        record(rows, kind="dummy_optimizer_step", device=device, batch=1024, channels_last=channels_last,
               **timed(step, device, repeats=5, groups=3))
        del net, opt, scaler, x
        gc.collect()
        torch.cuda.empty_cache()


def sampling(device, rows):
    torch.cuda.set_device(device)
    w = torch.rand(2_000_000, device=device).square().add_(1e-6)
    record(rows, kind="replay_multinomial_1024", device=device,
           **timed(lambda: torch.multinomial(w, 1024, replacement=True), device))
    record(rows, kind="replay_multinomial_262144", device=device,
           **timed(lambda: torch.multinomial(w, 262144, replacement=True), device, repeats=2, groups=3))
    cdf = w.cumsum(0)
    record(rows, kind="replay_cached_cdf_1024", device=device,
           **timed(lambda: torch.searchsorted(cdf, torch.rand(1024, device=device)*cdf[-1]), device))


def main():
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = True
    torch.manual_seed(0)
    rows = []
    record(rows, kind="environment", torch=torch.__version__, cuda=torch.version.cuda,
           threads=torch.get_num_threads(),
           gpus=[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
           peer_access_0_to_1=torch.cuda.can_device_access_peer(0, 1))
    for device in ("cuda:0", "cuda:1"):
        inference(device, rows)
    training_layout("cuda:0", rows)
    sampling("cuda:0", rows)
    (OUT / "bench.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
