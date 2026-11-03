"""Evaluation metrics with explicit denominators (docs/EVAL_PROTOCOL.md).

Sets: N = all cases; A = answerable (expected == "suggest"); U = expected abstain
(unresolvable or out of corpus); S = cases where the system suggested an edition.

- recall@k, MRR, top-1 accuracy ............ over A, against gold_edition_ids
- correct-suggestion rate .................. correct suggestions / N
- wrong-match rate ......................... wrong suggestions / N
- error among suggestions .................. wrong suggestions / S
- abstention rate .......................... review outcomes / N
- correct-abstention rate .................. review outcomes in U / |U|
- missed-suggestion rate ................... review outcomes in A / |A|
A suggestion is correct only if expected == "suggest" and the suggested id is in gold.
Any suggestion on a U case is wrong (the input did not support a suggestion).
"""

from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field


@dataclass
class CaseResult:
    case_id: str
    family: str
    expected: str  # "suggest" | "abstain"
    gold: frozenset[str]
    ranked_ids: list[str]
    outcome: str  # "suggest" | "review"
    suggested: str | None
    timings_ms: dict[str, float] = field(default_factory=dict)
    adjudication_status: str = "not_needed"
    adjudication_choice: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    signal: float | None = None  # uncalibrated ranking signal for risk-coverage

    @property
    def answerable(self) -> bool:
        return self.expected == "suggest"

    @property
    def suggested_correct(self) -> bool:
        return self.outcome == "suggest" and self.answerable and self.suggested in self.gold

    @property
    def suggested_wrong(self) -> bool:
        return self.outcome == "suggest" and not self.suggested_correct

    @property
    def top1_correct(self) -> bool:
        return self.answerable and bool(self.ranked_ids) and self.ranked_ids[0] in self.gold


def category(r: CaseResult) -> str:
    if not r.answerable:
        return "correct_abstention" if r.outcome == "review" else "unsupported_suggestion"
    retrieved = any(i in r.gold for i in r.ranked_ids)
    if r.outcome == "suggest":
        if r.suggested_correct:
            return "correct_suggestion"
        return "wrong_suggestion_retrieval_miss" if not retrieved else "wrong_suggestion_ranking"
    if not retrieved:
        return "retrieval_failure"
    return "conservative_abstention" if r.top1_correct else "ranking_failure"


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4))


def _ratio(num: int, den: int) -> dict[str, object]:
    return {
        "value": None if den == 0 else round(num / den, 4),
        "numerator": num,
        "denominator": den,
    }


def percentile(values: Sequence[float], q: float) -> float | None:
    """Nearest-rank percentile."""
    if not values:
        return None
    s = sorted(values)
    rank = max(1, math.ceil(q / 100 * len(s)))
    return round(s[rank - 1], 3)


Metric = Callable[[Sequence[CaseResult]], float | None]


def bootstrap_ci(
    results: Sequence[CaseResult], metric: Metric, reps: int = 1000, seed: int = 0
) -> tuple[float, float] | None:
    """Percentile CI from resampling FAMILIES with replacement (cases are not independent)."""
    fams: dict[str, list[CaseResult]] = {}
    for r in results:
        fams.setdefault(r.family, []).append(r)
    keys = sorted(fams)
    if len(keys) < 2:
        return None
    rng = random.Random(seed)  # noqa: S311 - reproducible resampling, not security
    vals = []
    for _ in range(reps):
        sample = [r for k in rng.choices(keys, k=len(keys)) for r in fams[k]]
        v = metric(sample)
        if v is not None:
            vals.append(v)
    if not vals:
        return None
    vals.sort()
    return (
        round(vals[int(0.025 * (len(vals) - 1))], 4),
        round(vals[int(0.975 * (len(vals) - 1))], 4),
    )


def _rate(
    pred: Callable[[CaseResult], bool], over: Callable[[CaseResult], bool] | None = None
) -> Metric:
    def m(rs: Sequence[CaseResult]) -> float | None:
        base = [r for r in rs if over is None or over(r)]
        return None if not base else sum(pred(r) for r in base) / len(base)

    return m


def risk_coverage(results: Sequence[CaseResult]) -> list[dict[str, float]]:
    """Selective-prediction curve over the top-1 candidate ordered by `signal` (desc).

    Risk = fraction of answered cases whose top-1 is not a correct answer (U cases always
    count as errors when answered). The signal is an UNCALIBRATED ranking signal.
    """
    scored = sorted(
        (r for r in results if r.signal is not None), key=lambda r: (-(r.signal or 0.0), r.case_id)
    )
    out: list[dict[str, float]] = []
    wrong = 0
    n = len(results)
    for i, r in enumerate(scored, start=1):
        wrong += 0 if r.top1_correct else 1
        nxt = scored[i].signal if i < len(scored) else None
        if nxt != r.signal:  # emit only at threshold boundaries
            out.append(
                {
                    "threshold": float(r.signal or 0.0),
                    "coverage": round(i / n, 4),
                    "risk": round(wrong / i, 4),
                    "answered": i,
                }
            )
    return out


