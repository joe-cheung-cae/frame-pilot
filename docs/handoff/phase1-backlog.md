# Desktop Phase 1 Accepted Backlog

Handoff stage: `归档`  
Date: 2026-08-19  
Branch: `feature/desktop-packaging`  
Sources: `docs/handoff/phase1-requirements.md` (`90a2f48`), `docs/handoff/phase1-review.md` (`0ad2d77`), `docs/plans/2026-08-18-desktop-packaging.md` D1.01–D1.09 and §5.1

**Verdict folded:** accept-with-notes. This file is the accepted implementation contract for **D1.01–D1.09 only**. Do not reopen Electron vs Tauri, Next vs Vite, or `output: 'export'`.

This document does not implement production code. §5.1 Phase 1 boxes stay `[ ]` until `上线`. Do not start D2–D5. Do not bump `APP_VERSION`. Do not start `开发` from this archive commit.

---

## Process

- Implement **one id at a time**, tests first, then the smallest change that makes those tests pass.
- Suggested serial order: lowest incomplete id whose `depends-on` ids are done (table below).
- `开发` may make extra per-task commits using the `commit-hint` subjects. It **must** still finish with a `开发` stage commit **and push** (`git push -u origin HEAD`).
- `测试` drives the verification plan in §Required test list. Do not invent health/projects bodies if a live sidecar launch fails.
- `上线` owns final §5.1 tracker ticks (`[x]` / `[~]`). Do not tick §5.1 in `归档` or `开发`.
- Stay on `feature/desktop-packaging`. Do not open a PR. Do not merge to `main`. Do not checkout other branches.
- Local-first. Never modify original photos. English for code, comments, tests, docs, and commits.
- `npm run verify` stays free of rustc/cargo/Tauri/Playwright.
- rustc stays `[~]` unless user-space rustup works (**N4**). Never brew/apt/system packages. Missing rustc is not an excuse to skip TypeScript adapters, Vite, HTTP smoke, or job tests.
- Do not reopen locked fences (**N5**).

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

Allowed D1.01 split (finish all three before D1.03a): (a) adapter + tests, (b) Shell/list/dashboard/processing, (c) import/creator/culling + mocks.

---

## Folded review notes

| Id | Finding | Folded into |
|----|---------|-------------|
| H1 | `/help` is App Router markup, not a reusable component | D1.03b — extract shared `HelpShortcuts`; Next help page and desktop `/help` both wrap it in `Shell` |
| H2 | “No photo in processing” clashes with shipped cooperative cancel | D1.09 — split cancel vs kill vs processing-job; keep existing cancel+retry test |
| I1 | Vite alias keyed as `"./navigation.next"` often does not match | D1.03a — alias the **resolved path** of `navigation.next.tsx` |
| I2 | Two Reacts / `.ts` suffix imports break desktop | D1.03a — `resolve.dedupe` react/react-dom; `allowImportingTsExtensions` |
| I3 | Unguarded `document` throws during `next build` | D1.02a — `applyShellDataset()` SSR-safe |
| I4 | Phase 0 `frontendDist: ".."` would ship the wrong tree | D1.03a (keep in D1.07) — `frontendDist` `../dist`, `devUrl` `http://localhost:1420` |
| I5 | `split_whitespace` truncates macOS `Application Support` | D1.04 — keep `data_dir` remainder; reject port `0` / mismatch |
| N1 | Hex tokens must not be copied | D1.03a — one shared tokens module |
| N2 | Safer rust-free verify gate | D1.03a / D1.07 — `typecheck:desktop` **must** be in `verify`; `lint:desktop` only if rust-free |
| N3 | Do not mock the unit under test | D1.01 / D1.02 / D1.02a tests-first |
| N4 | No brew/apt Rust | D1.04 / D1.05 / D1.06 — user-space rustup only; land source + tests anyway |
| N5 | Do not reopen locked fences | Locked decisions below |

---

## Locked decisions (do not re-litigate)

1. **Shell:** Tauri 2 + Python sidecar. Electron stays off the table. Missing rustc is compile-blocked, not the Electron trigger.
2. **Frontend:** Dual shell, single component library. `apps/web` stays Next.js (no migrate, no `output: 'export'`). `apps/desktop` is Vite SPA. Shared: `apps/web/src/components/*`, `lib/*`, `store/*`.
3. **Navigation swap:** `navigation.ts` re-exports `./navigation.next` only. Vite aliases the **resolved file** `apps/web/src/lib/navigation.next.tsx` to `apps/desktop/src/navigation.router.tsx`. A barrel that re-exports `next/link` must never be loaded by Vite.
4. **IPC:** HTTP to the sidecar. No scoring/grouping rewrite onto Rust. Native dialogs/paths/reveal are Phase 2.
5. **Bind:** Sidecar listens on `127.0.0.1` only. Never `0.0.0.0`.
6. **Port:** Rust allocates a free loopback TCP port (`TcpListener::bind("127.0.0.1:0")`, read addr, **drop the listener**, pass `--port <n>`). The shipped path **never** passes `--port 0`. `--port 0` remains valid for tests and standalone smoke. Ready-line port must match the allocated port or fail fast; reject reported port `0`.
7. **Data dir:** Tauri always passes absolute `--data-dir` / `FRAMEPILOT_DATA_DIR`:
   - macOS: `~/Library/Application Support/FramePilot`
   - Windows: `%APPDATA%\FramePilot`
   - Linux (dev only): `~/.local/share/FramePilot`
   Packaged runs never use repo `.framepilot-data`. Dev may use `.framepilot-desktop-dev` (already gitignored). Sidecar `--data-dir` stays required.
