# Desktop Testing Matrix

> Language: **English** | [中文](desktop_testing.zh.md)

Manual and command-driven checks for FramePilot desktop (`2.1.0-desktop` track). Local-first: never modify or delete original camera files. Prefer project copies under `{root_path}/originals`.

`npm run verify` is the rust-free CI gate (lint, typecheck, tests, artifacts). It does **not** open a WebView or run `cargo`/`tauri`. GUI rows need a host with rustc ≥1.88 (and a display). Mark unverified GUI rows `[~]` with date and host notes — never invent pass results.

**Related:** [Desktop shell README](../apps/desktop/README.md) · [Signing runbook](desktop_signing.md) · [Phase 2 workflow checklist](../tests/desktop/workflow.md) · [Phase 5 design](plans/2026-08-29-phase5-docs-design.md)

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
| `npm run test:desktop:smoke` | HTTP smoke: sidecar health + `/api/projects` (`tests/desktop/smoke.sh`) |
| `npm run generate:synthetic -- --output <dir> --count <n>` | Synthetic JPEGs for path-import rows |
| `npm run perf:api -- --output <dir> --counts 100 500 2000` | Optional API-scale multipart import/process smoke (not `from-paths`) |
| `npm run packaging:sidecar` | PyInstaller one-dir sidecar |
| `npm run test:sidecar` | Sidecar ready-line smoke |
| `npm run verify` | Rust-free full verify |

No extra npm alias is required for this matrix; use the scripts above directly.

---

## Matrix — lifecycle

| Row | Command / action | Pass criteria | Automates? |
| --- | ---------------- | ------------- | ---------- |
| Start (dev) | `npm run dev:desktop` | Window title `FramePilot`; sidecar on loopback; `GET /health` → 200 with `version` + `service` | Manual GUI |
| Start (installed) | Launch NSIS/DMG build from CI or local `tauri build` | Same as above without running uvicorn yourself | Manual |
| HTTP smoke | `npm run test:desktop:smoke` | Exit 0 | Yes |
| Quit clean | Close window with no active import/processing job | Sidecar exits; no orphan uvicorn on that port | Manual GUI |
| Quit + import | Close during an active import | Dialogs per [apps/desktop/README.md](../apps/desktop/README.md) (Keep working / cancel import / Quit anyway); source originals unchanged | Manual GUI |
| Sidecar crash | Kill sidecar while UI is open | UI shows failure / unreachable API; restarting the app recovers or documents retry; originals untouched | Manual |
| Port in use | Force bind conflict on the intended loopback port | Clear error; process must **not** listen on `0.0.0.0` | Manual / note |

---

## Matrix — import / scale

| Row | Command / action | Pass criteria | Automates? |
| --- | ---------------- | ------------- | ---------- |
| 100 synthetic path import | `npm run generate:synthetic -- --output /tmp/fp-synth-100 --count 100` then path-import via desktop (**Choose a folder**) or `POST .../imports/from-paths` (chunk ≤100, same `job_id`, `finalize` on last slice) | Job reaches `complete` (or `complete_with_errors` only for unsupported skips); copies under `{root_path}/originals`; source size/mtime/bytes unchanged | Partial (API tests cover path-import immutability; GUI picker may be `[~]`) |
| Optional 500 | `npm run perf:api -- --output /tmp/fp-perf --counts 500` | Documented timing/RSS in performance notes when run; no crash. Multipart `/import` only — not `from-paths` (#97) | Yes (API) |
| Optional 2000 | `npm run perf:api -- --output /tmp/fp-perf --counts 2000` | Same; GUI review of 2000 is **not** required by default | Yes (API) |
| Full cull workflow | Follow [tests/desktop/workflow.md](../tests/desktop/workflow.md) | Import → process → keyboard cull → CSV/ZIP/folder export + reveal | Manual / API pytest for path-import→export |
| Install / uninstall | Install CI Windows NSIS or macOS DMG; launch once; uninstall | App binary removed; **data directory may remain** (document for users) — see app-support paths in [apps/desktop/README.md](../apps/desktop/README.md) | Manual |

---

## Matrix — security / network

| Row | Notes | Pass criteria |
| --- | ----- | ------------- |
| Loopback only | Sidecar binds `127.0.0.1` | No listen on LAN interfaces / `0.0.0.0` |
| Origin / Host | `FRAMEPILOT_DESKTOP=1` enables Tauri origins; Host checks reject non-loopback | Browsing `http://<LAN-IP>:<port>` from another device **fails**; localhost desktop UI works |
| CORS / LAN | Desktop is not a LAN photo server | Document that LAN access is intentionally impossible |
| Project roots | Custom project folders only via D2.00 registration (`POST /api/desktop/project-roots`) | Paths outside allowlist rejected; no `$HOME` / drive-root allowlist |

---

## Suggested record template

When you run a GUI or install pass, record:

- Date / OS / `APP_VERSION` (from `GET /health`)
- Which rows were `[x]` vs dated `[~]`
- CI artifact run URL if using installers (Actions → `desktop` workflow)
- Confirmation that source originals were not modified

Do not commit photos, databases, or export trees.
