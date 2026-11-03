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

## Open Library corpus (planned, download pending approval)

Dated dump `ol_dump_2026-10-31`. Sizes from HTTP `Content-Length` headers on 2026-11-03:

| file | bytes | archive.org sha1 |
|---|---|---|
| editions | 12,630,804,778 | 78d5434c97782081e3f3adf37e2c53c18aed0b41 |
| authors | 784,183,875 | 93c27cf01586db495f2f0245d78a4ebfcdf298e5 |
| redirects | 75,673,010 | d8559bfbd88934d1b9d1caf354105eb4a2adefec |
| works (optional) | 4,078,855,962 | 07d086eb1c5b06b6a3905c1ab48469891b194d86 |

The construction protocol (seed strata fixed before filtering, author resolution order,
missing-metadata rules, manifest contents) is described in the Phase 0 amended plan and is
being implemented in `src/bera/ingest/`.
