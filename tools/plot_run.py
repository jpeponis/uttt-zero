"""Training-curve figure for a run: losses, self-play outcome shares, end reasons, strength ladder.

    .venv/Scripts/python.exe tools/plot_run.py runs/dev1
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"  # validated categorical slots 1-3
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e2"


def smooth(v, k=5):
    out = []
    for i in range(len(v)):
        w = v[max(0, i - k + 1) : i + 1]
        out.append(sum(w) / len(w))
    return out


def style(ax, title, ylabel):
    ax.set_title(title, loc="left", fontsize=10, color=INK, pad=8)
    ax.set_ylabel(ylabel, fontsize=8, color=MUTED)
    ax.set_xlabel("iteration (4096 games each)", fontsize=8, color=MUTED)
    ax.grid(True, axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)


def label_end(ax, x, y, text, color, dy=0):
    ax.annotate(text, (x[-1], y[-1]), xytext=(4, dy), textcoords="offset points", fontsize=8, color=color, va="center")


def main(run: str) -> None:
    rows = [json.loads(l) for l in open(os.path.join(run, "log.jsonl"))]
    it = [r["iter"] + 1 for r in rows]
    ladder_path = os.path.join(run, "ladder.json")
    ladder = json.load(open(ladder_path)) if os.path.exists(ladder_path) else {}

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), facecolor="#fcfcfb")
    fig.subplots_adjust(hspace=0.55, wspace=0.35, left=0.07, right=0.93, top=0.9, bottom=0.1)

    ax = axes[0, 0]
    for k, c, name, dy in (("loss_policy", BLUE, "policy", -7), ("loss_value", ORANGE, "value (WDL)", 7)):
        y = smooth([r[k] for r in rows])
        ax.plot(it, y, color=c, linewidth=1.6, label=name)
        label_end(ax, it, y, name, c, dy)
    style(ax, "Training loss (5-iteration mean)", "cross-entropy")
    ax.set_ylim(0, None)
    ax.legend(frameon=False, fontsize=8, loc="upper right")

    ax = axes[0, 1]
    for k, c, name in (("x_win", BLUE, "X wins"), ("o_win", ORANGE, "O wins"), ("draw", AQUA, "draws")):
        y = smooth([r[k] for r in rows])
        ax.plot(it, y, color=c, linewidth=1.6, label=name)
        label_end(ax, it, y, name, c)
    style(ax, "Self-play outcomes (32 sims, Gumbel exploration)", "share of games")
    ax.set_ylim(0, 0.7)
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    ax = axes[1, 0]
    line = smooth([r["end_line"] for r in rows])
    count = smooth([r["end_count"] for r in rows])
    drawn = smooth([1 - r["end_line"] - r["end_count"] for r in rows])
    for y, c, name in ((line, BLUE, "three boards in a row"), (count, ORANGE, "more boards (count)"), (drawn, AQUA, "equal boards (draw)")):
        ax.plot(it, y, color=c, linewidth=1.6, label=name)
        label_end(ax, it, y, name, c)
    style(ax, "How self-play games end", "share of games")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=8, loc="center right")

    ax = axes[1, 1]
    pts = sorted((int(k.split("_")[1][:4]), v["score"]) for k, v in ladder.items() if "vs net_0150" in k)
    title = "Strength ladder: score vs net_0150 at 64 sims (512 games)"
    if pts:
        label = "checkpoint vs net_0150 (64 sims)"
    else:  # in-run evaluation against fixed anchors (train2 logs vs_<anchor>)
        keys = sorted({k for r in rows for k in r if k.startswith("vs_")})
        pts = [(r["iter"] + 1, r[keys[0]]) for r in rows if keys and keys[0] in r]
        label = f"checkpoint {keys[0].replace('vs_', 'vs ')} (64 sims)" if keys else ""
        title = f"Strength: score {label.split(' ', 1)[1] if label else ''}"
    if pts:
        x, y = zip(*pts)
        ax.plot(x, y, color=BLUE, linewidth=1.6, marker="o", markersize=4, label=label)
        for xi, yi in pts:
            ax.annotate(f"{100 * yi:.0f}", (xi, yi), xytext=(0, 6), textcoords="offset points", fontsize=7, color=MUTED, ha="center")
    ax.axhline(0.5, color=GRID, linewidth=1)
    style(ax, title, "score")
    ax.set_ylim(0, 0.7)
    ax.legend(frameon=False, fontsize=8, loc="lower right")

    cfg_path = os.path.join(run, "config.json")
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
    desc = f"{cfg.get('blocks', 6)}x{cfg.get('filters', 64)} ResNet, Gumbel AlphaZero {cfg.get('sims', 32)} sims, {len(rows)} iterations x {cfg.get('games', 4096)} games"
    fig.suptitle(f"{run}: {desc}", x=0.07, ha="left", fontsize=11, color=INK)
    for a in axes.flat:
        a.set_xlabel(f"iteration ({cfg.get('games', 4096)} games" + (f" x {cfg['steps']} moves" if "steps" in cfg else "") + ")", fontsize=8, color=MUTED)
    out = os.path.join(run, "curves.png")
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "runs/dev1")
