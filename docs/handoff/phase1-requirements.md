# Desktop Phase 1 Requirements Breakdown

Handoff stage: `需求拆解`  
Date: 2026-08-19T16:59:14+08:00  
Branch for this pipeline: `feature/desktop-packaging` (checked out from `origin/main` at `1d6ffa7`)  
Scope fence: **desktop packaging Phase 1 only** — task ids **D1.01–D1.09** from `docs/plans/2026-08-18-desktop-packaging.md`.

This document is the implementation contract for later stages (`评审` → `归档` → `开发` → `测试` → `上线`). It does not implement production code.

**Not this document:**

- `implement_goals.md` Phase 1 (“v2.1 Processing and Progress” for the older v2 web Goal Mode)
- Desktop Phase 0 (D0.00–D0.09) — already closed `上线` 2026-08-19 with GO
- Desktop Phases 2–5 (D2.00–D5.05): registered project roots, native pickers, menus, installers, version bump to `2.1.0-desktop`

**Sources of truth (read in this order when implementing):**

1. `AGENTS.md` + `develop_plan.md` (local-first, original-file safety, English, tests)
2. `docs/plans/2026-08-18-desktop-packaging.md` (technical decisions, files, tests, commit messages; wins on technical conflict)
3. `docs/desktop_development_plan.md` §6 Phase 1 (product why; this file does not add task ids)
4. `docs/plans/2026-08-18-desktop-packaging-review.md` (adapter / Vite / allowlist defects already folded into the refined backlog)
5. This file (phase-bounded contract for the `feature/desktop-packaging` pipeline)
6. `docs/desktop_goal_mode.md` (loop rules; tracker still lives in the implementation plan §5.1)
7. `docs/desktop_feasibility_notes.md` (Phase 0 GO; D0.07 rustc `[~]` inherited)

Conflict rule from the implementation plan: on any technical conflict that plan wins, and the product plan must be edited in the same commit that resolves the conflict. The product plan never introduces a new task id.

---

## 1. Goal

`npm run dev:desktop` opens FramePilot UI that can list projects through the sidecar, or a Vite/HTTP equivalent is `[x]` while WebView/compile remains dated `[~]` on this host.

Phase 1 must leave the tree able to:

- Isolate Next.js navigation behind a types + re-export adapter so shared components never import `next/link` or `next/navigation`.
- Resolve the API base **at call time** from `window.__FRAMEPILOT_API_BASE__`, then `NEXT_PUBLIC_API_BASE_URL`, then `http://127.0.0.1:8000`.
- Detect the desktop shell only via `isDesktopShell()` (`window.__FRAMEPILOT_DESKTOP__ === true`).
- Build a Vite + React SPA in `apps/desktop` that reuses `apps/web/src/components`, `src/lib`, and `src/store` through a `@` alias, with Tailwind tokens imported (not copied) and `globals.css` imported (not forked).
- Route the same pages as `apps/web/src/app` plus a catch-all to home.
- Manage sidecar lifecycle in Rust: allocate a loopback port, pass `--port <n>` (never `--port 0` on the shipped path), required absolute `--data-dir`, `FRAMEPILOT_DESKTOP=1`, ready-line parse, inject both window globals before UI load.
- Use OS app-support data directories. Packaged runs never fall back to CWD-relative `.framepilot-data`.
- Provide window basics (title `FramePilot`, min size ~1100×720, remembered bounds, single instance) when a WebView can open.
- Wire `dev:desktop` without making `npm run verify` require rustc, cargo, or Tauri.
- Smoke `GET /health` and `GET /api/projects` from the injected base (HTTP is enough for the non-GUI half).
- On quit with an active job: confirm, cancel-or-drain, reuse the existing POST cancel route, and show `importLoadRecoveryMessage` on next launch rather than a bare “failed”.

Product baseline today (verified against the live tree on `feature/desktop-packaging` at `1d6ffa7`):

