"""Run the six-system comparison on a case file and write a JSON + Markdown report.

    uv run python -m bera.evalkit.run --cases data/eval/synthetic_cases.jsonl --split dev \
        --out reports/synthetic-dev

Every system shares the ISBN stage, the deterministic field checks and the same policy;
they differ in candidate generation (and later in reranking and adjudication). Systems
whose components are not yet available are reported as BLOCKED with a reason. They are
never simulated.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from bera.catalog import Catalog
from bera.config import Settings
from bera.evalkit.cases import EvalCase, load_cases
from bera.evalkit.metrics import CaseResult, compute
from bera.models import AdjudicationStatus
from bera.retrieval import FtsBm25Retriever, FuzzyScanRetriever, Retriever, TrigramRetriever
from bera.service import Resolver


@dataclass(frozen=True)
class SystemSpec:
    key: str
    label: str
    make_retrievers: Callable[[Catalog], list[Retriever]] | None
    blocked_reason: str | None = None


SYSTEMS: list[SystemSpec] = [
    SystemSpec(
        "1_exact_fuzzy", "Exact identifier + fuzzy matching", lambda c: [FuzzyScanRetriever(c)]
    ),
    SystemSpec("2_lexical", "Lexical retrieval (FTS5 BM25)", lambda c: [FtsBm25Retriever(c)]),
    SystemSpec(
        "2b_lexical_rrf",
        "Lexical BM25 + trigram, RRF (current default)",
        lambda c: [FtsBm25Retriever(c), TrigramRetriever(c)],
    ),
    SystemSpec(
        "3_embedding", "Embedding retrieval", None, "blocked: embedding model download not approved"
    ),
    SystemSpec(
        "4_hybrid",
        "Hybrid lexical + embedding (RRF)",
        None,
        "blocked: embedding model download not approved",
    ),
    SystemSpec(
        "5_hybrid_rerank",
        "Hybrid + cross-encoder reranker",
        None,
        "blocked: embedding and reranker downloads not approved",
    ),
    SystemSpec(
        "6_routed_llm",
        "Routed LLM adjudication over retrieved candidates",
        None,
        "blocked: local LLM weights not approved (mock provider is a test double, "
        "not a system to evaluate)",
    ),
]


def run_system(spec: SystemSpec, catalog: Catalog, cases: Sequence[EvalCase]) -> list[CaseResult]:
    assert spec.make_retrievers is not None
    resolver = Resolver(
        catalog, traces=None, provider=None, retrievers=spec.make_retrievers(catalog)
    )
    results = []
    for c in cases:
        r = resolver.resolve(c.query)
        top = r.candidates[0] if r.candidates else None
        adj = r.adjudication
        results.append(
            CaseResult(
                case_id=c.case_id,
                family=c.family,
                expected=c.expected,
                gold=frozenset(c.gold_edition_ids),
                ranked_ids=[x.edition.edition_id for x in r.candidates],
                outcome=r.outcome.value,
                suggested=r.suggested_edition_id,
                timings_ms=r.timings_ms,
                adjudication_status=adj.status.value,
                adjudication_choice=adj.chosen_edition_id
                if adj.status is AdjudicationStatus.COMPLETED
                else None,
                input_tokens=adj.input_tokens or 0,
                output_tokens=adj.output_tokens or 0,
                signal=None if top is None else float(top.agreements - 2 * top.conflicts),
            )
        )
    return results


def evaluate(
    catalog: Catalog, cases: Sequence[EvalCase], reps: int = 1000, seed: int = 0
) -> dict[str, object]:
    synthetic_catalog = catalog.meta().get("all_synthetic") == "True"
    synthetic_cases = all(c.origin == "synthetic_perturbation" for c in cases)
    report: dict[str, object] = {
        "label": "ENGINEERING CHECK ON SYNTHETIC DATA. NOT A REAL-WORLD EVALUATION."
        if synthetic_catalog or synthetic_cases
        else "evaluation",
        "catalog_meta": catalog.meta(),
        "cases": len(cases),
        "human_labeled_cases": sum(c.human_labeled for c in cases),
        "confidence_note": "signal = top-1 agreements - 2*conflicts: an UNCALIBRATED ranking "
        "signal; buckets and risk-coverage use it, not a probability",
        "systems": {},
    }
    systems: dict[str, object] = {}
    for spec in SYSTEMS:
        if spec.blocked_reason:
            systems[spec.key] = {"label": spec.label, "status": spec.blocked_reason}
            continue
        res = run_system(spec, catalog, cases)
        systems[spec.key] = {
            "label": spec.label,
            "status": "ran",
            "metrics": compute(res, reps=reps, seed=seed),
            "per_case": [
                {
                    "case_id": r.case_id,
                    "outcome": r.outcome,
                    "suggested": r.suggested,
                    "top1": r.ranked_ids[0] if r.ranked_ids else None,
                }
                for r in res
            ],
        }
    report["systems"] = systems
    return report


def _fmt(m: object) -> str:
    if isinstance(m, dict) and "value" in m:
        v = m["value"]
        den = m.get("denominator")
        return "n/a" if v is None else f"{v:.3f} ({m.get('numerator', '?')}/{den})"
    return str(m)


def markdown(report: dict[str, object]) -> str:
    lines = [
        f"# Evaluation report\n\n**{report['label']}**\n",
        f"Cases: {report['cases']} (human-labeled: {report['human_labeled_cases']})\n",
        f"_{report['confidence_note']}_\n",
        "| system | status | top-1 | recall@10 | MRR | correct sugg. /N | wrong match /N "
        "| error among sugg. | correct abstain | p95 total ms |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    systems = report["systems"]
    assert isinstance(systems, dict)
    for s in systems.values():
        if s["status"] != "ran":
            lines.append(f"| {s['label']} | {s['status']} | | | | | | | | |")
            continue
        m = s["metrics"]
        lines.append(
            f"| {s['label']} | ran | {_fmt(m['top1_accuracy'])} | "
            f"{_fmt(m['retrieval']['recall@10'])} | {m['mrr']['value']} | "
            f"{_fmt(m['correct_suggestion_rate'])} | {_fmt(m['wrong_match_rate'])} | "
            f"{_fmt(m['error_among_suggestions'])} | {_fmt(m['correct_abstention_rate'])} | "
            f"{m['latency_ms'].get('total', {}).get('p95')} |"
        )
    lines.append(
        "\nFull metrics, categories, bootstrap intervals and risk-coverage points are in "
        "the JSON report."
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - thin CLI
    p = argparse.ArgumentParser(prog="bera-eval")
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--split", choices=["dev", "heldout", "all"], default="dev")
    p.add_argument("--db", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--reps", type=int, default=1000)
    a = p.parse_args(argv)
    cases = [c for c in load_cases(a.cases) if a.split == "all" or c.split == a.split]
    catalog = Catalog(a.db or Settings.from_env().catalog_db)
    report = evaluate(catalog, cases, reps=a.reps)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    (a.out / "report.md").write_text(markdown(report))
    print(markdown(report))


if __name__ == "__main__":  # pragma: no cover
    main()
