"""OpenAI-compatible chat-completions adapter for a LOCAL model server.

Intended targets: llama.cpp `llama-server` or Ollama's OpenAI-compatible endpoint, running
natively on the host. The base URL must be a loopback or host.docker.internal address;
anything else is refused. No API key is sent. Note: the Pydantic schema uses $defs/$ref,
which llama.cpp's grammar converter only partly supports; this is unverified until a real
model is approved. Constrained decoding (`response_format` + JSON schema) only shapes
output; strict validation downstream remains mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

from bera.llm.provider import (
    AdjudicationRequest,
    ProviderError,
    ProviderResponse,
    ProviderTimeout,
    ProviderTransportError,
)

LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "host.docker.internal"})
MAX_RESPONSE_BYTES = 65_536


def check_local_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in LOCAL_HOSTS:
        raise ValueError(
            f"refusing non-local LLM endpoint {base_url!r}; allowed hosts: {sorted(LOCAL_HOSTS)}"
        )
    return base_url.rstrip("/")


@dataclass
class OpenAICompatProvider:
    base_url: str
    model: str
    name: str = "openai_compat"
    transport: httpx.BaseTransport | None = None  # injectable for tests
    temperature: float = 0.0
    _client: httpx.Client | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.base_url = check_local_url(self.base_url)
        self.name = f"openai_compat:{self.model}"

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(transport=self.transport, follow_redirects=False)
        return self._client

    def complete(self, request: AdjudicationRequest, timeout_s: float) -> ProviderResponse:
        body = {
            "model": self.model,
            "messages": request.messages,
            "temperature": self.temperature,
            "max_tokens": request.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "adjudication",
                    "strict": True,
                    "schema": request.json_schema,
                },
            },
        }
        try:
            resp = self._http().post(
                f"{self.base_url}/chat/completions", json=body, timeout=timeout_s
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeout(type(exc).__name__) from exc
        except httpx.TransportError as exc:
            raise ProviderTransportError(type(exc).__name__) from exc
        if resp.status_code >= 500:
            raise ProviderTransportError(f"http {resp.status_code}")
        if resp.status_code != 200:
            raise ProviderError(f"http {resp.status_code}")
        if len(resp.content) > MAX_RESPONSE_BYTES:
            raise ProviderError("response too large")
        try:
            payload = resp.json()
            choice = payload["choices"][0]
            text = choice["message"]["content"]
            finish = choice.get("finish_reason")
            usage = payload.get("usage") or {}
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError("malformed provider payload") from exc
        if not isinstance(text, str):
            raise ProviderError("non-text content")
        if finish == "length":
            raise ProviderError("output truncated at max_tokens")
        return ProviderResponse(
            text=text,
            input_tokens=_int_or_none(usage.get("prompt_tokens")),
            output_tokens=_int_or_none(usage.get("completion_tokens")),
        )


def _int_or_none(v: object) -> int | None:
    return v if isinstance(v, int) and not isinstance(v, bool) else None
