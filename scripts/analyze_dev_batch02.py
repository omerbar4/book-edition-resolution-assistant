"""Error analysis of the seven configurations on dev batch 02 (20 human labels).

    uv run python scripts/analyze_dev_batch02.py --db var/catalog_v3.sqlite \
        --report data/eval/results/dev_batch02_human_policy_v1/report.json

DEVELOPMENT DATA, n=20, one labeler, uncalibrated policy; NOT a held-out estimate.
Reads the harness report and re-runs only the default lexical resolver (no models) to record
the reasons behind each outcome. Changes nothing: no policy, threshold, prompt or model.
Template names are deliberately omitted, so the analysis cannot teach a future labeler a
template-to-answer pattern. Agreement with drafted proposals is reported as drafter quality,
never as accuracy.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from bera.catalog import Catalog
from bera.evalkit.cases import EvalCase, load_cases
from bera.evalkit.families import load_frozen_queue, resolve_families
from bera.evalkit.metrics import wilson
from bera.policy import is_compatible
from bera.service import Resolver

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data/eval/labels/dev_batch02_labels.jsonl"
QUEUE = ROOT / "data/eval/drafts/dev_batch02.jsonl"
FAMILIES = ROOT / "data/corpus/v3_proposed/families.json"
DEV_CHECK = ROOT / "data/eval/dev_check_v3_synthetic.jsonl"
REPS = 1000

Row = dict[str, Any]


def ratio(rows: Sequence[Row], num: Callable[[Row], bool], den: Callable[[Row], bool]) -> Row:
    d = [r for r in rows if den(r)]
    k = sum(1 for r in d if num(r))
    n = len(d)
    return {
        "numerator": k,
        "denominator": n,
        "value": None if n == 0 else round(k / n, 4),
        "wilson95_case_level": wilson(k, n),
        "bootstrap95_family_grouped": grouped_bootstrap(rows, num, den),
    }


def grouped_bootstrap(
    rows: Sequence[Row], num: Callable[[Row], bool], den: Callable[[Row], bool]
) -> list[float] | None:
    fams: dict[str, list[Row]] = {}
    for r in rows:
        fams.setdefault(r["family"], []).append(r)
    keys = sorted(fams)
    rng = random.Random(0)
    vals = []
    for _ in range(REPS):
        sample = [r for k in (rng.choice(keys) for _ in keys) for r in fams[k]]
        d = [r for r in sample if den(r)]
        if d:
            vals.append(sum(1 for r in d if num(r)) / len(d))
    if not vals:
        return None
    vals.sort()
    return [
        round(vals[int(0.025 * (len(vals) - 1))], 4),
        round(vals[int(0.975 * (len(vals) - 1))], 4),
    ]


def metrics(rows: Sequence[Row]) -> Row:
    def answerable(r: Row) -> bool:
        return r["expected"] == "suggest"

    def correct(r: Row) -> bool:
        return r["outcome"] == "suggest" and r["suggested"] in r["gold"]

    def wrong(r: Row) -> bool:
        return r["outcome"] == "suggest" and r["suggested"] not in r["gold"]

    def everything(r: Row) -> bool:
        return True

    return {
        "n_cases": len(rows),
        "n_families": len({r["family"] for r in rows}),
        "correct_suggestion_rate /N": ratio(rows, correct, everything),
        "wrong_match_rate /N": ratio(rows, wrong, everything),
        "error_among_suggestions /S": ratio(rows, wrong, lambda r: r["outcome"] == "suggest"),
        "suggestion_coverage_on_answerable /A": ratio(rows, correct, answerable),
        "top1_accuracy /A": ratio(rows, lambda r: r["top1"] in r["gold"], answerable),
        "correct_abstention /U": ratio(
            rows, lambda r: r["outcome"] == "review", lambda r: r["expected"] == "abstain"
        ),
    }


def cause(reasons: list[str]) -> str:
    rs = set(reasons)
    if rs & {"undistinguished_alternative_unknown_fields", "multiple_consistent_candidates"}:
        return "undistinguished alternatives among retrieved candidates"
    if "catalog_scan_found_undistinguished_alternative" in rs:
        return "undistinguished alternative found by the catalog-wide scan"
    if "catalog_scan_incomplete" in rs:
        return "catalog scan incomplete"
    if rs & {"isbn_repair_hypothesis_only", "isbn_bad_checksum", "isbn_bad_format"}:
        return "damaged ISBN: repair is only a hypothesis"
    if "duplicate_isbn_mapping" in rs:
        return "ISBN maps to several records"
    if "field_conflict" in rs:
        return "a supplied field conflicts with the top candidate"
    if "insufficient_evidence" in rs:
        return "insufficient distinguishing evidence"
    return "other: " + ",".join(sorted(rs))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    report = json.loads(a.report.read_text())
    catalog = Catalog(a.db)
    drafts, queue_sha = load_frozen_queue(QUEUE)
    by_draft = {d.draft_id: d for d in drafts}
    cases: list[EvalCase] = resolve_families(
        load_cases(LABELS), drafts, json.loads(FAMILIES.read_text()), catalog
    )
    prior = {json.loads(x)["family"] for x in DEV_CHECK.read_text().splitlines() if x.strip()}

    systems = {k: v for k, v in report["systems"].items() if v["status"] == "ran"}
    per_sys: dict[str, list[Row]] = {}
    for key, s in systems.items():
        pc = {r["case_id"]: r for r in s["per_case"]}
        per_sys[key] = [
            {
                "case_id": c.case_id,
                "family": c.family,
                "prior_dev_family": c.family in prior,
                "expected": c.expected,
                "gold": set(c.gold_edition_ids),
                "outcome": pc[c.case_id]["outcome"],
                "suggested": pc[c.case_id]["suggested"],
                "top1": pc[c.case_id]["top1"],
            }
            for c in cases
        ]

    def same(field: Callable[[Row], object]) -> bool:
        return len({json.dumps([field(r) for r in rows]) for rows in per_sys.values()}) == 1

    identical_outcomes = same(lambda r: (r["outcome"], r["suggested"]))
    identical_top1 = same(lambda r: r["top1"])

    default = per_sys["2b_lexical_rrf"]
    groups = {
        "all": default,
        "prior_dev_families (also used in the 300-case policy-development check)": [
            r for r in default if r["prior_dev_family"]
        ],
        "other_dev_families": [r for r in default if not r["prior_dev_family"]],
    }

    resolver = Resolver(catalog, traces=None, provider=None)
    rows_out = []
    for c in cases:
        r = resolver.resolve(c.query)
        gold_rank = next(
            (x.rank for x in r.candidates if x.edition.edition_id in c.gold_edition_ids), None
        )
        compatible = [x for x in r.candidates if is_compatible(x)]
        alts = [
            x.edition.edition_id
            for x in compatible
            if x.edition.edition_id not in c.gold_edition_ids
        ]
        d = by_draft[c.case_id]
        agrees = c.expected == d.proposed.expected and set(c.gold_edition_ids) == set(
            d.proposed.gold_edition_ids
        )
        human_vs_policy = (
            "agree"
            if (c.expected == "suggest") == (r.outcome.value == "suggest")
            else "human edition, policy review"
            if c.expected == "suggest"
            else "human review, policy edition"
        )
        rows_out.append(
            {
                "case_id": c.case_id,
                "prior_dev_family": c.family in prior,
                "query_fields": sorted(c.query.model_dump(exclude_none=True)),
                "human": c.expected,
                "human_reason": c.ambiguity_reason,
                "policy_outcome": r.outcome.value,
                "route": r.route.value,
                "reasons": [x.value for x in r.reasons],
                "cause_if_review": None
                if r.outcome.value == "suggest"
                else cause([x.value for x in r.reasons]),
                "human_gold_rank": gold_rank,
                "compatible_candidates": len(compatible),
                "compatible_alternatives_to_human_gold": alts[:10],
                "human_vs_policy": human_vs_policy,
                "agrees_with_drafted_proposal": agrees,
            }
        )

    reviews_on_answerable = [
        x for x in rows_out if x["human_vs_policy"] == "human edition, policy review"
    ]
    llm = systems["6_routed_llm"]["metrics"]
    out = {
        "label": "DEVELOPMENT DATA, n=20 human labels (one labeler), uncalibrated policy "
        "conservative-rules-v1; NOT held-out performance; NOT calibrated",
        "labels": str(LABELS.relative_to(ROOT)),
        "queue_sha256": queue_sha,
        "family_source": "frozen queue draft family, cross-checked against families.json",
        "systems_ran": sorted(systems),
        "outcome_and_suggestion_identical_across_systems": identical_outcomes,
        "top1_identical_across_systems": identical_top1,
        "interval_note": (
            "wilson95_case_level treats cases as independent. bootstrap95_family_grouped "
            "resamples families (1000 reps, seed 0). Batch 02 has one case per family, so the "
            "grouped bootstrap equals a case bootstrap here; it cannot show uncertainty for "
            "0/n or n/n, so use the Wilson bound for zero-event rates."
        ),
        "metrics_default_2b_by_group": {k: metrics(v) for k, v in groups.items()},
        "llm": {
            "status": "advisory only: it can never turn review into suggest, so it cannot "
            "improve final coverage yet (validated LLM suggestion path unfinished)",
            "invocation_rate": llm["adjudication"]["invocation_rate"],
            "statuses": llm["adjudication"]["statuses"],
            "tokens_total": llm["adjudication"]["tokens_total"],
            "estimated_cost": llm["adjudication"]["estimated_cost"],
            "final_outcome_when_invoked": llm["adjudication"]["breakdown"][
                "final_outcome_when_invoked"
            ],
            "advisory_choice_in_gold": llm["adjudication"]["advisory_choice_in_gold"],
        },
        "latency_ms_total": {
            k: v["metrics"]["latency_ms"].get("total") for k, v in systems.items()
        },
        "latency_ms_stages_6_routed_llm": llm["latency_ms"],
        "review_causes_on_human_answerable": dict(
            Counter(x["cause_if_review"] for x in reviews_on_answerable)
        ),
        "drafter_agreement_not_accuracy": {
            "exact": sum(x["agrees_with_drafted_proposal"] for x in rows_out),
            "of": len(rows_out),
            "note": "agreement between the human and the program's drafted proposal (spec v2); "
            "measures the drafter, not any system",
        },
        "cases": rows_out,
    }
    dest = a.report.parent / "error_analysis.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=False, default=sorted) + "\n")
    print(f"wrote {dest}")
    (a.report.parent / "error_analysis.md").write_text(markdown(out))
    print(f"wrote {a.report.parent / 'error_analysis.md'}")


def _iv(v: object) -> str:
    return "n/a" if v is None else f"[{v[0]:.3f}, {v[1]:.3f}]"  # type: ignore[index]


FINDINGS = """
## Findings (hypotheses only; nothing was changed)

