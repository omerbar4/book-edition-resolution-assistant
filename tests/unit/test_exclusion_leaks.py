"""An excluded (out-of-corpus) probe must not re-enter through another title, edition,
translation, omnibus, study guide, author-less record, or random sampling. Synthetic dumps."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

import pytest

from bera import isbn
from bera.ingest.corpus import BuildInputs, Quotas, build_corpus

_n = [7000]


def new_isbn() -> str:
    _n[0] += 1
    body = f"9780{_n[0]:08d}"
    return body + isbn.isbn13_check_digit(body)


def dump(path: Path, rows: list[tuple[str, str, dict[str, Any]]]) -> Path:
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for t, k, d in rows:
            fh.write(f"{t}\t{k}\t1\t2026-10-31T00:00:00\t{json.dumps(d)}\n")
    return path


def ed(key: str, work: str, title: str, **kw: Any) -> tuple[str, str, dict[str, Any]]:
    data = {
        "key": key,
        "title": title,
        "works": [{"key": work}],
        "isbn_13": [new_isbn()],
        "languages": [{"key": "/languages/eng"}],
        **kw,
    }
    return ("/type/edition", key, data)


PROBE_AUTHOR = [{"key": "/authors/OL50A"}]
OTHER = [{"key": "/authors/OL60A"}]
LEAKS = {
    "OL500M": ed("/books/OL500M", "/works/OL50W", "Gödel Sample Book", authors=PROBE_AUTHOR),
    "OL510M": ed("/books/OL510M", "/works/OL51W", "Godel Sample Book"),  # accent variant
    "OL520M": ed(
        "/books/OL520M",
        "/works/OL52W",
        "Libro de muestra",  # retitled translation
        authors=PROBE_AUTHOR,
        languages=[{"key": "/languages/spa"}],
    ),
    "OL530M": ed(
        "/books/OL530M",
        "/works/OL53W",
        "Collected Novels Omnibus",
        authors=[{"key": "/authors/OL59A"}],
    ),  # credited via a redirected author key
    "OL540M": ed("/books/OL540M", "/works/OL54W", "Study Guide: Godel Sample Book", authors=OTHER),
    "OL550M": ed(
        "/books/OL550M",
        "/works/OL55W",
        "Muestra",
        authors=OTHER,
        translation_of="Gödel Sample Book",
    ),
    "OL560M": ed(
        "/books/OL560M", "/works/OL56W", "The Gödel Sample Book", by_statement="by P. Author"
    ),
}


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, Path]:
    d = tmp_path_factory.mktemp("leak")
    rows = list(LEAKS.values())
    for i in range(6):  # legitimate random-sample candidates
        rows.append(
            ed(f"/books/OL{800 + i}M", f"/works/OL{80 + i}W", f"Ordinary Book {i}", authors=OTHER)
        )
    rows.append(ed("/books/OL900M", "/works/OL90W", "Shared Title", authors=OTHER))
    rows.append(
        ed("/books/OL901M", "/works/OL91W", "Shared Title", authors=[{"key": "/authors/OL61A"}])
    )
    excl = d / "excl.jsonl"
    excl.write_text(
        json.dumps(
            {"title": "Gödel Sample Book", "author": "Probe Author", "author_keys": ["OL50A"]}
        )
        + "\n"
    )
    seeds = d / "seeds.jsonl"
    seeds.write_text(
        json.dumps({"title": "Shared Title", "author": "Third Writer", "author_keys": ["OL61A"]})
        + "\n"
    )
    inputs = BuildInputs(
        dump(d / "e.gz", rows),
        dump(
            d / "a.gz",
            [
                ("/type/author", "/authors/OL50A", {"name": "Probe Author"}),
                ("/type/author", "/authors/OL60A", {"name": "Other Writer"}),
                ("/type/author", "/authors/OL61A", {"name": "Third Writer"}),
            ],
        ),
        dump(d / "r.gz", [("/type/redirect", "/authors/OL59A", {"location": "/authors/OL50A"})]),
        None,
        seeds,
        excl,
    )
    q = Quotas(
        s1_confusable=50,
        s2_translated=50,
        s3_revised=50,
        s4_companion_max=50,
        s5_box_set=50,
        s6_same_title_max=50,
        s7_random=50,
    )
    preview = build_corpus(
        inputs, d / "preview", seed=3, source_label="t", quotas=q, preview_only=True
    )
    m = build_corpus(inputs, d / "out", seed=3, source_label="t", quotas=q)
    return (preview, m), d


def test_no_leak_path_reaches_the_corpus(built: tuple[Any, Path]) -> None:
    (_, m), d = built
    ids = {
        json.loads(line)["edition_id"]
        for line in (d / "out" / "corpus.jsonl").read_text().splitlines()
    }
    assert not ids & set(LEAKS), sorted(ids & set(LEAKS))
    assert {"OL800M", "OL801M"} <= ids  # random sampling still works for ordinary works
    assert m.exclusion_check["violations"] == []


def test_preview_lists_every_excluded_work_with_rule(built: tuple[Any, Path]) -> None:
    (preview, _), d = built
    p = json.loads((d / "preview" / "selection_preview.json").read_text())
    rules = {r["work"]: r["rule"] for r in p["excluded_works"]}
    assert rules == {
        "OL50W": "R1_author_key",
        "OL51W": "R2_title",
        "OL52W": "R1_author_key",
        "OL53W": "R1_author_key",
        "OL54W": "R2_title",
        "OL55W": "R3_translation_of",
        "OL56W": "R2_title",
    }
    assert not (d / "preview" / "corpus.jsonl").exists()  # preview never builds a corpus
    assert preview.selected_works == len(p["selected"])


def test_seed_title_is_author_constrained(built: tuple[Any, Path]) -> None:
    (_, _), d = built
    p = json.loads((d / "preview" / "selection_preview.json").read_text())
    h = [r["work"] for r in p["selected"] if r["stratum"] == "H"]
    assert h == ["OL91W"]  # same title by another author is not taken as the seed
