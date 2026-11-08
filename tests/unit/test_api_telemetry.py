from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from bera import isbn
from bera.api import create_app
from bera.config import Settings
from bera.service import Resolver


@pytest.fixture
def client(make_resolver: Any, tmp_path: Any) -> TestClient:
    settings = Settings(
        var_dir=tmp_path,
        catalog_db=tmp_path / "unused",
        llm_provider="none",
        mock_mode="cite_first",
    )
    resolver: Resolver = make_resolver(None)
    return TestClient(create_app(settings, resolver))


def isbn_of(n: int) -> str:
    body = f"9780{n:08d}"
    return body + isbn.isbn13_check_digit(body)


def test_health_reports_pending_capabilities(client: TestClient) -> None:
    body = client.get("/api/health").json()
    caps = body["capabilities"]
    assert caps["embedding_retrieval"] == "not configured in this process"
    assert caps["reranker"] == "not configured in this process"
    assert caps["calibration"].startswith("uncalibrated")
    assert caps["llm"] == "disabled"
    assert body["catalog_meta"]["all_synthetic"] == "True"


def test_resolve_and_security_headers(client: TestClient) -> None:
    r = client.post("/api/resolve", json={"isbn": isbn_of(1001)})
    assert r.status_code == 200 and r.json()["outcome"] == "suggest"
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize(
    "payload", [{}, {"bogus": "x"}, {"publish_year": 2001}, {"title": "x" * 2001}]
)
def test_invalid_queries_rejected(client: TestClient, payload: dict[str, Any]) -> None:
    assert client.post("/api/resolve", json=payload).status_code == 422


def test_body_size_limit(client: TestClient) -> None:
    big = json.dumps({"title": "a" * 1000, "free_text": "b" * 20000})
    r = client.post("/api/resolve", content=big, headers={"content-type": "application/json"})
    assert r.status_code == 413


def test_feedback_flow(client: TestClient) -> None:
    rid = client.post("/api/resolve", json={"isbn": isbn_of(1012)}).json()["request_id"]
    ok = client.post(
        "/api/feedback", json={"request_id": rid, "edition_id": "SYN-E0013", "decision": "confirm"}
    )
    assert ok.status_code == 200
    not_shown = client.post(
        "/api/feedback", json={"request_id": rid, "edition_id": "SYN-E0001", "decision": "confirm"}
    )
    assert not_shown.status_code == 422
    unknown = client.post("/api/feedback", json={"request_id": "0" * 32, "decision": "reject"})
    assert unknown.status_code == 404
    summary = client.get("/api/traces/summary").json()
    assert summary["feedback"] == {"confirm": 1}


def test_traces_never_store_raw_query_text(make_resolver: Any, traces: Any) -> None:
    from bera.models import Query

    marker = "ZebraMarker7731"
    make_resolver(None).resolve(
        Query(title=f"{marker} lighthouse", author=marker, free_text=f"{marker} notes")
    )
    rows = traces.raw_rows()
    assert rows
    dumped = json.dumps(rows)
    assert marker not in dumped and marker.lower() not in dumped
    assert len(rows[0]["query_hmac"]) == 64


def test_hmac_is_stable_per_salt(traces: Any) -> None:
    from bera.models import Query

    q = Query(title="Salt Roads")
    assert traces.query_hmac(q) == traces.query_hmac(Query(title="Salt Roads"))
    assert traces.query_hmac(q) != traces.query_hmac(Query(title="Salt Road"))