| Area | Live state | Phase 1 implication |
|------|------------|---------------------|
| Version | `2.0.0-rc2` via `apps/api/app/core/version.py` (`APP_VERSION`) | Do not bump. D5.04 is out of scope |
| Frontend | Next.js 15 App Router; shared pages wrap components in `Shell` | Do not migrate `apps/web`. Do not add `output: 'export'` |
| API base | Frozen module-level `API_BASE` in `apps/web/src/lib/api.ts:1`; `request`, `exportDownloadUrl`, `assetUrl` bake it at load | D1.02 must call `resolveApiBase()` at call time |
| Navigation | `next/link` in `Shell.tsx`, `ProjectList.tsx`, `ProjectDashboard.tsx`, `ProcessingPanel.tsx`, `ImportPanel.tsx`, `CullingWorkspace.tsx`; `next/navigation` `useRouter` in `ProjectCreator.tsx` and `CullingWorkspace.tsx`; `useSearchParams` in `CullingWorkspace.tsx:67` | D1.01 adapter; Vite aliases `./navigation.next` in D1.03a |
| Test runners | `node --test src/lib/*.test.ts` plus vitest `src/**/*.test.tsx` only (`apps/web/package.json`, `vitest.config.ts`) | Adapter tests must be `navigation.test.tsx`, not `.test.ts` |
| Component mocks | `CullingWorkspace.test.tsx` mocks `next/link` + `next/navigation`; `ProcessingPanel.test.tsx` and `ImportExportPanels.test.tsx` mock `next/link` | Re-point mocks to `@/lib/navigation` in the D1.01 commit |
| Shell flag | No `shell.ts`; `Providers.tsx` is QueryClient only | D1.02a + `applyShellDataset()` from Providers (browser) and desktop entry |
| Desktop tree | Phase 0 verify-safe skeleton: `index.html` + `health.js`, `src-tauri/` (CSP locked, spawn notes in `lib.rs`), no Vite `src/` | Evolve in place; D1.03b replaces the blank HTML probe |
| Root scripts | `install:all` installs api + root + `apps/web` only; `typecheck` is web only; `dev:desktop` echoes rustc missing and exits 1; `verify` does not invoke Rust | D1.03a adds `typecheck:desktop` / `lint:desktop` to `verify` **without** Rust; D1.07 rewires `dev:desktop` |
| Sidecar | Phase 0 CLI works (`--host 127.0.0.1`, required `--data-dir`, `--port 0` for tests, ready line). Origins add Tauri hosts only when `FRAMEPILOT_DESKTOP=1` | Shipped Tauri path must pass `--port <n>` and set the env before serve |
| Rust spawn skeleton | `lib.rs` allocates a port and documents spawn, but `terminate` uses `kill` and `run()` does not start the child | D1.04/D1.09 must SIGTERM then kill after 5s; inject globals; parse ready line |
| Jobs | In-process FastAPI `BackgroundTasks`; `test_job_reliability.py` already covers crash/startup/idempotent fail | D1.09 **extends** that file on the shipped cancel/retry path |
| Recovery copy | `importLoadRecoveryMessage` in `apps/web/src/lib/importWorkflow.ts` | Next launch after a killed job must show this, not a bare “failed” |
| Path import | API exists (D0.04b/c). Frontend `api.ts` still has multipart only | Client `from-paths` loop is **D2.03**, not Phase 1 |
| Project roots | Allowlist still `{data_dir}/projects` or `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` | D2.00 is out. Never set the allowlist to `$HOME` |
| Artifact check | Single icons exception from D0.07a; `.gitignore` has `target/` and `.framepilot-desktop-dev/` | Do not widen further |
| `tests/desktop/` | Missing | D1.08 creates smoke |
| Phase 0 GUI | D0.07 `[~]` — rustc/cargo/rustup missing 2026-08-19 | Inherited. Not a Phase 1 **start** blocker |

Phase 0 acceptance already holds: sidecar/health/SIGTERM `[x]`; origin+Host `[x]`; path import + immutability `[x]`; feasibility notes `[x]`; `test:api` + `verify` `[x]`; browser web app `[x]`; GUI shell `[~]`.

---

## 2. Locked decisions

These are binding for Phase 1. Do not re-litigate them unless a later stage writes a go/no-go change in `docs/desktop_feasibility_notes.md`. Phase 0 already chose Tauri 2 + Vite SPA + keep scipy.

1. **Shell:** Tauri 2 + Python sidecar. Electron stays off the table. Missing rustc is compile-blocked, not the Electron trigger. Sidecar **was** spawned in Phase 0.
2. **Frontend:** Dual shell, single component library.
   - `apps/web` = Next.js for browser + Playwright. **Do not migrate. Do not add `output: 'export'`.**
   - `apps/desktop` = Tauri + Vite SPA.
   - Shared: `apps/web/src/components/*`, `apps/web/src/lib/*`, `apps/web/src/store/*`.
   - Navigation adapter is swapped by **Vite alias** of `./navigation.next` → `apps/desktop/src/navigation.router.tsx`. A barrel that re-exports `next/link` would pull Next into Vite (review A2.6 / A2.7).
3. **IPC:** HTTP to the sidecar for v2.1. No rewrite of scoring/grouping onto Rust. Optional Tauri IPC for dialogs/paths/reveal is **Phase 2**.
4. **Bind:** Sidecar listens on `127.0.0.1` only. Never `0.0.0.0`.
5. **Port:** Rust allocates a free loopback TCP port (`TcpListener::bind("127.0.0.1:0")`, read addr, **drop the listener**, pass `--port <n>`). The shipped path **never** passes `--port 0`. `--port 0` remains valid for tests and standalone smoke. Ready-line port must match the allocated port or fail fast.
6. **Data dir:** Tauri always passes absolute `--data-dir` / `FRAMEPILOT_DATA_DIR`:
   - macOS: `~/Library/Application Support/FramePilot`
   - Windows: `%APPDATA%\FramePilot`
   - Linux (dev only): `~/.local/share/FramePilot`
   Packaged runs never use repo `.framepilot-data`. Dev may use `.framepilot-desktop-dev` (already gitignored). Sidecar `--data-dir` stays required.
