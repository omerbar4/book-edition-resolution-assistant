"""Pydantic schemas: catalog records, queries, the LLM contract, and API responses."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# ---- limits (docs/THREAT_MODEL.md) -------------------------------------------------------
MAX_FIELD_CHARS = 2000
MAX_QUERY_CHARS = 8000
MAX_CANDIDATES_RETURNED = 10
MAX_ADJUDICATION_CANDIDATES = 5
MAX_EVIDENCE_ITEMS = 8
MAX_EVIDENCE_VALUE_CHARS = 200
MAX_REASON_CHARS = 400

QueryText = Annotated[str, StringConstraints(max_length=MAX_FIELD_CHARS)]


class PhysicalFormat(StrEnum):
    HARDCOVER = "hardcover"
    PAPERBACK = "paperback"
    MASS_MARKET_PAPERBACK = "mass_market_paperback"
    LIBRARY_BINDING = "library_binding"
    BOARD_BOOK = "board_book"
    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"
    OTHER = "other"
    UNKNOWN = "unknown"


class Edition(BaseModel):
    """One catalog edition. Missing metadata is an explicit None / empty list, never imputed."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    edition_id: str
    work_id: str | None = None
    title: str
    subtitle: str | None = None
    authors: tuple[str, ...] = ()
    publishers: tuple[str, ...] = ()
    publish_date_raw: str | None = None
    publish_year: int | None = None
    physical_format: PhysicalFormat = PhysicalFormat.UNKNOWN
    physical_format_raw: str | None = None
    edition_name: str | None = None
    languages: tuple[str, ...] = ()  # MARC-style codes, e.g. "eng", "spa"
    isbn_10: tuple[str, ...] = ()
    isbn_13: tuple[str, ...] = ()
    number_of_pages: int | None = None
    series: tuple[str, ...] = ()
    translation_of: str | None = None
    source: str  # e.g. "synthetic-fixture-v1" or "openlibrary-dump-2026-10-31"
    synthetic: bool
    # Where derived values came from, e.g. {"authors": "edition_keys", "publish_year":
    # "year_only"}. Missing values are never imputed; this records how each was obtained.
    field_provenance: dict[str, str] = Field(default_factory=dict)


