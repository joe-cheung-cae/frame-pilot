#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

if [[ -n "${PYTHON:-}" ]]; then
  python_bin="$PYTHON"
elif [[ -x "$repo_root/.venv/bin/python" ]]; then
  python_bin="$repo_root/.venv/bin/python"
elif [[ -f "$repo_root/.venv/Scripts/python.exe" ]]; then
  python_bin="$repo_root/.venv/Scripts/python.exe"
else
  echo "Python executable not found (set PYTHON or create .venv)" >&2
  exit 1
fi

if [[ ! -x "$python_bin" && ! -f "$python_bin" ]]; then
  echo "Python executable not found at $python_bin" >&2
  exit 1
fi

"$python_bin" -m pip install -q pyinstaller
"$python_bin" -m PyInstaller --noconfirm --clean --distpath "$repo_root/dist" --workpath "$repo_root/build/pyinstaller" \
  "$repo_root/packaging/pyinstaller/framepilot-api.spec"

sidecar=""
if [[ -x "$repo_root/dist/framepilot-api/framepilot-api" ]]; then
  sidecar="$repo_root/dist/framepilot-api/framepilot-api"
elif [[ -f "$repo_root/dist/framepilot-api/framepilot-api.exe" ]]; then
  sidecar="$repo_root/dist/framepilot-api/framepilot-api.exe"
fi

if [[ -z "$sidecar" ]]; then
  echo "PyInstaller did not produce dist/framepilot-api/framepilot-api[.exe]" >&2
  exit 1
fi

echo "Built $sidecar"
bash "$repo_root/scripts/sidecar-smoke.sh"
