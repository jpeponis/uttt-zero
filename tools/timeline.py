"""Checkpoint timeline (PLAN5 §3 B1): what changed over a training run, checkpoint by checkpoint.

    .venv/Scripts/python.exe tools/timeline.py runs/deep10_c1_300 --corpus runs/deep8_c1_300 --last 20 --device cuda:1

For every net_NNNN.pt of the run: the in-run paired score against each anchor (from log.jsonl, ±6 points — shape
only), the raw value head on the exact endgame set (WDL accuracy, draw recognition, regret, optimal-move rate), the
raw first-move policy on the empty board (entropy in bits and top-1 share — the opening-narrowing statistic of
McGrath et al. 2022), raw policy entropy by ply bucket on held-out positions, and D4 consistency (mean Jensen–Shannon
divergence of the policy across the 8 orientations, mean std of the value). Writes <run>/timeline.json and
<run>/timeline.png with the LR drops marked. Held-out positions come from another run's games (PLAN5 §8).
When <run>/eval_full.jsonl exists (tools/eval_worker.py, PLAN6 E7), the full-suite scores and CIs of every
evaluated checkpoint are carried as full_<anchor> / full_ci_<anchor> and drawn with error bars on the score panel.

--rule count|draw is the rule the checkpoints are READ under: the endgame set must have been solved under it
and the held-out corpus generated under it, and neither is inferred. The run's own training rule is printed
beside it and never substituted for it. The outputs take the rule tag (timeline_draw.json / .png) and the
eval_full ledger read is that rule's, so two readings of one run cannot overwrite each other (PLAN7 §5 K1).

first_top_share / first_top_move / first_entropy_bits are the RAW policy on the empty board, not the agent's
generated self-play top-move share at its training budget; the two differ (M2 row 7, whose remedy is in
tools/empty_board.py, which prints the log's generated share beside this one).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from corpus_stats import corpus_rule  # noqa: E402
from freemove import sample_positions  # noqa: E402
from uttt.batch import SYM_CELL, BatchUTTT, apply_symmetry  # noqa: E402
from uttt.endgame import EndgameSet, breakdown, evaluate  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.rules import RULES, tag_path  # noqa: E402

PLY_BUCKETS = ((0, 7), (8, 19), (20, 31), (32, 43), (44, 80))


def entropy_bits(p: torch.Tensor) -> torch.Tensor:
    return -(p * torch.log2(p.clamp(min=1e-12))).sum(1)


def state_tensors(rows, device):
    t = lambda a, dt: torch.from_numpy(np.asarray(a, dtype=dt)).to(device)  # noqa: E731
    cells = t(np.stack([r[2] for r in rows]), np.int8)
    macro = t(np.stack([r[3] for r in rows]), np.int8)
    nb = t([r[4] for r in rows], np.int8)
    player = t([r[5] for r in rows], np.int8)
    return cells, macro, nb, player


@torch.no_grad()
def policy_stats(fe, cells, macro, nb, player, bs=4096):
    ent, val = [], []
    for i in range(0, cells.shape[0], bs):
        sl = slice(i, i + bs)
        done = torch.zeros(cells[sl].shape[0], dtype=torch.bool, device=cells.device)
        p, v = fe(cells[sl], macro[sl], nb[sl], player[sl], done)
        ent.append(entropy_bits(p))
        val.append(v)
    return torch.cat(ent).cpu().numpy(), torch.cat(val).cpu().numpy()


@torch.no_grad()
def d4_consistency(fe, cells, macro, nb, player):
    """Mean JS divergence (bits) of the policy across the 8 orientations, mapped back to the original frame, and the
    mean std of the value across them. 0 = exactly equivariant."""
    n = cells.shape[0]
    done = torch.zeros(n, dtype=torch.bool, device=cells.device)
    sym = SYM_CELL.to(cells.device)
    P, V = [], []
    for s in range(8):
        c, m, b = apply_symmetry(s, cells, macro, nb)
        p, v = fe(c, m, b, player, done)
        P.append(p.gather(1, sym[s].unsqueeze(0).expand(n, 81)))  # back[:, m] = p[:, SYM_CELL[s][m]]
        V.append(v)
    P = torch.stack(P, 1)  # (n, 8, 81)
    js = entropy_bits(P.mean(1)) - entropy_bits(P.view(n * 8, 81)).view(n, 8).mean(1)
    vstd = torch.stack(V, 1).std(1)
    return js.cpu().numpy(), vstd.cpu().numpy()


@torch.no_grad()
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--corpus", default="runs/deep8_c1_300", help="held-out games (another run's) for the policy statistics")
    ap.add_argument("--last", type=int, default=20)
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--n_sym", type=int, default=4096, help="positions for the D4-consistency measure")
    ap.add_argument("--set", default="suites/endgame_v1.npz")
    ap.add_argument("--rule", choices=RULES, default="count", help="terminal rule the checkpoints are read under (the set must be solved under it)")
    ap.add_argument("--corpus_rule", choices=RULES, default="", help="the held-out corpus's rule, when its directory records none")
    ap.add_argument("--device", default="cuda:1")
    ap.add_argument("--only", default="", help="comma-separated iterations to restrict to, e.g. 20,300")
    ap.add_argument("--no_fig", action="store_true")
    a = ap.parse_args()
    device = torch.device(a.device)
    t0 = time.perf_counter()
    ckpts = sorted(glob.glob(os.path.join(a.run, "net_[0-9][0-9][0-9][0-9].pt")))
    if a.only:
        keep = {int(x) for x in a.only.split(",")}
        ckpts = [p for p in ckpts if int(os.path.basename(p)[4:8]) in keep]
    if not ckpts:
        sys.exit(f"no checkpoints net_NNNN.pt in {a.run}")
    log = {r["iter"] + 1: r for r in map(json.loads, open(os.path.join(a.run, "log.jsonl")))}  # net_NNNN is saved after log iter NNNN-1
    cfg = json.load(open(os.path.join(a.run, "config.json")))
    run_rule = cfg.get("rule", "count")  # the run's TRAINING rule: printed beside --rule, never substituted for it
    anchors = sorted({k[3:] for r in log.values() for k in r if k.startswith("vs_")})
    full_path = tag_path(os.path.join(a.run, "eval_full.jsonl"), a.rule)
    full = {r["iter"]: r for r in map(json.loads, open(full_path))} if os.path.exists(full_path) else {}
    full_anchors = sorted({k for r in full.values() for k in r["anchors"]})
    corpus_src = corpus_rule(a.corpus, a.corpus_rule)
    if corpus_src != a.rule:
        sys.exit(f"{a.corpus} was generated under rule {corpus_src!r} and --rule is {a.rule!r}: the held-out policy "
                 f"statistics would then be read off another rule's positions. Point --corpus at a {a.rule}-rule run.")
    files = sorted(glob.glob(os.path.join(a.corpus, "games", "games_*.npz")))[-a.last :]
    rows = sample_positions(files, 4, 0, 80, a.n, np.random.default_rng(0), a.rule)
    ply = np.array([r[1] for r in rows])
    cells, macro, nb, player = state_tensors(rows, device)
    es = EndgameSet.load(a.set)
    if es.rule != a.rule:  # up front, not on the first checkpoint's evaluate() call
        sys.exit(f"endgame set {a.set} was solved under rule {es.rule!r} and --rule is {a.rule!r}: build a "
                 f"{a.rule}-rule set with tools/endgame.py build --rule {a.rule}.")
    empty = BatchUTTT(1, device, a.rule)
    print(f"{a.run}: {len(ckpts)} checkpoints; {len(rows)} held-out positions from {len(files)} files of {a.corpus}; "
          f"endgame set {es.meta['name']} ({es.n}); read under rule {a.rule} (the run trained under {run_rule})")
    out = []
    for p in ckpts:
        it = int(os.path.basename(p)[4:8])
        fe = FusedEvaluator(load_checkpoint(p, device), device)
        rec = {"iter": it, "checkpoint": p}
        lr = log.get(it, {})
        for k in anchors:
            if "vs_" + k in lr:
                rec["vs_" + k] = lr["vs_" + k]
        for k, v in full.get(it, {}).get("anchors", {}).items():
            rec["full_" + k], rec["full_ci_" + k] = v["score"], v["ci"]
        rec["lr"] = lr.get("lr")
        r0 = evaluate(fe, es, device, sims=(), n_boot=100, symmetrise=False, rule=a.rule)["rows"][0]
        rec.update(eg_wdl_acc=r0["wdl_acc"], eg_draw_recognition=breakdown(es, r0, "wdl_acc")["draw"][0], eg_regret=r0["regret"], eg_optimal=r0["optimal"])
        probs, _ = fe(empty.cells, empty.macro, empty.next_board, empty.player, empty.done)
        # the RAW policy on the empty board, not the generated self-play top-move share (M2 row 7)
        rec.update(first_entropy_bits=float(entropy_bits(probs)[0]), first_top_share=float(probs.max()), first_top_move=int(probs.argmax()))
        ent, val = policy_stats(fe, cells, macro, nb, player)
        rec["entropy_by_ply"] = {f"{lo}-{hi}": float(ent[(ply >= lo) & (ply <= hi)].mean()) for lo, hi in PLY_BUCKETS}
        rec["abs_value_by_ply"] = {f"{lo}-{hi}": float(np.abs(val[(ply >= lo) & (ply <= hi)]).mean()) for lo, hi in PLY_BUCKETS}
        js, vstd = d4_consistency(fe, cells[: a.n_sym], macro[: a.n_sym], nb[: a.n_sym], player[: a.n_sym])
        ps = ply[: a.n_sym]
        rec["d4_policy_js_bits"], rec["d4_value_std"] = float(js.mean()), float(vstd.mean())
        rec["d4_policy_js_by_ply"] = {f"{lo}-{hi}": float(js[(ps >= lo) & (ps <= hi)].mean()) for lo, hi in PLY_BUCKETS}
        rec["d4_value_std_by_ply"] = {f"{lo}-{hi}": float(vstd[(ps >= lo) & (ps <= hi)].mean()) for lo, hi in PLY_BUCKETS}
        out.append(rec)
        vs = " ".join(f"vs {k} {100 * rec['vs_' + k]:4.1f}" for k in anchors if "vs_" + k in rec)
        print(f"  net_{it:04d}: {vs} | endgame WDL {100 * rec['eg_wdl_acc']:.1f} draws {100 * rec['eg_draw_recognition']:.1f} regret {rec['eg_regret']:.3f} "
              f"| first move [{rec['first_top_move']}] top1 {rec['first_top_share']:.2f} H {rec['first_entropy_bits']:.2f}b "
              f"| H by ply " + " ".join(f"{v:.2f}" for v in rec["entropy_by_ply"].values())
              + f" | D4 JS {rec['d4_policy_js_bits']:.3f}b vstd {rec['d4_value_std']:.3f}  ({time.perf_counter() - t0:.0f}s)", flush=True)
    meta = {"run": a.run, "rule": a.rule, "run_rule": run_rule, "corpus": a.corpus, "corpus_rule": corpus_src,
            "corpus_files": [os.path.basename(f) for f in files], "n_positions": len(rows), "n_sym": a.n_sym,
            "endgame_set": a.set, "lr_drops": cfg.get("lr_drops", ""), "anchors": anchors, "full_anchors": full_anchors,
            "ply_buckets": [list(b) for b in PLY_BUCKETS],
            "first_move_note": "first_top_share / first_top_move / first_entropy_bits are the raw policy on the "
                               "empty board, not the generated self-play top-move share (M2 row 7)"}
    path = tag_path(os.path.join(a.run, "timeline.json"), a.rule)
    with open(path, "w") as f:
        json.dump({"meta": meta, "rows": out}, f, indent=1)
    print(f"wrote {path}  [{time.perf_counter() - t0:.0f}s]")
    if not a.no_fig:
        plot(out, meta, tag_path(os.path.join(a.run, "timeline.png"), a.rule))


def plot(rows, meta, path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from plot_run import AQUA, BLUE, GRID, INK, MUTED, ORANGE, style

    SEQ = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]  # sequential blue, steps 250-700 (ply buckets are ordered)
    it = [r["iter"] for r in rows]
    drops = [int(d) for d in str(meta.get("lr_drops", "")).split(",") if d]
    fig, axes = plt.subplots(2, 3, figsize=(15, 7.5), facecolor="#fcfcfb")
    fig.subplots_adjust(hspace=0.5, wspace=0.3, left=0.05, right=0.98, top=0.88, bottom=0.09)

    def series(ax, y, color, name):
        ax.plot(it, y, color=color, linewidth=2, marker="o", markersize=4, label=name)

    ax = axes[0, 0]
    for k, c in zip(meta["anchors"], (BLUE, ORANGE, AQUA)):
        pts = [(r["iter"], r["vs_" + k]) for r in rows if "vs_" + k in r]
        if pts:
            ax.plot(*zip(*pts), color=c, linewidth=2, marker="o", markersize=4, label=f"vs {k}")
    for k, c in zip(meta.get("full_anchors", []), (BLUE, ORANGE, AQUA)):
        pts = [(r["iter"], r["full_" + k], r["full_ci_" + k]) for r in rows if "full_" + k in r]
        if pts:
            x, y, ci = zip(*pts)
            ax.errorbar(x, y, yerr=[[yy - lo for yy, (lo, hi) in zip(y, ci)], [hi - yy for yy, (lo, hi) in zip(y, ci)]],
                        color=c, linewidth=0, elinewidth=1.2, marker="s", markersize=5, capsize=2, label=f"vs {k} (full suite)")
    ax.axhline(0.5, color=GRID, linewidth=1)
    style(ax, "Paired score vs anchors (64 sims): in-run ±6; squares: full suite ±2.8", "score")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=8, loc="lower right")

    ax = axes[0, 1]
    series(ax, [r["eg_wdl_acc"] for r in rows], BLUE, "WDL accuracy")
    series(ax, [r["eg_draw_recognition"] for r in rows], ORANGE, "draw recognition")
    series(ax, [r["eg_optimal"] for r in rows], AQUA, "optimal move")
    style(ax, f"Raw value head on {os.path.basename(meta['endgame_set'])}", "share correct")
    ax.set_ylim(0.4, 1)
    ax.legend(frameon=False, fontsize=8, loc="lower left")

    ax = axes[0, 2]
    series(ax, [r["eg_regret"] for r in rows], BLUE, "regret")
    style(ax, "Raw policy regret on the endgame set", "exact value lost per move")
    ax.set_ylim(0, None)

    ax = axes[1, 0]
    series(ax, [r["first_top_share"] for r in rows], BLUE, "top-1 share")
    style(ax, f"Raw first-move policy: share of the top move (final: [{rows[-1]['first_top_move']}])", "probability")
    ax.set_ylim(0, 1)

    ax = axes[1, 1]
    for (lo, hi), c in zip(meta["ply_buckets"], SEQ):
        key = f"{lo}-{hi}"
        series(ax, [r["entropy_by_ply"][key] for r in rows], c, f"ply {lo}-{hi}")
    series(ax, [r["first_entropy_bits"] for r in rows], ORANGE, "empty board")
    style(ax, "Raw policy entropy on held-out positions, by ply", "bits")
    ax.set_ylim(0, None)
    ax.legend(frameon=False, fontsize=7, loc="upper right", ncol=2)

    ax = axes[1, 2]
    series(ax, [r["d4_policy_js_bits"] for r in rows], BLUE, "policy JS across D4")
    style(ax, "D4 consistency: policy JS divergence over the 8 orientations", "bits (0 = equivariant)")
    ax.set_ylim(0, None)

    for ax in axes.flat:
        for d in drops:
            ax.axvline(d, color=MUTED, linewidth=1, linestyle=(0, (3, 3)))
        ax.set_xlabel("iteration", fontsize=8, color=MUTED)
    fig.suptitle(f"{meta['run']}: checkpoint timeline (dashed: LR drops at {', '.join(map(str, drops))}; held-out positions from {meta['corpus']})",
                 x=0.05, ha="left", fontsize=11, color=INK)
    fig.savefig(path, dpi=130)
    print("wrote", path)


if __name__ == "__main__":
    main()
