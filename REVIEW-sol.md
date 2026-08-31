# REVIEW-sol: technical and research review of `uttt-zero`

## A. Summary verdict

This is a strong research prototype with an unusually coherent end-to-end pipeline. The reference and batched engines are separately implemented and heavily cross-checked; the v2 search has explicit eager/graph comparisons; self-play, exact solving, persisted corpora, paired play, endgame regret, and provenance-aware analyses are all real rather than aspirational. In a static pass I did **not** find a new rules-engine, side-to-move sign, legality, or solver defect. I also deliberately do not repeat any of the ten findings in `REVIEW-codex.md`, which the hand-off marks closed.

The main weakness is now the experimental layer, not basic game correctness. `PLAN3.md` overstates three conclusions: that measurement is finished, that width scaling has not flattened, and that brute scaling is the only live strength lever. The current best checkpoint is the best at **64 simulations per move**, but it is not yet shown to be best at equal latency, equal GPU-hours, or equal deployment cost. The adjacent 64→96→128 width gains are smaller than the stated noise rule and have not been replicated across training seeds. The proposed `--games 8192` run also changes data volume, optimizer work, replay age, learning-rate exposure, and exact-label fraction at once, so it is not a clean batching experiment.

There is meaningful throughput left on the table before buying more width/depth: every search evaluation recomputes legality up to four times, inference computes two auxiliary heads it discards, CUDA-graph search evaluates every row even when no expansion is required, the dense tree is about 1.1 GiB at 8192×64 before graph temporaries, replay sampling repeatedly traverses a two-million-row distribution, and checkpoint/replay maintenance is omitted from the reported “wall-clock.” These are measurable, actionable opportunities.

My overall verdict is therefore: **the engine is credible and the strength trend is promising, but the next research phase should first establish equal-compute evaluation, immutable experiment provenance, sealed evaluation sets, and training-seed uncertainty; then optimize target generation and the existing GPU path; only then commit to deeper/wider 300-iteration runs.**

Scope note: this was a static review of the documentation, source, tests, suites, run scripts, recorded logs/results, and web path. Per the task constraints, I did not run tests or training.

## B. Numbered findings, ordered by importance

### 1. “Strongest” currently means equal simulations, not equal compute or equal latency

**Confidence: High.**

**Evidence.** The headline ladder fixes every network at 64 simulations (`PLAN3.md:44-58`), while the hand-off itself reports materially different costs: about 2.3 h for 6×64, 3.8 h for 6×96, and 4.5 h for 6×128 (`PLAN3.md:60-62`). At the final 64-simulation stage, recorded iteration 149 throughput is 97.6 games/s for v2b, 56.9 for `wide96_c1`, and 44.1 for `wide128_c1` (`runs/v2b/log.jsonl:150`, `runs/wide96_c1/log.jsonl:150`, `runs/wide128_c1/log.jsonl:150`). Thus the 128-wide model costs about 2.2× as much per self-play game as v2b at the same search budget.

That difference is inherent in the implementation: there is one root network evaluation and one full-batch evaluation for every simulation (`uttt/search.py:241-242`, `uttt/search.py:266-278`), and the residual trunk's dominant convolutions scale approximately quadratically with channel width (`uttt/model.py:39-45`, `uttt/model.py:58-65`). Meanwhile, search is far from saturated: v2b at 256 simulations beat the same v2b at 64 by 78.4% / about +224 Elo (`PLAN2.md:47-48`). This does not prove that a narrow net at a matched-time larger search budget beats `wide128_c1`; it proves that the relevant comparison has not been run.

**Risk.** “Current best” is valid only under the artificial constraint “same number of network calls.” It may select the wrong deployment model, wrong self-play teacher, and wrong direction for the next GPU-hour. Width can improve sample quality while reducing games/s; more simulations on a narrower net can improve the policy teacher while retaining cheaper inference. The project has not mapped that trade-off.

**Recommendation.** Build a Pareto frontier over at least 6×64, 6×96, and 6×128 crossed with several simulation budgets. Measure both batch-1 latency (web/CodinGame use) and production batched latency at fixed wall-clock per move, including p50/p95, peak memory, and evaluated positions/s. Run direct paired matches at matched time, not only matched simulations. Report Elo against milliseconds/move, GPU-hours per million positions, and memory. Choose the play agent and self-play teacher from that frontier; they need not be the same model.

### 2. The reported confidence intervals do not support “width has not flattened” or a universal ±3-point decision rule

**Confidence: High.**

