"""Relabel SYNTHETIC development cases under a newer label spec, case by case, with evidence.

The original case file is never modified. Each case's query is re-derived from its recorded
source edition, ops and seed and must reproduce byte-for-byte (otherwise the script refuses).
Only the label (expected / gold / ambiguity_reason) is recomputed under `--spec`; every
change is written to `--changes` with the rule applied and the catalog evidence.

Refuses non-dev cases. These remain synthetic engineering-check labels, never human labels.

    uv run python scripts/relabel_synthetic_cases.py --db var/catalog_v3.sqlite \
        --cases data/eval/dev_check_v3_synthetic.jsonl --spec v2 \
        --out data/eval/dev_check_v3_synthetic.labels_v2.jsonl \
        --changes data/eval/label_changes/dev_check_v3_v1_to_v2.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from bera.catalog import Catalog
from bera.evalkit.cases import EvalCase
from bera.evalkit.perturb import judged_fields, label, perturbed_fields
from bera.models import Query


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--from-spec", default="v1")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--changes", type=Path, required=True)
    a = ap.parse_args()
    cases = [EvalCase.model_validate_json(x) for x in a.cases.read_text().splitlines() if x.strip()]
    if any(c.split != "dev" for c in cases):
        raise SystemExit("refusing: only development cases may be relabeled here")
    cat = Catalog(a.db)
    with cat.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    by_id = cat.get(ids)
    catalog = list(by_id.values())

    out, changes = [], []
    for c in cases:
        p = c.perturbation
        if p is None or p.source_edition_id not in by_id:
            raise SystemExit(f"{c.case_id}: no reproducible perturbation record")
        src = by_id[p.source_edition_id]
        fields = perturbed_fields(src, p.ops, p.seed)
        if Query.model_validate(fields) != c.query:
            raise SystemExit(f"{c.case_id}: query does not reproduce from its seed; refusing")
        judged = judged_fields(fields, src)
        old = label(judged, src, catalog, a.from_spec)
        if (old[0], old[1], old[2]) != (c.expected, c.gold_edition_ids, c.ambiguity_reason):
            raise SystemExit(f"{c.case_id}: stored label is not spec {a.from_spec}; refusing")
        exp, gold, reason, ev = label(judged, src, catalog, a.spec)
        new = c.model_copy(
            update={"expected": exp, "gold_edition_ids": gold, "ambiguity_reason": reason}
        )
        out.append(new)
        if (exp, gold, reason) != (c.expected, c.gold_edition_ids, c.ambiguity_reason):
            changes.append(
                {
                    "case_id": c.case_id,
                    "from_spec": a.from_spec,
                    "to_spec": a.spec,
                    "query": c.query.model_dump(exclude_none=True),
                    "before": {
                        "expected": c.expected,
                        "gold_edition_ids": c.gold_edition_ids,
                        "ambiguity_reason": c.ambiguity_reason,
                    },
                    "after": {
                        "expected": exp,
                        "gold_edition_ids": gold,
                        "ambiguity_reason": reason,
                    },
                    "removed_from_gold": sorted(set(c.gold_edition_ids) - set(gold)),
                    "evidence": ev,
                }
            )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.changes.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", encoding="utf-8") as fh:
        for c in out:
            fh.write(c.model_dump_json(exclude_none=True) + "\n")
    with a.changes.open("w", encoding="utf-8") as fh:
        for ch in changes:
            fh.write(json.dumps(ch, ensure_ascii=False) + "\n")
    summary = {
        "label": "SYNTHETIC development labels (engineering check), not human labels",
        "from_spec": a.from_spec,
        "to_spec": a.spec,
        "source_cases": str(a.cases),
        "source_cases_sha256": sha256(a.cases),
        "relabeled_cases": str(a.out),
        "relabeled_cases_sha256": sha256(a.out),
        "catalog_fixtures_sha256": cat.meta().get("fixtures_sha256"),
        "cases": len(out),
        "changed": len(changes),
        "transitions": dict(
            Counter(f"{ch['before']['expected']}->{ch['after']['expected']}" for ch in changes)
        ),
        "rules_applied": dict(Counter(str(ch["evidence"].get("rule")) for ch in changes)),
        "expected_after": dict(Counter(c.expected for c in out)),
    }
    a.changes.with_suffix(".summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
