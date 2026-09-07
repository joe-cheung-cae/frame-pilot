#!/usr/bin/env bash
# Packaged macOS DMG GUI smoke: attach + launch + loopback GET /health.
# Install+run DoD only. Do not import photos. Do not claim Gatekeeper-clean.
set -euo pipefail

os="$(uname -s)"
if [[ "$os" != "Darwin" ]]; then
  echo "skip is not pass: uname -s is ${os}, not Darwin; cannot mount or launch a .dmg" >&2
  exit 2
fi

if [[ $# -lt 1 || -z "${1:-}" ]]; then
  echo "usage: $0 <path-to-FramePilot.dmg>" >&2
  exit 1
fi

dmg="$1"
if [[ "$dmg" != *.dmg ]]; then
  echo "expected a .dmg path, got: ${dmg}" >&2
  exit 1
fi
if [[ "$dmg" != /* ]]; then
  dmg="$(pwd)/${dmg}"
fi
if [[ ! -f "$dmg" ]]; then
  echo "dmg not found: ${dmg}" >&2
  exit 1
fi

cache="${HOME}/.cache/framepilot-macos-gui-dod"
mkdir -p "$cache"
chmod 700 "$cache"
scratch="$(mktemp -d "${cache}/smoke.XXXXXX")"
chmod 700 "$scratch"

attach_dev=""
app_copy=""
opened=0

cleanup() {
  set +e
  if [[ "$opened" -eq 1 ]]; then
    osascript -e 'tell application "FramePilot" to quit' >/dev/null 2>&1
    osascript -e 'tell application id "com.framepilot.app" to quit' >/dev/null 2>&1
    pids="$(pgrep -f '/FramePilot\.app/Contents/MacOS/' 2>/dev/null || true)"
    while IFS= read -r pid; do
      [[ -n "${pid}" ]] || continue
      # Quit the GUI process; do not kill only framepilot-api.
      kill "${pid}" >/dev/null 2>&1 || true
    done <<< "${pids}"
  fi
  if [[ -n "${attach_dev}" ]]; then
    hdiutil detach "${attach_dev}" >/dev/null 2>&1 || hdiutil detach "${attach_dev}" -force >/dev/null 2>&1
    attach_dev=""
  fi
  if [[ -n "${app_copy}" && -e "${app_copy}" ]]; then
    rm -rf "${app_copy}"
    app_copy=""
  fi
  if [[ -n "${scratch}" && -d "${scratch}" ]]; then
    rm -rf "${scratch}"
  fi
}

trap cleanup EXIT

port_from_ps_argv() {
  local args host port
  while IFS= read -r args; do
    case "$args" in
      *macos-dmg-gui-smoke*)
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
  local name host port
  while IFS= read -r name; do
    [[ "$name" == n* ]] || continue
    name="${name#n}"
    host="${name%:*}"
    port="${name##*:}"
    if [[ "$host" == "0.0.0.0" || "$host" == "*" || "$host" == "[::]" || "$host" == "::" ]]; then
      echo "sidecar LISTEN on ${name} is not loopback (rejected)" >&2
      return 3
    fi
    if [[ "$host" != "127.0.0.1" ]]; then
      echo "sidecar LISTEN on ${name} is not 127.0.0.1 (rejected)" >&2
      return 3
    fi
    if [[ ! "$port" =~ ^[0-9]+$ || "$port" == "0" ]]; then
      continue
    fi
    printf '%s\n' "$port"
    return 0
  done < <(lsof -nP -c framepilot-api -iTCP -sTCP:LISTEN -F n 2>/dev/null || true)
  return 1
}

# sidecar.log is stderr; ready line is stdout to Tauri. Optional hint only.
port_from_sidecar_log() {
  local log line host port
  log="${HOME}/Library/Application Support/FramePilot/logs/sidecar.log"
  if [[ ! -f "$log" ]]; then
    return 1
  fi
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      FRAMEPILOT_API\ ready\ host=*)
        ;;
      *)
        continue
        ;;
    esac
    host=""
    port=""
    if [[ "$line" =~ host=([^[:space:]]+) ]]; then
      host="${BASH_REMATCH[1]}"
    fi
    if [[ "$line" =~ port=([0-9]+) ]]; then
      port="${BASH_REMATCH[1]}"
    fi
    if [[ -z "$port" || "$port" == "0" ]]; then
      continue
    fi
    if [[ "$host" == "0.0.0.0" ]]; then
      echo "sidecar.log ready line host 0.0.0.0 is not allowed" >&2
      return 3
    fi
    if [[ "$host" != "127.0.0.1" ]]; then
      continue
    fi
    printf '%s\n' "$port"
    return 0
  done < "$log"
  return 1
}

discover_port() {
  local port rc
  # LISTEN is ready; argv --port can appear before the sidecar binds.
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
  set +e
  port="$(port_from_sidecar_log)"
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

framepilot_api_listening() {
  lsof -nP -c framepilot-api -iTCP -sTCP:LISTEN >/dev/null 2>&1
}

echo "attaching ${dmg}"
mount_root="${scratch}/mnt"
mkdir -p "$mount_root"
attach_out="$(hdiutil attach -nobrowse -mountroot "$mount_root" "$dmg")"
printf '%s\n' "$attach_out"
attach_dev="$(printf '%s\n' "$attach_out" | awk '/^\/dev\// { print $1; exit }')"
if [[ -z "$attach_dev" ]]; then
  echo "hdiutil attach did not report a /dev device" >&2
  exit 1
fi

app_src=""
while IFS= read -r -d '' candidate; do
  app_src="$candidate"
  break
done < <(find "$mount_root" -maxdepth 4 -name 'FramePilot.app' -type d -print0)
if [[ -z "$app_src" || ! -d "$app_src" ]]; then
  echo "FramePilot.app not found in attached dmg under ${mount_root}" >&2
  exit 1
fi

app_copy="${scratch}/FramePilot.app"
cp -R "$app_src" "$app_copy"
xattr -cr "$app_copy"
echo "opening ${app_copy}"
open "$app_copy"
opened=1

export http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= all_proxy= ALL_PROXY=
export no_proxy=127.0.0.1,localhost,::1
export NO_PROXY=127.0.0.1,localhost,::1

port=""
http_code=""
health_url=""
retried_open=0
start_ts="$(date +%s)"
while true; do
  now="$(date +%s)"
  elapsed=$((now - start_ts))
  if (( elapsed >= 30 )); then
    break
  fi
  set +e
  port="$(discover_port)"
  rc=$?
  set -e
  if [[ "$rc" -eq 3 ]]; then
    echo "sidecar bound a non-loopback address" >&2
    exit 1
  fi
  if [[ "$rc" -eq 0 && -n "$port" ]]; then
    health_url="http://127.0.0.1:${port}/health"
    : > "${scratch}/health.json"
    set +e
    http_code="$(curl --noproxy '*' -sS -o "${scratch}/health.json" -w '%{http_code}' "$health_url")"
    set -e
    if [[ "$http_code" == "200" ]]; then
      break
    fi
    echo "GET ${health_url} -> HTTP ${http_code:-000}; waiting for sidecar accept" >&2
  fi
  if (( elapsed >= 8 && retried_open == 0 )); then
    echo "sidecar not ready; retrying open once" >&2
    open "$app_copy" || true
    retried_open=1
  fi
  sleep 1
done

if [[ -z "$port" || "$http_code" != "200" ]]; then
  echo "sidecar did not become ready on 127.0.0.1 within 30s" >&2
  echo "ps argv (framepilot-api):" >&2
  ps -axww -o args= 2>/dev/null | grep -F 'framepilot-api' >&2 || true
  echo "lsof LISTEN (framepilot-api):" >&2
  lsof -nP -c framepilot-api -iTCP -sTCP:LISTEN >&2 || true
  if [[ -n "${health_url}" ]]; then
    echo "last GET ${health_url} -> HTTP ${http_code:-000}" >&2
    cat "${scratch}/health.json" >&2 || true
  fi
  exit 1
fi

echo "sidecar ready port=${port}"
health_body="$(cat "${scratch}/health.json")"
health_parsed="$(
  python3 - "$health_body" << 'PY'
import json
import sys

payload = json.loads(sys.argv[1])
for key in ("version", "service"):
    if key not in payload or not payload[key]:
        raise SystemExit(f"health JSON missing {key}: {payload}")
print(payload["version"])
print(json.dumps(payload, sort_keys=True))
PY
)"
app_version="$(printf '%s\n' "$health_parsed" | sed -n '1p')"
health_json="$(printf '%s\n' "$health_parsed" | sed -n '2p')"
echo "APP_VERSION=${app_version}"
echo "health=${health_json}"

title_ok=false
title_error=""
title=""
set +e
title="$(osascript -e 'tell application "System Events" to get name of window 1 of process "FramePilot"' 2>"${scratch}/title.err")"
title_rc=$?
set -e
if [[ "$title_rc" -eq 0 && "$title" == *FramePilot* ]]; then
  title_ok=true
else
  if [[ -z "$title_error" && -s "${scratch}/title.err" ]]; then
    title_error="$(tr '\n' ' ' < "${scratch}/title.err" | sed 's/[[:space:]]*$//')"
  elif [[ "$title_rc" -eq 0 ]]; then
    title_error="osascript window name was ${title}"
  fi
  set +e
  ls_info="$(lsappinfo info -app FramePilot 2>"${scratch}/lsappinfo.err")"
  ls_rc=$?
  set -e
  if [[ "$ls_rc" -eq 0 && "$ls_info" == *FramePilot* ]]; then
    title_ok=true
    title_error=""
  else
    if [[ -z "$title_error" && -s "${scratch}/lsappinfo.err" ]]; then
      title_error="$(tr '\n' ' ' < "${scratch}/lsappinfo.err" | sed 's/[[:space:]]*$//')"
    elif [[ -z "$title_error" ]]; then
      title_error="lsappinfo/osascript did not report window title FramePilot"
    fi
    echo "title_ok=false ${title_error}" >&2
  fi
fi

echo "quitting FramePilot.app"
set +e
osascript -e 'tell application "FramePilot" to quit' >/dev/null 2>"${scratch}/quit.err"
osascript -e 'tell application id "com.framepilot.app" to quit' >/dev/null 2>>"${scratch}/quit.err"
set -e
quit_wait=0
while (( quit_wait < 20 )); do
  gui_left="$(pgrep -f '/FramePilot\.app/Contents/MacOS/' 2>/dev/null || true)"
  if [[ -z "$gui_left" ]] && ! framepilot_api_listening; then
    break
  fi
  if (( quit_wait == 8 )) && [[ -n "$gui_left" ]]; then
    while IFS= read -r pid; do
      [[ -n "${pid}" ]] || continue
      # GUI quit, not sidecar-only kill.
      kill "${pid}" >/dev/null 2>&1 || true
    done <<< "${gui_left}"
  fi
  sleep 1
  quit_wait=$((quit_wait + 1))
done

if framepilot_api_listening; then
  echo "leftover framepilot-api LISTEN after quit:" >&2
  lsof -nP -c framepilot-api -iTCP -sTCP:LISTEN >&2 || true
  exit 1
fi

if [[ -n "${attach_dev}" ]]; then
  hdiutil detach "${attach_dev}" || hdiutil detach "${attach_dev}" -force
  attach_dev=""
fi
if [[ -n "${app_copy}" && -e "${app_copy}" ]]; then
  rm -rf "${app_copy}"
  app_copy=""
fi
opened=0

utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "os=${os}"
echo "utc=${utc}"
echo "health=${health_json}"
echo "port=${port}"
echo "title_ok=${title_ok}"
if [[ "$title_ok" != "true" ]]; then
  echo "title_error=${title_error}"
fi
echo "result=pass"