8. **Desktop env:** spawn sets `FRAMEPILOT_DESKTOP=1`.
9. **Window injection (before frontend load):**
   - `window.__FRAMEPILOT_API_BASE__` = `http://127.0.0.1:<allocated>` (no trailing slash)
   - `window.__FRAMEPILOT_DESKTOP__ === true` (literal boolean, not `"1"`)
10. **Shell detection:** shared code reads the flag only through `isDesktopShell()` (`=== true` only).
11. **Safety:** Copy-mode unchanged. Originals are never modified or deleted.
12. **Web app must keep working.** `npm run verify` must **not** install or require rustc, cargo, or Tauri. Playwright file inputs in `ImportPanel.tsx` stay.
13. **Project roots:** `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` must **never** be set to `$HOME`, `/`, a drive root, or any broad parent. Custom roots are D2.00.
14. **GUI/toolchain blocked work** is `[~]` with a dated command + error. `[~]` is never `[x]` without a recorded GUI/toolchain run. Split D1.08: HTTP smoke can be `[x]` while WebView stays `[~]`.
15. **Single version source:** `APP_VERSION` stays `2.0.0-rc2`. Do not bump `pyproject.toml` or either `package.json` in Phase 1.
16. **Vite / Tailwind:** alias `"@"` → `../web/src`. `server.fs.allow` includes `../web`. Port **1420**, `strictPort: true`. One shared token module. Desktop CSS is `@import` of `globals.css` only.
17. **CSP:** keep Phase 0 loopback `img-src` / `connect-src`. Do not drop those sources.
18. **No cloud, login, payment, bundled models, HEIC/RAW/XMP.**
19. **Tracker:** `docs/plans/2026-08-18-desktop-packaging.md` §5.1 remains the status source of truth. Final Phase 1 ticks belong to `上线`.
20. **This pipeline’s branch:** land on `feature/desktop-packaging`. Push after each finished stage.

---

## D1.01 — Navigation adapter

**depends-on:** Phase 0 exit (already GO)

**files:**
- create: `apps/web/src/lib/navigation.ts` — types + re-export point only (`Link`, `useNavigator`, `useQueryParams` from `./navigation.next`)
- create: `apps/web/src/lib/navigation.next.tsx` — `Link` wraps `next/link`; `useNavigator().push` uses `next/navigation` `useRouter`; `useQueryParams(): URLSearchParams` wraps `useSearchParams`
- modify:
  - `apps/web/src/components/Shell.tsx`
  - `apps/web/src/components/ProjectList.tsx`
  - `apps/web/src/components/ProjectDashboard.tsx`
  - `apps/web/src/components/ProcessingPanel.tsx`
  - `apps/web/src/components/ImportPanel.tsx`
  - `apps/web/src/components/ProjectCreator.tsx`
  - `apps/web/src/components/CullingWorkspace.tsx`
- modify mocks: `CullingWorkspace.test.tsx`, `ProcessingPanel.test.tsx`, `ImportExportPanels.test.tsx` — re-point to `@/lib/navigation`
- test: `apps/web/src/lib/navigation.test.tsx` (vitest; **not** `.test.ts`)

**implement:**
- Shared components import `@/lib/navigation` only. No `next/link` or `next/navigation` under `apps/web/src/components/`.
- `CullingWorkspace` consumes only `useQueryParams()` (must not call `useSearchParams` directly).
- Do **not** re-export `next/link` from a barrel Vite will load.
- App Router pages under `apps/web/src/app/**` may stay as they are.
- Allowed split (a)/(b)/(c); finish all three before D1.03a.

**tests-first:** write `apps/web/src/lib/navigation.test.tsx` first. Drive the shipped adapter (**N3**). Do not mock `Link` / `useNavigator` inside that unit file. Component tests may mock `@/lib/navigation`.
- Drive shipped `@/lib/navigation` (web build uses `navigation.next.tsx`).
- `Link` renders `<a href>`.
- `useNavigator().push` is called with the expected href.
- `useQueryParams()` reads a query value.
- Guard: `apps/web/src/components/*` source must not import `next/link` or `next/navigation`.
- Existing component tests pass after mocks move to `@/lib/navigation`.

Run: `npm run typecheck && npm run test:web`.

**commit-hint:** `web: isolate Next navigation behind an adapter`

