#!/usr/bin/env bash
# Drive the shipped leftover harness Path B packaged path (not a reimplementation).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
shipped="$repo_root/packaging/scripts/desktop-500-gui.sh"

if [[ ! -f "$shipped" ]]; then
  echo "missing packaging/scripts/desktop-500-gui.sh" >&2
  exit 1
fi

if grep -F -q "QA gate not in this slice" "$shipped"; then
  echo "shipped harness still contains Slice-2 placeholder 'QA gate not in this slice'" >&2
  exit 1
fi

if ! grep -E -q '^wait_done_jsonl\(\)|wait_done_jsonl \(\)' "$shipped"; then
  echo "shipped harness is missing wait_done_jsonl" >&2
  exit 1
fi

if ! grep -E -q '^macos_bundle_executable\(\)|macos_bundle_executable \(\)' "$shipped"; then
  echo "shipped harness is missing macos_bundle_executable" >&2
  exit 1
fi

if ! grep -E -q '^parse_windows_listen\(\)|parse_windows_listen \(\)' "$shipped"; then
  echo "shipped harness is missing parse_windows_listen" >&2
  exit 1
fi

if ! grep -F -q "dump_health_timeout_diagnostics" "$shipped"; then
  echo "shipped harness is missing dump_health_timeout_diagnostics" >&2
  exit 1
fi

if ! grep -E -q '^kill_macos_leftovers\(\)|kill_macos_leftovers \(\)' "$shipped"; then
  echo "shipped harness is missing kill_macos_leftovers" >&2
  exit 1
fi

if ! grep -F -q 'open -n "$APP_COPY"' "$shipped"; then
  echo "shipped harness must launch macOS via open -n so WKWebView gets Aqua" >&2
  exit 1
fi

if ! grep -F -q -- '--env "FRAMEPILOT_DESKTOP_QA=1"' "$shipped"; then
  echo "shipped harness must pass FRAMEPILOT_DESKTOP_QA through open --env" >&2
  exit 1
fi

if ! grep -F -q "WindowStyle Normal" "$shipped"; then
  echo "shipped harness must Start-Process Windows GUI with WindowStyle Normal" >&2
  exit 1
fi

if ! grep -F -q "cygpath -w" "$shipped"; then
  echo "shipped harness must convert Git Bash paths with cygpath -w" >&2
  exit 1
fi

if ! grep -F -q "MSYS2_ARG_CONV_EXCL" "$shipped"; then
  echo "shipped harness must disable MSYS path conversion for the GUI process" >&2
  exit 1
fi

if ! grep -F -q 'cp "${EVIDENCE_DIR}/milestones.jsonl"' "$shipped"; then
  echo "shipped harness must copy milestones.jsonl off scratch before wipe" >&2
  exit 1
fi

if ! grep -E -q '^kill_packaged_leftovers\(\)|kill_packaged_leftovers \(\)' "$shipped"; then
  echo "shipped harness is missing kill_packaged_leftovers" >&2
  exit 1
fi

if ! grep -F -q 'taskkill.exe //F //T //IM framepilot-desktop.exe' "$shipped"; then
  echo "kill_windows_leftovers must taskkill.exe /F /T the desktop process tree" >&2
  exit 1
fi

if ! grep -F -q "kill_packaged_leftovers" "$shipped" || ! awk '
  $0 ~ /^wipe_scratch_siblings\(\)/ { in_wipe = 1 }
  in_wipe && /kill_packaged_leftovers/ { found = 1 }
  in_wipe && /^}/ { exit }
  END { exit found ? 0 : 1 }
' "$shipped"; then
  echo "wipe_scratch_siblings must kill packaged leftovers before rm -rf" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

app="$tmpdir/FramePilot.app"
mkdir -p "$app/Contents/MacOS"
cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>framepilot-desktop</string>
  <key>CFBundleIdentifier</key>
  <string>com.framepilot.app</string>
</dict>
</plist>
PLIST
printf '%s\n' '#!/bin/sh' 'echo crate-binary' > "$app/Contents/MacOS/framepilot-desktop"
chmod +x "$app/Contents/MacOS/framepilot-desktop"

set +e
discovered="$(bash "$shipped" --macos-exec "$app" 2>"$tmpdir/macos.err")"
macos_status=$?
set -e
if [[ "$macos_status" -ne 0 ]]; then
  echo "--macos-exec failed" >&2
  cat "$tmpdir/macos.err" >&2 || true
  exit 1
fi
expected_exe="$app/Contents/MacOS/framepilot-desktop"
if [[ "$discovered" != "$expected_exe" ]]; then
  echo "expected CFBundleExecutable framepilot-desktop, got: ${discovered}" >&2
  exit 1
fi
if [[ "$discovered" == *"/Contents/MacOS/FramePilot" ]]; then
  echo "must not hardcode Contents/MacOS/FramePilot when crate binary is framepilot-desktop" >&2
  exit 1
fi

