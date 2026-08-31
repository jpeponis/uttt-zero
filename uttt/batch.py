"""Batched (vectorised, torch) implementation of the same rules as uttt.game.

Every tensor has a leading batch dimension n. Games that are finished ignore
further step() calls, so a fixed batch can be stepped in lockstep until all
games are done. Move index convention is identical to uttt.game:
m = 9*board + cell (board/cell row-major within their 3x3 grids).

Also provides the neural-network encoding (spatial 9x9 planes in grid order,
from the side-to-move's perspective) and the 8 dihedral symmetries of the game
as cell/board permutations.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F

FULL = 2
N_PLANES = 7  # base encoding
N_PLANES_EXTRA = 9  # + first-player plane + won-board count difference (encode(..., extra=True))

LINES = torch.tensor(
    [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)],
    dtype=torch.long,
)


def _grid_to_cell(g: int) -> int:
    row, col = divmod(g, 9)
    R, r = divmod(row, 3)
    C, c = divmod(col, 3)
    return 9 * (3 * R + C) + (3 * r + c)


# PERM[g] = engine cell index sitting at 9x9 grid position g (row-major).
PERM = torch.tensor([_grid_to_cell(g) for g in range(81)], dtype=torch.long)
INV_PERM = torch.empty(81, dtype=torch.long)
INV_PERM[PERM] = torch.arange(81)
BOARD_OF_CELL = torch.arange(81) // 9  # engine order
BOARD_OF_GRID = BOARD_OF_CELL[PERM]

# ---- dihedral symmetries -------------------------------------------------
# Each symmetry acts on a 3x3 coordinate (i, j) -> (i', j'); it is applied to
# the macro coordinate (R, C) and the micro coordinate (r, c) simultaneously,
# which is the same thing as applying it to the whole 9x9 grid.
_D4 = [
    lambda i, j: (i, j),  # identity
    lambda i, j: (j, 2 - i),  # rot 90
    lambda i, j: (2 - i, 2 - j),  # rot 180
    lambda i, j: (2 - j, i),  # rot 270
    lambda i, j: (i, 2 - j),  # flip left-right
    lambda i, j: (2 - i, j),  # flip up-down
    lambda i, j: (j, i),  # transpose
    lambda i, j: (2 - j, 2 - i),  # anti-transpose
]


def _sym_perms():
    cell = torch.empty(8, 81, dtype=torch.long)
    board = torch.empty(8, 9, dtype=torch.long)
    for s, f in enumerate(_D4):
        for b in range(9):
            R, C = divmod(b, 3)
            R2, C2 = f(R, C)
            board[s, b] = 3 * R2 + C2
            for c in range(9):
                r, cc = divmod(c, 3)
                r2, c2 = f(r, cc)
                cell[s, 9 * b + c] = 9 * (3 * R2 + C2) + (3 * r2 + c2)
    return cell, board


SYM_CELL, SYM_BOARD = _sym_perms()  # SYM_CELL[s][m] = image of move m under symmetry s
SYM_CELL_INV = torch.empty_like(SYM_CELL)
SYM_BOARD_INV = torch.empty_like(SYM_BOARD)
for _s in range(8):
    SYM_CELL_INV[_s, SYM_CELL[_s]] = torch.arange(81)
    SYM_BOARD_INV[_s, SYM_BOARD[_s]] = torch.arange(9)

_CONSTS = {"LINES": LINES, "PERM": PERM, "BOARD_OF_GRID": BOARD_OF_GRID, "SYM_CELL_INV": SYM_CELL_INV,
           "SYM_BOARD_INV": SYM_BOARD_INV, "SYM_BOARD": SYM_BOARD}
_DEV_CACHE: dict = {}


def consts(device) -> dict:
    """Constant index tensors resident on `device` (cached: no per-call host->device copies,
    which also keeps these functions CUDA-graph capturable)."""
    key = str(device)
    c = _DEV_CACHE.get(key)
    if c is None:
        c = {k: v.to(device) for k, v in _CONSTS.items()}
        _DEV_CACHE[key] = c
    return c


class BatchUTTT:
    def __init__(self, n: int, device: torch.device | str = "cpu") -> None:
        self.n = n
        self.device = torch.device(device)
        d = self.device
        self.cells = torch.zeros(n, 81, dtype=torch.int8, device=d)
        self.macro = torch.zeros(n, 9, dtype=torch.int8, device=d)
        self.next_board = torch.full((n,), -1, dtype=torch.int8, device=d)
        self.player = torch.ones(n, dtype=torch.int8, device=d)
        self.move_count = torch.zeros(n, dtype=torch.int16, device=d)
        self.done = torch.zeros(n, dtype=torch.bool, device=d)
        self.winner = torch.zeros(n, dtype=torch.int8, device=d)
        self.end_reason = torch.zeros(n, dtype=torch.int8, device=d)  # 0 ongoing 1 line 2 count 3 draw
        self._lines = LINES.to(d)
        self._idx = torch.arange(n, device=d)

    # ---- state management ------------------------------------------------
    def clone(self) -> "BatchUTTT":
        g = BatchUTTT.__new__(BatchUTTT)
        g.n, g.device, g._lines, g._idx = self.n, self.device, self._lines, self._idx
        for k in ("cells", "macro", "next_board", "player", "move_count", "done", "winner", "end_reason"):
            setattr(g, k, getattr(self, k).clone())
        return g

    def reset_where(self, mask: torch.Tensor) -> None:
        """Reset the games selected by boolean mask to the initial position."""
        self.cells[mask] = 0
        self.macro[mask] = 0
        self.next_board[mask] = -1
        self.player[mask] = 1
        self.move_count[mask] = 0
        self.done[mask] = False
        self.winner[mask] = 0
        self.end_reason[mask] = 0

    def state_tuple(self):
        return self.cells, self.macro, self.next_board, self.player, self.done

    # ---- rules -----------------------------------------------------------
    def legal_mask(self) -> torch.Tensor:
        return legal_mask(self.cells, self.macro, self.next_board, self.done)

    def step(self, moves: torch.Tensor) -> None:
        """Apply one move per game (long tensor, shape (n,)). Finished games are untouched."""
        active = ~self.done
        out = step_state(self.cells, self.macro, self.next_board, self.player, self.done, self.winner, moves)
        self.cells, self.macro, self.next_board, self.player, self.done, self.winner, reason = out
        self.move_count += active.to(torch.int16)
        self.end_reason = torch.where(active & self.done, reason, self.end_reason)

    def observation(self) -> torch.Tensor:
        return encode(self.cells, self.macro, self.next_board, self.player, self.done)


# ---- functional forms (usable on stored replay / tree states) --------------
def step_state(cells, macro, next_board, player, done, winner, moves):
    """Pure batched rules step. Returns new (cells, macro, next_board, player, done, winner, reason).

    reason is 0 unless the game ended on this step (1 line, 2 count, 3 draw).
    Games with done=True are returned unchanged.
    """
    n = cells.shape[0]
    d = cells.device
    idx = torch.arange(n, device=d)
    lines = consts(d)["LINES"]
    active = ~done
    moves = moves.long()
    b = moves // 9
    c = moves % 9
    p = player

    cells = cells.clone()
    macro = macro.clone()
    cells[idx, moves] = torch.where(active, p, cells[idx, moves])  # no boolean indexing: no host sync

    local = cells.view(n, 9, 9)[idx, b]  # (n, 9)
    won = (local[:, lines] == p.view(n, 1, 1)).all(-1).any(-1)
    full = (local != 0).all(-1)
    status = torch.where(won, p, torch.where(full, torch.full_like(p, FULL), torch.zeros_like(p)))
    macro[idx, b] = torch.where(active, status, macro[idx, b])

    won_only = macro * (macro.abs() == 1)
    mline = (won_only[:, lines] == p.view(n, 1, 1)).all(-1).any(-1)
    all_closed = (macro != 0).all(1)
    diff = (macro == 1).sum(1) - (macro == -1).sum(1)
    count_winner = torch.sign(diff).to(torch.int8)
    newly_done = active & (mline | all_closed)
    winner = torch.where(newly_done, torch.where(mline, p, count_winner), winner)
    reason = torch.where(mline, 1, torch.where(count_winner != 0, 2, 3)).to(torch.int8)
    reason = torch.where(newly_done, reason, torch.zeros_like(reason))
    done = done | newly_done

    target_closed = macro[idx, c] != 0
    nb = torch.where(target_closed, torch.full_like(c, -1), c).to(torch.int8)
    next_board = torch.where(active, nb, next_board)
    player = torch.where(active, -p, p)
    return cells, macro, next_board, player, done, winner, reason


def terminal_value(winner, player, done) -> torch.Tensor:
    """Game value in [-1, 1] from the side-to-move's perspective; 0 for ongoing games."""
    return torch.where(done, (winner * player).float(), torch.zeros(winner.shape, device=winner.device))
