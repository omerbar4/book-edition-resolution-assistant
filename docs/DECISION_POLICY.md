# Decision policy

## Current: `conservative-rules-v1` (uncalibrated)

Deterministic rules only (`src/bera/policy.py`). No threshold was fit on data, and no number
shown is a probability: the API returns `confidence_status = "uncalibrated: …"` and
`lexical_score` is a Reciprocal Rank Fusion ranking score.

**SUGGEST** only when all of the following hold:
- the query has no suspicious Unicode, and the suggested record has none either;
- *ISBN route*: a checksum-valid ISBN maps to exactly one edition through an explicit catalog
  mapping, and no field check disagrees. A record whose ISBN is missing is unknown; by
  itself it does not invalidate the mapping. **Or**
- *retrieval route*: all three of:
  - exactly one candidate is consistent (title AGREE, author AGREE, zero DISAGREE);
  - it agrees on a distinguishing field (isbn, format, year, publisher, language, edition);
  - **no other edition is compatible** with the query (title AGREE, author not DISAGREE,
    zero DISAGREE). Compatibility is checked against the retrieved candidates
    (`undistinguished_alternative_unknown_fields`), and then deterministically against a
    catalog-wide pool of every edition whose title contains the suggested title as a phrase,
    plus every edition of the same work (`catalog_scan_found_undistinguished_alternative`).
    If the pool cannot be enumerated completely (over 1,000 editions), the outcome is REVIEW
    (`catalog_scan_incomplete`).

Everything else is **REVIEW**, with reason codes. In particular:
- a duplicate ISBN mapping is never auto-resolved;
- a bad checksum yields repair *hypotheses* only (`isbn_repair_hypothesis_only`);
- free text with no structured title or author never produces a suggestion;
- missing metadata is `unknown`, never a conflict, and **never distinguishing**: an
  alternative whose author, year or format is merely missing blocks a suggestion;
- language codes `mul` and `und` are kept as distinct values: a query language checked
  against a record that lists only them, or a specific language plus `mul`/`und`, is
  UNKNOWN, neither AGREE nor DISAGREE.

**Changes from v0 (2026-11-04, development fixes; not tuned on results).**
1. v0 required author AGREE for consistency and ignored alternatives whose author was
   unknown, so it suggested even though an undistinguished alternative existed.
2. v0 inferred uniqueness from the retrieved list alone, so a compatible edition that
   retrieval missed went unnoticed.
3. v0 treated `mul`/`und` as a definite language conflict.

Regression tests: `tests/unit/test_policy_v1.py`, which fails on v0. These fixes came from a
synthetic development engineering check. Human-labeled dev cases are still needed to judge
whether they help or hurt.

**Not implemented:** a detector for "independently evidenced catalog inconsistency" beyond
duplicate ISBN mappings and field conflicts.

**Validated LLM suggestion path: implemented, gated, currently CLOSED (2026-11-07).** When
the policy finds an ambiguous set (duplicate ISBN, multiple consistent candidates, compatible
alternatives, or several uncontradicted candidates), a configured provider may be asked to
choose among opaque ids `c1..c5` or abstain. The model's `confidence` is logged and displayed
but never used. A completed choice belongs to a **route**: `agree` (the choice is the
top-ranked candidate) or `override` (another candidate).

- **Gate** (`bera.llm.routes`). A route may turn REVIEW into SUGGEST only if a frozen evidence
  file, measured on **development human labels**, shows at least **30** completed choices on
  that route and a Wilson 95% lower bound on precision of at least **0.95**. Precision counts
  every completed choice: a choice on a case the human sent to review is wrong. Both constants
  were fixed before measurement. The decision is recomputed from the counts whenever the file
  is loaded; a stored flag is never trusted. Without an evidence file, the gate is closed.
- **Hard rules stay REVIEW even on an open route.** The LLM can only resolve plain ambiguity
  (multiple consistent candidates, undistinguished or catalog-scan alternatives) in favour of
  a compatible candidate. Duplicate ISBN mappings, ISBN repair hypotheses, field conflicts,
  suspicious unicode and an incomplete catalog scan always stay REVIEW. An open-route
  suggestion carries the reason `llm_validated_route`.
- **Measured on 60 dev human labels** (`data/eval/llm_route_evidence.json`, from
  `scripts/measure_llm_routes.py`):
  - agree route: 10 choices, 4 correct (Wilson 0.168–0.687);
  - override route: 2 choices, 0 correct.

  Both routes are **closed**, on both case count and precision; 6 of the 10 agree-route
  choices picked an edition for a case the human sent to review. Method 6 therefore still
  cannot raise final coverage, but now because of measured evidence, not because the path
  is missing. With target 0.95, the Wilson lower bound needs roughly 73 consecutive correct
  choices to open a route, so this path is unlikely to open at this project's data scale.
  That limitation is reported, not worked around.

Field-check thresholds (`src/bera/features.py`): title AGREE ≥ 90 / DISAGREE < 60
(rapidfuzz), author 85/60, publisher 85/60, year: equal = AGREE, 1–2 years apart = unknown
(reprints), > 2 = DISAGREE. These are engineering defaults that will be revisited using
development data only.

## Planned: calibrated policy (pending human-labeled dev data)

1. **Scorer.** Logistic regression over per-candidate deterministic features plus retrieval and
   reranker scores. Its output is treated as a **score**, not a probability.
2. **Grouped out-of-fold predictions.** GroupKFold (K=5) grouped by work family on the
   **development split only**. Every dev query gets a score from a model that never saw its
   family. Calibration assessment, any calibration map, and threshold selection all use these
   out-of-fold predictions.
3. **Query-level confidence.** Fit on out-of-fold features: top-1 score, top-1/top-2 margin,
   conflict count, and route. Target: whether the top-1 is correct.
4. **Calibration or confidence bands.** Platt scaling only if there are ≥ 150 answerable dev
   queries and every reliability bin has ≥ 20; no isotonic regression at this size. Otherwise
   report uncalibrated scores with **High/Medium/Low bands**, each with its measured precision
   `k/n` and a Wilson 95% interval.
5. **Thresholds.** Choose the largest coverage whose *upper* Wilson bound on error among
   suggestions is ≤ the target. If none qualifies, the frozen policy is "always review".
   Out-of-fold numbers are optimistic because they were used for selection; only the frozen
   held-out run is the estimate.
6. **Freeze.** Refit on all dev with thresholds unchanged, tag the commit, then run held-out
   once.
7. **When the LLM picks a different candidate than the scorer.** Confidence is a property of
   the *route* (`agree` / `override` / `abstain`), measured separately on dev out-of-fold
   cases, never taken from the model. Overrides default to REVIEW, showing both candidates. An
   override may produce a suggestion only if dev has ≥ 30 override cases and their Wilson
   lower bound on precision meets the target.
