"""Held-out plan regression: full feasibility including probes and reserves. Synthetic only."""

from __future__ import annotations

import random

from bera import isbn
from bera.evalkit.heldout import counts, family_checks, heldout_probes, probe_drafts
from bera.evalkit.splits import family_split
from bera.evalkit.stratified import assign, candidates, to_drafts
from bera.models import Edition, PhysicalFormat

SEED = 0


def isbn_of(n: int) -> str:
    body = f"9780{n:08d}"
    return body + isbn.isbn13_check_digit(body)


def heldout_names(prefix: str, n: int) -> list[str]:
    out, i = [], 0
    while len(out) < n:
        name = f"{prefix}{i}"
        if family_split(name, SEED) == "heldout":
            out.append(name)
        i += 1
    return out


def catalog_for(families: list[str]) -> tuple[list[Edition], dict[str, str]]:
    eds, fam_of = [], {}
    for k, f in enumerate(families):
        wid = f"W{k}"
        fam_of[wid] = f
        eds.append(
            Edition.model_validate(
                {
                    "edition_id": f"E{k}",
                    "work_id": wid,
                    "title": f"Book number {k}",
                    "authors": (f"Author Person{k}",),
                    "physical_format": PhysicalFormat.PAPERBACK,
                    "publish_year": 2000 + k % 10,
                    "isbn_13": (isbn_of(k + 1),),
                    "source": "test",
                    "synthetic": True,
                }
            )
        )
    return eds, fam_of


def probe_rows() -> tuple[list[dict], dict]:
    # three verified-absent probes whose families are held-out; two share an author key
    shared = next(
        k
        for k in (f"a{i}" for i in range(500))
        if family_split(f"probe-author:{k}", SEED) == "heldout"
    )
    other = next(
        k
        for k in (f"b{i}" for i in range(500))
        if family_split(f"probe-author:{k}", SEED) == "heldout"
    )
    rows = [
        {"title": "Absent one", "author": "X", "author_keys": [shared]},
        {"title": "Absent two", "author": "X", "author_keys": [shared]},
        {"title": "Absent three", "author": "Y", "author_keys": [other]},
    ]
    status = {r["title"]: {"status": "verified_absent"} for r in rows}
    return rows, status


def full_plan() -> tuple[list, list, list]:
    fams = heldout_names("fam:h", 8)
    eds, fam_of = catalog_for(fams)
    by_family = {fam_of[e.work_id or ""]: [e] for e in eds}
    quotas = {"identifier": 2, "format_year_conflict": 2}
    c = candidates(by_family, fams, set(), eds, SEED)
    plan = assign(c, [], fams, quotas, 2)
    assert plan.feasible
    rng = random.Random(SEED)
    taken: set[str] = set()
    in_corpus = to_drafts(plan.assigned, eds, "h01", rng, taken, split="heldout")
    reserves = to_drafts(plan.reserves, eds, "h01", rng, taken, split="heldout")
    rows, status = probe_rows()
    probes = probe_drafts(heldout_probes(rows, status, SEED, 3), "h01", rng, taken)
    return in_corpus, probes, reserves


def test_full_feasibility_with_shared_probe_family_and_reserves() -> None:
    in_corpus, probes, reserves = full_plan()
    checks = family_checks(in_corpus, probes, reserves, 4, 3, 2)
    assert all(checks.values()), checks
    c = counts(in_corpus, probes)
    assert c["queries"] == 7 and c["probe_families"] == 2 and c["families"] == 6  # pair kept
    assert all(d.split == "heldout" for d in in_corpus + probes + reserves)


def test_duplicate_in_corpus_family_fails() -> None:
    in_corpus, probes, reserves = full_plan()
    dup = in_corpus[1].model_copy(update={"family": in_corpus[0].family})
    checks = family_checks([in_corpus[0], dup, *in_corpus[2:]], probes, reserves, 4, 3, 2)
    assert not all(checks.values())


def test_reserve_overlapping_the_queue_fails() -> None:
    in_corpus, probes, reserves = full_plan()
    bad = reserves[0].model_copy(update={"family": in_corpus[0].family})
    assert not all(family_checks(in_corpus, probes, [bad, reserves[1]], 4, 3, 2).values())
    same = reserves[1].model_copy(update={"family": reserves[0].family})
    assert not all(family_checks(in_corpus, probes, [reserves[0], same], 4, 3, 2).values())


def test_probe_family_shared_with_in_corpus_or_reserve_fails() -> None:
    in_corpus, probes, reserves = full_plan()
    bad = probes[0].model_copy(update={"family": in_corpus[0].family})
    assert not all(family_checks(in_corpus, [bad, *probes[1:]], reserves, 4, 3, 2).values())
    bad2 = probes[0].model_copy(update={"family": reserves[0].family})
    assert not all(family_checks(in_corpus, [bad2, *probes[1:]], reserves, 4, 3, 2).values())


def test_wrong_probe_count_fails() -> None:
    in_corpus, probes, reserves = full_plan()
    assert not all(family_checks(in_corpus, probes[:2], reserves, 4, 3, 2).values())
