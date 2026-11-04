# Evaluation report

**ENGINEERING CHECK: synthetic perturbation cases on the real Open Library catalog. NOT A REAL-WORLD EVALUATION; no human labels; not calibrated.**

Cases: 300 (human-labeled: 0)

_signal = top-1 agreements - 2*conflicts: an UNCALIBRATED ranking signal; buckets and risk-coverage use it, not a probability_

| system | status | top-1 | recall@10 | MRR | correct sugg. /N | wrong match /N | error among sugg. | correct abstain | p95 total ms |
|---|---|---|---|---|---|---|---|---|---|
| Hybrid + reranker + routed local LLM adjudication (advisory) | ran | 0.994 (166/167) | 0.994 (166/167) | 0.994 | 0.343 (103/300) | 0.057 (17/300) | 0.142 (17/120) | 0.872 (116/133) | 8371.258 |

Full metrics, categories, bootstrap intervals and risk-coverage points are in the JSON report.
