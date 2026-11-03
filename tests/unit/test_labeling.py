from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from bera.api import create_app
from bera.config import Settings
from bera.evalkit.cases import load_cases
from bera.evalkit.drafts import draft_batch, save_drafts
from bera.labeling import LabelStore


@pytest.fixture
def editions(catalog: Any) -> list[Any]:
    with catalog.connect() as con:
        ids = [r[0] for r in con.execute("SELECT edition_id FROM editions")]
    return list(catalog.get(ids).values())


PROBES = [{"title": f"Probe Book {i}", "author": "Nobody"} for i in range(12)]


def make_queue(tmp_path: Path, editions: list[Any], split: str = "dev") -> Path:
    drafts = draft_batch(
        editions,
        PROBES,
        split=split,
        split_seed=20261103,
        seed=1,
        n_in_corpus=8,
        n_probes=2,
        prefix=f"{split}-b1",
    )
    path = tmp_path / f"{split}_queue.jsonl"
    save_drafts(path, drafts)
    return path


def test_drafts_are_deterministic_and_split_pure(tmp_path: Path, editions: list[Any]) -> None:
    a = make_queue(tmp_path / "a", editions).read_text()
    b = make_queue(tmp_path / "b", editions).read_text()
    assert a == b
    assert all(json.loads(x)["split"] == "dev" for x in a.splitlines())


def test_heldout_queue_is_refused(tmp_path: Path, editions: list[Any], catalog: Any) -> None:
    q = make_queue(tmp_path, editions, split="heldout")
    with pytest.raises(RuntimeError):
        LabelStore(q, tmp_path / "labels.jsonl", catalog, allow_heldout=False)


def test_blind_first_flow(tmp_path: Path, editions: list[Any], make_resolver: Any) -> None:
    q = make_queue(tmp_path, editions)
    labels = tmp_path / "labels.jsonl"
    settings = Settings(
        var_dir=tmp_path,
        catalog_db=tmp_path / "x",
        llm_provider="none",
        mock_mode="cite_first",
        label_queue=q,
        labels_path=labels,
    )
    client = TestClient(create_app(settings, make_resolver(None)))
    body = client.get("/api/label/queue").json()
    assert body["total"] == 10 and "proposed" not in json.dumps(body)
    first = body["items"][0]["draft_id"]

    bad = client.post(
        "/api/label/submit",
        json={"draft_id": first, "labeler": "ob", "expected": "suggest", "gold_edition_ids": []},
    )
    assert bad.status_code == 422
    unknown = client.post(
        "/api/label/submit",
        json={
            "draft_id": first,
            "labeler": "ob",
            "expected": "suggest",
            "gold_edition_ids": ["NOPE"],
        },
    )
    assert unknown.status_code == 422

    ok = client.post(
        "/api/label/submit",
        json={
            "draft_id": first,
            "labeler": "ob",
            "expected": "suggest",
            "gold_edition_ids": ["SYN-E0001"],
        },
    ).json()
    assert ok["saved"] and "proposed" in ok
    cases = load_cases(labels)
    assert cases[0].origin == "ai_drafted_human_labeled" and cases[0].human_labeled
    assert cases[0].split == "dev"
    assert client.get("/api/label/queue").json()["labeled"] == 1

    rows = client.get("/api/label/search", params={"title": "lantern"}).json()
    titles = [r["title"] for r in rows]
    assert titles == sorted(titles)


def test_label_endpoints_absent_without_queue(make_resolver: Any, tmp_path: Path) -> None:
    settings = Settings(
        var_dir=tmp_path, catalog_db=tmp_path / "x", llm_provider="none", mock_mode="cite_first"
    )
    client = TestClient(create_app(settings, make_resolver(None)))
    assert client.get("/api/label/enabled").json() == {"enabled": False}
    assert client.get("/api/label/queue").status_code == 404
