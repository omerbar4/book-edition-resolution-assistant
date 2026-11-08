"""Scripted demo against a running local BERA server. SYNTHETIC catalog cases only.

    uv run python -m bera.cli build-catalog          # synthetic fixtures (30 editions)
    uv run python -m bera.cli serve --port 8000      # in another terminal
    uv run python demo/run_demo.py [--base http://127.0.0.1:8000]

Every query here targets data/fixtures/synthetic_editions.jsonl. None is a dev or held-out
evaluation case, and the expected outcomes are what the synthetic catalog is built to show,
not evaluation results. Standard library only; it talks only to the given local server.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from typing import Any

SCENARIOS: list[tuple[str, dict[str, Any], str, str]] = [
    (
        "ISBN with hyphens, unique mapping",
        {"isbn": "978-0-00-001002-5"},
        "suggest",
        "a checksum-valid ISBN that maps to exactly one edition, with no conflicting field",
    ),
    (
        "Title typo + author + format, no ISBN",
        {
            "title": "Practical Data Structurs",
            "author": "Priya Natarajan",
            "physical_format": "paperback",
        },
        "suggest",
        "trigram retrieval tolerates the typo; exactly one edition fits every supplied field",
    ),
    (
        "Title + author only",
        {"title": "The Lantern Keepers Daughter", "author": "Mara Ellison"},
        "review",
        "several editions fit everything supplied; unknown fields never break a tie",
    ),
    (
        "ISBN shared by different books",
        {"isbn": "9780000010124"},
        "review",
        "a duplicate ISBN mapping is never auto-resolved",
    ),
    (
        "ISBN with a bad checksum",
        {"isbn": "9780000010019"},
        "review",
        "a repaired ISBN is only a hypothesis; it goes to review",
    ),
    (
        "Book not in the catalog",
        {"title": "A Book That Is Not In The Catalog", "author": "Nobody Known"},
        "review",
        "no candidate fits; the case is flagged as likely out of corpus",
    ),
]


def post(base: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(  # noqa: S310 - local server URL given by the operator
        base + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        return json.loads(r.read())  # type: ignore[no-any-return]


def main() -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--base", default="http://127.0.0.1:8000")
    args = a.parse_args()
    if not args.base.startswith(("http://127.0.0.1", "http://localhost")):
        raise SystemExit("demo talks to a local server only")
    with urllib.request.urlopen(args.base + "/api/health", timeout=10) as r:  # noqa: S310
        health = json.loads(r.read())
    if health.get("catalog_meta", {}).get("all_synthetic") != "True":
        raise SystemExit("refusing: the demo expects the synthetic fixture catalog")
    n = health["catalog_editions"]
    print(f"policy {health['policy_version']}; catalog {n} synthetic editions")
    print(f"llm: {health['capabilities']['llm']}\n")
    mismatches = 0
    for name, query, expected, why in SCENARIOS:
        r = post(args.base, "/api/resolve", query)
        ok = r["outcome"] == expected
        mismatches += not ok
        top = [c["edition"]["edition_id"] for c in r["candidates"][:3]]
        print(f"{'OK ' if ok else 'DIFF'} {name}")
        print(f"     query    {json.dumps(query)}")
        print(f"     outcome  {r['outcome']}  suggested {r['suggested_edition_id']}  top {top}")
        print(f"     reasons  {', '.join(r['reasons'])}")
        print(f"     why      {why}\n")
    print(
        "Decision support only: a suggestion is not a confirmed match; confidence is uncalibrated."
    )
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
