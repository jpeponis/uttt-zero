# Prioritized findings

1. **High — The probe and surprise datasets are not actually deduplicated.**  
   **Location:** `tools/probe_value.py:49–51`; reused by `tools/surprise.py:23–24,57`.

   The code mistakes inverse cluster labels for row indices:

   ```python
   _, first = torch.unique(x, dim=0, return_inverse=True)
   sel = torch.unique(first)
   ```

   `return_inverse=True` returns one cluster label per input row. Consequently, `sel` is normally `0..K-1`, and the code selects the first `K` shuffled rows—not one representative of each unique position. The reported `K` is still the number of unique inputs, but the evaluated sample can retain duplicates and omit many unique states. This invalidates the claim that the probe and surprise summaries were computed over 49,968 and 6,969 distinct positions respectively.

   **Suggested fix:** compute the first original index for every inverse label, or use a stable `numpy.unique(..., return_index=True)` equivalent. Add a test containing interleaved duplicates and assert both uniqueness and preservation of one row per equivalence class. Then rerun all counterfactual and surprise analyses.

2. **High — The counterfactual value probes mostly measure responses to illegal, off-distribution tensors rather than game effects.**  
   **Location:** `tools/probe_value.py:54–59,106–117,138–145`; `RESULTS-v2a.md:91–112`.

   The color-flip experiment changes all nine cells of a local board and its macro owner. This generally violates global move-count parity and can create or remove a terminal macro line. The “close board” intervention marks a board `FULL` while filling every empty cell with X stones, often creating an X line inconsistent with the `FULL` label and heavily biasing the edit by absolute color. All probes pass `done=False`, including counterfactuals that have become terminal.

   Therefore figures such as the reported `+0.25` free-move tempo effect or `+1.03` center-board effect are not causal game values. They are neural-network responses to handcrafted, often unreachable inputs. Calling them “the net’s beliefs” is not enough because the input distribution is outside what the net was trained to interpret.

   **Suggested fix:** construct paired positions through legal histories, or match naturally occurring positions on ply, side to move, open-board count, macro score, target-board occupancy, and tactical threats. Reject terminal edits or assign their exact terminal values. For local ownership, compare legal move sequences that produce alternative ownership outcomes rather than rewriting the tensor. Report paired bootstrap intervals and repeat across checkpoints and search budgets.

3. **High — The principal strength claim is tied to an unpaired, artificial opening distribution.**  
   **Location:** `uttt/arena.py:81–85`; `uttt/train2.py:141–143`; `tools/match.py:70–71`; `tools/ladder.py:44–60`; `RESULTS-v2a.md:31–51`.

   Side-swapped games do not reuse a persisted paired opening state; random opening plies are generated independently. More importantly, both agents are forced through two uniformly random opening moves. That measures continuation strength and robustness to random openings, not normal empty-board playing strength. It plausibly favors v2a because v2a was explicitly trained with opening sampling and uniform floors, whereas dev1 collapsed toward a narrow opening distribution.

   The 60.1% score over 1,024 games is statistically real on this test distribution: using its W/D/L counts, the approximate 95% interval is about ±2.8 percentage points, corresponding roughly to +50 to +93 Elo around the quoted +70. The 512-game result is nearer ±4 points. In-run 256-game evaluations have worst-case 95% noise around ±6 points, so differences such as 53% versus 58% do not resolve a smooth plateau; a ±3-point description there is roughly one standard error, not a 95% interval.

   **Suggested fix:** create a fixed opening suite and reuse every opening with colors swapped for every checkpoint. Report separate evaluations for:

   - empty-board play;
   - a balanced set covering all 15 first-move orbits and selected reply orbits;
   - natural openings sampled from a frozen external distribution;
   - deliberately broad random openings.

   Bootstrap by opening pair, record opening IDs, estimate first-player effects, and reuse the identical suite for every anchor-curve point.

