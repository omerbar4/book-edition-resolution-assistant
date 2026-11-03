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
