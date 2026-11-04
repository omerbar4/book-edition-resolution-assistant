"""Local labeling API (enabled with BERA_LABEL_QUEUE=<path to a dev draft file>).

Blind-first protocol: GET endpoints never reveal a draft's proposed label. The proposal is
returned only after the human submits their own decision, together with agreement.
Labels are appended to a labels file (latest submission per draft wins when loaded). The
queue refuses held-out drafts unless BERA_LABEL_ALLOW_HELDOUT=1, so held-out cases stay
separate from development labeling.
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, StringConstraints

from bera.catalog import Catalog
from bera.evalkit.cases import EvalCase
from bera.evalkit.drafts import load_drafts
from bera.evalkit.label import search

AMBIGUITY_REASONS = ("underspecified", "out_of_corpus", "contradictory", "not_a_book_edition")


class Submission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: Annotated[str, StringConstraints(max_length=64)]
    labeler: Annotated[str, StringConstraints(min_length=1, max_length=40, pattern=r"^[\w .-]+$")]
    expected: Literal["suggest", "abstain"]
    gold_edition_ids: list[Annotated[str, StringConstraints(max_length=64)]] = []
    ambiguity_reason: Literal[AMBIGUITY_REASONS] | None = None  # type: ignore[valid-type]
    notes: Annotated[str, StringConstraints(max_length=500)] | None = None


class LabelStore:
    def __init__(self, queue: Path, labels: Path, catalog: Catalog, allow_heldout: bool) -> None:
        self.drafts = {d.draft_id: d for d in load_drafts(queue)}
        bad = [d.draft_id for d in self.drafts.values() if d.split != "dev"]
        if bad and not allow_heldout:
            raise RuntimeError(f"queue contains held-out drafts {bad[:3]}; refusing to serve")
        self.labels_path = labels
        self.catalog = catalog
        self._lock = threading.Lock()
        self.proposal_spec = self._proposal_spec(queue)

    @staticmethod
    def _proposal_spec(queue: Path) -> str:
        """Label-spec version of the recorded proposals, from `<queue>.manifest.json` if
        present. The manifest pins the queue's sha256, so a changed queue is refused rather
        than silently attributed to the wrong version."""
        manifest = queue.with_suffix(".manifest.json")
        if not manifest.exists():
            return "unrecorded"
        m = json.loads(manifest.read_text(encoding="utf-8"))
        digest = hashlib.sha256(queue.read_bytes()).hexdigest()
        if m.get("queue_sha256") != digest:
            raise RuntimeError(f"{queue} does not match {manifest} (sha256); refusing to serve")
        return str(m.get("proposal_label_spec") or "unrecorded")

    def labeled(self) -> dict[str, EvalCase]:
        out: dict[str, EvalCase] = {}
        if self.labels_path.exists():
            for line in self.labels_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    c = EvalCase.model_validate(json.loads(line))
                    out[c.case_id] = c
        return out

    def submit(self, s: Submission) -> dict[str, object]:
        d = self.drafts.get(s.draft_id)
        if d is None:
            raise HTTPException(404, "unknown draft")
        if s.expected == "suggest" and not s.gold_edition_ids:
            raise HTTPException(422, "choose at least one gold edition, or abstain")
        if s.expected == "abstain" and not s.ambiguity_reason:
            raise HTTPException(422, "abstain requires an ambiguity reason")
        missing = set(s.gold_edition_ids) - set(self.catalog.get(s.gold_edition_ids))
        if missing:
            raise HTTPException(422, f"unknown edition ids: {sorted(missing)}")
        family = d.family
        if s.gold_edition_ids:
            first = self.catalog.get(s.gold_edition_ids[:1])
            family = next(iter(first.values())).work_id or family
        case = EvalCase(
            case_id=d.draft_id,
            query=d.query,
            expected=s.expected,
            gold_edition_ids=sorted(s.gold_edition_ids),
            ambiguity_reason=s.ambiguity_reason,
            family=family,
            origin="ai_drafted_human_labeled",
            split=d.split,
            labeler=s.labeler,
            labeled_at=datetime.now(UTC).isoformat(timespec="seconds"),
            notes=s.notes,
        )
        with self._lock:
            self.labels_path.parent.mkdir(parents=True, exist_ok=True)
            with self.labels_path.open("a", encoding="utf-8") as fh:
                fh.write(case.model_dump_json(exclude_none=True) + "\n")
        p = d.proposed
        agree = s.expected == p.expected and set(s.gold_edition_ids) == set(p.gold_edition_ids)
        return {
            "saved": True,
            "proposed": p.model_dump(),
            "proposal_label_spec": self.proposal_spec,
            "agrees_with_proposal": agree,
        }


def router(store: LabelStore) -> APIRouter:
    r = APIRouter(prefix="/api/label")

    @r.get("/queue")
    def queue() -> dict[str, object]:
        done = store.labeled()
        items = [
            {
                "draft_id": d.draft_id,
                "split": d.split,
                "query": d.query.model_dump(exclude_none=True),
                "template": d.template,
                "labeled": d.draft_id in done,
            }
            for d in store.drafts.values()
        ]
        return {
            "items": items,
            "reasons": list(AMBIGUITY_REASONS),
            "labeled": len(done),
            "total": len(items),
            "proposal_label_spec": store.proposal_spec,
        }

    @r.get("/search")
    def do_search(
        title: Annotated[str, StringConstraints(min_length=2, max_length=200)],
    ) -> list[dict[str, object]]:
        return search(store.catalog, title, limit=60)

    @r.post("/submit")
    def submit(s: Submission) -> dict[str, object]:
        return store.submit(s)

    return r
