# Setup verification (2026-11-08)

## Summary

| path | status |
|---|---|
| offline clean clone, existing local caches (this machine) | **verified**, with the deviations below |
| fresh online install (new machine, empty caches) | **not verified**: needs PyPI and npm network access |
| Docker build / compose | **not re-verified**: the pinned base images are not cached (see below) |
| ML smoke tests, LLM adjudication, real catalog | **not reproducible from git alone**: weights and the catalog are not in git |

## Offline clean-clone check

**Method:**
- `git clone --no-local` of `main` into a disposable scratch directory.
- `UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never`, `npm ci --offline`.
- Existing tools: Homebrew Python 3.12.13, Node v26.0.0 / npm 11.12.1, uv 0.13.7, the uv cache
  (~1.0 GB) and the npm cache.
- Nothing was downloaded.

**Results:**
- Checked at `main` `8f9d26a`; first checked at `375fcbf`, with the same results.
- The branch was checked at `936d36f`.

| step | result |
|---|---|
| `python3.12 -m venv .tools/venv && pip install uv==0.13.7` | **fails offline** ("No matching distribution"); substituted the existing uv 0.13.7 binary (deviation) |
| `uv sync --locked` (core only) | installs from cache in about 0.2 s |
| core only: `mypy` | **3 errors** (torch, numpy, sentence_transformers not found) |
| core only: `pytest` | **9 failing** (5 failures + 4 errors in ingest/selection tests: `rapidfuzz.process.cdist` needs numpy) |
| `uv sync --locked --group ml` | installs from cache |
| with ml: `ruff format --check`, `ruff check`, `mypy` | pass |
| `bera.cli build-catalog` | 30 synthetic editions |
| with ml: `pytest` | **232 passed, 3 skipped** (the ML smoke tests need weights, not in git) |
| frontend `npm ci --offline`, `typecheck`, tests, `build` | pass; 11/11 tests |
| `bera.cli serve` + `/api/health` + UI | ok; `policy_version` `conservative-rules-v2`; UI 200 |
| `demo/run_demo.py` | 6/6 expected outcomes |
| browser: demo case 2 + Confirm | suggestion shown with per-field checks; "Recorded locally … not as an evaluation label" |

**Core-install fix:** local branch `post-eval/core-install-deps` (`936d36f`, unmerged) makes
numpy a core dependency and ignores the optional ml imports in mypy. A core-only clean clone
of that branch, with torch absent, passes ruff, mypy and 232 tests (3 skipped). The branch
changes `pyproject.toml`/`uv.lock`, which the r2 freeze pins, so merging it makes
`freeze_manifest.py verify` fail on `main`. The tag keeps the evaluated state. The CI
workflow (`.github/workflows/ci.yml`, core-only sync) would currently fail on `main` for the
same reason. It has never run.

## Fresh online installation (not verified)

The README steps need network access:
- PyPI, for `pip install uv==0.13.7` and `uv sync --locked`, plus `--group ml` (torch,
  sentence-transformers);
- the npm registry, for `npm ci`.

They have not been run from empty caches on another machine. Lockfiles pin exact versions,
and `uv.lock` pins hashes.

## Artifacts that are not in git

| artifact | local size | how it was obtained | reproducing it |
|---|---|---|---|
| `models/` (bge-small, MiniLM cross-encoder, Qwen3-4B Q4_K_M GGUF) | 2.5 GB | owner-approved download, pinned in `models.lock.json` and the freeze manifest | `scripts/fetch_models.py --approved-by-owner` (download; needs approval) |
| `.tools/llama.cpp` (llama-server) | 353 MB | built locally from llama.cpp `b12081` (`8fc03767…`), Metal; binary hash in the freeze manifest | needs the llama.cpp source (download) and a local build |
| `var/catalog_v3.sqlite` | 6.6 MB | built from corpus v3_proposed (Open Library dump 2026-10-31; dumps deleted after the build) | needs the dump again (download; many GB) and `scripts/build_corpus.sh` |

Without these, a clone can run the synthetic demo and all tests except the 3 ML smoke tests.
`freeze_manifest.py verify` fails in such a clone, because it also pins the models, the
llama-server binary and the catalog. A clone cannot re-run the held-out evaluation, and
re-running is refused anyway, now that results are committed.

## Docker (not re-verified; nothing pulled)

`docker build` with pulling disabled was **not attempted**, because the required base images
are not in the local image store:

- `node:22-bookworm-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da`
- `python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337`

Even with both images present, the build steps need network access:
- `npm ci` (npm registry);
- `pip install uv==0.13.7` and `uv sync --locked` (PyPI);
- with `INSTALL_ML=1`, torch and sentence-transformers as well.

An offline build would need a populated BuildKit cache for those layers. A local `bera:local`
image (2026-11-03) exists, but it predates policy v2 and was not used as evidence. The last
verified compose run (health, resolve, UI 200, uid 10001, read-only filesystem) is from
2026-11-03.
