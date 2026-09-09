"""Top Hessian eigenvalue (power iteration on Hessian-vector products) of the SAME training loss
for the trained G-CNN and ResNet at iteration 190, in the parameter space SGD actually steps in.

SGD is stable only while lr < 2/lambda_max; if weight sharing multiplies the curvature seen by a
shared bank, this is where it shows.  BN in eval mode so the Hessian is of a fixed function of the
weights (train-mode batch statistics make the loss a function of the batch's own statistics and
the HVP then mixes in the batch-stat path; both nets are treated identically either way).
"""
import sys, time
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\Users\John Peponis\Desktop\uttt-zero")
from uttt.batch import encode, INV_PERM
from uttt.model import load_checkpoint, MARGIN_BINS

DEV = torch.device("cpu")
N = 128
z = np.load(r"C:\Users\John Peponis\Desktop\uttt-zero\runs\gdata_v1.npz")
rng = np.random.default_rng(0)
sel = np.sort(rng.choice(np.flatnonzero(z["split"] == 1), N, replace=False))
T = lambda k, dt: torch.from_numpy(np.asarray(z[k][sel], dtype=dt))
obs = encode(T("cells", np.int8), T("macro", np.int8), T("next_board", np.int8), T("player", np.int8))
pol = T("teacher_policy", np.float32); pol = pol / pol.sum(1, keepdim=True)
tv = T("teacher_value", np.float32)
v_target = torch.where(tv > 0.33, 0, torch.where(tv < -0.33, 2, 1)).long()
g2 = torch.Generator().manual_seed(1)
o_target = torch.randint(0, 3, (N, 9), generator=g2)
m_target = torch.randint(0, MARGIN_BINS, (N,), generator=g2)
inv = INV_PERM

def loss_of(net):
    p, v, o, m = net(obs)
    p = p.float()[:, inv]
    return (-(pol * torch.log_softmax(p, 1)).sum(1).mean() + F.cross_entropy(v.float(), v_target)
            + 0.5 * F.cross_entropy(o.float().reshape(-1, 3), o_target.reshape(-1))
            + 0.25 * F.cross_entropy(m.float(), m_target))

def lam_max(net, iters=15, seed=0):
    net.eval()   # fixed BN statistics
    ps = [p for p in net.parameters() if p.requires_grad]
    g = torch.autograd.grad(loss_of(net), ps, create_graph=True)
    torch.manual_seed(seed)
    v = [torch.randn_like(p) for p in ps]
    nv = torch.sqrt(sum((x ** 2).sum() for x in v)); v = [x / nv for x in v]
    lam = 0.0
    hist = []
    for k in range(iters):
        Hv = torch.autograd.grad(g, ps, grad_outputs=v, retain_graph=True)
        lam = float(sum((a * b).sum() for a, b in zip(Hv, v)))
        nv = torch.sqrt(sum((x ** 2).sum() for x in Hv))
        v = [x / nv for x in Hv]
        hist.append(lam)
    return lam, hist

for tag, path in [("GCNN it190", r"runs\gcnn8_c1_300_e4\net_0190.pt"), ("ResNet it190", r"runs\deep8_c1_300_e4\net_0190.pt"),
                  ("GCNN it260", r"runs\gcnn8_c1_300_e4\net_0260.pt"), ("ResNet it260", r"runs\deep8_c1_300_e4\net_0260.pt")]:
    t0 = time.perf_counter()
    net = load_checkpoint(r"C:\Users\John Peponis\Desktop\uttt-zero\\" + path, DEV)
    lam, hist = lam_max(net)
    print(f"{tag:14s} lambda_max ~ {lam:9.2f}   2/lambda = {2/max(lam,1e-9):.5f}   lr0.02 / (2/lambda) = {0.02*lam/2:6.3f}"
          f"   [{time.perf_counter()-t0:.0f}s]  power-iters: " + " ".join(f"{h:.1f}" for h in hist[-5:]))
