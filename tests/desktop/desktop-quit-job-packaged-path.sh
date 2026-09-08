#!/usr/bin/env bash
# Drive the shipped leftover quit+job harness packaged path (not a reimplementation).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
shipped="$repo_root/packaging/scripts/desktop-quit-job-gui.sh"

if [[ ! -f "$shipped" ]]; then
  echo "missing packaging/scripts/desktop-quit-job-gui.sh" >&2
  exit 1
fi

if grep -E -q 'bash[[:space:]]+.*macos-dmg-gui-smoke|bash[[:space:]]+.*desktop-500-gui\.sh' "$shipped"; then
  echo "quit+job harness must not invoke #177/#179 scripts" >&2
  exit 1
fi

if ! grep -F -q 'framepilot-desktop-quit-job' "$shipped"; then
  echo "scratch prefix must be framepilot-desktop-quit-job" >&2
  exit 1
fi

if ! grep -F -q 'skip is not pass' "$shipped"; then
  echo "Linux path must print skip is not pass" >&2
  exit 1
fi

if ! grep -E -q 'exit 2' "$shipped"; then
  echo "Linux skip must exit 2" >&2
  exit 1
fi

if ! grep -F -q 'quit-clean' "$shipped"; then
  echo "harness must launch quit-clean" >&2
  exit 1
fi

if ! grep -F -q 'quit-import' "$shipped"; then
  echo "harness must launch quit-import" >&2
  exit 1
fi

if ! grep -F -q 'quit-processing' "$shipped"; then
  echo "harness must launch quit-processing" >&2
  exit 1
fi

if ! grep -F -q 'quit-export' "$shipped"; then
  echo "harness must launch quit-export" >&2
  exit 1
fi

if ! grep -F -q 'COUNT=30' "$shipped" && ! grep -E -q 'COUNT:-30|--count 30' "$shipped"; then
  echo "default corpus must be 30 JPEGs" >&2
  exit 1
fi

if ! grep -F -q '3000' "$shipped" || ! grep -F -q '2000' "$shipped"; then
  echo "corpus must be 3000x2000" >&2
  exit 1
fi

if ! grep -F -q 'open -n "$APP_COPY"' "$shipped"; then
  echo "harness must launch macOS via open -n so WKWebView gets Aqua" >&2
  exit 1
fi

if ! grep -F -q 'FRAMEPILOT_DESKTOP_QA_MODE' "$shipped"; then
  echo "harness must pass FRAMEPILOT_DESKTOP_QA_MODE" >&2
  exit 1
fi

if ! grep -F -q 'osascript' "$shipped"; then
  echo "harness must drive production quit via osascript" >&2
  exit 1
fi

if ! awk '
  /wait_milestone "\$running_ms"/ { in_job = 1 }
  in_job && /osascript/ { found = 1 }
  in_job && /wait_milestone "quit_dialog"/ { in_job = 0 }
  END { exit found ? 1 : 0 }
' "$shipped"; then
  echo "job rows must not osascript before quit_dialog (GHA Apple Event terminates)" >&2
  exit 1
fi

if ! grep -F -q 'originals.manifest' "$shipped"; then
  echo "harness must snapshot and verify originals" >&2
  exit 1
fi

if ! grep -E -q 'LISTEN|leftover' "$shipped"; then
  echo "harness must check leftover framepilot-api LISTEN" >&2
  exit 1
fi

if ! grep -F -q 'cancel_and_quit' "$shipped"; then
  echo "harness must require cancel_and_quit evidence" >&2
  exit 1
fi

echo "desktop-quit-job-packaged-path ok"
