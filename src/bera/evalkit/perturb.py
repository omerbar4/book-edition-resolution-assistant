"""Seeded, controlled query perturbations derived from catalog editions.

Each case records its ops, seed and source edition. The expected behavior is computed
deterministically AFTER perturbation by a versioned label spec (docs/SYNTHETIC_LABEL_SPEC.md):

- v1: if the surviving structured fields (compared exactly, after normalization) fit more than
  one edition, the case is `abstain` ("underspecified"). A record with NO ISBN still fits an
  ISBN query (missing = unknown).
- v2 (default): as v1, except a checksum-valid query ISBN with exactly ONE explicit catalog
  mapping, and no conflict between that record and the other supplied fields, makes that
  record the unique gold. A record whose ISBN is missing is unknown, which does not establish
  that it carries the queried ISBN, so it does not fit. Several explicit mappings -> abstain.

For abstain cases `gold_edition_ids` lists the editions consistent with the query; it is NOT
an acceptable set (no duplicate-record equivalence is ever inferred from missing fields).
- v3: as v2, except in the field-fit branch the source edition counts only if it fits the
  query as written (a deliberately changed year or format is a claim, not noise), the single
  fitting record is the gold even when it is not the source, and no fitting record means
  catalog absence (abstain, no gold), never "contradictory". v3 equals v2 whenever the source
  fits its own query, which holds for every template that does not change a claim.

These are synthetic cases; they never count as human-labeled.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence

from bera import isbn as isbnlib
from bera.evalkit.cases import EvalCase, Perturbation
from bera.models import Edition, PhysicalFormat, Query
from bera.text import norm_person, norm_text

Op = Callable[[dict[str, object], Edition, random.Random], None]


def _typo(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
    t = str(fields.get("title") or "")
    if len(t) < 4:
        return
    i = rng.randrange(1, len(t) - 1)
    kind = rng.choice(["swap", "drop", "dup"])
    if kind == "swap":
        t = t[:i] + t[i + 1] + t[i] + t[i + 2 :]
    elif kind == "drop":
        t = t[:i] + t[i + 1 :]
    else:
        t = t[:i] + t[i] + t[i:]
    fields["title"] = t


def _author_last_first(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
    a = str(fields.get("author") or "")
    parts = a.split()
    if len(parts) >= 2 and "," not in a:
        fields["author"] = f"{parts[-1]}, {' '.join(parts[:-1])}"


def _author_initials(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
    parts = str(fields.get("author") or "").split()
    if len(parts) >= 2:
        fields["author"] = " ".join([p[0] + "." for p in parts[:-1]] + [parts[-1]])


def _drop(name: str) -> Op:
    def op(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
        fields.pop(name, None)

    op.__name__ = f"drop_{name}"
    return op


def _isbn10_form(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
    p = isbnlib.parse(str(fields.get("isbn") or ""))
    if p.valid and p.isbn10:
        fields["isbn"] = f"{p.isbn10[:1]}-{p.isbn10[1:5]}-{p.isbn10[5:9]}-{p.isbn10[9]}"


def _isbn_digit_error(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
    raw = str(fields.get("isbn") or "")
    if len(raw) == 13 and raw.isdigit():
        i = rng.randrange(3, 12)
        fields["isbn"] = raw[:i] + str((int(raw[i]) + rng.randrange(1, 10)) % 10) + raw[i + 1 :]


def _lowercase_no_punct(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
    if fields.get("title"):
        fields["title"] = norm_text(str(fields["title"]))


def _strip_to_title_author(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
    """Keep only title and author; the conflict ops then add exactly one changed claim."""
    for k in [k for k in fields if k not in ("title", "author")]:
        fields.pop(k)


YEAR_SHIFTS = (-5, -4, -3, 3, 4, 5)  # never within the runtime +-2 "near" band
YEAR_RANGE = (1450, 2026)  # inclusive; a shift outside it is skipped (no-op), never altered
SWAP_FORMATS = tuple(
    f.value for f in PhysicalFormat if f not in (PhysicalFormat.OTHER, PhysicalFormat.UNKNOWN)
)


def _year_shift(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
    """Claim a publication year 3-5 years away from the source's known year."""
    if e.publish_year is None:
        return
    y = e.publish_year + rng.choice(YEAR_SHIFTS)
    if YEAR_RANGE[0] <= y <= YEAR_RANGE[1]:
        fields["publish_year"] = y


def _format_swap(fields: dict[str, object], e: Edition, rng: random.Random) -> None:
    """Claim a physical format different from the source's known format, drawn uniformly
    (seeded) from the other known formats. Never chosen by looking at sibling editions."""
    if e.physical_format in (PhysicalFormat.OTHER, PhysicalFormat.UNKNOWN):
        return
    others = [f for f in SWAP_FORMATS if f != e.physical_format.value]
    fields["physical_format"] = rng.choice(others).replace("_", " ")


