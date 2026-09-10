"""The frozen-teacher study (PLAN6 §4 G0 and the G arms): supervised students on runs/gdata_v1.npz.

    # G0: passes vs data for the plain 8x128 ResNet (data-limited or update-limited, for a fixed teacher?)
    .venv/Scripts/python.exe tools/gstudy.py --data runs/gdata_v1.npz --arm resnet8 --positions 50000,100000,200000,400000 --passes 1,2,4,8 --seeds 0 --device cuda:1 --out runs/plan6/G0_resnet8.json
    # an arm at the full data, two seeds
    .venv/Scripts/python.exe tools/gstudy.py --data runs/gdata_v1.npz --arm resnet8_mask --positions 400000 --passes 8 --seeds 0,1 --device cuda:1 --out runs/plan6/G_arm_c.json

Every student sees the same examples in the same order (the order is a function of --seed only; a student with fewer
positions sees a prefix of it). Targets: the teacher's search policy (cross-entropy, i.e. KL up to a constant), the
teacher's search value (squared error on the student's P(win) - P(loss), so the existing WDL head serves), the exact
3-way result where solved (cross-entropy on the WDL head), and the ownership / margin heads are left untrained (the
study is about policy and value). Augmentation: an independent random D4 element per example, as train2 does.

Metrics on --split (dev by default; the test slice is sealed until the end of Phase G): policy KL and top-1 vs the
teacher; value Brier (squared error of P(win) - P(loss) vs the teacher scalar) and 3-way accuracy vs the exact labels
where solved; the same on the subset of positions whose canonical key does not occur in the train slice (the opening
plies repeat across games); raw regret / optimal-move rate on --set (endgame_v2_dev); the D4 residual (mean policy JS
across the 8 orientations, bits); graph-replayed inference time per evaluation at batch 4096 and batch 1. Writes one
JSON with one record per (positions, passes, seed).

Arms (--arm): resnet10 (10x128), resnet8 (8x128), resnet8_mask (8x128 with the closed-board mask, §1 item 7),
resnet8_tied (8x128 with D4-tied heads, arm (d)), gcnn8x16 (the D4 group-convolutional net at activation width 128,
arm (e)), gcnn8x46 (the same G-CNN at activation width 368 -- 2 459 392 parameters against resnet8's 2 456 014, arm (g);
NOT equal cost: trunk work scales with the square of the activation width, so it costs 7.0x resnet8's per
evaluation on the 3060 -- 595.5 ms vs 84.8 ms per 4096, runs/plan6/G_timing_3060_gcnn8x46.json); uttt.equivariant
has the constructions,
tests/test_equivariant.py their checks.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from timeline import d4_consistency  # noqa: E402
from uttt.batch import INV_PERM, BatchUTTT, encode  # noqa: E402
from uttt.endgame import EndgameSet, evaluate as endgame_evaluate  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import NetConfig, build_net  # noqa: E402
from uttt.selfplay_cont import position_hash_sym  # noqa: E402
from uttt.train2 import symmetrise  # noqa: E402

ARMS = {
    "resnet10": lambda: NetConfig(blocks=10, filters=128),
    "resnet8": lambda: NetConfig(blocks=8, filters=128),
    "resnet8_mask": lambda: NetConfig(blocks=8, filters=128, mask_closed=1),
    "resnet8_tied": lambda: NetConfig(blocks=8, filters=128, head_tying=1),  # (d): D4-tied heads on the ordinary trunk
    "gcnn8x16": lambda: NetConfig(blocks=8, filters=128, gcnn=16),  # (e): 16 base filters x 8 orientations = width 128
    "gcnn8x46": lambda: NetConfig(blocks=8, filters=368, gcnn=46),  # (g): 46 x 8 = width 368, the same parameter count as resnet8 (PLAN6 §9b)
}


def load_data(path: str, device):
    z = np.load(path)
    t = lambda k, dt: torch.from_numpy(np.asarray(z[k], dtype=dt)).to(device)  # noqa: E731
    d = {"cells": t("cells", np.int8), "macro": t("macro", np.int8), "next_board": t("next_board", np.int8), "player": t("player", np.int8),
         "policy": t("teacher_policy", np.float16), "value": t("teacher_value", np.float32), "exact": t("exact_value", np.int8),
         "split": np.asarray(z["split"]), "ply": np.asarray(z["ply"])}
    d["meta"] = json.loads(str(z["meta"]))
    return d


def batch_dict(d, idx):
    """The fields symmetrise() expects, plus the targets; ownership is a dummy (untrained)."""
    return {"cells": d["cells"][idx], "macro": d["macro"][idx], "next_board": d["next_board"][idx], "player": d["player"][idx],
            "policy": d["policy"][idx], "ownership": torch.zeros(len(idx), 9, dtype=torch.int8, device=idx.device),
            "value": d["value"][idx], "exact": d["exact"][idx]}


def train_student(cfg: NetConfig, d, train_idx: torch.Tensor, passes: int, device, seed: int, batch: int = 1024, lr: float = 0.02,
                  log=print):
    torch.manual_seed(seed)
    net = build_net(cfg).to(device)
    opt = torch.optim.SGD(net.parameters(), lr=lr, momentum=0.9, weight_decay=1e-4, nesterov=True)
    scaler = torch.amp.GradScaler("cuda")
    gen = torch.Generator(device=device).manual_seed(seed)
    inv = INV_PERM.to(device)
    n_steps = passes * (len(train_idx) // batch)
    warm = 200
    net.train()
    step = 0
    t0 = time.perf_counter()
    for ep in range(passes):
        perm = train_idx[torch.randperm(len(train_idx), device=device, generator=gen)]  # a fixed order per seed
        for i in range(0, len(perm) - batch + 1, batch):
            step += 1
            frac = step / n_steps
            for g in opt.param_groups:  # warm-up, then two LR drops at 2/3 and 9/10 of the steps (as the runs do)
                g["lr"] = lr * min(1.0, step / warm) * (0.1 if frac > 2 / 3 else 1.0) * (0.1 if frac > 0.9 else 1.0)
            b = batch_dict(d, perm[i : i + batch])
            cells, macro, nb, pol, _ = symmetrise(b, device, gen)
            obs = encode(cells, macro, nb, b["player"], extra=cfg.extra_planes, mask_closed=bool(cfg.mask_closed))
            with torch.autocast("cuda", dtype=torch.float16):
                p_logits, v_logits, _, _ = net(obs)
            logp = torch.log_softmax(p_logits.float()[:, inv], dim=1)
            loss_p = -(pol * logp).sum(1).mean()
            wdl = torch.softmax(v_logits.float(), dim=1)
            loss_v = ((wdl[:, 0] - wdl[:, 2] - b["value"]) ** 2).mean()
            solved = b["exact"] > -2
            loss_e = F.cross_entropy(v_logits.float()[solved], (1 - b["exact"][solved].long()).clamp(0, 2)) if bool(solved.any()) else torch.zeros((), device=device)
            loss = loss_p + loss_v + 0.5 * loss_e
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        log(f"    pass {ep + 1}/{passes}: loss_p {loss_p.item():.3f} loss_v {loss_v.item():.4f} ({time.perf_counter() - t0:.0f}s)")
    net.eval()
    return net, time.perf_counter() - t0


@torch.no_grad()
def student_metrics(fe: FusedEvaluator, d, idx: torch.Tensor, disjoint: torch.Tensor, device, bs: int = 4096) -> dict:
    kl, top1, brier, acc3, n3 = [], [], [], [], 0
    for i in range(0, len(idx), bs):
        j = idx[i : i + bs]
        done = torch.zeros(len(j), dtype=torch.bool, device=device)
        p, v = fe(d["cells"][j], d["macro"][j], d["next_board"][j], d["player"][j], done)
        tp = d["policy"][j].float()
        kl.append((tp * (torch.log(tp.clamp(min=1e-12)) - torch.log(p.clamp(min=1e-12)))).sum(1))
        top1.append((p.argmax(1) == tp.argmax(1)).float())
        brier.append((v - d["value"][j]) ** 2)
        ex = d["exact"][j]
        m = ex > -2
        v3 = torch.where(v > 0.33, 1, torch.where(v < -0.33, -1, 0)).to(torch.int8)
        acc3.append((v3[m] == ex[m]).float())
    kl, top1, brier, acc3 = (torch.cat(x) for x in (kl, top1, brier, acc3))
    out = {"n": int(len(idx)), "policy_kl": float(kl.mean()), "policy_top1": float(top1.mean()), "value_brier": float(brier.mean()),
           "exact_acc3": float(acc3.mean()) if len(acc3) else float("nan"), "n_solved": int(len(acc3))}
    dm = disjoint[: len(idx)]
    out["disjoint"] = {"n": int(dm.sum()), "policy_kl": float(kl[dm].mean()), "policy_top1": float(top1[dm].mean()), "value_brier": float(brier[dm].mean())}
    return out


@torch.no_grad()
def inference_ms(fe: FusedEvaluator, device, n: int) -> float:
    g = BatchUTTT(n, device)
    args = g.state_tuple()
    with torch.cuda.device(device):  # capture on THIS card's stream (PLAN6 §8: one device per process, or say which)
        s = torch.cuda.Stream(device=device)
        s.wait_stream(torch.cuda.current_stream(device))
        with torch.cuda.stream(s):
            for _ in range(3):
                fe(*args)
        torch.cuda.current_stream(device).wait_stream(s)
        graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(graph):
            fe(*args)
    torch.cuda.synchronize(device)
    t = time.perf_counter()
    for _ in range(20):
        graph.replay()
    torch.cuda.synchronize(device)
    return (time.perf_counter() - t) / 20 * 1000


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="runs/gdata_v1.npz")
    ap.add_argument("--arm", default="resnet8", choices=sorted(ARMS))
    ap.add_argument("--positions", default="400000")
    ap.add_argument("--passes", default="8")
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--split", default="dev", choices=["dev", "test"], help="test is sealed until the end of Phase G")
    ap.add_argument("--set", default="suites/endgame_v2_dev.npz")
    ap.add_argument("--n_sym", type=int, default=4096)
    ap.add_argument("--lr", type=float, default=0.02)
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--save", default="", help="directory to save every student's weights as <arm>_p<positions>_x<passes>_s<seed>.pt")
    a = ap.parse_args()
    if a.save:
        os.makedirs(a.save, exist_ok=True)
    device = torch.device(a.device)
    t0 = time.perf_counter()
    d = load_data(a.data, device)
    split = d["split"]
    tr_all = torch.from_numpy(np.flatnonzero(split == 0)).to(device)
    ev_idx = torch.from_numpy(np.flatnonzero(split == (1 if a.split == "dev" else 2))).to(device)
    h = position_hash_sym(d["cells"], d["next_board"], d["player"])
    train_keys = torch.unique(h[tr_all])
    disjoint = ~torch.isin(h[ev_idx], train_keys)  # eval positions whose canonical key never occurs in train
    es = EndgameSet.load(a.set) if a.set else None
    print(f"{a.data}: train {len(tr_all)}, {a.split} {len(ev_idx)} ({int(disjoint.sum())} with no canonical twin in train); arm {a.arm}", flush=True)
    order_gen = torch.Generator(device=device).manual_seed(12345)
    order = tr_all[torch.randperm(len(tr_all), device=device, generator=order_gen)]  # the prefix property: fewer positions = a prefix
    results = []
    for n_pos in (int(x) for x in a.positions.split(",")):
        for passes in (int(x) for x in a.passes.split(",")):
            for seed in (int(x) for x in a.seeds.split(",")):
                cfg = ARMS[a.arm]()
                print(f"  {a.arm} positions {n_pos} passes {passes} seed {seed}", flush=True)
                net, t_train = train_student(cfg, d, order[:n_pos], passes, device, seed, lr=a.lr)
                fe = FusedEvaluator(net, device)
                rec = {"arm": a.arm, "positions": n_pos, "passes": passes, "seed": seed, "steps": passes * (n_pos // 1024), "t_train": round(t_train),
                       "params": sum(p.numel() for p in net.parameters()), a.split: student_metrics(fe, d, ev_idx, disjoint, device)}
                if es is not None:
                    r0 = endgame_evaluate(fe, es, device, sims=(), n_boot=100, symmetrise=False)["rows"][0]
                    rec["endgame"] = {"set": es.meta.get("name"), "wdl_acc": r0["wdl_acc"], "regret_raw": r0["regret"], "optimal_raw": r0["optimal"]}
                k = ev_idx[: a.n_sym]
                js, vstd = d4_consistency(fe, d["cells"][k], d["macro"][k], d["next_board"][k], d["player"][k])
                rec["d4_policy_js_bits"], rec["d4_value_std"] = float(js.mean()), float(vstd.mean())
                rec["ms_batch4096"], rec["ms_batch1"] = inference_ms(fe, device, 4096), inference_ms(fe, device, 1)
                results.append(rec)
                m = rec[a.split]
                print(f"    -> KL {m['policy_kl']:.4f} top1 {m['policy_top1']:.3f} brier {m['value_brier']:.4f} acc3 {m['exact_acc3']:.3f} | disjoint KL {m['disjoint']['policy_kl']:.4f}"
                      + (f" | endgame WDL {100 * rec['endgame']['wdl_acc']:.1f} regret {rec['endgame']['regret_raw']:.3f}" if es is not None else "")
                      + f" | D4 JS {rec['d4_policy_js_bits']:.4f}b | {rec['ms_batch4096']:.2f} ms @4096, {rec['ms_batch1']:.2f} ms @1 ({time.perf_counter() - t0:.0f}s)", flush=True)
                with open(a.out, "w") as f:
                    json.dump({"data": a.data, "meta": d["meta"], "split": a.split, "set": a.set, "results": results}, f, indent=1)
                if a.save:
                    from dataclasses import asdict
                    torch.save({"net": net.state_dict(), "cfg": asdict(cfg), "student": rec},
                               os.path.join(a.save, f"{a.arm}_p{n_pos}_x{passes}_s{seed}.pt"))
                del net, fe
                torch.cuda.empty_cache()
    print(f"wrote {a.out}  [{time.perf_counter() - t0:.0f}s]")


if __name__ == "__main__":
    main()
