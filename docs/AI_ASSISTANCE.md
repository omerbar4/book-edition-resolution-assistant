# AI-assistance log

This project is built with an AI coding assistant (Claude, via Claude Code). This log records
what was AI-assisted so that readers can judge the work honestly.

| Date | Work | AI role | Human role / verification |
|---|---|---|---|
| 2026-11-03 | Phase 0 plan and amendments (architecture, licensing review, evaluation protocol) | drafted the plan; researched primary sources | Omer Bar reviewed it, requested five corrections (calibration, licensing, corpus, evidence, operations), then approved |
| 2026-11-03 | Vertical slice: backend, synthetic fixtures, policy, mock adjudication, UI, tests, docs | wrote the code, tests and docs | the automated checks listed in the commit message; browser check of the UI against a local server |
| 2026-11-03 | Local adapter, ingestion tooling, eval kit (perturbations, splits, labeling tools, metrics, harness) | wrote code, tests and docs | automated checks; harness run on synthetic cases (engineering check only). The perturbation generator was changed after the first run (ISBN dropped in about half of cases) because ISBN-bearing cases made retrieval irrelevant; this is logged because it was a change made after seeing output. |
| 2026-11-03 | Model/dump download tooling, ML + llama.cpp integration, Docker, CI pinning, golden regression, selection v1 lists, labeling UI | wrote code, docs, and the proposed public seed/probe lists from general knowledge | owner approved downloads; seed list v1 pending owner review; automated checks and live local-model smoke runs |
| 2026-11-04 | Corpus v3_proposed build and audit, ISBN rule, synthetic label spec v2, policy `conservative-rules-v1`, labeling sidecars | wrote code, analyses and docs | owner approved the corpus build and decided the ISBN and unknown-field rules; checks reproduced builds byte for byte |
| 2026-11-04 to 11-07 | Batch 01 dev labels (practice) | 6 labels were AI-assisted practice: 2 recorded as AI-assisted, 4 reviewed with ChatGPT; proposals were revealed at submission | recorded as `practice_ai_assisted`; 14 drafts recorded as exposed before labeling (mostly template/outcome correlation); none of batch 01 counts |
| 2026-11-07 | Dev queues (batch 02, dev final), stratified drafter, label spec v3, dev evaluation, policy `conservative-rules-v2` (initials), LLM route gate, freeze manifest and tag r2, held-out generator | wrote code, tests, analyses and docs; drafted proposals were hidden from the labeler until each batch was complete | owner labeled 60 dev cases (self-reported independent), chose the policy change and the held-out family rule, and approved the freeze |
| 2026-11-07 | Ruling on dev case `d02-6463d76f7e` ("Darkwoods") | presented the query and the uncontradicted catalog records, without scores or recommendations | owner amended the label to review (underspecified); the original line is preserved; this final label is counted as human reviewed but **not strictly independent** |
| 2026-11-08 | Held-out labeling (40 cases) | served the blind queue (reveal never); never showed proposals or answers | owner labeled all 40 and self-reports no AI assistance (`heldout_labels.provenance.jsonl`) |
| 2026-11-08 | Held-out run, family supplement and deviation note, analysis, evaluation report, README/status/demo/setup docs, frontend test-timeout fix, core-install fix branch | ran the frozen harness once (after a load failure with 0 cases scored), wrote the analysis script, documents and fixes | owner approved the deviation (option 1) and the delivery work; outputs are committed as written; nothing was tuned on held-out results |

Rules:
- AI-generated queries or labels do **not** count as human-labeled until a human reviews and
  labels them; such rows carry `origin=ai_drafted_human_labeled`.
- No code, data, prompts or configuration were copied from other private projects.
- Metrics are only ever reported from actual runs; synthetic-fixture results are labeled as
  engineering checks.
