# K1 — the reading instruments: implementation notes (written 2026-09-13 by the implementing agent; verbatim)

*The instruments for PLAN7 §5 items 2–4 — `runs/plan7/K1_readings_3060.sh`, `tools/common_positions.py`
and `tools/paired_contrast.py` — were built and frozen in an isolated worktree before K1's final
checkpoint exists (§7e M2-R row R9), and smoke-tested on the two count-trained nets that do. These are
the agent's notes: the files, the choices made where the pre-registration left one, the smoke and test
outputs verbatim, and what was not done. **The count-net control finding is the first thing to read**
(deliverable 2, "The finding the smoke produced"): a count-trained net's own paired count-margin Δ is
−0.0196, 95 % [−0.0271, −0.0122], so a control already satisfies claim 16's registered "established
decrease" fourfold — M2 row 2's defect in the other direction, and an owner / M3 decision, not the
script's.*

## 1. Files

- `C:\Users\John Peponis\Desktop\uttt-zero\.claude\worktrees\agent-ac333cb3e36360c4f\runs\plan7\K1_readings_3060.sh`
- `C:\Users\John Peponis\Desktop\uttt-zero\.claude\worktrees\agent-ac333cb3e36360c4f\tools\common_positions.py`
- `C:\Users\John Peponis\Desktop\uttt-zero\.claude\worktrees\agent-ac333cb3e36360c4f\tools\paired_contrast.py`
- `C:\Users\John Peponis\Desktop\uttt-zero\.claude\worktrees\agent-ac333cb3e36360c4f\tests\test_common_positions.py`

Worktree fast-forwarded to `33ebd8a` before starting. No existing tool, `PLAN7.md`, `KNOWLEDGE.md`, `docs/`, `queue14.sh` or `eval_run_k1.sh` was touched; nothing was written into the main checkout (verified by mtime on the artifacts that could have been overwritten).

## 2. The deliverables

### `runs/plan7/K1_readings_3060.sh`

The count pass retargeted: `R=runs/deep8_c1_300_e8_draw`, `RULE=draw` passed explicitly to every tool that takes it, `D=cuda:1` (the 3060, as in the template), outputs `runs/plan7/K1_<tag>.out`, combined log `runs/plan7/K1_readings.out`. 20 invocations: corpus_stats, puzzles, surprise, probe_value, freemove, decision ×2, atlas + `--report`, probe build, principles, tablebase_grade, value_decomp, book, book_stats, probe fit, probe_report, ownership_grade, then `common_positions` (item 3) and `paired_contrast` (item 4).

**Exact final names on disk** (`tag_path` appends `_draw`; every downstream `--data`/`--report`/`--fig` in the script names the *tagged* file, not the one passed to `--out`):

| given to `--out` | written |
|---|---|
| `runs/probe_data_deep10late_e8draw.npz` | `runs/probe_data_deep10late_e8draw_draw.npz` |
| `suites/puzzles_v5_dev.npz` | `suites/puzzles_v5_dev_draw.npz` + `suites/puzzles_v5_dev_draw.json` |
| `runs/book_deep8_e8draw.json` | `runs/book_deep8_e8draw_draw.json` + `.md` |
| `runs/plan7/K1_A1_atlas.json` | `runs/plan7/K1_A1_atlas_draw.json` |
| `runs/plan7/K1_principles_deep8e8draw.json` | `runs/plan7/K1_principles_deep8e8draw_draw.json` |
| `runs/plan7/K1_E9_ownership.json` | `runs/plan7/K1_E9_ownership_draw.json` |
| (implicit) | `runs/deep8_c1_300_e8_draw/value_decomp_draw.json`, `probes_draw.json`, `probes_draw.png` |

Choices I made:

