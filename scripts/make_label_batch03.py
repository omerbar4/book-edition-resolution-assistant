"""Draft development batch 03 (drafter v4, one query per family this batch; batch-end reveal).

    uv run python scripts/make_label_batch03.py --db var/catalog_v3.sqlite

Selection rules (recorded in the manifest; see bera.evalkit.batchplan): families come from
pool A, the unused development families never used in the 300-case synthetic
policy-development check. A family contributes up to three queries, each from a distinct
template whose every op changes the query. No query repeats any seen before. The corpus and
split are read, never written; held-out families are never touched. Proposals are revealed
only after the whole batch is labeled (manifest "reveal": "after_batch"). Prints aggregate
checks only, never a per-case template, proposal or outcome distribution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from bera.catalog import Catalog
from bera.evalkit.batchplan import build_selection
from bera.evalkit.drafts import (
    DRAFTER_V4,
    MAX_QUERIES_PER_FAMILY,
    TEMPLATES,
    draft_batch_v4,
    query_key,
    save_drafts,
    template_effective,
)
from bera.evalkit.perturb import DEFAULT_LABEL_SPEC, perturbed_fields
from bera.evalkit.run import repo_relative
from bera.evalkit.splits import family_split

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/corpus/v3_proposed"
SPLIT_SEED = 20261103
# Owner decision 2026-11-07: family diversity first. Batch 03 takes ONE query from each of
# 20 distinct pool A families; additional queries per family (up to 3 overall) come in
# later batches.
BATCH_MAX_PER_FAMILY = 1
PRIOR = [ROOT / "data/eval/drafts/dev_batch01.jsonl", ROOT / "data/eval/drafts/dev_batch02.jsonl"]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20261108)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--out", type=Path, default=ROOT / "data/eval/drafts/dev_batch03.jsonl")
    a = p.parse_args()

    corpus_sha = sha256(CORPUS / "corpus.jsonl")
    family_of: dict[str, str] = json.loads((CORPUS / "families.json").read_text())
    cat = Catalog(a.db)
    with cat.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    catalog = list(cat.get(ids).values())
    by_id = {e.edition_id: e for e in catalog}
    sel = build_selection(ROOT, catalog, family_of, SPLIT_SEED, PRIOR)

    drafts = draft_batch_v4(
        catalog,
        split="dev",
        split_seed=SPLIT_SEED,
        seed=a.seed,
        n=a.n,
        prefix="d03",
        family_of=family_of,
        eligible_families=sel.pool_a,
        exclude_editions=sel.exclude_editions,
        exclude_queries=sel.seen_queries,
        existing_per_family=sel.existing_per_family,
        max_per_family=BATCH_MAX_PER_FAMILY,
    )

    tmpl = dict(TEMPLATES)
    per_family = Counter(d.family for d in drafts)
    by_family: dict[str, list[str]] = {}
    for d in drafts:
        by_family.setdefault(d.family, []).append(d.template)
    checks: dict[str, bool] = {
        "count == n": len(drafts) == a.n,
        "all dev split by family": all(
            d.split == "dev" and family_split(d.family, SPLIT_SEED) == "dev" for d in drafts
        ),
        "all families from pool A": set(per_family) <= sel.pool_a,
        "no used or discussed family": not set(per_family) & sel.used_families,
        "no policy-development family": not set(per_family) & sel.policy_dev_families,
        "one query per family in this batch (owner: diversity first)": len(per_family)
        == len(drafts)
        and all(n == BATCH_MAX_PER_FAMILY for n in per_family.values()),
        "at most three queries per family (including earlier batches)": all(
            n + sel.existing_per_family.get(f, 0) <= MAX_QUERIES_PER_FAMILY
            for f, n in per_family.items()
        ),
        "distinct templates within each family": all(
            len(set(v)) == len(v) for v in by_family.values()
        ),
        "no excluded source edition": not {d.source_edition_id for d in drafts}
        & sel.exclude_editions,
        "no previously seen query": not {query_key(d.query) for d in drafts} & sel.seen_queries,
        "queries distinct": len({query_key(d.query) for d in drafts}) == len(drafts),
        "every template effective": all(
            d.op_seed is not None
            and template_effective(d.template, by_id[d.source_edition_id or ""], d.op_seed)
            for d in drafts
        ),
        "query reproduces from source+ops": all(
            d.op_seed is not None
            and perturbed_fields(by_id[d.source_edition_id or ""], tmpl[d.template], d.op_seed)
            == d.query.model_dump(exclude_none=True)
            for d in drafts
        ),
        "opaque ids (d03- + 10 hex, unique)": all(
            re.fullmatch(r"d03-[0-9a-f]{10}", d.draft_id) for d in drafts
        )
        and len({d.draft_id for d in drafts}) == len(drafts),
        "no probe drafts": all(d.source_edition_id for d in drafts),
    }
    checks["corpus sha256 unchanged"] = sha256(CORPUS / "corpus.jsonl") == corpus_sha
    for k, v in checks.items():
        print(("PASS " if v else "FAIL ") + k)
    sizes = sorted(per_family.values(), reverse=True)
    print(f"queries {len(drafts)} in {len(per_family)} families; queries per family {sizes}")
    if not all(checks.values()):
        raise SystemExit("validation failed; nothing written")

    save_drafts(a.out, drafts)
    manifest = {
        "queue": repo_relative(a.out),
        "queue_sha256": sha256(a.out),
        "split": "dev",
        "drafts": len(drafts),
        "families": len(per_family),
        "queries_per_family": sizes,
        "drafted_by": DRAFTER_V4,
        "generator": "scripts/make_label_batch03.py",
        "seed": a.seed,
        "split_seed": SPLIT_SEED,
        "corpus_sha256": corpus_sha,
        "proposal_label_spec": DEFAULT_LABEL_SPEC,
        "reveal": "after_batch",
        "labels_file": "data/eval/labels/dev_batch03_labels.jsonl",
        "selection_criteria": {
            "pool": "A: unused development families never used in the 300-case synthetic "
            "policy-development check (bera.evalkit.batchplan)",
            "max_queries_per_family_overall": MAX_QUERIES_PER_FAMILY,
            "max_queries_per_family_this_batch": BATCH_MAX_PER_FAMILY,
            "family_priority": "diversity first: 20 distinct families; more queries per "
            "family in later batches",
            "within_family": "distinct templates; every op changes the query; editions may differ",
            "excluded": "families with any prior draft, families of discussed cases, previously "
            "seen queries, prior source/gold editions",
            "never_used_for_selection": "drafted proposals, system outputs or scores",
            "prior_queues": [str(q.relative_to(ROOT)) for q in PRIOR],
            "pool_sizes": {
                "unused_dev_families": len(sel.unused),
                "pool_a_families": len(sel.pool_a),
                "pool_a_query_capacity": sum(sel.capacity[f] for f in sel.pool_a),
                "pool_b_families": len(sel.pool_b),
                "pool_b_query_capacity": sum(sel.capacity[f] for f in sel.pool_b),
            },
        },
        "validation": checks,
        "note": (
            "Ids are opaque and the order is random. Before the whole batch is labeled, no "
            "template, template note, proposal, agreement or score is sent. The proposal is a "
            "program draft, not ground truth. Composition by template or proposed outcome is "
            "deliberately not summarized here."
        ),
    }
    a.out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"wrote {len(drafts)} drafts; queue sha256 {manifest['queue_sha256']}")


if __name__ == "__main__":
    main()