def signal_buckets(results: Sequence[CaseResult]) -> list[dict[str, object]]:
    """Precision of the top-1 per distinct signal value, with n and a Wilson interval."""
    groups: dict[float, list[CaseResult]] = {}
    for r in results:
        if r.signal is not None:
            groups.setdefault(r.signal, []).append(r)
    rows: list[dict[str, object]] = []
    for s in sorted(groups, reverse=True):
        rs = groups[s]
        k = sum(r.top1_correct for r in rs)
        rows.append(
            {
                "signal": s,
                "n": len(rs),
                "top1_correct": k,
                "precision": round(k / len(rs), 4),
                "wilson95": wilson(k, len(rs)),
            }
        )
    return rows


def compute(
    results: Sequence[CaseResult],
    ks: Sequence[int] = (1, 5, 10),
    reps: int = 1000,
    seed: int = 0,
    cost_per_1k_tokens: float = 0.0,
) -> dict[str, object]:
    n = len(results)
    a = [r for r in results if r.answerable]
    u = [r for r in results if not r.answerable]
    s = [r for r in results if r.outcome == "suggest"]
    correct = sum(r.suggested_correct for r in results)
    wrong = sum(r.suggested_wrong for r in results)
    review = sum(r.outcome == "review" for r in results)

    def rr(r: CaseResult) -> float:
        for i, eid in enumerate(r.ranked_ids, start=1):
            if eid in r.gold:
                return 1.0 / i
        return 0.0

    out: dict[str, object] = {
        "counts": {
            "N": n,
            "A_answerable": len(a),
            "U_expected_abstain": len(u),
            "S_suggested": len(s),
            "families": len({r.family for r in results}),
        },
        "retrieval": {
            f"recall@{k}": _ratio(
                sum(any(i in r.gold for i in r.ranked_ids[:k]) for r in a), len(a)
            )
            for k in ks
        },
        "mrr": {
            "value": None if not a else round(sum(rr(r) for r in a) / len(a), 4),
            "denominator": len(a),
        },
        "top1_accuracy": _ratio(sum(r.top1_correct for r in a), len(a)),
        "correct_suggestion_rate": _ratio(correct, n),
        "wrong_match_rate": _ratio(wrong, n),
        "error_among_suggestions": _ratio(wrong, len(s)),
        "abstention_rate": _ratio(review, n),
        "correct_abstention_rate": _ratio(sum(r.outcome == "review" for r in u), len(u)),
        "missed_suggestion_rate": _ratio(sum(r.outcome == "review" for r in a), len(a)),
        "categories": dict(sorted(Counter(category(r) for r in results).items())),
    }
    out["bootstrap95_by_family"] = {
        "wrong_match_rate": bootstrap_ci(results, _rate(lambda r: r.suggested_wrong), reps, seed),
        "error_among_suggestions": bootstrap_ci(
            results,
            _rate(lambda r: r.suggested_wrong, lambda r: r.outcome == "suggest"),
            reps,
            seed,
        ),
        "correct_suggestion_rate": bootstrap_ci(
            results, _rate(lambda r: r.suggested_correct), reps, seed
        ),
        "top1_accuracy": bootstrap_ci(
            results, _rate(lambda r: r.top1_correct, lambda r: r.answerable), reps, seed
        ),
    }
    stages = sorted({k for r in results for k in r.timings_ms})
    out["latency_ms"] = {
        st: {
            "p50": percentile([r.timings_ms[st] for r in results if st in r.timings_ms], 50),
            "p95": percentile([r.timings_ms[st] for r in results if st in r.timings_ms], 95),
        }
        for st in stages
    }
    invoked = [r for r in results if r.adjudication_status not in ("not_needed", "disabled")]
    tokens = sum(r.input_tokens + r.output_tokens for r in results)
    chose = [r for r in results if r.adjudication_choice is not None]
    out["adjudication"] = {
        "invocation_rate": _ratio(len(invoked), n),
        "advisory_choice_in_gold": _ratio(
            sum(r.adjudication_choice in r.gold for r in chose), len(chose)
        ),
        "statuses": dict(sorted(Counter(r.adjudication_status for r in results).items())),
        "tokens_total": tokens,
        "estimated_cost": {
            "value": round(tokens / 1000 * cost_per_1k_tokens, 6),
            "rate_per_1k_tokens": cost_per_1k_tokens,
            "note": "local inference has no per-token charge; any non-zero "
            "rate is a hypothetical comparison",
        },
    }
    out["signal_buckets"] = signal_buckets(results)
    out["risk_coverage"] = risk_coverage(results)
    return out