**Evidence.** Opening-suite CIs resample opening-pair outcomes from one already-trained checkpoint (`uttt/openings.py:227-245`). They do not include training stochasticity. Almost all recipe runs use seed 0; the sole explicit replicate is v2b seed 1 (`runs/v2b/config.json:37`, `runs/v2b_s1/config.json:49`, `runs/abl_cscale1/config.json:49`, `runs/wide96_c1/config.json:49`, `runs/wide128_c1/config.json:49`). One pair of baseline seeds cannot estimate the variance of wide or `c_scale=1` training.

The c-scale-1 width ladder is 55.7%, 58.4%, and 60.9% against the common v2b anchor (`PLAN3.md:55-58`; raw summaries at `runs/abl_cscale1/paired_vs_v2b_64.json:41-46`, `runs/wide96_c1/paired_vs_v2b_64.json:41-46`, and `runs/wide128_c1/paired_vs_v2b_64.json:41-46`). The adjacent increments are only +2.7 and +2.5 points, both below PLAN3's own “believe only above +3 points” rule (`PLAN3.md:36-39`). Joining the stored 516 per-opening records by id (`...paired_vs_v2b_64.json:160` onward) gives normal-approximation paired-difference intervals of approximately:

- 96-wide c1 minus 64-wide c1: +2.71 points, 95% interval −1.18 to +6.61.
- 128-wide c1 minus 96-wide c1: +2.42 points, 95% interval −1.34 to +6.18.
- 128-wide c1 minus 64-wide c1: +5.14 points, 95% interval +1.15 to +9.12.

These calculations are a diagnostic, not a replacement for a preregistered bootstrap, but they show the appropriate conclusion: the endpoint trend is positive conditional on these checkpoints; neither adjacent step is resolved. In addition, the same full suite has been inspected after many adaptive experiments, so nominal 95% intervals do not account for repeated looks, winner selection, or suite overfitting.

**Risk.** The project can mistake a selected seed/checkpoint fluctuation for a scaling law, dismiss real small effects using an ad hoc threshold, or overstate negative ablations. Bootstrap uncertainty over openings and run-to-run uncertainty answer different questions and cannot substitute for one another.

**Recommendation.** Keep the current suite as a development suite, create a sealed confirmation suite that is not read during tuning, and replicate at least the base plus each finalist across three independent training seeds. Use paired per-opening deltas when two candidates share a suite/anchor, and a hierarchical analysis whose top level is training seed and lower level is opening/source game. Predeclare the primary score, final checkpoint rule, and stopping criterion; correct or explicitly caveat multiple adaptive looks. Until then, change the wording to “64→128 is a positive endpoint trend; the 64→96 and 96→128 increments are unresolved.”

### 3. `--games 8192` is a compound training intervention, not a nearly-free batch-size experiment

**Confidence: High.**

**Evidence.** `games` controls both the search batch and the nominal amount of new training data: positions per iteration are `games * steps` (`uttt/train2.py:38-39`), the self-play object is constructed at that batch size (`uttt/train2.py:197`), and optimizer steps are `epochs * games * steps / batch` (`uttt/train2.py:260`). Doubling 4096→8192 at the current settings therefore changes approximately 262k→524k positions and 256→512 SGD steps per iteration. With the buffer fixed at two million rows (`uttt/train2.py:54`), the replay window falls from roughly 7.6 to 3.8 iterations. Learning-rate drops and evaluation cadence remain iteration-based (`uttt/train2.py:221`, `uttt/train2.py:238-253`, `uttt/train2.py:280-285`), so the model sees twice as many samples before each drop/evaluation. The fixed 8192 exact labels per iteration (`uttt/train2.py:76-79`) also become half the fraction of incoming data.

The memory change is nontrivial. At 8192 games and 64 simulations, each edge-shaped tensor contains `8192 * 65 * 81 = 43,130,880` elements. `children` alone is about 329 MiB as int64, and `prior`, `logits`, `N`, and `W` total about 658 MiB as float32 (`uttt/search.py:45-65`). Including state/legal arrays puts one search object at roughly 1.1 GiB before evaluator, self-play history, replay, optimizer, CUDA-graph workspaces, or capture snapshots. `_simulate_graphed` temporarily clones essentially the whole tree for capture (`uttt/search.py:204-223`).

Finally, “the wide nets are GPU-bound, so batch scaling is nearly free” (`PLAN3.md:105-108`) is not established by a utilization curve. If the network is already compute-bound, twice the examples cannot be assumed free; at best batching may improve occupancy enough to make time grow sublinearly.

