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
from bera.llm.routes import CLOSED_GATE, RouteGate
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
    route_gate: RouteGate = CLOSED_GATE  # validated LLM path; closed unless evidence given


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
    components: Components,
    catalog: Catalog,
    cases: Sequence[EvalCase],
    route_gate: RouteGate = CLOSED_GATE,
) -> list[CaseResult]:
    resolver = Resolver(
        catalog,
        traces=None,
        provider=components.provider,
        retrievers=components.retrievers,
        reranker=components.reranker,
        route_gate=route_gate,
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
    only: Sequence[str] | None = None,
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
        if only and spec.key not in only:
            continue
        try:
            components = spec.build(catalog, env)
        except Blocked as exc:
            systems[spec.key] = {"label": spec.label, "status": str(exc)}
            continue
        res = run_system(components, catalog, cases, env.route_gate)
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
                    "expected": r.expected,
                    "adjudication_status": r.adjudication_status,
                    "adjudication_choice": r.adjudication_choice,
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


def repo_relative(path: Path) -> str:
    """Path as written into reports: relative to the repository when inside it, so reports
    carry no machine-specific absolute paths; otherwise only the file name."""
    p = Path(path).resolve()
    try:
        return p.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return p.name


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
    p.add_argument("--cases", type=Path, nargs="+", required=True, help="one or more case files")
    p.add_argument("--split", choices=["dev", "heldout", "all"], default="dev")
    p.add_argument("--db", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--reps", type=int, default=1000)
    p.add_argument("--ml", action="store_true", help="enable embedding/reranker systems")
    p.add_argument("--llm-url", help="local OpenAI-compatible server for system 6")
    p.add_argument("--llm-model", default="qwen3-4b-instruct-2507-q4km")
    p.add_argument("--frozen-tag", help="required for --split heldout")
    p.add_argument("--systems", nargs="+", help="run only these system keys (default: all)")
    p.add_argument(
        "--llm-route-evidence",
        type=Path,
        help="frozen dev route evidence for the validated LLM path (default: gate closed)",
    )
    p.add_argument(
        "--queue",
        type=Path,
        nargs="+",
        help="frozen labeling queue (with manifest) the human-labeled cases came from; "
        "required for human-labeled cases so families come from the corpus mapping",
    )
    p.add_argument(
        "--families",
        type=Path,
        default=REPO_ROOT / "data/corpus/v3_proposed/families.json",
        help="frozen corpus work->family mapping",
    )
    a = p.parse_args(argv)
    from bera.evalkit.provenance import independent_human_cases

    loaded = {path: load_cases(path) for path in a.cases}
    if a.split in ("heldout", "all") and any(
        c.split == "heldout" and c.origin != "synthetic_perturbation"
        for cs in loaded.values()
        for c in cs
    ):
        _require_frozen(a.frozen_tag)
    cases: list[EvalCase] = []
    for path, cs in loaded.items():
        cs = [c for c in cs if a.split == "all" or c.split == a.split]
        # Practice labels and labels on cases exposed before labeling (provenance sidecars
        # next to each label file) are never independent human labels: exclude them.
        kept = independent_human_cases(cs, path)
        if len(kept) != len(cs):
            print(f"excluded {len(cs) - len(kept)} practice/exposed case(s) from {path.name}")
        cases.extend(kept)
    ids = [c.case_id for c in cases]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate case ids across case files")
    catalog = Catalog(a.db or Settings.from_env().catalog_db)
    family_source = None
    if any(c.human_labeled for c in cases):
        from bera.evalkit.families import load_frozen_queue, resolve_families

        if not a.queue:
            raise SystemExit("human-labeled cases need --queue (frozen queue) to resolve families")
        drafts = []
        queues = []
        for q in a.queue:
            ds, sha = load_frozen_queue(q)
            drafts.extend(ds)
            queues.append({"queue": repo_relative(q), "queue_sha256": sha})
        cases = resolve_families(cases, drafts, json.loads(a.families.read_text()), catalog)
        family_source = {
            "queues": queues,
            "families": repo_relative(a.families),
            "rule": "family = draft family; chosen editions must map to it; no fallback",
        }
    provider = None
    if a.llm_url:
        from bera.llm.openai_compat import OpenAICompatProvider

        provider = OpenAICompatProvider(a.llm_url, a.llm_model)
    from bera.llm.routes import load_gate

    gate = load_gate(a.llm_route_evidence)
    env = RunEnv(
        enable_ml=a.ml, cache_dir=REPO_ROOT / "var" / "cache", provider=provider, route_gate=gate
    )
    report = evaluate(catalog, cases, reps=a.reps, env=env, only=a.systems)
    if family_source:
        report["family_source"] = family_source
    report["llm_route_gate"] = {"source": gate.source, "open_routes": sorted(gate.open_routes)}
    import hashlib

    report["case_files"] = [
        {"path": repo_relative(x), "sha256": hashlib.sha256(x.read_bytes()).hexdigest()}
        for x in a.cases
    ]
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    (a.out / "report.md").write_text(markdown(report))
    print(markdown(report))


if __name__ == "__main__":  # pragma: no cover
    main()
