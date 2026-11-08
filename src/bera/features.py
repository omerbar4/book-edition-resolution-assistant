"""Deterministic field checks between an untrusted query and a catalog edition.

Every check returns AGREE / DISAGREE / UNKNOWN. UNKNOWN means missing (or too weak)
evidence on at least one side; it is never treated as a conflict. Thresholds are
engineering defaults documented in docs/DECISION_POLICY.md and are NOT calibrated.
"""

from __future__ import annotations

import re

from rapidfuzz import fuzz

from bera import isbn as isbnlib
from bera.models import CheckStatus, Edition, FieldCheck, PhysicalFormat, Query
from bera.text import initials_compatible, norm_person, norm_text, strip_accents

TITLE_AGREE = 90.0
TITLE_DISAGREE = 60.0
AUTHOR_AGREE = 85.0
AUTHOR_DISAGREE = 60.0
PUBLISHER_AGREE = 85.0
PUBLISHER_DISAGREE = 60.0
VAGUE_LANGUAGE_CODES = frozenset({"mul", "und"})  # MARC: multiple / undetermined
YEAR_NEAR = 2  # |diff| in 1..YEAR_NEAR -> UNKNOWN ("near", reprints); > YEAR_NEAR -> DISAGREE

_FORMAT_SYNONYMS: dict[str, PhysicalFormat] = {
    "hardcover": PhysicalFormat.HARDCOVER,
    "hardback": PhysicalFormat.HARDCOVER,
    "hard cover": PhysicalFormat.HARDCOVER,
    "hc": PhysicalFormat.HARDCOVER,
    "cloth": PhysicalFormat.HARDCOVER,
    "paperback": PhysicalFormat.PAPERBACK,
    "softcover": PhysicalFormat.PAPERBACK,
    "soft cover": PhysicalFormat.PAPERBACK,
    "trade paperback": PhysicalFormat.PAPERBACK,
    "pb": PhysicalFormat.PAPERBACK,
    "mass market paperback": PhysicalFormat.MASS_MARKET_PAPERBACK,
    "mass market": PhysicalFormat.MASS_MARKET_PAPERBACK,
    "library binding": PhysicalFormat.LIBRARY_BINDING,
    "board book": PhysicalFormat.BOARD_BOOK,
    "ebook": PhysicalFormat.EBOOK,
    "e book": PhysicalFormat.EBOOK,
    "kindle": PhysicalFormat.EBOOK,
    "audiobook": PhysicalFormat.AUDIOBOOK,
    "audio cd": PhysicalFormat.AUDIOBOOK,
    "audio": PhysicalFormat.AUDIOBOOK,
}

# Formats in one family do not contradict each other (e.g. "paperback" vs mass-market).
_FORMAT_FAMILY: dict[PhysicalFormat, str] = {
    PhysicalFormat.HARDCOVER: "hard",
    PhysicalFormat.LIBRARY_BINDING: "hard",
    PhysicalFormat.PAPERBACK: "soft",
    PhysicalFormat.MASS_MARKET_PAPERBACK: "soft",
    PhysicalFormat.BOARD_BOOK: "board",
    PhysicalFormat.EBOOK: "ebook",
    PhysicalFormat.AUDIOBOOK: "audio",
    PhysicalFormat.OTHER: "other",
}

_LANGUAGE_CODES: dict[str, str] = {
    "english": "eng",
    "en": "eng",
    "eng": "eng",
    "spanish": "spa",
    "espanol": "spa",
    "es": "spa",
    "spa": "spa",
    "french": "fre",
    "francais": "fre",
    "fr": "fre",
    "fre": "fre",
    "fra": "fre",
    "german": "ger",
    "deutsch": "ger",
    "de": "ger",
    "ger": "ger",
    "deu": "ger",
    "italian": "ita",
    "it": "ita",
    "ita": "ita",
    "portuguese": "por",
    "pt": "por",
    "por": "por",
    "japanese": "jpn",
    "ja": "jpn",
    "jpn": "jpn",
    "chinese": "chi",
    "zh": "chi",
    "chi": "chi",
    "zho": "chi",
}

