from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from bera.evalkit.cases import EvalCase
from bera.evalkit.label import search, validate
from bera.evalkit.perturb import generate, make_case
from bera.evalkit.splits import assign, family_split, leakage


@pytest.fixture
def editions(catalog: Any) -> list[Any]:
    with catalog.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    return list(catalog.get(ids).values())


def test_generation_is_deterministic(editions: list[Any]) -> None:
    a = [c.model_dump_json() for c in generate(editions, seed=11)]
    b = [c.model_dump_json() for c in generate(editions, seed=11)]
    c = [c.model_dump_json() for c in generate(editions, seed=12)]
    assert a == b and a != c
    assert all(
        x.origin == "synthetic_perturbation" and not x.human_labeled
        for x in generate(editions, seed=11)
    )


def test_dropping_distinguishing_fields_becomes_abstain(editions: list[Any]) -> None:
    e1 = next(e for e in editions if e.edition_id == "SYN-E0001")
    case = make_case(e1, ["drop_isbn", "drop_format", "drop_year"], 1, editions, "W001", "x")
    assert case.expected == "abstain" and "underspecified" in (case.ambiguity_reason or "")
    assert {"SYN-E0001", "SYN-E0002", "SYN-E0003"} <= set(case.gold_edition_ids)


def test_typo_keeps_identifiable_case(editions: list[Any]) -> None:
    e1 = next(e for e in editions if e.edition_id == "SYN-E0001")
    case = make_case(e1, ["typo"], 3, editions, "W001", "x")
    assert case.expected == "suggest" and case.gold_edition_ids == ["SYN-E0001"]
    assert case.query.title != e1.title


def test_case_schema_rules() -> None:
    with pytest.raises(ValidationError):
        EvalCase(
            case_id="a",
            query={"title": "x"},
            expected="suggest",
            family="f",
            origin="human",
            labeler="ob",
        )  # no gold
    with pytest.raises(ValidationError):
        EvalCase(
            case_id="a",
            query={"title": "x"},
            expected="suggest",
            gold_edition_ids=["e"],
            family="f",
            origin="human",
        )  # no labeler
    ok = EvalCase(
        case_id="a",
        query={"title": "x"},
        expected="abstain",
        family="f",
        ambiguity_reason="out_of_corpus",
        origin="human",
        labeler="ob",
    )
    assert ok.human_labeled


def test_grouped_split_has_no_leakage(editions: list[Any]) -> None:
    cases = assign(generate(editions, seed=5, per_edition=3), seed=99)
    assert leakage(cases) == []
    assert {c.split for c in cases} == {"dev", "heldout"}
    assert family_split("W001", 99) == family_split("W001", 99)


def test_label_tools(catalog: Any, editions: list[Any]) -> None:
    rows = search(catalog, "lantern")
    titles = [r["title"] for r in rows]
    assert titles == sorted(titles) and "score" not in rows[0]
    report = validate(generate(editions, seed=1), catalog)
    assert report["ok"] and report["human_labeled"] == 0


def test_unknown_metadata_never_counts_as_distinguishing(editions: list[Any]) -> None:
    from bera.models import PhysicalFormat

    e1 = next(e for e in editions if e.edition_id == "SYN-E0001")
    twin = e1.model_copy(
        update={
            "edition_id": "SYN-TWIN",
            "isbn_10": [],
            "isbn_13": [],
            "physical_format": PhysicalFormat.UNKNOWN,
            "publish_year": None,
        }
    )
    case = make_case(e1, ["drop_isbn"], 1, [*editions, twin], "W001", "x")
    # The twin's format/year are unknown, so it cannot be ruled out: no forced unique gold.
    assert case.expected == "abstain" and "SYN-TWIN" in case.gold_edition_ids
    assert "only because a field is unknown" in (case.ambiguity_reason or "")


def _isbn_twin(e1: Any) -> Any:
    from bera.models import PhysicalFormat

    return e1.model_copy(
        update={
            "edition_id": "SYN-NOISBN",
            "isbn_10": [],
            "isbn_13": [],
            "physical_format": PhysicalFormat.UNKNOWN,
            "publish_year": None,
        }
    )


def test_spec_v2_unique_isbn_mapping_is_unique_gold(editions: list[Any]) -> None:
    e1 = next(e for e in editions if e.edition_id == "SYN-E0001")
    cat = [*editions, _isbn_twin(e1)]
    v1 = make_case(e1, [], 1, cat, "W001", "x", spec="v1")
    v2 = make_case(e1, [], 1, cat, "W001", "x", spec="v2")
    # v1 let a record with no ISBN "fit" an ISBN query; v2 treats its ISBN as unknown,
    # which does not establish that it carries the queried ISBN.
    assert v1.expected == "abstain" and "SYN-NOISBN" in v1.gold_edition_ids
    assert v2.expected == "suggest" and v2.gold_edition_ids == ["SYN-E0001"]


def test_spec_v2_without_isbn_still_widens_on_unknown(editions: list[Any]) -> None:
    e1 = next(e for e in editions if e.edition_id == "SYN-E0001")
    case = make_case(e1, ["drop_isbn"], 1, [*editions, _isbn_twin(e1)], "W001", "x", spec="v2")
    assert case.expected == "abstain" and "SYN-NOISBN" in case.gold_edition_ids


def test_spec_v2_multiple_explicit_mappings_abstain(editions: list[Any]) -> None:
    e1 = next(e for e in editions if e.edition_id == "SYN-E0001")
    dup = e1.model_copy(update={"edition_id": "SYN-DUP", "publish_year": 1901})
    case = make_case(e1, [], 1, [*editions, dup], "W001", "x", spec="v2")
    assert case.expected == "abstain"
    assert "multiple explicit ISBN mappings" in (case.ambiguity_reason or "")


def test_spec_v2_isbn_holder_conflict_abstains(editions: list[Any]) -> None:
    from bera.evalkit.perturb import label

    e1 = next(e for e in editions if e.edition_id == "SYN-E0001")
    judged = {"isbn": e1.isbn_13[0], "title": e1.title, "publish_year": 1800}
    exp, _, reason, ev = label(judged, e1, editions, "v2")
    assert exp == "abstain" and reason == "ISBN holder conflicts with supplied metadata"
    assert ev["explicit_isbn_mappings"] == ["SYN-E0001"]
