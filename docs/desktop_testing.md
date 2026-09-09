# Desktop Testing Matrix

> Language: **English** | [中文](desktop_testing.zh.md)

Manual and command-driven checks for FramePilot desktop (`2.1.0-desktop` track). Local-first: never modify or delete original camera files. Prefer project copies under `{root_path}/originals`.

`npm run verify` is the rust-free CI gate (lint, typecheck, tests, artifacts, validation-decision). It does **not** open a WebView or run `cargo`/`tauri`. GitHub Actions (`.github/workflows/verify.yml`) also runs an independent **Playwright E2E** job (`npm run test:e2e`: mocked E2E plus `tests/e2e/real-local-smoke.spec.ts`), an independent **100-photo real-browser** job (`npm run test:e2e:real-browser`; not `test:e2e:real-browser:large`), an independent **frozen sidecar `/health`** job (`npm run packaging:sidecar` then `npm run test:sidecar`), and an independent **desktop HTTP smoke** job (`npm run test:desktop:smoke`: `/health`, `/api/projects`, desktop Origin CORS, attacker `Host` → 403). Frozen smoke unsets `PYTHONPATH` (same as packaged Tauri spawn). Desktop HTTP smoke may use the venv sidecar when no frozen binary is present. `.github/workflows/desktop.yml` runs the frozen sidecar smoke after PyInstaller and launches the packaged macOS DMG GUI for leftover installer DoD smoke (`packaging/scripts/macos-dmg-gui-smoke.sh`). It also launches the packaged NSIS and DMG GUIs for leftover packaged-desktop ≥500 Path B (`packaging/scripts/desktop-500-gui.sh`; native dialog stubbed). It also launches the packaged macOS DMG and Windows NSIS GUIs for leftover quit+job Path B (`packaging/scripts/desktop-quit-job-gui.sh` against the just-built DMG and NSIS; native dialog stubbed). `verify.yml` stays rust-free and does not launch GUI. Workflow YAML does not need a separate `check:pretag` job; `npm run verify` already includes `check:validation-decision`. GUI rows need a host with rustc ≥1.88 (and a display). Mark unverified GUI rows `[~]` with date and host notes — never invent pass results.

**Related:** [Unsigned desktop install tutorial](desktop_install.md) · [Desktop User Guide](desktop_user_guide.md) · [Desktop Development Plan](desktop_development_plan.md) · [Desktop shell README](../apps/desktop/README.md) · [Signing runbook](desktop_signing.md) · [Phase 2 workflow checklist](../tests/desktop/workflow.md) · [Phase 5 design](plans/2026-08-29-phase5-docs-design.md)

---

## Prerequisites

| Item | Notes |
| ---- | ----- |
| OS | **Windows / macOS** — primary installer targets (NSIS / DMG via `.github/workflows/desktop.yml`). **Linux / WSL** — useful for API/sidecar/dev; installer DoD does not require a Linux package. |
| Node | 22.x (see repo CI) |
| Python | 3.11 venv via `npm run install:all` |
| Rust (GUI only) | rustc / cargo ≥1.88 for `npm run dev:desktop` / `tauri build`. Missing toolchain → skip GUI rows; keep HTTP smoke. |
| Data | Use a throwaway folder **outside** the app data directory for source photos. |

---

## Commands to know

| Script | Purpose |
| ------ | ------- |
| `npm run dev:desktop` | Tauri + Vite + sidecar (needs Rust) |
| `npm run test:desktop:smoke` | HTTP smoke: sidecar health + `/api/projects` + CORS/Host (`tests/desktop/smoke.sh`; CI default gate) |
| `npm run generate:synthetic -- --output <dir> --count <n>` | Synthetic JPEGs for path-import rows |
| `npm run perf:api -- --output <dir> --counts 100 500 2000` | Optional API-scale multipart import/process smoke (not `from-paths`) |
| `npm run packaging:sidecar` | PyInstaller one-dir sidecar (CI frozen `/health` job builds this first) |
| `npm run test:sidecar` | Sidecar ready-line smoke; frozen binary unsets `PYTHONPATH` |
| `npm run test:e2e` | Playwright mocked E2E plus real-local-smoke (CI default gate; not large real-browser) |
| `npm run test:e2e:real-browser` | 100 generated JPEGs through Chromium + real backend (CI default gate; not large) |
| `npm run verify` | Rust-free full verify (includes artifacts + validation-decision) |

No extra npm alias is required for this matrix; use the scripts above directly.

---

## Matrix — lifecycle

