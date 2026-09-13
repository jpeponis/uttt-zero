Rebuttal round for your M0 review of `uttt-zero`'s PLAN7. Your review has been adjudicated finding by finding in `PLAN7.md` §7e — 36 rows: verdict, the evidence re-derived from the code or the logs, and where each lands — and the plan was amended accordingly in §0, §1a, §2, §3, §4, §5, §6, §7 and §8; three corrections went into `KNOWLEDGE.md` (14, 31a, 33), six into `knowledge/06`, one into `knowledge/07`. Read §7e first, then the amended sections it points to (the log's 20:03 entry says what was re-derived).

Answer, in ≤ 900 words, as your final message — it is saved verbatim as `docs/reviews/M0_plan/REBUTTAL.md`:

(a) **The Wang et al. 2020 reuse conversion.** With their default 20-iteration replay history and ep ∈ {5, 10, 15} passes over the whole buffer per iteration, is "≈ 100–300 uses per position" the right arithmetic? Show the calculation from the settings their paper states, and say what reuse range their sweep therefore covers relative to this project's 1 → 8 (defined as optimizer samples per generated position; `_e8`'s logged quotient is 8.0109).

(b) **pc29277's compute in comparable units.** 28 544 games in 22 T4-hours at 100 PUCT simulations per move, against 1 501 606 games in 22 RTX-3090-hours at 64 Gumbel simulations per move. What ratio of compute do you consider defensible to state, in what units, and with what caveat?

(c) **The relabel figures.** You cited 16.5 % of outcomes changing from a count decision to a draw and 33.1 % reaching the no-line terminal. Quote the lines of `runs/plan6/I1_A6_corpus_stats.out` they come from and confirm or correct both numbers.

(d) **Disputes.** Anything in §7e that misreads a finding of yours, and any verdict you dispute — say which row, why, and what evidence would settle it. Rows 20 and 23 are "accept with change"; if you think the change is wrong, say so.

Read-only sandbox, as before; recompute from the saved outputs, do not rerun models. The repository's own documents override any general working instructions you were given.
