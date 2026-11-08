"""Refresh dev metrics and LLM route evidence after an owner label amendment.

    uv run python scripts/refresh_dev_amended.py

Policy and thresholds are unchanged, so system decisions are exactly those of the committed
policy-v2 run (data/eval/results/dev60_human_policy_v2_initials/report.json); only labels
change. Metrics and route evidence are recomputed from that run's per-case outputs with owner
amendments applied (bera.evalkit.provenance.apply_amendments). Earlier reports are kept.
DEVELOPMENT evidence only; not held-out; uncalibrated.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bera.catalog import Catalog
from bera.evalkit.cases import load_cases
from bera.evalkit.devanalysis import metrics
from bera.evalkit.families import load_frozen_queue, resolve_families
from bera.evalkit.provenance import apply_amendments
from bera.evalkit.run import repo_relative
from bera.llm.routes import gate_from_evidence, measure

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data/eval/results/dev60_human_policy_v2_initials/report.json"
OUT_DIR = ROOT / "data/eval/results/dev60_human_policy_v2_amended"
ROUTES_OUT = ROOT / "data/eval/llm_route_evidence_policy_v2_amended.json"
LABELS = [
    ROOT / "data/eval/labels/dev_batch02_labels.jsonl",
    ROOT / "data/eval/labels/dev_final_labels.jsonl",
]
QUEUES = [ROOT / "data/eval/drafts/dev_batch02.jsonl", ROOT / "data/eval/drafts/dev_final.jsonl"]
FAMILIES = ROOT / "data/corpus/v3_proposed/families.json"
DEV_CHECK = ROOT / "data/eval/dev_check_v3_synthetic.jsonl"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows_for(report: dict[str, Any], key: str, cases: list[Any], prior: set[str]) -> list[dict]:
    pc = {r["case_id"]: r for r in report["systems"][key]["per_case"]}
    return [
        {
            "case_id": c.case_id,
            "family": c.family,
            "policy_dev_family": c.family in prior,
            "expected": c.expected,
            "gold": set(c.gold_edition_ids),
            "outcome": pc[c.case_id]["outcome"],
            "suggested": pc[c.case_id]["suggested"],
            "top1": pc[c.case_id]["top1"],
            "adj_status": pc[c.case_id]["adjudication_status"],
            "adj_choice": pc[c.case_id]["adjudication_choice"],
        }
        for c in cases
    ]


def main() -> None:
    report = json.loads(REPORT.read_text())
    catalog = Catalog(ROOT / "var/catalog_v3.sqlite")
    drafts = [d for q in QUEUES for d in load_frozen_queue(q)[0]]
    family_of = json.loads(FAMILIES.read_text())
    prior = {json.loads(x)["family"] for x in DEV_CHECK.read_text().splitlines() if x.strip()}
    original, amended, applied = [], [], []
    for lab in LABELS:
        cs = load_cases(lab)
        original += cs
        a, ids = apply_amendments(cs, lab)
        amended += a
        applied += ids
    original = resolve_families(original, drafts, family_of, catalog)
    amended = resolve_families(amended, drafts, family_of, catalog)

    default = "2b_lexical_rrf"
    before = rows_for(report, default, original, prior)
    after = rows_for(report, default, amended, prior)

    def group(rows: list[dict]) -> dict[str, Any]:
        return {
            "all": metrics(rows),
            "never in the policy-development check": metrics(
                [r for r in rows if not r["policy_dev_family"]]
            ),
            "policy-development families": metrics([r for r in rows if r["policy_dev_family"]]),
        }

    def remaining(rows: list[dict]) -> int:
        return sum(1 for r in rows if r["expected"] == "suggest" and r["outcome"] != "suggest")

    out = {
        "label": "DEVELOPMENT evidence only: same 60 human labels with owner amendments applied; "
        "system decisions are those of the committed policy-v2 run (no policy or threshold "
        "change); not held-out; uncalibrated",
        "source_report": repo_relative(REPORT),
        "source_report_sha256": sha256(REPORT),
        "amendments_applied": applied,
        "counts": {
            "cases": len(after),
            "families": len({r["family"] for r in after}),
            "human_edition": sum(r["expected"] == "suggest" for r in after),
            "human_review": sum(r["expected"] == "abstain" for r in after),
            "human_review_reasons": dict(
                Counter(c.ambiguity_reason for c in amended if c.ambiguity_reason)
            ),
            "remaining_reviews_on_human_edition_cases": remaining(after),
            "remaining_reviews_before_amendment": remaining(before),
            "wrong_suggestions": sum(
                1 for r in after if r["outcome"] == "suggest" and r["suggested"] not in r["gold"]
            ),
        },
        "metrics_default_after_amendment": group(after),
        "metrics_default_before_amendment": group(before),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "metrics.json").write_text(json.dumps(out, indent=1, default=sorted) + "\n")

    sys6 = rows_for(report, "6_routed_llm", amended, prior)
    routes = measure(
        {"choice": r["adj_choice"], "top1": r["top1"], "expected": r["expected"], "gold": r["gold"]}
        for r in sys6
        if r["adj_status"] == "completed" and r["adj_choice"]
    )
    routes["source"] = {
        "report": repo_relative(REPORT),
        "report_sha256": sha256(REPORT),
        "labels": [{"path": repo_relative(x), "sha256": sha256(x)} for x in LABELS],
        "amendments": [
            {"path": repo_relative(p), "sha256": sha256(p)}
            for lab in LABELS
            if (p := lab.with_name(lab.stem + ".amendments.jsonl")).exists()
        ],
        "split": "dev",
        "note": "same system run as llm_route_evidence_policy_v2.json; owner amendments applied",
    }
    gate = gate_from_evidence(routes, ROUTES_OUT.name)
    ROUTES_OUT.write_text(json.dumps(routes, indent=1) + "\n")
    c = out["counts"]
    print(
        f"cases {c['cases']} / families {c['families']}: edition {c['human_edition']}, "
        f"review {c['human_review']} {c['human_review_reasons']}; amendments {applied}"
    )
    m = out["metrics_default_after_amendment"]["all"]
    for k, v in m.items():
        if isinstance(v, dict):
            print(f"  {k}: {v['numerator']}/{v['denominator']} wilson {v['wilson95_case_level']}")
    print(
        f"remaining reviews on human-edition cases: {c['remaining_reviews_before_amendment']} "
        f"-> {c['remaining_reviews_on_human_edition_cases']}; wrong {c['wrong_suggestions']}"
    )
    for r, v in routes["routes"].items():
        print(f"route {r}: n={v['n']} correct={v['correct']} open={v['open']}")
    print(f"open routes: {sorted(gate.open_routes) or 'none'}")


if __name__ == "__main__":
    main()
