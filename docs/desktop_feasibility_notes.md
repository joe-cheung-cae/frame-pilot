# Desktop Feasibility Notes

**Status: FINAL** — Phase 1 `上线`, 2026-08-19T19:00:41+08:00, branch `feature/desktop-packaging`.

Phase 0 measurements remain below. Phase 1 close-out is in **Phase 1 notes** and **Phase 1 go/no-go**. `测试` re-ran web/desktop/verify/jobs/sidecar/cargo; `上线` owns §5.1 Phase 1 ticks and recorded a live `npm run dev:desktop` window plus browser `:3000`/`:8000`.

This host is **macOS**, not WSL2.

## Verdict

**GO — close desktop Phase 0.**

| Decision | Result | Why |
| -------- | ------ | --- |
| Close Phase 0 | **GO** | Sidecar, health, origin/Host, path import, CI, smoke, `npm run verify` hold. D0.07 is `[~]`, which is allowed. |
| Shell | **Stay Tauri 2 + Python sidecar** | Sidecar **was** spawned. Tauri compile is blocked by missing `rustc`. That is **not** the Electron trigger. |
| Frontend | **Vite SPA follow-up; do not export Next** | `output: 'export'` failed on dynamic `projects/[projectId]` routes. `apps/web` stays Next.js. |
| Scoring stack | **Keep imagehash / scipy / PyWavelets** | Unpacked sidecar size was **not measured** (no PyInstaller `dist/` on this host). Do not drop scipy. |
| Phase 1 | **Not started** | `next_stage=none`. |

## Blockers

### D0.07 Tauri GUI / Rust toolchain `[~]` — 2026-08-19

Re-run during `上线` on this host. Commands and exact errors:

```text
$ cargo --version
zsh:1: command not found: cargo

$ rustc --version
zsh:1: command not found: rustc

$ command -v rustup || echo rustup not found
rustup not found
```

This workspace eval shell printed the same missing-binary failure as:

```text
(eval):1: command not found: cargo
(eval):1: command not found: rustc
```

