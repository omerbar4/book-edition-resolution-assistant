"""FastAPI app. Decision support only: no endpoint performs an external action.

Two profiles:
- default (local): all routes, local trace/feedback store, optional labeling and LLM.
- public demo (`BERA_PUBLIC_DEMO=1`): deterministic resolver and review UI only. The LLM must
  be disabled; API docs, feedback, trace summary and labeling are not mounted (404); nothing
  is written to disk; the catalog is opened read-only and verified against the expected corpus
  sha256 and edition count before the app starts.
Both profiles enforce the request-size limit on received bytes and security headers; the
public demo adds HSTS, Permissions-Policy and a per-client rate limit on `/api/*` (health and
readiness exempt).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from bera import __version__
from bera.catalog import Catalog
from bera.config import REPO_ROOT, Settings
from bera.labeling import LabelStore
from bera.labeling import router as label_router
from bera.llm.mock import MockProvider
from bera.llm.openai_compat import OpenAICompatProvider
from bera.llm.provider import LLMProvider
from bera.models import FeedbackIn, Query, ResolveResponse
from bera.policy import POLICY_VERSION
from bera.service import Resolver
from bera.telemetry import TraceStore
from bera.web_security import CSP, BodySizeLimit, RateLimit, SecurityHeaders

__all__ = ["CSP", "MAX_BODY_BYTES", "create_app"]

MAX_BODY_BYTES = 16_384
ALL_METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


def build_provider(settings: Settings) -> LLMProvider | None:
    if settings.llm_provider == "mock":
        return MockProvider(mode=settings.mock_mode)
    if settings.llm_provider == "openai_compat":
        if not settings.llm_model:
            raise RuntimeError("BERA_LLM_MODEL is required for openai_compat")
        return OpenAICompatProvider(settings.llm_base_url, settings.llm_model)
    return None


def catalog_problems(catalog: Catalog, settings: Settings) -> list[str]:
    """Mismatches between the catalog and the expected corpus (empty = ready)."""
    problems = []
    try:
        count = catalog.count()
        meta = catalog.meta()
    except Exception as exc:  # any catalog failure means not ready
        return [f"catalog unreadable: {type(exc).__name__}"]
    if settings.expected_editions is not None and count != settings.expected_editions:
        problems.append(f"catalog has {count} editions, expected {settings.expected_editions}")
    expected_sha = settings.expected_catalog_sha256
    if expected_sha and meta.get("fixtures_sha256") != expected_sha:
        problems.append("catalog source sha256 does not match the expected corpus")
    return problems


def create_app(settings: Settings | None = None, resolver: Resolver | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    public = settings.public_demo
    if problems := settings.public_demo_problems():
        raise RuntimeError("unsafe public-demo configuration: " + "; ".join(problems))
    if resolver is None:
        if not settings.catalog_db.exists():
            raise RuntimeError(
                f"catalog not found at {settings.catalog_db}; run: "
                "uv run python -m bera.cli build-catalog"
            )
        from bera.llm.routes import load_gate

        resolver = Resolver(
            Catalog(settings.catalog_db, read_only=public),
            None if public else TraceStore(settings.trace_db, settings.salt_path),
            None if public else build_provider(settings),
            route_gate=load_gate(None if public else settings.llm_route_evidence),
        )
    if public:
        if resolver.provider is not None:
            raise RuntimeError("unsafe public-demo configuration: an LLM provider is set")
        if problems := catalog_problems(resolver.catalog, settings):
            raise RuntimeError("catalog check failed: " + "; ".join(problems))

    app = FastAPI(
        title="Book Edition Resolution Assistant",
        version=__version__,
        docs_url=None if public else "/docs",
        redoc_url=None if public else "/redoc",
        openapi_url=None if public else "/openapi.json",
    )
    app.state.resolver = resolver

    @app.get("/api/health")
    def health() -> dict[str, object]:
        """Liveness: the process is up and the catalog answers."""
        r: Resolver = app.state.resolver
        return {
            "status": "ok",
            "version": __version__,
            "policy_version": POLICY_VERSION,
            "public_demo": public,
            "catalog_editions": r.catalog.count(),
            "catalog_meta": r.catalog.meta(),
            "capabilities": r.capabilities().model_dump(),
        }

    @app.get("/api/ready", response_model=None)
    def ready() -> dict[str, object] | JSONResponse:
        """Readiness: the catalog matches the expected corpus and the profile is safe."""
        r: Resolver = app.state.resolver
        problems = catalog_problems(r.catalog, settings)
        if public and r.provider is not None:
            problems.append("LLM provider configured in public demo")
        if problems:
            return JSONResponse({"status": "not_ready", "problems": problems}, status_code=503)
        return {"status": "ready", "public_demo": public, "catalog_editions": r.catalog.count()}

    @app.post("/api/resolve", response_model=ResolveResponse)
    def resolve(query: Query) -> ResolveResponse:
        return app.state.resolver.resolve(query)  # type: ignore[no-any-return]

    if not public:

        @app.post("/api/feedback")
        def feedback(fb: FeedbackIn) -> dict[str, object]:
            r: Resolver = app.state.resolver
            if r.traces is None:
                raise HTTPException(503, "feedback store unavailable")
            shown = r.traces.candidate_ids(fb.request_id)
            if shown is None:
                raise HTTPException(404, "unknown request_id")
            if fb.edition_id is not None and fb.edition_id not in shown:
                raise HTTPException(422, "edition_id was not among the candidates shown")
            fid = r.traces.add_feedback(fb.request_id, fb.edition_id, fb.decision)
            return {"feedback_id": fid, "stored": "local feedback table (not a benchmark label)"}

        @app.get("/api/traces/summary")
        def traces_summary() -> dict[str, object]:
            r: Resolver = app.state.resolver
            return {} if r.traces is None else r.traces.summary()

        @app.get("/api/label/enabled")
        def label_enabled() -> dict[str, bool]:
            return {"enabled": settings.label_queue is not None}

        if settings.label_queue is not None and settings.labels_path is not None:
            store = LabelStore(
                settings.label_queue,
                settings.labels_path,
                resolver.catalog,
                settings.label_allow_heldout,
            )
            app.include_router(label_router(store))

    def not_found() -> None:
        raise HTTPException(404, "Not Found")

    # Any other /api path (and, in public demo, the docs paths) is a 404 for every method,
    # before the static UI mount could answer it with 405 or the SPA index.
    app.add_api_route("/api/{rest:path}", not_found, methods=ALL_METHODS, include_in_schema=False)
    if public:
        for path in ("/docs", "/docs/{rest:path}", "/redoc", "/openapi.json"):
            app.add_api_route(path, not_found, methods=ALL_METHODS, include_in_schema=False)

    dist = Path(REPO_ROOT / "frontend" / "dist")
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="ui")

    # Request path, outermost first: headers -> rate limit (public demo) -> body size -> app.
    # The rate limit is public-demo only: the local profile serves one operator (and the
    # labeling UI submits many cases in a row).
    app.add_middleware(BodySizeLimit, max_bytes=MAX_BODY_BYTES)
    if public:
        app.add_middleware(
            RateLimit,
            per_minute=settings.rate_limit_per_minute,
            burst=settings.rate_limit_burst,
            trusted_proxy_hops=settings.trusted_proxy_hops,
        )
    app.add_middleware(SecurityHeaders, public_demo=public)
    return app
