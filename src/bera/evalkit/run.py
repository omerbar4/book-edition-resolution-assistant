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
from bera.config import REPO_ROOT, Settings
from bera.evalkit.cases import EvalCase, load_cases
from bera.evalkit.metrics import CaseResult, compute
from bera.llm.provider import LLMProvider
from bera.models import AdjudicationStatus
from bera.retrieval import (
    FtsBm25Retriever,
    FuzzyScanRetriever,
    Reranker,
    Retriever,
    TrigramRetriever,
)
from bera.service import Resolver


class Blocked(Exception):
    """A system's components are unavailable for this run; it is reported, never simulated."""


@dataclass(frozen=True)
class RunEnv:
    enable_ml: bool = False
    cache_dir: Path = Path("var/cache")
    provider: LLMProvider | None = None  # real local provider for system 6, if running


@dataclass(frozen=True)
class Components:
    retrievers: list[Retriever]
    reranker: Reranker | None = None
    provider: LLMProvider | None = None


@dataclass(frozen=True)
class SystemSpec:
    key: str
    label: str
    build: Callable[[Catalog, RunEnv], Components]


def _embedding(catalog: Catalog, env: RunEnv) -> Retriever:
    if not env.enable_ml:
        raise Blocked("blocked: ML systems not enabled for this run (use --ml)")
    try:
        from bera.ml import EmbeddingRetriever, locked_model
    except ImportError as exc:  # pragma: no cover - depends on installed groups
        raise Blocked("blocked: ml dependency group not installed") from exc
    model = locked_model("embedding")
    if model is None:
        raise Blocked("blocked: pinned embedding model not present in ./models")
    return EmbeddingRetriever(catalog, model, env.cache_dir)


def _reranker(env: RunEnv) -> Reranker:
    from bera.ml import CrossEncoderReranker, locked_model

    model = locked_model("reranker")
    if model is None:
        raise Blocked("blocked: pinned reranker model not present in ./models")
    return CrossEncoderReranker(model)


def _hybrid(c: Catalog, env: RunEnv) -> list[Retriever]:
    return [FtsBm25Retriever(c), TrigramRetriever(c), _embedding(c, env)]


def _routed(c: Catalog, env: RunEnv) -> Components:
    if env.provider is None:
        raise Blocked("blocked: no local LLM server configured for this run (use --llm-url)")
    return Components(_hybrid(c, env), _reranker(env), env.provider)


SYSTEMS: list[SystemSpec] = [
    SystemSpec(
        "1_exact_fuzzy",
        "Exact identifier + fuzzy matching",
        lambda c, e: Components([FuzzyScanRetriever(c)]),
    ),
    SystemSpec(
        "2_lexical", "Lexical retrieval (FTS5 BM25)", lambda c, e: Components([FtsBm25Retriever(c)])
    ),
    SystemSpec(
        "2b_lexical_rrf",
        "Lexical BM25 + trigram, RRF (current default)",
        lambda c, e: Components([FtsBm25Retriever(c), TrigramRetriever(c)]),
    ),
    SystemSpec(
        "3_embedding",
        "Embedding retrieval (bge-small-en-v1.5)",
        lambda c, e: Components([_embedding(c, e)]),
    ),
    SystemSpec(
        "4_hybrid",
        "Hybrid BM25 + trigram + embedding (RRF)",
        lambda c, e: Components(_hybrid(c, e)),
    ),
    SystemSpec(
        "5_hybrid_rerank",
        "Hybrid + cross-encoder reranker",
        lambda c, e: Components(_hybrid(c, e), _reranker(e)),
    ),
    SystemSpec(
        "6_routed_llm", "Hybrid + reranker + routed local LLM adjudication (advisory)", _routed
    ),
]


def run_system(
    components: Components, catalog: Catalog, cases: Sequence[EvalCase]
) -> list[CaseResult]:
    resolver = Resolver(
        catalog,
        traces=None,
        provider=components.provider,
        retrievers=components.retrievers,
        reranker=components.reranker,
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
    catalog: Catalog,
    cases: Sequence[EvalCase],
    reps: int = 1000,
    seed: int = 0,
    env: RunEnv | None = None,
) -> dict[str, object]:
    env = env or RunEnv()
    synthetic_catalog = catalog.meta().get("all_synthetic") == "True"
    synthetic_cases = all(c.origin == "synthetic_perturbation" for c in cases)
    report: dict[str, object] = {
        "label": (
            "ENGINEERING CHECK ON SYNTHETIC DATA. NOT A REAL-WORLD EVALUATION."
            if synthetic_catalog
            else "ENGINEERING CHECK: synthetic perturbation cases on the real Open Library "
            "catalog. NOT A REAL-WORLD EVALUATION; no human labels; not calibrated."
        )
        if synthetic_catalog or synthetic_cases
        else "evaluation",
        "splits_in_cases": sorted({c.split or "unassigned" for c in cases}),
        "catalog_meta": catalog.meta(),
        "cases": len(cases),
        "human_labeled_cases": sum(c.human_labeled for c in cases),
        "confidence_note": "signal = top-1 agreements - 2*conflicts: an UNCALIBRATED ranking "
        "signal; buckets and risk-coverage use it, not a probability",
        "systems": {},
    }
    systems: dict[str, object] = {}
    for spec in SYSTEMS:
        try:
            components = spec.build(catalog, env)
        except Blocked as exc:
            systems[spec.key] = {"label": spec.label, "status": str(exc)}
            continue
        res = run_system(components, catalog, cases)
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


def _require_frozen(tag: str | None) -> None:
    """Held-out runs need HEAD to be exactly a tagged commit with a clean tree."""
    import subprocess

    if not tag:
        raise SystemExit("refusing held-out run: pass --frozen-tag <tag> for the frozen policy")

    def git(*args: str) -> str:
        return subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607 - git from PATH, fixed args
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    if git("status", "--porcelain"):
        raise SystemExit("refusing held-out run: working tree is not clean")
    if git("rev-parse", f"{tag}^{{commit}}") != git("rev-parse", "HEAD"):
        raise SystemExit(f"refusing held-out run: HEAD is not the frozen tag {tag}")


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - thin CLI
    p = argparse.ArgumentParser(prog="bera-eval")
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--split", choices=["dev", "heldout", "all"], default="dev")
    p.add_argument("--db", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--reps", type=int, default=1000)
    p.add_argument("--ml", action="store_true", help="enable embedding/reranker systems")
    p.add_argument("--llm-url", help="local OpenAI-compatible server for system 6")
    p.add_argument("--llm-model", default="qwen3-4b-instruct-2507-q4km")
    p.add_argument("--frozen-tag", help="required for --split heldout")
    a = p.parse_args(argv)
    if a.split in ("heldout", "all") and any(
        c.split == "heldout" and c.origin != "synthetic_perturbation" for c in load_cases(a.cases)
    ):
        _require_frozen(a.frozen_tag)
    cases = [c for c in load_cases(a.cases) if a.split == "all" or c.split == a.split]
    catalog = Catalog(a.db or Settings.from_env().catalog_db)
    provider = None
    if a.llm_url:
        from bera.llm.openai_compat import OpenAICompatProvider

        provider = OpenAICompatProvider(a.llm_url, a.llm_model)
    env = RunEnv(enable_ml=a.ml, cache_dir=REPO_ROOT / "var" / "cache", provider=provider)
    report = evaluate(catalog, cases, reps=a.reps, env=env)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    (a.out / "report.md").write_text(markdown(report))
    print(markdown(report))


if __name__ == "__main__":  # pragma: no cover
    main()
