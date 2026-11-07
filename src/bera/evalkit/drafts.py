"""Program-drafted labeling queue items (NOT labels).

Drafts are produced by a deterministic template generator from catalog editions in
development families, plus out-of-corpus probe books. A draft becomes an evaluation case
only after a human labels it in the labeling UI; it is then stored with
origin="ai_drafted_human_labeled" and the human's labeler id. Held-out drafts are written
to a separate file and are not served by the dev labeling queue.
"""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from bera.evalkit.perturb import OPS, clean_fields, make_case
from bera.evalkit.splits import family_split
from bera.models import Edition, Query

DRAFTER = "template-drafter-v1 (deterministic program; not a human, not an LLM)"
DRAFTER_V2 = "template-drafter-v2 (deterministic program; skips templates that cannot apply)"
DRAFTER_V3 = (
    "template-drafter-v3 (deterministic program; every op verified to change the query; "
    "one case per family; opaque ids)"
)

# Realistic-input templates: (name, perturbation ops)
TEMPLATES: list[tuple[str, list[str]]] = [
    ("damaged_barcode_title_author_format", ["drop_isbn", "author_last_first"]),
    ("typo_title_with_format_year", ["drop_isbn", "typo"]),
    ("isbn10_hyphenated", ["isbn10_form", "drop_author"]),
    ("misread_isbn_digit", ["isbn_digit_error"]),
    ("title_author_only", ["drop_isbn", "drop_format", "drop_year"]),
    ("initials_author", ["drop_isbn", "author_initials"]),
]


def template_applies(ops: Sequence[str], e: Edition) -> bool:
    """Can every op in a template actually change this source's query? ISBN ops need an
    ISBN-13 (the drafter builds queries from ISBN-13 only); author ops need a multi-word
    first author."""
    for op in ops:
        if op in ("isbn10_form", "isbn_digit_error") and not e.isbn_13:
            return False
        if op in ("author_last_first", "author_initials") and (
            not e.authors or len(e.authors[0].split()) < 2
        ):
            return False
    return True


# Fields a template's name promises the query still carries (v3 checks them).
TEMPLATE_KEEPS: dict[str, tuple[str, ...]] = {
    "damaged_barcode_title_author_format": ("title", "author", "physical_format"),
    "typo_title_with_format_year": ("title", "physical_format", "publish_year"),
    "isbn10_hyphenated": ("isbn", "title"),
    "misread_isbn_digit": ("isbn",),
    "title_author_only": ("title", "author"),
    "initials_author": ("title", "author"),
}


def template_effective(name: str, e: Edition, seed: int) -> bool:
    """v3 applicability: replaying the template's ops exactly as `perturbed_fields` does,
    EVERY op must change the query, and the fields the template name promises must remain."""
    import random as _random

    ops = dict(TEMPLATES)[name]
    rng = _random.Random(seed)  # noqa: S311 - same stream as perturbed_fields
    fields = clean_fields(e)
    for op in ops:
        before = dict(fields)
        OPS[op](fields, e, rng)
        if fields == before:
            return False
    return all(k in fields for k in TEMPLATE_KEEPS[name])


