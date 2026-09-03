"""Concept probes on the residual stream (PLAN5 §3 B2): can the hand-written concepts of uttt.concepts — and two
look-ahead labels — be read off the net's activations, at which layer, and from which checkpoint on?

    # 1. dataset: held-out positions with concept labels, final board ownership, and look-ahead labels
    .venv/Scripts/python.exe tools/probe.py build --corpus runs/deep8_c1_300 --last 20 --net runs/deep10_c1_300/net_0300.pt --out runs/probe_data_deep8late.npz --device cuda:1
    # 2. probes: one linear (or --mlp) read-out per concept, per layer, per checkpoint; random-init net as the control
    .venv/Scripts/python.exe tools/probe.py fit --data runs/probe_data_deep8late.npz --run runs/deep10_c1_300 --only 20,100,200,300 --control --device cuda:1

Labels: everything in uttt.concepts.CONCEPTS; final_own_b (who owns board b at the end of the source game: 0 self /
1 neither / 2 opponent, the ownership head's own classes); z (game result for the mover); best_move_now and
best_move_ply2 (the move the source net's 256-sim search prefers now and two plies down its principal variation —
the solver's exact line where the position has <= --max_exact empties); exact_value where solved. Positions are
split into train / test by source game. Layers: "input" (the encoded planes), "stem", "block01".. Metrics: test
accuracy (with the majority-class baseline) for class labels, test R² for regressions. Report accuracy above the
random-init control, never raw accuracy (PLAN5 §1c). Writes <run>/probes[_mlp].json.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from atlas import principal_variations  # noqa: E402
from uttt.batch import BatchUTTT, encode  # noqa: E402
from uttt.concepts import CONCEPTS, concept_labels  # noqa: E402
from uttt.game import FULL, UTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import NetConfig, ResNet, load_checkpoint  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.solver import empties_in_open_boards, solve_children  # noqa: E402

LABELS = dict(CONCEPTS)
LABELS.update({f"final_own_{b}": ("class:3", f"board {b} at the end of the game: self / neither / opponent") for b in range(9)})
LABELS.update({"z": ("class:3", "final result for the mover: loss / draw / win"),
               "best_move_now": ("class:81", "the source net's 256-sim (or exact) best move"),
               "best_move_ply2": ("class:81", "the move two plies down the source net's principal variation (exact where solved)"),
               "exact_value": ("class:3", "exact value for the mover (loss / draw / win) where solved")})


# ---- build ---------------------------------------------------------------------------------------
def sample_games(files, per_game, ply_hi, n_max, rng):
    """Positions with provenance and the source game's end (final macro, winner). ≤ per_game positions per game."""
    rows = []
    gid = 0
    for f in files:
        z = np.load(f)
        moves, lengths = z["moves"], z["lengths"]
        for k in range(len(lengths)):
            L = int(lengths[k])
            plies = list(range(0, min(ply_hi, L - 1) + 1))
            want = set(rng.choice(plies, size=min(per_game, len(plies)), replace=False).tolist())
            g = UTTT()
            snaps = []
            for t in range(L):
                if t in want:
                    snaps.append((t, g.cells.copy(), g.macro.copy(), g.next_board, g.player))
                g.play(int(moves[k, t]))
            for t, c, m, nb, p in snaps:
                rows.append((gid, t, c, m, nb, p, g.macro.copy(), g.winner))
            gid += 1
            if len(rows) >= n_max:
                return rows
    return rows


def exact_pv3(args):
    """(cells, macro, nb, player) -> (exact value, best move now, best move two plies on or -1) by greedy exact play."""
    cells, macro, nb, player = args
    g = UTTT()
    g.cells[:], g.macro[:], g.next_board, g.player = cells, macro, int(nb), int(player)
    g.move_count = int((g.cells != 0).sum())
    v, ch = solve_children((g.cells, g.macro, g.next_board, g.player))
    m0 = int(np.flatnonzero(ch == ch.max())[0])
    line = [m0]
    for _ in range(2):
        g.play(line[-1])
        if g.done:
            break
        _, ch = solve_children((g.cells, g.macro, g.next_board, g.player))
        line.append(int(np.flatnonzero(ch == ch.max())[0]))
    return int(v), m0, (line[2] if len(line) == 3 else -1)


