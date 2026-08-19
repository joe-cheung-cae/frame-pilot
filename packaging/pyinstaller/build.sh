#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

python_bin="${PYTHON:-$repo_root/.venv/bin/python}"
if [[ ! -x "$python_bin" ]]; then
  echo "Python executable not found at $python_bin" >&2
  exit 1
fi

"$python_bin" -m pip install -q pyinstaller
"$python_bin" -m PyInstaller --noconfirm --clean --distpath "$repo_root/dist" --workpath "$repo_root/build/pyinstaller" \
  "$repo_root/packaging/pyinstaller/framepilot-api.spec"

sidecar="$repo_root/dist/framepilot-api/framepilot-api"
if [[ ! -x "$sidecar" ]]; then
  echo "PyInstaller did not produce $sidecar" >&2
  exit 1
fi

echo "Built $sidecar"
bash "$repo_root/scripts/sidecar-smoke.sh"
