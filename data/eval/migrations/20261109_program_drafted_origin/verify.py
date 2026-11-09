"""Verify the 2026-11-09 label-data migration (run from the repository root, after `uv sync`):

    uv run python data/eval/migrations/20261109_program_drafted_origin/verify.py

1. every migrated file matches the new hash in migration.json;
2. every label line differs from its pre-migration line ONLY in the origin value (the old line
   is rebuilt by reversing that one substitution and must hash to the recorded old hash);
3. loading through the evaluation path (practice/exposure exclusion + owner amendments) gives
   the same cases before (files at the base commit, via git) and after, except `origin`;
4. headline metrics recomputed from the FROZEN per-case outputs with the migrated labels equal
   the stored metrics of each frozen report (the reports themselves are not rewritten).
Writes verification.json next to this script.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from bera.evalkit.cases import load_cases  # noqa: E402
from bera.evalkit.metrics import CaseResult, compute  # noqa: E402
from bera.evalkit.provenance import (  # noqa: E402
    apply_amendments,
    independent_human_cases,
    not_independent_case_ids,
)

MIG = json.loads((HERE / "migration.json").read_text())
OLD_O, NEW_O = '"origin":"ai_drafted_human_labeled"', '"origin":"program_drafted_human_labeled"'
SUFFIXES = (".provenance.jsonl", ".exposures.jsonl", ".amendments.jsonl", ".review_flags.jsonl")
REPORTS = [
    "data/eval/results/heldout40_frozen_r2/report.json",
    "data/eval/results/dev60_human_policy_v2_initials/report.json",
    "data/eval/results/dev60_human_policy_v1/report.json",
]
HEADLINE = [
    "correct_suggestion_rate",
    "wrong_match_rate",
    "error_among_suggestions",
    "abstention_rate",
    "correct_abstention_rate",
    "missed_suggestion_rate",
    "top1_accuracy",
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_show(path: str) -> bytes:
    return subprocess.run(  # noqa: S603 - fixed argument lists
        ["git", "show", f"{MIG['base_commit']}:{path}"],  # noqa: S607
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def evaluated_cases(labels: Path, amend: bool) -> list:
    cs = independent_human_cases(load_cases(labels), labels)
    return apply_amendments(cs, labels)[0] if amend else cs


def snapshot(label_path: str, amend: bool, old: bool) -> dict[str, object]:
    if not old:
        cs = evaluated_cases(ROOT / label_path, amend)
        excluded = not_independent_case_ids(ROOT / label_path)
    else:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / Path(label_path).name
            p.write_bytes(git_show(label_path).replace(OLD_O.encode(), NEW_O.encode()))
            for s in SUFFIXES:  # old sidecars, pins re-pointed only so the old files can load
                side = label_path[: -len(".jsonl")] + s
                try:
                    raw = git_show(side).decode()
                except subprocess.CalledProcessError:
                    continue
                for rec in MIG["label_lines"][label_path]:
                    raw = raw.replace(rec["old_sha256"], rec["new_sha256"])
                # status value renamed in the same migration (same meaning: practice, excluded)
                raw = raw.replace(
                    '"status": "practice_ai_assisted"', '"status": "practice_excluded"'
                )
                (Path(d) / Path(side).name).write_text(raw)
            cs = evaluated_cases(p, amend)
            excluded = not_independent_case_ids(p)
    return {"cases": [c.model_dump(exclude={"origin"}) for c in cs], "excluded": sorted(excluded)}


def main() -> int:
    out: dict[str, object] = {"checks": {}}
    checks: dict[str, object] = out["checks"]  # type: ignore[assignment]
    checks["file_hashes"] = {
        f: sha((ROOT / f).read_bytes()) == v["new_sha256"] for f, v in MIG["files"].items()
    }
    line_ok = {}
    for f, recs in MIG["label_lines"].items():
        lines = [x for x in (ROOT / f).read_text().split("\n") if x.strip()]
        line_ok[f] = len(lines) == len(recs) and all(
            sha(x.encode()) == r["new_sha256"]
            and sha(x.replace(NEW_O, OLD_O).encode()) == r["old_sha256"]
            for x, r in zip(lines, recs, strict=True)
        )
    checks["label_lines_only_origin_changed"] = line_ok
    eq = {}
    for f in MIG["label_lines"]:
        for amend in (False, True):
            a, b = snapshot(f, amend, old=True), snapshot(f, amend, old=False)
            eq[f"{f} amendments={amend}"] = {
                "identical": a == b,
                "cases": len(b["cases"]),  # type: ignore[arg-type]
                "excluded": len(b["excluded"]),  # type: ignore[arg-type]
            }
    checks["evaluation_inputs_identical_except_origin"] = eq
    metrics = {}
    for rp in REPORTS:
        rep = json.loads((ROOT / rp).read_text())
        amend = bool(rep.get("owner_amendments_applied"))
        cases = {}
        for cf in rep["case_files"]:
            for c in evaluated_cases(ROOT / cf["path"], amend):
                cases[c.case_id] = c
        per_sys = {}
        for key, s in rep["systems"].items():
            if s.get("status") != "ran":
                continue
            res = []
            for pc in s["per_case"]:
                c = cases[pc["case_id"]]
                res.append(
                    CaseResult(
                        case_id=c.case_id,
                        family=c.family,
                        expected=c.expected,
                        gold=frozenset(c.gold_edition_ids),
                        ranked_ids=[pc["top1"]] if pc["top1"] else [],
                        outcome=pc["outcome"],
                        suggested=pc["suggested"],
                    )
                )
            m = compute(res, reps=1)
            same = (
                all(
                    (m[k]["numerator"], m[k]["denominator"])  # type: ignore[index]
                    == (s["metrics"][k]["numerator"], s["metrics"][k]["denominator"])
                    for k in HEADLINE
                )
                and m["counts"] == s["metrics"]["counts"]
            )
            per_sys[key] = same
        metrics[rp] = {
            "amendments_applied": amend,
            "cases": len(cases),
            "per_case_rows_match_label_count": all(
                len(s["per_case"]) == len(cases)
                for s in rep["systems"].values()
                if s.get("status") == "ran"
            ),
            "headline_metrics_equal": per_sys,
        }
    checks["frozen_metrics_recomputed_with_migrated_labels"] = metrics

    def bools(x: object, key: str = "") -> list[bool]:
        if isinstance(x, bool):
            return [] if key == "amendments_applied" else [x]
        if isinstance(x, dict):
            return [b for k, v in x.items() for b in bools(v, k)]
        return []

    out["passed"] = all(bools(checks))
    (HERE / "verification.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0 if out["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
