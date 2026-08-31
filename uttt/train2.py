"""v2 training loop: continuous self-play (uttt.selfplay_cont) + sync-free search (uttt.search)
+ fused inference (uttt.infer) + GPU replay buffer with duplicate down-weighting + game persistence
+ margin head + LR schedule + cheap fixed-anchor evaluation.

    python -m uttt.train2 --run runs/v2a --iters 150 --games 4096 --steps 64 --sims 32

Each iteration advances all `games` parallel games by `steps` moves (games × steps positions),
trains ~`epochs` passes over that many positions sampled from the buffer, and logs one JSON line.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass

import numpy as np
import torch
import torch.nn.functional as F

from .arena import play_games
from .batch import INV_PERM, SYM_BOARD, SYM_BOARD_INV, SYM_CELL_INV, BatchUTTT, encode
from .endgame import EndgameSet
from .endgame import evaluate as endgame_evaluate
from .exact import ExactLabeler
from .infer import FusedEvaluator
from .model import MARGIN_BINS, NetConfig, ResNet, load_checkpoint
from .openings import Suite, play_paired, summarize
from .search import BatchedSearch, SearchConfig
from .selfplay_cont import ContinuousSelfPlay, GPUReplayBuffer


@dataclass
class TrainConfig:
    run: str = "runs/v2"
    iters: int = 150
    games: int = 4096  # parallel games
    steps: int = 64  # moves per game per iteration -> games*steps positions per iteration
    sims: int = 32
    mode: str = "gumbel"
    sample_moves: int = 8  # plies sampled from the improved policy (opening diversity)
    sample_uniform: float = 0.0  # exploration floor mixed into the sampling distribution during those plies
    temperature: float = 1.0
    sims_schedule: str = ""  # e.g. "60:64,110:96": simulations per move from the given iteration on
    root_prior_floor: float = 0.03
    c_scale: float = 0.1
    cuda_graph: int = 0  # 1: replay each simulation as a CUDA graph (depth_cap bounds the descent)
    depth_cap: int = 12
    blocks: int = 6
    filters: int = 64
    n_planes: int = 7  # 9: + first-player and won-board-count-difference input planes (new anchors needed)
    own_classes: int = 3  # 4: self / opponent / drawn-full / open-at-end ownership target
    buffer: int = 2_000_000
    dedup_alpha: float = 0.5  # sampling weight = count^-alpha over identical positions
    dedup_alpha_early: float = 0.0  # > 0: alpha used for plies < 8 (e.g. 1.0 = strictly uniform over distinct openings)
    dedup_sym: int = 0  # 1: count D4-symmetric positions as duplicates
    batch: int = 1024
    lr: float = 0.02
    lr_drops: str = ""  # e.g. "80,120": multiply lr by 0.1 at these iterations
    warmup_steps: int = 200
    momentum: float = 0.9
    wd: float = 1e-4
    epochs: float = 1.0
    min_steps: int = 50
    value_weight: float = 1.0
    own_weight: float = 0.5
    margin_weight: float = 0.25
    eval_every: int = 10
    eval_games: int = 128  # per side; only used when suite == "" (unpaired random 2-ply openings)
    eval_sims: int = 64
    eval_graph: int = 1  # 0: eager eval searches (slower; fallback if graph-mode eval ever faults again)
    anchors: str = "runs/dev1/net_0200.pt"  # comma-separated checkpoints used as fixed opponents
    suite: str = "suites/openings_v1.npz"  # fixed opening suite, every opening played with both colours (tools/openings.py)
    eval_openings: int = 100  # at most this many openings per sub-suite of the suite (0 = the whole suite)
    endgame_set: str = "suites/endgame_v1.npz"  # frozen exact-label endgame set scored at every evaluation ("" = off)
    exact_max_empty: int = 0  # > 0: solve positions with <= this many empties in open boards and train on exact labels
    exact_per_iter: int = 8192  # at most this many positions solved per iteration
    exact_weight: float = 2.0  # sampling weight multiplier for exactly labelled rows
    exact_policy: int = 1  # 1: also replace the policy target by uniform-over-optimal-moves
    exact_processes: int = 8
    save_buffer_every: int = 10
    device: str = "cuda:0"
    seed: int = 0


class SearchPlayer2:
    def __init__(self, evaluator, n, cfg: SearchConfig, device) -> None:
        self.s = BatchedSearch(evaluator, n, cfg, device)

    def act(self, g: BatchUTTT) -> torch.Tensor:
        return self.s.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False).action


load_net = load_checkpoint  # anchors: the net a checkpoint describes (blocks, filters, planes, ownership classes)


def _git_rev() -> str | None:
    try:
        import subprocess
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                           cwd=os.path.dirname(os.path.abspath(__file__)), timeout=5)
        return r.stdout.strip() or None
    except Exception:
        return None

# ownership target class by stored value (index = own + 1 for own in {-1 opponent, 0 open, 1 self, 2 full-drawn})
OWN_CLASS = {3: (2, 1, 0, 1), 4: (1, 3, 0, 2)}


def symmetrise(b: dict, device):
    """Apply an independent random D4 symmetry to every sample of a sampled batch."""
    n = b["cells"].shape[0]
    s = torch.randint(0, 8, (n,), device=device)
    cp = SYM_CELL_INV.to(device)[s]  # (n, 81)
    bp = SYM_BOARD_INV.to(device)[s]  # (n, 9)
    cells = b["cells"].gather(1, cp)
    macro = b["macro"].gather(1, bp)
    policy = b["policy"].float().gather(1, cp)
    own = b["ownership"].gather(1, bp)
    nb = b["next_board"].long()
    nb2 = torch.where(nb >= 0, SYM_BOARD.to(device)[s, nb.clamp(min=0)], nb).to(torch.int8)
    return cells, macro, nb2, policy, own


def train_steps(net, opt, scaler, buf: GPUReplayBuffer, cfg: TrainConfig, n_steps: int, device, lr_fn):
    net.train()
    inv = INV_PERM.to(device)
    own_map = torch.tensor(OWN_CLASS[cfg.own_classes], device=device)
    tot = torch.zeros(6, device=device)
    for _ in range(n_steps):
        for g in opt.param_groups:
            g["lr"] = lr_fn()
        b = buf.sample(cfg.batch)
        cells, macro, nb, pol, own = symmetrise(b, device)
        obs = encode(cells, macro, nb, b["player"], extra=cfg.n_planes > 7)
        with torch.autocast("cuda", dtype=torch.float16):
            p_logits, v_logits, o_logits, m_logits = net(obs)
        p_logits = p_logits.float()[:, inv]
        logp = torch.log_softmax(p_logits, dim=1)
        loss_p = -(pol * logp).sum(1).mean()
        v_target = (1 - b["value"].long()).clamp(0, 2)
        loss_v = F.cross_entropy(v_logits.float(), v_target)
        o_target = own_map[own.long() + 1]
        loss_o = F.cross_entropy(o_logits.float().reshape(-1, cfg.own_classes), o_target.reshape(-1))
        m_target = (b["margin"].long() + MARGIN_BINS // 2).clamp(0, MARGIN_BINS - 1)
        loss_m = F.cross_entropy(m_logits.float(), m_target)
        loss = loss_p + cfg.value_weight * loss_v + cfg.own_weight * loss_o + cfg.margin_weight * loss_m
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
        tot += torch.stack([loss_p.detach(), loss_v.detach(), loss_o.detach(), loss_m.detach(),
                            (v_logits.argmax(1) == v_target).float().mean(), (p_logits.argmax(1) == pol.argmax(1)).float().mean()])
    net.eval()
    t = (tot / n_steps).tolist()
    return dict(zip(("policy", "value", "own", "margin", "acc_v", "acc_p"), [round(x, 4) for x in t]))


class EvalKit:
    """Persistent evaluation machinery: candidate evaluator, per-anchor players and endgame search are
    built ONCE and reused for every evaluation, with the candidate's weights refreshed in place (the
    mechanism the self-play graphs already rely on). Before 2026-08-31 every evaluation created and
    destroyed 4+ CUDA-graph-capturing search objects; the two in-eval GPU faults of that night
    (nvlddmkm 153, illegal memory access at graph.replay) happened under exactly that churn.

    Logs vs_<anchor> (score), ci_<anchor> (95 % bootstrap over opening pairs), suites_<anchor>
    (score per sub-suite); without a suite: cfg.eval_games games per side, random 2-ply openings."""

    def __init__(self, net, cfg: TrainConfig, device, anchors: dict, suite: Suite | None, es: EndgameSet | None) -> None:
        self.cfg, self.device, self.suite, self.es = cfg, device, suite, es
        graph = device.type == "cuda" and bool(cfg.eval_graph)
        ecfg = SearchConfig(n_sims=cfg.eval_sims, mode="gumbel", gumbel_scale=0.0, cuda_graph=graph, depth_cap=min(cfg.eval_sims, 24))
        self.fe = FusedEvaluator(net, device)
        n = suite.n if suite is not None else cfg.eval_games
        self.pa = SearchPlayer2(self.fe, n, ecfg, device)
        self.pb = {name: SearchPlayer2(aev, n, ecfg, device) for name, aev in anchors.items()}
        self.eg_cache: dict = {}  # sims -> BatchedSearch reused across endgame evaluations

    def run(self, net) -> dict:
        self.fe.refresh(net)
        cfg, out = self.cfg, {}
        if self.suite is None:
            n = cfg.eval_games
            for name, pb in self.pb.items():
                r1 = play_games(self.pa, pb, n, self.device, 2)
                r2 = play_games(pb, self.pa, n, self.device, 2)
                out[f"vs_{name}"] = round((r1.wins + r2.losses + 0.5 * (r1.draws + r2.draws)) / (2 * n), 3)
        else:
            for name, pb in self.pb.items():
                s = summarize(play_paired(self.pa, pb, self.suite, self.device), n_boot=1000)
                o = s["overall"]
                out[f"vs_{name}"] = round(o["score"], 3)
                out[f"ci_{name}"] = [round(o["ci"][0], 3), round(o["ci"][1], 3)]
                out[f"suites_{name}"] = {k: round(v["score"], 3) for k, v in s["suites"].items()}
        if self.es is not None:
            res = endgame_evaluate(self.fe, self.es, self.device, sims=(cfg.eval_sims,), n_boot=200, symmetrise=False,
                                   graph=bool(cfg.eval_graph), search_cache=self.eg_cache)
            raw, srch = res["rows"][0], res["rows"][-1]
            out.update({"eg_wdl_acc": round(raw["wdl_acc"], 4), "eg_brier": round(raw["brier"], 4),
                        "eg_regret_raw": round(raw["regret"], 4), "eg_optimal_raw": round(raw["optimal"], 4),
                        "eg_acc3_search": round(srch["acc3"], 4), "eg_regret_search": round(srch["regret"], 4),
                        "eg_optimal_search": round(srch["optimal"], 4)})
        return out


def main(cfg: TrainConfig) -> None:
    torch.manual_seed(cfg.seed)
    torch.backends.cudnn.benchmark = True
    device = torch.device(cfg.device)
    os.makedirs(os.path.join(cfg.run, "games"), exist_ok=True)
    info = dict(asdict(cfg), _provenance={"argv": sys.argv[1:], "torch": torch.__version__, "git": _git_rev(),
                                          "started": time.strftime("%Y-%m-%d %H:%M:%S")})
    cfg_path = os.path.join(cfg.run, "config.json")
    if os.path.exists(cfg_path):  # never clobber the original run config; record every (re)invocation beside it
        with open(cfg_path) as f:
            old = json.load(f)
        if {k: v for k, v in old.items() if not k.startswith("_")} != asdict(cfg):
            print(f"WARNING: this invocation's config differs from {cfg_path}; the original is kept, "
                  "this one is recorded as config_resume_*.json", flush=True)
        with open(os.path.join(cfg.run, f"config_resume_{time.strftime('%Y%m%d_%H%M%S')}.json"), "w") as f:
            json.dump(info, f, indent=2)
    else:
        with open(cfg_path, "w") as f:
            json.dump(info, f, indent=2)
    net = ResNet(NetConfig(blocks=cfg.blocks, filters=cfg.filters, n_planes=cfg.n_planes, own_classes=cfg.own_classes)).to(device)
    opt = torch.optim.SGD(net.parameters(), lr=cfg.lr, momentum=cfg.momentum, weight_decay=cfg.wd, nesterov=True)
    scaler = torch.amp.GradScaler("cuda")
    buf = GPUReplayBuffer(cfg.buffer, device)
    scfg = SearchConfig(n_sims=cfg.sims, mode=cfg.mode, sample_moves=cfg.sample_moves, temperature=cfg.temperature,
                        sample_uniform=cfg.sample_uniform, root_prior_floor=cfg.root_prior_floor, c_scale=cfg.c_scale,
                        cuda_graph=bool(cfg.cuda_graph), depth_cap=cfg.depth_cap if cfg.cuda_graph else 32)
    fe = FusedEvaluator(net, device)
    sp = ContinuousSelfPlay(fe, cfg.games, scfg, device, sym_hash=bool(cfg.dedup_sym))
    def anchor_name(p):  # runs/dev1/net_0200.pt -> dev1_net_0200 (two runs may share a checkpoint name)
        return f"{os.path.basename(os.path.dirname(p))}_{os.path.splitext(os.path.basename(p))[0]}"

    anchors = {anchor_name(p): FusedEvaluator(load_net(p, device), device) for p in cfg.anchors.split(",") if p}
    suite = None
    if cfg.suite:
        if not os.path.exists(cfg.suite):
            raise FileNotFoundError(f"opening suite {cfg.suite} not found: build it with tools/openings.py build, or pass --suite '' "
                                    "for the old unpaired random-opening evaluation")
        suite = Suite.load(cfg.suite)
        if cfg.eval_openings:
            suite = suite.subset(cfg.eval_openings)
        print(f"evaluation: paired openings from {cfg.suite} {suite.counts()} -> {2 * suite.n} games per anchor at {cfg.eval_sims} sims", flush=True)
    es = None
    if cfg.endgame_set:
        if not os.path.exists(cfg.endgame_set):
            raise FileNotFoundError(f"endgame set {cfg.endgame_set} not found: build it with tools/endgame.py build, or pass --endgame_set ''")
        es = EndgameSet.load(cfg.endgame_set)
        print(f"evaluation: exact endgame set {cfg.endgame_set} ({es.n} positions)", flush=True)
    labeler = ExactLabeler(cfg.exact_processes, cfg.exact_max_empty, cfg.exact_per_iter, seed=cfg.seed) if cfg.exact_max_empty > 0 else None
    if labeler:
        print(f"exact labels: <= {cfg.exact_max_empty} empties, <= {cfg.exact_per_iter} positions/iteration, {cfg.exact_processes} workers, "
              f"weight x{cfg.exact_weight}, policy {'replaced' if cfg.exact_policy else 'kept'}", flush=True)
    drops = [int(x) for x in cfg.lr_drops.split(",") if x]
    log_path = os.path.join(cfg.run, "log.jsonl")
    ckpt_path = os.path.join(cfg.run, "latest.pt")  # every iteration, no buffer (small, fast)
    full_path = os.path.join(cfg.run, "latest_full.pt")  # every save_buffer_every iterations, WITH buffer
    start_iter, global_step = 0, 0
    resume_path = full_path if os.path.exists(full_path) else ckpt_path  # prefer full state: replaying a few
    if os.path.exists(resume_path):  # iterations beats resuming with an empty buffer (bit us 2026-08-30)
        ck = torch.load(resume_path, map_location=device, weights_only=False)
        net.load_state_dict(ck["net"])
        opt.load_state_dict(ck["opt"])
        if "buffer" in ck:
            buf.load_state_dict(ck["buffer"])
        else:
            print(f"WARNING: {resume_path} has no replay buffer (saved every {cfg.save_buffer_every} iterations); "
                  "resuming with an EMPTY buffer", flush=True)
        start_iter, global_step = ck["iter"] + 1, ck.get("global_step", 0)
        fe.refresh(net)
        print(f"resumed from iteration {ck['iter']} ({os.path.basename(resume_path)}, buffer {buf.size})", flush=True)
    ekit = EvalKit(net, cfg, device, anchors, suite, es) if cfg.eval_every else None

    schedule = sorted((int(a), int(b)) for a, b in (x.split(":") for x in cfg.sims_schedule.split(",") if x))
    for it in range(start_iter, cfg.iters):
        sims_now = max([cfg.sims] + [v for k, v in schedule if it >= k])
        if sims_now != sp.search.cfg.n_sims:
            from dataclasses import replace
            sp.search = BatchedSearch(fe, cfg.games, replace(scfg, n_sims=sims_now), device)
            print(f"iteration {it}: simulations per move -> {sims_now}", flush=True)
        t0 = time.perf_counter()
        sp.iteration = it
        pos, games, stats = sp.run(cfg.steps)
        t_sp = time.perf_counter() - t0
        np.savez_compressed(os.path.join(cfg.run, "games", f"games_{it:04d}.npz"), **games)
        n_new = buf.add(pos) if pos["cells"] is not None else 0
        n_submitted = labeler.submit(pos, buf.last_slots) if (labeler and n_new) else 0
        dup = buf.update_weights(cfg.dedup_alpha, cfg.exact_weight, cfg.dedup_alpha_early)
        base_lr = cfg.lr * (0.1 ** sum(it >= d for d in drops))

        def lr_fn():
            nonlocal global_step
            global_step += 1
            return base_lr * min(1.0, global_step / max(cfg.warmup_steps, 1))

        n_steps = max(cfg.min_steps, int(cfg.epochs * cfg.games * cfg.steps / cfg.batch))
        t1 = time.perf_counter()
        if buf.size >= cfg.batch:
            losses = train_steps(net, opt, scaler, buf, cfg, n_steps, device, lr_fn)
            fe.refresh(net)
        else:
            losses, n_steps = {}, 0  # nothing finished yet (first iterations of a short-step run)
        t_tr = time.perf_counter() - t1
        rec = {"iter": it, "positions_new": n_new, "buffer": buf.size, "steps": n_steps, "lr": round(base_lr, 5), "sims": sims_now,
               "t_selfplay": round(t_sp, 1), "t_train": round(t_tr, 1),
               "games_per_s": round(stats.games / t_sp, 1), "pos_per_s": round(cfg.games * cfg.steps / t_sp),
               **stats.summary(), **dup, **{f"loss_{k}": v for k, v in losses.items()}}
        if labeler and n_submitted:
            t3 = time.perf_counter()
            got = labeler.collect()  # solved while the trainer ran; waits for the remainder
            if got:
                slots, vals, pols = got
                buf.apply_exact(slots, vals, pols if cfg.exact_policy else None)
                rec.update({"exact_new": int(len(vals)), "exact_total": labeler.total, "t_exact_wait": round(time.perf_counter() - t3, 1),
                            "exact_wdl": [round(float((vals == v).mean()), 3) for v in (1, 0, -1)]})
        if ekit and (it + 1) % cfg.eval_every == 0:
            t2 = time.perf_counter()
            rec.update(ekit.run(net))
            rec["t_eval"] = round(time.perf_counter() - t2, 1)
            torch.save({"net": net.state_dict(), "cfg": asdict(cfg)}, os.path.join(cfg.run, f"net_{it + 1:04d}.pt"))
        t4 = time.perf_counter()
        ck = {"net": net.state_dict(), "opt": opt.state_dict(), "iter": it, "global_step": global_step, "cfg": asdict(cfg)}
        torch.save(ck, ckpt_path + ".tmp")  # atomic: a crash mid-save must not destroy the resume point
        os.replace(ckpt_path + ".tmp", ckpt_path)
        if cfg.save_buffer_every and (it + 1) % cfg.save_buffer_every == 0:
            ck["buffer"] = buf.state_dict()
            torch.save(ck, full_path + ".tmp")  # separate file: later bufferless saves can no longer destroy it
            os.replace(full_path + ".tmp", full_path)
        rec["t_ckpt"] = round(time.perf_counter() - t4, 1)
        rec["t_iter"] = round(time.perf_counter() - t0, 1)  # end-to-end, incl. persistence/buffer/exact/eval/ckpt
        print(json.dumps(rec), flush=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
    if labeler:
        labeler.close()
    with open(os.path.join(cfg.run, "DONE"), "w") as f:  # watchers wait for this, not for a checkpoint name
        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k, v in asdict(TrainConfig()).items():
        ap.add_argument(f"--{k}", type=type(v), default=v)
    main(TrainConfig(**vars(ap.parse_args())))
