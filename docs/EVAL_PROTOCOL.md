# Evaluation protocol

## Data
- **Human cases** (`data/eval/human_cases.jsonl`): ≥ 100 (target 120) realistic, labeled per
  LABELING_GUIDE.md. Not started (needs the real corpus and human time).
- **Abstention cases:** about 60, covering underspecified, out-of-corpus (listed in
  `exclusions.jsonl` before the corpus is built), contradictory, and wrong-product cases.
- **Synthetic perturbations** (`bera.evalkit.perturb`): seeded ops (typo, name order,
  initials, dropped fields, ISBN-10 form, ISBN digit error, case/punctuation). Each case stores
  its ops, seed and source edition. About half drop the ISBN. Expected behavior is recomputed
  after perturbation.
- **Split leakage limitation:** splits are by conservative work family (SELECTION_PROCEDURE.md §4). This reduces but **cannot eliminate** leakage between dev and held-out, because some aliases/duplicates are undetectable from dump metadata.
- **Splits:** `bera.evalkit.splits`, a SHA-256 hash of `(seed, family)`, 60/40 dev/held-out,
  with a leakage check.

## Rules
1. Tune features, thresholds and prompts on **dev only**, using grouped out-of-fold
   predictions (DECISION_POLICY.md).
2. Freeze the policy as a tagged commit. Run held-out **once**. Report what it says.
3. Human feedback from the UI is never merged into benchmark labels.
4. Synthetic-only or synthetic-catalog runs are labeled "ENGINEERING CHECK", automatically.

## Systems (`bera.evalkit.run`)

All six share the ISBN stage, the field checks and the policy:

| key | system | status |
|---|---|---|
| 1_exact_fuzzy | ISBN exact + brute-force rapidfuzz | runnable |
| 2_lexical | ISBN exact + FTS5 BM25 | runnable |
| 2b_lexical_rrf | BM25 + trigram via RRF (default) | runnable (extra ablation) |
| 3_embedding | bge-small-en-v1.5 | blocked: download approval |
| 4_hybrid | lexical + embedding via RRF | blocked |
| 5_hybrid_rerank | + cross-encoder | blocked |
| 6_routed_llm | + local LLM adjudication on ambiguous top-k | blocked |

## Metrics

Definitions and denominators are in the `bera.evalkit.metrics` docstring:
- recall@k, MRR and top-1 over A (answerable cases);
- correct-suggestion and wrong-match rates over N (all cases);
- error among suggestions over S (cases where the system suggested);
- abstention rate over N, and correct abstention over U (expected-abstain cases);
- failure categories: retrieval failure, ranking failure, conservative abstention,
  wrong suggestion (retrieval miss / ranking), unsupported suggestion on unresolvable input;
- signal buckets with n and Wilson intervals;
- a risk-coverage curve over an **uncalibrated** ranking signal, until a calibrated scorer
  exists;
- family-grouped bootstrap 95% intervals;
- p50/p95 latency for each stage;
- adjudication invocation rate, tokens, and cost (local = 0; any rate is hypothetical).

## Engineering check so far (synthetic, not an evaluation)

Generating 90 synthetic perturbation cases from the 30 synthetic fixtures (seed 20261103) and
running the three runnable systems shows that the harness works end to end. All three systems
produced **identical** category counts on these cases. The fixture catalog is too small for
retrieval differences to show, so it **cannot** tell the systems apart. That requires the real
Open Library corpus and human cases.

## Engineering check on corpus v3_proposed (2026-11-04)

**This is an engineering check, not an evaluation.** The 300 cases are synthetic
perturbations of 300 development editions (`scripts/make_dev_check_cases.py`, seed 20261104,
excluding the 17 labeling-draft sources). Gold labels were fitted against the whole catalog,
and unknown metadata never counted as distinguishing; 133 of the 300 cases expect abstention.
There are no human labels, no held-out cases, nothing is calibrated, and nothing was tuned on
these results. Report: `data/eval/results/dev_check_v3/report.md`.

All seven configurations ran: six methods plus the BM25 + trigram RRF default. Top-1 ranged
from 0.982 to 0.994 on the 167 suggest cases. Correct suggestions were 103/300 for every
configuration. Wrong matches were 16–18/300; these are mostly unsupported suggestions on
abstain cases. Correct abstention ranged from 0.865 to 0.880. These numbers show that the
pipeline runs end to end on real catalog data. They say nothing about accuracy on real user
inputs.

### Correction: LLM counts (reconciled 2026-11-04)

