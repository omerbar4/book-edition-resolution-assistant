"""Reproducible corpus construction from Open Library dumps.

Pass 1  stream editions -> per-edition feature rows in a scratch SQLite DB -> per-work stats
Select  strata rules fixed in code (below) -> sorted candidate keys -> seeded sampling
Pass 2  stream editions again -> keep editions of selected works (minus exclusions)
        -> optional works dump for work-level authors -> authors dump for names
Write   corpus.jsonl (sorted by edition_id) + manifest.json (inputs, digests, seed, quotas,
        stratum counts, drop reasons, exclusion verification, output digest)

Strata (all computed from pass-1 stats, BEFORE any filtering by outcome):
  S1 confusable  >= 8 editions with a valid ISBN and >= 2 known formats
  S2 translated  has English editions AND (another language OR translation_of/translated_from)
  S3 revised     some edition_name mentions revised/2nd+/anniversary/expanded/updated
  S4 companion   study-guide works whose stripped title equals a selected S1-S3 work title
  S5 box set     box-set works with >= 1 valid ISBN
  S6 same title  other works whose title equals a selected work's title (distractors)
  S7 random      English works with >= 1 valid ISBN (distractors)
  H  human seeds works whose title equals a title on the human seed list (all matches kept)
"""

from __future__ import annotations

import json
import random
import re
import sqlite3
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from bera import isbn as isbnlib
from bera.features import content_kind, parse_format
from bera.ingest.dumps import (
    DumpRow,
    ReadStats,
    Redirects,
    edition_author_keys,
    edition_work_key,
    file_digests,
    iter_dump,
    map_edition,
)
from bera.models import Edition, PhysicalFormat
from bera.text import norm_person, norm_text

_REVISED_RE = re.compile(
    r"\b(revised|rev|expanded|updated|anniversary|(?:[2-9]|1\d)(?:nd|rd|th)|second|third|fourth)\b"
)
_GUIDE_PREFIX_RE = re.compile(
    r"^(study guide|sparknotes|cliffsnotes|cliffs notes|summary of|workbook for|"
    r"companion to|readers guide)( (for|to|on))?\s*"
)


@dataclass(frozen=True)
class Quotas:
    s1_confusable: int = 60
    s2_translated: int = 30
    s3_revised: int = 30
    s4_companion_max: int = 40
    s5_box_set: int = 15
    s6_same_title_max: int = 40
    s7_random: int = 60
    max_editions_per_work: int = 60


@dataclass
class BuildInputs:
    editions: Path
    authors: Path
    redirects: Path | None = None
    works: Path | None = None
    human_seeds: Path | None = None  # JSONL {"title": ..., "author": ...}
    exclusions: Path | None = None  # JSONL {"isbn"?: ..., "title"?: ..., "author"?: ...}


@dataclass
class Manifest:
    source_label: str
    seed: int
    quotas: dict[str, int]
    python_version: str
    inputs: dict[str, Any] = field(default_factory=dict)
    read_stats: dict[str, dict[str, int]] = field(default_factory=dict)
    strata: dict[str, int] = field(default_factory=dict)
    selected_works: int = 0
    editions_written: int = 0
    dropped: dict[str, int] = field(default_factory=dict)
    exclusion_check: dict[str, Any] = field(default_factory=dict)
    human_seed_matches: dict[str, int] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)


def _load_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _edition_title(d: dict[str, Any]) -> str:
    raw_title, raw_prefix = d.get("title"), d.get("title_prefix")
    title: str = raw_title if isinstance(raw_title, str) else ""
    prefix: str = raw_prefix if isinstance(raw_prefix, str) else ""
    if prefix and not title.lower().startswith(prefix.lower()):
        title = f"{prefix} {title}"
    return norm_text(title)


