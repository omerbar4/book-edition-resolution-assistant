from __future__ import annotations

from bera.ingest.quality import (
    AuditEdition,
    AuthorRecord,
    EdFeat,
    WorkInfo,
    author_ambiguity,
    build_families,
    probe_audit,
    sample_editions,
)


def feats() -> list[EdFeat]:
    out = []
    for i in range(40):  # 40 near-identical English paperbacks from one publisher
        out.append(EdFeat(f"/books/OL{i}M", "paperback", "eng", 2000 + i % 3, "penguin", None))
    out += [
        EdFeat("/books/OL100M", "hardcover", "eng", 1951, "little brown", "1st edition"),
        EdFeat("/books/OL101M", "paperback", "spa", 1990, "edhasa", None),
        EdFeat("/books/OL102M", "audiobook", "eng", 2015, "audible", None),
        EdFeat("/books/OL103M", "mass_market_paperback", "fre", 1970, "folio", None),
        EdFeat("/books/OL104M", None, None, None, None, None),
    ]
    return out


def test_sampling_is_deterministic_and_keeps_rare_values() -> None:
    a, rep = sample_editions(feats(), cap=10, seed=1)
    b, _ = sample_editions(feats(), cap=10, seed=1)
    assert a == b and len(a) == 10
    assert {"/books/OL100M", "/books/OL101M", "/books/OL102M", "/books/OL103M"} <= set(a)
    assert rep.distinct_kept["format"] == rep.distinct_available["format"]
    assert rep.distinct_kept["language"] == rep.distinct_available["language"]


def test_sampling_reports_unmet_dimensions() -> None:
    many = [
        EdFeat(f"/books/OL{i}M", "paperback", "eng", 1900 + i, f"pub{i}", None) for i in range(30)
    ]
    _, rep = sample_editions(many, cap=5, seed=2)
    assert "publisher" in rep.unmet_dimensions and rep.kept == 5


def test_small_works_keep_everything() -> None:
    keys, rep = sample_editions(feats()[:3], cap=60, seed=3)
    assert len(keys) == 3 and rep.unmet_dimensions == []


def test_families_merge_aliases_translations_guides() -> None:
    works = [
        WorkInfo("/works/A", {"1984"}, set(), {"/authors/X"}, alias_group="orwell"),
        WorkInfo("/works/B", {"nineteen eighty four"}, set(), set(), alias_group="orwell"),
        WorkInfo("/works/C", {"petit prince"}, set(), {"/authors/Y"}),
        WorkInfo("/works/D", {"principito"}, {"petit prince"}, set()),
        WorkInfo(
            "/works/E", {"study guide great gatsby"}, set(), set(), guide_target="great gatsby"
        ),
        WorkInfo("/works/F", {"great gatsby"}, set(), {"/authors/Z"}),
        WorkInfo("/works/G", {"unrelated"}, set(), {"/authors/Q"}),
        WorkInfo("/works/H", {"another"}, set(), {"/authors/Q"}),
    ]
    fam = build_families(works).family_of
    assert fam["/works/A"] == fam["/works/B"]
    assert fam["/works/C"] == fam["/works/D"]
    assert fam["/works/E"] == fam["/works/F"]
    assert fam["/works/G"] == fam["/works/H"]  # shared (provisional) author key
    assert len({fam[w] for w in ("/works/A", "/works/C", "/works/E", "/works/G")}) == 4


def test_author_ambiguity_flags() -> None:
    recs = [
        AuthorRecord("OL1A", "Andrew Hunt", "1964"),
        AuthorRecord("OL2A", "Andrew Hunt", "1968"),
    ]
    r = author_ambiguity(recs, {"OL1A": 3, "OL2A": 1})
    assert r["status"] == "provisional_identity_candidates"
    assert "different_birth_years_likely_different_people" in r["flags"]
    assert "several_candidate_records_credited_in_matched_works" in r["flags"]


def test_probe_audit_quarantines_on_resemblance_or_missing_author() -> None:
    eds = [
        AuditEdition("E1", "remains day", "", "", frozenset({"someone"}), ""),
        AuditEdition("E2", "station eleven companion", "", "", frozenset(), ""),
    ]
    clean = probe_audit("never let me go", "kazuo ishiguro", "ishiguro", 2, eds)
    assert clean["status"] == "verified_absent"
    hit = probe_audit("station eleven", "emily st john mandel", "mandel", 1, eds)
    assert hit["status"] == "quarantined" and hit["hits"][0]["edition_id"] == "E2"
    unresolved = probe_audit("never let me go", "kazuo ishiguro", "ishiguro", 0, eds)
    assert unresolved["status"] == "quarantined"


def test_bulk_title_hits_match_per_title_rule() -> None:
    from bera.ingest.corpus import ExclusionRules, bulk_title_hits

    rules = ExclusionRules.load(
        [
            {
                "title": "Gödel, Escher, Bach",
                "author": "Douglas R. Hofstadter",
                "author_keys": ["OL1A"],
            },
            {"title": "Middlemarch", "author": "George Eliot", "author_keys": ["OL2A"]},
        ]
    )
    titles = [
        "godel escher bach",
        "godel escher bach eternal golden braid",
        "godel escher bash",
        "middlemarch study provincial life",
        "middle march",
        "escher prints",
        "bach cello suites",
        "unrelated",
    ]
    assert bulk_title_hits(titles, rules) == {t for t in titles if rules.title_hit(t)}


def test_r4_by_statement_catches_authorless_partial_title() -> None:
    from bera.ingest.corpus import ExclusionRules

    rules = ExclusionRules.load(
        [{"title": "The Remains of the Day", "author": "Kazuo Ishiguro", "author_keys": ["OL9A"]}]
    )
    reason = rules.edition_reason(
        author_keys=set(),
        ftitle="remains",
        ftrans="",
        by_statement="by Kazuo Ishiguro",
        isbn13s=set(),
    )
    assert reason == "R4_by_statement"
    assert (
        rules.edition_reason(
            author_keys=set(),
            ftitle="remains",
            ftrans="",
            by_statement="by someone else",
            isbn13s=set(),
        )
        is None
    )