_ORDINAL_WORDS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
}
# "10th anniversary edition" is not the 10th edition, so anniversaries are excluded.
_ORDINAL_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b(?! anniversary)")
_STUDY_GUIDE_RE = re.compile(
    r"\b(study guide|sparknotes|cliffsnotes|cliffs notes|summary of|workbook for|"
    r"companion to|reader s guide|readers guide)\b"
)
_BOX_SET_RE = re.compile(r"\b(box set|boxed set|boxset|books \d+ ?\d*|collection set|omnibus)\b")


def parse_format(text: str | None) -> PhysicalFormat:
    key = norm_text(text)
    if not key:
        return PhysicalFormat.UNKNOWN
    if key in _FORMAT_SYNONYMS:
        return _FORMAT_SYNONYMS[key]
    for syn in sorted(_FORMAT_SYNONYMS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(syn)}\b", key):
            return _FORMAT_SYNONYMS[syn]
    return PhysicalFormat.UNKNOWN


def parse_language(text: str | None) -> str | None:
    key = strip_accents(norm_text(text))
    return _LANGUAGE_CODES.get(key) if key else None


def edition_ordinal(text: str | None) -> int | None:
    t = norm_text(text)
    if not t:
        return None
    m = _ORDINAL_RE.search(t)
    if m:
        return int(m.group(1))
    for word, n in _ORDINAL_WORDS.items():
        if re.search(rf"\b{word}\b", t):
            return n
    return None


def content_kind(text: str | None) -> str:
    t = norm_text(text)
    if _STUDY_GUIDE_RE.search(t):
        return "study_guide"
    if _BOX_SET_RE.search(t):
        return "box_set"
    return "standard"


def title_similarity(query_title: str, edition: Edition) -> float:
    q = norm_text(query_title)
    if not q:
        return 0.0
    full = norm_text(f"{edition.title} {edition.subtitle or ''}")
    main = norm_text(edition.title)
    return max(fuzz.ratio(q, main), fuzz.token_sort_ratio(q, main), fuzz.ratio(q, full))


def author_similarity(query_author: str, edition: Edition) -> float:
    q = norm_person(query_author)
    if not q or not edition.authors:
        return 0.0
    return max(fuzz.token_sort_ratio(q, norm_person(a)) for a in edition.authors)


def _band(score: float, agree: float, disagree: float) -> CheckStatus:
    if score >= agree:
        return CheckStatus.AGREE
    if score < disagree:
        return CheckStatus.DISAGREE
    return CheckStatus.UNKNOWN


