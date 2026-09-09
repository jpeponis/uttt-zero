"""Same probe on the TRAINED checkpoints (iteration 190, end of the constant-LR phase) and on
freshly initialised nets, with real teacher targets from runs/gdata_v1.npz.

Reports per layer group: ||w||, ||g||, and the relative SGD step ||g||/||w|| (multiply by lr for
the fractional weight change per step). For shared-bank layers it also reports the exact
gradient-sharing amplification  amp = (|g_bank|/|bank|) / (|g_exp|/|W_exp|).
"""
import sys
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\Users\John Peponis\Desktop\uttt-zero")
from uttt.batch import encode, INV_PERM
from uttt.model import NetConfig, build_net, load_checkpoint, MARGIN_BINS
from uttt import equivariant as eq

DEV = torch.device("cpu")
N = 256
z = np.load(r"C:\Users\John Peponis\Desktop\uttt-zero\runs\gdata_v1.npz")
rng = np.random.default_rng(0)
sel = np.sort(rng.choice(np.flatnonzero(z["split"] == 1), N, replace=False))
T = lambda k, dt: torch.from_numpy(np.asarray(z[k][sel], dtype=dt))
cells, macro, nb, player = T("cells", np.int8), T("macro", np.int8), T("next_board", np.int8), T("player", np.int8)
obs = encode(cells, macro, nb, player, extra=False, mask_closed=False)
pol = T("teacher_policy", np.float32)
pol = pol / pol.sum(1, keepdim=True)
tv = T("teacher_value", np.float32)
v_target = torch.where(tv > 0.33, 0, torch.where(tv < -0.33, 2, 1)).long()   # hard WDL, as train2 trains it
g2 = torch.Generator().manual_seed(1)
o_target = torch.randint(0, 3, (N, 9), generator=g2)
m_target = torch.randint(0, MARGIN_BINS, (N,), generator=g2)
inv = INV_PERM

_st = {}
def gconv_forward(self, x):
    W = self.expanded(); W.retain_grad(); _st[id(self)] = (W, None)
    return F.conv2d(x, W, padding=self.k // 2)
def tied_forward(self, x):
    W, b = self.expanded(); W.retain_grad(); _st[id(self)] = (W, b)
    return F.linear(x, W, b)
eq.GConv2d.forward = gconv_forward
eq.TiedLinear.forward = tied_forward

def nrm(t): return float(t.detach().norm())

def probe(net):
    net.train()
    p_logits, v_logits, o_logits, m_logits = net(obs)
    p_logits = p_logits.float()[:, inv]
    lp = -(pol * torch.log_softmax(p_logits, dim=1)).sum(1).mean()
    lv = F.cross_entropy(v_logits.float(), v_target)
    lo = F.cross_entropy(o_logits.float().reshape(-1, 3), o_target.reshape(-1))
    lm = F.cross_entropy(m_logits.float(), m_target)
    loss = lp + 1.0 * lv + 0.5 * lo + 0.25 * lm
    net.zero_grad(); loss.backward()
    rows = []
    for name, mod in net.named_modules():
        if isinstance(mod, (eq.GConv2d, eq.TiedLinear)):
            p = mod.bank; W = _st[id(mod)][0]
            rel_b = nrm(p.grad) / nrm(p); rel_e = nrm(W.grad) / nrm(W)
            rows.append([name, "bank", p.numel(), nrm(p), nrm(p.grad), rel_b, rel_b / rel_e, rel_e])
        elif isinstance(mod, (torch.nn.Conv2d, torch.nn.Linear)) and mod.weight.requires_grad and mod.weight.grad is not None:
            p = mod.weight; rows.append([name, "w", p.numel(), nrm(p), nrm(p.grad), nrm(p.grad) / nrm(p), 1.0, nrm(p.grad) / nrm(p)])
        elif isinstance(mod, torch.nn.BatchNorm2d) and mod.weight.grad is not None:
            p = mod.weight; rows.append([name, "bn", p.numel(), nrm(p), nrm(p.grad), nrm(p.grad) / nrm(p), 1.0, nrm(p.grad) / nrm(p)])
    return rows, (loss.item(), lp.item(), lv.item(), lo.item(), lm.item())

def agg(rows, pred):
    s = [r for r in rows if pred(r[0], r[1])]
    if not s: return None
    wn = float(np.sqrt(sum(r[3] ** 2 for r in s))); gn = float(np.sqrt(sum(r[4] ** 2 for r in s)))
    return (len(s), sum(r[2] for r in s), wn, gn, gn / wn, float(np.mean([r[6] for r in s])))

GROUPS = [("stem", lambda n, k: n.startswith("stem") and k != "bn"),
          ("trunk convs", lambda n, k: n.startswith("blocks") and k != "bn"),
          ("trunk BN gamma", lambda n, k: n.startswith("blocks") and k == "bn"),
          ("p_conv+v_conv", lambda n, k: (n.startswith("p_conv") or n.startswith("v_conv")) and k != "bn"),
          ("head fcs", lambda n, k: n.split(".")[0] in ("p_fc", "v_fc1", "v_fc2", "o_fc", "m_fc"))]

cases = []
torch.manual_seed(0); cases.append(("GCNN init", build_net(NetConfig(blocks=8, filters=128, gcnn=16))))
torch.manual_seed(0); cases.append(("ResNet init", build_net(NetConfig(blocks=8, filters=128))))
for tag, path in [("GCNN it190", r"runs\gcnn8_c1_300_e4\net_0190.pt"), ("ResNet it190", r"runs\deep8_c1_300_e4\net_0190.pt"),
                  ("GCNN it260", r"runs\gcnn8_c1_300_e4\net_0260.pt"), ("ResNet it260", r"runs\deep8_c1_300_e4\net_0260.pt")]:
    cases.append((tag, load_checkpoint(r"C:\Users\John Peponis\Desktop\uttt-zero\\" + path, DEV)))

out = {}
for tag, net in cases:
    rows, L = probe(net)
    out[tag] = rows
    print(f"{tag:14s} loss {L[0]:.4f}  p {L[1]:.4f}  v {L[2]:.4f}  o {L[3]:.4f}  m {L[4]:.4f}   params {sum(p.numel() for p in net.parameters()):,}")

print(f"\n{'group':16s} " + " ".join(f"{t:>28s}" for t in out) )
for gname, pred in GROUPS:
    line = f"{gname:16s} "
    for t in out:
        a = agg(out[t], pred)
        line += f"  |w|{a[2]:7.2f} |g|{a[4]:8.5f}/|w| " if a else " " * 29
    print(line)
print("\n(the numbers above are ||g||/||w|| = relative step per unit lr; multiply by lr 0.02)")

print("\nper-layer detail, trunk + heads, trained it190:")
for t in ("GCNN it190", "ResNet it190"):
    print(f"-- {t}")
    print(f"{'layer':16s} {'kind':5s} {'numel':>9s} {'|w|':>8s} {'|g|':>10s} {'|g|/|w|':>9s} {'amp':>6s} {'exp|g|/|w|':>10s}")
    for r in out[t]:
        if r[1] == "bn":
            continue
        print(f"{r[0]:16s} {r[1]:5s} {r[2]:9d} {r[3]:8.3f} {r[4]:10.4f} {r[5]:9.5f} {r[6]:6.2f} {r[7]:10.5f}")
