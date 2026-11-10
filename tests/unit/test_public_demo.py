"""Public-demo profile (BERA_PUBLIC_DEMO=1): every restriction and security control.

The app is built through create_app's own path (no injected resolver) so the read-only
catalog, the startup checks and the absence of any trace store are exercised for real.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from bera.api import MAX_BODY_BYTES, create_app
from bera.catalog import Catalog
from bera.cli import DEFAULT_FIXTURES
from bera.config import Settings
from bera.web_security import RateLimit, client_key

FIXTURE_SHA = hashlib.sha256(DEFAULT_FIXTURES.read_bytes()).hexdigest()
FIXTURE_EDITIONS = 30


def public_settings(catalog_path: Path, var_dir: Path, **over: Any) -> Settings:
    base: dict[str, Any] = {
        "var_dir": var_dir,
        "catalog_db": catalog_path,
        "llm_provider": "none",
        "mock_mode": "cite_first",
        "public_demo": True,
        "expected_catalog_sha256": FIXTURE_SHA,
        "expected_editions": FIXTURE_EDITIONS,
        "rate_limit_per_minute": 600,
        "rate_limit_burst": 100,
    }
    base.update(over)
    return Settings(**base)


@pytest.fixture
def var_dir(tmp_path: Path) -> Path:
    d = tmp_path / "var"
    d.mkdir()
    return d


@pytest.fixture
def client(catalog_path: Path, var_dir: Path) -> Iterator[TestClient]:
    with TestClient(create_app(public_settings(catalog_path, var_dir))) as c:
        yield c


# ---- startup refuses unsafe configuration ----------------------------------------------------


@pytest.mark.parametrize(
    ("over", "message"),
    [
        ({"llm_provider": "mock"}, "LLM must stay disabled"),
        ({"llm_provider": "openai_compat", "llm_model": "x"}, "LLM must stay disabled"),
        ({"label_queue": Path("queue.jsonl")}, "labeling must not be enabled"),
        ({"expected_catalog_sha256": None}, "BERA_EXPECTED_CATALOG_SHA256 is required"),
        ({"expected_editions": None}, "BERA_EXPECTED_EDITIONS is required"),
        ({"expected_editions": 5366}, "catalog has 30 editions, expected 5366"),
        ({"expected_catalog_sha256": "0" * 64}, "sha256 does not match"),
    ],
)
def test_unsafe_or_mismatched_configuration_refuses_to_start(
    catalog_path: Path, var_dir: Path, over: dict[str, Any], message: str
) -> None:
    with pytest.raises(RuntimeError, match=message):
        create_app(public_settings(catalog_path, var_dir, **over))


def test_env_parsing_enables_public_demo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BERA_PUBLIC_DEMO", "1")
    monkeypatch.setenv("BERA_VAR_DIR", str(tmp_path))
    monkeypatch.setenv("BERA_EXPECTED_CATALOG_SHA256", "ab" * 32)
    monkeypatch.setenv("BERA_EXPECTED_EDITIONS", "5366")
    monkeypatch.setenv("BERA_TRUSTED_PROXY_HOPS", "1")
    s = Settings.from_env()
    assert s.public_demo and s.expected_editions == 5366 and s.trusted_proxy_hops == 1
    assert s.llm_provider == "none" and s.public_demo_problems() == []
    monkeypatch.setenv("BERA_LLM_PROVIDER", "mock")
    assert Settings.from_env().public_demo_problems()


# ---- routes ----------------------------------------------------------------------------------


def test_resolver_health_and_readiness_available(client: TestClient) -> None:
    health = client.get("/api/health").json()
    assert health["public_demo"] is True
    assert health["catalog_editions"] == FIXTURE_EDITIONS
    assert health["capabilities"]["llm"] == "disabled"
    ready = client.get("/api/ready")
    assert ready.status_code == 200 and ready.json()["status"] == "ready"
    r = client.post(
        "/api/resolve", json={"title": "Practical Data Structurs", "author": "Natarajan"}
    )
    assert r.status_code == 200
    assert r.json()["adjudication"]["status"] in {"disabled", "not_needed"}
    assert r.json()["capabilities"]["llm"] == "disabled"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/docs"),
        ("GET", "/docs/oauth2-redirect"),
        ("GET", "/redoc"),
        ("GET", "/openapi.json"),
        ("POST", "/openapi.json"),
        ("POST", "/api/feedback"),
        ("GET", "/api/traces/summary"),
        ("GET", "/api/label/enabled"),
        ("GET", "/api/label/queue"),
        ("POST", "/api/label/submit"),
        ("GET", "/api/label/search"),
        ("PUT", "/api/resolve-anything"),
        ("DELETE", "/api/health/x"),
    ],
)
def test_disabled_routes_return_404(client: TestClient, method: str, path: str) -> None:
    assert client.request(method, path).status_code == 404


def test_disabled_routes_404_even_with_ui_mounted(
    catalog_path: Path, var_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dist = tmp_path / "repo" / "frontend" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>ui</title>")
    monkeypatch.setattr("bera.api.REPO_ROOT", tmp_path / "repo")
    with TestClient(create_app(public_settings(catalog_path, var_dir))) as c:
        assert c.get("/").status_code == 200
        for method, path in [("POST", "/api/feedback"), ("GET", "/docs"), ("POST", "/docs")]:
            assert c.request(method, path).status_code == 404, (method, path)


def test_nothing_written_to_disk(client: TestClient, var_dir: Path) -> None:
    for _ in range(3):
        client.post("/api/resolve", json={"title": "Some Title", "author": "Somebody"})
    assert list(var_dir.iterdir()) == []


def test_catalog_opened_read_only(client: TestClient) -> None:
    catalog: Catalog = client.app.state.resolver.catalog  # type: ignore[attr-defined]
    assert catalog.read_only
    with catalog.connect() as con, pytest.raises(sqlite3.OperationalError):
        con.execute("DELETE FROM editions")


# ---- request size ----------------------------------------------------------------------------


def big_body() -> bytes:
    return json.dumps({"title": "x" * (MAX_BODY_BYTES + 100)}).encode()


def test_oversized_body_with_content_length_is_413(client: TestClient) -> None:
    r = client.post(
        "/api/resolve", content=big_body(), headers={"content-type": "application/json"}
    )
    assert r.status_code == 413


def test_oversized_chunked_body_without_content_length_is_413(client: TestClient) -> None:
    def chunks() -> Iterator[bytes]:
        body = big_body()
        for i in range(0, len(body), 1000):
            yield body[i : i + 1000]

    r = client.post("/api/resolve", content=chunks(), headers={"content-type": "application/json"})
    assert "content-length" not in {k.lower() for k in r.request.headers}
    assert r.status_code == 413


def test_invalid_content_length_is_refused(client: TestClient) -> None:
    r = client.post("/api/resolve", content=b"{}", headers={"content-length": "abc"})
    assert r.status_code in {400, 413}


def test_small_chunked_body_still_works(client: TestClient) -> None:
    def chunks() -> Iterator[bytes]:
        yield b'{"title": "Practical'
        yield b' Data Structures"}'

    r = client.post("/api/resolve", content=chunks(), headers={"content-type": "application/json"})
    assert r.status_code == 200


# ---- rate limit ------------------------------------------------------------------------------


def test_rate_limit_returns_429_with_retry_after(catalog_path: Path, var_dir: Path) -> None:
    s = public_settings(catalog_path, var_dir, rate_limit_per_minute=6, rate_limit_burst=3)
    with TestClient(create_app(s)) as c:
        codes = [c.post("/api/resolve", json={"title": "x"}).status_code for _ in range(5)]
        assert codes[:3] == [200, 200, 200] and codes[3:] == [429, 429]
        r = c.post("/api/resolve", json={"title": "x"})
        assert r.status_code == 429 and int(r.headers["retry-after"]) >= 1
        assert r.headers["strict-transport-security"]  # limit responses carry headers too
        # health and readiness stay available for uptime checks
        assert c.get("/api/health").status_code == 200
        assert c.get("/api/ready").status_code == 200


def test_rate_limit_is_per_client_and_ignores_spoofed_forwarded_for_without_trust(
    catalog_path: Path, var_dir: Path
) -> None:
    s = public_settings(catalog_path, var_dir, rate_limit_per_minute=6, rate_limit_burst=1)
    with TestClient(create_app(s)) as c:
        assert c.post("/api/resolve", json={"title": "x"}).status_code == 200
        # hops=0: X-Forwarded-For is ignored, so rotating it does not buy new buckets
        spoof = {"x-forwarded-for": "203.0.113.9"}
        assert c.post("/api/resolve", json={"title": "x"}, headers=spoof).status_code == 429


def scope(peer: str | None, xff: str | None = None) -> dict[str, Any]:
    headers = [] if xff is None else [(b"x-forwarded-for", xff.encode())]
    return {"type": "http", "client": (peer, 1234) if peer else None, "headers": headers}


def test_client_key_proxy_handling() -> None:
    # no trusted proxy: the TCP peer, header ignored
    assert client_key(scope("10.0.0.1", "1.2.3.4"), 0) == "10.0.0.1"
    # one trusted proxy: the right-most entry (appended by the proxy) wins; a client-supplied
    # left part cannot change the key
    assert client_key(scope("10.0.0.1", "6.6.6.6, 198.51.100.7"), 1) == "198.51.100.7"
    assert client_key(scope("10.0.0.1", "198.51.100.7"), 1) == "198.51.100.7"
    assert client_key(scope("10.0.0.1", "a, b, 198.51.100.7, 10.1.1.1"), 2) == "198.51.100.7"
    # safe fallbacks: malformed or too-short header -> TCP peer; no usable peer -> "unknown"
    assert client_key(scope("10.0.0.1", "not-an-ip"), 1) == "10.0.0.1"
    assert client_key(scope("10.0.0.1", ""), 1) == "10.0.0.1"
    assert client_key(scope("10.0.0.1", "198.51.100.7"), 2) == "10.0.0.1"
    assert client_key(scope(None, "garbage"), 1) == "unknown"
    assert client_key(scope("testclient"), 0) == "unknown"


def test_rate_limiter_memory_is_bounded() -> None:
    async def app(scope: Any, receive: Any, send: Any) -> None:  # pragma: no cover - unused
        return None

    now = [0.0]
    rl = RateLimit(app, per_minute=60, burst=2, max_clients=3, clock=lambda: now[0])
    for i in range(10):
        rl._take(f"10.0.0.{i}")
    assert len(rl.buckets) == 3 and list(rl.buckets) == ["10.0.0.7", "10.0.0.8", "10.0.0.9"]
    # refill: one token per second at 60/min
    assert rl._take("k") == 0 and rl._take("k") == 0 and rl._take("k") > 0
    now[0] += 1.0
    assert rl._take("k") == 0


# ---- headers ---------------------------------------------------------------------------------


def test_public_demo_security_headers(client: TestClient) -> None:
    for r in (client.get("/api/health"), client.post("/api/resolve", json={"title": "x"})):
        h = r.headers
        assert "default-src 'self'" in h["content-security-policy"]
        assert h["x-content-type-options"] == "nosniff"
        assert h["referrer-policy"] == "no-referrer"
        assert h["strict-transport-security"].startswith("max-age=")
        assert "camera=()" in h["permissions-policy"]
        assert "server" not in {k.lower() for k in h}


def test_local_profile_keeps_routes_and_has_no_hsts(make_resolver: Any, tmp_path: Path) -> None:
    s = Settings(var_dir=tmp_path, catalog_db=tmp_path / "x", llm_provider="none", mock_mode="m")
    with TestClient(create_app(s, make_resolver(None))) as c:
        assert c.get("/api/health").json()["public_demo"] is False
        assert c.get("/api/traces/summary").status_code == 200
        assert c.get("/openapi.json").status_code == 200
        r = c.get("/api/health")
        assert "strict-transport-security" not in r.headers
        assert "default-src 'self'" in r.headers["content-security-policy"]
        # the size limit applies in both profiles
        big = json.dumps({"title": "x" * (MAX_BODY_BYTES + 1)}).encode()
        assert c.post("/api/resolve", content=iter([big])).status_code == 413


def test_readiness_reports_mismatch_as_503(client: TestClient, var_dir: Path) -> None:
    client.app.state.resolver.catalog = Catalog(var_dir / "missing.sqlite", read_only=True)  # type: ignore[attr-defined]
    r = client.get("/api/ready")
    assert r.status_code == 503 and r.json()["status"] == "not_ready"
