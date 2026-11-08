"""Generate the 40-case held-out labeling queue (docs/EVALUATION_PLAN.md). FROZEN generator.

    uv run python scripts/make_heldout_queue.py --db var/catalog_v3.sqlite --frozen-tag <tag>

Refuses to run unless HEAD is exactly the freeze tag and the working tree is clean, so the
generation rules are the ones pinned in the freeze manifest. Contents:
- 37 in-corpus queries from 37 distinct held-out families, by predefined stratum quotas
  (identifier 8, missing metadata 7, author variation 7, edition ambiguity 7, format/year
  conflict 8), assigned by maximum bipartite matching in seeded family order (drafter v5;
  label spec v3 proposals);
- the 3 verified-absent held-out probes as out-of-corpus queries (title + author);
- 2 sealed reserves (distinct held-out families), used only to replace a case excluded for
  exposure.
The manifest sets reveal "never". Quotas are never relaxed: an infeasible plan writes
nothing. Prints aggregate checks only; never a template, stratum, proposal or outcome.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
from collections import Counter
from pathlib import Path

from bera.catalog import Catalog
from bera.evalkit.drafts import ALL_TEMPLATES, Draft, Proposed, query_key, template_effective
from bera.evalkit.perturb import judged_fields, label, perturbed_fields
from bera.evalkit.run import repo_relative
from bera.evalkit.splits import family_split
from bera.evalkit.stratified import (
    DRAFTER_V5,
    SPEC_FOR_NEW_DRAFTS,
    STRATA,
    assign,
    candidates,
    to_drafts,
)
from bera.models import Query

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/corpus/v3_proposed"
SPLIT_SEED = 20261103
SEED = 20261110
QUOTAS = {
    "identifier": 8,
    "missing_metadata": 7,
    "author_variation": 7,
    "edition_ambiguity": 7,
    "format_year_conflict": 8,
}
N_RESERVES = 2
N_PROBES = 3
OUT_DIR = ROOT / "data/eval/heldout"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def probe_family(p: dict[str, object]) -> str:
    keys = sorted(p.get("author_keys") or [])  # type: ignore[call-overload]
    return f"probe-author:{keys[0]}" if keys else f"probe:{p['title']}"


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--db", type=Path, required=True)
    a.add_argument("--frozen-tag", required=True)
    args = a.parse_args()
    if git("status", "--porcelain"):
        raise SystemExit("refusing: working tree is not clean")
    if git("rev-parse", f"{args.frozen_tag}^{{commit}}") != git("rev-parse", "HEAD"):
        raise SystemExit(f"refusing: HEAD is not the freeze tag {args.frozen_tag}")
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(
            f"refusing: {OUT_DIR} already has files; the held-out queue is generated once"
        )

    corpus_sha = sha256(CORPUS / "corpus.jsonl")
    family_of: dict[str, str] = json.loads((CORPUS / "families.json").read_text())
    cat = Catalog(args.db)
    with cat.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    catalog = list(cat.get(ids).values())
    by_id = {e.edition_id: e for e in catalog}

    def fam(e: object) -> str:
        w = e.work_id or e.edition_id  # type: ignore[attr-defined]
        return family_of.get(w, w)

    by_family: dict[str, list] = {}
    for e in catalog:
        f = fam(e)
        if e.work_id and family_split(f, SPLIT_SEED) == "heldout":
            by_family.setdefault(f, []).append(e)
    rng = random.Random(SEED)
    families = sorted(by_family)
    rng.shuffle(families)
    syn = [
        json.loads(x)
        for x in (ROOT / "data/eval/dev_check_v3_synthetic.jsonl").read_text().splitlines()
        if x.strip()
    ]
    seen = {query_key(Query.model_validate(c["query"])) for c in syn}
    for q in sorted((ROOT / "data/eval/drafts").glob("*.jsonl")):
        for x in q.read_text().splitlines():
            if x.strip():
                seen.add(query_key(Query.model_validate(json.loads(x)["query"])))
    cands = candidates(by_family, families, seen, catalog, SEED)
    plan = assign(cands, [], families, QUOTAS, N_RESERVES)
    print(f"feasible: {plan.feasible}; shortfall {plan.shortfall}")
    if not plan.feasible:
        raise SystemExit(
            "stratum quotas infeasible on held-out families; nothing written (not relaxed)"
        )

    taken: set[str] = set()
    in_corpus = to_drafts(plan.assigned, catalog, "h01", rng, taken, split="heldout")
    reserves = to_drafts(plan.reserves, catalog, "h01", rng, taken, split="heldout")

    probes = [
        json.loads(x)
        for x in (ROOT / "data/selection/exclusions_v3_proposed.jsonl").read_text().splitlines()
        if x.strip()
    ]
    status = json.loads((CORPUS / "probe_status_for_labeling.json").read_text())
    held_probes = sorted(
        (
            p
            for p in probes
            if status.get(p["title"], {}).get("status") == "verified_absent"
            and family_split(probe_family(p), SPLIT_SEED) == "heldout"
        ),
        key=lambda p: p["title"],
    )
    probe_drafts = []
    for p in held_probes[:N_PROBES]:
        token = f"{rng.getrandbits(40):010x}"
        while f"h01-{token}" in taken:
            token = f"{rng.getrandbits(40):010x}"
        taken.add(f"h01-{token}")
        probe_drafts.append(
            Draft(
                draft_id=f"h01-{token}",
                split="heldout",
                family=probe_family(p),
                query=Query(title=p["title"], author=p.get("author")),
                template="out_of_corpus_probe",
                drafted_by=DRAFTER_V5,
                stratum="out_of_corpus_probe",
                proposal_label_spec=SPEC_FOR_NEW_DRAFTS,
                proposed=Proposed(
                    expected="abstain", gold_edition_ids=[], ambiguity_reason="out_of_corpus"
                ),
            )
        )
    queue = sorted(in_corpus + probe_drafts, key=lambda d: d.draft_id)

    def reproduces(d: Draft) -> bool:
        e = by_id[d.source_edition_id or ""]
        f = perturbed_fields(e, ALL_TEMPLATES[d.template], d.op_seed or 0)
        exp, gold, reason, _ = label(judged_fields(f, e), e, catalog, SPEC_FOR_NEW_DRAFTS)
        return f == d.query.model_dump(exclude_none=True) and (exp, gold, reason) == (
            d.proposed.expected,
            d.proposed.gold_edition_ids,
            d.proposed.ambiguity_reason,
        )

    fams = Counter(d.family for d in queue + reserves)
    checks = {
        "queue size 40": len(queue) == 40,
        "37 in-corpus + 3 probes": len(in_corpus) == 37 and len(probe_drafts) == N_PROBES,
        "all held-out split by family": all(
            family_split(d.family, SPLIT_SEED) == "heldout" for d in queue + reserves
        ),
        "one query per family (incl. reserves)": all(n == 1 for n in fams.values()),
        "stratum quotas met exactly": Counter(d.stratum for d in in_corpus) == Counter(QUOTAS),
        "template belongs to its stratum": all(
            d.template in STRATA[d.stratum or ""] for d in in_corpus
        ),
        "every template effective": all(
            template_effective(d.template, by_id[d.source_edition_id or ""], d.op_seed or 0)
            for d in in_corpus + reserves
        ),
        "queries and proposals reproduce (spec v3)": all(map(reproduces, in_corpus + reserves)),
        "no previously seen query": not {query_key(d.query) for d in queue + reserves} & seen,
        "queries distinct": len({query_key(d.query) for d in queue + reserves})
        == len(queue) + len(reserves),
        "opaque unique ids": all(
            re.fullmatch(r"h01-[0-9a-f]{10}", d.draft_id) for d in queue + reserves
        )
        and len(taken) == len(queue) + len(reserves),
        "corpus sha256 unchanged": sha256(CORPUS / "corpus.jsonl") == corpus_sha,
    }
    for k, v in checks.items():
        print(("PASS " if v else "FAIL ") + k)
    if not all(checks.values()):
        raise SystemExit("validation failed; nothing written")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    qpath = OUT_DIR / "heldout_queue.jsonl"
    qpath.write_text("".join(d.model_dump_json(exclude_none=True) + "\n" for d in queue))
    rpath = OUT_DIR / "heldout_queue.reserves.jsonl"
    rpath.write_text("".join(d.model_dump_json(exclude_none=True) + "\n" for d in reserves))
    manifest = {
        "queue": repo_relative(qpath),
        "queue_sha256": sha256(qpath),
        "split": "heldout",
        "drafts": len(queue),
        "families": len({d.family for d in queue}),
        "reveal": "never",
        "labels_file": "data/eval/heldout/heldout_labels.jsonl",
        "proposal_label_spec": SPEC_FOR_NEW_DRAFTS,
        "frozen_tag": args.frozen_tag,
        "frozen_commit": git("rev-parse", "HEAD"),
        "generator": "scripts/make_heldout_queue.py",
        "seed": SEED,
        "split_seed": SPLIT_SEED,
        "quotas": QUOTAS,
        "probes": N_PROBES,
        "reserves": {
            "file": repo_relative(rpath),
            "sha256": sha256(rpath),
            "count": len(reserves),
            "use": "only to replace a case excluded for exposure, in file order",
        },
        "corpus_sha256": corpus_sha,
        "validation": checks,
        "note": "Held-out: proposals are never revealed; labels and results are never used for "
        "tuning; evaluated once with the frozen system.",
    }
    qpath.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(
        f"wrote {len(queue)} held-out drafts ({manifest['families']} families) "
        f"+ {len(reserves)} sealed reserves"
    )


if __name__ == "__main__":
    main()
