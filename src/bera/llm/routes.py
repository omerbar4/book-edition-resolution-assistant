"""Validated LLM suggestion path: route-level gating (DECISION_POLICY.md, item 7).

The model's own confidence is never used. A completed adjudication choice belongs to a route:
- "agree": the choice is the top-ranked candidate;
- "override": the choice is a different candidate.

A route may turn REVIEW into SUGGEST only if a frozen evidence file, measured on
DEVELOPMENT human labels, shows at least MIN_ROUTE_CASES cases on that route and a Wilson
95% lower bound on precision of at least ROUTE_PRECISION_TARGET. Precision counts every
completed choice on the route: a choice on a case the human sent to review is wrong. Both
constants were fixed before any route was measured. The open/closed decision is always
recomputed from the recorded counts; a stored "open" flag is never trusted.

Even on an open route the LLM can only resolve plain ambiguity among compatible candidates.
Owner rules and safety blocks stay REVIEW: duplicate ISBN mappings, ISBN repair hypotheses,
field conflicts, suspicious unicode and an incomplete catalog scan.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bera.evalkit.metrics import wilson
from bera.models import Reason

ROUTE_PRECISION_TARGET = 0.95
MIN_ROUTE_CASES = 30
ROUTES = ("agree", "override")
# Reasons the LLM may resolve on an open route; any other decision reason keeps REVIEW.
GATE_ELIGIBLE_REASONS = frozenset(
    {
        Reason.MULTIPLE_CONSISTENT,
        Reason.UNDISTINGUISHED_ALTERNATIVE,
        Reason.CATALOG_ALTERNATIVE,
    }
)


@dataclass(frozen=True)
class RouteGate:
    open_routes: frozenset[str]
    source: str = "none"

    @classmethod
    def closed(cls) -> RouteGate:
        return cls(frozenset(), "none")


CLOSED_GATE = RouteGate(frozenset(), "none")


def route_of(choice: str, top1: str | None) -> str:
    return "agree" if choice == top1 else "override"


def measure(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """rows: completed adjudications with keys choice, top1, expected, gold (set of ids)."""
    counts = {r: {"n": 0, "correct": 0} for r in ROUTES}
    for row in rows:
        route = route_of(row["choice"], row["top1"])
        counts[route]["n"] += 1
        if row["expected"] == "suggest" and row["choice"] in row["gold"]:
            counts[route]["correct"] += 1
    return {
        "target_precision": ROUTE_PRECISION_TARGET,
        "min_cases": MIN_ROUTE_CASES,
        "routes": {r: counts[r] | decide(counts[r]["correct"], counts[r]["n"]) for r in ROUTES},
    }


def decide(correct: int, n: int) -> dict[str, Any]:
    ci = wilson(correct, n)
    lower = None if ci is None else ci[0]
    reasons = []
    if n < MIN_ROUTE_CASES:
        reasons.append(f"n={n} < {MIN_ROUTE_CASES}")
    if lower is None or lower < ROUTE_PRECISION_TARGET:
        reasons.append(f"Wilson lower bound {lower} < target {ROUTE_PRECISION_TARGET}")
    return {"wilson95": ci, "open": not reasons, "closed_because": reasons}


def gate_from_evidence(evidence: Mapping[str, Any], source: str) -> RouteGate:
    """Recompute every route decision from its counts; refuse a changed target or minimum."""
    if (
        evidence.get("target_precision") != ROUTE_PRECISION_TARGET
        or evidence.get("min_cases") != MIN_ROUTE_CASES
    ):
        raise ValueError("route evidence was measured under different constants; refusing")
    open_routes = set()
    for r in ROUTES:
        c = evidence["routes"][r]
        if decide(int(c["correct"]), int(c["n"]))["open"]:
            open_routes.add(r)
    return RouteGate(frozenset(open_routes), source)


def load_gate(path: Path | None) -> RouteGate:
    if path is None:
        return RouteGate.closed()
    return gate_from_evidence(json.loads(path.read_text(encoding="utf-8")), path.name)
