"""Compare two development harness runs case by case (same 60 human labels).

    uv run python scripts/compare_dev_runs.py --db var/catalog_v3.sqlite \
        --before data/eval/results/dev60_human_policy_v1/report.json \
        --after data/eval/results/dev60_human_policy_v2_initials/report.json

Reports gained and lost suggestions, wrong suggestions, and the remaining reviews with their
causes (re-running the current default resolver, no models). DEVELOPMENT evidence only: the
change being compared was motivated by these same cases, so this is not independent proof of
improvement.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bera.catalog import Catalog
from bera.evalkit.cases import load_cases
from bera.evalkit.devanalysis import cause, metrics
from bera.evalkit.families import load_frozen_queue, resolve_families
from bera.evalkit.run import repo_relative
from bera.policy import POLICY_VERSION
from bera.service import Resolver

ROOT = Path(__file__).resolve().parents[1]
LABELS = [
    ROOT / "data/eval/labels/dev_batch02_labels.jsonl",
    ROOT / "data/eval/labels/dev_final_labels.jsonl",
]
QUEUES = [ROOT / "data/eval/drafts/dev_batch02.jsonl", ROOT / "data/eval/drafts/dev_final.jsonl"]
FAMILIES = ROOT / "data/corpus/v3_proposed/families.json"
DEV_CHECK = ROOT / "data/eval/dev_check_v3_synthetic.jsonl"
DEFAULT = "2b_lexical_rrf"


def per_case(report: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    return {r["case_id"]: r for r in report["systems"][key]["per_case"]}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    a = p.parse_args()
    before, after = json.loads(a.before.read_text()), json.loads(a.after.read_text())
    catalog = Catalog(a.db)
    drafts = [d for q in QUEUES for d in load_frozen_queue(q)[0]]
    cases = resolve_families(
        [c for lab in LABELS for c in load_cases(lab)],
        drafts,
        json.loads(FAMILIES.read_text()),
        catalog,
    )
    prior = {json.loads(x)["family"] for x in DEV_CHECK.read_text().splitlines() if x.strip()}
    b, f = per_case(before, DEFAULT), per_case(after, DEFAULT)
    systems_after = [k for k, v in after["systems"].items() if v["status"] == "ran"]
    identical = (
        len(
            {
                json.dumps(
                    [(r["outcome"], r["suggested"]) for r in after["systems"][k]["per_case"]]
                )
                for k in systems_after
            }
        )
        == 1
    )

    def correct(r: dict[str, Any], gold: set[str]) -> bool:
        return r["outcome"] == "suggest" and r["suggested"] in gold

    resolver = Resolver(catalog, traces=None, provider=None)
    gained, lost, wrong, remaining = [], [], [], []
    rows = []
    for c in cases:
        gold = set(c.gold_edition_ids)
        rb, ra = b[c.case_id], f[c.case_id]
        rows.append(
            {
                "case_id": c.case_id,
                "family": c.family,
                "policy_dev_family": c.family in prior,
                "expected": c.expected,
                "gold": gold,
                "outcome": ra["outcome"],
                "suggested": ra["suggested"],
                "top1": ra["top1"],
            }
        )
        if ra["outcome"] == "suggest" and not correct(ra, gold):
            wrong.append(c.case_id)
        if correct(ra, gold) and not correct(rb, gold):
            gained.append(c.case_id)
        if correct(rb, gold) and not correct(ra, gold):
            lost.append(c.case_id)
        if c.expected == "suggest" and ra["outcome"] != "suggest":
            r = resolver.resolve(c.query)
            remaining.append({"case_id": c.case_id, "cause": cause([x.value for x in r.reasons])})

    out = {
        "label": "DEVELOPMENT EVIDENCE ONLY: same 60 human labels that motivated the change; "
        "not independent proof of improvement; not held-out; uncalibrated",
        "before": repo_relative(a.before),
        "after": repo_relative(a.after),
        "after_policy_version": POLICY_VERSION,
        "change": "conservative initials compatibility (only change between the runs)",
        "after_outcomes_identical_across_systems": identical,
        "gained_correct_suggestions": {"n": len(gained), "cases": gained},
        "lost_correct_suggestions": {"n": len(lost), "cases": lost},
        "wrong_suggestions_after": {"n": len(wrong), "cases": wrong},
        "remaining_reviews_on_human_edition_cases": {
            "n": len(remaining),
            "causes": dict(Counter(x["cause"] for x in remaining)),
            "cases": remaining,
        },
        "human_review_cases_still_review": sum(
            1 for r in rows if r["expected"] == "abstain" and r["outcome"] != "suggest"
        ),
        "human_review_cases": sum(1 for r in rows if r["expected"] == "abstain"),
        "metrics_after_default": {
            "all": metrics(rows),
            "never in the policy-development check": metrics(
                [r for r in rows if not r["policy_dev_family"]]
            ),
            "policy-development families": metrics([r for r in rows if r["policy_dev_family"]]),
        },
        "gained_by_pool": dict(
            Counter(
                "policy-dev"
                if c in {r["case_id"] for r in rows if r["policy_dev_family"]}
                else "never-policy-dev"
                for c in gained
            )
        ),
    }
    dest = a.after.parent / "comparison_vs_v1.json"
    dest.write_text(json.dumps(out, indent=1, default=sorted) + "\n")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
