"""Validated LLM suggestion path: route gate semantics. Synthetic records and a mock provider
(a deterministic test double, not a model)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bera import isbn
from bera.catalog import Catalog
from bera.llm.mock import MockProvider
from bera.llm.routes import (
    MIN_ROUTE_CASES,
    ROUTE_PRECISION_TARGET,
    RouteGate,
    decide,
    gate_from_evidence,
    load_gate,
    measure,
)
from bera.models import Edition, Outcome, PhysicalFormat, Query, Reason
from bera.service import Resolver


def isbn_of(n: int) -> str:
    body = f"9780{n:08d}"
    return body + isbn.isbn13_check_digit(body)


def ed(eid: str, **kw: object) -> Edition:
    base: dict[str, object] = {
        "edition_id": eid,
        "work_id": "W",
        "title": "Dune",
        "authors": ("Frank Herbert",),
        "physical_format": PhysicalFormat.PAPERBACK,
        "publish_year": 2015,
        "source": "test",
        "synthetic": True,
    }
    return Edition.model_validate(base | kw)


Q = Query(title="Dune", author="Frank Herbert", physical_format="paperback", publish_year=2015)


def ambiguous(tmp_path: Path) -> Catalog:
    cat = Catalog(tmp_path / "c.sqlite")
    cat.build([ed("T-A", isbn_13=(isbn_of(1),)), ed("T-B", authors=(), isbn_13=(isbn_of(2),))])
    return cat


def test_decide_needs_both_minimum_cases_and_wilson_lower_bound() -> None:
    assert not decide(29, 29)["open"]  # below the minimum
    assert not decide(MIN_ROUTE_CASES, MIN_ROUTE_CASES)["open"]  # 30/30: lower bound < 0.95
    assert decide(80, 80)["open"]
    assert not decide(79, 80)["open"]


def test_measure_counts_a_choice_on_a_human_review_case_as_wrong() -> None:
    rows = [
        {"choice": "a", "top1": "a", "expected": "suggest", "gold": {"a"}},
        {"choice": "a", "top1": "a", "expected": "abstain", "gold": set()},
        {"choice": "b", "top1": "a", "expected": "suggest", "gold": {"a"}},
    ]
    ev = measure(rows)
    assert ev["routes"]["agree"]["n"] == 2 and ev["routes"]["agree"]["correct"] == 1
    assert ev["routes"]["override"] == ev["routes"]["override"] | {"n": 1, "correct": 0}
    assert ev["target_precision"] == ROUTE_PRECISION_TARGET


def test_gate_recomputes_from_counts_and_refuses_changed_constants(tmp_path: Path) -> None:
    forged = measure([])
    forged["routes"]["agree"].update({"n": 5, "correct": 5, "open": True})  # stored flag ignored
    assert gate_from_evidence(forged, "f").open_routes == frozenset()
    bad = measure([]) | {"target_precision": 0.5}
    with pytest.raises(ValueError):
        gate_from_evidence(bad, "f")
    assert load_gate(None).open_routes == frozenset()
    p = tmp_path / "e.json"
    p.write_text(json.dumps(measure([])))
    assert load_gate(p).open_routes == frozenset()


def test_closed_gate_keeps_llm_advisory(tmp_path: Path) -> None:
    r = Resolver(ambiguous(tmp_path), None, MockProvider()).resolve(Q)
    assert r.outcome is Outcome.REVIEW
    assert Reason.LLM_ADVISORY_ONLY in r.reasons and Reason.LLM_VALIDATED_ROUTE not in r.reasons


def test_open_route_turns_plain_ambiguity_into_a_suggestion(tmp_path: Path) -> None:
    gate = RouteGate(frozenset({"agree", "override"}), "test")
    r = Resolver(ambiguous(tmp_path), None, MockProvider(), route_gate=gate).resolve(Q)
    assert r.outcome is Outcome.SUGGEST
    assert r.suggested_edition_id == r.adjudication.chosen_edition_id
    assert Reason.LLM_VALIDATED_ROUTE in r.reasons


def test_route_not_open_stays_review(tmp_path: Path) -> None:
    cat = ambiguous(tmp_path)
    first = Resolver(cat, None, MockProvider()).resolve(Q)
    route = "agree" if first.adjudication.agrees_with_top1 else "override"
    other = {"agree": "override", "override": "agree"}[route]
    gate = RouteGate(frozenset({other}), "test")
    r = Resolver(cat, None, MockProvider(), route_gate=gate).resolve(Q)
    assert r.outcome is Outcome.REVIEW and Reason.LLM_ADVISORY_ONLY in r.reasons


def test_owner_rules_stay_review_even_on_an_open_route(tmp_path: Path) -> None:
    cat = Catalog(tmp_path / "d.sqlite")
    shared = isbn_of(7)
    cat.build([ed("D-1", isbn_13=(shared,)), ed("D-2", isbn_13=(shared,), publish_year=2016)])
    gate = RouteGate(frozenset({"agree", "override"}), "test")
    r = Resolver(cat, None, MockProvider(), route_gate=gate).resolve(Query(isbn=shared))
    assert Reason.DUPLICATE_ISBN in r.reasons
    assert r.outcome is Outcome.REVIEW and Reason.LLM_VALIDATED_ROUTE not in r.reasons