fallback="$tmpdir/Fallback.app"
mkdir -p "$fallback/Contents/MacOS"
printf '%s\n' '#!/bin/sh' 'echo fallback' > "$fallback/Contents/MacOS/framepilot-desktop"
chmod +x "$fallback/Contents/MacOS/framepilot-desktop"
set +e
fallback_exe="$(bash "$shipped" --macos-exec "$fallback" 2>"$tmpdir/fallback.err")"
fallback_status=$?
set -e
if [[ "$fallback_status" -ne 0 || "$fallback_exe" != "$fallback/Contents/MacOS/framepilot-desktop" ]]; then
  echo "plist-less Contents/MacOS/* fallback failed: ${fallback_exe}" >&2
  cat "$tmpdir/fallback.err" >&2 || true
  exit 1
fi

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

prefix="$tmpdir/prefix"
mkdir -p "$prefix/photos" "$prefix/project" "$prefix/data/logs" "$prefix/evidence"
python3 - "$prefix/photos/qa_000.jpg" <<'PY'
from pathlib import Path
import sys

Path(sys.argv[1]).write_bytes(b"\xff\xd8\xff\xd9synthetic-jpeg")
PY
bash "$shipped" --snapshot-originals "$prefix"

python3 - "$prefix/evidence" <<'PY'
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sys

evidence = Path(sys.argv[1])
base = datetime(2026, 9, 7, 13, 12, 26, tzinfo=timezone.utc)

def iso(delta_s):
    return (base + timedelta(seconds=delta_s)).strftime("%Y-%m-%dT%H:%M:%SZ")

milestones = [
    {"milestone": "idle", "t": iso(0), "import_workers": 1},
    {"milestone": "import_complete", "t": iso(8), "accepted_files": 1},
    {"milestone": "process_complete", "t": iso(12)},
    {"milestone": "first_preview", "t": iso(14), "preview_natural_width": 1800},
    {"milestone": "done", "t": iso(15), "accepted_files": 1, "preview_natural_width": 1800},
]
(evidence / "milestones.jsonl").write_text(
    "".join(json.dumps(row) + "\n" for row in milestones),
    encoding="utf-8",
)
rss = [
    {"t": iso(0), "sidecar_mb": 120.5, "ui_mb": 80.0},
    {"t": iso(8), "sidecar_mb": 130.0, "ui_mb": 90.0},
    {"t": iso(12), "sidecar_mb": 140.0, "ui_mb": 95.0},
    {"t": iso(14), "sidecar_mb": 150.0, "ui_mb": 100.0},
]
(evidence / "rss.jsonl").write_text(
    "".join(json.dumps(row) + "\n" for row in rss),
    encoding="utf-8",
)
PY

set +e
bash "$shipped" --probe --finish-from-evidence "$prefix" >"$tmpdir/finish.out" 2>"$tmpdir/finish.err"
finish_status=$?
set -e
if [[ "$finish_status" -ne 0 ]]; then
  echo "--finish-from-evidence failed" >&2
  cat "$tmpdir/finish.out" >&2 || true
  cat "$tmpdir/finish.err" >&2 || true
  exit 1
fi
python3 - "$prefix/evidence/result.json" <<'PY'
import json
import sys

payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
if payload.get("result") != "pass":
    raise SystemExit(f"expected result=pass, got {payload.get('result')}")
if payload.get("native_dialog") != "stubbed":
    raise SystemExit("native_dialog must stay stubbed")
if payload.get("preview_natural_width", 0) <= 0:
    raise SystemExit("preview_natural_width must be > 0")
if payload.get("rss_mb", {}).get("idle", {}).get("sidecar") in (None, 0, 0.0):
    raise SystemExit("idle sidecar RSS was not joined")
if payload.get("originals_unchanged") is not True:
    raise SystemExit("originals_unchanged must be true")
PY

wipe_prefix="$tmpdir/wipe-prefix"
mkdir -p "$wipe_prefix/photos" "$wipe_prefix/project" "$wipe_prefix/data/logs" "$wipe_prefix/evidence"
printf 'busy\n' > "$wipe_prefix/data/framepilot.db"
printf 'keep-prefix\n' > "$wipe_prefix/keep.txt"
set +e
bash "$shipped" --wipe-scratch "$wipe_prefix" >"$tmpdir/wipe.out" 2>"$tmpdir/wipe.err"
wipe_status=$?
set -e
if [[ "$wipe_status" -ne 0 ]]; then
  echo "--wipe-scratch failed" >&2
  cat "$tmpdir/wipe.out" >&2 || true
  cat "$tmpdir/wipe.err" >&2 || true
  exit 1
fi
if [[ -e "$wipe_prefix/data/framepilot.db" || -d "$wipe_prefix/photos" || -d "$wipe_prefix/project" || -d "$wipe_prefix/evidence" ]]; then
  echo "--wipe-scratch left sibling dirs/files behind" >&2
  find "$wipe_prefix" -print >&2 || true
  exit 1
fi
if [[ ! -f "$wipe_prefix/keep.txt" ]]; then
  echo "--wipe-scratch must not delete the prefix root" >&2
  exit 1
fi

echo "desktop-500-gui-packaged-path ok (wait-done path, macos exec, windows listen)"