7. **Desktop env:** spawn sets `FRAMEPILOT_DESKTOP=1` so origin/Host policy allows `:1420` and `tauri.localhost` / `tauri://localhost`.
8. **Window injection (before frontend load):**
   - `window.__FRAMEPILOT_API_BASE__` = `http://127.0.0.1:<allocated>`
   - `window.__FRAMEPILOT_DESKTOP__ === true` (literal boolean, not `"1"`)
9. **Shell detection:** shared code reads the flag only through `isDesktopShell()` in `apps/web/src/lib/shell.ts`. D3.02/D3.04 later consume the helper / `[data-shell="desktop"]`, never inline `window` checks.
10. **Safety:** Copy-mode unchanged. Originals are never modified or deleted. Do not weaken export/asset path-escape or allowlist tests.
11. **Web app must keep working.** `npm run dev` on `:3000` / `:8000`, `npm run verify`, and Playwright file inputs in `ImportPanel.tsx` stay green. `npm run verify` must **not** install or require rustc, cargo, or Tauri.
12. **Project roots:** `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` must **never** be set to `$HOME`, `/`, a drive root, or any broad parent by the Tauri shell. Custom roots are D2.00. `test_create_project_rejects_root_outside_allowlist` stays green unchanged.
13. **GUI-blocked tasks:** if remaining verification needs a real WebView or rustc/cargo and this host cannot provide them, mark `[~]`, append a dated command + error to `docs/desktop_feasibility_notes.md`, and continue. `[~]` is never `[x]` without a recorded GUI/toolchain run. Split D1.08: HTTP smoke can be `[x]` while WebView stays `[~]`.
14. **Single version source:** `APP_VERSION` stays `2.0.0-rc2`. Do not bump `pyproject.toml` or either `package.json` in Phase 1.
15. **Vite / Tailwind:** alias `"@"` → `../web/src`. `server.fs.allow` includes `../web`. Port **1420**, `strictPort: true`. Extract shared color tokens from `apps/web/tailwind.config.ts` and import them from both configs — do not duplicate hex (`ink #151515`, `mist #f5f7f8`, `line #d8dedc`, `leaf #2f6f5e`, `coral #bf5b45`, `gold #a77721`). `src/styles.css` is `@import "../../web/src/app/globals.css";` — no CSS fork.
16. **Desktop downloads:** not Phase 1. Browser keeps `<a download>`. Reveal-in-folder is D2.09.
17. **This pipeline’s branch:** land on `feature/desktop-packaging`. Do not checkout other branches. Do not open a PR. Do not merge to `main`. Push after each finished stage (`git push -u origin HEAD`).
18. **No cloud, login, payment, bundled models, HEIC/RAW/XMP.**
19. **Tracker:** `docs/plans/2026-08-18-desktop-packaging.md` §5.1 remains the status source of truth. `开发` may make extra per-task commits. Final Phase 1 ticks are owned by `上线`. Do not start D2–D5. Do not retick Phase 0 except to leave D0.07 `[~]`.

---

## 3. In-scope ids

Implement **only** these ids, in dependency order. Session rule from the plan: one id at a time, tests first, then implementation. This pipeline allows extra per-task commits during `开发` and requires a final `开发` stage commit.

Suggested serial order (lowest incomplete id whose dependencies are done):

| ID | Title | Depends on |
|----|-------|------------|
| D1.01 | Navigation adapter | Phase 0 exit (already GO) |
| D1.02 | Runtime API base | D1.01 |
| D1.02a | Desktop shell flag | D1.02 |
| D1.03a | Vite build, aliases, Tailwind | D1.01, D1.02 |
| D1.03b | Desktop router | D1.03a, D1.02a |
| D1.04 | Sidecar lifecycle in Rust | D0.07 (source exists; `[~]` compile is OK), D1.03b |
| D1.05 | App-support data directory | D1.04 |
| D1.06 | Window basics and single instance | D1.04 |
| D1.07 | Dev scripts and verify wiring | D1.03a, D1.04 |
| D1.08 | Desktop smoke: health + project list | D1.04, D1.05, D1.07 |
| D1.09 | Graceful quit with a running job | D1.04, D1.06 |

Current §5.1 Phase 1 boxes (all `[ ]` as of this breakdown):

- [ ] D1.01 Navigation adapter
- [ ] D1.02 Runtime API base
- [ ] D1.02a Desktop shell flag
- [ ] D1.03a Vite build, aliases, Tailwind
- [ ] D1.03b Desktop router
- [ ] D1.04 Sidecar lifecycle in Rust
- [ ] D1.05 App-support data directory
- [ ] D1.06 Window basics and single instance
- [ ] D1.07 Dev scripts and verify wiring
- [ ] D1.08 Desktop smoke: health + project list
- [ ] D1.09 Graceful quit with a running job

Do not tick a box in this documentation stage.

Allowed D1.01 split from the plan (finish all three before D1.03a): (a) adapter + tests, (b) Shell/list/dashboard/processing, (c) import/creator/culling + mocks.

---

## 4. Out of scope

Explicitly **not** Phase 1:

