"""Read-only checkpoint integrity check. CPU only."""
import os, sys, time, json, hashlib
import torch

ROOT = r"C:\Users\John Peponis\Desktop\uttt-zero"
sys.path.insert(0, ROOT)
from uttt.model import NetConfig, build_net

def describe(v, depth=0):
    if torch.is_tensor(v):
        return f"tensor{tuple(v.shape)} {v.dtype} dev={v.device}"
    if isinstance(v, dict):
        return "dict(%d): %s" % (len(v), list(v.keys())[:8])
    if isinstance(v, (list, tuple)):
        return f"{type(v).__name__}({len(v)})"
    return f"{type(v).__name__} {v!r}"[:120]

def check(path):
    out = {"path": path}
    if not os.path.exists(path):
        out["ERROR"] = "missing"
        return out
    out["size_bytes"] = os.path.getsize(path)
    st = os.stat(path)
    out["mtime"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
    t0 = time.perf_counter()
    try:
        ck = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as e:
        out["ERROR"] = f"{type(e).__name__}: {e}"
        return out
    out["load_seconds"] = round(time.perf_counter() - t0, 2)
    out["keys"] = list(ck.keys())
    for k in ("iter", "attempt", "global_step"):
        out[k] = ck.get(k, "<absent>")
    # buffer
    buf_key = next((k for k in ("buffer", "buf") if k in ck), None)
    out["buffer_key"] = buf_key
    if buf_key is not None:
        sd = ck[buf_key]
        out["buffer_top_keys"] = list(sd.keys()) if isinstance(sd, dict) else describe(sd)
        if isinstance(sd, dict):
            out["buffer_size"] = sd.get("size")
            out["buffer_pos"] = sd.get("pos")
            inner = sd.get("buf")
            if isinstance(inner, dict):
                rows = {}
                for k, v in inner.items():
                    rows[k] = describe(v)
                out["buffer_arrays"] = rows
                nrows = {k: (tuple(v.shape)[0] if torch.is_tensor(v) else None) for k, v in inner.items()}
                out["buffer_row_counts"] = nrows
                out["buffer_rows_consistent"] = len(set(nrows.values())) == 1
                nbytes = sum(v.numel() * v.element_size() for v in inner.values() if torch.is_tensor(v))
                out["buffer_bytes"] = nbytes
                out["buffer_MiB"] = round(nbytes / 2**20, 1)
                # finite check on a couple of float arrays
                bad = []
                for k, v in inner.items():
                    if torch.is_tensor(v) and v.is_floating_point():
                        if not torch.isfinite(v).all():
                            bad.append(k)
                out["buffer_nonfinite_float_arrays"] = bad
    # net state dict
    net_sd = ck.get("net")
    if net_sd is None:
        out["net"] = "<absent>"
    else:
        out["net_n_tensors"] = len(net_sd)
        out["net_n_params"] = int(sum(v.numel() for v in net_sd.values() if torch.is_tensor(v)))
        nonfinite = [k for k, v in net_sd.items() if torch.is_tensor(v) and v.is_floating_point() and not torch.isfinite(v).all()]
        out["net_nonfinite_tensors"] = nonfinite
        c = ck.get("cfg", {})
        try:
            with torch.random.fork_rng(devices=[]):
                net = build_net(NetConfig(blocks=c.get("blocks", 6), filters=c.get("filters", 64),
                                          n_planes=c.get("n_planes", 7), own_classes=c.get("own_classes", 3),
                                          mask_closed=c.get("mask_closed", 0), head_tying=c.get("head_tying", 0),
                                          gcnn=c.get("gcnn", 0)))
            net.load_state_dict(net_sd, strict=True)
            out["net_load_state_dict_strict"] = "OK"
            out["net_class"] = type(net).__name__
        except Exception as e:
            out["net_load_state_dict_strict"] = f"{type(e).__name__}: {e}"
    if "opt" in ck:
        o = ck["opt"]
        try:
            out["opt_param_groups"] = len(o["param_groups"])
            out["opt_lr"] = o["param_groups"][0].get("lr")
            out["opt_state_entries"] = len(o.get("state", {}))
        except Exception as e:
            out["opt"] = f"unreadable: {e}"
    if "scaler" in ck:
        out["scaler"] = ck["scaler"]
    if "rng" in ck:
        out["rng_keys"] = list(ck["rng"].keys())
    if "cfg" in ck:
        out["cfg_run"] = ck["cfg"].get("run")
        out["cfg_iters"] = ck["cfg"].get("iters")
    del ck
    return out

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(json.dumps(check(p), indent=2, default=str))
        print("---")
