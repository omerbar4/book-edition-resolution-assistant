# Dev evaluation (60 human labels) and error analysis

**DEVELOPMENT DATA: 60 human labels (one labeler), uncalibrated policy conservative-rules-v1; NOT held-out performance; NOT calibrated**

60 cases from 60 distinct families: 44 human edition choices, 16 human review (reasons: {'underspecified': 12, 'out_of_corpus': 4}).
Outcome and suggestion identical across all configurations: True; top-1 identical: False.

_wilson95_case_level treats cases as independent; bootstrap95_family_grouped resamples families with all their queries (1000 reps, seed 0). Every case here is from a distinct family. Bootstrap cannot show uncertainty for 0/n or n/n; use the Wilson bound for zero-event rates._

## Metrics (default configuration; outcomes identical in all configurations)

N = all, A = human edition, S = system suggested, U = human review.

| group | metric | k/n | value | Wilson 95% (case) | bootstrap 95% (family) |
|---|---|---|---|---|---|
| all (60 q / 60 fam) | correct_suggestion_rate /N | 16/60 | 0.267 | [0.171, 0.390] | [0.150, 0.383] |
| all (60 q / 60 fam) | wrong_match_rate /N | 0/60 | 0.000 | [0.000, 0.060] | [0.000, 0.000] |
| all (60 q / 60 fam) | error_among_suggestions /S | 0/16 | 0.000 | [0.000, 0.194] | [0.000, 0.000] |
| all (60 q / 60 fam) | suggestion_coverage_on_answerable /A | 16/44 | 0.364 | [0.238, 0.511] | [0.225, 0.522] |
| all (60 q / 60 fam) | top1_accuracy /A | 44/44 | 1.000 | [0.920, 1.000] | [1.000, 1.000] |
| all (60 q / 60 fam) | correct_abstention /U | 16/16 | 1.000 | [0.806, 1.000] | [1.000, 1.000] |
| never in the policy-development check (43 q / 43 fam) | correct_suggestion_rate /N | 11/43 | 0.256 | [0.149, 0.402] | [0.116, 0.395] |
| never in the policy-development check (43 q / 43 fam) | wrong_match_rate /N | 0/43 | 0.000 | [0.000, 0.082] | [0.000, 0.000] |
| never in the policy-development check (43 q / 43 fam) | error_among_suggestions /S | 0/11 | 0.000 | [0.000, 0.259] | [0.000, 0.000] |
| never in the policy-development check (43 q / 43 fam) | suggestion_coverage_on_answerable /A | 11/34 | 0.324 | [0.191, 0.492] | [0.161, 0.485] |
| never in the policy-development check (43 q / 43 fam) | top1_accuracy /A | 34/34 | 1.000 | [0.898, 1.000] | [1.000, 1.000] |
| never in the policy-development check (43 q / 43 fam) | correct_abstention /U | 9/9 | 1.000 | [0.701, 1.000] | [1.000, 1.000] |
| policy-development families (reported separately) (17 q / 17 fam) | correct_suggestion_rate /N | 5/17 | 0.294 | [0.133, 0.531] | [0.059, 0.529] |
| policy-development families (reported separately) (17 q / 17 fam) | wrong_match_rate /N | 0/17 | 0.000 | [0.000, 0.184] | [0.000, 0.000] |
| policy-development families (reported separately) (17 q / 17 fam) | error_among_suggestions /S | 0/5 | 0.000 | [0.000, 0.434] | [0.000, 0.000] |
| policy-development families (reported separately) (17 q / 17 fam) | suggestion_coverage_on_answerable /A | 5/10 | 0.500 | [0.237, 0.763] | [0.167, 0.818] |
| policy-development families (reported separately) (17 q / 17 fam) | top1_accuracy /A | 10/10 | 1.000 | [0.723, 1.000] | [1.000, 1.000] |
| policy-development families (reported separately) (17 q / 17 fam) | correct_abstention /U | 7/7 | 1.000 | [0.646, 1.000] | [1.000, 1.000] |

## Why human-answerable cases went to review (default configuration)

- insufficient distinguishing evidence: 15
- damaged ISBN: repair is only a hypothesis: 6
- undistinguished alternatives among retrieved candidates: 4
- other: suspicious_unicode: 1
- a supplied field conflicts with the top candidate: 2

