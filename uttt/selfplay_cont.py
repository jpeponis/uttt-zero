"""Continuous self-play (v2): n games run in parallel indefinitely; a finished game is
flushed to the output and reset in place, so no simulation is spent on a lock-step tail.

Per position we keep: state, policy target, search root value, ply; and, once the
game ends: result z, final local-board ownership, and the won-board margin, all from
the side-to-move's perspective. Every finished game's move sequence is returned so
it can be persisted (tools/corpus_stats.py reads those files).

Also here: GPUReplayBuffer — a ring buffer on the GPU with a 64-bit position hash,
so identical positions (the opening plies) can be down-weighted at sampling time.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from .batch import FULL, BatchUTTT, consts
from .search import BatchedSearch, SearchConfig

MAX_PLY = 82
POS_FIELDS = ("cells", "macro", "next_board", "player", "policy", "value", "ownership", "margin", "root_value", "ply", "hash",
              "game", "iter")  # game: id of the source game (counter per self-play object); iter: training iteration it finished in


_HASH_COEF: dict = {}


def position_hash(cells, next_board, player) -> torch.Tensor:
    """64-bit hash of (cells, next_board, player); collisions are negligible for our buffer sizes."""
    d = cells.device
    coef = _HASH_COEF.get(str(d))
    if coef is None:
        gen = torch.Generator(device="cpu").manual_seed(12345)
        coef = _HASH_COEF[str(d)] = torch.randint(-(2**62), 2**62, (83,), generator=gen).to(d)
    x = torch.cat([cells.long() + 1, next_board.long().unsqueeze(1) + 2, player.long().unsqueeze(1) + 2], dim=1)
    return (x * coef).sum(1)  # wraps mod 2^64


def position_hash_sym(cells, next_board, player) -> torch.Tensor:
    """Symmetry-invariant hash: the minimum of position_hash over the 8 D4 images, so symmetric
    positions count as duplicates (the trainer applies random symmetries anyway)."""
    c = consts(cells.device)
    nb = next_board.long()
    hs = []
    for s in range(8):
        nbs = torch.where(nb >= 0, c["SYM_BOARD"][s][nb.clamp(min=0)], nb).to(next_board.dtype)
        hs.append(position_hash(cells[:, c["SYM_CELL_INV"][s]], nbs, player))
    return torch.stack(hs, 1).min(1).values


@dataclass
class SelfPlayStats:
    games: int = 0
    x_win: int = 0
    o_win: int = 0
    draw: int = 0
    end_line: int = 0
    end_count: int = 0
    total_len: int = 0
    surprise: float = 0.0
    cap_hits: float = 0.0  # mean per-move fraction of simulations truncated by depth_cap
    raw_kl: float = 0.0  # mean KL(search policy || raw policy) at the root (PLAN6 E8)
    q_range: float = 0.0  # mean root Q range over visited children (E8)
    target_entropy: float = 0.0  # mean entropy of the policy target, bits (E8)
    steps: int = 0
    first_moves: list = field(default_factory=list)

    def summary(self) -> dict:
        g = max(self.games, 1)
        fm = np.bincount(np.array(self.first_moves, dtype=np.int64), minlength=81) if self.first_moves else np.zeros(81)
        return {
            "games": self.games, "x_win": round(self.x_win / g, 3), "o_win": round(self.o_win / g, 3),
            "draw": round(self.draw / g, 3), "end_line": round(self.end_line / g, 3), "end_count": round(self.end_count / g, 3),
            "mean_len": round(self.total_len / g, 1), "surprise": round(self.surprise / max(self.steps, 1), 4),
            "cap_hit": round(self.cap_hits / max(self.steps, 1), 4),
            "raw_kl": round(self.raw_kl / max(self.steps, 1), 4), "q_range": round(self.q_range / max(self.steps, 1), 4),
            "target_entropy": round(self.target_entropy / max(self.steps, 1), 4),
            "first_move_top": int(fm.argmax()), "first_move_top_share": round(float(fm.max() / max(fm.sum(), 1)), 3),
            "first_move_distinct": int((fm > 0).sum()),
        }


class ContinuousSelfPlay:
    def __init__(self, evaluator, n: int, cfg: SearchConfig, device, sym_hash: bool = False,
                 generator: torch.Generator | None = None) -> None:
        self.n = n
        self.device = torch.device(device)
        self.sym_hash = sym_hash  # duplicate counting under D4 symmetry
        self.gen = generator  # the search's noise and move sampling draw from it (PLAN6 E4)
        d = self.device
        self.g = BatchUTTT(n, d)
        self.search = BatchedSearch(evaluator, n, cfg, d, generator=generator)
        self.idx = torch.arange(n, device=d)
        self.len = torch.zeros(n, dtype=torch.long, device=d)
        self.st_cells = torch.zeros(n, MAX_PLY, 81, dtype=torch.int8, device=d)
        self.st_macro = torch.zeros(n, MAX_PLY, 9, dtype=torch.int8, device=d)
        self.st_next = torch.zeros(n, MAX_PLY, dtype=torch.int8, device=d)
        self.st_player = torch.zeros(n, MAX_PLY, dtype=torch.int8, device=d)
        self.st_policy = torch.zeros(n, MAX_PLY, 81, dtype=torch.float16, device=d)
        self.st_rootv = torch.zeros(n, MAX_PLY, dtype=torch.float16, device=d)
        self.st_moves = torch.zeros(n, MAX_PLY, dtype=torch.int8, device=d)
        self.game_id = torch.arange(n, device=d)  # provenance: id of the game currently in each slot
        self.games_started = n
        self.iteration = 0  # set by the trainer before run(); recorded with every position

    def set_evaluator(self, evaluator) -> None:
        self.search.eval = evaluator

    @torch.no_grad()
    def run(self, steps: int):
        """Advance every game by `steps` moves. Returns (positions dict, games dict, SelfPlayStats).

        positions: tensors on the device for every position whose game finished during
        these steps (fields in POS_FIELDS). games: numpy arrays moves (G, 82) int8 padded
        with -1, root_values (G, 82) f16, winners, reasons, lengths.
        """
        g, idx, d = self.g, self.idx, self.device
        out = {k: [] for k in POS_FIELDS}
        games = {"moves": [], "root_values": [], "winners": [], "reasons": [], "lengths": []}
        stats = SelfPlayStats()
        for _ in range(steps):
            res = self.search.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=True, ply=self.len)
            t = self.len
            self.st_cells[idx, t] = g.cells
            self.st_macro[idx, t] = g.macro
            self.st_next[idx, t] = g.next_board
            self.st_player[idx, t] = g.player
            self.st_policy[idx, t] = res.policy.half()
            self.st_rootv[idx, t] = res.root_value.half()
            self.st_moves[idx, t] = res.action.to(torch.int8)
            stats.surprise += float((res.root_value - res.raw_value).abs().mean())
            if res.cap_hits is not None:
                stats.cap_hits += float(res.cap_hits.mean()) / self.search.cfg.n_sims
            if res.raw_kl is not None:
                stats.raw_kl += float(res.raw_kl.mean())
                stats.q_range += float(res.q_range.mean())
            stats.target_entropy += float(-(res.policy * torch.log2(res.policy.clamp(min=1e-12))).sum(1).mean())
            stats.steps += 1
            self.len = t + 1
            g.step(res.action)

            fin = torch.nonzero(g.done).squeeze(1)
            k = int(fin.numel())
            if k == 0:
                continue
            L = self.len[fin]
            tt = torch.arange(MAX_PLY, device=d)
            m2 = tt.unsqueeze(0) < L.unsqueeze(1)  # (k, MAX_PLY)
            gi = fin.unsqueeze(1).expand(-1, MAX_PLY)[m2]
            ti = tt.unsqueeze(0).expand(k, -1)[m2]
            player = self.st_player[gi, ti]
            winner = g.winner[gi]
            final_macro = g.macro[gi]
            p1 = player.unsqueeze(1)
            # ownership at the end: 1 self-won, -1 opponent-won, 2 full without a winner, 0 still open
            own = torch.where(final_macro == p1, 1, torch.where(final_macro == -p1, -1, torch.where(final_macro == FULL, 2, 0))).to(torch.int8)
            margin = ((final_macro == 1).sum(1) - (final_macro == -1).sum(1)).to(torch.int8) * player
            cells = self.st_cells[gi, ti]
            nb = self.st_next[gi, ti]
            out["cells"].append(cells)
            out["macro"].append(self.st_macro[gi, ti])
            out["next_board"].append(nb)
            out["player"].append(player)
            out["policy"].append(self.st_policy[gi, ti])
            out["value"].append((winner * player).to(torch.int8))
            out["ownership"].append(own)
            out["margin"].append(margin)
            out["root_value"].append(self.st_rootv[gi, ti])
            out["ply"].append(ti.to(torch.int16))
            out["hash"].append((position_hash_sym if self.sym_hash else position_hash)(cells, nb, player))
            out["game"].append(self.game_id[gi])
            out["iter"].append(torch.full((gi.numel(),), self.iteration, dtype=torch.int16, device=d))
            # games
            mv = torch.where(m2, self.st_moves[fin], torch.full_like(self.st_moves[fin], -1))
            games["moves"].append(mv.cpu().numpy())
            games["root_values"].append(torch.where(m2, self.st_rootv[fin], torch.zeros_like(self.st_rootv[fin])).cpu().numpy())
            w = g.winner[fin]
            r = g.end_reason[fin]
            games["winners"].append(w.cpu().numpy())
            games["reasons"].append(r.cpu().numpy())
            games["lengths"].append(L.cpu().numpy())
            stats.games += k
            stats.x_win += int((w == 1).sum())
            stats.o_win += int((w == -1).sum())
            stats.draw += int((w == 0).sum())
            stats.end_line += int((r == 1).sum())
            stats.end_count += int((r == 2).sum())
            stats.total_len += int(L.sum())
            stats.first_moves.extend(self.st_moves[fin, 0].tolist())
            g.reset_where(g.done)
            self.len[fin] = 0
            self.game_id[fin] = torch.arange(self.games_started, self.games_started + k, device=d)
            self.games_started += k
        positions = {k: (torch.cat(v) if v else None) for k, v in out.items()}
        games = {k: (np.concatenate(v) if v else np.zeros((0,) + ((MAX_PLY,) if k in ("moves", "root_values") else ()))) for k, v in games.items()}
        return positions, games, stats


class GPUReplayBuffer:
    """Ring buffer on the GPU. sample() draws ∝ weight, where weight = count^-alpha of identical positions."""

    def __init__(self, capacity: int, device, generator: torch.Generator | None = None) -> None:
        self.capacity = capacity
        self.device = torch.device(device)
        self.gen = generator  # sampling draws from it (PLAN6 E4)
        self.last_sample = None  # row indices of the last sample_batches() draw (for the budget log, E8)
        d = self.device
        self.size = 0
        self.pos = 0
        z = lambda *shape, dtype: torch.zeros(*shape, dtype=dtype, device=d)  # noqa: E731
        self.buf = {
            "cells": z(capacity, 81, dtype=torch.int8), "macro": z(capacity, 9, dtype=torch.int8),
            "next_board": z(capacity, dtype=torch.int8), "player": z(capacity, dtype=torch.int8),
            "policy": z(capacity, 81, dtype=torch.float16), "value": z(capacity, dtype=torch.int8),
            "ownership": z(capacity, 9, dtype=torch.int8), "margin": z(capacity, dtype=torch.int8),
            "root_value": z(capacity, dtype=torch.float16), "ply": z(capacity, dtype=torch.int16),
            "hash": z(capacity, dtype=torch.int64),
            "game": z(capacity, dtype=torch.int64), "iter": z(capacity, dtype=torch.int16),
            "exact": z(capacity, dtype=torch.int8),  # 1 where value (and policy) were replaced by exact solver labels
        }
        self.weights = torch.ones(capacity, device=d)
        self.dup_stats = {}
        self.last_slots = None  # rows written by the last add()

    def add(self, positions: dict) -> int:
        m = int(positions["cells"].shape[0])
        if m == 0:
            self.last_slots = None
            return 0
        idx = (torch.arange(m, device=self.device) + self.pos) % self.capacity
        for k in POS_FIELDS:
            self.buf[k][idx] = positions[k].to(self.buf[k].dtype)
        self.buf["exact"][idx] = 0
        self.pos = (self.pos + m) % self.capacity
        self.size = min(self.size + m, self.capacity)
        self.last_slots = idx
        return m

    def apply_exact(self, slots, values, policies=None) -> int:
        """Overwrite the value target (and, if given, the policy target) of the given rows with exact labels."""
        slots = torch.as_tensor(slots, device=self.device).long()
        self.buf["value"][slots] = torch.as_tensor(values, device=self.device).to(torch.int8)
        if policies is not None:
            self.buf["policy"][slots] = torch.as_tensor(policies, device=self.device).to(torch.float16)
        self.buf["exact"][slots] = 1
        return int(slots.numel())

    def update_weights(self, alpha: float = 0.5, exact_weight: float = 1.0, alpha_early: float = 0.0, early_plies: int = 8) -> dict:
        """Recompute sampling weights = count^-alpha over identical positions (count^-alpha_early for plies
        < early_plies when alpha_early > 0; x exact_weight for exactly labelled rows); returns duplication stats."""
        if self.size == 0:
            self.dup_stats = {}
            return {}
        h = self.buf["hash"][: self.size]
        _, inv, counts = torch.unique(h, return_inverse=True, return_counts=True)
        c = counts[inv].float()
        w = c.pow(-alpha) if alpha > 0 else torch.ones_like(c)
        ply = self.buf["ply"][: self.size]
        if alpha_early > 0:
            w = torch.where(ply < early_plies, c.pow(-alpha_early), w)
        exact = self.buf["exact"][: self.size] > 0
        if exact_weight != 1.0:
            w = torch.where(exact, w * exact_weight, w)
        self.weights[: self.size] = w
        stats = {"distinct_frac": round(float(counts.numel() / self.size), 3), "exact_frac": round(float(exact.float().mean()), 4)}
        for p in (0, 2, 4, 8, 12):
            m = ply == p
            if m.any():
                stats[f"dup_mean_ply{p}"] = round(float(c[m].mean()), 1)
        self.dup_stats = stats
        return stats

    def sample(self, batch_size: int) -> dict:
        idx = torch.multinomial(self.weights[: self.size], batch_size, replacement=True, generator=self.gen)
        return {k: self.buf[k][idx] for k in POS_FIELDS + ("exact",)}

    def sample_batches(self, batch_size: int, n: int):
        """n batches from ONE multinomial draw (REVIEW-astra §7.5's pre-draw: the per-step draw cost 0.45 s per
        iteration); yields the same dicts as sample(). The draw is kept in last_sample for the budget log."""
        idx = torch.multinomial(self.weights[: self.size], batch_size * n, replacement=True, generator=self.gen)
        self.last_sample = idx
        idx = idx.view(n, batch_size)
        for i in range(n):
            yield {k: self.buf[k][idx[i]] for k in POS_FIELDS + ("exact",)}

    def sample_stats(self, iteration: int) -> dict:
        """Of the last sample_batches() draw: rows, mean replay age in iterations, distinct-position fraction (E8)."""
        idx = self.last_sample
        if idx is None:
            return {}
        age = (iteration - self.buf["iter"][idx].float()).mean()
        distinct = torch.unique(self.buf["hash"][idx]).numel()
        return {"rows_sampled": int(idx.numel()), "replay_age": round(float(age), 2),
                "sample_distinct_frac": round(distinct / idx.numel(), 3)}

    def state_dict(self) -> dict:
        return {"size": self.size, "pos": self.pos, "buf": {k: v[: self.size].cpu() for k, v in self.buf.items()}}

    def load_state_dict(self, sd: dict) -> None:
        n = min(sd["size"], self.capacity)
        for k in POS_FIELDS + ("exact",):
            if k in sd["buf"]:
                self.buf[k][:n] = sd["buf"][k][:n].to(self.device)
            else:
                self.buf[k][:n] = 0
        self.size, self.pos = n, sd["pos"] % self.capacity
        self.update_weights()
