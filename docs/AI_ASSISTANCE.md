# AI-assistance log

This project is built with an AI coding assistant (Claude, via Claude Code). This log records
what was AI-assisted so that readers can judge the work honestly.

| Date | Work | AI role | Human role / verification |
|---|---|---|---|
| 2026-11-03 | Phase 0 plan and amendments (architecture, licensing review, evaluation protocol) | drafted the plan; researched primary sources | Omer Bar reviewed it, requested five corrections (calibration, licensing, corpus, evidence, operations), then approved |
| 2026-11-03 | Vertical slice: backend, synthetic fixtures, policy, mock adjudication, UI, tests, docs | wrote the code, tests and docs | the automated checks listed in the commit message; browser check of the UI against a local server |
| 2026-11-03 | Local adapter, ingestion tooling, eval kit (perturbations, splits, labeling tools, metrics, harness) | wrote code, tests and docs | automated checks; harness run on synthetic cases (engineering check only). The perturbation generator was changed after the first run (ISBN dropped in about half of cases) because ISBN-bearing cases made retrieval irrelevant; this is logged because it was a change made after seeing output. |
| 2026-11-03 | Model/dump download tooling, ML + llama.cpp integration, Docker, CI pinning, golden regression, selection v1 lists, labeling UI | wrote code, docs, and the proposed public seed/probe lists from general knowledge | owner approved downloads; seed list v1 pending owner review; automated checks and live local-model smoke runs |

Rules:
- AI-generated queries or labels do **not** count as human-labeled until a human reviews and
  labels them; such rows carry `origin=ai_drafted_human_labeled`.
- No code, data, prompts or configuration were copied from other private projects.
- Metrics are only ever reported from actual runs; synthetic-fixture results are labeled as
  engineering checks.
