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
abstain cases. Correct abstention ranged from 0.865 to 0.880. The local LLM was invoked on 140/300 cases: 102 completed,
28 hit the deadline and 10 had invalid evidence. Its advisory choice was in the gold set for
91/93 of the completed adjudications. These numbers show that the pipeline runs end to end on
real catalog data. They say nothing about accuracy on real user inputs.
