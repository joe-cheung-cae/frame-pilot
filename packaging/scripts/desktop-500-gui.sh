#!/usr/bin/env bash
# Packaged-desktop ≥500 GUI harness (leftover #179, Path B).
# Linux/WSL2: skip is not pass (exit 2) before generating photos.
# Do not print result=pass on Linux. Do not call npm generate:synthetic.
# Do not set PYTHONPATH. Do not call macos-dmg-gui-smoke.sh.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

WIDTH=3000
HEIGHT=2000
QUALITY=88
MODE=""
COUNT=""
INSTALLER=""
RESOLVE_PYTHON=0
RSS_KB=""
MACOS_EXEC=""
PARSE_NETSTAT=""
PARSE_TASKLIST=""
FINISH_PREFIX=""
SNAPSHOT_PREFIX=""
WIPE_PREFIX=""
RESULT="fail"
RSS_IDLE_SIDECAR="null"
RSS_IDLE_UI="null"
RSS_IMPORT_SIDECAR="null"
RSS_IMPORT_UI="null"
RSS_PROCESS_SIDECAR="null"
RSS_PROCESS_UI="null"
RSS_PREVIEW_SIDECAR="null"
RSS_PREVIEW_UI="null"
RSS_PEAK_SIDECAR="null"
RSS_PEAK_UI="null"
FAIL_REASON=""
APP_VERSION=""
ACCEPTED_FILES=0
IMPORT_WORKERS=0
PREVIEW_NATURAL_WIDTH=0
ORIGINALS_UNCHANGED=true
CLEANUP_DONE=0
RSS_PID=""
GUI_PID=""
ATTACH_DEV=""
APP_COPY=""
INSTALLED_EXE=""
UNINSTALL_EXE=""
OPENED=0

os="$(uname -s)"
uname_s="$os"

os_label() {
  case "$os" in
    Linux) printf 'linux\n' ;;
    Darwin) printf 'macos\n' ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT) printf 'windows\n' ;;
    *) printf 'unknown\n' ;;
  esac
}

scratch_prefix() {
  local label
  label="$(os_label)"
  if [[ "$label" == "windows" && -n "${LOCALAPPDATA:-}" ]]; then
    printf '%s\n' "${LOCALAPPDATA}/framepilot-desktop-500-gui"
  else
    printf '%s\n' "${HOME}/.cache/framepilot-desktop-500-gui"
  fi
}

python_is_usable() {
  local candidate="${1:-}"
  [[ -n "$candidate" ]] || return 1
  if [[ -x "$candidate" ]]; then
    return 0
  fi
  # Git Bash: .exe may exist without a Unix execute bit.
  if [[ "$candidate" == *.exe && -f "$candidate" ]]; then
    return 0
  fi
  return 1
}

resolve_python() {
  local python_bin=""
  if python_is_usable "${PYTHON:-}"; then
    python_bin="$PYTHON"
  elif python_is_usable "$repo_root/.venv/Scripts/python.exe"; then
    python_bin="$repo_root/.venv/Scripts/python.exe"
  elif python_is_usable "$repo_root/.venv/bin/python"; then
    python_bin="$repo_root/.venv/bin/python"
  else
    echo "python interpreter not found (PYTHON, .venv/Scripts/python.exe, .venv/bin/python)" >&2
    return 1
  fi
  printf '%s\n' "$python_bin"
}