def query_key(q: Query | Mapping[str, Any]) -> str:
    d = q.model_dump(exclude_none=True) if isinstance(q, Query) else dict(q)
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def draft_batch_v3(
    catalog: Sequence[Edition],
    *,
    split: Literal["dev", "heldout"],
    split_seed: int,
    seed: int,
    n: int,
    prefix: str,
    family_of: Mapping[str, str],
    exclude_families: set[str],
    exclude_editions: set[str],
    exclude_queries: set[str],
) -> list[Draft]:
    """Independent-labeling batch: at most one case per family, no excluded family/edition,
    no previously seen query, every template verified effective, and opaque random ids in
    random order, so neither the id nor the position hints at the template or answer.
    Proposals use the current synthetic label spec (DEFAULT_LABEL_SPEC). No probes."""

    def fam(e: Edition) -> str:
        wid = e.work_id or e.edition_id
        return family_of.get(wid, wid)

    rng = random.Random(seed)  # noqa: S311 - reproducible drafting, not security
    by_family: dict[str, list[Edition]] = {}
    for e in sorted(catalog, key=lambda e: e.edition_id):
        f = fam(e)
        if (
            e.work_id
            and family_split(f, split_seed) == split
            and f not in exclude_families
            and e.edition_id not in exclude_editions
        ):
            by_family.setdefault(f, []).append(e)
    families = sorted(by_family)
    rng.shuffle(families)
    names = [t[0] for t in TEMPLATES]
    out: list[Draft] = []
    used_ids: set[str] = set()
    k = 0
    for f in families:
        if len(out) >= n:
            break
        e = rng.choice(by_family[f])
        op_seed = rng.randrange(2**31)
        chosen = None
        for j in range(len(names)):  # round-robin, first template that truly applies
            name = names[(k + j) % len(names)]
            if template_effective(name, e, op_seed):
                chosen = name
                break
        if chosen is None:
            continue
        case = make_case(e, dict(TEMPLATES)[chosen], op_seed, catalog, f, "tmp")
        if query_key(case.query) in exclude_queries:
            continue
        k += 1
        token = f"{rng.getrandbits(40):010x}"
        while token in used_ids:
            token = f"{rng.getrandbits(40):010x}"
        used_ids.add(token)
        out.append(
            Draft(
                draft_id=f"{prefix}-{token}",
                split=split,
                family=f,
                query=case.query,
                template=chosen,
                drafted_by=DRAFTER_V3,
                source_edition_id=e.edition_id,
                op_seed=op_seed,
                proposed=Proposed(
                    expected=case.expected,
                    gold_edition_ids=case.gold_edition_ids,
                    ambiguity_reason=case.ambiguity_reason,
                ),
            )
        )
    return sorted(out, key=lambda d: d.draft_id)  # random order: ids are random


def template_note(d: Draft, source: Edition | None) -> str | None:
    """Plain-language note when a v1 draft's template did not apply to its source, so the
    template name does not describe the query. Reveals nothing about the answer."""
    if source is None:
        return None
    ops = dict(TEMPLATES).get(d.template, [])
    notes = []
    if any(op in ("isbn10_form", "isbn_digit_error") for op in ops) and not d.query.isbn:
        notes.append("the ISBN step was not applied, so this query has no ISBN")
    if any(op in ("author_last_first", "author_initials") for op in ops) and (
        not source.authors or len(source.authors[0].split()) < 2
    ):
        notes.append("the author-rewriting step could not change this author")
    if not notes:
        return None
    return f"Template '{d.template}' did not fully apply: " + "; ".join(notes) + "."


class Proposed(BaseModel):
    expected: Literal["suggest", "abstain"]
    gold_edition_ids: list[str]
    ambiguity_reason: str | None = None


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str
    split: Literal["dev", "heldout"]
    family: str
    query: Query
    template: str
    drafted_by: str = DRAFTER
    source_edition_id: str | None = None
    op_seed: int | None = None  # v3: replay with perturbed_fields(source, ops, op_seed)
    proposed: Proposed