Both commands exited **127**. Capture: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-a63c25686341/implementer/tauri-gui.txt`.

No system Rust toolchain was installed. `npm run verify` does not invoke `cargo`, `rustc`, or Tauri (`测试` fail-if-invoked wrappers were never called). A verify-safe skeleton lives under `apps/desktop/` (blank HTML health probe, locked CSP in `src-tauri/tauri.conf.json`, sidecar spawn notes in `src-tauri/src/lib.rs`). Sidecar smoke was run without a WebView.

Until a dated `cargo` / WebView run succeeds, D0.07 stays `[~]`. Missing `rustc` means Tauri cannot compile on this host. That does **not** mean Tauri cannot spawn the sidecar: the Python sidecar started twice under `测试` and once via `scripts/sidecar-smoke.sh`. Electron stays off the table.

## D0.06 — Next.js `output: 'export'` spike

Attempted a throwaway change to `apps/web/next.config.ts`:

```ts
output: 'export',
```

`npm --prefix apps/web run build` compiled, then failed:

```text
Error: Page "/projects/[projectId]/cull" is missing "generateStaticParams()" so it cannot be used with "output: export" config.
```

Current App Router pages under `apps/web/src/app/projects/[projectId]/` with no `generateStaticParams`:

- `page.tsx`
- `cull/page.tsx`
- `export/page.tsx`
- `import/page.tsx`
- `process/page.tsx`

`CullingWorkspace.tsx` calls `useSearchParams()` from `next/navigation`. The export build never reached a full static emit, so Suspense warnings for `useSearchParams` were not observed on this run. They remain a known Next 15 App Router issue if export were forced later.

The throwaway `output: 'export'` line was **reverted** in the same work. Live `apps/web/next.config.ts` has no `output: 'export'`. `测试` `npm run verify` rebuilt Next.js 15.5.19 successfully (`Generating static pages (7/7)`; the five project routes stay dynamic `ƒ`). `apps/web` stays Next.js. Locked follow-up remains a Vite SPA in `apps/desktop` (Phase 1). No frontend migration was started. Next static export is **not viable**.

## Baselines

Recorded 2026-08-19 on this macOS host.

Sidecar start and health are from `测试` live launches (venv module, not a packed binary):

```text
PYTHONPATH=apps/api .venv/bin/python -m app.sidecar_main --host 127.0.0.1 --port 0 --data-dir <tmp>
```

| Measurement | Result | Source |
| ----------- | ------ | ------ |
| Ready line (run 1) | `FRAMEPILOT_API ready host=127.0.0.1 port=55238 data_dir=<tmp>` | `sidecar-run-1.txt` |
| Ready line (run 2) | `FRAMEPILOT_API ready host=127.0.0.1 port=55243 data_dir=<tmp>` | `sidecar-run-2.txt` |
| `GET /health` body | `{"status":"ok","version":"2.0.0-rc2","service":"framepilot-api"}` | both live runs, HTTP 200 |
| `GET /api/health` body | same JSON | run 1 only, HTTP 200 |
| SIGTERM | process exited (wait_rc=143) | both live runs |
| Sidecar smoke | `sidecar-smoke ok port=55271` | `sidecar-smoke.txt` |
| Time to ready + `/health` | 0.703 s (ready ~0.663 s, curl ~0.040 s) | `开发` venv timing, same host/day |
| Sidecar RSS after `/health` | 98320 KB (~96 MB) | `开发` measurement, same host/day |
| PyInstaller `dist/framepilot-api` size | **not built** on this host (smoke used `.venv` module) | not measured |
| Tauri hello RSS | **blocked-gui** — missing rustc/WebView | `tauri-gui.txt`, 2026-08-19 |
| `imagehash` | 4.3.2 present | `开发` |
| `numpy` | 2.5.2 present | `开发` |
| `scipy` | 1.18.0 present | `开发` |
| `pywt` (PyWavelets) | 1.8.0 present | `开发` |

`scripts/sidecar-smoke.sh` passed: ephemeral `--data-dir`, `--port 0`, parsed ready line, curled `/health` for `version`, SIGTERM, process exited within 5 s.

`测试` also recorded: Phase 0 pytest **57 passed**; `npm run test:api` **211 passed**; `npm run verify` **exit 0** without invoking rustc/cargo.

Unpacked sidecar **>250 MB** was **not** observed because PyInstaller `dist/` was not produced. Keep the scoring stack.

## Go / no-go (final)

`上线` wording, 2026-08-19:

1. **Shell: GO Tauri 2 + Python sidecar.** Electron is only in play if a dated run shows Tauri cannot spawn the sidecar or the WebView cannot reach loopback. The sidecar **was spawned** (venv CLI, twice, plus smoke). Tauri **compile** is blocked (`cargo`/`rustc` command not found, 2026-08-19). Compile-blocked is **not** the Electron trigger. Keep the `apps/desktop` skeleton and do not switch shells.

2. **Frontend: GO Vite SPA follow-up. Next `output: 'export'` is not viable.** Keep `apps/web` on Next.js for browser + Playwright. Do not migrate `apps/web`. Desktop UI remains a Phase 1 Vite SPA in `apps/desktop`.

3. **Scoring stack: GO keep imagehash / scipy / PyWavelets.** The drop trigger is unpacked sidecar **>250 MB**. Dist size is **not measured / not built**. Do not drop scipy.

4. **Phase 0 API work is in place:** loopback sidecar CLI, health `version`/`service`, origin + Host policy, path import with 100-file leftover-file chunks, and copy-mode immutability tests. `npm run test:api` and `npm run verify` are green without Rust.

5. **Do not start Phase 1 from this close-out.** Do not publish installers, push, or open a PR.

Phase 0 acceptance (see §5.1 / D0.09): sidecar/health/SIGTERM `[x]`; origin+Host `[x]`; path import + immutability `[x]`; feasibility notes `[x]`; `test:api` + `verify` `[x]`; browser web app `[x]`; GUI release `[~]` with the dated `cargo`/`rustc` error above.

## Phase 1 notes — 2026-08-19

User-space rustup (`curl https://sh.rustup.rs -sSf | sh -s -- -y`) installed `rustc 1.97.1` / `cargo 1.97.1` into `$HOME/.cargo`. No brew/apt. `cargo test` in `apps/desktop/src-tauri` passed D1.04 unit tests (allocate/drop port, ready-line parse including spaced `data_dir`, reject port 0 / mismatch). D0.07 stays `[~]` as the Phase 0 close-out (dated `cargo`/`rustc` command not found, exit 127).

Windows sidecar shutdown (source; not executed on this macOS host): spawn uses `CREATE_NEW_PROCESS_GROUP`, shutdown sends `GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT)`, waits 5s, then `Child::kill()` (`TerminateProcess`). Unix uses SIGTERM, wait 5s, then kill.

D1.06 `cargo check` in `apps/desktop/src-tauri` succeeded on 2026-08-19 (`tauri-plugin-window-state` 2.4.1, `tauri-plugin-single-instance` 2.4.3).

