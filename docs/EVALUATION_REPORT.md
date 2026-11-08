# Final evaluation report: held-out run (2026-11-08)

This is the single scored held-out run of the frozen system, tag
`bera-eval-freeze-2026-11-07-r2` (commit `c32f7f0`). It reports 40 human-labeled held-out
queries across 39 families, with one labeler.

- **Policy:** `conservative-rules-v2`, uncalibrated.
- **LLM route gates:** both closed, so the LLM is advisory only.
- **Scope:** decision support only. Nothing here is a calibrated probability.

Sources:
- Raw harness output: [report.json](../data/eval/results/heldout40_frozen_r2/report.json),
  [report.md](../data/eval/results/heldout40_frozen_r2/report.md) and the run log
  [run.log](../data/eval/results/heldout40_frozen_r2/run.log).
- Descriptive analysis: [analysis.json](../data/eval/results/heldout40_frozen_r2/analysis.json),
  built by `data/eval/heldout/analyze_heldout_eval.py`. It reads only the committed report, labels and
  queue, and re-runs nothing.

## 1. Integrity of the run

| item | value |
|---|---|
| labels | `data/eval/heldout/heldout_labels.jsonl`, 40/40 cases, labeler `omer`, committed unchanged (`6e2aa31`, sha256 `48978db4…`) |
| independence | owner self-report: labeled without AI assistance (`heldout_labels.provenance.jsonl`, status `independent_human_attested`, attestation `self_reported`); not independently verifiable |
| blindness | queue served with reveal `never`. No proposal, template, stratum or agreement was ever sent to the labeling UI |
| skips / exposures / practice / flags / amendments | 0 / 0 / 0 / 0 / 0 |
| queue / reserves | sha256 `bfd55711…` / `428635c8…`, byte-identical to `73a0f5d`; reserves unused |
| freeze | manifest verified; tag is an ancestor of HEAD; only `data/eval/heldout/` changed between the tag and the run |
| attempt 1 | failed at case loading: the probe families were not in `families.json`. 0 systems ran and 0 cases were scored; recorded in `heldout_run_attempts.jsonl` (`df3dbb1`) |
| deviation | attempt 2 passed `--families data/eval/heldout/heldout_families_supplement.json` (sha256 `9716fa70…`): the corpus mapping (387 entries, unchanged) plus 2 identity entries for the probe families. Grouping and validation only; the resolver never sees a family. See [RUN_PROCEDURE_DEVIATION.md](../data/eval/heldout/RUN_PROCEDURE_DEVIATION.md) |
| attempt 2 | exit 0, 7/7 configurations ran on 40/40 cases, 22:48:54–22:51:17 UTC (143 s wall time, including model loading). Not rerun |

Committing the results under `data/eval/results/` puts files outside the post-tag allowed
prefix, so the frozen-system guard now refuses any further held-out run.

## 2. What the labels contain

| | queries | families |
|---|---|---|
| all | 40 | 39 (the same-author probe pair counts as one family) |
| human chose one edition (answerable, A) | 15 | 15 |
| human chose review (U) | 25 (22 in-corpus + 3 probes) | 24 (22 in-corpus + 2 probe families) |
| review reasons | underspecified 11, out of corpus 11, contradictory 3 | |
| in-corpus queries / out-of-corpus probes | 37 / 3 | 37 / 2 |

- **Out-of-corpus labels:** 8 of the 11 "out of corpus" labels are on in-corpus queries,
  where the query as written fits no catalog record (catalog absence); the other 3 are the
  probes.
- **Comparison with dev:** the held-out set is far more review-heavy than dev (25/40 vs 17/60).
  The format/year-conflict, edition-ambiguity and missing-metadata strata produced mostly
  review labels.
- **Drafter agreement:** the human label agreed with the drafted proposal on 35/40 queries.
  That measures the drafter, not the system.

## 3. Final decisions

The final decisions were **identical across all seven configurations**:

- 1 exact + fuzzy
- 2 BM25
- 2b BM25 + trigram RRF (default)
- 3 embedding
- 4 hybrid
- 5 hybrid + reranker
- 6 hybrid + reranker + routed LLM

The conservative policy's field checks, not the retrieval method, determine the outcome, and
the LLM cannot change a decision while its route gates are closed.

Intervals below: Wilson is a 95% case-level interval. "Family bootstrap" is a 95% percentile
interval from 1000 resamples of families with the pair kept together, seed 0, the same
method as the dev reports. The harness's own bootstrap uses a different resampler and gives
[0.049, 0.275] for the first row.

