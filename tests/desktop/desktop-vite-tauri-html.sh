#!/usr/bin/env bash
# Packaged WebView must load the Vite SPA. Absolute /assets + crossorigin CORS-fails
# on the Tauri custom protocol (GHA 34132759503: page_load + qa=init, no idle).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
vite_config="$repo_root/apps/desktop/vite.config.ts"
helper="$repo_root/apps/desktop/stripCrossOriginHtml.ts"

if [[ ! -f "$vite_config" ]]; then
  echo "missing $vite_config" >&2
  exit 1
fi
if [[ ! -f "$helper" ]]; then
  echo "missing $helper" >&2
  exit 1
fi

if ! grep -E -q 'base:[[:space:]]*["'"'"']\./["'"'"']' "$vite_config"; then
  echo "apps/desktop/vite.config.ts must set base: \"./\"" >&2
  exit 1
fi
if ! grep -F -q "stripCrossOriginHtml" "$vite_config"; then
  echo "apps/desktop/vite.config.ts must run stripCrossOriginHtml on index.html" >&2
  exit 1
fi

echo "desktop-vite-tauri-html ok (relative base, strip crossorigin)"
