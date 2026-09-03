# Five positions the searching agent gets wrong

*PLAN5 §4 C3. The hard puzzles of `suites/puzzles_v2_dev.npz`: positions from strong play
(deep8_c1_300's late games, ≤ 14 empties) in which the +242 net's raw policy **and** its
64-simulation search both choose a move that loses exact value. Five of 6000 positions.
Everything below except the commentary is the solver's: `tools/annotate.py` prints the
board, the exact value after every legal move, and the best line after the best move and
after the net's move (`docs/positions_raw.md` is that output verbatim).*

*Reading the diagrams: the board is nine small boards in a 3 × 3 grid, `X` / `O` / `.`;
the `macro` block is who owns each small board (`.` open). The value map has one symbol
per legal move: `+` the mover wins with best play from there, `=` draws, `-` loses.
Move numbers are `m = 9·board + cell`, boards and cells row-major from the top left.*

---

## 1. The "safe" move loses; both winning moves hand X a free move

Game 373, ply 47. **O to move, sent to the bottom-right board.** Exact value for O: **+1**.
The net plays 80 (bottom-right cell of that board); the solver says only 74 or 77 win.

```
O O O  X O X  . O X        macro
. . .  X X X  O X .        O X X
. X X  . X .  X . O        X . X
                           X O .
X X X  . O O  X O O
O . O  . X O  . X O        value after each move
. . .  O O .  . X X        (bottom-right board only):
                            - - +
. . .  O O .  . . .         - . +
X X X  O . O  . O .         - . -
. . .  O X .  . X .
```

X owns five boards and threatens to win the game with either the centre board (two lines:
the middle row and the anti-diagonal) or the bottom-right board (the right column). O owns
two and has one line left: the main diagonal, which needs *both* the centre and the
bottom-right board. The centre board is O's for the taking (44 completes O's right column
there). So the whole game is: can O win both open boards before X wins either?

