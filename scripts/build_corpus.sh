#!/usr/bin/env bash
# Usage:
#   scripts/build_corpus.sh preview <version>   # pass 1 + selection only; no corpus written
#   scripts/build_corpus.sh reanalyze <version> # preview again from the existing pass-1 scratch
#   scripts/build_corpus.sh build   <version>   # two full builds + hash comparison
# A full build REQUIRES data/selection/APPROVED_<version>.txt, written by the owner.
# A checksum freezes a configuration; it is not approval.
set -euo pipefail
MODE="${1:?preview|build}"; V="${2:?version, e.g. v2_proposed}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
CFG="data/selection/selection_config_${V}.json"
SEEDS=$(python3 -I -c "import json;print(json.load(open('$CFG'))['seed_list'])")
EXCL=$(python3 -I -c "import json;print(json.load(open('$CFG'))['exclusions'])")
SEED=$(python3 -I -c "import json;print(json.load(open('$CFG'))['seed'])")
D=downloads
ARGS=(--editions "$D/ol_dump_editions_2026-10-31.txt.gz"
      --authors "$D/ol_dump_authors_2026-10-31.txt.gz"
      --redirects "$D/ol_dump_redirects_2026-10-31.txt.gz"
      --human-seeds "$SEEDS" --exclusions "$EXCL" --config "$CFG"
      --seed "$SEED" --source-label openlibrary-dump-2026-10-31)
UV="$ROOT/.tools/venv/bin/uv"; mkdir -p var
if [ "$MODE" = reanalyze ]; then  # preview again from the existing pass-1 scratch DB
  "$UV" run python -m bera.ingest.corpus "${ARGS[@]}" --preview-only --reuse-scratch \
    --out "var/selection_preview/${V}" --scratch "var/scratch_${V}_preview.sqlite"
  echo "PROVISIONAL preview re-analyzed into var/selection_preview/${V}/ (not a corpus; not approved)"
  exit 0
fi
if [ "$MODE" = preview ]; then
  rm -f "var/scratch_${V}_preview.sqlite"
  "$UV" run python -m bera.ingest.corpus "${ARGS[@]}" --preview-only \
    --out "var/selection_preview/${V}" --scratch "var/scratch_${V}_preview.sqlite"
  echo "PROVISIONAL preview written to var/selection_preview/${V}/ (not a corpus; not approved)"
  exit 0
fi
[ -f "data/selection/APPROVED_${V}.txt" ] || { echo "refusing: no owner approval file data/selection/APPROVED_${V}.txt"; exit 3; }
for run in a b; do
  rm -f "var/scratch_${V}_${run}.sqlite"
  OUT=$([ "$run" = a ] && echo "data/corpus/${V}" || echo "var/corpus_check/${V}_b")
  "$UV" run python -m bera.ingest.corpus "${ARGS[@]}" --out "$OUT" --scratch "var/scratch_${V}_${run}.sqlite"
done
A=$(python3 -I -c "import json;print(json.load(open('data/corpus/${V}/manifest.json'))['output']['sha256'])")
B=$(python3 -I -c "import json;print(json.load(open('var/corpus_check/${V}_b/manifest.json'))['output']['sha256'])")
echo "A=$A"; echo "B=$B"; [ "$A" = "$B" ] && echo REPRODUCIBLE || { echo "NOT REPRODUCIBLE"; exit 2; }
