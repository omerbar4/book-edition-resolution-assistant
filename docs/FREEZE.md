# Full-system freeze (evaluation milestone)

The freeze is the tagged commit after which held-out cases are generated, labeled and
evaluated once. Its contents are pinned in `data/freeze/freeze_manifest.json`
(`scripts/freeze_manifest.py write`; check with `verify`).

## What is frozen

- **Code:** every git-tracked file under `src/`, `scripts/`, `tests/` and `frontend/src/`,
  plus lock and build files.
- **Prompt:** `src/bera/llm/prompt.py`.
- **Models:** every file under `models/` (bge-small-en-v1.5, ms-marco-MiniLM-L6-v2,
  Qwen3-4B-Instruct-2507 Q4_K_M), plus the llama-server binary.
- **Retrieval settings, thresholds, budgets and route constants:** every module-level
  constant of the decision path, recorded in the manifest.
- **Policy:** `conservative-rules-v2` (v1 plus conservative initials compatibility). No
  dev-fitted confidence mapping exists: confidence is uncalibrated.
- **LLM route evidence:** `data/eval/llm_route_evidence_policy_v2.json`. **Both suggestion
  routes are closed** (agree 5/10, override 0/0; target 0.95, minimum 30); the LLM is
  advisory.
- **Corpus and catalog:** corpus v3_proposed (sha256 `cdabcf84…`), `families.json`, split
  seed 20261103, `var/catalog_v3.sqlite`.
- **Held-out generation rules:** `scripts/make_heldout_queue.py` (seed 20261110; quotas
  identifier 8, missing metadata 7, author variation 7, edition ambiguity 7, format/year
  conflict 8; 3 verified-absent probes; 2 reserves; reveal never), plus the stratified drafter.
- **Evaluation protocol:** EVALUATION_PLAN, EVAL_PROTOCOL, DECISION_POLICY,
  SYNTHETIC_LABEL_SPEC, LABELING_GUIDE, REQUIREMENTS_AUDIT and REQUIREMENTS_TRACKER.
- **Dev evidence base:** every dev label file, sidecar and queue.

## Deferred items (documented, not hidden)

1. Calibrated scorer (C1): insufficient evidence. Confidence is reported as uncalibrated
   bands.
2. Validated LLM suggestion path: implemented, both routes closed on dev evidence.
3. Damaged-ISBN fallback: deferred. A repaired ISBN still goes to review.
4. Unicode-guard scope: deferred, unchanged.
5. Catalog-inconsistency detector beyond duplicate ISBNs and field conflicts: not
   implemented.
6. About 60 abstention/out-of-corpus cases: unmet (16 dev plus 3 held-out probes).
7. Preferred 120 labels: not pursued.
8. CI never executed (no remote); Docker not re-verified at the freeze.

## Pre-tag checklist

- Disputed dev label `d02-6463d76f7e`: the owner's ruling is recorded append-only. The
  original line is preserved, and any amendment is a separate record.
- `scripts/freeze_manifest.py verify --pre-tag` passes: clean tree, all pins match, both LLM
  routes closed, no held-out data.
- Backend and frontend tests, ruff, ruff format and mypy pass.
- Held-out feasibility was checked on catalog structure only (counts; nothing written): all
  quotas fillable.

## After the tag

1. `scripts/make_heldout_queue.py --frozen-tag <tag>` (refuses unless HEAD is the tag and
   the tree is clean). Commit the queue, manifest and sealed reserves.
2. Serve on a separate port with held-out serving enabled. Proposals are never revealed.
3. After labeling: one held-out run from a worktree at the tag (see the manifest's
   `heldout_run_procedure`). Held-out labels and results are never used for tuning.
