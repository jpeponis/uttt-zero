"""CPU gradient-scale probe: G-CNN (gcnn=16) vs plain ResNet 8x128 at the run's config.

One forward/backward on the same batch of real self-play positions with the same loss
(train2.train_steps recipe), then per-layer ||grad|| / ||param||  -- the relative SGD step
lr * ||g||/||w|| is what "effective learning rate" means for a layer.

For GConv2d/TiedLinear it also reports the gradient-sharing amplification:
    amp = (||g_bank|| / ||bank||) / (||g_expanded|| / ||W_expanded||)
i.e. how much hotter training the shared bank is than training the expanded weight directly.
Since each bank entry is tiled into exactly R copies, ||W_exp|| = sqrt(R)*||bank||, so
amp = sqrt(R) * ||g_bank|| / ||g_exp||, in [0, R]; R = 8 for GConv2d, up to 8 for TiedLinear.
"""
import os, sys, json
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\Users\John Peponis\Desktop\uttt-zero")
from uttt.batch import BatchUTTT, encode, legal_mask, INV_PERM, step_state
from uttt.model import NetConfig, build_net, MARGIN_BINS
from uttt import equivariant as eq

torch.manual_seed(0)
DEV = torch.device("cpu")
N = 64

# ---- real positions: replay a slice of the run's own saved games to a mid-game ply ----
z = np.load(r"C:\Users\John Peponis\Desktop\uttt-zero\runs\gcnn8_c1_300_e4\games\games_0100.npz")
moves, lengths, winners = z["moves"], z["lengths"], z["winners"]
keep = np.flatnonzero(lengths >= 30)[:N]
g = BatchUTTT(N, DEV)
mv = torch.from_numpy(moves[keep].astype(np.int64))
PLY = 20
for t in range(PLY):
    g.step(mv[:, t])
obs = encode(g.cells, g.macro, g.next_board, g.player, extra=False, mask_closed=False)
legal = legal_mask(g.cells, g.macro, g.next_board, g.done)  # engine order
print("batch:", obs.shape, "legal moves/pos:", float(legal.float().sum(1).mean()))

# ---- targets: peaked policy on a random legal move (search-like), real outcome for value ----
gen = torch.Generator().manual_seed(1)
pol = legal.float() * torch.rand(N, 81, generator=gen)
pol = pol / pol.sum(1, keepdim=True)
pol = 0.6 * F.one_hot(pol.argmax(1), 81).float() + 0.4 * pol            # peaked, entropy ~ the run's targets
win = torch.from_numpy(winners[keep].astype(np.int64))
v_target = (1 - (win * g.player.long()).clamp(-1, 1)).clamp(0, 2)
o_target = torch.randint(0, 3, (N, 9), generator=gen)
m_target = torch.randint(0, MARGIN_BINS, (N,), generator=gen)
inv = INV_PERM

def loss_of(net):
    p_logits, v_logits, o_logits, m_logits = net(obs)
    p_logits = p_logits.float()[:, inv]
    logp = torch.log_softmax(p_logits, dim=1)
    lp = -(pol * logp).sum(1).mean()
    lv = F.cross_entropy(v_logits.float(), v_target)
    lo = F.cross_entropy(o_logits.float().reshape(-1, 3), o_target.reshape(-1))
    lm = F.cross_entropy(m_logits.float(), m_target)
    return lp + 1.0 * lv + 0.5 * lo + 0.25 * lm, (lp, lv, lo, lm)