def legal_mask(cells, macro, next_board, done=None) -> torch.Tensor:
    open_board = macro == 0  # (n, 9)
    nb = next_board.long()
    nb0 = nb.clamp(min=0)
    sent_open = (nb >= 0) & open_board.gather(1, nb0.unsqueeze(1)).squeeze(1)
    one_hot = F.one_hot(nb0, 9).bool()
    allowed = torch.where(sent_open.unsqueeze(1), one_hot, open_board)
    mask = (cells == 0) & allowed.repeat_interleave(9, dim=1)
    if done is not None:
        mask = mask & ~done.unsqueeze(1)
    return mask


def encode(cells, macro, next_board, player, done=None, extra: bool = False) -> torch.Tensor:
    """(n, N_PLANES, 9, 9) float32 planes from the side-to-move's perspective, grid order.

    0 own stones, 1 opponent stones, 2 boards won by self, 3 boards won by
    opponent, 4 boards closed full/drawn, 5 legal-move mask, 6 all ones.
    extra=True appends 7: side to move is X (first player), 8: (boards won by self
    - boards won by opponent) / 4, broadcast — the quantity the most-boards tiebreak is decided by.
    """
    n = cells.shape[0]
    c = consts(cells.device)
    perm = c["PERM"]
    bog = c["BOARD_OF_GRID"]
    p = player.view(n, 1)
    grid = cells[:, perm]
    mg = macro[:, bog]
    legal = legal_mask(cells, macro, next_board, done)[:, perm]
    planes = [grid == p, grid == -p, mg == p, mg == -p, mg == FULL, legal, torch.ones_like(legal)]
    if extra:
        mp = macro.view(n, 9)
        diff = ((mp == p).sum(1, keepdim=True) - (mp == -p).sum(1, keepdim=True)).float() / 4
        planes += [(p == 1).expand(n, 81), diff.expand(n, 81)]
    obs = torch.stack([t.float() for t in planes], dim=1)
    return obs.view(n, len(planes), 9, 9)


def apply_symmetry(s: int, cells, macro, next_board, policy=None):
    """Return the state (and optional policy over 81 engine-order moves) transformed by symmetry s.

    Convention: new_cells[SYM_CELL[s][m]] = cells[m], i.e. a stone on m moves to its image.
    """
    c = consts(cells.device)
    cp = c["SYM_CELL_INV"][s]
    bp = c["SYM_BOARD_INV"][s]
    new_cells = cells[:, cp]
    new_macro = macro[:, bp]
    sb = c["SYM_BOARD"][s]
    new_next = torch.where(next_board >= 0, sb[next_board.long().clamp(min=0)].to(next_board.dtype), next_board)
    if policy is None:
        return new_cells, new_macro, new_next
    return new_cells, new_macro, new_next, policy[:, cp]