Every configuration produced the same outcome and suggestion on all 20 cases. The candidate
generators did not matter on this batch: in all 18 human-answerable cases the human's edition
was ranked first by every configuration. What limited coverage was the decision policy.

Causes of review on the 11 human-answerable cases (default configuration):

1. **Initials vs full author name (5).** For example a query author "S. Reynolds" against a
   record author "Sophia Reynolds". The author check returns UNKNOWN rather than AGREE, so a
   title + year match is "insufficient evidence". Hypothesis: an initials-consistent surname
   match could count as agreement. It is a feature change, and it would need fresh labels to
   validate.
2. **Checksum-invalid ISBN (4).** The repair is only a hypothesis, so the owner rule routes
   it to review, even when title/author/year agree with the repaired record. Synthetic label
   spec v2 discards a damaged ISBN and judges the remaining fields, so here the policy is
   stricter than the spec. Changing this is an owner decision.
3. **Catalog encoding damage trips the unicode guard (1).** The record's author contains a
   control character from mis-decoded UTF-8. That field was not even supplied by the query,
   whose ISBN maps uniquely to the record. Hypothesis: the guard should apply to query input
   and to fields actually compared, not to unrelated catalog fields. Owner decision.
4. **Unknown-format twin (1).** A second record with the same title, author and year has no
   format. Under the owner rule missing metadata is unknown, never distinguishing, so review
   is the rule-consistent outcome. The human chose the record whose format is known, so this
   case shows a human-vs-rule disagreement for the owner to rule on. The label is unchanged.