## Disagreements (reported separately; no label was changed)

- A. Human vs drafted proposal (measures the drafter; labels are never changed to match proposals): {'agree': 45, 'both review, different listed records': 12, 'human edition, proposal review': 3}
- B. Human vs policy outcome: {'agree': 32, 'human edition, policy review': 28}
- C. Open owner-review flags: {'d02-6463d76f7e': ['human_vs_missing_metadata_rule']}

Case ids for A and B are in error_analysis.json.

## LLM (advisory), tokens, cost

- advisory only in conservative-rules-v1: it cannot turn review into suggest, so it cannot raise final coverage.
- Invoked 15/60; statuses {'completed': 12, 'deadline_exceeded': 1, 'evidence_invalid': 2, 'not_needed': 45}; final outcome when invoked {'review': 15, 'suggest': 0, 'suggest_correct': 0, 'suggest_on_expected_abstain': 0}.
- Routes: {'completed_with_choice': 12, 'agree_with_top1': 10, 'override_top1': 2, 'agree_route_choice_correctness': {'answerable': 4, 'choice_in_human_gold': 4}, 'override_route_choice_correctness': {'answerable': 0, 'choice_in_human_gold': 0}}.
- Tokens 14684; estimated cost $0.00 (local).

## Latency p50/p95 (ms per query)

- 1_exact_fuzzy: 13.909 / 25.175
- 2_lexical: 3.64 / 6.116
- 2b_lexical_rrf: 4.447 / 7.625
- 3_embedding: 9.611 / 15.136
- 4_hybrid: 11.481 / 19.388
- 5_hybrid_rerank: 36.546 / 57.991
- 6_routed_llm: 50.605 / 7695.593

## Per case (default configuration)