1. **The corpus question — option (a), stated in the header as the thing M3 should judge.** Held-out readings keep the template's corpora (`runs/deep10_c1_300` last 20, `runs/v2a` last 2) and read them under `draw`: the same natural positions `_e8` was read on under `count`, so any difference from the count pass is the rule and the net with the position distribution held fixed. The cost is stated plainly in the header: these are positions a *count*-rule policy produced, so the readings describe the draw net's judgement of count-play positions, not of the positions it actually meets. The draw net's own games are used only where the corpus *is* the object — `corpus_stats` (24, 25, 27) and `principles`' draw statistics (26, 33–35) — exactly as the template does.
2. **`surprise` and `probe_value` read the draw run's own buffer.** `probe_value.check_buffer_rule` refuses a count-rule run's buffer under `--rule draw`; I verified the refusal fires (output below). The only draw-rule buffer that will exist is `$R/latest_full.pt`, so those two readings — and only those two — are not held out. The header says so and names the tool change that would fix it (separating "where the positions come from" from "what rule the search runs under"), which I did not make.
3. **Two guards added** (`$R/DONE` and `net_0300.pt`), matching `eval_run_k1.sh`'s R8 remedy; the template had none.
4. **Items 3 and 4 appended** so one command produces the whole pre-registered reading; `paired_contrast` is skipped with a message if `eval_run_k1.sh` has not run, rather than silently producing a partial reading.
5. **`common_positions`' two corpora are the two nets' own** (`$R` and `runs/deep8_c1_300_e8`) — symmetric, neither net advantaged by the position source, and every number reported by source corpus as well as pooled (M2 row 17).
6. **`DRY=1` and `REPO=`** — three lines in `run()` so the frozen commands themselves can be re-verified without executing them, and so the dry run can be made from a worktree.

