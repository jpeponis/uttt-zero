# Prioritised findings

1. **High — `docs/paper/02_literature.md:101–107`: Wang’s adjudicated correction has not reached the draft.** The text still infers an optimum between the sweeps and omits their generally positive fixed-setting result. This directly contradicts PLAN7 §7e R5. Replace it with both findings, distinguish the budget axes, and infer no shared optimum.

2. **High — literature `:147–153,205`; survey `:639–650,860–865`: the probing comparator is materially understated.** Lovering et al. did not study only one trajectory: their supplement lists **four agents**, with additional cross-architecture results in Appendix D. Four-net replication remains valuable here, but is not the missing feature of that literature. Cite and compare against the [supplement, Appendix A/Table 1 and Appendix D](https://proceedings.neurips.cc/paper_files/paper/2022/file/a705747417d32ebf1916169e1a442274-Supplemental-Conference.pdf).

3. **High — map row 30; `:140–150,263`: the map is stale relative to committed KNOWLEDGE.** Claim 30 already contains J1a’s `_e8` sealed reading, and KNOWLEDGE’s opening note already qualifies the “one reversal” statement. Remove the purported open sealed-set gap and uncorrected-note finding. These are completed corrections, not missing experiments.

4. **High — map outline `:169,186–189,211,230`: qualifications in the table disappear in the proposed prose.** Search agreement becomes game truth; nonzero negative coefficients become “nothing”; sampled perfection becomes a solved phase; one inadequate surrogate becomes proof that concepts carry no strength. Replace these sentences as specified below.

5. **Medium — map row 14 and `:115–123`: the reconciliation is incorrect and the drift cell omits B3.** The draft preserves the corrected A4 reading but drops KNOWLEDGE’s subsequent B3 correction. Its “deep10’s two fits” range also does not describe those fits. This understates model-dependent drift.

6. **Medium — map `:125–131`: the drift tally is not a partition.** Its totals sum to **62**, not 59; it double-counts components, omits row 47 from its named unmeasured list, and understates both compatible-containing and reversal-containing cells. Generate the tally from explicit row assignments.

7. **Medium — literature `:31–33,193,202`: comparator conclusions exceed their evidence.** SaltZero supplies no board-count distribution establishing that *most* draws would become wins. SLAP retained an eightfold sample reduction with similar winning rate; “did not transfer” omits that benefit. “Augment, don’t enforce” generalises beyond this implementation’s negative result.

# 1. Fidelity of the map

I checked ten numbered entries—**2, 3, 14, 15, 18, 30, 31, 32, 33, 35**—including both halves of all three split entries. This covers thirteen displayed rows, three magnitude-changed rows, three compound cells, an unmeasured entry and the unresolved entry. Checks used saved outputs only.

| Entry | Cell-by-cell assessment |
|---|---|
| **2** | Search-relative level and named four-net coverage are correct. Recomputed Kendall τ from `runs/plan5_A1_atlas.json` and `runs/plan6/I1_A1_atlas.json`: `_e4` against v2b/deep10/deep8 is **0.847619/0.885714/0.923810**, matching **0.85/0.89/0.92**. Magnitude changed is defensible descriptively; no CI exists. Restrict “top four never change” to **16k**: KNOWLEDGE `:81–83` explicitly records lower-budget swaps. The displayed v2b-to-`_e4` comparison spans 363 reference Elo, not 340; 340 belongs to the earlier dev1-to-deep10 span. |
| **3** | Numbers and source match: `plan5_A1_atlas.out:30` gives **+0.354/+0.455/+0.447**; `I1_A1_atlas.out` gives **+0.495**, with **+0.100** over [36]. Level and coverage are correct; intervals are unavailable. “Rises at every strength” is false: deep8→deep10 decreases **0.008**. Keep descriptive magnitude drift, delete monotonicity and extrapolation. |
| **14** | Numerical columns reproduce KNOWLEDGE, but coverage’s “six fits” confuses fits with coefficients: the four strong nets contribute **seven fits**, with s1 B3-only. A4’s centre/edge compatibility and corner drift check out. B3’s **0.0209/0.0337/0.0316** all lie below deep10’s earlier intervals (`plan5_B3_value_deep10.out:36–41`; `I1_B3_value_decomp.out:51–56`). State both models. Deep10’s own coefficient span is approximately **0.056–0.079**, not **0.03–0.08**. The pooled **0.02–0.08** is a point-estimate span, not an interval. |
| **15** | **Unresolved** remains appropriate. Level should cover **predictive and search-relative** regressions, not predictive alone; add A4/B3 citations and distinguish self-ownership coefficients from self-minus-opponent contrasts. Counterfactual means **1.052/0.941/0.827** correctly round to the map’s **1.05/0.94/0.83** (`plan5_B4_probe_value_deep10.out:14–17`). However, KNOWLEDGE’s “unchanged to the second decimal since v2a” is false: `runs/v2a/probe_surprise_rerun.out:15–18` gives **1.026/0.910/0.794**. Stable ordering survives, identical magnitudes do not. No contrast CI establishes a hierarchy. |
| **18** | Predictive level and unmeasured-after-deep10 status are appropriate. But **+0.017** is specifically the **centre-board** removal mean; corner/edge are **+0.012/+0.014** (`plan5_B4_probe_value_deep10.out:19–21`). The centre’s p10–p90 is **−0.647 to +0.677**: a small signed mean conceals substantial responses. No CI is reported. Replace “worth nothing” with a description of the tensor intervention. |
| **30** | Existing v2 numbers match, but coverage, drift and file cells omit committed J1a. Add `_e8` on the s1-derived v3 split: sealed **92.7 [91.8,93.6]**, dev **91.6 [90.6,92.6]**; search **99.9 [99.8,100.0]** versus **100.0** (`runs/plan7/J1a_endgame_v3_{test,dev}_e8.out:3–11`). “Not measured” is no longer the sealed component’s verdict. Also, earlier dev/test agreement was not universally within 0.3: deep8’s **83.5→84.8** is **1.3 points**, acknowledged in KNOWLEDGE `:383` and `:673`. Metrics are solver-graded; absence of selection bias is an inference. |
| **31, both halves** | The split is necessary. `deep8_c1_300/timeline.json`, iterations 200/210, confirms draw recognition **58.8→65.7%**; `_e4`/`_e8` endpoints confirm **79.0/81.0%**. Magnitude drift is correct. Diagnosis coverage must include the later timelines it uses, and identify the solver set as `endgame_v1`, not the timeline’s separate 20,000-position corpus. The `_e4` “≈+6” is paired-score improvement, not draw recognition, which rises **70.6→74.7%**. Change causal diagnosis to **unresolved**, retaining LR-drop timing as supporting evidence rather than proof. |
| **32** | Both numerical components match `plan5_A7_puzzles_deep10_on_deep8late.out:1–5` and `I1_A7_puzzles.out:1–5`: **126/6000→61/6001** raw failures, **7/6000→2/6001** search failures. Exact grading applies to sampled action values, not population rates. Non-paired sampling is correctly disclosed; the outputs alone do not substantiate “same corpus.” Preserve rate drift and observed motif-order change, without asserting a resolved population ordering. The bottom motifs swap too: closing/macro **4/0→0/3**. |
| **33, both halves** | Values round correctly, and the deterministic-optimal-policy caveat is essential. Coverage needs sharpening: the JSON explicitly separates **unsolved positions** for the agent’s **24.6%** from **4,791 solved positions** for the solver’s **70.2%**. These are not a paired agent-versus-solver comparison. `principles_deep10.json` uses deep8’s corpus; deep8 and `_e4` use deep10-derived data. The latter solver readings are identical, **0.7021498643**, not independent strength replications. No CI is supplied. |
| **35, both halves** | Regression level, two-net coverage and compatibility are sound: search **0.0102±0.0418→0.0315±0.0437**; raw **−0.0484±0.0412→−0.0598±0.0459** (`plan5_B3_value_deep10.out:37`; `I1_B3_value_decomp.out:52`). Rounded map numbers agree. Counterfactual **+0.111** matches its source, and unmeasured status is correct. But attributing that premium specifically to the fourth line is not identified by the intervention; call it consistent with line-count structure. |

## Judgement cells and tally

There are **24**, not 22, cells containing “compatible”:  
**1, 8, 11, 13, 14, 17, 19, 21, 23, 26, 31 diagnosis, 31a, 33 agent, 33 solver, 34, 35 regression, 36, 37, 38, 40, 41, 42, 44, 45**.

The definition “inside the earlier interval” cannot govern all these:

- Keep interval-based compatibility where an earlier CI actually supports it, notably **8, 19, 35 regression**.
- Label rank/profile repetitions **“qualitatively unchanged; no interval test”**, rather than treating missing intervals as compatibility evidence.
- Rows **20, 24, 25, 27** already say magnitude changed; **21** separates ordering from plies. That is sensible descriptive reporting, not statistical drift detection.
- **17** does not establish “never moves”; **31 diagnosis** should become unresolved.
- Preserve **7** as an observed reply reversal, but replace “within 0.02” by approximately **0.02**: its own value is **0.022**.
- Preserve **32**’s descriptive swap. In **48**, distinguish widths: narrow G-CNN still leads at 6,240 (**0.7875 versus 0.8145**) and trails at 12,480; the **wide** arm reverses by 6,240 (`H4_lr*.json`, `G_arm_gcnn8x46.json`).
- **42** is magnitude/architecture dependence, not necessarily a sign reversal: unresolved positive gains becoming resolved positive gains do not reverse sign.
- **5** must explicitly retain its near-tie-to-separated reply change, regardless of whether the primary-ordering ledger calls it a reversal.

Applying reversal→magnitude→unresolved→compatible→unmeasured precedence to the **written cells**, before these corrections, gives **5+24+1+18+11=59**. “Compound” should be a separate annotation, not another exclusive bucket. Recompute after adjudication.

# 2. Literature fairness

## Every summary-table row

| Comparator, literature lines | Assessment |
|---|---|
| First move, **190** | CLOSED-DRAW is appropriate; “best and worst agree” should mean best move and broad worst board class, not an independently measured rank-15 orbit. |
| O’s reply, **191** | CLOSED-DRAW appropriate; agreement is with prose, not a matched-budget engine experiment. |
| First-player edge, **192** | CLOSED-COUNT appropriate; retain exploration and opponent-population differences. |
| Draws/tiebreak, **193** | CLOSED-DRAW comparator correctly distinguished; ours reaches a no-line terminal in about one-third, but **unequal count decides 16.5%**. |
| Game length, **194** | “CLOSED” is incomplete. Split sources and identify each tiebreak or mark unknown. |
| Free move, **195** | Integer 2 comes from a **course report**, not the blog. Its tiebreak remains unverified from the primary report. |
| Winnable board, **196** | Separate folk advice from Elhage’s narrower theorem; restore the sampled-policy qualifier. |
| Centre board, **197** | “CLOSED” incomplete; specify that 3 is the corner feature, and whether bonuses are additive. |
| Exploitability, **198** | Keep variant unverified; do not simultaneously claim no academic work touches CLOSED-COUNT. |
| Solved status, **199** | OPEN is correct; the project’s solved samples are not an established frontier. |
| Sample reuse, **200** | UTTT variant inapplicable; identify games and budget axes. Correct Wang as below. |
| Scaling, **201** | Name Connect Four/Pentago; increased update benefit does not exclude simultaneous parameter limitation. |
| Symmetry, **202** | Name Gomoku for SLAP; retain its sample-saving result and narrow this project’s recommendation. |
| LR schedule, **203** | Attribute the warning to its particular discussion, not a field-wide prohibition; preserve the G-CNN exception. |
| Depth/updates, **204** | “Deeper is better” needs a specific source and conditioning, not an anonymous maxim. |
| Concept probing, **205** | “One trajectory” is false for Hex; four-agent precedent must be acknowledged. |

## Five numerical source checks

1. **SaltZero:** **113–87** is score, not wins/losses: **65+48=113**, **39+48=87**; **96/200=48%** draws. Confirmed by its [README](https://github.com/farmersrice/saltzero). No evidence there supports the “most would become winners” counterfactual.
2. **SLAP:** **83%** supervised convergence improvement and one-eighth sample size are correctly quoted; AISB **2023** is correct. Its RL result also retained eightfold sample reduction with similar winning rate. [Authors’ abstract](https://arxiv.org/abs/2301.04746)
3. **Jones:** **500 Elo/decade** is correct; **500 log₁₀2=150.515** per doubling. Preserve the linearly increasing regime and compute definition. [§IV-A](https://arxiv.org/html/2104.03113)
4. **Bertholon et al.:** **43 moves/29 rounds** and OPEN rules are supported. They are not CLOSED results. [Paper, §§1,4](https://arxiv.org/html/2006.02353)
5. **Wang:** default history **20**, epochs **5/10/15**, and correlation-run lengths **25/50/75** support nominal reuse **100/200/300**, or finite-run arithmetic \(ep(20-190/I)\), approximately **62–262**, assuming constant generated volume. [Tables 1–2](https://arxiv.org/html/2003.05988)

The surviving Wang account must include both: larger epochs generally improve tournament Elo at fixed outer settings, with an exception; their time-budget analysis favours low inner-loop settings. **Different games and non-overlapping reuse regimes establish no common optimum.** [§6.2](https://arxiv.org/html/2003.05988)

The ±30% conversion warning survives in literature `:95–96`, but disappears from the outline’s “field sits at ≈1.” Likewise, the heuristic UTTT state-count range cannot justify a factual “five to ten orders higher” conclusion (`:175`).

Neumann–Gros’s unverified venue can be updated to **ICLR 2023**, supported by the [indexed OpenReview record](https://openreview.net/profile?id=~Oren_Neumann1); direct opening encountered browser verification. pc29277’s repository/raw README failed retrieval; D’Alberton returned 403; gPress presented a challenge; the HUJI primary report failed. Their unresolved details require archived primary documents, not inferred corrections.

# 3. Five hostile-referee sentences

1. **Row 2, outline `:169`: “a fact about the game, not the net.”**  
   **Survives:** “At 16,384 simulations, the search-relative first-move rankings of v2b, deep8, deep10 and `_e4` retain the same top four; reported cross-net τ values are 0.85–0.96, with no sampling CI.”

2. **Row 19, `:186`: “an own local win is worth nothing alone.”**  
   **Survives:** “In B3’s search-value regression, the own-local-win coefficient is negative on deep10, −0.026±0.017, and `_e4`, −0.037±0.018; these adjusted associations are not causal costs.”  
   Both intervals exclude zero (`plan5_B3_value_deep10.out:30`; `I1_B3_value_decomp.out:45`).

3. **Row 18, `:189`: “a dead open board is worth nothing.”**  
   **Survives:** “On deep10’s tensor-edit probe, removing the open centre board changes predicted utility by +0.017 on average across 33,947 edits; p10–p90 is −0.647 to +0.677, not a confidence interval, and no mean CI was reported.”

4. **Row 31a, `:211`: “solved outright … a tablebase adds nothing.”**  
   **Survives:** “Against exact tablebase labels, deep10 and `_e4` achieved 100% on their 701 and 689 sampled one-open-board positions for the three reported metrics; no population CI or universal neural correctness guarantee follows.”  
   Cite `I1_C5_tablebase_grade.out:1–5`; distinguish the exhaustive table from sampled agents.

5. **Row 41a, `:230`: “named concepts carry none of the strength.”**  
   **Survives:** “This 20-feature linear surrogate fitted to deep10 scored 2.18% [1.36,3.05] against v2b at 64 simulations, −661 Elo [−745,−601]; this behavioural failure tests the surrogate, not every representation using these concepts.”  
   Intervals are from `runs/paired_surrogate_vs_v2b_64.json`, `summary.overall`; add them to KNOWLEDGE before manuscript use.

Additional unsupported promises: row 6’s first-move concentration does not show that training learns the entire opening book first; the “three guards passed” assertion (`:247`) is not a demonstrated per-concept causal validation.

Actual four-strong-net coverage exists for **37**. It does not extend automatically to adjacent probes: **39 has three; 40 three; 36 two; 38a and 41a deep10 only**. Row 13’s “four strengths” includes **v2b**, not s1; row 8 has only three strong nets.

# 4. Is the outline the paper?

Not yet: it is an evidence catalogue in KNOWLEDGE order.

Put rules, utility units, corpus construction, budgets, strength calibration and limitations **before** the game claims. Keep the full map as an appendix; select findings for the main argument rather than promising every row once.

The seed band and ±3-point adoption rule are present, but must distinguish match uncertainty from training-seed variability. Bring forward PLAN7 §0’s limitations: related agents can share errors; regressions are associations; solved samples are selected; one-seed interventions do not identify general mechanisms; external playing strength and exploitability remain unmeasured.

Keep exact/search-relative labels, the reply reversal and both near-tie ordering qualifications. Add the completed J1a result. Do not reserve space as though unrun J3/J4/K1 results already exist, or treat the in-flight parent readings as missing evidence.

# 5. KNOWLEDGE defects inherited or exposed

Besides the checks above:

- **14, `:242`:** “significant in three” conflicts with printed intervals: four exclude zero, counting B3 corner **0.0337±0.0336**, whose lower endpoint is only **0.0001**. Report that fragility rather than rounding it into or out of significance.
- **31, `:395–400`:** the causal headline remains under *Exact* despite the adjudicated split.
- **35, `:451`:** the rejected “costs what its lines cost, no more” headline remains.
- **48, `:742`; 50, `:854–856`:** “capacity and not LR” and “width is not what cost … 220 Elo” still overstate what frozen-data experiments establish about self-play.
- **51, `:883–910`:** positive benefit from four to eight does not establish that eight itself lies below a plateau. The direct parent result does survive: recomputing 516 opening records gives **55.7655%**, **40.2418 Elo**.

# What should not change

- Independent level, coverage and drift columns; all three substantive splits.
- The adjusted-association framing for free moves.
- Explicit pc29277 acknowledgement and rejection of a total-compute ratio.
- Solver-policy tie-breaking and sampled-optimality caveats.
- The narrow equal-inference-cost D4 negative result.
- The measured reuse gains and direct head-to-head comparison, without summing Elo.
- Judging the earlier architectural recommendation by its stated uncertainty and information value, not by its losing outcome.