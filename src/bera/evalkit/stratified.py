"""Stratified, family-diverse drafting for the fixed evaluation plan (docs/EVALUATION_PLAN.md).

Strata are predefined. A family-stratum pair is feasible if some edition of the family
yields a query for one of the stratum's templates whose every op changes the query, whose
promised fields remain, and which repeats no seen query. The edition-ambiguity stratum also
requires catalog structure (at least two editions of the family sharing the normalized title
and first author, the source being one of them). Feasibility never looks at proposals or
system results.

Assignment: one query per family. Required families (pool A) are matched first, then
optional families (pool B) in seeded order, by maximum bipartite matching of quota slots to
families. If the quotas cannot all be filled, or a required family cannot be placed, the
result says so. Quotas are never relaxed silently.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from bera.evalkit.drafts import (
    ALL_TEMPLATES,
    Draft,
    Proposed,
    query_key,
    template_effective,
)
from bera.evalkit.perturb import make_case
from bera.models import Edition
from bera.text import norm_person, norm_text

DRAFTER_V5 = (
    "template-drafter-v5 (deterministic program; predefined strata; one query per family; "
    "pool A first; opaque ids)"
)

STRATA: dict[str, tuple[str, ...]] = {
    "identifier": ("isbn10_hyphenated", "misread_isbn_digit"),
    "missing_metadata": ("title_author_only", "typo_title_with_format_year"),
    "author_variation": ("initials_author", "damaged_barcode_title_author_format"),
    "edition_ambiguity": ("title_author_only", "initials_author"),
    "format_year_conflict": ("year_shift", "format_swap"),
}
SPEC_FOR_NEW_DRAFTS = "v3"
SEED_TRIES = 8


def ambiguity_editions(eds: Sequence[Edition]) -> list[Edition]:
    """Editions sharing normalized title and first author with at least one other edition of
    the same family (catalog structure only)."""
    groups: dict[tuple[str, str], list[Edition]] = {}
    for e in eds:
        if e.authors:
            groups.setdefault((norm_text(e.title), norm_person(e.authors[0])), []).append(e)
    return sorted(
        (e for g in groups.values() if len(g) >= 2 for e in g), key=lambda e: e.edition_id
    )


@dataclass
class Candidate:
    family: str
    stratum: str
    template: str
    edition: Edition
    op_seed: int


@dataclass
class Plan:
    assigned: list[Candidate] = field(default_factory=list)
    reserves: list[Candidate] = field(default_factory=list)
    shortfall: dict[str, int] = field(default_factory=dict)
    unplaced_required: list[str] = field(default_factory=list)
    feasible_pairs: dict[str, int] = field(default_factory=dict)

    @property
    def feasible(self) -> bool:
        return not self.shortfall and not self.unplaced_required


def candidates(
    by_family: Mapping[str, Sequence[Edition]],
    families: Sequence[str],
    seen: set[str],
    catalog: Sequence[Edition],
    seed: int,
) -> dict[tuple[str, str], Candidate]:
    """The first feasible candidate per (family, stratum), found in a seeded order."""
    out: dict[tuple[str, str], Candidate] = {}
    for f in families:
        for stratum, templates in STRATA.items():
            rng = random.Random(f"{seed}:{f}:{stratum}")  # noqa: S311 - reproducible; str seeds are hash-independent
            pool = list(
                ambiguity_editions(by_family[f]) if stratum == "edition_ambiguity" else by_family[f]
            )
            rng.shuffle(pool)
            order = list(templates)
            rng.shuffle(order)
            found = None
            for name in order:
                for e in pool:
                    for _ in range(SEED_TRIES):
                        s = rng.randrange(2**31)
                        if not template_effective(name, e, s):
                            continue
                        q = make_case(e, ALL_TEMPLATES[name], s, catalog, f, "t", "v3").query
                        if query_key(q) in seen:
                            continue
                        found = Candidate(f, stratum, name, e, s)
                        break
                    if found:
                        break
                if found:
                    break
            if found:
                out[(f, stratum)] = found
    return out


def assign(
    cands: Mapping[tuple[str, str], Candidate],
    required: Sequence[str],
    optional: Sequence[str],
    quotas: Mapping[str, int],
    n_reserves: int,
) -> Plan:
    slots = [s for s, k in quotas.items() for _ in range(k)]
    slot_of: dict[int, str] = {}  # slot index -> family
    fam_of: dict[str, int] = {}

    def try_place(f: str, seen: set[int]) -> bool:
        for i, s in enumerate(slots):
            if (f, s) not in cands or i in seen:
                continue
            seen.add(i)
            if i not in slot_of or try_place(slot_of[i], seen):
                slot_of[i] = f
                fam_of[f] = i
                return True
        return False

    plan = Plan(feasible_pairs={s: sum(1 for (_, x) in cands if x == s) for s in quotas})
    for f in required:
        if not try_place(f, set()):
            plan.unplaced_required.append(f)
    for f in optional:
        if len(slot_of) == len(slots):
            break
        try_place(f, set())
    for i, s in enumerate(slots):
        if i in slot_of:
            plan.assigned.append(cands[(slot_of[i], s)])
        else:
            plan.shortfall[s] = plan.shortfall.get(s, 0) + 1
    used = set(fam_of)
    order = list(quotas)
    for f in optional:
        if len(plan.reserves) >= n_reserves:
            break
        if f in used:
            continue
        for s in order:
            if (f, s) in cands:
                plan.reserves.append(cands[(f, s)])
                used.add(f)
                order = order[1:] + order[:1]  # rotate reserve strata
                break
    return plan


def to_drafts(
    plan_items: Sequence[Candidate],
    catalog: Sequence[Edition],
    prefix: str,
    rng: random.Random,
    taken_ids: set[str],
) -> list[Draft]:
    out = []
    for c in plan_items:
        case = make_case(
            c.edition,
            ALL_TEMPLATES[c.template],
            c.op_seed,
            catalog,
            c.family,
            "t",
            SPEC_FOR_NEW_DRAFTS,
        )
        token = f"{rng.getrandbits(40):010x}"
        while f"{prefix}-{token}" in taken_ids:
            token = f"{rng.getrandbits(40):010x}"
        did = f"{prefix}-{token}"
        taken_ids.add(did)
        out.append(
            Draft(
                draft_id=did,
                split="dev",
                family=c.family,
                query=case.query,
                template=c.template,
                drafted_by=DRAFTER_V5,
                source_edition_id=c.edition.edition_id,
                op_seed=c.op_seed,
                stratum=c.stratum,
                proposal_label_spec=SPEC_FOR_NEW_DRAFTS,
                proposed=Proposed(
                    expected=case.expected,
                    gold_edition_ids=case.gold_edition_ids,
                    ambiguity_reason=case.ambiguity_reason,
                ),
            )
        )
    return out
