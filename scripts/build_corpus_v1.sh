#!/usr/bin/env bash
# Build corpus v1 twice from the verified dumps and require identical outputs.
# Usage: scripts/build_corpus_v1.sh   (run from anywhere; uses the repo root)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
D=downloads
ARGS=(--editions "$D/ol_dump_editions_2026-10-31.txt.gz"
      --authors "$D/ol_dump_authors_2026-10-31.txt.gz"
      --redirects "$D/ol_dump_redirects_2026-10-31.txt.gz"
      --human-seeds data/selection/seed_list_v1.jsonl
      --exclusions data/selection/exclusions_v1.jsonl
      --config data/selection/selection_config_v1.json
      --seed 20261103 --source-label openlibrary-dump-2026-10-31)
mkdir -p var
rm -f var/scratch_v1_a.sqlite var/scratch_v1_b.sqlite
UV="$ROOT/.tools/venv/bin/uv"
echo "build A start $(date -u +%FT%TZ)"
"$UV" run python -m bera.ingest.corpus "${ARGS[@]}" --out data/corpus/v1 --scratch var/scratch_v1_a.sqlite
echo "build B start $(date -u +%FT%TZ)"
"$UV" run python -m bera.ingest.corpus "${ARGS[@]}" --out var/corpus_check/v1b --scratch var/scratch_v1_b.sqlite
A=$(python3 -I -c "import json;print(json.load(open('data/corpus/v1/manifest.json'))['output']['sha256'])")
B=$(python3 -I -c "import json;print(json.load(open('var/corpus_check/v1b/manifest.json'))['output']['sha256'])")
echo "A=$A"; echo "B=$B"
[ "$A" = "$B" ] && echo "REPRODUCIBLE" || { echo "NOT REPRODUCIBLE"; exit 2; }
rm -f var/scratch_v1_a.sqlite var/scratch_v1_b.sqlite
echo "done $(date -u +%FT%TZ)"