# ---- pass 1 --------------------------------------------------------------------------------
def pass1_stats(
    editions: Path, redirects: Redirects, scratch: sqlite3.Connection, stats: ReadStats
) -> None:
    scratch.executescript("""
        DROP TABLE IF EXISTS ed;
        CREATE TABLE ed (work TEXT, has_isbn INT, fmt TEXT, eng INT, other_lang INT,
                         translated INT, revised INT, kind TEXT, ntitle TEXT);
    """)
    batch: list[tuple[Any, ...]] = []
    for row in iter_dump(editions, stats):
        if row.type != "/type/edition":
            continue
        d = row.data
        work = edition_work_key(d, redirects)
        if work is None:
            continue
        raw_isbns = [*d.get("isbn_10", []), *d.get("isbn_13", [])]
        has_isbn = any(isbnlib.parse(x).valid for x in raw_isbns if isinstance(x, str))
        fmt_raw = d.get("physical_format")
        fmt = parse_format(fmt_raw) if isinstance(fmt_raw, str) else PhysicalFormat.UNKNOWN
        langs = {
            lk.get("key", "").rsplit("/", 1)[-1]
            for lk in d.get("languages", [])
            if isinstance(lk, dict)
        }
        translated = bool(d.get("translation_of") or d.get("translated_from"))
        ed_name = d.get("edition_name") if isinstance(d.get("edition_name"), str) else ""
        title = _edition_title(d)
        subtitle = d.get("subtitle") if isinstance(d.get("subtitle"), str) else ""
        batch.append(
            (
                work,
                int(has_isbn),
                fmt.value,
                int("eng" in langs),
                int(bool(langs - {"eng"})),
                int(translated),
                int(bool(_REVISED_RE.search(norm_text(ed_name)))),
                content_kind(f"{title} {subtitle}"),
                title,
            )
        )
        if len(batch) >= 10_000:
            scratch.executemany("INSERT INTO ed VALUES (?,?,?,?,?,?,?,?,?)", batch)
            batch.clear()
    scratch.executemany("INSERT INTO ed VALUES (?,?,?,?,?,?,?,?,?)", batch)
    scratch.executescript("""
        DROP TABLE IF EXISTS works;
        CREATE TABLE works AS
        WITH titles AS (
            SELECT work, ntitle, COUNT(*) c,
                   ROW_NUMBER() OVER (PARTITION BY work ORDER BY COUNT(*) DESC, ntitle) rn
            FROM ed WHERE ntitle != '' GROUP BY work, ntitle
        )
        SELECT e.work, COUNT(*) n, SUM(has_isbn) n_isbn,
               COUNT(DISTINCT CASE WHEN fmt NOT IN ('unknown','other') THEN fmt END) n_fmt,
               MAX(eng) eng, MAX(other_lang) other_lang, MAX(translated) translated,
               MAX(revised) revised, MAX(kind = 'study_guide') guide, MAX(kind = 'box_set') boxset,
               (SELECT ntitle FROM titles t WHERE t.work = e.work AND rn = 1) title
        FROM ed e GROUP BY e.work;
        CREATE INDEX works_title ON works(title);
    """)


# ---- selection -----------------------------------------------------------------------------
def _sample(rng: random.Random, keys: Iterable[str], k: int, taken: set[str]) -> list[str]:
    pool = sorted(set(keys) - taken)
    picked = pool if len(pool) <= k else rng.sample(pool, k)
    picked = sorted(picked)
    taken.update(picked)
    return picked


