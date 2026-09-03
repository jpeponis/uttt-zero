"""A legible surrogate player (PLAN5 §3 B6): a linear model over hand-written, per-move features imitates the
network's search policy, and a linear model over position features imitates its value. Everything is computed in
torch so the surrogate can sit inside the batched search like a network would.

    feats = move_features(cells, macro, next_board, player)        # (n, 81, F) from the mover's view, illegal rows zero
    pos = position_features(cells, macro, next_board, player)      # (n, G)
    ev = SurrogateEvaluator(w_policy, w_value, b_value, device)     # policy = softmax over legal of feats @ w_policy
    ev.save(path) / SurrogateEvaluator.load(path, device)

The point is not strength but a number: the surrogate's Elo gap to the network at equal sims is the share of the
network's play that the named features do not capture (tools/distill.py).
"""
from __future__ import annotations

import json

import torch

from .batch import FULL, consts, legal_mask, step_state

MOVE_FEATURES = [
    "wins_board", "fills_board", "wins_game", "ends_game_lost", "ends_game_draw",
    "gives_free_move", "opp_local_win_next", "opp_macro_win_next", "opp_threat_boards_next",
    "my_threats_after", "opp_threats_after", "my_local_threats_after", "count_margin_after", "dead_boards_after",
    "self_send", "send_to_centre", "send_to_corner", "cell_centre", "cell_corner", "target_empties_after",
]
POSITION_FEATURES = [
    "free_move", "count_margin", "open_boards", "empties", "is_X", "threats_for", "threats_against",
    "dead_boards", "local_win_now", "local_threat_against", "macro_win_now", "full_boards",
]


def _line_counts(cells, macro, who):
    """Per board: number of lines with two stones of `who` and an empty third (n, 9); and whether the board is open."""
    n = cells.shape[0]
    lines = consts(cells.device)["LINES"]
    b = cells.view(n, 9, 9)[:, :, lines]  # (n, 9, 8, 3)
    w = who.view(n, 1, 1, 1)
    two = ((b == w).sum(-1) == 2) & ((b == 0).sum(-1) == 1)
    return two.sum(-1) * (macro == 0)


def _macro_threats(macro, who):
    lines = consts(macro.device)["LINES"]
    ml = macro[:, lines]  # (n, 8, 3)
    w = who.view(-1, 1, 1)
    return (((ml == w).sum(-1) == 2) & ((ml == 0).sum(-1) == 1)).sum(-1)


_CACHE: dict = {}  # per-device constants, created outside any CUDA-graph capture


def _consts(device):
    key = str(device)
    if key not in _CACHE:
        lines = consts(device)["LINES"]  # (8, 3)
        other = torch.tensor([[1, 2], [0, 2], [0, 1]], dtype=torch.long, device=device)  # the other two slots of a line, per slot
        _CACHE[key] = {"other": other, "lines24": lines.reshape(1, 24)}
    return _CACHE[key]


def _completes(macro, who):
    """Per board: winning it now would complete a macro line for `who` (n, 9). No host syncs (CUDA-graph safe)."""
    lines = consts(macro.device)["LINES"]  # (8, 3)
    k = _consts(macro.device)
    n = macro.shape[0]
    mine = (macro == who.view(n, 1)).float()
    ml = mine[:, lines]  # (n, 8, 3)
    both = ml[:, :, k["other"][:, 0]] * ml[:, :, k["other"][:, 1]]  # (n, 8, 3): the other two slots of slot j are mine
    out = torch.zeros(n, 9, device=macro.device).scatter_add_(1, k["lines24"].expand(n, 24), both.reshape(n, 24))
    return out > 0


def _dead(cells, macro):
    n = cells.shape[0]
    lines = consts(cells.device)["LINES"]
    b = cells.view(n, 9, 9)[:, :, lines]
    blocked = ((b == 1).any(-1) & (b == -1).any(-1)).all(-1)
    return (blocked & (macro == 0)).sum(1)


def _allowed(macro, next_board):
    n = macro.shape[0]
    open_b = macro == 0
    nb = next_board.long()
    nb0 = nb.clamp(min=0)
    sent_open = (nb >= 0) & open_b[torch.arange(n, device=macro.device), nb0]
    onehot = torch.nn.functional.one_hot(nb0, 9).bool()
    return torch.where(sent_open.unsqueeze(1), onehot, open_b), sent_open


@torch.no_grad()
def position_features(cells, macro, next_board, player) -> torch.Tensor:
    n = cells.shape[0]
    p = player.view(n, 1)
    allowed, sent_open = _allowed(macro, next_board)
    open_b = macro == 0
    mine, theirs = macro == p, macro == -p
    my_two = _line_counts(cells, macro, player) > 0
    op_two = _line_counts(cells, macro, -player) > 0
    empties = ((cells.view(n, 9, 9) == 0) & open_b.unsqueeze(2)).sum((1, 2))
    f = [
        (~sent_open).float(),
        (mine.sum(1) - theirs.sum(1)).float(),
        open_b.sum(1).float(),
        empties.float() / 10,
        (player == 1).float(),
        _macro_threats(macro, player).float(),
        _macro_threats(macro, -player).float(),
        _dead(cells, macro).float(),
        (my_two & allowed).any(1).float(),
        op_two.any(1).float(),
        (my_two & allowed & _completes(macro, player)).any(1).float(),
        (macro == FULL).sum(1).float(),
    ]
    return torch.stack(f, 1)


