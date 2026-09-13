"""Independent strength anchor: plain UCT with uniformly random playouts on bitboards (Numba),
the CodinGame-Legend recipe (PLAN2 §5 step 1b). Shares no code with uttt.search or the network:
its strength is a fixed function of the playouts per move, so it is an external yardstick.

    RolloutPlayer(playouts=100_000).act(batch)   # one move per unfinished game, games in parallel threads

Rules are re-implemented on 9-bit local boards (bit = cell, macro masks for X-won / O-won / full);
tests/test_rollout.py checks them move by move against uttt.game. The terminal rule ("count" or
"draw", uttt.rules) is an explicit argument, carried into the Numba kernels as a boolean flag, so
this anchor plays the same game as the net it is measured against. Tree: one node per playout,
children as linked lists, untried moves as an 81-bit mask; rewards in [0, 1] from the mover's
perspective; final move = most visited root child; no tree reuse between moves.
"""
from __future__ import annotations

import math

import numpy as np
import torch
from numba import njit, prange

from .rules import check_rule

# state layout (int64 array of length LEN)
MX, MO, MF, NB, PL, WN, DN, LEN = 18, 19, 20, 21, 22, 23, 24, 25  # [0:9] X boards, [9:18] O boards
WIN = np.array([0o7, 0o70, 0o700, 0o111, 0o222, 0o444, 0o421, 0o124], dtype=np.int64)
FULL9 = 0x1FF
HALF = 41  # moves 0..40 in the low mask word, 41..80 in the high one


def encode_states(cells: np.ndarray, macro: np.ndarray, next_board: np.ndarray, player: np.ndarray) -> np.ndarray:
    """(G, 81) cells / (G, 9) macro / (G,) next_board / (G,) player  ->  (G, LEN) bitboard states."""
    G = cells.shape[0]
    st = np.zeros((G, LEN), dtype=np.int64)
    bits = (1 << np.arange(9, dtype=np.int64))
    c = cells.reshape(G, 9, 9).astype(np.int64)
    st[:, 0:9] = ((c == 1) * bits).sum(-1)
    st[:, 9:18] = ((c == -1) * bits).sum(-1)
    m = macro.astype(np.int64)
    st[:, MX] = ((m == 1) * bits).sum(-1)
    st[:, MO] = ((m == -1) * bits).sum(-1)
    st[:, MF] = ((m == 2) * bits).sum(-1)
    st[:, NB] = next_board.astype(np.int64)
    st[:, PL] = player.astype(np.int64)
    return st


@njit(cache=True)
def _is_win(b):
    for k in range(8):
        if (b & WIN[k]) == WIN[k]:
            return True
    return False


@njit(cache=True)
def _popcount(v):
    n = 0
    while v:
        v &= v - 1
        n += 1
    return n


@njit(cache=True)
def _apply(st, m, draw_rule):
    """Play move m for the side to move; sets DN/WN when the game ends."""
    b = m // 9
    c = m - 9 * b
    p = st[PL]
    off = 0 if p == 1 else 9
    st[off + b] |= 1 << c
    if _is_win(st[off + b]):
        if p == 1:
            st[MX] |= 1 << b
            if _is_win(st[MX]):
                st[DN] = 1
                st[WN] = 1
        else:
            st[MO] |= 1 << b
            if _is_win(st[MO]):
                st[DN] = 1
                st[WN] = -1
    elif (st[b] | st[9 + b]) == FULL9:
        st[MF] |= 1 << b
    closed = st[MX] | st[MO] | st[MF]
    if st[DN] == 0 and closed == FULL9:
        st[DN] = 1
        st[WN] = 0  # the "draw" rule stops here
        if not draw_rule:
            x = _popcount(st[MX])
            o = _popcount(st[MO])
            st[WN] = 1 if x > o else (-1 if x < o else 0)
    st[NB] = c if ((closed >> c) & 1) == 0 else -1
    st[PL] = -p


@njit(cache=True)
def _legal(st, out):
    """Fill `out` with the legal moves; return their number (0 if the game is over)."""
    if st[DN] == 1:
        return 0
    n = 0
    closed = st[MX] | st[MO] | st[MF]
    nb = st[NB]
    if nb >= 0 and ((closed >> nb) & 1) == 0:
        empty = ~(st[nb] | st[9 + nb]) & FULL9
        for c in range(9):
            if (empty >> c) & 1:
                out[n] = 9 * nb + c
                n += 1
    else:
        for b in range(9):
            if (closed >> b) & 1:
                continue
            empty = ~(st[b] | st[9 + b]) & FULL9
            for c in range(9):
                if (empty >> c) & 1:
                    out[n] = 9 * b + c
                    n += 1
    return n


@njit(cache=True)
def _mask_of(buf, n):
    lo = 0
    hi = 0
    for i in range(n):
        m = buf[i]
        if m < HALF:
            lo |= 1 << m
        else:
            hi |= 1 << (m - HALF)
    return lo, hi


