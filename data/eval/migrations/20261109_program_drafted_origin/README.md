# Label-data migration 2026-11-09: `program_drafted_human_labeled`

**What changed**
- Label lines (`origin`): `ai_drafted_human_labeled` became `program_drafted_human_labeled`.
  The queries were drafted by the deterministic template drafters (`drafted_by` in each queue
  line), and the owner chose every label in the labeling UI.
- Provenance sidecars:
  - `recorded_by` is split into `decided_by`, the person who made the decision (always the
    owner), and `recorded_via`, how the line was written to the file.
  - The status `practice_ai_assisted` became `practice_excluded`.
  - The exposure kind `answer_supplied_by_ai` became `answer_supplied_externally`.
  - A few reasons were reworded to describe the event: practice label made with outside help,
    answer exposed before labeling, amended after a catalog-record review.
- Sidecar pins (`applies_to_label_sha256`) now point to the migrated label lines.

**What did not change**
- Every label decision: expected, gold editions, ambiguity reason, labeler, timestamps, query,
  family and split.
- Every practice or exposure exclusion and the Darkwoods amendment.
- Every independence status, including the held-out self-attestation.

**Frozen results are not rewritten.** The r2 freeze manifest, the frozen reports and
analyses, the route evidence, the reveal marker and the evaluation report keep their
pre-migration hashes, because those are the files that were evaluated.
`migration.json` maps every old file and line hash to its new one and lists those historical
references.

**Files**
- `migrate.py` is deterministic. It reads the inputs from git at the base commit `c15876d`
  and writes the migrated files and `migration.json`.
- `verify.py` checks four things and writes `verification.json`:
  - every migrated file has the new hash recorded in `migration.json`;
  - in each label line, only the `origin` value changed;
  - the evaluation inputs before and after the migration are identical, including the
    excluded cases and the amendments;
  - the headline metrics recomputed from the frozen per-case outputs with the migrated labels
    equal the stored metrics, for the held-out r2 report and both dev60 reports, across all
    7 configurations.
- `tests/unit/test_label_migration.py` runs the checks that need no git in CI.
