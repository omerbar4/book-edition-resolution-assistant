"""Build the single resumable dev queue of the fixed evaluation plan (docs/EVALUATION_PLAN.md).

    uv run python scripts/make_dev_final_queue.py --db var/catalog_v3.sqlite

The queue holds the 20 batch 03 drafts with their lines byte-identical, plus 20 new drafts
(drafter v5): one per family; all 11 untouched pool A families first, then pool B in seeded
order; 4 per predefined stratum. Two reserves go to a separate sealed file; they are used
only to replace a case excluded for exposure, in fixed order. New proposals use label spec v3
(spec v3 equals v2 on every existing template; verified here on the batch 03 drafts). The
manifest sets reveal "after_batch". Prints aggregate checks only, never a per-case template,
stratum, proposal or outcome distribution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path

from bera.catalog import Catalog
from bera.evalkit.batchplan import build_selection
from bera.evalkit.drafts import (
    ALL_TEMPLATES,
    TEMPLATES,
    Draft,
    load_drafts,
    query_key,
    template_effective,
)
from bera.evalkit.perturb import judged_fields, label, perturbed_fields
from bera.evalkit.run import repo_relative
from bera.evalkit.splits import family_split
from bera.evalkit.stratified import (
    DRAFTER_V5,
    SPEC_FOR_NEW_DRAFTS,
    STRATA,
    ambiguity_editions,
    assign,
    candidates,
    to_drafts,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/corpus/v3_proposed"
SPLIT_SEED = 20261103
B03 = ROOT / "data/eval/drafts/dev_batch03.jsonl"
PRIOR = [ROOT / f"data/eval/drafts/dev_batch0{i}.jsonl" for i in (1, 2, 3)]
QUOTA = 4
N_RESERVES = 2


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20261109)
    p.add_argument("--out", type=Path, default=ROOT / "data/eval/drafts/dev_final.jsonl")
    a = p.parse_args()

    corpus_sha = sha256(CORPUS / "corpus.jsonl")
    b03_sha = sha256(B03)
    family_of: dict[str, str] = json.loads((CORPUS / "families.json").read_text())
    cat = Catalog(a.db)
    with cat.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    catalog = list(cat.get(ids).values())
    by_id = {e.edition_id: e for e in catalog}
    sel = build_selection(ROOT, catalog, family_of, SPLIT_SEED, PRIOR)

    def fam(e: object) -> str:
        w = e.work_id or e.edition_id  # type: ignore[attr-defined]
        return family_of.get(w, w)

    by_family: dict[str, list] = {}
    for e in catalog:
        f = fam(e)
        if f in sel.unused and e.work_id and e.edition_id not in sel.exclude_editions:
            by_family.setdefault(f, []).append(e)
    rng = random.Random(a.seed)
    pool_a = sorted(sel.pool_a)
    pool_b = sorted(sel.pool_b)
    rng.shuffle(pool_a)
    rng.shuffle(pool_b)
    cands = candidates(by_family, pool_a + pool_b, sel.seen_queries, catalog, a.seed)
    quotas = dict.fromkeys(STRATA, QUOTA)
    plan = assign(cands, pool_a, pool_b, quotas, N_RESERVES)
    print(
        f"feasible: {plan.feasible}; shortfall {plan.shortfall}; "
        f"unplaced required families {len(plan.unplaced_required)}"
    )
    if not plan.feasible:
        raise SystemExit("quotas or pool A placement infeasible; nothing written (not relaxed)")

    b03_lines = [x for x in B03.read_text(encoding="utf-8").splitlines() if x.strip()]
    b03 = load_drafts(B03)
    taken = {d.draft_id for d in b03}
    new = to_drafts(plan.assigned, catalog, "d03", rng, taken)
    reserves = to_drafts(plan.reserves, catalog, "d03", rng, taken)
    new_lines = [d.model_dump_json(exclude_none=True) for d in new]
    line_of = {d.draft_id: x for d, x in zip(b03, b03_lines, strict=True)}
    line_of |= {d.draft_id: x for d, x in zip(new, new_lines, strict=True)}
    queue_lines = [line_of[i] for i in sorted(line_of)]

    allq: list[Draft] = b03 + new
    fams = Counter(d.family for d in allq)
    a_set, b_set = set(pool_a), set(pool_b)

    def reproduces(d: Draft) -> bool:
        e = by_id[d.source_edition_id or ""]
        ops = ALL_TEMPLATES[d.template]
        f = perturbed_fields(e, ops, d.op_seed or 0)
        if f != d.query.model_dump(exclude_none=True):
            return False
        exp, gold, reason, _ = label(judged_fields(f, e), e, catalog, SPEC_FOR_NEW_DRAFTS)
        return (exp, gold, reason) == (
            d.proposed.expected,
            d.proposed.gold_edition_ids,
            d.proposed.ambiguity_reason,
        )

    def v3_equals_v2(d: Draft) -> bool:
        e = by_id[d.source_edition_id or ""]
        j = judged_fields(perturbed_fields(e, dict(TEMPLATES)[d.template], d.op_seed or 0), e)
        return label(j, e, catalog, "v2")[:3] == label(j, e, catalog, "v3")[:3]

    checks: dict[str, bool] = {
        "batch 03 file unchanged": sha256(B03) == b03_sha,
        "all 20 batch 03 lines present byte-identical": all(x in queue_lines for x in b03_lines),
        "queue size 40": len(queue_lines) == 40,
        "one query per family across the queue (40 distinct families)": len(fams) == 40,
        "all dev split by family": all(family_split(d.family, SPLIT_SEED) == "dev" for d in allq),
        "new drafts avoid used/discussed families": not {d.family for d in new} & sel.used_families,
        "all 11 untouched pool A families used": a_set <= {d.family for d in new},
        "remaining new families from pool B": {d.family for d in new} - a_set <= b_set,
        "stratum quotas met exactly (4 each)": Counter(d.stratum for d in new) == Counter(quotas),
        "template belongs to its stratum": all(d.template in STRATA[d.stratum or ""] for d in new),
        "edition-ambiguity sources sit in a same-title/author group (catalog structure)": all(
            by_id[d.source_edition_id or ""]
            in ambiguity_editions([e for e in catalog if e.work_id and fam(e) == d.family])
            for d in new
            if d.stratum == "edition_ambiguity"
        ),
        "every new template effective": all(
            template_effective(d.template, by_id[d.source_edition_id or ""], d.op_seed or 0)
            for d in new + reserves
        ),
        "new queries and proposals reproduce (spec v3)": all(map(reproduces, new + reserves)),
        "spec v3 == v2 on the batch 03 drafts": all(map(v3_equals_v2, b03)),
        "no previously seen query": not {query_key(d.query) for d in new + reserves}
        & sel.seen_queries,
        "queries distinct": len({query_key(d.query) for d in allq + reserves})
        == len(allq) + len(reserves),
        "opaque unique ids": all(re.fullmatch(r"d03-[0-9a-f]{10}", d.draft_id) for d in new)
        and len({d.draft_id for d in allq + reserves}) == len(allq) + len(reserves),
        "reserves: distinct pool B families not in the queue": {d.family for d in reserves} <= b_set
        and not {d.family for d in reserves} & set(fams)
        and len({d.family for d in reserves}) == len(reserves) == N_RESERVES,
        "corpus sha256 unchanged": sha256(CORPUS / "corpus.jsonl") == corpus_sha,
    }
    for k, v in checks.items():
        print(("PASS " if v else "FAIL ") + k)
    if not all(checks.values()):
        raise SystemExit("validation failed; nothing written")

    a.out.write_text("\n".join(queue_lines) + "\n", encoding="utf-8")
    res_path = a.out.with_suffix(".reserves.jsonl")
    res_path.write_text(
        "".join(d.model_dump_json(exclude_none=True) + "\n" for d in reserves), encoding="utf-8"
    )
    manifest = {
        "queue": repo_relative(a.out),
        "queue_sha256": sha256(a.out),
        "split": "dev",
        "drafts": len(queue_lines),
        "families": len(fams),
        "reveal": "after_batch",
        "labels_file": "data/eval/labels/dev_final_labels.jsonl",
        "proposal_label_spec": "v2",
        "proposal_label_spec_note": (
            "v2 applies to the 20 batch 03 drafts (lines byte-identical; batch 03 manifest). "
            "New drafts carry proposal_label_spec v3 per draft. v3 equals v2 on every existing "
            "template (verified on these drafts)."
        ),
        "composition": {
            "batch03_drafts": len(b03),
            "batch03_sha256": b03_sha,
            "new_drafts": len(new),
            "new_drafter": DRAFTER_V5,
            "new_from_pool_a": len({d.family for d in new} & a_set),
            "new_from_pool_b": len({d.family for d in new} & b_set),
            "stratum_quotas_new": quotas,
        },
        "reserves": {
            "file": repo_relative(res_path),
            "sha256": sha256(res_path),
            "count": len(reserves),
            "use": "only to replace a case excluded for exposure, in file order; never to "
            "replace a hard, skipped or disputed case",
        },
        "selection_criteria": {
            "strata": {k: list(v) for k, v in STRATA.items()},
            "edition_ambiguity_rule": "source in a group of >=2 family editions sharing "
            "normalized title and first author (catalog structure only)",
            "family_rule": "one query per family; 11 untouched pool A families first, then "
            "pool B in seeded order; maximum bipartite matching of quota slots",
            "never_used_for_selection": "drafted proposals, system outputs or scores",
            "seed": a.seed,
            "split_seed": SPLIT_SEED,
            "prior_queues": [repo_relative(q) for q in PRIOR],
        },
        "corpus_sha256": corpus_sha,
        "generator": "scripts/make_dev_final_queue.py",
        "validation": checks,
    }
    a.out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(
        f"wrote {len(queue_lines)} drafts ({len(fams)} families) + {len(reserves)} sealed "
        f"reserves; queue sha256 {manifest['queue_sha256']}"
    )


if __name__ == "__main__":
    main()
