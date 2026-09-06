# Review of uttt-zero: training, GPU use, and game-respecting architectures

**2026-09-06 — reviewed commit `e386baac60f3273f909af302b2aeeeb75e5085e5`.**

I read README, PLAN5, KNOWLEDGE, and RETROSPECTIVE in full, followed the current engine → search → self-play → replay → optimizer → evaluation path, and inspected the relevant analysis tools and historical review adjudication. I ran bounded checks and in-memory microbenchmarks, not a training run or a new strength ladder. Existing project files were left unchanged. Reproduction scripts and measurements are in [`review_astra/`](review_astra/).

## 1. Main conclusions

**The next useful architectural experiment is not another increment in depth. It is a model whose information flow follows local boards, winning lines, and the send rule, with exact D4 equivariance.** The justification is not that symmetry must improve Elo. It is that it removes a known nuisance variable from a scientific instrument and supplies an appropriate inductive bias. Whether that also improves learning or playing efficiency remains an experiment.

Before that experiment, I would correct two problems in the experimental instrument itself:

1. **The opening book sometimes concatenates moves in different coordinate frames, producing illegal displayed lines.** Symmetry-equivalent replies also occupy multiple places in its “top three.” These are reproduced implementation problems, not speculative architectural objections.
2. **Evaluation changes training's random-number stream.** Consequently, changing evaluation cadence is not currently a training-neutral change. The “same-seed” earlier-LR-drop comparison also diverges before its LR intervention. Its measured final loss stands; its precise causal interpretation is weaker than the documents suggest.

The GPU allocation is broadly sensible. The 3090 should remain the principal self-play/learning device; the 3060 is especially useful for independent evaluation, analysis, and bounded teacher-labeling jobs. **Do not adopt synchronous two-GPU training merely to make both utilization graphs busy.** Self-play, not backpropagation, dominates this workload.

| Priority | Recommendation | Basis |
|---|---|---|
| First | Repair opening-book frame transport and rank distinct reply orbits | Reproduced illegal lines and duplicate children |
| First, before another controlled run | Isolate RNG streams; make restart semantics explicit | Reproduced evaluation RNG consumption; incomplete continuation checkpoints |
| Next architectural branch | Compare exact-D4 CNN and local/macro/routing model on fixed teacher data | Correct symmetries; measured residual orientation dependence |
| Low-risk pipeline improvement | Run checkpoint evaluation in a separate 3060 process | Removes critical-path evaluation and isolates its failures/RNG |
| Next learning-efficiency question | Separate data generation, update count, replay mixture, and LR timing | Current “duration” changes all of them together |
| Defer | DDP, larger self-play batches, dense-tree rewrite, broad micro-optimization | Small upside or already-negative evidence; profile before reopening |

There is substantial work worth retaining: two independently expressed rules engines, exact late-game checking, continuous self-play, GPU-resident replay, fused inference, graph/eager comparison tests, frozen opponents, paired openings, and a documented negative-results ledger. The recommendations below are additions and corrections, not a proposal to replace that foundation.

## 2. What the system is actually optimizing

The project is an empirical instrument for understanding **closed-board, most-boards UTTT**, not a proof that this game has a particular minimax outcome. Its main loop is:

1. A frozen inference copy guides Gumbel search over many independent games.
2. Completed games supply policy targets, outcomes, final ownership, and margin labels.
3. A weighted replay buffer supplies randomly D4-augmented minibatches.
4. SGD trains the four-headed residual network; a fresh fused copy guides the next iteration.
5. Fixed opponents and solved endgames measure the resulting instrument.

Three different quantities should remain distinct:

- **Strength at equal simulations**: useful for the existing ladder.
- **Strength per wall-clock inference/training budget**: useful for engineering choices.
- **Reliability of a game claim**: requires suitable positions, valid symmetry handling, uncertainty, and sometimes an exact argument—not just more Elo.

The current 10×128 network is a strong measured player. Its superiority to 8×128 as a *recipe*, and its superiority under every deployment budget, are not established. PLAN5 has largely recognized this already.

## 3. The correct symmetries—and the wrong ones

### 3.1 The spatial group is a diagonal D4

Write a move as `(b, c)`, where `b` is its local board and `c` its cell. Both indices range over a 3×3 grid. A spatial symmetry acts as

\[
g\cdot(b,c)=(g b,g c),\qquad g\in D_4.
\]

The **same** rotation/reflection must act on both indices. This is what [`uttt/batch.py:41–77`](uttt/batch.py) implements correctly.

Why not rotate each small board independently? Suppose boards transform by `P` and the cells inside board `b` by `Q_b`. The original move sends the opponent to board `c`, which transforms to `P(c)`. But the transformed move sends the opponent to `Q_b(c)`. Preserving the send rule for every move requires `Q_b(c)=P(c)`: the local and macro transformations cannot be chosen independently.

A cheap exhaustive check of the nine-point/eight-winning-line hypergraph found exactly eight automorphisms, matching the implemented D4. Burnside's count then gives

\[
\#\text{first-move orbits}
=\frac{9^2+3\cdot1^2+4\cdot3^2}{8}=15.
\]

These results are in [`checks.json`](review_astra/checks.json). They support the spatial group for this ruleset; they are not a classification of every possible state-dependent equivalence of the entire game tree.

