"""Out-of-process checkpoint evaluator (PLAN6 E7): scores a run's numbered checkpoints on the FULL paired suite against
fixed anchors and on an exact endgame set, on its own device, while (or after) the trainer runs on the other one.

    .venv/Scripts/python.exe tools/eval_worker.py --run runs/deep8_c1_300_e2 --device cuda:1              # follow a live run
    .venv/Scripts/python.exe tools/eval_worker.py --run runs/deep8_c1_300 --once --only 200,220,260,280,300   # a finished run (F2)

The trainer then runs with --eval_every 0 --ckpt_every 10: no evaluation path in the training process at all — the
in-run evaluation is where all three driver faults happened, and its 100-opening subset (±6 points) could not
resolve the questions the checkpoint timelines ask (the second LR drop; "flat after 220"). Here every checkpoint
gets the full suite (516 openings × 2 colours, ±2.8) at --sims per move, with the CI, plus the endgame set.

Behaviour: watches <run>/net_NNNN.pt (the trainer writes them atomically, E5), keeps <run>/eval_full.jsonl with one
line per evaluated checkpoint (iteration, file hash, evaluator settings, per-anchor score / CI / Elo, endgame raw
and search metrics, timing). While the run is live it always takes the NEWEST unevaluated checkpoint (so it never
falls behind); once <run>/DONE exists it finishes the outstanding ones in order and exits. --once: evaluate what is
pending now and exit. tools/timeline.py reads eval_full.jsonl when present. Cost on the 3060: ≈ 4–8 min per anchor
match plus ≈ 2 min for the endgame set (an 8-block iteration is ≈ 165 s, so every tenth checkpoint keeps the card
about a third busy with one anchor).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.arena import SearchPlayer  # noqa: E402
from uttt.endgame import EndgameSet, evaluate as endgame_evaluate  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.openings import Suite, play_paired, summarize  # noqa: E402
from uttt.search import SearchConfig  # noqa: E402


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def anchor_name(p: str) -> str:  # runs/v2b/net_0150.pt -> v2b_net_0150 (as train2 names them)
    return f"{os.path.basename(os.path.dirname(p))}_{os.path.splitext(os.path.basename(p))[0]}"


class Worker:
    """Candidate evaluator and per-anchor players are built once and reused (the candidate's weights are refreshed
    in place); CUDA graphs are captured once, the way train2.EvalKit does it."""

    def __init__(self, a, device) -> None:
        self.a, self.device = a, device
        self.suite = Suite.load(a.suite)
        if a.cap:
            self.suite = self.suite.subset(a.cap)
        self.es = EndgameSet.load(a.set) if a.set else None
        self.cfg = SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(a.sims, 24))
        self.anchors = {anchor_name(p): FusedEvaluator(load_checkpoint(p, device), device) for p in a.anchors.split(",") if p}
        self.pb = {k: SearchPlayer(ev, self.suite.n, self.cfg, device) for k, ev in self.anchors.items()}
        self.fe = self.pa = None
        self.eg_cache: dict = {}
        print(f"evaluator: suite {a.suite} ({self.suite.n} openings), anchors {list(self.anchors)}, {a.sims} sims, "
              f"endgame set {a.set or 'off'}, device {torch.cuda.get_device_name(device) if device.type == 'cuda' else 'cpu'}", flush=True)

    def evaluate(self, path: str) -> dict:
        t0 = time.perf_counter()
        net = load_checkpoint(path, self.device)
        if self.fe is None:
            self.fe = FusedEvaluator(net, self.device)
            self.pa = SearchPlayer(self.fe, self.suite.n, self.cfg, self.device)
        else:
            self.fe.refresh(net)
        rec = {"iter": int(os.path.basename(path)[4:8]), "checkpoint": path, "sha256": sha256(path),
               "suite": self.suite.meta.get("name"), "openings": self.suite.n, "sims": self.a.sims, "anchors": {}}
        for k, pb in self.pb.items():
            t1 = time.perf_counter()
            o = summarize(play_paired(self.pa, pb, self.suite, self.device), n_boot=2000)["overall"]
            rec["anchors"][k] = {"score": round(o["score"], 4), "ci": [round(x, 4) for x in o["ci"]], "elo": round(o["elo"], 1),
                                 "elo_ci": [round(x, 1) for x in o["elo_ci"]], "draws": round(o["draws"], 3), "seconds": round(time.perf_counter() - t1)}
        if self.es is not None:
            t1 = time.perf_counter()
            res = endgame_evaluate(self.fe, self.es, self.device, sims=(self.a.sims,), n_boot=200, symmetrise=False,
                                   graph=self.device.type == "cuda", search_cache=self.eg_cache)
            raw, srch = res["rows"][0], res["rows"][-1]
            rec["endgame"] = {"set": self.es.meta.get("name"), "wdl_acc": round(raw["wdl_acc"], 4), "regret_raw": round(raw["regret"], 4),
                              "optimal_raw": round(raw["optimal"], 4), "regret_search": round(srch["regret"], 4),
                              "optimal_search": round(srch["optimal"], 4), "seconds": round(time.perf_counter() - t1)}
        rec["seconds"] = round(time.perf_counter() - t0)
        rec["when"] = time.strftime("%Y-%m-%d %H:%M:%S")
        return rec


def pending(run: str, done: set, only: set | None) -> list[str]:
    files = sorted(glob.glob(os.path.join(run, "net_[0-9][0-9][0-9][0-9].pt")))
    out = [p for p in files if int(os.path.basename(p)[4:8]) not in done]
    if only is not None:
        out = [p for p in out if int(os.path.basename(p)[4:8]) in only]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--anchors", default="runs/v2b/net_0150.pt")
    ap.add_argument("--sims", type=int, default=64)
    ap.add_argument("--suite", default="suites/openings_v1.npz")
    ap.add_argument("--cap", type=int, default=0, help="openings per sub-suite (0 = the full suite; the point of this worker)")
    ap.add_argument("--set", default="suites/endgame_v2_dev.npz", help="exact endgame set ('' = off)")
    ap.add_argument("--only", default="", help="comma-separated iterations to evaluate (default: every numbered checkpoint)")
    ap.add_argument("--once", action="store_true", help="evaluate what is pending and exit (do not wait for DONE)")
    ap.add_argument("--poll", type=int, default=30, help="seconds between checks while the run is live")
    ap.add_argument("--device", default="cuda:1")
    a = ap.parse_args()
    device = torch.device(a.device)
    only = {int(x) for x in a.only.split(",") if x} or None
    out_path = os.path.join(a.run, "eval_full.jsonl")
    done = {json.loads(l)["iter"] for l in open(out_path)} if os.path.exists(out_path) else set()
    worker = Worker(a, device)
    settings = {"anchors": a.anchors, "sims": a.sims, "suite": a.suite, "cap": a.cap, "set": a.set, "device": a.device}
    while True:
        todo = pending(a.run, done, only)
        finished = os.path.exists(os.path.join(a.run, "DONE"))
        if not todo:
            if finished or a.once:
                break
            time.sleep(a.poll)
            continue
        path = todo[0] if (finished or a.once) else todo[-1]  # live run: the newest first, so the worker never falls behind
        rec = worker.evaluate(path)
        rec["settings"] = settings
        done.add(rec["iter"])
        with open(out_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        vs = "  ".join(f"vs {k} {100 * v['score']:.1f} [{100 * v['ci'][0]:.1f}, {100 * v['ci'][1]:.1f}]" for k, v in rec["anchors"].items())
        eg = f"  endgame WDL {100 * rec['endgame']['wdl_acc']:.1f} regret {rec['endgame']['regret_raw']:.3f}" if "endgame" in rec else ""
        print(f"net_{rec['iter']:04d}: {vs}{eg}  ({rec['seconds']}s; {len(todo) - 1} pending)", flush=True)
    print(f"done: {len(done)} checkpoints in {out_path}")


if __name__ == "__main__":
    main()