# Darwin/Linux `ps -o rss=` is kilobytes. Do not reuse performance_smoke.py.
rss_mb_from_ps_kb() {
  local kb="${1:-}"
  if [[ ! "$kb" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "rss-kb must be a number, got: ${kb}" >&2
    return 1
  fi
  awk -v kb="$kb" 'BEGIN { printf "%.2f\n", kb / 1024 }'
}

rss_mb_from_workingset_bytes() {
  local bytes="${1:-}"
  if [[ ! "$bytes" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "working-set bytes must be a number, got: ${bytes}" >&2
    return 1
  fi
  awk -v b="$bytes" 'BEGIN { printf "%.2f\n", b / 1024 / 1024 }'
}

iso_now() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

ci_run_url() {
  if [[ -n "${GITHUB_SERVER_URL:-}" && -n "${GITHUB_REPOSITORY:-}" && -n "${GITHUB_RUN_ID:-}" ]]; then
    printf '%s/%s/actions/runs/%s\n' "$GITHUB_SERVER_URL" "$GITHUB_REPOSITORY" "$GITHUB_RUN_ID"
  fi
}

usage() {
  echo "usage: $0 --probe|--count N|--resolve-python|--rss-kb KB|--macos-exec APP|--parse-windows-listen NETSTAT TASKLIST|--snapshot-originals PREFIX|--finish-from-evidence PREFIX|--wipe-scratch PREFIX [--installer PATH]" >&2
}

json_escape() {
  local s="${1:-}"
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$s" 2>/dev/null || {
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    printf '"%s"' "$s"
  }
}

write_result_json() {
  local dest="${1:-}"
  local ts url os_json uname_json fail_json version_json
  [[ -n "$dest" ]] || return 1
  mkdir -p "$(dirname "$dest")"
  ts="$(iso_now)"
  url="$(ci_run_url || true)"
  os_json="$(json_escape "$(os_label)")"
  uname_json="$(json_escape "$uname_s")"
  fail_json="$(json_escape "${FAIL_REASON:-}")"
  version_json="$(json_escape "${APP_VERSION:-}")"
  cat > "$dest" <<EOF
{
  "mode": $(json_escape "${MODE:-probe}"),
  "result": $(json_escape "$RESULT"),
  "os": ${os_json},
  "uname": ${uname_json},
  "timestamp": $(json_escape "$ts"),
  "app_version": ${version_json},
  "ci_run_url": $(json_escape "${url:-}"),
  "native_dialog": "stubbed",
  "import_workers": ${IMPORT_WORKERS:-0},
  "accepted_files": ${ACCEPTED_FILES:-0},
  "count": ${COUNT:-0},
  "width": ${WIDTH},
  "height": ${HEIGHT},
  "quality": ${QUALITY},
  "rss_mb": {
    "idle": {"sidecar": ${RSS_IDLE_SIDECAR}, "ui": ${RSS_IDLE_UI}},
    "import_complete": {"sidecar": ${RSS_IMPORT_SIDECAR}, "ui": ${RSS_IMPORT_UI}},
    "process_complete": {"sidecar": ${RSS_PROCESS_SIDECAR}, "ui": ${RSS_PROCESS_UI}},
    "first_preview": {"sidecar": ${RSS_PREVIEW_SIDECAR}, "ui": ${RSS_PREVIEW_UI}}
  },
  "rss_peak_mb": {"sidecar": ${RSS_PEAK_SIDECAR}, "ui": ${RSS_PEAK_UI}},
  "originals_unchanged": ${ORIGINALS_UNCHANGED},
  "preview_natural_width": ${PREVIEW_NATURAL_WIDTH:-0},
  "fail_reason": ${fail_json}
}
EOF
}

copy_evidence() {
  local dest sidecar
  dest="${RUNNER_TEMP:-/tmp}/desktop-500-gui/${MODE:-probe}-$(os_label)"
  mkdir -p "$dest"
  if [[ -f "${EVIDENCE_DIR}/result.json" ]]; then
    cp "${EVIDENCE_DIR}/result.json" "${dest}/result.json"
  fi
  if [[ -f "${EVIDENCE_DIR}/milestones.jsonl" ]]; then
    cp "${EVIDENCE_DIR}/milestones.jsonl" "${dest}/milestones.jsonl"
  fi
  sidecar="${DATA_DIR}/logs/sidecar.log"
  if [[ -f "$sidecar" ]]; then
    tail -n 200 "$sidecar" > "${dest}/sidecar.log.excerpt" 2>/dev/null || true
  fi
}

kill_packaged_leftovers() {
  case "$(os_label)" in
    windows) kill_windows_leftovers ;;
    macos) kill_macos_leftovers ;;
  esac
}

wipe_scratch_siblings() {
  local n
  kill_packaged_leftovers
  for n in 1 2 3 4 5; do
    if rm -rf "${PHOTOS_DIR}" "${PROJECT_DIR}" "${DATA_DIR}" "${EVIDENCE_DIR}"; then
      return 0
    fi
    kill_packaged_leftovers
    sleep 1
  done
  # Probe leftovers on Windows can keep SQLite busy; do not fail the 500 run.
  rm -rf "${PHOTOS_DIR}" "${PROJECT_DIR}" "${DATA_DIR}" "${EVIDENCE_DIR}" 2>/dev/null || true
  return 0
}

cleanup() {
  local status=$?
  set +e
  if [[ "$CLEANUP_DONE" -eq 1 ]]; then
    return 0
  fi
  CLEANUP_DONE=1
  if [[ -n "${RSS_PID}" ]]; then
    kill "${RSS_PID}" >/dev/null 2>&1
    wait "${RSS_PID}" >/dev/null 2>&1
  fi
  if [[ "$OPENED" -eq 1 ]]; then
    quit_gui
  fi
  if [[ -n "${ATTACH_DEV}" ]]; then
    hdiutil detach "${ATTACH_DEV}" >/dev/null 2>&1 || hdiutil detach "${ATTACH_DEV}" -force >/dev/null 2>&1
    ATTACH_DEV=""
  fi
  if [[ -n "${UNINSTALL_EXE}" && -f "${UNINSTALL_EXE}" ]]; then
    "${UNINSTALL_EXE}" //S >/dev/null 2>&1 || true
  fi
  if [[ -n "${EVIDENCE_DIR:-}" && ! -f "${EVIDENCE_DIR}/result.json" ]]; then
    mkdir -p "${EVIDENCE_DIR}"
    write_result_json "${EVIDENCE_DIR}/result.json" || true
  fi
  if [[ -n "${EVIDENCE_DIR:-}" ]]; then
    copy_evidence || true
  fi
  if [[ -n "${PREFIX:-}" ]]; then
    wipe_scratch_siblings || true
  fi
  return "$status"
}

quit_gui() {
  case "$(os_label)" in
    macos)
      osascript -e 'tell application "FramePilot" to quit' >/dev/null 2>&1 || true
      osascript -e 'tell application id "com.framepilot.app" to quit' >/dev/null 2>&1 || true
      if [[ -n "${GUI_PID}" ]]; then
        kill "${GUI_PID}" >/dev/null 2>&1 || true
      fi
      ;;
    windows)
      if [[ -n "${GUI_PID}" ]]; then
        kill "${GUI_PID}" >/dev/null 2>&1 || true
      fi
      kill_windows_leftovers
      ;;
  esac
}

prepare_scratch() {
  PREFIX="$(scratch_prefix)"
  mkdir -p "$PREFIX"
  chmod 700 "$PREFIX" 2>/dev/null || true
  PHOTOS_DIR="${PREFIX}/photos"
  PROJECT_DIR="${PREFIX}/project"
  DATA_DIR="${PREFIX}/data"
  EVIDENCE_DIR="${PREFIX}/evidence"
  APP_DIR="${PREFIX}/app"
  wipe_scratch_siblings
  mkdir -p "$PHOTOS_DIR" "$PROJECT_DIR" "$DATA_DIR" "$EVIDENCE_DIR"
}

linux_skip() {
  echo "skip is not pass: uname -s is ${os}; packaged NSIS/DMG GUI cannot run here" >&2
  RESULT="skip"
  FAIL_REASON="skip is not pass: uname -s is ${os}; packaged NSIS/DMG GUI cannot run here"
  ORIGINALS_UNCHANGED=true
  write_result_json "${EVIDENCE_DIR}/result.json" || true
  exit 2
}

generate_dataset() {
  local python_bin
  if [[ "$WIDTH" -eq 160 && "$HEIGHT" -eq 120 ]]; then
    echo "refusing default 160x120 synthetic size; use 3000x2000" >&2
    RESULT="fail"
    FAIL_REASON="synthetic dataset used default 160x120 size"
    exit 1
  fi
  python_bin="$(resolve_python)"
  # pip install -e apps/api[dev] provides the module. Do not set PYTHONPATH.
  "$python_bin" -m app.devtools.synthetic_dataset \
    --output "$PHOTOS_DIR" \
    --count "$COUNT" \
    --width "$WIDTH" \
    --height "$HEIGHT" \
    --quality "$QUALITY"
}

