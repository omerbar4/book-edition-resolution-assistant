# Remaining delivery work (after the held-out evaluation, 2026-11-08)

All of this is local work. None of it changes the frozen policy, models, prompts, thresholds,
gates or labels. Pushing, deployment and downloads each need a separate owner decision.

## README
- [ ] Replace the status block, which still says "no real evaluation result". Give the
      held-out headline with denominators and intervals: 0/40 wrong, 6/40 correct, coverage
      6/15, correct abstention 25/25, all uncalibrated. Link
      [EVALUATION_REPORT.md](EVALUATION_REPORT.md).
- [ ] Policy row: `conservative-rules-v1` → `conservative-rules-v2` (initials compatibility).
- [ ] Labeling section: describe the dev and held-out queues as they are now. The batch 02
      example and the line "held-out drafts are refused" are out of date; held-out serving
      needs `BERA_LABEL_ALLOW_HELDOUT=1`.
- [ ] Evaluation section: add the frozen held-out command, including `--families`, and say
      that the guard now refuses further held-out runs.
- [ ] Add a short "What the results show / don't show" section: retrieval is not the
      bottleneck, the LLM stays advisory, and there's no calibration.
- [ ] Update the docs index: add EVALUATION_REPORT, EVALUATION_PLAN, FREEZE and this checklist.

## Status documents
- [ ] REQUIREMENTS_TRACKER / REQUIREMENTS_AUDIT:
  - D4 → met (100 = 60 dev + 40 held-out);
  - E3 → verified (frozen r2, single run);
  - D6 → still partial (42 review cases, 15 out of corpus, against about 60);
  - E1 → verified on held-out.
- [ ] EVALUATION_PLAN: mark the milestone complete and link the report and the deviation note.
- [ ] AI_ASSISTANCE.md: add the held-out phase (labels self-reported unassisted; analysis and
      report drafted with AI assistance).

## Demo
- [ ] A script or doc for a 3–5 minute local walkthrough:
  - ISBN hit → suggestion;
  - ambiguous title → review with evidence;
  - out-of-corpus → review;
  - LLM advisory panel (needs llama-server).

  Use only dev or synthetic queries, never held-out cases.
- [ ] Screenshots or a short recording of the review UI and the labeling tab, using dev data.
- [ ] A one-page "how to read the evidence panel" note for reviewers.

## Reproducible setup
- [ ] Clean-clone dry run following README steps only, in a fresh directory. Confirm the
      `uv sync --locked`, catalog build, frontend build and test commands.
- [ ] Document rebuilding `var/catalog_v3.sqlite` from the recorded Open Library dump
      (2026-10-31): exact script, expected sha256, disk and time needed. The dump download
      itself needs owner approval.
- [ ] Document building llama.cpp (the pinned binary hash is in the freeze manifest) and the
      exact `llama-server` flags used here (`-c 8192 -ngl 99`, port 8080).
- [ ] Model fetch: confirm `scripts/fetch_models.py --approved-by-owner` reproduces the pinned
      hashes in `data/freeze/freeze_manifest.json`. That is a download, so it needs owner
      approval.
- [ ] Docker: `compose.yaml` and `Dockerfile` exist but weren't re-verified in this phase;
      building pulls base images, which needs owner approval.
- [ ] CI: `.github/workflows/ci.yml` exists but has never run (no remote, by instruction).
      Either run the same steps locally as a recorded check, or mark it explicitly as unrun.
- [ ] Fix or document the intermittent frontend test (`LabelView` "is blind-first", 1 failure
      in 8 runs).
- [ ] A one-command check that re-verifies the evaluation from committed files:
      `freeze_manifest.py verify`, `build_family_supplement.py --check`, and
      `analyze_heldout_eval.py` reproducing `analysis.json` byte for byte.

## Deferred (documented, not delivery blockers)
- Calibrated scorer (C1), opening the LLM route, the damaged-ISBN fallback, unicode-guard
  scope, the catalog-inconsistency detector, the D6 abstention target and the 120-label goal.
