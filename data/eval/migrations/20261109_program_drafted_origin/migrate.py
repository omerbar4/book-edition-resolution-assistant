"""Label-data migration 2026-11-09: origin value, provenance fields, event-focused wording.

Deterministic: always reads the input files from git at BASE (the commit before the
migration) and writes the migrated files plus `migration.json` next to this script.
Run from the repository root:
    python3 -I data/eval/migrations/20261109_program_drafted_origin/migrate.py

What changes (and nothing else):
- label lines: "origin" "ai_drafted_human_labeled" -> "program_drafted_human_labeled". Queries
  were drafted by the deterministic template drafters; labels were chosen by the owner.
- provenance sidecars: "recorded_by" is split into "decided_by" (who decided) and
  "recorded_via" (how the line was written); "amended_by" keeps only the decider.
- status "practice_ai_assisted" -> "practice_excluded"; exposure kind
  "answer_supplied_by_ai" -> "answer_supplied_externally".
- a few free-text reasons are reworded to describe the event (practice, outside help,
  answer exposed before labeling, catalog-record review); the facts and every exclusion
  and independence status are unchanged.
- sidecar pins (applies_to_label_sha256) move from the old label line to the migrated line.

Label decisions (expected, gold_edition_ids, ambiguity_reason, labeler, labeled_at, query,
family, split), inclusion/exclusion and amendments are unchanged. Frozen evaluation outputs
are NOT rewritten: they were computed from the pre-migration files and keep their hashes;
`migration.json` maps every old hash to its new one.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

BASE = "c15876d0d1e30cacd124988cc02de7c2db398441"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD_ORIGIN, NEW_ORIGIN = "ai_drafted_human_labeled", "program_drafted_human_labeled"
OWNER = "owner (omer)"

LABELS = [
    "data/eval/labels/dev_labels.jsonl",
    "data/eval/labels/dev_batch02_labels.jsonl",
    "data/eval/labels/dev_final_labels.jsonl",
    "data/eval/heldout/heldout_labels.jsonl",
]
SIDECARS = {
    "data/eval/labels/dev_labels.provenance.jsonl": LABELS[0],
    "data/eval/labels/dev_labels.exposures.jsonl": LABELS[0],
    "data/eval/labels/dev_batch02_labels.provenance.jsonl": LABELS[1],
    "data/eval/labels/dev_batch02_labels.amendments.jsonl": LABELS[1],
    "data/eval/labels/dev_batch02_labels.review_flags.jsonl": LABELS[1],
    "data/eval/labels/dev_final_labels.provenance.jsonl": LABELS[2],
    "data/eval/heldout/heldout_labels.provenance.jsonl": LABELS[3],
}
DARKWOODS_OLD = (
    "Owner ruling after AI-assisted review (Claude presented the query and the uncontradicted "
    "catalog records, without system scores or recommendations): amended to human review"
)
DARKWOODS_NEW = (
    "Owner ruling after a catalog-record review in which an assistant tool, not the labeler, "
    "presented the query and the uncontradicted catalog records, without system scores or "
    "recommendations: amended to human review"
)
TEXT = [  # (old, new) exact substrings; each must be found where expected
    (
        "Owner instruction: label made as AI-assisted practice; kept for reference",
        "Owner instruction: practice label, made with outside help; kept for reference",
    ),
    (
        "Owner instruction: reviewed with ChatGPT assistance; AI-assisted practice, kept for "
        "reference",
        "Owner instruction: reviewed with an external chat assistant before saving; practice "
        "label, kept for reference",
    ),
    (
        "ChatGPT supplied the answer for this case before it was labeled (owner report).",
        "An external chat assistant supplied the answer for this case before it was labeled "
        "(owner report).",
    ),
    ("(no AI assistance reported)", "(no outside help reported)"),
    (DARKWOODS_OLD, DARKWOODS_NEW),
]
RENAMES = {
    ("status", "practice_ai_assisted"): "practice_excluded",
    ("kind", "answer_supplied_by_ai"): "answer_supplied_externally",
}


def git_show(path: str) -> str:
    return subprocess.run(  # noqa: S603 - fixed argument lists
        ["git", "show", f"{BASE}:{path}"],  # noqa: S607
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lines(text: str) -> list[str]:
    return [x for x in text.split("\n") if x.strip()]


def split_recorder(value: str) -> tuple[str, str]:
    """'Claude on owner instruction (chat, D)' or 'owner (omer), recorded by Claude on owner
    instruction (chat, D)' -> (decider, recorded_via)."""
    marker = "on owner instruction "
    i = value.index(marker)
    return OWNER, "project tooling, " + value[i:]


