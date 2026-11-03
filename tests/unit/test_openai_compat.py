"""Adapter tests use httpx.MockTransport: no network, no model."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from bera.llm.adjudicator import Adjudicator
from bera.llm.openai_compat import OpenAICompatProvider, check_local_url
from bera.llm.provider import AdjudicationRequest, ProviderError, ProviderTransportError
from bera.models import AdjudicationStatus, Query


def provider(handler: Any) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        "http://127.0.0.1:8080/v1", "test-model", transport=httpx.MockTransport(handler)
    )


def chat(content: str, finish: str = "stop", status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        json={
            "choices": [{"message": {"content": content}, "finish_reason": finish}],
            "usage": {"prompt_tokens": 321, "completion_tokens": 45},
        },
    )


REQ = AdjudicationRequest("r", [{"role": "user", "content": "x"}], {"type": "object"})


def test_rejects_non_local_endpoints() -> None:
    for url in ["https://api.example.com/v1", "http://10.0.0.5:8080", "file:///etc/passwd"]:
        with pytest.raises(ValueError):
            check_local_url(url)
    assert (
        check_local_url("http://host.docker.internal:8080/v1/")
        == "http://host.docker.internal:8080/v1"
    )


def test_request_shape_and_usage() -> None:
    seen: dict[str, Any] = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen.update(json.loads(req.content))
        seen["url"] = str(req.url)
        seen["auth"] = req.headers.get("authorization")
        return chat('{"ok": 1}')

    out = provider(handler).complete(REQ, 5)
    assert seen["url"] == "http://127.0.0.1:8080/v1/chat/completions"
    assert seen["auth"] is None
    assert seen["temperature"] == 0.0 and seen["max_tokens"] == 400
    assert seen["response_format"]["type"] == "json_schema"
    assert out.input_tokens == 321 and out.output_tokens == 45


@pytest.mark.parametrize("status,exc", [(503, ProviderTransportError), (400, ProviderError)])
def test_http_errors_classified(status: int, exc: type[Exception]) -> None:
    with pytest.raises(exc):
        provider(lambda r: httpx.Response(status)).complete(REQ, 5)


def test_connection_error_is_retryable() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(ProviderTransportError):
        provider(handler).complete(REQ, 5)


def test_truncated_output_is_an_error() -> None:
    with pytest.raises(ProviderError):
        provider(lambda r: chat('{"cho', finish="length")).complete(REQ, 5)


def test_malformed_payload_is_an_error() -> None:
    with pytest.raises(ProviderError):
        provider(lambda r: httpx.Response(200, json={"nope": 1})).complete(REQ, 5)


def test_end_to_end_with_adjudicator(catalog: Any) -> None:
    eds = catalog.get(["SYN-E0012", "SYN-E0013"])
    refs = {"c1": eds["SYN-E0012"], "c2": eds["SYN-E0013"]}
    answer = json.dumps(
        {
            "choice": "c2",
            "confidence": 0.7,
            "decision_reason": "hardcover requested",
            "evidence_fields": [
                {"candidate_id": "c2", "field": "physical_format", "value": "hardcover"}
            ],
            "needs_human": False,
        }
    )
    v = Adjudicator(provider(lambda r: chat(answer))).run(
        "r", Query(title="Gardens of Quiet Stone", physical_format="hardcover"), refs
    )
    assert v.status is AdjudicationStatus.COMPLETED and v.chosen_edition_id == "SYN-E0013"
    assert v.input_tokens == 321


def test_transport_failure_then_success_uses_two_attempts(catalog: Any) -> None:
    calls = {"n": 0}
    eds = catalog.get(["SYN-E0012"])

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(502)
        return chat(
            json.dumps(
                {
                    "choice": "ABSTAIN",
                    "confidence": 0.1,
                    "decision_reason": "tie",
                    "evidence_fields": [],
                    "needs_human": True,
                }
            )
        )

    v = Adjudicator(provider(handler), sleep=lambda s: None).run(
        "r", Query(title="x"), {"c1": eds["SYN-E0012"]}
    )
    assert v.status is AdjudicationStatus.COMPLETED and v.attempts == 2
