#!/usr/bin/env bash
# Stage the PyInstaller one-dir sidecar into apps/desktop/src-tauri/resources/
# for Tauri bundle.resources.
#
# Why resources (not externalBin alone):
#   framepilot-api is a PyInstaller one-dir build. The executable needs its
#   sibling _internal/ (and other COLLECT outputs) beside it for _MEIPASS.
#   Tauri externalBin only copies a single binary renamed with a target triple,
#   so it cannot ship the one-dir dependency tree. Bundle the whole directory
#   as a resource and spawn resources/framepilot-api/framepilot-api[.exe].
#
# Prereq: packaging/pyinstaller/build.sh (writes dist/framepilot-api/).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
src="$repo_root/dist/framepilot-api"
dst="$repo_root/apps/desktop/src-tauri/resources/framepilot-api"

binary=""
if [[ -x "$src/framepilot-api" ]]; then
  binary="$src/framepilot-api"
elif [[ -f "$src/framepilot-api.exe" ]]; then
  binary="$src/framepilot-api.exe"
fi

if [[ ! -d "$src" || -z "$binary" ]]; then
  echo "PyInstaller one-dir output missing at $src" >&2
  echo "Run packaging/pyinstaller/build.sh first, then re-run this script." >&2
  exit 1
fi

rm -rf "$dst"
mkdir -p "$(dirname "$dst")"
cp -a "$src" "$dst"

if [[ -f "$dst/framepilot-api" ]]; then
  chmod +x "$dst/framepilot-api"
fi

# Preserve a tracked placeholder so the directory exists before the next stage.
# (gitignored contents replace .gitkeep when staged; stage output must not be committed.)
if [[ ! -e "$dst/.gitkeep" ]]; then
  : >"$dst/.gitkeep"
fi

echo "Staged sidecar → $dst"
echo "Binary: $dst/$(basename "$binary")"
