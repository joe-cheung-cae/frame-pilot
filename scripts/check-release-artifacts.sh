#!/usr/bin/env bash
set -euo pipefail

if ! command -v rg > /dev/null 2>&1; then
  rg() {
    grep -E "$@"
  }
fi

blocked_pattern='(^|/)(node_modules|\.venv|\.ruff_cache|\.mypy_cache|\.pytest_cache|\.next|\.next-e2e|test-results|playwright-report|exports|cache|\.framepilot-validation|\.local-validation|\.local-validation-notes)(/|$)|\.(zip|sqlite|db|jpe?g|png|webp|arw|cr3|nef|dng|heic)$'
allowed_pattern='^apps/desktop/src-tauri/icons/[^/]+\.(png|ico|icns)$'

matches="$(git ls-files | rg -i "$blocked_pattern" || true)"

if [[ -n "$matches" ]]; then
  matches="$(printf '%s\n' "$matches" | rg -v "$allowed_pattern" || true)"
fi

if [[ -n "$matches" ]]; then
  echo "Tracked generated or private release artifacts were found:" >&2
  printf '%s\n' "$matches" >&2
  echo "Remove these from Git tracking before release." >&2
  exit 1
fi

echo "No tracked generated or private release artifacts found."