def draft_batch(
    catalog: Sequence[Edition],
    probes: Sequence[dict[str, Any]],
    *,
    split: Literal["dev", "heldout"],
    split_seed: int,
    seed: int,
    n_in_corpus: int,
    n_probes: int,
    prefix: str,
    family_of: Mapping[str, str] | None = None,
    probe_status: Mapping[str, str] | None = None,
    drafter: str = "v2",
) -> list[Draft]:
    """family_of maps work ids to conservative work families (families.json); split
    assignment uses the family, so aliases/translations never straddle dev and held-out.
    Probe drafts are produced ONLY for probes whose frozen-corpus audit status is
    'verified_absent'; quarantined or unaudited probes get no abstention draft."""

    def fam(e: Edition) -> str:
        wid = e.work_id or e.edition_id
        return (family_of or {}).get(wid, wid)

    rng = random.Random(seed)  # noqa: S311 - reproducible drafting, not security
    pool = sorted(
        (e for e in catalog if e.work_id and family_split(fam(e), split_seed) == split),
        key=lambda e: e.edition_id,
    )
    picked = sorted(rng.sample(pool, min(n_in_corpus, len(pool))), key=lambda e: e.edition_id)
    out: list[Draft] = []
    for i, e in enumerate(picked):
        name, ops = TEMPLATES[i % len(TEMPLATES)]
        if drafter == "v2":
            # rotate to the first template whose ops can actually apply to this source
            for j in range(len(TEMPLATES)):
                cand = TEMPLATES[(i + j) % len(TEMPLATES)]
                if template_applies(cand[1], e):
                    name, ops = cand
                    break
        case = make_case(e, ops, rng.randrange(2**31), catalog, fam(e), "tmp")
        out.append(
            Draft(
                draft_id=f"{prefix}-{i + 1:03d}",
                split=split,
                family=case.family,
                query=case.query,
                template=name,
                drafted_by=DRAFTER_V2 if drafter == "v2" else DRAFTER,
                source_edition_id=e.edition_id,
                proposed=Proposed(
                    expected=case.expected,
                    gold_edition_ids=case.gold_edition_ids,
                    ambiguity_reason=case.ambiguity_reason,
                ),
            )
        )

    def probe_family(p: Mapping[str, Any]) -> str:
        keys = sorted(p.get("author_keys") or [])
        return f"probe-author:{keys[0]}" if keys else f"probe:{p['title']}"

    status = probe_status or {}
    probe_pool = [
        p
        for p in probes
        if status.get(p["title"]) == "verified_absent"
        and family_split(probe_family(p), split_seed) == split
    ]
    for j, p in enumerate(sorted(probe_pool, key=lambda p: p["title"])[:n_probes]):
        out.append(
            Draft(
                draft_id=f"{prefix}-p{j + 1:02d}",
                split=split,
                family=probe_family(p),
                query=Query(title=p["title"], author=p.get("author")),
                template="out_of_corpus_probe",
                proposed=Proposed(
                    expected="abstain", gold_edition_ids=[], ambiguity_reason="out_of_corpus"
                ),
            )
        )
    return out


def save_drafts(path: Path, drafts: Sequence[Draft]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for d in drafts:
            fh.write(d.model_dump_json(exclude_none=True) + "\n")


def load_drafts(path: Path) -> list[Draft]:
    with path.open(encoding="utf-8") as fh:
        return [Draft.model_validate(json.loads(line)) for line in fh if line.strip()]


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - thin CLI
    import argparse

    from bera.catalog import Catalog

    p = argparse.ArgumentParser(prog="bera-drafts")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--probes", type=Path, required=True, help="exclusions_vN.jsonl")
    p.add_argument("--split", choices=["dev", "heldout"], required=True)
    p.add_argument("--split-seed", type=int, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--n", type=int, default=16)
    p.add_argument("--n-probes", type=int, default=4)
    p.add_argument("--prefix", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--families", type=Path, help="families.json from the corpus build")
    p.add_argument("--probe-audit", type=Path, help="probe_audit.json from the corpus build")
    a = p.parse_args(argv)
    family_of = json.loads(a.families.read_text()) if a.families else None
    probe_status = (
        {k: v["status"] for k, v in json.loads(a.probe_audit.read_text()).items()}
        if a.probe_audit
        else None
    )
    cat = Catalog(a.db)
    with cat.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    probes = [json.loads(x) for x in a.probes.read_text(encoding="utf-8").splitlines() if x]
    drafts = draft_batch(
        list(cat.get(ids).values()),
        probes,
        split=a.split,
        split_seed=a.split_seed,
        seed=a.seed,
        n_in_corpus=a.n,
        n_probes=a.n_probes,
        prefix=a.prefix,
        family_of=family_of,
        probe_status=probe_status,
    )
    save_drafts(a.out, drafts)
    print(f"wrote {len(drafts)} {a.split} drafts to {a.out}")


if __name__ == "__main__":  # pragma: no cover
    main()
