#!/usr/bin/env bash
set -euo pipefail
set +m

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

data_dir="$(mktemp -d "${TMPDIR:-/tmp}/framepilot-sidecar-smoke.XXXXXX")"
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
elif [[ -f "$repo_root/dist/framepilot-api/framepilot-api.exe" ]]; then
  sidecar=("$repo_root/dist/framepilot-api/framepilot-api.exe")
elif [[ -x "$repo_root/.venv/bin/python" ]]; then
  sidecar=("$repo_root/.venv/bin/python" -m app.sidecar_main)
elif [[ -f "$repo_root/.venv/Scripts/python.exe" ]]; then
  sidecar=("$repo_root/.venv/Scripts/python.exe" -m app.sidecar_main)
else
  echo "Neither a PyInstaller sidecar nor .venv python is available" >&2
  exit 1
fi

export PYTHONPATH="$repo_root/apps/api${PYTHONPATH:+:$PYTHONPATH}"

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

port="${ready##* port=}"
port="${port%% *}"
if [[ -z "$port" || "$port" == "0" ]]; then
  echo "Ready line did not report a bound port: $ready" >&2
  exit 1
fi

body="$(curl -fsS "http://127.0.0.1:${port}/health")"
python3 - "$body" << 'PY'
import json
import sys

payload = json.loads(sys.argv[1])
assert payload.get("status") == "ok", payload
assert payload.get("service") == "framepilot-api", payload
assert payload.get("version"), payload
print(json.dumps(payload, sort_keys=True))
PY

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
if command -v pgrep > /dev/null 2>&1; then
  leftover="$(pgrep -P $$ || true)"
  if [[ -n "${leftover}" ]]; then
    echo "Leftover child processes: $leftover" >&2
    exit 1
  fi
fi

echo "sidecar-smoke ok port=$port"
