# Evaluation report

**evaluation**

Cases: 60 (human-labeled: 60)

_signal = top-1 agreements - 2*conflicts: an UNCALIBRATED ranking signal; buckets and risk-coverage use it, not a probability_

| system | status | top-1 | recall@10 | MRR | correct sugg. /N | wrong match /N | error among sugg. | correct abstain | p95 total ms |
|---|---|---|---|---|---|---|---|---|---|
| Exact identifier + fuzzy matching | ran | 1.000 (44/44) | 1.000 (44/44) | 1.0 | 0.267 (16/60) | 0.000 (0/60) | 0.000 (0/16) | 1.000 (16/16) | 25.175 |
| Lexical retrieval (FTS5 BM25) | ran | 1.000 (44/44) | 1.000 (44/44) | 1.0 | 0.267 (16/60) | 0.000 (0/60) | 0.000 (0/16) | 1.000 (16/16) | 6.116 |
| Lexical BM25 + trigram, RRF (current default) | ran | 1.000 (44/44) | 1.000 (44/44) | 1.0 | 0.267 (16/60) | 0.000 (0/60) | 0.000 (0/16) | 1.000 (16/16) | 7.625 |
| Embedding retrieval (bge-small-en-v1.5) | ran | 1.000 (44/44) | 1.000 (44/44) | 1.0 | 0.267 (16/60) | 0.000 (0/60) | 0.000 (0/16) | 1.000 (16/16) | 15.136 |
| Hybrid BM25 + trigram + embedding (RRF) | ran | 1.000 (44/44) | 1.000 (44/44) | 1.0 | 0.267 (16/60) | 0.000 (0/60) | 0.000 (0/16) | 1.000 (16/16) | 19.388 |
| Hybrid + cross-encoder reranker | ran | 1.000 (44/44) | 1.000 (44/44) | 1.0 | 0.267 (16/60) | 0.000 (0/60) | 0.000 (0/16) | 1.000 (16/16) | 57.991 |
| Hybrid + reranker + routed local LLM adjudication (advisory) | ran | 1.000 (44/44) | 1.000 (44/44) | 1.0 | 0.267 (16/60) | 0.000 (0/60) | 0.000 (0/16) | 1.000 (16/16) | 7695.593 |

Full metrics, categories, bootstrap intervals and risk-coverage points are in the JSON report.
