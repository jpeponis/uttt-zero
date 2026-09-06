"""One-line status of a training run, with an ETA modelled on a reference run.

    python tools/run_status.py runs/deep10_c1_300_s1 [--ref runs/deep10_c1_300]

The ETA takes the reference run's per-iteration time at the same iteration (so the sims
schedule and LR phases are built in), scales it by the ratio observed so far on this run,
and adds this run's own eval cost (the reference's until one has been seen) at every
iteration where (iter+1) % eval_every == 0.  Wall clock counts from config.json's
'started', so crash gaps are included.
"""
import argparse, datetime as dt, json, os, subprocess, sys


def rows(run):
    p = os.path.join(run, "log.jsonl")
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def base_time(r):  # iteration time without its eval
    t = r.get("t_iter", r["t_selfplay"] + r["t_train"] + r.get("t_exact_wait", 0))
    return t - r.get("t_eval", 0)


def gpu_line(match="3090"):
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,utilization.gpu,temperature.gpu,clocks.sm",
                              "--format=csv,noheader"], capture_output=True, text=True, timeout=10).stdout
        for l in out.splitlines():
            if match in l:
                n, u, t, c = [x.strip() for x in l.split(",")]
                return f"{match}: {u} {t}C {c}"
    except Exception:
        pass
    return f"{match}: n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--ref", default="runs/deep10_c1_300")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(a.run, "config.json")))
    iters, every = cfg["iters"], cfg["eval_every"]
    started = dt.datetime.strptime(cfg["_provenance"]["started"], "%Y-%m-%d %H:%M:%S")
    now = dt.datetime.now()
    R, F = rows(a.run), rows(a.ref)
    name = os.path.basename(a.run.rstrip("/"))
    out = os.path.join("runs", name + ".out")
    died = sum(1 for l in open(out) if "attempt" in l and "died" in l) if os.path.exists(out) else 0
    done = os.path.exists(os.path.join(a.run, "DONE"))
    if not R:
        print(f"{name}: no iterations logged yet ({(now - started).total_seconds() / 60:.0f} min since start); {gpu_line()}")
        return
    last = R[-1]
    n = last["iter"] + 1
    # ETA
    ref_base = {r["iter"]: base_time(r) for r in F}
    ref_evals = [r["t_eval"] for r in F if "t_eval" in r]
    my_evals = [r["t_eval"] for r in R if "t_eval" in r]
    common = [r["iter"] for r in R if r["iter"] in ref_base]
    scale = (sum(base_time(r) for r in R if r["iter"] in ref_base) / sum(ref_base[i] for i in common)) if common else 1.0
    t_eval = (sum(my_evals) / len(my_evals)) if my_evals else (sum(ref_evals) / len(ref_evals) if ref_evals else 0)
    remaining = 0.0
    for i in range(n, iters):
        remaining += scale * ref_base.get(i, ref_base[max(ref_base)] if ref_base else base_time(last))
        if every and (i + 1) % every == 0:  # --eval_every 0 (PLAN6 E7: evaluation out of process) has no in-run eval cost
            remaining += t_eval
    eta = now + dt.timedelta(seconds=remaining)
    elapsed_h = (now - started).total_seconds() / 3600
    state = "DONE" if done else "running"
    print(f"{name} {state}: iter {n}/{iters}  elapsed {elapsed_h:.1f}h  ETA {eta:%Y-%m-%d %H:%M} "
          f"(+{remaining / 3600:.1f}h; ref x{scale:.2f}, eval {t_eval / 60:.0f} min x{sum(1 for i in range(n, iters) if every and (i + 1) % every == 0)})"
          f"  sims {last['sims']} lr {last['lr']}  t_iter {base_time(last):.0f}s  died {died}  {gpu_line()}")
    ev = [r for r in R if any(k.startswith("vs_") for k in r)]
    if ev:
        e = ev[-1]
        vs = "  ".join(f"{k[3:].replace('_net_', '@')} {e[k]:.3f} [{e['ci_' + k[3:]][0]:.3f},{e['ci_' + k[3:]][1]:.3f}]"
                       for k in e if k.startswith("vs_"))
        print(f"  eval @{e['iter']}: {vs}  eg_wdl {e['eg_wdl_acc']:.3f} regret_raw {e['eg_regret_raw']:.3f}  t_eval {e['t_eval']:.0f}s")
        near = [r for r in F if any(k.startswith("vs_") for k in r) and abs(r["iter"] - e["iter"]) <= every]
        for r in sorted(near, key=lambda r: r["iter"]):  # the ref's evals bracketing this one
            vs = "  ".join(f"{k[3:].replace('_net_', '@')} {r[k]:.3f}" for k in r if k.startswith("vs_") and k in e)
            print(f"  ref  @{r['iter']}: {vs}  eg_wdl {r['eg_wdl_acc']:.3f} regret_raw {r['eg_regret_raw']:.3f}")


if __name__ == "__main__":
    main()