OPS: dict[str, Op] = {
    "strip_to_title_author": _strip_to_title_author,
    "year_shift": _year_shift,
    "format_swap": _format_swap,
    "typo": _typo,
    "author_last_first": _author_last_first,
    "author_initials": _author_initials,
    "drop_isbn": _drop("isbn"),
    "drop_format": _drop("physical_format"),
    "drop_year": _drop("publish_year"),
    "drop_author": _drop("author"),
    "isbn10_form": _isbn10_form,
    "isbn_digit_error": _isbn_digit_error,
    "lowercase_no_punct": _lowercase_no_punct,
}


def clean_fields(e: Edition) -> dict[str, object]:
    f: dict[str, object] = {"title": e.title}
    if e.authors:
        f["author"] = e.authors[0]
    if e.isbn_13:
        f["isbn"] = e.isbn_13[0]
    if e.physical_format not in (PhysicalFormat.UNKNOWN, PhysicalFormat.OTHER):
        f["physical_format"] = e.physical_format.value.replace("_", " ")
    if e.publish_year is not None:
        f["publish_year"] = e.publish_year
    return f


def _fit(fields: dict[str, object], e: Edition) -> str | None:
    """Does edition `e` agree with every provided structured field?

    Returns None if any provided field contradicts a KNOWN value of `e`, "unknown" if `e`
    could match only because some provided field is missing on `e` (unknown is never treated
    as a mismatch), else "exact". Missing metadata therefore widens the set of editions that
    fit; it is never used as distinguishing evidence."""
    unknown = False
    isbn_raw = fields.get("isbn")
    if isbn_raw:
        p = isbnlib.parse(str(isbn_raw))
        if not p.valid:
            return None  # a damaged ISBN identifies nothing exactly
        mine = {isbnlib.parse(x).isbn13 for x in (*e.isbn_10, *e.isbn_13)} - {None}
        if not mine:
            unknown = True
        elif p.isbn13 not in mine:
            return None
    if fields.get("title") and norm_text(str(fields["title"])) != norm_text(e.title):
        return None
    if fields.get("author"):
        if not e.authors:
            unknown = True
        elif norm_person(str(fields["author"])) not in {norm_person(a) for a in e.authors}:
            return None
    fmt = fields.get("physical_format")
    if fmt:
        if e.physical_format in (PhysicalFormat.UNKNOWN, PhysicalFormat.OTHER):
            unknown = True
        elif str(fmt).replace(" ", "_") != e.physical_format.value:
            return None
    if fields.get("publish_year") is not None:
        if e.publish_year is None:
            unknown = True
        elif fields["publish_year"] != e.publish_year:
            return None
    return "unknown" if unknown else "exact"


LABEL_SPECS = ("v1", "v2", "v3")
DEFAULT_LABEL_SPEC = "v2"


def isbn13s(e: Edition) -> set[str]:
    return {p for x in (*e.isbn_10, *e.isbn_13) if (p := isbnlib.parse(x).isbn13)}


