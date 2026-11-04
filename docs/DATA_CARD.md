# Data card

## Synthetic fixture set `synthetic-fixture-v1`

- **Generator:** `scripts/make_synthetic_fixtures.py` (deterministic; no randomness).
- **File:** `data/fixtures/synthetic_editions.jsonl`, 30 editions. The sha256 is recorded in the
  catalog's `catalog_meta.fixtures_sha256` at build time.
- **Purpose:** engineering checks of each pipeline branch. **Not** an evaluation set; no
  accuracy figure from it describes real-world performance.

| Scenario | Records |
|---|---|
| One work, many editions (hardcover, paperback, mass-market, anniversary, Spanish translation) | SYN-E0001–E0005 |
| Study guide for that work | E0006 |
| Box set | E0007 |
| Similar title, different author | E0008 |
| Numbered editions, author written "Last, First", 979-prefix ISBN | E0009–E0011 |
| One ISBN on three records with contradictory metadata | E0012–E0014 |
| Catalog ISBN with a bad checksum | E0015 |
| Prompt-injection text in a subtitle | E0016 (+ clean sibling E0017) |
| Zero-width character in the title + Cyrillic homoglyph in the author | E0018 |
| Sparse metadata | E0019 |
| Accented author | E0020 |
| Distractors | E0021–E0030 |

## Open Library corpus v3_proposed (built 2026-11-04)

Dated dump `ol_dump_2026-10-31`. Sizes from HTTP `Content-Length` headers on 2026-11-03:

| file | bytes | archive.org sha1 |
|---|---|---|
| editions | 12,630,804,778 | 78d5434c97782081e3f3adf37e2c53c18aed0b41 |
| authors | 784,183,875 | 93c27cf01586db495f2f0245d78a4ebfcdf298e5 |
| redirects | 75,673,010 | d8559bfbd88934d1b9d1caf354105eb4a2adefec |
| works (optional) | 4,078,855,962 | 07d086eb1c5b06b6a3905c1ab48469891b194d86 |

Built from the editions, authors and redirects dumps (the works dump was not used). The
selection was approved by the owner on 2026-11-03 (`data/selection/APPROVED_v3_proposed.txt`,
code pinned at `0fe293b`). The raw dumps were deleted after both builds and all checks passed.

| fact | value |
|---|---|
| corpus sha256 (`data/corpus/v3_proposed/corpus.jsonl`) | `cdabcf84712f29c104c11cc3e4bb640b00486ab55529ab94917666ef2e609464` |
| editions / works / families | 5,366 / 387 / 223 (largest family 14) |
| groups (works) | H 112, S1 60, S2 30, S3 30, S4 40, S5 15, S6 40, S7 60 |
| dev split | 123 families, 208 works, 2,998 editions |
| held-out split | 100 families, 179 works, 2,368 editions |
| excluded works | 2,484 (R1 author key 2,166, R2 title 314, R3 translation-of 4); 0 violations |
| missing rates | physical format 0.681, edition statement 0.683, language 0.142 |

Missing format, language and edition statements stay unknown in the corpus. When gold
labels are fitted, an unknown value never counts as distinguishing two editions.

**Reproducibility.** Two independent builds (separate scratch DBs, both rescanned the dumps)
produced byte-identical corpora. `scripts/verify_build.py` passed 26/26 checks against the
approved preview: selected ids, family assignments, split balance, strata, edition sampling,
exclusion counts, written + dropped = sampled, and every edition belongs to a selected work.
Results: `data/corpus/v3_proposed/reproducibility.json`; logs and the build-B manifest are in
`data/corpus/v3_proposed/build_records/`; the preview runs are in `data/selection/preview_reports/`.

**Probe audit.** A probe can receive an abstention label only if it is `verified_absent` in
both the pre-audit (every edition of the selected works, before sampling) and the final audit
(the written corpus); see `data/corpus/v3_proposed/probe_audit_final.json`. Verified absent (6):
The Remains of the Day, Never Let Me Go, Middlemarch (held-out); The Name of the Wind, Gödel,
Escher, Bach, Their Eyes Were Watching God (dev). Quarantined and unlabeled (4): Station
Eleven, The Left Hand of Darkness, A Wizard of Earthsea (resembling editions in the
pre-audit only) and The Pragmatic Programmer (by-statement surname hits in both audits).

**Known limitation.** Families are conservative but heuristic: 94 possible unrelated merges
are flagged in the manifest, and one spurious cross-seed family is accepted (Crime and
Punishment with Wuthering Heights, via a CliffsNotes title link). Merging too much only
costs split balance; it cannot leak a family across the two splits.
