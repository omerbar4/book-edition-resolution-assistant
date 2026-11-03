"""Offline regression: exact outcome categories on the committed synthetic case file.

This is a change detector for pipeline behavior on SYNTHETIC fixtures, not a quality claim.
If an intentional change moves these numbers, update them in the same commit and say why.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bera.evalkit.cases import load_cases
from bera.evalkit.run import evaluate

CASES = Path(__file__).resolve().parents[2] / "data" / "eval" / "synthetic_fixture_cases.jsonl"
EXPECTED = {
    "conservative_abstention": 21,
    "correct_abstention": 2,
    "correct_suggestion": 66,
    "ranking_failure": 1,
}


def test_synthetic_regression(catalog: Any) -> None:
    report = evaluate(catalog, load_cases(CASES), reps=10)
    for key in ("1_exact_fuzzy", "2_lexical", "2b_lexical_rrf"):
        m = report["systems"][key]["metrics"]
        assert m["categories"] == EXPECTED, key
        assert m["wrong_match_rate"]["numerator"] == 0, key
