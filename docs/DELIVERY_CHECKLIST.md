# Delivery checklist (2026-11-08)

Local only: nothing is pushed, deployed or published.

**Two states:**
- **The evaluated snapshot** is tag `bera-eval-freeze-2026-11-07-r2`, plus the held-out data
  and result commits. It is unchanged and still passes `freeze_manifest.py verify`.
- **`main`** has post-evaluation changes and no longer matches that snapshot; the verifier
  fails on it by design ([STATUS.md](STATUS.md)).

## Ready

- [x] **Evaluation:** 100 human-reviewed labels (99 strictly independent), the r2 freeze, one
      scored held-out run, and the report with denominators and family-grouped intervals
      ([EVALUATION_REPORT.md](EVALUATION_REPORT.md)).
- [x] **Provenance:** held-out independence self-reported, the AI-assisted Darkwoods amendment,
      batch 01 excluded, both run attempts recorded, the `--families` deviation documented.
- [x] **README:** policy v2; held-out headline (0/40 observed wrong, not zero risk; 6/15
      coverage; intervals); 7 configurations identical; LLM advisory with gates closed; no
      calibration claim; label provenance; a note that `main` diverges from the snapshot.
- [x] **Core-only install** (`91adf72`): numpy only, no torch. Verified in an offline clean
      clone: ruff, mypy, 232 passed / 3 skipped.
- [x] **Health and confidence text** (`9eca484`): uncalibrated; dev labeling and held-out
      evaluation complete; calibration deferred.
- [x] **Frontend:** the intermittent-test fix (`a2d8f26`); typecheck, 11/11 tests and the build
      pass in the clean clone.
- [x] **Demo:** `demo/run_demo.py` plus [DEMO.md](DEMO.md), synthetic catalog only; 6/6 in the
      clean clone.
- [x] **Rebuild without dumps:** `var/catalog_v3.sqlite` rebuilds byte-identically from the
      committed corpus; the family supplement and `analysis.json` reproduce
      ([SETUP_VERIFICATION.md](SETUP_VERIFICATION.md)).

## Release blockers / not verified

- [ ] **CI never executed:** no remote exists. Needs owner approval to create a remote and
      push.
- [ ] **Fresh online install** from empty caches: not verified (needs PyPI/npm access). The
      README's `pip install uv==0.13.7` step was substituted offline.
- [ ] **Docker:** not re-verified. Missing locally: `node:22-bookworm-slim@sha256:4b150b48…`
      and `python:3.12-slim-bookworm@sha256:e697c818…`. The build also needs registry access
      for npm, uv and PyPI. The last verified run was 2026-11-03.
- [ ] **ML and LLM paths from a fresh checkout:** need model weights (2.5 GB) and a llama.cpp
      source build; both are downloads.
- [ ] **Release identity:** decide whether a release is cut from the evaluated tag or from
      `main`. Results apply to the tag; `main` adds the post-evaluation changes listed in
      STATUS.md. No release tag exists for `main` yet.
- [ ] **No README screenshots or recording** yet (optional; capture from the synthetic demo).

## Approvals still needed (none were used)

1. Any download:
   - Docker base images, plus registry access for a Docker build;
   - model weights (`fetch_models.py --approved-by-owner`);
   - llama.cpp source;
   - the Open Library dump. The dump is needed only to regenerate the corpus itself; the
     catalog rebuilds from the committed corpus.
2. Creating a remote, pushing, running CI, tagging a release, or publishing or deploying
   anything.

## Deferred (documented, not release blockers)

The calibrated scorer (C1), opening the LLM route, the damaged-ISBN fallback, unicode-guard
scope, the catalog-inconsistency detector, the about-60 abstention-case target (42 reached)
and the 120-label goal.
