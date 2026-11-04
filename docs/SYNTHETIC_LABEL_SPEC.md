# Synthetic label specification

Synthetic perturbation cases are **engineering-check data**. They are not human labels, they
are never mixed with human labels, and no quality claim rests on them. They are generated
from development families only (`scripts/make_dev_check_cases.py`), and held-out cases are
never generated, relabeled or evaluated here.

Implementation: `bera.evalkit.perturb.label(judged, source, catalog, spec)`. Every case
records its source edition, ops and seed, so its query can be re-derived exactly and its
label recomputed under any spec version.

"Judged fields" are the clean information that survived perturbation: the source's title and
author stand in for typo'd ones, and a checksum-invalid ISBN is discarded because a damaged
ISBN identifies nothing exactly.

## v1 (original; frozen)

- An edition fits if no supplied field contradicts a **known** value on it. Unknown values
  are compatible: missing metadata widens the set of editions that fit and is never treated
  as distinguishing.
- Exactly one fitting edition gives `suggest` with that edition as gold. Otherwise the case
  is `abstain`, the fitting editions are listed, and the reason is "underspecified: N
  editions fit".
- A record with **no ISBN** was treated as fitting an ISBN query (missing = unknown).

Cases: `data/eval/dev_check_v3_synthetic.jsonl` (sha256 `5d03d43a…`). Results:
`data/eval/results/dev_check_v3/`. Both are preserved unchanged.

## v2 (owner decision 2026-11-04; current default)

The rules below were decided by the owner and are not derived from model results.

1. **Unique explicit ISBN mapping.** The query ISBN is checksum-valid, exactly one catalog
   record carries it, and that record does not conflict with any other supplied field. The
   case is `suggest`, and that record is the only gold edition. No LLM is needed.
2. **Missing ISBN is unknown.** It does not establish that a record carries the queried ISBN,
   so a record without an ISBN does not fit an ISBN query. It also does not, by itself,
   invalidate the unique mapping.
3. **Multiple explicit mappings** (two or more records carry the ISBN) give `abstain`, with
   the reason "multiple explicit ISBN mappings". This holds even when another supplied field
   would separate them.
4. **A conflict between the ISBN holder and a supplied field** gives `abstain`.
5. **Independently evidenced catalog inconsistency** must go to review. No automatic detector
   beyond rules 3 and 4 is implemented; this is a known gap.
6. **Without a valid ISBN**, the v1 field-fit rules apply unchanged.
7. **No acceptable sets are inferred.** For `abstain` cases, `gold_edition_ids` lists the
   editions consistent with the query. It is **not** a set of interchangeable correct answers.
   Duplicate-record equivalence is never inferred from missing fields; an acceptable set
   needs affirmative evidence, and no synthetic case currently has one.
8. **`mul` and `und`** are kept as distinct metadata values. Neither proves equivalence with a
   specific language, nor a definite conflict with one. Synthetic queries do not currently
   carry a language. The runtime language check returns UNKNOWN for both (see
   DECISION_POLICY).

## v1 → v2 relabel of the dev engineering-check cases

`scripts/relabel_synthetic_cases.py` applies the new spec case by case. For each case it
re-derives the query from the recorded seed and refuses if the query does not reproduce
exactly. It also verifies that the stored label equals the v1 recomputation before applying
v2.

- Output: `data/eval/dev_check_v3_synthetic.labels_v2.jsonl` (sha256 `ff76179e…`).
- Every change, with its rule and catalog evidence (query ISBN, explicit mappings, mappings
  consistent with the other fields, records without an ISBN that were no longer counted):
  `data/eval/label_changes/dev_check_v3_v1_to_v2.jsonl` and `.summary.json`.

**18 of 300 cases changed:**

| transition | cases | rule |
|---|---|---|
| abstain → suggest | 14 | unique explicit ISBN mapping, no conflict; the editions removed from gold all lack an ISBN |
| suggest → abstain | 2 | multiple explicit ISBN mappings (El principito: 2 records; A Game of Thrones 9780553593716: 3 records) |
| abstain → abstain (reason only) | 2 | multiple explicit ISBN mappings (Introduction to Algorithms CD-ROM; Dirty Weekend) |

The 14 abstain → suggest cases are the same 14 on which every method had suggested. Each was
checked individually against rule 1; none was relabeled because a system agreed with it. For
example, in syn-OL35418469M-0 the Turkish A Game of Thrones ISBN maps to one record, and the
three English records lack an ISBN. All 14 met rule 1, so none stayed `abstain`.

**Labeling drafts.** Under v2, one program-drafted proposal in the first labeling batch would
change: dev-b01-009 (Jane Eyre, ISBN 0-3939-4427-1) goes from abstain to suggest
OL46077521M. The queue file was left unchanged while the owner labels. Proposals are shown
only after a blind label is entered, and human labels are unaffected. Record:
`data/eval/label_changes/dev_batch01_proposals_v1_to_v2.json`.
