# Evidence specification

Model output must match `AdjudicationOutput` (`src/bera/models.py`): `extra="forbid"` and
strict types (no string→number or string→bool coercion), parsed from JSON exactly as received.
Markdown fences, extra keys, wrong types and out-of-range values are **rejected, never
repaired, and never retried**.

```
choice:          "c1".."c5" (ids issued for this request only) | "ABSTAIN"
confidence:      float in [0, 1]   — logged only, never a decision input
decision_reason: str ≤ 400
evidence_fields: ≤ 8 × {candidate_id, field, value ≤ 200}
needs_human:     bool              — ABSTAIN requires true
```

## Citation check (exact typed equality, no substring matching)

| field | type | normalizer N | rule |
|---|---|---|---|
| title, subtitle, edition_name, translation_of | scalar text | NFKC → drop hidden characters → casefold → punctuation set to spaces (apostrophes removed) → collapse whitespace | `N(value) == N(stored)` |
| authors | list of person names | text normalizer + "Last, First" reordering + accent folding | `N(value) ∈ {N(x)}` |
| publishers, series | list of text | text normalizer | `N(value) ∈ {N(x)}` |
| languages | list of codes | trim + lowercase | membership |
| isbn_13 / isbn_10 | list of ISBNs | parse; must be checksum-valid; canonical ISBN-13 or compact ISBN-10 | membership |
| publish_year, number_of_pages | int | `^\d{1,5}$` then int | equality (`"2016.0"` is rejected) |
| physical_format | enum | trim + lowercase | equality with the enum value |

A citation also fails if:
- its `candidate_id` was not issued for this request, or
- the cited stored value carries suspicious Unicode.

A non-abstain choice must cite at least one field **of the chosen candidate**.

## Citation correctness ≠ inference correctness

A passing check proves only that the model quoted data that really is in that candidate's
record. It does not prove the model chose correctly. For example, `c2.publisher = "Lotus
Press"` can be a true citation even when the user's copy is the paperback. For this reason the
policy never relies on valid citations alone (see DECISION_POLICY.md).

## Suspicious Unicode

`bera.text.detect_suspicious` flags:
- bidi controls (U+061C, U+200E/F, U+202A–202E, U+2066–2069);
- zero-width and format characters;
- tag characters (U+E0000–E007F);
- C0/C1 controls;
- mixed-script tokens (a coarse Latin/Cyrillic/Greek/Armenian/Cherokee check).

Raw text is preserved. The UI and the prompt show hidden characters as `⟦U+XXXX⟧`. A flagged
query or flagged suggested record forces REVIEW (`suspicious_unicode`).