def label(
    judged: dict[str, object], source: Edition, catalog: Sequence[Edition], spec: str
) -> tuple[str, list[str], str | None, dict[str, object]]:
    """(expected, gold_edition_ids, ambiguity_reason, evidence) under label spec `spec`."""
    if spec not in LABEL_SPECS:
        raise ValueError(f"unknown label spec {spec!r}")
    evidence: dict[str, object] = {"spec": spec}
    q = isbnlib.parse(str(judged["isbn"])) if judged.get("isbn") else None
    if spec in ("v2", "v3") and q is not None and q.valid and q.isbn13:
        holders = sorted(x.edition_id for x in catalog if q.isbn13 in isbn13s(x))
        rest = {k: v for k, v in judged.items() if k != "isbn"}
        by_id = {x.edition_id: x for x in catalog}
        fitting = [h for h in holders if _fit(rest, by_id[h]) is not None]
        no_isbn_fit = sorted(
            x.edition_id
            for x in catalog
            if not isbn13s(x) and x.edition_id not in holders and _fit(rest, x) is not None
        )
        evidence |= {
            "query_isbn13": q.isbn13,
            "explicit_isbn_mappings": holders,
            "mappings_consistent_with_other_fields": fitting,
            "records_without_isbn_not_counted": no_isbn_fit,
        }
        if len(holders) == 1 and fitting:
            evidence["rule"] = "unique explicit ISBN mapping, no conflict with supplied fields"
            return "suggest", fitting, None, evidence
        if len(holders) > 1:
            evidence["rule"] = "multiple explicit ISBN mappings -> review"
            return (
                "abstain",
                fitting or holders,
                f"multiple explicit ISBN mappings: {len(holders)} records carry this ISBN",
                evidence,
            )
        if len(holders) == 1:
            evidence["rule"] = "ISBN holder conflicts with a supplied field -> review"
            return "abstain", holders, "ISBN holder conflicts with supplied metadata", evidence
        evidence["rule"] = "ISBN not in catalog; judged on the other fields"
    kinds = {x.edition_id: k for x in catalog if (k := _fit(judged, x)) is not None}
    if spec in ("v1", "v2"):
        kinds.setdefault(source.edition_id, "exact")
    fits = sorted(kinds)
    via_unknown = sum(1 for k in kinds.values() if k == "unknown")
    evidence.setdefault("rule", "field fit; unknown is compatible, never distinguishing")
    evidence["fitting"] = fits
    evidence["fitting_only_via_unknown"] = sorted(i for i, k in kinds.items() if k == "unknown")
    if spec == "v3":
        # v3: the source counts only if it fits the query AS WRITTEN (a deliberately changed
        # year/format is a claim, not noise), and the one fitting record is the gold even
        # when it is not the source. No fitting record is catalog absence, not contradiction.
        if not fits:
            evidence["rule"] = "no catalog record fits the supplied fields"
            return (
                "abstain",
                [],
                "catalog absence: no catalog record fits the supplied fields "
                "(not evidence that the supplied fields contradict each other)",
                evidence,
            )
        if len(fits) == 1:
            return "suggest", fits, None, evidence
    elif len(fits) == 1:
        return "suggest", [source.edition_id], None, evidence
    reason = f"underspecified: {len(fits)} editions fit" + (
        f" ({via_unknown} only because a field is unknown on them)" if via_unknown else ""
    )
    return "abstain", fits, reason, evidence


def _fits(fields: dict[str, object], e: Edition) -> bool:
    return _fit(fields, e) is not None


def perturbed_fields(e: Edition, ops: Sequence[str], seed: int) -> dict[str, object]:
    rng = random.Random(seed)  # noqa: S311 - reproducible perturbation, not security
    fields = clean_fields(e)
    for name in ops:
        OPS[name](fields, e, rng)
    return fields


def judged_fields(fields: dict[str, object], e: Edition) -> dict[str, object]:
    """The clean information that survived perturbation (typos are noise, so the source
    title/author stand in for perturbed ones when judging identifiability)."""
    judged = dict(fields)
    if "title" in judged:
        judged["title"] = e.title
    if "author" in judged and e.authors:
        judged["author"] = e.authors[0]
    if "isbn" in judged and not isbnlib.parse(str(judged["isbn"])).valid:
        judged.pop("isbn")
    return judged


def make_case(
    e: Edition,
    ops: Sequence[str],
    seed: int,
    catalog: Sequence[Edition],
    family: str,
    case_id: str,
    spec: str = DEFAULT_LABEL_SPEC,
) -> EvalCase:
    fields = perturbed_fields(e, ops, seed)
    expected, gold, reason, _ = label(judged_fields(fields, e), e, catalog, spec)
    return EvalCase(
        case_id=case_id,
        query=Query.model_validate(fields),
        expected=expected,  # type: ignore[arg-type]
        gold_edition_ids=gold,
        ambiguity_reason=reason,
        family=family,
        origin="synthetic_perturbation",
        perturbation=Perturbation(ops=list(ops), seed=seed, source_edition_id=e.edition_id),
    )


def generate(
    catalog: Sequence[Edition],
    seed: int,
    per_edition: int = 2,
    family_of: Callable[[Edition], str] | None = None,
    sources: Sequence[Edition] | None = None,
    spec: str = DEFAULT_LABEL_SPEC,
) -> list[EvalCase]:
    """One or more cases per source edition (default: every catalog edition). Fit and
    ambiguity are always judged against the whole `catalog`."""
    rng = random.Random(seed)  # noqa: S311 - reproducible generation, not security
    fam = family_of or (lambda e: e.work_id or e.edition_id)
    names = sorted(OPS)
    out: list[EvalCase] = []
    for e in sorted(catalog if sources is None else sources, key=lambda x: x.edition_id):
        for j in range(per_edition):
            k = rng.randint(1, 2)
            ops = sorted(rng.sample(names, k))
            # Half of all cases lose the ISBN (damaged/missing barcode) so that retrieval,
            # not the exact-identifier path, decides them.
            if rng.random() < 0.5 and "drop_isbn" not in ops:
                ops = sorted([*ops, "drop_isbn"])
            if "drop_isbn" in ops:
                ops = [o for o in ops if not o.startswith("isbn")]
            case_seed = rng.randrange(2**31)
            out.append(
                make_case(e, ops, case_seed, catalog, fam(e), f"syn-{e.edition_id}-{j}", spec)
            )
    return out
