# Dev batch 02: seven configurations and error analysis

**DEVELOPMENT DATA, n=20 human labels (one labeler), uncalibrated policy conservative-rules-v1; NOT held-out performance; NOT calibrated**

Labels `data/eval/labels/dev_batch02_labels.jsonl`; queue sha256 `554cc8635d9b99fe...`; families: frozen queue draft family, cross-checked against families.json.
Outcome and suggestion identical across all 7 configurations: True. Top-1 identical: False (differs only on a human-abstain case).

_wilson95_case_level treats cases as independent. bootstrap95_family_grouped resamples families (1000 reps, seed 0). Batch 02 has one case per family, so the grouped bootstrap equals a case bootstrap here; it cannot show uncertainty for 0/n or n/n, so use the Wilson bound for zero-event rates._

## Metrics (default configuration; identical outcomes in all configurations)

N = all cases, A = human-answerable, S = system suggested, U = human abstain.

| group | metric | k/n | value | Wilson 95% (case) | bootstrap 95% (family-grouped) |
|---|---|---|---|---|---|
| all (20) | correct_suggestion_rate /N | 7/20 | 0.350 | [0.181, 0.567] | [0.150, 0.550] |
| all (20) | wrong_match_rate /N | 0/20 | 0.000 | [0.000, 0.161] | [0.000, 0.000] |
| all (20) | error_among_suggestions /S | 0/7 | 0.000 | [0.000, 0.354] | [0.000, 0.000] |
| all (20) | suggestion_coverage_on_answerable /A | 7/18 | 0.389 | [0.203, 0.614] | [0.158, 0.625] |
| all (20) | top1_accuracy /A | 18/18 | 1.000 | [0.824, 1.000] | [1.000, 1.000] |
| all (20) | correct_abstention /U | 2/2 | 1.000 | [0.342, 1.000] | [1.000, 1.000] |
| prior_dev_families (8) | correct_suggestion_rate /N | 3/8 | 0.375 | [0.137, 0.694] | [0.125, 0.750] |
| prior_dev_families (8) | wrong_match_rate /N | 0/8 | 0.000 | [0.000, 0.324] | [0.000, 0.000] |
| prior_dev_families (8) | error_among_suggestions /S | 0/3 | 0.000 | [0.000, 0.561] | [0.000, 0.000] |
| prior_dev_families (8) | suggestion_coverage_on_answerable /A | 3/6 | 0.500 | [0.188, 0.812] | [0.125, 1.000] |
| prior_dev_families (8) | top1_accuracy /A | 6/6 | 1.000 | [0.610, 1.000] | [1.000, 1.000] |
| prior_dev_families (8) | correct_abstention /U | 2/2 | 1.000 | [0.342, 1.000] | [1.000, 1.000] |
| other_dev_families (12) | correct_suggestion_rate /N | 4/12 | 0.333 | [0.138, 0.609] | [0.083, 0.583] |
| other_dev_families (12) | wrong_match_rate /N | 0/12 | 0.000 | [0.000, 0.242] | [0.000, 0.000] |
| other_dev_families (12) | error_among_suggestions /S | 0/4 | 0.000 | [0.000, 0.490] | [0.000, 0.000] |
| other_dev_families (12) | suggestion_coverage_on_answerable /A | 4/12 | 0.333 | [0.138, 0.609] | [0.083, 0.583] |
| other_dev_families (12) | top1_accuracy /A | 12/12 | 1.000 | [0.757, 1.000] | [1.000, 1.000] |
| other_dev_families (12) | correct_abstention /U | 0/0 | n/a | n/a | n/a |

## LLM, tokens, cost

- advisory only: it can never turn review into suggest, so it cannot improve final coverage yet (validated LLM suggestion path unfinished).
- Invoked 2/20; statuses {'completed': 2, 'not_needed': 18}; final outcome when invoked {'review': 2, 'suggest': 0, 'suggest_correct': 0, 'suggest_on_expected_abstain': 0}.
- Advisory choice in human gold: 1/2.
- Tokens total: 1568. Estimated cost: $0.00 (local inference has no per-token charge; any non-zero rate is a hypothetical comparison).

## Latency (ms, end to end per query)

| configuration | p50 | p95 |
|---|---|---|
| 1_exact_fuzzy | 14.556 | 29.933 |
| 2_lexical | 3.021 | 5.995 |
| 2b_lexical_rrf | 4.553 | 8.649 |
| 3_embedding | 12.12 | 17.604 |
| 4_hybrid | 12.93 | 24.558 |
| 5_hybrid_rerank | 38.805 | 54.755 |
| 6_routed_llm | 41.592 | 5968.151 |

Configuration 6 p95 is dominated by local LLM adjudication (2 invocations).

