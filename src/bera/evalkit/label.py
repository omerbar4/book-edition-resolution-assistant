"""Human-labeling helpers (see docs/LABELING_GUIDE.md).

    uv run python -m bera.evalkit.label search --title "lantern"      # alphabetical, unranked
    uv run python -m bera.evalkit.label validate data/eval/human_cases.jsonl
    uv run python -m bera.evalkit.label template

`search` deliberately shows catalog records alphabetically with no system scores, so the
labeler is not anchored on the system's own ranking.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from bera.catalog import Catalog
from bera.config import Settings
from bera.evalkit.cases import EvalCase, load_cases
from bera.evalkit.splits import leakage
from bera.text import norm_text, strip_accents

TEMPLATE = {
    "case_id": "h-0001",
    "query": {
        "title": "words exactly as you would type them",
        "author": "…",
        "physical_format": "paperback",
    },
    "expected": "suggest",
    "gold_edition_ids": ["OL123M"],
    "family": "OL45W",
    "origin": "human",
    "labeler": "your-initials",
    "labeled_at": "2026-11-10",
    "notes": "physical copy on my shelf; barcode scuffed",
}


SEARCH_FIELDS = (
    "edition_id",
    "work_id",
    "title",
    "subtitle",
    "authors",
    "publishers",
    "publish_year",
    "physical_format",
    "edition_name",
    "languages",
    "isbn_13",
    "isbn_10",
)
SEARCH_MATCH_RULE = (
    "every word you type appears in the title, subtitle or original title "
    "(case and accents ignored)"
)
SEARCH_ORDER = "alphabetical by title, then edition id (not ranked by the system)"


def _fold(text: str | None) -> str:
    return strip_accents(norm_text(text or ""))


def search_page(catalog: Catalog, text: str, offset: int = 0, limit: int = 50) -> dict[str, object]:
    """Unranked catalog search for labelers, with an explicit total so nothing is silently
    cut off. Deterministic full scan (fine for a catalog of this size)."""
    words = [w for w in _fold(text).split() if w]
    with catalog.connect() as con:
        rows = con.execute("SELECT edition_id, record_json FROM editions").fetchall()
    hits = []
    for r in rows:
        d = json.loads(r["record_json"])
        hay = " ".join(_fold(d.get(k)) for k in ("title", "subtitle", "translation_of"))
        if words and all(w in hay for w in words):
            hits.append(d)
    hits.sort(key=lambda d: (_fold(d.get("title")), d["edition_id"]))
    total = len(hits)
    offset = max(0, min(offset, total))
    page = hits[offset : offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "returned": len(page),
        "truncated": offset + len(page) < total,
        "match_rule": SEARCH_MATCH_RULE,
        "order": SEARCH_ORDER,
        "items": [{k: d.get(k) for k in SEARCH_FIELDS} for d in page],
    }


def search(catalog: Catalog, title: str, limit: int = 50) -> list[dict[str, object]]:
    """First page only; prefer `search_page`, which reports the total."""
    items = search_page(catalog, title, 0, limit)["items"]
    assert isinstance(items, list)
    return items


def validate(cases: Sequence[EvalCase], catalog: Catalog) -> dict[str, object]:
    ids = Counter(c.case_id for c in cases)
    dupes = sorted(k for k, n in ids.items() if n > 1)
    referenced = {g for c in cases for g in c.gold_edition_ids}
    present = set(catalog.get(referenced))
    missing = sorted(referenced - present)
    return {
        "cases": len(cases),
        "human_labeled": sum(c.human_labeled for c in cases),
        "by_origin": dict(Counter(c.origin for c in cases)),
        "by_expected": dict(Counter(c.expected for c in cases)),
        "duplicate_case_ids": dupes,
        "gold_ids_missing_from_catalog": missing,
        "families_in_both_splits": leakage(cases),
        "ok": not dupes and not missing and not leakage(cases),
    }


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="bera-label")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("--title", required=True)
    s.add_argument("--db", type=Path)
    v = sub.add_parser("validate")
    v.add_argument("cases", type=Path)
    v.add_argument("--db", type=Path)
    sub.add_parser("template")
    a = p.parse_args(argv)
    if a.cmd == "template":
        print(json.dumps(TEMPLATE, ensure_ascii=False))
        return
    catalog = Catalog(a.db or Settings.from_env().catalog_db)
    if a.cmd == "search":
        for row in search(catalog, a.title):
            print(json.dumps(row, ensure_ascii=False))
    else:
        report = validate(load_cases(a.cases), catalog)
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
