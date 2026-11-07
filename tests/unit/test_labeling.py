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
        probe_status={p["title"]: "verified_absent" for p in PROBES},
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

    page = client.get("/api/label/search", params={"title": "lantern"}).json()
    titles = [r["title"] for r in page["items"]]
    assert titles == sorted(titles)
    assert page["total"] >= len(page["items"]) and "truncated" in page

    small = client.get("/api/label/search", params={"title": "lantern", "limit": 1}).json()
    assert small["returned"] == 1 and small["truncated"] == (small["total"] > 1)

    second = body["items"][1]["draft_id"]
    sk = client.post("/api/label/skip", json={"draft_id": second, "labeler": "ob"})
    assert sk.status_code == 200 and "proposed" not in sk.text
    q2 = client.get("/api/label/queue").json()
    assert q2["skipped"] == 1 and q2["independent"] == 1
    assert {i["draft_id"]: i["status"] for i in q2["items"]}[second] == "skipped"


PRE_SAVE_ITEM_KEYS = {"draft_id", "split", "query", "labeled", "status"}
LEAK_KEYS = ("proposed", "template", "template_note", "gold_edition_ids", "ambiguity_reason")


def test_pre_save_responses_hide_template_proposal_and_gold(
    tmp_path: Path, editions: list[Any], make_resolver: Any
) -> None:
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
    store_drafts = [json.loads(x) for x in q.read_text().splitlines()]
    templates = {d["template"] for d in store_drafts}
    proposed_gold = {g for d in store_drafts for g in d["proposed"]["gold_edition_ids"]}
    client = TestClient(create_app(settings, make_resolver(None)))

    def assert_blind(text: str) -> None:
        for key in LEAK_KEYS:
            assert f'"{key}"' not in text, key
        for t in templates:
            assert t not in text, t

    queue = client.get("/api/label/queue")
    assert_blind(queue.text)
    items = queue.json()["items"]
    assert items and all(set(i) == PRE_SAVE_ITEM_KEYS for i in items)
    # the queue never carries a proposed gold edition id (search results may list any record)
    assert not proposed_gold & set(json.dumps(items).split('"'))

    first, second = items[0]["draft_id"], items[1]["draft_id"]
    assert_blind(client.post("/api/label/skip", json={"draft_id": second, "labeler": "ob"}).text)
    assert_blind(client.get("/api/label/queue").text)

    # rejected submissions save nothing and reveal nothing
    bad = client.post(
        "/api/label/submit",
        json={"draft_id": first, "labeler": "ob", "expected": "abstain"},
    )
    assert bad.status_code == 422 and not labels.exists()
    assert_blind(bad.text)

    ok = client.post(
        "/api/label/submit",
        json={
            "draft_id": first,
            "labeler": "ob",
            "expected": "abstain",
            "ambiguity_reason": "underspecified",
        },
    ).json()
    draft = next(d for d in store_drafts if d["draft_id"] == first)
    assert ok["saved"]
    assert ok["proposed"]["expected"] == draft["proposed"]["expected"]
    assert ok["proposed"]["gold_edition_ids"] == draft["proposed"]["gold_edition_ids"]
    assert ok["template"] == draft["template"] and "template_note" in ok
    # after a save the queue is still blind for every case, including the saved one
    assert_blind(client.get("/api/label/queue").text)


def test_label_endpoints_absent_without_queue(make_resolver: Any, tmp_path: Path) -> None:
    settings = Settings(
        var_dir=tmp_path, catalog_db=tmp_path / "x", llm_provider="none", mock_mode="cite_first"
    )
    client = TestClient(create_app(settings, make_resolver(None)))
    assert client.get("/api/label/enabled").json() == {"enabled": False}
    assert client.get("/api/label/queue").status_code == 404


def test_unaudited_or_quarantined_probes_get_no_drafts(editions: list[Any]) -> None:
    none = draft_batch(
        editions,
        PROBES,
        split="dev",
        split_seed=20261103,
        seed=1,
        n_in_corpus=0,
        n_probes=5,
        prefix="x",
    )
    assert none == []
    q = draft_batch(
        editions,
        PROBES,
        split="dev",
        split_seed=20261103,
        seed=1,
        n_in_corpus=0,
        n_probes=5,
        prefix="x",
        probe_status={p["title"]: "quarantined" for p in PROBES},
    )
    assert q == []