An earlier version of this section said the LLM's advisory choice was in the gold set "for
91/93 of the completed adjudications". That was wrong: 102 adjudications completed, and the 93
were only those that chose a candidate; the other 9 completed responses were LLM abstentions.
The first run did not store per-case adjudication fields, so the LLM method was re-run alone
on the same 300 cases with explicit counts (`data/eval/results/dev_check_v3_llm_rerun/`).
Temperature is 0, but the 12 s stage deadline makes completion timing-dependent:

| count | first run | re-run |
|---|---|---|
| invoked (policy said REVIEW) | 140 / 300 | 140 / 300 (105 expected abstain, 35 expected suggest) |
| deadline exceeded | 28 | 23 |
| evidence invalid | 10 | 10 |
| completed (valid responses) | 102 | 107 |
| completed, LLM abstained | 9 | 11 (all on expected-abstain cases) |
| completed, chose a candidate | 93 | 96 |
| choice in gold, all | 91 / 93 | 92 / 96 |
| choice correct, expected-suggest cases | not recorded | 31 / 33 |
| choice in acceptable set, expected-abstain cases | not recorded | 61 / 63 |
| choice differs from retrieval top-1 | not recorded | 9 / 96 |
| final SUGGEST among invoked cases | 0 | 0 |

"In gold" on an expected-abstain case only means the choice was one of several editions that
fit; it is not a correct answer, and the correct output for those cases is review. The LLM is
advisory: it never turned a REVIEW into a SUGGEST, and method 6's final decisions are identical
to method 5's (and identical across both runs). Every wrong suggestion counted for method 6
came from the policy before the LLM stage.

### Wrong suggestions (analysis 2026-11-04; gold labels unchanged)

Every "wrong match" in this check is an unsupported suggestion: a SUGGEST on a case whose
synthetic gold says abstain because several editions fit, and the suggested edition was one
of them. No system suggested an edition outside the gold set. There are 18 distinct cases
(16–18 per method). `scripts/analyze_dev_check_suggestions.py` re-ran each and classified it;
output: `data/eval/results/dev_check_v3/unsupported_suggestions.json`.

| bucket | cases | what happened | type |
|---|---|---|---|
| ISBN exact, twins known distinct | 5 | The query ISBN maps to exactly one record. Each other fitting edition has no ISBN but differs from the ISBN-holding record on a field known on both (year, subtitle, language or format). | questionable synthetic gold: the fit rule compares twins only to the query, not to the record holding the ISBN |
| ISBN exact, possible duplicate record | 5 | At least one twin has no ISBN and nothing known that differs from the ISBN holder; it may be a duplicate record of the same edition (an acceptable-set case) or a different edition. Four of these involve one sparse record (OL25415630M, "war and peace", publisher only). | rule conflict for the owner: is an exact unique ISBN distinguishing against an unknown ISBN? |
| ISBN exact, vague language code only | 4 | The only difference from the ISBN holder is a `mul`/`und` language code (all four involve Jane Eyre OL13856380M). | undecided |
| Retrieval: fitting edition not retrieved | 2 | Another fitting edition never reached the candidate list, so "exactly one consistent candidate" was judged on an incomplete list (War and Peace 1990; Frankenstein 1818, where the actual 1818 hardcover was not retrieved). | policy error |
| Retrieval: unknown treated as disagreement | 2 | Consistency requires author AGREE, so twins whose author is UNKNOWN were dropped (War and Peace by "Louise" vs 3 author-less 2016 records; Dune 2015, embedding only). | policy error: contradicts "unknown is never distinguishing" |

Per method: exact+fuzzy 16 (14 ISBN, 1 not-retrieved, 1 unknown-as-disagreement); embedding
18 (14, 2, 2); every other method 17 (14, 2, 1).

Nothing was tuned on this analysis. The two policy errors and the ISBN rule question are
recorded as open decisions; any policy change would be judged on human-labeled dev cases,
not on these synthetic ones.


### Re-check after label spec v2 and policy v1 (2026-11-04; development engineering check)

Labels: `data/eval/dev_check_v3_synthetic.labels_v2.jsonl`. The 300 cases have the same
queries as before; 18 labels changed, all logged with evidence in
`data/eval/label_changes/`, spec in `docs/SYNTHETIC_LABEL_SPEC.md`. Results:
`data/eval/results/dev_check_v3_labels_v2_policy_v1/`. The original cases and results are
preserved unchanged. Under v2 labels there are 179 suggest and 121 abstain cases.