@torch.no_grad()
def cmd_build(a) -> None:
    device = torch.device(a.device)
    t0 = time.perf_counter()
    files = sorted(glob.glob(os.path.join(a.corpus, "games", "games_*.npz")))[-a.last :]
    rng = np.random.default_rng(a.seed)
    rows = sample_games(files, a.per_game, a.ply_hi, a.n_train + a.n_test, rng)
    N = len(rows)
    gid = np.array([r[0] for r in rows])
    ply = np.array([r[1] for r in rows], dtype=np.int16)
    cells = np.stack([r[2] for r in rows]).astype(np.int8)
    macro = np.stack([r[3] for r in rows]).astype(np.int8)
    nb = np.array([r[4] for r in rows], dtype=np.int8)
    player = np.array([r[5] for r in rows], dtype=np.int8)
    final = np.stack([r[6] for r in rows]).astype(np.int8)
    winner = np.array([r[7] for r in rows], dtype=np.int8)
    games = np.unique(gid)
    test_games = set(rng.choice(games, size=int(round(len(games) * a.n_test / (a.n_train + a.n_test))), replace=False).tolist())
    split = np.array([g in test_games for g in gid], dtype=np.int8)
    print(f"{N} positions from {len(games)} games of {a.corpus} ({[os.path.basename(f) for f in files][:3]}...); test games {len(test_games)} "
          f"({int(split.sum())} positions)  [{time.perf_counter() - t0:.0f}s]", flush=True)
    lab = concept_labels(cells, macro, nb, player)
    p1 = player[:, None]
    lab.update({f"final_own_{b}": np.where(final[:, b] == p1[:, 0], 0, np.where(final[:, b] == -p1[:, 0], 2, 1)).astype(np.int64) for b in range(9)})
    lab["z"] = (winner * player + 1).astype(np.int64)
    # look-ahead labels from the source net's search
    fe = FusedEvaluator(load_checkpoint(a.net, device), device)
    now, ply2 = np.full(N, -1, dtype=np.int64), np.full(N, -1, dtype=np.int64)
    bs = 4096
    for i in range(0, N, bs):
        sl = slice(i, min(i + bs, N))
        n = sl.stop - sl.start
        g = BatchUTTT(n, device)
        g.cells[:] = torch.from_numpy(cells[sl]).to(device)
        g.macro[:] = torch.from_numpy(macro[sl]).to(device)
        g.next_board[:] = torch.from_numpy(nb[sl]).to(device)
        g.player[:] = torch.from_numpy(player[sl]).to(device)
        s = BatchedSearch(fe, n, SearchConfig(n_sims=a.sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=device.type == "cuda", depth_cap=min(a.sims, 24)), device)
        r = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
        pvs = principal_variations(s, 3)
        now[sl] = r.action.cpu().numpy()
        ply2[sl] = [pv[2] if len(pv) == 3 else -1 for pv in pvs]
    print(f"search labels done [{time.perf_counter() - t0:.0f}s]", flush=True)
    empt = np.array([empties_in_open_boards(cells[i], macro[i]) for i in range(N)])
    ex = np.flatnonzero(empt <= a.max_exact)
    exact = np.full(N, -1, dtype=np.int64)
    with Pool(a.processes) as pool:
        res = pool.map(exact_pv3, [(cells[i], macro[i], nb[i], player[i]) for i in ex], chunksize=16)
    for i, (v, m0, m2) in zip(ex, res):
        exact[i], now[i], ply2[i] = v + 1, m0, m2
    lab.update(best_move_now=now, best_move_ply2=ply2, exact_value=exact)
    print(f"exact labels for {len(ex)} positions with <= {a.max_exact} empties [{time.perf_counter() - t0:.0f}s]", flush=True)
    meta = {"corpus": a.corpus, "files": [os.path.basename(f) for f in files], "net": a.net, "sims": a.sims, "max_exact": a.max_exact,
            "per_game": a.per_game, "ply_hi": a.ply_hi, "seed": a.seed, "labels": LABELS}
    np.savez_compressed(a.out, cells=cells, macro=macro, next_board=nb, player=player, ply=ply, game_id=gid, split=split, empties=empt,
                        meta=np.array(json.dumps(meta)), **{"label_" + k: v for k, v in lab.items()})
    print(f"wrote {a.out}: {N} positions, {len(lab)} labels  [{time.perf_counter() - t0:.0f}s]")