**done-when:**
- Shared components import `@/lib/navigation` only.
- `navigation.test.tsx` is collected by vitest and green.
- Existing component tests still pass.
- Next web app still typechecks.

---

## D1.02 — Runtime API base

**depends-on:** D1.01

**files:**
- create: `apps/web/src/lib/apiBase.ts` (`resolveApiBase()`)
- create: `apps/web/src/types/globals.d.ts` (`Window.__FRAMEPILOT_API_BASE__`, `Window.__FRAMEPILOT_DESKTOP__`)
- modify: `apps/web/src/lib/api.ts` — keep exporting `API_BASE`, but `request`, `exportDownloadUrl`, and `assetUrl` must call `resolveApiBase()` **at call time**
- test: `apps/web/src/lib/apiBase.test.ts` (`node --test`) and update `apps/web/src/lib/api.test.ts`

**implement:**
- Order: `window.__FRAMEPILOT_API_BASE__`, then `NEXT_PUBLIC_API_BASE_URL`, then `http://127.0.0.1:8000`.
- Trim trailing slash.
- Missing `window` must not throw (`next build`).
- Do not hardcode unexpected hosts. The only baked default is `http://127.0.0.1:8000`.
- Keep exporting `API_BASE` for default assertions if useful, but `request` / `exportDownloadUrl` / `assetUrl` must not read the frozen constant.
- `ExportPanel.tsx` already calls `exportDownloadUrl`; it must pick up an injected host without further UI work.

**tests-first:** write `apps/web/src/lib/apiBase.test.ts` and update `api.test.ts` first. Drive the shipped helper (**N3**). Do not mock `resolveApiBase` when testing it.
- `resolveApiBase()` order: window, then env, then `http://127.0.0.1:8000`.
- Trailing slash trimmed.
- Missing `window` does not throw.
- Injected base is used by `assetUrl` and `exportDownloadUrl` at **call time**.
- Existing encoding assertions (`api.test.ts:79–93`) still hold against whatever `resolveApiBase()` returns at call time (default or injected).

Run: `npm run typecheck && npm run test:web`.

**commit-hint:** `web: resolve API base at runtime for desktop`

**done-when:**
- Call-time resolution is in `request` / `exportDownloadUrl` / `assetUrl`.
- Default encoding tests still pass.
- Injected base is used at call time.
- No throw without `window`.

---

## D1.02a — Desktop shell flag

**depends-on:** D1.02

**files:**
- create: `apps/web/src/lib/shell.ts`
- modify: `apps/web/src/components/Providers.tsx` — call `applyShellDataset()` so the browser shell is `"browser"`
- test: `apps/web/src/lib/shell.test.ts` (`.test.tsx` only if DOM is required)

**implement:**
- `isDesktopShell()` is true only for `window.__FRAMEPILOT_DESKTOP__ === true`. False for `undefined`, `"1"`, `0`, or missing `window`. Must not throw without `window`.
- **I3:** `applyShellDataset()` must be SSR-safe. No-op (or `useEffect`) when `document` is missing. Do **not** throw during `next build` / `npm run test:web`.
- When a document exists, set `document.documentElement.dataset.shell` to `"desktop"` or `"browser"`.
- Desktop entry also calls it after injection (D1.03b).
- D3.02/D3.04 later consume the helper / `[data-shell="desktop"]`; never inline `window` checks in shared UI now.

**tests-first:** write `apps/web/src/lib/shell.test.ts` first. Drive the shipped helper (**N3**).
- `isDesktopShell()` is true only for literal `true`.
- False for `undefined`, `"1"`, `0`, missing `window`.
- `applyShellDataset()` is safe without `document` and sets `document.documentElement.dataset.shell` when a document exists.

Run: `npm run typecheck && npm run test:web`.

**commit-hint:** `web: add desktop shell detection helper`

**done-when:**
- Literal-`true` detection only.
- `applyShellDataset()` does not throw without `document`.
- `Providers.tsx` applies the browser dataset without breaking SSR/`next build`.

---

## D1.03a — Vite build, aliases, Tailwind

**depends-on:** D1.01, D1.02

**files:**
- create: `apps/desktop/vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`, `src/main.tsx`, `src/styles.css`
- create: `apps/desktop/src/navigation.router.tsx` stub until D1.03b
- create: shared Tailwind token module imported by both configs — suggested `apps/web/src/theme/tokens.ts` (or `apps/web/tailwind.tokens.ts`). **N1:** do not duplicate hex (`ink #151515`, `mist #f5f7f8`, `line #d8dedc`, `leaf #2f6f5e`, `coral #bf5b45`, `gold #a77721`).
- modify: `apps/web/tailwind.config.ts` — import the shared tokens
- modify: `apps/desktop/package.json` (replace the Phase 0 echo-only skeleton). Dependencies mirroring web: `react`, `react-dom`, `@tanstack/react-query`, `@tanstack/react-virtual`, `zustand`, `lucide-react`, plus `react-router-dom`. Dev: `vite`, `@vitejs/plugin-react`, `typescript`, `tailwindcss` ^3.4, `postcss`, `autoprefixer`, `@tauri-apps/cli`
- modify: root `package.json` — `install:all` also `npm --prefix apps/desktop install`; add `typecheck:desktop` and (optionally) `lint:desktop`
- modify: `apps/desktop/src-tauri/tauri.conf.json` (**I4**)
- keep: existing `apps/desktop/src-tauri/` tree and D0.07a icons

