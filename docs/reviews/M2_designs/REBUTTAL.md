## (a) Margins

**Keep 0.005 and 0.03 as practical margins, not precision-derived thresholds. Change the decision rules.**

The printed 95% half-widths are approximately 0.028 for free moves, 0.018–0.021 for threats, and **0.0118/0.0122** for search/raw count-margin coefficients (`runs/plan6/I1_A4_freemove.out`; `I1_B3_value_decomp.out`, final-checkpoint table). With independent, equally precise estimates, difference half-widths would be about **0.040**, **0.025–0.030**, and **0.017**, respectively. Pairing can reduce these; the saved marginal intervals cannot establish how much. The proposed 4,000-position common set is also smaller than those earlier samples.

Thus 0.005 is an ambitious resolution target, but a meaningful fraction of the existing +0.0139 search coefficient. Do not enlarge it merely to manufacture power.

For claims 8/13, **a point difference below 0.03 is not equivalence**. Set:

- invariant: the entire paired 95% interval lies within \((-0.03,0.03)\);
- dependent: the interval lies wholly beyond either boundary;
- unresolved: otherwise.

For the count prediction, distinguish “negative difference, estimate at least 0.005” from “established decrease of at least 0.005.” The latter requires the upper interval endpoint ≤−0.005. I would use that stricter reading, with contradiction when the interval lies wholly above −0.005. Freeze the estimator and assess paired precision before interpreting an unresolved result.

## (b) Kept refusals

**The premise does not match commit `465e764`.** `tools/value_decomp.py:92-97` loads the dataset without checking its rule; `tools/tablebase_grade.py:39-43` likewise. Only `tools/ownership_grade.py:144-147` implements the stated refusal.

I accept conservative defaults, **not the rationale that positions sampled under another rule are inherently invalid**. That would obstruct K1’s common-position control. Rebuilding is acceptable only if position IDs, sampling and weights remain identical; otherwise it changes the population. Keep source-corpus rule, label rule and evaluation rule distinct. Correct the adjudication’s description rather than adding unnecessary refusals.

## (c) Did the remedies land?

Mostly:

- **Resume:** the configuration-rule refusal precedes filesystem writes (`uttt/train2.py:255-270`). However, an orphaned/copied checkpoint without `config.json` bypasses it. Check checkpoint `cfg.rule` before restoration, and reject ambiguous existing run directories before writing new provenance.
- **Cache:** `(sims, rule)` plus the assertion fixes the rule collision (`uttt/endgame.py:291-297`). An old integer-key cache is ignored, not rejected as the notes suggest. Dimensions and evaluator identity remain caller obligations.
- **Rollout:** explicit rule validation and construction landed correctly (`uttt/endgame.py:303-313`).
- **Draw sampling:** seeded sampling without replacement over all draws is correct (`tools/principles.py:95-106`).
- **J3:** plain game-playing evaluators and the corrected interval interpretation landed (`tools/empty_board.py:124-131,249-251`). The paired trajectory rows are chronological context, not same-teacher measurements: checkpoint N is produced **after** iteration N−1’s generation (`:169-182`).
- **J4:** renamed coverage fields, Wilson intervals and retained position records landed. But the saved move comes from a second search; disagreement merely warns while pairing that move with the first search’s regret (`tools/frontier.py:357-364`). Export the actual graded move, or mark mismatched records invalid.

The one-line, O-winning J3 smoke demonstrates **sensitivity to evaluator and search settings**, not O’s game-theoretic advantage. Keep the registered 256-simulation experiment. Two thousand independent draws can estimate a concentrated policy accurately; they do not provide broad opening coverage. If all 2,000 were O wins, Wilson’s lower endpoint would be approximately **99.81%**, still only for that policy. Claim 24 concerns exploratory, changing training policies; disagreement would not refute its corpus statistic.

## (d) Launcher

The training arguments and draw-rule worker are consistent with the intended intervention (`runs/queue14.sh:54-55`). **Fix failure handling before launch:**

- `run_train` failure does not prevent post-processing (`:55-56`).
- The post-run script selects the latest available checkpoint, potentially an incomplete run’s.
- Command failures inside post-processing are not propagated reliably.
- The background worker can remain waiting after terminal training failure.

Require successful training, `DONE` and `net_0300.pt`; retain/check the worker PID and exit status; stop it on terminal failure; make analysis failures return nonzero.

Items 0/1 are documented. Items **2, the common-position part of 3, 5, and the joint contrast bootstrap** remain separate work, not completed by these scripts. Freeze their commands, sampling and estimator definitions before outcomes are inspected.

The independently WDL-stratified count/draw endgame sets are **not identical-position twins**. Their differing source-game counts already demonstrate this (`K1_prep_endgame_v2_draw.out`; parent `analysis.out:134`). Keep those diagnostic reads, but never substitute them for item 3.

## (e) Disputes

**Row 6:** accept the explicit orphan-corpus declaration. However, `games_rule()` ignores untagged files when tagged files exist (`tools/corpus_stats.py:43-52`); one draw tag cannot establish every untagged file’s provenance. Test mixed tagged/untagged directories.

**Row 14:** accept declining optional decision/gradient instrumentation given no committed consumer. State that the resulting mechanism questions remain unavailable, not retrospectively recoverable.

The substantive outstanding misreading is row 12’s point-estimate “invariant” criterion: it still does not implement equivalence. No models or training were run for this rebuttal.