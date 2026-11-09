"""Spec v3, conflict templates and strict stratified assignment. Synthetic records only."""

from __future__ import annotations

from pathlib import Path

import pytest

from bera.evalkit.drafts import ALL_TEMPLATES, TEMPLATES, template_effective
from bera.evalkit.perturb import YEAR_SHIFTS, judged_fields, label, perturbed_fields
from bera.evalkit.stratified import STRATA, Candidate, assign
from bera.models import Edition, PhysicalFormat


def ed(
    eid: str, year: int | None = 2000, fmt: PhysicalFormat = PhysicalFormat.PAPERBACK
) -> Edition:
    return Edition.model_validate(
        {
            "edition_id": eid,
            "work_id": "W",
            "title": "Dune",
            "authors": ("Frank Herbert",),
            "physical_format": fmt,
            "publish_year": year,
            "source": "test",
            "synthetic": True,
        }
    )


def v(spec: str, src: Edition, catalog: list[Edition], template: str, seed: int):  # type: ignore[no-untyped-def]
    f = perturbed_fields(src, ALL_TEMPLATES[template], seed)
    return f, label(judged_fields(f, src), src, catalog, spec)[:3]


def test_year_shift_claim_is_judged_as_written_and_never_assumes_abstain() -> None:
    src = ed("S", 2000)
    seed = next(
        s
        for s in range(200)
        if perturbed_fields(src, ALL_TEMPLATES["year_shift"], s)["publish_year"] == 2004
    )
    # another edition of the work matches the claimed year: v3 proposes THAT edition
    other = ed("O", 2004)
    f, (exp, gold, _) = v("v3", src, [src, other], "year_shift", seed)
    assert set(f) == {"title", "author", "publish_year"} and f["publish_year"] == 2004
    assert (exp, gold) == ("suggest", ["O"])
    # nothing matches: catalog absence, not contradiction, and no gold
    f, (exp, gold, reason) = v("v3", src, [src], "year_shift", seed)
    assert exp == "abstain" and gold == [] and reason and reason.startswith("catalog absence")
    assert "contradict" not in reason.split("(")[0]
    # an edition with an unknown year fits only via unknown: underspecified, not a suggestion
    _, (exp, gold, reason) = v("v3", src, [src, other, ed("U", None)], "year_shift", seed)
    assert exp == "abstain" and set(gold) == {"O", "U"} and reason.startswith("underspecified")
    # v2 would have forced the source in, which is exactly the assumption v3 removes
    _, (exp2, gold2, _) = v("v2", src, [src], "year_shift", seed)
    assert (exp2, gold2) == ("suggest", ["S"])


def test_year_shift_range_and_band() -> None:
    assert all(3 <= abs(d) <= 5 for d in YEAR_SHIFTS)  # never inside the runtime +-2 band
    assert not template_effective("year_shift", ed("S", None), 1)  # unknown year: not applicable
    assert not any(
        template_effective("year_shift", ed("S", 2026), s)
        and perturbed_fields(ed("S", 2026), ALL_TEMPLATES["year_shift"], s)["publish_year"] > 2026
        for s in range(50)
    )


def test_format_swap_changes_to_another_known_format() -> None:
    src = ed("S", fmt=PhysicalFormat.HARDCOVER)
    for s in range(30):
        f = perturbed_fields(src, ALL_TEMPLATES["format_swap"], s)
        assert set(f) == {"title", "author", "physical_format"}
        assert f["physical_format"] not in ("hardcover", "other", "unknown")
    assert not template_effective("format_swap", ed("S", fmt=PhysicalFormat.UNKNOWN), 1)


def test_conflict_templates_do_not_change_the_existing_rotation() -> None:
    names = [t for t, _ in TEMPLATES]
    assert "year_shift" not in names and "format_swap" not in names and len(names) == 6


def test_v3_equals_v2_when_the_source_fits_its_query() -> None:
    src, twin = ed("S"), ed("T", fmt=PhysicalFormat.HARDCOVER)
    for name, ops in TEMPLATES:
        f = perturbed_fields(src, ops, 3)
        j = judged_fields(f, src)
        assert label(j, src, [src, twin], "v2")[:3] == label(j, src, [src, twin], "v3")[:3], name


def test_assignment_reports_shortfall_and_unplaced_required_never_relaxes() -> None:
    e = ed("S")
    cands = {
        ("A1", "identifier"): Candidate("A1", "identifier", "isbn10_hyphenated", e, 1),
        ("B1", "identifier"): Candidate("B1", "identifier", "isbn10_hyphenated", e, 1),
        ("A2", "format_year_conflict"): Candidate("A2", "format_year_conflict", "year_shift", e, 1),
    }
    quotas = {"identifier": 2, "format_year_conflict": 1, "edition_ambiguity": 1}
    plan = assign(cands, ["A1", "A2", "A3"], ["B1"], quotas, 0)
    assert not plan.feasible
    assert plan.shortfall == {"edition_ambiguity": 1}
    assert plan.unplaced_required == ["A3"]
    assert {c.family for c in plan.assigned} == {"A1", "A2", "B1"}  # one query per family
    assert set(STRATA) >= set(quotas)


def test_reveal_uses_the_per_draft_spec(tmp_path: Path) -> None:
    from bera.evalkit.cases import EvalCase
    from bera.evalkit.drafts import Draft, Proposed
    from bera.labeling import LabelStore

    d = Draft(
        draft_id="x",
        split="dev",
        family="f",
        query={"title": "Dune"},
        template="year_shift",
        proposal_label_spec="v3",
        proposed=Proposed(expected="abstain", gold_edition_ids=[]),
    )
    case = EvalCase.model_validate(
        {
            "case_id": "x",
            "query": {"title": "Dune"},
            "expected": "abstain",
            "gold_edition_ids": [],
            "ambiguity_reason": "out_of_corpus",
            "family": "f",
            "origin": "program_drafted_human_labeled",
            "split": "dev",
            "labeler": "ob",
        }
    )
    store = LabelStore.__new__(LabelStore)
    store.proposal_spec = "v2"
    store.notes = {}
    assert store.proposal_view(d, case)["proposal_label_spec"] == "v3"
    with pytest.raises(KeyError):
        ALL_TEMPLATES["no_such_template"]
