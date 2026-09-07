#!/usr/bin/env bash
# Host check for leftover macOS DMG GUI smoke: skip is not pass on non-Darwin.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="$repo_root/packaging/scripts/macos-dmg-gui-smoke.sh"
os="$(uname -s)"

if [[ "$os" == "Darwin" ]]; then
  echo "macos-dmg-gui-smoke-nondarwin: this check is for non-Darwin hosts (os=$os)" >&2
  exit 0
fi

set +e
output="$(bash "$script" 2>&1)"
status=$?
set -e

printf '%s\n' "$output"

if [[ "$status" -eq 0 ]]; then
  echo "expected non-zero exit from macos-dmg-gui-smoke.sh on $os, got 0" >&2
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

echo "macos-dmg-gui-smoke-nondarwin ok (skip is not pass, exit=$status)"