The 2 human abstentions were both routed to review (2/2).

**LLM.** The LLM was invoked on 2 of 20 cases and completed both. It is advisory only: it
can never turn review into suggest, so it cannot improve final coverage yet (the validated
LLM suggestion path is unfinished). Its choice equalled the top-1 candidate in both cases.

## What this does not show

- Not held-out performance; not calibrated; one labeler; n=20 (18 answerable, 2 abstain,
  0 out-of-corpus). Abstention quality is essentially untested.
- 0 wrong suggestions is not proof of safety: the case-level Wilson upper bound on the
  wrong-match rate is about 16%.
- The 8 prior-development families also appeared in the 300-case synthetic check that shaped
  policy v1, so those cases may be optimistic. The 12/8 split is too small to compare.
- Any change motivated by these 20 cases makes them development data for that change;
  improvement must be shown on fresh labels.
- Agreement with drafted proposals measures the drafter, not any system.
"""


def markdown(out: Row) -> str:
    lines = [
        "# Dev batch 02: seven configurations and error analysis",
        "",
        f"**{out['label']}**",
        "",
        f"Labels `{out['labels']}`; queue sha256 `{out['queue_sha256'][:16]}...`; families: "
        f"{out['family_source']}.",
        f"Outcome and suggestion identical across all {len(out['systems_ran'])} configurations: "
        f"{out['outcome_and_suggestion_identical_across_systems']}. Top-1 identical: "
        f"{out['top1_identical_across_systems']} (differs only on a human-abstain case).",
        "",
        f"_{out['interval_note']}_",
        "",
        "## Metrics (default configuration; identical outcomes in all configurations)",
        "",
        "N = all cases, A = human-answerable, S = system suggested, U = human abstain.",
        "",
        "| group | metric | k/n | value | Wilson 95% (case) | bootstrap 95% (family-grouped) |",
        "|---|---|---|---|---|---|",
    ]
    for g, m in out["metrics_default_2b_by_group"].items():
        name = g.split(" (")[0]
        for k, v in m.items():
            if not isinstance(v, dict):
                continue
            val = "n/a" if v["value"] is None else f"{v['value']:.3f}"
            lines.append(
                f"| {name} ({m['n_cases']}) | {k} | {v['numerator']}/{v['denominator']} | {val} "
                f"| {_iv(v['wilson95_case_level'])} | {_iv(v['bootstrap95_family_grouped'])} |"
            )
    llm = out["llm"]
    lines += [
        "",
        "## LLM, tokens, cost",
        "",
        f"- {llm['status']}.",
        f"- Invoked {llm['invocation_rate']['numerator']}/{llm['invocation_rate']['denominator']}"
        f"; statuses {llm['statuses']}; final outcome when invoked "
        f"{llm['final_outcome_when_invoked']}.",
        f"- Advisory choice in human gold: {llm['advisory_choice_in_gold']['numerator']}/"
        f"{llm['advisory_choice_in_gold']['denominator']}.",
        f"- Tokens total: {llm['tokens_total']}. Estimated cost: "
        f"${llm['estimated_cost']['value']:.2f} ({llm['estimated_cost']['note']}).",
        "",
        "## Latency (ms, end to end per query)",
        "",
        "| configuration | p50 | p95 |",
        "|---|---|---|",
    ]
    for k, v in out["latency_ms_total"].items():
        lines.append(f"| {k} | {v['p50']} | {v['p95']} |")
    lines += [
        "",
        "Configuration 6 p95 is dominated by local LLM adjudication (2 invocations).",
        "",
        "## Per case (default configuration)",
        "",
        "| case | prior-dev family | query fields | human | policy | route | cause of review |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in out["cases"]:
        lines.append(
            f"| {c['case_id']} | {'yes' if c['prior_dev_family'] else 'no'} | "
            f"{', '.join(c['query_fields'])} | {c['human']}"
            f"{' (' + c['human_reason'] + ')' if c['human_reason'] else ''} | "
            f"{c['policy_outcome']} | {c['route']} | {c['cause_if_review'] or ''} |"
        )
    d = out["drafter_agreement_not_accuracy"]
    lines += [
        "",
        "## Drafter agreement (not accuracy)",
        "",
        f"The human matched the program's drafted proposal exactly on {d['exact']}/{d['of']}. "
        f"{d['note']}.",
        FINDINGS,
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
