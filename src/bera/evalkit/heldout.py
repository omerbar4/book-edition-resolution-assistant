"""Held-out queue plan: probe selection, probe drafts and the family checks (frozen rules).

Family rule (owner decision 2026-11-07): the 37 in-corpus queries come from 37 distinct
held-out families; reserves come from further distinct families. The only permitted shared
family is within the predefined set of verified-absent held-out probes: two of the three
probes share an author family, so the queue has 40 queries across 39 families. Family-grouped
statistics keep that pair together. Nothing else may overlap.
"""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from bera.evalkit.drafts import Draft, Proposed
from bera.evalkit.splits import family_split
from bera.evalkit.stratified import DRAFTER_V5, SPEC_FOR_NEW_DRAFTS
from bera.models import Query

PROBE_STRATUM = "out_of_corpus_probe"


def probe_family(p: Mapping[str, Any]) -> str:
    keys = sorted(p.get("author_keys") or [])
    return f"probe-author:{keys[0]}" if keys else f"probe:{p['title']}"


def heldout_probes(
    probes: Sequence[Mapping[str, Any]],
    status: Mapping[str, Mapping[str, Any]],
    split_seed: int,
    n: int,
) -> list[Mapping[str, Any]]:
    """Verified-absent probes whose family falls in the held-out split, in title order."""
    keep = [
        p
        for p in probes
        if status.get(str(p["title"]), {}).get("status") == "verified_absent"
        and family_split(probe_family(p), split_seed) == "heldout"
    ]
    return sorted(keep, key=lambda p: str(p["title"]))[:n]


def probe_drafts(
    probes: Sequence[Mapping[str, Any]], prefix: str, rng: random.Random, taken: set[str]
) -> list[Draft]:
    out = []
    for p in probes:
        did = f"{prefix}-{rng.getrandbits(40):010x}"
        while did in taken:
            did = f"{prefix}-{rng.getrandbits(40):010x}"
        taken.add(did)
        out.append(
            Draft(
                draft_id=did,
                split="heldout",
                family=probe_family(p),
                query=Query(title=str(p["title"]), author=p.get("author")),
                template=PROBE_STRATUM,
                drafted_by=DRAFTER_V5,
                stratum=PROBE_STRATUM,
                proposal_label_spec=SPEC_FOR_NEW_DRAFTS,
                proposed=Proposed(
                    expected="abstain", gold_edition_ids=[], ambiguity_reason="out_of_corpus"
                ),
            )
        )
    return out


def family_checks(
    in_corpus: Sequence[Draft],
    probes: Sequence[Draft],
    reserves: Sequence[Draft],
    expected_in_corpus: int,
    expected_probes: int,
    expected_reserves: int,
) -> dict[str, bool]:
    ic = Counter(d.family for d in in_corpus)
    pr = Counter(d.family for d in probes)
    rs = Counter(d.family for d in reserves)
    return {
        f"{expected_in_corpus} in-corpus queries from {expected_in_corpus} distinct families": (
            len(in_corpus) == expected_in_corpus and len(ic) == expected_in_corpus
        ),
        f"{expected_probes} probes; shared family only within the probe set": (
            len(probes) == expected_probes and all(d.stratum == PROBE_STRATUM for d in probes)
        ),
        "probe families disjoint from in-corpus and reserve families": not (set(pr) & set(ic))
        and not (set(pr) & set(rs)),
        f"{expected_reserves} reserves from distinct families, disjoint from the queue": (
            len(reserves) == expected_reserves
            and len(rs) == expected_reserves
            and not (set(rs) & set(ic))
        ),
        "no in-corpus query is a probe and no probe has a source edition": all(
            d.source_edition_id for d in in_corpus
        )
        and not any(d.source_edition_id for d in probes),
    }


def counts(in_corpus: Sequence[Draft], probes: Sequence[Draft]) -> dict[str, int]:
    fams = {d.family for d in [*in_corpus, *probes]}
    return {
        "queries": len(in_corpus) + len(probes),
        "families": len(fams),
        "in_corpus_queries": len(in_corpus),
        "probe_queries": len(probes),
        "probe_families": len({d.family for d in probes}),
    }