The net's 80 keeps X confined to the bottom-right board, which looks prudent — every other
cell sends X to a closed board and gives X a free move. But confined X simply plays 72 (the
board's top-left corner), sending O to a closed board, and now *X* has the tempo in the one
board O must win. The solver's line 80, 72, 36, 74, 73, 75, 77, 78 shows O unable even to
cash the centre at once (44 would send X straight back into the bottom-right board): O
fences in the centre with 36, X takes 74 — the very cell O needed — and after the forced
exchanges 73, 75, 77 X completes the left column of the bottom-right board with 78. That
board is X's, and with it X's macro right column: X wins by a line.

74 gives X a free move — and X has nothing to do with it. Neither open board can be won by
X in one move, and O's 44 is still hanging. In the line 74, 36, 44, 72, 75, 73, 77 X uses
the free move to start a threat in the centre, O takes the centre anyway, and the stone O
already placed on 74 turns the bottom-right board into O's with 77 (a completed middle row).
O wins on the diagonal. *The free move was harmless because X had no target for it; the
tempo in the last open board was the thing worth keeping.* This is the "gives_free_move"
motif from the other side: the net over-prices confinement.

## 2. One winning move, and it is a quiet one

Game 511, ply 44. **X to move, free move.** Exact value: **+1**. The net plays 78 (bottom-
right board, bottom-left cell), which only draws; the single winning move is 56.

```
O O X  X X X  O . X        macro
X . X  . . .  X . O        X X .
. . X  . O .  O X O        O O X
                           . O .
X O .  . . O  . . X
X O .  . X O  O . X        value map (open boards):
. O .  . . O  . . X        top-right      bottom-left    bottom-right
                            . - .          - - +          . = .
. . .  O O O  O . O         . = .          - - -          . . .
. . .  . . .  O X O         . . .          . - .          = . .
X . O  . X X  . X X
```

X's only macro line is the top row, which needs the top-right board; X has three stones
there and needs two more cells. O's lines need the bottom-left board plus either the
bottom-right or the top-right. The winning move 56 places X's second stone on the
bottom-left board's diagonal (X already has its bottom-left corner) and sends O to the
top-right board — where O's two legal cells (19 and 22) both send X to a closed board, i.e.
give X a free move. With that free move X keeps the initiative (73), O must keep answering,
and the game ends on the **count**, X ahead (line 56, 19, 73, 22, 54, 55, 57).

The net's 78 starts in the bottom-right board instead. O replies with 56 itself, taking the
diagonal cell X needed; the same sequence of forced answers follows, but now the count comes
out level: a draw (78, 56, 22, 19, 54, 59). *A tiebreak-conversion puzzle: the move order
decides who gets the one cell that swings the count.*

## 3. Give a free move to win a line

Game 2249, ply 40. **X to move, free move.** Exact value: **+1**. Only 33 wins; the net's
26 loses, and even its 64-sim search's 31 is not the winning move.

```
X O .  X X O  O X .        macro
X . O  . . O  X O .        . O .
O . O  . X O  . . .        . X X
                           X O O
X O .  X . O  O . .
. . O  . X .  . . .        value map (open boards):
. . .  . . X  X X X        top-left   top-right   middle-left
                            . . -      . . -       . . -
. . X  . X .  . . .         . - .      . . -       - - .
. . X  . . .  O O O         . - .      - - -       + - -
O . X  O O O  . X X
```

X owns the centre, middle-right and bottom-left boards; the middle row is X's line and it
needs the middle-left board. 33 is the bottom-left cell of that board: it makes X's left
column there (X has the top-left corner already) a threat, and it sends O to the
bottom-left board — X's, closed — so O gets a free move. O uses it in the top-left board
(2), and the line 33, 2, 26, 20, 24, 23, 25 ends with X completing a macro line. The net's
26 (bottom-right cell of the top-right board) sends O into the top-right board's fight
first; O wins the count at the end (26, 29, 20, 23, 2, 24, 4, 7). *Again the free move the
net refuses to give is the winning move: what matters is which board the fight happens
in first.*

## 4. Sent into a double threat

Game 2522, ply 51. **O to move, sent to the bottom-left board.** Exact value: **+1** for O
— but only one of the five legal cells keeps it. The net plays 57 and loses.

```
O X X  O X .  . X X        macro
. . X  . . O  . O .        X O O
. . X  O O O  O O O        . O .
                           . X .
. . .  O . O  X X O
O X O  O X .  X . O        value map (bottom-left board):
. X O  O X .  . O .         - - -
                            - . +
. . .  . O X  O X X         . . .
. X .  . X X  X . X
X X O  . O X  X . O
```

In the bottom-left board X has the centre and two more stones and threatens to complete a
line at either of two cells; O cannot block both, so the board is X's whenever X is allowed
to play there. O's move therefore decides *where X plays next*, and only 59 — which sends X
to the middle-right board, still open, where X's own threat can be met with tempo — holds.
The solver's line after 59 (59, 49, 28, 27, 29, 51, 54, 55) ends on the count with O ahead.
The net's 57 sends X to the middle-left board, where X completes a line at once (28) and the
sequence 57, 28, 49, 51, 54, 55 finishes with an X macro line. *The rule "never send the
opponent to a board they can win" is beside the point here — the bottom-left board is lost
whatever O does; the question is which board X gets to win **next**.*

## 5. Holding a draw with a free move

Game 2829, ply 45. **O to move, free move.** Exact value: **0** — a draw is the best O can
do, and only two moves hold it (47 and 51, both in the middle-right board). The net's 46
loses; the 64-sim search's 50 also loses.

```
O . X  . O O  . X O        macro
O . .  O O .  X X X        O . X
O . X  . X .  X O O        X . .
                           O X X
X X X  . X .  O . .
O X .  O O X  . X .        value map (open boards):
. . O  . . O  . O X        top-middle   centre   middle-right
                            - . .        - . -    . - =
. . O  X . .  X X X         . . -        . . .    - . -
. . O  X . O  . . .         - . -        - - .    = . .
X . O  X . .  . O O
```

Three boards are open; X owns four boards to O's two, and X needs only the middle-right
board to complete the macro right column (the middle row is a second, slower line). O has no
line that can still be completed, so O is playing for the count: keep the middle-right board
out of X's hands and split the rest. In that board X has the centre and the bottom-right
corner, so X's live lines run through cells 2, 3, 5 and 6; O's two drawing moves are the two
ends of X's diagonal, 47 (cell 2, which also cuts the right column) and 51 (cell 6). Every
move in the top-middle or centre board loses (the map is all `-` there), and so do the other
cells of the middle-right board. After 47 the line 47, 9, 14, 46, 36, 48, 50, 51 ends with the
count equal. After the net's 46 — one cell over, on the edge instead of the corner — the
sequence 46, 15, 9, 36, 38, 47, 42, 48 ends in an X macro line. *The draw_hold + tiebreak
motif: with no line of its own, the defender's only resource is the exact count, and one
cell is the difference between a level count and a lost line.*

---

**What the five have in common.** None is a local tactic: in every one the net's move is a
reasonable-looking play *inside* a board, and what it misses is *which board the opponent
will be sent to* and what that does to the count or to a macro line two or three moves
later. Three of the five winning moves deliberately hand the opponent a free move. That is
the A7 result (`KNOWLEDGE.md` claim 32) in five pictures: what the raw policy still misses
at +242 Elo is tempo and the count rule, and the 64-simulation search, which fixes 99.9 % of
its endgame errors, misses exactly the same kind of thing in the last 0.1 %.
