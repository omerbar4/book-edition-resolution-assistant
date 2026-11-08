# Project status after the held-out evaluation (2026-11-08)

[REQUIREMENTS_TRACKER.md](REQUIREMENTS_TRACKER.md) and
[REQUIREMENTS_AUDIT.md](REQUIREMENTS_AUDIT.md) are **pinned by the r2 freeze manifest**. They
are kept unchanged as the snapshot the evaluation was frozen against. This page records what
changed since then. Where the two disagree, this page is current.

## Requirement status changes since the frozen snapshot

| # | Frozen snapshot | Now | Evidence |
|---|---|---|---|
| F6 | `conservative-rules-v1` named in the evidence column | **`conservative-rules-v2`** is the frozen and evaluated policy (v1 + conservative initials) | `src/bera/policy.py` `POLICY_VERSION`; [FREEZE.md](FREEZE.md) |
| C3 | agree 4/10, override 0/2 (`llm_route_evidence.json`) | frozen evidence is `llm_route_evidence_policy_v2_amended.json`: agree 4/10, override 0/0; **both routes closed** | freeze manifest `route_evidence` |
| D4 | in progress (60/100) | **met: 100** human-reviewed labels (60 dev + 40 held-out); 99 strictly independent final labels (see below); preferred 120 not pursued | [EVALUATION_REPORT.md](EVALUATION_REPORT.md) §1 |
| D6 | partially met | **still partially met**: 42 human review labels (17 dev + 25 held-out), 15 of them out of corpus, against about 60 | report §2 |
| E1 | verified on dev | **verified on held-out**: 7 configurations, 40 queries; identical final decisions | `data/eval/results/heldout40_frozen_r2/` |
| E3 | pending (freeze) | **verified**: tag `bera-eval-freeze-2026-11-07-r2`; one scored held-out run; one documented deviation; nothing tuned on held-out | report §1, [RUN_PROCEDURE_DEVIATION.md](../data/eval/heldout/RUN_PROCEDURE_DEVIATION.md) |
| C1 | deferred | **still deferred**: 15 held-out answerable cases add no fitting data (held-out is never used for fitting) | |
| S8 | implemented, never executed | unchanged. On `main`, a core-only install fails 9 tests and mypy; fixed on branch `post-eval/core-install-deps` | [SETUP_VERIFICATION.md](SETUP_VERIFICATION.md) |
| S9 | verified 2026-11-03 | **not re-verified**: the pinned base images are not cached locally | [SETUP_VERIFICATION.md](SETUP_VERIFICATION.md) |
| O2 | implemented | updated through the held-out phase | [AI_ASSISTANCE.md](AI_ASSISTANCE.md) |

## Labels: human reviewed vs strictly independent

- **100 counted cases, all human reviewed:** batch 02 (20) + dev final (40) + held-out (40).
- **99 strictly independent final labels:**
  - All 100 original label lines were saved by the owner and attested as independent
    (self-reported).
  - One dev case, `d02-6463d76f7e` ("Darkwoods"), was flagged because the human's label
    disagreed with the rules.
  - The owner then **amended** that label to human review (underspecified), after an
    **AI-assisted** review: Claude showed the query and the uncontradicted catalog records,
    without scores or recommendations.
  - The original line is preserved, and the amendment is a separate append-only record
    (`dev_batch02_labels.amendments.jsonl`). That one final label is therefore not strictly
    independent.
- **Held-out:** 40/40 labeled with reveal `never`. The owner self-reports no AI assistance
  (`heldout_labels.provenance.jsonl`, attestation `self_reported`).
- **Not counted:** batch 01, with 6 AI-assisted practice labels and 14 drafts exposed before
  labeling.
- **Dev is not independent of the system:** dev labels were used to develop policy v2, so dev
  metrics are development evidence. Only held-out is a test.

## Post-evaluation changes (separate commits)

- **On `main`:** these don't touch frozen files, and `freeze_manifest.py verify` passes.
  - Frontend test stability: a Testing Library async timeout of 5 s in the new
    `frontend/vitest.setup.ts`. The test failed 1 in 25 runs under CPU load before the fix and
    0 in 40 after.
  - `demo/run_demo.py`, plus docs: README, this page, DEMO, SETUP_VERIFICATION, the
    evaluation report and the AI assistance log.
- **On local branch `post-eval/core-install-deps`, not merged:** numpy becomes a core
  dependency, and mypy ignores the optional ml-group imports. This changes the pinned
  `pyproject.toml`/`uv.lock`, so merging it means `freeze_manifest.py verify` will fail on
  `main`. The tag still preserves the evaluated state.

## Known, unfixed (frozen code)

- `/api/health` still reports calibration as "pending: needs human-labeled dev set + grouped
  out-of-fold fit". The labels now exist; calibration is deferred for insufficient evidence,
  not missing labels. Fixing it is a one-line change in `src/bera/service.py:95` (frozen).
- Deferred design items: calibrated scorer (C1), opening the LLM route, the damaged-ISBN
  fallback, unicode-guard scope, and the catalog-inconsistency detector.
