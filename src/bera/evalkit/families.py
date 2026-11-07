"""Load-time family resolution for human-labeled cases.

The labeling UI stored `family` as the chosen edition's work id (or the draft family for
abstentions), which is not the corpus family. Grouped statistics (family bootstrap, grouped
cross-validation, leakage checks) need the corpus family, so it is resolved at load time from
the frozen queue (each draft's family) and cross-checked against the frozen corpus mapping
(families.json). Label files are never rewritten.

Strict: a missing draft, an unknown family, or a chosen edition whose corpus family differs
from the draft's family raises FamilyMappingError. There is no fallback to work ids.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from bera.catalog import Catalog
from bera.evalkit.cases import EvalCase
from bera.evalkit.drafts import Draft, load_drafts


class FamilyMappingError(ValueError):
    pass


def resolve_families(
    cases: Sequence[EvalCase],
    drafts: Sequence[Draft],
    family_of: Mapping[str, str],
    catalog: Catalog,
) -> list[EvalCase]:
    """Return human-labeled cases with `family` set to the corpus family. Synthetic cases are
    returned unchanged (their family was assigned from families.json at generation)."""
    by_id = {d.draft_id: d for d in drafts}
    known = set(family_of.values())
    ids = {g for c in cases if c.human_labeled for g in c.gold_edition_ids}
    ids |= {d.source_edition_id for d in drafts if d.source_edition_id}
    eds = catalog.get(sorted(ids))

    def corpus_family(edition_id: str) -> str | None:
        e = eds.get(edition_id)
        if e is None or not e.work_id:
            return None
        return family_of.get(e.work_id)

    errors: list[str] = []
    out: list[EvalCase] = []
    for c in cases:
        if not c.human_labeled:
            out.append(c)
            continue
        d = by_id.get(c.case_id)
        if d is None:
            errors.append(f"{c.case_id}: no draft in the frozen queue")
            continue
        if d.family not in known:
            errors.append(f"{c.case_id}: draft family {d.family!r} not in families.json")
            continue
        if d.source_edition_id and corpus_family(d.source_edition_id) != d.family:
            errors.append(f"{c.case_id}: draft source edition is not in the draft's family")
            continue
        bad = [g for g in c.gold_edition_ids if corpus_family(g) != d.family]
        if bad:
            errors.append(
                f"{c.case_id}: chosen edition(s) {bad} missing from or conflicting with the "
                f"draft family {d.family!r}"
            )
            continue
        out.append(c.model_copy(update={"family": d.family}))
    if errors:
        raise FamilyMappingError("; ".join(errors))
    return out


def load_frozen_queue(queue: Path) -> tuple[list[Draft], str]:
    """Load a queue only if its manifest exists and pins its exact sha256."""
    manifest = queue.with_suffix(".manifest.json")
    if not manifest.exists():
        raise FamilyMappingError(f"{queue}: no manifest; queue is not frozen")
    digest = hashlib.sha256(queue.read_bytes()).hexdigest()
    if json.loads(manifest.read_text(encoding="utf-8")).get("queue_sha256") != digest:
        raise FamilyMappingError(f"{queue} does not match {manifest} (sha256)")
    return load_drafts(queue), digest