**Do not enforce** independent local rotations, arbitrary board permutations, translations of the 9×9 picture, or interchange of the board and cell indices. These do not generally preserve the game. In particular, UTTT is not simply a small Go board: adjacency across the boundary between two local boards is much less fundamental than the nonlocal send relation.

### 3.2 Values are invariant; policies and ownership maps are equivariant

The desired laws are

\[
v(gs)=v(s),\quad
\pi(gs,ga)=\pi(s,a),\quad
o(gs,gb)=o(s,b).
\]

WDL probabilities and the margin distribution are invariant to spatial D4; move probabilities and per-board ownership predictions must move with their indices. A network that pools away all orientation information before producing its policy is therefore not the right solution.

Global player-name exchange is a separate issue. Swapping X/O stones, won-board owners, **and the side to move** leaves the seven-plane relative encoding identical. I verified this exactly. It does **not** imply that changing only the side to move should negate the value of an otherwise unchanged position. The optional absolute-X plane would break this input-level relabeling invariance; the current seven-plane recipe does not use it.

### 3.3 Stabilizers matter: sometimes an equivariant deterministic move is impossible

After the opening move `[40]`, the position is fixed by every D4 transformation. Its legal replies are the four corners and four edges of board 4. None is fixed by all D4 transformations.

An exactly equivariant **deterministic action selector cannot exist at this position**: its chosen action would have to be fixed by the entire stabilizer. An equivariant probability distribution can exist—it assigns equal probability within each four-move orbit—and an action sampled from it is equivariant *in distribution*.

This distinction applies to search as well as networks. `argmax`, sequential tie-breaking, a finite simulation budget, and independently drawn noise can break sample-wise symmetry even with an exactly equivariant evaluator. For paired transformation tests, transport the same noise; for symmetric ties, compare distributions, optimal-action sets, or stabilizer orbits rather than demanding identical coordinate-valued decisions.

### 3.4 A useful quotient beyond D4: forget the interiors of closed boards

Once a board closes, its individual stones cannot affect future legal moves, board ownership, sending, or the winner. Its macro status is sufficient. Thus two positions with identical open-board cells, macro statuses, normalized target, side to move, and terminal status have the same continuation game even if their closed-board interiors differ.

This is a **state abstraction/bisimulation**, not another global board rotation. It suggests:

- mask closed-board cell details in a future model's input;
- preserve their owner/full status explicitly;
- use the same abstraction in an evaluation-cache key;
- retain any separately needed historical ply metadata for exploration schedules and analysis.

I erased only closed-board interiors in 311 sampled diagnostic positions while retaining macro state. The current net changed its value by **0.061 mean absolute utility** and its policy argmax in **3.9%** of cases. This measures sensitivity to information that the continuation rules do not need. It is **not** evidence that applying this edit to the existing trained net improves play: these edited tensors are outside its training distribution. Retrain or distill with the abstraction, and validate it against the engine/solver before deploying it.

## 4. Symmetry already exposes concrete analysis bugs

### 4.1 Displayed principal variations can be illegal

`tools/book.py` canonicalizes each child sequence, but `principal_line()` follows that canonical child and appends its next move without transporting it back to the preceding coordinate frame (`book.py:68–99`).

Replaying the displayed depth-four lines found:

- deep10 book: **`[0, 6, 20, 23]`** fails at 20. After move 6, the next board is 6, not board 2.
- deep8 book: **`[40, 41, 10, 16]`** fails at 10. After move 41, the next board is 5, not board 1.

There was one illegal displayed first-move line in each book's fifteen rows. The stored canonical nodes remain useful; the concatenated display is wrong. A legal-looking line can also be in the wrong frame, so legality alone is necessary but insufficient as a regression test.

**Repair:** canonicalization should return the transformation as well as the key. Store/compose edge frame transforms when following a PV, or regenerate the line in a single original frame. Test that every displayed prefix is both legal and symmetry-equivalent to the corresponding stored node. See [`book_audit.json`](review_astra/book_audit.json).

### 4.2 “Top three moves” can mean one strategic alternative three times

After `[40]`, deep10's saved top three are **37, 39, 41**; all lead to the same canonical child `40 37`. Deep8's **41, 43, 37** do too. The other legal reply orbit, the corners, is excluded from the expansion despite the advertised top-three budget.

There are **28 deep10 nodes and 29 deep8 nodes** with duplicate canonical children among their saved top moves. Aggregate visits by child orbit before ranking alternatives. Preserve total orbit mass and an appropriate visit-weighted Q; retain the complete root arrays if the analysis will need to change its aggregation later. The currently saved top three cannot recover all omitted mass.

### 4.3 Some “disagreement” and “flatness” is coordinate bookkeeping

The documents cite deep10 choosing **37** and deep8 choosing **41** after `[40]` as an example of disagreement. They are symmetry-equivalent replies. Comparing canonical child keys instead of literal indices changes overall book agreement from **256/341 = 75.07%** to **258/341 = 75.66%**. The overall correction is small; the highlighted example is nevertheless wrong.

The root-Q gap in `tools/atlas.py:91–94` compares the two most-visited **individual** actions. They can be in the same orbit. In the deep10 book this happens at first moves 0, 8, and 40. A near-zero difference between symmetry copies is not evidence that distinct choices are equally good. Even two genuinely good alternatives being close would not establish that *all* replies hardly matter.

