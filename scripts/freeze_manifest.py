"""Full-system freeze manifest: write it before tagging, verify it any time after.

    uv run python scripts/freeze_manifest.py write
    uv run python scripts/freeze_manifest.py verify [--pre-tag]

Pins (sha256) every git-tracked file of code, tests, frontend, build/lock files, the LLM
prompt, the local model files and inference binary, the corpus/catalog, the frozen route
evidence, the held-out generation rules, the evaluation protocol documents and the dev
evidence base (labels, sidecars, queues). It also records every module-level constant of the
decision path (retrieval settings, thresholds, budgets, route-gate constants) and the
deferred items. `verify` recomputes everything and fails on any difference. With --pre-tag
it also requires that no held-out queue, label or result exists yet.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/freeze/freeze_manifest.json"
TRACKED_PREFIXES = ("src/", "scripts/", "tests/", "frontend/src/")
TRACKED_FILES = (
    "pyproject.toml",
    "uv.lock",
    "frontend/package.json",
    "frontend/package-lock.json",
    "Dockerfile",
    "compose.yaml",
    ".github/workflows/ci.yml",
)
PROMPT = "src/bera/llm/prompt.py"
PROTOCOL = (
    "docs/EVALUATION_PLAN.md",
    "docs/EVAL_PROTOCOL.md",
    "docs/DECISION_POLICY.md",
    "docs/SYNTHETIC_LABEL_SPEC.md",
    "docs/LABELING_GUIDE.md",
    "docs/REQUIREMENTS_AUDIT.md",
    "docs/REQUIREMENTS_TRACKER.md",
    "docs/FREEZE.md",
)
DATA = (
    "data/corpus/v3_proposed/corpus.jsonl",
    "data/corpus/v3_proposed/families.json",
    "data/corpus/v3_proposed/manifest.json",
    "data/corpus/v3_proposed/probe_status_for_labeling.json",
    "data/selection/exclusions_v3_proposed.jsonl",
    "data/eval/dev_check_v3_synthetic.jsonl",
)
UNTRACKED_DATA = ("var/catalog_v3.sqlite",)
ROUTE_EVIDENCE = "data/eval/llm_route_evidence_policy_v2.json"
GENERATION = ("scripts/make_heldout_queue.py", "src/bera/evalkit/stratified.py")
DEV_EVIDENCE_GLOBS = ("data/eval/labels/*", "data/eval/drafts/*")
MODEL_DIR = "models"
LLAMA_BIN = ".tools/llama.cpp/build/bin/llama-server"
CONSTANT_MODULES = (
    "bera.features",
    "bera.policy",
    "bera.retrieval",
    "bera.service",
    "bera.catalog",
    "bera.llm.adjudicator",
    "bera.llm.routes",
    "bera.llm.prompt",
    "bera.evalkit.stratified",
    "bera.evalkit.perturb",
)
DEFERRED = [
    "C1 calibrated scorer: insufficient evidence; confidence reported as uncalibrated bands",
    "Validated LLM suggestion path: implemented, both routes CLOSED on dev evidence "
    "(agree 5/10, override 0/0 under policy v2; target 0.95, minimum 30)",
    "Damaged-ISBN fallback to other fields: deferred (rule unchanged: repair -> review)",
    "Unicode-guard scope (catalog fields not supplied by the query): deferred (unchanged)",
    "Catalog-inconsistency detector beyond duplicate ISBN and field conflicts: not implemented",
    "D6 ~60 abstention/out-of-corpus cases: unmet (16 dev + 3 held-out probes)",
    "D4 preferred 120 labels: not pursued (minimum 100 in progress)",
    "S8 CI execution: not run (no remote); S9 Docker: not re-verified at freeze",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def tracked() -> list[str]:
    files = git("ls-files").splitlines()
    keep = [f for f in files if f.startswith(TRACKED_PREFIXES) or f in TRACKED_FILES]
    return sorted(keep)


def hashes(paths: list[str]) -> dict[str, str]:
    return {p: sha256(ROOT / p) for p in paths}


def constants() -> dict[str, dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "src"))
    out: dict[str, dict[str, Any]] = {}
    for name in CONSTANT_MODULES:
        mod = importlib.import_module(name)
        vals: dict[str, Any] = {}
        for k, v in vars(mod).items():
            if k.isupper() and not k.startswith("_"):
                if isinstance(v, (int, float, str, bool)):
                    vals[k] = v
                elif isinstance(v, (frozenset, set, tuple, list)):
                    vals[k] = (
                        sorted(map(str, v))
                        if isinstance(v, (set, frozenset))
                        else [str(x) for x in v]
                    )
                elif isinstance(v, dict):
                    vals[k] = json.loads(json.dumps(v, default=str))
        out[name] = vals
    return out


def route_state() -> dict[str, Any]:
    from bera.llm.routes import load_gate

    gate = load_gate(ROOT / ROUTE_EVIDENCE)
    return {"evidence": ROUTE_EVIDENCE, "open_routes": sorted(gate.open_routes)}


def build() -> dict[str, Any]:
    from bera.policy import POLICY_VERSION

    dev = sorted(
        str(p.relative_to(ROOT)) for g in DEV_EVIDENCE_GLOBS for p in ROOT.glob(g) if p.is_file()
    )
    models = sorted(str(p.relative_to(ROOT)) for p in (ROOT / MODEL_DIR).rglob("*") if p.is_file())
    return {
        "policy_version": POLICY_VERSION,
        "split_seed": 20261103,
        "code": hashes(tracked()),
        "prompt": {PROMPT: sha256(ROOT / PROMPT)},
        "constants": constants(),
        "models": hashes(models),
        "inference_binary": {LLAMA_BIN: sha256(ROOT / LLAMA_BIN)},
        "data": hashes(list(DATA)),
        "untracked_data": hashes(list(UNTRACKED_DATA)),
        "route_evidence": {ROUTE_EVIDENCE: sha256(ROOT / ROUTE_EVIDENCE)},
        "route_gate": route_state(),
        "generation_rules": hashes(list(GENERATION)),
        "protocol": hashes(list(PROTOCOL)),
        "dev_evidence": hashes(dev),
        "deferred": DEFERRED,
        "heldout_run_procedure": (
            "After held-out labeling: create a git worktree at the freeze tag and run "
            "bera.evalkit.run there with --split heldout --frozen-tag <tag> "
            f"--llm-route-evidence {ROUTE_EVIDENCE}, passing the held-out label file and "
            "queue from the main checkout. One run; nothing is changed and re-run."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["write", "verify"])
    p.add_argument("--pre-tag", action="store_true")
    a = p.parse_args()
    if a.mode == "write":
        OUT.parent.mkdir(parents=True, exist_ok=True)
        m = build()
        OUT.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
        print(
            f"wrote {OUT.relative_to(ROOT)}: {len(m['code'])} code files, "
            f"{len(m['models'])} model files, {len(m['dev_evidence'])} dev evidence files; "
            f"open LLM routes: {m['route_gate']['open_routes'] or 'none'}"
        )
        return
    want = json.loads(OUT.read_text())
    have = build()
    problems = []
    for section in want:
        if want[section] != have.get(section):
            if isinstance(want[section], dict):
                keys = set(want[section]) | set(have.get(section, {}))
                diff = sorted(k for k in keys if want[section].get(k) != have[section].get(k))
                problems.append(f"{section}: {diff[:5]}{' ...' if len(diff) > 5 else ''}")
            else:
                problems.append(section)
    if git("status", "--porcelain"):
        problems.append("working tree not clean")
    if have["route_gate"]["open_routes"]:
        problems.append("an LLM route is open")
    if a.pre_tag and (ROOT / "data/eval/heldout").exists():
        problems.append("held-out data exists before the freeze tag")
    for line in problems:
        print("FAIL", line)
    if problems:
        raise SystemExit(1)
    print(
        "PASS freeze manifest verified (all pins match; both LLM routes closed"
        f"{'; no held-out data yet' if a.pre_tag else ''})"
    )


if __name__ == "__main__":
    main()
