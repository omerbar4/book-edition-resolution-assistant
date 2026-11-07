"""Local labeling API (enabled with BERA_LABEL_QUEUE=<path to a dev draft file>).

Blind-first protocol: GET endpoints never reveal a draft's proposed label, nor its generator
template or template note (in batch 01 several templates always produced the same proposed
outcome, so the name hints at the answer). The proposal, template and template note are
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
from bera.evalkit.drafts import Draft, load_drafts, template_note
from bera.evalkit.label import search_page
from bera.evalkit.provenance import append_skip, exposed_case_ids, practice_case_ids, skipped

AMBIGUITY_REASONS = ("underspecified", "out_of_corpus", "contradictory", "not_a_book_edition")


class Submission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: Annotated[str, StringConstraints(max_length=64)]
    labeler: Annotated[str, StringConstraints(min_length=1, max_length=40, pattern=r"^[\w .-]+$")]
    expected: Literal["suggest", "abstain"]
    gold_edition_ids: list[Annotated[str, StringConstraints(max_length=64)]] = []
    ambiguity_reason: Literal[AMBIGUITY_REASONS] | None = None  # type: ignore[valid-type]
    notes: Annotated[str, StringConstraints(max_length=500)] | None = None


class Skip(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: Annotated[str, StringConstraints(max_length=64)]
    labeler: Annotated[str, StringConstraints(min_length=1, max_length=40, pattern=r"^[\w .-]+$")]
    reason: Annotated[str, StringConstraints(max_length=300)] | None = None


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
        self.reveal_mode = self._reveal_mode(queue)
        self.revealed_marker = labels.with_name(labels.stem + ".revealed.json")
        sources = catalog.get(
            d.source_edition_id for d in self.drafts.values() if d.source_edition_id
        )
        self.notes = {
            d.draft_id: template_note(d, sources.get(d.source_edition_id or ""))
            for d in self.drafts.values()
        }

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

    @staticmethod
    def _reveal_mode(queue: Path) -> str:
        """ "per_case" (default; the proposal is shown after each save) or "after_batch"
        (nothing about any proposal is shown until every case in the queue is labeled)."""
        manifest = queue.with_suffix(".manifest.json")
        mode = "per_case"
        if manifest.exists():
            mode = str(json.loads(manifest.read_text(encoding="utf-8")).get("reveal", mode))
        if mode not in ("per_case", "after_batch"):
            raise RuntimeError(f"unknown reveal mode {mode!r} in {manifest}")
        return mode

    def remaining(self) -> int:
        done = self.labeled()
        return sum(1 for i in self.drafts if i not in done)

    def proposal_view(self, d: Draft, case: EvalCase) -> dict[str, object]:
        p = d.proposed
        return {
            "draft_id": d.draft_id,
            "your_label": {
                "expected": case.expected,
                "gold_edition_ids": case.gold_edition_ids,
                "ambiguity_reason": case.ambiguity_reason,
            },
            "proposed": p.model_dump(),
            "proposal_label_spec": self.proposal_spec,
            "agrees_with_proposal": case.expected == p.expected
            and set(case.gold_edition_ids) == set(p.gold_edition_ids),
            "template": d.template,
            "template_note": self.notes.get(d.draft_id),
        }

    def reveal_batch(self) -> dict[str, object]:
        """All proposals at once, only when every case is labeled (after_batch mode). The
        first reveal writes a marker; after it, labels are final and resubmission is refused."""
        with self._lock:
            left = self.remaining()
            if left:
                raise HTTPException(409, f"{left} case(s) still unlabeled; proposals stay hidden")
            done = self.labeled()
            if not self.revealed_marker.exists():
                self.revealed_marker.write_text(
                    json.dumps(
                        {
                            "revealed_at": datetime.now(UTC).isoformat(timespec="seconds"),
                            "labels_sha256": hashlib.sha256(
                                self.labels_path.read_bytes()
                            ).hexdigest(),
                            "note": "proposals shown for the whole batch; labels final",
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
        items = [self.proposal_view(d, done[i]) for i, d in self.drafts.items()]
        return {
            "items": items,
            "agree": sum(1 for x in items if x["agrees_with_proposal"]),
            "total": len(items),
            "note": "agreement with drafted proposals measures the drafter, not accuracy",
        }

    def labeled(self) -> dict[str, EvalCase]:
        out: dict[str, EvalCase] = {}
        if self.labels_path.exists():
            for line in self.labels_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    c = EvalCase.model_validate(json.loads(line))
                    out[c.case_id] = c
        return out

    def status(
        self,
        draft: Draft,
        done: dict[str, EvalCase],
        practice: set[str],
        skips: dict[str, dict[str, object]],
        exposed: frozenset[str] | set[str] = frozenset(),
    ) -> str:
        if draft.draft_id in practice:
            return "practice"
        if draft.draft_id in exposed:
            return "exposed"  # labelable, but never an independent label
        if draft.draft_id in done:
            return "labeled"
        if draft.draft_id in skips:
            return "skipped"
        return "unlabeled"

    def skip(self, s: Skip) -> dict[str, object]:
        if s.draft_id not in self.drafts:
            raise HTTPException(404, "unknown draft")
        with self._lock:
            append_skip(self.labels_path, s.draft_id, s.labeler, s.reason)
        return {"skipped": True}  # never reveals the proposal

    def submit(self, s: Submission) -> dict[str, object]:
        d = self.drafts.get(s.draft_id)
        if d is None:
            raise HTTPException(404, "unknown draft")
        if self.reveal_mode == "after_batch" and self.revealed_marker.exists():
            raise HTTPException(409, "batch proposals were revealed; labels are final")
        if s.expected == "suggest" and not s.gold_edition_ids:
            raise HTTPException(422, "choose at least one gold edition, or abstain")
        if s.expected == "abstain" and not s.ambiguity_reason:
            raise HTTPException(422, "abstain requires an ambiguity reason")
        missing = set(s.gold_edition_ids) - set(self.catalog.get(s.gold_edition_ids))
        if missing:
            raise HTTPException(422, f"unknown edition ids: {sorted(missing)}")
        # The corpus family comes from the frozen draft (families.json at drafting time),
        # never from the chosen edition's work id. Whether the chosen editions map to that
        # family is checked at evaluation load time (bera.evalkit.families), which rejects
        # conflicts instead of silently regrouping; the human's choice is saved as given.
        family = d.family
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
        if self.reveal_mode == "after_batch":
            # nothing about the proposal (not even agreement) until the batch is complete
            return {"saved": True, "reveal": "after_batch", "remaining": self.remaining()}
        view = self.proposal_view(d, case)
        return {
            "saved": True,
            "proposed": view["proposed"],
            "proposal_label_spec": view["proposal_label_spec"],
            "agrees_with_proposal": view["agrees_with_proposal"],
            "template": view["template"],
            "template_note": view["template_note"],
        }


def router(store: LabelStore) -> APIRouter:
    r = APIRouter(prefix="/api/label")

    @r.get("/queue")
    def queue() -> dict[str, object]:
        done = store.labeled()
        practice = practice_case_ids(store.labels_path)
        skips = skipped(store.labels_path)
        exposed = exposed_case_ids(store.labels_path)
        items = [
            {
                "draft_id": d.draft_id,
                "split": d.split,
                "query": d.query.model_dump(exclude_none=True),
                # no proposal, template or template note before a label is saved
                "labeled": d.draft_id in done,
                "status": store.status(d, done, practice, skips, exposed),
            }
            for d in store.drafts.values()
        ]
        independent = [
            i for i in done if i not in practice and i not in exposed and i in store.drafts
        ]
        return {
            "items": items,
            "reasons": list(AMBIGUITY_REASONS),
            "labeled": len(done),
            "independent": len(independent),
            "practice": len(practice & set(store.drafts)),
            # exposed before labeling (practice cases are counted once, as practice)
            "exposed": len((exposed - practice) & set(store.drafts)),
            "skipped": sum(1 for i in items if i["status"] == "skipped"),
            "total": len(items),
            "proposal_label_spec": store.proposal_spec,
            "reveal_mode": store.reveal_mode,
            "revealed": store.revealed_marker.exists(),
        }

    @r.get("/search")
    def do_search(
        title: Annotated[str, StringConstraints(min_length=2, max_length=200)],
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, object]:
        if not 0 <= offset <= 100_000 or not 1 <= limit <= 200:
            raise HTTPException(422, "offset/limit out of range")
        return search_page(store.catalog, title, offset, limit)

    @r.post("/skip")
    def skip(s: Skip) -> dict[str, object]:
        return store.skip(s)

    @r.get("/reveal")
    def reveal() -> dict[str, object]:
        if store.reveal_mode != "after_batch":
            raise HTTPException(404, "this queue reveals per case after each save")
        return store.reveal_batch()

    @r.post("/submit")
    def submit(s: Submission) -> dict[str, object]:
        return store.submit(s)

    return r
