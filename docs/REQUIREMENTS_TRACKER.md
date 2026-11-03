# Requirements tracker

**Statuses:**
- `verified`: implemented, and checked by automated tests and/or the browser.
- `implemented`: code exists, but its check is incomplete.
- `pending`: not built yet; authorized work.
- `blocked`: needs an approval, a download or human labels.

## Request flow

| # | Requirement | Status | Evidence / blocker |
|---|---|---|---|
| F1 | ISBN normalization, checksum, 10↔13, exact lookup | verified | `tests/unit/test_isbn.py` (property tests) |
| F1a | Duplicate ISBN mapping handled explicitly | verified | `test_duplicate_isbn_never_auto_resolves` |
| F1b | Contradictory metadata → conflict, not silent pick | verified | `test_unique_isbn_with_conflicting_format_goes_to_review` |
| F2 | Retrieval when identifiers are absent or insufficient (lexical + fuzzy) | verified | FTS5 BM25 + trigram + RRF; `test_typos_still_retrieve_the_work` |
| F2b | Embedding retrieval + hybrid | blocked | model download approval (bge-small-en-v1.5) |
| F3 | Deterministic conflict checks | verified | `features.py`, pipeline tests |
| F3b | Cross-encoder reranking | blocked | model download approval |
| F4 | LLM adjudication only for ambiguous top-k | verified (mock) | `service.py`; real local adapter pending |
| F5 | Strict output schema + evidence validation | verified | `tests/security/test_adjudication_attacks.py` |
| F6 | Suggest-or-review outcome | verified | `conservative-rules-v0` (uncalibrated) |
| F7 | Explicit local confirm/reject | verified | API tests + UI test + browser check |

## Models and serving

| # | Requirement | Status | Evidence / blocker |
|---|---|---|---|
| M1 | Project-owned provider interface | verified | `llm/provider.py` |
| M2 | Mock provider tests | verified | mock modes: cite_first, abstain, scripted, error, transport, timeout |
| M3 | Real local-provider adapter (OpenAI-compatible) | implemented | `llm/openai_compat.py`, loopback-only; tested with httpx.MockTransport; real inference blocked on GGUF download; llama.cpp `$ref` support in schema unverified |
| M4 | Model self-confidence never a threshold | verified | logged only; policy ignores it |

## Confidence and calibration

| # | Requirement | Status | Evidence / blocker |
|---|---|---|---|
| C1 | Calibrated scorer from grouped out-of-fold dev predictions | blocked | needs human-labeled dev set |
| C2 | Confidence bands with k/n + Wilson intervals | implemented | `metrics.signal_buckets` over an uncalibrated signal; calibrated bands blocked on C1 |
| C3 | LLM-override route confidence measured separately | blocked | needs dev data + real model |

## Data and evaluation

| # | Requirement | Status | Evidence / blocker |
|---|---|---|---|
| D1 | Versioned local Open Library corpus | blocked | dump download approval (13.49 GB; +4.08 GB works) |
| D1a | Ingestion and provenance tooling (streaming, strata, author resolution, manifest) | verified | `ingest/`, tests on synthetic dump-format files; gated downloader not run |
| D2 | Reproducible splits grouped by work family | verified | `evalkit/splits.py`, leakage test |
| D3 | Seeded synthetic perturbations | verified | `evalkit/perturb.py`, determinism test |
| D4 | ≥ 100 (target 120) human-labeled cases | blocked | human labeling time |
| D5 | Labeling workflow + instructions + ambiguity rules | implemented | LABELING_GUIDE.md, `evalkit/label.py` (unranked search, validator) |
| D6 | Abstention and out-of-corpus cases | implemented (tooling) | schema + exclusion verification in corpus builder; cases blocked on corpus + labeling |
| E1 | Six baselines compared | implemented | 1, 2 (+2b) run; 3–6 reported as blocked, never simulated |
| E2 | Metrics: recall@k, MRR, top-1, correct-suggestion, wrong-match, error among suggestions, abstention, correct abstention, bucket precision with n, risk-coverage, bootstrap CIs, failure categories, p50/p95 per stage, invocation rate, tokens, cost | verified | `evalkit/metrics.py` with denominator tests; engineering check run on synthetic cases |
| E3 | Dev-only tuning; frozen policy before held-out | pending | process documented in DECISION_POLICY.md |

## Security, reliability and operations

| # | Requirement | Status | Evidence / blocker |
|---|---|---|---|
| S1 | Injection tests in user input and catalog metadata | verified | security tests |
| S2 | Forged ids, fabricated citations, Unicode obfuscation | verified | security tests |
| S3 | Input, context and output limits | verified | API and adjudicator tests |
| S4 | Timeouts, bounded retries, budgets | verified (mock clock) | |
| S5 | Provider failure → review | verified | |
| S6 | Escaped UI rendering | verified | vitest + CSP header + browser |
| S7 | Local telemetry without raw text | verified | `test_traces_never_store_raw_query_text` + manual DB check |
| S8 | Offline CI regression | implemented | `.github/workflows/ci.yml` (not run: no GitHub remote by instruction); golden eval pending |
| S9 | Docker setup | pending | |
| S10 | Pin GitHub Actions to commit SHAs | pending | before any publication |
| O1 | MIT for code; separate data and model notices | verified | LICENSE, DATA_NOTICE.md, MODEL_NOTICE.md |
| O2 | AI-assistance log | implemented | docs/AI_ASSISTANCE.md |
