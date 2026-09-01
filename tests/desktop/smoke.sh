#!/usr/bin/env bash
set -euo pipefail
set +m

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

data_dir="$(mktemp -d "${TMPDIR:-/tmp}/framepilot-desktop-smoke.XXXXXX")"
sidecar_pid=""
cleanup() {
  if [[ -n "${sidecar_pid}" ]] && kill -0 "$sidecar_pid" 2> /dev/null; then
    kill -TERM "$sidecar_pid" 2> /dev/null || true
    wait "$sidecar_pid" 2> /dev/null || true
  fi
  rm -rf "$data_dir"
}
trap cleanup EXIT

if [[ -x "$repo_root/dist/framepilot-api/framepilot-api" ]]; then
  sidecar=("$repo_root/dist/framepilot-api/framepilot-api")
elif [[ -x "$repo_root/.venv/bin/python" ]]; then
  sidecar=("$repo_root/.venv/bin/python" -m app.sidecar_main)
else
  echo "Neither a PyInstaller sidecar nor .venv python is available" >&2
  exit 1
fi

export PYTHONPATH="$repo_root/apps/api${PYTHONPATH:+:$PYTHONPATH}"
export FRAMEPILOT_DESKTOP=1
export http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= all_proxy= ALL_PROXY=
export no_proxy=127.0.0.1,localhost,::1
export NO_PROXY=127.0.0.1,localhost,::1

stdout_log="$data_dir/stdout.log"
stderr_log="$data_dir/stderr.log"

"${sidecar[@]}" --host 127.0.0.1 --port 0 --data-dir "$data_dir" > "$stdout_log" 2> "$stderr_log" &
sidecar_pid=$!

ready=""
for _ in $(seq 1 50); do
  if [[ -s "$stdout_log" ]]; then
    ready="$(tr -d '\r' < "$stdout_log" | head -n 1)"
    if [[ "$ready" == FRAMEPILOT_API\ ready\ host=127.0.0.1\ port=* ]]; then
      break
    fi
  fi
  if ! kill -0 "$sidecar_pid" 2> /dev/null; then
    echo "Sidecar exited before printing a ready line" >&2
    cat "$stderr_log" >&2 || true
    cat "$stdout_log" >&2 || true
    exit 1
  fi
  sleep 0.1
done

if [[ "$ready" != FRAMEPILOT_API\ ready\ host=127.0.0.1\ port=* ]]; then
  echo "Unexpected ready line: $ready" >&2
  cat "$stderr_log" >&2 || true
  cat "$stdout_log" >&2 || true
  exit 1
fi

rest="${ready#FRAMEPILOT_API ready }"
host_field="${rest%% *}"
host="${host_field#host=}"
port_and_rest="${rest#host=${host} port=}"
port="${port_and_rest%% *}"
if [[ "$host" != "127.0.0.1" ]]; then
  echo "Ready line host must be 127.0.0.1: $ready" >&2
  exit 1
fi
if [[ -z "$port" || "$port" == "0" || ! "$port" =~ ^[0-9]+$ ]]; then
  echo "Ready line did not report a bound non-zero port: $ready" >&2
  exit 1
fi

base="http://127.0.0.1:${port}"

curl_loopback() {
  curl --noproxy '*' "$@"
}

health_body="$(curl_loopback -fsS "${base}/health")"
python3 - "$health_body" << 'PY'
import json
import sys

payload = json.loads(sys.argv[1])
for key in ("status", "version", "service"):
    if key not in payload or not payload[key]:
        raise SystemExit(f"health JSON missing {key}: {payload}")
print(json.dumps(payload, sort_keys=True))
PY

projects_body="$(curl_loopback -fsS -H "Origin: http://127.0.0.1:1420" "${base}/api/projects")"
python3 - "$projects_body" << 'PY'
import json
import sys

payload = json.loads(sys.argv[1])
if not isinstance(payload, list):
    raise SystemExit(f"/api/projects must be a JSON array: {payload!r}")
print(json.dumps(payload))
PY

preflight_headers="$data_dir/preflight.headers"
preflight_status="$(
  curl_loopback -sS -D "$preflight_headers" -o /dev/null -w '%{http_code}' \
    -X OPTIONS \
    -H "Origin: http://127.0.0.1:1420" \
    -H "Access-Control-Request-Method: GET" \
    -H "Host: 127.0.0.1:${port}" \
    "${base}/api/projects"
)"
echo "desktop Origin OPTIONS /api/projects -> HTTP ${preflight_status}"
if [[ "$preflight_status" != "200" && "$preflight_status" != "204" ]]; then
  echo "Desktop CORS preflight failed (not a silent 403): HTTP ${preflight_status}" >&2
  cat "$preflight_headers" >&2 || true
  cat "$stderr_log" >&2 || true
  exit 1
fi
if ! grep -i '^access-control-allow-origin: http://127.0.0.1:1420' "$preflight_headers" > /dev/null; then
  echo "Desktop CORS preflight missing Access-Control-Allow-Origin for Vite :1420" >&2
  cat "$preflight_headers" >&2
  exit 1
fi

host_deny_body="$data_dir/host-deny.json"
host_deny_status="$(
  curl_loopback -sS -o "$host_deny_body" -w '%{http_code}' \
    -H "Host: attacker.example" \
    "${base}/api/projects"
)"
echo "Host attacker.example GET /api/projects -> HTTP ${host_deny_status} body=$(cat "$host_deny_body")"
if [[ "$host_deny_status" != "403" ]]; then
  echo "Attacker Host must fail visibly with HTTP 403, got ${host_deny_status}" >&2
  exit 1
fi
python3 - "$host_deny_body" << 'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
detail = payload.get("detail")
if not detail:
    raise SystemExit(f"Host 403 body must include a visible detail, not a silent reject: {payload!r}")
print(detail)
PY

echo "desktop-smoke: skipping WebView project-list render (HTTP sidecar smoke only; no Tauri GUI in this path)"

kill -TERM "$sidecar_pid" 2> /dev/null || true
elapsed=0
while kill -0 "$sidecar_pid" 2> /dev/null; do
  if ((elapsed >= 50)); then
    echo "Sidecar did not exit within 5s of SIGTERM" >&2
    kill -KILL "$sidecar_pid" 2> /dev/null || true
    exit 1
  fi
  sleep 0.1
  elapsed=$((elapsed + 1))
done
wait "$sidecar_pid" > /dev/null 2>&1 || true
sidecar_pid=""

# pgrep is unreliable under Git Bash on Windows; skip leftover check when absent.
# Linux procps `pgrep -P $$` includes pgrep itself (a child of this shell), so
# only fail on leftover sidecar/uvicorn processes.
if command -v pgrep > /dev/null 2>&1; then
  leftover="$(pgrep -P $$ -a || true)"
  leftover="$(printf '%s\n' "$leftover" | grep -E 'framepilot-api|sidecar_main|[Uu]vicorn' || true)"
  if [[ -n "${leftover}" ]]; then
    echo "Leftover child processes: $leftover" >&2
    exit 1
  fi
fi

echo "desktop-smoke ok port=$port"