@njit(cache=True)
def _pop_random(LO, HI, node):
    """Remove and return a uniformly random untried move of `node`."""
    k = np.random.randint(_popcount(LO[node]) + _popcount(HI[node]))
    lo = LO[node]
    while lo:
        low = lo & -lo
        if k == 0:
            LO[node] ^= low
            return int(math.log2(low))
        k -= 1
        lo ^= low
    hi = HI[node]
    while hi:
        low = hi & -hi
        if k == 0:
            HI[node] ^= low
            return int(math.log2(low)) + HALF
        k -= 1
        hi ^= low
    return -1


@njit(cache=True)
def _uct_search(root, n_playouts, c_uct, seed, draw_rule):
    """Returns (best move, its win rate for the root player, root child visit counts over 81 moves)."""
    np.random.seed(seed)
    M = n_playouts + 2
    N = np.zeros(M, np.int32)
    W = np.zeros(M, np.float64)
    MV = np.zeros(M, np.int16)
    MOVER = np.zeros(M, np.int8)
    PAR = np.full(M, -1, np.int32)
    FIRST = np.full(M, -1, np.int32)
    NEXT = np.full(M, -1, np.int32)
    LO = np.zeros(M, np.int64)
    HI = np.zeros(M, np.int64)
    buf = np.zeros(81, np.int64)
    st = root.copy()
    LO[0], HI[0] = _mask_of(buf, _legal(st, buf))
    n_nodes = 1
    for _ in range(n_playouts):
        st[:] = root
        node = 0
        while st[DN] == 0:
            if LO[node] != 0 or HI[node] != 0:  # expand one untried child, then play out from it
                m = _pop_random(LO, HI, node)
                child = n_nodes
                n_nodes += 1
                MV[child] = m
                MOVER[child] = st[PL]
                PAR[child] = node
                NEXT[child] = FIRST[node]
                FIRST[node] = child
                _apply(st, m, draw_rule)
                LO[child], HI[child] = _mask_of(buf, _legal(st, buf))
                node = child
                break
            best = -1
            best_u = -1e18
            log_n = math.log(N[node])
            ch = FIRST[node]
            while ch >= 0:
                u = W[ch] / N[ch] + c_uct * math.sqrt(log_n / N[ch])
                if u > best_u:
                    best_u = u
                    best = ch
                ch = NEXT[ch]
            _apply(st, MV[best], draw_rule)
            node = best
        while st[DN] == 0:  # random playout
            n = _legal(st, buf)
            _apply(st, buf[np.random.randint(n)], draw_rule)
        r = 1.0 if st[WN] == 1 else (0.0 if st[WN] == -1 else 0.5)  # X's reward
        while node >= 0:
            N[node] += 1
            if node > 0:
                W[node] += r if MOVER[node] == 1 else 1.0 - r
            node = PAR[node]
    visits = np.zeros(81, np.int64)
    best = -1
    best_n = -1
    ch = FIRST[0]
    while ch >= 0:
        visits[MV[ch]] = N[ch]
        if N[ch] > best_n:
            best_n = N[ch]
            best = ch
        ch = NEXT[ch]
    if best < 0:
        return -1, 0.5, visits
    return int(MV[best]), W[best] / N[best], visits


@njit(parallel=True, cache=True)
def _search_batch(states, active, n_playouts, c_uct, seeds, moves, values, draw_rule):
    for g in prange(states.shape[0]):
        if active[g]:
            m, v, _ = _uct_search(states[g], n_playouts, c_uct, seeds[g], draw_rule)
            moves[g] = m
            values[g] = v


class RolloutPlayer:
    """Batch player for uttt.arena / uttt.openings: one independent UCT search per unfinished game,
    games spread over all CPU threads. `playouts` sets the strength; results are reproducible for a seed."""

    def __init__(self, playouts: int = 100_000, c_uct: float = 1.4, seed: int = 0, rule: str = "count") -> None:
        self.playouts = playouts
        self.c_uct = c_uct
        self.seed = seed
        self.rule = check_rule(rule)
        self.calls = 0
        self.last_values = None

    def act(self, g) -> torch.Tensor:
        cells, macro = g.cells.cpu().numpy(), g.macro.cpu().numpy()
        nb, player, done = g.next_board.cpu().numpy(), g.player.cpu().numpy(), g.done.cpu().numpy()
        states = encode_states(cells, macro, nb, player)
        G = states.shape[0]
        seeds = (np.arange(G, dtype=np.int64) * 1_000_003 + self.calls * 7919 + self.seed) & 0x7FFFFFFF
        moves = np.zeros(G, dtype=np.int64)
        values = np.zeros(G, dtype=np.float64)
        _search_batch(states, ~done, self.playouts, self.c_uct, seeds, moves, values, self.rule == "draw")
        self.calls += 1
        self.last_values = values
        return torch.from_numpy(np.maximum(moves, 0)).to(g.cells.device)


def search_position(cells, macro, next_board, player, playouts: int = 100_000, c_uct: float = 1.4, seed: int = 0,
                    rule: str = "count"):
    """Single-position convenience: (best move, win rate for the mover, visits over 81 moves)."""
    st = encode_states(np.asarray(cells)[None], np.asarray(macro)[None], np.array([next_board]), np.array([player]))[0]
    return _uct_search(st, playouts, c_uct, seed, check_rule(rule) == "draw")
