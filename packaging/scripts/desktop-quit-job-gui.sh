#!/usr/bin/env bash
# Packaged macOS quit+job matrix (leftover #181, Path B start + production quit).
# Linux/WSL2: skip is not pass (exit 2) before generating photos.
# Do not print result=pass on Linux. Do not call npm generate:synthetic.
# Do not set PYTHONPATH. Do not call macos-dmg-gui-smoke.sh or desktop-500-gui.sh.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

WIDTH=3000
HEIGHT=2000
QUALITY=88
COUNT=500
MODE=""
INSTALLER=""
RESULT="fail"
FAIL_REASON=""
APP_VERSION=""
ORIGINALS_UNCHANGED=true
LEFTOVER_LISTEN=false
CLEANUP_DONE=0
GUI_PID=""
ATTACH_DEV=""
APP_COPY=""
OPENED=0
ROW=""
ROW_QUIT_CLEAN="fail"
ROW_QUIT_IMPORT="fail"
ROW_QUIT_PROCESSING="fail"
ROW_QUIT_EXPORT="fail"

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
  printf '%s\n' "${HOME}/.cache/framepilot-desktop-quit-job"
}

python_is_usable() {
  local candidate="${1:-}"
  [[ -n "$candidate" ]] || return 1
  if [[ -x "$candidate" ]]; then
    return 0
  fi
  if [[ "$candidate" == *.exe && -f "$candidate" ]]; then
    return 0
  fi
  return 1
}

resolve_python() {
  local python_bin=""
  if python_is_usable "${PYTHON:-}"; then
    python_bin="$PYTHON"
  elif python_is_usable "$repo_root/.venv/bin/python"; then
    python_bin="$repo_root/.venv/bin/python"
  else
    echo "python interpreter not found (PYTHON, .venv/bin/python)" >&2
    return 1
  fi
  printf '%s\n' "$python_bin"
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
  echo "usage: $0 --probe|--count N [--installer PATH]" >&2
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
  "mode": $(json_escape "${MODE:-quit-job-matrix}"),
  "result": $(json_escape "$RESULT"),
  "os": ${os_json},
  "uname": ${uname_json},
  "timestamp": $(json_escape "$ts"),
  "app_version": ${version_json},
  "ci_run_url": $(json_escape "${url:-}"),
  "native_dialog": "stubbed",
  "count": ${COUNT:-0},
  "width": ${WIDTH},
  "height": ${HEIGHT},
  "quality": ${QUALITY},
  "rows": {
    "quit-clean": $(json_escape "$ROW_QUIT_CLEAN"),
    "quit-import": $(json_escape "$ROW_QUIT_IMPORT"),
    "quit-processing": $(json_escape "$ROW_QUIT_PROCESSING"),
    "quit-export": $(json_escape "$ROW_QUIT_EXPORT")
  },
  "originals_unchanged": ${ORIGINALS_UNCHANGED},
  "leftover_listen": ${LEFTOVER_LISTEN},
  "fail_reason": ${fail_json}
}
EOF
}

