# Prioritised findings

1. **High — `PLAN7.md:149–155`: the five tiers are not a partition.** They mix evidence source, robustness and measurement recency; several claims occupy multiple tiers, and compound claims conceal changed components. This undermines the paper’s central audit. **Fix:** separate evidence level from drift status, split compound claims, and record the actual net/corpus coverage.

2. **High — `PLAN7.md:352–395`: K1 does not yet identify rule invariance.** Its parent is `_e8`, but most count-rule readings are from `_e4`. Comparing independently trained agents on different corpora additionally mixes rule effects, learning trajectories and position distributions. **Fix:** re-read the `_e8` parent, use common-position comparisons, and permit an “unresolved” verdict.

3. **High — `PLAN7.md:124`, `:237–240`, §3 C3: robustness is repeatedly promoted into game truth.** Regression associations become prices, insignificant coefficients become absence of effects, and sampled optimality becomes a solving milestone. **Fix:** retain the population, estimator and uncertainty in each claim’s headline—not only its caveat.

4. **High — `PLAN7.md:332–342`: J3’s outcome experiment is defective; J4 needs additional engineering.** Truly greedy self-play from one empty position repeats a trajectory, not 2,000 independent games. J3 also changes search budget while attributing the difference to exploration. The solver has no node-budget interface. **Fix:** specify the randomness and matched-budget control; implement and test cancellable solving before J4.

5. **Medium — `PLAN7.md:246–248`: the method comparisons exaggerate novelty.** Wang already varies epochs and reports playing strength; KataGo’s documentation permits increasing reuse; this repository’s symmetry ensemble operates throughout search, not just at its root. **Fix:** narrow the novelty claims and compare actual protocols.

6. **Medium — `PLAN7.md:125–129`, §6: external strength and compute comparisons are unsupported.** A locally implemented rollout baseline is not a measured CodinGame Legend bot. Rebuilding a forum recipe does not connect an agent to the arena’s rating scale. **Fix:** distinguish independent algorithmic baselines from externally calibrated opponents.

7. **Medium — `PLAN7.md:492–502`: reviewer calibration contains outcome bias.** Recommending an experiment was not predicting its success; the first review explicitly said so. **Fix:** assess recommendation quality against its stated uncertainty, cost and information value, separately from the experimental outcome.

## 1. The five tiers

**Keep the audit; replace the tier model.** Use separate columns:

- evidence level: exact theorem/tablebase, solver-anchored measurement, search-relative, predictive, behavioural, descriptive;
- replication coverage: named checkpoints, seeds, architectures and corpora;
- drift: compatible, changed magnitude, changed sign/order, unresolved, not measured.

“Inside the previous CI” is a descriptive compatibility rule, not an equivalence test or a confidence interval on the difference. Unequal precision can determine whether a claim “holds.” Where possible, compare estimates on identical positions and bootstrap their difference by source game.

Specific corrections:

- **31:** improvement without changing architecture argues against the previously asserted representational ceiling. It is not an exact causal diagnosis of optimisation versus capacity. Move its explanatory component out of E (`KNOWLEDGE.md`, claim 31).
- **31a:** split the exact tablebase construction from the network’s sampled accuracy. It currently appears in E and S. “100 / 100 / 100 on every net” contradicts the weaker-net results in the claim itself. Furthermore, `_e4`’s 689 positions came from **deep10’s** corpus, not its own: `runs/plan6/I1_C5_tablebase_grade.out`.
- **11:** the final raw-minus-search gap is compatible across measurements, but the training-path component reverses direction. The S assignment must not conceal that reversal (`KNOWLEDGE.md`, claim 11; `runs/plan6/I1_B3_value_decomp.out`).
- **14:** mixed, not uniformly M. Recomputing from `runs/plan5_A4_freemove_deep10_on_deep8late.out` and `runs/plan6/I1_A4_freemove.out`, the old centre CI is **[0.0300, 0.1094]**, containing the new **0.0489**; the edge CI **[0.0290, 0.0822]** contains **0.0382**. Only the corner estimate leaves its earlier A4 interval. The claim’s “every one” is false.
- **32:** the failure frequency moves, but the detailed motif ordering also changes: holding a draw overtakes giving a free move. Split the frequency, broad interpretation and detailed ordering. “One reversal” survives only for a carefully enumerated set of primary orderings—not every ordering in the claims file.
- **6:** N is incorrect as a coverage label. `runs/deep8_c1_300_e4/timeline.json` already records the opening trajectory: [40] carries 0.941 at iteration 20 and 0.950 at 30.
- **35:** retain “no resolved residual in this regression,” not “costs what its lines cost, no more.” The counterfactual component remains unrepeated; the claim is not uniformly S.
- **33–34:** separate solver-anchored statements from behavioural frequencies. The solver’s column is not a replication across networks. Its selected optimal move is also a deterministic tie-break (`tools/probe.py:77–92`); a frequency over that choice is not the frequency with which sacrifice is *necessary*.

