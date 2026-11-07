"""Measure LLM adjudication routes on DEVELOPMENT human labels -> frozen route evidence.

    uv run python scripts/measure_llm_routes.py \
        --report data/eval/results/dev60_human_policy_v1/report.json \
        --out data/eval/llm_route_evidence.json

Uses system 6's per-case adjudication results and the human labels. Development cases only;
any held-out case is refused. The route rule has no fitted parameters, so measuring it on
all development cases is equivalent to an out-of-fold measurement. The gate decision is
recomputed from the counts whenever the file is loaded (bera.llm.routes).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bera.evalkit.cases import load_cases
from bera.evalkit.run import repo_relative
from bera.llm.routes import gate_from_evidence, measure

ROOT = Path(__file__).resolve().parents[1]
LABELS = [
    ROOT / "data/eval/labels/dev_batch02_labels.jsonl",
    ROOT / "data/eval/labels/dev_final_labels.jsonl",
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    report = json.loads(a.report.read_text())
    cases = {c.case_id: c for lab in LABELS for c in load_cases(lab)}
    if any(c.split != "dev" for c in cases.values()):
        raise SystemExit("refusing: route evidence may only be measured on development cases")
    sys6 = report["systems"]["6_routed_llm"]
    if sys6["status"] != "ran":
        raise SystemExit("system 6 did not run in this report")
    rows = []
    for r in sys6["per_case"]:
        if r["adjudication_status"] == "completed" and r["adjudication_choice"]:
            c = cases[r["case_id"]]
            rows.append(
                {
                    "choice": r["adjudication_choice"],
                    "top1": r["top1"],
                    "expected": c.expected,
                    "gold": set(c.gold_edition_ids),
                }
            )
    evidence = measure(rows)
    evidence["source"] = {
        "report": repo_relative(a.report),
        "report_sha256": sha256(a.report),
        "labels": [{"path": repo_relative(x), "sha256": sha256(x)} for x in LABELS],
        "split": "dev",
        "completed_choices": len(rows),
        "note": "precision counts every completed choice on a route; a choice on a case the "
        "human sent to review is wrong. Constants were fixed before measurement.",
    }
    gate = gate_from_evidence(evidence, a.out.name)  # recomputed, never trusted from the file
    a.out.write_text(json.dumps(evidence, indent=1) + "\n")
    for route, c in evidence["routes"].items():
        print(
            f"{route}: n={c['n']} correct={c['correct']} wilson95={c['wilson95']} "
            f"open={c['open']} {c['closed_because']}"
        )
    print(f"open routes: {sorted(gate.open_routes) or 'none'}")


if __name__ == "__main__":
    main()
