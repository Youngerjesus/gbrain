#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-promptfooconfig.yaml}"
OUT_DIR="${2:-.runtime/promptfoo}"
LABEL="${3:-eval}"

if [[ $# -gt 0 ]]; then shift; fi
if [[ $# -gt 0 ]]; then shift; fi
if [[ $# -gt 0 ]]; then shift; fi
EXTRA_ARGS=("$@")

if [[ ! -f "$CONFIG" ]]; then
  echo "promptfoo config not found: $CONFIG" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SAFE_LABEL="$(printf '%s' "$LABEL" | tr -c 'A-Za-z0-9._-' '-')"
RUN_BASENAME="$STAMP-$SAFE_LABEL"

mkdir -p "$OUT_DIR"

RUN_DIR=""
for suffix in "" "-1" "-2" "-3" "-4" "-5" "-6" "-7" "-8" "-9"; do
  candidate="$OUT_DIR/$RUN_BASENAME$suffix"
  if mkdir "$candidate" 2>/dev/null; then
    RUN_DIR="$candidate"
    break
  fi
done

if [[ -z "$RUN_DIR" ]]; then
  echo "could not create a unique promptfoo result directory under: $OUT_DIR" >&2
  exit 3
fi

echo "Writing promptfoo results to $RUN_DIR" >&2

npx promptfoo@latest eval \
  --config "$CONFIG" \
  --no-share \
  --output "$RUN_DIR/results.json" \
  --output "$RUN_DIR/report.html" \
  "${EXTRA_ARGS[@]}"
