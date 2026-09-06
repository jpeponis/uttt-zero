"""Opening book consistency (PLAN6 E1): replies are ranked by orbit, every edge carries the transform onto the child's
canonical frame, and principal lines assembled across nodes replay legally in one frame. Builds a small book on the
CPU with an exactly equivariant evaluator (symmetry-averaged random net) and audits it; then checks the audit itself
catches the two bugs REVIEW-astra §4 found (a frame-mixing line and a duplicated child orbit)."""
import copy
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from book import audit, build, principal_line  # noqa: E402
from uttt.model import Evaluator, NetConfig, ResNet  # noqa: E402
from uttt.openings import canonical, reply_orbits, transform_move  # noqa: E402
from uttt.symmetry import SymmetryAveragedEvaluator  # noqa: E402


def small_book(depth=3, top=2, sims=24):
    torch.manual_seed(0)
    device = torch.device("cpu")
    ev = SymmetryAveragedEvaluator(Evaluator(ResNet(NetConfig(blocks=2, filters=16)), device))
    return build(ev, depth, top, sims, device, batch=64, log=lambda *a: None)


def test_orbits_after_40():
    """After [40] every symmetry fixes the position: the 8 legal replies form two orbits (edges, corners), and their
    shares add up to the whole root."""
    legal = torch.zeros(81, dtype=torch.bool)
    legal[36:45] = True
    legal[40] = False
    share = torch.zeros(81)
    share[36:45] = torch.tensor([0.05, 0.2, 0.05, 0.2, 0.0, 0.2, 0.05, 0.2, 0.05])
    orbits = reply_orbits([40], legal.numpy(), share.numpy(), torch.zeros(81).numpy())
    assert [o["child"] for o in orbits] == ["40 37", "40 36"], orbits
    assert sorted(orbits[0]["members"]) == [37, 39, 41, 43] and sorted(orbits[1]["members"]) == [36, 38, 42, 44]
    assert abs(orbits[0]["share"] - 0.8) < 1e-6 and abs(orbits[1]["share"] - 0.2) < 1e-6
    for o in orbits:
        assert [transform_move(o["g"], m) for m in [40, o["move"]]] == [int(x) for x in o["child"].split()]
    print("orbits after [40] ok")


def test_book_is_consistent():
    nodes = small_book()
    chk = audit(nodes)
    assert chk["clean"], chk
    assert chk["lines"] == 15 and chk["nodes"] > 15
    n40 = nodes["40"]
    assert len(n40["moves"]) == 2 and {o["child"] for o in n40["moves"]} == {"40 37", "40 36"}
    assert abs(sum(o["share"] for o in n40["moves"]) - 1.0) < 1e-4  # the whole root, not three copies of one reply
    # a line printed in the first move's frame is legal AND lands on the stored nodes
    for k, n in nodes.items():
        if n["depth"] == 1:
            seq = list(n["seq"])
            for m, _, child in principal_line(nodes, k, 9, with_keys=True):
                seq.append(m)
                assert " ".join(map(str, canonical(seq))) == child
    print(f"book consistent: {chk['nodes']} nodes, {chk['lines']} lines")
    return nodes


def test_audit_catches_the_old_bugs(nodes):
    # frame mixing: the old book represented an orbit by its most-visited member and followed the canonical child,
    # whose moves are in another frame — emulate by naming a non-canonical member as the reply after [40]
    broken = copy.deepcopy(nodes)
    assert all(o["g"] == 0 for n in nodes.values() for o in n["moves"])  # canonical representatives: identity edges
    broken["40"]["moves"][0]["move"] = 41  # the review's illegal line [40, 41, 10, 16] came from exactly this
    chk = audit(broken)
    assert not chk["clean"] and chk["transform_mismatch"] and (chk["illegal_line"] or chk["frame_mismatch"]), chk
    # duplicate child orbits: list one orbit twice, as the old top-k over individual moves did
    broken = copy.deepcopy(nodes)
    broken["40"]["moves"] = [broken["40"]["moves"][0], dict(broken["40"]["moves"][0], move=39)]
    chk = audit(broken)
    assert chk["duplicate_child"] == ["40"], chk
    print("audit catches frame mixing and duplicated orbits")


if __name__ == "__main__":
    test_orbits_after_40()
    nodes = test_book_is_consistent()
    test_audit_catches_the_old_bugs(nodes)
    print("ok")