| metric | k / n | value | Wilson 95% | family bootstrap 95% |
|---|---|---|---|---|
| correct suggestion / all queries | 6 / 40 (39 fam.) | 0.150 | 0.071–0.291 | 0.050–0.275 |
| **wrong match / all queries** | **0 / 40** (39 fam.) | **0.000** | 0.000–0.088 | 0.000–0.000 |
| error among suggestions | 0 / 6 | 0.000 | 0.000–0.390 | 0.000–0.000 |
| suggestion coverage on answerable | 6 / 15 (15 fam.) | 0.400 | 0.198–0.643 | 0.167–0.667 |
| correct abstention (review when human chose review) | 25 / 25 (24 fam.) | 1.000 | 0.867–1.000 | 1.000–1.000 |
| abstention rate (all queries) | 34 / 40 | 0.850 | | |
| out-of-corpus probes routed to review | 3 / 3 (2 fam.) | | | |

- **Errors:** no wrong suggestion was observed in 40 queries. That is not zero risk: with
  n = 40, the upper Wilson bound on the wrong-match rate is 8.8%. With only 6 suggestions,
  error among suggestions is barely constrained (upper bound 39%).
- **Conservative abstentions:** 9 of the 15 answerable queries went to review. By stratum:
  identifier 2, author variation 2, missing metadata 2, edition ambiguity 2, format/year
  conflict 1. One of the 9 is the only ranking failure, a missing-metadata case whose top-1
  was not the human's edition; it went to review, not to a wrong suggestion.
- **Comparison with dev (60 cases, amended; context only):**
  - correct 28/60 (0.47) vs 6/40 (0.15) here;
  - coverage on answerable 28/43 (0.65) vs 6/15 (0.40) here;
  - wrong 0/60 vs 0/40 here;
  - correct abstention 17/17 vs 25/25 here.

  Most of the drop in correct/N comes from the review-heavy label mix. Coverage on answerable
  is also lower, but with n = 15 its interval (0.20–0.64) overlaps the dev interval
  (0.50–0.78).

### By stratum (post hoc and descriptive; small n, no tests)

| stratum | queries | correct / N | coverage on answerable | correct abstention | wrong |
|---|---|---|---|---|---|
| identifier | 8 | 3 / 8 | 3 / 5 | 3 / 3 | 0 |
| author variation | 7 | 3 / 7 | 3 / 5 | 2 / 2 | 0 |
| missing metadata | 7 | 0 / 7 | 0 / 2 | 5 / 5 | 0 |
| edition ambiguity | 7 | 0 / 7 | 0 / 2 | 5 / 5 | 0 |
| format/year conflict | 8 | 0 / 8 | 0 / 1 | 7 / 7 | 0 |
| out-of-corpus probe | 3 (2 fam.) | 0 / 3 | – | 3 / 3 | 0 |

## 4. Retrieval (answerable queries only, A = 15)

| configuration | recall@1 | recall@5 | recall@10 | MRR |
|---|---|---|---|---|
| 1 exact + fuzzy | 14/15 | 15/15 | 15/15 | 0.956 |
| 2 BM25 | 14/15 | 15/15 | 15/15 | 0.956 |
| 2b BM25 + trigram RRF (default) | 14/15 | 15/15 | 15/15 | 0.956 |
| 3 embedding | 14/15 | 15/15 | 15/15 | 0.967 |
| 4 hybrid | 14/15 | 15/15 | 15/15 | 0.967 |
| 5 hybrid + reranker | 14/15 | 15/15 | 15/15 | 0.967 |
| 6 routed LLM | 14/15 | 15/15 | 15/15 | 0.967 |

- **Top-1 accuracy:** 14/15 (Wilson 0.702–0.988; family bootstrap 0.786–1.000) in every
  configuration.
- **What limits coverage:** retrieval is not the bottleneck. The human's edition is always in
  the top 5, and coverage is limited by the decision policy's conservative checks.
- **Embedding configurations:** they improve MRR only by placing the one failure higher; they
  change no top-1 result and no decision.

## 5. LLM: advisory choices vs final decisions (configuration 6 only)

The LLM is invoked only on ambiguous top-k. Its choice is recorded but can change a final
decision only through an open route gate, and both gates are closed (dev evidence: agree
4/10, override 0/0).