- **`implement_goals.md` Phase 1** (v2 web job-progress / ranking work). Do not mix v2 algorithm Goal Mode into this track.
- **Desktop Phase 0 redo.** Do not reimplement sidecar CLI, health payload, origins, path-import API, PyInstaller spec, or D0.07a. D0.07 remains `[~]` until a dated rustc/WebView run succeeds.
- **Desktop Phase 2:** D2.00 registered project roots, native file dialogs, picker-backed project create, import-panel `from-paths` client loop, drag-and-drop, reveal-in-folder, recent projects, path hardening, full workflow E2E, reveal-instead-of-download.
- **Desktop Phase 3:** native menus, status bar, `GET /api/meta`, system theme, tray, shortcut-vs-menu pass.
- **Desktop Phase 4:** bundling sidecar into Tauri resources, NSIS/DMG, desktop CI matrix, signing, size pass.
- **Desktop Phase 5:** desktop test matrix, user docs, performance notes, **version bump to `2.1.0-desktop`**, known-limitations closeout (except a D1.09 gap note if a remaining quit hole exists).
- Detached preview window, concurrency/cache knobs, auto-update (deferred to 2.2).
- Setting `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME` as a shortcut for native pickers.
- Migrating `apps/web` off Next.js, deleting App Router pages, or adding `output: 'export'`.
- Removing the two `ImportPanel.tsx` file inputs (`tests/e2e/local-workflow.spec.ts` depends on them).
- Replacing scoring/grouping with Rust.
- HEIC / RAW / XMP / bundled neural models / cloud / login / payment.
- Making `npm run verify` require Rust, Tauri, or Playwright.
- Publishing installers, opening a PR, or merging to `main`.
- Starting `评审` implementation notes as if they were code, or starting `开发` in this stage.

---

## 5. Files to create / modify

### D1.01 — Navigation adapter (keep Next working)

- **Create:** `apps/web/src/lib/navigation.ts` — types + re-export point only (`Link`, `useNavigator`, `useQueryParams` from `./navigation.next`)
- **Create:** `apps/web/src/lib/navigation.next.tsx` — `Link` wraps `next/link`; `useNavigator().push` uses `next/navigation` `useRouter`; `useQueryParams(): URLSearchParams` wraps `useSearchParams`. Do **not** re-export `next/link` from a barrel Vite will load.
- **Modify (live `next/link` / `next/navigation` imports, grep-verified 2026-08-19):**
  - `apps/web/src/components/Shell.tsx` (`next/link`)
  - `apps/web/src/components/ProjectList.tsx` (`next/link`)
  - `apps/web/src/components/ProjectDashboard.tsx` (`next/link`)
  - `apps/web/src/components/ProcessingPanel.tsx` (`next/link`)
  - `apps/web/src/components/ImportPanel.tsx` (`next/link`)
  - `apps/web/src/components/ProjectCreator.tsx` (`useRouter` from `next/navigation`; `router.push` on create success)
  - `apps/web/src/components/CullingWorkspace.tsx` (`next/link`, `useRouter`, `useSearchParams`; filter query via `searchParams.get("filter")`)
- **Modify mocks:** `CullingWorkspace.test.tsx`, `ProcessingPanel.test.tsx`, `ImportExportPanels.test.tsx` — re-point to `@/lib/navigation`
- **Test:** `apps/web/src/lib/navigation.test.tsx` (vitest; **not** `.test.ts`)

Shared components import `@/lib/navigation` only. No `next/link` or `next/navigation` under `apps/web/src/components/`. `CullingWorkspace` consumes only `useQueryParams()`. App Router pages under `apps/web/src/app/**` may stay as they are (they do not import Next navigation today).

### D1.02 — Runtime API base

- **Create:** `apps/web/src/lib/apiBase.ts` (`resolveApiBase()`)
- **Create:** `apps/web/src/types/globals.d.ts` (`Window.__FRAMEPILOT_API_BASE__`, `Window.__FRAMEPILOT_DESKTOP__`)
- **Modify:** `apps/web/src/lib/api.ts` — keep exporting `API_BASE`, but `request`, `exportDownloadUrl`, and `assetUrl` must call `resolveApiBase()` **at call time**
- **Test:** `apps/web/src/lib/apiBase.test.ts` (node `--test`) and update `apps/web/src/lib/api.test.ts`

Order: `window.__FRAMEPILOT_API_BASE__`, then `NEXT_PUBLIC_API_BASE_URL`, then `http://127.0.0.1:8000`. Trim trailing slash. Missing `window` must not throw (`next build`). Existing `assetUrl` encoding assertions in `api.test.ts:79-93` must still hold on the default base. `ExportPanel.tsx` already calls `exportDownloadUrl`; it must pick up an injected host without further UI work.

### D1.02a — Desktop shell flag

- **Create:** `apps/web/src/lib/shell.ts`
- **Test:** `apps/web/src/lib/shell.test.ts` (and `.test.tsx` only if DOM is required)
- **Modify:** `apps/web/src/components/Providers.tsx` — call `applyShellDataset()` so the browser shell is `"browser"`

`isDesktopShell()` is true only for literal `true`. False for `undefined`, `"1"`, `0`, or missing `window`. `applyShellDataset()` sets `document.documentElement.dataset.shell`. Desktop entry calls it in D1.03b.

### D1.03a — Vite desktop build with shared aliases and Tailwind

