# Delivery checklist (2026-11-08)

**Published:** https://github.com/omerbar4/book-edition-resolution-assistant, release `v0.1.0`
cut from `main`.

**Two states:**
- **The evaluated snapshot** is tag `bera-eval-freeze-2026-11-07-r2`, plus the held-out data
  and result commits. It is unchanged and still passes `freeze_manifest.py verify`.
- **`main` / `v0.1.0`** add documented post-evaluation fixes ([STATUS.md](STATUS.md)). The
  verifier fails there by design, and the fixes were not re-evaluated on held-out data.

## Done

- [x] **Evaluation:** 100 human-reviewed labels (99 strictly independent), the r2 freeze, one
      scored held-out run, and the report with denominators and family-grouped intervals
      ([EVALUATION_REPORT.md](EVALUATION_REPORT.md)).
- [x] **Provenance:** held-out independence self-reported, the AI-assisted Darkwoods amendment,
      batch 01 excluded, both run attempts recorded, the `--families` deviation documented.
- [x] **Publication audit** of every blob, commit message and tag in history:
  - no credentials and no private-project or infrastructure content;
  - no large or binary artifacts (pack 1.34 MB);
  - two absolute home paths kept in provenance and history, documented in STATUS.
- [x] **README:**
  - policy v2;
  - held-out headline: 0/40 observed wrong (not zero risk), 6/15 coverage, intervals;
  - 7 configurations identical; LLM advisory with gates closed; no calibration claim;
  - label provenance, and the relation between the release and the evaluated tag.
- [x] **Setup verified** ([SETUP_VERIFICATION.md](SETUP_VERIFICATION.md)):
  - fresh online install from empty caches (core and ml);
  - offline clean clone;
  - no-cache Docker build and compose run;
  - GitHub Actions CI passing.
- [x] **Demo:** `demo/run_demo.py` plus [DEMO.md](DEMO.md), synthetic catalog only; 6/6 locally
      and against the container.
- [x] **Rebuild without dumps:** `var/catalog_v3.sqlite` rebuilds byte-identically from the
      committed corpus.

## Remaining limitations

- [ ] **ML and LLM paths from a fresh checkout** need the model weights (2.5 GB,
      `fetch_models.py`) and a llama.cpp source build; CI covers the core path only.
- [ ] **Setup coverage:** verified on macOS arm64 (local) and ubuntu-24.04 (CI) only.
      `INSTALL_ML=1` Docker images were not built.
- [ ] **Regenerating the corpus itself** (rather than the catalog) needs the Open Library dumps.
- [ ] **No README screenshots or recording** (optional).

## Deferred (documented)

The calibrated scorer (C1), opening the LLM route, the damaged-ISBN fallback, unicode-guard
scope, the catalog-inconsistency detector, the about-60 abstention-case target (42 reached)
and the 120-label goal.
