"""Summarise a tools/probe.py fit (PLAN5 §3 B2): per concept, accuracy above the random-init control by layer and
checkpoint, the layer where it is best read, and the checkpoint from which it is "learned" (90 % of its final gain).

    .venv/Scripts/python.exe tools/probe_report.py runs/deep10_c1_300/probes.json [--fig runs/deep10_c1_300/probes.png]

Class labels are scored by test accuracy, regressions by test R²; "gain" is the metric minus the same probe on the
randomly initialised net at the same layer (iteration 0 in the JSON), so a concept that the board encoding already
exposes linearly (count_margin, the free-move flag) shows a gain near zero. A heatmap grid of the chosen concepts
(layer × checkpoint, gain over control) is written when --fig is given.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

KEY = ["free_move", "target_board", "threats_for", "threats_against", "threat_for_any", "dead_count", "local_win_now",
       "local_threat_against", "macro_win_now", "count_margin", "open_count", "empties", "status_4", "final_own_4", "z",
       "best_move_now", "best_move_ply2", "exact_value"]


def metric(d: dict) -> float:
    return d["acc"] if "acc" in d else d["r2"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--concepts", default=",".join(KEY))
    ap.add_argument("--fig", default="")
    a = ap.parse_args()
    r = json.load(open(a.json))
    layers = r["meta"]["layers"]
    ck = {int(k): v for k, v in r["checkpoints"].items()}
    its = sorted(ck)
    control = ck.get(0)
    concepts = [c for c in a.concepts.split(",") if c in r["meta"]["kinds"]]
    trained = [i for i in its if i > 0]
    if not trained:
        sys.exit("no trained checkpoints in the file yet (only the control)")
    print(f"{a.json}: {len(trained)} checkpoints {'+ control ' if control else ''}x {len(layers)} layers; "
          f"{r['meta']['n_train']} train / {r['meta']['n_test']} test positions; probe hidden={r['meta']['hidden']}")
    print(f"\n{'concept':22s} {'kind':9s} {'base':>6s} {'ctrl@best':>9s} {'final':>6s} {'gain':>6s} {'best layer':>10s} {'learned by':>10s}  gain by layer at the final checkpoint")
    grids = {}
    for c in concepts:
        kind = r["meta"]["kinds"][c]
        last = ck[trained[-1]]["layers"]
        base = last[layers[0]][c].get("majority", 0.0) if kind != "reg" else 0.0
        fin = np.array([metric(last[l][c]) for l in layers])
        ctl = np.array([metric(control["layers"][l][c]) for l in layers]) if control else np.zeros(len(layers))
        gain = fin - ctl
        b = int(np.argmax(gain))
        # when learned: first checkpoint whose gain at the best layer reaches 90 % of the final gain
        g_by_it = np.array([metric(ck[i]["layers"][layers[b]][c]) - ctl[b] for i in trained])
        learned = next((i for i, g in zip(trained, g_by_it) if g >= 0.9 * gain[b]), trained[-1]) if gain[b] > 0.01 else "-"
        grids[c] = np.array([[metric(ck[i]["layers"][l][c]) - (metric(control["layers"][l][c]) if control else 0) for i in trained] for l in layers])
        print(f"{c:22s} {kind:9s} {base:6.3f} {ctl[b]:9.3f} {fin[b]:6.3f} {gain[b]:+6.3f} {layers[b]:>10s} {str(learned):>10s}  "
              + " ".join(f"{g:+.2f}" for g in gain))
    if a.fig:
        plot(grids, layers, trained, a.fig, r["meta"])


def plot(grids, layers, its, path, meta) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from plot_run import INK, MUTED

    names = list(grids)
    n = len(names)
    cols = 4
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(4.2 * cols, 2.6 * rows), facecolor="#fcfcfb")
    fig.subplots_adjust(hspace=0.75, wspace=0.35, left=0.06, right=0.98, top=0.9, bottom=0.08)
    for ax, c in zip(axes.flat, names):
        g = grids[c]
        vmax = max(0.05, float(np.nanmax(np.abs(g))))
        im = ax.imshow(g, aspect="auto", cmap="Blues", vmin=0, vmax=vmax, origin="lower")
        ax.set_title(c, loc="left", fontsize=9, color=INK)
        ax.set_yticks(range(len(layers)))
        ax.set_yticklabels([l.replace("block", "b") for l in layers], fontsize=6, color=MUTED)
        ax.set_xticks(range(len(its)))
        ax.set_xticklabels(its, fontsize=6, color=MUTED, rotation=90)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        cb = fig.colorbar(im, ax=ax, fraction=0.05, pad=0.02)
        cb.ax.tick_params(labelsize=6, colors=MUTED, length=0)
        cb.outline.set_visible(False)
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    kind = "linear" if not meta["hidden"] else f"MLP-{meta['hidden']}"
    fig.suptitle(f"{meta['run']}: probe gain over the random-init control (test accuracy or R²), layer x checkpoint; "
                 f"{kind} probes on {meta['n_train']} held-out positions", x=0.06, ha="left", fontsize=10, color=INK)
    fig.savefig(path, dpi=130)
    print("wrote", path)


if __name__ == "__main__":
    main()
