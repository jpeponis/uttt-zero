"""Raw policy at the empty board (a D4-fixed position) for both nets: is the G-CNN's mass exactly
tied inside D4 orbits, and what does that do to first_move_top_share?"""
import sys
import numpy as np, torch
sys.path.insert(0, r"C:\Users\John Peponis\Desktop\uttt-zero")
from uttt.batch import BatchUTTT
from uttt.model import load_checkpoint, Evaluator
from uttt.equivariant import GRID

orb = {}
key = np.full(81, 10**9, dtype=np.int64)
for s in range(8):
    key = np.minimum(key, GRID[s])
for c in range(81):
    orb.setdefault(int(key[c]), []).append(c)

g = BatchUTTT(1, "cpu")
for tag, p in [("GCNN 180", r"runs\gcnn8_c1_300_e4\net_0180.pt"), ("GCNN 190", r"runs\gcnn8_c1_300_e4\net_0190.pt"),
               ("GCNN 200", r"runs\gcnn8_c1_300_e4\net_0200.pt"), ("GCNN 260", r"runs\gcnn8_c1_300_e4\net_0260.pt"),
               ("RN 190", r"runs\deep8_c1_300_e4\net_0190.pt"), ("RN 260", r"runs\deep8_c1_300_e4\net_0260.pt")]:
    net = load_checkpoint(r"C:\Users\John Peponis\Desktop\uttt-zero\\" + p, "cpu")
    ev = Evaluator(net, "cpu", amp=False)
    probs, val = ev(*g.state_tuple())
    pr = probs[0].numpy()
    top = np.argsort(-pr)[:10]
    # centre-of-centre cell in ENGINE order is board 4 cell 4 -> index 4*9+4 = 40
    grp = {}
    for o, cs in orb.items():
        grp[o] = (len(cs), float(pr[cs].sum()), float(pr[cs].std()))
    best = sorted(grp.values(), key=lambda t: -t[1])[:4]
    print(f"{tag:9s} value {float(val[0]):+.3f}  p(cell40)={pr[40]:.4f}  top10 cells {list(top)}")
    print(f"          top10 p {np.round(pr[top],4)}")
    print(f"          biggest orbits (size, mass, within-orbit std): " + "  ".join(f"({a},{b:.3f},{c:.2e})" for a, b, c in best))
