# FramePilot desktop shell

Tauri 2 + Vite SPA that reuses `apps/web` components over HTTP to a local Python sidecar.

## Dev

`npm run dev:desktop` from the repo root starts `tauri dev`, which:

1. Runs Vite on port **1420** (`strictPort: true`) via `beforeDevCommand`.
2. Spawns the sidecar with an allocated loopback `--port <n>` (never `--port 0`), absolute `--data-dir`, and `FRAMEPILOT_DESKTOP=1`.
3. Injects `window.__FRAMEPILOT_API_BASE__` and `window.__FRAMEPILOT_DESKTOP__ = true` before the UI loads.

Requires a user-space Rust toolchain (`rustup`). If `cargo`/`rustc` are missing, the script prints a clear error and exits 1. Do not install brew/apt Rust from this tree.

`build:desktop` / installers wait until Phase 4.

## Data directory

- Packaged: macOS `~/Library/Application Support/FramePilot`; Windows `%APPDATA%\FramePilot`; Linux `~/.local/share/FramePilot`
- Dev: repo `.framepilot-desktop-dev` (gitignored)
- Packaged runs never use CWD-relative `.framepilot-data`

Override with absolute `FRAMEPILOT_DATA_DIR`. Sidecar stderr is appended to `{data_dir}/logs/sidecar.log`.

## Verify

`npm run verify` typechecks the desktop Vite app (`typecheck:desktop`) and **must not** invoke `rustc`, `cargo`, or Tauri. `install:all` already installs `apps/desktop`.

## Quit while a job is running

Closing the window with an active import shows Keep working / Quit and cancel import / Quit anyway. Cancel reuses `POST /api/projects/{id}/jobs/{job_id}/cancel`, waits up to 10s, then SIGTERM. Processing jobs cannot be cancelled; that dialog omits Quit and cancel. Quit anyway SIGTERMs the sidecar and kills it after 5s. The next launch runs the existing startup sweep.

HTTP smoke: `npm run test:desktop:smoke` from the repo root. WebView render of the dialog is not part of that smoke.
