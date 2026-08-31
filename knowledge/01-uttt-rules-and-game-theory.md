# Ultimate Tic-Tac-Toe: rules, variants, and game-theoretic status

Knowledge-base file 01 for the `uttt-zero` project. Researched 2026-08-29. Every fact below is tagged with the rule variant it applies to, because the single most common error in the literature on this game is quoting a result proved for one variant as if it applied to another.

## 0. Our variant, stated precisely

- Nine local 3x3 boards in a 3x3 grid; 81 cells. X moves first, anywhere.
- A move in cell (r,c) of any local board sends the opponent to local board (r,c).
- A local board that is **won** or **full** is *closed*: no further moves may be played in it.
- A player sent to a closed board may play in any empty cell of any open board (a "free move").
- Three local boards in a line on the global board wins immediately. A full, unwon local board is *drawn*: it counts for nobody and blocks every global line through it.
- If all nine boards close with no global line, the player who **won more local boards** wins; **equal counts are a draw**.

This is, cell for cell, the CodinGame "Ultimate Tic-Tac-Toe" arena ruleset for Bronze league and above (verified against the referee source in section 1.3). It is **not** the variant solved by the 2020 paper (section 2.1).

## 1. Canonical rules and the variant axes

### 1.1 Ben Orlin's post (June 2013) and its later edit

The game was popularized by Ben Orlin's post ["Ultimate Tic-Tac-Toe" on Math with Bad Drawings](https://mathwithbaddrawings.com/2013/06/16/ultimate-tic-tac-toe/) (June 2013). He credits no inventor; he saw mathematicians playing it at a picnic. Wikipedia lists a commercial predecessor, [Tic-Tac-Ku](https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe) (Asperheim and Van Oosterum, Mensa Select 2009), whose win condition is "five boards" rather than three in a line, and a Hacker News commenter linked a [Khan Academy implementation](https://www.khanacademy.org/computer-programming/in-tic-tac-toe-ception-perfect/1681243068) that the 2020 paper's footnote also cites as predating 2013.

Orlin's four core rules: each turn you mark one small square; three in a row on a small board wins that board; three small boards in a row wins the game; and "you don't get to pick which of the nine boards to play on. That's determined by your opponent's previous move. Whichever square he picks, that's the board you must play in next."

The edge cases are where the variants come from. Orlin's [preserved original text](https://mathwithbaddrawings.com/ultimate-tic-tac-toe-original-post/) said:

- Sent to an already-won board: "If there are open squares, you must pick one. While you can't really affect that board, you can at least determine where your opponent will go next."
- Sent to a full board: "congratulations - you get to go anywhere you like, on any of the other boards."
- Tied small board: "I recommend that the board counts for neither X nor O. But, if you feel like a crazy variant, you could agree before the game to count a tied board for both X and O."

