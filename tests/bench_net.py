"""Inference throughput of candidate network sizes on each GPU (positions/sec, batched)."""
import os
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.model import NetConfig, ResNet  # noqa: E402


def bench(dev, blocks, filters, batch, amp, iters=30):
    net = ResNet(NetConfig(blocks=blocks, filters=filters)).to(dev).eval()
    x = torch.randn(batch, 7, 9, 9, device=dev)
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=amp):
        for _ in range(5):
            net(x)
        torch.cuda.synchronize(dev)
        t = time.perf_counter()
        for _ in range(iters):
            net(x)
        torch.cuda.synchronize(dev)
    dt = (time.perf_counter() - t) / iters
    params = sum(p.numel() for p in net.parameters())
    return dt, batch / dt, params


if __name__ == "__main__":
    torch.backends.cudnn.benchmark = True
    for dev in ["cuda:0", "cuda:1"][: torch.cuda.device_count()]:
        print(f"== {torch.cuda.get_device_name(dev)} ({dev})")
        for blocks, filters in [(4, 64), (6, 64), (6, 96), (8, 128), (10, 128)]:
            for batch in [512, 4096, 16384]:
                for amp in [False, True]:
                    dt, tput, params = bench(dev, blocks, filters, batch, amp)
                    print(f"  {blocks}x{filters} ({params/1e6:.2f}M)  batch {batch:6d}  {'fp16' if amp else 'fp32'}: "
                          f"{dt*1000:7.2f} ms/batch  {tput/1e6:6.2f} M pos/s")
