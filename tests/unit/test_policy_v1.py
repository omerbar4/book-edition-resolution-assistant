"""Regression tests for conservative-rules-v1 (development fixes found by the dev engineering
check on synthetic cases). Synthetic test records only; no real catalog data."""

from __future__ import annotations

from pathlib import Path

import pytest

from bera import isbn
from bera.catalog import Catalog
from bera.features import check_fields
from bera.models import CheckStatus, Edition, Outcome, PhysicalFormat, Query, Reason, Route
from bera.retrieval import Hit
from bera.service import Resolver


def isbn_of(n: int) -> str:
    body = f"9780{n:08d}"
    return body + isbn.isbn13_check_digit(body)


def ed(eid: str, **kw: object) -> Edition:
    base: dict[str, object] = {
        "edition_id": eid,
        "work_id": "W-DUNE",
        "title": "Dune",
        "authors": ("Frank Herbert",),
        "physical_format": PhysicalFormat.PAPERBACK,
        "publish_year": 2015,
        "source": "test",
        "synthetic": True,
    }
    return Edition.model_validate(base | kw)


A = ed("T-A", isbn_13=(isbn_of(1),))


def build(tmp_path: Path, *editions: Edition) -> Catalog:
    cat = Catalog(tmp_path / "c.sqlite")
    cat.build(editions)
    return cat


class OnlyA:
    """A retriever that omits everything except T-A (simulates a retrieval miss)."""

    name = "only_a"

    def retrieve(self, query: Query, k: int) -> list[Hit]:
        return [Hit("T-A", self.name, 1, 1.0)]


Q = Query(title="Dune", author="Frank Herbert", physical_format="paperback", publish_year=2015)


def test_unknown_author_alternative_blocks_suggestion(tmp_path: Path) -> None:
    twin = ed("T-B", authors=(), isbn_13=(isbn_of(2),))
    r = Resolver(build(tmp_path, A, twin), None, None).resolve(Q)
    assert r.outcome is Outcome.REVIEW
    assert Reason.UNDISTINGUISHED_ALTERNATIVE in r.reasons
    assert {"T-A", "T-B"} <= {c.edition.edition_id for c in r.candidates}


def test_contradicted_alternative_does_not_block(tmp_path: Path) -> None:
    other = ed("T-B", authors=("Someone Else Entirely",), isbn_13=(isbn_of(2),))
    r = Resolver(build(tmp_path, A, other), None, None).resolve(Q)
    assert r.outcome is Outcome.SUGGEST and r.suggested_edition_id == "T-A"


def test_unretrieved_compatible_edition_found_by_catalog_scan(tmp_path: Path) -> None:
    twin = ed("T-B", authors=(), publish_year=None)
    r = Resolver(build(tmp_path, A, twin), None, None, retrievers=[OnlyA()]).resolve(Q)
    assert r.outcome is Outcome.REVIEW and Reason.CATALOG_ALTERNATIVE in r.reasons
    scanned = [c for c in r.candidates if c.edition.edition_id == "T-B"]
    assert scanned and scanned[0].retrieval_sources == ["catalog_ambiguity_scan"]
    assert Reason.UNIQUE_CONSISTENT_MATCH not in r.reasons


def test_catalog_scan_includes_same_work_under_another_title(tmp_path: Path) -> None:
    twin = ed("T-B", title="Der Wüstenplanet", translation_of="Dune", authors=())
    r = Resolver(build(tmp_path, A, twin), None, None, retrievers=[OnlyA()]).resolve(Q)
    assert r.outcome is Outcome.REVIEW and Reason.CATALOG_ALTERNATIVE in r.reasons


def test_catalog_scan_ignores_contradicted_editions(tmp_path: Path) -> None:
    other = ed("T-B", publish_year=1965)
    r = Resolver(build(tmp_path, A, other), None, None, retrievers=[OnlyA()]).resolve(Q)
    assert r.outcome is Outcome.SUGGEST and r.suggested_edition_id == "T-A"


def test_incomplete_catalog_scan_goes_to_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cat = build(tmp_path, A)
    monkeypatch.setattr(cat, "ambiguity_pool", lambda title, work_id: (["T-A"], False))
    r = Resolver(cat, None, None, retrievers=[OnlyA()]).resolve(Q)
    assert r.outcome is Outcome.REVIEW and Reason.CATALOG_SCAN_INCOMPLETE in r.reasons


def test_unique_isbn_not_invalidated_by_record_without_isbn(tmp_path: Path) -> None:
    twin = ed("T-B", authors=(), physical_format=PhysicalFormat.UNKNOWN, publish_year=None)
    r = Resolver(build(tmp_path, A, twin), None, None).resolve(Query(isbn=isbn_of(1)))
    assert r.route is Route.ISBN_EXACT
    assert r.outcome is Outcome.SUGGEST and r.suggested_edition_id == "T-A"


def test_unique_isbn_with_conflicting_supplied_field_goes_to_review(tmp_path: Path) -> None:
    r = Resolver(build(tmp_path, A), None, None).resolve(Query(isbn=isbn_of(1), publish_year=1965))
    assert r.outcome is Outcome.REVIEW and Reason.FIELD_CONFLICT in r.reasons


@pytest.mark.parametrize(
    ("langs", "status"),
    [
        (("mul",), CheckStatus.UNKNOWN),
        (("und",), CheckStatus.UNKNOWN),
        (("fre", "mul"), CheckStatus.UNKNOWN),
        (("eng", "mul"), CheckStatus.AGREE),
        (("fre",), CheckStatus.DISAGREE),
        ((), CheckStatus.UNKNOWN),
    ],
)
def test_mul_und_are_neither_equivalence_nor_conflict(
    langs: tuple[str, ...], status: CheckStatus
) -> None:
    checks = check_fields(Query(title="Dune", language="English"), ed("T", languages=langs), None)
    assert next(c for c in checks if c.field == "language").status is status
