"""Descriptive analysis of the single held-out run (data/eval/results/heldout40_frozen_r2).

    uv run python data/eval/heldout/analyze_heldout_eval.py

Reads ONLY the committed harness report, the held-out labels and the frozen queue. It re-runs
nothing and changes no label, policy, threshold, prompt, model or gate. Every rate carries
numerator/denominator, a case-level Wilson interval and a family-grouped bootstrap interval
(families resampled together; the same-author probe pair stays together). Uncalibrated.
Post-hoc breakdowns (by stratum, by review reason) are descriptive, not pre-registered tests.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bera.evalkit.cases import load_cases
from bera.evalkit.devanalysis import metrics, ratio
from bera.evalkit.families import load_frozen_queue

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "data/eval/results/heldout40_frozen_r2"
LABELS = ROOT / "data/eval/heldout/heldout_labels.jsonl"
QUEUE = ROOT / "data/eval/heldout/heldout_queue.jsonl"
FAMILIES = ROOT / "data/eval/heldout/heldout_families_supplement.json"
DEV = ROOT / "data/eval/results/dev60_human_policy_v2_amended/metrics.json"
DEFAULT = "2b_lexical_rrf"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    report = json.loads((RUN / "report.json").read_text())
    drafts = {d.draft_id: d for d in load_frozen_queue(QUEUE)[0]}
    cases = {c.case_id: c for c in load_cases(LABELS)}
    systems = report["systems"]

    def rows(key: str) -> list[dict[str, Any]]:
        out = []
        for r in systems[key]["per_case"]:
            c, d = cases[r["case_id"]], drafts[r["case_id"]]
            out.append(
                {
                    "case_id": c.case_id,
                    "family": d.family,
                    "stratum": d.stratum,
                    "expected": c.expected,
                    "reason": c.ambiguity_reason,
                    "gold": set(c.gold_edition_ids),
                    "outcome": r["outcome"],
                    "suggested": r["suggested"],
                    "top1": r["top1"],
                    "adj_status": r["adjudication_status"],
                    "adj_choice": r["adjudication_choice"],
                    "drafted_expected": d.proposed.expected,
                    "drafted_gold": set(d.proposed.gold_edition_ids),
                }
            )
        return out

    base = rows(DEFAULT)
    decisions = {
        k: [(r["case_id"], r["outcome"], r["suggested"]) for r in rows(k)] for k in systems
    }
    identical = all(v == decisions[DEFAULT] for v in decisions.values())

    by_stratum = {
        s: metrics([r for r in base if r["stratum"] == s])
        for s in sorted({r["stratum"] for r in base})
    }
    answerable_review = Counter(
        r["stratum"] for r in base if r["expected"] == "suggest" and r["outcome"] != "suggest"
    )
    ranking_failures = [
        {"stratum": r["stratum"], "outcome": r["outcome"]}
        for r in base
        if r["expected"] == "suggest" and r["top1"] not in r["gold"]
    ]

    def drafted_agree(r: dict[str, Any]) -> bool:
        if r["expected"] != r["drafted_expected"]:
            return False
        return r["expected"] == "abstain" or r["gold"] == r["drafted_gold"]

    llm = rows("6_routed_llm")
    inv = [r for r in llm if r["adj_status"] != "not_needed"]
    chose = [r for r in inv if r["adj_status"] == "completed" and r["adj_choice"]]
    advisory = {
        "invoked /N": ratio(llm, lambda r: r["adj_status"] != "not_needed", lambda r: True),
        "statuses_when_invoked": dict(Counter(r["adj_status"] for r in inv)),
        "invoked_by_human_label": dict(Counter(r["expected"] for r in inv)),
        "chose_a_candidate": len(chose),
        "choice_in_human_gold /chose": ratio(
            chose, lambda r: r["adj_choice"] in r["gold"], lambda r: True
        ),
        "choice_on_human_edition_cases_correct": ratio(
            chose, lambda r: r["adj_choice"] in r["gold"], lambda r: r["expected"] == "suggest"
        ),
        "chose_a_candidate_on_human_review_cases": sum(r["expected"] == "abstain" for r in chose),
        "choice_equals_top1": sum(r["adj_choice"] == r["top1"] for r in chose),
        "final_decisions_when_invoked": dict(Counter(r["outcome"] for r in inv)),
        "changed_a_final_decision_vs_default": sum(
            (a["outcome"], a["suggested"]) != (b["outcome"], b["suggested"])
            for a, b in zip(llm, base, strict=True)
        ),
        "note": "route gate closed (both routes); the LLM choice is advisory and never changed "
        "a final decision; final decisions equal the non-LLM configurations",
    }

    sys_table = {}
    for k, s in systems.items():
        m = s["metrics"]
        sys_table[k] = {
            "label": s["label"],
            "status": s["status"],
            "retrieval": m["retrieval"],
            "mrr": m["mrr"],
            "top1_accuracy": m["top1_accuracy"],
            "latency_ms": m["latency_ms"],
            "llm_invocations": m["adjudication"]["invocation_rate"],
            "llm_tokens_total": m["adjudication"]["tokens_total"],
            "llm_statuses": m["adjudication"]["statuses"],
        }

    dev = json.loads(DEV.read_text())["metrics_default_after_amendment"]["all"]
    out = {
        "label": "HELD-OUT, single run at bera-eval-freeze-2026-11-07-r2 (attempt 2; attempt 1 "
        "failed at load, 0 cases scored). One labeler; uncalibrated; descriptive.",
        "inputs": {
            str(p.relative_to(ROOT)): sha256(p)
            for p in [RUN / "report.json", LABELS, QUEUE, FAMILIES]
        },
        "counts": {
            "queries": len(base),
            "families": len({r["family"] for r in base}),
            "human_edition": sum(r["expected"] == "suggest" for r in base),
            "human_review": sum(r["expected"] == "abstain" for r in base),
            "human_review_reasons": dict(Counter(r["reason"] for r in base if r["reason"])),
            "skipped": 0,
            "disputed_or_flagged": 0,
            "excluded_exposed_or_practice": 0,
        },
        "final_decisions_identical_across_all_7_configurations": identical,
        "metrics_final_decisions": metrics(base),
        "metrics_by_stratum_post_hoc": by_stratum,
        "human_edition_cases_routed_to_review_by_stratum": dict(answerable_review),
        "ranking_failures_on_human_edition_cases": ranking_failures,
        "human_vs_drafted_proposal_agreement": {
            "value": ratio(base, drafted_agree, lambda r: True),
            "note": "measures the drafter, not system accuracy; proposals were never shown",
        },
        "advisory_llm_system6": advisory,
        "systems": sys_table,
        "dev60_amended_default_for_context": dev,
    }
    (RUN / "analysis.json").write_text(json.dumps(out, indent=1, default=sorted) + "\n")
    print(
        json.dumps(
            {
                k: out[k]
                for k in ("counts", "final_decisions_identical_across_all_7_configurations")
            },
            indent=1,
        )
    )
    for k, v in out["metrics_final_decisions"].items():
        print(
            k,
            v
            if not isinstance(v, dict)
            else (
                v["numerator"],
                v["denominator"],
                v["wilson95_case_level"],
                v["bootstrap95_family_grouped"],
            ),
        )
    for s, m in by_stratum.items():
        print(
            s,
            m["n_cases"],
            {k: (v["numerator"], v["denominator"]) for k, v in m.items() if isinstance(v, dict)},
        )
    print(
        "answerable->review by stratum",
        dict(answerable_review),
        "ranking failures",
        ranking_failures,
    )
    print(
        "drafter agreement", out["human_vs_drafted_proposal_agreement"]["value"]["numerator"], "/40"
    )
    print(json.dumps({k: v for k, v in advisory.items() if k != "note"}, default=str)[:1500])


if __name__ == "__main__":
    main()