- **Create:** `apps/desktop/vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`, `src/main.tsx`, `src/styles.css`
- **Create:** shared Tailwind token module imported by both `apps/web/tailwind.config.ts` and `apps/desktop/tailwind.config.ts` (do not duplicate hex)
- **Create:** `apps/desktop/src/navigation.router.tsx` stub until D1.03b
- **Modify:** `apps/desktop/package.json` (replace the Phase 0 echo-only skeleton). Dependencies mirroring web: `react`, `react-dom`, `@tanstack/react-query`, `@tanstack/react-virtual`, `zustand`, `lucide-react`, plus `react-router-dom`. Dev: `vite`, `@vitejs/plugin-react`, `typescript`, `tailwindcss` ^3.4, `postcss`, `autoprefixer`, `@tauri-apps/cli`
- **Modify:** root `package.json` — `install:all` also `npm --prefix apps/desktop install`; add `typecheck:desktop` and `lint:desktop`; add `typecheck:desktop` to `verify` **without** rustc/cargo/tauri
- Keep existing `apps/desktop/src-tauri/` tree. Do not delete D0.07a icons.

Vite: alias `"@"` → `../web/src`; alias the `./navigation.next` import to `./src/navigation.router.tsx`; `server.fs.allow` includes `../web`; port **1420**, `strictPort: true`. `src/styles.css`: `@import "../../web/src/app/globals.css";`.

### D1.03b — Desktop router reusing shared page components

- **Create:** `apps/desktop/src/router.tsx`, full `navigation.router.tsx` (D1.01 contract: `href` → `to`, drop `prefetch`), `App.tsx`
- **Modify:** `apps/desktop/src/main.tsx`
- **Replace:** Phase 0 `index.html` / `health.js` placeholder with the Vite entry

Routes must match `apps/web/src/app` exactly (verified 2026-08-19):

| Path | Shared UI |
|------|-----------|
| `/` | `ProjectList` inside `Shell` |
| `/help` | Help shortcuts page inside `Shell` |
| `/settings` | `SettingsPanel` inside `Shell` |
| `/projects/new` | `ProjectCreator` inside `Shell` |
| `/projects/:projectId` | `ProjectDashboard` |
| `/projects/:projectId/import` | `ImportPanel` |
| `/projects/:projectId/process` | `ProcessingPanel` |
| `/projects/:projectId/cull` | `CullingWorkspace` |
| `/projects/:projectId/export` | `ExportPanel` |
| `*` | home |

Same providers as `Providers.tsx`. Call `applyShellDataset()`. Leave `"use client"` directives in shared files.

### D1.04 — Sidecar lifecycle in Rust

- **Create:** `apps/desktop/src-tauri/src/sidecar.rs`
- **Modify:** `apps/desktop/src-tauri/src/lib.rs` (and `Cargo.toml` only if tests/new crates require it)
- **Tests:** Rust unit tests for `allocate_loopback_port()` and `parse_ready_line()`

Implement:

- Allocate port in Rust; drop the listener; pass `--port <n>`. Never `--port 0` in the shipped path.
- Always pass absolute `--data-dir`. Env `FRAMEPILOT_DESKTOP=1`.
- Inject both globals **before** frontend load.
- Parse stdout ready line `FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>`; fail fast if reported port differs.
- Crash policy: one automatic restart; if health fails twice, blocking error page.
- Shutdown: SIGTERM, wait 5s, then kill. Windows: job object or `GenerateConsoleCtrlEvent` — document which in feasibility notes if reached.
- Log sidecar stderr to `{data_dir}/logs/sidecar.log`.

Phase 0 `lib.rs` already has a port helper and a ready-line prefix check, but `run()` does not spawn and `terminate` kills immediately. Replace that with the lifecycle above. Tick D1.04 `[x]` only if `cargo test` ran; else `[~]` with a dated toolchain note, while still landing the Rust **source** and unit tests.

### D1.05 — App-support data directory

- **Files:** Rust path helper only (do not duplicate the policy in TypeScript)
- Default dirs as locked decision 6. Create on first launch.
- **Tests:** table-driven Rust tests for macOS / Windows / Linux prefixes

### D1.06 — Window basics and single instance

- **Modify:** `apps/desktop/src-tauri/tauri.conf.json` and Rust setup
- Title `FramePilot` (already set). Min size ~1100×720 (current window is 1200×800 with no min). Remember position/size. Single instance focuses the first window. Close window stops the sidecar.
- **Tests:** none (shell). Run `cargo check` if rustc exists; otherwise record `[~]`.

### D1.07 — Dev scripts and verify wiring

- **Modify:** root `package.json`, `apps/desktop/package.json`, `apps/desktop/README.md`
- `npm run dev:desktop` → tauri dev + Vite + sidecar **when cargo exists**. If rustc is still missing, fail with a clear message (today’s echo is acceptable until cargo exists) but must not be invoked by `verify`.
- `build:desktop` may wait until Phase 4.
- `verify` must **not** require Rust. `install:all` already installs desktop from D1.03a.
- Tick D1.07 `[x]` if `verify` stays rust-free.

### D1.08 — Desktop smoke: health + project list

