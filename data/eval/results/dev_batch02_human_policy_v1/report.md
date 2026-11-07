# Evaluation report

**evaluation**

Cases: 20 (human-labeled: 20)

_signal = top-1 agreements - 2*conflicts: an UNCALIBRATED ranking signal; buckets and risk-coverage use it, not a probability_

| system | status | top-1 | recall@10 | MRR | correct sugg. /N | wrong match /N | error among sugg. | correct abstain | p95 total ms |
|---|---|---|---|---|---|---|---|---|---|
| Exact identifier + fuzzy matching | ran | 1.000 (18/18) | 1.000 (18/18) | 1.0 | 0.350 (7/20) | 0.000 (0/20) | 0.000 (0/7) | 1.000 (2/2) | 29.933 |
| Lexical retrieval (FTS5 BM25) | ran | 1.000 (18/18) | 1.000 (18/18) | 1.0 | 0.350 (7/20) | 0.000 (0/20) | 0.000 (0/7) | 1.000 (2/2) | 5.995 |
| Lexical BM25 + trigram, RRF (current default) | ran | 1.000 (18/18) | 1.000 (18/18) | 1.0 | 0.350 (7/20) | 0.000 (0/20) | 0.000 (0/7) | 1.000 (2/2) | 8.649 |
| Embedding retrieval (bge-small-en-v1.5) | ran | 1.000 (18/18) | 1.000 (18/18) | 1.0 | 0.350 (7/20) | 0.000 (0/20) | 0.000 (0/7) | 1.000 (2/2) | 17.604 |
| Hybrid BM25 + trigram + embedding (RRF) | ran | 1.000 (18/18) | 1.000 (18/18) | 1.0 | 0.350 (7/20) | 0.000 (0/20) | 0.000 (0/7) | 1.000 (2/2) | 24.558 |
| Hybrid + cross-encoder reranker | ran | 1.000 (18/18) | 1.000 (18/18) | 1.0 | 0.350 (7/20) | 0.000 (0/20) | 0.000 (0/7) | 1.000 (2/2) | 54.755 |
| Hybrid + reranker + routed local LLM adjudication (advisory) | ran | 1.000 (18/18) | 1.000 (18/18) | 1.0 | 0.350 (7/20) | 0.000 (0/20) | 0.000 (0/7) | 1.000 (2/2) | 5968.151 |

Full metrics, categories, bootstrap intervals and risk-coverage points are in the JSON report.
