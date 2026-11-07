# Requirements audit (2026-11-07, before the full-system freeze)

Every item in [REQUIREMENTS_TRACKER.md](REQUIREMENTS_TRACKER.md) was re-checked against the
code, tests and recorded evidence at HEAD. Automated checks at the time of the audit: 203
backend tests (including 22 security tests), 10 frontend tests, ruff, ruff format and mypy
all pass. Every test or file cited as evidence exists. The audit used no held-out data,
downloads or external services.

## Verdicts

| # | Verdict | Notes |
|---|---|---|
| F1, F1a, F1b, F2, F3, F5, F6, F7 | verified | cited tests exist and pass |
| F2b, F3b | verified (wiring) | pinned models load; on 60 dev human labels the hybrid and reranker configurations made the same decisions as lexical retrieval (top-1 44/44 in every configuration), so they show no measurable benefit at this scale |
| F4 | verified, **gate closed** | LLM adjudication runs on ambiguous top-k; the validated suggestion path is implemented as a route gate (see C3) and is closed on measured dev evidence |
| M1–M4 | verified | model self-confidence is never used |
| C1 | **deferred** | calibrated scorer: 44 answerable dev cases is far below what a reliable fit needs (planning heuristic ≥150; Platt also needs ≥20 per reliability bin). Confidence is reported as **uncalibrated** bands with k/n, case-level Wilson and family-grouped bootstrap intervals |
| C2 | implemented (uncalibrated) | `metrics.signal_buckets` over an uncalibrated signal with n and Wilson intervals |
| C3 | verified | route precision measured on dev human labels (`data/eval/llm_route_evidence.json`): agree 4/10, override 0/2; both closed |
| D1, D1a, D2, D3, D5 | verified | |
| D4 | **in progress** | 60 eligible dev labels (batch 02 + dev_final); 40 held-out pending, after the freeze. The minimum of 100 is not met yet; the preferred 120 is not pursued |
| D6 | **partially met; ~60 target unmet** | 16 dev human review cases (12 underspecified, 4 out-of-corpus); 3 verified-absent held-out probes are planned. About 60 abstention/out-of-corpus cases will not be reached |
| E1 | verified on dev | all six methods (plus the RRF default) ran on 60 dev human labels; they made identical decisions |
| E2 | verified | all metrics with explicit denominators; family-grouped intervals |
| E3 | **pending (freeze)** | dev-only work is done; the freeze and tag come next |
| S1–S7, S10 | verified | security tests pass; S4 is verified with a mock clock |
| S8 | implemented, **not executed** | CI workflow exists; never run (no remote, by instruction) |
| S9 | verified earlier, **not re-run** | Docker build not repeated in this audit (it could download base images) |
| O1, O2 | verified / implemented | |

## Deferred or unmet requirements (explicit)

1. **C1 calibrated scorer:** deferred for insufficient evidence. Uncalibrated bands are
   reported instead.
2. **Opening the validated LLM suggestion path:** implemented but closed. With target 0.95,
   about 73 consecutive correct choices would be needed. The LLM remains advisory.
3. **D6 ~60 abstention/out-of-corpus cases:** unmet (16 dev plus 3 planned held-out).
4. **D4 preferred target of 120:** not pursued; the minimum of 100 is still in progress.
5. **Catalog-inconsistency detector** (synthetic spec v2 rule 5): not implemented beyond
   duplicate ISBN mappings and field conflicts.
6. **S8 CI execution:** not run (no remote). **S9 Docker:** not re-verified in this audit.

## Must be settled before the freeze (owner decisions)

- Review flag `d02-6463d76f7e` (missing-format twin).
- Policy hypotheses from the dev analysis, each either implemented and evaluated on dev, or
  explicitly deferred: initials-consistent author matching (the largest cause of review on
  human-answerable cases), damaged-ISBN fallback to the other fields, and unicode-guard scope
  (catalog fields not supplied by the query).
- Confirm the LLM route constants (target 0.95, minimum 30). They were fixed before
  measurement and closing the gate does not depend on them; any change must be made before
  the freeze, not after seeing held-out data.
- Then freeze code, prompts, models, thresholds, retrieval settings, the route evidence file,
  the held-out generation rules and the protocol as one tagged commit. No held-out case is
  drafted before that tag.