- **Create:** `tests/desktop/smoke.sh` (or Playwright against Vite `:1420`)
- **Modify:** root `package.json` (`test:desktop:smoke`)

Acceptance: UI or the Vite page can call `GET /api/projects` and render the home list (empty is OK). Failure must be visible, not a silent CORS 403.

Non-GUI `[x]`: launch the **real** sidecar entry with absolute temp `--data-dir` and `--port 0` (test path only). Parse ready line `host=127.0.0.1` and port ≠ 0. `GET /health` JSON has `status`, `version`, `service`. `GET /api/projects` is a JSON array (empty OK). SIGTERM and process exits. WebView render stays `[~]` if needed — split the tracker note; do not leave the whole id `[ ]`.

### D1.09 — Graceful quit while a job is running

- **Modify:** sidecar/window close handler; reuse existing `POST /api/projects/{id}/jobs/{job_id}/cancel`
- **Test:** extend `apps/api/tests/test_job_reliability.py` on the **shipped** cancel/retry path (do not reimplement cancel in the test). Rust shutdown state machine unit test (returns Kill after the grace window).
- **Docs:** `docs/v2_known_limitations.md` only if a remaining gap exists (current text already says jobs are not durable across API process exits and cancel is cooperative)

On close, if an import/process job is active: confirm — Cancel quit / Quit and cancel job / Quit anyway.

- Cancel: existing POST cancel, wait up to 10s, then SIGTERM.
- Quit anyway: SIGTERM then kill after 5s.
- Next launch: existing startup sweep (`fail_active_jobs_on_startup`); UI must show `importLoadRecoveryMessage`, not a bare “failed”.

Assertions: cancelled-then-restarted import leaves no photo in `processing`; job terminal `cancelled` not `failed`; killed worker still retryable.

### Shared docs in this pipeline

- `docs/handoff/phase1-requirements.md` (this file)
- `docs/handoff/STATUS.md`
- `.grok/workflows/desktop-phase1.rhai` (pipeline definition; include in the breakdown commit if untracked)

---

## 6. Tests-first list

Write the failing test **before** the implementation. A test written after a green implementation does not count for import, export, scoring, status updates, path validation, or job cancel/retry.

This list is the contract that `评审` and the `测试` stage must match.

| ID | Write first | Must assert | Run |
|----|-------------|-------------|-----|
| D1.01 | `apps/web/src/lib/navigation.test.tsx` | `Link` renders `<a href>`; `push` called with expected href; `useQueryParams` reads a value; guard that `apps/web/src/components/*` do not import `next/link` or `next/navigation`; existing component tests pass after mocks move to `@/lib/navigation` | `npm run typecheck && npm run test:web` |
| D1.02 | `apps/web/src/lib/apiBase.test.ts` + `api.test.ts` | window wins; env second; default third; trailing slash trimmed; no throw without window; injected base used by `assetUrl` and `exportDownloadUrl`; existing encoding assertions still hold on the default; do not hardcode unexpected hosts | `npm run typecheck && npm run test:web` |
| D1.02a | `apps/web/src/lib/shell.test.ts` | true only for literal `true`; false for `undefined` / `"1"` / `0`; no throw without window; drive shipped `isDesktopShell` | `npm run typecheck && npm run test:web` |
| D1.03a | desktop build (no unit file required) | `npm --prefix apps/desktop run build` emits non-trivial CSS; `npm run typecheck:desktop`; `npm run verify` still does not require Rust | desktop build + `typecheck:desktop` + `verify` |
| D1.03b | typecheck + desktop build | router typechecks; desktop build still green; `npm run test:web` unaffected | `npm run typecheck:desktop`, desktop build, `npm run test:web` |
| D1.04 | Rust unit tests in `src-tauri` | `allocate_loopback_port()` returns a non-zero `127.0.0.1` port; `parse_ready_line()` accepts the exact ready string and rejects a mismatched port | `cargo test` in `src-tauri` **or** dated rustc/cargo capture; `npm run verify` |
| D1.05 | table-driven Rust tests | macOS / Windows / Linux prefixes match locked decision 6; packaged path is not CWD `.framepilot-data` | `cargo test` or dated `[~]` |
| D1.06 | none (shell) | `cargo check` if possible; GUI recorded or `[~]` | `cargo check` or dated note |
| D1.07 | none (scripts) | `npm run verify` exit 0 and does not invoke rustc/cargo/Tauri | `npm run verify` |
| D1.08 | `tests/desktop/smoke.sh` | ready line host/port; `/health` has `status`/`version`/`service`; `/api/projects` 200 JSON array; SIGTERM exits; CORS/Host failure is visible | `npm run test:desktop:smoke` (skip **only** the WebView half with an explicit message) |
| D1.09 | extend `apps/api/tests/test_job_reliability.py`; Rust quit state machine | cancel-then-restart leaves no photo in `processing`; terminal job status is `cancelled` not `failed`; killed worker remains retryable; Rust machine returns Kill after the grace window | `.venv/bin/pytest apps/api/tests/test_job_reliability.py`; `cargo test` or dated `[~]` |

**`测试` stage verification plan** (must match `.grok/workflows/desktop-phase1.rhai` and what `评审` requires):

