"""Dev-only evaluation analysis: 60 human-labeled development cases (batch 02 + dev_final).

    uv run python scripts/analyze_dev_eval.py --db var/catalog_v3.sqlite \
        --report data/eval/results/dev60_human_policy_v1/report.json

DEVELOPMENT DATA, one labeler, uncalibrated policy; NOT held-out performance. Reads the
harness report and re-runs only the default lexical resolver (no models) to record each
outcome's reasons. It changes no label, policy, threshold, prompt or model.

Disagreements are reported separately and never "fixed":
  A. human label vs drafted proposal (measures the drafter, not accuracy);
  B. human label vs policy outcome (edition vs review);
  C. open owner-review flags.

Deliberately deferred until held-out labeling is complete: per-stratum and per-template
summaries of human answers. Held-out cases use the same templates and strata, so those
summaries could bias held-out labels.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bera.catalog import Catalog
from bera.evalkit.cases import EvalCase, load_cases
from bera.evalkit.devanalysis import cause, metrics
from bera.evalkit.families import load_frozen_queue, resolve_families
from bera.policy import is_compatible
from bera.service import Resolver

ROOT = Path(__file__).resolve().parents[1]
LABELS = [
    ROOT / "data/eval/labels/dev_batch02_labels.jsonl",
    ROOT / "data/eval/labels/dev_final_labels.jsonl",
]
QUEUES = [ROOT / "data/eval/drafts/dev_batch02.jsonl", ROOT / "data/eval/drafts/dev_final.jsonl"]
B03 = ROOT / "data/eval/drafts/dev_batch03.jsonl"
FAMILIES = ROOT / "data/corpus/v3_proposed/families.json"
DEV_CHECK = ROOT / "data/eval/dev_check_v3_synthetic.jsonl"

Row = dict[str, Any]


def flags() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for lab in LABELS:
        p = lab.with_name(lab.stem + ".review_flags.jsonl")
        if p.exists():
            for x in p.read_text().splitlines():
                if x.strip():
                    r = json.loads(x)
                    if r.get("status") == "open_owner_review":
                        out.setdefault(r["case_id"], []).append(r["issue"])
    return out


def proposal_category(c: EvalCase, expected: str, gold: list[str]) -> str:
    if c.expected == expected and set(c.gold_edition_ids) == set(gold):
        return "agree"
    if c.expected == "suggest" and expected == "suggest":
        return "both edition, different record"
    if c.expected == "suggest":
        return "human edition, proposal review"
    if expected == "suggest":
        return "human review, proposal edition"
    return "both review, different listed records"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    report = json.loads(a.report.read_text())
    catalog = Catalog(a.db)
    drafts = []
    queue_sha = {}
    for q in QUEUES:
        ds, sha = load_frozen_queue(q)
        drafts.extend(ds)
        queue_sha[str(q.relative_to(ROOT))] = sha
    by_draft = {d.draft_id: d for d in drafts}
    b03_ids = {json.loads(x)["draft_id"] for x in B03.read_text().splitlines() if x.strip()}
    raw = [c for lab in LABELS for c in load_cases(lab)]
    cases = resolve_families(raw, drafts, json.loads(FAMILIES.read_text()), catalog)
    prior = {json.loads(x)["family"] for x in DEV_CHECK.read_text().splitlines() if x.strip()}
    open_flags = flags()

    def source(cid: str) -> str:
        if cid.startswith("d02-"):
            return "batch02"
        return "batch03" if cid in b03_ids else "stratified"

    systems = {k: v for k, v in report["systems"].items() if v["status"] == "ran"}
    per_sys: dict[str, list[Row]] = {}
    for key, s in systems.items():
        pc = {r["case_id"]: r for r in s["per_case"]}
        per_sys[key] = [
            {
                "case_id": c.case_id,
                "family": c.family,
                "policy_dev_family": c.family in prior,
                "source": source(c.case_id),
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

    def same(key: str) -> bool:
        return len({json.dumps([r[key] for r in rows]) for rows in per_sys.values()}) == 1

    default = per_sys["2b_lexical_rrf"]
    groups = {
        "all": default,
        "never in the policy-development check": [r for r in default if not r["policy_dev_family"]],
        "policy-development families (reported separately)": [
            r for r in default if r["policy_dev_family"]
        ],
    }

    resolver = Resolver(catalog, traces=None, provider=None)
    rows_out = []
    for c in cases:
        r = resolver.resolve(c.query)
        d = by_draft[c.case_id]
        compatible = [x for x in r.candidates if is_compatible(x)]
        gold_rank = next(
            (x.rank for x in r.candidates if x.edition.edition_id in c.gold_edition_ids), None
        )
        hv = (
            "agree"
            if (c.expected == "suggest") == (r.outcome.value == "suggest")
            else "human edition, policy review"
            if c.expected == "suggest"
            else "human review, policy edition"
        )
        rows_out.append(
            {
                "case_id": c.case_id,
                "policy_dev_family": c.family in prior,
                "query_fields": sorted(c.query.model_dump(exclude_none=True)),
                "human": c.expected,
                "human_reason": c.ambiguity_reason,
                "human_gold_count": len(c.gold_edition_ids),
                "policy_outcome": r.outcome.value,
                "route": r.route.value,
                "reasons": [x.value for x in r.reasons],
                "cause_if_review": None
                if r.outcome.value == "suggest"
                else cause([x.value for x in r.reasons]),
                "human_gold_rank": gold_rank,
                "compatible_candidates": len(compatible),
                "human_vs_policy": hv,
                "human_vs_proposal": proposal_category(
                    c, d.proposed.expected, d.proposed.gold_edition_ids
                ),
                "open_review_flags": open_flags.get(c.case_id, []),
            }
        )

    llm_rows = per_sys["6_routed_llm"]
    completed = [r for r in llm_rows if r["adj_status"] == "completed" and r["adj_choice"]]
    agree_route = [r for r in completed if r["adj_choice"] == r["top1"]]
    override_route = [r for r in completed if r["adj_choice"] != r["top1"]]
    llm = systems["6_routed_llm"]["metrics"]["adjudication"]

    def correct_choice(rs: list[Row]) -> dict[str, int]:
        ans = [r for r in rs if r["expected"] == "suggest"]
        return {
            "answerable": len(ans),
            "choice_in_human_gold": sum(r["adj_choice"] in r["gold"] for r in ans),
        }

    reviews = [x for x in rows_out if x["human_vs_policy"] == "human edition, policy review"]
    out = {
        "label": "DEVELOPMENT DATA: 60 human labels (one labeler), uncalibrated policy "
        "conservative-rules-v1; NOT held-out performance; NOT calibrated",
        "case_files": [str(x.relative_to(ROOT)) for x in LABELS],
        "queues": queue_sha,
        "counts": {
            "cases": len(cases),
            "families": len({c.family for c in cases}),
            "human_edition": sum(c.expected == "suggest" for c in cases),
            "human_review": sum(c.expected == "abstain" for c in cases),
            "human_review_reasons": dict(
                Counter(c.ambiguity_reason for c in cases if c.ambiguity_reason)
            ),
        },
        "outcome_and_suggestion_identical_across_systems": same("outcome") and same("suggested"),
        "top1_identical_across_systems": same("top1"),
        "interval_note": (
            "wilson95_case_level treats cases as independent; bootstrap95_family_grouped "
            "resamples families with all their queries (1000 reps, seed 0). Every case here is "
            "from a distinct family. Bootstrap cannot show uncertainty for 0/n or n/n; use the "
            "Wilson bound for zero-event rates."
        ),
        "metrics_default_2b_by_group": {k: metrics(v) for k, v in groups.items()},
        "review_causes_on_human_answerable": dict(Counter(x["cause_if_review"] for x in reviews)),
        "disagreements": {
            "A_human_vs_drafted_proposal": {
                "note": "measures the drafter; labels are never changed to match proposals",
                "counts": dict(Counter(x["human_vs_proposal"] for x in rows_out)),
                "cases": {
                    k: [x["case_id"] for x in rows_out if x["human_vs_proposal"] == k]
                    for k in sorted({x["human_vs_proposal"] for x in rows_out} - {"agree"})
                },
            },
            "B_human_vs_policy": {
                "counts": dict(Counter(x["human_vs_policy"] for x in rows_out)),
                "cases": {
                    k: [x["case_id"] for x in rows_out if x["human_vs_policy"] == k]
                    for k in sorted({x["human_vs_policy"] for x in rows_out} - {"agree"})
                },
            },
            "C_open_review_flags": open_flags,
        },
        "llm": {
            "status": "advisory only in conservative-rules-v1: it cannot turn review into "
            "suggest, so it cannot raise final coverage",
            "invocation_rate": llm["invocation_rate"],
            "statuses": llm["statuses"],
            "tokens_total": llm["tokens_total"],
            "estimated_cost": llm["estimated_cost"],
            "final_outcome_when_invoked": llm["breakdown"]["final_outcome_when_invoked"],
            "routes": {
                "completed_with_choice": len(completed),
                "agree_with_top1": len(agree_route),
                "override_top1": len(override_route),
                "agree_route_choice_correctness": correct_choice(agree_route),
                "override_route_choice_correctness": correct_choice(override_route),
            },
        },
        "latency_ms_total": {
            k: v["metrics"]["latency_ms"].get("total") for k, v in systems.items()
        },
        "deferred": "per-stratum, per-template and per-source-batch summaries of human answers: "
        "withheld until held-out labeling is complete (held-out uses the same templates and "
        "strata, so those base rates could bias held-out labels)",
        "cases": rows_out,
    }
    dest = a.report.parent / "error_analysis.json"
    dest.write_text(json.dumps(out, indent=1, default=sorted) + "\n")
    print(f"wrote {dest}")
    (a.report.parent / "error_analysis.md").write_text(markdown(out))
    print(f"wrote {a.report.parent / 'error_analysis.md'}")


def _iv(v: object) -> str:
    return "n/a" if v is None else f"[{v[0]:.3f}, {v[1]:.3f}]"  # type: ignore[index]


def markdown(out: Row) -> str:
    c = out["counts"]
    L = [
        "# Dev evaluation (60 human labels) and error analysis",
        "",
        f"**{out['label']}**",
        "",
        f"{c['cases']} cases from {c['families']} distinct families: {c['human_edition']} "
        f"human edition choices, {c['human_review']} human review (reasons: "
        f"{c['human_review_reasons']}).",
        f"Outcome and suggestion identical across all configurations: "
        f"{out['outcome_and_suggestion_identical_across_systems']}; top-1 identical: "
        f"{out['top1_identical_across_systems']}.",
        "",
        f"_{out['interval_note']}_",
        "",
        "## Metrics (default configuration; outcomes identical in all configurations)",
        "",
        "N = all, A = human edition, S = system suggested, U = human review.",
        "",
        "| group | metric | k/n | value | Wilson 95% (case) | bootstrap 95% (family) |",
        "|---|---|---|---|---|---|",
    ]
    for g, m in out["metrics_default_2b_by_group"].items():
        for k, v in m.items():
            if isinstance(v, dict):
                val = "n/a" if v["value"] is None else f"{v['value']:.3f}"
                L.append(
                    f"| {g} ({m['n_cases']} q / {m['n_families']} fam) | {k} | "
                    f"{v['numerator']}/{v['denominator']} | {val} | "
                    f"{_iv(v['wilson95_case_level'])} | {_iv(v['bootstrap95_family_grouped'])} |"
                )
    d = out["disagreements"]
    llm = out["llm"]
    L += [
        "",
        "## Why human-answerable cases went to review (default configuration)",
        "",
        *[f"- {k}: {v}" for k, v in out["review_causes_on_human_answerable"].items()],
        "",
        "## Disagreements (reported separately; no label was changed)",
        "",
        f"- A. Human vs drafted proposal ({d['A_human_vs_drafted_proposal']['note']}): "
        f"{d['A_human_vs_drafted_proposal']['counts']}",
        f"- B. Human vs policy outcome: {d['B_human_vs_policy']['counts']}",
        f"- C. Open owner-review flags: {d['C_open_review_flags']}",
        "",
        "Case ids for A and B are in error_analysis.json.",
        "",
        "## LLM (advisory), tokens, cost",
        "",
        f"- {llm['status']}.",
        f"- Invoked {llm['invocation_rate']['numerator']}/{llm['invocation_rate']['denominator']};"
        f" statuses {llm['statuses']}; final outcome when invoked "
        f"{llm['final_outcome_when_invoked']}.",
        f"- Routes: {llm['routes']}.",
        f"- Tokens {llm['tokens_total']}; estimated cost ${llm['estimated_cost']['value']:.2f} "
        "(local).",
        "",
        "## Latency p50/p95 (ms per query)",
        "",
        *[f"- {k}: {v['p50']} / {v['p95']}" for k, v in out["latency_ms_total"].items()],
        "",
        "## Per case (default configuration)",
        "",
        "| case | policy-dev family | query fields | human | policy | route | cause of review "
        "| vs proposal |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for x in out["cases"]:
        L.append(
            f"| {x['case_id']} | {'yes' if x['policy_dev_family'] else 'no'} | "
            f"{', '.join(x['query_fields'])} | {x['human']}"
            f"{' (' + x['human_reason'] + ')' if x['human_reason'] else ''} | "
            f"{x['policy_outcome']} | {x['route']} | {x['cause_if_review'] or ''} | "
            f"{x['human_vs_proposal']} |"
        )
    L += [
        "",
        "## Not shown on purpose",
        "",
        f"{out['deferred']}.",
        "",
        "## Limits",
        "",
        "- Development data, one labeler, uncalibrated policy; not held-out performance.",
        "- 0 wrong suggestions is not proof of safety; read the Wilson upper bounds.",
        "- Policy-development families may be optimistic and are reported separately.",
        "- Any change motivated by these cases makes them development data for that change.",
    ]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