copy_row_evidence() {
  local dest sidecar row="${1:-}"
  dest="${RUNNER_TEMP:-/tmp}/desktop-quit-job/${row}"
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

copy_summary_evidence() {
  local dest
  dest="${RUNNER_TEMP:-/tmp}/desktop-quit-job"
  mkdir -p "$dest"
  if [[ -f "${PREFIX}/evidence/result.json" ]]; then
    cp "${PREFIX}/evidence/result.json" "${dest}/result.json"
  fi
}

kill_macos_leftovers() {
  osascript -e 'tell application "FramePilot" to quit' >/dev/null 2>&1 || true
  osascript -e 'tell application id "com.framepilot.app" to quit' >/dev/null 2>&1 || true
  pkill -f '/FramePilot\.app/Contents/MacOS/' >/dev/null 2>&1 || true
  pkill -f 'framepilot-api' >/dev/null 2>&1 || true
  sleep 1
}

wipe_launch_siblings() {
  rm -rf "${PROJECT_DIR}" "${DATA_DIR}" "${EVIDENCE_DIR}"
  mkdir -p "${PROJECT_DIR}" "${DATA_DIR}" "${EVIDENCE_DIR}"
}

wipe_scratch_siblings() {
  kill_macos_leftovers || true
  rm -rf "${PHOTOS_DIR}" "${PROJECT_DIR}" "${DATA_DIR}" "${EVIDENCE_DIR}" "${APP_DIR}" 2>/dev/null || true
}

cleanup() {
  local status=$?
  set +e
  if [[ "$CLEANUP_DONE" -eq 1 ]]; then
    return 0
  fi
  CLEANUP_DONE=1
  if [[ "$OPENED" -eq 1 ]]; then
    quit_gui
  fi
  if [[ -n "${ATTACH_DEV}" ]]; then
    hdiutil detach "${ATTACH_DEV}" >/dev/null 2>&1 || hdiutil detach "${ATTACH_DEV}" -force >/dev/null 2>&1
    ATTACH_DEV=""
  fi
  if [[ -n "${PREFIX:-}" ]]; then
    mkdir -p "${PREFIX}/evidence"
    write_result_json "${PREFIX}/evidence/result.json" || true
    copy_summary_evidence || true
    wipe_scratch_siblings || true
  fi
  return "$status"
}

quit_gui() {
  osascript -e 'tell application "FramePilot" to quit' >/dev/null 2>&1 || true
  osascript -e 'tell application id "com.framepilot.app" to quit' >/dev/null 2>&1 || true
  if [[ -n "${GUI_PID}" ]]; then
    kill "${GUI_PID}" >/dev/null 2>&1 || true
  fi
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
  echo "skip is not pass: uname -s is ${os}; packaged DMG quit+job matrix cannot run here" >&2
  RESULT="skip"
  FAIL_REASON="skip is not pass: uname -s is ${os}; packaged DMG quit+job matrix cannot run here"
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
  "$python_bin" -m app.devtools.synthetic_dataset \
    --output "$PHOTOS_DIR" \
    --count "$COUNT" \
    --width "$WIDTH" \
    --height "$HEIGHT" \
    --quality "$QUALITY"
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

port_from_ps_argv() {
  local args host port
  while IFS= read -r args; do
    case "$args" in
      *desktop-quit-job*|*desktop-500-gui*)
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

framepilot_api_listen_count() {
  lsof -nP -c framepilot-api -iTCP -sTCP:LISTEN 2>/dev/null | grep -c 'LISTEN' || true
}

export_qa_env() {
  local mode="${1:-}"
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY || true
  export no_proxy='127.0.0.1,localhost,::1'
  export NO_PROXY='127.0.0.1,localhost,::1'
  export FRAMEPILOT_DATA_DIR="$DATA_DIR"
  export FRAMEPILOT_DESKTOP_QA=1
  export FRAMEPILOT_DESKTOP_QA_PHOTOS="$PHOTOS_DIR"
  export FRAMEPILOT_DESKTOP_QA_PROJECT="$PROJECT_DIR"
  export FRAMEPILOT_DESKTOP_QA_EVIDENCE="$EVIDENCE_DIR"
  export FRAMEPILOT_DESKTOP_QA_MODE="$mode"
}

dump_health_timeout_diagnostics() {
  echo "--- health-timeout diagnostics ---" >&2
  echo "os=$(os_label) uname=${uname_s} data_dir=${DATA_DIR:-} row=${ROW:-}" >&2
  ps -axww -o pid,args= 2>/dev/null | head -n 80 >&2 || true
  if [[ -n "${DATA_DIR:-}" && -f "${DATA_DIR}/logs/sidecar.log" ]]; then
    echo "--- sidecar.log (stderr; last 80) ---" >&2
    tail -n 80 "${DATA_DIR}/logs/sidecar.log" >&2 || true
  fi
  if [[ -f "${EVIDENCE_DIR}/milestones.jsonl" ]]; then
    echo "--- milestones.jsonl ---" >&2
    cat "${EVIDENCE_DIR}/milestones.jsonl" >&2 || true
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
        printf '%s\n' "$port"
        return 0
      fi
    fi
    sleep 1
  done
}

jsonl_has_milestone() {
  local name="${1:-}"
  local line
  if [[ ! -f "${EVIDENCE_DIR}/milestones.jsonl" ]]; then
    return 1
  fi
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      *'"milestone": "'"$name"'"'*|*'"milestone":"'"$name"'"'*)
        return 0
        ;;
    esac
  done < "${EVIDENCE_DIR}/milestones.jsonl"
  return 1
}

wait_milestone() {
  local name="${1:-}"
  local timeout_s="${2:-90}"
  local start now elapsed
  start="$(date +%s)"
  while true; do
    now="$(date +%s)"
    elapsed=$((now - start))
    if (( elapsed >= timeout_s )); then
      echo "milestone ${name} not written within ${timeout_s}s" >&2
      dump_health_timeout_diagnostics
      return 1
    fi
    if jsonl_has_milestone "fail"; then
      echo "QA runner wrote milestone fail" >&2
      dump_health_timeout_diagnostics
      return 1
    fi
    if jsonl_has_milestone "$name"; then
      return 0
    fi
    sleep 1
  done
}

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
  echo "no executable under ${macos_dir}" >&2
  return 1
}