| method | v1 labels, policy v0 | v2 labels, policy v0 (old outputs rescored) | v2 labels, policy v1 |
|---|---|---|---|
| 1 exact + fuzzy | 103 correct / 16 wrong / 117 of 133 abstain | 117 / 2 / 119 of 121 | 115 / 0 / 121 of 121 |
| 2 BM25 | 103 / 17 / 116 | 117 / 3 / 118 | 115 / 0 / 121 |
| 2b BM25 + trigram (default) | 103 / 17 / 116 | 117 / 3 / 118 | 115 / 0 / 121 |
| 3 embedding | 103 / 18 / 115 | 117 / 4 / 117 | 115 / 0 / 121 |
| 4 hybrid | 103 / 17 / 116 | 117 / 3 / 118 | 115 / 0 / 121 |
| 5 hybrid + reranker | 103 / 17 / 116 | 117 / 3 / 118 | 115 / 0 / 121 |
| 6 routed LLM (advisory) | 103 / 17 / 116 | 117 / 3 / 118 | 115 / 0 / 121 |

"correct" and "wrong" are counted out of 300 cases; "abstain" counts correct abstentions out
of the expected-abstain cases.

How to read this:

- **The zero is partly circular.** The v2 synthetic labels and policy v1 now share the same
  rules: unknown is never distinguishing, and a unique explicit ISBN wins. Agreement on
  synthetic cases is expected by construction. It shows the code implements the rules; it
  says nothing about quality on real inputs. Human-labeled dev cases are required for that.
- **Policy v1 costs 2 correct suggestions** compared with v0 on v2 labels. Both are
  conservative reviews, where runtime checks are more permissive than the synthetic spec:
  - syn-OL3310784M-0 (The Woman Warrior, 2005): a German translation with no author and no
    year matches the title through `translation_of`.
  - syn-OL7508358M-0 (Of Mice and Men, 1975): two author-less records from 1974 and 1977 are
    year-"near" (±2 → unknown), while the spec compares years exactly.

  Whether a translation title or a near year should count as distinguishing is an open owner
  decision. Neither was tuned.
- **LLM (method 6):** invoked on 145 of 300 cases. 36 hit the deadline, 13 had invalid
  evidence, and 96 completed. Of the completed responses, 7 were LLM abstentions and 89 chose
  a candidate. Of those 89 choices: 29 of 30 were correct on expected-suggest cases, and 57
  of 59 were within the consistent set on expected-abstain cases. **Final suggestions among
  invoked cases: 0 of 145.** Method 6's decisions are identical to method 5's, so it cannot
  raise coverage until the validated LLM suggestion path exists.

## Development run on human labels: batch 02 (2026-11-07)

**Development data, 20 human labels from one labeler; not held-out performance; not
calibrated.** Report: `data/eval/results/dev_batch02_human_policy_v1/` (`report.json` from the
harness, plus `error_analysis.md`/`.json` from `scripts/analyze_dev_batch02.py`). Policy,
thresholds, prompts and models were unchanged. Families were resolved from the frozen queue
and `families.json` (`bera.evalkit.families`).

- All seven configurations gave the same outcome and suggestion on every case. Correct
  suggestions 7/20; wrong matches 0/20 (case-level Wilson upper bound 0.161); top-1 18/18 on
  the human-answerable cases; 2/2 human abstentions routed to review.
- Coverage was limited by the policy, not retrieval. The 11 reviews on human-answerable cases
  were caused by: initials vs full author name (5), checksum-invalid ISBN repair (4), catalog
  encoding damage tripping the unicode guard (1), and an unknown-format twin (1, which is
  rule-consistent).
- The LLM was invoked 2/20 times, used 1,568 tokens and cost $0 (local). It is advisory and
  cannot raise final coverage yet.
- Results are reported for the 8 families also used in the synthetic policy-development
  check and for the other 12. Both groups are too small to compare.

## Development run on 60 human labels (2026-11-07)

**Development data: 60 human labels from one labeler, from 60 distinct families; not
held-out performance; not calibrated.** Report: `data/eval/results/dev60_human_policy_v1/`
(harness `report.json`, plus `error_analysis.md`/`.json` from `scripts/analyze_dev_eval.py`).
Policy, thresholds, prompts and models were unchanged. The harness now accepts several case
files and frozen queues and records each case file's sha256.

- All seven configurations made the same decisions. Correct suggestions 16/60; wrong matches
  0/60 (case-level Wilson upper bound 0.060); top-1 44/44 on the human-answerable cases; 16/16
  human review cases routed to review.
- Families never in the policy-development check (43) and policy-development families (17)
  are reported separately.
- Coverage is limited by the policy. Causes of the 28 reviews on human-answerable cases:
  insufficient distinguishing evidence 15, damaged-ISBN repair 6, undistinguished
  alternatives 4, supplied-field conflict 2, unicode guard 1.
- Disagreements are reported separately and no label was changed. The LLM is advisory: it was
  invoked on 15/60 cases (14,684 tokens, $0 local) and changed no final outcome.
- Withheld until held-out labeling is complete: per-stratum, per-template and per-source
  summaries of human answers.
