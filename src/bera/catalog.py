"""SQLite catalog: edition records, an ISBN index that keeps duplicates, and FTS5 indexes.

Tables
- editions(edition_id PK, work_id, record_json, source, synthetic)
- isbn_index(isbn13, edition_id)       -- canonical ISBN-13; one ISBN may map to MANY editions
- invalid_isbns(raw, edition_id)       -- catalog ISBNs failing checksum: kept, never exact-matched
- editions_fts  (FTS5, unicode61 + diacritics removal + porter)  -- BM25 lexical search
- editions_tri  (FTS5 trigram)                                    -- typo-tolerant substring search
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

from bera import isbn as isbnlib
from bera.models import Edition
from bera.text import norm_person, norm_text

SCHEMA = """
CREATE TABLE IF NOT EXISTS editions (
    edition_id TEXT PRIMARY KEY,
    work_id TEXT,
    record_json TEXT NOT NULL,
    source TEXT NOT NULL,
    synthetic INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS isbn_index (
    isbn13 TEXT NOT NULL,
    edition_id TEXT NOT NULL REFERENCES editions(edition_id),
    PRIMARY KEY (isbn13, edition_id)
);
CREATE TABLE IF NOT EXISTS invalid_isbns (
    raw TEXT NOT NULL,
    edition_id TEXT NOT NULL REFERENCES editions(edition_id)
);
CREATE TABLE IF NOT EXISTS catalog_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE VIRTUAL TABLE IF NOT EXISTS editions_fts USING fts5(
    edition_id UNINDEXED, title, authors, publishers, extra,
    tokenize = 'porter unicode61 remove_diacritics 2'
);
CREATE VIRTUAL TABLE IF NOT EXISTS editions_tri USING fts5(
    edition_id UNINDEXED, text, tokenize = 'trigram'
);
"""


def check_sqlite_features() -> None:
    """Fail fast if this SQLite build lacks FTS5 or the trigram tokenizer (SQLite >= 3.34)."""
    con = sqlite3.connect(":memory:")
    try:
        con.execute("CREATE VIRTUAL TABLE t USING fts5(x, tokenize='trigram')")
    except sqlite3.OperationalError as exc:  # pragma: no cover - environment specific
        raise RuntimeError(f"SQLite FTS5 trigram support missing: {exc}") from exc
    finally:
        con.close()


class Catalog:
    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        check_sqlite_features()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        try:
            yield con
        finally:
            con.close()

    # ---- build ----------------------------------------------------------------------------
    def build(self, editions: Iterable[Edition], meta: dict[str, str] | None = None) -> int:
        n = 0
        with self.connect() as con:
            con.executescript(SCHEMA)
            for e in editions:
                self._insert(con, e)
                n += 1
            for k, v in (meta or {}).items():
                con.execute("INSERT OR REPLACE INTO catalog_meta VALUES (?, ?)", (k, v))
            con.commit()
        return n

    @staticmethod
    def _insert(con: sqlite3.Connection, e: Edition) -> None:
        con.execute(
            "INSERT INTO editions VALUES (?, ?, ?, ?, ?)",
            (e.edition_id, e.work_id, e.model_dump_json(), e.source, int(e.synthetic)),
        )
        for raw in (*e.isbn_10, *e.isbn_13):
            p = isbnlib.parse(raw)
            if p.valid and p.isbn13:
                con.execute(
                    "INSERT OR IGNORE INTO isbn_index VALUES (?, ?)", (p.isbn13, e.edition_id)
                )
            else:
                con.execute("INSERT INTO invalid_isbns VALUES (?, ?)", (raw, e.edition_id))
        title = norm_text(f"{e.title} {e.subtitle or ''}")
        authors = " ".join(norm_person(a) for a in e.authors)
        publishers = norm_text(" ".join(e.publishers))
        extra = norm_text(" ".join([e.edition_name or "", *e.series, e.translation_of or ""]))
        con.execute(
            "INSERT INTO editions_fts VALUES (?, ?, ?, ?, ?)",
            (e.edition_id, title, authors, publishers, extra),
        )
        con.execute("INSERT INTO editions_tri VALUES (?, ?)", (e.edition_id, f"{title} {authors}"))

    # ---- read -----------------------------------------------------------------------------
    def get(self, edition_ids: Iterable[str]) -> dict[str, Edition]:
        ids = list(dict.fromkeys(edition_ids))
        if not ids:
            return {}
        with self.connect() as con:
            rows = con.execute(
                f"SELECT edition_id, record_json FROM editions WHERE edition_id IN "  # noqa: S608
                f"({','.join('?' * len(ids))})",
                ids,
            ).fetchall()
        return {r["edition_id"]: Edition.model_validate_json(r["record_json"]) for r in rows}

    def lookup_isbn13(self, isbn13: str) -> list[str]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT edition_id FROM isbn_index WHERE isbn13 = ? ORDER BY edition_id", (isbn13,)
            ).fetchall()
        return [r["edition_id"] for r in rows]

    def ambiguity_pool(
        self, title: str, work_id: str | None, limit: int = 1000
    ) -> tuple[list[str], bool]:
        """Deterministic, catalog-wide pool for uniqueness checks: every edition whose indexed
        title contains `title` as a phrase, plus every edition of `work_id`. Returns
        (edition ids, complete); complete is False if either part hit `limit`."""
        tokens = [t for t in norm_text(title).split() if t]
        ids: list[str] = []
        complete = True
        with self.connect() as con:
            if tokens:
                phrase = '"' + " ".join(t.replace('"', '""') for t in tokens) + '"'
                rows = con.execute(
                    "SELECT edition_id FROM editions_fts WHERE editions_fts MATCH ? LIMIT ?",
                    (f"title : {phrase}", limit + 1),
                ).fetchall()
                complete &= len(rows) <= limit
                ids += [r[0] for r in rows[:limit]]
            if work_id:
                rows = con.execute(
                    "SELECT edition_id FROM editions WHERE work_id = ? LIMIT ?",
                    (work_id, limit + 1),
                ).fetchall()
                complete &= len(rows) <= limit
                ids += [r[0] for r in rows[:limit]]
        return sorted(set(ids)), complete

    def count(self) -> int:
        with self.connect() as con:
            return int(con.execute("SELECT COUNT(*) FROM editions").fetchone()[0])

    def meta(self) -> dict[str, str]:
        with self.connect() as con:
            try:
                rows = con.execute("SELECT key, value FROM catalog_meta").fetchall()
            except sqlite3.OperationalError:
                return {}
        return {r["key"]: r["value"] for r in rows}


def fts_or_query(text: str) -> str:
    """Build a safe FTS5 query: every token is double-quoted, joined with OR.

    Quoting means user text can never inject FTS5 operators (NEAR, column filters, ^, *).
    """
    tokens = [t for t in norm_text(text).split() if t]
    quoted = ['"' + t.replace('"', '""') + '"' for t in dict.fromkeys(tokens)]
    return " OR ".join(quoted)


def load_jsonl(path: Path) -> list[Edition]:
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(Edition.model_validate(json.loads(line)))
    return out
