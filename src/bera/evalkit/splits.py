"""Grouped dev/held-out split: every case of a family lands in the same split.

Assignment is a pure function of (seed, family) via SHA-256, so adding cases never moves an
existing family between splits.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable

from bera.evalkit.cases import EvalCase


def family_split(family: str, seed: int, dev_fraction: float = 0.6) -> str:
    h = hashlib.sha256(f"{seed}:{family}".encode()).digest()
    u = int.from_bytes(h[:8], "big") / 2**64
    return "dev" if u < dev_fraction else "heldout"


def assign(cases: Iterable[EvalCase], seed: int, dev_fraction: float = 0.6) -> list[EvalCase]:
    return [
        c.model_copy(update={"split": family_split(c.family, seed, dev_fraction)}) for c in cases
    ]


def leakage(cases: Iterable[EvalCase]) -> list[str]:
    """Families that appear in both splits (must be empty)."""
    seen: dict[str, set[str]] = {}
    for c in cases:
        if c.split:
            seen.setdefault(c.family, set()).add(c.split)
    return sorted(f for f, s in seen.items() if len(s) > 1)


def summary(cases: Iterable[EvalCase]) -> dict[str, dict[str, int]]:
    out: dict[str, Counter[str]] = {}
    for c in cases:
        key = c.split or "unassigned"
        out.setdefault(key, Counter())
        out[key][f"origin:{c.origin}"] += 1
        out[key][f"expected:{c.expected}"] += 1
    return {k: dict(sorted(v.items())) for k, v in sorted(out.items())}
