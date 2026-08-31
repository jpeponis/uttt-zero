"""FusedEvaluator must match Evaluator (within fp16 tolerance) and be faster."""
import os
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import Evaluator, NetConfig, ResNet  # noqa: E402

DEV = os.environ.get("UTTT_DEV", "cuda:0")


def main(n=4096):
    torch.manual_seed(0)
    g = BatchUTTT(n, DEV)
    for _ in range(10):
        m = g.legal_mask().float() + 1e-9
        g.step(torch.multinomial(m, 1).squeeze(1))
    ck = "runs/dev1/net_0200.pt"
    net = ResNet(NetConfig())
    if os.path.exists(ck):
        net.load_state_dict(torch.load(ck, map_location="cpu", weights_only=False)["net"], strict=False)
    ev = Evaluator(net, DEV)
    fe = FusedEvaluator(net, DEV)
    args = (g.cells, g.macro, g.next_board, g.player, g.done)
    p1, v1 = ev(*args)
    p2, v2 = fe(*args)
    print(f"max |dp| = {float((p1 - p2).abs().max()):.4f}   max |dv| = {float((v1 - v2).abs().max()):.4f}   argmax agreement = {float((p1.argmax(1) == p2.argmax(1)).float().mean()):.4f}")
    assert float((v1 - v2).abs().max()) < 0.02 and float((p1 - p2).abs().max()) < 0.02
    for name, f in (("Evaluator (autocast)", ev), ("FusedEvaluator", fe)):
        for _ in range(3):
            f(*args)
        torch.cuda.synchronize(DEV)
        t = time.perf_counter()
        for _ in range(20):
            f(*args)
        torch.cuda.synchronize(DEV)
        dt = (time.perf_counter() - t) / 20
        print(f"{name:22s}: {dt * 1000:6.2f} ms per batch of {n}  ({n / dt / 1e6:.2f} M pos/s)")


if __name__ == "__main__":
    main()