def select_works(
    scratch: sqlite3.Connection,
    seed: int,
    q: Quotas,
    human_titles: list[str],
    excluded_titles: set[str],
    manifest: Manifest,
) -> set[str]:
    rng = random.Random(seed)  # noqa: S311 - reproducible sampling, not security

    def keys(sql: str, params: tuple[Any, ...] = ()) -> list[str]:
        rows = scratch.execute(sql, params).fetchall()
        return [r[0] for r in rows if (r[1] or "") not in excluded_titles]

    taken: set[str] = set()
    strata: dict[str, list[str]] = {}
    strata["H"] = []
    for title in human_titles:
        matches = keys("SELECT work, title FROM works WHERE title = ?", (title,))
        manifest.human_seed_matches[title] = len(matches)
        strata["H"] += [m for m in matches if m not in taken]
        taken.update(matches)
    strata["S1"] = _sample(
        rng,
        keys("SELECT work, title FROM works WHERE n_isbn >= 8 AND n_fmt >= 2"),
        q.s1_confusable,
        taken,
    )
    strata["S2"] = _sample(
        rng,
        keys("SELECT work, title FROM works WHERE eng = 1 AND (other_lang = 1 OR translated = 1)"),
        q.s2_translated,
        taken,
    )
    strata["S3"] = _sample(
        rng, keys("SELECT work, title FROM works WHERE revised = 1"), q.s3_revised, taken
    )

    core = strata["H"] + strata["S1"] + strata["S2"] + strata["S3"]
    core_titles = (
        {
            r[0]
            for r in scratch.execute(
                f"SELECT title FROM works WHERE work IN ({','.join('?' * len(core))})",  # noqa: S608
                core,
            )
            if r[0]
        }
        if core
        else set()
    )
    guides = [
        (w, t)
        for w, t in scratch.execute("SELECT work, title FROM works WHERE guide = 1 ORDER BY work")
        if _GUIDE_PREFIX_RE.sub("", t or "").strip() in core_titles
    ]
    strata["S4"] = _sample(rng, [w for w, _ in guides], q.s4_companion_max, taken)
    strata["S5"] = _sample(
        rng,
        keys("SELECT work, title FROM works WHERE boxset = 1 AND n_isbn >= 1"),
        q.s5_box_set,
        taken,
    )
    same: list[str] = []
    for t in sorted(core_titles):
        same += [w for (w,) in scratch.execute("SELECT work FROM works WHERE title = ?", (t,))]
    strata["S6"] = _sample(rng, same, q.s6_same_title_max, taken)
    strata["S7"] = _sample(
        rng, keys("SELECT work, title FROM works WHERE eng = 1 AND n_isbn >= 1"), q.s7_random, taken
    )

    manifest.strata = {k: len(v) for k, v in strata.items()}
    return set(taken)


