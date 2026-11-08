# Setup verification (2026-11-08)

## Summary

| path | status |
|---|---|
| offline clean clone of `main`, core only (existing local caches) | **verified** at `9eca484`, with one deviation (uv binary) |
| fresh online install (empty uv/pip/npm caches, this machine) | **verified** at `bbc7423`: core and `--group ml` |
| Docker build / compose | **verified** at `bbc7423`: pinned base images pulled, no layer cache |
| real catalog (`var/catalog_v3.sqlite`) | **rebuilt from committed data**, byte-identical to the pinned hash; no dump needed |
| ML smoke tests, LLM adjudication | **not reproducible from git alone**: model weights and llama.cpp need downloads |

## Offline clean-clone check (`main` `9eca484`, core only)

**Method:**
- `git clone --no-local` into a disposable scratch directory.
- `UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never`, `npm ci --offline`.
- Existing tools: Homebrew Python 3.12.13, Node v26.0.0 / npm 11.12.1, uv 0.13.7, the uv cache
  (~1.0 GB) and the npm cache.
- Nothing was downloaded.

| step | result |
|---|---|
| `python3.12 -m venv .tools/venv && pip install uv==0.13.7` | **fails offline** ("No matching distribution"); substituted the existing uv 0.13.7 binary (deviation) |
| `uv sync --locked` (core only) | 33 packages from cache; **numpy 2.5.4 present; torch, transformers and sentence-transformers absent** |
| `ruff format --check`, `ruff check`, `mypy` | pass |
| `bera.cli build-catalog` | 30 synthetic editions |
| `pytest` | **232 passed, 3 skipped** (the ML smoke tests need the ml group and weights) |
| frontend `npm ci --offline`, `typecheck`, tests, `build` | pass; 11/11 tests |
| `bera.cli serve`: `/api/health`, resolve, UI | `conservative-rules-v2`; calibration "uncalibrated: human dev labeling and held-out evaluation are complete; … deferred"; UI 200 |
| `demo/run_demo.py` | 6/6 expected outcomes |

**Earlier runs:**
- At `375fcbf` and `8f9d26a`, before the dependency fix, a core-only install failed `mypy`
  (3 errors) and 9 ingestion tests (`rapidfuzz.process.cdist` needs numpy). With `--group ml`
  they passed.
- The browser check of demo case 2 and Confirm was done at `375fcbf`.
- The fix (`936d36f`, merged in `91adf72`) adds only `numpy>=2,<3` to the core dependencies,
  which has no transitive packages in `uv.lock`, plus a mypy override for the optional ml
  imports.
- In the main checkout, with the ml group and local weights, `pytest` gives 235 passed.

**CI:** `.github/workflows/ci.yml` runs this core-only path. It has never run, because there
is no remote.

## Fresh online installation (verified 2026-11-08, `bbc7423`)

**Method:** a disposable clone, with **new empty** `UV_CACHE_DIR`, `PIP_CACHE_DIR` and npm
caches, following the README exactly:
- `python3.12 -m venv .tools/venv` (existing Homebrew Python 3.12.13);
- `pip install uv==0.13.7` from PyPI;
- `uv sync --locked`;
- `npm ci` from the registry.

| step | result |
|---|---|
| `pip install uv==0.13.7`, `uv sync --locked` | ok; 134 MB downloaded into the empty uv cache; numpy present, **no torch / sentence-transformers** |
| ruff format, ruff check, mypy | pass |
| `pytest` (core) | 232 passed, 3 skipped (ML smoke tests) |
| frontend `npm ci` (registry), typecheck, tests, build | pass; 11/11 |
| `uv sync --locked --group ml` | ok; cache grew to 952 MB (torch etc. from PyPI) |
| `pytest` with ml + the existing local weights (copy-on-write clone; not re-downloaded) | **235 passed** (ML smoke tests included) |

**Not covered:**
- another operating system (beyond the Linux CI below);
- an Intel Mac;
- Python obtained another way.

## What can be rebuilt without the Open Library dumps

| artifact | in git? | rebuild without downloads? | how / status |
|---|---|---|---|
| synthetic catalog `var/catalog.sqlite` | no | **yes** | `bera.cli build-catalog` from `data/fixtures/` (verified) |
| real catalog `var/catalog_v3.sqlite` (5,366 editions) | no | **yes** | `bera.cli build-catalog --fixtures data/corpus/v3_proposed/corpus.jsonl --db var/catalog_v3.sqlite`: **byte-identical**, sha256 `2e265fa5…` = the freeze pin (verified 2026-11-08) |
| corpus `data/corpus/v3_proposed/corpus.jsonl`, `families.json`, probe audits | **yes** (3.7 MB) | committed as-is; regenerating them **needs the dumps** | two independent builds were byte-identical (`build_records/`, `reproducibility.json`); the dumps were deleted after approval |
| dev and held-out queues, reserves, manifests | yes | committed and hash-pinned | generators are deterministic from the catalog; the held-out generator runs only at the tag, once (not re-run) |
| human labels, provenance, amendments | yes | **no** (human judgments) | committed; never regenerated |
| held-out family supplement | yes | **yes** | `data/eval/heldout/build_family_supplement.py --check` (verified) |
| held-out `analysis.json` | yes | **yes** | `data/eval/heldout/analyze_heldout_eval.py`: byte-identical (verified on `main`) |
| held-out `report.json` (raw harness output) | yes | **not re-run** | the guard refuses further held-out runs; systems 1–2b need only the catalog, 3–6 need models and the LLM |
| frontend `dist/` | no | yes, from the npm cache (offline here) or the registry | `npm run build` (verified) |
| `models/` (bge-small, MiniLM, Qwen3-4B GGUF; 2.5 GB) | no | **no** | `scripts/fetch_models.py --approved-by-owner` (download; pins in `models.lock.json`) |
| `llama-server` (llama.cpp `b12081`, Metal; 353 MB tree) | no | **no** | needs the llama.cpp source (download) and a local build; binary hash pinned |
| Docker image | no | yes, with free public downloads | the pinned base images plus npm and PyPI (verified below) |

**Freeze verifier:** `scripts/freeze_manifest.py verify` checks the r2 pins. It **passes at
the tag** (checked 2026-11-08 in a temporary worktree with the same local models, catalog
and binary). It **fails on `main` by design**, because post-evaluation commits changed
pinned files. It also fails in any clone that lacks the models and binary.

## Docker (verified 2026-11-08, `bbc7423`)

Pulled the digest-pinned base images, which are free public downloads:

- `node:22-bookworm-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da`
- `python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337`

| step | result |
|---|---|
| `docker build --no-cache --pull=false .` from a clean clone | ok; every step ran (`npm ci` 176 packages, `pip install uv`, `uv sync --locked --no-dev` 20 packages); image about 84 MB, `USER bera` |
| `docker compose up -d --build` | healthcheck `healthy`; `/api/health` gives `conservative-rules-v2`, 30 synthetic editions, LLM disabled |
| UI | 200, with `content-security-policy` |
| container user / filesystem | uid 10001; writing to `/app` fails (read-only root filesystem); `no-new-privileges:true`; port bound to 127.0.0.1 only |
| `demo/run_demo.py` against the container | 6/6 expected outcomes |

The test containers, volume and images were removed afterwards. `INSTALL_ML=1` (torch in the
image) was not built.
