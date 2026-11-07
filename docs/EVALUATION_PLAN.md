# Fixed evaluation plan: 100 human-labeled cases (approved 2026-11-07)

This plan replaces batch-by-batch approval. It completes the **evaluation milestone**, not
the whole project (see "After the evaluation milestone").

## Allocation

The frozen corpus split (seed 20261103) is **123 development / 100 held-out families**,
about 55/45. It does not change. Separately, the **chosen evaluation allocation** of the 100
human-labeled cases is **60 dev / 40 held-out**.

| | eligible now | to label | source |
|---|---|---|---|
| dev | 20 (batch 02) | 40 | one resumable queue `data/eval/drafts/dev_final.jsonl` |
| held-out | 0 | 40 | one separate queue, drafted only after the full system is frozen |
| **total** | **20** | **80** | **100** |

Batch 01 contributes no eligible labels (practice/exposed). The flagged batch 02 case
(`d02-6463d76f7e`, open owner review) counts unless the owner rules otherwise.

## The 100-label minimum is a minimum

A shortfall does not satisfy it. Skipped or disputed cases are preserved and reported
separately, and no answer is ever forced. If a case is excluded (for example, exposure
before labeling), a sealed reserve replaces it, in fixed order. Reserves never replace a
case for being hard, skipped or disputed. If the minimum cannot be met, the milestone stays
open and the gap is reported.

## Dev queue (40 cases, one queue, resumable)

- **Contents:** the 20 batch 03 drafts with their lines byte-identical, plus 20 new drafts
  (drafter v5).
- **Families:** one query per family across the whole queue, so 40 distinct families. The 20
  new drafts use all 11 untouched pool A families, then 9 pool B families chosen in seeded
  order. Pool B families were used in the synthetic policy-development check and are
  reported separately.
- **Strata for the new 20 (4 each, predefined):**

  | stratum | templates |
  |---|---|
  | identifier queries | ISBN-10 hyphenated; one misread ISBN digit |
  | missing metadata | title + author only; ISBN missing with title noise |
  | author variations | initials + surname; "Surname, Given" with ISBN missing |
  | edition ambiguity | title + author or initials, on a family with ≥2 editions sharing normalized title and first author (catalog structure only) |
  | format/year conflicts | `year_shift` (±3–5 years, never inside the runtime ±2 near band); `format_swap` (another known format, seeded) |

  Batch 03's 20 drafts predate the strata (existing templates in rotation). They are kept
  exactly and not re-labeled with a stratum.
- **Feasibility was checked before generating:** all quotas met, all 11 pool A families
  placed, 2 reserves, 22 distinct families. Infeasible quotas would have stopped generation;
  nothing was relaxed.
- **Reserves:** 2, in the sealed file `dev_final.reserves.jsonl` (hash in the manifest),
  distinct pool B families, not served.
- **Blindness:** opaque ids, random order, `reveal: after_batch`. Nothing about any proposal,
  template, stratum, agreement or score is sent until all 40 are labeled. The reveal makes
  the labels final. Labels go to `data/eval/labels/dev_final_labels.jsonl` with their own
  sidecars.
- **Proposal semantics (label spec v3 for the new drafts):** a changed year or format is a
  claim, judged as written; the source edition is never assumed to be the answer. The single
  fitting record is the proposal, even when it is not the source. Records that fit only
  because a field is unknown make it underspecified. **No fitting record is catalog
  absence**, which is distinct from **conflicting supplied evidence** (for example an ISBN
  whose record contradicts a supplied field). Absence never becomes "contradictory" by
  default. v3 equals v2 on every existing template (verified on all 340 existing cases), so
  batch 03's recorded v2 proposals remain valid.
- **Selection never uses** drafted proposals, system outputs, scores or failures.

## Freeze before held-out labeling

After dev labeling and the dev analysis, the **full system** is frozen as a tagged commit
before any held-out case is drafted. That covers code, prompts, models (pinned files),
thresholds, retrieval settings, any dev-fitted confidence mapping, the generation rules for
the held-out queue, and this evaluation protocol. Owner decisions pending before the freeze:
the review flag; the batch 02 policy hypotheses (initials matching, damaged-ISBN fallback,
unicode-guard scope); the validated LLM suggestion path (see below).

## Held-out queue (40 cases, after the freeze)

- **Contents:** 37 in-corpus queries from 37 distinct held-out families using the same
  strata, plus the 3 unused verified-absent held-out probes as out-of-corpus cases, plus 2
  sealed reserves. The generator is frozen with the system.
- **Separation:** separate directory (`data/eval/heldout/`), separate server, held-out serving
  explicitly enabled. No proposals are ever revealed for held-out cases.
- **Results:** one harness run at the frozen tag (enforced). Held-out labels and results are
  never used for tuning, and nothing is changed and re-run against them.

## Stopping criteria

- **Dev labeling stops** when 40 eligible labels exist, or when the reserves are exhausted
  (the milestone then stays open, with the gap reported).
- **Held-out labeling** follows the same rule.
- **Never a stopping or selection reason:** a metric value, agreement with proposals, or an
  answerable-count target.
- **The evaluation milestone is complete** when there are 100 eligible labels (60 dev,
  40 held-out), the dev analysis is done, the system is frozen, and the single held-out run is
  reported with skipped and disputed cases listed separately.

## Confidence and calibration

150 answerable cases is a planning heuristic, not a universal requirement. The dev set will
give roughly 40–50 answerable cases. Unless the evidence supports more, confidence is
reported as **uncalibrated** High/Medium/Low bands, each with measured k/n, a case-level
Wilson interval and a family-grouped bootstrap interval, with query and family counts. If
calibration lacks sufficient evidence, the report says so.

## Known limitations

- About 60 abstention/out-of-corpus cases (LABELING_GUIDE target) will not be reached. Dev
  has no unused probes and held-out has 3. This is reported as unmet.
- Queries are program-drafted perturbations of catalog records, so external validity is
  limited. There is one labeler, so no agreement measure.

## After the evaluation milestone (before the final project freeze)

- **Validated LLM suggestion path:** currently the LLM is advisory and cannot raise
  coverage. Implement and evaluate the route rule (DECISION_POLICY §7) on dev data, or
  document it as deferred, with the evidence count that blocked it.
- **Requirements audit:** re-check every item in REQUIREMENTS_TRACKER against the code and
  evidence, and explicitly document any deferred requirement with its reason.
