# Puzzle positions from `suites/puzzles_v2_dev.npz` (hard: 5; net runs/deep10_c1_300/net_0300.pt, search 64 sims)

## Puzzle 12 — game 373, ply 47, O to move, sent to board 8; exact value for the mover +1; motifs: gives_free_move

```
to move: O   next board: 8   moves: 47
O O O  X O X  . O X
. . .  X X X  O X .
. X X  . X .  X . O

X X X  . O O  X O O
O . O  . X O  . X O
. . .  O O .  . X X

. . .  O O .  . . .
X X X  O . O  . O .
. . .  O X .  . X .
macro:
OXX
X.X
XO.
```

Exact value after each legal move (mover's view: `+` win, `=` draw, `-` loss):

```
. . .  . . .  . . .
. . .  . . .  . . .
. . .  . . .  . . .

. . .  . . .  . . .
. . .  . . .  . . .
. . .  . . .  . . .

. . .  . . .  - - +
. . .  . . .  - . +
. . .  . . .  - . -
```

- best move 74 (board 8, cell 2): line [74, 36, 44, 72, 75, 73, 77] → line, winner O
- the net's move 80 (board 8, cell 8) (search 80 (board 8, cell 8)), value -1: line [80, 72, 36, 74, 73, 75, 77, 78] → line, winner X

## Puzzle 16 — game 511, ply 44, X to move, free move; exact value for the mover +1; motifs: tiebreak_conversion

```
to move: X   next board: any   moves: 44
O O X  X X X  O . X
X . X  . . .  X . O
. . X  . O .  O X O

X O .  . . O  . . X
X O .  . X O  O . X
. O .  . . O  . . X

. . .  O O O  O . O
. . .  . . .  O X O
X . O  . X X  . X X
macro:
XX.
OOX
.O.
```

Exact value after each legal move (mover's view: `+` win, `=` draw, `-` loss):

```
. . .  . . .  . - .
. . .  . . .  . = .
. . .  . . .  . . .

. . .  . . .  . . .
. . .  . . .  . . .
. . .  . . .  . . .

- - +  . . .  . = .
- - -  . . .  . . .
. - .  . . .  = . .
```

- best move 56 (board 6, cell 2): line [56, 19, 73, 22, 54, 55, 57] → count, winner X
- the net's move 78 (board 8, cell 6) (search 78 (board 8, cell 6)), value +0: line [78, 56, 22, 19, 54, 59] → draw, winner .

## Puzzle 88 — game 2249, ply 40, X to move, free move; exact value for the mover +1; motifs: gives_free_move

```
to move: X   next board: any   moves: 40
X O .  X X O  O X .
X . O  . . O  X O .
O . O  . X O  . . .

X O .  X . O  O . .
. . O  . X .  . . .
. . .  . . X  X X X

. . X  . X .  . . .
. . X  . . .  O O O
O . X  O O O  . X X
macro:
.O.
.XX
XOO
```

Exact value after each legal move (mover's view: `+` win, `=` draw, `-` loss):

```
. . -  . . .  . . -
. - .  . . .  . . -
. - .  . . .  - - -

. . -  . . .  . . .
- - .  . . .  . . .
+ - -  . . .  . . .

. . .  . . .  . . .
. . .  . . .  . . .
. . .  . . .  . . .
```

- best move 33 (board 3, cell 6): line [33, 2, 26, 20, 24, 23, 25] → line, winner X
- the net's move 26 (board 2, cell 8) (search 31 (board 3, cell 4)), value -1: line [26, 29, 20, 23, 2, 24, 4, 7] → count, winner O

## Puzzle 96 — game 2522, ply 51, O to move, sent to board 6; exact value for the mover +1; motifs: tiebreak_conversion

```
to move: O   next board: 6   moves: 51
O X X  O X .  . X X
. . X  . . O  . O .
. . X  O O O  O O O

. . .  O . O  X X O
O X O  O X .  X . O
. X O  O X .  . O .

. . .  . O X  O X X
. X .  . X X  X . X
X X O  . O X  X . O
macro:
XOO
.O.
.X.
```

Exact value after each legal move (mover's view: `+` win, `=` draw, `-` loss):

```
. . .  . . .  . . .
. . .  . . .  . . .
. . .  . . .  . . .

. . .  . . .  . . .
. . .  . . .  . . .
. . .  . . .  . . .

- - -  . . .  . . .
- . +  . . .  . . .
. . .  . . .  . . .
```

- best move 59 (board 6, cell 5): line [59, 49, 28, 27, 29, 51, 54, 55] → count, winner O
- the net's move 57 (board 6, cell 3) (search 57 (board 6, cell 3)), value -1: line [57, 28, 49, 51, 54, 55] → line, winner X

## Puzzle 102 — game 2829, ply 45, O to move, free move; exact value for the mover +0; motifs: gives_free_move,tiebreak_conversion,draw_hold

```
to move: O   next board: any   moves: 45
O . X  . O O  . X O
O . .  O O .  X X X
O . X  . X .  X O O

X X X  . X .  O . .
O X .  O O X  . X .
. . .  . . O  . O X

. . O  X . .  X X X
. . O  X . O  . . .
X . O  X . .  . O O
macro:
O.X
X..
OXX
```

Exact value after each legal move (mover's view: `+` win, `=` draw, `-` loss):

```
. . .  - . .  . . .
. . .  . . -  . . .
. . .  - . -  . . .

. . .  - . -  . - =
. . .  . . .  - . -
. . .  - - .  = . .

. . .  . . .  . . .
. . .  . . .  . . .
. . .  . . .  . . .
```

- best move 47 (board 5, cell 2): line [47, 9, 14, 46, 36, 48, 50, 51] → draw, winner .
- the net's move 46 (board 5, cell 1) (search 50 (board 5, cell 5)), value -1: line [46, 15, 9, 36, 38, 47, 42, 48] → line, winner X