## Per case (default configuration)

| case | prior-dev family | query fields | human | policy | route | cause of review |
|---|---|---|---|---|---|---|
| d02-02b810abce | no | author, physical_format, publish_year, title | suggest | suggest | retrieval |  |
| d02-03c77f5cc6 | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence |
| d02-0589d2fcff | yes | author, title | abstain (underspecified) | review | retrieval | undistinguished alternatives among retrieved candidates |
| d02-08a4bf8ae5 | no | isbn, publish_year, title | suggest | suggest | isbn_exact |  |
| d02-451a45f8ac | yes | author, physical_format, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence |
| d02-4a5ec910db | no | author, physical_format, publish_year, title | suggest | suggest | retrieval |  |
| d02-4c1008b303 | no | isbn, publish_year, title | suggest | suggest | isbn_exact |  |
| d02-4c2ae5e76e | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence |
| d02-500b786619 | yes | isbn, publish_year, title | suggest | suggest | isbn_exact |  |
| d02-5ad58c7355 | yes | author, isbn, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis |
| d02-6463d76f7e | no | author, physical_format, publish_year, title | suggest | review | retrieval | undistinguished alternatives among retrieved candidates |
| d02-a45a6e14e1 | no | author, isbn, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis |
| d02-ad6b44676f | no | isbn, physical_format, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis |
| d02-b1c25eb8ef | no | isbn, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis |
| d02-bd2b145215 | yes | isbn, publish_year, title | suggest | suggest | isbn_exact |  |
| d02-ed610d5d91 | yes | author, isbn, publish_year, title | abstain (underspecified) | review | isbn_repair | damaged ISBN: repair is only a hypothesis |
| d02-f13c90f2c1 | yes | isbn, publish_year, title | suggest | suggest | isbn_exact |  |
| d02-f290f0c95f | no | isbn, publish_year, title | suggest | review | isbn_exact | other: suspicious_unicode |
| d02-f69c8768ce | yes | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence |
| d02-fdf24a4194 | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence |

## Drafter agreement (not accuracy)

The human matched the program's drafted proposal exactly on 17/20. agreement between the human and the program's drafted proposal (spec v2); measures the drafter, not any system.

## Findings (hypotheses only; nothing was changed)

Every configuration produced the same outcome and suggestion on all 20 cases. The candidate
generators did not matter on this batch: in all 18 human-answerable cases the human's edition
was ranked first by every configuration. What limited coverage was the decision policy.

Causes of review on the 11 human-answerable cases (default configuration):

1. **Initials vs full author name (5).** For example a query author "S. Reynolds" against a
   record author "Sophia Reynolds". The author check returns UNKNOWN rather than AGREE, so a
   title + year match is "insufficient evidence". Hypothesis: an initials-consistent surname
   match could count as agreement. It is a feature change, and it would need fresh labels to
   validate.
2. **Checksum-invalid ISBN (4).** The repair is only a hypothesis, so the owner rule routes
   it to review, even when title/author/year agree with the repaired record. Synthetic label
   spec v2 discards a damaged ISBN and judges the remaining fields, so here the policy is
   stricter than the spec. Changing this is an owner decision.
3. **Catalog encoding damage trips the unicode guard (1).** The record's author contains a
   control character from mis-decoded UTF-8. That field was not even supplied by the query,
   whose ISBN maps uniquely to the record. Hypothesis: the guard should apply to query input
   and to fields actually compared, not to unrelated catalog fields. Owner decision.
4. **Unknown-format twin (1).** A second record with the same title, author and year has no
   format. Under the owner rule missing metadata is unknown, never distinguishing, so review
   is the rule-consistent outcome. The human chose the record whose format is known, so this
   case shows a human-vs-rule disagreement for the owner to rule on. The label is unchanged.

The 2 human abstentions were both routed to review (2/2).

**LLM.** The LLM was invoked on 2 of 20 cases and completed both. It is advisory only: it
can never turn review into suggest, so it cannot improve final coverage yet (the validated
LLM suggestion path is unfinished). Its choice equalled the top-1 candidate in both cases.

## What this does not show

- Not held-out performance; not calibrated; one labeler; n=20 (18 answerable, 2 abstain,
  0 out-of-corpus). Abstention quality is essentially untested.
- 0 wrong suggestions is not proof of safety: the case-level Wilson upper bound on the
  wrong-match rate is about 16%.
- The 8 prior-development families also appeared in the 300-case synthetic check that shaped
  policy v1, so those cases may be optimistic. The 12/8 split is too small to compare.
- Any change motivated by these 20 cases makes them development data for that change;
  improvement must be shown on fresh labels.
- Agreement with drafted proposals measures the drafter, not any system.