The saved atlas already permits a better, zero-GPU check using its separately searched reply orbits. For deep10@16384:

- after `[40]`, the two distinct reply-orbit values differ by **0.0197**;
- the best-to-worst reply-orbit range after other first moves is roughly **0.066–0.191**, not uniformly negligible;
- the two best distinct reply orbits remain within 0.03 in **12/15** cases.

These are **child-root search values**, not a recalculation of the original parent-tree Q statistic. They support the narrower statement “there are often multiple comparably good replies,” not “the choice of reply hardly matters.” No new opening search was needed for this correction.

## 5. Architectural options, from smallest experiment to most game-specific

### 5.1 First acknowledge what is already present

`train2.symmetrise()` independently rotates/reflects every sampled training example, including cells, macro state, target, policy, and ownership. Random D4 **augmentation is already on**. `dedup_sym` changes duplicate weighting, not whether the network sees augmented examples. PLAN5 B5's explanation should not be read as evidence of missing training augmentation.

The ordinary convolutional kernels are not D4-equivariant by construction, and the unrestricted flattened `p_fc`, `v_fc1`, `o_fc`, and `m_fc` heads do not impose the required transformation laws either (`uttt/model.py:39–75`). An equivariant trunk alone would not fix those heads.

On 483 positions reconstructed from 128 archived deep8 games at selected middlegame/late plies, I measured:

- mean Jensen–Shannon policy divergence across orientations: **0.0308 bits**;
- mean value range across orientations: **0.199**;
- agreement of all eight mapped-back policy argmaxes: **61.9%**.

This is a small diagnostic sample, not an independent strength estimate. It confirms that the residual symmetry error measured in PLAN5 is real. The existing +35-Elo eight-way-averaging result establishes a benefit from that intervention at equal simulations; it does not establish that an exactly equivariant architecture will earn the same gain for free.

### 5.2 A cheap exact-symmetry control: canonicalize once, handle ties correctly

There is a middle option between random augmentation and eight neural-network calls.

Choose an exact canonical state `c(s)`. Evaluate the existing network **once** there. Map its policy back through every transformation taking `s` to `c(s)`, and average those transports. Usually there is only one such transformation; multiple ones handle a nontrivial stabilizer.

Writing `G_s={g : gs=c(s)}`:

\[
\pi_{\rm can}(s)=\frac{1}{|G_s|}\sum_{g\in G_s}P_g^{-1}\pi_\theta(c(s)),
\qquad v_{\rm can}(s)=v_\theta(c(s)).
\]

This is algebraically D4-equivariant/invariant without eight forward passes. Selecting just one canonicalizing transform and ignoring stabilizers would **not** suffice for the policy.

I implemented a standalone prototype using exact lexicographic keys, not probabilistic hashes: [`canonical_demo.py`](review_astra/canonical_demo.py). It passed all eight transformations on 256 endgame states with **zero measured policy/value error at matching batch shape**, plus the fully symmetric `[40]` case.

Results with the existing deep10 checkpoint:

| Evaluator | Graph-replayed batch of 256, RTX 3060 | Raw-policy optimal, endgame_v1 | Raw-policy regret |
|---|---:|---:|---:|
| Plain fused | 7.07 ms | 96.67% | 0.0370 |
| One-call canonical | 7.26 ms | 96.13% | 0.0417 |
| Eight-way averaged | 52.71 ms | 96.67% | 0.0370 |

**Interpretation:** exact symmetry cost about **2.6% extra in this specific evaluator microbenchmark**, but did not improve this policy metric. Canonicalization chooses one orientation's errors consistently; it does not ensemble them away. No match-strength or training-benefit claim follows. It is a useful inexpensive control and possible cache front end, not a reason to replace the play agent now. The timing excludes search and canonical-cache lookup machinery; other batch sizes need their own measurements. Details: [`canonical_demo.json`](review_astra/canonical_demo.json).

### 5.3 Smaller architectural departure: a true D4 group-equivariant CNN

