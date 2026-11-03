"""Selection-quality components: diversity-preserving edition sampling, conservative work
families, author-identity ambiguity flags, and per-probe absence audits.

None of these use retrieval or model outputs; they depend only on dump metadata.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from rapidfuzz import fuzz

DIMENSIONS = ("format", "language", "decade", "publisher", "edition_statement")


@dataclass(frozen=True)
class EdFeat:
    key: str
    format: str | None
    language: str | None
    year: int | None
    publisher: str | None
    edition_statement: str | None

    def value(self, dim: str) -> str | None:
        if dim == "decade":
            return None if self.year is None else f"{self.year // 10 * 10}s"
        v = getattr(self, dim)
        return v or None


def _h(seed: int, key: str) -> str:
    return hashlib.sha256(f"{seed}:{key}".encode()).hexdigest()


@dataclass
class SampleReport:
    available: int
    kept: int
    distinct_available: dict[str, int]
    distinct_kept: dict[str, int]
    missing_rate_kept: dict[str, float]
    unmet_dimensions: list[str]


def sample_editions(eds: Sequence[EdFeat], cap: int, seed: int) -> tuple[list[str], SampleReport]:
    """Deterministic, seeded, diversity-preserving sample of at most `cap` editions.

    Greedy max-coverage: each step takes the edition that adds the most not-yet-covered
    values across format, language, decade, publisher and edition statement (missing values
    add nothing); ties go to a seeded SHA-256 order. If everything fits, all are kept.
    """
    order = sorted(eds, key=lambda e: _h(seed, e.key))
    if len(order) <= cap:
        chosen = order
    else:
        covered: dict[str, set[str]] = {d: set() for d in DIMENSIONS}
        remaining = list(order)
        chosen = []
        while remaining and len(chosen) < cap:
            best_i, best_gain = 0, -1
            for i, e in enumerate(remaining):
                gain = sum(
                    1 for d in DIMENSIONS if (v := e.value(d)) is not None and v not in covered[d]
                )
                if gain > best_gain:
                    best_i, best_gain = i, gain
                    if gain == len(DIMENSIONS):
                        break
            e = remaining.pop(best_i)
            chosen.append(e)
            for d in DIMENSIONS:
                if (v := e.value(d)) is not None:
                    covered[d].add(v)

    def distinct(xs: Iterable[EdFeat]) -> dict[str, int]:
        return {d: len({v for e in xs if (v := e.value(d)) is not None}) for d in DIMENSIONS}

    da, dk = distinct(eds), distinct(chosen)
    missing = {
        d: round(sum(e.value(d) is None for e in chosen) / len(chosen), 3) if chosen else 0.0
        for d in DIMENSIONS
    }
    report = SampleReport(
        len(eds), len(chosen), da, dk, missing, [d for d in DIMENSIONS if dk[d] < da[d]]
    )
    return sorted(e.key for e in chosen), report


# ---- families ------------------------------------------------------------------------------
@dataclass
class WorkInfo:
    work: str
    titles: set[str]  # folded edition titles
    translation_of: set[str]  # folded
    author_keys: set[str]
    guide_target: str | None = None  # folded title a study guide refers to
    alias_group: str | None = None


class _UF:
    def __init__(self, items: Iterable[str]) -> None:
        self.p = {x: x for x in items}

    def find(self, x: str) -> str:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            lo, hi = sorted((ra, rb))
            self.p[hi] = lo


@dataclass
class FamilyResult:
    family_of: dict[str, str]
    edge_counts: dict[str, int] = field(default_factory=dict)

    def sizes(self) -> Counter[str]:
        return Counter(self.family_of.values())


def build_families(works: Sequence[WorkInfo]) -> FamilyResult:
    """Conservative grouping for split assignment. Two works share a family if ANY holds:
    F1 shared (provisional) author key; F2 any shared folded edition title;
    F3 one's translation_of matches the other's title; F4 study guide target;
    F5 explicit seed alias group (e.g. 1984 / Nineteen Eighty-Four).
    Over-merging is accepted: it only reduces the number of independent families."""
    uf = _UF(w.work for w in works)
    edges: Counter[str] = Counter()

    def link(index: Mapping[str, list[str]], tag: str) -> None:
        for members in index.values():
            for other in members[1:]:
                if uf.find(members[0]) != uf.find(other):
                    edges[tag] += 1
                uf.union(members[0], other)

    by_author: dict[str, list[str]] = {}
    by_title: dict[str, list[str]] = {}
    by_alias: dict[str, list[str]] = {}
    for w in sorted(works, key=lambda w: w.work):
        for k in w.author_keys:
            by_author.setdefault(k, []).append(w.work)
        for t in w.titles:
            if t:
                by_title.setdefault(t, []).append(w.work)
        if w.alias_group:
            by_alias.setdefault(w.alias_group, []).append(w.work)
    link(by_author, "F1_author_key")
    link(by_title, "F2_title")
    for w in works:
        for t in (*w.translation_of, *([w.guide_target] if w.guide_target else [])):
            for other in by_title.get(t, []):
                tag = "F3_translation" if t in w.translation_of else "F4_guide"
                if uf.find(w.work) != uf.find(other):
                    edges[tag] += 1
                uf.union(w.work, other)
    link(by_alias, "F5_alias")
    fam = {w.work: "fam:" + uf.find(w.work).rsplit("/", 1)[-1] for w in works}
    return FamilyResult(fam, dict(edges))


# ---- author identity ambiguity ------------------------------------------------------------
@dataclass
class AuthorRecord:
    key: str
    name: str | None
    birth_date: str | None


def _birth_year(s: str | None) -> str | None:
    if not s:
        return None
    digits = [
        t for t in s.replace(",", " ").replace("-", " ").split() if t.isdigit() and len(t) == 4
    ]
    return digits[0] if digits else None


def author_ambiguity(
    records: Sequence[AuthorRecord], editions_by_key: Mapping[str, int]
) -> dict[str, Any]:
    """Exact-name matches are PROVISIONAL identity candidates. Flags, never conclusions."""
    years = {r.key: _birth_year(r.birth_date) for r in records}
    distinct_years = {y for y in years.values() if y}
    credited = [r.key for r in records if editions_by_key.get(r.key, 0) > 0]
    flags = []
    if len(records) > 1:
        flags.append("multiple_records_same_name")
    if len(distinct_years) > 1:
        flags.append("different_birth_years_likely_different_people")
    if len(credited) > 1:
        flags.append("several_candidate_records_credited_in_matched_works")
    if records and not distinct_years:
        flags.append("no_birth_year_on_any_record")
    return {
        "status": "provisional_identity_candidates",
        "candidates": [
            {
                "key": r.key,
                "name": r.name,
                "birth_date": r.birth_date,
                "editions_credited_in_scope": editions_by_key.get(r.key, 0),
            }
            for r in records
        ],
        "flags": flags,
    }


# ---- probe absence audit ------------------------------------------------------------------
@dataclass(frozen=True)
class AuditEdition:
    edition_id: str
    ftitle: str
    fsubtitle: str
    ftrans: str
    author_names: frozenset[str]  # accent-folded normalized names
    by_statement: str


def probe_audit(
    probe_ftitle: str,
    probe_author: str,
    probe_surname: str,
    author_keys_found: int,
    editions: Iterable[AuditEdition],
    threshold: float = 85.0,
) -> dict[str, object]:
    """Absence cannot be proven from incomplete metadata. A probe is `verified_absent` only
    if its author resolved to >= 1 record AND no edition resembles it by title (partial
    ratio >= threshold on title/subtitle/translation_of), author name, or by_statement
    surname. Otherwise it is `quarantined` and must not receive an abstention label."""
    hits = []
    for e in editions:
        reasons = []
        for label, text in (
            ("title", e.ftitle),
            ("subtitle", e.fsubtitle),
            ("translation_of", e.ftrans),
        ):
            if text and len(text) >= 4 and fuzz.partial_ratio(probe_ftitle, text) >= threshold:
                reasons.append(label)
        if probe_author and probe_author in e.author_names:
            reasons.append("author_name")
        if probe_surname and probe_surname in e.by_statement:
            reasons.append("by_statement_surname")
        if reasons:
            hits.append({"edition_id": e.edition_id, "reasons": reasons})
    reasons_q = []
    if author_keys_found == 0:
        reasons_q.append("author_not_resolved_in_authors_dump")
    if hits:
        reasons_q.append(f"{len(hits)}_resembling_editions")
    return {
        "status": "quarantined" if reasons_q else "verified_absent",
        "reasons": reasons_q,
        "hits": hits[:50],
    }
