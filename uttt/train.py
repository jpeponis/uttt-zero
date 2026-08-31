"""AlphaZero-style training loop: self-play -> replay buffer -> gradient steps -> evaluate -> repeat.

Usage:  python -m uttt.train --run runs/dev --iters 20 --games 1024 --sims 32
"""
from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass

import torch
import torch.nn.functional as F

from .arena import RandomPlayer, SearchPlayer, match, play_games
from .batch import apply_symmetry, encode
from .mcts import MCTSConfig
from .model import Evaluator, NetConfig, ResNet, UniformEvaluator
from .selfplay import ReplayBuffer, selfplay


@dataclass
class TrainConfig:
    run: str = "runs/dev"
    iters: int = 50
    games: int = 1024  # self-play games per iteration (all in one lock-step batch)
    sims: int = 32
    mode: str = "gumbel"
    blocks: int = 6
    filters: int = 64
    buffer: int = 2_000_000
    batch: int = 1024
    lr: float = 0.02
    momentum: float = 0.9
    wd: float = 1e-4
    epochs: float = 1.0  # passes over the NEW positions per iteration (sampled from whole buffer)
    min_steps: int = 50
    value_weight: float = 1.0
    own_weight: float = 0.5
    eval_every: int = 5
    eval_games: int = 256
    eval_sims: int = 64
    device: str = "cuda:0"
    seed: int = 0


def build(cfg: TrainConfig):
    net = ResNet(NetConfig(blocks=cfg.blocks, filters=cfg.filters))
    opt = torch.optim.SGD(net.parameters(), lr=cfg.lr, momentum=cfg.momentum, weight_decay=cfg.wd, nesterov=True)
    return net, opt


def train_steps(net, opt, scaler, buf: ReplayBuffer, cfg: TrainConfig, n_steps: int, device):
    net.train()
    tot = {"policy": 0.0, "value": 0.0, "own": 0.0, "acc_v": 0.0, "acc_p": 0.0}
    for _ in range(n_steps):
        b = buf.sample(cfg.batch, device)
        s = int(torch.randint(0, 8, (1,)))
        cells, macro, nb, pol = apply_symmetry(s, b["cells"], b["macro"], b["next_board"], b["policy"].float())
        from .batch import SYM_BOARD_INV
        own = b["ownership"][:, SYM_BOARD_INV[s].to(device)]
        obs = encode(cells, macro, nb, b["player"])
        with torch.autocast("cuda", dtype=torch.float16):
            p_logits, v_logits, o_logits, _ = net(obs)
        p_logits = p_logits.float()
        from .batch import INV_PERM
        p_logits = p_logits[:, INV_PERM.to(device)]  # engine order to match targets
        logp = torch.log_softmax(p_logits, dim=1)
        loss_p = -(pol * logp).sum(1).mean()
        v_target = (1 - b["value"].long()).clamp(0, 2)  # +1 -> 0 (win), 0 -> 1 (draw), -1 -> 2 (loss)
        loss_v = F.cross_entropy(v_logits.float(), v_target)
        o_target = (1 - own.long()).clamp(0, 2)
        loss_o = F.cross_entropy(o_logits.float().reshape(-1, 3), o_target.reshape(-1))
        loss = loss_p + cfg.value_weight * loss_v + cfg.own_weight * loss_o
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
        tot["policy"] += float(loss_p)
        tot["value"] += float(loss_v)
        tot["own"] += float(loss_o)
        tot["acc_v"] += float((v_logits.argmax(1) == v_target).float().mean())
        tot["acc_p"] += float((p_logits.argmax(1) == pol.argmax(1)).float().mean())
    net.eval()
    return {k: v / n_steps for k, v in tot.items()}


def evaluate(net, cfg: TrainConfig, device, prev_net=None):
    n = cfg.eval_games
    ev = Evaluator(net, device)
    ecfg = MCTSConfig(n_sims=cfg.eval_sims, mode="gumbel", gumbel_scale=0.0)
    out = {}
    # vs uniform-prior search (plain UCT with the same budget)
    uni = UniformEvaluator(device)
    r = match(lambda: SearchPlayer(ev, n, ecfg, device), lambda: SearchPlayer(uni, n, ecfg, device), n, device)
    out["vs_uct"] = r.score
    # raw policy (no search) vs random
    ecfg1 = MCTSConfig(n_sims=1, mode="gumbel", gumbel_scale=0.0)
    r = play_games(SearchPlayer(ev, n, ecfg1, device), RandomPlayer(device), n, device)
    out["policy_vs_random"] = r.score
    if prev_net is not None:
        pev = Evaluator(prev_net, device)
        r = match(lambda: SearchPlayer(ev, n, ecfg, device), lambda: SearchPlayer(pev, n, ecfg, device), n, device)
        out["vs_prev"] = r.score
    return out