| case | policy-dev family | query fields | human | policy | route | cause of review | vs proposal |
|---|---|---|---|---|---|---|---|
| d02-02b810abce | no | author, physical_format, publish_year, title | suggest | suggest | retrieval |  | agree |
| d02-03c77f5cc6 | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d02-0589d2fcff | yes | author, title | abstain (underspecified) | review | retrieval | undistinguished alternatives among retrieved candidates | both review, different listed records |
| d02-08a4bf8ae5 | no | isbn, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d02-451a45f8ac | yes | author, physical_format, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d02-4a5ec910db | no | author, physical_format, publish_year, title | suggest | suggest | retrieval |  | agree |
| d02-4c1008b303 | no | isbn, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d02-4c2ae5e76e | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d02-500b786619 | yes | isbn, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d02-5ad58c7355 | yes | author, isbn, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis | agree |
| d02-6463d76f7e | no | author, physical_format, publish_year, title | suggest | review | retrieval | undistinguished alternatives among retrieved candidates | human edition, proposal review |
| d02-a45a6e14e1 | no | author, isbn, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis | agree |
| d02-ad6b44676f | no | isbn, physical_format, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis | agree |
| d02-b1c25eb8ef | no | isbn, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis | agree |
| d02-bd2b145215 | yes | isbn, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d02-ed610d5d91 | yes | author, isbn, publish_year, title | abstain (underspecified) | review | isbn_repair | damaged ISBN: repair is only a hypothesis | both review, different listed records |
| d02-f13c90f2c1 | yes | isbn, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d02-f290f0c95f | no | isbn, publish_year, title | suggest | review | isbn_exact | other: suspicious_unicode | agree |
| d02-f69c8768ce | yes | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d02-fdf24a4194 | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-0997062a58 | no | author, physical_format, publish_year, title | suggest | suggest | retrieval |  | agree |
| d03-0ad6ec4b93 | no | author, physical_format, publish_year, title | abstain (underspecified) | review | retrieval | undistinguished alternatives among retrieved candidates | both review, different listed records |
| d03-0f3cf5a743 | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-10956f0d07 | no | isbn, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d03-14b21ee1ac | yes | author, title | abstain (underspecified) | review | retrieval | undistinguished alternatives among retrieved candidates | both review, different listed records |
| d03-14b62c92d6 | no | author, physical_format, publish_year, title | suggest | review | retrieval | undistinguished alternatives among retrieved candidates | agree |
| d03-1d4f410493 | no | author, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-250eb0fe92 | no | author, physical_format, publish_year, title | suggest | review | retrieval | a supplied field conflicts with the top candidate | agree |
| d03-30dd74b830 | yes | author, physical_format, publish_year, title | suggest | suggest | retrieval |  | agree |
| d03-4163d593ce | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-5c1c081224 | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-5f0e5144cc | no | isbn, physical_format, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d03-74535cab45 | no | isbn, publish_year, title | abstain (underspecified) | review | isbn_duplicate | ISBN maps to several records | both review, different listed records |
| d03-75cf44c22c | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-762da472d6 | yes | author, isbn, publish_year, title | abstain (underspecified) | review | isbn_repair | damaged ISBN: repair is only a hypothesis | both review, different listed records |
| d03-7aad427028 | no | physical_format, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-7cc54b9b04 | no | author, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-850f54c394 | no | author, isbn, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis | agree |
| d03-8d23d849d7 | yes | isbn, publish_year, title | abstain (underspecified) | review | isbn_duplicate | ISBN maps to several records | both review, different listed records |
| d03-9cfe4ce6d4 | yes | author, publish_year, title | suggest | review | retrieval | a supplied field conflicts with the top candidate | agree |
| d03-9de462b511 | no | author, publish_year, title | abstain (underspecified) | review | retrieval | insufficient distinguishing evidence | both review, different listed records |
| d03-a25b4a7700 | yes | author, isbn, publish_year, title | suggest | review | isbn_repair | damaged ISBN: repair is only a hypothesis | agree |
| d03-a726c1f61b | no | author, publish_year, title | abstain (out_of_corpus) | review | retrieval | a supplied field conflicts with the top candidate | agree |
| d03-a8516126b7 | no | author, title | abstain (underspecified) | review | retrieval | undistinguished alternatives among retrieved candidates | both review, different listed records |
| d03-af83489aca | no | author, publish_year, title | abstain (out_of_corpus) | review | retrieval | a supplied field conflicts with the top candidate | agree |
| d03-afed02d380 | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-b19fe7c00d | no | author, publish_year, title | abstain (out_of_corpus) | review | retrieval | a supplied field conflicts with the top candidate | agree |
| d03-bb3fd433d8 | no | isbn, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d03-bb7313d1c4 | no | author, publish_year, title | abstain (out_of_corpus) | review | retrieval | a supplied field conflicts with the top candidate | agree |
| d03-c47a605b4c | yes | isbn, physical_format, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d03-d23ebead95 | yes | author, title | abstain (underspecified) | review | retrieval | undistinguished alternatives among retrieved candidates | both review, different listed records |
| d03-d9a6484759 | no | author, physical_format, publish_year, title | abstain (underspecified) | review | retrieval | insufficient distinguishing evidence | both review, different listed records |
| d03-df4da76948 | yes | author, title | abstain (underspecified) | review | retrieval | undistinguished alternatives among retrieved candidates | both review, different listed records |
| d03-df6f5a2f7b | no | author, physical_format, publish_year, title | suggest | review | retrieval | undistinguished alternatives among retrieved candidates | human edition, proposal review |
| d03-e1efb2be9c | no | author, publish_year, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-e54c949143 | no | author, physical_format, publish_year, title | suggest | suggest | retrieval |  | agree |
| d03-e5d6255eb8 | no | isbn, physical_format, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d03-f3d2e5552f | no | isbn, publish_year, title | suggest | suggest | isbn_exact |  | agree |
| d03-f45519bd4a | no | author, title | suggest | review | retrieval | insufficient distinguishing evidence | agree |
| d03-f48c5fe4db | no | author, physical_format, publish_year, title | suggest | review | retrieval | undistinguished alternatives among retrieved candidates | human edition, proposal review |

## Not shown on purpose

per-stratum, per-template and per-source-batch summaries of human answers: withheld until held-out labeling is complete (held-out uses the same templates and strata, so those base rates could bias held-out labels).

## Limits

- Development data, one labeler, uncalibrated policy; not held-out performance.
- 0 wrong suggestions is not proof of safety; read the Wilson upper bounds.
- Policy-development families may be optimistic and are reported separately.
- Any change motivated by these cases makes them development data for that change.