# ---- fit -----------------------------------------------------------------------------------------
class Heads(nn.Module):
    def __init__(self, d_in: int, specs: dict, hidden: int = 0) -> None:
        super().__init__()
        self.specs = specs
        self.body = nn.Sequential(nn.Linear(d_in, hidden), nn.ReLU()) if hidden else nn.Identity()
        d = hidden or d_in
        self.heads = nn.ModuleDict({k: nn.Linear(d, int(kind[6:]) if kind.startswith("class:") else 2 if kind == "binary" else 1)
                                    for k, (kind, _) in specs.items()})

    def forward(self, x):
        h = self.body(x)
        return {k: head(h) for k, head in self.heads.items()}

    def loss(self, out, y):
        tot = 0.0
        for k, (kind, _) in self.specs.items():
            if kind == "reg":
                m = ~torch.isnan(y[k])
                if m.any():
                    tot = tot + F.mse_loss(out[k][m, 0], y[k][m])
            else:
                tot = tot + F.cross_entropy(out[k], y[k], ignore_index=-1)
        return tot


@torch.no_grad()
def layer_activations(net, cells, macro, nb, player, layer: str, device, bs=2048):
    """Flattened activations (N, F) fp16 at one layer: 'input', 'stem' or 'blockNN' (1-based)."""
    outs = []
    store = {}
    mod = None if layer == "input" else net.stem if layer == "stem" else net.blocks[int(layer[5:]) - 1]
    h = mod.register_forward_hook(lambda m, i, o: store.__setitem__("a", o)) if mod is not None else None
    for i in range(0, cells.shape[0], bs):
        sl = slice(i, i + bs)
        done = torch.zeros(cells[sl].shape[0], dtype=torch.bool, device=device)
        x = encode(cells[sl], macro[sl], nb[sl], player[sl], done, extra=net.cfg.extra_planes)
        if mod is None:
            outs.append(x.flatten(1).half())
        else:
            net(x)
            outs.append(store["a"].detach().flatten(1).half())
    if h is not None:
        h.remove()
    return torch.cat(outs)


