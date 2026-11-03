# syntax=docker/dockerfile:1
# Base images pinned by digest (resolved 2026-11-03).
FROM node:22-bookworm-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337 AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv BERA_VAR_DIR=/var/bera
# INSTALL_ML=1 adds sentence-transformers/torch (large). Weights are never baked in:
# mount ./models read-only at /app/models.
ARG INSTALL_ML=0
RUN pip install --no-cache-dir "uv==0.13.7"
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN if [ "$INSTALL_ML" = "1" ]; then uv sync --locked --no-dev --group ml; \
    else uv sync --locked --no-dev; fi
COPY data/fixtures ./data/fixtures
COPY --from=ui /ui/dist ./frontend/dist
RUN useradd --uid 10001 --create-home bera && mkdir -p /var/bera && chown bera /var/bera
USER bera
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=4)"
CMD ["sh", "-c", "[ -f \"$BERA_VAR_DIR/catalog.sqlite\" ] || /opt/venv/bin/python -m bera.cli build-catalog; exec /opt/venv/bin/python -m uvicorn --factory bera.api:create_app --host 0.0.0.0 --port 8000"]