**Risk.** A positive or negative 8192-game result would be uninterpretable: it simultaneously tests occupancy, data volume, optimizer updates, replay freshness, schedule timing, and label mixture. It may also run out of graph-capture headroom when phase pools or larger search budgets are added.

**Recommendation.** First run an isolated, inference-only batch sweep (512 through the largest safe batch) for every candidate width and simulation budget, recording throughput, latency, utilization, and `max_memory_allocated/reserved`. Then separate `search_batch_size`, `positions_per_iteration`, optimizer samples, replay age in positions, and LR schedule in samples. For a clean training comparison, keep total generated positions, optimizer examples, replay-age distribution, exact-label fraction, and evaluation sample count fixed. Add phase pools only after measuring their combined peak memory.

### 4. Experiment provenance is a prerequisite, not end-of-plan housekeeping

**Confidence: High.**

**Evidence.** PLAN3 acknowledges that there is no Git repository and puts source control/backups last (`PLAN3.md:124-126`). The trainer writes only the current dataclass config (`uttt/train2.py:186-189`) and stores that config with checkpoints (`uttt/train2.py:286`, `uttt/train2.py:290-293`). It does not record a source revision/diff, suite hashes, dependency lock/hash, exact command line, driver/CUDA/cuDNN versions, GPU clocks, or host state. The source evolved materially across the run series, so a run directory's `config.json` is insufficient to prove which implementation produced it. The config is also overwritten whenever `main` starts in an existing run directory (`uttt/train2.py:186-188`).

**Risk.** Differences attributed to width, targets, or labels can silently include code changes. Old results cannot be exactly reproduced or audited, and a future refactor may make an anchor name point to behavior different from the behavior that generated its report. This is more serious now that effect sizes are a few points.

**Recommendation.** Before another run, put source and small metadata under version control. Make every run write an immutable manifest containing commit id, dirty diff hash/content, command line, config, suite/checkpoint SHA-256s, Python/Torch/CUDA/cuDNN versions, device name, and seed. Refuse to overwrite an existing run manifest. Keep large checkpoints/corpora in LFS, DVC, or a separately checksummed artifact store. The report for every comparison should name both checkpoint hashes and the evaluator/search code revision.

### 5. The opening-suite “overall” CI pools incompatible sampling designs, and the natural score has an ambiguous estimand

**Confidence: High.**

**Evidence.** The paired/color-swapped unit is a good design, but the four strata are not draws from one population. Empty and the 15 orbits are deterministic coverage sets; natural openings are distinct canonical prefixes sampled without replacement with probability proportional to corpus count (`uttt/openings.py:74-84`); random openings are distinct canonical legal sequences from a different generator (`uttt/openings.py:87-101`). Yet `summarize` pools all 516 pair scores and bootstraps them as exchangeable observations (`uttt/openings.py:227-245`, `uttt/openings.py:259-264`). The resulting headline is an arbitrary near-50/50 natural/random mixture plus coverage rows.

For the natural sample, selected prefixes are subsequently weighted equally. Probability-proportional-to-size sampling without replacement followed by an unweighted mean is not generally the corpus-frequency mean; that target would require known inclusion probabilities/appropriate weights, or sampling corpus games with replacement. Conversely, if the target is “a uniformly weighted set of distinct openings selected by PPS,” it should be named as such. PLAN2 recommended natural as the headline and random as robustness (`PLAN2.md:53-56`), whereas PLAN3's ladder uses the pooled overall score (`PLAN3.md:44-58`).

**Risk.** The nominal ±2.8-point interval has no single clean population interpretation. A model can gain on the broad random generator and be declared stronger overall despite no gain on natural play, or vice versa. Resampling deterministic coverage rows also manufactures sampling uncertainty for rows that were not sampled.

**Recommendation.** Define primary estimands before evaluation. A sensible set is: (1) expected score under a frozen natural corpus distribution, using corpus-frequency weights or a with-replacement game-prefix sample; (2) an equally weighted distinct-opening robustness score; and (3) empty/orbit coverage reported descriptively. Bootstrap within natural/random strata and combine only using explicit prespecified target weights; never resample empty/orbit coverage as if iid. Preserve per-opening outcomes so candidate deltas can be clustered by underlying opening.

### 6. Canonicalizing each opening to one D4 orientation leaves a systematic orientation bias outside the CI

**Confidence: High.**

