# FramePilot desktop skeleton (Phase 0)

This tree is a verify-safe Tauri 2 placeholder. It is not a runnable desktop app on hosts without `rustc`/`cargo`.

Phase 0 intent:

- Blank Tauri 2 window
- Spawn the Python sidecar with `--host 127.0.0.1 --port <free> --data-dir <app-support>`
- Set `FRAMEPILOT_DESKTOP=1`
- Poll `GET /health` for up to 15 seconds and show “API ready” or the error
- On exit: SIGTERM, then kill after 5 seconds

`npm run verify` must not invoke Rust, Cargo, or Tauri. GUI/toolchain work is recorded as `[~]` in `docs/desktop_feasibility_notes.md` when `cargo --version` fails.

Do not install a system Rust toolchain from this skeleton.