4. **High — Resume behavior can silently discard the replay buffer and continuous games.**  
   **Location:** `uttt/train2.py:169–177,219–222`; `uttt/selfplay_cont.py:60–75`.

   `latest.pt` is overwritten every iteration, but the replay buffer is embedded only on `save_buffer_every` iterations. Resuming from a later `latest.pt` therefore finds no buffer and silently starts with an empty one. Optimizer state is saved, but RNG and `GradScaler` state are not.

   Continuous self-play also retains active games in memory across iteration boundaries. When the evaluator is refreshed, those games continue under a new checkpoint, so one trajectory may contain policy targets from multiple generations. On process restart, all partial games and staged histories disappear. The v2a logs show a restart after iteration 9; the resumed run consequently is not fully equivalent to an uninterrupted run. Aggregate reported completed-game counts remain usable, but iteration-level corpus provenance and reproducibility are weakened.

   **Suggested fix:** keep an independently versioned buffer checkpoint and make every `latest.pt` reference it; never interpret a missing buffer as an empty buffer without a warning. Save scaler, RNG, active boards, lengths, staged histories, and the generation used for every ply. Either finish active games before changing the network or explicitly record mixed-generation trajectories.

5. **Medium — Terminal roots have incorrect values in the batched v2 search.**  
   **Location:** `uttt/search.py:191–199,249–252,280`.

   A terminal root begins with its correct terminal evaluation, but simulations increment root visit count without adding a root edge value. The final computation

   ```python
   root_value = (raw_value + sum_edge_W) / node_N
   ```

   therefore shrinks a terminal value of ±1 toward zero as simulations accumulate. With all actions invalid, `-inf` logits also create NaNs that are later suppressed with `nan_to_num`.

   This does not normally affect active self-play games, since they stop before another search, but it is wrong search semantics and can corrupt mixed-batch diagnostics or future callers.

   **Suggested fix:** short-circuit terminal rows and return their exact value and an all-zero policy, or explicitly select the terminal value in the summary. Use a finite minimum logit for invalid actions, as mctx does. Add a test containing terminal and nonterminal roots in the same batch.

6. **Medium — Several corpus conclusions are stronger than the statistics support.**  
   **Location:** `tools/corpus_stats.py:68–95`; `RESULTS-v2a.md:62–89`.

   “Decided by ply 42” is inferred from separation between the conditional mean root values of games that eventually win, draw, or lose. Conditional means do not show that individual games were decided, that their outcome was irreversible, or even that the class distributions had little overlap. This analysis conditions on the future result and on games surviving to each ply.

   The free-move replay analyzes the first 30,000 games encountered from a 159,241-game window rather than a random or iteration-stratified sample. The all-run and last-window outputs differ substantially in free-move and board-closure counts, demonstrating that temporal composition matters. Correlation between free moves and results is also confounded by ply, game length, board closure, macro advantage, and policy strength.

   The opening-orbit table is a useful description of v2a’s self-play distribution, but it is not an opening-value table. Empirical scores mix opening choice, later policy, changing checkpoints, and sparse categories; some orbit counts are only a few hundred. The deeper-search figures remain beliefs of one model/search configuration, not solved opening values.

   **Suggested fix:** sample uniformly by game and iteration, bootstrap by trajectory, and report distributions rather than only conditional means. Define “decision time” using out-of-sample outcome classification, sign stability under stronger search, or exact solvability. For openings, use balanced interventions, fixed opponents, multiple checkpoints/seeds, and convergence across search budgets.

