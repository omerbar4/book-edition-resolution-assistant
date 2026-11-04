"""Explain every unsupported suggestion in a DEVELOPMENT engineering-check report.

An "unsupported suggestion" is a SUGGEST on a case whose synthetic gold says abstain because
several editions fit. For each one this re-runs the systems that suggested it (no LLM: the
LLM is advisory and cannot turn REVIEW into SUGGEST) and records the route, the reasons, and
how each OTHER fitting edition was judged field by field. Gold labels are never modified.

Refuses any report or case file containing held-out cases.

    uv run python scripts/analyze_dev_check_suggestions.py \
        --report data/eval/results/dev_check_v3/report.json \
        --cases data/eval/dev_check_v3_synthetic.jsonl --db var/catalog_v3.sqlite \
        --out data/eval/results/dev_check_v3/unsupported_suggestions.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from bera.catalog import Catalog
from bera.evalkit.cases import EvalCase
from bera.evalkit.perturb import _fit
from bera.evalkit.run import SYSTEMS, RunEnv
from bera.service import Resolver


def known_differences(twin: dict[str, Any], holder: Any) -> list[str]:
    """Fields KNOWN on both the twin and the suggested (ISBN-holding) edition that differ.
    'mul'/'und' language codes are not treated as a difference."""
    out = []
    if twin["year"] and holder.publish_year and twin["year"] != holder.publish_year:
        out.append("publish_year")
    a, b = (twin["subtitle"] or "").casefold(), (holder.subtitle or "").casefold()
    if a and b and a != b:
        out.append("subtitle")
    vague = {"mul", "und"}
    la, lb = set(twin["languages"]) - vague, set(holder.languages) - vague
    if la and lb and la != lb:
        out.append("language")
    fa, fb = twin["format"], holder.physical_format.value
    if fa not in ("unknown", "other") and fb not in ("unknown", "other") and fa != fb:
        out.append("physical_format")
    return out


def classify(route: str, twins: list[dict[str, Any]]) -> tuple[str, str]:
    """Bucket by mechanism. No bucket changes any label; buckets marked gold_question are
    questions for the owner, not corrections."""
    if route == "isbn_exact":
        if all(t["known_differences_vs_suggested"] for t in twins):
            return (
                "isbn_exact__gold_question_twins_known_distinct",
                "Valid ISBN maps to exactly one record. Every other 'fitting' edition has no "
                "ISBN, but it differs from the ISBN-holding record on a field known on both "
                "(year/subtitle/language/format). The fit rule compares twins only to the "
                "query, so the gold set may be broader than the evidence supports.",
            )
        if any(t["mul_or_und_language_only"] for t in twins) and not any(
            t["no_known_difference"] for t in twins
        ):
            return (
                "isbn_exact__undecided_language_code_only",
                "A twin differs from the ISBN holder only by a vague language code (mul/und).",
            )
        return (
            "isbn_exact__rule_conflict_possible_duplicate_record",
            "At least one twin has no ISBN and no known field that differs from the ISBN "
            "holder; it may be a duplicate record of the same edition (an acceptable-set "
            "case) or a different edition. Abstain is the gold under the unknown-is-"
            "compatible rule; the policy's ISBN rule suggests. Owner decision.",
        )
    if any(not t["in_candidates"] for t in twins):
        return (
            "policy_error_fitting_edition_not_retrieved",
            "Retrieval route: another fitting edition was not in the candidate list, so "
            "'exactly one consistent candidate' was judged on an incomplete list.",
        )
    if twins and all(t["excluded_by_unknown_only"] for t in twins):
        fields = sorted({f for t in twins for f in t["excluded_by"]})
        return (
            "policy_error_unknown_treated_as_disagreement",
            f"Retrieval route excluded every other fitting edition only because {fields} "
            "was UNKNOWN on it (consistency requires AGREE); this contradicts the rule that "
            "unknown metadata is never distinguishing.",
        )
    return ("unclassified", "needs manual review")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    report = json.loads(a.report.read_text())
    if report.get("splits_in_cases") != ["dev"]:
        raise SystemExit("refusing: report is not dev-only")
    cases = {}
    for line in a.cases.read_text().splitlines():
        if line.strip():
            c = EvalCase.model_validate_json(line)
            if c.split != "dev":
                raise SystemExit(f"refusing: {c.case_id} is not a dev case")
            cases[c.case_id] = c

    by_case: dict[str, dict[str, str]] = defaultdict(dict)
    for sid, s in report["systems"].items():
        for pc in s["per_case"]:
            c = cases[pc["case_id"]]
            if pc["outcome"] == "suggest" and c.expected == "abstain":
                by_case[pc["case_id"]][sid] = pc["suggested"]

    catalog = Catalog(a.db)
    env = RunEnv(enable_ml=True)
    specs = {s.key: s for s in SYSTEMS}
    resolvers: dict[str, Resolver] = {}

    def resolver(sid: str) -> Resolver:
        if sid not in resolvers:
            key = "5_hybrid_rerank" if sid == "6_routed_llm" else sid
            comp = specs[key].build(catalog, env)
            resolvers[sid] = Resolver(
                catalog,
                traces=None,
                provider=None,
                retrievers=comp.retrievers,
                reranker=comp.reranker,
            )
        return resolvers[sid]

    out = []
    for cid, systems in sorted(by_case.items()):
        c = cases[cid]
        sid = "2b_lexical_rrf" if "2b_lexical_rrf" in systems else sorted(systems)[0]
        r = resolver(sid).resolve(c.query)
        if r.suggested_edition_id != systems[sid]:
            raise SystemExit(f"{cid}: re-run of {sid} did not reproduce the report")
        views = {v.edition.edition_id: v for v in r.candidates}
        eds = catalog.get(c.gold_edition_ids)
        holder = catalog.get([r.suggested_edition_id])[r.suggested_edition_id]
        fields = c.query.model_dump(exclude_none=True)
        twins = []
        for gid in c.gold_edition_ids:
            if gid == r.suggested_edition_id:
                continue
            v = views.get(gid)
            checks = {ch.field: ch.status.value for ch in v.checks} if v else None
            not_agree = sorted(
                k for k in ("title", "author") if checks and checks.get(k) != "agree"
            )
            disagree = sorted(k for k, s in (checks or {}).items() if s == "disagree")
            excl = sorted(set(not_agree) | set(disagree))
            twins.append(
                {
                    "edition_id": gid,
                    "in_candidates": v is not None,
                    "fit_to_query": _fit(fields, eds[gid]),
                    "checks": checks,
                    "excluded_by": excl if v else ["not_retrieved"],
                    "excluded_by_unknown_only": bool(v) and not disagree and bool(excl),
                    "title": eds[gid].title,
                    "subtitle": eds[gid].subtitle,
                    "authors": list(eds[gid].authors),
                    "format": str(eds[gid].physical_format),
                    "year": eds[gid].publish_year,
                    "isbns": list(eds[gid].isbn_13 + eds[gid].isbn_10),
                    "edition_name": eds[gid].edition_name,
                    "publishers": list(eds[gid].publishers or []),
                    "languages": list(eds[gid].languages or []),
                }
            )
        for t in twins:
            t["known_differences_vs_suggested"] = known_differences(t, holder)
            t["no_known_difference"] = not t["known_differences_vs_suggested"]
            t["mul_or_und_language_only"] = (
                t["no_known_difference"]
                and bool(set(t["languages"]) & {"mul", "und"})
                and set(t["languages"]) != set(holder.languages)
            )
            if t["mul_or_und_language_only"]:
                t["no_known_difference"] = False
        bucket, why = classify(r.route.value, twins)
        out.append(
            {
                "case_id": cid,
                "systems_suggesting": sorted(systems),
                "n_systems": len(systems),
                "rerun_system": sid,
                "route": r.route.value,
                "reasons": [x.value for x in r.reasons],
                "query": fields,
                "perturbation": c.perturbation,
                "gold_size": len(c.gold_edition_ids),
                "ambiguity_reason": c.ambiguity_reason,
                "suggested": r.suggested_edition_id,
                "twins": twins,
                "bucket": bucket,
                "explanation": why,
            }
        )
    per_system = {
        sid: Counter(o["bucket"] for o in out if sid in o["systems_suggesting"])
        for sid in report["systems"]
    }
    result = {
        "label": "DEVELOPMENT ENGINEERING CHECK on synthetic cases; gold labels unchanged; "
        "no held-out cases; not an evaluation",
        "distinct_cases": len(out),
        "by_bucket": Counter(o["bucket"] for o in out),
        "per_system": per_system,
        "cases": out,
    }
    a.out.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str))
    print(
        json.dumps(
            {k: result[k] for k in ("distinct_cases", "by_bucket", "per_system")},
            indent=1,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
