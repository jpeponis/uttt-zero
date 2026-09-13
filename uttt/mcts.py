"""Batched Monte-Carlo tree search: n independent trees advanced in lockstep.

Two search policies share one tree structure:

* ``puct``   — AlphaZero: PUCT selection, Dirichlet root noise, visit-count
               policy target, temperature sampling of the move.
* ``gumbel`` — Gumbel AlphaZero (Danihelka et al. 2022) following DeepMind's
               mctx: Gumbel-top-k + Sequential Halving at the root, deterministic
               interior selection, "completed Q" improved-policy target. Works
               with very few simulations (16–64) and needs no noise/temperature.

Simulation i (1..n_sims) creates at most one node per tree, stored in slot i,
so all tree arrays are fixed-size (n, n_sims + 1, ...). Each simulation costs
one batched network call over the n leaves.

Value convention: value_sum[node] accumulates values from the perspective of
the player to move AT that node (same convention as the network). Selection at
a parent therefore uses Q(child) = -value_sum[child] / visit[child].
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import torch

from .batch import legal_mask, step_state, terminal_value
from .rules import check_rule


@dataclass
class MCTSConfig:
    n_sims: int = 32
    mode: str = "gumbel"  # "gumbel" | "puct"
    max_depth: int = 82
    # gumbel
    m_considered: int = 16
    gumbel_scale: float = 1.0  # 0 => deterministic (evaluation)
    c_visit: float = 50.0
    c_scale: float = 0.1  # mctx value_scale (q rescaled to [0,1])
    # puct
    c_puct: float = 1.25
    fpu: float = 0.0
    dirichlet_alpha: float = 1.0
    noise_frac: float = 0.25
    temperature: float = 1.0
    temp_moves: int = 10  # plies sampled ∝ visits^(1/T) before switching to argmax


@dataclass
class SearchResult:
    policy: torch.Tensor  # (n, 81) training target
    action: torch.Tensor  # (n,) chosen move
    visits: torch.Tensor  # (n, 81) root child visit counts
    root_value: torch.Tensor  # (n,) search value estimate, side-to-move perspective
    raw_value: torch.Tensor  # (n,) network value at root
    cap_hits: torch.Tensor | None = None  # (n,) simulations whose descent hit depth_cap without expanding (v2 search)
    raw_kl: torch.Tensor | None = None  # (n,) KL(search policy || raw net policy) at the root (v2 search; PLAN6 E8)
    q_range: torch.Tensor | None = None  # (n,) max - min of the root's visited-child Q (what Gumbel's sigma rescales; E8)


def table_of_considered_visits(m: int, n_sims: int) -> torch.Tensor:
    """(m+1, n_sims) table: row k = Sequential-Halving visit schedule for k considered actions."""
    table = torch.zeros(m + 1, n_sims, dtype=torch.long)
    for k in range(1, m + 1):
        if k <= 1:
            seq = list(range(n_sims))
        else:
            log2max = int(math.ceil(math.log2(k)))
            seq, visits, num = [], [0] * k, k
            while len(seq) < n_sims:
                extra = max(1, int(n_sims / (log2max * num)))
                for _ in range(extra):
                    seq.extend(visits[:num])
                    for i in range(num):
                        visits[i] += 1
                num = max(2, num // 2)
        table[k] = torch.tensor(seq[:n_sims])
    return table


class BatchedMCTS:
    def __init__(self, evaluator, n: int, cfg: MCTSConfig, device, rule: str = "count") -> None:
        self.eval = evaluator
        self.n = n
        self.cfg = cfg
        self.rule = check_rule(rule)
        self.device = torch.device(device)
        d = self.device
        M = cfg.n_sims + 1
        self.M = M
        self.idx = torch.arange(n, device=d)
        self.s_cells = torch.zeros(n, M, 81, dtype=torch.int8, device=d)
        self.s_macro = torch.zeros(n, M, 9, dtype=torch.int8, device=d)
        self.s_next = torch.zeros(n, M, dtype=torch.int8, device=d)
        self.s_player = torch.zeros(n, M, dtype=torch.int8, device=d)
        self.s_done = torch.zeros(n, M, dtype=torch.bool, device=d)
        self.s_winner = torch.zeros(n, M, dtype=torch.int8, device=d)
        self.s_legal = torch.zeros(n, M, 81, dtype=torch.bool, device=d)
        self.s_value = torch.zeros(n, M, dtype=torch.float32, device=d)  # network value at node
        self.prior = torch.zeros(n, M, 81, dtype=torch.float32, device=d)
        self.children = torch.full((n, M, 81), -1, dtype=torch.long, device=d)
        self.visit = torch.zeros(n, M, dtype=torch.float32, device=d)
        self.value_sum = torch.zeros(n, M, dtype=torch.float32, device=d)
        self.table = table_of_considered_visits(cfg.m_considered, cfg.n_sims).to(d)

    def _reset(self) -> None:
        self.children.fill_(-1)
        self.visit.zero_()
        self.value_sum.zero_()
        self.prior.zero_()
        self.s_done.zero_()

    def _put(self, slot, mask, cells, macro, nb, player, done, winner, prior, value) -> None:
        self.s_cells[mask, slot] = cells[mask]
        self.s_macro[mask, slot] = macro[mask]
        self.s_next[mask, slot] = nb[mask]
        self.s_player[mask, slot] = player[mask]
        self.s_done[mask, slot] = done[mask]
        self.s_winner[mask, slot] = winner[mask]
        self.s_legal[mask, slot] = legal_mask(cells, macro, nb, done)[mask]
        self.prior[mask, slot] = prior[mask]
        self.s_value[mask, slot] = value[mask]

    # ---- child statistics for a batch of nodes -----------------------------
    def _child_stats(self, node):
        ch = self.children[self.idx, node]
        has = ch >= 0
        chc = ch.clamp(min=0)
        zeros = torch.zeros_like(self.prior[:, 0])
        Nc = torch.where(has, self.visit.gather(1, chc), zeros)
        Wc = torch.where(has, self.value_sum.gather(1, chc), zeros)
        Qc = torch.where(Nc > 0, -Wc / Nc.clamp(min=1), zeros)  # from this node's perspective
        return ch, Nc, Qc

    def _completed_q_sigma(self, node, P, legal, Nc, Qc):
        """mctx qtransform_completed_by_mix_value: sigma(completed q) rescaled to [0,1]."""
        cfg = self.cfg
        visited = Nc > 0
        sum_visits = Nc.sum(1)
        sum_probs = (P * visited).sum(1)
        weighted_q = (P * Qc * visited).sum(1) / torch.where(sum_probs > 0, sum_probs, torch.ones_like(sum_probs))
        raw = self.s_value[self.idx, node]
        v_mix = (raw + sum_visits * weighted_q) / (sum_visits + 1)
        completed = torch.where(visited, Qc, v_mix.unsqueeze(1))
        big = torch.finfo(torch.float32).max
        lo = torch.where(legal, completed, torch.full_like(completed, big)).min(1, keepdim=True).values
        hi = torch.where(legal, completed, torch.full_like(completed, -big)).max(1, keepdim=True).values
        qn = (completed - lo) / (hi - lo).clamp(min=1e-6)
        return (cfg.c_visit + Nc.max(1, keepdim=True).values) * cfg.c_scale * qn

    @torch.no_grad()
    def search(self, cells, macro, next_board, player, done, winner, selfplay: bool, ply: int = 0) -> SearchResult:
        cfg, n, idx, d = self.cfg, self.n, self.idx, self.device
        gumbel = cfg.mode == "gumbel"
        self._reset()
        all_mask = torch.ones(n, dtype=torch.bool, device=d)

        probs, value = self.eval(cells, macro, next_board, player, done)
        root_legal = legal_mask(cells, macro, next_board, done)
        if not gumbel and selfplay:
            gamma = torch.distributions.Gamma(torch.full((1,), cfg.dirichlet_alpha, device=d), torch.ones(1, device=d))
            noise = gamma.sample((n, 81)).squeeze(-1) * root_legal
            noise = noise / noise.sum(1, keepdim=True).clamp(min=1e-9)
            probs = (1 - cfg.noise_frac) * probs + cfg.noise_frac * noise
        root_value0 = torch.where(done, terminal_value(winner, player, done), value)
        self._put(0, all_mask, cells, macro, next_board, player, done, winner, probs, root_value0)
        self.visit[:, 0] = 1
        self.value_sum[:, 0] = root_value0

        if gumbel:
            root_logits = torch.log(probs.clamp(min=1e-30)).masked_fill(~root_legal, float("-inf"))
            root_logits = root_logits - root_logits.max(1, keepdim=True).values
            u = torch.rand(n, 81, device=d).clamp(min=1e-20)
            g = (-torch.log(-torch.log(u))) * (cfg.gumbel_scale if selfplay else 0.0)
            n_legal = root_legal.sum(1).clamp(max=cfg.m_considered)
            schedule = self.table[n_legal]  # (n, n_sims)

        path = torch.zeros((n, cfg.max_depth + 1), dtype=torch.long, device=d)
        for i in range(1, cfg.n_sims + 1):
            node = torch.zeros(n, dtype=torch.long, device=d)
            depth = torch.zeros(n, dtype=torch.long, device=d)
            active = all_mask.clone()
            need_expand = torch.zeros(n, dtype=torch.bool, device=d)
            exp_parent = torch.zeros(n, dtype=torch.long, device=d)
            exp_action = torch.zeros(n, dtype=torch.long, device=d)

            # ---- selection ------------------------------------------------
            for dpt in range(cfg.max_depth):
                term = self.s_done[idx, node]
                active &= ~term
                if not bool(active.any()):
                    break
                P = self.prior[idx, node]
                legal = self.s_legal[idx, node]
                ch, Nc, Qc = self._child_stats(node)
                neg_inf = torch.full_like(P, float("-inf"))
                if gumbel:
                    sigma = self._completed_q_sigma(node, P, legal, Nc, Qc)
                    if dpt == 0:
                        considered = schedule[:, i - 1].unsqueeze(1)
                        score = torch.where(Nc == considered, g + root_logits + sigma, neg_inf)
                    else:
                        logits = torch.log(P.clamp(min=1e-30)).masked_fill(~legal, float("-inf"))
                        pi = torch.softmax(logits + sigma, dim=1)
                        score = pi - Nc / (1 + Nc.sum(1, keepdim=True))
                else:
                    Q = torch.where(Nc > 0, Qc, torch.full_like(P, cfg.fpu))
                    Np = self.visit[idx, node]
                    score = Q + cfg.c_puct * P * Np.sqrt().unsqueeze(1) / (1 + Nc)
                score = torch.where(legal, score, neg_inf)
                a = score.argmax(1)
                child = ch[idx, a]
                exists = child >= 0
                ex = active & ~exists
                exp_parent = torch.where(ex, node, exp_parent)
                exp_action = torch.where(ex, a, exp_action)
                need_expand |= ex
                active &= exists
                node = torch.where(active, child, node)
                depth += active.long()
                path[idx, depth] = torch.where(active, node, path[idx, depth])

            # ---- expansion ------------------------------------------------
            pc = self.s_cells[idx, exp_parent]
            pm = self.s_macro[idx, exp_parent]
            pn = self.s_next[idx, exp_parent]
            pp = self.s_player[idx, exp_parent]
            pd = self.s_done[idx, exp_parent]
            pw = self.s_winner[idx, exp_parent]
            nc, nm, nn_, npl, nd, nw, _ = step_state(pc, pm, pn, pp, pd, pw, exp_action, self.rule)
            probs, value = self.eval(nc, nm, nn_, npl, nd)
            value = torch.where(nd, terminal_value(nw, npl, nd), value)
            self._put(i, need_expand, nc, nm, nn_, npl, nd, nw, probs, value)
            self.children[idx[need_expand], exp_parent[need_expand], exp_action[need_expand]] = i
            depth = depth + need_expand.long()
            path[idx, depth] = torch.where(need_expand, torch.full_like(node, i), path[idx, depth])

            leaf = path[idx, depth]
            lw = self.s_winner[idx, leaf]
            lp = self.s_player[idx, leaf]
            ld = self.s_done[idx, leaf]
            v = torch.where(ld, terminal_value(lw, lp, ld), value)

            # ---- backup ---------------------------------------------------
            for j in range(int(depth.max().item()) + 1):
                valid = depth >= j
                nodes_j = path[:, j]
                sign = torch.where((depth - j) % 2 == 0, 1.0, -1.0)
                self.visit.index_put_((idx[valid], nodes_j[valid]), torch.ones(int(valid.sum()), device=d), accumulate=True)
                self.value_sum.index_put_((idx[valid], nodes_j[valid]), (v * sign)[valid], accumulate=True)

        # ---- root summary -------------------------------------------------
        root = torch.zeros(n, dtype=torch.long, device=d)
        P = self.prior[:, 0]
        ch, Nc, Qc = self._child_stats(root)
        root_value = self.value_sum[:, 0] / self.visit[:, 0]
        neg_inf = torch.full_like(P, float("-inf"))
        if gumbel:
            sigma = self._completed_q_sigma(root, P, root_legal, Nc, Qc)
            policy = torch.softmax((root_logits + sigma).masked_fill(~root_legal, float("-inf")), dim=1)
            top = Nc.max(1, keepdim=True).values
            score = torch.where((Nc == top) & root_legal, g + root_logits + sigma, neg_inf)
            action = score.argmax(1)
        else:
            policy = Nc / Nc.sum(1, keepdim=True).clamp(min=1)
            if selfplay and ply < cfg.temp_moves and cfg.temperature > 0:
                w = Nc.pow(1.0 / cfg.temperature) * root_legal
                action = torch.multinomial(w.clamp(min=1e-12) * root_legal, 1).squeeze(1)
            else:
                action = torch.where(root_legal, Nc, neg_inf).argmax(1)
        policy = torch.nan_to_num(policy, nan=0.0)
        return SearchResult(policy=policy, action=action, visits=Nc, root_value=root_value, raw_value=self.s_value[:, 0])
