# Labeling guide

Target: at least **100 (preferably 120) human-labeled cases**, plus about 60
abstention/out-of-corpus cases. AI-drafted queries count only after a human labels them, and
they get `origin: "ai_drafted_human_labeled"`.

## Sources you may use

- Physical books you own, or books you look at in a public library or bookstore.
- Never seller, customer, marketplace or inventory data, and never records from other private
  projects.

## Writing the query (do this BEFORE looking at the catalog)

1. Write the query the way a person really would, given only what is in front of you: a
   partial or damaged ISBN, a misremembered title, the author name as printed, the format,
   the year from the copyright page.
2. Don't polish it. Keep your typos and missing fields. Record what was hard in `notes`.

## Finding the gold edition

1. Run `uv run python -m bera.evalkit.label search --title "<words>"`. It lists catalog
   records **alphabetically with no system scores**, so you aren't anchored by the system's
   ranking.
2. Compare against the physical item: ISBN on the copyright page, publisher/imprint, format,
   year, edition statement, language.
3. Set `gold_edition_ids` to the single matching edition. If several records truly describe
   the same physical edition (catalog duplicates), list all of them.

## Ambiguity rules

Use `expected: "abstain"` with a specific `ambiguity_reason` when:

| reason | rule |
|---|---|
| `underspecified` | the information in the query fits ≥ 2 distinct editions and nothing in it distinguishes them (list them in `gold_edition_ids`) |
| `out_of_corpus` | your edition is not in the catalog (`gold_edition_ids: []`) |
| `contradictory` | the query's own facts conflict (e.g. a year before the first edition) |
| `not_a_book_edition` | the item is a different product, e.g. a box set when the query is about a volume, or vice versa (label the product actually described) |

Out-of-corpus books must be listed in `data/eval/exclusions.jsonl` **before** the corpus is
built, so the builder removes them and verifies they're absent.

## Families and splits

`family` = the Open Library work id of the gold (or of the main work for study
guides/translations of it). Splits are assigned by `bera.evalkit.splits` from a hash of
`(seed, family)`; never set `split` by hand.

## Check

```bash
uv run python -m bera.evalkit.label validate data/eval/human_cases.jsonl
```

This fails on duplicate ids, gold ids missing from the catalog, or a family appearing in both
splits.

## Effort estimate

About 3–5 minutes per case: 120 cases ≈ 6–10 hours, plus about 2 hours for abstention cases.
Optionally, a second labeler on 30 cases to measure agreement.

## Labeling screen notes (2026-11-04)

- **Search** matches records where every word you type appears in the title, subtitle or
  original title, ignoring case and accents. Results are alphabetical, never ranked. The
  screen shows "Showing a–b of N" and pages of 50. Results used to be cut off silently at 60;
  they no longer are.
- **Skip for now** records that a case cannot be assessed yet. It is written to
  `dev_labels.skips.jsonl`, is not a label, never reveals the proposal, and does not count.
- **Practice labels.** `dev_labels.provenance.jsonl` annotates existing label lines without
  editing them; each annotation is pinned by the line's sha256. dev-b01-001 and dev-b01-002
  are marked `practice_ai_assisted`. They are kept, but excluded from the independent
  human-label count and from evaluation. Their proposals were revealed, so they stay practice
  even if relabeled.
- **Template notes.** Some batch-01 drafts' generator templates did not apply to their
  source record: 001 and 013 (author unchanged), 003 (no ISBN-13, so no ISBN in the query)
  and 016 (source has no ISBN). The query itself is what you label; fields not shown were
  not given. Drafter v2, used for future batches, only uses templates that can apply.

## Blind-labeling fix (2026-11-07)

- **The template is hidden until you save.** The generator template name and template note
  are no longer sent or shown before a label is saved. They appear after Save, with the
  drafted proposal. In batch 01 several templates always produced the same proposed outcome
  (for example `out_of_corpus_probe`, `title_author_only`, `misread_isbn_digit`), so the
  name hinted at the answer.
- **The answer is a required choice with no default.** Pick "One specific edition" (and
  tick one or more records) or "Human review (abstain)" (and pick a reason). Save stays
  disabled until the answer is complete. The old screen had a checkbox reading "Correct
  behavior is human review (abstain)". It was an unticked answer option, not the answer,
  but it read like a statement.

## Exposure before labeling (batch 01, recorded 2026-11-07)

Exposures are recorded in `data/eval/labels/dev_labels.exposures.jsonl`, an append-only
sidecar. A record can exist before a case is labeled. Any label on an exposed case, whether
it already exists or is added later, is excluded from the independent count and from
evaluation, exactly like a practice label. The queue shows such a case as `exposed`. The
records name the kind of exposure only, never the answer or the drafted outcome. No
clearing mechanism exists: re-admitting a case needs an explicit owner decision.

| Cases | Exposure | Assessment |
|---|---|---|
| 007 | ChatGPT supplied the answer before labeling | exposed |
| 010, 011, 012, 016, 017, p01, p02, p03 | template ↔ drafted-outcome table; the case's template had one drafted outcome across batch 01 | exposed: the outcome is inferable from the template name |
| p01, p02, p03 | the draft id suffix `pNN`, shown before saving, marks the draft as a probe (a separate generation type) | exposed (in addition to the row above) |
| 007, 008, 009, 013, 014, 015 | the same table; the case's template had more than one drafted outcome | unresolved partial exposure, excluded until the owner decides |

Why the table matters for every remaining case: until commit 4dff187, every labeling
interface showed each case's template name before saving, so the table could be matched to
any case that was opened. The drafted proposal is a program's draft, not ground truth.
Knowing it biases a labeler toward agreement, which also contaminates the human-vs-proposal
agreement figure.

**Result: batch 01 currently has no case that can yield an independent human label**
(6 practice, 14 exposed). Labeling 007–020 is still useful as development practice, but
independent labels need a fresh batch drafted after this fix. Its case ids should not mark
probes; batch 01's queue and draft ids are left unchanged.
