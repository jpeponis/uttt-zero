## (a) Wang et al.: reuse conversion

**Yes—as a nominal full-window conversion, not an exact whole-run quotient.** Their training description and Tables 1–2 specify a 20-iteration history and \(ep=5,10,15\) epochs over the training examples. With \(D\) new positions per iteration and buffer \(B\approx20D\),

\[
R=\frac{ep\,B}{D}\approx20ep=\{100,200,300\}.
\]

Batch size cancels. Their epoch sweep therefore occupies a substantially higher regime than this project’s 1→8. [Wang et al., §§4–5](https://arxiv.org/html/2003.05988)

**Finite-run qualification:** assuming an initially empty history, equal-sized generation batches and no additional truncation,

\[
R_I=ep\,\frac{\sum_{t=1}^{I}\min(t,20)}I
=ep(20-190/I),\quad I\ge20.
\]

Their correlation experiment’s \(I=25,50,75\) thus implies approximately **62–262** across its settings under those assumptions. Implementation-level caps, augmentation and sampling conventions require separate accounting.

The distinction remains: even nominal reuse 100 is approximately 12.5 times `_e8`’s independently recomputed \(629,145,600/78,536,533=\mathbf{8.010865}\), from `runs/deep8_c1_300_e8/log.jsonl`.

## (b) pc29277: comparable compute

**A total-compute ratio is not established.** Defensible quantities are:

- **52.6067× completed games:** \(1,501,606/28,544\).
- Assuming equal mean game lengths and the brief’s flat-64 budget, **33.6683× nominal self-play simulations:** \(52.6067\times64/100\). This is a search-work proxy, not FLOPs.
- `_e8` actually records **60 iterations at 32, 40 at 48, and 200 at 64 simulations**. Equal move counts per iteration give a mean of 55.4667; accounting for that schedule makes the same proxy approximately **29.2×**.
- **22 T4-hours versus 21.962 RTX-3090-hours**, not equivalent hardware-normalized compute. [pc29277 README](https://github.com/pc29277/AlphaZero_UTTT#architecture); local `runs/deep8_c1_300_e8/{config.json,log.jsonl}`.

Different game lengths, networks, search implementations, batching/utilization and optimizer work prevent translating these proxies into total training FLOPs. That requires operation counts or comparable profiling. Neither **10× nor 100× total compute** follows; PLAN7 §0 incorrectly attributes the former to M0.

## (c) Relabel figures

`runs/plan6/I1_A6_corpus_stats.out:1–3` says:

> 99346 games from 20 files  
> X wins 62.7%  O wins 20.7%  draws 16.6%  
> ended by line 67.0%  by count 16.5%  equal count 16.6%

**16.5% is confirmed:** those count-decided wins become draws on the unchanged trajectories.

**I correct 33.1% to approximately 33.0%.** My figure added independently rounded components, \(16.5+16.6\). The terminal categories are exhaustive under `count` (`uttt/batch.py`), and `tools/corpus_stats.py` rounds each separately. Combining those rounding intervals with exhaustiveness constrains the no-line fraction to **[33.00%, 33.05%)**, which rounds to **33.0%**. Its exact unrounded value is not recoverable from these printed percentages.

Equal-count draws already remain draws; they are not part of the changed-outcome fraction. Amend row 12 and §5 accordingly.

## (d) Disputes and incomplete amendments

- **Row 20: I agree with “accept with change.”** The diagnostics may remain as evidence *consistent with* a capacity/data-regime explanation. They do not identify the self-play cause. A stronger causal claim would require interventions separating capacity, optimization and changing training data; no additional architecture campaign is required for this paper. Delete the still-unqualified “capacity, not LR” formulations in §0, §2b and KNOWLEDGE claim 50.

- **Row 23: I agree with the higher-regime qualification and withdrawal of the novelty phrases.** However, §2b still suggests a shared optimum/plateau. Cross-game curves cannot establish one. Wang generally finds larger epochs improve Elo; preferring outer iterations under a time budget is not a universal negative reuse result. A matched-recipe sweep would test an optimum. [Wang et al., §6.2](https://arxiv.org/html/2003.05988#S6.SS2)

- **Row 5 needs “in A4.”** That was my finding’s scope. B3’s new centre/corner/edge estimates, **0.0209/0.0337/0.0316**, all fall below their respective old intervals, **[0.0323,0.1205]/[0.0474,0.1108]/[0.0376,0.0948]**, recomputed from `runs/plan5_B3_value_deep10.out` and `runs/plan6/I1_B3_value_decomp.out`. Report the two models separately.

- **Row 26’s verdict stands; its implementation does not:** see (b). §2c also still says “two orders of magnitude less compute.”

- **Accepted corrections should replace superseded text, not merely follow it.** Examples remain: “KataGo caps at 4” (§0; row 24), “8-way root average” (§2b; row 25), “with everything else controlled” (§2a; row 18), and §3 C2’s binary rule-invariance claim despite §5’s unresolved verdict. These are incomplete edits, not reasons to reverse the accepted findings.