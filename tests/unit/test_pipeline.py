"""End-to-end pipeline checks on SYNTHETIC fixtures. Engineering checks, not evaluation."""

from __future__ import annotations

from typing import Any

from bera import isbn
from bera.llm.mock import MockProvider
from bera.models import AdjudicationStatus, Outcome, Reason, Route


def isbn_of(n: int, prefix: str = "978") -> str:
    body = f"{prefix}0{n:08d}"
    return body + isbn.isbn13_check_digit(body)


def ids(resp: Any) -> list[str]:
    return [c.edition.edition_id for c in resp.candidates]


def test_unique_isbn13_suggests(resolve: Any) -> None:
    r = resolve(isbn=isbn_of(1001))
    assert r.route is Route.ISBN_EXACT
    assert r.outcome is Outcome.SUGGEST and r.suggested_edition_id == "SYN-E0001"


def test_isbn10_form_maps_to_same_edition(resolve: Any) -> None:
    ten = isbn.isbn13_to_10(isbn_of(1001))
    r = resolve(isbn=ten)
    assert r.suggested_edition_id == "SYN-E0001"


def test_isbn_inside_free_text(resolve: Any) -> None:
    r = resolve(free_text=f"barcode torn, ISBN {isbn_of(1001)} on copyright page")
    assert r.route is Route.ISBN_EXACT and r.suggested_edition_id == "SYN-E0001"


def test_unique_isbn_with_conflicting_format_goes_to_review(resolve: Any) -> None:
    r = resolve(isbn=isbn_of(1001), physical_format="paperback")
    assert r.outcome is Outcome.REVIEW and Reason.FIELD_CONFLICT in r.reasons


def test_duplicate_isbn_never_auto_resolves(resolve: Any) -> None:
    r = resolve(isbn=isbn_of(1012))
    assert r.route is Route.ISBN_DUPLICATE and r.outcome is Outcome.REVIEW
    assert set(ids(r)) == {"SYN-E0012", "SYN-E0013", "SYN-E0014"}
    assert Reason.DUPLICATE_ISBN in r.reasons and Reason.LLM_DISABLED in r.reasons
    assert r.adjudication.status is AdjudicationStatus.DISABLED


def test_duplicate_isbn_with_mock_is_advisory_only(resolve: Any) -> None:
    r = resolve(provider=MockProvider(), isbn=isbn_of(1012), physical_format="hardcover")
    assert r.adjudication.status is AdjudicationStatus.COMPLETED
    assert r.outcome is Outcome.REVIEW and Reason.LLM_ADVISORY_ONLY in r.reasons
    # The hardcover record has no conflict, so it is ranked (and referenced) first.
    assert r.candidates[0].edition.edition_id == "SYN-E0013"


def test_bad_checksum_produces_repair_hypotheses_not_matches(resolve: Any) -> None:
    good = isbn_of(1002)
    damaged = good[:-2] + str((int(good[-2]) + 1) % 10) + good[-1]
    r = resolve(isbn=damaged)
    assert r.route is Route.ISBN_REPAIR and r.outcome is Outcome.REVIEW
    assert Reason.ISBN_BAD_CHECKSUM in r.reasons and "SYN-E0002" in ids(r)


def test_title_author_only_is_ambiguous(resolve: Any) -> None:
    r = resolve(title="The Lantern Keeper's Daughter", author="Mara Ellison")
    assert r.outcome is Outcome.REVIEW and Reason.MULTIPLE_CONSISTENT in r.reasons


def test_distinguishing_format_resolves(resolve: Any) -> None:
    r = resolve(
        title="The Lantern Keeper's Daughter", author="Mara Ellison", physical_format="hardcover"
    )
    assert r.outcome is Outcome.SUGGEST and r.suggested_edition_id == "SYN-E0001"


def test_typos_still_retrieve_the_work(resolve: Any) -> None:
    r = resolve(title="Lantren Keepers Daugter", author="Mara Elison", publish_year=2013)
    assert "SYN-E0003" in ids(r)[:3]


def test_study_guide_is_not_the_novel(resolve: Any) -> None:
    r = resolve(title="The Lantern Keeper's Daughter", author="Mara Ellison", publish_year=2015)
    guide = next(c for c in r.candidates if c.edition.edition_id == "SYN-E0006")
    assert any(ch.field == "content_kind" and ch.status.value == "disagree" for ch in guide.checks)
    assert r.suggested_edition_id != "SYN-E0006"


