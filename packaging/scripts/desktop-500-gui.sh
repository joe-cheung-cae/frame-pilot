#!/usr/bin/env bash
# Packaged-desktop ≥500 GUI harness.
# Slice 1 stub: Linux/WSL2 skip-not-pass only. Slice 2 replaces this with
# probe/500 launch. Do not print result=pass on Linux.
set -euo pipefail

os="$(uname -s)"
if [[ "$os" == "Linux" ]]; then
  echo "skip is not pass: uname -s is ${os}; packaged NSIS/DMG GUI cannot run here" >&2
  exit 2
fi

echo "desktop-500-gui Slice 1 stub: ${os} launch is not implemented yet" >&2
exit 1
