# Setup verification (2026-11-08)

## Summary

| path | status |
|---|---|
| offline clean clone of `main`, core only (existing local caches) | **verified** at `9eca484`, with one deviation (uv binary) |
| fresh online install (new machine, empty caches) | **not verified**: needs PyPI and npm network access |
| Docker build / compose | **not re-verified**: the pinned base images are not cached (see below) |
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

## Fresh online installation (not verified)

The README steps need network access:
- PyPI, for `pip install uv==0.13.7` and `uv sync --locked`, plus `--group ml` (torch,
  sentence-transformers);
- the npm registry, for `npm ci`.

They have not been run from empty caches on another machine. Lockfiles pin exact versions,
and `uv.lock` pins hashes.

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
| Docker image | no | **no** | needs the base images and package registries (below) |

**Freeze verifier:** `scripts/freeze_manifest.py verify` checks the r2 pins. It **passes at
the tag** (checked 2026-11-08 in a temporary worktree with the same local models, catalog
and binary). It **fails on `main` by design**, because post-evaluation commits changed
pinned files. It also fails in any clone that lacks the models and binary.

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
