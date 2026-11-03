from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from bera.catalog import Catalog
from bera.cli import DEFAULT_FIXTURES, build_catalog
from bera.llm.provider import LLMProvider
from bera.models import Query
from bera.service import Resolver
from bera.telemetry import TraceStore


@pytest.fixture(scope="session")
def catalog_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    db = tmp_path_factory.mktemp("catalog") / "catalog.sqlite"
    build_catalog(DEFAULT_FIXTURES, db)
    return db


@pytest.fixture
def catalog(catalog_path: Path) -> Catalog:
    return Catalog(catalog_path)


@pytest.fixture
def traces(tmp_path: Path) -> TraceStore:
    return TraceStore(tmp_path / "traces.sqlite", tmp_path / "salt.bin")


@pytest.fixture
def make_resolver(catalog: Catalog, traces: TraceStore) -> Callable[..., Resolver]:
    def _make(provider: LLMProvider | None = None) -> Resolver:
        return Resolver(catalog, traces, provider)

    return _make


@pytest.fixture
def resolve(make_resolver: Callable[..., Resolver]) -> Callable[..., object]:
    def _resolve(provider: LLMProvider | None = None, **fields: object):  # type: ignore[no-untyped-def]
        return make_resolver(provider).resolve(Query(**fields))  # type: ignore[arg-type]

    return _resolve