**Evidence.** Natural and random sequences are replaced by the lexicographically smallest D4 image (`uttt/openings.py:40-63`, `uttt/openings.py:80-100`). Training applies independent random D4 augmentation (`uttt/train2.py:100-112`), but the ordinary convolutional network is not exactly group-equivariant (`uttt/model.py:39-75`). Exact equivariance exists only through the eight-way wrapper (`uttt/symmetry.py:1-5`, `uttt/symmetry.py:25-37`), and the dedicated test explicitly measures base-versus-averaged disagreement (`tests/test_symmetry_eval.py:25-38`). Full-suite matches use a plain `FusedEvaluator`, not the symmetry-averaged wrapper (`tools/openings.py:32-50`). PLAN3 itself reports a 1–2-point WDL effect from symmetry averaging (`PLAN3.md:113-115`).

**Risk.** Every symmetry class is evaluated in the arbitrary “smallest index” orientation. Residual orientation errors, convolution boundary effects, and fp16 argmax ties can systematically favor one checkpoint. Pairing colors does not cancel orientation. The current bootstrap treats that chosen orientation as fixed and therefore cannot reveal the sensitivity.

**Recommendation.** Evaluate all unique D4 images of each base opening and cluster the analysis at the base-opening level, or use the symmetry-averaged evaluator for the measurement path. Report orientation spread and verify that candidate ordering is invariant. If 8× games is too expensive for every in-run curve, use one balanced rotation panel in development and reserve the full eight-orientation confirmation for finalists.

### 7. Target quality and reanalysis are higher-priority strength levers than another blind depth/width run

**Confidence: High.**

**Evidence.** The largest cost-free gain came from changing only the completed-Q scale used to form the Gumbel improved-policy target (`PLAN3.md:68-70`; implementation at `uttt/search.py:101-115`). That is direct evidence that teacher/target formation is not exhausted. However, training exposes only `c_scale`; inherited `c_visit=50` and `m_considered=16` remain fixed defaults (`uttt/mcts.py:31-39`, `uttt/train2.py:40-48`, `uttt/train2.py:193-195`). There is no systematic sweep of their interaction with simulation budget, target entropy, policy KL, or value-Q spread.

The pipeline also already stores search information it does not exploit. Self-play saves the improved policy and root value (`uttt/selfplay_cont.py:23`, `uttt/selfplay_cont.py:117-126`, `uttt/selfplay_cont.py:151-159`), but training consumes the policy and terminal outcome only (`uttt/train2.py:123-137`). It is correct not to use the scalar root value naively as a WDL target, but replay positions could be re-searched by a newer/better teacher. The +224 Elo 64→256-simulation self-match (`PLAN2.md:47-48`) shows a large teacher gap.

**Risk.** Scaling the student while leaving a weak or poorly tuned 32→64-simulation teacher fixed can spend most new FLOPs fitting a bounded improvement of the current prior. The width gains may partly compensate for target deficiencies rather than reveal a clean architecture scaling law.

**Recommendation.** Before 8/10×128, run a small target study crossing `c_scale`, `c_visit`, `m_considered`, and simulation budget while holding generated positions and GPU-hours fixed. Log improved-policy entropy, KL(target || raw policy), number of considered actions, Q range, and subsequent policy fit. Then reanalyse a controlled fraction of replay—preferably high-surprise/high-entropy or recent states—with the latest/best network at 128–256 simulations, asynchronously if possible. Compare strength per GPU-hour against pure online self-play. A practical deployment path is to distill high-budget policies into a smaller, faster student rather than require the widest net at play time.

### 8. The exact-label negative result rules out label correction, but does not establish a representation-capacity limit

**Confidence: High.**

**Evidence.** PLAN3 concludes that because 98.7% of self-play outcomes at ≤14 empties match exact values, the remaining endgame error is representational (`PLAN3.md:71-77`; detailed claim at `PLAN2.md:175-183`). The experiment does show that replacing already-mostly-correct outcomes/policies in a small slice of replay is ineffective. It does **not** distinguish network capacity from sampling frequency, class imbalance, optimization, loss interference, or target weighting.

Exact candidates are capped at 8192 per iteration (`uttt/exact.py:39-55`, `uttt/train2.py:76-79`) and made up about 2.7% of the final buffers (`runs/wide128_c1/log.jsonl:150`). The value head receives one global unweighted cross-entropy over replay outcomes (`uttt/train2.py:123-137`), whose self-play draw prior is much lower than the deliberately balanced endgame set. Widening from 64 through 128 did not materially repair draw recognition (`PLAN3.md:72-77`), which is evidence against “just add capacity.” Post-hoc calibration failing to move Elo also does not prove that a training-time class-balanced objective or better leaf representation cannot help; those interventions alter learned features and policy/value coupling, not just logits at inference.

