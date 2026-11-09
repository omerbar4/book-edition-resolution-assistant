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
| S8 | implemented, never executed | **verified**: GitHub Actions passing on `main` (first run 42535389309 on `67f313f`: backend 232 passed / 3 skipped, frontend 11/11) | [SETUP_VERIFICATION.md](SETUP_VERIFICATION.md) |
| S9 | verified 2026-11-03 | **re-verified 2026-11-08**: no-cache build from a clean clone, compose healthy, uid 10001, read-only root filesystem, demo 6/6 | [SETUP_VERIFICATION.md](SETUP_VERIFICATION.md) |
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

## Post-evaluation changes: `main` no longer matches the evaluated snapshot

The evaluated system is tag **`bera-eval-freeze-2026-11-07-r2`** (`c32f7f0`), plus the
held-out data and result commits through `863ab15`. The tag, labels, provenance sidecars,
the family supplement, the run records and `data/eval/results/heldout40_frozen_r2/` are
unchanged. `main` now also has post-evaluation commits. Two of them change frozen files, so
**`scripts/freeze_manifest.py verify` fails on `main` by design**. It names `pyproject.toml`,
`src/bera/policy.py`, `src/bera/service.py`, two tests, and the `bera.policy`/`bera.service`
constants.

The verifier and `data/freeze/freeze_manifest.json` were **not** changed. Checked on
2026-11-08: the verifier passes at the r2 tag, in a temporary worktree using the same local
models, catalog and llama-server binary.

| commit | change | touches frozen files |
|---|---|---|
| `a2d8f26` | frontend test stability: Testing Library async timeout 5 s (`frontend/vitest.setup.ts`); 1 failure in 25 runs under load before, 0 in 40 after. **Misdiagnosed**: the flake recurred in CI on 2026-11-09; superseded by the row below | no |
| (`fix/labelview-test-flake`) | LabelView test race: tests clicked Search before LabelView's effect enabled it, so the click was dropped and a later test's render rescued the wait. Tests now wait for Search to be enabled and scope queries to their own container; async-wait budget back to 1 s, under the explicit 5 s test timeout. Test files and config only; app code unchanged | no |
| `8f9d26a` | `demo/run_demo.py` (synthetic catalog only) | no |
| `b221ce2` | README, STATUS, DEMO, SETUP_VERIFICATION, evaluation report, AI log | no |
| `936d36f` via merge `91adf72` | numpy as a core dependency (needed by `rapidfuzz.process.cdist` in ingestion); mypy ignores the optional ml imports (torch, sentence-transformers) | yes: `pyproject.toml`, `uv.lock` |
| `9eca484` | `/api/health` calibration and `confidence_status` text: uncalibrated; dev labeling and held-out evaluation complete; calibration deferred. Strings only; `POLICY_VERSION`, rules and thresholds unchanged | yes: `src/bera/policy.py`, `src/bera/service.py`, two tests |

Held-out numbers describe the r2 snapshot. No held-out inference was rerun after these
changes. Running the held-out harness on `main` is refused, both because the manifest no
longer verifies and because results are committed outside the allowed prefix.

## Known, unfixed

- **Absolute home path in two committed records:**
  - the held-out attempt-1 failure excerpt (`data/eval/heldout/heldout_run_attempts.jsonl`);
  - an earlier version of `data/eval/results/dev_batch02_human_policy_v1/report.json` in the
    history (`938348e`), replaced by repo-relative paths in `1574b41`.

  They show only a local username and project folder, no credentials. They are kept so that
  held-out provenance and the history leading to the frozen tags stay unaltered.
- Deferred design items: calibrated scorer (C1), opening the LLM route, the damaged-ISBN
  fallback, unicode-guard scope, and the catalog-inconsistency detector.