**implement:**
- Vite: alias `"@"` → `../web/src`.
- **I1:** alias the **resolved path** of `apps/web/src/lib/navigation.next.tsx` (regex or `find`/`replacement`) to `apps/desktop/src/navigation.router.tsx`. Do **not** key the alias as the string `"./navigation.next"`. Do not re-export `next/link` from any module Vite loads.
- **I2:** `resolve.dedupe: ["react", "react-dom"]` and/or alias both to `apps/desktop/node_modules/react` and `react-dom`. Desktop `tsconfig` must set `allowImportingTsExtensions` (or otherwise resolve `./api.ts` imports used by `processingProgress.ts` / `reviewFilters.ts`) so `typecheck:desktop` matches the web lib.
- `server.fs.allow` includes `../web`. Port **1420**, `strictPort: true`.
- `src/styles.css`: `@import "../../web/src/app/globals.css";` — no CSS fork.
- **N2:** `typecheck:desktop` **must** be in `verify`. `lint:desktop` may exist; add it to `verify` only if it is TypeScript/ESLint and never invokes rustc/cargo/Tauri. `dev:desktop` stays out of `verify`.
- **I4:** `frontendDist` → Vite `../dist`; `devUrl` → `http://localhost:1420`; `beforeDevCommand` / `beforeBuildCommand` only when those npm scripts exist. Do not drop the locked CSP `img-src` / `connect-src` loopback sources. D1.06 still owns min size, window state, and single-instance.

**tests-first:** no unit file required. Prove the build:
- `npm --prefix apps/desktop run build` emits non-trivial CSS (shared tokens + imported `globals.css`, not a fork).
- `npm run typecheck:desktop` exit 0 (including `.ts` suffix imports and the navigation alias).
- `npm run test:web` still green (Next app unchanged aside from adapters).
- `npm run verify` still does not require rustc, cargo, or Tauri.

**commit-hint:** `desktop: add Vite build with shared aliases and Tailwind`

**done-when:**
- Desktop Vite build emits non-trivial CSS from shared tokens + `globals.css`.
- `typecheck:desktop` is in `verify` and is TypeScript-only.
- Resolved navigation alias + React dedupe + `.ts` extensions work.
- `tauri.conf.json` points at `../dist` and `http://localhost:1420`.
- Locked CSP loopback sources remain.

---

## D1.03b — Desktop router

**depends-on:** D1.03a, D1.02a

**files:**
- create: `apps/desktop/src/router.tsx`, full `navigation.router.tsx` (D1.01 contract: `href` → `to`, drop `prefetch`), `App.tsx`
- create: `apps/web/src/components/HelpShortcuts.tsx` (name may vary) — **H1**
- modify: `apps/web/src/app/help/page.tsx` — wrap `HelpShortcuts` in `Shell` (keep Next metadata on the page, not in the shared component)
- modify: `apps/desktop/src/main.tsx`
- replace: Phase 0 `index.html` / `health.js` placeholder with the Vite entry

**implement:**
- React Router implements the D1.01 contract.
- Routes must match `apps/web/src/app` exactly (verified 2026-08-19):

| Path | Shared UI |
|------|-----------|
| `/` | `ProjectList` inside `Shell` (no `app/page.tsx` marketing column) |
| `/help` | shared `HelpShortcuts` inside `Shell` |
| `/settings` | `SettingsPanel` inside `Shell` |
| `/projects/new` | `ProjectCreator` inside `Shell` |
| `/projects/:projectId` | `ProjectDashboard` |
| `/projects/:projectId/import` | `ImportPanel` |
| `/projects/:projectId/process` | `ProcessingPanel` |
| `/projects/:projectId/cull` | `CullingWorkspace` |
| `/projects/:projectId/export` | `ExportPanel` |
| `*` | home |

- **H1:** extract a shared `HelpShortcuts` into `apps/web/src/components/` that renders `REVIEW_SHORTCUT_HELP_SECTIONS`. Both `apps/web/src/app/help/page.tsx` and the desktop `/help` route wrap that component in `Shell`. Do not duplicate the shortcut table. Do not import `next` metadata from the desktop router. Do not import Next `page.tsx` files into Vite.
- Same providers as `Providers.tsx`. Call `applyShellDataset()`. Leave `"use client"` directives in shared files.
- Do not migrate App Router pages.

**tests-first:** typecheck + desktop build.
- Router typechecks.
- Desktop build still green.
- `npm run test:web` unaffected (Next help page still wraps the shared component).