# ---- monkeypatch (script-local) so the expanded weights keep their gradients ----
_expanded_store = {}
def gconv_forward(self, x):
    W = self.expanded(); W.retain_grad(); _expanded_store[id(self)] = W
    return F.conv2d(x, W, padding=self.k // 2)
def tied_forward(self, x):
    W, b = self.expanded(); W.retain_grad(); _expanded_store[id(self)] = W
    return F.linear(x, W, b)
eq.GConv2d.forward = gconv_forward
eq.TiedLinear.forward = tied_forward

def nrm(t): return float(t.norm())

def report(tag, cfg):
    torch.manual_seed(0)
    net = build_net(cfg).to(DEV)
    net.train()
    loss, parts = loss_of(net)
    net.zero_grad()
    loss.backward()
    n_par = sum(p.numel() for p in net.parameters())
    print(f"\n===== {tag}: params {n_par:,}  loss {loss.item():.4f} "
          f"(p {parts[0].item():.4f} v {parts[1].item():.4f} o {parts[2].item():.4f} m {parts[3].item():.4f})")
    rows = []
    for name, mod in net.named_modules():
        if isinstance(mod, (eq.GConv2d, eq.TiedLinear)):
            p = mod.bank
            W = _expanded_store.get(id(mod))
            R = W.numel() / p.numel()
            amp = float(np.sqrt(R)) * nrm(p.grad) / max(nrm(W.grad), 1e-30)
            rows.append((name, "bank", p.numel(), nrm(p), nrm(p.grad), nrm(p.grad) / nrm(p), R, amp,
                         nrm(W.grad) / nrm(W)))
        elif isinstance(mod, (torch.nn.Conv2d, torch.nn.Linear)) and mod.weight.requires_grad and mod.weight.grad is not None:
            p = mod.weight
            rows.append((name, "w", p.numel(), nrm(p), nrm(p.grad), nrm(p.grad) / nrm(p), 1.0, 1.0,
                         nrm(p.grad) / nrm(p)))
        elif isinstance(mod, torch.nn.BatchNorm2d) and mod.weight.grad is not None:
            p = mod.weight
            rows.append((name, "bn", p.numel(), nrm(p), nrm(p.grad), nrm(p.grad) / nrm(p), 1.0, 1.0,
                         nrm(p.grad) / nrm(p)))
    print(f"{'layer':38s} {'kind':5s} {'numel':>9s} {'|w|':>9s} {'|g|':>10s} {'|g|/|w|':>10s} {'R':>4s} {'amp':>6s} {'exp |g|/|w|':>11s}")
    for r in rows:
        print(f"{r[0]:38s} {r[1]:5s} {r[2]:9d} {r[3]:9.3f} {r[4]:10.4f} {r[5]:10.5f} {r[6]:4.0f} {r[7]:6.2f} {r[8]:11.5f}")
    return rows

def groups(rows):
    def agg(pred):
        sel = [r for r in rows if pred(r[0], r[1])]
        if not sel: return None
        gn = float(np.sqrt(sum(r[4] ** 2 for r in sel)))
        wn = float(np.sqrt(sum(r[3] ** 2 for r in sel)))
        return len(sel), sum(r[2] for r in sel), wn, gn, gn / wn
    out = {}
    out["stem"] = agg(lambda n, k: n.startswith("stem") and k != "bn")
    out["trunk convs"] = agg(lambda n, k: n.startswith("blocks") and k != "bn")
    out["trunk BN"] = agg(lambda n, k: n.startswith("blocks") and k == "bn")
    out["head convs (p/v_conv)"] = agg(lambda n, k: (n.startswith("p_conv") or n.startswith("v_conv")) and k != "bn")
    out["head fcs"] = agg(lambda n, k: n.endswith("_fc") or n.endswith("_fc1") or n.endswith("_fc2"))
    return out

rg = report("GResNet gcnn=16 (8 blocks, width 128)", NetConfig(blocks=8, filters=128, gcnn=16))
rr = report("ResNet 8x128", NetConfig(blocks=8, filters=128))
gg, gr = groups(rg), groups(rr)
print(f"\n{'group':24s} {'GCNN n':>7s} {'GCNN numel':>11s} {'GCNN |g|/|w|':>13s} | {'RN n':>5s} {'RN numel':>10s} {'RN |g|/|w|':>11s} | {'ratio':>6s}")
for k in gg:
    a, b = gg[k], gr[k]
    if a is None or b is None: continue
    print(f"{k:24s} {a[0]:7d} {a[1]:11d} {a[4]:13.5f} | {b[0]:5d} {b[1]:10d} {b[4]:11.5f} | {a[4]/b[4]:6.2f}")
