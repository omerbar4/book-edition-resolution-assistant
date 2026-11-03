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
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from bera.evalkit.perturb import make_case
from bera.evalkit.splits import family_split
from bera.models import Edition, Query

DRAFTER = "template-drafter-v1 (deterministic program; not a human, not an LLM)"

# Realistic-input templates: (name, perturbation ops)
TEMPLATES: list[tuple[str, list[str]]] = [
    ("damaged_barcode_title_author_format", ["drop_isbn", "author_last_first"]),
    ("typo_title_with_format_year", ["drop_isbn", "typo"]),
    ("isbn10_hyphenated", ["isbn10_form", "drop_author"]),
    ("misread_isbn_digit", ["isbn_digit_error"]),
    ("title_author_only", ["drop_isbn", "drop_format", "drop_year"]),
    ("initials_author", ["drop_isbn", "author_initials"]),
]


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
) -> list[Draft]:
    rng = random.Random(seed)  # noqa: S311 - reproducible drafting, not security
    pool = sorted(
        (e for e in catalog if e.work_id and family_split(e.work_id, split_seed) == split),
        key=lambda e: e.edition_id,
    )
    picked = sorted(rng.sample(pool, min(n_in_corpus, len(pool))), key=lambda e: e.edition_id)
    out: list[Draft] = []
    for i, e in enumerate(picked):
        name, ops = TEMPLATES[i % len(TEMPLATES)]
        case = make_case(e, ops, rng.randrange(2**31), catalog, e.work_id or e.edition_id, "tmp")
        out.append(
            Draft(
                draft_id=f"{prefix}-{i + 1:03d}",
                split=split,
                family=case.family,
                query=case.query,
                template=name,
                source_edition_id=e.edition_id,
                proposed=Proposed(
                    expected=case.expected,
                    gold_edition_ids=case.gold_edition_ids,
                    ambiguity_reason=case.ambiguity_reason,
                ),
            )
        )
    probe_pool = [p for p in probes if family_split(f"probe:{p['title']}", split_seed) == split]
    for j, p in enumerate(sorted(probe_pool, key=lambda p: p["title"])[:n_probes]):
        out.append(
            Draft(
                draft_id=f"{prefix}-p{j + 1:02d}",
                split=split,
                family=f"probe:{p['title']}",
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
    a = p.parse_args(argv)
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
    )
    save_drafts(a.out, drafts)
    print(f"wrote {len(drafts)} {a.split} drafts to {a.out}")


if __name__ == "__main__":  # pragma: no cover
    main()
