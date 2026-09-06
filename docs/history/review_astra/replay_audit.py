"""CPU-only examination of the saved replay distribution, without modifying it."""
from pathlib import Path
import json
import torch

ROOT = Path(__file__).resolve().parents[3]  # moved to docs/history/review_astra by PLAN6


def main():
    torch.set_num_threads(4)
    ck = torch.load(ROOT / "runs/deep10_c1_300/latest_full.pt", map_location="cpu", weights_only=False)
    b, n = ck["buffer"]["buf"], ck["buffer"]["size"]
    _, inv, cnt = torch.unique(b["hash"], return_inverse=True, return_counts=True)
    w = cnt[inv].float().pow(-0.5) * torch.where(b["exact"] > 0, 2.0, 1.0)
    p = w / w.sum()
    result = {"checkpoint_keys": sorted(ck), "iteration": ck["iter"], "global_step": ck["global_step"],
              "rows": n, "distinct_hashes": cnt.numel(), "row_weight_ESS": (1 / p.square().sum()).item(),
              "expected_weighted_replay_age_iters": (p * (ck["iter"]-b["iter"].float())).sum().item(),
              "value_classes_sample_probability": {str(v): p[b["value"] == v].sum().item() for v in (-1, 0, 1)},
              "exact_sample_probability": p[b["exact"] > 0].sum().item(), "ply_buckets": []}
    for lo, hi in ((0, 7), (8, 19), (20, 31), (32, 43), (44, 81)):
        mask = (b["ply"] >= lo) & (b["ply"] <= hi)
        result["ply_buckets"].append({"plies": [lo, hi], "row_fraction": mask.float().mean().item(),
                                      "sample_fraction": p[mask].sum().item()})
    path = ROOT / "review_astra/replay_audit.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