# ---- pass 2 + write ------------------------------------------------------------------------
def build_corpus(
    inputs: BuildInputs,
    out_dir: Path,
    *,
    seed: int,
    source_label: str,
    quotas: Quotas | None = None,
    scratch_path: Path | None = None,
) -> Manifest:
    q = quotas or Quotas()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = Manifest(
        source_label=source_label,
        seed=seed,
        quotas=asdict(q),
        python_version=sys.version.split()[0],
    )
    for name in ("editions", "authors", "redirects", "works", "human_seeds", "exclusions"):
        path = getattr(inputs, name)
        if path is not None:
            manifest.inputs[name] = {"file": path.name, **file_digests(path)}

    redirects = Redirects.from_dump(inputs.redirects, ("/works/", "/authors/", "/books/"))
    human = [norm_text(r.get("title")) for r in _load_jsonl(inputs.human_seeds) if r.get("title")]
    excl = _load_jsonl(inputs.exclusions)
    excl_isbns = {
        p.isbn13 for p in (isbnlib.parse(str(r["isbn"])) for r in excl if r.get("isbn")) if p.valid
    }
    excl_titles = {norm_text(r["title"]) for r in excl if r.get("title")}

    scratch = sqlite3.connect(scratch_path or ":memory:")
    s1 = ReadStats()
    pass1_stats(inputs.editions, redirects, scratch, s1)
    manifest.read_stats["editions_pass1"] = asdict(s1)
    selected = select_works(scratch, seed, q, human, excl_titles, manifest)
    manifest.selected_works = len(selected)
    scratch.close()

    # pass 2: collect raw rows of selected works
    kept: dict[str, list[DumpRow]] = {}
    dropped: dict[str, int] = {}
    s2 = ReadStats()
    for row in iter_dump(inputs.editions, s2):
        if row.type != "/type/edition":
            continue
        work = edition_work_key(row.data, redirects)
        if work not in selected:
            continue
        raw = [*row.data.get("isbn_10", []), *row.data.get("isbn_13", [])]
        if any(isbnlib.parse(x).isbn13 in excl_isbns for x in raw if isinstance(x, str)):
            dropped["excluded_isbn"] = dropped.get("excluded_isbn", 0) + 1
            continue
        kept.setdefault(work, []).append(row)
    manifest.read_stats["editions_pass2"] = asdict(s2)

    for work, rows in kept.items():
        rows.sort(key=lambda r: r.key)
        if len(rows) > q.max_editions_per_work:
            dropped["over_work_cap"] = (
                dropped.get("over_work_cap", 0) + len(rows) - q.max_editions_per_work
            )
            kept[work] = rows[: q.max_editions_per_work]

    work_authors: dict[str, list[str]] = {}
    if inputs.works is not None:
        for row in iter_dump(inputs.works):
            if row.key in selected:
                ks = [
                    redirects.resolve(a["author"]["key"])
                    for a in row.data.get("authors", [])
                    if isinstance(a, dict)
                    and isinstance(a.get("author"), dict)
                    and isinstance(a["author"].get("key"), str)
                ]
                work_authors[row.key] = ks

    needed = {
        k for rows in kept.values() for r in rows for k in edition_author_keys(r.data, redirects)
    }
    needed |= {k for ks in work_authors.values() for k in ks}
    names: dict[str, str] = {}
    for row in iter_dump(inputs.authors):
        if row.key in needed:
            author_name = row.data.get("name") or row.data.get("personal_name")
            if isinstance(author_name, str) and author_name.strip():
                names[row.key] = author_name.strip()

    excl_pairs = {
        (norm_text(r["title"]), norm_person(r.get("author") or "")) for r in excl if r.get("title")
    }

    def excluded(e: Edition) -> bool:
        if {isbnlib.parse(x).isbn13 for x in (*e.isbn_10, *e.isbn_13)} & excl_isbns:
            return True
        authors = {norm_person(x) for x in e.authors}
        return any(norm_text(e.title) == t and (not a or a in authors) for t, a in excl_pairs)

    editions = []
    for rows in kept.values():
        for r in rows:
            e = map_edition(
                r,
                redirects=redirects,
                author_names=names,
                work_author_keys=work_authors,
                source=source_label,
            )
            if e is None:
                dropped["no_title_no_isbn"] = dropped.get("no_title_no_isbn", 0) + 1
            elif excluded(e):
                dropped["excluded_title_author"] = dropped.get("excluded_title_author", 0) + 1
            else:
                editions.append(e)
    editions.sort(key=lambda e: e.edition_id)
    manifest.dropped = dict(sorted(dropped.items()))

    # Independent re-check: out-of-corpus cases must really be absent from the output.
    violations = sorted(e.edition_id for e in editions if excluded(e))
    manifest.exclusion_check = {"exclusions": len(excl), "violations": violations}

    corpus = out_dir / "corpus.jsonl"
    with corpus.open("w", encoding="utf-8") as fh:
        for e in editions:
            fh.write(e.model_dump_json() + "\n")
    manifest.editions_written = len(editions)
    manifest.output = {"file": corpus.name, **file_digests(corpus)}
    (out_dir / "manifest.json").write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True))
    return manifest


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - thin CLI
    import argparse

    p = argparse.ArgumentParser(prog="bera-build-corpus")
    for name in ("editions", "authors"):
        p.add_argument(f"--{name}", type=Path, required=True)
    for name in ("redirects", "works", "human-seeds", "exclusions"):
        p.add_argument(f"--{name}", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--source-label", required=True)
    p.add_argument("--scratch", type=Path, help="on-disk scratch DB for large dumps")
    a = p.parse_args(argv)
    m = build_corpus(
        BuildInputs(a.editions, a.authors, a.redirects, a.works, a.human_seeds, a.exclusions),
        a.out,
        seed=a.seed,
        source_label=a.source_label,
        scratch_path=a.scratch,
    )
    print(
        json.dumps(
            {
                "editions": m.editions_written,
                "strata": m.strata,
                "violations": m.exclusion_check["violations"],
            }
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