snapshot_originals() {
  local manifest
  manifest="${PREFIX}/originals.manifest"
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
  manifest="${PREFIX}/originals.manifest"
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

verify_no_leftover_listen() {
  local count
  count="$(framepilot_api_listen_count)"
  if [[ "${count:-0}" -gt 0 ]]; then
    echo "leftover framepilot-api LISTEN count=${count}" >&2
    lsof -nP -c framepilot-api -iTCP -sTCP:LISTEN >&2 || true
    LEFTOVER_LISTEN=true
    return 1
  fi
  LEFTOVER_LISTEN=false
  return 0
}

wait_app_exit() {
  local timeout_s="${1:-45}"
  local start now elapsed
  start="$(date +%s)"
  while true; do
    now="$(date +%s)"
    elapsed=$((now - start))
    if (( elapsed >= timeout_s )); then
      echo "FramePilot did not exit within ${timeout_s}s after quit" >&2
      return 1
    fi
    if ! pgrep -f '/FramePilot\.app/Contents/MacOS/' >/dev/null 2>&1 \
      && ! pgrep -f 'framepilot-api' >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
}

attach_dmg() {
  local dmg mount_root attach_out app_src bundle_exe
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
  bundle_exe="$(macos_bundle_executable "$APP_COPY")"
  if [[ -z "$bundle_exe" || ! -f "$bundle_exe" ]]; then
    echo "could not discover CFBundleExecutable under ${APP_COPY}/Contents/MacOS" >&2
    return 1
  fi
}

launch_macos() {
  local mode="${1:-}"
  local bundle_exe open_rc i
  kill_macos_leftovers
  export_qa_env "$mode"
  bundle_exe="$(macos_bundle_executable "$APP_COPY")"
  set +e
  open -n "$APP_COPY" \
    --env "FRAMEPILOT_DESKTOP_QA=1" \
    --env "FRAMEPILOT_DATA_DIR=${FRAMEPILOT_DATA_DIR}" \
    --env "FRAMEPILOT_DESKTOP_QA_PHOTOS=${FRAMEPILOT_DESKTOP_QA_PHOTOS}" \
    --env "FRAMEPILOT_DESKTOP_QA_PROJECT=${FRAMEPILOT_DESKTOP_QA_PROJECT}" \
    --env "FRAMEPILOT_DESKTOP_QA_EVIDENCE=${FRAMEPILOT_DESKTOP_QA_EVIDENCE}" \
    --env "FRAMEPILOT_DESKTOP_QA_MODE=${mode}" \
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

jsonl_field() {
  local milestone="${1:-}"
  local field="${2:-}"
  python3 - "${EVIDENCE_DIR}/milestones.jsonl" "$milestone" "$field" <<'PY'
import json, sys
path, milestone, field = sys.argv[1], sys.argv[2], sys.argv[3]
value = ""
for raw in open(path, encoding="utf-8"):
    raw = raw.strip()
    if not raw:
        continue
    row = json.loads(raw)
    if row.get("milestone") == milestone and field in row:
        value = row.get(field) or ""
print(value)
PY
}

verify_quit_dialog_evidence() {
  local expected_title="${1:-}"
  python3 - "${EVIDENCE_DIR}/milestones.jsonl" "$expected_title" <<'PY'
import json, sys
path, expected = sys.argv[1], sys.argv[2]
dialog = None
choice = None
for raw in open(path, encoding="utf-8"):
    raw = raw.strip()
    if not raw:
        continue
    row = json.loads(raw)
    if row.get("milestone") == "quit_dialog":
        dialog = row
    if row.get("milestone") == "quit_choice":
        choice = row
if not dialog:
    raise SystemExit("quit_dialog milestone missing")
if dialog.get("title") != expected:
    raise SystemExit(f"quit dialog title {dialog.get('title')!r} != {expected!r}")
buttons = dialog.get("buttons") or []
missing = [name for name in ("stay", "cancel_and_quit", "quit_anyway") if name not in buttons]
if missing:
    raise SystemExit(f"quit dialog missing buttons: {','.join(missing)}")
if not choice or choice.get("choice") != "cancel_and_quit":
    raise SystemExit("quit_choice cancel_and_quit missing")
PY
}

verify_job_cancelled() {
  local job_id="${1:-}"
  local db="${DATA_DIR}/framepilot.db"
  if [[ ! -f "$db" ]]; then
    echo "framepilot.db missing after quit" >&2
    return 1
  fi
  python3 - "$db" "$job_id" <<'PY'
import sqlite3
import sys

db, job_id = sys.argv[1], sys.argv[2]
con = sqlite3.connect(db)
row = con.execute(
    "SELECT status, cancellation_requested FROM processingjob WHERE id = ?",
    (job_id,),
).fetchone()
if row is None:
    raise SystemExit(f"job {job_id} not found")
status, requested = row
if status != "cancelled":
    raise SystemExit(f"job {job_id} status {status!r} is not cancelled")
if not requested:
    raise SystemExit(f"job {job_id} cancellation_requested is false")
PY
}

verify_groups_cleared() {
  local db="${DATA_DIR}/framepilot.db"
  python3 - "$db" <<'PY'
import sqlite3
import sys

con = sqlite3.connect(sys.argv[1])
count = con.execute("SELECT COUNT(*) FROM photogroup").fetchone()[0]
if count != 0:
    raise SystemExit(f"partial groups remain: {count}")
PY
}

verify_export_artifacts_removed() {
  python3 - "${PROJECT_DIR}" "${DATA_DIR}/framepilot.db" <<'PY'
import os
import sqlite3
import sys
from pathlib import Path

project = Path(sys.argv[1])
db = sys.argv[2]
con = sqlite3.connect(db)
row = con.execute(
    "SELECT status FROM exportrecord ORDER BY created_at DESC, id DESC LIMIT 1"
).fetchone()
if row is None:
    raise SystemExit("exportrecord missing")
if row[0] not in {"cancelled", "failed"}:
    raise SystemExit(f"export status {row[0]!r} is not cancelled/failed")
export_root = project / "exports"
if export_root.exists():
    leftovers = [path for path in export_root.rglob("*") if path.is_file()]
    if leftovers:
        raise SystemExit("partial export artifacts remain: " + ", ".join(str(p) for p in leftovers[:8]))
PY
}

set_row_result() {
  local row="${1:-}"
  local value="${2:-}"
  case "$row" in
    quit-clean) ROW_QUIT_CLEAN="$value" ;;
    quit-import) ROW_QUIT_IMPORT="$value" ;;
    quit-processing) ROW_QUIT_PROCESSING="$value" ;;
    quit-export) ROW_QUIT_EXPORT="$value" ;;
  esac
}