| | k / n |
|---|---|
| invoked | 17 / 40 (Wilson 0.285–0.578) |
| invoked on human edition / review cases | 5 / 12 |
| completed, valid response | 12 / 17 (deadline exceeded 2, evidence invalid 3) |
| LLM abstained | 1 / 12 |
| chose a candidate | 11 / 12 |
| advisory choice equals the human's edition | **2 / 11** (Wilson 0.051–0.477) |
| advisory choice on human edition cases, correct | 2 / 2 |
| chose a candidate on cases the human sent to review | 9 / 11 |
| advisory choice equals the retrieval top-1 | 10 / 11 |
| **final decisions on invoked cases** | **review 17 / 17** |
| final decisions changed vs the default configuration | **0 / 40** |

**What this shows:** the gate behaved as intended. Had the LLM been allowed to decide, at
least 9 of its 11 choices would have become suggestions on cases a human judged unresolvable,
out of corpus or contradictory. The held-out evidence supports keeping the path closed. It is
not used to change the gate, the prompt or the model.

## 6. Latency (per query, ms, Apple M5, 16 GB, local)

| configuration | total p50 | total p95 | dominant stage (p95) |
|---|---|---|---|
| 1 exact + fuzzy | 16.4 | 41.3 | retrieval 34.8 |
| 2 BM25 | 7.8 | 22.0 | checks 17.3 |
| 2b default (lexical RRF) | 5.4 | 9.1 | checks 5.2 |
| 3 embedding | 11.6 | 53.6 | retrieval 28.3 |
| 4 hybrid | 16.1 | 28.3 | retrieval 22.0 |
| 5 hybrid + reranker | 41.8 | 74.2 | rerank 45.8 |
| 6 routed LLM | 236.7 | 8,253.5 | adjudication 7,992.5 |

The p95 for configuration 6 is set by the attempt deadline; 2 of 17 invocations hit it.

## 7. Tokens and cost

- **Configuration 6 tokens:** 15,799 in total (input plus output, as recorded by the harness),
  about 929 per invocation over 17 invocations. The per-case report does not split input from
  output. Configurations 1–5 use no LLM tokens.
- **Monetary cost:** $0. All inference was local:
  - the llama-server binary built in the project;
  - Qwen3-4B-Instruct-2507 Q4_K_M, `-c 8192 -ngl 99`;
  - the bge-small embedder and the MiniLM cross-encoder.

  The harness rate is 0.0 per 1k tokens; any non-zero rate would be a hypothetical comparison.
- **Not measured:** electricity, hardware amortization, model download and build time. Each
  query's latency depends on one Apple M5 machine running one query at a time, and was not
  measured under concurrency or on other hardware.

## 8. Uncertainty and confidence bands

- The policy's confidence is **uncalibrated**; calibration is deferred (C1) for lack of
  evidence.
- The harness signal (top-1 agreements − 2 × conflicts) is a ranking signal, not a
  probability. On held-out, "top-1 is the human's edition" within each signal bucket was:
  signal 4: 3/5; signal 3: 9/15; signal 2: 1/10; signal 0: 1/8; signal −2: 0/2. These are
  over all 40 queries, including review cases.
- Used as a threshold alone, the signal is unsafe: answering at signal ≥ 3 would answer 20/40
  with risk 0.40. The policy's field checks are what keep wrong matches at 0.

## 9. Limitations

- **Labeler:** one labeler and no agreement measure; independence is self-reported.
- **Sample size:** 40 queries, 39 families, 15 answerable. Intervals are wide, and the stratum
  table is descriptive only.
- **External validity:** queries are program-drafted perturbations of catalog records plus 3
  probes, so they are not real user traffic.
- **Run deviation:** one procedural deviation (`--families` supplement); it is documented, and
  it doesn't touch inference.
- **D6 abstention target:** unmet. Human review cases total 42 (17 dev + 25 held-out), of
  which 15 are out of corpus, against a target of about 60.
- **Not established:** calibration and the validated LLM path; both are closed or deferred.

## 10. Milestone status

The evaluation milestone is **complete**:

- 100 human-reviewed eligible labels (60 dev + 40 held-out), with no skipped or disputed
  held-out cases. **99 are strictly independent final labels.** The exception is the dev
  case `d02-6463d76f7e` ("Darkwoods"): its label was amended to review (underspecified)
  after an AI-assisted review of the catalog records. The original line is preserved, and
  the amendment is an append-only record. All 40 held-out labels are used exactly as saved,
  with independence self-reported. Batch 01 (6 AI-assisted practice labels, 14 exposed
  drafts) does not count;
- the dev analysis is done;
- the full system is frozen (r2);
- the single held-out run is reported here.

Nothing was changed or re-run on the basis of held-out outcomes.
