"""Opening book (PLAN5 §4 C1): the 15 first-move orbits and their replies to a chosen depth, evaluated by deep
search with the symmetry-averaged evaluator, expanding the top-k replies (by root visits) of every node.

    .venv/Scripts/python.exe tools/book.py --net runs/deep10_c1_300/net_0300.pt --depth 4 --top 3 --sims 16384 --device cuda:0 --out runs/book_deep10.json
    .venv/Scripts/python.exe tools/book.py --net runs/deep8_c1_300/net_0300.pt ... --out runs/book_deep8.json --compare runs/book_deep10.json

Every node is a move sequence in canonical D4 form (uttt.openings.canonical), so transpositions by symmetry are
merged. Per node: the search value for X (search-relative, not game-theoretic), the full root visit-share and Q
arrays, and the children — the top-k *reply orbits* (replies grouped under the symmetries that fix the node, each
with its representative, members, summed share, visit-weighted Q, child key and the transform onto the child's
canonical frame). Lines are printed in one frame: principal_line() composes the stored transforms, so every
displayed prefix replays legally and canonicalises to the node it came from (PLAN6 E1; the earlier version listed
one orbit several times and mixed frames between nodes). --paired attaches, per first-move orbit, X's score and the
draw share from a paired-suite match file whose openings start with that move. Writes JSON and a Markdown table.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.batch import BatchUTTT  # noqa: E402
from uttt.infer import FusedEvaluator  # noqa: E402
from uttt.model import load_checkpoint  # noqa: E402
from uttt.game import UTTT  # noqa: E402
from uttt.openings import canonical, compose, inverse, orbit_representatives, reply_orbits, transform_move  # noqa: E402
from uttt.search import BatchedSearch, SearchConfig  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402


def mv(m: int) -> str:
    return f"{m}(b{m // 9}c{m % 9})"


@torch.no_grad()
def evaluate_level(ev, seqs: list[list[int]], sims: int, device, batch: int):
    """For sequences of equal length: value for X, root visit shares (n, 81), root Q from the mover's view (n, 81),
    legal replies (n, 81)."""
    vals, shares, qs, legals = [], [], [], []
    for i in range(0, len(seqs), batch):
        chunk = seqs[i : i + batch]
        n = len(chunk)
        g = BatchUTTT(n, device)
        for t in range(len(chunk[0])):
            g.step(torch.tensor([s[t] for s in chunk], device=device))
        cfg = SearchConfig(n_sims=sims, mode="puct", c_puct=1.25, root_prior_floor=0.0, gumbel_scale=0.0, m_considered=81,
                           cuda_graph=device.type == "cuda", depth_cap=40)
        s = BatchedSearch(ev, n, cfg, device)
        r = s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False)
        sign = torch.where(g.player == 1, 1.0, -1.0)
        vals.append((r.root_value * sign).cpu().numpy())
        N0 = s.N[:, 0].float()
        shares.append((N0 / N0.sum(1, keepdim=True).clamp(min=1)).cpu().numpy())
        qs.append((s.W[:, 0] / s.N[:, 0].clamp(min=1)).cpu().numpy())
        legals.append(g.legal_mask().cpu().numpy())
        del s
        torch.cuda.empty_cache() if device.type == "cuda" else None
    return np.concatenate(vals), np.concatenate(shares), np.concatenate(qs), np.concatenate(legals)


def build(ev, depth: int, top: int, sims: int, device, batch: int, log=print) -> dict:
    nodes = {}
    frontier = [[m] for m in orbit_representatives()]
    t0 = time.perf_counter()
    for d in range(1, depth + 1):
        vals, shares, qs, legals = evaluate_level(ev, frontier, sims, device, batch)
        nxt = {}
        for seq, v, sh, q, lg in zip(frontier, vals, shares, qs, legals):
            kids = [o for o in reply_orbits(seq, lg, sh, q) if o["share"] > 0][:top]
            for o in kids:
                if d < depth:
                    nxt.setdefault(o["child"], [int(m) for m in o["child"].split()])
            nodes[" ".join(map(str, seq))] = {"seq": seq, "depth": d, "value_x": float(v), "moves": kids,
                                              "root_share": [round(float(x), 5) for x in sh], "root_q": [round(float(x), 4) for x in q]}
        log(f"depth {d}: {len(frontier)} nodes evaluated at {sims} sims ({time.perf_counter() - t0:.0f}s)")
        frontier = [nxt[k] for k in sorted(nxt)]
    return nodes


def principal_line(nodes: dict, key: str, max_len: int, with_keys: bool = False) -> list:
    """Follow the most-visited reply orbit from node to node, printing every move in the frame of the node `key`:
    [(move, value_x after it), ...] (with_keys: [(move, value_x, key of the node the move leads to), ...]).

    Each node's replies are stored in that node's own canonical frame; the transform on each edge maps the parent's
    frame onto the child's, so the frame of node k relative to the start is G = g_k o ... o g_1 and a move stored at
    node k reads G^-1(move) at the start. With canonical representatives (uttt.openings.reply_orbits) every edge
    transform is the identity and the child key extends the parent's literally, so this reduces to reading the moves
    off; the composition is kept so the line stays honest under any other choice of representative, and audit()
    checks the stored transforms. The pre-PLAN6 book concatenated moves from different frames, which made one
    displayed line per book illegal (REVIEW-astra §4.1)."""
    out, G = [], 0
    while key in nodes and len(out) < max_len:
        n = nodes[key]
        if not n["moves"]:
            break
        best = n["moves"][0]
        child = best["child"]
        move = transform_move(inverse(G), best["move"])
        value = nodes[child]["value_x"] if child in nodes else float("nan")
        out.append((move, value, child) if with_keys else (move, value))
        G = compose(best["g"], G)
        key = child
    return out


def audit(nodes: dict) -> dict:
    """Consistency of a book (the regression test for PLAN6 E1). Every stored orbit must map onto its child by the
    stored transform with every member legal; a node's children must be distinct orbits; every principal line from
    every first-move node must replay legally with every prefix canonicalising to the node it passes through."""
    bad = {"illegal_member": [], "transform_mismatch": [], "duplicate_child": [], "illegal_line": [], "frame_mismatch": []}
    for k, n in nodes.items():
        g0 = UTTT()
        for m in n["seq"]:
            g0.play(m)
        legal = set(int(x) for x in g0.legal_moves())
        if len({o["child"] for o in n["moves"]}) < len(n["moves"]):
            bad["duplicate_child"].append(k)
        for o in n["moves"]:
            if any(m not in legal for m in o["members"]) or o["move"] not in o["members"]:
                bad["illegal_member"].append((k, o["move"]))
            image = [transform_move(o["g"], m) for m in n["seq"] + [o["move"]]]
            if image != [int(x) for x in o["child"].split()] or any(canonical(n["seq"] + [m]) != tuple(image) for m in o["members"]):
                bad["transform_mismatch"].append((k, o["move"]))
    for k, n in nodes.items():
        if n["depth"] != 1:
            continue
        line = principal_line(nodes, k, 99, with_keys=True)
        g0, seq = UTTT(), list(n["seq"])
        for m in seq:
            g0.play(m)
        for m, _, child in line:
            if g0.done or m not in {int(x) for x in g0.legal_moves()}:
                bad["illegal_line"].append((k, seq + [m]))
                break
            g0.play(m)
            seq.append(m)
            if " ".join(map(str, canonical(seq))) != child:
                bad["frame_mismatch"].append((k, seq, child))
                break
    return {"nodes": len(nodes), "lines": sum(n["depth"] == 1 for n in nodes.values()), **{k: v for k, v in bad.items()},
            "clean": not any(bad.values())}


def paired_stats(path: str) -> dict:
    """Per first-move orbit representative: X's mean score and draw share over the paired games that start with it."""
    d = json.load(open(path))
    acc = {}
    for o in d["openings"]:
        if not o["moves"]:
            continue
        rep = canonical(o["moves"][:1])[0]
        x_scores = [o["a_as_x"], 1.0 - o["a_as_o"]]  # X's score in the two games of the pair
        acc.setdefault(rep, []).extend(x_scores)
    return {rep: {"x_score": float(np.mean(v)), "draw_share": float(np.mean(np.isclose(v, 0.5))), "games": len(v)} for rep, v in acc.items()}


