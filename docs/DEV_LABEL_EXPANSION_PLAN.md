# Development label expansion plan (proposed 2026-11-07; awaiting owner approval)

This plan covers development labeling after batch 02. It is a proposal: batch 03 is drafted
under the rules below, and **no batch after 03 is generated until the owner approves this
plan**. The frozen corpus (v3_proposed, sha256 `cdabcf84…`) and the dev/held-out split
(seed 20261103) do not change. No held-out family is drafted, labeled, inspected or
evaluated.

## Fixed rules

1. **At most three meaningfully different queries per family**, counted across all batches.
   Within a family, every query uses a different template, every op of the template changes
   the query, and no query repeats one already seen. Queries in a family may come from
   different editions.
2. **Selection is predefined and seeded.** Quotas, pools and seeds are fixed before a batch
   is generated. Selection never uses drafted proposals, system outputs, scores or failures.
   Each manifest records its selection criteria, pool sizes and validation checks.
3. **Blindness.** Ids are opaque (`dNN-` plus 10 random hex digits) and the order is random.
   Before the whole batch is labeled, nothing about any proposal, template, template note,
   agreement or score is sent (`"reveal": "after_batch"`). Revealing makes that batch's labels
   final. No report summarizes a future batch's templates or proposed outcomes.
4. **Family grouping everywhere.** Cross-validation folds (GroupKFold) and bootstrap
   resampling keep all queries of a family together. Every metric reports both its query
   count and its family count. Families come from the frozen queue and `families.json`
   (`bera.evalkit.families`), and labels now store the draft family at save time.
5. **Human labels only.** Synthetic gold is never mixed in. Batch 01 stays practice/exposed.

## Feasibility (measured, existing six templates)

| | families | query capacity (≤3 each) |
|---|---|---|
| development families | 123 | |
| used or discussed (batches 01–02, discussed cases) | 41 | |
| unused, no applicable template | 20 | 0 |
| **pool A**: unused, never in the 300-case policy-development check | 31 | 87 |
| **pool B**: unused, used in that check (results reported separately) | 31 | 92 |

Batch 03 takes one query from each of 20 distinct pool A families (owner decision: family
diversity first; further queries per family come in later batches). That leaves about 67
(pool A, of which 11 families are untouched) + 92 (pool B) ≈ 159 queries. With batches 02 and 03 (40 queries), the ceiling is about **199
labeled queries across about 82 families**. Batch 02's answerable share was 18/20; the
strata below are designed to produce more abstentions, so the answerable count will be
lower.

**150 answerable queries is a planning target, not a reliability guarantee.** With about 3
queries per family, the effective sample is closer to the family count (about 60–80) than
the query count. Platt scaling still requires ≥150 answerable queries *and* ≥20 per
reliability bin (DECISION_POLICY). If either fails, report High/Medium/Low bands with
family-grouped intervals instead. Reaching 150 answerable needs most of pools A and B, so
pool B cases (optimistic, because those families shaped policy v1) will be a large share
and must be reported separately.

## Strata for batches 04 and later (predefined quotas)

Each batch of 20 has 4 queries per stratum. A family's queries come from different strata.

| stratum | how a query is made | status |
|---|---|---|
| identifier queries | ISBN-10 hyphenated form; one misread ISBN digit | existing templates |
| missing metadata | title + author only; barcode damaged (ISBN dropped) | existing templates |
| author variations | initials + surname; "Surname, Given" | existing templates |
| edition ambiguity | a title + author style query on a family whose catalog structure has ≥2 editions sharing title and author (chosen from catalog structure only, never from the proposal) | selection rule on existing templates |
| format / year conflicts | a supplied year shifted by 1–5 years, or a different physical format than the source | **new templates, need approval** (`year_shift`, `format_swap`) |

Order: pool A first, then pool B. Stratum quotas are filled family by family in seeded
random order. If a stratum cannot fill its quota from the pool, the shortfall is recorded
in the manifest and nothing is substituted by looking at results.

## Acceptance criteria per batch

- Generator validation all PASS: dev split by family; pool membership; ≤3 per family
  including earlier batches; distinct templates within a family; templates effective and
  reproducible from `op_seed`; no seen query; opaque unique ids; corpus hash unchanged; a
  rerun with the same seed gives the same sha256.
- Manifest pins the queue sha256, `reveal: after_batch`, proposal label spec, selection
  criteria, pool sizes and stratum quotas/shortfalls.
- The pre-save queue sends only id, split, query and status (tested). The reveal endpoint
  refuses until every case is labeled, then freezes the labels.
- Queue and manifest are committed before labeling. Labels are committed unchanged
  afterwards, separately from any analysis.

## Acceptance criteria for the expansion as a whole

- Each evaluation reports query and family counts, case-level Wilson intervals and
  family-grouped bootstrap intervals; pool A and pool B separately; per stratum with n.
- No policy, threshold or prompt change is evaluated on the labels that motivated it.
  Improvements are shown on later batches.
- Calibration is attempted only if the planning target is met. Otherwise confidence bands
  with measured precision k/n are reported. Held-out is run once, after freezing.

## Open owner decisions

- Approve this plan, including the two new templates for the format/year stratum.
- Rule on review flag `d02-6463d76f7e` (`dev_batch02_labels.review_flags.jsonl`): the human
  chose the record with a known format, while a same-title/author/year twin has no format.
  The label is unchanged and the policy is unchanged.
- Policy hypotheses from batch 02 (initials matching, damaged-ISBN fallback, unicode guard
  scope) stay unimplemented until approved, and are then evaluated on later batches.
