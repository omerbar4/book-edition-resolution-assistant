"""Candidate retrieval behind a small Protocol so stages can be swapped for ablations.

Implemented now:
- FtsBm25Retriever     SQLite FTS5 BM25 over title/authors/publishers/extra (lexical).
- TrigramRetriever     FTS5 trigram index queried with the query's character trigrams,
                       ranked by BM25 over trigrams -> tolerant to typos.
- rrf_fuse             Reciprocal Rank Fusion (Cormack, Clarke & Buettcher, SIGIR 2009).

PENDING (requires approved model download; NOT simulated):
- Embedding retrieval  -> see EmbeddingRetrieverPending
- Cross-encoder rerank -> see bera.rerank
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from rapidfuzz import fuzz

from bera.catalog import Catalog, fts_or_query
from bera.models import Edition, Query
from bera.text import norm_person, norm_text

RRF_K = 60
MAX_TRIGRAMS = 64


@dataclass(frozen=True)
class Hit:
    edition_id: str
    source: str
    rank: int  # 1-based within its source
    raw_score: float  # source-native score (BM25 is lower-is-better in SQLite; stored as-is)


class Reranker(Protocol):
    max_candidates: int

    @property
    def label(self) -> str: ...

    def score(self, query: Query, editions: list[Edition]) -> list[float]: ...


class Retriever(Protocol):
    name: str

    def retrieve(self, query: Query, k: int) -> list[Hit]: ...


def query_search_text(query: Query) -> str:
    parts = [
        query.title,
        query.author and norm_person(query.author),
        query.publisher,
        query.edition,
        query.free_text,
    ]
    return " ".join(p for p in parts if p)


class FtsBm25Retriever:
    name = "fts_bm25"

    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog

    def retrieve(self, query: Query, k: int) -> list[Hit]:
        match = fts_or_query(query_search_text(query))
        if not match:
            return []
        with self.catalog.connect() as con:
            try:
                rows = con.execute(
                    "SELECT edition_id, bm25(editions_fts, 0.0, 10.0, 5.0, 1.0, 2.0) AS s "
                    "FROM editions_fts WHERE editions_fts MATCH ? ORDER BY s LIMIT ?",
                    (match, k),
                ).fetchall()
            except sqlite3.OperationalError:
                return []
        return [Hit(r["edition_id"], self.name, i + 1, float(r["s"])) for i, r in enumerate(rows)]


def char_trigrams(text: str) -> list[str]:
    grams: list[str] = []
    for token in norm_text(text).split():
        if len(token) < 3:
            continue
        grams.extend(token[i : i + 3] for i in range(len(token) - 2))
    return list(dict.fromkeys(grams))[:MAX_TRIGRAMS]


class TrigramRetriever:
    name = "trigram"

    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog

    def retrieve(self, query: Query, k: int) -> list[Hit]:
        grams = char_trigrams(
            " ".join(p for p in [query.title, query.author, query.free_text] if p)
        )
        if not grams:
            return []
        match = " OR ".join('"' + g.replace('"', '""') + '"' for g in grams)
        with self.catalog.connect() as con:
            try:
                rows = con.execute(
                    "SELECT edition_id, bm25(editions_tri) AS s FROM editions_tri "
                    "WHERE editions_tri MATCH ? ORDER BY s LIMIT ?",
                    (match, k),
                ).fetchall()
            except sqlite3.OperationalError:
                return []
        return [Hit(r["edition_id"], self.name, i + 1, float(r["s"])) for i, r in enumerate(rows)]


def rrf_fuse(
    rankings: Sequence[Sequence[Hit]], k: int = RRF_K
) -> list[tuple[str, float, list[str]]]:
    """Fuse ranked lists. Returns (edition_id, rrf_score, sources) sorted by score desc, id asc."""
    scores: dict[str, float] = {}
    sources: dict[str, list[str]] = {}
    for hits in rankings:
        for h in hits:
            scores[h.edition_id] = scores.get(h.edition_id, 0.0) + 1.0 / (k + h.rank)
            sources.setdefault(h.edition_id, []).append(h.source)
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [(eid, s, sources[eid]) for eid, s in ordered]


class EmbeddingRetrieverPending:
    """Placeholder that refuses to run. Embedding retrieval needs an approved model download.

    It exists so the pipeline and /api/health can report the capability as pending instead of
    silently pretending to have it.
    """

    name = "embedding"
    status = "pending: model download not yet approved (planned: BAAI/bge-small-en-v1.5)"

    def retrieve(self, query: Query, k: int) -> list[Hit]:
        raise NotImplementedError(self.status)


class FuzzyScanRetriever:
    """Baseline 1 retriever: brute-force rapidfuzz over every edition's title and authors.

    No index, no BM25. Suitable for small corpora (it scans everything per query).
    """

    name = "fuzzy_scan"

    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self._rows: list[tuple[str, str, str]] | None = None

    def _load(self) -> list[tuple[str, str, str]]:
        if self._rows is None:
            with self.catalog.connect() as con:
                rows = con.execute("SELECT edition_id, record_json FROM editions").fetchall()
            out = []
            for r in rows:
                d = json.loads(r["record_json"])
                out.append(
                    (
                        r["edition_id"],
                        norm_text(d.get("title")),
                        " ".join(norm_person(a) for a in d.get("authors", [])),
                    )
                )
            self._rows = sorted(out)
        return self._rows

    def retrieve(self, query: Query, k: int) -> list[Hit]:
        title = norm_text(query.title or query.free_text)
        author = norm_person(query.author)
        if not title and not author:
            return []
        scored = []
        for eid, t, a in self._load():
            s = (fuzz.WRatio(title, t) if title else 0.0) + (
                0.5 * fuzz.token_sort_ratio(author, a) if author and a else 0.0
            )
            scored.append((s, eid))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [Hit(eid, self.name, i + 1, s) for i, (s, eid) in enumerate(scored[:k])]
