"""Local ML components: embedding retrieval and cross-encoder reranking.

Models load only from the pinned, verified local copies listed in models.lock.json; nothing
is fetched at runtime (HF_HUB_OFFLINE is forced). `sentence_transformers` is imported lazily
so the core package and tier-1 CI do not need torch.

Query instruction for bge-small-en-v1.5: the model card recommends the prefix below for
short-query -> passage retrieval and says it is optional for v1.5. We use it as the fixed
default; any change must be decided on development data only.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bera.catalog import Catalog
from bera.config import REPO_ROOT
from bera.models import Edition, Query
from bera.retrieval import Hit
from bera.text import visible_escape

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
LOCK = REPO_ROOT / "models.lock.json"


@dataclass(frozen=True)
class LockedModel:
    role: str
    repo: str
    revision: str
    path: Path

    @property
    def label(self) -> str:
        return f"{self.repo}@{self.revision[:12]}"


def locked_model(role: str, models_dir: Path | None = None) -> LockedModel | None:
    """Return the verified local copy for a role, or None if absent/incomplete."""
    lock = json.loads(LOCK.read_text())
    for m in lock["models"]:
        if m["role"] == role:
            base = (
                (models_dir or REPO_ROOT / "models") / m["repo"].replace("/", "__") / m["revision"]
            )
            ok = all(
                (base / f["path"]).is_file() and (base / f["path"]).stat().st_size == f["size"]
                for f in m["files"]
            )
            if ok:
                return LockedModel(role, m["repo"], m["revision"], base)
            return None
    return None


def edition_text(e: Edition) -> str:
    parts = [
        e.title,
        e.subtitle or "",
        "; ".join(e.authors),
        "; ".join(e.publishers),
        e.edition_name or "",
        e.physical_format.value,
        str(e.publish_year or ""),
    ]
    return " | ".join(p for p in parts if p)


def query_text(q: Query) -> str:
    parts = [
        q.title,
        q.author,
        q.publisher,
        q.edition,
        q.physical_format,
        str(q.publish_year) if q.publish_year else None,
        q.free_text,
    ]
    return " | ".join(p for p in parts if p)


def _device() -> str:
    import torch

    return "mps" if torch.backends.mps.is_available() else "cpu"


def _offline() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


@dataclass
class EmbeddingRetriever:
    catalog: Catalog
    model: LockedModel
    cache_dir: Path
    name: str = "embedding"
    batch_size: int = 128
    _st: Any = field(default=None, init=False, repr=False)
    _ids: list[str] = field(default_factory=list, init=False, repr=False)
    _matrix: Any = field(default=None, init=False, repr=False)

    @property
    def label(self) -> str:
        return self.model.label

    def _load(self) -> None:
        if self._matrix is not None:
            return
        _offline()
        import numpy as np
        from sentence_transformers import SentenceTransformer

        self._st = SentenceTransformer(str(self.model.path), device=_device())
        with self.catalog.connect() as con:
            rows = con.execute(
                "SELECT edition_id, record_json FROM editions ORDER BY edition_id"
            ).fetchall()
        self._ids = [r["edition_id"] for r in rows]
        digest = hashlib.sha256(
            "".join(r["edition_id"] + r["record_json"] for r in rows).encode()
        ).hexdigest()[:16]
        cache = self.cache_dir / f"emb_{self.model.revision[:12]}_{digest}.npy"
        if cache.exists():
            self._matrix = np.load(cache)
            return
        texts = [edition_text(Edition.model_validate_json(r["record_json"])) for r in rows]
        self._matrix = self._st.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype("float32")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        np.save(cache, self._matrix)

    def retrieve(self, query: Query, k: int) -> list[Hit]:
        text = query_text(query)
        if not text:
            return []
        self._load()
        import numpy as np

        qv = self._st.encode(
            [BGE_QUERY_PREFIX + text],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0]
        scores = self._matrix @ qv.astype("float32")
        k = min(k, len(self._ids))
        top = np.argpartition(-scores, k - 1)[:k]
        order = sorted(top.tolist(), key=lambda i: (-float(scores[i]), self._ids[i]))
        return [Hit(self._ids[i], self.name, n + 1, float(scores[i])) for n, i in enumerate(order)]


@dataclass
class CrossEncoderReranker:
    model: LockedModel
    max_candidates: int = 30
    _ce: Any = field(default=None, init=False, repr=False)

    @property
    def label(self) -> str:
        return self.model.label

    def score(self, query: Query, editions: list[Edition]) -> list[float]:
        if not editions:
            return []
        if self._ce is None:
            _offline()
            from sentence_transformers import CrossEncoder

            self._ce = CrossEncoder(str(self.model.path), device=_device(), max_length=256)
        q = visible_escape(query_text(query))
        pairs = [(q, visible_escape(edition_text(e))) for e in editions]
        return [float(s) for s in self._ce.predict(pairs, show_progress_bar=False)]
