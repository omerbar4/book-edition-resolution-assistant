"""Conservative, UNCALIBRATED decision policy `conservative-rules-v1`.

This policy uses deterministic rules only. No score here is a probability and no threshold
was fit on data: calibration is PENDING until grouped out-of-fold dev predictions exist
(docs/DECISION_POLICY.md). Until then, model adjudication is advisory: it can never turn a
REVIEW into a SUGGEST.

SUGGEST requires ALL of:
- no suspicious Unicode in the query, nor in the suggested record;
- ISBN route: the valid ISBN maps to exactly one edition and no field check disagrees; or
- retrieval route: exactly one candidate is "consistent" (title AGREE, author AGREE, zero
  DISAGREE checks), it also agrees on at least one distinguishing field
  (isbn, physical_format, publish_year, publisher, language, or edition), AND no other
  edition is "compatible" with the query (title AGREE, author not DISAGREE, zero DISAGREE).
  Unknown fields never distinguish, so an alternative whose author/year/format is merely
  missing blocks the suggestion. Compatibility is checked against the retrieved candidates
  and, deterministically, against a catalog-wide pool (same title phrase or same work); if
  that pool cannot be enumerated completely the query goes to REVIEW.
Everything else is REVIEW with explicit reason codes.

v1 changes from v0: unknown-author alternatives block suggestions (v0 dropped them because
consistency requires author AGREE), and uniqueness is no longer inferred from the retrieved
list alone. The ISBN route is unchanged: a missing ISBN on another record is unknown and does
not by itself invalidate a unique explicit mapping.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bera.models import CandidateView, CheckStatus, Outcome, Reason, Route

POLICY_VERSION = "conservative-rules-v1"
CONFIDENCE_STATUS = (
    "uncalibrated: rule-based policy; scores are ranking scores, not probabilities "
    "(calibration pending grouped out-of-fold dev evaluation)"
)
DISTINGUISHING = frozenset(
    {"isbn", "physical_format", "publish_year", "publisher", "language", "edition"}
)


@dataclass
class Decision:
    outcome: Outcome
    suggested: str | None
    reasons: list[Reason] = field(default_factory=list)
    ambiguous_ids: list[str] = field(default_factory=list)  # candidates worth adjudicating


def _status(c: CandidateView, name: str) -> CheckStatus | None:
    for ch in c.checks:
        if ch.field == name:
            return ch.status
    return None


def is_consistent(c: CandidateView) -> bool:
    return (
        c.conflicts == 0
        and _status(c, "title") is CheckStatus.AGREE
        and _status(c, "author") is CheckStatus.AGREE
        and not c.unicode_flags
    )


def is_compatible(c: CandidateView) -> bool:
    """Not contradicted by anything the query supplied: unknown is compatible."""
    return (
        c.conflicts == 0
        and _status(c, "title") is CheckStatus.AGREE
        and _status(c, "author") is not CheckStatus.DISAGREE
    )


def has_distinguishing_agreement(c: CandidateView) -> bool:
    return any(ch.status is CheckStatus.AGREE and ch.field in DISTINGUISHING for ch in c.checks)


def decide(
    route: Route,
    candidates: list[CandidateView],
    query_flags: list[str],
    pre_reasons: list[Reason],
) -> Decision:
    reasons = list(pre_reasons)
    if query_flags:
        reasons.append(Reason.SUSPICIOUS_UNICODE)

    if not candidates:
        reasons += [Reason.NO_CANDIDATES, Reason.LIKELY_NOT_IN_CORPUS]
        return Decision(Outcome.REVIEW, None, _dedupe(reasons))

    if route is Route.ISBN_DUPLICATE:
        reasons.append(Reason.DUPLICATE_ISBN)
        return Decision(
            Outcome.REVIEW, None, _dedupe(reasons), [c.edition.edition_id for c in candidates]
        )

    if route is Route.ISBN_REPAIR:
        reasons.append(Reason.ISBN_REPAIR_HYPOTHESIS)
        return Decision(Outcome.REVIEW, None, _dedupe(reasons))

    if route is Route.ISBN_EXACT:
        only = candidates[0]
        if only.conflicts > 0:
            reasons.append(Reason.FIELD_CONFLICT)
        if only.unicode_flags:
            reasons.append(Reason.SUSPICIOUS_UNICODE)
        if Reason.FIELD_CONFLICT in reasons or Reason.SUSPICIOUS_UNICODE in reasons:
            return Decision(Outcome.REVIEW, None, _dedupe(reasons))
        reasons.append(Reason.UNIQUE_ISBN_NO_CONFLICT)
        return Decision(Outcome.SUGGEST, only.edition.edition_id, _dedupe(reasons))

    # Retrieval route
    top = candidates[0]
    if _status(top, "title") is CheckStatus.DISAGREE or top.agreements == 0:
        reasons.append(Reason.LIKELY_NOT_IN_CORPUS)
    consistent = [c for c in candidates if is_consistent(c)]
    if any(c.conflicts > 0 for c in candidates[:1]):
        reasons.append(Reason.FIELD_CONFLICT)
    if len(consistent) > 1:
        reasons.append(Reason.MULTIPLE_CONSISTENT)
        return Decision(
            Outcome.REVIEW, None, _dedupe(reasons), [c.edition.edition_id for c in consistent]
        )
    if len(consistent) == 1 and has_distinguishing_agreement(consistent[0]) and not query_flags:
        alts = [c for c in candidates if c is not consistent[0] and is_compatible(c)]
        if alts:
            reasons.append(Reason.UNDISTINGUISHED_ALTERNATIVE)
            return Decision(
                Outcome.REVIEW,
                None,
                _dedupe(reasons),
                [consistent[0].edition.edition_id, *[c.edition.edition_id for c in alts]][:5],
            )
        reasons.append(Reason.UNIQUE_CONSISTENT_MATCH)
        return Decision(Outcome.SUGGEST, consistent[0].edition.edition_id, _dedupe(reasons))
    if len(consistent) == 1:
        reasons.append(Reason.INSUFFICIENT_EVIDENCE)
    elif Reason.LIKELY_NOT_IN_CORPUS not in reasons:
        reasons.append(Reason.INSUFFICIENT_EVIDENCE)
    # Ambiguous among the top candidates that are not contradicted.
    ambiguous = [c.edition.edition_id for c in candidates if c.conflicts == 0][:5]
    return Decision(Outcome.REVIEW, None, _dedupe(reasons), ambiguous if len(ambiguous) > 1 else [])


def apply_catalog_scan(
    decision: Decision, alternatives: list[CandidateView], complete: bool
) -> Decision:
    """Downgrade a retrieval-route SUGGEST when the catalog-wide pool holds another compatible
    edition, or when the pool could not be enumerated completely."""
    if decision.outcome is not Outcome.SUGGEST or decision.suggested is None:
        return decision
    alts = [a for a in alternatives if a.edition.edition_id != decision.suggested]
    alts = [a for a in alts if is_compatible(a)]
    base = [r for r in decision.reasons if r is not Reason.UNIQUE_CONSISTENT_MATCH]
    if not complete:
        return Decision(Outcome.REVIEW, None, _dedupe([*base, Reason.CATALOG_SCAN_INCOMPLETE]))
    if alts:
        return Decision(
            Outcome.REVIEW,
            None,
            _dedupe([*base, Reason.CATALOG_ALTERNATIVE]),
            [decision.suggested, *[a.edition.edition_id for a in alts]][:5],
        )
    return decision


def _dedupe(reasons: list[Reason]) -> list[Reason]:
    return list(dict.fromkeys(reasons))
