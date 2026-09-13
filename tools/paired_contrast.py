"""The cross-play contrast of PLAN7 §5 item 4, with the joint pair bootstrap M2 row 13 asked for.
Written and frozen before K1's final checkpoint exists (§7e M2-R row R9).

    .venv/Scripts/python.exe tools/paired_contrast.py \
      --count runs/deep8_c1_300_e8_draw/paired_vs_deep8c1_300e8_64.json \
      --draw  runs/deep8_c1_300_e8_draw/paired_vs_deep8c1_300e8_64_draw.json \
      --out runs/plan7/K1_paired_contrast.json

Two paired matches of the SAME pair of nets on the SAME opening suite, one played under `count` and one
under `draw` (tools/openings.py match --rule ..., which tags the draw file's name). A is the draw-trained
net in K1's use; s_C is A's score under count and s_D its score under draw. Because a paired match is
zero-sum, B's score under draw is 1 - s_D, so §5 item 4's pre-registered contrast -- the count-trained
net's score under draw minus the draw-trained net's score under count -- is

    contrast = (1 - s_D) - s_C = 1 - s_D - s_C

and its prediction is positive. The two scores come from the same 516 openings, so they are not
independent: the interval is a JOINT pair bootstrap -- one resample of opening IDs, both scores and the
contrast recomputed from that same resample, 2 000 draws, seed 0 (M2 row 13). Resampling each score on
its own would give each marginal right and the contrast's interval wrong.

The verdict is the project's +-3 point rule, which is the run-to-run band a score is read against (§5's
closing paragraph): POSITIVE if the whole 95 % interval lies above +3 points, NEGATIVE if it lies wholly
below -3, UNRESOLVED otherwise. Two scores and a contrast -- not an interaction: either net's general
superiority moves it, so no mechanism is attributed to it (M2 row 13).

The two files must share the suite and must differ in their rule. A pair that shares the rule is reported
and computed anyway -- the arithmetic is the same and it is how the mechanics are smoke-tested -- but
every line of the output says the contrast is not interpretable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uttt.openings import bootstrap_mean_ci, elo  # noqa: E402

MARGIN = 0.03  # +- 3 points, the band a score is read against


def load_match(path: str) -> dict:
    """A tools/openings.py match JSON, reduced to what the contrast needs: the rule, the suite, the
    players, and A's score in every opening pair."""
    with open(path) as f:
        d = json.load(f)
    for key in ("openings", "summary", "suite"):
        if key not in d:
            sys.exit(f"{path} is not a tools/openings.py match file: no {key!r} field")
    ids = np.array([o["id"] for o in d["openings"]], dtype=np.int64)
    pair = np.array([0.5 * (o["a_as_x"] + o["a_as_o"]) for o in d["openings"]], dtype=np.float64)
    recorded = d["summary"]["overall"]["score"]
    if abs(float(pair.mean()) - recorded) > 1e-9:
        sys.exit(f"{path}: the per-opening records average to {pair.mean():.6f} but summary.overall.score is "
                 f"{recorded:.6f}; the file is inconsistent and the contrast would be read off the wrong numbers")
    return {"path": path, "rule": d.get("rule", "count"), "suite": d["suite"], "a": d.get("a"), "b": d.get("b"),
            "a_sims": d.get("a_sims"), "b_sims": d.get("b_sims"), "ids": ids, "pair": pair,
            "score": float(pair.mean()), "recorded_ci": d["summary"]["overall"]["ci"],
            "draws": d["summary"]["overall"]["draws"], "end_count": d["summary"]["overall"]["end_count"],
            "end_equal": d["summary"]["overall"]["end_equal"]}


def check_pair(c: dict, d: dict) -> list[str]:
    """The suite must be the same one, opening for opening. Returns the notes to print; exits on a
    difference that would make the contrast meaningless."""
    notes = []
    suite_keys = ("name", "corpus", "corpus_games", "plies", "seed", "built")
    cs = {k: c["suite"].get(k) for k in suite_keys}
    ds = {k: d["suite"].get(k) for k in suite_keys}
    if cs != ds:
        sys.exit(f"the two matches were played on different suites:\n  {c['path']}: {cs}\n  {d['path']}: {ds}")
    if not np.array_equal(c["ids"], d["ids"]):
        sys.exit(f"the two matches do not hold the same openings in the same order ({len(c['ids'])} vs "
                 f"{len(d['ids'])} records): a joint pair bootstrap has to resample one list of openings")
    if c["rule"] == d["rule"]:
        notes.append(f"!!! BOTH FILES WERE PLAYED UNDER RULE {c['rule']!r}. The contrast 1 - s_D - s_C is defined "
                     f"across the two rules; with one rule it is not interpretable and no claim of sec. 5 item 4 may be "
                     f"read off it. The arithmetic below is exercised, not the reading.")
    else:
        if c["rule"] != "count" or d["rule"] != "draw":
            sys.exit(f"--count must be the count-rule match and --draw the draw-rule one; got rules "
                     f"{c['rule']!r} and {d['rule']!r}")
    for side in ("a", "b"):
        if c[side] != d[side]:
            notes.append(f"!!! the two matches do not share player {side.upper()}: {c[side]} (count file) vs "
                         f"{d[side]} (draw file). The contrast assumes one pair of nets played twice.")
    for side in ("a_sims", "b_sims"):
        if c[side] != d[side]:
            notes.append(f"note: {side} differs between the files ({c[side]} vs {d[side]}).")
    return notes