He later revised the won-board rule to "If you are sent to a board that's already been won, you may go wherever you like", explaining that "the rules as I've described them are not the best" because "my gambit is too strong, and can be extended into a guaranteed win for X." The current post reads: "What if my opponent sends me to a board that's already been won? In that case, congratulations - you get to go anywhere you like." A commenter on [Joachim Breitner's July 2013 analysis](https://www.joachim-breitner.de/blog/604-Ultimate_Tic_Tac_Toe_is_always_won_by_X) states the same history: the free-move-on-won-board rule "was a variant later added, precisely because of the known winning strategy without".

### 1.2 The variant axes and who uses what

| Axis | Option A | Option B |
|---|---|---|
| (a) Play inside a won board? | **Allowed** (moves change nothing): Orlin 2013 original, Breitner 2013, Khan Academy, [Bertholon et al. 2020](https://arxiv.org/abs/2006.02353), [Diamond 2022](https://arxiv.org/abs/2207.06239), Chapel Hill Math Circle handout | **Closed**: Orlin (revised), [Wikipedia](https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe), CodinGame, [uttt.ai](https://github.com/arnowaczynski/utttai), [nelhage's solver](https://minimax.dev/docs/ultimate/the-game/), [bejofo](https://bejofo.com/ttt), [victorz.ca](https://victorz.ca/game/ut3_rules), Google Play / App Store apps ([example](https://play.google.com/store/apps/details?hl=en_US&id=com.ultimatetictactoe.android)), Zirkelbach and Sadikov 2024 |
| (b) Drawn (full, unwon) board | **Counts for nobody, blocks lines** (Orlin's recommendation, Wikipedia, CodinGame, nearly all apps) | **Counts for both players** (Orlin's "crazy variant"; played as "Cutthroat" by [gPress](https://gpress.soopergrape.com/index.php/2025/06/26/n-in-a-row-games-part-3/); implemented by [Baker et al. 2021](https://books.aijr.org/index.php/press/catalog/download/114/44/1531-1?inline=1)) |
| (c) Sent to a completed board | **Free move anywhere** whether won or full (all modern rulesets) | Free move only when **full**; must play inside a won board with empty cells (2013 original, 2020 paper) |
| (d) No global line at the end | **Draw** (Wikipedia, Orlin, uttt.ai, nelhage, victorz.ca, the app-store apps quoted above) | **Most local boards wins, equal is a draw** (CodinGame only, among sources found) |

Two more knobs appear in the literature: random opening moves to neutralize the forced win in variant (a)/(c)-B ([Diamond 2022](https://arxiv.org/abs/2207.06239)), and Tic-Tac-Ku's "win five boards" objective, which gPress notes "does affect the outcome of the game, for similar reasons as why a popular vote can result in different outcomes from the electoral college."

No Kaggle competition or `kaggle-environments` environment for UTTT exists; Kaggle ships only `tictactoe` and `connectx` ([README](https://github.com/Kaggle/kaggle-environments/blob/master/README.md)). A few community notebooks train AlphaZero-style UTTT agents on Kaggle ([example](https://github.com/htnminh/AlphaZero-Ultimate-TicTacToe)).

### 1.3 CodinGame's rules, exactly

The [CodinGame arena](https://www.codingame.com/multiplayer/bot-programming/tic-tac-toe) (about 10,000 entrants; Legend league about 400 bots, Gold about 1,400) plays classic 3x3 tic-tac-toe in Wood league and UTTT from Bronze up. The Bronze+ [statement](https://github.com/CodinGame/game-ultimate-tictactoe/blob/master/config/level2/statement_en.html) says: "When a player plays on a small board, that player also decides where the next player will be allowed to play"; "If a player is sent to a board that is either already won, or full, then that player is allowed to play in any empty square"; victory is "You've won on 3 aligned smaller tic-tac-toe boards"; and "If nobody managed to get 3 marks aligned, the player that won the most smaller tic-tac-toe boards wins." Protocol: input is the opponent's last move as `row col` (`-1 -1` on turn one), then `validActionCount` and the list of legal cells; output is `row col` in 0-8 coordinates. Time: 1000 ms for each player's first turn, 100 ms afterwards.

The [referee source](https://github.com/CodinGame/game-ultimate-tictactoe/blob/master/src/main/java/com/codingame/game/Referee.java) pins down the ambiguities:

- `TicTacToe.getValidActions()` returns nothing once `winner != 0`, so a won board is closed even if it has empty cells; a full board is trivially closed. If the target board yields no actions, the referee collects the empty cells of every open board (free move).
- Winning a small board adds 1 to the player's score; a global three-in-a-row sets the score to 10 and ends the game. When no valid actions remain the game ends and scores are compared, so equal board counts are a draw. The game designer confirmed this on the [forum](https://www.codingame.com/forum/t/ultimate-tic-tac-toe-puzzle-discussion/22616): "When no players have 3 marks aligned, the winner is the player that won the most small boards (if the same number, that's a draw)." A drawn small board never touches the master grid, so it counts for nobody and blocks lines.
- Max turns is 81 (the natural bound). Invalid moves and timeouts lose (score -1).

The tiebreak was contested when introduced (March 2018). Daporan argued it "makes the game even more one-sided": the first player "can now focus on controlling small boards, which is easy, while preventing player 2 from making a line, which is also easy." Neumann proposed plain draws; dbdr proposed a tiered tiebreak; the most-boards rule stayed.

## 2. Solved status

### 2.1 Bertholon, Géraud-Stewart, Kugelmann, Lenoir, Naccache (2020)

["At Most 43 Moves, At Least 29: Optimal Strategies and Bounds for Ultimate Tic-Tac-Toe"](https://arxiv.org/abs/2006.02353) (arXiv 2006.02353, cs.GT, ENS Paris, v1 3 June 2020, v2 6 June 2020).

**Variant solved.** The active field is the field indexed by the previous spot "if there are free spots in field j"; if field j has no free spots "the current player can freely choose the active field." A won field stays open: "Any further action in that field will not change this status and it is not possible to win an already won field." This is Orlin's *original* 2013 ruleset: free move only on a full board, forced play inside won boards. The paper never mentions the closed-board variant.

**Result.** The first player has a winning strategy; an optimal one wins in at most 43 moves; the second player can hold out at least 29 rounds; and "Xavier's optimal strategy's first move is a double" (a spot (i,i), what gPress calls a "home square"), after which "If Olivia's first move is (i,j), then Xavier must play (j,i)."

**Method.** A hand-constructed strategy with an invariant-based proof (properties P1-P6 maintained by induction through opening, middlegame and endgame), plus an explicit second-player delaying strategy for the lower bound. No computer search or compute is reported; the arXiv source is 10 KB.

**The strategy, and why it dies under closed boards.** X opens (4,4), centre of the centre. For seven more moves X answers each O move (4,j) with (j,4), the centre spot of field j, which sends O straight back to the centre field. O fills the centre field (and wins it), X holds the centre spot of every other field, and X then gets the free move when the centre is full; the middlegame and endgame repeat the same tempo trick using spot 0 and spot 8. Every step relies on O being forced to keep playing inside a field O has already won. Under closed-board rules O gets a free move the moment the centre is won, and the forcing chain breaks. This is exactly the "Orlin gambit" that Breitner described in July 2013 as "not a formal proof yet, but hopefully close enough to convince you", that a [2013 Hacker News thread](https://news.ycombinator.com/item?id=5898506) dissected move by move, and that Presh Talwalkar's [Mind Your Decisions video](https://mindyourdecisions.com/blog/2014/11/29/ultimate-tic-tac-toe-a-winning-strategy-video/) (2014, crediting Breitner) popularized. The 2020 paper's contribution was to formalize and bound it.

[Diamond (2022, v3 2023)](https://arxiv.org/abs/2207.06239) keeps the same rules and proposes randomizing the first four moves with five random digits; the body computes the chance of landing in an "easily calculable" forced win as 56/59,049 (0.0948%), while the abstract of the arXiv version says 64/59,049 (0.108%). The discrepancy is in the source, not a transcription error.

### 2.2 Attempts on the closed-board variant

- **Nelson Elhage's solver (2020-2022).** Rust engine, parallel PN / DFPN proof-number search, positional pruning, bitboards; rules are the Wikipedia ones (won *or drawn* boards give a free move; draw on no line). Status per [minimax.dev](https://minimax.dev/docs/ultimate/): "capable of solving Ultimate Tic Tac Toe positions after about 20 ply (10 moves by each player) in a few hours of search on my Ryzen 3900X", with "a total computational cost of a few hundred million CPU-hours to solve the whole game without further optimization", roughly "$2M - $10M" of cloud CPU. The game value is not determined. Code: [github.com/nelhage/ultimatettt](https://github.com/nelhage/ultimatettt); write-up ["Towards solving Ultimate Tic Tac Toe"](https://blog.nelhage.com/post/solving-ultimate-ttt/).
- [Zirkelbach and Sadikov (2024)](https://is.ijs.si/wp-content/uploads/2024/10/SCAI_2024_paper_7299.pdf), working in the closed-board variant, summarize: "Some researchers have attempted to solve the game theoretically, but the spatial complexity proved too great to allow for a complete solution."
- No solving attempt targeting the **most-boards tiebreak** was found anywhere.

### 2.3 What is believed about the value of our variant

Our exact variant is **unsolved**, and no source claims otherwise. The evidence on its value:

- CodinGame veteran jacek (2022, [forum p.7](https://forum.codingame.com/t/ultimate-tic-tac-toe-puzzle-discussion/22616?page=7)): "it is agreed upon that either p1 wins or a draw can be forced", adding that the most-boards rule "probably further makes the p1 player better." sscg13 argued in the same thread that a second-player win is "highly improbable" under optimal play. (A strategy-stealing argument does not apply cleanly here because the send rule makes an extra mark non-monotone, so this is intuition, not a theorem.)
- darkhorse64, a top CodinGame bot author (2020, [forum p.5](https://forum.codingame.com/t/ultimate-tic-tac-toe-puzzle-discussion/22616?page=5)): "P1 has a 60% winrate for UTTT so chances are not equal." Di_Masta reported roughly 70% as first player but 10% as second against the Gold boss with the same bot.
- Random playouts under CodinGame rules (snowfrogdev, one million games, 2018, [forum p.2](https://forum.codingame.com/t/ultimate-tic-tac-toe-puzzle-discussion/22616?page=2)): X wins 50.9%, draw 7.2%, O wins 41.9%.
- Kevin Royer's Monte-Carlo opening study on CodinGame data: the centre opening (4,4) gives X "about 52% chance of winning" ([royerk.github.io](https://royerk.github.io/Neural-Network-UT3/)).
- Under the draw-tiebreak closed-board variant, the gPress author (a long-time human player using uttt.ai analysis) writes: "Like Chess, the game is not proven to be a draw with perfect play, but it likely is." Rule (d)-B removes most of those draws by construction.
- Heuristic-bot tournaments confirm the first-mover edge is robust: [Baker, Mukhoti and Chandavarkar (2021)](https://books.aijr.org/index.php/press/catalog/download/114/44/1531-1?inline=1) conclude "it is far easier to win games of UTT as X than as O"; Shayak Banerjee's RL bot reached ~70% as X vs ~60% as O against a random opponent ([Medium](https://medium.com/@shayak_89588/playing-ultimate-tic-tac-toe-with-reinforcement-learning-7bea5b9d7252)).

No AlphaZero-style project found publishes side-conditioned self-play win rates; uttt.ai's evaluation deliberately swaps sides across 50 fixed openings to cancel the bias.

### 2.4 Related theory

- [Whitney George and Janine Janoski (2016), arXiv 1606.04779](https://arxiv.org/abs/1606.04779): an *impartial* "Super Tic-Tac-Toe" (both players mark X) on n x n boards; board actions form a dihedral group of equivalent games. Not the partisan game.
- Konforti and Epstein, "NP Completeness in Contemporary Board Games" (Columbia), cited by Wikipedia for a complexity claim; the link is dead and the content could not be verified. Any hardness claim must concern a generalized (n x n) game, since the 9x9 game is finite.

## 3. State-space and game-tree size

Nothing rigorous is published for any variant; Wikipedia's [game-complexity table](https://en.wikipedia.org/wiki/Game_complexity) has no UTTT row. What can be said:

- **Naive state bound (any variant):** 3^81 ~ 4.4 x 10^38 cell colourings, the figure used by the [INF581 report](https://josselinsomervilleroberts.github.io/papers/Report_INF581.pdf) ("theoretically, there are 3^81 possible states. In practice, the space of valid states is smaller"). A full state also needs side-to-move and the forced board (9 choices or free), a factor below 20. Secondary sources quoting "about 10^39" (Grokipedia) or "trillions of positions or beyond" ([Rare Pike](https://rarepike.com/three/ultimate-tic-tac-toe/)) derive from this bound or from nothing; treat them as unsourced.
- **Why per-board counting does not shrink it much:** only the *global* X-O count is constrained (equal, or X one ahead), so a local board can legally hold five X and no O; the 5,478 legal 3x3 positions of ordinary tic-tac-toe are not the per-board alphabet. Closing boards removes states (no marks after a local win), and the 8 dihedral symmetries divide by at most 8.
- **Game tree:** at most 81 plies; the branching factor is at most 9 on a forced move, 81 on move one, and up to the number of open cells on a free move ("a branching factor that can go through the roof (max = 81)", [Royer](https://royerk.github.io/Neural-Network-UT3/)). Elhage's measured difficulty is the best practical yardstick: ~20-ply positions solve in hours on a 12-core desktop; the root is "a few hundred million CPU-hours" away.
- **Game length:** [Addison, Peeler and Alvin (FLAIRS 2022)](https://journals.flvc.org/FLAIRS/article/view/130698): "a typical game lasting at least 30 moves". Baker et al.'s heuristic bots (closed boards, both-count tie variant) averaged roughly 50-58 plies in decisive games and longer in draws. In the 2020 paper's variant the forced win takes 29-43 moves. No published length distribution for strong closed-board play was found; uttt.ai's [datasets README](https://github.com/arnowaczynski/utttai/blob/main/datasets/README.md) has per-depth histograms of its 16 million evaluated positions but no summary statistics.

## 4. Strategic knowledge (closed-board rules unless noted)

**Opening.** Strong bots overwhelmingly open centre-of-centre. gPress reports uttt.ai analysis scores for X's first move: centre-centre +11.81 ("Strong AIs strongly prefer this move"), centre-corner +11.07, centre-edge +8.16, corner-of-same-corner +6.47, corner-opposing-corner +6.12, and every edge-board opening "bad"; the scale is uttt.ai's internal evaluation and is not documented. CodinGame's Di_Masta runs MCTS but "always play[s] on (4,4)"; Royer's simulations rate it best at ~52%. Arkadiusz Nowaczynski's own tips from playing his AlphaZero-like agent (relayed on [Board & Card Games SE](https://boardgames.stackexchange.com/questions/49291/strategy-for-ultimate-tic-tac-toe)): "Start in the center square of the center subgame"; O's response is to push to a corner subgame, "so then let the next 8 moves be played in the corner subgames"; when O breaks out, "jump between the side subgames"; "maintain the overall balance on the board and wait for the opponent's mistake (the game is a marathon, not a sprint)". Human guides split between centre-of-centre ([tictoe.org](https://tictoe.org/games/ultimate-tic-tac-toe), [tictactoefun](https://tictactoefun.com/blog/ultimate-strategy.html)) and corner-of-centre ([Rare Pike](https://rarepike.com/three/ultimate-tic-tac-toe/)). Note that in the 2020 paper's variant the same (4,4) opening is the start of a *forced win*; the move is good in both worlds for different reasons.

**Centre board.** The 2016 HUJI heuristic (Lifshitz and Tsurel, quoted on the SE thread) weights winning the centre board 10 versus 3 for a corner board and 5 for any board; gPress: "good positioning on the center board can provide an enduring advantage that is difficult to offset"; Cohensius: "don't let your opponent play in the middle board. Do it by completing 3-in-a-row without the middle in the non-middle boards." A centre-cell move sends the opponent to the centre board, so centre cells are spent carefully.

**Free moves as tempo.** Nowaczynski: "Think twice before sending your opponent to the finished subgame (being able to choose any move from the unfinished subgames is very powerful)." gPress: "Never underestimate the power of a free move. Many games have been won by someone being forced to move on a free move square. Don't give up free moves for free", but "don't underestimate the power of a good major board position, even if securing it gives up a free move." Nearly-full boards are free-move squares in waiting ([tictoe.org](https://tictoe.org/games/ultimate-tic-tac-toe)); completing boards early "narrows the playing field and can create free-move opportunities for the opponent" (Rare Pike).

**Poisoned squares and forcing.** Elhage's [positional analysis](https://minimax.dev/docs/ultimate/pruning/): once a player is one local move from a global win, every cell that would send the opponent to that board is losing and can be pruned outright; late in the game this collapses branching. gPress states the human version: a standing global threat means "any free move square you land on ends the game. It's a move that pays you interest." Sacrificing local boards for position is standard ([Wikipedia](https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe); Rare Pike). The 2020 paper's strategy is the extreme case: give O the whole centre board for eight tempi.

**Three boards suffice.** gPress: "If you can win or draw on merely three boards - the center, and two opposing corners - that is sufficient to not lose the game, even if your opponent wins every other board." That is exactly why the most-boards tiebreak changes the endgame.

**When the most-boards tiebreak dominates (our variant).** Under draw rules, "it is common to see a player that won 5 mini-boards losing the game" (Cohensius); a five-board set such as {0,2,3,5,7} contains no line. Under CodinGame rules that player wins once the board fills, so material (board count) becomes a second win condition and "deny every line, then collect boards" is a coherent plan (Daporan's objection). Draws still exist (equal counts, e.g. 4-4 with one drawn board), but random play gives only 7.2% draws, and Di_Masta observed that his MCTS initially saw very few until draws were rewarded 0.5.

**Bot engineering benchmarks (CodinGame).** Legend was reachable in 2018 with ~25k full random rollouts on the second turn ([Magus](https://forum.codingame.com/t/ultimate-tic-tac-toe-puzzle-discussion/22616?page=2)); by 2019 "the top of legend goes more towards 100k+" per 100 ms turn in C++ (reCurse), and Magus reported 300k heuristic-guided rollouts. uttt.ai's neural MCTS at 1k simulations beats plain MCTS at 10M ([README](https://github.com/arnowaczynski/utttai)). Offline tooling: the [official referee](https://github.com/CodinGame/game-ultimate-tictactoe) and [Agade's arena](https://github.com/Agade09/CG-UTTT-Arena).

## 5. Academic and thesis work

- Bertholon et al. 2020, arXiv [2006.02353](https://arxiv.org/abs/2006.02353) (section 2.1). Diamond 2022, arXiv [2207.06239](https://arxiv.org/abs/2207.06239).
- Whitney George and Janoski 2016, arXiv [1606.04779](https://arxiv.org/abs/1606.04779), group actions on impartial super tic-tac-toe.
- Zirkelbach and Sadikov, ["Puzzle Generation for Ultimate-Tic-Tac-Toe"](https://doi.org/10.70314/is.2024.scai.7299), Information Society 2024 (Ljubljana): minimax-generated tactical puzzles (1,263 across five depths, 1 to 9 plies) plus 50 strategic ones, closed-board variant; identifies the AlphaZero-style agent (uttt.ai) as "currently considered one of the strongest players of this game".
- Addison, Peeler and Alvin, ["Ultimate Tic-Tac-Toe Bot Techniques"](https://journals.flvc.org/FLAIRS/article/view/130698), FLAIRS-35 (2022): random, heat-map, MCTS and an AlphaZero-inspired CNN bot (24 h of training on MCTS data) that won 88% of 50,000 games.
- Baker, Mukhoti and Chandavarkar, ["An Analysis of Heuristics for a Mathematically Incomplete Variant of TicTacToe"](https://books.aijr.org/index.php/press/catalog/download/114/44/1531-1?inline=1), WREC 2021 (NIT Karnataka): 64,000 games between eight cell-priority heuristics; X wins most matchups; note their tied boards count for both players.
- Enrico D'Alberton, ["When Tic-Tac-Toe Wasn't Hard Enough: A Reinforcement Learning Journey in Ultimate Tic Tac Toe"](https://thesis.unipd.it/handle/20.500.12608/86899), MSc thesis, University of Padua 2024/25: DQN, DDQN, A2C, PPO; best-response training shows "standard self-play" yields exploitable policies.
- Subrahmanya Srivathsava Sista, ["Adversarial Game Playing Using Monte Carlo Tree Search"](https://etd.ohiolink.edu/acprod/odb_etd/ws/send_file/send?accession=ucin1479820656701076&disposition=inline), MSc thesis, University of Cincinnati 2016 (the 2020 paper mislabels it a PhD thesis): MCTS beats minimax under tight time limits.
- Course reports: Lifshitz and Tsurel 2016 (HUJI, heuristic weights; link now dead), Chen, Doan and Xu 2018 "AI Agents for Ultimate Tic-Tac-Toe" (cited by the 2020 paper; link dead), Somerville Roberts et al. 2022 ([INF581, Ecole Polytechnique](https://josselinsomervilleroberts.github.io/papers/Report_INF581.pdf)), [Columbia COMS 4995 UTTTSolver 2023](https://www.cs.columbia.edu/~sedwards/classes/2023/4995-fall/reports/UTTSolver-report.pdf), Powell and Merrill 2021 (heuristic weights quoted on the SE thread).
- Non-academic but substantive: Breitner 2013, Elhage 2020-2022, gPress 2022/2025, and the uttt.ai repository and datasets (16 million MCTS/NMCTS-evaluated positions, mirrored on Hugging Face as [markstanl/u3t](https://huggingface.co/datasets/markstanl/u3t)).

## Key takeaways for our project

1. Our ruleset is exactly CodinGame Bronze+ (closed won/full boards, free move, most-boards tiebreak with equal = draw, drawn boards count for nobody and block lines). It is unsolved and no solving attempt targets the most-boards tiebreak.
2. The 2020 "first player wins in at most 43 moves" result is for Orlin's original rules (forced play inside won boards, free move only on full boards). Its tempo trick collapses under closed boards; never cite it as the value of our game.
3. Best available belief for our variant: X wins or draws with perfect play; strong CodinGame bots see roughly 60% X wins; random play gives 50.9 / 7.2 / 41.9. Evaluate agents with side-swapped paired games from fixed openings (uttt.ai's protocol) and report X and O results separately.
4. Size: 3^81 ~ 4.4 x 10^38 is the only defensible state bound; no reachable-position count exists. Elhage's DFPN solves ~20-ply positions in hours, which makes exact late-middlegame solves a feasible ground-truth check for our value head.
5. Branching is at most 9 except on free moves (up to 81); games last at most 81 plies and typically 30-60; policy head = 81 masked logits; use the 8 dihedral symmetries for augmentation (uttt.ai used flips).
6. Strategy priors to test against the trained agent: centre-of-centre opening; centre-board weight; free-move squares as tempo (poisoned squares once a global threat exists); deliberate board sacrifices; the three-board (centre plus opposite corners) non-losing set.
7. The most-boards tiebreak turns board count into a second win condition; check whether self-play learns "deny lines, collect boards" (Daporan's prediction) and how often games reach the count.
8. Reference strong players: CodinGame Legend (C++ MCTS, 100k+ rollouts per 100 ms) and uttt.ai (5M-parameter policy-value net, NMCTS at 1k sims beats 10M-rollout MCTS). The official referee and Agade's arena support offline matches.
9. Rule-variant hygiene: record the exact variant on every dataset, model and result; the 16M uttt.ai positions use draw-tiebreak rules and are usable for bootstrapping only with that caveat.
10. Data mirrors: uttt.ai datasets on Google Drive and Hugging Face (markstanl/u3t); the FLAIRS and WREC papers show 24-hour CNN training already dominates classical bots, so a home-PC AlphaZero is well within precedent.