7. **Medium — Endgame and surprise reports use misleading notions of correctness.**  
   **Location:** `tools/endgame_accuracy.py:79–88`; `tools/surprise.py:63–94`; `uttt/solver.py:90`; `RESULTS-v2a.md:113–131`.

   “3-way accuracy” thresholds a scalar expected score at ±0.33. It is not the argmax accuracy of the network’s WDL head, despite being described as WDL classification. Those can disagree substantially. Raw WDL evaluation should retain all three probabilities and report argmax accuracy, log loss, Brier score, and calibration. Search produces a scalar, so its threshold result should be labeled as such and accompanied by value MAE and action regret.

   Surprise mining compares the raw net with a 256-simulation search driven by the same net. A search value near −1 is not proof of a “forced loss,” and disagreement with self-search cannot establish that value loss is “mostly an endgame-tactics floor.” That conclusion would require exact labels or an independently stronger evaluator.

   The solver’s logic appears sound, including its perspective handling and count tiebreak. However, `max_nodes` is accepted and then ignored, making runtime safeguards illusory. The reported exact-action error is credible for the sampled positions, but those positions come from the agent’s own trajectories and are correlated within games.

   **Suggested fix:** enforce `max_nodes` with an explicit incomplete/timeout result, cache transpositions, cluster confidence intervals by source game, and validate surprise cases with exact solving or a demonstrably converged search. Separate “self-search disagreement,” “exact tactical error,” and “forced result” throughout the report.

8. **Medium — Replay weighting still gives common openings substantial excess mass, and the ownership target loses useful information.**  
   **Location:** `uttt/train2.py:45–65`; `uttt/selfplay_cont.py:119–131`; `uttt/model.py:5–9`.

   With per-occurrence weight \(c^{-\alpha}\), a state appearing \(c\) times has total training mass \(c^{1-\alpha}\). At the configured \(\alpha=0.5\), a position repeated 10,000 times still carries 100 times the mass of a singleton. Thus this is duplicate down-weighting, not deduplication, and the empty position and common opening prefixes can continue to dominate. D4-equivalent positions are not canonicalized before counting.

   Ownership has only three classes. At a macro-line termination, still-open boards and genuinely drawn/full boards receive the same “neither player” label, although they represent different strategic facts. The WDL and margin sign conversions themselves appear correct.

   **Suggested fix:** measure effective mass by ply and canonical symmetry class. Consider per-ply sampling, capped counts, \(\alpha\) nearer 1 for opening states, or aggregation of repeated states with target means and recency metadata. Use four ownership states—current player, opponent, closed draw, unfinished—or separate “closed” and “owner” heads. Add an explicit first-player/count-parity feature rather than asking a small convolutional trunk to recover it globally.

9. **Medium — The production depth cap and claimed “UCT” baseline are not validated as described.**  
   **Location:** `runs/v2a/config.json` (`max_depth: 12`); `tests/test_search_graph.py:43–62`; `uttt/model.py:97–106`; `tools/match.py:25–39`; `RESULTS-dev1.md:54–56`.

   Production graph search stops expansion at depth 12 and substitutes the raw network value. The graph tests establish eager/graph equivalence, but not that depth 12 is strength-equivalent to the uncapped/default search. Progressive 48/64-simulation runs can broaden the tree while still being unable to follow a forced line beyond 12 plies. Late tactical sequences are exactly where this matters.

   The reported “plain UCT” anchor is a uniform-prior, zero-value evaluator run through the project’s Gumbel/PUCT tree search. It has no random rollout evaluator and is not classical UCT. It is a useful ablation, but not an external or algorithmically independent strength anchor.

   **Suggested fix:** log depth-cap hit rates by phase and play cap-12 versus cap-24/32 matches at equal simulations and wall time. Rename the current anchor, and add a genuinely independent bitboard rollout MCTS or established compatible engine.

