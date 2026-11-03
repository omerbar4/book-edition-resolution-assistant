"""Ingestion tests on tiny SYNTHETIC files in Open Library dump format (no download)."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

import pytest

from bera import isbn
from bera.ingest.corpus import BuildInputs, Quotas, build_corpus
from bera.ingest.dumps import Redirects, parse_year

_n = [5000]


def new_isbn() -> str:
    _n[0] += 1
    body = f"9780{_n[0]:08d}"
    return body + isbn.isbn13_check_digit(body)


def write_dump(path: Path, rows: list[tuple[str, str, dict[str, Any]]], junk: bool = False) -> Path:
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for type_, key, data in rows:
            fh.write(f"{type_}\t{key}\t1\t2026-10-31T00:00:00\t{json.dumps(data)}\n")
        if junk:
            fh.write("this line is malformed\n")
    return path


def ed(key: str, work: str, title: str, **kw: Any) -> tuple[str, str, dict[str, Any]]:
    data: dict[str, Any] = {"key": key, "title": title, "works": [{"key": work}], **kw}
    return ("/type/edition", key, data)


def lang(code: str) -> list[dict[str, str]]:
    return [{"key": f"/languages/{code}"}]


@pytest.fixture(scope="module")
def dumps(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    d = tmp_path_factory.mktemp("dumps")
    a1 = [{"key": "/authors/OL1A"}]
    rows: list[tuple[str, str, dict[str, Any]]] = []
    fmts = ["Hardcover", "Paperback", "Mass Market Paperback"]
    for i in range(9):  # W1: confusable (S1)
        rows.append(
            ed(
                f"/books/OL{100 + i}M",
                "/works/OL1W",
                "The Test Book",
                authors=a1,
                physical_format=fmts[i % 3],
                isbn_13=[new_isbn()],
                languages=lang("eng"),
                publish_date=["2001", "May 2003", "c1999?"][i % 3],
            )
        )
    rows.append(
        ed(
            "/books/OL120M",
            "/works/OL1W",
            "Test Book",
            title_prefix="The",
            authors=[{"key": "/authors/OL9A"}],
            isbn_13=[new_isbn()],
        )
    )  # redirected author
    rows.append(
        ed(
            "/books/OL121M",
            "/works/OL99W",
            "The Test Book",  # redirected work
            by_statement="by Jane Q. Doe",
            isbn_13=[new_isbn()],
        )
    )
    rows.append(
        ed(
            "/books/OL200M",
            "/works/OL2W",
            "Sea Glass",
            authors=a1,
            languages=lang("eng"),
            isbn_13=[new_isbn()],
        )
    )
    rows.append(
        ed(
            "/books/OL201M",
            "/works/OL2W",
            "Vidrio de mar",
            authors=a1,
            languages=lang("spa"),
            translation_of="Sea Glass",
            isbn_13=[new_isbn()],
        )
    )
    rows.append(
        ed(
            "/books/OL300M",
            "/works/OL3W",
            "Algorithms Primer",
            authors=a1,
            edition_name="2nd ed.",
            isbn_13=[new_isbn()],
            languages=lang("eng"),
        )
    )
    rows.append(
        ed(
            "/books/OL301M",
            "/works/OL9W",
            "Garden Chemistry",
            authors=a1,
            edition_name="Revised edition",
            isbn_13=[new_isbn()],
            languages=lang("eng"),
        )
    )
    rows.append(
        ed(
            "/books/OL400M",
            "/works/OL4W",
            "Study Guide: The Test Book",
            isbn_13=[new_isbn()],
            languages=lang("eng"),
        )
    )
    rows.append(
        ed(
            "/books/OL500M",
            "/works/OL5W",
            "Test Series Box Set",
            authors=a1,
            isbn_13=[new_isbn()],
            languages=lang("eng"),
        )
    )
    rows.append(
        ed(
            "/books/OL600M",
            "/works/OL6W",
            "The Test Book",
            authors=[{"key": "/authors/OL2A"}],
            isbn_13=[new_isbn()],
            languages=lang("eng"),
        )
    )
    for i in range(4):
        rows.append(
            ed(
                f"/books/OL{700 + i}M",
                f"/works/OL{70 + i}W",
                f"Random {i}",
                isbn_13=[new_isbn()],
                languages=lang("eng"),
            )
        )
    rows.append(
        (
            "/type/edition",
            "/books/OL799M",
            {"key": "/books/OL799M", "works": [{"key": "/works/OL70W"}]},
        )
    )  # no title/isbn
    hidden = new_isbn()
    rows.append(
        ed(
            "/books/OL800M",
            "/works/OL8W",
            "Hidden Book",
            authors=a1,
            isbn_13=[hidden],
            languages=lang("eng"),
        )
    )
    rows.append(
        ed(
            "/books/OL801M",
            "/works/OL71W",
            "Hidden Book",  # same title elsewhere
            authors=a1,
            isbn_13=[new_isbn()],
            languages=lang("eng"),
        )
    )
    authors = [
        ("/type/author", "/authors/OL1A", {"name": "Ada Lumen"}),
        ("/type/author", "/authors/OL2A", {"name": "Other Writer"}),
        ("/type/author", "/authors/OL3A", {"name": "Work Level Author"}),
    ]
    redirects = [
        ("/type/redirect", "/authors/OL9A", {"location": "/authors/OL1A"}),
        ("/type/redirect", "/works/OL99W", {"location": "/works/OL1W"}),
        ("/type/redirect", "/authors/OLXA", {"location": "/authors/OLYA"}),
        ("/type/redirect", "/authors/OLYA", {"location": "/authors/OLXA"}),
    ]  # cycle
    works = [("/type/work", "/works/OL70W", {"authors": [{"author": {"key": "/authors/OL3A"}}]})]
    excl = d / "exclusions.jsonl"
    excl.write_text(
        json.dumps({"isbn": hidden})
        + "\n"
        + json.dumps({"title": "Hidden Book", "author": "Ada Lumen"})
        + "\n"
    )
    seeds = d / "seeds.jsonl"
    seeds.write_text(json.dumps({"title": "Algorithms Primer", "author": "Ada Lumen"}) + "\n")
    return {
        "editions": write_dump(d / "editions.txt.gz", rows, junk=True),
        "authors": write_dump(d / "authors.txt.gz", authors),
        "redirects": write_dump(d / "redirects.txt.gz", redirects),
        "works": write_dump(d / "works.txt.gz", works),
        "exclusions": excl,
        "seeds": seeds,
    }


Q = Quotas(
    s1_confusable=5,
    s2_translated=5,
    s3_revised=5,
    s4_companion_max=5,
    s5_box_set=5,
    s6_same_title_max=5,
    s7_random=10,
    max_editions_per_work=50,
)


def build(dumps: dict[str, Path], out: Path, seed: int = 7) -> Any:
    inputs = BuildInputs(
        dumps["editions"],
        dumps["authors"],
        dumps["redirects"],
        dumps["works"],
        dumps["seeds"],
        dumps["exclusions"],
    )
    return build_corpus(inputs, out, seed=seed, source_label="test-dump", quotas=Q)


def corpus(out: Path) -> dict[str, dict[str, Any]]:
    rows = [json.loads(x) for x in (out / "corpus.jsonl").read_text().splitlines()]
    return {r["edition_id"]: r for r in rows}


def test_build_is_deterministic(dumps: dict[str, Path], tmp_path: Path) -> None:
    m1, m2 = build(dumps, tmp_path / "a"), build(dumps, tmp_path / "b")
    assert m1.output["sha256"] == m2.output["sha256"]
    assert m1.strata == m2.strata


def test_strata_and_provenance(dumps: dict[str, Path], tmp_path: Path) -> None:
    m = build(dumps, tmp_path)
    assert m.strata["H"] == 1  # human seed resolved by title before sampling
    for s in ("S1", "S2", "S3", "S4", "S5", "S6", "S7"):
        assert m.strata[s] >= 1, s
    assert m.read_stats["editions_pass1"]["malformed"] == 1
    assert m.inputs["editions"]["sha256"] and m.inputs["editions"]["bytes"] > 0
    assert m.dropped["no_title_no_isbn"] == 1


def test_field_mapping(dumps: dict[str, Path], tmp_path: Path) -> None:
    build(dumps, tmp_path)
    c = corpus(tmp_path)
    assert c["OL120M"]["title"] == "The Test Book"  # title_prefix joined
    assert c["OL120M"]["authors"] == ["Ada Lumen"]  # author key followed through a redirect
    assert c["OL121M"]["work_id"] == "OL1W"  # work key followed through a redirect
    assert c["OL121M"]["field_provenance"]["authors"] == "by_statement"
    assert c["OL700M"]["authors"] == ["Work Level Author"]
    assert c["OL700M"]["field_provenance"]["authors"] == "work_keys"
    assert c["OL201M"]["translation_of"] == "Sea Glass" and c["OL201M"]["languages"] == ["spa"]
    assert c["OL100M"]["physical_format"] == "hardcover"
    assert c["OL100M"]["synthetic"] is False and c["OL100M"]["source"] == "test-dump"
    assert c["OL600M"]["authors"] == ["Other Writer"]


def test_exclusions_are_absent_and_verified(dumps: dict[str, Path], tmp_path: Path) -> None:
    m = build(dumps, tmp_path)
    c = corpus(tmp_path)
    assert "OL800M" not in c and "OL801M" not in c
    assert m.exclusion_check["violations"] == []


def test_parse_year_statuses() -> None:
    assert parse_year("2001") == (2001, "exact")
    assert parse_year("May 2003") == (2003, "year_only")
    assert parse_year("1999-2003") == (None, "unparseable")
    assert parse_year(None) == (None, "missing")


def test_redirect_cycle_is_safe() -> None:
    r = Redirects({"/a": "/b", "/b": "/a"})
    assert r.resolve("/a") in {"/a", "/b"}
