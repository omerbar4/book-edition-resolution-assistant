"""Label provenance sidecars. Label files are append-only and are never rewritten.

`<labels>.provenance.jsonl`: one JSON object per line, appended; it annotates existing label
entries without editing them. Each record pins the exact label line it refers to by sha256.

- `status: "practice_ai_assisted"`: the label was made as AI-assisted practice. It is kept,
  but it is NOT an independent human label and is excluded from the independent count and
  from evaluation. Because the drafted proposal was revealed when the label was submitted,
  the case is no longer blind; a later label on the same case stays practice.

`<labels>.exposures.jsonl`: one JSON object per line, appended. It records that information
about a case's answer reached the labeler BEFORE they labeled it (for example an AI assistant
supplied the answer, or the labeler saw material that correlates the case's generator
template with the drafted outcome). The case need not be labeled yet. Any label on an
exposed case, present or future, is not an independent human label: it is excluded from the
independent count and from evaluation exactly like practice labels. Records name the kind of
exposure only, never the answer or the drafted outcome, so the record itself leaks nothing.
No clearing mechanism exists; re-admitting a case needs an explicit owner decision.

`<labels>.review_flags.jsonl`: open questions about an existing label for the owner to rule
on (for example a human-vs-rule disagreement). A flag never edits the label and never changes
any count; the label stays exactly as saved until the owner decides.

`<labels>.skips.jsonl`: "cannot assess yet" markers. A skip is not a label, never reveals
the proposal, and never counts. A later label supersedes it in the queue display.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bera.evalkit.cases import EvalCase

PRACTICE = "practice_ai_assisted"


def provenance_path(labels: Path) -> Path:
    return labels.with_name(labels.stem + ".provenance.jsonl")


def skips_path(labels: Path) -> Path:
    return labels.with_name(labels.stem + ".skips.jsonl")


def exposures_path(labels: Path) -> Path:
    return labels.with_name(labels.stem + ".exposures.jsonl")


def line_sha256(line: str) -> str:
    return hashlib.sha256(line.rstrip("\n").encode("utf-8")).hexdigest()


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def practice_case_ids(labels: Path) -> set[str]:
    return {r["case_id"] for r in _read(provenance_path(labels)) if r.get("status") == PRACTICE}


def skipped(labels: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for r in _read(skips_path(labels)):
        out[r["draft_id"]] = r
    return out


def append_skip(labels: Path, draft_id: str, labeler: str, reason: str | None) -> None:
    path = skips_path(labels)
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "draft_id": draft_id,
        "labeler": labeler,
        "reason": reason,
        "skipped_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "note": "not a label; proposal not revealed",
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def mark_practice(labels: Path, case_id: str, recorded_by: str, reason: str) -> dict[str, Any]:
    """Annotate the latest existing label line for `case_id` as AI-assisted practice."""
    lines = [x for x in labels.read_text(encoding="utf-8").splitlines() if x.strip()]
    mine = [x for x in lines if json.loads(x).get("case_id") == case_id]
    if not mine:
        raise ValueError(f"no label entry for {case_id}")
    entry = json.loads(mine[-1])
    rec = {
        "case_id": case_id,
        "status": PRACTICE,
        "applies_to_label_sha256": line_sha256(mine[-1]),
        "label_labeled_at": entry.get("labeled_at"),
        "label_labeler": entry.get("labeler"),
        "excluded_from_independent_count": True,
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "recorded_by": recorded_by,
        "reason": reason,
    }
    path = provenance_path(labels)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def review_flags_path(labels: Path) -> Path:
    return labels.with_name(labels.stem + ".review_flags.jsonl")


def flag_for_review(
    labels: Path, case_id: str, issue: str, recorded_by: str, detail: str
) -> dict[str, Any]:
    """Append an owner-review flag pinned to the latest label line for `case_id`."""
    lines = [x for x in labels.read_text(encoding="utf-8").splitlines() if x.strip()]
    mine = [x for x in lines if json.loads(x).get("case_id") == case_id]
    if not mine:
        raise ValueError(f"no label entry for {case_id}")
    rec = {
        "case_id": case_id,
        "status": "open_owner_review",
        "issue": issue,
        "applies_to_label_sha256": line_sha256(mine[-1]),
        "label_unchanged": True,
        "affects_counts": False,
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "recorded_by": recorded_by,
        "detail": detail,
    }
    with review_flags_path(labels).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def amendments_path(labels: Path) -> Path:
    return labels.with_name(labels.stem + ".amendments.jsonl")


def record_ruling(
    labels: Path,
    case_id: str,
    ruling: str,
    ruled_by: str,
    note: str,
    amended: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve an open review flag. The original label line is never edited.

    ruling "reaffirmed": appends a resolved record to the review-flags sidecar.
    ruling "amended": also appends the amended answer (expected, gold_edition_ids,
    ambiguity_reason) to `<labels>.amendments.jsonl`, pinned to the original line's sha256.
    Evaluation applies amendments at load time (apply_amendments) and reports them."""
    if ruling not in ("reaffirmed", "amended"):
        raise ValueError("ruling must be 'reaffirmed' or 'amended'")
    if (ruling == "amended") != (amended is not None):
        raise ValueError("an amended ruling needs an amended label, and only then")
    lines = [x for x in labels.read_text(encoding="utf-8").splitlines() if x.strip()]
    mine = [x for x in lines if json.loads(x).get("case_id") == case_id]
    if not mine:
        raise ValueError(f"no label entry for {case_id}")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    pin = line_sha256(mine[-1])
    if amended is not None:
        keys = {"expected", "gold_edition_ids", "ambiguity_reason"}
        if set(amended) - keys or "expected" not in amended:
            raise ValueError(f"amended label may only set {sorted(keys)}")
        with amendments_path(labels).open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "case_id": case_id,
                        "applies_to_label_sha256": pin,
                        "amended_label": amended,
                        "amended_by": ruled_by,
                        "amended_at": now,
                        "note": note,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    rec = {
        "case_id": case_id,
        "status": f"resolved_owner_{ruling}",
        "applies_to_label_sha256": pin,
        "label_unchanged": True,
        "affects_counts": False,
        "recorded_at": now,
        "recorded_by": ruled_by,
        "detail": note,
    }
    with review_flags_path(labels).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def apply_amendments(cases: list[EvalCase], labels: Path) -> tuple[list[EvalCase], list[str]]:
    """Overlay owner amendments (latest per case) whose pin matches the current label line."""
    path = amendments_path(labels)
    if not path.exists():
        return cases, []
    lines = [x for x in labels.read_text(encoding="utf-8").splitlines() if x.strip()]
    latest_line = {json.loads(x)["case_id"]: x for x in lines}
    amends: dict[str, dict[str, Any]] = {}
    for r in _read(path):
        if line_sha256(latest_line.get(r["case_id"], "")) != r["applies_to_label_sha256"]:
            raise ValueError(f"amendment for {r['case_id']} does not match its label line")
        amends[r["case_id"]] = r["amended_label"]
    out = []
    for c in cases:
        if c.case_id in amends:
            a = amends[c.case_id]
            c = c.model_copy(
                update={
                    "expected": a["expected"],
                    "gold_edition_ids": sorted(a.get("gold_edition_ids", [])),
                    "ambiguity_reason": a.get("ambiguity_reason"),
                }
            )
        out.append(c)
    return out, sorted(amends)


