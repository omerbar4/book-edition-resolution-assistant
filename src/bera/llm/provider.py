"""Provider interface. Providers only transport text; they never see raw OLIDs or act."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from bera.models import Edition


class ProviderError(Exception):
    """Non-retryable provider failure (bad request, auth, malformed transport payload)."""


class ProviderTransportError(ProviderError):
    """Retryable failure: connection refused/reset, HTTP 5xx."""


class ProviderTimeout(ProviderTransportError):
    """Per-attempt timeout. Retryable only while the stage deadline allows."""


@dataclass(frozen=True)
class AdjudicationRequest:
    request_id: str
    messages: list[dict[str, str]]
    json_schema: dict[str, object]
    # Opaque ref -> edition. Real providers must not use this; MockProvider may script on it.
    candidates: dict[str, Edition] = field(default_factory=dict)
    max_output_tokens: int = 400


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(Protocol):
    name: str

    def complete(self, request: AdjudicationRequest, timeout_s: float) -> ProviderResponse: ...