**Risk.** Misdiagnosing an optimization/data-mixture problem as capacity pushes the programme toward the most expensive lever and prematurely dismisses class-balanced or curriculum approaches.

**Recommendation.** Run a diagnostic overfit experiment on a **training split** of balanced exact endgames using the existing 6×64 model. If it cannot approach near-perfect train accuracy/regret, capacity/optimization is plausible; if it can, the online mixture/weighting is the issue. Then test stratified late-state minibatches or W/D/L-balanced value loss while keeping total optimizer examples fixed, and confirm on a sealed endgame test split. Treat “labels are already correct” and “the model cannot represent the mapping” as separate hypotheses.

### 9. The inference/search hot path repeats avoidable kernels on every simulation

**Confidence: High.**

**Evidence.** For every root and leaf evaluation, legality is computed inside `FusedEvaluator` (`uttt/infer.py:62-70`) and again inside `encode` (`uttt/batch.py:210-232`). Search then recomputes it for the root/expanded child (`uttt/search.py:96`, `uttt/search.py:172-175`, `uttt/search.py:241-255`). In the common path this is up to four equivalent legal-mask constructions per network call. `encode` builds float32 planes and inference immediately converts them to fp16 (`uttt/batch.py:225-232`, `uttt/infer.py:64-68`). The network's ordinary `forward` always evaluates ownership and margin heads (`uttt/model.py:69-75`), even though inference discards them with `*_` (`uttt/infer.py:69`). These are small operations, but small operations matter in the documented Windows/WDDM launch-bound regime.

Continuous self-play also performs host synchronizations for diagnostics on every ply via `float(tensor)` (`uttt/selfplay_cont.py:117-129`) and several scalar statistics/conversions when games finish (`uttt/selfplay_cont.py:133-180`). They are not per simulation, so they are secondary, but they are easy to accumulate on-device.

**Risk.** Extra launches and memory traffic are paid 33–65 times per move across thousands of games. This directly reduces self-play games/s and makes larger batches appear necessary before the existing kernel path is clean.

**Recommendation.** Compute legality once in search, pass it into both the encoder and evaluator, and pass expanded-child legality into `_put_slot`. Provide an inference-only forward that emits only policy and WDL. Build fp16 channels-last planes directly into a reusable buffer, or fuse encoding/legal masking with `torch.compile`/Triton after profiling. Accumulate self-play metrics on GPU and transfer once per iteration. Use Nsight Systems/Compute or at least CUDA-event timings and kernel counts to verify each change; do not infer gains from Python wall time alone.

### 10. Replay-buffer maintenance, sampling, and checkpoint I/O are both under-instrumented and likely optimizable

**Confidence: High.**

**Evidence.** Every iteration recomputes `torch.unique(..., return_inverse=True, return_counts=True)` over up to two million hashes (`uttt/selfplay_cont.py:237-260`). Every one of the 256 current training steps independently calls `torch.multinomial` on the full weight vector (`uttt/selfplay_cont.py:262-264`, `uttt/train2.py:115-124`, `uttt/train2.py:260-263`); an 8192-game run would make 512 such calls. The exact backend complexity should be profiled rather than assumed, but rebuilding/reading the same categorical distribution hundreds of times is avoidable.

The published timing cannot reveal the cost. `t_selfplay` stops before compressed game persistence, buffer insertion, exact submission, and `update_weights`; `t_train` begins afterward (`uttt/train2.py:245-267`). Every tenth `GPUReplayBuffer.state_dict` synchronously copies the entire live GPU buffer to CPU (`uttt/selfplay_cont.py:266-267`), and checkpoint serialization occurs after the logged timers (`uttt/train2.py:286-293`). Nevertheless `runs/eval_run.sh` labels the sum of only `t_selfplay + t_train + t_eval + t_exact_wait` as “wall-clock” (`runs/eval_run.sh:8-13`).

**Risk.** Reported run duration and games/s omit exactly the costs that may grow most at 8192 games or a larger replay window. Optimizing only the timed regions can move work outside the metric without improving end-to-end throughput.

**Recommendation.** Add an outer iteration timer and separate CUDA-synchronized timings for game D2H/compression, buffer add, dedup/hash update, sampler construction, index sampling/gather, forward/backward, evaluator refresh, exact labeling, evaluation, checkpoint D2H, and disk write. Cache a CDF/alias sampler after weights change or draw all training indices for an iteration in one call. Benchmark incremental hash-count maintenance across ring insertions/evictions against full `unique`. Move replay checkpoints through pinned CPU memory to an asynchronous writer, or checkpoint deltas plus periodic full snapshots. Report actual process elapsed time and throughput in completed positions per end-to-end second.

