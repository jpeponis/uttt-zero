## Prioritised findings

1. **High — Rule isolation is incomplete at reuse boundaries.** `uttt/train2.py:259-266,319-336` merely warns about changed configuration, then restores weights, optimizer and replay buffer without checking the checkpoint’s rule. Resuming with another rule can mix incompatible labels while `config.json` still describes the original corpus. Separately, `uttt/endgame.py:288-295` reuses searches keyed only by simulation count: a count search can grade a draw-labelled set despite the set-rule check passing. **Fix:** reject cross-rule resumes before writing anything or loading state; validate cached search rule and dimensions, or key caches by their full identity. Test both failures.

2. **High — The count-coefficient prediction lacks an explicit failure outcome and may already describe the control.** `PLAN7.md:715-718` permits “or unresolved”; `KNOWLEDGE.md:267-268` already gives `_e4`’s **search** coefficient as **+0.014**, below 0.015. A small draw-run coefficient alone does not demonstrate a fall. **Fix:** distinguish supported, contradicted and imprecise; pre-register a paired coefficient difference on the common positions, separately from the absolute small-coefficient prediction.

3. **High — J3’s proposed duplication correction is statistically wrong.** `tools/empty_board.py:108-109` and `PLAN7.md:619-621` say repeated trajectories make binomial intervals optimistic. Independent samples from a concentrated opening distribution can legitimately produce identical deterministic continuations. Duplicate *outcomes* are not dependent *draws*. Bootstrapping uniformly over distinct lines would change their probability weights. **Fix:** retain game-level intervals for the specified stochastic policy; report concentration separately. Do not enlarge the sampled opening merely to improve the distinct-line count.

4. **Medium — J4 prints unjustifiably certain population intervals.** `uttt/endgame.py:255-261`, called at `tools/frontier.py:199-205`, bootstraps an all-success sample into `[1,1]`; the smoke prints 100% optimal `[100,100]` from 20 positions. No uncertainty interval accompanies solvability. **Fix:** use boundary-safe proportion intervals, with finite-population treatment where appropriate; retain the bootstrap for nondegenerate regret samples, but do not present zero-width intervals as population certainty.

5. **Medium — Promised launch provenance is still absent.** `uttt/train2.py:48-102,256-279` neither records nor explicitly passes `gumbel_scale`, contrary to `PLAN7.md:666-669`. **Fix:** serialize the resolved search configuration, including inherited defaults, into the run and checkpoints. Keep 1.0; this is documentation of the recipe, not an intervention.

6. **Medium — Rule tags do not prevent every silent mixture.** `tools/openings.py:55-62` accepts a count-only surrogate under `--rule draw`; `tools/book.py:151-161,239-242` attaches paired statistics without checking their rule. `tools/corpus_stats.py:33-39` treats a missing configuration as count, including an orphaned new draw corpus. **Fix:** reject unsupported surrogate/rule combinations, validate attached result metadata, and tag each new game file. Restrict legacy count fallback to positively identified legacy artifacts.

7. **Medium — J3 mislabels raw policy as generated play.** `tools/empty_board.py:195-200` describes `timeline.json` as self-play at the training budget. Its first-move statistic is actually the raw evaluator probability (`tools/timeline.py:129-130`). The saved final probability is **0.982254**; iteration 299’s generated-game top-move share is **0.835** (`runs/deep8_c1_300_e8/log.jsonl:300`). **Fix:** label these separately; neither substitutes for the other.

8. **Medium — Draw anatomy becomes chronologically truncated.** `tools/principles.py:101` takes the **first** 20,000 draws. At the predicted draw rate, the late corpus exceeds that cap, so anatomy no longer represents the whole last-20-file window. `:123` also labels X’s mean board count “mean boards each side”; equality no longer follows under draw. **Fix:** sample uniformly across the window or replay all draws, record sampled versus total counts, and report X and O separately.

## Answers to (1)–(6)

### 1. Is the rule change complete?

**The inspected fresh-run terminal path appears complete; the broader plumbing guarantee is not.** I found no remaining count-only payoff branch in:

- reference and batch engines (`uttt/game.py:98-108`; `uttt/batch.py:181-187`);
- either solver kernel (`uttt/solver.py:60-84,147-175`) or child enumeration (`:227-233,256-266`);
- pooled exact labels (`uttt/exact.py:56-59`);
- the tablebase payoff map (`uttt/tablebase.py:79-98`);
- search expansion (`uttt/search.py:183`; `uttt/mcts.py:231`);
- the rollout anchor’s application and search paths (`uttt/rollout.py:85-94,188-209,257-270`).

The margin and ownership labels are auxiliary observations, not terminal values; leaving them unchanged is intentional and coherent (`uttt/selfplay_cont.py:155-170`).