Run: `npm run typecheck:desktop`, desktop build, `npm run test:web`.

**commit-hint:** `desktop: add router reusing web page components`

**done-when:**
- Desktop routes match the table.
- Help shortcuts live in one shared component used by both shells.
- Vite does not import Next `page.tsx` or Next metadata.
- `applyShellDataset()` is called from the desktop entry.

---

## D1.04 — Sidecar lifecycle in Rust

**depends-on:** D0.07 (source exists; `[~]` compile is OK), D1.03b

**files:**
- create: `apps/desktop/src-tauri/src/sidecar.rs`
- modify: `apps/desktop/src-tauri/src/lib.rs` (and `Cargo.toml` only if tests/new crates require it)
- tests: Rust unit tests for `allocate_loopback_port()` and `parse_ready_line()`

**implement:**
- Allocate port in Rust; drop the listener; pass `--port <n>`. Never `--port 0` in the shipped path. `--port 0` remains test-only (D1.08 / 测试 dual sidecar).
- Always pass absolute `--data-dir`. Env `FRAMEPILOT_DESKTOP=1`.
- Inject both globals **before** the WebView loads the UI (`initialization_script` or equivalent):
  - `window.__FRAMEPILOT_API_BASE__ = "http://127.0.0.1:<n>"` (no trailing slash)
  - `window.__FRAMEPILOT_DESKTOP__ = true` (literal boolean)
- **I5:** `parse_ready_line()` accepts the exact Phase 0 string `FRAMEPILOT_API ready host=127.0.0.1 port=<n> data_dir=<path>`, extracts `host`, `port`, and **the remainder after `data_dir=`** (spaces allowed — macOS `Application Support`). Reject a port that is `0` or that differs from the allocated port.
- Crash policy: one automatic restart; if health fails twice, blocking error page.
- Shutdown: SIGTERM, wait 5s, then kill. Windows: job object or `GenerateConsoleCtrlEvent` — document which in feasibility notes if reached.
- Log sidecar stderr to `{data_dir}/logs/sidecar.log`.
- Phase 0 `lib.rs` already has a port helper and a ready-line prefix check, but `run()` does not spawn and `terminate` kills immediately. Replace that with the lifecycle above.
- **N4:** `开发` may try `curl https://sh.rustup.rs` into user space. Never brew/apt. If `cargo test` still cannot run, land the Rust **source** and unit tests anyway, keep compile/WebView `[~]`, and capture exact `cargo --version` / `rustc --version` (command + error + exit) to scratch `tauri-toolchain.txt`. Do not add `cargo test` or `tauri` to `npm run verify`.

**tests-first:** write Rust unit tests in `apps/desktop/src-tauri` first (land even if cargo cannot run).
- `allocate_loopback_port()` returns a non-zero port on `127.0.0.1`; listener is dropped.
- `parse_ready_line()` accepts `FRAMEPILOT_API ready host=127.0.0.1 port=<n> data_dir=<path>` including a `data_dir` with spaces; rejects port `0` and a mismatched allocated port.

Run: `cargo test` in `apps/desktop/src-tauri` **twice**, or dated rustc/cargo capture. `npm run verify` still rust-free.

**commit-hint:** `desktop: manage sidecar lifecycle and API base injection`

**done-when:**
- Source implements allocate/drop/`--port <n>`, absolute `--data-dir`, `FRAMEPILOT_DESKTOP=1`, ready-line parse with spaced `data_dir`, reject port 0/mismatch, inject both globals before load, SIGTERM then kill after 5s.
- Unit tests exist even if cargo cannot run.
- D1.04 is `[x]` only if `cargo test` ran; else `[~]` with a dated toolchain note (`上线` ticks).

---

## D1.05 — App-support data directory

**depends-on:** D1.04

**files:**
- Rust path helper only (do not duplicate the policy in TypeScript)
- tests: table-driven Rust tests for macOS / Windows / Linux prefixes

**implement:**
- Default dirs as locked decision 7. Create on first launch.
- Packaged path is not CWD `.framepilot-data`.
- Dev may use `.framepilot-desktop-dev` (already gitignored).
- **N4:** land tests even if cargo cannot run.

**tests-first:** table-driven Rust tests.
- macOS `Library/Application Support/FramePilot`
- Windows `AppData\\Roaming\\FramePilot` / `%APPDATA%\\FramePilot`
- Linux `.local/share/FramePilot`
- Packaged path is not CWD `.framepilot-data`

Run: `cargo test` or dated `[~]`.

**commit-hint:** `desktop: use OS app-support data directory`

**done-when:**
- Packaged data dir is OS app-support, never CWD `.framepilot-data`.
- Table-driven tests exist (green or dated `[~]`).

---

## D1.06 — Window basics and single instance

**depends-on:** D1.04

**files:**
- modify: `apps/desktop/src-tauri/tauri.conf.json` and Rust setup
- expect `tauri-plugin-window-state` and `tauri-plugin-single-instance` in `Cargo.toml` if cargo can be compiled

