# Delivery checklist (2026-11-08)

Local only: nothing is pushed, deployed or published. The evaluated state is tag
`bera-eval-freeze-2026-11-07-r2` plus the held-out data and result commits; it is unchanged.

## Ready

- [x] **Evaluation:** 100 human-reviewed labels (99 strictly independent), the r2 freeze, one
      scored held-out run, and the report with denominators and family-grouped intervals
      ([EVALUATION_REPORT.md](EVALUATION_REPORT.md)).
- [x] **Provenance:** held-out independence self-reported, the AI-assisted Darkwoods amendment,
      batch 01 excluded, both run attempts recorded, the `--families` deviation documented.
- [x] **README:** policy v2; held-out headline (0/40 observed wrong, 6/15 coverage, intervals,
      not zero risk); 7 configurations identical; LLM advisory with gates closed; no
      calibration claim; label provenance.
- [x] **Status:** [STATUS.md](STATUS.md) records the changes since the frozen
      tracker/audit snapshot, which stays unchanged.
- [x] **AI assistance log** updated through 2026-11-08.
- [x] **Demo:** `demo/run_demo.py` plus [DEMO.md](DEMO.md). It uses only the synthetic
      catalog: 6/6 expected outcomes and the UI path checked in the browser.
- [x] **Offline clean-clone setup** verified with the ml group: ruff, mypy, 232 tests
      (3 skipped, need weights), frontend 11/11, build, serve
      ([SETUP_VERIFICATION.md](SETUP_VERIFICATION.md)).
- [x] **Intermittent frontend test** fixed in a separate post-evaluation commit (`a2d8f26`):
      1 failure in 25 runs under load before, 0 in 40 after; frozen `frontend/src` untouched.
- [x] **Reproducibility checks from committed files:** `freeze_manifest.py verify`,
      `build_family_supplement.py --check`, and `analyze_heldout_eval.py` byte-identical.

## Not ready / needs a decision

- [ ] **Core-only install on `main`:** 9 tests and mypy fail without numpy. The fix is on the
      unmerged local branch `post-eval/core-install-deps` (`936d36f`), verified in a
      core-only clean clone. Merging it changes the pinned `pyproject.toml`/`uv.lock`, so
      `freeze_manifest.py verify` would fail on `main` afterwards; the tag still preserves the
      evaluated state. **Owner decision: merge or keep separate.**
- [ ] **CI** (`.github/workflows/ci.yml`) has never run (no remote), and it would fail on
      `main` until the branch above is merged.
- [ ] **Fresh online install** from empty caches: not verified (needs PyPI/npm access).
- [ ] **Docker:** not re-verified. Missing locally: `node:22-bookworm-slim@sha256:4b150b48…`
      and `python:3.12-slim-bookworm@sha256:e697c818…`. The build also needs registry access
      for npm, uv and PyPI. The last verified run was 2026-11-03.
- [ ] **Model weights, llama.cpp and the Open Library catalog** can't be reproduced from git;
      each needs a download.
- [ ] **`/api/health` text:** calibration still reads "pending: needs human-labeled dev set"
      (`src/bera/service.py:95`, frozen code). Optional post-evaluation fix.
- [ ] **No README screenshots or recording** yet; capture from the synthetic demo if wanted.

## Approvals still needed (none were used)

1. Merging `post-eval/core-install-deps` into `main`, and optionally the one-line health-text
   fix in frozen code.
2. Any download:
   - Docker base images, plus registry access for a Docker build;
   - model weights (`fetch_models.py --approved-by-owner`);
   - llama.cpp source;
   - the Open Library dump.
3. Creating a remote, pushing, or running CI; publishing or deploying anything.

## Deferred (documented, not delivery blockers)

The calibrated scorer (C1), opening the LLM route, the damaged-ISBN fallback, unicode-guard
scope, the catalog-inconsistency detector, the about-60 abstention-case target (42 reached)
and the 120-label goal.