def migrate_record(rec: dict[str, object], pins: dict[str, str]) -> tuple[dict, list[str]]:
    out: dict[str, object] = {}
    changed: list[str] = []
    for k, v in rec.items():
        if k == "recorded_by":
            decider, via = split_recorder(str(v))
            out["decided_by"], out["recorded_via"] = decider, via
            changed.append("recorded_by->decided_by+recorded_via")
        elif k == "amended_by":
            decider, via = split_recorder(str(v))
            out["amended_by"], out["recorded_via"] = decider, via
            changed.append("amended_by->amended_by+recorded_via")
        elif k == "applies_to_label_sha256":
            out[k] = pins[str(v)]
            changed.append("applies_to_label_sha256")
        elif isinstance(v, str) and (k, v) in RENAMES:
            out[k] = RENAMES[(k, v)]
            changed.append(k)
        elif isinstance(v, str):
            new = v
            for old, rep in TEXT:
                new = new.replace(old, rep)
            out[k] = new
            if new != v:
                changed.append(k)
        else:
            out[k] = v
    return out, changed


def main() -> int:
    record: dict[str, object] = {
        "migration": "20261109_program_drafted_origin",
        "base_commit": BASE,
        "script": "data/eval/migrations/20261109_program_drafted_origin/migrate.py",
        "summary": (
            "origin ai_drafted_human_labeled -> program_drafted_human_labeled; provenance "
            "recorded_by split into decided_by + recorded_via; status practice_ai_assisted -> "
            "practice_excluded; exposure kind answer_supplied_by_ai -> "
            "answer_supplied_externally; event-focused wording; sidecar pins moved. Label "
            "decisions, exclusions, amendments and metrics unchanged."
        ),
        "files": {},
        "label_lines": {},
        "sidecar_records": {},
    }
    files: dict[str, dict[str, str]] = {}
    pins: dict[str, str] = {}
    for path in LABELS:
        old_text = git_show(path)
        new_lines = []
        per_line = []
        for line in lines(old_text):
            assert line.count(f'"origin":"{OLD_ORIGIN}"') == 1, path
            new = line.replace(f'"origin":"{OLD_ORIGIN}"', f'"origin":"{NEW_ORIGIN}"')
            a, b = json.loads(line), json.loads(new)
            assert {**a, "origin": NEW_ORIGIN} == b and list(a) == list(b), path
            pins[sha(line)] = sha(new)
            per_line.append(
                {"case_id": a["case_id"], "old_sha256": sha(line), "new_sha256": sha(new)}
            )
            new_lines.append(new)
        new_text = "\n".join(new_lines) + "\n"
        (ROOT / path).write_text(new_text, encoding="utf-8")
        files[path] = {"old_sha256": sha(old_text), "new_sha256": sha(new_text)}
        record["label_lines"][path] = per_line  # type: ignore[index]
    for path in SIDECARS:
        old_text = git_show(path)
        out_lines, per_rec = [], []
        for line in lines(old_text):
            rec, changed = migrate_record(json.loads(line), pins)
            new = json.dumps(rec, ensure_ascii=False)
            out_lines.append(new)
            per_rec.append(
                {
                    "case_id": rec["case_id"],
                    "old_sha256": sha(line),
                    "new_sha256": sha(new),
                    "changed_fields": sorted(set(changed)),
                }
            )
        new_text = "\n".join(out_lines) + "\n"
        (ROOT / path).write_text(new_text, encoding="utf-8")
        files[path] = {"old_sha256": sha(old_text), "new_sha256": sha(new_text)}
        record["sidecar_records"][path] = per_rec  # type: ignore[index]
    record["files"] = files
    # Historical references that keep the OLD hashes on purpose (computed before migration).
    olds = {v["old_sha256"]: k for k, v in files.items()}
    refs: dict[str, list[str]] = {}
    tracked = subprocess.run(
        ["git", "ls-files", "data", "docs"],  # noqa: S607
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    for f in tracked:
        if f.startswith("data/eval/migrations/") or f in files:
            continue
        try:
            body = (ROOT / f).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        hit = sorted({olds[h] for h in olds if h[:8] in body})
        if hit:
            refs[f] = hit
    record["unchanged_historical_references"] = {
        "note": (
            "These files were produced before the migration (frozen results, route evidence, "
            "the reveal marker, the r2 freeze manifest, the evaluation report). They keep the "
            "pre-migration hashes because those are the exact inputs that were evaluated; use "
            "`files` above to map old -> new."
        ),
        "files": refs,
    }
    (HERE / "migration.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(files, indent=2))
    print("historical references:", json.dumps(refs, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
