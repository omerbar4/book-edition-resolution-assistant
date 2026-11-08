# Held-out run: deviation from the pinned procedure (owner decision 2026-11-08)

## What happened
Attempt 1 (`heldout_run_attempts.jsonl`, commit `df3dbb1`) followed the procedure pinned in
`data/freeze/freeze_manifest.json` exactly and failed at case loading. The 3 out-of-corpus
probes have families defined by the frozen held-out plan (`bera.evalkit.heldout.probe_family`),
which are not in the corpus mapping `data/corpus/v3_proposed/families.json`. The strict loader
(`bera.evalkit.families.resolve_families`) rejects any family outside the mapping it is given.
0 systems ran, 0 cases were scored, no outputs were written. No dev queue had probes, so this
path was never exercised before the freeze.

## Deviation
The run passes `--families data/eval/heldout/heldout_families_supplement.json` instead of the
default `data/corpus/v3_proposed/families.json`. Nothing else changes: tag
`bera-eval-freeze-2026-11-07-r2`, every frozen file, policy, models, thresholds, prompts, seeds,
LLM route gates and labels are unchanged.

- **Supplement:** `heldout_families_supplement.json`,
  sha256 `9716fa70374ae5a968b8a031265aefba493f70aa485ccafd42244217ac1cc65b`. It contains the
  387 corpus entries unchanged plus 2 identity entries, one per distinct probe family (the
  same-author pair shares one family, so 2 additions, not 3). Total 389.
- **Derivation:** `build_family_supplement.py` (here). Its inputs are only the pinned corpus
  mapping and the frozen queue (verified against its manifest), never labels or model outputs.
  `--check` rebuilds and compares the bytes.
- **Scope of `--families`:** it is read once in `bera.evalkit.run.main` and passed only to
  `resolve_families`, which validates the case-to-family mapping and sets `EvalCase.family`.
  `run_system` gives the resolver only `case.query`. `family` is copied into `CaseResult` and
  used only for the family-grouped bootstrap (`metrics.bootstrap_ci`) and family counts. No
  inference module (`service`, `policy`, `retrieval`, `evidence`, `features`, `ml`, `catalog`,
  `llm/`) reads families. It cannot affect retrieval, candidate selection or decisions.
- **Load validation (before the run):** all 40 cases load. The 37 in-corpus families are
  identical to resolution with the base mapping. There are exactly 39 families, and the probe
  pair is kept together (3 probes, 2 families). Only `family` differs from the saved label
  lines. The queries reaching the resolver are identical to the frozen queue.

## Exact command (attempt 2, run once from the main checkout, with the clean tree at the supplement commit)

```
uv run python -m bera.evalkit.run \
  --cases data/eval/heldout/heldout_labels.jsonl \
  --queue data/eval/heldout/heldout_queue.jsonl \
  --families data/eval/heldout/heldout_families_supplement.json \
  --split heldout --frozen-tag bera-eval-freeze-2026-11-07-r2 \
  --llm-route-evidence data/eval/llm_route_evidence_policy_v2_amended.json \
  --ml --llm-url http://127.0.0.1:8080/v1 --db var/catalog_v3.sqlite \
  --out data/eval/results/heldout40_frozen_r2
```

The local LLM is served the same way as in the dev evaluations: llama-server, Qwen3-4B-Instruct-2507
Q4_K_M, `-c 8192 -ngl 99`, 127.0.0.1:8080. Results are committed under `data/eval/results/`,
outside the post-tag allowed prefix, so the frozen-system guard refuses any later held-out run.