S’s “all four strong nets” requirement is also unmet by several listed claims, including 8, 26, 35 and 40. Record actual coverage rather than expanding it by category membership.

## 2. One paper, its title, and its likely overclaim

**One game-centred paper is the right choice.** The training ledger explains construction of the instrument; measurement discipline explains its limitations. Neither requires a separate methods paper.

The working title is engaging but insufficiently qualified: “knows” encourages readers to confuse agreement with truth, and “Ultimate Tic-Tac-Toe” hides the variant. Prefer:

> **A strength-audited self-play analysis of closed-board, most-boards Ultimate Tic-Tac-Toe**

The likeliest overclaim is **turning robustness within one related agent family into validation of optimal strategy**. A sentence that survives:

> Across the specified networks and search budgets, several strategic associations persisted, while magnitudes changed and the preferred reply after [40] reversed; these are properties of the measured agents and position distributions, not proofs of optimal play.

The free-move result should read:

> On the specified natural-position corpus, the free-move indicator had an adjusted association of +0.195 utility with the 256-simulation search estimate, with a game-clustered 95% interval of approximately ±0.028.

Not “with everything else controlled,” and not a causal exchange rate against board ownership or macro threats (`PLAN7.md:237`; `tools/freemove.py`).

Likewise, the architecture conclusion should be **“this equal-cost D4 implementation lost under this recipe.”** Frozen-data overfitting and one lower-LR test do not establish the self-play mechanism as “capacity, not LR.” `KNOWLEDGE.md`, claim 48’s matched-parameter caveat already admits the unresolved data-regime issue. Keep that caveat; do not reopen the architectural programme merely to settle it.

## 3. K1: the right single run?

**Yes, as an exploratory matched-recipe rule comparison—not as a universal invariance test.** Its value is studying adaptation to the rule, not merely showing that terminal labels change.

First add a no-training control: relabel existing completed games under draw rules. From the rounded `_e4` corpus report, **16.5%** of outcomes change from count decisions to draws; **33.1%** reach the no-line terminal condition. Those are different quantities (`runs/plan6/I1_A6_corpus_stats.out`). This control measures mechanical relabelling without claiming unchanged agents would actually follow identical trajectories.

Before launch:

1. **Supply the missing parent readings.** Compare draw-trained `_e8` with count-trained `_e8`, not the existing `_e4` analysis. Amend §8’s prohibition on another full analysis pass accordingly.
2. **Separate estimands.** Evaluate both networks under both rules on a common frozen position set; report each network’s own-corpus results separately. Exact positions can additionally measure the rule-induced minimax-value change without a neural estimator.
3. **Sharpen predictions.** “Far above 16.6%” and “approximately zero” need numerical thresholds, populations, estimators and decision intervals. Positive coefficients should have a specified confidence criterion; rank predictions need a tie tolerance. Add **unresolved**, rather than interpreting matching signs as invariance.
4. **Define cross-play algebraically.** Two agents produce one independent match score per rule; colour-swapped cells are complementary. Pre-register the contrast between those scores and its paired-opening uncertainty.

The board-count prediction is especially weak. Count remains correlated with line opportunities under draw rules; removing terminal count reward does not force a regression coefficient to zero. The unchanged recipe also retains ownership and margin auxiliary supervision (`uttt/train2.py`, configuration; `uttt/selfplay_cont.py:159–169`).

One seed confounds the rule change with a particular optimisation trajectory, rule-by-recipe interactions, unequal learning progress and altered state visitation. The old two-seed, count-rule score spread bounds none of those reliably—and is not an uncertainty model for regression coefficients or opening ranks. No extra training run is compulsory, but the conclusion must remain **“observed in this pair of runs.”**

## 4. Comparators: corrections and omissions

