"""Conservative, UNCALIBRATED decision policy `conservative-rules-v0`.

This policy uses deterministic rules only. No score here is a probability and no threshold
was fit on data: calibration is PENDING until grouped out-of-fold dev predictions exist
(docs/DECISION_POLICY.md). Until then, model adjudication is advisory: it can never turn a
REVIEW into a SUGGEST.

SUGGEST requires ALL of:
- no suspicious Unicode in the query, nor in the suggested record;
- ISBN route: the valid ISBN maps to exactly one edition and no field check disagrees; or
- retrieval route: exactly one candidate is "consistent" (title AGREE, author AGREE, zero
  DISAGREE checks) and it also agrees on at least one distinguishing field
  (isbn, physical_format, publish_year, publisher, language, or edition).
Everything else is REVIEW with explicit reason codes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bera.models import CandidateView, CheckStatus, Outcome, Reason, Route

POLICY_VERSION = "conservative-rules-v0"
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
        reasons.append(Reason.UNIQUE_CONSISTENT_MATCH)
        return Decision(Outcome.SUGGEST, consistent[0].edition.edition_id, _dedupe(reasons))
    if len(consistent) == 1:
        reasons.append(Reason.INSUFFICIENT_EVIDENCE)
    elif Reason.LIKELY_NOT_IN_CORPUS not in reasons:
        reasons.append(Reason.INSUFFICIENT_EVIDENCE)
    # Ambiguous among the top candidates that are not contradicted.
    ambiguous = [c.edition.edition_id for c in candidates if c.conflicts == 0][:5]
    return Decision(Outcome.REVIEW, None, _dedupe(reasons), ambiguous if len(ambiguous) > 1 else [])


def _dedupe(reasons: list[Reason]) -> list[Reason]:
    return list(dict.fromkeys(reasons))
