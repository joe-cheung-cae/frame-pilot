#!/usr/bin/env bash
set -euo pipefail

blocked_pattern='(^|/)(node_modules|\.venv|\.ruff_cache|\.mypy_cache|\.pytest_cache|\.next|\.next-e2e|test-results|playwright-report|exports|cache)(/|$)|\.(zip|sqlite|db|jpe?g|png|webp|arw|cr3|nef|dng|heic)$'

matches="$(git ls-files | rg -i "$blocked_pattern" || true)"

if [[ -n "$matches" ]]; then
  echo "Tracked generated or private release artifacts were found:" >&2
  printf '%s\n' "$matches" >&2
  echo "Remove these from Git tracking before release." >&2
  exit 1
fi

echo "No tracked generated or private release artifacts found."