**implement:**
- Title `FramePilot` (already set).
- Min size ~1100×720 (current window is 1200×800 with no min).
- Remember position/size.
- Single instance focuses the first window.
- Close window stops the sidecar.
- Keep **I4** values: `frontendDist` `../dist`, `devUrl` `http://localhost:1420`. Do not drop locked CSP loopback sources.
- **N4:** `cargo check` if rustc exists; otherwise record `[~]`.

**tests-first:** none (shell). Run `cargo check` if rustc exists; otherwise dated note. D1.06 is shell-only (`cargo check` or `[~]`).

**commit-hint:** `desktop: add window state and single-instance lock`

**done-when:**
- Min size, window state, and single-instance are in source (or dated `[~]` if cargo cannot compile plugins).
- `tauri.conf.json` still points at Vite `../dist` / `http://localhost:1420`.
- Close stops the sidecar.

---

## D1.07 — Dev scripts and verify wiring

**depends-on:** D1.03a, D1.04

**files:**
- modify: root `package.json`, `apps/desktop/package.json`, `apps/desktop/README.md`
- keep: `apps/desktop/src-tauri/tauri.conf.json` **I4** values from D1.03a (`frontendDist` `../dist`, `devUrl` `http://localhost:1420`; `beforeDevCommand` / `beforeBuildCommand` only when those npm scripts exist)

**implement:**
- `npm run dev:desktop` → tauri dev + Vite + sidecar **when cargo exists**. If rustc is still missing, fail with a clear message (today’s echo is acceptable until cargo exists) but must not be invoked by `verify`.
- `build:desktop` may wait until Phase 4.
- **N2:** `verify` must **not** require Rust. `typecheck:desktop` is already in `verify` from D1.03a. `lint:desktop` is in `verify` only if rust-free. `dev:desktop` stays out of `verify`.
- `install:all` already installs desktop from D1.03a.

**tests-first:** none (scripts). Run: `npm run verify` exit 0 and does not invoke rustc/cargo/Tauri.

**commit-hint:** `desktop: add tauri dev scripts`

**done-when:**
- `dev:desktop` is wired (or still clearly fails without cargo) and is not in `verify`.
- `npm run verify` stays rust-free and includes `typecheck:desktop`.
- D1.07 is `[x]` if `verify` stays rust-free (`上线` ticks).

---

## D1.08 — Desktop smoke: health + project list

**depends-on:** D1.04, D1.05, D1.07

**files:**
- create: `tests/desktop/smoke.sh` (or Playwright against Vite `:1420`)
- modify: root `package.json` (`test:desktop:smoke`)

**implement:**
- Acceptance: UI or the Vite page can call `GET /api/projects` and render the home list (empty is OK). Failure must be visible, not a silent CORS 403.
- Non-GUI `[x]`: launch the **real** sidecar entry with absolute temp `--data-dir` and `--port 0` (test path only). Parse ready line `host=127.0.0.1` and port ≠ 0. `GET /health` JSON has `status`, `version`, `service`. `GET /api/projects` is a JSON array (empty OK). SIGTERM and process exits.
- WebView render stays `[~]` if needed — split the tracker note; do not leave the whole id `[ ]`.
- Do not invent a health/projects body if launch fails.

**tests-first:** write `tests/desktop/smoke.sh` first.
- Ready line host/port.
- `/health` has `status`/`version`/`service`.
- `/api/projects` 200 JSON array.
- SIGTERM exits.
- CORS/Host failure is visible.

Run: `npm run test:desktop:smoke` (skip **only** the WebView half with an explicit message). `测试` also launches the real sidecar **twice**.

**commit-hint:** `test: add desktop project-list smoke`

**done-when:**
- HTTP sidecar smoke exists and can be `[x]` independently of WebView.
- CORS/Host failures are visible.
- WebView half is `[x]` or dated `[~]`, not left `[ ]` as a whole id.

---

## D1.09 — Graceful quit with a running job

**depends-on:** D1.04, D1.06

**files:**
- modify: sidecar/window close handler; reuse existing `POST /api/projects/{id}/jobs/{job_id}/cancel`
- modify: `fail_active_jobs_on_startup` / import crash reset as needed for the kill path (do **not** change cooperative-cancel photo-row behavior)
- test: extend `apps/api/tests/test_job_reliability.py` on the **shipped** cancel and startup-sweep paths
- test: Rust shutdown state machine unit test (returns Kill after the 5s grace window)
- docs: `docs/v2_known_limitations.md` only if a remaining gap exists

**implement:** **H2** — split the three shipped paths. Do **not** weaken `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`. Do not invent a second cancel implementation inside the pytest. Do not add a fake processing cancel route.

On close, if an import/process job is active: confirm — Cancel quit / Quit and cancel job / Quit anyway.