def test_study_guide_query_finds_guide(resolve: Any) -> None:
    r = resolve(
        title="Study Guide: The Lantern Keeper's Daughter",
        author="Brightpath Notes Editorial",
        physical_format="paperback",
    )
    assert r.suggested_edition_id == "SYN-E0006"


def test_box_set_not_suggested_for_single_volume(resolve: Any) -> None:
    r = resolve(title="The Lantern Keeper's Daughter", author="Mara Ellison", publish_year=2019)
    assert r.suggested_edition_id != "SYN-E0007"


def test_translation_by_original_title_and_language(resolve: Any) -> None:
    r = resolve(title="The Lantern Keeper's Daughter", author="Mara Ellison", language="Spanish")
    assert r.outcome is Outcome.SUGGEST and r.suggested_edition_id == "SYN-E0005"


def test_language_conflict_goes_to_review(resolve: Any) -> None:
    r = resolve(title="La hija del farero", author="Mara Ellison", language="English")
    assert r.outcome is Outcome.REVIEW
    spanish = next(c for c in r.candidates if c.edition.edition_id == "SYN-E0005")
    assert any(ch.field == "language" and ch.status.value == "disagree" for ch in spanish.checks)


def test_similar_title_different_author(resolve: Any) -> None:
    r = resolve(title="The Lantern Keeper", author="Tomas Reyes", physical_format="hardcover")
    assert r.suggested_edition_id == "SYN-E0008"
    r2 = resolve(title="The Lantern Keeper", author="Mara Ellison", physical_format="hardcover")
    assert r2.suggested_edition_id != "SYN-E0008"


def test_numbered_edition_with_author_variant(resolve: Any) -> None:
    r = resolve(title="Practical Data Structures", author="Natarajan, Priya", edition="2nd ed.")
    assert r.outcome is Outcome.SUGGEST and r.suggested_edition_id == "SYN-E0010"


def test_979_isbn(resolve: Any) -> None:
    r = resolve(isbn=isbn_of(1011, "979"))
    assert r.suggested_edition_id == "SYN-E0011"


def test_out_of_corpus_abstains(resolve: Any) -> None:
    r = resolve(title="Moonlight Over Glass", author="Zed Quill")
    assert r.outcome is Outcome.REVIEW and r.suggested_edition_id is None


def test_suspicious_query_unicode_forces_review(resolve: Any) -> None:
    r = resolve(
        title="The Lantern Keeper's Daughter\u200b",
        author="Mara Ellison",
        physical_format="hardcover",
    )
    assert r.outcome is Outcome.REVIEW and Reason.SUSPICIOUS_UNICODE in r.reasons
    assert "zero_width" in r.query_unicode_flags


def test_suspicious_record_is_never_suggested(resolve: Any) -> None:
    r = resolve(isbn=isbn_of(1018))
    assert r.outcome is Outcome.REVIEW and Reason.SUSPICIOUS_UNICODE in r.reasons
    assert set(r.candidates[0].unicode_flags) >= {"zero_width", "mixed_script"}


def test_catalog_invalid_isbn_is_never_exact(resolve: Any, catalog: Any) -> None:
    rec = catalog.get(["SYN-E0015"])["SYN-E0015"]
    r = resolve(isbn=rec.isbn_10[0])
    assert r.route is not Route.ISBN_EXACT and r.outcome is Outcome.REVIEW


def test_missing_metadata_is_unknown_not_conflict(resolve: Any) -> None:
    r = resolve(isbn=isbn_of(1019), author="Anyone")
    author = next(ch for ch in r.candidates[0].checks if ch.field == "author")
    assert author.status.value == "unknown"
    assert r.outcome is Outcome.SUGGEST  # unique ISBN, nothing contradicts it


def test_accent_insensitive_author(resolve: Any) -> None:
    r = resolve(title="Salt Roads", author="Ines Duarte Lobo", publish_year=2009)
    assert r.suggested_edition_id == "SYN-E0020"


def test_free_text_only_never_suggests(resolve: Any) -> None:
    r = resolve(free_text="lantern keeper daughter ellison hardcover")
    assert r.outcome is Outcome.REVIEW


def test_response_marks_pending_capabilities(resolve: Any) -> None:
    r = resolve(title="Salt Roads")
    assert r.capabilities.embedding_retrieval.startswith("pending")
    assert r.capabilities.reranker.startswith("pending")
    assert r.capabilities.calibration.startswith("pending")
    assert r.confidence_status.startswith("uncalibrated")