find_nsis() {
  local dir files
  if [[ -n "$INSTALLER" ]]; then
    printf '%s\n' "$INSTALLER"
    return 0
  fi
  dir="$repo_root/apps/desktop/src-tauri/target/release/bundle/nsis"
  shopt -s nullglob
  files=("$dir"/*.exe)
  shopt -u nullglob
  if [[ "${#files[@]}" -lt 1 ]]; then
    echo "NSIS installer not found under ${dir}" >&2
    return 1
  fi
  printf '%s\n' "${files[0]}"
}

find_dmg() {
  local dir files
  if [[ -n "$INSTALLER" ]]; then
    printf '%s\n' "$INSTALLER"
    return 0
  fi
  dir="$repo_root/apps/desktop/src-tauri/target/release/bundle/dmg"
  shopt -s nullglob
  files=("$dir"/*.dmg)
  shopt -u nullglob
  if [[ "${#files[@]}" -lt 1 ]]; then
    echo "DMG not found under ${dir}" >&2
    return 1
  fi
  printf '%s\n' "${files[0]}"
}

webview2_present() {
  local base
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command \
      "if (Get-ItemProperty HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5} -ErrorAction SilentlyContinue) { exit 0 }; if (Test-Path \$env:LOCALAPPDATA\\Microsoft\\EdgeWebView\\Application) { exit 0 }; exit 1" \
      >/dev/null 2>&1 && return 0
  fi
  for base in \
    "${LOCALAPPDATA:-}/Microsoft/EdgeWebView/Application" \
    "/c/Program Files (x86)/Microsoft/EdgeWebView/Application"; do
    if [[ -d "$base" ]]; then
      return 0
    fi
  done
  return 1
}

windows_image_running() {
  local image="${1:-}"
  tasklist.exe //FI "IMAGENAME eq ${image}" 2>/dev/null | grep -qi "$image"
}

kill_windows_leftovers() {
  local n
  for n in 1 2 3 4 5 6 7 8 9 10; do
    # /T kills sidecar + WebView2 children that keep SQLite busy after probe.
    taskkill.exe //F //T //IM framepilot-desktop.exe >/dev/null 2>&1 || true
    taskkill.exe //F //T //IM framepilot-api.exe >/dev/null 2>&1 || true
    if ! windows_image_running "framepilot-desktop.exe" && ! windows_image_running "framepilot-api.exe"; then
      sleep 1
      return 0
    fi
    sleep 1
  done
}

kill_macos_leftovers() {
  osascript -e 'tell application "FramePilot" to quit' >/dev/null 2>&1 || true
  osascript -e 'tell application id "com.framepilot.app" to quit' >/dev/null 2>&1 || true
  pkill -f '/FramePilot\.app/Contents/MacOS/' >/dev/null 2>&1 || true
  pkill -f 'framepilot-api' >/dev/null 2>&1 || true
  sleep 1
}

# Git Bash POSIX paths fail the Rust QA prefix gate. Windows exe needs native paths.
native_path() {
  local raw="${1:-}"
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$raw"
  else
    printf '%s\n' "$raw"
  fi
}

port_from_ps_argv() {
  local args host port
  while IFS= read -r args; do
    case "$args" in
      *desktop-500-gui*)
        continue
        ;;
      *framepilot-api*)
        ;;
      *)
        continue
        ;;
    esac
    host=""
    port=""
    if [[ "$args" =~ --host[[:space:]]+([^[:space:]]+) ]]; then
      host="${BASH_REMATCH[1]}"
    fi
    if [[ "$args" =~ --port[[:space:]]+([0-9]+) ]]; then
      port="${BASH_REMATCH[1]}"
    fi
    if [[ -z "$port" || "$port" == "0" ]]; then
      continue
    fi
    if [[ "$host" == "0.0.0.0" ]]; then
      echo "sidecar argv --host 0.0.0.0 is not allowed" >&2
      return 3
    fi
    if [[ -n "$host" && "$host" != "127.0.0.1" && "$host" != "localhost" ]]; then
      echo "sidecar argv --host ${host} is not loopback" >&2
      return 3
    fi
    printf '%s\n' "$port"
    return 0
  done < <(ps -axww -o args= 2>/dev/null || true)
  return 1
}

port_from_lsof() {
  local line name host port
  while IFS= read -r line; do
    case "$line" in
      *TCP*' (LISTEN)')
        name="${line##*TCP }"
        name="${name%% (LISTEN)*}"
        name="${name#"${name%%[![:space:]]*}"}"
        name="${name%"${name##*[![:space:]]}"}"
        ;;
      *)
        continue
        ;;
    esac
    if [[ -z "$name" || "$name" != *:* ]]; then
      continue
    fi
    host="${name%:*}"
    port="${name##*:}"
    if [[ "$name" == \[*\]:* ]]; then
      host="${name#\[}"
      host="${host%%\]*}"
      port="${name##*\]:}"
    fi
    if [[ "$host" == "0.0.0.0" || "$host" == "*" || "$host" == "::" ]]; then
      echo "sidecar LISTEN on ${name} is not loopback (rejected)" >&2
      return 3
    fi
    if [[ "$host" != "127.0.0.1" && "$host" != "::1" && "$host" != "localhost" ]]; then
      echo "sidecar LISTEN on ${name} is not 127.0.0.1 (rejected)" >&2
      return 3
    fi
    if [[ ! "$port" =~ ^[0-9]+$ || "$port" == "0" ]]; then
      continue
    fi
    printf '%s\n' "$port"
    return 0
  done < <(lsof -nP -c framepilot-api -iTCP -sTCP:LISTEN 2>/dev/null || true)
  return 1
}

# Parse Windows netstat -ano + tasklist dumps. Sidecar /health does not need WebView.
parse_windows_listen() {
  local netstat_file="${1:-}"
  local tasklist_file="${2:-}"
  if [[ ! -f "$netstat_file" || ! -f "$tasklist_file" ]]; then
    return 1
  fi
  python3 - "$netstat_file" "$tasklist_file" <<'PY'
import re
import sys

netstat_path, tasklist_path = sys.argv[1], sys.argv[2]
pids = set()
for raw in open(tasklist_path, encoding="utf-8", errors="replace"):
    line = raw.strip()
    if "framepilot-api" not in line.lower():
        continue
    parts = line.split()
    for index, part in enumerate(parts):
        if "framepilot-api" in part.lower() and index + 1 < len(parts) and parts[index + 1].isdigit():
            pids.add(parts[index + 1])
            break
if not pids:
    sys.exit(1)

for raw in open(netstat_path, encoding="utf-8", errors="replace"):
    line = raw.strip()
    upper = line.upper()
    if "LISTEN" not in upper:
        continue
    # Foreign address is often 0.0.0.0:0; only skip non-loopback LOCAL bind.
    if re.match(r"TCP\s+(0\.0\.0\.0|\*|\[::\]):", line, re.I):
        continue
    match = re.search(r"(127\.0\.0\.1|\[::1\]):(\d+)", line)
    if not match:
        continue
    port = match.group(2)
    if port == "0":
        continue
    numbers = re.findall(r"\b(\d+)\b", line)
    pid = numbers[-1] if numbers else ""
    if pid in pids:
        print(port)
        sys.exit(0)
sys.exit(1)
PY
}

port_from_powershell_listen() {
  local port
  if ! command -v powershell.exe >/dev/null 2>&1; then
    return 1
  fi
  port="$(
    powershell.exe -NoProfile -Command '
$p = Get-Process -Name framepilot-api -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $p) { exit 1 }
$c = Get-NetTCPConnection -OwningProcess $p.Id -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalAddress -eq "127.0.0.1" } |
  Select-Object -First 1
if (-not $c) { exit 1 }
Write-Output $c.LocalPort
' 2>/dev/null | tr -d "\r" | tail -n 1
  )"
  if [[ "$port" =~ ^[1-9][0-9]*$ ]]; then
    printf '%s\n' "$port"
    return 0
  fi
  return 1
}

port_from_windows_netstat() {
  local netstat_file tasklist_file port
  netstat_file="${EVIDENCE_DIR:-/tmp}/netstat-listen.txt"
  tasklist_file="${EVIDENCE_DIR:-/tmp}/tasklist-api.txt"
  mkdir -p "$(dirname "$netstat_file")"
  netstat -ano 2>/dev/null > "$netstat_file" || true
  if command -v tasklist.exe >/dev/null 2>&1; then
    tasklist.exe //FI "IMAGENAME eq framepilot-api.exe" > "$tasklist_file" 2>/dev/null || true
  elif command -v tasklist >/dev/null 2>&1; then
    tasklist //FI "IMAGENAME eq framepilot-api.exe" > "$tasklist_file" 2>/dev/null || true
  else
    return 1
  fi
  set +e
  port="$(parse_windows_listen "$netstat_file" "$tasklist_file")"
  set -e
  if [[ -n "${port:-}" ]]; then
    printf '%s\n' "$port"
    return 0
  fi
  return 1
}

discover_port() {
  local port rc
  set +e
  port="$(port_from_lsof)"
  rc=$?
  set -e
  if [[ "$rc" -eq 3 ]]; then
    return 3
  fi
  if [[ "$rc" -eq 0 && -n "$port" ]]; then
    printf '%s\n' "$port"
    return 0
  fi
  set +e
  port="$(port_from_ps_argv)"
  rc=$?
  set -e
  if [[ "$rc" -eq 3 ]]; then
    return 3
  fi
  if [[ "$rc" -eq 0 && -n "$port" ]]; then
    printf '%s\n' "$port"
    return 0
  fi
  if [[ "$(os_label)" == "windows" ]]; then
    set +e
    port="$(port_from_powershell_listen)"
    rc=$?
    set -e
    if [[ "$rc" -eq 0 && -n "$port" ]]; then
      printf '%s\n' "$port"
      return 0
    fi
    set +e
    port="$(port_from_windows_netstat)"
    rc=$?
    set -e
    if [[ "$rc" -eq 0 && -n "$port" ]]; then
      printf '%s\n' "$port"
      return 0
    fi
  fi
  return 1
}

export_qa_env() {
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY || true
  export no_proxy='127.0.0.1,localhost,::1'
  export NO_PROXY='127.0.0.1,localhost,::1'
  export MSYS2_ARG_CONV_EXCL='*'
  export MSYS_NO_PATHCONV=1
  export FRAMEPILOT_DATA_DIR="$(native_path "$DATA_DIR")"
  export FRAMEPILOT_DESKTOP_QA=1
  export FRAMEPILOT_DESKTOP_QA_PHOTOS="$(native_path "$PHOTOS_DIR")"
  export FRAMEPILOT_DESKTOP_QA_PROJECT="$(native_path "$PROJECT_DIR")"
  export FRAMEPILOT_DESKTOP_QA_EVIDENCE="$(native_path "$EVIDENCE_DIR")"
}

sample_rss_once() {
  local t sidecar_kb ui_kb sidecar_mb ui_mb line
  t="$(iso_now)"
  sidecar_kb="0"
  ui_kb="0"
  case "$(os_label)" in
    macos|linux)
      if command -v pgrep >/dev/null 2>&1; then
        line="$(pgrep -n -f 'framepilot-api' 2>/dev/null || true)"
        if [[ -n "$line" ]]; then
          sidecar_kb="$(ps -o rss= -p "$line" 2>/dev/null | awk '{print $1}' || true)"
        fi
        line="$(pgrep -n -f 'FramePilot|framepilot-desktop' 2>/dev/null || true)"
        if [[ -n "$line" ]]; then
          ui_kb="$(ps -o rss= -p "$line" 2>/dev/null | awk '{print $1}' || true)"
        fi
      fi
      sidecar_mb="$(rss_mb_from_ps_kb "${sidecar_kb:-0}" 2>/dev/null || printf '0.00\n')"
      ui_mb="$(rss_mb_from_ps_kb "${ui_kb:-0}" 2>/dev/null || printf '0.00\n')"
      ;;
    windows)
      sidecar_mb="0.00"
      ui_mb="0.00"
      if command -v powershell.exe >/dev/null 2>&1; then
        sidecar_mb="$(
          powershell.exe -NoProfile -Command \
            "\$p = Get-Process -Name framepilot-api -ErrorAction SilentlyContinue | Select-Object -First 1; if (\$p) { [math]::Round(\$p.WorkingSet64/1MB, 2) } else { 0 }" \
            2>/dev/null | tr -d '\r' || printf '0.00'
        )"
        ui_mb="$(
          powershell.exe -NoProfile -Command \
            "\$sum = 0; Get-Process -Name framepilot-desktop,msedgewebview2 -ErrorAction SilentlyContinue | ForEach-Object { \$sum += \$_.WorkingSet64 }; [math]::Round(\$sum/1MB, 2)" \
            2>/dev/null | tr -d '\r' || printf '0.00'
        )"
      fi
      ;;
    *)
      sidecar_mb="0.00"
      ui_mb="0.00"
      ;;
  esac
  printf '{"t":%s,"sidecar_mb":%s,"ui_mb":%s}\n' \
    "$(json_escape "$t")" "${sidecar_mb:-0}" "${ui_mb:-0}" >> "${EVIDENCE_DIR}/rss.jsonl"
}

start_rss_sampler() {
  : > "${EVIDENCE_DIR}/rss.jsonl"
  (
    while true; do
      sample_rss_once || true
      sleep 2
    done
  ) &
  RSS_PID=$!
}

dump_health_timeout_diagnostics() {
  echo "--- health-timeout diagnostics ---" >&2
  echo "os=$(os_label) uname=${uname_s} data_dir=${DATA_DIR:-}" >&2
  ps -axww -o pid,args= 2>/dev/null | head -n 80 >&2 || true
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command \
      "Get-Process framepilot-api,framepilot-desktop,msedgewebview2 -ErrorAction SilentlyContinue | Format-Table Name,Id,WorkingSet64 -AutoSize" \
      >&2 || true
  fi
  if command -v tasklist >/dev/null 2>&1; then
    tasklist 2>/dev/null | head -n 40 >&2 || true
  fi
  if command -v netstat >/dev/null 2>&1; then
    netstat -ano 2>/dev/null | head -n 40 >&2 || true
  fi
  if [[ -n "${DATA_DIR:-}" && -f "${DATA_DIR}/logs/sidecar.log" ]]; then
    echo "--- sidecar.log (stderr; last 80) ---" >&2
    tail -n 80 "${DATA_DIR}/logs/sidecar.log" >&2 || true
  else
    echo "--- sidecar.log missing under ${DATA_DIR:-unset}/logs ---" >&2
  fi
}

wait_health() {
  local start now elapsed port rc http_code health_file
  health_file="${EVIDENCE_DIR}/health.json"
  start="$(date +%s)"
  port=""
  http_code=""
  while true; do
    now="$(date +%s)"
    elapsed=$((now - start))
    if (( elapsed >= 60 )); then
      echo "sidecar GET /health did not return 200 within 60s" >&2
      dump_health_timeout_diagnostics
      return 1
    fi
    set +e
    port="$(discover_port)"
    rc=$?
    set -e
    if [[ "$rc" -eq 3 ]]; then
      echo "sidecar bound a non-loopback address" >&2
      return 1
    fi
    if [[ "$rc" -eq 0 && -n "$port" ]]; then
      : > "$health_file"
      set +e
      http_code="$(curl --noproxy '*' -sS -o "$health_file" -w '%{http_code}' "http://127.0.0.1:${port}/health")"
      set -e
      if [[ "$http_code" == "200" ]]; then
        APP_VERSION="$(
          python3 - "$health_file" <<'PY'
import json, sys
payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
print(payload.get("version") or "")
PY
        )"
        printf '%s' "${APP_VERSION}" > "${EVIDENCE_DIR}/app_version.txt"
        printf '%s\n' "$port"
        return 0
      fi
    fi
    sleep 1
  done
}

dump_idle_timeout_diagnostics() {
  echo "no idle JSONL within 90s after /health 200; SPA never booted" >&2
  echo "GUI_PID=${GUI_PID:-unset}" >&2
  echo "--- evidence ---" >&2
  ls -la "${EVIDENCE_DIR}" >&2 || true
  if [[ -f "${EVIDENCE_DIR}/milestones.jsonl" ]]; then
    echo "--- milestones.jsonl ---" >&2
    cat "${EVIDENCE_DIR}/milestones.jsonl" >&2 || true
  else
    echo "milestones.jsonl missing" >&2
  fi
  if [[ -n "${GUI_PID:-}" ]]; then
    ps -p "${GUI_PID}" -o pid,etime,args= >&2 || echo "GUI pid ${GUI_PID} is dead" >&2
  fi
  case "$(os_label)" in
    macos)
      pgrep -alf 'FramePilot|WebKit|framepilot' >&2 || true
      ;;
    windows)
      tasklist.exe //FI "IMAGENAME eq framepilot-desktop.exe" >&2 || true
      tasklist.exe //FI "IMAGENAME eq msedgewebview2.exe" >&2 || true
      ;;
  esac
  ps -axww -o args= 2>/dev/null | head -n 80 >&2 || true
  if [[ -f "${DATA_DIR}/logs/sidecar.log" ]]; then
    echo "--- sidecar.log head ---" >&2
    head -n 20 "${DATA_DIR}/logs/sidecar.log" >&2 || true
    echo "--- sidecar.log tail ---" >&2
    tail -n 80 "${DATA_DIR}/logs/sidecar.log" >&2 || true
  fi
}

wait_idle_jsonl() {
  local start now elapsed line
  start="$(date +%s)"
  while true; do
    now="$(date +%s)"
    elapsed=$((now - start))
    if (( elapsed >= 90 )); then
      dump_idle_timeout_diagnostics
      return 1
    fi
    if [[ -f "${EVIDENCE_DIR}/milestones.jsonl" ]]; then
      while IFS= read -r line || [[ -n "$line" ]]; do
        case "$line" in
          *'"milestone": "idle"'*|*'"milestone":"idle"'*)
            return 0
            ;;
        esac
      done < "${EVIDENCE_DIR}/milestones.jsonl"
    fi
    sleep 1
  done
}

# Crate binary is framepilot-desktop. Do not hardcode Contents/MacOS/FramePilot.
macos_bundle_executable() {
  local app="${1:-}"
  local macos_dir plist name exe cand
  if [[ -z "$app" || ! -d "$app" ]]; then
    echo "macOS app bundle not found: ${app}" >&2
    return 1
  fi
  macos_dir="${app}/Contents/MacOS"
  plist="${app}/Contents/Info.plist"
  if [[ ! -d "$macos_dir" ]]; then
    echo "missing ${macos_dir}" >&2
    return 1
  fi
  name=""
  if [[ -f "$plist" ]]; then
    if [[ -x /usr/libexec/PlistBuddy ]]; then
      name="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$plist" 2>/dev/null || true)"
    fi
    if [[ -z "$name" ]]; then
      name="$(
        python3 - "$plist" <<'PY'
import re
import sys

path = sys.argv[1]
try:
    import plistlib

    with open(path, "rb") as handle:
        data = plistlib.load(handle)
    print(data.get("CFBundleExecutable") or "")
except Exception:
    text = open(path, encoding="utf-8", errors="replace").read()
    match = re.search(
        r"<key>CFBundleExecutable</key>\s*<string>([^<]+)</string>",
        text,
    )
    print(match.group(1) if match else "")
PY
      )"
    fi
  fi
  if [[ -n "$name" ]]; then
    exe="${macos_dir}/${name}"
    if [[ -f "$exe" ]]; then
      printf '%s\n' "$exe"
      return 0
    fi
  fi
  for cand in "$macos_dir"/*; do
    [[ -e "$cand" ]] || continue
    if [[ -f "$cand" ]]; then
      printf '%s\n' "$cand"
      return 0
    fi
  done
  echo "no executable under ${macos_dir} (looked for CFBundleExecutable=${name:-unset})" >&2
  return 1
}

snapshot_originals() {
  local manifest
  manifest="${EVIDENCE_DIR}/originals.manifest"
  mkdir -p "$EVIDENCE_DIR"
  python3 - "$PHOTOS_DIR" "$manifest" <<'PY'
import hashlib
import os
import sys

photos, manifest = sys.argv[1], sys.argv[2]
rows = []
for root, _dirs, files in os.walk(photos):
    for name in files:
        path = os.path.join(root, name)
        rel = os.path.relpath(path, photos)
        st = os.stat(path)
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        nsec = getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000))
        rows.append(f"{rel}\t{st.st_size}\t{nsec}\t{digest.hexdigest()}\n")
rows.sort()
with open(manifest, "w", encoding="utf-8") as handle:
    handle.writelines(rows)
PY
}

verify_originals() {
  local manifest
  manifest="${EVIDENCE_DIR}/originals.manifest"
  if [[ ! -f "$manifest" ]]; then
    echo "originals.manifest missing" >&2
    return 1
  fi
  python3 - "$PHOTOS_DIR" "$manifest" "${PROJECT_DIR:-}" <<'PY'
import hashlib
import os
import sys

photos, manifest, project = sys.argv[1], sys.argv[2], sys.argv[3]
expected = []
with open(manifest, encoding="utf-8") as handle:
    for line in handle:
        line = line.rstrip("\n")
        if not line:
            continue
        rel, size, nsec, digest = line.split("\t")
        expected.append((rel, int(size), int(nsec), digest))
if not expected:
    raise SystemExit("originals.manifest is empty")
for rel, size, nsec, digest in expected:
    path = os.path.join(photos, rel)
    st = os.stat(path)
    got_ns = getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000))
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    if st.st_size != size or got_ns != nsec or hasher.hexdigest() != digest:
        raise SystemExit(f"source changed: {rel}")
    copy_dir = os.path.join(project, "originals") if project else ""
    copy = os.path.join(copy_dir, rel) if copy_dir else ""
    if copy and os.path.isfile(copy) and hasattr(os.stat(path), "st_ino"):
        if os.stat(path).st_ino == os.stat(copy).st_ino and os.stat(path).st_dev == os.stat(copy).st_dev:
            raise SystemExit(f"project original shares inode with source: {rel}")
PY
}

wait_done_jsonl() {
  local start now elapsed line timeout_s
  if [[ "${MODE:-probe}" == "500" ]]; then
    timeout_s=2160
  else
    timeout_s=480
  fi
  start="$(date +%s)"
  while true; do
    now="$(date +%s)"
    elapsed=$((now - start))
    if (( elapsed >= timeout_s )); then
      echo "Path B runner did not reach milestone done within ${timeout_s}s" >&2
      dump_health_timeout_diagnostics
      return 1
    fi
    if [[ -f "${EVIDENCE_DIR}/milestones.jsonl" ]]; then
      while IFS= read -r line || [[ -n "$line" ]]; do
        case "$line" in
          *'"milestone": "fail"'*|*'"milestone":"fail"'*)
            echo "QA runner wrote milestone fail: ${line}" >&2
            return 1
            ;;
          *'"milestone": "done"'*|*'"milestone":"done"'*)
            ACCEPTED_FILES="$(
              python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("accepted_files") or 0)' "$line" 2>/dev/null || printf '0'
            )"
            PREVIEW_NATURAL_WIDTH="$(
              python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("preview_natural_width") or 0)' "$line" 2>/dev/null || printf '0'
            )"
            return 0
            ;;
        esac
      done < "${EVIDENCE_DIR}/milestones.jsonl"
    fi
    sleep 1
  done
}

join_rss_milestones() {
  local envfile
  envfile="${EVIDENCE_DIR}/rss_join.env"
  python3 - "${EVIDENCE_DIR}/milestones.jsonl" "${EVIDENCE_DIR}/rss.jsonl" "$envfile" <<'PY'
import json
import sys
from datetime import datetime, timezone

milestones_path, rss_path, env_path = sys.argv[1], sys.argv[2], sys.argv[3]

def parse_t(value):
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(timezone.utc)

def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            rows.append(json.loads(raw))
    return rows

milestones = load_jsonl(milestones_path)
rss = load_jsonl(rss_path)
by_name = {}
for row in milestones:
    name = row.get("milestone")
    if name:
        by_name[name] = row

required = ("idle", "import_complete", "process_complete", "first_preview")
joined = {}
for name in required:
    row = by_name.get(name)
    if not row or "t" not in row:
        raise SystemExit(f"missing milestone {name}")
    target = parse_t(row["t"])
    chosen = None
    for sample in rss:
        if "t" not in sample:
            continue
        stamp = parse_t(sample["t"])
        delta = (target - stamp).total_seconds()
        if 0 <= delta <= 5:
            chosen = sample
    if chosen is None:
        raise SystemExit(f"RSS join miss for {name}")
    sidecar = chosen.get("sidecar_mb")
    ui = chosen.get("ui_mb")
    if sidecar in (None, "", 0, 0.0, "0", "0.00"):
        raise SystemExit(f"sidecar RSS missing or 0 at {name}")
    joined[name] = (float(sidecar), float(ui or 0))

peak_sidecar = max(float(sample.get("sidecar_mb") or 0) for sample in rss) if rss else 0
peak_ui = max(float(sample.get("ui_mb") or 0) for sample in rss) if rss else 0
idle = joined["idle"]
imp = joined["import_complete"]
proc = joined["process_complete"]
prev = joined["first_preview"]
with open(env_path, "w", encoding="utf-8") as handle:
    handle.write(f"RSS_IDLE_SIDECAR={idle[0]}\nRSS_IDLE_UI={idle[1]}\n")
    handle.write(f"RSS_IMPORT_SIDECAR={imp[0]}\nRSS_IMPORT_UI={imp[1]}\n")
    handle.write(f"RSS_PROCESS_SIDECAR={proc[0]}\nRSS_PROCESS_UI={proc[1]}\n")
    handle.write(f"RSS_PREVIEW_SIDECAR={prev[0]}\nRSS_PREVIEW_UI={prev[1]}\n")
    handle.write(f"RSS_PEAK_SIDECAR={peak_sidecar}\nRSS_PEAK_UI={peak_ui}\n")
PY
  # shellcheck disable=SC1090
  source "$envfile"
  if [[ -f "${EVIDENCE_DIR}/milestones.jsonl" ]]; then
    IMPORT_WORKERS="$(
      python3 - "${EVIDENCE_DIR}/milestones.jsonl" <<'PY'
import json, sys
workers = 0
for raw in open(sys.argv[1], encoding="utf-8"):
    raw = raw.strip()
    if not raw:
        continue
    row = json.loads(raw)
    if row.get("milestone") == "idle":
        workers = int(row.get("import_workers") or 0)
print(workers)
PY
    )"
  fi
}

finish_from_evidence() {
  if [[ ! -f "${EVIDENCE_DIR}/milestones.jsonl" ]]; then
    echo "milestones.jsonl missing" >&2
    return 1
  fi
  if ! grep -E -q '"milestone":[[:space:]]*"done"' "${EVIDENCE_DIR}/milestones.jsonl"; then
    echo "milestone done missing" >&2
    return 1
  fi
  ACCEPTED_FILES="$(
    python3 - "${EVIDENCE_DIR}/milestones.jsonl" <<'PY'
import json, sys
accepted = 0
for raw in open(sys.argv[1], encoding="utf-8"):
    raw = raw.strip()
    if not raw:
        continue
    row = json.loads(raw)
    if row.get("milestone") == "done":
        accepted = int(row.get("accepted_files") or 0)
print(accepted)
PY
  )"
  PREVIEW_NATURAL_WIDTH="$(
    python3 - "${EVIDENCE_DIR}/milestones.jsonl" <<'PY'
import json, sys
width = 0
for raw in open(sys.argv[1], encoding="utf-8"):
    raw = raw.strip()
    if not raw:
        continue
    row = json.loads(raw)
    if row.get("milestone") in ("done", "first_preview"):
        width = int(row.get("preview_natural_width") or width)
print(width)
PY
  )"
  if ! join_rss_milestones; then
    RESULT="fail"
    FAIL_REASON="RSS join failed"
    return 1
  fi
  if ! verify_originals; then
    ORIGINALS_UNCHANGED=false
    RESULT="fail"
    FAIL_REASON="originals changed"
    return 1
  fi
  if [[ "${PREVIEW_NATURAL_WIDTH:-0}" -le 0 ]]; then
    RESULT="fail"
    FAIL_REASON="preview_natural_width was not > 0"
    return 1
  fi
  RESULT="pass"
  FAIL_REASON=""
  write_result_json "${EVIDENCE_DIR}/result.json"
}

launch_windows() {
  local installer
  installer="$(find_nsis)"
  if [[ ! -f "$installer" ]]; then
    echo "NSIS installer not found: ${installer}" >&2
    return 1
  fi
  if ! webview2_present; then
    echo "WebView2 runtime is missing" >&2
    return 1
  fi
  kill_windows_leftovers
  "$installer" //S
  INSTALLED_EXE="${LOCALAPPDATA}/FramePilot/framepilot-desktop.exe"
  UNINSTALL_EXE="${LOCALAPPDATA}/FramePilot/uninstall.exe"
  if [[ ! -f "$INSTALLED_EXE" ]]; then
    echo "framepilot-desktop.exe missing after NSIS /S (productName=FramePilot)" >&2
    return 1
  fi
  export_qa_env
  export WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--disable-gpu --use-gl=swiftshader --disable-features=CalculateNativeWinOcclusion --disable-backgrounding-occluded-windows --disable-renderer-backgrounding'
  local ps1 exe_win
  ps1="${EVIDENCE_DIR}/launch-gui.ps1"
  exe_win="$(native_path "$INSTALLED_EXE")"
  cat > "$ps1" <<EOF
\$ErrorActionPreference = 'Stop'
\$env:FRAMEPILOT_DESKTOP_QA = '1'
\$env:FRAMEPILOT_DATA_DIR = '$(native_path "$DATA_DIR")'
\$env:FRAMEPILOT_DESKTOP_QA_PHOTOS = '$(native_path "$PHOTOS_DIR")'
\$env:FRAMEPILOT_DESKTOP_QA_PROJECT = '$(native_path "$PROJECT_DIR")'
\$env:FRAMEPILOT_DESKTOP_QA_EVIDENCE = '$(native_path "$EVIDENCE_DIR")'
\$env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = '$WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'
\$env:no_proxy = '127.0.0.1,localhost,::1'
\$env:NO_PROXY = '127.0.0.1,localhost,::1'
\$p = Start-Process -FilePath '$exe_win' -WindowStyle Normal -PassThru
Write-Output \$p.Id
EOF
  GUI_PID="$(
    MSYS2_ARG_CONV_EXCL='*' powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(native_path "$ps1")" | tr -d '\r' | tail -n 1
  )"
  if [[ ! "$GUI_PID" =~ ^[1-9][0-9]*$ ]]; then
    echo "Start-Process did not return a PID (got ${GUI_PID:-empty}); falling back to bash launch" >&2
    "$INSTALLED_EXE" &
    GUI_PID=$!
  fi
  OPENED=1
}

launch_macos() {
  local dmg mount_root attach_out app_src bundle_exe open_rc i
  dmg="$(find_dmg)"
  if [[ "$dmg" != /* ]]; then
    dmg="$(pwd)/${dmg}"
  fi
  if [[ ! -f "$dmg" ]]; then
    echo "dmg not found: ${dmg}" >&2
    return 1
  fi
  mkdir -p "$APP_DIR"
  mount_root="${PREFIX}/mnt"
  mkdir -p "$mount_root"
  attach_out="$(hdiutil attach -nobrowse -mountroot "$mount_root" "$dmg")"
  ATTACH_DEV="$(printf '%s\n' "$attach_out" | awk '/^\/dev\// { print $1; exit }')"
  if [[ -z "$ATTACH_DEV" ]]; then
    echo "hdiutil attach did not report a /dev device" >&2
    return 1
  fi
  app_src=""
  while IFS= read -r -d '' candidate; do
    app_src="$candidate"
    break
  done < <(find "$mount_root" -maxdepth 4 -name 'FramePilot.app' -type d -print0)
  if [[ -z "$app_src" ]]; then
    while IFS= read -r -d '' candidate; do
      app_src="$candidate"
      break
    done < <(find "$mount_root" -maxdepth 4 -name '*.app' -type d -print0)
  fi
  if [[ -z "$app_src" || ! -d "$app_src" ]]; then
    echo "FramePilot.app not found in attached dmg" >&2
    return 1
  fi
  APP_COPY="${APP_DIR}/$(basename "$app_src")"
  rm -rf "$APP_COPY"
  cp -R "$app_src" "$APP_COPY"
  xattr -cr "$APP_COPY"
  kill_macos_leftovers
  export_qa_env
  bundle_exe="$(macos_bundle_executable "$APP_COPY")"
  if [[ -z "$bundle_exe" || ! -f "$bundle_exe" ]]; then
    echo "could not discover CFBundleExecutable under ${APP_COPY}/Contents/MacOS" >&2
    return 1
  fi
  # Launch Services (`open --env`) so WKWebView gets an Aqua session. Direct
  # Contents/MacOS child inherit env but often never paints on GHA.
  set +e
  open -n "$APP_COPY" \
    --env "FRAMEPILOT_DESKTOP_QA=1" \
    --env "FRAMEPILOT_DATA_DIR=${FRAMEPILOT_DATA_DIR}" \
    --env "FRAMEPILOT_DESKTOP_QA_PHOTOS=${FRAMEPILOT_DESKTOP_QA_PHOTOS}" \
    --env "FRAMEPILOT_DESKTOP_QA_PROJECT=${FRAMEPILOT_DESKTOP_QA_PROJECT}" \
    --env "FRAMEPILOT_DESKTOP_QA_EVIDENCE=${FRAMEPILOT_DESKTOP_QA_EVIDENCE}" \
    --env "no_proxy=127.0.0.1,localhost,::1" \
    --env "NO_PROXY=127.0.0.1,localhost,::1"
  open_rc=$?
  set -e
  if [[ "$open_rc" -ne 0 ]]; then
    echo "open --env failed (rc=${open_rc}); launching bundle executable as child" >&2
    "$bundle_exe" &
    GUI_PID=$!
  else
    GUI_PID=""
    for i in 1 2 3 4 5 6 7 8 9 10; do
      GUI_PID="$(pgrep -n -f "${APP_COPY}/Contents/MacOS/" || true)"
      if [[ -n "$GUI_PID" ]]; then
        break
      fi
      sleep 0.5
    done
  fi
  osascript -e 'tell application "FramePilot" to activate' >/dev/null 2>&1 || true
  OPENED=1
}

run_packaged() {
  local port
  if [[ "$WIDTH" -eq 160 || "$HEIGHT" -eq 120 ]]; then
    RESULT="fail"
    FAIL_REASON="refusing default 160x120 dataset dimensions"
    exit 1
  fi
  generate_dataset
  snapshot_originals
  start_rss_sampler
  case "$(os_label)" in
    windows) launch_windows ;;
    macos) launch_macos ;;
    *)
      RESULT="fail"
      FAIL_REASON="packaged NSIS/DMG GUI launch is not supported on $(os_label)"
      exit 1
      ;;
  esac
  set +e
  port="$(wait_health)"
  set -e
  if [[ -f "${EVIDENCE_DIR}/app_version.txt" ]]; then
    APP_VERSION="$(cat "${EVIDENCE_DIR}/app_version.txt" || true)"
  fi
  if [[ -z "${port:-}" ]]; then
    RESULT="fail"
    FAIL_REASON="sidecar GET /health did not return 200 within 60s"
    exit 1
  fi
  if ! wait_idle_jsonl; then
    RESULT="fail"
    FAIL_REASON="no idle JSONL within 90s after /health 200"
    exit 1
  fi
  if ! wait_done_jsonl; then
    RESULT="fail"
    FAIL_REASON="Path B runner did not reach milestone done"
    exit 1
  fi
  if ! join_rss_milestones; then
    RESULT="fail"
    FAIL_REASON="RSS join failed"
    exit 1
  fi
  if ! verify_originals; then
    ORIGINALS_UNCHANGED=false
    RESULT="fail"
    FAIL_REASON="originals changed"
    exit 1
  fi
  if [[ "${PREVIEW_NATURAL_WIDTH:-0}" -le 0 ]]; then
    RESULT="fail"
    FAIL_REASON="preview_natural_width was not > 0"
    exit 1
  fi
  RESULT="pass"
  FAIL_REASON=""
  write_result_json "${EVIDENCE_DIR}/result.json"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --resolve-python)
      RESOLVE_PYTHON=1
      shift
      ;;
    --rss-kb)
      if [[ $# -lt 2 ]]; then
        echo "--rss-kb requires a kilobyte value" >&2
        exit 1
      fi
      RSS_KB="$2"
      shift 2
      ;;
    --macos-exec)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        echo "--macos-exec requires an .app path" >&2
        exit 1
      fi
      MACOS_EXEC="$2"
      shift 2
      ;;
    --parse-windows-listen)
      if [[ $# -lt 3 || -z "${2:-}" || -z "${3:-}" ]]; then
        echo "--parse-windows-listen requires NETSTAT and TASKLIST files" >&2
        exit 1
      fi
      PARSE_NETSTAT="$2"
      PARSE_TASKLIST="$3"
      shift 3
      ;;
    --snapshot-originals)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        echo "--snapshot-originals requires a prefix directory" >&2
        exit 1
      fi
      SNAPSHOT_PREFIX="$2"
      shift 2
      ;;
    --finish-from-evidence)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        echo "--finish-from-evidence requires a prefix directory" >&2
        exit 1
      fi
      FINISH_PREFIX="$2"
      shift 2
      ;;
    --wipe-scratch)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        echo "--wipe-scratch requires a prefix directory" >&2
        exit 1
      fi
      WIPE_PREFIX="$2"
      shift 2
      ;;
    --probe)
      MODE="probe"
      COUNT=1
      shift
      ;;
    --count)
      if [[ $# -lt 2 || ! "$2" =~ ^[1-9][0-9]*$ ]]; then
        echo "--count requires a positive integer" >&2
        exit 1
      fi
      COUNT="$2"
      if [[ "$COUNT" -eq 1 ]]; then
        MODE="probe"
      else
        MODE="500"
      fi
      shift 2
      ;;
    --installer)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        echo "--installer requires a path" >&2
        exit 1
      fi
      INSTALLER="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$RESOLVE_PYTHON" -eq 1 ]]; then
  resolve_python
  exit 0
fi

if [[ -n "$RSS_KB" ]]; then
  rss_mb_from_ps_kb "$RSS_KB"
  exit 0
fi

if [[ -n "$MACOS_EXEC" ]]; then
  macos_bundle_executable "$MACOS_EXEC"
  exit $?
fi

if [[ -n "$PARSE_NETSTAT" ]]; then
  parse_windows_listen "$PARSE_NETSTAT" "$PARSE_TASKLIST"
  exit $?
fi

bind_prefix_dirs() {
  PREFIX="$1"
  PHOTOS_DIR="${PREFIX}/photos"
  PROJECT_DIR="${PREFIX}/project"
  DATA_DIR="${PREFIX}/data"
  EVIDENCE_DIR="${PREFIX}/evidence"
  APP_DIR="${PREFIX}/app"
}

if [[ -n "$WIPE_PREFIX" ]]; then
  bind_prefix_dirs "$WIPE_PREFIX"
  wipe_scratch_siblings
  exit 0
fi

if [[ -n "$SNAPSHOT_PREFIX" ]]; then
  bind_prefix_dirs "$SNAPSHOT_PREFIX"
  mkdir -p "$PHOTOS_DIR" "$EVIDENCE_DIR"
  snapshot_originals
  exit 0
fi

if [[ -n "$FINISH_PREFIX" ]]; then
  bind_prefix_dirs "$FINISH_PREFIX"
  MODE="${MODE:-probe}"
  COUNT="${COUNT:-1}"
  if finish_from_evidence; then
    exit 0
  fi
  write_result_json "${EVIDENCE_DIR}/result.json" || true
  exit 1
fi

if [[ -z "$MODE" || -z "$COUNT" ]]; then
  usage
  exit 1
fi

prepare_scratch
trap cleanup EXIT

if [[ "$os" == "Linux" ]]; then
  linux_skip
fi

run_packaged
