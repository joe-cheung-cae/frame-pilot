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

use_frozen=0
if [[ -x "$repo_root/dist/framepilot-api/framepilot-api" ]]; then
  sidecar=("$repo_root/dist/framepilot-api/framepilot-api")
  use_frozen=1
elif [[ -f "$repo_root/dist/framepilot-api/framepilot-api.exe" ]]; then
  sidecar=("$repo_root/dist/framepilot-api/framepilot-api.exe")
  use_frozen=1
elif [[ -x "$repo_root/.venv/bin/python" ]]; then
  sidecar=("$repo_root/.venv/bin/python" -m app.sidecar_main)
elif [[ -f "$repo_root/.venv/Scripts/python.exe" ]]; then
  sidecar=("$repo_root/.venv/Scripts/python.exe" -m app.sidecar_main)
else
  echo "Neither a PyInstaller sidecar nor .venv python is available" >&2
  exit 1
fi

if [[ "$use_frozen" -eq 1 ]]; then
  # Match packaged Tauri spawn: do not let a parent PYTHONPATH shadow bundled imports.
  unset PYTHONPATH
else
  export PYTHONPATH="$repo_root/apps/api${PYTHONPATH:+:$PYTHONPATH}"
fi

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

if [[ "$use_frozen" -eq 1 ]]; then
  unpacked="$repo_root/dist/framepilot-api"
  unpacked_bytes="$(du -sb "$unpacked" | awk '{print $1}')"
  max_bytes=$((400 * 1024 * 1024))
  echo "unpacked sidecar bytes=$unpacked_bytes max=$max_bytes"
  if [[ "$unpacked_bytes" -gt "$max_bytes" ]]; then
    echo "Unpacked sidecar exceeds the 400 MB D4.06 threshold: $unpacked_bytes" >&2
    exit 1
  fi

  if [[ -x "$repo_root/.venv/bin/python" ]]; then
    gen_python="$repo_root/.venv/bin/python"
  elif [[ -f "$repo_root/.venv/Scripts/python.exe" ]]; then
    gen_python="$repo_root/.venv/Scripts/python.exe"
  else
    echo "Need .venv python to generate tiny HEIC, AVIF, and DNG for frozen decode smoke" >&2
    exit 1
  fi

  heic_path="$data_dir/still.heic"
  "$gen_python" - "$heic_path" << 'PY'
from io import BytesIO
from pathlib import Path
import sys

from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()
image = Image.new("RGB", (8, 6), (12, 34, 56))
buffer = BytesIO()
image.save(buffer, format="HEIF")
Path(sys.argv[1]).write_bytes(buffer.getvalue())
print(f"wrote {sys.argv[1]} bytes={len(buffer.getvalue())}")
PY

  python3 - "$port" "$heic_path" << 'PY'
import json
import sys
import time
import urllib.error
import urllib.request

port = sys.argv[1]
heic_path = sys.argv[2]
base = f"http://127.0.0.1:{port}"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{port}"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


project = request("POST", "/api/projects", {"name": "sidecar-heic"})
imported = request(
    "POST",
    f"/api/projects/{project['id']}/imports/from-paths",
    {"paths": [heic_path], "finalize": True},
)
assert imported["imported"] and imported["imported"][0]["filename"] == "still.heic", imported
job = imported["job"]
for _ in range(50):
    if job["status"] in {"complete", "complete_with_errors", "failed", "cancelled"}:
        break
    time.sleep(0.1)
    job = request("GET", f"/api/projects/{project['id']}/jobs/{job['id']}")
assert job["status"] == "complete", job
photo = request("GET", f"/api/projects/{project['id']}/photos/{imported['imported'][0]['id']}")
assert photo["processing_state"] == "imported", photo
assert photo["file_ext"] == ".heic", photo
print(json.dumps({"job": job["status"], "photo": photo["filename"], "state": photo["processing_state"]}))
PY

  avif_path="$data_dir/still.avif"
  "$gen_python" - "$avif_path" << 'PY'
from io import BytesIO
from pathlib import Path
import sys

from PIL import Image

image = Image.new("RGB", (8, 6), (90, 12, 40))
buffer = BytesIO()
image.save(buffer, format="AVIF")
Path(sys.argv[1]).write_bytes(buffer.getvalue())
print(f"wrote {sys.argv[1]} bytes={len(buffer.getvalue())}")
PY

  python3 - "$port" "$avif_path" << 'PY'
import json
import sys
import time
import urllib.request

port = sys.argv[1]
avif_path = sys.argv[2]
base = f"http://127.0.0.1:{port}"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{port}"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


project = request("POST", "/api/projects", {"name": "sidecar-avif"})
imported = request(
    "POST",
    f"/api/projects/{project['id']}/imports/from-paths",
    {"paths": [avif_path], "finalize": True},
)
assert imported["imported"] and imported["imported"][0]["filename"] == "still.avif", imported
job = imported["job"]
for _ in range(50):
    if job["status"] in {"complete", "complete_with_errors", "failed", "cancelled"}:
        break
    time.sleep(0.1)
    job = request("GET", f"/api/projects/{project['id']}/jobs/{job['id']}")
assert job["status"] == "complete", job
photo = request("GET", f"/api/projects/{project['id']}/photos/{imported['imported'][0]['id']}")
assert photo["processing_state"] == "imported", photo
assert photo["file_ext"] == ".avif", photo
print(json.dumps({"job": job["status"], "photo": photo["filename"], "state": photo["processing_state"]}))
PY

  dng_path="$data_dir/still.dng"
  "$gen_python" - "$dng_path" "$repo_root/apps/api" << 'PY'
from pathlib import Path
import sys

sys.path.insert(0, sys.argv[2])
from tests.raw_helpers import tiny_dng_bytes

payload = tiny_dng_bytes()
Path(sys.argv[1]).write_bytes(payload)
print(f"wrote {sys.argv[1]} bytes={len(payload)}")
PY

  python3 - "$port" "$dng_path" << 'PY'
import json
import sys
import time
import urllib.request

port = sys.argv[1]
dng_path = sys.argv[2]
base = f"http://127.0.0.1:{port}"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{port}"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


project = request("POST", "/api/projects", {"name": "sidecar-dng"})
imported = request(
    "POST",
    f"/api/projects/{project['id']}/imports/from-paths",
    {"paths": [dng_path], "finalize": True},
)
assert imported["imported"] and imported["imported"][0]["filename"] == "still.dng", imported
job = imported["job"]
for _ in range(50):
    if job["status"] in {"complete", "complete_with_errors", "failed", "cancelled"}:
        break
    time.sleep(0.1)
    job = request("GET", f"/api/projects/{project['id']}/jobs/{job['id']}")
assert job["status"] == "complete", job
photo = request("GET", f"/api/projects/{project['id']}/photos/{imported['imported'][0]['id']}")
assert photo["processing_state"] == "imported", photo
assert photo["file_ext"] == ".dng", photo
print(json.dumps({"job": job["status"], "photo": photo["filename"], "state": photo["processing_state"]}))
PY
fi

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

echo "sidecar-smoke ok port=$port"
