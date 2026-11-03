# Corpus selection procedure, v1 (proposed, pending owner review)

**Status:** v1 is *frozen* for the first corpus build, so that build is reproducible. It is
still *proposed*: if the owner changes anything, a v2 is cut (new files and hashes), the
corpus is rebuilt, and every label is re-validated against the new corpus with
`bera.evalkit.label validate`. Evaluation results are reported only against a version the
owner has approved.

## Inputs (all public)

| file | sha256 |
|---|---|
| `data/selection/seed_list_v1.jsonl`: 42 public, well-known titles chosen for edition confusability (title variants, translations, numbered/revised editions, box sets, study-guide-heavy classics, short shared titles) | `9afdbe553bd9c3bc480c960cc06761465254a668de6208d63e7a0c91d79646cc` |
| `data/selection/exclusions_v1.jsonl`: 10 out-of-corpus probe books for abstention cases | `7111d5e7a175299dab0b8de8658aad16c99defd7ca4a2b1ff40b4f7321000538` |
| `data/selection/selection_config_v1.json`: dump date, seeds, quotas | `c87ab42d2b733f5678c3c460621994855b517ce2c27c1adc690ce014e7a0a704` |

The lists were written from general public knowledge of widely published books. No
private-project data, seller or customer records, or inventory were used.

## Deterministic steps (`bera.ingest.corpus`)

1. **Pass 1** streams the editions dump and computes per-work statistics (edition count,
   valid-ISBN count, known formats, languages, translation and revision markers, study-guide
   and box-set markers, most common normalized title).
2. **H (seed titles).** For each seed title, take the works whose normalized title equals it
   exactly, ordered by edition count (descending), then key. Keep the top 3. Matching is by
   title only, so author agreement is checked afterwards in the manifest review.
3. **Strata S1–S7** use the fixed SQL rules in the module docstring. Candidates are sorted by
   work key and sampled with `random.Random(20261103)` against the quotas (CPython's Mersenne
   Twister; the Python version is recorded in the manifest).
4. **Exclusions.** Works whose dominant title equals a probe title are never selected (this
   over-excludes same-titled works; that's intended). Editions matching a probe's title and
   author, or ISBN, are dropped in pass 2. The output is then **re-checked independently**,
   and the manifest must show `violations: []`.
5. **Pass 2** keeps the selected works' editions (at most 60 per work, in key order), resolves
   redirects and authors, maps factual fields only, and writes `corpus.jsonl` sorted by
   edition id plus `manifest.json` (input digests, read statistics, strata counts, drops,
   exclusion check, output digest).
6. **Reproducibility check.** Run the build twice from the same inputs; the output SHA-256
   must be identical. Only then are the raw dumps deleted.

## Known limitations

- Title-only matching for seed titles can pull in an unrelated work that shares the exact
  title. The manifest review lists every H match so these are visible.
- Author names come from the authors dump's `name` field; alternate names are not yet used
  for matching.
