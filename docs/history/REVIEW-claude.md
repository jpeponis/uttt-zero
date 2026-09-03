# REVIEW-claude — once-over of the codebase and PLAN3 (2026-08-30)

Independent of `REVIEW-sol.md` (written before reading it). Scope: correctness risks,
optimizations, and PLAN3 §6 priorities. The ten REVIEW-codex findings are treated as closed
except where a residual is noted.

## Verdict

The pipeline, measurement kit and result tables held up under a line-by-line read: no
correctness bug found in the engines, search, buffer, training loop, suites or statistics.
The findings below are operational hazards (2 will actively break the planned longer runs),
one wrong claim in PLAN3 §6 that would misdirect a 9-hour run, and priority adjustments.

## Findings

1. **PLAN3 §6.1(b) has the batch-scaling logic backwards** (high confidence, empirical
   check running). "The wide nets are GPU-bound, so batch scaling is now nearly free" —
   it is the *launch-bound* regime where batch scaling is nearly free (search cost ≈
   Σ sims regardless of batch, PLAN2 §5.3 says exactly this). If wide128 at 4096 games
   is GPU-bound, `--games 8192` doubles self-play wall-clock and games/s stays ~43: not
   free, and by itself worth nothing. What 8192 actually buys is (a) per-pool
   phase-dependent self-play budgets without the ~2× launch penalty, and (b) a bigger
   sample per checkpoint — not throughput. Evidence the regime is mixed: 6×64→6×96→6×128
   slowdowns (200→57→43 g/s) exceed the FLOP ratios (1→2.25→4), so part of the time is
   still launch/CPU overhead and some gain is possible, but "nearly free" is unmeasured.
   → `runs/probe_g8192` (3 iterations, running now) settles it before any 9 h commitment.

2. **`runs/eval_run.sh`, `watch_run.sh`, `tools/plot_run.py` hardcode `net_0150.pt` /
   `iter >= 119`** (certain). A `--iters 300` run (PLAN3 §6.1c) produces `net_0300.pt`;
   the post-run chain would silently evaluate a missing file and the watcher would wait
   forever. Parameterize the final-checkpoint name (derive from config.json or `ls
   net_*.pt | tail -1`) and the tail-iteration threshold before launching longer runs.

3. **`latest.pt` is written non-atomically every iteration** (high). With the buffer
   embedded (~0.5–1 GB every 10th iteration) the write takes seconds; a crash or power
   loss mid-save destroys the only resume point *and* the buffer. `torch.save` to
   `latest.pt.tmp` + `os.replace` is a 2-line fix. (Residual of REVIEW-codex finding 4;
   RNG/GradScaler state still unsaved — accept that part, the noise band swallows it.)

4. **The replay window shrinks when games double** (certain, arithmetic). Buffer 2 M ÷
   ~262 k positions/iter ≈ 7.6 iterations of history at 4096 games; at 8192 it halves to
   3.8. PLAN3 §6.1c says "replay window up" only for longer runs — couple it to `--games`
   too: `--games 8192` should come with `--buffer 4000000` (~1.1 GB VRAM, fine on the
   3090) or the effective recipe changes in two ways at once, violating the
   one-change-per-run rule.

5. **Self-play sims scaling is missing from §6.1's "only live strength lever" list**
   (medium). The evidence points at target quality: c_scale 1.0 (+40) sharpened the
   improved-policy target; 256-vs-64 self-match is 77–80 % (search far from saturated);
   the teacher is the binding constraint per PLAN2 §4. A `wide128_c1 + sims_schedule
   →96` run is the same kind of lever and costs only linear time in the GPU-bound
   regime. Watch `cap_hit` at 96 sims (currently 0.004–0.009 at 64, depth_cap 12);
   raise `--depth_cap` to 16 if it climbs past a few percent.

6. **Anchor loading for mixed-architecture anchors works, verified** (certain):
   `load_checkpoint` rebuilds from the checkpoint's own cfg (blocks/filters/planes/
   own_classes), so adding `runs/wide128_c1/net_0150.pt` as a third anchor (PLAN3 §6.2)
   needs no code change. In-run eval grows to ~110 s per eval point — acceptable.

7. **All frozen suites descend from v2a games** (medium, no action yet). Openings
   ("natural" ∝ v2a frequency), endgame set, puzzles, decision/freemove analyses all
   sample the distribution of a net that is now −112 Elo below current best. The
   yardstick stays valid for *ranking* (never rebuild v1), but a second yardstick built
   from wide128_c1 games (openings_v2, endgame_v2) would guard against slowly
   overfitting the recipe to a stale distribution. Cheap, 3060-able, not urgent.

8. **No git repo** (certain; PLAN3 §6.6 already says it). Two days of work, one
   non-atomic checkpoint file, no backup. `git init` + commit code/docs/suites/configs/
   one final net per run (~20 MB each, plain git is fine) should precede the next long
   run, not follow it.

9. **`tools/puzzles.py` defaults `--out suites/puzzles_v1.npz`** (certain). PLAN3 §6.5
   says to rerun the puzzle miner against wide128_c1; doing so with defaults silently
   overwrites the frozen v1 yardstick — the exact trap §7 warns about. Make `--out`
   required or default it to a non-suite path.

10. Minor, no action needed: `evaluate()` re-captures CUDA graphs each eval point (~10 s,
   measured inside t_eval); `stats.first_moves.tolist()` syncs per step; exact-label
   machinery stays on in the recipe as a no-op (harmless, keeps config parity);
   `sims_schedule` rebuild leaks the old search's graphs until GC (transient VRAM);
   mctx golden test still absent (REVIEW-codex 10 residual) — the eager/graph and
   v1/v2-identity tests cover the practically dangerous regressions.

## PLAN3 §6 priorities — what I would change

Keep the ordering (scaling first) but restructure the first day:

0. **Before any run**: git init + commit (finding 8), fix eval_run.sh/watch_run.sh
   (finding 2), atomic latest.pt (finding 3). ~30 min total.
1. **Probe, then scale**: read `runs/probe_g8192` / `runs/probe_b8` (running); commit to
   `--games 8192` only if games/s materially improves; otherwise spend the wall-clock on
   blocks and iterations. First run: 8×128 c_scale 1.0 (probe prices it), second:
   sims→96 (finding 5), third: `--iters 300` with drops 200/280 — one change per run,
   judged by §2 rules, wide128_c1 added as third anchor.
2. Analysis second pass + best-play retune on the 3060 concurrently (as written).
3. CodinGame port stays last (as written).