def main(cfg: TrainConfig) -> None:
    torch.manual_seed(cfg.seed)
    torch.backends.cudnn.benchmark = True
    device = torch.device(cfg.device)
    os.makedirs(cfg.run, exist_ok=True)
    with open(os.path.join(cfg.run, "config.json"), "w") as f:
        json.dump(asdict(cfg), f, indent=2)
    net, opt = build(cfg)
    net.to(device)
    scaler = torch.amp.GradScaler("cuda")
    buf = ReplayBuffer(cfg.buffer)
    mcfg = MCTSConfig(n_sims=cfg.sims, mode=cfg.mode)
    log_path = os.path.join(cfg.run, "log.jsonl")
    start_iter = 0
    ckpt_path = os.path.join(cfg.run, "latest.pt")
    if os.path.exists(ckpt_path):
        ck = torch.load(ckpt_path, map_location=device, weights_only=False)
        net.load_state_dict(ck["net"])
        opt.load_state_dict(ck["opt"])
        buf.load_state_dict(ck["buffer"])
        start_iter = ck["iter"] + 1
        print(f"resumed from iteration {ck['iter']} (buffer {buf.size})")
    prev_state = None
    for it in range(start_iter, cfg.iters):
        t0 = time.perf_counter()
        ev = Evaluator(net, device)
        sp = selfplay(ev, cfg.games, mcfg, device)
        t_sp = time.perf_counter() - t0
        buf.add(sp)
        n_new = len(sp)
        n_steps = max(cfg.min_steps, int(cfg.epochs * n_new / cfg.batch))
        t1 = time.perf_counter()
        losses = train_steps(net, opt, scaler, buf, cfg, n_steps, device)
        t_tr = time.perf_counter() - t1
        w = sp.winners
        rec = {
            "iter": it, "positions": n_new, "buffer": buf.size, "steps": n_steps,
            "t_selfplay": round(t_sp, 1), "t_train": round(t_tr, 1),
            "games_per_s": round(cfg.games / t_sp, 1),
            "x_win": round(float((w == 1).float().mean()), 3), "o_win": round(float((w == -1).float().mean()), 3),
            "draw": round(float((w == 0).float().mean()), 3),
            "end_line": round(float((sp.reasons == 1).float().mean()), 3),
            "end_count": round(float((sp.reasons == 2).float().mean()), 3),
            "mean_len": round(float(sp.lengths.float().mean()), 1),
            "surprise": round(sp.surprise, 4),
            "first_move_top": int(torch.bincount(sp.first_moves, minlength=81).argmax()),
            **{f"loss_{k}": round(v, 4) for k, v in losses.items()},
        }
        if cfg.eval_every and (it + 1) % cfg.eval_every == 0:
            t2 = time.perf_counter()
            prev_net = None
            if prev_state is not None:
                prev_net = ResNet(NetConfig(blocks=cfg.blocks, filters=cfg.filters)).to(device)
                prev_net.load_state_dict(prev_state)
            rec.update({f"eval_{k}": round(v, 3) for k, v in evaluate(net, cfg, device, prev_net).items()})
            rec["t_eval"] = round(time.perf_counter() - t2, 1)
            prev_state = {k: v.clone() for k, v in net.state_dict().items()}
            torch.save({"net": net.state_dict(), "cfg": asdict(cfg)}, os.path.join(cfg.run, f"net_{it + 1:04d}.pt"))
        print(json.dumps(rec), flush=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        torch.save({"net": net.state_dict(), "opt": opt.state_dict(), "buffer": buf.state_dict(), "iter": it,
                    "cfg": asdict(cfg)}, ckpt_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k, v in asdict(TrainConfig()).items():
        ap.add_argument(f"--{k}", type=type(v), default=v)
    main(TrainConfig(**vars(ap.parse_args())))
