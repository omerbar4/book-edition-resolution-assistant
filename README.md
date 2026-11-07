# Book Edition Resolution Assistant (BERA)

Given an ISBN or an incomplete book description, BERA suggests the most likely Open Library
**edition** and routes uncertain cases to **human review**. It is decision support only: it
never creates listings, changes prices, calls external services, or makes irreversible
decisions.

> **Status.** Pipeline, local models, ingestion, labeling and the evaluation harness all
> work. **No calibrated confidence and no real evaluation result exist yet.** Both require
> human-labeled development cases, which are in progress. Results on synthetic fixtures are
> engineering checks only. See [docs/REQUIREMENTS_TRACKER.md](docs/REQUIREMENTS_TRACKER.md).

## Components

| Stage | Implementation |
|---|---|
| ISBN | normalization, checksum validation, 10↔13 conversion, exact lookup; duplicate mappings and bad-checksum repair hypotheses always go to review |
| Retrieval | SQLite FTS5 BM25, trigram (typo tolerant), `BAAI/bge-small-en-v1.5` embeddings, fused with RRF (k=60) |
| Rerank | `cross-encoder/ms-marco-MiniLM-L6-v2` (uncalibrated logits, used only for ordering) |
| Checks | deterministic field agreement/conflict checks (title, author, format, year, publisher, language, edition, study guide / box set) |
| Policy | `conservative-rules-v1`, **uncalibrated**; model output is advisory and never turns review into suggest, so the LLM method cannot yet raise suggestion coverage (validated LLM suggestion path unfinished) |
| Adjudication | Qwen3-4B-Instruct-2507 Q4_K_M via a project-built `llama-server` on 127.0.0.1; strict schema, candidate allowlist, typed evidence checks, bounded attempts and deadlines |
| UI | React review screen with local confirm/reject; blind-first labeling tab |
| Tracing | local SQLite; queries stored only as a salted HMAC |

## Quick start (Python 3.12, Node ≥ 20)

```bash
python3.12 -m venv .tools/venv && .tools/venv/bin/pip install uv==0.13.7
.tools/venv/bin/uv sync --locked                 # core only
.tools/venv/bin/uv run python -m bera.cli build-catalog   # synthetic fixtures
npm --prefix frontend ci && npm --prefix frontend run build
.tools/venv/bin/uv run python -m bera.cli serve  # http://127.0.0.1:8000
```

Optional local ML (requires owner-approved downloads; see MODEL_NOTICE.md):

```bash
.tools/venv/bin/uv sync --locked --group ml
.tools/venv/bin/uv run python scripts/fetch_models.py --approved-by-owner
```

Docker (API + UI; LLM off by default; weights never baked in):

```bash
docker compose up --build    # binds 127.0.0.1:8000, non-root, read-only filesystem
```

Labeling (development queue only; held-out drafts are refused):

```bash
BERA_CATALOG_DB=var/catalog_v3.sqlite BERA_LABEL_QUEUE=data/eval/drafts/dev_batch02.jsonl \
  BERA_LABELS=data/eval/labels/dev_batch02_labels.jsonl \
  .tools/venv/bin/uv run python -m bera.cli serve --host 127.0.0.1 --port 8000
# then open http://127.0.0.1:8000 and use the "Label dev cases" tab.
# Batch 02 is the independent batch; batch 01 (dev_batch01.jsonl + dev_labels.jsonl) is practice.
```

## Evaluation

```bash
.tools/venv/bin/uv run python -m bera.evalkit.run --cases <cases.jsonl> --split dev --out reports/x [--ml] [--llm-url http://127.0.0.1:8080/v1]
```

- Systems 1–6 are compared on identical cases. Systems whose components are missing are
  reported as blocked, never simulated.
- Held-out runs refuse unless HEAD is a clean, tagged, frozen commit.
- Protocol: [docs/EVAL_PROTOCOL.md](docs/EVAL_PROTOCOL.md). Corpus selection:
  [docs/SELECTION_PROCEDURE.md](docs/SELECTION_PROCEDURE.md).

## Docs

[decision policy](docs/DECISION_POLICY.md) · [evidence spec](docs/EVIDENCE_SPEC.md) ·
[threat model](docs/THREAT_MODEL.md) · [data card](docs/DATA_CARD.md) ·
[labeling guide](docs/LABELING_GUIDE.md) · [AI assistance log](docs/AI_ASSISTANCE.md) ·
[DATA_NOTICE](DATA_NOTICE.md) · [MODEL_NOTICE](MODEL_NOTICE.md)

## License

Project-authored code: MIT ([LICENSE](LICENSE)). Data and models have separate notices.