A D4 group-convolutional residual network is the closest controlled replacement for the existing ResNet. Hidden features retain orientation channels which **permute with the spatial transformation**, rather than independently treating every feature channel as an invariant scalar. This is the construction introduced by [Cohen and Welling](https://arxiv.org/abs/1602.07576); [steerable CNNs](https://arxiv.org/abs/1911.08251) provide a broader representation-based formulation.

Required changes include:

- equivariant convolutional blocks and compatible residual connections;
- normalization parameters/statistics tied consistently across transforming channels;
- an equivariant policy readout, e.g. orientation reduction followed by a shared pointwise spatial head;
- a per-board equivariant ownership head;
- invariant WDL/margin heads, using invariant pooling after the trunk has encoded useful geometry.

Do not simply symmetrize every 3×3 kernel into “centre/edge/corner weights.” That is a restrictive scalar-field construction and can discard useful orientation-sensitive intermediate features. Keeping orientation channels lets the model represent a threat's direction without privileging a global compass direction.

Likewise, **eight orientations are not eight free channels**. Compare actual inference time, activation memory, parameter count, and sample efficiency. Group-convolution weight sharing reduces independent parameters; it does not make the expanded computation disappear. Keep the effective activation width controlled when choosing the first pilot.

A useful mathematical fallback for a dense equivariant spatial map is weight tying:

\[
W_{ga,gb}=W_{a,b},\qquad b_{ga}=b_a.
\]

On the 81-action representation there are **861 ordered-pair orbits**, rather than 6561 unrestricted spatial weights per input/output feature-channel pair. This follows from `(9^4 + 3 + 4·3^4)/8`, and the exhaustive check confirms it. It gives a simple exact implementation/reference for a head or mixing layer. It does not by itself make a preceding ordinary trunk equivariant, nor guarantee that a particular shallow scalar-field network is sufficiently expressive.

### 5.4 My preferred game-specific design: local boards + macro lines + routing

The natural object is an **81-entry directed relation tensor** `h[b,c]`, not just 81 neighboring pixels. An available move in entry `(b,c)` changes board `b` and routes the next player to board `c`. A played stone records a consumed entry of that relation.

A compact candidate could retain:

- **81 cell/route features** `h[b,c]`;
- **9 board features** `u[b]`;
- **8 local winning-line features per board**;
- **8 macro winning-line features**;
- a small global summary.

One repeated block would perform:

1. **Local line aggregation.** Aggregate the three cells of each local winning line with a shared function, then send line messages back to their constituent cells. This makes the actual local win relation explicit.
2. **Board summarization.** Combine a board's cell/line features and its current open/won/full status into `u[b]`. Do not discard the individual cell features.
3. **Macro line aggregation.** Exchange board messages through the eight macro lines and update `u[b]`.
4. **Routing update.** Update `h[b,c]` using its own state, source-board `u[b]`, destination-board `u[c]`, legal/target status, and optionally the reverse-route feature `h[c,b]`.
5. **Global conditioning.** Broadcast an invariant summary back to boards/cells so local choices can depend on macro advantage and remaining resources.

For example, the routing part can have the form

\[
h'_{bc}=\operatorname{MLP}\big(h_{bc},h_{cb},u_b,u_c,
\text{local-line messages}_{bc},z,\mathbf1[b=c]\big),
\]

with shared functions and permutation-respecting aggregation. The diagonal indicator explicitly names the **self-send**, which is a genuinely invariant relation, not a privileged direction. Source and destination have different roles; do not force them to be interchangeable.

Readouts:

- policy: one shared scalar readout of `h[b,c]`, then the legal mask;
- ownership: one shared classifier on each `u[b]`;
- WDL and margin: invariant aggregate readouts.

The rule-incidence tensors stay fixed; under D4, all indexed quantities permute consistently, so every operation commutes with the group action. Centre/corner/edge distinctions remain available through their incidence structure; invariance does not require treating these classes as interchangeable. Conversely, arbitrary absolute position embeddings or separate untied row/column-direction weights can silently break the guarantee.

