# Desktop Phase 1 Handoff Status

- current_stage: 开发
- status: in_progress
- files changed:
  - D1.01 navigation adapter (`a5bffba`)
  - D1.02 runtime API base (`cdc3423`); §5.1 D1.02 `[x]`
  - D1.02a desktop shell flag (`fabe7a1`); §5.1 D1.02a `[x]`
  - D1.03a Vite build, aliases, Tailwind; §5.1 D1.03a `[x]`
  - D1.03b desktop router (`616fea3`); §5.1 D1.03b `[x]`
  - D1.04 sidecar lifecycle (`apps/desktop/src-tauri/src/sidecar.rs`); §5.1 D1.04 `[x]`
  - D1.05 OS app-support data dir (`apps/desktop/src-tauri/src/data_dir.rs`): macOS `Library/Application Support/FramePilot`, Windows `%APPDATA%\\FramePilot`, Linux `.local/share/FramePilot`; packaged never CWD `.framepilot-data`; dev `.framepilot-desktop-dev`
  - §5.1 D1.05 `[x]` (`cargo test --lib` twice, 15 passed)
- tests_run: `cargo test --lib` in `apps/desktop/src-tauri` twice (15 passed, exit 0). User-space rustup: `rustc 1.97.1` / `cargo 1.97.1`.
- next_stage: 开发
- blockers: none (D0.07 WebView still [~]; rustc now present via user-space rustup)
- branch: feature/desktop-packaging
- timestamp: 2026-08-19

开发 in progress. D1.05 OS app-support data directory is landed and §5.1 D1.05 is `[x]`. Remaining Phase 1 boxes stay `[ ]` until their commits. Do not start D1.08/D1.09 in this handoff.

Phase 0 remains closed GO on `origin/main` (`1d6ffa7`). D0.07 GUI/WebView remains `[~]` (no `tauri dev` window on this host). User-space rustup on 2026-08-19 installed rustc/cargo; see `docs/desktop_feasibility_notes.md`.
