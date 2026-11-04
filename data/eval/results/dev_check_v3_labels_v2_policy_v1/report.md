# Evaluation report

**ENGINEERING CHECK: synthetic perturbation cases on the real Open Library catalog. NOT A REAL-WORLD EVALUATION; no human labels; not calibrated.**

Cases: 300 (human-labeled: 0)

_signal = top-1 agreements - 2*conflicts: an UNCALIBRATED ranking signal; buckets and risk-coverage use it, not a probability_

| system | status | top-1 | recall@10 | MRR | correct sugg. /N | wrong match /N | error among sugg. | correct abstain | p95 total ms |
|---|---|---|---|---|---|---|---|---|---|
| Exact identifier + fuzzy matching | ran | 0.994 (178/179) | 0.994 (178/179) | 0.9944 | 0.383 (115/300) | 0.000 (0/300) | 0.000 (0/115) | 1.000 (121/121) | 20.939 |
| Lexical retrieval (FTS5 BM25) | ran | 0.989 (177/179) | 0.994 (178/179) | 0.9902 | 0.383 (115/300) | 0.000 (0/300) | 0.000 (0/115) | 1.000 (121/121) | 8.118 |
| Lexical BM25 + trigram, RRF (current default) | ran | 0.983 (176/179) | 0.989 (177/179) | 0.9846 | 0.383 (115/300) | 0.000 (0/300) | 0.000 (0/115) | 1.000 (121/121) | 10.686 |
| Embedding retrieval (bge-small-en-v1.5) | ran | 0.989 (177/179) | 0.994 (178/179) | 0.9902 | 0.383 (115/300) | 0.000 (0/300) | 0.000 (0/115) | 1.000 (121/121) | 17.204 |
| Hybrid BM25 + trigram + embedding (RRF) | ran | 0.989 (177/179) | 0.994 (178/179) | 0.9902 | 0.383 (115/300) | 0.000 (0/300) | 0.000 (0/115) | 1.000 (121/121) | 19.595 |
| Hybrid + cross-encoder reranker | ran | 0.994 (178/179) | 0.994 (178/179) | 0.9944 | 0.383 (115/300) | 0.000 (0/300) | 0.000 (0/115) | 1.000 (121/121) | 50.911 |
| Hybrid + reranker + routed local LLM adjudication (advisory) | ran | 0.994 (178/179) | 0.994 (178/179) | 0.9944 | 0.383 (115/300) | 0.000 (0/300) | 0.000 (0/115) | 1.000 (121/121) | 8499.236 |

Full metrics, categories, bootstrap intervals and risk-coverage points are in the JSON report.
