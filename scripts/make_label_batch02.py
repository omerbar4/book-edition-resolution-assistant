"""Draft development batch 02 for INDEPENDENT human labeling (drafter v3).

    uv run python scripts/make_label_batch02.py --db var/catalog_v3.sqlite

Exclusions (decided before generation, never from model results):
- every family of a batch 01 draft (so no batch 01 source edition, twin or translation);
- every family of an edition referenced by a development case already discussed: the
  synthetic cases named in docs/, data/eval/label_changes/ and the unsupported-suggestion
  analysis, and any edition id those records or docs mention;
- every query already seen (batch 01 and the 300 dev-check synthetic queries).

Only development families (families.json + split seed 20261103) are used; the corpus and
split are read, never written. No probes: all verified-absent development probes were
used in batch 01. Prints aggregate checks only, never a per-case template or proposal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from bera.catalog import Catalog
from bera.evalkit.drafts import (
    DRAFTER_V3,
    TEMPLATES,
    draft_batch_v3,
    load_drafts,
    query_key,
    save_drafts,
    template_effective,
)
from bera.evalkit.perturb import DEFAULT_LABEL_SPEC, perturbed_fields
from bera.evalkit.splits import family_split
from bera.models import Query

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/corpus/v3_proposed"
SPLIT_SEED = 20261103
SYN = re.compile(r"syn-(OL\d+M)-\d+")
EDITION = re.compile(r"\bOL\d+M\b")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20261107)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--out", type=Path, default=ROOT / "data/eval/drafts/dev_batch02.jsonl")
    a = p.parse_args()

    corpus_sha = sha256(CORPUS / "corpus.jsonl")
    family_of: dict[str, str] = json.loads((CORPUS / "families.json").read_text())
    cat = Catalog(a.db)
    with cat.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    catalog = list(cat.get(ids).values())
    by_id = {e.edition_id: e for e in catalog}

    def fam(eid: str) -> str | None:
        e = by_id.get(eid)
        if e is None:
            return None
        w = e.work_id or e.edition_id
        return family_of.get(w, w)

    b01 = load_drafts(ROOT / "data/eval/drafts/dev_batch01.jsonl")
    b01_families = {d.family for d in b01}
    b01_editions = {d.source_edition_id for d in b01 if d.source_edition_id}
    for d in b01:
        b01_editions |= set(d.proposed.gold_edition_ids)

    discussed_sources = [
        *(ROOT / "docs").glob("*.md"),
        ROOT / "README.md",
        *(ROOT / "data/eval/label_changes").glob("*"),
        ROOT / "data/eval/results/dev_check_v3/unsupported_suggestions.json",
    ]
    discussed_text = "\n".join(f.read_text(encoding="utf-8") for f in discussed_sources)
    discussed_cases = set(SYN.findall(discussed_text))
    discussed_editions = set(EDITION.findall(discussed_text)) | discussed_cases
    syn_cases = [
        json.loads(x)
        for x in (ROOT / "data/eval/dev_check_v3_synthetic.jsonl").read_text().splitlines()
        if x.strip()
    ]
    named = {m.group(0) for m in re.finditer(r"syn-OL\d+M-\d+", discussed_text)}
    for c in syn_cases:
        if c["case_id"] in named:
            discussed_editions |= set(c["gold_edition_ids"])
    discussed_families = {f for f in map(fam, discussed_editions) if f}

    seen_queries = {query_key(d.query) for d in b01} | {
        query_key(Query.model_validate(c["query"])) for c in syn_cases
    }
    exclude_families = b01_families | discussed_families
    exclude_editions = b01_editions | discussed_editions

    drafts = draft_batch_v3(
        catalog,
        split="dev",
        split_seed=SPLIT_SEED,
        seed=a.seed,
        n=a.n,
        prefix="d02",
        family_of=family_of,
        exclude_families=exclude_families,
        exclude_editions=exclude_editions,
        exclude_queries=seen_queries,
    )

    # ---- validation (aggregate output only) ----
    tmpl = dict(TEMPLATES)
    checks: dict[str, bool] = {
        "count == n": len(drafts) == a.n,
        "all dev split by family": all(
            d.split == "dev" and family_split(d.family, SPLIT_SEED) == "dev" for d in drafts
        ),
        "one case per family": len({d.family for d in drafts}) == len(drafts),
        "no batch 01 family": not {d.family for d in drafts} & b01_families,
        "no discussed family": not {d.family for d in drafts} & discussed_families,
        "no excluded source edition": not {d.source_edition_id for d in drafts} & exclude_editions,
        "no previously seen query": not {query_key(d.query) for d in drafts} & seen_queries,
        "queries distinct": len({query_key(d.query) for d in drafts}) == len(drafts),
        "every template effective (each op changes the query; promised fields kept)": True,
        "query reproduces from source+ops": True,
        "opaque ids (d02- + 10 hex, unique)": all(
            re.fullmatch(r"d02-[0-9a-f]{10}", d.draft_id) for d in drafts
        )
        and len({d.draft_id for d in drafts}) == len(drafts),
        "no probe drafts": all(d.template != "out_of_corpus_probe" for d in drafts),
    }
    for d in drafts:
        e = by_id[d.source_edition_id or ""]
        q = d.query.model_dump(exclude_none=True)
        if d.op_seed is None or not template_effective(d.template, e, d.op_seed):
            checks["every template effective (each op changes the query; promised fields kept)"] = (
                False
            )
        if d.op_seed is None or perturbed_fields(e, tmpl[d.template], d.op_seed) != q:
            checks["query reproduces from source+ops"] = False
    probes = [
        json.loads(x)
        for x in (ROOT / "data/selection/exclusions_v3_proposed.jsonl").read_text().splitlines()
        if x.strip()
    ]
    status = json.loads((CORPUS / "probe_status_for_labeling.json").read_text())

    def probe_family(pr: dict[str, object]) -> str:
        keys = sorted(pr.get("author_keys") or [])  # type: ignore[call-overload]
        return f"probe-author:{keys[0]}" if keys else f"probe:{pr['title']}"

    b01_probe_titles = {d.query.title for d in b01 if d.template == "out_of_corpus_probe"}
    unused_dev_probes = [
        pr["title"]
        for pr in probes
        if status.get(pr["title"], {}).get("status") == "verified_absent"
        and family_split(probe_family(pr), SPLIT_SEED) == "dev"
        and pr["title"] not in b01_probe_titles
    ]
    checks["corpus sha256 unchanged"] = sha256(CORPUS / "corpus.jsonl") == corpus_sha
    for k, v in checks.items():
        print(("PASS " if v else "FAIL ") + k)
    print(f"unused verified-absent dev probes: {len(unused_dev_probes)}")
    if not all(checks.values()):
        raise SystemExit("validation failed; nothing written")

    save_drafts(a.out, drafts)
    manifest = {
        "queue": str(a.out.relative_to(ROOT)),
        "queue_sha256": sha256(a.out),
        "split": "dev",
        "drafts": len(drafts),
        "drafted_by": DRAFTER_V3,
        "generator": "scripts/make_label_batch02.py",
        "seed": a.seed,
        "split_seed": SPLIT_SEED,
        "corpus_sha256": corpus_sha,
        "proposal_label_spec": DEFAULT_LABEL_SPEC,
        "purpose": "independent human labeling (batch 01 is practice/exposed and kept separately)",
        "labels_file": "data/eval/labels/dev_batch02_labels.jsonl",
        "exclusions": {
            "batch01_families": len(b01_families),
            "discussed_cases": len(discussed_cases),
            "discussed_families": len(discussed_families),
            "excluded_families_total": len(exclude_families),
            "seen_queries": len(seen_queries),
        },
        "probes": (
            f"none: {len(unused_dev_probes)} unused verified-absent development probes "
            "(all were used in batch 01)"
        ),
        "validation": checks,
        "note": (
            "Ids are opaque and the order is random. Templates, template notes, proposals and "
            "system scores are never sent before a label is saved. The proposal is a "
            "program draft, not ground truth. Composition by template or proposed outcome is "
            "deliberately not summarized here."
        ),
    }
    a.out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"wrote {len(drafts)} drafts; queue sha256 {manifest['queue_sha256']}")


if __name__ == "__main__":
    main()
