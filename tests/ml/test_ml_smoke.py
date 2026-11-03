"""Smoke tests for the locally pinned models. Skipped when models or the ml group are absent
(tier-1 CI). They check wiring and determinism, not quality."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from bera.ml import CrossEncoderReranker, EmbeddingRetriever, locked_model
from bera.models import Query
from bera.service import Resolver

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("sentence_transformers") is None
    or locked_model("embedding") is None
    or locked_model("reranker") is None,
    reason="ml group or pinned models not installed",
)


def test_embedding_retrieval_and_cache(catalog: Any, tmp_path: Path) -> None:
    model = locked_model("embedding")
    assert model is not None
    r = EmbeddingRetriever(catalog, model, tmp_path)
    hits = r.retrieve(Query(title="The Lantern Keeper's Daughter"), 5)
    assert hits[0].edition_id.startswith("SYN-E000") and len(hits) == 5
    assert list(tmp_path.glob("emb_*.npy"))
    again = EmbeddingRetriever(catalog, model, tmp_path).retrieve(
        Query(title="The Lantern Keeper's Daughter"), 5
    )
    assert [h.edition_id for h in again] == [h.edition_id for h in hits]


def test_reranker_scores_relevant_higher(catalog: Any) -> None:
    model = locked_model("reranker")
    assert model is not None
    rr = CrossEncoderReranker(model)
    eds = catalog.get(["SYN-E0009", "SYN-E0021"])
    s = rr.score(
        Query(title="Practical Data Structures", author="Priya Natarajan"),
        [eds["SYN-E0009"], eds["SYN-E0021"]],
    )
    assert s[0] > s[1]


def test_resolver_reports_active_models(catalog: Any, tmp_path: Path) -> None:
    emb, rer = locked_model("embedding"), locked_model("reranker")
    assert emb is not None and rer is not None
    res = Resolver(
        catalog,
        None,
        None,
        retrievers=[EmbeddingRetriever(catalog, emb, tmp_path)],
        reranker=CrossEncoderReranker(rer),
    ).resolve(
        Query(title="Practical Data Structures", author="Natarajan, Priya", edition="2nd ed.")
    )
    assert res.capabilities.embedding_retrieval.startswith("active: BAAI/bge-small-en-v1.5")
    assert res.capabilities.reranker.startswith("active: cross-encoder/ms-marco-MiniLM-L6-v2")
    assert res.suggested_edition_id == "SYN-E0010"
    assert res.candidates[0].rerank_score is not None
