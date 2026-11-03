"""MockProvider: a deterministic test double. It is NOT a model and performs no inference.

Modes
- "cite_first":  choose the first candidate ref and cite its title (shape/plumbing check only)
- "abstain":     return a valid ABSTAIN
- "scripted":    return caller-provided raw text verbatim (attack and malformed-output tests)
- "error":       raise a non-retryable ProviderError
- "transport":   raise a retryable ProviderTransportError (optionally only for the first N calls)
- "timeout":     raise ProviderTimeout
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from bera.llm.provider import (
    AdjudicationRequest,
    ProviderError,
    ProviderResponse,
    ProviderTimeout,
    ProviderTransportError,
)


@dataclass
class MockProvider:
    mode: str = "cite_first"
    scripted_text: str = ""
    fail_first_n: int | None = (
        None  # for "transport"/"timeout": fail this many calls, then cite_first
    )
    name: str = "mock"
    calls: list[str] = field(default_factory=list)

    def complete(self, request: AdjudicationRequest, timeout_s: float) -> ProviderResponse:
        self.calls.append(request.request_id)
        n = len(self.calls)
        if self.mode in ("transport", "timeout"):
            if self.fail_first_n is None or n <= self.fail_first_n:
                if self.mode == "timeout":
                    raise ProviderTimeout("mock timeout")
                raise ProviderTransportError("mock connection refused")
            return self._cite_first(request)
        if self.mode == "error":
            raise ProviderError("mock non-retryable error")
        if self.mode == "scripted":
            return ProviderResponse(self.scripted_text, 0, 0)
        if self.mode == "abstain":
            payload = {
                "choice": "ABSTAIN",
                "confidence": 0.0,
                "decision_reason": "mock abstain",
                "evidence_fields": [],
                "needs_human": True,
            }
            return ProviderResponse(json.dumps(payload), 0, 0)
        return self._cite_first(request)

    @staticmethod
    def _cite_first(request: AdjudicationRequest) -> ProviderResponse:
        ref, edition = next(iter(request.candidates.items()))
        payload = {
            "choice": ref,
            "confidence": 0.5,
            "decision_reason": "MOCK: picks the first candidate; not an inference",
            "evidence_fields": [{"candidate_id": ref, "field": "title", "value": edition.title}],
            "needs_human": True,
        }
        return ProviderResponse(json.dumps(payload), 0, 0)