def fit_probe(acts, labels, split, specs, device, hidden=0, epochs=10, bs=1024, lr=1e-3, wd=1e-4, seed=0):
    """Train one multi-head read-out on the train split and score it on the test split."""
    torch.manual_seed(seed)
    tr, te = torch.from_numpy(np.flatnonzero(split == 0)).to(device), torch.from_numpy(np.flatnonzero(split == 1)).to(device)
    mu = acts[tr].float().mean(0, keepdim=True)
    sd = acts[tr].float().std(0, keepdim=True) + 1e-3
    y = {}
    stats = {}
    for k, (kind, _) in specs.items():
        v = torch.from_numpy(labels[k]).to(device)
        if kind == "reg":
            v = v.float()
            m, s = v[tr].mean(), v[tr].std() + 1e-6
            stats[k] = (float(m), float(s))
            y[k] = (v - m) / s
        else:
            y[k] = v.long()
    heads = Heads(acts.shape[1], specs, hidden).to(device)
    opt = torch.optim.AdamW(heads.parameters(), lr=lr, weight_decay=wd)
    steps = epochs * ((len(tr) + bs - 1) // bs)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    g = torch.Generator(device=device).manual_seed(seed)
    for _ in range(epochs):
        perm = tr[torch.randperm(len(tr), device=device, generator=g)]
        for i in range(0, len(perm), bs):
            idx = perm[i : i + bs]
            x = (acts[idx].float() - mu) / sd
            loss = heads.loss(heads(x), {k: v[idx] for k, v in y.items()})
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
    heads.eval()
    res = {}
    with torch.no_grad():
        outs = {k: [] for k in specs}
        for i in range(0, len(te), 4096):
            idx = te[i : i + 4096]
            o = heads((acts[idx].float() - mu) / sd)
            for k in specs:
                outs[k].append(o[k])
        for k, (kind, _) in specs.items():
            o, t = torch.cat(outs[k]), y[k][te]
            if kind == "reg":
                m = ~torch.isnan(t)
                ss_res = ((o[m, 0] - t[m]) ** 2).sum()
                ss_tot = ((t[m] - t[m].mean()) ** 2).sum()
                res[k] = {"r2": float(1 - ss_res / ss_tot.clamp(min=1e-9)), "n": int(m.sum())}
            else:
                m = t >= 0
                acc = float((o.argmax(1)[m] == t[m]).float().mean()) if m.any() else float("nan")
                maj = float(torch.bincount(t[m]).max() / m.sum()) if m.any() else float("nan")
                res[k] = {"acc": acc, "majority": maj, "n": int(m.sum())}
    return res


@torch.no_grad()
def ownership_head_accuracy(net, cells, macro, nb, player, labels, split, device) -> float:
    te = np.flatnonzero(split == 1)
    correct, total = 0, 0
    for i in range(0, len(te), 2048):
        idx = torch.from_numpy(te[i : i + 2048]).to(device)
        done = torch.zeros(len(idx), dtype=torch.bool, device=device)
        _, _, o, _ = net(encode(cells[idx], macro[idx], nb[idx], player[idx], done, extra=net.cfg.extra_planes))
        pred = o.argmax(2).cpu().numpy()  # (n, 9) in the head's classes: 0 self / 1 neither / 2 opponent
        truth = np.stack([labels[f"final_own_{b}"][te[i : i + 2048]] for b in range(9)], 1)
        if net.cfg.own_classes == 4:  # 4-class heads: self 0 / opponent 1 / full 2 / open 3 -> 3-class
            pred = np.where(pred == 0, 0, np.where(pred == 1, 2, 1))
        correct += int((pred == truth).sum())
        total += pred.size
    return correct / total


def cmd_fit(a) -> None:
    device = torch.device(a.device)
    t0 = time.perf_counter()
    z = np.load(a.data)
    meta = json.loads(str(z["meta"]))
    labels = {k[6:]: z[k] for k in z.files if k.startswith("label_")}
    split = z["split"]
    specs = {k: LABELS[k] for k in labels if (not a.labels or k in a.labels.split(","))}
    t = lambda k: torch.from_numpy(z[k]).to(device)  # noqa: E731
    cells, macro, nb, player = t("cells"), t("macro"), t("next_board"), t("player")
    ckpts = sorted(glob.glob(os.path.join(a.run, "net_[0-9][0-9][0-9][0-9].pt")))
    if a.only:
        keep = {int(x) for x in a.only.split(",")}
        ckpts = [p for p in ckpts if int(os.path.basename(p)[4:8]) in keep]
    nets = [(int(os.path.basename(p)[4:8]), load_checkpoint(p, device).eval()) for p in ckpts]
    if a.control:
        torch.manual_seed(0)
        nets.insert(0, (0, ResNet(nets[0][1].cfg).to(device).eval()))  # iteration 0 = random initialisation, the control
    layers = ["input", "stem"] + [f"block{i + 1:02d}" for i in range(nets[0][1].cfg.blocks)]
    if a.layers:
        layers = [l for l in layers if l in a.layers.split(",")]
    out_path = a.out or os.path.join(a.run, "probes_mlp.json" if a.hidden else "probes.json")
    result = {"meta": {"data": a.data, "data_meta": {k: v for k, v in meta.items() if k != "labels"}, "run": a.run, "hidden": a.hidden, "epochs": a.epochs,
                       "layers": layers, "labels": {k: v[1] for k, v in specs.items()}, "kinds": {k: v[0] for k, v in specs.items()},
                       "n_train": int((split == 0).sum()), "n_test": int((split == 1).sum())}, "checkpoints": {}}
    print(f"{a.data}: {len(split)} positions ({result['meta']['n_train']} train / {result['meta']['n_test']} test), {len(specs)} labels; "
          f"{len(nets)} nets x {len(layers)} layers; probe hidden={a.hidden}", flush=True)
    for it, net in nets:
        rec = {"ownership_head_acc": ownership_head_accuracy(net, cells, macro, nb, player, labels, split, device), "layers": {}}
        for layer in layers:
            acts = layer_activations(net, cells, macro, nb, player, layer, device)
            rec["layers"][layer] = fit_probe(acts, labels, split, specs, device, hidden=a.hidden, epochs=a.epochs, seed=a.seed)
            del acts
            torch.cuda.empty_cache()
            head = rec["layers"][layer]
            show = [k for k in ("free_move", "threats_for", "count_margin", "final_own_4", "best_move_ply2", "exact_value") if k in head]
            print(f"  net_{it:04d} {layer:8s} " + "  ".join(f"{k} {head[k].get('acc', head[k].get('r2')):.3f}" for k in show) + f"  ({time.perf_counter() - t0:.0f}s)", flush=True)
        result["checkpoints"][str(it)] = rec
        with open(out_path, "w") as f:
            json.dump(result, f, indent=1)
    print(f"wrote {out_path}  [{time.perf_counter() - t0:.0f}s]")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--corpus", default="runs/deep8_c1_300")
    b.add_argument("--last", type=int, default=20)
    b.add_argument("--net", default="runs/deep10_c1_300/net_0300.pt", help="source of the search look-ahead labels")
    b.add_argument("--n_train", type=int, default=50000)
    b.add_argument("--n_test", type=int, default=10000)
    b.add_argument("--per_game", type=int, default=4)
    b.add_argument("--ply_hi", type=int, default=60)
    b.add_argument("--sims", type=int, default=256)
    b.add_argument("--max_exact", type=int, default=14)
    b.add_argument("--processes", type=int, default=12)
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--device", default="cuda:1")
    b.add_argument("--out", required=True)
    f = sub.add_parser("fit")
    f.add_argument("--data", required=True)
    f.add_argument("--run", default="runs/deep10_c1_300")
    f.add_argument("--only", default="", help="checkpoint iterations, e.g. 20,100,200,300 (default: all)")
    f.add_argument("--layers", default="", help="subset of layers, e.g. input,stem,block05,block10")
    f.add_argument("--labels", default="", help="subset of labels (default: all)")
    f.add_argument("--control", action="store_true", help="add a randomly initialised net of the same shape as iteration 0")
    f.add_argument("--hidden", type=int, default=0, help="0 = linear probe; >0 = one-hidden-layer probe of this width")
    f.add_argument("--epochs", type=int, default=10)
    f.add_argument("--seed", type=int, default=0)
    f.add_argument("--device", default="cuda:1")
    f.add_argument("--out", default="")
    a = ap.parse_args()
    {"build": cmd_build, "fit": cmd_fit}[a.cmd](a)


if __name__ == "__main__":
    main()