1. `npm run typecheck && npm run test:web` → scratch `test-web.log` (exit 0). Covers adapters, `apiBase`, `shell`, and existing component tests.
2. Desktop typecheck/build → scratch `desktop-build.log` (non-trivial CSS; exit 0).
3. `npm run verify` → scratch `verify.log` (exit 0). Must not install or invoke rustc, cargo, or Tauri. Use fail-if-invoked wrappers on `PATH` if needed to prove this.
4. `.venv/bin/pytest apps/api/tests/test_job_reliability.py -q` → scratch `pytest-jobs.txt` (exit 0).
5. Launch the **real** sidecar entry **twice** with an absolute temp `--data-dir` and `--port 0`. Parse the ready line, `GET /health` and `GET /api/projects` both runs, SIGTERM, process exits. Captures: `sidecar-run-1.txt`, `sidecar-run-2.txt`. Do not invent a health/projects body if launch fails.
6. If `npm run test:desktop:smoke` exists, run it **twice** → `desktop-smoke-1.txt`, `desktop-smoke-2.txt`.
7. If cargo/rustc work, `cargo test` in `apps/desktop/src-tauri` **twice** → `cargo-test-1.txt`, `cargo-test-2.txt`. Else capture `cargo --version` / `rustc --version` exact error to scratch `tauri-toolchain.txt`.

Keep existing `apps/api/tests/test_ranking_export.py` and path-import immutability coverage green whenever import/export/job code changes.

---

## 7. Acceptance boxes

Copied from the implementation plan Phase 1 acceptance, plus this host’s GUI split.

**Phase 1 acceptance (must all hold at `上线`, as `[x]` or `[~]` per locked decision 13):**

- [ ] Home UI or HTTP smoke lists projects
- [ ] Sidecar health OK
- [ ] `npm run verify` green without Tauri
- [ ] Browser `npm run dev` still works on `:3000` / `:8000`

**No-Rust / no-WebView host (this machine, 2026-08-19):**

- Navigation adapter, runtime API base, shell flag, Vite SPA, and desktop router are implemented and typecheck/`test:web`/desktop-build green.
- HTTP sidecar smoke (`/health` + `/api/projects`) is `[x]`.
- Job cancel-then-restart pytest is `[x]`.
- `npm run verify` stays rust-free.
- D1.04 / D1.05 / D1.06 compile and WebView halves may stay `[~]` with a dated `cargo`/`rustc` error. Land the Rust **source** and unit tests anyway.
- Missing rustc is **not** an excuse to skip TS adapters, Vite, HTTP smoke, or job tests.

**GUI host (macOS/Windows with rustc + WebView, or later CI):**

- `npm run dev:desktop` opens a window that lists projects (empty OK) against the injected API base.
- Single-instance and remembered window bounds can be recorded then.

**`2.1.0-desktop` product DoD is out of Phase 1.** Phase 1 only proves the dual-shell + sidecar lifecycle.

---

## 8. Environment notes

- **OBJECTIVE branch is `feature/desktop-packaging`.** HEAD at branch time equals `origin/main` (`1d6ffa7`) except commits from this pipeline. Do not checkout other branches. Do not open a PR. Do not merge to `main`. `isolation_worktree` is false; edit the shared workspace.
- **This host is macOS.** The 2026-08-18 plan text still describes the author’s Linux WSL2 machine; do not copy that as fact for this run.
- **No rustc / cargo / rustup on this host as of 2026-08-19T08:26:40Z.** Recorded in `docs/desktop_feasibility_notes.md`:

  ```text
  $ cargo --version
  zsh:1: command not found: cargo

  $ rustc --version
  zsh:1: command not found: rustc

  $ command -v rustup || echo rustup not found
  rustup not found
  ```

  Both `cargo` and `rustc` exited **127**. This is inherited D0.07 `[~]`, **not** a Phase 1 start blocker.
- **`开发` may try a user-space rustup install** (`curl https://sh.rustup.rs`) if rustc is still missing. **Never** brew / apt / system packages. **Never** install a display server or WebView. If rustup/cargo still fail, capture exact command + error + exit to scratch `tauri-toolchain.txt` and keep compile/WebView ids `[~]`.
- **This `需求拆解` stage must not install rustup or implement production code.**
- **`npm run verify` must stay Rust-free.** Do not add `cargo test` or `tauri build` to `verify`. Adding `typecheck:desktop` (TypeScript only) is required in D1.03a.
- Python 3.11+ and Node 22 are the CI versions. Local `.venv` already exists from Phase 0. Do not set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`. Do not set `HOME` or package-manager homes to the scratch directory.
- Scratch for this pipeline: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-c2f1e0e66478/implementer`. Never use `/tmp` for handoff captures. If `git push` fails, write the exact git error to that directory’s `git-push.txt` and still finish the docs.
- Sidecar live launches in tests must use an **absolute** temp `--data-dir`. `--port 0` is allowed in smoke/tests only.
- Vite dev server is **1420** with `strictPort: true`. Desktop origins are already allowlisted when `FRAMEPILOT_DESKTOP=1` (`http://localhost:1420`, `http://127.0.0.1:1420`, `http://tauri.localhost`, `https://tauri.localhost`, `tauri://localhost`). Host must remain loopback or `tauri.localhost`.
- Locked CSP from Phase 0 already includes `img-src` / `connect-src` for `http://127.0.0.1:*` because `assetUrl` returns absolute loopback URLs. Do not drop those sources.
- `create_app()` still builds at import; sidecar already sets `FRAMEPILOT_DATA_DIR` before importing `app.main`. Do not regress that.
- English only for code, comments, tests, docs, and commit messages.
- Suggested per-task commit subjects stay those in the implementation plan (`web:`, `desktop:`, `test:`, `docs:`). Final stage commits are named in `.grok/workflows/desktop-phase1.rhai`.
- Do not add `Co-authored-by Cursor` or similar trailers.

