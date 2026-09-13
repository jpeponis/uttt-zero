"""v2 batched tree search: same algorithms as uttt.mcts (PUCT / Gumbel AlphaZero) with

* edge statistics N[node, a], W[node, a] stored on the parent (W from the parent's
  side-to-move perspective) instead of gathered through child nodes;
* no boolean-mask indexing and no per-level host syncs — at most one sync per
  simulation (to bound the descent loop), or none with sync_per_sim=False;
* a fully vectorised backup (one index_add_ per statistic);
* optional CUDA-graph replay of the whole simulation (cuda_graph=True): one graph
  per descent length, captured on first use; the simulation index, the Gumbel
  schedule column, the Gumbel noise and the root logits are static tensors;
* two self-play changes motivated by run dev1 (RESULTS-dev1.md): an optional
  uniform floor mixed into the root prior, and sampling the self-play move from
  the improved policy for the first `sample_moves` plies;
* RNG hygiene (PLAN6 E4): the Gumbel noise and the self-play move sampling draw from
  the search's own torch.Generator when one is given, and a deterministic search
  (selfplay=False, or gumbel_scale 0) draws nothing at all — so an evaluation
  inserted between two training iterations leaves the trainer's random streams
  where they were (tests/test_rng_hygiene.py). This makes evaluation observationally
  neutral; it does not make training trajectories reproducible (the pipeline is not
  bitwise deterministic under cudnn.benchmark + fp16, and a 4096-game self-play loop
  amplifies a last-bit difference within one iteration: PLAN6 §1 item 13).

search() returns the same SearchResult as uttt.mcts and, with the new options at
their defaults, produces identical trees (tests/test_search_v2.py).
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

from .batch import legal_mask, step_state, terminal_value
from .mcts import MCTSConfig, SearchResult, table_of_considered_visits
from .rules import check_rule


@dataclass
class SearchConfig(MCTSConfig):
    root_prior_floor: float = 0.0  # mix this fraction of uniform-over-legal into the root prior
    sample_moves: int = 0  # plies (from the start of the game) whose self-play move is sampled ∝ target^(1/T)
    sample_uniform: float = 0.0  # exploration floor: sampled from (1-u)*target + u*uniform(legal) during those plies
    depth_cap: int = 32  # maximum descent length per simulation; deeper descents back up the node's raw value
    sync_per_sim: bool = True  # read the max tree depth once per simulation to shorten the descent loop
    cuda_graph: bool = False  # capture/replay each simulation as a CUDA graph (implies sync_per_sim=False)


class BatchedSearch:
    def __init__(self, evaluator, n: int, cfg: SearchConfig, device, generator: torch.Generator | None = None,
                 rule: str = "count") -> None:
        self.eval = evaluator
        self.n = n
        self.cfg = cfg
        self.rule = check_rule(rule)  # the rule the tree expands under (uttt.rules)
        self.device = torch.device(device)
        self.gen = generator  # None: torch's global generator (the pre-PLAN6 behaviour)
        d = self.device
        M = cfg.n_sims + 1
        self.M = M
        self.idx = torch.arange(n, device=d)
        z = lambda *shape, dtype=torch.float32: torch.zeros(*shape, dtype=dtype, device=d)  # noqa: E731
        self.s_cells = z(n, M, 81, dtype=torch.int8)
        self.s_macro = z(n, M, 9, dtype=torch.int8)
        self.s_next = z(n, M, dtype=torch.int8)
        self.s_player = z(n, M, dtype=torch.int8)
        self.s_done = z(n, M, dtype=torch.bool)
        self.s_winner = z(n, M, dtype=torch.int8)
        self.s_legal = z(n, M, 81, dtype=torch.bool)
        self.s_value = z(n, M)
        self.prior = z(n, M, 81)
        self.logits = z(n, M, 81)
        self.children = torch.full((n, M, 81), -1, dtype=torch.long, device=d)
        self.N = z(n, M, 81)
        self.W = z(n, M, 81)
        self.node_N = z(n, M)
        self.table = table_of_considered_visits(cfg.m_considered, cfg.n_sims).to(d)
        self.path_nodes = z(n, cfg.depth_cap + 2, dtype=torch.long)
        self.path_actions = z(n, cfg.depth_cap + 2, dtype=torch.long)
        self._neg_inf = torch.full((n, 81), float("-inf"), device=d)
        # static per-search / per-simulation inputs (also the CUDA-graph inputs)
        self.g = z(n, 81)
        self.root_logits = z(n, 81)
        self.root_legal = z(n, 81, dtype=torch.bool)
        self.sched_col = z(n, dtype=torch.long)
        self.slot_t = z(n, dtype=torch.long)
        self.cap_hits = z(n)  # per search: simulations that descended depth_cap levels without expanding a node
        self._graphs: dict[int, torch.cuda.CUDAGraph] = {}
        self._graph_pool = None
        if cfg.cuda_graph:
            assert self.device.type == "cuda"
            self.cfg.sync_per_sim = False

    # ---- helpers -----------------------------------------------------------
    def _put_slot(self, mask, cells, macro, nb, player, done, winner, prior, logits, value) -> None:
        """Write the new node into slot self.slot_t (per game) where mask is set."""
        flat = self.idx * self.M + self.slot_t
        m1 = mask.unsqueeze(1)

        def put(store, new, m):
            v = store.view(self.n * self.M, *store.shape[2:])
            v.index_copy_(0, flat, torch.where(m, new.to(store.dtype), v[flat]))

        put(self.s_cells, cells, m1)
        put(self.s_macro, macro, m1)
        put(self.s_next, nb, mask)
        put(self.s_player, player, mask)
        put(self.s_done, done, mask)
        put(self.s_winner, winner, mask)
        put(self.s_legal, legal_mask(cells, macro, nb, done), m1)
        put(self.prior, prior, m1)
        put(self.logits, logits, m1)
        put(self.s_value, value, mask)

    def _sigma(self, node, P, legal, Nc, Qc):
        """mctx qtransform_completed_by_mix_value, rescaled over legal actions."""
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

    @staticmethod
    def _masked_logits(probs, legal):
        lg = torch.log(probs.clamp(min=1e-30)).masked_fill(~legal, float("-inf"))
        return lg - lg.max(1, keepdim=True).values

    # ---- one simulation (graph-capturable: no host syncs, no Python ints that vary per simulation) ----
    def _simulate(self, levels: int) -> torch.Tensor:
        """Descend `levels` levels, expand, evaluate, back up. Returns the leaf depth per game."""
        cfg, n, idx, d, M = self.cfg, self.n, self.idx, self.device, self.M
        gumbel = cfg.mode == "gumbel"
        node = torch.zeros(n, dtype=torch.long, device=d)
        depth = torch.zeros(n, dtype=torch.long, device=d)
        active = torch.ones(n, dtype=torch.bool, device=d)
        need_expand = torch.zeros(n, dtype=torch.bool, device=d)
        exp_parent = torch.zeros(n, dtype=torch.long, device=d)
        exp_action = torch.zeros(n, dtype=torch.long, device=d)

        for lvl in range(levels):
            active = active & ~self.s_done[idx, node]
            legal = self.s_legal[idx, node]
            Nc = self.N[idx, node]
            Qc = self.W[idx, node] / Nc.clamp(min=1)
            P = self.prior[idx, node]
            if gumbel:
                sigma = self._sigma(node, P, legal, Nc, Qc)
                if lvl == 0:
                    score = torch.where(Nc == self.sched_col.unsqueeze(1), self.g + self.root_logits + sigma, self._neg_inf)
                else:
                    pi = torch.softmax(self.logits[idx, node] + sigma, dim=1)
                    score = pi - Nc / (1 + Nc.sum(1, keepdim=True))
            else:
                Q = torch.where(Nc > 0, Qc, torch.full_like(P, cfg.fpu))
                score = Q + cfg.c_puct * P * self.node_N[idx, node].sqrt().unsqueeze(1) / (1 + Nc)
            score = torch.where(legal, score, self._neg_inf)
            a = score.argmax(1)
            child = self.children[idx, node, a]
            exists = child >= 0
            ex = active & ~exists
            exp_parent = torch.where(ex, node, exp_parent)
            exp_action = torch.where(ex, a, exp_action)
            need_expand |= ex
            self.path_actions[idx, depth] = torch.where(active, a, self.path_actions[idx, depth])
            active = active & exists
            node = torch.where(active, child, node)
            depth = depth + active.long()
            self.path_nodes[idx, depth] = torch.where(active, node, self.path_nodes[idx, depth])

        # ---- expansion ----------------------------------------------------
        pc = self.s_cells[idx, exp_parent]
        pm = self.s_macro[idx, exp_parent]
        pn = self.s_next[idx, exp_parent]
        pp = self.s_player[idx, exp_parent]
        pd = self.s_done[idx, exp_parent]
        pw = self.s_winner[idx, exp_parent]
        nc, nm, nn_, npl, nd, nw, _ = step_state(pc, pm, pn, pp, pd, pw, exp_action, self.rule)
        probs, value = self.eval(nc, nm, nn_, npl, nd)
        value = torch.where(nd, terminal_value(nw, npl, nd), value)
        nlegal = legal_mask(nc, nm, nn_, nd)
        self._put_slot(need_expand, nc, nm, nn_, npl, nd, nw, probs, self._masked_logits(probs, nlegal), value)
        cur = self.children[idx, exp_parent, exp_action]
        self.children[idx, exp_parent, exp_action] = torch.where(need_expand, self.slot_t, cur)
        depth = depth + need_expand.long()
        self.path_nodes[idx, depth] = torch.where(need_expand, self.slot_t, self.path_nodes[idx, depth])

        if levels >= cfg.depth_cap:
            self.cap_hits += ((depth >= levels) & ~need_expand & ~self.s_done[idx, self.path_nodes[idx, depth]]).float()
        leaf = self.path_nodes[idx, depth]
        leaf_done = self.s_done[idx, leaf]
        v_leaf = torch.where(leaf_done, terminal_value(self.s_winner[idx, leaf], self.s_player[idx, leaf], leaf_done), self.s_value[idx, leaf])
        v = torch.where(need_expand, value, v_leaf)

        # ---- backup (vectorised) --------------------------------------------
        L = levels + 1
        j = torch.arange(L, device=d).unsqueeze(0)
        nodes_j = self.path_nodes[:, :L]
        acts_j = self.path_actions[:, :L]
        dj = depth.unsqueeze(1)
        edge_valid = j < dj
        node_valid = j <= dj
        sign = torch.where((dj - j) % 2 == 0, 1.0, -1.0)
        flat_edge = torch.where(edge_valid, (idx.unsqueeze(1) * M + nodes_j) * 81 + acts_j, torch.zeros_like(nodes_j))
        self.N.view(-1).index_add_(0, flat_edge.flatten(), edge_valid.float().flatten())
        self.W.view(-1).index_add_(0, flat_edge.flatten(), (v.unsqueeze(1) * sign * edge_valid).flatten())
        flat_node = torch.where(node_valid, idx.unsqueeze(1) * M + nodes_j, torch.zeros_like(nodes_j))
        self.node_N.view(-1).index_add_(0, flat_node.flatten(), node_valid.float().flatten())
        return depth

    def _simulate_graphed(self, levels: int) -> None:
        graph = self._graphs.get(levels)
        if graph is None:
            snapshot = {k: getattr(self, k).clone() for k in ("s_cells", "s_macro", "s_next", "s_player", "s_done", "s_winner",
                                                             "s_legal", "s_value", "prior", "logits", "children", "N", "W",
                                                             "node_N", "path_nodes", "path_actions", "cap_hits")}
            s = torch.cuda.Stream(device=self.device)
            s.wait_stream(torch.cuda.current_stream(self.device))
            with torch.cuda.stream(s):
                for _ in range(2):
                    self._simulate(levels)
            torch.cuda.current_stream(self.device).wait_stream(s)
            graph = torch.cuda.CUDAGraph()
            if self._graph_pool is None:
                self._graph_pool = torch.cuda.graph_pool_handle()
            with torch.cuda.device(self.device), torch.cuda.graph(graph, pool=self._graph_pool):
                self._simulate(levels)
            for k, v in snapshot.items():
                getattr(self, k).copy_(v)
            self._graphs[levels] = graph
        graph.replay()

    # ---- search ------------------------------------------------------------
    @torch.no_grad()
    def search(self, cells, macro, next_board, player, done, winner, selfplay: bool, ply=0) -> SearchResult:
        """ply: int (all games at the same ply) or (n,) long tensor; only used for move sampling."""
        cfg, n, idx, d = self.cfg, self.n, self.idx, self.device
        gumbel = cfg.mode == "gumbel"
        self.children.fill_(-1)
        self.N.zero_()
        self.W.zero_()
        self.node_N.zero_()
        self.s_done.zero_()
        self.cap_hits.zero_()
        ones = torch.ones(n, dtype=torch.bool, device=d)

        # ---- root -------------------------------------------------------
        probs, value = self.eval(cells, macro, next_board, player, done)
        raw_probs = probs
        root_legal = legal_mask(cells, macro, next_board, done)
        self.root_legal.copy_(root_legal)
        if not gumbel and selfplay and cfg.noise_frac > 0:
            gamma = torch.distributions.Gamma(torch.full((1,), cfg.dirichlet_alpha, device=d), torch.ones(1, device=d))
            noise = gamma.sample((n, 81)).squeeze(-1) * root_legal
            noise = noise / noise.sum(1, keepdim=True).clamp(min=1e-9)
            probs = (1 - cfg.noise_frac) * probs + cfg.noise_frac * noise
        if cfg.root_prior_floor > 0:
            uni = root_legal.float() / root_legal.sum(1, keepdim=True).clamp(min=1)
            probs = (1 - cfg.root_prior_floor) * probs + cfg.root_prior_floor * uni
        self.root_logits.copy_(self._masked_logits(probs, root_legal))
        root_value0 = torch.where(done, terminal_value(winner, player, done), value)
        self.slot_t.zero_()
        self._put_slot(ones, cells, macro, next_board, player, done, winner, probs, self.root_logits, root_value0)
        self.node_N[:, 0] = 1
        if gumbel:
            if selfplay and cfg.gumbel_scale > 0:
                u = torch.rand(n, 81, device=d, generator=self.gen).clamp(min=1e-20)
                self.g.copy_((-torch.log(-torch.log(u))) * cfg.gumbel_scale)
            else:
                self.g.zero_()  # deterministic search: no draw, so it cannot advance anyone's RNG (PLAN6 E4)
            n_legal = root_legal.sum(1).clamp(max=cfg.m_considered)
            schedule = self.table[n_legal]  # (n, n_sims)
        else:
            self.g.zero_()
        max_depth_seen = 0

        for i in range(1, cfg.n_sims + 1):
            levels = min(i, cfg.depth_cap)
            if cfg.sync_per_sim:
                levels = min(levels, max_depth_seen + 1)
            self.slot_t.fill_(i)
            if gumbel:
                self.sched_col.copy_(schedule[:, i - 1])
            if cfg.cuda_graph:
                self._simulate_graphed(levels)
            else:
                depth = self._simulate(levels)
                if cfg.sync_per_sim:
                    max_depth_seen = max(max_depth_seen, int(depth.max().item()))

        # ---- root summary -------------------------------------------------
        root = torch.zeros(n, dtype=torch.long, device=d)
        Nc = self.N[:, 0]
        Qc = self.W[:, 0] / Nc.clamp(min=1)
        root_value = (self.s_value[:, 0] + self.W[:, 0].sum(1)) / self.node_N[:, 0]
        root_value = torch.where(done, root_value0, root_value)  # terminal roots: exact value, not diluted by visits
        if gumbel:
            sigma = self._sigma(root, self.prior[:, 0], root_legal, Nc, Qc)
            policy = torch.softmax((self.root_logits + sigma).masked_fill(~root_legal, float("-inf")), dim=1)
            top = Nc.max(1, keepdim=True).values
            action = torch.where((Nc == top) & root_legal, self.g + self.root_logits + sigma, self._neg_inf).argmax(1)
        else:
            policy = Nc / Nc.sum(1, keepdim=True).clamp(min=1)
            action = torch.where(root_legal, Nc, self._neg_inf).argmax(1)
        policy = torch.nan_to_num(policy, nan=0.0)
        if selfplay and cfg.sample_moves > 0 and cfg.temperature > 0:
            if torch.is_tensor(ply):
                sample = ply < cfg.sample_moves
            else:
                sample = torch.full((n,), ply < cfg.sample_moves, dtype=torch.bool, device=d)
            w = policy.pow(1.0 / cfg.temperature) * root_legal
            w = torch.where(w.sum(1, keepdim=True) > 0, w, root_legal.float())
            if cfg.sample_uniform > 0:
                w = w / w.sum(1, keepdim=True).clamp(min=1e-12)
                uni = root_legal.float() / root_legal.sum(1, keepdim=True).clamp(min=1)
                w = (1 - cfg.sample_uniform) * w + cfg.sample_uniform * uni
            w = w.clamp(min=1e-12) * root_legal + (~root_legal.any(1, keepdim=True)).float()  # finished games: any row (discarded)
            sampled = torch.multinomial(w, 1, generator=self.gen).squeeze(1)
            action = torch.where(sample, sampled, action)
        # diagnostics for the budget log (PLAN6 E8): how far the search moved the net's policy, and the Q spread it saw
        raw_kl = (policy * (torch.log(policy.clamp(min=1e-12)) - torch.log(raw_probs.clamp(min=1e-12)))).sum(1)
        visited = (Nc > 0) & root_legal
        big = torch.finfo(torch.float32).max
        q_range = torch.where(visited, Qc, torch.full_like(Qc, -big)).max(1).values - torch.where(visited, Qc, torch.full_like(Qc, big)).min(1).values
        q_range = torch.where(visited.any(1), q_range, torch.zeros_like(q_range))
        # clones: the result must not alias tree buffers that the next search() overwrites
        return SearchResult(policy=policy, action=action, visits=Nc.clone(), root_value=root_value, raw_value=self.s_value[:, 0].clone(),
                            cap_hits=self.cap_hits.clone(), raw_kl=raw_kl, q_range=q_range)