run_row() {
  local row="${1:-}"
  local running_ms port
  ROW="$row"
  EVIDENCE_DIR="${PREFIX}/evidence/${row}"
  wipe_launch_siblings
  mkdir -p "$EVIDENCE_DIR"
  launch_macos "$row"
  set +e
  port="$(wait_health)"
  set -e
  if [[ -z "${port:-}" ]]; then
    FAIL_REASON="${row}: sidecar GET /health did not return 200 within 60s"
    return 1
  fi
  if ! wait_milestone "idle" 90; then
    FAIL_REASON="${row}: no idle JSONL within 90s after /health 200"
    return 1
  fi
  case "$row" in
    quit-clean)
      osascript -e 'tell application "FramePilot" to quit' >/dev/null 2>&1 || true
      osascript -e 'tell application id "com.framepilot.app" to quit' >/dev/null 2>&1 || true
      if ! wait_app_exit 45; then
        FAIL_REASON="${row}: app did not exit after clean quit"
        return 1
      fi
      OPENED=0
      if ! verify_no_leftover_listen; then
        FAIL_REASON="${row}: leftover framepilot-api LISTEN"
        return 1
      fi
      ;;
    *)
      case "$row" in
        quit-import) running_ms="import_running" ;;
        quit-processing) running_ms="process_running" ;;
        quit-export) running_ms="export_running" ;;
      esac
      if ! wait_milestone "$running_ms" 900; then
        FAIL_REASON="${row}: ${running_ms} not written before complete"
        return 1
      fi
      # Do not Apple-Event quit here. On GHA macos-latest, `tell application
      # to quit` terminates the process without ExitRequested / handle_close_requested
      # (sidecar log has no GET /api/projects after import). Path B invokes
      # production handle_close_requested via fail-closed qa_request_close.
      if ! wait_milestone "quit_dialog" 60; then
        FAIL_REASON="${row}: quit dialog did not appear"
        return 1
      fi
      if ! wait_milestone "quit_choice" 30; then
        FAIL_REASON="${row}: quit_choice not written"
        return 1
      fi
      case "$row" in
        quit-import)
          if ! verify_quit_dialog_evidence "Import is still running"; then
            FAIL_REASON="${row}: quit dialog evidence failed"
            return 1
          fi
          ;;
        quit-processing)
          if ! verify_quit_dialog_evidence "Grouping and ranking is still running"; then
            FAIL_REASON="${row}: quit dialog evidence failed"
            return 1
          fi
          ;;
        quit-export)
          if ! verify_quit_dialog_evidence "Export is still running"; then
            FAIL_REASON="${row}: quit dialog evidence failed"
            return 1
          fi
          ;;
      esac
      if ! wait_app_exit 60; then
        FAIL_REASON="${row}: app did not exit after cancel-and-quit"
        return 1
      fi
      OPENED=0
      if ! verify_no_leftover_listen; then
        FAIL_REASON="${row}: leftover framepilot-api LISTEN"
        return 1
      fi
      if ! job_cancel_msg="$(verify_job_cancelled "$(jsonl_field "$running_ms" "job_id")" 2>&1)"; then
        FAIL_REASON="${row}: job did not end cancelled${job_cancel_msg:+ (${job_cancel_msg})}"
        return 1
      fi
      if [[ "$row" == "quit-processing" ]] && ! verify_groups_cleared; then
        FAIL_REASON="${row}: partial groups were not cleared"
        return 1
      fi
      if [[ "$row" == "quit-export" ]] && ! verify_export_artifacts_removed; then
        FAIL_REASON="${row}: partial export artifacts remain"
        return 1
      fi
      ;;
  esac
  if ! verify_originals; then
    ORIGINALS_UNCHANGED=false
    FAIL_REASON="${row}: originals changed"
    return 1
  fi
  set_row_result "$row" "pass"
  RESULT="pass"
  FAIL_REASON=""
  write_result_json "${EVIDENCE_DIR}/result.json"
  copy_row_evidence "$row"
  RESULT="fail"
  return 0
}