---

## 9. Risks

| Risk | Why it bites | Mitigation |
|------|--------------|------------|
| Navigation adapter pulled into Next by a Vite barrel | Review A2.6: a barrel that re-exports `next/link` loads Next into the desktop build | `navigation.ts` re-exports `./navigation.next` only; Vite aliases that module to `navigation.router.tsx` |
| Adapter tests not collected | `node --test` has no JSX; vitest only includes `*.test.tsx` | Name the file `navigation.test.tsx` |
| Forgotten component imports | Six components plus two hooks still import Next directly (live grep 2026-08-19) | Guard test reads `apps/web/src/components/*` source and forbids `next/link` / `next/navigation`; move the three existing mocks |
| Frozen `API_BASE` | Module-level constant cannot see a port injected after load (`api.ts:1`, `request` at line 218) | `resolveApiBase()` at call time inside `request` / `assetUrl` / `exportDownloadUrl` |
| `isDesktopShell()` too loose | `"1"` / `0` would mis-detect and later hide Playwright file inputs | Literal `=== true` only |
| Vite missing `@` / Tailwind / PostCSS | Review A2.7; first desktop build would fail | D1.03a aliases, Tailwind v3, shared tokens, import `globals.css` |
| Duplicated hex tokens | Drift between web and desktop themes | Extract one shared token module |
| Shared CSS fork | Two design systems | `@import` `apps/web/src/app/globals.css` only |
| `--port 0` in the shipped Tauri path | Review A2.1; ready line cannot report 0 | Rust binds, drops listener, passes `--port <n>`; fail if ready-line port differs |
| Data dir CWD after freeze | Packaged CWD is unusable | Required absolute `--data-dir`; OS app-support; never `.framepilot-data` in packaged runs |
| `FRAMEPILOT_DESKTOP` unset | Tauri Origin `:1420` / `tauri://localhost` → 403 (looks like a dead API) | Spawn sets env; D1.08 must surface CORS/Host errors |
| Globals injected too late | Frontend reads base at first fetch | Inject `__FRAMEPILOT_API_BASE__` and `__FRAMEPILOT_DESKTOP__` before load |
| `verify` accidentally requires Tauri | Root scripts start calling `cargo` / `tauri dev` | `typecheck:desktop` is TS only; `dev:desktop` is not in `verify` |
| rustc missing | Cannot `cargo test` or open WebView | Inherited D0.07 `[~]`; land source + HTTP/TS tests; optional user-space rustup only; never brew/apt |
| Phase 0 `terminate` uses `kill` | Abrupt shutdown looks like data loss during a job | D1.04 SIGTERM + 5s; D1.09 confirm + cancel route |
| Quit during `BackgroundTasks` | Jobs are in-process; kill leaves photos in `processing` | D1.09 cancel-then-restart pytest; startup sweep already exists; UI uses `importLoadRecoveryMessage` |
| Broad allowlist temptation | Native picker still cannot produce a legal `root_path` | Leave D2.00 out; never set allowlist to `$HOME` |
| Mixing v2 algorithm Goal Mode | `implement_goals.md` Phase 1 is a different track | Do not touch scoring/grouping/HEIC unless a tiny shared-code fix is required by a D1 test |
| Replacing the Next app | Dynamic `projects/[projectId]` routes have no `generateStaticParams` (D0.06) | Keep Next; Vite SPA is the desktop shell |
| Ticking tracker too early | §5.1 is the only status source | This docs stage does not tick boxes; `上线` ticks `[x]` / `[~]` after measured evidence |
| Treating D0.07 `[~]` as a Phase 1 start blocker | Would freeze adapters/Vite that do not need rustc | Start D1.01 now; keep compile/WebView `[~]` until a dated cargo run |

---

## 10. Definition of done for this breakdown

- This file decomposes desktop Phase 1 ids **D1.01–D1.09** only (not `implement_goals.md` Phase 1, not desktop Phases 2–5).
- Locked decisions, files, tests-first list, acceptance boxes, environment notes (including no rustc/cargo/rustup as of 2026-08-19T08:26:40Z), and risks are explicit enough for an adversarial `评审`.
- No production code, tests, or build scripts were changed in the `需求拆解` commit except documentation (and `.grok/workflows/desktop-phase1.rhai` if it was untracked).
- Next stage: `评审` writes `docs/handoff/phase1-review.md`.