D1.08 HTTP sidecar smoke (`npm run test:desktop:smoke`) passed on 2026-08-19: ready line `host=127.0.0.1` with non-zero port, `GET /health` has `status`/`version`/`service`, `GET /api/projects` is a JSON array, attacker `Host` returns visible HTTP 403 JSON (`Host not allowed for local FramePilot API`), desktop Origin `:1420` CORS preflight allows, SIGTERM exits. The HTTP smoke script still prints `desktop-smoke: skipping WebView project-list render` by design.

`上线` 2026-08-19T18:54:32+08:00 ran `npm run dev:desktop` (`npx tauri dev`). It compiled and ran `target/debug/framepilot-desktop`. osascript recorded process `framepilot-desktop` with window title `FramePilot` (1200×800). Sidecar spawned as `--host 127.0.0.1 --port 54451 --data-dir <repo>/.framepilot-desktop-dev`. `GET /health` → `{"status":"ok","version":"2.0.0-rc2","service":"framepilot-api"}`. `GET /api/projects` → `[]`. `sidecar.log` shows WebView `OPTIONS` then `GET /api/projects` 200. Vite answered `http://[::1]:1420/` with the FramePilot HTML shell. D1.08 WebView is `[x]`.

D1.09 quit dialog is injected HTML. Rust unit tests cover Kill-after-5s and cancel-vs-quit-anyway decisions; pytest covers cancel/retry and killed-worker startup sweep. This close-out did not click the on-screen confirm.

`上线` 2026-08-19T18:59:32+08:00 also ran browser `npm run dev`: `GET http://127.0.0.1:8000/health` 200 same health JSON; `GET http://127.0.0.1:8000/api/projects` `[]`; `GET http://127.0.0.1:3000/` 200 with `<title>FramePilot</title>`.

## Phase 1 go/no-go (final)

`上线` wording, 2026-08-19T19:00:41+08:00, `feature/desktop-packaging`:

1. **GO — close desktop Phase 1** on this feature branch. Do not publish installers. Do not open a PR. Do not merge to `main`. Do not start Phase 2.
2. **Shell stays Tauri 2 + Python sidecar.** User-space rustup provides `rustc 1.97.1` / `cargo 1.97.1`. `cargo test --lib` **19 passed**. Sidecar HTTP smoke passed. `npm run dev:desktop` opened a `FramePilot` window whose WebView called `GET /api/projects`. D0.07 stays dated `[~]` as the Phase 0 record. Missing Phase 0 GUI was **not** the Electron trigger.
3. **Frontend: Vite SPA in `apps/desktop`.** Shared navigation/API/shell adapters landed. `apps/web` stays Next.js. Live `npm run dev` still serves `:3000` / `:8000`.
4. **`npm run verify` stays rust-free.** Fail-if-invoked `rustc`/`cargo`/`tauri` wrappers were not called by verify (`verify.log`).
5. **Jobs:** cancel-then-retry leaves no photo in `processing` after retry; killed import is `failed`+retryable via startup sweep; processing jobs have no cancel route. See `docs/v2_known_limitations.md`.
6. **`APP_VERSION` remains `2.0.0-rc2`.** Do not bump to `2.1.0-desktop`.

Phase 1 acceptance (see §5.1): HTTP/home project list `[x]`; sidecar health `[x]`; `verify` without Tauri `[x]`; browser `:3000`/`:8000` `[x]`.

## D3.01 Native menu bar — 2026-08-23

Branch `feature/d3-01-native-menu-bar`. Non-GUI tests passed. The native menu was not clicked in a live WebView on this host.

Commands and exact errors for remaining GUI / Rust compile verification:

```text
$ rustc --version
rustc 1.85.0 (4d91de4e4 2025-02-17) (built from a source tarball)

$ cargo --version
cargo 1.85.0 (d73d2caf9 2024-12-31)

$ cargo test --locked --manifest-path apps/desktop/src-tauri/Cargo.toml --lib
error: the lock file apps/desktop/src-tauri/Cargo.lock needs to be updated but --locked was passed to prevent this

$ cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib
error: rustc 1.85.0 is not supported by the following packages:
  darling@0.23.0 requires rustc 1.88.0
  ... (icu_*, plist, serde_with, time, zbus require rustc 1.86–1.88)
```

`npm run test:web` (node unit + vitest + Next build) and `npm run typecheck:desktop` passed. `APP_VERSION` stays `2.0.0-rc2`. `npm run dev:desktop` was not started because it would invoke the same failing `cargo` compile. No display-server packages were installed.

Until a dated `cargo test` / WebView menu click succeeds, D3.01 stays `[~]`.
