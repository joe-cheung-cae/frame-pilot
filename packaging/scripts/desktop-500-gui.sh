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
RESULT="fail"
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
  echo "usage: $0 --probe|--count N|--resolve-python|--rss-kb KB [--installer PATH]" >&2
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
    "idle": {"sidecar": null, "ui": null},
    "import_complete": {"sidecar": null, "ui": null},
    "process_complete": {"sidecar": null, "ui": null},
    "first_preview": {"sidecar": null, "ui": null}
  },
  "rss_peak_mb": {"sidecar": null, "ui": null},
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
  sidecar="${DATA_DIR}/logs/sidecar.log"
  if [[ -f "$sidecar" ]]; then
    tail -n 200 "$sidecar" > "${dest}/sidecar.log.excerpt" 2>/dev/null || true
  fi
}

wipe_scratch_siblings() {
  rm -rf "${PHOTOS_DIR}" "${PROJECT_DIR}" "${DATA_DIR}" "${EVIDENCE_DIR}"
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
      taskkill //F //IM framepilot-desktop.exe >/dev/null 2>&1 || true
      taskkill //F //IM framepilot-api.exe >/dev/null 2>&1 || true
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

kill_windows_leftovers() {
  taskkill //F //IM framepilot-desktop.exe >/dev/null 2>&1 || true
  taskkill //F //IM framepilot-api.exe >/dev/null 2>&1 || true
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
  return 1
}

export_qa_env() {
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY || true
  export no_proxy='127.0.0.1,localhost,::1'
  export NO_PROXY='127.0.0.1,localhost,::1'
  export FRAMEPILOT_DATA_DIR="$DATA_DIR"
  export FRAMEPILOT_DESKTOP_QA=1
  export FRAMEPILOT_DESKTOP_QA_PHOTOS="$PHOTOS_DIR"
  export FRAMEPILOT_DESKTOP_QA_PROJECT="$PROJECT_DIR"
  export FRAMEPILOT_DESKTOP_QA_EVIDENCE="$EVIDENCE_DIR"
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
        printf '%s\n' "$port"
        return 0
      fi
    fi
    sleep 1
  done
}

wait_idle_jsonl() {
  local start now elapsed line
  start="$(date +%s)"
  while true; do
    now="$(date +%s)"
    elapsed=$((now - start))
    if (( elapsed >= 90 )); then
      echo "no idle JSONL within 90s after /health 200; SPA never booted" >&2
      ps -axww -o args= 2>/dev/null | head -n 80 >&2 || true
      if [[ -f "${DATA_DIR}/logs/sidecar.log" ]]; then
        tail -n 80 "${DATA_DIR}/logs/sidecar.log" >&2 || true
      fi
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
  export WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--disable-gpu --use-gl=swiftshader --disable-features=CalculateNativeWinOcclusion'
  "$INSTALLED_EXE" &
  GUI_PID=$!
  OPENED=1
}

launch_macos() {
  local dmg mount_root attach_out app_src
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
  if [[ -z "$app_src" || ! -d "$app_src" ]]; then
    echo "FramePilot.app not found in attached dmg" >&2
    return 1
  fi
  APP_COPY="${APP_DIR}/FramePilot.app"
  rm -rf "$APP_COPY"
  cp -R "$app_src" "$APP_COPY"
  xattr -cr "$APP_COPY"
  export_qa_env
  "${APP_COPY}/Contents/MacOS/FramePilot" &
  GUI_PID=$!
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
  RESULT="fail"
  FAIL_REASON="Path B runner did not reach milestone done (QA gate not in this slice)"
  exit 1
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
