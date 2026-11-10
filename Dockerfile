# syntax=docker/dockerfile:1
# Base images pinned by digest (resolved 2026-11-09). The runtime stage uses Alpine: on
# Debian bookworm/trixie the system SQLite (used by Python's sqlite3, including FTS5 MATCH on
# user input) and several base packages carry unfixed HIGH/CRITICAL CVEs; python:3.12-alpine
# ships SQLite 3.53 and scanned with no HIGH/CRITICAL findings. The Node stage only builds
# the static UI and is not shipped.
#
# Public-demo image: deterministic resolver + review UI over the committed Open Library corpus
# (5,366 editions). The LLM is disabled; the catalog is built at image build time from the
# committed corpus, its sha256 is checked, and it is opened read-only at runtime. Nothing is
# written to disk at runtime; /tmp is the only location the app may use (mount it as tmpfs).
FROM node:22-bookworm-slim@sha256:5ec23b7c622b00547753bc6ffd78085dd868a68aeb41c8e0a1418f033e13d96d AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-alpine@sha256:e064671ca452259bab50e8e2c7bd896e39e9a343bb06ca25234adf6fe18d0fc7 AS app
ARG CORPUS_SHA256=cdabcf84712f29c104c11cc3e4bb640b00486ab55529ab94917666ef2e609464
ARG CORPUS_EDITIONS=5366
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_PYTHON_DOWNLOADS=never UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    HOME=/tmp BERA_VAR_DIR=/tmp/bera \
    BERA_PUBLIC_DEMO=1 BERA_LLM_PROVIDER=none \
    BERA_CATALOG_DB=/app/catalog/catalog.sqlite \
    BERA_EXPECTED_CATALOG_SHA256=${CORPUS_SHA256} \
    BERA_EXPECTED_EDITIONS=${CORPUS_EDITIONS} \
    BERA_TRUSTED_PROXY_HOPS=0
# INSTALL_ML=1 adds sentence-transformers/torch (large; not used by the public demo).
ARG INSTALL_ML=0
RUN pip install --no-cache-dir "uv==0.13.7"
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN if [ "$INSTALL_ML" = "1" ]; then uv sync --locked --no-dev --group ml; \
    else uv sync --locked --no-dev; fi
# Build the catalog from the committed corpus; refuse to build from anything else.
COPY data/corpus/v3_proposed/corpus.jsonl ./data/corpus/v3_proposed/corpus.jsonl
RUN echo "${CORPUS_SHA256}  data/corpus/v3_proposed/corpus.jsonl" | sha256sum -c - \
    && mkdir -p /app/catalog \
    && /opt/venv/bin/python -m bera.cli build-catalog \
        --fixtures data/corpus/v3_proposed/corpus.jsonl --db /app/catalog/catalog.sqlite \
    && chmod 0444 /app/catalog/catalog.sqlite && chmod 0555 /app/catalog
# Build tools are not needed at runtime: remove uv and pip from the final image.
RUN python -m pip uninstall --yes --no-input uv pip && rm -rf /tmp/* /root/.cache
COPY --from=ui /ui/dist ./frontend/dist
RUN adduser -D -H -u 10001 -s /sbin/nologin bera
USER bera
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/ready',timeout=4)"
# --no-server-header: no server identification. --no-proxy-headers: uvicorn does not rewrite
# the client address; the rate limiter reads X-Forwarded-For itself, trusting only
# BERA_TRUSTED_PROXY_HOPS proxies (0 by default = the TCP peer).
CMD ["/opt/venv/bin/python", "-m", "uvicorn", "--factory", "bera.api:create_app", \
     "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-proxy-headers"]