class Query(BaseModel):
    """Untrusted user input. Every field optional; at least one must be non-empty."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    isbn: QueryText | None = None
    title: QueryText | None = None
    author: QueryText | None = None
    physical_format: QueryText | None = None
    publish_year: int | None = Field(default=None, ge=0, le=2100)
    publisher: QueryText | None = None
    language: QueryText | None = None
    edition: QueryText | None = None
    free_text: QueryText | None = None

    @model_validator(mode="after")
    def _non_empty_and_bounded(self) -> Query:
        texts = [v for v in self.text_fields().values() if v]
        if not texts and self.publish_year is None:
            raise ValueError("query must contain at least one field")
        if self.publish_year is not None and not texts:
            raise ValueError("a year alone is not enough to search")
        if sum(len(t) for t in texts) > MAX_QUERY_CHARS:
            raise ValueError(f"query exceeds {MAX_QUERY_CHARS} characters")
        return self

    def text_fields(self) -> dict[str, str | None]:
        return {
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "physical_format": self.physical_format,
            "publisher": self.publisher,
            "language": self.language,
            "edition": self.edition,
            "free_text": self.free_text,
        }


# ---- deterministic checks ----------------------------------------------------------------
class CheckStatus(StrEnum):
    AGREE = "agree"
    DISAGREE = "disagree"
    UNKNOWN = "unknown"  # missing on either side: no evidence, NOT a conflict


class FieldCheck(BaseModel):
    field: str
    status: CheckStatus
    query_value: str | None
    candidate_value: str | None
    detail: str | None = None


class Outcome(StrEnum):
    SUGGEST = "suggest"
    REVIEW = "review"


class Route(StrEnum):
    ISBN_EXACT = "isbn_exact"
    ISBN_DUPLICATE = "isbn_duplicate"
    ISBN_REPAIR = "isbn_repair"
    RETRIEVAL = "retrieval"


class Reason(StrEnum):
    UNIQUE_ISBN_NO_CONFLICT = "unique_isbn_no_conflict"
    UNIQUE_CONSISTENT_MATCH = "unique_consistent_match"
    DUPLICATE_ISBN = "duplicate_isbn_mapping"
    ISBN_BAD_CHECKSUM = "isbn_bad_checksum"
    ISBN_BAD_FORMAT = "isbn_bad_format"
    ISBN_NOT_IN_CATALOG = "isbn_not_in_catalog"
    ISBN_REPAIR_HYPOTHESIS = "isbn_repair_hypothesis_only"
    FIELD_CONFLICT = "field_conflict"
    NO_CANDIDATES = "no_candidates"
    LIKELY_NOT_IN_CORPUS = "likely_not_in_corpus"
    MULTIPLE_CONSISTENT = "multiple_consistent_candidates"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    SUSPICIOUS_UNICODE = "suspicious_unicode"
    LLM_DISABLED = "llm_disabled"
    LLM_ABSTAINED = "llm_abstained"
    LLM_ADVISORY_ONLY = "llm_advisory_only_pending_route_measurement"
    LLM_OUTPUT_INVALID = "llm_output_invalid"
    EVIDENCE_INVALID = "evidence_invalid"
    LLM_PROVIDER_ERROR = "llm_provider_error"
    LLM_DEADLINE = "llm_deadline_exceeded"
    LLM_BUDGET = "llm_budget_exceeded"


class CandidateView(BaseModel):
    rank: int
    candidate_ref: str | None = None  # opaque c1..c5 id when sent to adjudication
    edition: Edition
    retrieval_sources: list[str]
    lexical_score: float  # UNCALIBRATED ranking score; not a probability
    checks: list[FieldCheck]
    conflicts: int
    agreements: int
    unicode_flags: list[str]


# ---- LLM contract -------------------------------------------------------------------------
class EvidenceField(StrEnum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    AUTHORS = "authors"
    PUBLISHERS = "publishers"
    PUBLISH_YEAR = "publish_year"
    PHYSICAL_FORMAT = "physical_format"
    EDITION_NAME = "edition_name"
    LANGUAGES = "languages"
    ISBN_10 = "isbn_10"
    ISBN_13 = "isbn_13"
    NUMBER_OF_PAGES = "number_of_pages"
    SERIES = "series"
    TRANSLATION_OF = "translation_of"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_id: Annotated[str, StringConstraints(max_length=8)]
    field: EvidenceField
    value: Annotated[str, StringConstraints(max_length=MAX_EVIDENCE_VALUE_CHARS)]


class AdjudicationOutput(BaseModel):
    """The ONLY shape accepted from a model. Anything else is rejected, never repaired."""

    model_config = ConfigDict(extra="forbid", strict=True)

    choice: Annotated[str, StringConstraints(max_length=8)]  # "c1".."c5" or "ABSTAIN"
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]  # logged only; never a threshold
    decision_reason: Annotated[str, StringConstraints(max_length=MAX_REASON_CHARS)]
    evidence_fields: Annotated[list[EvidenceItem], Field(max_length=MAX_EVIDENCE_ITEMS)]
    needs_human: bool


class AdjudicationStatus(StrEnum):
    NOT_NEEDED = "not_needed"
    DISABLED = "disabled"
    COMPLETED = "completed"
    INVALID_OUTPUT = "invalid_output"
    EVIDENCE_INVALID = "evidence_invalid"
    PROVIDER_ERROR = "provider_error"
    DEADLINE = "deadline_exceeded"
    BUDGET = "budget_exceeded"


class AdjudicationView(BaseModel):
    status: AdjudicationStatus
    provider: str
    attempts: int = 0
    output: AdjudicationOutput | None = None
    chosen_edition_id: str | None = None
    agrees_with_top1: bool | None = None
    validation_errors: list[str] = []
    input_tokens: int | None = None
    output_tokens: int | None = None


class Capabilities(BaseModel):
    lexical_retrieval: Literal["active"] = "active"
    embedding_retrieval: str
    reranker: str
    llm: str
    calibration: str


class ResolveResponse(BaseModel):
    request_id: str
    outcome: Outcome
    suggested_edition_id: str | None
    route: Route
    reasons: list[Reason]
    candidates: list[CandidateView]
    adjudication: AdjudicationView
    query_unicode_flags: list[str]
    confidence_status: str
    capabilities: Capabilities
    policy_version: str
    timings_ms: dict[str, float]
    disclaimer: str = (
        "Decision support only. A suggestion is not a confirmed match; "
        "nothing is listed, priced, or changed."
    )


class FeedbackDecision(StrEnum):
    CONFIRM = "confirm"
    REJECT = "reject"


class FeedbackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]
    edition_id: Annotated[str, StringConstraints(max_length=64)] | None = None
    decision: FeedbackDecision