1. **Quit and cancel (import only).** Reuse POST cancel. Wait up to 10s. Then SIGTERM. Terminal job status is `cancelled`, not `failed`. In-flight photo **may** stay `processing` until retry (existing test). **After retry, no photo remains `processing`.** Originals unchanged.
2. **Quit anyway / SIGTERM then kill.** Do not POST cancel. Next launch runs `fail_active_jobs_on_startup`. Job is `failed` + `retryable` with `current_step == "failed - restart"`. Extend the **startup sweep** (or call existing `_reset_import_photos_after_crash`) so import photos stuck in `processing` without derivatives are reset. That is the “killed worker remains retryable / no photo left in processing” assertion. Do not pretend this path is `cancelled`.
3. **Active processing job.** There is no cancel route (`POST /jobs/{id}/cancel` 422s `"Only import jobs can be cancelled"`). Confirm dialog still applies. “Quit and cancel job” is not available (or is disabled / mapped to quit-anyway). SIGTERM + startup sweep already calls `reset_project_after_processing_failure`.

UI after next launch: show the existing **failed-job** recovery copy (`importTerminalStatusMessage` / `processingRecoveryMessage` plus `job.error_message`), not a bare status label `"Failed"`. `importLoadRecoveryMessage` is the API-down helper; use it only when the sidecar is actually unreachable.

**tests-first:** extend `apps/api/tests/test_job_reliability.py` first. Keep `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state` green. Drive shipped cancel + startup-sweep paths (**N3**).
- Cooperative cancel then retry: job terminal `cancelled` not `failed`; after retry, no photo remains `processing`; originals unchanged. Do not change the existing assertion that the unfinished photo stays `processing` at the cancel checkpoint.
- Killed / interrupted import then `fail_active_jobs_on_startup`: job `failed` + retryable; no photo left stuck in `processing`; retry still works.
- Processing-job interrupt still uses the existing reset helper; do not add a fake processing cancel route.
- Rust quit state machine returns Kill after the 5s grace window.

Run: `.venv/bin/pytest apps/api/tests/test_job_reliability.py`; `cargo test` or dated `[~]`. Keep `apps/api/tests/test_ranking_export.py` and path-import immutability coverage green whenever import/export/job code changes.

**commit-hint:** `desktop: cancel or drain jobs before quitting`

**done-when:**
- Close dialog distinguishes cancel (import only) vs quit-anyway vs processing-job (no cancel route).
- Existing cancel+retry test stays green unchanged in meaning.
- After retry of a cancelled import, no photo remains `processing`.
- Killed worker is `failed` + retryable via startup sweep; stuck import photos are reset; not labelled `cancelled`.
- No fake processing cancel route.
- Recovery UI uses failed-job copy, not a bare `"Failed"` and not `importLoadRecoveryMessage` unless the sidecar is down.
- Rust Kill-after-grace test exists (green or dated `[~]`).

---

## Required test list

This is the `测试`-stage verification plan. Copied from `docs/handoff/phase1-review.md` §3. It matches `.grok/workflows/desktop-phase1.rhai` and `docs/handoff/phase1-requirements.md` §6. `开发` writes the failing tests first. `测试` drives the shipped code (no invented health/projects bodies).

### 3.1 Navigation adapter (D1.01)

File: `apps/web/src/lib/navigation.test.tsx` (vitest; **not** `.test.ts`).

- Drive shipped `@/lib/navigation` (web build uses `navigation.next.tsx`).
- `Link` renders `<a href>`.
- `useNavigator().push` is called with the expected href.
- `useQueryParams()` reads a query value (`CullingWorkspace` must not call `useSearchParams` directly).
- Guard: `apps/web/src/components/*` source must not import `next/link` or `next/navigation`.
- Existing component tests pass after mocks move to `@/lib/navigation`.

Run: `npm run typecheck && npm run test:web`.

### 3.2 Runtime API base (D1.02)

Files: `apps/web/src/lib/apiBase.test.ts` (`node --test`) and `apps/web/src/lib/api.test.ts`.

- `resolveApiBase()` order: `window.__FRAMEPILOT_API_BASE__`, then `NEXT_PUBLIC_API_BASE_URL`, then `http://127.0.0.1:8000`.
- Trailing slash trimmed.
- Missing `window` does not throw.
- Injected base is used by `assetUrl` and `exportDownloadUrl` at **call time** (not a frozen `API_BASE`).
- Existing encoding assertions still hold on the default base.
- Do not hardcode unexpected hosts. Do not mock `resolveApiBase` when testing it.

Run: `npm run typecheck && npm run test:web`.

### 3.3 Desktop shell flag (D1.02a)

File: `apps/web/src/lib/shell.test.ts` (`.test.tsx` only if DOM is required).

- `isDesktopShell()` is true only for literal `true`.
- False for `undefined`, `"1"`, `0`, missing `window`.
- `applyShellDataset()` is safe without `document` and sets `document.documentElement.dataset.shell` when a document exists.
- Drive the shipped helper.

Run: `npm run typecheck && npm run test:web`.

### 3.4 Vite build, aliases, Tailwind, router (D1.03a / D1.03b)

