"""The terminal rule as one explicit argument (PLAN7 §5 K1).

    "count"  a full macro grid with no macro line goes to the board count; equal counts draw.
             The CodinGame variant, and the rule every run up to deep8_c1_300_e8 was trained under.
    "draw"   a full macro grid with no macro line is a draw whatever the count.
             The Wikipedia / uttt.ai / SaltZero / OpenSpiel variant.

The rule is passed explicitly wherever the terminal value is decided — there is no global default to
flip. A checkpoint's *training* rule is recorded in its config.json; a tool's *evaluation* rule is
always an argument of that tool, and the two are never conflated (M0 finding 34).

This module imports nothing: uttt.game (numpy), uttt.solver (numpy + numba, whose pool workers stay
light) and uttt.batch (torch) all depend on it.
"""
from __future__ import annotations

import os

RULES = ("count", "draw")


def check_rule(rule: str) -> str:
    """Validate and return a rule name; a typo must not silently mean "count"."""
    if rule not in RULES:
        raise ValueError(f"rule must be one of {RULES}, got {rule!r}")
    return rule


def tag_path(path: str, rule: str) -> str:
    """Rule tag in the file name of any dataset or result a tool writes: runs/x.npz -> runs/x_draw.npz.

    "count" keeps the historical name, so every existing path and every pre-K1 file is untouched; a
    second rule therefore cannot silently overwrite or be mistaken for the first one's cache."""
    if check_rule(rule) == "count":
        return path
    stem, ext = os.path.splitext(path)
    return f"{stem}_{rule}{ext}"