### 11. Dense fixed-shape search is approaching a memory/bandwidth wall, and the CUDA-graph benchmark is not apples-to-apples

**Confidence: High for the diagnosis; Medium for which replacement wins.**

**Evidence.** The search stores dense state, legality, priors, logits, children, visits, and value sums for every possible slot/action (`uttt/search.py:45-65`). It evaluates the full `n` rows after selection regardless of whether a row actually needs expansion (`uttt/search.py:123-186`), including terminal or depth-capped rows. At 8192×64 the persistent search object is about 1.1 GiB as calculated in finding 3; graph capture clones most of it (`uttt/search.py:204-223`). A phased player creates a separate full `BatchedSearch` for every budget (`uttt/arena.py:63-68`).

The current benchmark compares eager with its default depth cap 32 against graph with depth cap 12 (`tests/test_search_graph.py:65-78`). The measured difference therefore combines CUDA-graph launch savings with 20 fewer selection/backup levels. Correctness comparisons do use matching caps (`tests/test_search_graph.py:26-40`), but the performance comparison does not. Inference benchmarking covers only one 6×64 network at batch 4096 (`tests/test_infer.py:33-42`), not the width/batch regime proposed next.

There is also a small diagnostic correctness issue: graph capture snapshots/restores tree tensors but not `cap_hits` (`uttt/search.py:204-223`), although `_simulate` mutates `cap_hits` at the depth cap (`uttt/search.py:181-182`). The first capture executes warmups, capture, and replay, so a freshly constructed depth-cap graph can overcount that first call's truncations. This does not change moves, but it can contaminate the metric used to justify cap 12.

**Risk.** Scaling batches, budgets, and phase pools can exhaust memory or spend most time evaluating dummy rows. The existing benchmark can over-credit graph replay and understate depth-cap cost.

**Recommendation.** Run a 2×2 benchmark: eager/graph crossed with cap 12/32, identical states/evaluator/batch, warm capture excluded, explicit synchronization, multiple repetitions, p50/p95, and peak allocated/reserved memory. Sweep batch and network width, and profile root evaluation, selection/backup, leaf evaluation, and capture separately. Fix `cap_hits` capture semantics. Then benchmark, rather than assume, compact alternatives: bucket active leaves into a few fixed graph sizes and scatter back; use narrower validated storage (`children` need only address `n_sims+1` slots, and priors/logits may tolerate fp16); remove redundant dense fields; and measure a state-evaluation cache/dedup path for the extremely duplicated early tree states. Retaining a chosen-child subtree or at least cached network evaluations across moves need not preserve the old root sequential-halving schedule; the root schedule can be rebuilt while reusing evaluations.

### 12. The “equal mean cost” phased-search result is not equal actual GPU work in the paired arena

**Confidence: High.**

**Evidence.** Paired games remain in a full-size batch until the longest game finishes (`uttt/openings.py:186-196`). `PhasedSearchPlayer` chooses a budget from the maximum batch ply and invokes a full-size search (`uttt/arena.py:59-75`). `BatchedSearch.search` still runs the root evaluator and every simulation over terminal rows (`uttt/search.py:228-285`), relying on masks only to suppress their logical effect. Thus after shorter games finish, the expensive late 96-simulation phase continues to evaluate their rows until the batch tail ends.

The reported 32-until-ply-24/96-after schedule is called equal mean cost to uniform 64 (`PLAN3.md:80-82`; `PLAN2.md:394-400`). That nominal average is based on game plies/simulation counts, not synchronized batch wall-clock or neural evaluations. With a longest game materially longer than the mean, the late high-budget tail can be appreciably more expensive than uniform 64.

**Risk.** Some or all of the reported +50 Elo may buy extra real compute. The same issue can make a proposed two-pool self-play implementation cost far more memory/work than its per-game schedule suggests.

**Recommendation.** Re-run schedule comparisons at equal measured wall-clock per side and report network-evaluated rows, simulation-row products, peak memory, and energy if available. For evaluation, compact active games or bucket them by active batch size and scatter results. For self-play phase pools, allocate/search only the members of each pool rather than two full original-batch search objects. Tune the phase boundary and budgets on an actual latency budget, not nominal mean simulations.