def exposed_case_ids(labels: Path) -> set[str]:
    return {r["case_id"] for r in _read(exposures_path(labels))}


def record_exposure(
    labels: Path, case_id: str, kind: str, assessment: str, recorded_by: str, detail: str
) -> dict[str, Any]:
    """Append an exposure record for `case_id` (labeled or not). Never include the answer."""
    existing = []
    if labels.exists():
        existing = [
            x
            for x in labels.read_text(encoding="utf-8").splitlines()
            if x.strip() and json.loads(x).get("case_id") == case_id
        ]
    rec = {
        "case_id": case_id,
        "kind": kind,
        "assessment": assessment,
        "excluded_from_independent_count": True,
        "label_existed_when_recorded": bool(existing),
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "recorded_by": recorded_by,
        "detail": detail,
    }
    path = exposures_path(labels)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def not_independent_case_ids(labels: Path) -> set[str]:
    """Cases whose labels can never count as independent: practice or exposed."""
    return practice_case_ids(labels) | exposed_case_ids(labels)


def independent_human_cases(cases: list[EvalCase], labels: Path) -> list[EvalCase]:
    """Drop cases marked practice or exposed in the sidecars next to `labels`."""
    excluded = not_independent_case_ids(labels)
    return [c for c in cases if c.case_id not in excluded]
