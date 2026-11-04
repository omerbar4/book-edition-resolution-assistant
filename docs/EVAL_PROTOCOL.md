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