| Row | Command / action | Pass criteria | Automates? |
| --- | ---------------- | ------------- | ---------- |
| Start (dev) | `npm run dev:desktop` | Window title `FramePilot`; sidecar on loopback; `GET /health` → 200 with `version` + `service` | Manual GUI |
| Start (installed) | Launch NSIS/DMG build from CI or local `tauri build` | Same as above without running uvicorn yourself. Windows first Start after NSIS may take up to two minutes (#190); fail if the window shows `timed out waiting for sidecar ready line` | Manual |
| HTTP smoke | `npm run test:desktop:smoke` | Exit 0; `/health`, `/api/projects`, desktop Origin CORS, attacker `Host` → 403 | Yes (CI) |
| Frozen sidecar `/health` | `npm run packaging:sidecar` then `npm run test:sidecar` | Exit 0; frozen `GET /health` with `PYTHONPATH` unset | Yes (CI) |
| Playwright E2E | `npm run test:e2e` | Exit 0; mocked E2E plus `real-local-smoke` | Yes (CI) |
| Playwright real-browser (100) | `npm run test:e2e:real-browser` | Exit 0; 100 generated JPEGs, Chromium | Yes (CI) |
| Quit clean | Close window with no active import/processing job | Sidecar exits; no orphan uvicorn on that port | Manual GUI |
| Quit + import | Close during an active import | Dialogs per [apps/desktop/README.md](../apps/desktop/README.md) (Keep working / cancel import / Quit anyway); source originals unchanged | Manual GUI |
| Quit + processing | Close during grouping/ranking | Dialogs per [apps/desktop/README.md](../apps/desktop/README.md) (Keep working / Quit and cancel processing / Quit anyway); cancelled processing clears partial groups; source originals unchanged | Manual GUI |
| Quit + export | Close during an active export | Dialogs per [apps/desktop/README.md](../apps/desktop/README.md) (Keep working / Quit and cancel export / Quit anyway); partial export artifacts cleaned; source originals unchanged | Manual GUI |
| Sidecar crash | Kill sidecar while UI is open | UI shows failure / unreachable API; restarting the app recovers or documents retry; originals untouched | Manual |
| Port in use | Force bind conflict on the intended loopback port | Clear error; process must **not** listen on `0.0.0.0` | Manual / note |

---

## Matrix — import / scale

| Row | Command / action | Pass criteria | Automates? |
| --- | ---------------- | ------------- | ---------- |
| 100 synthetic path import | `npm run generate:synthetic -- --output /tmp/fp-synth-100 --count 100` then path-import via desktop (**Choose a folder**) or `POST .../imports/from-paths` (chunk ≤100, same `job_id`, `finalize` on last slice) | Job reaches `complete` (or `complete_with_errors` only for unsupported skips); copies under `{root_path}/originals`; source size/mtime/bytes unchanged | Partial (API tests cover path-import immutability; GUI picker may be `[~]`) |
| 100 from-paths RSS | `npm run perf:api -- --output /tmp/fp-from-paths-100 --count 100 --import-mode from-paths` | Documented in performance baseline; no crash; originals unchanged | Yes (API) |
| Optional 500 | `npm run perf:api -- --output /tmp/fp-perf --counts 500` | Documented timing/RSS in performance notes when run; no crash. Multipart `/import` (scale) or add `--import-mode from-paths` | Yes (API) |
| Optional 2000 | `npm run perf:api -- --output /tmp/fp-perf --counts 2000` | Same; GUI review of 2000 is **not** required by default | Yes (API) |
| Full cull workflow | Follow [tests/desktop/workflow.md](../tests/desktop/workflow.md) | Import → process → keyboard cull → CSV/ZIP/folder export + reveal | Manual / API pytest for path-import→export |
| Install / uninstall | Follow [Unsigned desktop install tutorial](desktop_install.md): download the unsigned GitHub Release (`v2.1.3-desktop`) NSIS `.exe` / macOS `.dmg` (Actions `FramePilot-windows-nsis` / `FramePilot-macos-dmg` fallback), handle SmartScreen / Gatekeeper, launch once, quit, uninstall | App binary removed; **data directory may remain** (document for users) — see app-support paths in [apps/desktop/README.md](../apps/desktop/README.md). Unsigned only; do not claim SmartScreen-clean / Gatekeeper-clean. | Manual |

---

## Matrix — security / network

| Row | Notes | Pass criteria |
| --- | ----- | ------------- |
| Loopback only | Sidecar binds `127.0.0.1` | No listen on LAN interfaces / `0.0.0.0` |
| Origin / Host | `FRAMEPILOT_DESKTOP=1` enables Tauri origins; Host checks reject non-loopback | Browsing `http://<LAN-IP>:<port>` from another device **fails**; localhost desktop UI works |
| CORS / LAN | Desktop is not a LAN photo server | Document that LAN access is intentionally impossible |
| Project roots | Custom project folders only via D2.00 registration (`POST /api/desktop/project-roots`) | Paths outside allowlist rejected; `register_root` rejects `$HOME` / `Path.home()` by name; no `$HOME` / drive-root allowlist |
| Native FS | Desktop `getNativeFs()` | Adapter in Tauri (`__TAURI_INTERNALS__` or `__TAURI__`); `null` in a normal browser, including desktop Vite without Tauri, so native pickers are not taken |

---

## Suggested record template

When you run a GUI or install pass, record:

- Date / OS / `APP_VERSION` (from `GET /health`)
- Which rows were `[x]` vs dated `[~]`
- CI artifact run URL if using installers (Actions → `desktop` workflow)
- Confirmation that source originals were not modified

Do not commit photos, databases, or export trees.

---

## S9.12 macOS DMG GUI results

**Verdict: skip, not pass.** Dated `2026-09-05T12:31:10Z` (UTC). Skip is not a macOS GUI pass.

| Field | Value |
| ----- | ----- |
| Date | `2026-09-05T12:31:10Z` |
| OS | Linux / WSL2 — `uname -s` = `Linux`, host `TFSZD-zhangc`, kernel `6.6.87.2-microsoft-standard-WSL2`. Not Darwin. This host cannot mount or launch a `.dmg`. |
| `APP_VERSION` | Not obtained (no packaged macOS window; no DMG sidecar `GET /health`) |
| CI artifact | Not launched. `.github/workflows/desktop.yml` uploads `FramePilot-macos-dmg` and does **not** start the packaged GUI. `verify.yml` is rust-free and also does not. |
| Originals | Not involved (no import-quit session; no camera files) |

Manual GUI rows from the lifecycle + install/uninstall matrix — **none `[x]`**:

| Row | Result |
| --- | ------ |
| Start (installed) | skip `2026-09-05T12:31:10Z` — no macOS GUI host |
| Quit clean | skip — same |
| Quit + import | skip — same |
| Quit + processing | skip — same |
| Quit + export | skip — same |
| Sidecar crash | skip — same |
| Port in use | skip — same |
| Install / uninstall | skip — same |

Linux `npm run test:desktop:smoke` stayed green on this host (`2.1.0-desktop` from a loopback sidecar, not a DMG). That HTTP smoke, frozen sidecar `/health`, and Playwright staying green do **not** convert this skip into a macOS GUI pass.

Windows NSIS GUI lifecycle is already recorded on [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) (Windows-only, 2026-09-04). This slice does not re-run Windows. Unsigned DMG Gatekeeper warnings remain expected; this record does not claim a signed or Gatekeeper-clean Mac pass. Issue: [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172).

---

## Leftover dual-platform installer GUI DoD (macOS DMG install+run)

**Verdict: pass (install+run).** Dated `2026-09-07T09:34:57Z` (UTC). This is **not** a full S9.12 quit+job matrix. The S9.12 skip subsection above stays history. Do not reopen [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172).

| Field | Value |
| ----- | ----- |
| Date | `2026-09-07T09:34:57Z` |
| OS | Darwin — GitHub-hosted `macos-latest` (`uname -s` = `Darwin`) |
| `APP_VERSION` | `2.1.0-desktop` from packaged `GET /health` |
| health | `{"service": "framepilot-api", "status": "ok", "version": "2.1.0-desktop"}` |
| port | `49288` (loopback `127.0.0.1`, not hardcoded `8000`/`6300`) |
| `title_ok` | `true` |
| `result` | `pass` |
| CI | [desktop.yml run 34105891421](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34105891421) — step `Smoke packaged macOS DMG GUI launch` exit 0 |
| Originals | Not involved (leftover smoke does not import photos) |

Install+run row: **Start (installed)** `[x]` — same-job DMG attach + `open` of `FramePilot.app` + loopback `GET /health` with `version` and `service`. The quit+import/processing/export dialog matrix later shipped as leftover [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181).

Windows NSIS GUI pass remains [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144). Unsigned Gatekeeper warnings remain expected; this record does not claim Gatekeeper-clean or store listing. No `APP_VERSION` bump. Issue: [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177).

---

## Leftover unattended packaged-desktop ≥500 GUI

**Verdict: pass (both OS 500).** Dated Windows `2026-09-07T19:39:23Z` and macOS `2026-09-07T19:30:33Z` (UTC). Packaged WebView from-paths + culling preview (**native dialog stubbed**). This is **not** a full S9.12 click-through. Probe-only is not this tick. Playwright `test:e2e:real-browser:large` and `perf:api` 500 are not packaged-desktop GUI evidence.

| Field | Windows | macOS |
| ----- | ------- | ----- |
| Date | `2026-09-07T19:39:23Z` | `2026-09-07T19:30:33Z` |
| OS | `windows` (`uname` `MINGW64_NT-10.0-26100`) | `macos` (`uname` `Darwin`) |
| `APP_VERSION` | `2.1.0-desktop` | `2.1.0-desktop` |
| `mode` / `result` | `500` / `pass` | `500` / `pass` |
| `native_dialog` | `stubbed` | `stubbed` |
| `accepted_files` | 500 | 500 |
| Dataset | 3000×2000 q88 | 3000×2000 q88 |
| `preview_natural_width` | 1800 | 1800 |
| `originals_unchanged` | `true` | `true` |
| Sidecar peak RSS MB | 213.05 | 566.66 |
| UI peak RSS MB | 317.56 | 568.92 |
| CI | [desktop.yml run 34155284835](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34155284835) | same run, job `macos-latest` |

Same-job Path B (`packaging/scripts/desktop-500-gui.sh`) after the just-built unsigned NSIS/DMG. Preview came from a Path B `createRoot` overlay (`via=root`), not a native folder dialog or a full cull-route click-through. Linux/WSL2 `--probe` remains exit 2 / skip is not pass. No `APP_VERSION` bump. Issue: [#179](https://github.com/joe-cheung-cae/frame-pilot/issues/179).

---

## Leftover packaged macOS quit+job matrix

**Verdict: pass (four Darwin rows).** Dated `2026-09-08T13:26:18Z` (UTC). Path B starts the job; production `handle_close_requested`; **Quit and cancel** click. Native folder dialog stays stubbed. The S9.12 skip subsection and leftover [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) / [#179](https://github.com/joe-cheung-cae/frame-pilot/issues/179) records stay history. Do not reopen [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172).

| Field | Value |
| ----- | ----- |
| Date | `2026-09-08T13:26:18Z` |
| OS | Darwin — GitHub-hosted `macos-latest` (`uname` `Darwin`) |
| `APP_VERSION` | `2.1.0-desktop` |
| `mode` / `result` | `quit-job-matrix` / `pass` |
| `native_dialog` | `stubbed` |
| Corpus | 500 JPEG 3000×2000 q88 |
| `originals_unchanged` | `true` |
| `leftover_listen` | `false` |
| CI | [desktop.yml run 34230112750](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34230112750) on `8658e14` |

| Row | Result | Dialog |
| --- | ------ | ------ |
| Quit clean | `pass` | no dialog (no active job) |
| Quit + import | `pass` | `Import is still running`; stay / cancel_and_quit / quit_anyway |
| Quit + processing | `pass` | `Grouping and ranking is still running`; stay / cancel_and_quit / quit_anyway |
| Quit + export | `pass` | `Export is still running`; stay / cancel_and_quit / quit_anyway |

Same-job Path B (`packaging/scripts/desktop-quit-job-gui.sh`) after the just-built unsigned DMG. Linux/WSL2 remains exit 2 / skip is not pass. Stay / Quit anyway stay Rust unit-tested. No `APP_VERSION` bump. No Gatekeeper-clean or store listing claim. Issue: [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181).

---

## Leftover packaged Windows quit+job matrix

**Verdict: pass (four Windows rows).** Dated `2026-09-08T15:29:33Z` (UTC). Path B starts the job; production `CloseMainWindow` / `handle_close_requested`; **Quit and cancel** click. Native folder dialog stays stubbed. Do not reopen [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) / [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172) / [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) / [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181). Do not re-stamp the Darwin #181 table above.

| Field | Value |
| ----- | ----- |
| Date | `2026-09-08T15:29:33Z` |
| OS | Windows — GitHub-hosted `windows-latest` (`uname` `MINGW64_NT-10.0-26100`) |
| `APP_VERSION` | `2.1.0-desktop` |
| `mode` / `result` | `quit-job-matrix` / `pass` |
| `native_dialog` | `stubbed` |
| Corpus | 500 JPEG 3000×2000 q88 |
| `originals_unchanged` | `true` |
| `leftover_listen` | `false` |
| Production quit-clean | `CloseMainWindow` → `CloseRequested` |
| Job-row quit | fail-closed `qa_request_close` + `[data-choice=cancel_and_quit]` |
| CI | [desktop.yml run 34242430942](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34242430942) on `37b710b` |

| Row | Result | Dialog |
| --- | ------ | ------ |
| Quit clean | `pass` | no dialog (no active job) |
| Quit + import | `pass` | `Import is still running`; stay / cancel_and_quit / quit_anyway |
| Quit + processing | `pass` | `Grouping and ranking is still running`; stay / cancel_and_quit / quit_anyway |
| Quit + export | `pass` | `Export is still running`; stay / cancel_and_quit / quit_anyway |

Same-job Path B (`packaging/scripts/desktop-quit-job-gui.sh`) after the just-built unsigned NSIS. First dispatch [34238830561](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34238830561) failed quit-clean leftover LISTEN (`tasklist | grep` UTF-16); harness waits via `Get-Process`. Same-run `macos-latest` quit-export flaked (`complete` before cancel); do not reopen #181. Linux/WSL2 remains exit 2 / skip is not pass. Stay / Quit anyway stay Rust unit-tested. No signing. No SmartScreen-clean or store listing claim. Issue: [#184](https://github.com/joe-cheung-cae/frame-pilot/issues/184).

---

## Leftover Windows packaged sidecar first-launch timeout

**Verdict: code landed; do not invent a Windows GUI pass.** Issue [#190](https://github.com/joe-cheung-cae/frame-pilot/issues/190). Joe’s unsigned `v2.1.0-desktop` NSIS first Start on Windows 11 failed with `timed out waiting for sidecar ready line` (retry also failed). Warm `windows-latest` GUI leftovers (#179 / #184) did not catch a cold Defender + PyInstaller boot that exceeds 15s.

| Check | Command / action | Pass |
| ----- | ---------------- | ---- |
| API sidecar CLI | `npm run test:api -- apps/api/tests/test_sidecar_cli.py` | Exit 0; ready marker + Windows 120s source assert |
| Rust sidecar unit | `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml` | Exit 0; preamble skip, ready-file fallback, spawn cwd / `PYTHONUNBUFFERED` |
| Windows first Start | Fresh unsigned NSIS from `v2.1.3-desktop` → Start menu **FramePilot** (do not pre-run `framepilot-api.exe`) | Window title `FramePilot`; project UI; no ready-line timeout within two minutes; optional `sidecar.ready` + `GET /health` on the allocated port |

Do not reopen [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) / [#184](https://github.com/joe-cheung-cae/frame-pilot/issues/184). Do not touch tray / D3.06 / #41. No `APP_VERSION` bump. No signing. Manual path: [Unsigned desktop install tutorial](desktop_install.md). Win11 cold first-start, Import/Export, and locked-file upgrade packages: leftover [#200](https://github.com/joe-cheung-cae/frame-pilot/issues/200) `v2.1.3-desktop` (do not invent a pass here).

---

## Leftover NSIS locked `_internal` upgrade

**Verdict: code landed; do not invent a Windows GUI pass.** Issue [#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198). Joe’s unsigned `v2.1.2-desktop` NSIS upgrade on Windows 11 hit **Error opening file for writing** on `framepilot-api\_internal\MSVCP140.dll`. Repeated **Ignore** left a half-written `_internal` tree and blank Import/Export. That is a broken install, not a #195 regression. Tauri only stops `framepilot-desktop.exe`; the sidecar keeps the DLLs locked.

| Check | Command / action | Pass |
| ----- | ---------------- | ---- |
| Hook wiring | `bash scripts/check-nsis-locked-upgrade-hooks.sh` | Exit 0; `installerHooks` → `windows/hooks.nsh`; Retry/Cancel only; no Ignore |
| Win11 upgrade while running | Previous NSIS installed + FramePilot UI up + run **`v2.1.3-desktop`** / #198+ NSIS | Installer stops with Retry/Cancel; Cancel leaves the old tree intact; after File → Quit + Retry, `_internal\MSVCP140.dll` exists; create project → Import/Export open |

Use leftover [#200](https://github.com/joe-cheung-cae/frame-pilot/issues/200) `v2.1.3-desktop` for the locked-file upgrade check. Published `v2.1.2-desktop` NSIS does **not** include the hooks. If that older wizard shows the file-in-use dialog, click **Abort**, quit FramePilot, retry — never Ignore. Written path: [Unsigned desktop install tutorial](desktop_install.md#upgrade-close-the-app-first). Plan: [docs/plans/2026-09-09-unsigned-desktop-nsis-hooks-release.md](plans/2026-09-09-unsigned-desktop-nsis-hooks-release.md). Do not reopen #194 / #196 / #190. Do not touch tray / D3.06 / #41. No `APP_VERSION` bump. No signing.
