"""The 2026-11-09 label-data migration stays consistent (no git needed).

See data/eval/migrations/20261109_program_drafted_origin/ for the record and the fuller
verification (which also compares against the pre-migration files and frozen metrics)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bera.evalkit.cases import load_cases
from bera.evalkit.provenance import apply_amendments, line_sha256, not_independent_case_ids

ROOT = Path(__file__).resolve().parents[2]
MIG = json.loads(
    (ROOT / "data/eval/migrations/20261109_program_drafted_origin/migration.json").read_text()
)
OLD_O, NEW_O = '"origin":"ai_drafted_human_labeled"', '"origin":"program_drafted_human_labeled"'


def test_migrated_files_match_record() -> None:
    for path, h in MIG["files"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == h["new_sha256"], path


def test_label_lines_differ_only_in_origin() -> None:
    for path, recs in MIG["label_lines"].items():
        lines = [x for x in (ROOT / path).read_text().split("\n") if x.strip()]
        assert len(lines) == len(recs)
        for line, rec in zip(lines, recs, strict=True):
            assert NEW_O in line and OLD_O not in line
            assert line_sha256(line) == rec["new_sha256"]
            assert line_sha256(line.replace(NEW_O, OLD_O)) == rec["old_sha256"]


def test_labels_load_and_every_pin_resolves() -> None:
    for path in MIG["label_lines"]:
        labels = ROOT / path
        cases = load_cases(labels)
        assert all(c.origin == "program_drafted_human_labeled" and c.human_labeled for c in cases)
        apply_amendments(cases, labels)  # raises if an amendment pin does not match
        latest = {json.loads(x)["case_id"]: x for x in labels.read_text().splitlines() if x}
        for suffix in (".provenance.jsonl", ".review_flags.jsonl", ".amendments.jsonl"):
            side = labels.with_name(labels.stem + suffix)
            if side.exists():
                for x in side.read_text().splitlines():
                    r = json.loads(x)
                    assert line_sha256(latest[r["case_id"]]) == r["applies_to_label_sha256"]
                    assert "recorded_by" not in r
        not_independent_case_ids(labels)


def test_no_legacy_values_left_in_label_data() -> None:
    for path in MIG["files"]:
        text = (ROOT / path).read_text()
        for legacy in ("ai_drafted_human_labeled", "practice_ai_assisted", "answer_supplied_by_ai"):
            assert legacy not in text, (path, legacy)
