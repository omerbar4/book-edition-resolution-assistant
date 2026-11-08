# Evaluation report

**evaluation**

Cases: 40 (human-labeled: 40)

_signal = top-1 agreements - 2*conflicts: an UNCALIBRATED ranking signal; buckets and risk-coverage use it, not a probability_

| system | status | top-1 | recall@10 | MRR | correct sugg. /N | wrong match /N | error among sugg. | correct abstain | p95 total ms |
|---|---|---|---|---|---|---|---|---|---|
| Exact identifier + fuzzy matching | ran | 0.933 (14/15) | 1.000 (15/15) | 0.9556 | 0.150 (6/40) | 0.000 (0/40) | 0.000 (0/6) | 1.000 (25/25) | 41.306 |
| Lexical retrieval (FTS5 BM25) | ran | 0.933 (14/15) | 1.000 (15/15) | 0.9556 | 0.150 (6/40) | 0.000 (0/40) | 0.000 (0/6) | 1.000 (25/25) | 21.995 |
| Lexical BM25 + trigram, RRF (current default) | ran | 0.933 (14/15) | 1.000 (15/15) | 0.9556 | 0.150 (6/40) | 0.000 (0/40) | 0.000 (0/6) | 1.000 (25/25) | 9.09 |
| Embedding retrieval (bge-small-en-v1.5) | ran | 0.933 (14/15) | 1.000 (15/15) | 0.9667 | 0.150 (6/40) | 0.000 (0/40) | 0.000 (0/6) | 1.000 (25/25) | 53.621 |
| Hybrid BM25 + trigram + embedding (RRF) | ran | 0.933 (14/15) | 1.000 (15/15) | 0.9667 | 0.150 (6/40) | 0.000 (0/40) | 0.000 (0/6) | 1.000 (25/25) | 28.347 |
| Hybrid + cross-encoder reranker | ran | 0.933 (14/15) | 1.000 (15/15) | 0.9667 | 0.150 (6/40) | 0.000 (0/40) | 0.000 (0/6) | 1.000 (25/25) | 74.152 |
| Hybrid + reranker + routed local LLM adjudication (advisory) | ran | 0.933 (14/15) | 1.000 (15/15) | 0.9667 | 0.150 (6/40) | 0.000 (0/40) | 0.000 (0/6) | 1.000 (25/25) | 8253.486 |

Full metrics, categories, bootstrap intervals and risk-coverage points are in the JSON report.
