# Evaluation report

**ENGINEERING CHECK: synthetic perturbation cases on the real Open Library catalog. NOT A REAL-WORLD EVALUATION; no human labels; not calibrated.**

Cases: 300 (human-labeled: 0)

_signal = top-1 agreements - 2*conflicts: an UNCALIBRATED ranking signal; buckets and risk-coverage use it, not a probability_

| system | status | top-1 | recall@10 | MRR | correct sugg. /N | wrong match /N | error among sugg. | correct abstain | p95 total ms |
|---|---|---|---|---|---|---|---|---|---|
| Exact identifier + fuzzy matching | ran | 0.994 (166/167) | 0.994 (166/167) | 0.994 | 0.343 (103/300) | 0.053 (16/300) | 0.135 (16/119) | 0.880 (117/133) | 17.225 |
| Lexical retrieval (FTS5 BM25) | ran | 0.988 (165/167) | 0.994 (166/167) | 0.9895 | 0.343 (103/300) | 0.057 (17/300) | 0.142 (17/120) | 0.872 (116/133) | 5.02 |
| Lexical BM25 + trigram, RRF (current default) | ran | 0.982 (164/167) | 0.988 (165/167) | 0.9835 | 0.343 (103/300) | 0.057 (17/300) | 0.142 (17/120) | 0.872 (116/133) | 6.552 |
| Embedding retrieval (bge-small-en-v1.5) | ran | 0.988 (165/167) | 0.994 (166/167) | 0.9895 | 0.343 (103/300) | 0.060 (18/300) | 0.149 (18/121) | 0.865 (115/133) | 14.417 |
| Hybrid BM25 + trigram + embedding (RRF) | ran | 0.988 (165/167) | 0.994 (166/167) | 0.9895 | 0.343 (103/300) | 0.057 (17/300) | 0.142 (17/120) | 0.872 (116/133) | 19.431 |
| Hybrid + cross-encoder reranker | ran | 0.994 (166/167) | 0.994 (166/167) | 0.994 | 0.343 (103/300) | 0.057 (17/300) | 0.142 (17/120) | 0.872 (116/133) | 51.72 |
| Hybrid + reranker + routed local LLM adjudication (advisory) | ran | 0.994 (166/167) | 0.994 (166/167) | 0.994 | 0.343 (103/300) | 0.057 (17/300) | 0.142 (17/120) | 0.872 (116/133) | 8439.518 |

Full metrics, categories, bootstrap intervals and risk-coverage points are in the JSON report.