The set-rule refusal and table/evaluator refusal are correctly placed (`uttt/endgame.py:275-276`; `uttt/tablebase.py:120-126`). Add the reuse checks in finding 1. The worker should reject a mismatched endgame set during construction, **before playing its matches**, rather than discovering it during grading (`tools/eval_worker.py:73-104`).

Inference is not categorically absent: `evaluate_rollout` constructs its game using `es.rule` (`uttt/endgame.py:300-309`). Require an explicit evaluation rule and validate it. In contrast, `probe fit` adopting its dataset’s label rule is sensible: it performs no rule-dependent search. Likewise, tools that consume only states and rule-independent concepts—`value_decomp` and `tablebase_grade` here—need not reject a dataset merely because its original labels used another rule; they recompute their targets.

The five I1 tools listed at `PLAN7.md:681-684` must be completed before their readings. Their absence need not block a correctly configured fresh training run. Other count-only tools may stay count-only if clearly labelled and prevented from masquerading as draw analyses. J3/J4 themselves currently default silently to count; that is correct for their specified parents, but add explicit count metadata and either a rule argument or an unsupported-rule refusal before reuse.

Mechanical count→draw relabelling is correct. Reverse relabelling is unavailable from the **aggregate outcome fields**, but not fundamentally impossible: saved move sequences permit replay. Describe the refusal as “requires replay,” not “requires rebuilding the corpus.”

### 2. Are the pre-registered readings falsifiable?

**Only partly.**

**Relabel control.** `I1_A6_corpus_stats.out:1-3` supports **16.5% changed outcomes** and approximately **33.0% resulting draws**, not 33.1%. Combining the three rounding intervals with exhaustiveness constrains the no-line share to approximately `[33.00%,33.05%)`. These are `_e4` figures, not `_e8` results.

As a saved-output check, weighting `_e8`’s last 20 log rows by completed games gives **98,581 games**, approximately **16.60% existing draws** and **32.33% draws after relabelling**. Those percentages inherit the logs’ rounding; obtain exact counts from the persisted games. Thus **≥30%** is falsifiable but weaker than the parent’s mechanical relabel baseline. It does not establish additional draw-seeking adaptation.

**Coefficient.** Keep **0.015** as a declared practical threshold; the unchanged auxiliaries provide no numerical basis for relaxing it. For an interval \(I\):

- supported small coefficient: \(I\subseteq[-0.015,0.015]\);
- contradicted: \(I\) lies wholly outside that band;
- unresolved: otherwise.

This is stricter than the current point-estimate-plus-exclusion criterion. If retaining that criterion, explicitly state that a precisely larger coefficient contradicts it. “Unresolved” must mean insufficient precision, not any inconvenient result.

For “falls,” additionally report \(\Delta=\beta_{\text{draw}}-\beta_{\text{count}}\), using the same design matrix and game-clustered paired inference. A **0.005 utility/board decrease** would be a reasonable predeclared practical margin—not a theoretically derived constant. Do not confuse search coefficients with raw-head coefficients.

**Other predictions.** “Inside the count interval” establishes compatibility, not equivalence. Freeze numerical difference margins, populations and estimators for claims 8 and 13 before reading K1. Claim 1’s rank criterion is observable; specify ties. Claim 33’s qualitative counterexample can survive while its percentages change; claim 34’s immediate-loss avoidance is distinct from those percentages (`KNOWLEDGE.md:433-447`).

The **0.02 visit-share** tolerance is operationally testable if the comparison uses aggregated reply-orbit visits at specified budgets. It is not a 0.02 value tolerance. Save both visits and Q values; a sharply preferred visit allocation can coexist with nearly equal estimated values.

**Cross-play.** Let \(s_C,s_D\) be the draw-trained net’s scores under count and draw. The registered contrast is

\[
(1-s_D)-s_C=1-s_D-s_C.
\]

It is falsifiable against the three-percentage-point margin, but is not an interaction isolating “collect boards” skill: general count-net superiority can make it positive. Report the two scores and contrast without that mechanistic attribution. Bootstrap the contrast jointly by opening ID across rules; sharing the suite means the two estimates need not be statistically independent.

**In-run retention.** Save resolved configurations, artifact hashes, per-game/position provenance and the generating iteration or teacher version. On a small fixed diagnostic sample, retain raw WDL, improved policy, sampling probabilities, root noise, chosen action, visits, Q values and depth-cap hits. The current game files retain moves and root values, not that full decision record (`uttt/selfplay_cont.py:176-198`). Overwritten teachers and nondeterministic execution make exact recovery impossible.

For the auxiliary-target concern, sparsely log separate value/policy versus auxiliary trunk-gradient norms and alignment. This can reveal competing training signals, not prove their causal effect.

### 3. J3: which design?

