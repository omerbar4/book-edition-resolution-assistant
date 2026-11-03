# Book Edition Resolution Assistant (BERA)

Given an ISBN or an incomplete book description, BERA suggests the most likely catalog
**edition** and routes uncertain cases to **human review**. It is decision support only: it
never creates listings, changes prices, calls external services, or makes irreversible
decisions.

> **Status: vertical slice on synthetic fixtures.** All catalog records in this repository
> are invented test fixtures (`synthetic: true`). Results on them are engineering checks,
> **not** real-world evaluation results. Embedding retrieval, reranking, real LLM inference
> and calibrated confidence are **pending** and are reported as pending by the API.
> See [docs/REQUIREMENTS_TRACKER.md](docs/REQUIREMENTS_TRACKER.md).

## What works now

| Stage | State |
|---|---|
| ISBN-10/13 normalization, checksum validation, 10↔13 conversion, exact lookup | implemented, tested |
| Duplicate ISBN mappings and bad-checksum repair hypotheses | implemented, tested (always human review) |
| Lexical retrieval: SQLite FTS5 BM25 + trigram (typo tolerant), fused with RRF | implemented, tested |
| Deterministic field checks (title, author, format, year, publisher, language, edition, study guide / box set) | implemented, tested |
| Conservative rule policy `conservative-rules-v0` (uncalibrated) | implemented, tested |
| Provider interface, mock adjudication, strict schema, candidate allowlist, typed evidence checks | implemented, tested |
| Bounded attempts / deadlines / token budgets | implemented, tested with a mock |
| Review UI with local confirm/reject | implemented, tested |
| Local tracing with HMAC'd queries (no raw text) | implemented, tested |
| Embeddings, cross-encoder reranker, real local LLM, calibration | **pending**: needs approved downloads + human labels |

## Quick start (macOS/Linux, Python 3.12, Node ≥ 20)

```bash
# 1. Python env (uv is installed into a project-local tools venv; nothing global)
python3.12 -m venv .tools/venv && .tools/venv/bin/pip install uv==0.13.7
.tools/venv/bin/uv sync --locked

# 2. Build the local catalog from the synthetic fixtures
.tools/venv/bin/uv run python -m bera.cli build-catalog

# 3. Build the UI and serve API + UI on http://127.0.0.1:8000
npm --prefix frontend ci && npm --prefix frontend run build
.tools/venv/bin/uv run python -m bera.cli serve
```

For UI development use `npm --prefix frontend run dev` (http://127.0.0.1:5173, proxies `/api`
to port 8000).

Environment variables: `BERA_LLM_PROVIDER=none|mock` (default `none`; `mock` is a test
double, not a model), `BERA_VAR_DIR` (default `./var`, git-ignored: catalog DB, traces,
feedback, HMAC salt).

## Checks

```bash
.tools/venv/bin/uv run ruff format --check . && .tools/venv/bin/uv run ruff check .
.tools/venv/bin/uv run mypy
.tools/venv/bin/uv run pytest
npm --prefix frontend run typecheck && npm --prefix frontend test
```

## Request flow

1. Normalize untrusted input (NFKC, length limits); flag hidden or bidi Unicode, never delete it.
2. ISBN: checksum, 10↔13, exact lookup. 1 hit → check fields; >1 hit → duplicate → review;
   bad checksum → repair *hypotheses* → review.
3. Retrieval when the ISBN is absent or insufficient: FTS5 BM25 + trigram, fused with RRF (k=60).
4. Deterministic field checks; candidates are ordered by agreements minus 2×conflicts.
5. Policy: suggest only on a unique, non-contradicted, sufficiently specific match.
6. Ambiguous cases → optional adjudication (advisory only in v0) with strict validation.
7. Local confirm/reject feedback, stored apart from benchmark labels.

Docs: [decision policy](docs/DECISION_POLICY.md) · [evidence spec](docs/EVIDENCE_SPEC.md) ·
[threat model](docs/THREAT_MODEL.md) · [data card](docs/DATA_CARD.md) ·
[AI assistance log](docs/AI_ASSISTANCE.md) · [DATA_NOTICE](DATA_NOTICE.md) ·
[MODEL_NOTICE](MODEL_NOTICE.md)

## License

Project-authored code: MIT ([LICENSE](LICENSE)). Data and models have separate notices.
