"""Synthetic perturbation cases from DEVELOPMENT families of the built corpus (engineering check).

Source editions are drawn only from dev families (families.json + split seed). Which editions
"fit" a perturbed query is judged against the WHOLE catalog, with unknown metadata never
treated as a mismatch, so no case gets a forced unique gold. These cases are synthetic; they
are never human labels and never held-out.

    uv run python scripts/make_dev_check_cases.py --db var/catalog_v3.sqlite \
        --families data/corpus/v3_proposed/families.json --n 300 --seed 20261103 \
        --out data/eval/dev_check_v3_synthetic.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from bera.catalog import Catalog
from bera.evalkit.perturb import generate
from bera.evalkit.splits import family_split


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--families", type=Path, required=True)
    p.add_argument("--split-seed", type=int, default=20261103)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--n", type=int, default=300, help="source editions (1 case each)")
    p.add_argument("--exclude-sources", type=Path, help="drafts JSONL whose sources to skip")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    family_of: dict[str, str] = json.loads(a.families.read_text())
    cat = Catalog(a.db)
    with cat.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    catalog = list(cat.get(ids).values())

    def fam(e: object) -> str:
        wid = getattr(e, "work_id", None) or getattr(e, "edition_id")  # noqa: B009
        return family_of.get(wid, wid)

    skip: set[str] = set()
    if a.exclude_sources:
        for line in a.exclude_sources.read_text().splitlines():
            if line.strip() and (s := json.loads(line).get("source_edition_id")):
                skip.add(s)
    dev = sorted(
        (
            e
            for e in catalog
            if e.work_id
            and e.work_id in family_of
            and family_split(fam(e), a.split_seed) == "dev"
            and e.edition_id not in skip
        ),
        key=lambda e: e.edition_id,
    )
    rng = random.Random(a.seed)
    sources = sorted(rng.sample(dev, min(a.n, len(dev))), key=lambda e: e.edition_id)
    cases = [
        c.model_copy(update={"split": "dev"})
        for c in generate(catalog, seed=a.seed, per_edition=1, family_of=fam, sources=sources)
    ]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", encoding="utf-8") as fh:
        for c in cases:
            fh.write(c.model_dump_json(exclude_none=True) + "\n")
    print(
        f"wrote {len(cases)} synthetic dev cases from {len(dev)} dev editions "
        f"({sum(c.expected == 'abstain' for c in cases)} expected abstain) to {a.out}"
    )


if __name__ == "__main__":
    main()