run_matrix() {
  local row
  if [[ "$WIDTH" -eq 160 || "$HEIGHT" -eq 120 ]]; then
    RESULT="fail"
    FAIL_REASON="refusing default 160x120 dataset dimensions"
    exit 1
  fi
  generate_dataset
  snapshot_originals
  attach_dmg
  for row in quit-clean quit-import quit-processing quit-export; do
    if ! run_row "$row"; then
      write_result_json "${EVIDENCE_DIR}/result.json" || true
      copy_row_evidence "$row" || true
      RESULT="fail"
      exit 1
    fi
  done
  if [[ "$ROW_QUIT_CLEAN" != "pass" || "$ROW_QUIT_IMPORT" != "pass" \
    || "$ROW_QUIT_PROCESSING" != "pass" || "$ROW_QUIT_EXPORT" != "pass" ]]; then
    RESULT="fail"
    FAIL_REASON="not all four Darwin rows passed"
    exit 1
  fi
  RESULT="pass"
  FAIL_REASON=""
  EVIDENCE_DIR="${PREFIX}/evidence"
  mkdir -p "$EVIDENCE_DIR"
  write_result_json "${EVIDENCE_DIR}/result.json"
  copy_summary_evidence
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --probe)
      MODE="probe"
      COUNT=30
      shift
      ;;
    --count)
      if [[ $# -lt 2 || ! "$2" =~ ^[1-9][0-9]*$ ]]; then
        echo "--count requires a positive integer" >&2
        exit 1
      fi
      COUNT="$2"
      MODE="quit-job-matrix"
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

if [[ -z "$MODE" ]]; then
  MODE="quit-job-matrix"
fi

prepare_scratch
trap cleanup EXIT

if [[ "$os" == "Linux" ]]; then
  linux_skip
fi

if [[ "$os" != "Darwin" ]]; then
  echo "packaged macOS quit+job matrix cannot run on $(os_label)" >&2
  RESULT="fail"
  FAIL_REASON="packaged DMG quit+job matrix is Darwin-only"
  write_result_json "${EVIDENCE_DIR}/result.json" || true
  exit 1
fi

run_matrix
