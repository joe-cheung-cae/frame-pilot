#!/usr/bin/env bash
# Host check for leftover packaged NSIS/DMG quit+job matrix: skip is not pass on Linux.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="$repo_root/packaging/scripts/desktop-quit-job-gui.sh"
os="$(uname -s)"

if [[ "$os" != "Linux" ]]; then
  echo "desktop-quit-job-linux: this check is for Linux hosts (os=$os)" >&2
  exit 0
fi

if [[ ! -f "$script" ]]; then
  echo "missing packaging/scripts/desktop-quit-job-gui.sh" >&2
  exit 1
fi

set +e
output="$(bash "$script" --probe 2>&1)"
status=$?
set -e

printf '%s\n' "$output"

if [[ "$status" -eq 0 ]]; then
  echo "expected exit 2 from desktop-quit-job-gui.sh on $os, got 0" >&2
  exit 1
fi

if [[ "$status" -ne 2 ]]; then
  echo "expected exit 2 (skip is not pass) from desktop-quit-job-gui.sh on $os, got $status" >&2
  exit 1
fi

if [[ "$output" != *"skip is not pass"* ]]; then
  echo "expected stdout/stderr to contain 'skip is not pass'" >&2
  exit 1
fi

if printf '%s\n' "$output" | grep -E -q '^result=pass$'; then
  echo "must never print result=pass on $os" >&2
  exit 1
fi

if printf '%s\n' "$output" | grep -E -q '"result": "pass"'; then
  echo "must never write result=pass JSON on $os" >&2
  exit 1
fi

echo "desktop-quit-job-linux ok (skip is not pass, exit=$status)"
