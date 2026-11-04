"""Render a selection_preview.json as a Markdown review document.

    uv run python scripts/summarize_preview.py \
        var/selection_preview/v3_proposed/selection_preview.json \
        --out docs/review/selection_preview_v3.md
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _dims(d: dict[str, int]) -> str:
    return " ".join(f"{k[:4]}={v}" for k, v in d.items())


def render(p: dict[str, Any]) -> str:
    a = p["analysis"]
    sel = p["selected"]
    out = [
        "# Selection preview (PROVISIONAL: not a corpus, not approved)",
        "",
        f"- Selected works: **{p['selected_works']}**",
        f"- Editions after diversity sampling: **{p['expected_editions']}**",
        f"- Excluded works: **{len(p['excluded_works'])}**",
        f"- Families: **{a['families']['count']}** (edges by rule: {a['families']['edges']})",
        "",
        "## Counts by sampling group",
        "",
        "| group | works | editions sampled |",
        "|---|---|---|",
    ]
    by = Counter(r["stratum"] for r in sel)
    eds = Counter()
    for r in sel:
        eds[r["stratum"]] += r["editions_sampled"]
    for s in sorted(by):
        out.append(f"| {s} | {by[s]} | {eds[s]} |")
    out += ["", "## Warnings", ""]
    out += [f"- {w}" for w in a["warnings"]] or ["- none"]
    out += ["", "## Largest families", "", "| family | works |", "|---|---|"]
    out += [f"| {f['family']} | {f['works']} |" for f in a["families"]["largest"]]
    s = a["edition_sampling"]
    out += [
        "",
        "## Edition sampling",
        "",
        f"Method: {s['method']} (cap {s['cap']}).",
        "",
        f"Works whose kept sample could not cover every distinct value, by dimension: "
        f"{s['works_with_unmet_diversity_by_dimension'] or 'none'}",
    ]
    out += [
        "",
        "## Seed author identity (provisional candidates)",
        "",
        "| seed | flags | candidates (key: editions credited in matched works) |",
        "|---|---|---|",
    ]
    for title, amb in a["author_identity"]["seeds"].items():
        cands = ", ".join(
            f"{c['key']}: {c['editions_credited_in_scope']}"
            for c in amb["candidates"]
            if c["editions_credited_in_scope"]
        )
        out.append(f"| {title} | {', '.join(amb['flags']) or '—'} | {cands or 'none credited'} |")
    out += [
        "",
        "## Probe author identity and pre-audit",
        "",
        "| probe | identity flags | provisional pre-audit | reasons |",
        "|---|---|---|---|",
    ]
    for title, amb in a["author_identity"]["probes"].items():
        pa = a["probe_preaudit_provisional"][title]
        out.append(
            f"| {title} | {', '.join(amb['flags']) or '—'} | {pa['status']} | "
            f"{'; '.join(pa['reasons']) or '—'} |"
        )
    out += [
        "",
        "## Selected works",
        "",
        "| group | work | family | title | editions avail→sampled | distinct kept "
        "(fmt lang deca publ edit) | missing rate kept |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sel:
        miss = " ".join(f"{k[:4]}={v}" for k, v in r["missing_rate_kept"].items())
        out.append(
            f"| {r['stratum']} | {r['work']} | {r['family']} | {r['title']} | "
            f"{r['editions_available']}→{r['editions_sampled']} | "
            f"{_dims(r['distinct_kept'])} | {miss} |"
        )
    rules = Counter(x["rule"] for x in p["excluded_works"])
    out += [
        "",
        "## Exclusions",
        "",
        f"By rule: {dict(rules)}",
        "",
        "| work | rule | title | editions |",
        "|---|---|---|---|",
    ]
    for x in p["excluded_works"][:300]:
        out.append(f"| {x['work']} | {x['rule']} | {x['title']} | {x['editions']} |")
    if len(p["excluded_works"]) > 300:
        out.append(f"| … | | {len(p['excluded_works']) - 300} more in the JSON | |")
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("preview", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(render(json.loads(a.preview.read_text())))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
