"""Evaluation matches between evaluators (network or baseline) with batched search.

Every entry point takes the *evaluation* rule explicitly (uttt.rules; default "count"): the players'
search trees and the game being played must agree, and neither is inferred from a checkpoint."""
from __future__ import annotations

from dataclasses import dataclass

import torch

from dataclasses import asdict

from .batch import BatchUTTT
from .mcts import MCTSConfig
from .search import BatchedSearch, SearchConfig


@dataclass
class MatchResult:
    wins: int
    draws: int
    losses: int

    @property
    def n(self) -> int:
        return self.wins + self.draws + self.losses

    @property
    def score(self) -> float:
        return (self.wins + 0.5 * self.draws) / max(self.n, 1)

    def __str__(self) -> str:
        return f"+{self.wins} ={self.draws} -{self.losses} ({100 * self.score:.1f}%)"

    def __add__(self, o: "MatchResult") -> "MatchResult":
        return MatchResult(self.wins + o.wins, self.draws + o.draws, self.losses + o.losses)


class RandomPlayer:
    """Uniform random mover (not an evaluator; used directly by play_games)."""

    def __init__(self, device) -> None:
        self.device = device

    def act(self, g: BatchUTTT) -> torch.Tensor:
        m = g.legal_mask().float() + 1e-9
        return torch.multinomial(m, 1).squeeze(1)


class SearchPlayer:
    """Search-based player (v2 search; a plain MCTSConfig is upgraded to SearchConfig)."""

    def __init__(self, evaluator, n: int, cfg: MCTSConfig, device, rule: str = "count") -> None:
        if not isinstance(cfg, SearchConfig):
            cfg = SearchConfig(**asdict(cfg))
        self.mcts = BatchedSearch(evaluator, n, cfg, device, rule=rule)

    def act(self, g: BatchUTTT) -> torch.Tensor:
        return self.mcts.search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False).action


class PhasedSearchPlayer:
    """Search budget by game phase: schedule {ply: sims} (sorted by ply) applied to the batch's current ply,
    which is uniform across the batch in lock-step / paired play. One BatchedSearch per distinct budget."""

    def __init__(self, evaluator, n: int, cfg: SearchConfig, schedule: dict, device, rule: str = "count") -> None:
        from dataclasses import replace

        self.schedule = sorted(schedule.items())
        self.searches = {s: BatchedSearch(evaluator, n, replace(cfg, n_sims=s, depth_cap=min(s, cfg.depth_cap)), device, rule=rule)
                         for s in {v for _, v in self.schedule}}

    def sims_at(self, ply: int) -> int:
        return max([v for k, v in self.schedule if ply >= k] or [self.schedule[0][1]])

    def act(self, g: BatchUTTT) -> torch.Tensor:
        ply = int(g.move_count.max())
        return self.searches[self.sims_at(ply)].search(g.cells, g.macro, g.next_board, g.player, g.done, g.winner, selfplay=False).action


@torch.no_grad()
def play_games(px, po, n: int, device, opening_random_plies: int = 0, rule: str = "count") -> MatchResult:
    """n lock-step games with px moving as X and po as O. Result from X's perspective.

    opening_random_plies > 0 randomises the first plies so deterministic players
    do not replay one identical game n times.
    """
    g = BatchUTTT(n, device, rule)
    rnd = RandomPlayer(device)
    ply = 0
    while not bool(g.done.all()):
        if ply < opening_random_plies:
            moves = rnd.act(g)
        else:
            moves = (px if ply % 2 == 0 else po).act(g)
        g.step(moves)
        ply += 1
    w = int((g.winner == 1).sum())
    l = int((g.winner == -1).sum())
    return MatchResult(w, n - w - l, l)


def match(pa_factory, pb_factory, n: int, device, opening_random_plies: int = 2, rule: str = "count") -> MatchResult:
    """Side-swapped match: A vs B with n games each way. Result from A's perspective."""
    r1 = play_games(pa_factory(), pb_factory(), n, device, opening_random_plies, rule)
    r2 = play_games(pb_factory(), pa_factory(), n, device, opening_random_plies, rule)
    return r1 + MatchResult(r2.losses, r2.draws, r2.wins)
