"""FastAPI app. Local-only decision support: no endpoint performs an external action."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from bera import __version__
from bera.catalog import Catalog
from bera.config import REPO_ROOT, Settings
from bera.llm.mock import MockProvider
from bera.llm.openai_compat import OpenAICompatProvider
from bera.llm.provider import LLMProvider
from bera.models import FeedbackIn, Query, ResolveResponse
from bera.policy import POLICY_VERSION
from bera.service import Resolver
from bera.telemetry import TraceStore

MAX_BODY_BYTES = 16_384
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
)


def build_provider(settings: Settings) -> LLMProvider | None:
    if settings.llm_provider == "mock":
        return MockProvider(mode=settings.mock_mode)
    if settings.llm_provider == "openai_compat":
        if not settings.llm_model:
            raise RuntimeError("BERA_LLM_MODEL is required for openai_compat")
        return OpenAICompatProvider(settings.llm_base_url, settings.llm_model)
    return None


def create_app(settings: Settings | None = None, resolver: Resolver | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    if resolver is None:
        if not settings.catalog_db.exists():
            raise RuntimeError(
                f"catalog not found at {settings.catalog_db}; run: "
                "uv run python -m bera.cli build-catalog"
            )
        resolver = Resolver(
            Catalog(settings.catalog_db),
            TraceStore(settings.trace_db, settings.salt_path),
            build_provider(settings),
        )
    app = FastAPI(title="Book Edition Resolution Assistant", version=__version__)
    app.state.resolver = resolver

    @app.middleware("http")
    async def guard(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        length = request.headers.get("content-length")
        if length is not None and (not length.isdigit() or int(length) > MAX_BODY_BYTES):
            return JSONResponse({"detail": "request body too large"}, status_code=413)
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get("/api/health")
    def health() -> dict[str, object]:
        r: Resolver = app.state.resolver
        return {
            "status": "ok",
            "version": __version__,
            "policy_version": POLICY_VERSION,
            "catalog_editions": r.catalog.count(),
            "catalog_meta": r.catalog.meta(),
            "capabilities": r.capabilities().model_dump(),
        }

    @app.post("/api/resolve", response_model=ResolveResponse)
    def resolve(query: Query) -> ResolveResponse:
        return app.state.resolver.resolve(query)  # type: ignore[no-any-return]

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

    dist = Path(REPO_ROOT / "frontend" / "dist")
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="ui")
    return app
