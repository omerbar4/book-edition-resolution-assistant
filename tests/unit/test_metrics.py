from __future__ import annotations

from typing import Any

from bera.evalkit.metrics import CaseResult, category, compute, percentile, risk_coverage, wilson
from bera.evalkit.perturb import generate
from bera.evalkit.run import evaluate, markdown


def cr(
    cid: str,
    fam: str,
    expected: str,
    gold: set[str],
    ranked: list[str],
    outcome: str,
    suggested: str | None,
    signal: float | None = None,
) -> CaseResult:
    return CaseResult(
        cid,
        fam,
        expected,
        frozenset(gold),
        ranked,
        outcome,
        suggested,
        timings_ms={"total": float(len(cid))},
        signal=signal,
    )


RESULTS = [
    cr("a1", "f1", "suggest", {"e1"}, ["e1", "e2"], "suggest", "e1", 3),  # correct suggestion
    cr("a2", "f1", "suggest", {"e2"}, ["e1", "e2"], "suggest", "e1", 3),  # wrong (ranking)
    cr("a3", "f2", "suggest", {"e3"}, ["e3"], "review", None, 2),  # conservative abstention
    cr("a4", "f2", "suggest", {"e9"}, ["e3"], "review", None, 1),  # retrieval failure
    cr("u1", "f3", "abstain", set(), ["e5"], "review", None, 0),  # correct abstention
    cr("u2", "f3", "abstain", {"e5", "e6"}, ["e5"], "suggest", "e5", 2),  # unsupported
]


def test_denominators_are_explicit() -> None:
    m = compute(RESULTS, reps=50)
    assert m["counts"] == {
        "N": 6,
        "A_answerable": 4,
        "U_expected_abstain": 2,
        "S_suggested": 3,
        "families": 3,
    }
    assert m["correct_suggestion_rate"] == {"value": 0.1667, "numerator": 1, "denominator": 6}
    assert m["wrong_match_rate"] == {"value": 0.3333, "numerator": 2, "denominator": 6}
    assert m["error_among_suggestions"] == {"value": 0.6667, "numerator": 2, "denominator": 3}
    assert m["abstention_rate"]["numerator"] == 3
    assert m["correct_abstention_rate"] == {"value": 0.5, "numerator": 1, "denominator": 2}
    assert m["top1_accuracy"] == {"value": 0.5, "numerator": 2, "denominator": 4}
    assert m["retrieval"]["recall@1"]["numerator"] == 2
    assert m["retrieval"]["recall@5"]["numerator"] == 3
    assert m["mrr"]["value"] == round((1 + 0.5 + 1 + 0) / 4, 4)


def test_failure_categories() -> None:
    cats = [category(r) for r in RESULTS]
    assert cats == [
        "correct_suggestion",
        "wrong_suggestion_ranking",
        "conservative_abstention",
        "retrieval_failure",
        "correct_abstention",
        "unsupported_suggestion",
    ]


def test_wilson_and_percentile() -> None:
    assert wilson(0, 0) is None
    lo, hi = wilson(8, 10) or (0, 0)
    assert 0.44 < lo < 0.5 and 0.94 < hi < 0.98
    assert percentile([1, 2, 3, 4], 50) == 2 and percentile([1, 2, 3, 4], 95) == 4


def test_risk_coverage_monotone_coverage() -> None:
    pts = risk_coverage(RESULTS)
    covs = [p["coverage"] for p in pts]
    assert covs == sorted(covs) and covs[-1] == 1.0


def test_bootstrap_is_deterministic() -> None:
    a = compute(RESULTS, reps=200, seed=3)["bootstrap95_by_family"]
    b = compute(RESULTS, reps=200, seed=3)["bootstrap95_by_family"]
    assert a == b


def test_harness_runs_unblocked_systems_and_marks_blocked(catalog: Any) -> None:
    with catalog.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    cases = generate(list(catalog.get(ids).values()), seed=4, per_edition=1)
    report = evaluate(catalog, cases, reps=20)
    assert report["label"].startswith("ENGINEERING CHECK")
    systems = report["systems"]
    assert systems["1_exact_fuzzy"]["status"] == "ran"
    assert systems["2_lexical"]["status"] == "ran"
    for k in ("3_embedding", "4_hybrid", "5_hybrid_rerank", "6_routed_llm"):
        assert systems[k]["status"].startswith("blocked")
        assert "metrics" not in systems[k]
    md = markdown(report)
    assert "NOT A REAL-WORLD EVALUATION" in md and "blocked" in md
