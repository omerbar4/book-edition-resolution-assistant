"""conservative-rules-v2: initials compatibility is supporting evidence only. Synthetic records."""

from __future__ import annotations

from pathlib import Path

import pytest

from bera.catalog import Catalog
from bera.features import check_fields
from bera.models import CheckStatus, Edition, Outcome, PhysicalFormat, Query, Reason
from bera.retrieval import Hit
from bera.service import Resolver
from bera.text import initials_compatible


@pytest.mark.parametrize(
    ("query", "catalog"),
    [
        ("S. Reynolds", "Sophia Reynolds"),
        ("Reynolds, S.", "Sophia Reynolds"),  # surname first
        ("S Reynolds", "Sophia Reynolds"),  # punctuation difference
        ("G. G. Márquez", "Gabriel García Márquez"),  # accents
        ("J.R.R. Tolkien", "John Ronald Reuel Tolkien"),  # run-together initials
        ("J.-P. Sartre", "Jean-Paul Sartre"),  # hyphenated given name
        ("U. K. Le Guin", "Ursula K. Le Guin"),  # initial on both sides
        ("Sophia Reynolds", "S. Reynolds"),  # initials on the catalog side
        ("S. Reynolds", "Sophia Anne Reynolds"),  # catalog has more given names
    ],
)
def test_initials_compatible_positive(query: str, catalog: str) -> None:
    assert initials_compatible(query, catalog)


@pytest.mark.parametrize(
    ("query", "catalog"),
    [
        ("J. Smith", "Mary Smith"),  # conflicting initial
        ("S. Reynolds", "Sophia Rogers"),  # conflicting surname
        ("S. A. Reynolds", "Sophia Reynolds"),  # supplied initial cannot be verified
        ("A. Reynolds", "Sophia Anne Reynolds"),  # initial must match the same position
        ("Reynolds", "Sophia Reynolds"),  # surname only: nothing to match
        ("Sophie Reynolds", "Sophia Reynolds"),  # full names: left to similarity
        ("S. Reynolds", ""),
        ("", "Sophia Reynolds"),
    ],
)
def test_initials_compatible_negative(query: str, catalog: str) -> None:
    assert not initials_compatible(query, catalog)


def ed(eid: str, **kw: object) -> Edition:
    base: dict[str, object] = {
        "edition_id": eid,
        "work_id": f"W-{eid}",
        "title": "Norway",
        "authors": ("Snorre Evensberget",),
        "physical_format": PhysicalFormat.PAPERBACK,
        "publish_year": 2003,
        "source": "test",
        "synthetic": True,
    }
    return Edition.model_validate(base | kw)


def author_status(query_author: str, edition: Edition) -> tuple[CheckStatus, str | None]:
    c = next(
        x for x in check_fields(Query(author=query_author), edition, None) if x.field == "author"
    )
    return c.status, c.detail


def test_check_upgrades_only_compatible_names() -> None:
    status, detail = author_status("S. Evensberget", ed("A"))
    assert status is CheckStatus.AGREE and detail and "supporting evidence only" in detail
    # a conflicting initial is never upgraded (it keeps its similarity status)
    status, _ = author_status("J. Smith", ed("A", authors=("Mary Smith",)))
    assert status is not CheckStatus.AGREE
    # a conflicting surname stays a conflict
    status, _ = author_status("S. Reynolds", ed("A", authors=("Sophia Rogers",)))
    assert status is CheckStatus.DISAGREE
    # missing author metadata stays unknown
    status, _ = author_status("S. Evensberget", ed("A", authors=()))
    assert status is CheckStatus.UNKNOWN


def build(tmp_path: Path, *editions: Edition) -> Catalog:
    cat = Catalog(tmp_path / "c.sqlite")
    cat.build(editions)
    return cat


Q = Query(title="Norway", author="S. Evensberget", publish_year=2003)


def test_initials_plus_distinguishing_field_can_suggest_a_unique_edition(tmp_path: Path) -> None:
    r = Resolver(build(tmp_path, ed("A")), None, None).resolve(Q)
    assert r.outcome is Outcome.SUGGEST and r.suggested_edition_id == "A"


def test_two_authors_sharing_surname_and_initial_stay_review(tmp_path: Path) -> None:
    cat = build(
        tmp_path,
        ed("A", authors=("Snorre Evensberget",)),
        ed("B", authors=("Sigrid Evensberget",)),
    )
    r = Resolver(cat, None, None).resolve(Q)
    assert r.outcome is Outcome.REVIEW
    assert Reason.MULTIPLE_CONSISTENT in r.reasons


def test_twin_with_missing_author_still_blocks(tmp_path: Path) -> None:
    r = Resolver(build(tmp_path, ed("A"), ed("B", authors=())), None, None).resolve(Q)
    assert r.outcome is Outcome.REVIEW
    assert Reason.UNDISTINGUISHED_ALTERNATIVE in r.reasons


class OnlyA:
    name = "only_a"

    def retrieve(self, query: Query, k: int) -> list[Hit]:
        return [Hit("A", self.name, 1, 1.0)]


def test_catalog_wide_scan_still_finds_an_unretrieved_compatible_edition(tmp_path: Path) -> None:
    cat = build(tmp_path, ed("A"), ed("B", authors=(), publish_year=None))
    r = Resolver(cat, None, None, retrievers=[OnlyA()]).resolve(Q)
    assert r.outcome is Outcome.REVIEW and Reason.CATALOG_ALTERNATIVE in r.reasons


def test_hard_rules_unchanged_suspicious_unicode_blocks(tmp_path: Path) -> None:
    q = Query(title="Nor" + chr(0x200B) + "way", author="S. Evensberget", publish_year=2003)
    r = Resolver(build(tmp_path, ed("A")), None, None).resolve(q)
    assert r.outcome is Outcome.REVIEW