def markdown(nodes: dict, meta: dict, paired: dict | None, other: dict | None) -> str:
    lines = [f"# Opening book: {meta['net']} at {meta['sims']} sims, depth {meta['depth']}, top-{meta['top']} replies per node",
             "", "Values are the deep-search value for X after the moves (search-relative: what this net + search prefers, "
             "not game-theoretic). Moves are `m(b<board>c<cell>)`, m = 9*board + cell. The line follows the most-visited move.", ""]
    hdr = "| first move | value X | best reply orbit (O) | share | X's next | line to depth " + str(meta["depth"]) + " |"
    if paired:
        hdr += " paired X score | draw share |"
    if other:
        hdr += f" {other['meta']['net_name']} value / best reply |"
    lines[2] += (" A reply is one *orbit* (replies equivalent under the symmetries that fix the position), shown by its "
                 "canonical (smallest-index) member with the orbit size in brackets when > 1; share is the orbit's summed "
                 "visit share; every line is in the frame of its first move.")
    lines += [hdr, "|" + "---|" * (hdr.count("|") - 1)]
    firsts = sorted((k for k, n in nodes.items() if n["depth"] == 1), key=lambda k: -nodes[k]["value_x"])
    for k in firsts:
        n = nodes[k]
        m = n["seq"][0]
        reply = n["moves"][0] if n["moves"] else None
        line = principal_line(nodes, k, meta["depth"] - 1)
        nxt = line[1][0] if len(line) > 1 else None
        size = f" [{len(reply['members'])}]" if reply and len(reply["members"]) > 1 else ""
        row = (f"| {mv(m)} | {n['value_x']:+.3f} | {mv(reply['move']) + size if reply else '-'} | {reply['share']:.2f} | "
               f"{mv(nxt) if nxt is not None else '-'} | " + " ".join(f"{mv(a)}({v:+.2f})" for a, v in line) + " |")
        if paired:
            p = paired.get(m)
            row += f" {100 * p['x_score']:.0f} % ({p['games']}) | {100 * p['draw_share']:.0f} % |" if p else " - | - |"
        if other:
            on = other["nodes"].get(k)
            if on:
                orep = on["moves"][0] if on["moves"] else None
                agree = "=" if reply and orep and orep["child"] == reply["child"] else "!="
                row += f" {on['value_x']:+.3f} / {mv(orep['move']) if orep else '-'} {agree} |"
            else:
                row += " - |"
        lines.append(row)
    if other:
        common = [k for k in nodes if k in other["nodes"] and nodes[k]["moves"] and other["nodes"][k]["moves"]]
        same = {k: nodes[k]["moves"][0]["child"] == other["nodes"][k]["moves"][0]["child"] for k in common}  # same reply orbit
        agree = np.mean(list(same.values())) if common else float("nan")
        dv = np.mean([abs(nodes[k]["value_x"] - other["nodes"][k]["value_x"]) for k in common]) if common else float("nan")
        by_depth = {d: np.mean([same[k] for k in common if nodes[k]["depth"] == d])
                    for d in range(1, meta["depth"] + 1) if any(nodes[k]["depth"] == d for k in common)}
        lines += ["", f"Agreement with {other['meta']['net']} on the most-visited reply orbit: {agree:.2f} over {len(common)} shared nodes "
                  f"(by depth: " + ", ".join(f"{d}: {v:.2f}" for d, v in by_depth.items()) + f"); mean |value difference| {dv:.3f}."]
    lines += ["", f"Nodes: {len(nodes)}; built {meta['built']} in {meta['seconds']:.0f} s."]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default="runs/deep10_c1_300/net_0300.pt")
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--sims", type=int, default=16384)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--no_sym", action="store_true")
    ap.add_argument("--paired", default="", help="paired-suite match JSON to attach X score / draw share per first-move orbit")
    ap.add_argument("--compare", default="", help="another book JSON: per-node agreement on the best move")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = torch.device(a.device)
    t0 = time.perf_counter()
    fe = FusedEvaluator(load_checkpoint(a.net, device), device)
    ev = fe if a.no_sym else SymmetryAveragedEvaluator(fe)
    nodes = build(ev, a.depth, a.top, a.sims, device, a.batch)
    chk = audit(nodes)
    print(f"audit: {chk}")
    assert chk["clean"], "book failed its consistency audit"
    meta = {"net": a.net, "net_name": os.path.basename(os.path.dirname(a.net)), "depth": a.depth, "top": a.top, "sims": a.sims,
            "symmetry_averaged": not a.no_sym, "built": time.strftime("%Y-%m-%d %H:%M"), "seconds": time.perf_counter() - t0}
    with open(a.out, "w") as f:
        json.dump({"meta": meta, "nodes": nodes}, f, indent=1)
    paired = paired_stats(a.paired) if a.paired else None
    other = json.load(open(a.compare)) if a.compare else None
    md = markdown(nodes, meta, paired, other)
    md_path = os.path.splitext(a.out)[0] + ".md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md + "\n")
    print(md)
    print(f"\nwrote {a.out} and {md_path}  [{time.perf_counter() - t0:.0f}s]")


if __name__ == "__main__":
    main()