**Keep the four-ply arm as a precisely named policy-distribution experiment; do not bootstrap over deduplicated lines.** Independent opening sampling estimates the outcome distribution of that policy even when its support is narrow. More sampled plies would answer a different question. If broader opening robustness is desired, add a separately labelled, preweighted opening-suite experiment rather than silently redefining “near-greedy.”

Repeated deterministic suffixes can be memoized after validating deterministic continuation. Preserve sampled frequencies. Before relying on that optimization, check repeated states across batches and seeds; symmetry averaging alone does not eliminate index-based search tie-breaking.

Arms (b) and (c) isolate the **joint exploration-settings package** at matched simulations, not the individual effects of four knobs. That is interpretable if stated exactly. A full factorial is unnecessary unless individual attribution is wanted.

For comparison with claim 24’s generated corpus, I would use the **plain evaluator for both game-playing arms**. Retain symmetry averaging for (a)’s separate search-relative root estimate. If the ensemble remains in (b)/(c), their contrast is still valid for that ensemble, but neither arm recreates the corpus-generating agent.

Arm (a) is not a matched-budget comparator: it uses deeper PUCT rather than the game arms’ Gumbel configuration (`tools/atlas.py:92-95`; `tools/empty_board.py:162-176`). That is acceptable as a separate measurement. Also disclose that (c) changes the trained depth cap from 12 to 24 and budget from the training schedule to 256; “exploration settings as trained” is accurate, “play as trained” is not.

### 4. J4: budget, grader and curve

**The shared budget and abort propagation are sound for complete action-value enumeration.** However, this is stricter than solving the root, and every child is not mathematically necessary merely to grade one chosen move: exact root value plus that child’s value suffice. Keep the conservative design, but call its ordinate **complete legal-action value coverage within budget**, not generic root solvability.

The counted nodes are recursive kernel entries; terminal children handled directly consume zero (`uttt/solver.py:255-263`). Document this convention. It bounds search work, not wall time.

`length > ply`, sampling without replacement and one position per game per ply are correct. Using the plain grader is appropriate; changing J3 as above also removes the evaluator mismatch. Across-ply comparisons need game-linked resampling, not independent-row inference.

Save per-position IDs, completion flags, node counts, child values and selected moves. Currently J4 discards those and writes aggregates (`tools/frontier.py:177-211`), preventing later joint uncertainty calculations without recomputation.

A supportable sentence is:

> Among games in this checkpoint’s specified late corpus still alive at each sampled ply, the measured fraction admitted complete action-value enumeration within \(10^8\) counted nodes; the stated 256-simulation agent achieved the reported optimal-move rate on that solved subset.

No monotonicity, universal frontier, or “solved from ply N” follows—even from 100% sampled success.

### 5. One seed under a new rule

`PLAN7.md:736-741` already concedes the essential confounds. Unchanged auxiliary supervision, rule-dependent exact-label selection and changed replay composition are mechanisms of the rule-by-recipe interaction, not newly discovered independent treatments.

The cheapest useful decomposition is the planned two-net × two-evaluation-rule common-position matrix, reported separately by source corpus and on the intersection solved under both rules. It separates observed network, search-rule and position-mixture differences; it does **not** identify the training-rule effect independently of seed.

Existing checkpoints can cheaply show temporal sensitivity. Existing count replicates can show some count-side variability on the same positions. Neither bounds draw-training seed variance; only additional independent draw training would do that. No extra GPU-day is required merely to preserve the qualified pair-of-runs claim.

### 6. Code and test coverage

The 2,000-game fixture pins final winner, reason, macro and length—not intermediate cells, legal masks, search values, gradients or training reproducibility (`tests/test_rules.py:52-71`).

The 100,000-game cross-check can miss divergence: it skips references already done and checks terminal agreement only after the batch finishes, without comparing move counts or cells (`:85-99`). Compare **done, cells, macro, next board, player and move count after every ply**, including completed rows.

Add focused tests for:

- bounded **child enumeration**, shared-budget exhaustion and pooled rule propagation;
- tight-budget correctness under draw, not only generous-budget equivalence;
- tablebase payoffs versus the solver under both rules;
- terminal-value backup in both search implementations;
- resume/cache/refusal boundaries and actual `relabel()` behavior.

The printed suites and smoke runs are evidence supplied by the implementers, not tests I reran. This review used static inspection and arithmetic on saved outputs; no model or training execution.

## What is right and should remain

- Explicit training/evaluation-rule separation and unchanged opening positions.
- The payoff-independent tablebase with rule-specific outcome mapping.
- Independent rollout-rule threading.
- `None` for aborted bounded searches, never a game-value sentinel.
- The relabel control, `_e8` parent reread, common positions and two-score cross-play.
- Unchanged auxiliary targets, conditional frontier claims and “observed in this pair of runs.”