def joint_bootstrap(pair_c: np.ndarray, pair_d: np.ndarray, n_boot: int, seed: int) -> dict:
    """One resample of opening IDs; both scores and the contrast recomputed from it. The marginal interval
    of each score is therefore exactly uttt.openings.bootstrap_mean_ci's with the same seed and n_boot --
    asserted here, so the joint estimator cannot drift away from the one the match reports."""
    n = len(pair_c)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    sc, sd = pair_c[idx].mean(1), pair_d[idx].mean(1)
    contrast = 1.0 - sd - sc
    q = lambda x: (float(np.quantile(x, 0.025)), float(np.quantile(x, 0.975)))  # noqa: E731
    out = {"s_count": q(sc), "s_draw": q(sd), "contrast": q(contrast), "n_boot": n_boot, "seed": seed,
           "contrast_excludes_zero": bool(np.quantile(contrast, 0.025) > 0 or np.quantile(contrast, 0.975) < 0)}
    for name, x, series in (("s_count", pair_c, sc), ("s_draw", pair_d, sd)):
        ref = bootstrap_mean_ci(x, n_boot, seed)
        assert ref is None or max(abs(a - b) for a, b in zip(out[name], ref)) < 1e-12, (name, out[name], ref)
    return out


def verdict(lo: float, hi: float, margin: float = MARGIN) -> str:
    """§5 item 4's +- 3 point rule."""
    if lo > margin:
        return "positive"
    if hi < -margin:
        return "negative"
    return "unresolved"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", required=True, help="the paired match JSON played under rule count")
    ap.add_argument("--draw", required=True, help="the paired match JSON played under rule draw")
    ap.add_argument("--boot", type=int, default=2000, help="joint pair-bootstrap resamples (§5 item 4: 2 000)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    c, d = load_match(a.count), load_match(a.draw)
    notes = check_pair(c, d)
    interpretable = c["rule"] != d["rule"]
    n = len(c["ids"])
    b = joint_bootstrap(c["pair"], d["pair"], a.boot, a.seed)
    contrast = 1.0 - d["score"] - c["score"]
    v = verdict(*b["contrast"]) if interpretable else "not interpretable (the two files share a rule)"

    print(f"PLAN7 sec. 5 item 4 -- cross-play contrast on {n} openings ({2 * n} games per match) of suite "
          f"{c['suite'].get('name')}")
    print(f"  A = {c['a']} @ {c['a_sims']} sims      B = {c['b']} @ {c['b_sims']} sims")
    print(f"  count-rule match: {c['path']}  (rule {c['rule']})")
    print(f"  draw-rule match : {d['path']}  (rule {d['rule']})")
    for note in notes:
        print(f"  {note}")
    print(f"\n  s_C  A's score under {c['rule']:5s} = {100 * c['score']:6.2f} %   95 % [{100 * b['s_count'][0]:6.2f}, "
          f"{100 * b['s_count'][1]:6.2f}]   Elo {elo(c['score']):+5.0f}   draws {100 * c['draws']:5.1f} %")
    print(f"  s_D  A's score under {d['rule']:5s} = {100 * d['score']:6.2f} %   95 % [{100 * b['s_draw'][0]:6.2f}, "
          f"{100 * b['s_draw'][1]:6.2f}]   Elo {elo(d['score']):+5.0f}   draws {100 * d['draws']:5.1f} %")
    print(f"       (B's score under {d['rule']} is 1 - s_D = {100 * (1 - d['score']):6.2f} %: a paired match is zero-sum, "
          f"so the colour-swapped cells are complementary, not four numbers)")
    print(f"\n  contrast 1 - s_D - s_C = {100 * contrast:+6.2f} points   95 % [{100 * b['contrast'][0]:+6.2f}, "
          f"{100 * b['contrast'][1]:+6.2f}]   (joint pair bootstrap over opening IDs, {a.boot} draws, seed {a.seed})")
    print(f"  verdict by the +- {100 * MARGIN:.0f} point rule: {v.upper()}")
    if interpretable:
        print(f"  (the interval {'excludes' if b['contrast_excludes_zero'] else 'includes'} zero; the verdict is read "
              f"against +- {100 * MARGIN:.0f} points, not against zero -- one seed per rule, so a difference inside the "
              f"band is not separable from the run-to-run band)")
    print(f"\n  end reasons, count-rule match: count-decided {100 * c['end_count']:.1f} %, no-line terminal "
          f"{100 * c['end_equal']:.1f} %;  draw-rule match: {100 * d['end_count']:.1f} % / {100 * d['end_equal']:.1f} %")

    if a.out:
        rec = {"rules": [c["rule"], d["rule"]], "interpretable": interpretable, "notes": notes,
               "suite": c["suite"], "openings": n, "a": c["a"], "b": c["b"], "a_sims": c["a_sims"], "b_sims": c["b_sims"],
               "files": {"count": c["path"], "draw": d["path"]},
               "s_count": {"score": c["score"], "ci": b["s_count"], "elo": elo(c["score"]), "draws": c["draws"]},
               "s_draw": {"score": d["score"], "ci": b["s_draw"], "elo": elo(d["score"]), "draws": d["draws"]},
               "contrast": {"value": contrast, "ci": b["contrast"], "margin": MARGIN, "verdict": v,
                            "excludes_zero": b["contrast_excludes_zero"]},
               "bootstrap": {"kind": "joint pair bootstrap over opening IDs", "n_boot": a.boot, "seed": a.seed}}
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        with open(a.out, "w") as f:
            json.dump(rec, f, indent=1)
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
