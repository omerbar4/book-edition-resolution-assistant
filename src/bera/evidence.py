"""Typed-field evidence validation for adjudication output.

A citation is valid only if, after the field's documented normalizer, the cited value is
EQUAL to the candidate's scalar field or a MEMBER of its list field. No substring matching.

What this proves: the model quoted data that really is in the cited candidate record.
What it does NOT prove: that the model's inference (which edition the user holds) is right.
The decision policy therefore never relies on valid citations alone.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping

from bera import isbn as isbnlib
from bera.models import AdjudicationOutput, Edition, EvidenceField, EvidenceItem
from bera.text import detect_suspicious, norm_person, norm_text

ABSTAIN = "ABSTAIN"
_INT_RE = re.compile(r"^\d{1,5}$")


def _isbn13_of(value: str) -> str | None:
    p = isbnlib.parse(value)
    return p.isbn13 if p.valid else None


def _isbn10_of(value: str) -> str | None:
    p = isbnlib.parse(value)
    return p.compact if p.status is isbnlib.IsbnStatus.VALID_10 else None


Normalizer = Callable[[str], str | None]

# field -> (normalizer, accessor returning the candidate's values as a list)
_SPEC: dict[EvidenceField, tuple[Normalizer, Callable[[Edition], list[str]]]] = {
    EvidenceField.TITLE: (norm_text, lambda e: [e.title]),
    EvidenceField.SUBTITLE: (norm_text, lambda e: [e.subtitle] if e.subtitle else []),
    EvidenceField.EDITION_NAME: (norm_text, lambda e: [e.edition_name] if e.edition_name else []),
    EvidenceField.TRANSLATION_OF: (
        norm_text,
        lambda e: [e.translation_of] if e.translation_of else [],
    ),
    EvidenceField.AUTHORS: (norm_person, lambda e: list(e.authors)),
    EvidenceField.PUBLISHERS: (norm_text, lambda e: list(e.publishers)),
    EvidenceField.SERIES: (norm_text, lambda e: list(e.series)),
    EvidenceField.LANGUAGES: (lambda v: v.strip().lower(), lambda e: list(e.languages)),
    EvidenceField.ISBN_13: (_isbn13_of, lambda e: list(e.isbn_13)),
    EvidenceField.ISBN_10: (_isbn10_of, lambda e: list(e.isbn_10)),
    EvidenceField.PUBLISH_YEAR: (
        lambda v: str(int(v)) if _INT_RE.match(v.strip()) else None,
        lambda e: [str(e.publish_year)] if e.publish_year is not None else [],
    ),
    EvidenceField.NUMBER_OF_PAGES: (
        lambda v: str(int(v)) if _INT_RE.match(v.strip()) else None,
        lambda e: [str(e.number_of_pages)] if e.number_of_pages is not None else [],
    ),
    EvidenceField.PHYSICAL_FORMAT: (
        lambda v: v.strip().lower(),
        lambda e: [e.physical_format.value],
    ),
}


def validate_item(item: EvidenceItem, candidates: Mapping[str, Edition]) -> str | None:
    """Return an error string, or None if the citation is verified."""
    edition = candidates.get(item.candidate_id)
    if edition is None:
        return f"evidence cites unknown candidate_id {item.candidate_id!r}"
    normalize, accessor = _SPEC[item.field]
    cited = normalize(item.value)
    if not cited:
        return f"evidence value for {item.field.value} is empty or malformed after normalization"
    stored_raw = accessor(edition)
    stored = {n for n in (normalize(v) for v in stored_raw) if n}
    if cited not in stored:
        return (
            f"evidence {item.candidate_id}.{item.field.value}={item.value!r} "
            "does not equal any stored value"
        )
    # The cited field itself must not carry hidden/obfuscating characters.
    for raw in stored_raw:
        if normalize(raw) == cited and detect_suspicious(raw).suspicious:
            return (
                f"evidence cites {item.candidate_id}.{item.field.value}, "
                "which has suspicious Unicode"
            )
    return None


def validate_output(out: AdjudicationOutput, candidates: Mapping[str, Edition]) -> list[str]:
    errors: list[str] = []
    if out.choice != ABSTAIN and out.choice not in candidates:
        errors.append(f"choice {out.choice!r} is not an allowed candidate id or ABSTAIN")
    for item in out.evidence_fields:
        err = validate_item(item, candidates)
        if err:
            errors.append(err)
    if out.choice != ABSTAIN and out.choice in candidates:
        if not any(i.candidate_id == out.choice for i in out.evidence_fields):
            errors.append(
                "a non-abstain choice must cite at least one field of the chosen candidate"
            )
    if out.choice == ABSTAIN and not out.needs_human:
        errors.append("ABSTAIN requires needs_human=true")
    return errors
