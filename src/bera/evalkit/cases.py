"""Evaluation case schema.

`expected` is the correct BEHAVIOR:
- "suggest": the query identifies one edition; `gold_edition_ids` holds it (or a set of true
  duplicates, any of which is correct).
- "abstain": correct behavior is human review. Either the input is genuinely unresolvable
  (several editions fit everything provided; `gold_edition_ids` lists them, for retrieval
  diagnostics), or the book is out of corpus (`gold_edition_ids` is empty).

`origin` keeps provenance honest. Only "human" and "ai_drafted_human_labeled" rows count
toward the human-labeled requirement, and only after a human set `labeler`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bera.models import Query

Origin = Literal["human", "ai_drafted_human_labeled", "synthetic_perturbation"]


class Perturbation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ops: list[str]
    seed: int
    source_edition_id: str


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    query: Query
    expected: Literal["suggest", "abstain"]
    gold_edition_ids: list[str] = Field(default_factory=list)
    ambiguity_reason: str | None = None
    family: str  # grouping key for splits (work family); never split across dev/held-out
    origin: Origin
    split: Literal["dev", "heldout"] | None = None
    perturbation: Perturbation | None = None
    labeler: str | None = None
    labeled_at: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> EvalCase:
        if self.expected == "suggest" and not self.gold_edition_ids:
            raise ValueError("expected=suggest requires gold_edition_ids")
        if self.expected == "abstain" and not self.ambiguity_reason:
            raise ValueError("expected=abstain requires ambiguity_reason")
        if self.origin != "synthetic_perturbation" and not self.labeler:
            raise ValueError("human-origin cases require a labeler")
        if self.origin == "synthetic_perturbation" and self.perturbation is None:
            raise ValueError("synthetic cases require perturbation provenance")
        return self

    @property
    def human_labeled(self) -> bool:
        return self.origin in ("human", "ai_drafted_human_labeled") and bool(self.labeler)


def load_cases(path: Path) -> list[EvalCase]:
    with path.open(encoding="utf-8") as fh:
        return [EvalCase.model_validate(json.loads(line)) for line in fh if line.strip()]


def save_cases(path: Path, cases: list[EvalCase]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for c in sorted(cases, key=lambda c: c.case_id):
            fh.write(c.model_dump_json(exclude_none=True) + "\n")
