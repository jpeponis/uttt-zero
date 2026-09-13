# M1 rebuttal — `0691716`

## 1. E31: recurrence is not mechanism identification

I withdraw **unresolved** as the drift verdict **for recurrence of the LR-aligned step**. Re-reading the three `timeline.json` files reproduces draw-recognition increases of **6.9, 4.1 and 6.5 percentage points** across iterations 200→210, all on `suites/endgame_v1.npz`.

The amended explanation makes **compatible [no CI]** adequate; no sixth verdict is needed. But neither that mark nor *inference* repairs the categorical statement “It was optimisation, not capacity.” Replace it with:

> Draw recognition improves after the first LR drop across these runs, consistent with an optimisation explanation; capacity limitations are not excluded.

Apply the same qualification to KNOWLEDGE 31’s headline. Also finish the metric correction: row 31’s `_e4` strength column still says “first drop ≈+6,” while `_e8` still displays WDL rather than draw recognition. Those cells should show **70.6→74.7%** and **73.1→79.6%**.

## 2. J2: move row 44

Retain **[CI]** for **8, 14’s A4 centre/edge component, 19, 35 regression and 45**. Move **44 to [no CI]**.

Row 44’s compatibility means that the qualitative deployment conclusion recurs, not that a later estimate falls inside an earlier interval. Its gains against deep10 rise from **+86 [67,105]** through **+141 [121,160]** to **+186 [165,208]**. The later point estimates are outside their predecessors’ intervals. Having match CIs somewhere in the row does not satisfy the column’s stated criterion.

Row 45 does satisfy it: `_e2`’s saved JSON gives **10.7767 Elo**, inside deep10’s earlier **[−7,+26]** interval. Describe that inclusion, rather than treating two failures of the adoption rule as evidence of equivalence.

Consequently, there are **five interval-based compatible components**, four within the compatible partition bucket and one within row 14. Update both explanatory counts. Broaden “[no CI]” to mean *no interval-based drift comparison*, rather than *no interval was ever quoted*.

## 3. J6: no supported flip

**No.** The G-CNN result changes the magnitude and the conclusion that a second drop provides no resolved benefit; it does not establish a sign reversal. First-drop improvement exceeds second-drop improvement in both architecture families.

The revised bucket and **4 / 25 / 1 / 18 / 11 = 59** partition stand. Keep the distinction between uncertainty on individual checkpoint scores and uncertainty on their difference: the ±2.8 figure is not itself a calculated CI for each drop.

## 4. E32: different corpora strengthen the qualification

**Nothing in my descriptive entry-32 reading depends on identical corpora.** The rates and motif reorderings remain observations of the two evaluated sets.

The scripts establish more than my original cautious wording: deep10 uses deep8’s late games; `_e4` uses deep10’s. Therefore the decrease in puzzle errors cannot be attributed solely to the stronger network. Network, visited-position distribution and selected puzzle set change together.

Evaluating both networks on one frozen set would settle a within-set network comparison; a crossed evaluation on both corpora would additionally reveal corpus dependence. Neither is required merely to report the existing descriptive difference.

## 5. L9/L6: primary documents recovered

The Firecrawl CLI was unavailable; direct web requests and archive-index requests also failed. Firecrawl’s MCP fetches nevertheless recovered both PDFs.

**HUJI:** the [archived report](https://web.archive.org/web/20230503105450id_/https://www.cs.huji.ac.il/w~ai/projects/2013/UlitmateTic-Tac-Toe/files/report.pdf), §II, supports **CLOSED-DRAW**. Its rule sentences state, with omissions:

> “The game ends … in a tie if all squares have been exhausted.”

Free choice also applies:

> “if the board has already been won”

Section V directly confirms the free-move weight **2**, board-win weight **5**, and that the weights were chosen somewhat arbitrarily. Replace “unverified” for this comparator; retain its course-report status.

**Padua:** the [repository PDF](https://thesis.unipd.it/bitstream/20.500.12608/86899/1/D%27Alberton_Enrico.pdf), §3.0.1, p. 28, explicitly establishes **closed boards**. Following redirection to a full or won board:

> “… the next player can choose to play in any open cell on any available local board that has not been won or drawn.”

Section 6.1 repeats that restriction. The stated global victory condition is a line of won boards; I found no explicit no-line terminal adjudication in those sections. Mark **CLOSED; terminal tiebreak unverified**, rather than asserting CLOSED-COUNT or presenting CLOSED-DRAW as fully verified. The executable terminal rule would settle the remaining distinction.

## 6. X6: delete the comparison from the paper

Conditioning makes the arithmetic honest, but not the estimate informative enough. `knowledge/06` §2 multiplies independent per-board possibilities while omitting inter-board reachability constraints; its lower endpoint is expressly **not a lower bound**. It supplies no quantified reason why the reachable population should lie within the proposed range.

Delete “five to ten orders above Othello” from the manuscript. The heuristic calculation may remain in the feasibility note, without using it to infer solving cost or categorical impossibility. A defensible reachable-state estimate—not another conditional phrase—would change this recommendation.

## 7. Remaining disputes

- **E2:** accepted. Membership holds across all twelve columns; fixed ordering requires the 16k qualification.
- **E14:** accepted: seven strong-net fits, eight including v2b.
- **E32:** accepted; stronger provenance evidence than I originally supplied.
- **J2:** accepted with the row-44 correction above.
- **L9:** I concede the distinction: a thesis does not contradict “nothing peer-reviewed.” My original objection conflated that wording with the survey’s broader academic claim.
- **X6:** the conditional repair addresses factual presentation; I still recommend deletion.
- **K5:** the caveat is correct, but “the supervised curves do not put the 220 Elo down to the width” still invites causal exclusion. State only that the parameter-matched supervised arm also loses later; self-play width effects remain unmeasured.
- **K9:** the sampled qualification is correct. Replace the surviving “solved outright” headlines in KNOWLEDGE 31a and the map with **“Perfect measured accuracy on the sampled one-open-board positions.”**

One minor adjudication correction: **K1’s “six fits” should read “six coefficients across two fits.”**