10. **Medium — Important tests can pass without testing their stated property.**  
    **Location:** `tests/test_selfplay_cont.py:50`; `tests/test_search_v2.py`; `NOTES-v2.md`, search-validation section.

    `test_selfplay_cont.py` ends one assertion with `or True`, making it vacuous. The v2 search is mainly compared with the project’s v1 implementation, so shared mistakes would survive. There is no independent golden test against mctx for Sequential Halving, completed-Q mixing, interior selection, terminal mixtures, or value signs.

    The core implementation nevertheless appears close to DeepMind’s definitions: the Sequential Halving schedule, prior-weighted mixed value, sigma scaling, interior score, and final visit-count selection agree with the official [Sequential Halving implementation](https://github.com/google-deepmind/mctx/blob/main/mctx/_src/seq_halving.py), [Q transforms](https://github.com/google-deepmind/mctx/blob/main/mctx/_src/qtransforms.py), and [action selection](https://github.com/google-deepmind/mctx/blob/main/mctx/_src/action_selection.py). The local legal-only min/max normalization is a deliberate difference worth testing explicitly.

    **Suggested fix:** remove the vacuous clause, add resume-equivalence tests, and freeze small official-mctx-derived golden arrays. Exercise terminal/nonterminal mixed batches, graph replay after several in-place weight refreshes, depth truncation, symmetry augmentation, and every value-perspective transition.

# Strategy assessment

The overall recipe is sensible for this game and hardware. Both rule engines implement the stated closed-board/count-tiebreak variant consistently; policy/action ordering and D4 transforms appear correct; nonterminal value backup signs are coherent; Gumbel search at low simulation counts is a defensible choice; and CUDA graphs plus continuous batched self-play deliver a real throughput improvement. The project is no longer primarily compute-starved.

The current limitation is more likely teacher quality, data composition, and evaluation resolution than any single optimizer setting:

- Search is far from saturated: v2a at 256 simulations beating itself at 64 simulations by 80.1% shows a large search-strength gap. A 32-simulation teacher, further limited to depth 12, supplies noisy and sometimes shallow policy targets.
- The small 6×64 network may be capacity-limited, but the evidence does not isolate capacity from target noise, auxiliary-head competition, replay imbalance, or optimization. A plateau in value loss is not by itself a capacity diagnosis.
- Opening duplicates retain high effective replay weight even after \(c^{-0.5}\) weighting. Uniform move and prior floors improve exploration but also make the training and evaluation distributions unlike clean competitive play.
- Self-play remains a moving, self-referential target. Without fixed external suites, multiple seeds, or a league of older opponents, apparent plateaus and improvements can reflect cyclic specialization.
- The partial v2b log through iteration 69 has the 48-simulation checkpoint at roughly 46.7% against v2a over only 256 games. That is consistent with either parity or modest weakness; it is evidence to continue the experiment, not yet evidence that progressive simulations broke the plateau.

Recommended priorities are:

1. **Fix measurement first and establish external anchors.** A paired opening suite, empty-board matches, an independent rollout MCTS, and a frozen exact endgame set are prerequisites for deciding which training change works. This ranks above another long self-play run.

2. **Add exact-label training where the solver is reliable.** Oversample late states and train WDL/value plus action targets from exact minimax. Start with memoization, move ordering, enforced node budgets, and a persistent on-demand cache. Exact labels provide independent signal; they are more valuable initially than mixing in another estimate produced by the same 32-simulation search.

3. **Continue progressive or phase-dependent simulations, while measuring depth truncation.** Allocate more simulations and depth late in games, after free moves, and in tactically volatile states rather than increasing every root uniformly. Tree reuse between moves and transposition caching could yield more effective search per inference than simply increasing the batch-wide simulation count.

4. **Then test a wider network, preferably 6×96 before 8×128.** Profile inference and training throughput and run a controlled paired ablation. Wider capacity is plausible, especially for global macro/micro interactions, but it should not be inferred from one loss curve.

5. **Use search-value mixing cautiously.** Mixing terminal outcome with a stronger reanalysis value or exact short-horizon label can reduce variance. Mixing with the same current network’s shallow root estimate risks self-confirmation. The coefficient should depend on search budget, phase, and exact-label availability and be tested for calibration as well as Elo.

6. **Increase training batch size only if profiling shows unused GPU throughput or unstable gradients.** Batch 4,096 is already large; doubling it is less likely to address the strategic plateau than better targets or capacity, and it increases policy lag unless replay/training ratios are adjusted.

7. **Defer a dense tablebase until reachable-state counts and representation costs are measured.** The raw one-byte estimate ignores indexing, build-time working space, metadata, and integration. An on-demand solver cache and exact-leaf search integration offer a lower-risk path to most of the benefit.

Other missing experiments include multiple independent seeds, auxiliary-loss ablations—especially the relatively heavy margin loss—EMA/SWA evaluation, reanalysis of high-surprise positions, a population of historical opponents, explicit calibration tracking, and best-response-style adversarial evaluation.

# Analysis-methodology assessment

The central methodological need is to separate four kinds of statement:

1. **Behavioral:** what this self-play population happened to do.
2. **Predictive:** what the network predicts on natural held-out states.
3. **Search-relative:** what this particular net-plus-search configuration prefers.
4. **Game-theoretic:** what is true under sufficiently strong or exact play.

The results currently move too easily between those levels. Opening frequencies are behavioral; raw probe outputs are predictive only on valid inputs; 4,096-simulation opening scores are search-relative; “forced loss” and “decided by ply 42” approach game-theoretic language without the required evidence.

For opening analysis, construct a balanced atlas across all first-move orbits and representative reply orbits. Evaluate each with fixed colors, multiple checkpoints, multiple seeds, and geometrically increasing search budgets. Record principal variations, action-value gaps, and rank stability. An opening should be called strategically preferred only when its ordering is stable across those controls.

For the free-move tempo question, use legal natural positions and a prespecified model controlling for ply, macro score, open-board count, threat counts, target-board occupancy, and network generation. Better still, identify paired legal histories that reach closely matched states differing in free-move status. Report within-game or trajectory-cluster uncertainty. The present association is interesting hypothesis generation, not evidence of a causal tempo value.

For “decision time,” plot held-out outcome log loss, calibration, AUC, conditional entropy, and the fraction of games whose predicted sign never changes afterward. Stronger still, define resolution through exact solving or convergence of several independent high-budget searches. Conditional class means alone cannot locate when a game became decided.

Surprise mining should become a tactical-puzzle pipeline: deduplicate correctly, validate candidates with exact solving or budget convergence, store principal variations, measure selected-action regret, and classify motifs such as send-board sacrifice, macro fork, tempo gain, forced closure, and count-tiebreak conversion. Split train and evaluation puzzles by source trajectory and symmetry orbit.

Endgame evaluation should be balanced by empties, result class, side to move, macro-score margin, free-move status, and tactical motif—not merely sampled from the current policy’s visitation distribution. Report WDL calibration, value error, best-action accuracy, regret, and confidence intervals clustered by original game.

Finally, every persisted analysis position should carry game ID, iteration, network generation, search configuration, and opening ID. That provenance would make longitudinal claims, bootstrap estimates, and reproduction substantially more reliable.

# Things done well

- The reference and batched engines agree on the important rule details: won or full boards close, a closed target produces a free move, macro lines take precedence, and otherwise won-board count determines the result.
- Grid-order versus engine-order conversion is handled consistently in inference, training, and analysis. D4 transformations correctly act on both macro and micro coordinates, including policy indices, ownership labels, and target boards.
- WDL, ownership perspective, margin sign, and nonterminal MCTS backup signs are internally coherent. No broad sign inversion was found.
- The principal Gumbel mechanics closely follow mctx rather than an informal approximation. This is one of the strongest parts of the implementation.
- The CUDA-graph design carefully snapshots and restores tree tensors and refreshes evaluator weights in place. Existing eager/graph tests provide useful evidence that the fast path preserves ordinary nonterminal results.
- Run configurations, logs, small text outputs, corpus totals, and provisional caveats are unusually transparent. The reported aggregate game and position counts match the logs.
- The exact solver agrees with the reference-style minimax tests and appears to implement the unusual count-tiebreak terminal rule correctly. It is a strong foundation for a substantially better tactical training and evaluation program.