- **Sample reuse:** withdraw “no dose-response exists” and “the lever nobody pulls.” [Wang et al., §§5.2 and 6.2](https://arxiv.org/html/2003.05988) vary epochs at fixed settings and report tournament Elo. Their different reuse regime is an important qualification, not grounds for erasing the precedent. Their default replay history is 20 iterations; show the conversion explicitly. A common optimum across different games, architectures and optimisers is not established.

- **KataGo:** its [training instructions](https://github.com/lightvector/KataGo/blob/master/SelfplayTraining.md) describe four samples per new row as conservative and explicitly permit increasing it. That is not a universal warning against exceeding one. The honest contribution is a positive, local 1→8 sweep under a documented recipe.

- **Symmetry:** `SymmetryAveragedEvaluator` averages both policies and values (`uttt/symmetry.py:35–48`), and the search invokes it at roots **and expanded leaves** (`uttt/search.py:180–182`, `:250`). Thus +35 is not a measurement of KataGo’s root-only trick. Preserve the measured ensemble result; withdraw the claimed protocol identity.

- **pc29277:** its [README](https://github.com/pc29277/AlphaZero_UTTT) already reports fixed opponents, colour-paired openings and confidence intervals. “First calibrated” needs a definition that does not arbitrarily exclude that work. Recomputed local logs give 1,501,606 games for `_e8`, approximately **52.6×** its reported 28,544; the reported durations are approximately 22 hours on different GPUs. Neither establishes “two orders of magnitude less compute.”

- **External calibration:** `uttt/rollout.py:1–10` describes uniform playouts and no tree reuse. The Legend recipe includes additional search machinery. L1 would create another reproducible baseline, not an arena rating anchor without an independently rated opponent.

- **Opening comparison:** [gPress](https://gpress.soopergrape.com/index.php/2025/06/26/n-in-a-row-games-part-3/) reports 8.16 versus 6.47 for centre-edge versus corner-home. “A tie on both” is unsupported: its uncertainty and scale are undocumented.

**Missing from §2’s central comparison:** exploitability and common blind spots. D’Alberton’s best-response study is already identified in `knowledge/07`, §2.4, but its lesson never reaches the stability argument. Agreement among related networks is not adversarial validation. Verify the thesis’s rule variant before using its results; its primary page could not be independently retrieved here.

Also repair the inherited solver background: `knowledge/06` mislabels Elhage as open-board in places, constructs no defensible reachable-state lower bound, and incorrectly treats the count tiebreak as requiring a richer-than-WDL outcome space. `uttt/solver.py` already reduces it to −1/0/+1.

## 5. The staged review protocol

The stages, immutable reviews, explicit adjudications and rebuttal round are sound. Keep them.

Changes:

- Freeze each review’s commit, artifact manifest and claim IDs. Record unresolved disagreements alongside verdicts.
- Review **J3/J4’s designs before execution**, not just their eventual manuscript wording.
- Separate “finding correct?” from “remedy worth buying?” and “experiment succeeded?” The first review expressly denied that symmetry must improve Elo (`docs/history/REVIEW-astra.md`, §1). Its negative result cannot alone establish that recommending the experiment was confidently wrong.
- Change this brief’s calibration paragraph to quote that uncertainty rather than supply a retrospective verdict.
- Make reproduction feasible in the specified sandbox: distinguish recomputation from saved JSON from rerunning models, identify permitted unsealed datasets, and do not require script-file deliverables from a read-only reviewer.
- Apply “nothing outside KNOWLEDGE” to **empirical claims**, not literally every manuscript sentence; methods, definitions and cited literature need their own provenance.

## 6. Code and log checks

I recomputed scores directly from the 516 per-opening records, then applied \(400\log_{10}(s/(1-s))\):

| Comparison | Score | Elo |
|---|---:|---:|
| `_e2` versus 1× parent | 63.9535% | +99.600 |
| `_e4` versus `_e2` | 59.0601% | +63.659 |
| `_e8` versus `_e4` | 55.7655% | +40.242 |
| G-CNN versus `_e4` | 21.9961% | −219.908 |

These validate the headline point estimates in `runs/*/paired_vs_*.json`. The saved books also confirm the [40] reply reversal.

Further corrections:

- **J3:** zero Gumbel noise does not disable opening-policy sampling (`uttt/search.py:308–318`). Either disable sampling and report the deterministic line, or define the stochastic experiment. Compare exploration settings at the same simulation budget.
- **J4:** `uttt/solver.py:90–99` explicitly has no node budget. Aborted searches must return **unknown**, with safe cancellation. Report solvability conditional on games still alive at each ply and optimality conditional on solved samples—not “solved from ply N.”
- **K1 plumbing:** include `uttt/tablebase.py:76–90`, probe/puzzle labels, evaluator construction and rule-tagged cached datasets. Distinguish a checkpoint’s training rule from its explicit evaluation rule.
- **Reuse accounting:** exact labels overwrite existing rows; they do not add 8,192 positions (`uttt/selfplay_cont.py:241–247`). The survey’s 0.97 multiplier is wrong. Logged sampled rows divided by inserted rows give **1.0026, 2.0027, 4.0054, 8.0109**.
- `KNOWLEDGE.md` contains **56 numbered claims**, not 55.

This was a read-only source/JSON audit; no checkpoints, game archives or sealed suites were opened. GPU tests were not rerun.

## What should not change

- One game-centred paper, with training and measurement supporting it.
- Explicit rule variants and named opponents/search budgets.
- The paired suite, final-checkpoint discipline and distinction between adoption and equivalence.
- Solver-anchored samples and visible corrections to earlier claims.
- Publishing the negative architectural result without buying another architecture campaign.
- K1’s owner-approval gate and the decision not to pursue a full solve.