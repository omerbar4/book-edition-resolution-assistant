"""Load-time family resolution: strict, no fallback to work ids. Synthetic records only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bera.catalog import Catalog
from bera.evalkit.cases import EvalCase
from bera.evalkit.drafts import Draft, Proposed, save_drafts
from bera.evalkit.families import FamilyMappingError, load_frozen_queue, resolve_families
from bera.models import Edition, PhysicalFormat, Query


def ed(eid: str, work: str) -> Edition:
    return Edition.model_validate(
        {
            "edition_id": eid,
            "work_id": work,
            "title": f"T {eid}",
            "authors": ("A B",),
            "physical_format": PhysicalFormat.PAPERBACK,
            "source": "test",
            "synthetic": True,
        }
    )


FAMILY_OF = {"W1": "fam:A", "W1b": "fam:A", "W2": "fam:B"}


@pytest.fixture
def cat(tmp_path: Path) -> Catalog:
    c = Catalog(tmp_path / "c.sqlite")
    # E1 and E1b are in family A (different works); E2 is in family B; EX has an unmapped work
    c.build([ed("E1", "W1"), ed("E1b", "W1b"), ed("E2", "W2"), ed("EX", "WX")])
    return c


def draft(did: str, family: str, source: str | None = "E1") -> Draft:
    return Draft(
        draft_id=did,
        split="dev",
        family=family,
        query=Query(title="T"),
        template="t",
        source_edition_id=source,
        proposed=Proposed(expected="abstain", gold_edition_ids=[]),
    )


def label(cid: str, expected: str, gold: list[str], family: str) -> EvalCase:
    return EvalCase.model_validate(
        {
            "case_id": cid,
            "query": {"title": "T"},
            "expected": expected,
            "gold_edition_ids": gold,
            "ambiguity_reason": None if expected == "suggest" else "underspecified",
            "family": family,  # as the UI stored it (a work id for edition choices)
            "origin": "ai_drafted_human_labeled",
            "split": "dev",
            "labeler": "ob",
        }
    )


def test_edition_choice_gets_corpus_family_not_work_id(cat: Catalog) -> None:
    # chosen edition is in another WORK of the same family: family must be fam:A, not W1b
    out = resolve_families(
        [label("c1", "suggest", ["E1b"], "W1b")], [draft("c1", "fam:A")], FAMILY_OF, cat
    )
    assert out[0].family == "fam:A"


def test_abstention_gets_draft_family(cat: Catalog) -> None:
    out = resolve_families(
        [label("c2", "abstain", [], "fam:A")], [draft("c2", "fam:A")], FAMILY_OF, cat
    )
    assert out[0].family == "fam:A"


@pytest.mark.parametrize(
    ("case", "drafts", "msg"),
    [
        (label("c3", "suggest", ["E1"], "W1"), [], "no draft"),
        (label("c4", "abstain", [], "fam:Z"), [draft("c4", "fam:Z")], "not in families.json"),
        (label("c5", "suggest", ["E2"], "W2"), [draft("c5", "fam:A")], "conflicting"),
        (label("c6", "suggest", ["EX"], "WX"), [draft("c6", "fam:A")], "conflicting"),
        (label("c7", "abstain", [], "fam:B"), [draft("c7", "fam:B", "E1")], "source edition"),
    ],
)
def test_missing_or_conflicting_mappings_are_rejected(
    cat: Catalog, case: EvalCase, drafts: list[Draft], msg: str
) -> None:
    with pytest.raises(FamilyMappingError, match=msg):
        resolve_families([case], drafts, FAMILY_OF, cat)


def test_synthetic_cases_untouched(cat: Catalog) -> None:
    syn = label("s1", "abstain", [], "fam:anything").model_copy(
        update={"origin": "synthetic_perturbation", "labeler": None}
    )
    assert resolve_families([syn], [], FAMILY_OF, cat) == [syn]


def test_frozen_queue_requires_matching_manifest(tmp_path: Path) -> None:
    q = tmp_path / "q.jsonl"
    save_drafts(q, [draft("c1", "fam:A")])
    with pytest.raises(FamilyMappingError, match="no manifest"):
        load_frozen_queue(q)
    m = q.with_suffix(".manifest.json")
    m.write_text(json.dumps({"queue_sha256": hashlib.sha256(q.read_bytes()).hexdigest()}))
    drafts, digest = load_frozen_queue(q)
    assert [d.draft_id for d in drafts] == ["c1"] and len(digest) == 64
    q.write_text(q.read_text() + "\n")
    with pytest.raises(FamilyMappingError, match="sha256"):
        load_frozen_queue(q)


def test_harness_refuses_human_cases_without_queue(tmp_path: Path, cat: Catalog) -> None:
    from bera.evalkit.run import main

    labels = tmp_path / "l.jsonl"
    labels.write_text(label("c1", "abstain", [], "fam:A").model_dump_json() + "\n")
    with pytest.raises(SystemExit, match="--queue"):
        main(["--cases", str(labels), "--db", str(cat.path), "--out", str(tmp_path / "o")])


def test_report_paths_are_repo_relative(tmp_path: Path) -> None:
    from bera.config import REPO_ROOT
    from bera.evalkit.run import repo_relative

    inside = REPO_ROOT / "data/corpus/v3_proposed/families.json"
    assert repo_relative(inside) == "data/corpus/v3_proposed/families.json"
    assert repo_relative(Path("data/eval/drafts/dev_batch02.jsonl")) == (
        "data/eval/drafts/dev_batch02.jsonl"
    )
    outside = tmp_path / "x" / "q.jsonl"
    assert repo_relative(outside) == "q.jsonl"  # never an absolute machine path


def test_harness_refuses_duplicate_case_ids_across_files(tmp_path: Path, cat: Catalog) -> None:
    from bera.evalkit.run import main

    one = tmp_path / "a.jsonl"
    two = tmp_path / "b.jsonl"
    line = label("c1", "abstain", [], "fam:A").model_dump_json() + "\n"
    one.write_text(line)
    two.write_text(line)
    with pytest.raises(SystemExit, match="duplicate case ids"):
        main(["--cases", str(one), str(two), "--db", str(cat.path), "--out", str(tmp_path / "o")])
