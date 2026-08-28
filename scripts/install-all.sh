#!/usr/bin/env bash
# Cross-platform workspace install (Linux/macOS/Windows Git Bash).
# Creates .venv and installs API + npm packages for web and desktop.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python_bin="${PYTHON:-}"
if [[ -z "$python_bin" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python_bin="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    python_bin="$(command -v python)"
  else
    echo "python3/python not found on PATH" >&2
    exit 1
  fi
fi

"$python_bin" -m venv .venv

venv_python=""
if [[ -x "$repo_root/.venv/Scripts/python.exe" ]]; then
  venv_python="$repo_root/.venv/Scripts/python.exe"
elif [[ -x "$repo_root/.venv/bin/python" ]]; then
  venv_python="$repo_root/.venv/bin/python"
else
  echo "venv python not found under .venv/bin or .venv/Scripts" >&2
  exit 1
fi

"$venv_python" -m pip install -e "apps/api[dev]"
npm install
npm --prefix apps/web install
npm --prefix apps/desktop install
