"""CPU-only checks of symmetry handling in the saved opening books."""
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[3]  # moved to docs/history/review_astra by PLAN6
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from uttt.batch import SYM_CELL
from uttt.game import UTTT
from uttt.openings import canonical
from book import principal_line


def main():
    a = json.loads((ROOT / "runs/book_deep10.json").read_text())["nodes"]
    b = json.loads((ROOT / "runs/book_deep8.json").read_text())["nodes"]
    common = [k for k in a.keys() & b.keys() if a[k]["moves"] and b[k]["moves"]]
    exact, orbit = [], []
    for k in common:
        x, y = a[k]["moves"][0], b[k]["moves"][0]
        exact.append(x["move"] == y["move"])
        orbit.append(x["child"] == y["child"])
    result = {"common_nodes": len(common), "literal_agreement": sum(exact), "orbit_agreement": sum(orbit),
              "fraction_literal": sum(exact)/len(common), "fraction_orbit": sum(orbit)/len(common),
              "by_depth": {str(d): {"n": sum(a[k]["depth"] == d for k in common),
                                     "literal": sum(x for k, x in zip(common, exact) if a[k]["depth"] == d),
                                     "orbit": sum(x for k, x in zip(common, orbit) if a[k]["depth"] == d)} for d in range(1,5)}}
    for name, nodes in (("deep10", a), ("deep8", b)):
        duplicated = [k for k,n in nodes.items() if len({x["child"] for x in n["moves"]}) < len(n["moves"])]
        top2_same = [k for k,n in nodes.items() if n["depth"] == 1 and len(n["moves"]) > 1 and n["moves"][0]["child"] == n["moves"][1]["child"]]
        invalid = []
        for k,n in nodes.items():
            if n["depth"] != 1:
                continue
            line = n["seq"] + [x[0] for x in principal_line(nodes, k, 3)]
            g = UTTT()
            try:
                for move in line:
                    g.play(move)
            except ValueError as exc:
                invalid.append({"first": k, "line": line, "error": str(exc)})
        result[name] = {"nodes_with_duplicate_child_orbits": len(duplicated),
                        "first_move_nodes_with_top2_same_orbit": top2_same,
                        "illegal_displayed_principal_lines": invalid,
                        "after40": nodes["40"]["moves"]}
    # After [40] all D4 elements stabilize the state, and no remaining legal
    # move is fixed by all D4 elements: no deterministic equivariant action exists.
    g = UTTT()
    g.play(40)
    result["after40_fixed_legal_actions"] = [m for m in g.legal_moves() if all(int(p[m]) == m for p in SYM_CELL)]
    result["after40_legal_action_orbits"] = sorted({canonical([40, m]) for m in g.legal_moves()})
    atlas = json.loads((ROOT / "runs/plan5_A1_atlas.json").read_text())
    vals = atlas["values_replies"]["deep10_c1_300@16384"]
    i, distinct = 0, []
    for first in atlas["first_moves"]:
        replies = atlas["replies"][str(first)]
        v = vals[i:i+len(replies)]
        i += len(replies)
        order = sorted(range(len(v)), key=lambda j: v[j])  # O minimizes X's value.
        distinct.append({"first": first, "best_reply": replies[order[0]][1],
                         "gap_two_best_distinct_orbits": v[order[1]]-v[order[0]],
                         "all_reply_orbit_range": max(v)-min(v)})
    result["atlas_child_search_values_not_parent_Q"] = distinct
    (Path(__file__).resolve().parent / "book_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
