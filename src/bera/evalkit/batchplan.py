"""Shared, recorded selection rules for development labeling batches.

Everything here is decided from the frozen corpus, prior queues and documents, never from
system results or drafted proposals:

- used families: every family with a draft in any prior queue, plus every family of an
  edition referenced by a discussed development case (cases named in docs/, label-change
  records and the unsupported-suggestion analysis, and any edition id those mention);
- seen queries: every prior draft query and every dev-check synthetic query;
- pool A: unused development families never used in the 300-case synthetic
  policy-development check; pool B: unused families that were (reported separately);
- capacity: how many distinct effective templates a family supports (capped at 3).
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from bera.evalkit.drafts import (
    MAX_QUERIES_PER_FAMILY,
    TEMPLATES,
    Draft,
    load_drafts,
    query_key,
    template_effective,
)
from bera.evalkit.splits import family_split
from bera.models import Edition, Query

SYN = re.compile(r"syn-(OL\d+M)-\d+")
SYN_ID = re.compile(r"syn-OL\d+M-\d+")
EDITION = re.compile(r"\bOL\d+M\b")


@dataclass
class Selection:
    used_families: set[str]
    discussed_families: set[str]
    exclude_editions: set[str]
    seen_queries: set[str]
    existing_per_family: Counter[str]
    dev_families: set[str]
    policy_dev_families: set[str]
    capacity: dict[str, int] = field(default_factory=dict)

    @property
    def unused(self) -> set[str]:
        return self.dev_families - self.used_families

    @property
    def pool_a(self) -> set[str]:
        return {f for f in self.unused - self.policy_dev_families if self.capacity.get(f, 0)}

    @property
    def pool_b(self) -> set[str]:
        return {f for f in self.unused & self.policy_dev_families if self.capacity.get(f, 0)}


def build_selection(
    root: Path,
    catalog: Sequence[Edition],
    family_of: Mapping[str, str],
    split_seed: int,
    prior_queues: Sequence[Path],
) -> Selection:
    by_id = {e.edition_id: e for e in catalog}

    def fam(e: Edition) -> str:
        w = e.work_id or e.edition_id
        return family_of.get(w, w)

    prior: list[Draft] = [d for q in prior_queues for d in load_drafts(q)]
    sources = [
        *(root / "docs").glob("*.md"),
        root / "README.md",
        *(root / "data/eval/label_changes").glob("*"),
        root / "data/eval/results/dev_check_v3/unsupported_suggestions.json",
    ]
    text = "\n".join(f.read_text(encoding="utf-8") for f in sources if f.exists())
    named = set(SYN_ID.findall(text))
    discussed = set(EDITION.findall(text)) | set(SYN.findall(text))
    syn = [
        json.loads(x)
        for x in (root / "data/eval/dev_check_v3_synthetic.jsonl").read_text().splitlines()
        if x.strip()
    ]
    for c in syn:
        if c["case_id"] in named:
            discussed |= set(c["gold_edition_ids"])
    discussed_families = {fam(by_id[e]) for e in discussed if e in by_id}
    exclude_editions = set(discussed)
    for d in prior:
        if d.source_edition_id:
            exclude_editions.add(d.source_edition_id)
        exclude_editions |= set(d.proposed.gold_edition_ids)
    seen = {query_key(d.query) for d in prior} | {
        query_key(Query.model_validate(c["query"])) for c in syn
    }
    dev = {fam(e) for e in catalog if e.work_id and family_split(fam(e), split_seed) == "dev"}
    sel = Selection(
        used_families={d.family for d in prior} | discussed_families,
        discussed_families=discussed_families,
        exclude_editions=exclude_editions,
        seen_queries=seen,
        existing_per_family=Counter(d.family for d in prior),
        dev_families=dev,
        policy_dev_families={c["family"] for c in syn},
    )
    eds: dict[str, list[Edition]] = {}
    for e in catalog:
        f = fam(e)
        if f in sel.unused and e.work_id and e.edition_id not in exclude_editions:
            eds.setdefault(f, []).append(e)
    for f, items in eds.items():
        ok = {
            name
            for name, _ in TEMPLATES
            if any(template_effective(name, e, s) for e in items for s in range(5))
        }
        sel.capacity[f] = min(len(ok), MAX_QUERIES_PER_FAMILY)
    return sel