### 13. Brute width/depth is being tested before a UTTT-structured or exactly equivariant architecture

**Confidence: Medium-High.**

**Evidence.** The encoder maps the game to a conventional 9×9 grid (`uttt/batch.py:27-39`, `uttt/batch.py:210-232`), and the model applies an ordinary stack of translation-shared 3×3 convolutions followed by flattened policy/value heads (`uttt/model.py:39-75`). That representation is workable, but it gives the same local operator to within-board adjacency, across-board boundaries, and macro-scale relations. The network must learn the macro/micro hierarchy and boundary semantics from data. It is also only augmentation-equivariant, not exactly D4-equivariant (finding 6).

The current evidence says extra channels help at equal simulations; it does not say dense 9×9 width is the most compute-efficient way to add capacity. The 64→128 endpoint roughly quadruples dominant convolution work and more than halves final self-play throughput (`runs/v2b/log.jsonl:150`, `runs/wide128_c1/log.jsonl:150`).

**Risk.** A 10×128 run can spend most additional compute learning structure already known from the rules, then lock the deployment into a slow model. Width gains may be evidence of architectural underfitting rather than a scalable law.

**Recommendation.** Before or alongside deeper 128-wide runs, test a parameter/FLOP-matched hierarchical model that keeps explicit `(macro_row, macro_col, micro_row, micro_col)` axes: shared micro-board processing, macro-board mixing, then cross-scale interaction/attention and a factorized policy head. Also test an exactly D4-equivariant trunk or weight-sharing ensemble. Compare Elo at equal latency and equal training GPU-hours, not parameter count alone. Keep the existing ResNet as the control.

### 14. `endgame_v1` is now a development set, and its CI does not preserve the balanced estimand

**Confidence: High.**

**Evidence.** The set is deliberately balanced over four empties buckets × W/D/L × side (`uttt/endgame.py:111-158`) and has good source-game provenance. But its CIs resample source-game groups without stratifying by those designed cells (`uttt/endgame.py:162-171`, `uttt/endgame.py:207-228`). Bootstrap replicates can therefore change the very W/D/L/side/empties mixture whose macro-balanced mean is reported.

More importantly, the same `suites/endgame_v1.npz` is evaluated every ten training iterations (`uttt/train2.py:173-179`, `uttt/train2.py:207-216`, `uttt/train2.py:280-285`), used across every architecture/recipe choice, and reused for calibration/diagnosis. It is no longer an untouched test set. Its source is also a narrow slice of one historical corpus (`uttt/endgame.py:118-128`; metadata described in `README.md:33-35`).

**Risk.** Adaptive model/recipe selection can overfit this fixed set even without gradient training on it. A pooled source-game bootstrap can give a CI for a moving mixture rather than the intended balanced score. Conclusions about draw blindness or motif prevalence may be specific to v2a-generated late states.

**Recommendation.** Treat `endgame_v1` as development. Build a sealed test set split at the source-file/game level before solving, with no source games shared with dev/calibration/puzzles. Use a stratified cluster bootstrap that samples source games within each designed stratum, then macro-averages fixed stratum weights. Broaden the test source to current-net self-play, rollout/random play, and deliberately adversarial/free-move/count-rule positions; report both macro-balanced and natural-frequency metrics.

### 15. The 300-iteration plan will currently evaluate the midpoint checkpoint as if it were final

**Confidence: High.**

**Evidence.** PLAN3 proposes `--iters 300` and tells the next instance to use the existing run scripts/templates (`PLAN3.md:103-109`, `PLAN3.md:142`). `runs/eval_run.sh` hardcodes `net_0150.pt` (`runs/eval_run.sh:4`, `runs/eval_run.sh:16-19`). `runs/watch_run.sh` and `runs/watch_queue.sh` also wait only for `net_0150.pt` (`runs/watch_run.sh:5`, `runs/watch_queue.sh:5`), while queue templates hardcode 150 iterations (`runs/queue_3090.sh:5`, `runs/after_queue2.sh:7`). In a 300-iteration run, checkpoint 0150 appears halfway through; the watcher can start post-run evaluation while training is still using the GPU.

**Risk.** A long-run experiment can be scored and archived at its midpoint, mislabeled as final, and slowed/perturbed by concurrent evaluation. This is a direct operational blocker for PLAN3 section 6.

**Recommendation.** Make evaluation require either an explicit checkpoint or derive the expected final checkpoint from the immutable run manifest. Wait for process completion/a `.done` marker, not checkpoint existence. Record the evaluated checkpoint hash in every JSON/report and fail if the configured iteration count and checkpoint number disagree.

