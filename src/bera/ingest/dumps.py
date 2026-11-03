"""Streaming readers for Open Library dump files and record mapping.

Dump line format (https://openlibrary.org/developers/dumps): tab-separated
`type, key, revision, last_modified, JSON`. Files may be gzip-compressed.

Mapping rules (docs/DATA_CARD.md):
- Only factual fields are kept. Descriptions, excerpts, notes, TOCs and covers are dropped.
- `title_prefix` (e.g. "The ") is joined to `title` when present.
- Authors, in priority order: edition `authors[].key` -> work `authors[].author.key` (only
  if a works dump was supplied) -> raw `by_statement` text (provenance "by_statement") ->
  none (provenance "unresolved"). Keys follow redirects (<= 5 hops, cycle-safe).
- `publish_date` is kept raw; a year is parsed with status exact/year_only/unparseable.
- `physical_format` is mapped through the documented synonym table; the raw value is kept.
- Missing values stay None/empty. Nothing is imputed.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

from bera.features import parse_format
from bera.models import Edition, PhysicalFormat

MAX_REDIRECT_HOPS = 5
_YEAR_RE = re.compile(r"\b(1[5-9]\d\d|20\d\d)\b")
_EXACT_DATE_RE = re.compile(r"^\s*(1[5-9]\d\d|20\d\d)\s*$")


@dataclass(frozen=True)
class DumpRow:
    type: str
    key: str
    revision: int
    last_modified: str
    data: dict[str, Any]


@dataclass
class ReadStats:
    lines: int = 0
    malformed: int = 0


def open_text(path: Path) -> IO[str]:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def iter_dump(path: Path, stats: ReadStats | None = None) -> Iterator[DumpRow]:
    stats = stats if stats is not None else ReadStats()
    with open_text(path) as fh:
        for line in fh:
            stats.lines += 1
            parts = line.rstrip("\n").split("\t", 4)
            if len(parts) != 5:
                stats.malformed += 1
                continue
            try:
                data = json.loads(parts[4])
                rev = int(parts[2])
            except (ValueError, json.JSONDecodeError):
                stats.malformed += 1
                continue
            if not isinstance(data, dict):
                stats.malformed += 1
                continue
            yield DumpRow(parts[0], parts[1], rev, parts[3], data)


def file_digests(path: Path, chunk: int = 1 << 20) -> dict[str, str | int]:
    sha1, sha256 = hashlib.sha1(usedforsecurity=False), hashlib.sha256()
    size = 0
    with path.open("rb") as fh:
        while block := fh.read(chunk):
            sha1.update(block)
            sha256.update(block)
            size += len(block)
    return {"bytes": size, "sha1": sha1.hexdigest(), "sha256": sha256.hexdigest()}


class Redirects:
    def __init__(self, mapping: Mapping[str, str] | None = None) -> None:
        self.mapping: dict[str, str] = dict(mapping or {})

    @classmethod
    def from_dump(cls, path: Path | None, wanted_prefixes: tuple[str, ...] = ()) -> Redirects:
        out: dict[str, str] = {}
        if path is not None:
            for row in iter_dump(path):
                loc = row.data.get("location")
                if isinstance(loc, str) and (
                    not wanted_prefixes or row.key.startswith(wanted_prefixes)
                ):
                    out[row.key] = loc
        return cls(out)

    def resolve(self, key: str) -> str:
        seen = {key}
        cur = key
        for _ in range(MAX_REDIRECT_HOPS):
            nxt = self.mapping.get(cur)
            if nxt is None or nxt in seen:
                return cur
            seen.add(nxt)
            cur = nxt
        return cur


def _key_list(value: Any, inner: str | None = None) -> list[str]:
    out: list[str] = []
    if not isinstance(value, list):
        return out
    for item in value:
        if inner is not None and isinstance(item, dict):
            item = item.get(inner)
        if isinstance(item, dict) and isinstance(item.get("key"), str):
            out.append(item["key"])
    return out


def _str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [v.strip() for v in value if isinstance(v, str) and v.strip()]
    return []


def _opt_str(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def parse_year(raw: str | None) -> tuple[int | None, str]:
    if not raw:
        return None, "missing"
    if _EXACT_DATE_RE.match(raw):
        return int(raw.strip()), "exact"
    years = _YEAR_RE.findall(raw)
    if len(set(years)) == 1:
        return int(years[0]), "year_only"
    return None, "unparseable"


def edition_work_key(data: Mapping[str, Any], redirects: Redirects) -> str | None:
    works = _key_list(data.get("works"))
    return redirects.resolve(works[0]) if works else None


def edition_author_keys(data: Mapping[str, Any], redirects: Redirects) -> list[str]:
    return [redirects.resolve(k) for k in _key_list(data.get("authors"))]


def map_edition(
    row: DumpRow,
    *,
    redirects: Redirects,
    author_names: Mapping[str, str],
    work_author_keys: Mapping[str, list[str]],
    source: str,
) -> Edition | None:
    d = row.data
    title = _opt_str(d.get("title"))
    prefix = _opt_str(d.get("title_prefix"))
    if title and prefix and not title.lower().startswith(prefix.lower()):
        title = f"{prefix} {title}"
    isbn10 = _str_list(d.get("isbn_10"))
    isbn13 = _str_list(d.get("isbn_13"))
    if not title and not (isbn10 or isbn13):
        return None
    prov: dict[str, str] = {}
    work = edition_work_key(d, redirects)

    keys = edition_author_keys(d, redirects)
    if keys:
        prov["authors"] = "edition_keys"
    elif work and work_author_keys.get(work):
        keys = work_author_keys[work]
        prov["authors"] = "work_keys"
    authors = [author_names[k] for k in keys if k in author_names]
    if keys and len(authors) < len(keys):
        prov["authors"] += f";unresolved={len(keys) - len(authors)}"
    if not authors:
        by = _opt_str(d.get("by_statement"))
        if by:
            authors, prov["authors"] = [by], "by_statement"
        else:
            prov["authors"] = "unresolved"

    date_raw = _opt_str(d.get("publish_date"))
    year, prov["publish_year"] = parse_year(date_raw)
    fmt_raw = _opt_str(d.get("physical_format"))
    fmt = parse_format(fmt_raw) if fmt_raw else PhysicalFormat.UNKNOWN
    if fmt_raw and fmt is PhysicalFormat.UNKNOWN:
        fmt = PhysicalFormat.OTHER
    pages = d.get("number_of_pages")
    languages = [k.rsplit("/", 1)[-1] for k in _key_list(d.get("languages"))]

    return Edition(
        edition_id=row.key.rsplit("/", 1)[-1],
        work_id=work.rsplit("/", 1)[-1] if work else None,
        title=title or "",
        subtitle=_opt_str(d.get("subtitle")),
        authors=tuple(authors),
        publishers=tuple(_str_list(d.get("publishers"))),
        publish_date_raw=date_raw,
        publish_year=year,
        physical_format=fmt,
        physical_format_raw=fmt_raw,
        edition_name=_opt_str(d.get("edition_name")),
        languages=tuple(languages),
        isbn_10=tuple(isbn10),
        isbn_13=tuple(isbn13),
        number_of_pages=pages if isinstance(pages, int) and 0 < pages < 100_000 else None,
        series=tuple(_str_list(d.get("series"))),
        translation_of=_opt_str(d.get("translation_of")),
        source=source,
        synthetic=False,
        field_provenance=prov,
    )