@torch.no_grad()
def move_features(cells, macro, next_board, player) -> torch.Tensor:
    """(n, 81, F): features of the position after each move, from the mover's view; zero for illegal moves."""
    n = cells.shape[0]
    d = cells.device
    legal = legal_mask(cells, macro, next_board)
    rep = lambda t: t.repeat_interleave(81, dim=0)  # noqa: E731
    moves = torch.arange(81, device=d).repeat(n)
    done0 = torch.zeros(n * 81, dtype=torch.bool, device=d)
    win0 = torch.zeros(n * 81, dtype=torch.int8, device=d)
    c2, m2, nb2, p2, done2, win2, _ = step_state(rep(cells), rep(macro), rep(next_board), rep(player), done0, win0, moves)
    p = rep(player)  # the mover, from whose view everything is scored
    idx = torch.arange(n * 81, device=d)
    b, c = moves // 9, moves % 9
    won_board = m2[idx, b] == p
    filled = m2[idx, b] == FULL
    free_after = (nb2 < 0) & ~done2
    allowed2, _ = _allowed(m2, nb2)
    opp_two = _line_counts(c2, m2, -p)  # boards where the opponent (now to move) has a two-in-line
    opp_can_win_board = ((opp_two > 0) & allowed2).any(1) & ~done2
    opp_can_win_game = ((opp_two > 0) & allowed2 & _completes(m2, -p)).any(1) & ~done2
    my_two = _line_counts(c2, m2, p)
    mine2, theirs2 = m2 == p.view(-1, 1), m2 == -p.view(-1, 1)
    tgt = nb2.long().clamp(min=0)
    tgt_empties = ((c2.view(n * 81, 9, 9)[idx, tgt] == 0).sum(1).float() / 9) * (nb2 >= 0).float()
    f = [
        won_board.float(), filled.float(), (done2 & (win2 == p)).float(), (done2 & (win2 == -p)).float(), (done2 & (win2 == 0)).float(),
        free_after.float(), opp_can_win_board.float(), opp_can_win_game.float(), ((opp_two > 0) & allowed2).sum(1).float(),
        _macro_threats(m2, p).float(), _macro_threats(m2, -p).float(), (my_two > 0).sum(1).float(),
        (mine2.sum(1) - theirs2.sum(1)).float(), _dead(c2, m2).float(),
        (c == b).float(), (c == 4).float(), ((c == 0) | (c == 2) | (c == 6) | (c == 8)).float(),
        (c == 4).float(), ((c == 0) | (c == 2) | (c == 6) | (c == 8)).float(), tgt_empties,
    ]
    F = torch.stack(f, 1).view(n, 81, len(f))
    return F * legal.unsqueeze(2).float()


class SurrogateEvaluator:
    def __init__(self, w_policy, w_value, b_value, device, mu=None, sd=None) -> None:
        self.device = torch.device(device)
        self.w_policy = torch.as_tensor(w_policy, dtype=torch.float32, device=self.device)
        self.w_value = torch.as_tensor(w_value, dtype=torch.float32, device=self.device)
        self.b_value = float(b_value)
        self.mu = torch.zeros(len(POSITION_FEATURES), device=self.device) if mu is None else torch.as_tensor(mu, dtype=torch.float32, device=self.device)
        self.sd = torch.ones(len(POSITION_FEATURES), device=self.device) if sd is None else torch.as_tensor(sd, dtype=torch.float32, device=self.device)

    @torch.no_grad()
    def __call__(self, cells, macro, next_board, player, done):
        legal = legal_mask(cells, macro, next_board, done)
        F = move_features(cells, macro, next_board, player)
        logits = (F @ self.w_policy).masked_fill(~legal, float("-inf"))
        probs = torch.nan_to_num(torch.softmax(logits, dim=1), nan=0.0)
        G = (position_features(cells, macro, next_board, player) - self.mu) / self.sd
        value = torch.tanh(G @ self.w_value + self.b_value)
        return probs, torch.where(done, torch.zeros_like(value), value)

    def save(self, path: str, meta: dict | None = None) -> None:
        rec = {"move_features": MOVE_FEATURES, "position_features": POSITION_FEATURES, "w_policy": self.w_policy.tolist(),
               "w_value": self.w_value.tolist(), "b_value": self.b_value, "mu": self.mu.tolist(), "sd": self.sd.tolist(), "meta": meta or {}}
        with open(path, "w") as f:
            json.dump(rec, f, indent=1)

    @classmethod
    def load(cls, path: str, device) -> "SurrogateEvaluator":
        r = json.load(open(path))
        return cls(r["w_policy"], r["w_value"], r["b_value"], device, r.get("mu"), r.get("sd"))
