# Decision policy

## Current: `conservative-rules-v0` (uncalibrated)

Deterministic rules only (`src/bera/policy.py`). No threshold was fit on data, and no number
shown is a probability: the API returns `confidence_status = "uncalibrated: …"` and
`lexical_score` is a Reciprocal Rank Fusion ranking score.

**SUGGEST** only when all of the following hold:
- the query has no suspicious Unicode, and the suggested record has none either;
- *ISBN route*: a checksum-valid ISBN maps to exactly one edition and no field check
  disagrees; **or**
- *retrieval route*: exactly one candidate is consistent (title AGREE, author AGREE, zero
  DISAGREE) and it also agrees on a distinguishing field (isbn, format, year, publisher,
  language, edition).

Everything else is **REVIEW**, with reason codes. In particular:
- a duplicate ISBN mapping is never auto-resolved;
- a bad checksum yields repair *hypotheses* only (`isbn_repair_hypothesis_only`);
- free text with no structured title or author never produces a suggestion;
- missing metadata is `unknown`, never a conflict.

**Adjudication is advisory in v0.** When the policy finds an ambiguous set (duplicate ISBN,
multiple consistent candidates, or several uncontradicted candidates), a configured provider
may be asked to choose among opaque ids `c1..c5` or abstain. Even a valid, well-evidenced
choice leaves the outcome as REVIEW (`llm_advisory_only_pending_route_measurement`). The
model's `confidence` is logged and displayed but never used.

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
