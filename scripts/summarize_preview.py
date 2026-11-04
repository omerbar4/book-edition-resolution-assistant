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
    f = a["families"]
    out += [
        "",
        "## Families (split unit)",
        "",
        f"- Independent families: **{f['count']}** (singletons: {f['singleton_families']})",
        f"- Merge edges by rule: {f['edges']}",
        f"- Limitation: {f['limitation']}.",
        "",
        "| largest family | works |",
        "|---|---|",
    ]
    out += [f"| {x['family']} | {x['works']} |" for x in f["largest"]]
    if "author_link_rule" in f:
        out += ["", f"Author-link rule: {f['author_link_rule']}."]
    cross = f.get("cross_seed_families", {})
    out += ["", f"### Families joining several seed titles ({len(cross)})", ""]
    out += [f"- {fam}: {', '.join(gs)}" for fam, gs in cross.items()] or ["- none"]
    for fam, ms in f.get("cross_seed_family_merges", {}).items():
        out += ["", f"Merges inside {fam}:", ""]
        out += [f"- {m['rule']} `{m['value']}`: {m['a']} ↔ {m['b']}" for m in ms[:40]]
    sec = f.get("secondary_credit_keys_not_linking", [])
    if sec:
        out += [
            "",
            "### Most frequent secondary credits (not used for linking)",
            "",
            "| key | name | works credited |",
            "|---|---|---|",
        ]
        out += [f"| {x['key']} | {x['name']} | {x['works']} |" for x in sec[:15]]
    sus = f["suspicious_merges"]
    out += [
        "",
        f"### Possibly unrelated merges ({len(sus)})",
        "",
        "| rule | linking value | work a | work b | reason |",
        "|---|---|---|---|---|",
    ]
    out += [
        f"| {m['rule']} | {m['value']} | {m['a']} | {m['b']} | {m['reason']} |" for m in sus[:80]
    ] or ["| none | | | | |"]
    if len(sus) > 80:
        out.append(f"| … {len(sus) - 80} more in JSON | | | | |")
    b = a["split_balance"]
    out += [
        "",
        "## Proposed dev / held-out balance (by family hash)",
        "",
        f"Split seed {b['split_seed']}, dev fraction {b['dev_fraction']}.",
        "",
        "| split | families | works | editions | works by group | editions by group |",
        "|---|---|---|---|---|---|",
    ]
    for sp in ("dev", "heldout"):
        x = b[sp]
        out.append(
            f"| {sp} | {x['families']} | {x['works']} | {x['editions']} | "
            f"{x['works_by_group']} | {x['editions_by_group']} |"
        )
    out += ["", "| probe | family | split |", "|---|---|---|"]
    out += [f"| {k} | {v['family']} | {v['split']} |" for k, v in b["probes"].items()]
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
    tot = sum(r["editions_sampled"] for r in sel) or 1
    agg = {
        d: round(sum(r["missing_rate_kept"][d] * r["editions_sampled"] for r in sel) / tot, 3)
        for d in ("format", "language", "decade", "publisher", "edition_statement")
    }
    out += ["", f"Missing-metadata rate across all sampled editions: {agg}"]
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
