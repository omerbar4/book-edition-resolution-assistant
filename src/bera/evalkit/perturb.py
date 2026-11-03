"""Seeded, controlled query perturbations derived from catalog editions.

Each case records its ops, seed and source edition. The expected behavior is computed
deterministically AFTER perturbation: if the surviving structured fields (compared exactly,
after normalization) fit more than one edition, the case is labeled `abstain` with reason
"underspecified". These are synthetic cases; they never count as human-labeled.
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


OPS: dict[str, Op] = {
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


def _fits(fields: dict[str, object], e: Edition) -> bool:
    """Exact (normalized) agreement of every provided structured field with an edition."""
    isbn_raw = fields.get("isbn")
    if isbn_raw:
        p = isbnlib.parse(str(isbn_raw))
        if not p.valid:
            return False  # a damaged ISBN identifies nothing exactly
        mine = {isbnlib.parse(x).isbn13 for x in (*e.isbn_10, *e.isbn_13)}
        if p.isbn13 not in mine:
            return False
    if fields.get("title") and norm_text(str(fields["title"])) != norm_text(e.title):
        return False
    if fields.get("author") and norm_person(str(fields["author"])) not in {
        norm_person(a) for a in e.authors
    }:
        return False
    fmt = fields.get("physical_format")
    if fmt and str(fmt).replace(" ", "_") != e.physical_format.value:
        return False
    return not (fields.get("publish_year") is not None and fields["publish_year"] != e.publish_year)


def make_case(
    e: Edition,
    ops: Sequence[str],
    seed: int,
    catalog: Sequence[Edition],
    family: str,
    case_id: str,
) -> EvalCase:
    rng = random.Random(seed)  # noqa: S311 - reproducible perturbation, not security
    fields = clean_fields(e)
    for name in ops:
        OPS[name](fields, e, rng)
    # Which editions does the remaining *clean* information fit? (typos are noise, so the
    # source title/author stand in for perturbed ones when judging identifiability)
    judged = dict(fields)
    if "title" in judged:
        judged["title"] = e.title
    if "author" in judged and e.authors:
        judged["author"] = e.authors[0]
    if "isbn" in judged and not isbnlib.parse(str(judged["isbn"])).valid:
        judged.pop("isbn")
    fits = sorted(x.edition_id for x in catalog if _fits(judged, x))
    if e.edition_id not in fits:
        fits = sorted({*fits, e.edition_id})
    unique = len(fits) == 1
    return EvalCase(
        case_id=case_id,
        query=Query.model_validate(fields),
        expected="suggest" if unique else "abstain",
        gold_edition_ids=[e.edition_id] if unique else fits,
        ambiguity_reason=None if unique else f"underspecified: {len(fits)} editions fit",
        family=family,
        origin="synthetic_perturbation",
        perturbation=Perturbation(ops=list(ops), seed=seed, source_edition_id=e.edition_id),
    )


def generate(
    catalog: Sequence[Edition],
    seed: int,
    per_edition: int = 2,
    family_of: Callable[[Edition], str] | None = None,
) -> list[EvalCase]:
    rng = random.Random(seed)  # noqa: S311 - reproducible generation, not security
    fam = family_of or (lambda e: e.work_id or e.edition_id)
    names = sorted(OPS)
    out: list[EvalCase] = []
    for e in sorted(catalog, key=lambda x: x.edition_id):
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
            out.append(make_case(e, ops, case_seed, catalog, fam(e), f"syn-{e.edition_id}-{j}"))
    return out