### 16. The second-pass analysis plan would reproduce some descriptive heuristics without strengthening their inferential status

**Confidence: High on the code behavior; Medium on the practical impact.**

**Evidence.** Puzzle positions and regrets are solver-validated, which is excellent, but motif labels are heuristic and overlapping. The tool selects the first optimal move by index, follows one greedily tie-broken optimal PV, and labels `tiebreak_conversion` from that one eventual ending (`tools/puzzles.py:66-108`, `tools/puzzles.py:163-180`). Counts therefore do not show that a motif caused the raw policy's error, nor are they robust to multiple optimal continuations. PLAN3 nevertheless summarizes failures as concentrated on tiebreak conversion/free-move handling and proposes simply rerunning the tool on the new net (`PLAN3.md:100-101`, `PLAN3.md:119-123`).

The decision-time tool defines “settled” retrospectively as being correct now and at every later ply (`tools/decision.py:78-104`). That is a useful descriptive statistic, but it is not an online stopping rule and has no uncertainty band. The atlas is properly labeled search-relative, but its opening-book PVs come from one net/search configuration and select top actions under a particular deep PUCT procedure (`tools/atlas.py:75-95`, `tools/atlas.py:115-168`).

The rollout anchor also contains stochastic UCT expansion/playouts (`uttt/rollout.py:132-157`, `uttt/rollout.py:172-203`) and the match tool instantiates one default seeded realization (`tools/openings.py:39-50`, `uttt/rollout.py:234-253`). One large suite does average over many pseudo-random streams, but the interval is still presented solely as an opening-pair bootstrap.

**Risk.** Re-running against `wide128_c1` can produce more precise-looking motif counts, settling plies, and opening PVs without answering causal or out-of-sample questions. The “absolute” rollout yardstick may understate Monte Carlo seed uncertainty.

**Recommendation.** Define motif tests counterfactually: compare the raw and all optimal moves for whether they give/deny a free move, win/close a board, or preserve count-rule value; aggregate across all optimal continuations or mark ambiguity. Version puzzle discovery and confirmation sets separately. For decision time, bootstrap source games and evaluate a genuinely online, calibrated stopping rule on a second corpus. Require opening-book choices to survive training seeds, D4 orientations, and matched-time budgets. Repeat rollout matches over several independent UCT seeds and use a hierarchical opening/seed interval.

## C. What I would change in PLAN3 section 6

I would reorder and narrow the next steps as follows:

1. **Immediate reproducibility/measurement gate.** Put the source under version control; add immutable run manifests, actual end-to-end timers, peak-memory telemetry, and checkpoint hashes. Fix the 0150 script assumption. Freeze a development/confirmation opening split and a dev/test endgame split. Predeclare equal-compute primary metrics and seed-replication rules.

2. **Map the compute frontier before naming the next base.** Cross 64/96/128 widths with simulation budgets at matched batch-1 and batched wall-clock. Confirm the finalist on the sealed suite and at multiple training seeds. Keep `wide128_c1` as the equal-64-sim leader, not automatically the universal base.

3. **Exploit target quality next.** Run the small Gumbel target sweep (`c_scale`, `c_visit`, `m_considered`, simulations), then a controlled high-budget replay-reanalysis/distillation experiment. The c-scale result and 64→256 search gain make this better motivated than blind depth.

4. **Profile and clean the current GPU path.** Remove repeated legality/aux-head/encoding work, cache replay sampling state, time checkpoint I/O, fix the graph benchmark, and measure active-leaf/duplicate fractions. Only after the batch-utilization and memory curves justify it should `games=8192` or two phase pools be attempted. Decouple that batch change from data and optimizer volume.

5. **Compare structured architecture against brute depth.** A parameter/FLOP/latency-matched hierarchical or D4-equivariant model should be in the same stage as 8×128 and 10×128. Run longer training only for architectures/teachers that are on the equal-compute frontier; schedule LR and replay age by samples, not copied iteration numbers.

6. **Move the external test earlier if deployment is the objective.** A minimal CodinGame baseline and compact-net latency budget can reveal whether the research metric matches the real constraint before the project optimizes a model that cannot be ported. Treat the second analysis pass as confirmation with improved methods/splits, not merely a rerun on the newest checkpoint.

In short: retain scaling as one branch, but remove “the only live strength lever.” The evidence most strongly supports a three-branch programme—**teacher/target improvement, compute-efficient architecture/search, and statistically replicated scaling**—under a single equal-compute measurement protocol.