def test_family_map_controls_split(editions: list[Any]) -> None:
    all_dev = {e.work_id: "fam:same" for e in editions if e.work_id}
    from bera.evalkit.splits import family_split

    target = family_split("fam:same", 20261103)
    d = draft_batch(
        editions,
        [],
        split=target,
        split_seed=20261103,
        seed=1,
        n_in_corpus=30,
        n_probes=0,
        prefix="x",
        family_of=all_dev,
    )
    assert d and {x.family for x in d} == {"fam:same"}


def test_proposal_spec_comes_from_pinned_manifest(
    tmp_path: Path, editions: list[Any], catalog: Any
) -> None:
    import hashlib

    q = make_queue(tmp_path, editions)
    assert LabelStore(q, tmp_path / "l.jsonl", catalog, False).proposal_spec == "unrecorded"
    digest = hashlib.sha256(q.read_bytes()).hexdigest()
    m = q.with_suffix(".manifest.json")
    m.write_text(json.dumps({"queue_sha256": digest, "proposal_label_spec": "v1"}))
    assert LabelStore(q, tmp_path / "l.jsonl", catalog, False).proposal_spec == "v1"
    q.write_text(q.read_text() + "\n")  # queue changed after the manifest was written
    with pytest.raises(RuntimeError):
        LabelStore(q, tmp_path / "l.jsonl", catalog, False)


def test_practice_labels_kept_but_not_counted(
    tmp_path: Path, editions: list[Any], catalog: Any
) -> None:
    from bera.evalkit.provenance import independent_human_cases, mark_practice, provenance_path
    from bera.labeling import Submission

    q = make_queue(tmp_path, editions)
    labels = tmp_path / "labels.jsonl"
    store = LabelStore(q, labels, catalog, False)
    ids = list(store.drafts)
    for i in ids[:2]:
        store.submit(
            Submission(
                draft_id=i, labeler="ob", expected="abstain", ambiguity_reason="underspecified"
            )
        )
    before = labels.read_text()
    rec = mark_practice(labels, ids[0], "test", "practice")
    assert labels.read_text() == before  # original entries are never edited
    assert rec["applies_to_label_sha256"] and provenance_path(labels).exists()
    cases = load_cases(labels)
    assert [c.case_id for c in independent_human_cases(cases, labels)] == [ids[1]]


def test_template_note_and_drafter_v2(editions: list[Any]) -> None:
    from bera.evalkit.drafts import TEMPLATES, template_applies, template_note

    no13 = next(e for e in editions if e.isbn_13).model_copy(update={"isbn_13": ()})
    ops = dict(TEMPLATES)["isbn10_hyphenated"]
    assert not template_applies(ops, no13)
    v1 = draft_batch(
        [no13],
        [],
        split="dev",
        split_seed=0,
        seed=1,
        n_in_corpus=1,
        n_probes=0,
        prefix="x",
        drafter="v1",
    )
    v2 = draft_batch(
        [no13],
        [],
        split="dev",
        split_seed=0,
        seed=1,
        n_in_corpus=1,
        n_probes=0,
        prefix="x",
        drafter="v2",
    )
    for d in v1 + v2:
        if d.template == "isbn10_hyphenated" and not d.query.isbn:
            assert "ISBN step was not applied" in (template_note(d, no13) or "")
    assert all(template_applies(dict(TEMPLATES)[d.template], no13) for d in v2)


def test_exposed_case_never_counts_as_independent(
    tmp_path: Path, editions: list[Any], make_resolver: Any
) -> None:
    from bera.evalkit.provenance import exposures_path, independent_human_cases, record_exposure

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
    ids = [i["draft_id"] for i in client.get("/api/label/queue").json()["items"]]
    # recorded while the case is still unlabeled
    rec = record_exposure(labels, ids[0], "answer_supplied_by_ai", "exposed", "test", "x")
    assert rec["label_existed_when_recorded"] is False and exposures_path(labels).exists()
    assert not labels.exists()  # recording an exposure writes no label

    body = client.get("/api/label/queue").json()
    status = {i["draft_id"]: i["status"] for i in body["items"]}
    assert status[ids[0]] == "exposed" and status[ids[1]] == "unlabeled"
    assert body["exposed"] == 1 and body["independent"] == 0
    assert "answer_supplied_by_ai" not in json.dumps(body)  # the record's details stay server-side

    for i in ids[:2]:
        client.post(
            "/api/label/submit",
            json={
                "draft_id": i,
                "labeler": "ob",
                "expected": "abstain",
                "ambiguity_reason": "underspecified",
            },
        )
    body = client.get("/api/label/queue").json()
    assert body["labeled"] == 2 and body["independent"] == 1 and body["exposed"] == 1
    kept = independent_human_cases(load_cases(labels), labels)
    assert [c.case_id for c in kept] == [ids[1]]
