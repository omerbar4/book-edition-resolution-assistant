"""Shared metric helpers for development analyses (human labels only).

Every rate carries its numerator and denominator, a case-level Wilson interval and a
family-grouped bootstrap interval (all queries of a family resampled together, 1000 reps,
seed 0). These are development statistics, never held-out estimates.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from typing import Any

from bera.evalkit.metrics import wilson

REPS = 1000

Row = dict[str, Any]


def ratio(rows: Sequence[Row], num: Callable[[Row], bool], den: Callable[[Row], bool]) -> Row:
    d = [r for r in rows if den(r)]
    k = sum(1 for r in d if num(r))
    n = len(d)
    return {
        "numerator": k,
        "denominator": n,
        "value": None if n == 0 else round(k / n, 4),
        "wilson95_case_level": wilson(k, n),
        "bootstrap95_family_grouped": grouped_bootstrap(rows, num, den),
    }


def grouped_bootstrap(
    rows: Sequence[Row], num: Callable[[Row], bool], den: Callable[[Row], bool]
) -> list[float] | None:
    fams: dict[str, list[Row]] = {}
    for r in rows:
        fams.setdefault(r["family"], []).append(r)
    keys = sorted(fams)
    rng = random.Random(0)  # noqa: S311 - reproducible resampling
    vals = []
    for _ in range(REPS):
        sample = [r for k in (rng.choice(keys) for _ in keys) for r in fams[k]]
        d = [r for r in sample if den(r)]
        if d:
            vals.append(sum(1 for r in d if num(r)) / len(d))
    if not vals:
        return None
    vals.sort()
    return [
        round(vals[int(0.025 * (len(vals) - 1))], 4),
        round(vals[int(0.975 * (len(vals) - 1))], 4),
    ]


def metrics(rows: Sequence[Row]) -> Row:
    def answerable(r: Row) -> bool:
        return bool(r["expected"] == "suggest")

    def correct(r: Row) -> bool:
        return r["outcome"] == "suggest" and r["suggested"] in r["gold"]

    def wrong(r: Row) -> bool:
        return r["outcome"] == "suggest" and r["suggested"] not in r["gold"]

    def everything(r: Row) -> bool:
        return True

    return {
        "n_cases": len(rows),
        "n_families": len({r["family"] for r in rows}),
        "correct_suggestion_rate /N": ratio(rows, correct, everything),
        "wrong_match_rate /N": ratio(rows, wrong, everything),
        "error_among_suggestions /S": ratio(rows, wrong, lambda r: r["outcome"] == "suggest"),
        "suggestion_coverage_on_answerable /A": ratio(rows, correct, answerable),
        "top1_accuracy /A": ratio(rows, lambda r: r["top1"] in r["gold"], answerable),
        "correct_abstention /U": ratio(
            rows, lambda r: r["outcome"] == "review", lambda r: r["expected"] == "abstain"
        ),
    }


def cause(reasons: list[str]) -> str:
    rs = set(reasons)
    if rs & {"undistinguished_alternative_unknown_fields", "multiple_consistent_candidates"}:
        return "undistinguished alternatives among retrieved candidates"
    if "catalog_scan_found_undistinguished_alternative" in rs:
        return "undistinguished alternative found by the catalog-wide scan"
    if "catalog_scan_incomplete" in rs:
        return "catalog scan incomplete"
    if rs & {"isbn_repair_hypothesis_only", "isbn_bad_checksum", "isbn_bad_format"}:
        return "damaged ISBN: repair is only a hypothesis"
    if "duplicate_isbn_mapping" in rs:
        return "ISBN maps to several records"
    if "field_conflict" in rs:
        return "a supplied field conflicts with the top candidate"
    if "insufficient_evidence" in rs:
        return "insufficient distinguishing evidence"
    return "other: " + ",".join(sorted(rs))