- `npm --prefix apps/desktop run build` emits non-trivial CSS (shared tokens + imported `globals.css`, not a fork).
- `npm run typecheck:desktop` exit 0 (including `.ts` suffix imports and the navigation alias).
- `npm run test:web` still green (Next app unchanged aside from adapters).
- `npm run verify` still does not require rustc, cargo, or Tauri.

### 3.5 Sidecar lifecycle, data dir, window (D1.04–D1.06)

Rust unit tests in `apps/desktop/src-tauri` (land even if cargo cannot run):

- `allocate_loopback_port()` returns a non-zero port on `127.0.0.1`; listener is dropped.
- `parse_ready_line()` accepts `FRAMEPILOT_API ready host=127.0.0.1 port=<n> data_dir=<path>` including a `data_dir` with spaces; rejects port `0` and a mismatched allocated port.
- Table-driven data-dir prefixes: macOS `Library/Application Support/FramePilot`, Windows `AppData\\Roaming\\FramePilot` / `%APPDATA%\\FramePilot`, Linux `.local/share/FramePilot`. Packaged path is not CWD `.framepilot-data`.
- Quit state machine returns Kill after the 5s grace window (D1.09).

Run: `cargo test` in `apps/desktop/src-tauri` **twice**, or dated rustc/cargo capture. `npm run verify` still rust-free. D1.06 is shell-only (`cargo check` or `[~]`).

### 3.6 Job cancel / kill / retry (D1.09)

File: extend `apps/api/tests/test_job_reliability.py` on the **shipped** cancel and startup-sweep paths. Keep `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state` green.

- Cooperative cancel then retry: job terminal `cancelled` not `failed`; after retry, no photo remains `processing`; originals unchanged.
- Killed / interrupted import then `fail_active_jobs_on_startup`: job `failed` + retryable; no photo left stuck in `processing`; retry still works.
- Processing-job interrupt still uses the existing reset helper; do not add a fake processing cancel route.

Run: `.venv/bin/pytest apps/api/tests/test_job_reliability.py`.

### 3.7 Commands the 测试 stage must run

1. `npm run typecheck && npm run test:web` → scratch `test-web.log` (exit 0). Covers adapters, `apiBase`, `shell`, and existing component tests.
2. Desktop typecheck/build → scratch `desktop-build.log` (non-trivial CSS; exit 0).
3. `npm run verify` → scratch `verify.log` (exit 0). Must not install or invoke rustc, cargo, or Tauri. Use fail-if-invoked wrappers on `PATH` if needed to prove this.
4. `.venv/bin/pytest apps/api/tests/test_job_reliability.py -q` → scratch `pytest-jobs.txt` (exit 0).
5. Launch the **real** sidecar entry **twice** with an **absolute** temp `--data-dir` and `--port 0` (test path only). Parse the ready line (`host=127.0.0.1`, port ≠ 0). `GET /health` JSON has `status`, `version`, `service`. `GET /api/projects` is a JSON array (empty OK). SIGTERM; process exits. Captures: `sidecar-run-1.txt`, `sidecar-run-2.txt`. Do not invent a health/projects body if launch fails.
6. If `npm run test:desktop:smoke` exists, run it **twice** → `desktop-smoke-1.txt`, `desktop-smoke-2.txt`. CORS/Host failure must be visible, not a silent 403.
7. If cargo/rustc work, `cargo test` in `apps/desktop/src-tauri` **twice** → `cargo-test-1.txt`, `cargo-test-2.txt`. Else capture `cargo --version` / `rustc --version` exact error to scratch `tauri-toolchain.txt`.

Keep `apps/api/tests/test_ranking_export.py` and path-import immutability coverage green whenever import/export/job code changes.

---

## Acceptance boxes

Copied from the implementation plan Phase 1 acceptance, plus this host’s GUI split. Do **not** tick these in `归档`.

**Phase 1 acceptance (must all hold at `上线`, as `[x]` or `[~]` per locked decision 14):**

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

## Out of scope

- `implement_goals.md` Phase 1 (v2 web job-progress / ranking work).
- Desktop Phase 0 redo. D0.07 remains `[~]` until a dated rustc/WebView run succeeds.
- Desktop Phases 2–5 (D2.00–D5.05), including registered project roots, native pickers, menus, installers, and version bump to `2.1.0-desktop`.
- Setting `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`.
- Migrating `apps/web` off Next.js, adding `output: 'export'`, or deleting App Router pages.
- Removing the two `ImportPanel.tsx` file inputs.
- Replacing scoring/grouping with Rust.
- HEIC / RAW / XMP / bundled neural models / cloud / login / payment.
- Making `npm run verify` require Rust, Tauri, or Playwright.
- Installing a system Rust toolchain (brew/apt). User-space rustup only.
- Weakening `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`.
- Adding a fake processing-job cancel route.
- Publishing installers, opening a PR, or merging to `main`.
- Ticking §5.1 in this archive or in `开发`.
- Starting `开发` from this `归档` commit.