This is an application of [relational inductive biases](https://arxiv.org/abs/1806.01261) and [permutation-respecting aggregation](https://arxiv.org/abs/1703.06114), but the particular UTTT construction above is my proposed design, not a published result for this project.

Why prefer it conceptually? A local win, a macro threat, and a send-to-danger relation become short, explicit computational paths. The existing late ResNet layers already have whole-board receptive fields; the problem is **not that they cannot see remote boards**. It is that pixel locality is an inefficient description of which remote objects matter.

Implementation should still favor the hardware: small dense tensors, precomputed incidence matrices/gathers, batched matrix multiplications, and fixed-shape graph-compatible operations—not Python objects per board or an unnecessarily general sparse-graph framework. A relational model could otherwise win in parameter count and lose badly in wall time. Its expressive sufficiency also needs testing; an elegant message-passing construction is not automatically universal.

### 5.5 Tests that make “respects symmetry” a verifiable claim

Require these before interpreting a new model:

- engine transition commutation `T(gs,ga)=gT(s,a)`, including free moves, closure, and terminal count outcomes;
- encoder equivariance and simultaneous player-relabeling invariance where intended;
- policy, ownership, WDL, and margin transformation tests at initialization **and after optimizer updates**;
- nontrivial-stabilizer positions, especially the empty board and `[40]`;
- matching tests after inference fusion, fp16 conversion, checkpoint reload, and CUDA-graph capture;
- transported-noise search tests and distribution/orbit-aware tie handling;
- game-level train/validation splits plus measured canonical-position overlap, so augmented duplicates do not masquerade as generalization.

Fix tensor shape and precision in equality tests. My first canonical-wrapper check inadvertently compared batch 3000 against batch 256, allowing different fp16 cuDNN algorithms; matching shapes eliminated the numerical discrepancy. This is another reason to separate algebraic equivariance from finite-precision argmax stability.

## 6. Training-pipeline improvements

### 6.1 Evaluation must be observational

At `uttt/search.py:257–259`, evaluation still draws `torch.rand(n,81)` and then multiplies its Gumbel noise by zero. It therefore advances the global RNG even with `selfplay=False`. I reproduced this on CPU and CUDA. Loading a checkpoint also initializes layers before replacing their weights and consumes CPU RNG state.

Meanwhile, self-play noise, replay sampling, and augmentation use shared default generators. Increasing evaluation frequency can therefore change subsequent training data and SGD samples even though evaluation is nominally deterministic.

**Recommended fix:** separate generators for initialization, self-play, replay sampling, augmentation, and label selection; or, as a smaller first step, use an RNG-preserving context around evaluation and evaluation-only model construction. Skip the unused random draw in deterministic search. A separate evaluation process provides a cleaner boundary. Regression test: inserting an evaluation between otherwise identical training operations must not change the next sampled moves/minibatch/transforms.

This matters for D3. Its config changes `eval_every=20→10`, `eval_graph=0→1`, and the anchor list relative to the reference, in addition to LR drops. The logs also show pre-treatment divergence: at iteration 1, new positions are **243,072 versus 226,202**, well before iteration 150. Small numerical differences are present even at iteration 0. I have **not** established which numerical/runtime change first caused that early divergence; the later RNG-cadence coupling is independently demonstrated.

Keep the actual D3 result—45.4% against the reference—but describe it as evidence from one perturbed training trajectory, not an isolated measurement proving that exactly fifty high-LR iterations are worth a fixed five points. A future LR experiment should branch from the same saved full state near the intervention, preserve all RNG/scaler/actor state, and use identical evaluation machinery.

### 6.2 “Full checkpoint” is recovery-capable, not continuation-complete

The saved full checkpoint contains `net`, `opt`, `buffer`, `iter`, `global_step`, and `cfg`. It omits:

- CPU/CUDA RNG states and dedicated-generator states;
- GradScaler state;
- ongoing self-play game states, lengths, move/target histories, and game-ID counter;
- the exact-label sampler's generator state.

Thus restart loses unfinished games and resumes with a different sampling trajectory. The two-file atomic scheme is valuable operational recovery, but not a reproducible continuation. This was an accepted debt in an earlier review; it should be revisited now that individual runs support claims about learning timelines and seed effects.

Save the omitted state, or explicitly label resumes as statistically perturbed continuations and include attempt/version provenance. Retain the two-file design. Also apply atomic writes to any checkpoint consumed asynchronously by another process; numbered `net_NNNN.pt` files are currently written directly at `uttt/train2.py:325`.

### 6.3 Define the data/update budget precisely

At the standard settings, an iteration advances **4096 game slots × 64 moves = 262,144 positions**, not “4096 completed games.” Late in the reference run, it finishes about **5043 games** per iteration.

It then makes **256 updates × 1024 samples = 262,144 sampled rows** from a two-million-row replay buffer. Consequently:

- `epochs=1` is approximately one sampled training example per newly generated position, **not one epoch over the buffer**;
- the buffer spans roughly **7.6 iterations**, rather than a precise ten;
- the complete run generated **78.54 million positions** and sampled **78.64 million training rows**;
- under an idealized stationary uniform replay model, one expected use per incoming row leaves about `exp(-1)=36.8%` of rows unsampled before eviction. Real duplicate/exact weighting changes this substantially.

This does not establish undertraining. It identifies a confound: doubling duration doubles data and optimizer work, changes the self-play teacher, and changes the time spent in LR phases. The existing results have not isolated which resource is limiting learning.

Log generated positions, sampled positions, successful optimizer updates, teacher version, replay age, policy-target entropy/KL, and data reuse as first-class axes. When benchmarking a different search batch, keep total generated positions, total updates, and schedule milestones fixed; `games` is not merely a device batch-size knob.

The final saved replay provides a useful reality check. Reconstructing its configured weights gave:

| Quantity | Value |
|---|---:|
| Rows / distinct stored hashes | 2,000,000 / 922,325 |
| Mean sampled age, by completion iteration | 3.37 iterations |
| Sample probability on exactly labeled rows | 8.87% |
| Sampled loss/draw/win labels | 41.45% / 15.93% / 42.62% |
| Plies 0–7: stored fraction → sampling fraction | 15.42% → 3.28% |
| Plies 44+: stored fraction → sampling fraction | 15.32% → 25.20% |

These are reconstructed weights for the saved buffer, not a replay of historical minibatches. They show why raw corpus frequencies alone do not describe what the learner sees. “Exact labels were a small slice” and “the opening dominates the games” need to be checked against **sample weights**, not just row counts. Source: [`replay_audit.json`](review_astra/replay_audit.json).

### 6.4 Buy better policy supervision before buying many more games

The useful frontier appears to be contested middlegames and multi-board tactical/tempo interactions, not the already-easy one-board endgame. The strong net's frequent raw/search disagreements there support a focused target-quality study.

I would first use a frozen corpus and teacher to compare:

- ordinary network students versus exactly equivariant students;
- existing self-play policy targets versus deeper-search/reanalyzed targets;
- extra optimizer passes on the same examples versus more new examples;
- present sampling weights versus a modest, explicit middlegame mixture.

This is **neural distillation**, not a repetition of the linear-surrogate experiment. A weak linear surrogate does not show that a smaller nonlinear, game-structured network cannot capture the teacher.

The Gumbel target deserves instrumentation. `_sigma()` rescales completed legal Q-values by their within-node range and then applies `(c_visit + max_visits) * c_scale`. A very small Q-range can therefore be expanded into a large logit preference. That is an intended family of transformation, not a discovered bug: compare the [official mctx implementation](https://github.com/google-deepmind/mctx/blob/main/mctx/_src/qtransforms.py). But in a game with close alternatives and residual orientation noise, log Q-range, target entropy, search/raw KL, and stability under transformed inputs before further sharpening targets. Add small golden arithmetic/search-tree cases against the independent reference; agreement of v1 and v2 is not independent validation of an algorithm copied between them.

Playout-cap randomization is another later candidate: a mixture of cheaper moves and occasional deeper teacher searches. [KataGo's original account](https://arxiv.org/abs/1902.10565) explicitly separates its expensive recorded training positions from cheap moves and reports an ablation benefit in Go. That is a mechanism worth testing, **not a transferable UTTT speedup claim**. In this implementation, randomly splitting thousands of lanes among heterogeneous budgets can defeat the fixed-batch graph advantage. Use a few persistent fixed-shape pools and a matched total budget if this branch is pursued.

### 6.5 Improve the auxiliary task before adding more auxiliary tasks

The ownership head's aggregate accuracy mixes boards whose ownership is already fixed with boards whose future ownership is uncertain. Grade it separately on **currently open boards**, by phase, and compare against a deterministic current-status baseline plus a simple local-board predictor. Otherwise a one-point improvement over a random-trunk probe is hard to interpret.

The existing ablation supports “these auxiliary losses did not improve measured strength under this recipe.” It does not prove their causal mechanism, or that all board-level supervision is useless. A structured architecture would make per-board predictions and their failure modes much easier to inspect. Avoid adding many new handcrafted heads before establishing that one improved target actually helps.

## 7. GPU use: measured economics on this machine

### 7.1 Device identity and interconnect

The local virtual environment reports Python 3.10.1, PyTorch **2.13.0+cu126**, and working CUDA on both cards:

| Framework device | Card | VRAM | Loaded link observed |
|---|---|---:|---|
| `cuda:0` | RTX 3090 | 24 GiB | PCIe Gen4 ×16 |
| `cuda:1` | RTX 3060 | 12 GiB | PCIe Gen4 ×4 |

`nvidia-smi` lists these in the **opposite numeric order**. Record UUID/bus ID and verify the actual name when launching; do not equate an `nvidia-smi` ordinal with a CUDA ordinal. The current driver is WDDM. PyTorch reports **no peer access from device 0 to device 1** in this environment. The cards do not form one 36-GiB memory pool; cross-device work must budget actual transfers/staging.

### 7.2 Most time goes to self-play, not SGD or persistence

Summing logged stage times, with the last record winning for replayed iteration numbers:

| Stage | Reference deep10, 300 iterations | D3, 300 iterations |
|---|---:|---:|
| Self-play | 13.44 h / 71.2% | 14.38 h / 84.3% |
| Training | 1.43 h / 7.6% | 1.49 h / 8.8% |
| Evaluation | 3.93 h / 20.8% | 1.12 h / 6.6% |
| Exact wait + checkpoint + unattributed | 0.06 h | 0.06 h |
| Logged total | 18.87 h | 17.05 h |

These totals exclude unlogged downtime and discarded attempts; they are not job wall-clock measurements for interrupted runs. D3 also differs in runtime conditions, so the two columns are not a clean timing A/B. They do show the priority ordering unambiguously. Source: [`checks.json`](review_astra/checks.json), computed from the existing logs.

Even eliminating all training time would remove less than 9% of D3's elapsed time. Optimizing a replay sampler or optimizer kernel cannot produce another 9× overall improvement in this regime.

### 7.3 Small-batch launch overhead and large-batch compute are different regimes

Short synchronized measurements of the **actual 10×128 checkpoint's fused evaluator**, including encoding and legal masking but not search:

| Batch | 3090 eager | 3090 graph | 3060 graph |
|---:|---:|---:|---:|
| 1 | 5.60 ms | 0.53 ms | 0.45 ms |
| 64 | 6.03 ms | 1.01 ms | 1.80 ms |
| 256 | 7.97 ms | 2.91 ms | 7.03 ms |
| 1024 | 20.17 ms | 11.07 ms | 26.63 ms |
| 4096 | 48.87 ms | 42.29 ms | 104.86 ms |

Warmups/capture were excluded; medians are over groups of repeated calls. Both cards were tested sequentially. Batch-1 figures are especially sensitive to scheduling and kernel choices: **do not infer that the 3060 is generally faster from that one row**. These are evaluator-throughput measurements, not complete move latency or tournament results. [`bench.json`](review_astra/bench.json) contains ranges and CUDA-event measurements.

For the larger batches the 3090 is about **2.4–2.5×** faster. Its graph time scales nearly linearly from 1024 to 4096, consistent with the project's conclusion that indiscriminate batch growth no longer buys much throughput. At batch 1, graph capture matters enormously. Equal FLOPs remain only a rough deployment proxy; measure whole-search latency at the relevant batch and simulation budget.

### 7.4 Recommended roles for the second GPU

**First choice: an independent evaluation/analysis worker.** Give it immutable, atomically published checkpoints; record checkpoint hash, evaluator settings, and completion status. The trainer should not wait for every diagnostic. Keep a bounded queue or evaluate the newest available checkpoint if the worker falls behind, while ensuring the final required comparisons are completed.

For graph-enabled D3, this removes at most its roughly 1.1 h of current critical-path evaluation—not the reference's old 3.9 h eager cost. Even if 3060 evaluation took roughly 2.5× as long, its aggregate work could fit within the much longer training job; actual search/capture throughput should still be measured. Process isolation also prevents an evaluation exception from necessarily killing the learner, though a driver-wide reset can affect both.

**Second choice: bounded reanalysis or offline student experiments.** Transfer compact state/target batches or checkpoint files rather than invoking the other GPU for every search leaf. The checkpoint's model weights are only about 12 MB; this architecture favors occasional snapshots, not frequent synchronized gradients.

**Optional later: separate self-play actors on both GPUs.** At the measured large-batch evaluator rates, adding the 3060 offers an optimistic inference-capacity ceiling near **1.4×**, not 2×. Real search, transfers, batching, and learner freshness reduce or alter that figure. Preserve total positions and update ratio in an A/B; stamp every trajectory with its teacher version.

**Not recommended now:** synchronous DDP/DataParallel, or putting all self-play on the slower 3060 to reserve the 3090 for SGD. The former targets a small fraction of runtime and introduces a slow-device/communication constraint; the latter moves the dominant work to the slower card. Overlapping learner and actors also changes teacher staleness unless a synchronization boundary is retained—it is not a semantics-free speed optimization.

### 7.5 What the cheap benchmarks ruled out

- **Channels-last training is not an automatic win here.** In a short dummy-minibatch test with the current model, AMP, SGD, and batch 1024, contiguous training took **67 ms/step**, versus **266 ms/step** with channels-last model/input. Inference is already correctly using channels-last. Leave training layout unchanged unless a better controlled profile explains and reverses this result. The [PyTorch tutorial](https://docs.pytorch.org/tutorials/intermediate/memory_format_tutorial.html) documents the mechanism and possible gains, not a guarantee for this small spatial workload. This test measures throughput, not convergence.
- **Replay sampling has a cheap local optimization, but tiny total upside.** Sampling 1024 rows from two million weights took about **1.75 ms**; drawing all 262,144 indices for an iteration at once took about **1.97 ms** total. Since weights are fixed during `train_steps`, pre-drawing independent replacement samples is distributionally appropriate, although it changes RNG ordering. The gross saving is roughly **0.45 s per late iteration**, around **0.2%** end-to-end. Worth a simple change during maintenance, not an optimization project.
- **Persistence is already small in the logs.** I would not build an incremental replay database or complicated asynchronous buffer writer on this evidence.

If profiling search further, measure the fraction of NN rows that actually expand, the terminal-row fraction, duplicate leaf keys, and time by phase. The current code evaluates a full batch even when some rows need no expansion (`search.py:164–185`). There may be savings, but compaction, caching, or subtree reuse must beat the excellent fixed-shape graph path. Do not assume dynamic skipping is free.

### 7.6 Graph safety and observed tool failures

The project's small graph/eager and in-place-refresh checks passed in this review. That does not establish the cause of its historical driver faults or stress-test all depth/batch configurations.

My first **new** two-device benchmark failed: the installed `torch.cuda.graph` caches a process-global default capture stream (`.venv/Lib/site-packages/torch/cuda/graphs.py:408–427`). After capture on one device, relying on that default for the other produced empty captures and then a capture error. Explicit device-specific capture streams fixed the benchmark. Failed/empty-graph timings in `review_astra/bench.out` are excluded; the valid run is `bench_fixed.out`/`bench.json`.

This is relevant if a future implementation puts both GPUs in one process: `uttt/search.py` currently also omits an explicit graph `stream=`. The present one-device-per-process scripts avoid the particular cross-device scenario I exercised. **This finding is not an explanation of the earlier single-device `nvlddmkm` incidents.** Follow the documented [CUDA graph memory/stream constraints](https://docs.pytorch.org/docs/stable/notes/cuda.html#cuda-graphs), keep stock hardware settings during fault diagnosis, and prefer process isolation over changing timeout/driver settings speculatively.

Windows CIM hardware queries were denied by this session's permissions; `nvidia-smi`, CUDA, and a registry CPU-name fallback supplied the hardware facts used here. No driver settings, clocks, task-scheduler jobs, dependencies, or existing files were changed.

## 8. Tighten several scientific interpretations

These qualifications matter because understanding the game is the deliverable.

1. **Failure to clear ±3 points is not a proof of equivalence within ±3.** Use the interval on the relevant difference and a prespecified equivalence margin. Two seeds provide an observed spread, not a well-estimated universal seed variance or a calibrated “2σ” band. Keep the threshold as a practical adoption rule, not as a substitute for either uncertainty calculation.
2. **The LR drop is a useful intervention, not a universal fixed-gain operator.** D3's own write-up reports raw WDL improving from about 80.3 to 83.3 and draw recognition from about 60 to 68 after its first drop. “No further resolved playing-strength gain” is defensible; “nothing learns after it” is too strong. Likewise, a flat low-LR phase is not proof of representational exhaustion.
3. **A free-move regression coefficient is a conditional association with model/search value.** Adding “macro win now” and observing a smaller coefficient does not identify a causal decomposition saying half the benefit is mediated by that option. Tensor-edited positions and matched natural positions estimate different things; one being larger does not make it a proved upper bound on the other. A stronger follow-up would solve paired continuation problems or compare carefully defined legal alternative actions on the same states, with the changed game/estimand explicit.
4. **Use “expected utility” for the `[-1,1]` scale.** The network computes `P(win)-P(loss)`. Ordinary match score is `P(win)+½P(draw)=(1+v)/2`. Thus +0.196 utility corresponds to +0.098 expected-score units, not 19.6 percentage points. KNOWLEDGE defines its signed scale, so the internal numbers are not thereby wrong; the vocabulary risks confusing readers with the separate percentage-point rule.
5. **“Settled” is retrospective prediction stability, not game-theoretic decision time.** Claim 20's “nothing is settled by ply 30” conflicts with its own first quartile around 28–30 and the early-settling caveat. Report the fraction settled at each ply, plus threshold sensitivity. A future trajectory no longer changing a prediction is not proof that optimal defense was already impossible.
6. **Exact ground truth does not make coverage exhaustive.** The measured 99.7–99.9% optimality is compelling on the specified solved samples, not a solution of every position with 6–16 empties. The 701 one-board examples likewise do not prove the network solves the entire one-board state space; the tablebase does provide exact answers there. Keep those two objects distinct.
7. **Decodability remains weaker than causal use.** A fading linear probe does not show the trunk has “used up” a concept; a failed short-budget nonlinear probe does not establish absence. A concept already available at input can still be crucial to the policy. Score future-move labels against sets/distributions of valid alternatives, not just the solver's first optimal index or one tie-broken PV. This is particularly important in a symmetric game with many equally optimal endgame moves.

None of these qualifications requires abandoning the empirical findings. They prevent good measurements from becoming stronger explanatory claims than the experiment supports.

## 9. A bounded next program—not a request to restart the ladder

I would keep the current play checkpoint and run the following work only as separately approved changes/experiments:

**A. Repair the instrument.** Fix book frame transport/orbit aggregation, add an evaluation-RNG-neutrality test, add complete restart-state tests, and record environment/dependency versions in a reproducible manifest. There is no need for a large MLOps framework; a tested runner and machine-readable manifest suffice.

**B. Establish a frozen supervised comparison.** Use existing strong-play data, split by source game, and measure canonical overlap. Build one fixed teacher-target set with a prespecified phase distribution. Compare the current ordinary ResNet, a compact D4-equivariant CNN, and the local/macro/routing candidate. Include the one-call canonical wrapper as an inference-only symmetry control. Keep targets, successful update count, and data order paired where possible; report both data-matched and wall-clock-matched curves.

**C. Judge useful quantities.** Report held-out policy KL, exact regret on development endgames, calibration/Brier, symmetry residuals, and inference/search latency on both cards. Add a small paired-play gate only after the cheap metrics and implementation tests pass. A low parameter count or zero symmetry residual alone is not success. Freeze an untouched final confirmation set before selection if making a new generalization claim.

**D. Only then choose a self-play experiment.** If the structured student preserves strength with materially cheaper inference, it attacks the dominant cost and deserves a controlled self-play comparison. If extra fitting on fixed data helps more than extra teacher work, test the update/data ratio before generating another 78 million positions. If neither helps and the analysis needs more strength, a longer constant-LR phase on the established 8-block baseline remains a reasonable, but still unproved, duration hypothesis.

The most important design change is conceptual: **use symmetry both inside the model and in the definition of what counts as the same state, the same move, the same explanation, and an independent test.** The book bugs show that doing only the first would miss an immediate benefit to the project's actual purpose.

---

### Reproduction and limits

New review files:

- [`checks.py`](review_astra/checks.py), [`checks.json`](review_astra/checks.json): group enumeration, RNG checks, log arithmetic, archived-game diagnostics, and **23 passing existing-test invocations** at documented sizes. These include reduced-size engine cross-checks, v1/v2 search agreement, eager/graph agreement, fused refresh, self-play replay consistency, exact-solver comparison, and the symmetry/tablebase checks. This was not the complete default-size test/benchmark suite; the small concept-label sample did not exercise positive dead-board examples.
- [`book_audit.py`](review_astra/book_audit.py), [`book_audit.json`](review_astra/book_audit.json): CPU-only audit of saved books/atlas.
- [`replay_audit.py`](review_astra/replay_audit.py), [`replay_audit.json`](review_astra/replay_audit.json): saved-buffer sampling distribution and checkpoint contents.
- [`bench.py`](review_astra/bench.py), [`bench.json`](review_astra/bench.json): bounded evaluator, layout, and sampling benchmarks; valid transcript `bench_fixed.out`.
- [`canonical_demo.py`](review_astra/canonical_demo.py), [`canonical_demo.json`](review_astra/canonical_demo.json): one-call canonical evaluator prototype and checks; valid transcript `canonical_demo_fixed.out`.

Run scripts from the repository root with `.venv/Scripts/python.exe -B review_astra/<script>.py`. They are review artifacts, not additions to the production pipeline. Do not run GPU timing scripts concurrently. The checks redirect Numba caches into the new review directory; no existing suites, corpora, or checkpoints were rewritten. No sealed test set was opened, no full match was launched, and no background server was started.