def check_fields(query: Query, edition: Edition, query_isbn13: str | None) -> list[FieldCheck]:
    checks: list[FieldCheck] = []

    if query_isbn13 is not None:
        cand13 = {
            p.isbn13 for p in map(isbnlib.parse, edition.isbn_13 + edition.isbn_10) if p.valid
        }
        if not cand13:
            status = CheckStatus.UNKNOWN
        else:
            status = CheckStatus.AGREE if query_isbn13 in cand13 else CheckStatus.DISAGREE
        checks.append(
            FieldCheck(
                field="isbn",
                status=status,
                query_value=query_isbn13,
                candidate_value=", ".join(sorted(c for c in cand13 if c)) or None,
            )
        )

    if query.title:
        sim = title_similarity(query.title, edition)
        title_detail = f"similarity={sim:.0f}"
        # A translation may be described by its original title; record that explicitly.
        if edition.translation_of:
            q = norm_text(query.title)
            orig = fuzz.ratio(q, norm_text(edition.translation_of))
            if orig > sim:
                sim, title_detail = orig, f"similarity={orig:.0f} via translation_of"
        checks.append(
            FieldCheck(
                field="title",
                status=_band(sim, TITLE_AGREE, TITLE_DISAGREE),
                query_value=query.title,
                candidate_value=edition.title,
                detail=title_detail,
            )
        )

    if query.author:
        if not edition.authors:
            checks.append(
                FieldCheck(
                    field="author",
                    status=CheckStatus.UNKNOWN,
                    query_value=query.author,
                    candidate_value=None,
                    detail="catalog record has no author",
                )
            )
        else:
            sim = author_similarity(query.author, edition)
            status = _band(sim, AUTHOR_AGREE, AUTHOR_DISAGREE)
            author_detail = f"similarity={sim:.0f}"
            # conservative-rules-v2: an initials-compatible name (same surname, every supplied
            # initial matching) is supporting AGREE evidence. It never proves identity or
            # uniqueness: catalog-wide ambiguity checks and hard rules still apply. A
            # non-compatible name keeps the similarity status above (never upgraded).
            if status is not CheckStatus.AGREE and any(
                initials_compatible(query.author, a) for a in edition.authors
            ):
                status = CheckStatus.AGREE
                author_detail = (
                    f"initials-compatible (supporting evidence only); similarity={sim:.0f}"
                )
            checks.append(
                FieldCheck(
                    field="author",
                    status=status,
                    query_value=query.author,
                    candidate_value="; ".join(edition.authors),
                    detail=author_detail,
                )
            )

    if query.physical_format:
        qf = parse_format(query.physical_format)
        cf = edition.physical_format
        if qf is PhysicalFormat.UNKNOWN or cf is PhysicalFormat.UNKNOWN:
            status = CheckStatus.UNKNOWN
        else:
            same = _FORMAT_FAMILY.get(qf) == _FORMAT_FAMILY.get(cf)
            status = CheckStatus.AGREE if same else CheckStatus.DISAGREE
        checks.append(
            FieldCheck(
                field="physical_format",
                status=status,
                query_value=query.physical_format,
                candidate_value=cf.value,
            )
        )

    if query.publish_year is not None:
        detail: str | None
        if edition.publish_year is None:
            status, detail = CheckStatus.UNKNOWN, "catalog year missing"
        else:
            diff = abs(query.publish_year - edition.publish_year)
            if diff == 0:
                status, detail = CheckStatus.AGREE, None
            elif diff <= YEAR_NEAR:
                status, detail = CheckStatus.UNKNOWN, f"near (diff={diff})"
            else:
                status, detail = CheckStatus.DISAGREE, f"diff={diff}"
        checks.append(
            FieldCheck(
                field="publish_year",
                status=status,
                query_value=str(query.publish_year),
                candidate_value=None if edition.publish_year is None else str(edition.publish_year),
                detail=detail,
            )
        )

    if query.publisher:
        if not edition.publishers:
            status = CheckStatus.UNKNOWN
        else:
            q = norm_text(query.publisher)
            sim = max(fuzz.token_set_ratio(q, norm_text(p)) for p in edition.publishers)
            status = _band(sim, PUBLISHER_AGREE, PUBLISHER_DISAGREE)
        checks.append(
            FieldCheck(
                field="publisher",
                status=status,
                query_value=query.publisher,
                candidate_value="; ".join(edition.publishers) or None,
            )
        )

    if query.language:
        code = parse_language(query.language)
        langs = set(edition.languages)
        if code is None or code in VAGUE_LANGUAGE_CODES or not langs:
            status = CheckStatus.UNKNOWN
        elif code in langs:
            status = CheckStatus.AGREE
        elif langs & VAGUE_LANGUAGE_CODES:
            # 'mul' / 'und' are kept as distinct values; neither proves a specific language
            # nor rules one out.
            status = CheckStatus.UNKNOWN
        else:
            status = CheckStatus.DISAGREE
        checks.append(
            FieldCheck(
                field="language",
                status=status,
                query_value=query.language,
                candidate_value=", ".join(edition.languages) or None,
            )
        )

    q_ord = edition_ordinal(query.edition)
    if query.edition:
        c_ord = edition_ordinal(edition.edition_name)
        if q_ord is None or c_ord is None:
            status = CheckStatus.UNKNOWN
        else:
            status = CheckStatus.AGREE if q_ord == c_ord else CheckStatus.DISAGREE
        checks.append(
            FieldCheck(
                field="edition",
                status=status,
                query_value=query.edition,
                candidate_value=edition.edition_name,
            )
        )

    # Content kind: a study guide or box set is a different product from the book itself.
    # Only judged when the query actually describes the book in words.
    q_desc = " ".join(filter(None, [query.title, query.free_text, query.edition]))
    q_kind = content_kind(q_desc)
    c_kind = content_kind(f"{edition.title} {edition.subtitle or ''} {edition.edition_name or ''}")
    if q_desc and (q_kind != "standard" or c_kind != "standard"):
        checks.append(
            FieldCheck(
                field="content_kind",
                status=CheckStatus.AGREE if q_kind == c_kind else CheckStatus.DISAGREE,
                query_value=q_kind,
                candidate_value=c_kind,
            )
        )

    return checks
