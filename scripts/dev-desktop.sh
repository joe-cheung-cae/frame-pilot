#!/usr/bin/env bash
# Start Tauri + Vite + the Python sidecar when cargo/rustc exist.
# Not invoked by `npm run verify`.
set -euo pipefail

export PATH="${HOME}/.cargo/bin:${PATH}"

if ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then
  echo "desktop shell blocked: rustc/cargo not found on this host" >&2
  echo "Install a user-space Rust toolchain (https://rustup.rs) to run npm run dev:desktop." >&2
  echo "npm run verify does not require Rust, Cargo, or Tauri." >&2
  exit 1
fi

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root/apps/desktop"
exec npx tauri dev
