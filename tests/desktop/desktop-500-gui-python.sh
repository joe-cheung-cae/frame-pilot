#!/usr/bin/env bash
# Rust-free check: shipped desktop-500-gui.sh prefers .venv/Scripts/python.exe.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
shipped="$repo_root/packaging/scripts/desktop-500-gui.sh"

if [[ ! -f "$shipped" ]]; then
  echo "missing packaging/scripts/desktop-500-gui.sh" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

mkdir -p "$tmpdir/packaging/scripts" "$tmpdir/.venv/Scripts" "$tmpdir/.venv/bin"
cp "$shipped" "$tmpdir/packaging/scripts/desktop-500-gui.sh"
chmod +x "$tmpdir/packaging/scripts/desktop-500-gui.sh"

# Both Windows and POSIX venv layouts exist; Scripts must win when PYTHON is unset.
printf '%s\n' '#!/bin/sh' 'echo fake-scripts' > "$tmpdir/.venv/Scripts/python.exe"
printf '%s\n' '#!/bin/sh' 'echo fake-bin' > "$tmpdir/.venv/bin/python"
chmod +x "$tmpdir/.venv/Scripts/python.exe" "$tmpdir/.venv/bin/python"

harness="$tmpdir/packaging/scripts/desktop-500-gui.sh"
unset PYTHON || true

set +e
resolved="$(env -u PYTHON bash "$harness" --resolve-python 2>"$tmpdir/resolve.err")"
status=$?
set -e

if [[ "$status" -ne 0 ]]; then
  echo "--resolve-python exited $status" >&2
  cat "$tmpdir/resolve.err" >&2 || true
  exit 1
fi

expected="$tmpdir/.venv/Scripts/python.exe"
if [[ "$resolved" != "$expected" ]]; then
  echo "expected --resolve-python to prefer Scripts/python.exe" >&2
  echo "expected: $expected" >&2
  echo "got: $resolved" >&2
  cat "$tmpdir/resolve.err" >&2 || true
  exit 1
fi

if [[ "$resolved" == *"/bin/python" ]]; then
  echo "--resolve-python must not select .venv/bin/python when Scripts/python.exe exists" >&2
  exit 1
fi

rss="$(bash "$shipped" --rss-kb 2048)"
if [[ "$rss" != "2.00" ]]; then
  echo "expected Darwin ps rss-kb 2048 -> 2.00 MB, got: $rss" >&2
  exit 1
fi

echo "desktop-500-gui-python ok (Scripts/python.exe wins, rss-kb 2048=2.00)"
