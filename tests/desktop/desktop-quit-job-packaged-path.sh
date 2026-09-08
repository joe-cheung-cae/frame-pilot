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

if ! grep -F -q 'COUNT=500' "$shipped" && ! grep -E -q 'COUNT:-500|--count 500' "$shipped"; then
  echo "default corpus must be 500 JPEGs so processing stays cancellable" >&2
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

if ! grep -F -q 'LOCALAPPDATA' "$shipped" || ! grep -F -q 'framepilot-desktop-quit-job' "$shipped"; then
  echo "Windows scratch prefix must use LOCALAPPDATA/framepilot-desktop-quit-job" >&2
  exit 1
fi

if ! grep -F -q '.venv/Scripts/python.exe' "$shipped"; then
  echo "Windows python discovery must prefer Scripts/python.exe" >&2
  exit 1
fi

if ! grep -F -q 'find_nsis' "$shipped"; then
  echo "harness must discover the unsigned NSIS installer" >&2
  exit 1
fi

if ! grep -F -q "WindowStyle Normal" "$shipped"; then
  echo "harness must Start-Process Windows GUI with WindowStyle Normal" >&2
  exit 1
fi

if ! grep -F -q "cygpath -w" "$shipped"; then
  echo "harness must convert Git Bash paths with cygpath -w" >&2
  exit 1
fi

if ! grep -F -q "MSYS2_ARG_CONV_EXCL" "$shipped"; then
  echo "harness must disable MSYS path conversion for the GUI process" >&2
  exit 1
fi

if ! grep -F -q 'CloseMainWindow' "$shipped"; then
  echo "quit-clean must use production CloseMainWindow on Windows" >&2
  exit 1
fi

if ! grep -F -q "Get-Process -Name" "$shipped"; then
  echo "Windows process probe must use Get-Process -Name (Git Bash tasklist is UTF-16)" >&2
  exit 1
fi

if ! grep -E -q '^dump_leftover_listen_diagnostics\(\)|dump_leftover_listen_diagnostics \(\)' "$shipped"; then
  echo "harness is missing dump_leftover_listen_diagnostics" >&2
  exit 1
fi

if ! python3 - "$shipped" <<'PY'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
start = text.find("dump_leftover_listen_diagnostics()")
if start < 0:
    raise SystemExit("dump_leftover_listen_diagnostics missing")
chunk = text[start:]
win = chunk.find("windows)")
star = chunk.find("*)", win)
if win < 0 or star < 0:
    raise SystemExit("dump_leftover_listen_diagnostics missing windows/* branches")
if "lsof" in chunk[win:star]:
    raise SystemExit("Windows leftover diagnostics must not call lsof")
PY
then
  echo "Windows leftover diagnostics must not call lsof" >&2
  exit 1
fi

if ! grep -E -q '^parse_windows_listen\(\)|parse_windows_listen \(\)' "$shipped"; then
  echo "harness is missing parse_windows_listen" >&2
  exit 1
fi

if ! awk '
  /wait_milestone "\$running_ms"/ { in_job = 1 }
  in_job && /CloseMainWindow/ { found = 1 }
  in_job && /taskkill/ { found = 1 }
  in_job && /wait_milestone "quit_dialog"/ { in_job = 0 }
  END { exit found ? 1 : 0 }
' "$shipped"; then
  echo "job rows must not CloseMainWindow or taskkill before quit_dialog" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
cat > "$tmpdir/netstat.txt" <<'NET'
  TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       1
  TCP    127.0.0.1:14198        0.0.0.0:0              LISTENING       44316
  TCP    192.168.1.9:445        0.0.0.0:0              LISTENING       4
NET
cat > "$tmpdir/tasklist.txt" <<'TL'
Image Name                     PID Session Name        Session#    Mem Usage
========================= ======== ================ =========== ============
svchost.exe                        1 Services                   0      1,024 K
framepilot-api.exe             44316 Console                    1     12,345 K
TL
set +e
listen_port="$(bash "$shipped" --parse-windows-listen "$tmpdir/netstat.txt" "$tmpdir/tasklist.txt" 2>"$tmpdir/listen.err")"
listen_status=$?
set -e
if [[ "$listen_status" -ne 0 || "$listen_port" != "14198" ]]; then
  echo "expected Windows LISTEN parser to return 14198 for framepilot-api.exe, got: ${listen_port}" >&2
  cat "$tmpdir/listen.err" >&2 || true
  exit 1
fi

python3 - "$tmpdir/tasklist-utf16.txt" <<'PY'
from pathlib import Path
import sys

Path(sys.argv[1]).write_text(
    "Image Name                     PID Session Name        Session#    Mem Usage\n"
    "========================= ======== ================ =========== ============\n"
    "framepilot-api.exe             44316 Console                    1     12,345 K\n",
    encoding="utf-16",
)
PY
set +e
utf16_port="$(bash "$shipped" --parse-windows-listen "$tmpdir/netstat.txt" "$tmpdir/tasklist-utf16.txt" 2>"$tmpdir/listen-utf16.err")"
utf16_status=$?
set -e
if [[ "$utf16_status" -ne 0 || "$utf16_port" != "14198" ]]; then
  echo "expected UTF-16 tasklist LISTEN parser to return 14198, got: ${utf16_port}" >&2
  cat "$tmpdir/listen-utf16.err" >&2 || true
  exit 1
fi

echo "desktop-quit-job-packaged-path ok"
