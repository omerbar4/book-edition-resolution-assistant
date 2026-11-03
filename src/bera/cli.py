"""Command line: build the local catalog and run the API.

uv run python -m bera.cli build-catalog [--fixtures PATH] [--db PATH]
uv run python -m bera.cli serve [--host 127.0.0.1] [--port 8000]
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from bera.catalog import Catalog, load_jsonl
from bera.config import REPO_ROOT, Settings

DEFAULT_FIXTURES = REPO_ROOT / "data" / "fixtures" / "synthetic_editions.jsonl"


def build_catalog(fixtures: Path, db: Path) -> int:
    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()
    editions = load_jsonl(fixtures)
    sha = hashlib.sha256(fixtures.read_bytes()).hexdigest()
    sources = sorted({e.source for e in editions})
    return Catalog(db).build(
        editions,
        {
            "fixtures_sha256": sha,
            "sources": ",".join(sources),
            "all_synthetic": str(all(e.synthetic for e in editions)),
        },
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="bera")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-catalog")
    b.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    b.add_argument("--db", type=Path, default=None)
    s = sub.add_parser("serve")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.cmd == "build-catalog":
        db = args.db or Settings.from_env().catalog_db
        n = build_catalog(args.fixtures, db)
        print(f"built {db} with {n} editions from {args.fixtures}")
    elif args.cmd == "serve":
        import uvicorn

        from bera.api import create_app

        uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