Rule bookkeeping checked against the code: every corpus named resolves through `corpus_stats.corpus_rule` (all four count runs carry a `config.json` with no `rule` key = pre-K1 = count; the draw run's files carry the tag), so **no `--corpus_rule` override is needed anywhere and no refusal fires** — with the one exception in choice 2, which is why that choice exists. `book.py` checks `--paired`'s rule but not `--compare`'s, so the cross-rule book comparison (`runs/book_deep8_e8.json`) passes by design; noted in the header.

`bash -n` clean.

### `tools/common_positions.py`

15 000 positions per corpus (default) via `freemove.sample_positions` (plies 6–60, ≤ 5 per game, seed 0 per corpus, `game_id` kept and offset so two corpora's clusters cannot collide); 2 × 2 cells of (net, rule), raw and 256-sim search value from `value_decomp.values` (one `BatchedSearch` per batch, `gumbel_scale 0`, `depth_cap min(sims,24)`); `freemove`'s design matrix and its ownership-by-class model fitted per cell with `freemove.ols_cluster`; the paired Δ per net as **one** regression of `(v_draw − v_count)`; every position with ≤ 14 empties in open boards solved exactly under both rules with `solve_batch` in a pool of 8. JSON + readable stdout. Refuses nothing on rule grounds; records each corpus's generating rule.

Choices:

1. **`freemove` has no importable design function** — it builds both matrices inline in `main()`. `macro_threats`, `ols_cluster` and `sample_positions` are imported; the column list is `freemove.py:127`/`:140-141` verbatim and in order, with the file-and-line reference in a comment. The test checks three columns against a hand computation.
2. **The intersection solved under both rules is the whole subset** — `solve_children` is complete, not bounded — so M2 row 17's "intersection" is stated, not assumed.
3. **The raw value head never sees the rule.** For one net the paired raw Δ is *identically zero* with a zero-width interval. Reported as `vacuous`, never as "invariant", and an **across-net block** (β(A) − β(B) under each rule) added, since that is the only form in which claim 16's "raw head" half is readable at all.
4. **A difference-in-differences block**, labelled NOT pre-registered — see the finding below.
5. Claim 16's **secondary** (each cell's own coefficient against [−0.015, +0.015]) is printed too, since §5 item 2 states it.
6. `§` removed from *printed* strings (it was emitting a raw cp1252 byte 0xA7 into the `.out`); kept in docstrings, which are never printed.

**The finding the smoke produced, and why it matters.** On two *count*-trained nets, each net's own paired count-margin Δ is **−0.0196, 95 % [−0.0271, −0.0122]** — the rule change alone moves that coefficient, because under `draw` a count-decided terminal backs up 0 instead of ±1 and every position with a positive count margin is pulled towards zero. A count-trained control therefore **already satisfies §5 item 2's registered "established decrease" (upper endpoint ≤ −0.005) by a factor of four.** This is M2 row 2's defect in the other direction. I did not change the registered verdict — it prints unchanged — but the count parent runs as net B in the same call so its Δ sits beside the draw net's as the control, and the DiD block gives the confound-free quantity. **The DiD is the null the smoke was supposed to show: `macro_score −0.0000, 95 % [−0.0011, +0.0010]`.** This is for M3 / the owner to decide before the readings are written up; it is recorded in the script header, the tool's docstring and the commit message.

### `tools/paired_contrast.py`

`--count` / `--draw` match JSONs; s_C and s_D with their own intervals, the contrast **1 − s_D − s_C**, one joint resample of opening IDs (2 000 draws, seed 0) from which both scores *and* the contrast are recomputed, and the ±3-point verdict (positive / negative / unresolved).

Choices:

1. **±3 points = ±0.03 in score**: positive if the whole interval lies above +0.03, negative if wholly below −0.03, else unresolved. Whether the interval excludes *zero* is printed separately so both readings are visible.
2. **The marginal intervals come from the joint resample**, and are asserted equal to `uttt.openings.bootstrap_mean_ci` at the same seed and `n_boot` — so the joint estimator cannot drift from the one the match file reports.
3. **Integrity checks**: exits if the suites differ or the opening lists differ; exits if `summary.overall.score` disagrees with the mean of `openings[]`; warns if the two files do not share player A or B. A shared rule is **not** fatal — the arithmetic runs and every line says the contrast is not interpretable.

## 3. Outputs, verbatim

**`common_positions.py` smoke** (`--n 2000 --sims 64 --device cuda:0`, the two count nets), abridged to the head, the paired block and the DiD; the full 330-line output is at `C:\Users\JOHNPE~1\AppData\Local\Temp\claude\C--Users-John-Peponis-Desktop-uttt-zero\4d42c8ec-1c70-463f-90b5-73b4ac48ead1\scratchpad\cp_smoke.out`:

```
corpus A: 2000 positions from 400 games of .../runs/deep8_c1_300_e8 (generated under count; 20 game files, plies 6-60, <= 5 per game, seed 0)
corpus B: 2000 positions from 400 games of .../runs/deep8_c1_300_e4 (generated under count; 20 game files, plies 6-60, <= 5 per game, seed 0)
4000 positions in all; 800 source games; free move 0.106; design 9 regressors + the ownership model's 14  [2s]

solving the 503 positions with <= 14 empties in open boards under both rules (8 processes) ...
solved in 8s. Exact value for the mover (W/D/L) and the rule's effect:
  pooled    n=   503  count 0.408/0.217/0.376   draw 0.247/0.519/0.235   changed 0.302  (win->draw 0.161, loss->draw 0.141)
  corpus_a  n=   236  count 0.407/0.208/0.386   draw 0.225/0.559/0.216   changed 0.352  (win->draw 0.182, loss->draw 0.169)
  corpus_b  n=   267  count 0.408/0.225/0.367   draw 0.266/0.483/0.251   changed 0.258  (win->draw 0.142, loss->draw 0.116)

  net A under count: mean 64-sim search value -0.1511, raw +0.0008  [30s]
  net A under draw : mean 64-sim search value -0.1483, raw +0.0008  [52s]
  net B under count: mean 64-sim search value -0.1483, raw +0.0021  [73s]
  net B under draw : mean 64-sim search value -0.1454, raw +0.0021  [95s]

--- net A (runs/deep8_c1_300_e8/net_0300.pt), pooled (n = 4000, 800 games)
  paired difference, search value (Delta = beta_draw - beta_count, cluster-robust by game):
    claim  8  free_move        +0.0004  95 % [-0.0214, +0.0222]   INVARIANT
    claim 13  threats_for      -0.0155  95 % [-0.0324, +0.0014]   UNRESOLVED
    claim 13  threats_against  -0.0089  95 % [-0.0250, +0.0071]   INVARIANT
    claim 16  macro_score      -0.0196  95 % [-0.0271, -0.0122]   ESTABLISHED DECREASE
  raw value: the difference is identically zero -- the raw value head is a function of the position alone and never sees the rule, so this contrast is vacuous for one net. Claim 16's raw-head reading is the across-net block below.

--- net B (runs/deep8_c1_300_e4/net_0300.pt), pooled (n = 4000, 800 games)
  paired difference, search value (Delta = beta_draw - beta_count, cluster-robust by game):
    claim  8  free_move        -0.0050  95 % [-0.0273, +0.0173]   INVARIANT
    claim 13  threats_for      -0.0164  95 % [-0.0335, +0.0007]   UNRESOLVED
    claim 13  threats_against  -0.0088  95 % [-0.0250, +0.0073]   INVARIANT
    claim 16  macro_score      -0.0196  95 % [-0.0270, -0.0122]   ESTABLISHED DECREASE

DIFFERENCE IN DIFFERENCES -- NOT a pre-registered reading; the verdicts above are the registered ones.
--- pooled (n = 4000, 800 games)
  paired difference, search value, DiD (Delta_A - Delta_B, cluster-robust by game):
    claim  8  free_move        +0.0054  95 % [+0.0010, +0.0098]   INVARIANT
    claim 13  threats_for      +0.0009  95 % [-0.0021, +0.0040]   INVARIANT
    claim 13  threats_against  -0.0001  95 % [-0.0035, +0.0033]   INVARIANT
    claim 16  macro_score      -0.0000  95 % [-0.0011, +0.0010]   CONTRADICTED
  raw value: identically zero (neither net's raw head sees the rule)
```

(`CONTRADICTED` on the DiD is the rule working correctly: the interval lies wholly above −0.005.)

**`paired_contrast.py` smoke** (two existing count files sharing the suite):

```
PLAN7 sec. 5 item 4 -- cross-play contrast on 516 openings (1032 games per match) of suite openings_v1
  A = runs/deep8_c1_300_e8/net_0300.pt @ 64 sims      B = runs/deep8_c1_300_e4/net_0300.pt @ 64 sims
  count-rule match: .../paired_vs_deep8c1_300e4_64.json  (rule count)
  draw-rule match : .../paired_vs_deep8c1_300_64.json  (rule count)
  !!! BOTH FILES WERE PLAYED UNDER RULE 'count'. The contrast 1 - s_D - s_C is defined across the two rules; with one rule it is not interpretable and no claim of sec. 5 item 4 may be read off it. The arithmetic below is exercised, not the reading.
  !!! the two matches do not share player B: runs/deep8_c1_300_e4/net_0300.pt (count file) vs runs/deep8_c1_300/net_0300.pt (draw file). The contrast assumes one pair of nets played twice.

  s_C  A's score under count =  55.77 %   95 % [ 53.39,  58.24]   Elo   +40   draws  22.2 %
  s_D  A's score under count =  77.08 %   95 % [ 74.85,  79.22]   Elo  +211   draws  15.2 %
       (B's score under count is 1 - s_D =  22.92 %: a paired match is zero-sum, so the colour-swapped cells are complementary, not four numbers)

  contrast 1 - s_D - s_C = -32.85 points   95 % [-36.09, -29.55]   (joint pair bootstrap over opening IDs, 2000 draws, seed 0)
  verdict by the +- 3 point rule: NOT INTERPRETABLE (THE TWO FILES SHARE A RULE)

  end reasons, count-rule match: count-decided 13.6 %, no-line terminal 22.2 %;  draw-rule match: 10.1 % / 15.2 %
```

**Tests** (`.venv/Scripts/python.exe tests/test_common_positions.py`):

```
design: 2887 positions from 220 random games, 10 columns, full rank; free move 0.112; the count margin and the empty count agree with a hand computation
  macro_score      put in -0.0200  recovered -0.0201  95 % [-0.0205, -0.0196]  established decrease
  free_move        put in +0.0500  recovered +0.0503  95 % [+0.0492, +0.0513]  dependent
  threats_for      put in +0.0000  recovered -0.0003  95 % [-0.0013, +0.0008]  invariant
  threats_against  put in +0.0100  recovered +0.0099  95 % [+0.0089, +0.0108]  invariant
  the game-level random effect (sd 1.0, in both responses) cancels: the paired intercept is +0.0075 and the raw difference of means +0.0091
an identically zero paired difference is reported as vacuous, not as an invariance finding
the three verdict rules of sec. 5 item 2 behave at their boundaries
contrast: s_C 0.5613, s_D 0.4750, 1 - s_D - s_C = -0.0363 (put in -0.0363), 95 % [-0.0975, +0.0225], verdict unresolved
joint bootstrap: with s_D's openings set to 1 - s_C's, the contrast interval is [-1.1e-16, +1.1e-16] while each score's own interval is 8.5 points wide -- the same resample was used for both
a shared rule is flagged, a different suite is refused, and the +- 3 point rule reads as positive / negative / unresolved
ok [3.1s]
```

**Dry run of the frozen script** (`DRY=1 REPO=<worktree> bash runs/plan7/K1_readings_3060.sh`): 19 of 20 invocations return `argparse exit 0`; the 20th is `book_stats.py`, which has no argparse (it reads paths from `argv`) and is handled explicitly. Because argparse validates left-to-right before `-h` fires, this also validates `--rule draw` against each tool's `choices`.

**Tiny execution pass** (real runs, tiny sizes, all writes in the scratchpad — this is what proves the tag names the frozen script hard-codes): `corpus_stats` count and draw (relabel), `decision --rule draw`, `freemove --rule draw`, `puzzles`, `atlas` + `--report` on the tagged name, `probe build`, `principles`, `tablebase_grade`, `value_decomp`, `probe fit`, `probe_report`, `ownership_grade`, `surprise`, `probe_value`, `book` (with a draw-tagged paired file and a cross-rule `--compare`), `book_stats` — every one exit 0, and the files produced were exactly `atlas_draw.json`, `book_draw.json`/`.md`, `ownership_draw.json`, `principles_draw.json`, `probe_data_draw.npz`, `puzzles_v5_dev_draw.npz`/`.json`, `mini_run/value_decomp_draw.json`, `mini_run/probes_draw.json`. The buffer refusal the header rests on:

```
$ .venv/Scripts/python.exe tools/probe_value.py ... --buffer runs/deep8_c1_300/latest_full.pt --rule draw
runs/deep8_c1_300/latest_full.pt holds positions from a count-rule run and --rule is draw: its values, ownership and margin targets were decided under count. Read it under --rule count, or point --buffer at a draw-rule run.
   exit 1
```

## 4. Not done, and why

- **The full pass was not run** — as instructed, and `runs/deep8_c1_300_e8_draw` does not exist.
- **The count parent's pass is still in flight** on cuda:1 (it was at the 16 384-sim `book` step at 00:16). `runs/book_deep8_e8.json` — the readings script's `--compare` — does not exist yet; it is a forward reference like `net_0300.pt`. All my GPU work used **cuda:0** (the 3090; torch orders `cuda:0`=3090, `cuda:1`=3060 here, matching the template's comment).
- **`freemove.ols_cluster` raises `LinAlgError: Singular matrix` on very small samples** (n = 60 in my first tiny run; fine at n = 600 and at the smoke's 4000). The real pass runs 30 000. I did not add a `pinv` fallback because that means editing `freemove.py`.
- **I did not change `check_buffer_rule`** to separate "where positions come from" from "what rule the search runs under", though the draw readings would be better for it. That is a tool change, and the brief said not to touch existing tools.
- **I did not change the registered verdict rules** despite the finding that a count-trained control already satisfies claim 16's primary. Changing a pre-registration is the owner's and M3's decision, not a reading script's; the tool prints the control and the DiD so the decision can be made on evidence.
- **Cosmetic**: the new files are LF; `core.autocrlf=true` will make them CRLF on the next checkout, matching the existing `runs/*.sh`, which are already CRLF and run fine.
