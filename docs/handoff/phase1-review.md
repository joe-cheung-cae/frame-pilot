# Desktop Phase 1 Requirements Review

Handoff stage: `评审`  
Date: 2026-08-19T17:14:00+08:00  
Branch: `feature/desktop-packaging`  
Reviewed: `docs/handoff/phase1-requirements.md` (需求拆解) against the live `2.0.0-rc2` tree on `feature/desktop-packaging`  
Sources: `docs/plans/2026-08-18-desktop-packaging.md` D1.01–D1.09 and §5.1, `docs/plans/2026-08-18-desktop-packaging-review.md` (A2.6 / A2.7), `AGENTS.md`, live web/desktop/API files named in the breakdown

**Verdict: accept-with-notes**

The breakdown is a safe Phase 1 contract. It fences **D1.01–D1.09** only, keeps `apps/web` on Next.js, does not start desktop Phases 2–5, does not bump `APP_VERSION`, and already folds in the refined-plan traps: adapter tests as `*.test.tsx`, Vite alias (not a Next barrel), API base at **call time**, `isDesktopShell()` only for literal `true`, shared Tailwind tokens / no CSS fork, shipped sidecar never `--port 0`, required absolute `--data-dir`, `FRAMEPILOT_DESKTOP=1`, ready-line parse, window injection before load, `npm run verify` without Rust, and compile/WebView `[~]` while rustc is missing. It is not rejected.

归档 must fold the notes below into `docs/handoff/phase1-backlog.md` before 开发. The highest notes are not product-policy holes; they are a missing shared Help component, a D1.09 cancel-vs-kill semantics clash with the shipped import cancel test, and Vite resolve details that would make the first desktop build fail.

No production code, tests, or build scripts were changed in this stage. §5.1 Phase 1 boxes stay `[ ]`.

---

## 1. Live-tree facts (verified 2026-08-19T17:14:00+08:00)

| Claim in the breakdown | Live tree |
|------------------------|-----------|
| `API_BASE` frozen at module load; `request` / `exportDownloadUrl` / `assetUrl` bake it | Confirmed `apps/web/src/lib/api.ts:1`, `:218`, `:375–390`. No other production `API_BASE` readers |
| No `shell.ts` / `apiBase.ts` / `navigation.ts`; Providers is QueryClient only | Confirmed. `Providers.tsx` has no `document` / window checks |
| `next/link` or `next/navigation` in seven shared components | Confirmed: `Shell`, `ProjectList`, `ProjectDashboard`, `ProcessingPanel`, `ImportPanel`, `ProjectCreator` (`useRouter`), `CullingWorkspace` (`Link`, `useRouter`, `useSearchParams` at `:67–68`) |
| Vitest collects `src/**/*.test.tsx` only; `node --test` collects `src/lib/*.test.ts` | Confirmed `apps/web/package.json` + `vitest.config.ts` |
| Component mocks still target `next/link` / `next/navigation` | Confirmed `CullingWorkspace.test.tsx`, `ProcessingPanel.test.tsx`, `ImportExportPanels.test.tsx` |
| Tailwind hex tokens inline in `apps/web/tailwind.config.ts` | `ink #151515`, `mist #f5f7f8`, `line #d8dedc`, `leaf #2f6f5e`, `coral #bf5b45`, `gold #a77721` |
| `apps/web/src/app/globals.css` is `@tailwind` + local rules, no Next-only CSS | Confirmed. Safe to `@import` from desktop |
| Help UI is **not** a shared component | `apps/web/src/app/help/page.tsx` inlines `REVIEW_SHORTCUT_HELP_SECTIONS`. No `HelpPanel` |
| Home `/` wraps extra marketing chrome around `ProjectList` | `apps/web/src/app/page.tsx`. All other App Router pages wrap the named component in `Shell` |
| Web tsconfig `allowImportingTsExtensions: true`; some lib files import `./api.ts` | `processingProgress.ts`, `reviewFilters.ts` |
| Desktop tree is Phase 0 verify-safe skeleton | `index.html` + `health.js`; `package.json` echo-only `dev`; no Vite `src/`; `src-tauri/` present |
| `tauri.conf.json` | Title `FramePilot`, window 1200×800, **no min size**, `frontendDist: ".."`, no `devUrl` / `beforeDevCommand`. CSP already has loopback `img-src` / `connect-src` |
| Rust `lib.rs` | Allocates a loopback port and documents spawn with `--port <n>`, absolute `--data-dir`, `FRAMEPILOT_DESKTOP=1`. `wait_for_ready_line` is **prefix-only**. `terminate` **kills immediately**. `run()` does not spawn |
| `Cargo.toml` | tauri 2 + serde only. No window-state or single-instance plugin |
| Sidecar CLI | `--data-dir` required and absolute; ready line `FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>`; `--port 0` valid for tests |
| POST cancel is **import-only** | `routes.py:759–760` → 422 `"Only import jobs can be cancelled"` |
| `fail_active_jobs_on_startup` | Processing jobs call `reset_project_after_processing_failure`. Import jobs are marked `failed` / `failed - restart` only — **does not** call `_reset_import_photos_after_crash` |
| Existing cancel+retry test | `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state` asserts the in-flight photo stays `processing` after cancel, then retry completes it |
| `importLoadRecoveryMessage` | Used only for query/mutation **load** errors in `ImportPanel`. Failed/cancelled jobs use `importTerminalStatusMessage` + `error_message` |
| `test_job_reliability.py` | Crash, startup fail, idempotent sweep, processing boom, interrupted export. **No** cancel-then-restart / quit state machine yet |
| Root `verify` | `lint && typecheck && test && check:artifacts`. No rustc/cargo/Tauri. `install:all` does not install `apps/desktop` |
| `APP_VERSION` | `2.0.0-rc2`. `next.config.ts` has no `output: 'export'` |
| This host | macOS. rustc/cargo/rustup missing as of 2026-08-19T08:26:40Z (exit 127). Inherited D0.07 `[~]` |
| `tests/desktop/` | Missing |
| ImportPanel file inputs | Still present at ~234 and ~253 including `webkitdirectory` |

---

## 2. Findings

### H1 — `/help` is not a reusable component (high)

**Why.** D1.03b requires routes to match `apps/web/src/app` and lists `/help` as “Help shortcuts page inside Shell”. The live help page is App Router markup in `apps/web/src/app/help/page.tsx`. It is not under `src/components/`. Desktop Vite must not import Next `page.tsx` files.

**Required change for 归档/开发.** In D1.03b (or a tiny slice of D1.01 if that is cleaner), extract a shared `HelpShortcuts` (name may vary) into `apps/web/src/components/` that renders `REVIEW_SHORTCUT_HELP_SECTIONS`. Both `apps/web/src/app/help/page.tsx` and the desktop `/help` route wrap that component in `Shell`. Do not duplicate the shortcut table. Do not import `next` metadata from the desktop router.

Home `/` may keep desktop as `ProjectList` inside `Shell` without the marketing column in `app/page.tsx`. That matches the breakdown table and is enough for “list projects”. Do not migrate App Router pages.

### H2 — D1.09 “no photo in processing” vs shipped cancel semantics (high)

**Why.** The tests-first row says a cancelled-then-restarted import leaves **no** photo in `processing`, and that 开发 must reuse the existing POST cancel route without reimplementing cancel in the test.

The shipped cooperative-cancel test already asserts the opposite at the cancel checkpoint:

- `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state` (`test_import_process_export_api.py:1487–1494`): after POST cancel, the unfinished photo stays `processing_state == "processing"`; after retry the job completes.
- `docs/v2_known_limitations.md`: cancel is cooperative, keeps completed derivatives, leaves unprocessed photos retryable.
- `_cancel_import_job` does not reset photo rows.
- `fail_active_jobs_on_startup` for **import** only marks the job `failed` / `failed - restart`. It does not call `_reset_import_photos_after_crash`. A SIGKILL/quit-anyway can leave import photos stuck in `processing` after the next launch.
- POST `/jobs/{id}/cancel` 422s for processing jobs (`"Only import jobs can be cancelled"`). D1.09 still says “if an import/process job is active”.

Changing cooperative cancel so no photo remains `processing` would break the existing test and the documented checkpoint model. Treating a killed worker as `cancelled` would also be wrong: the startup sweep marks those jobs `failed`.

**Required change for 归档/开发.** Split D1.09 into the three shipped paths. Do not weaken the existing cancel+retry test.

1. **Quit and cancel (import only).** Reuse POST cancel. Wait up to 10s. Then SIGTERM. Terminal job status is `cancelled`, not `failed`. In-flight photo **may** stay `processing` until retry (existing test). After retry, no photo remains `processing`.
2. **Quit anyway / SIGTERM then kill.** Do not POST cancel. Next launch runs `fail_active_jobs_on_startup`. Job is `failed` + `retryable` with `current_step == "failed - restart"`. Extend the **startup sweep** (or call existing `_reset_import_photos_after_crash`) so import photos stuck in `processing` without derivatives are reset. That is the “killed worker remains retryable / no photo left in processing” assertion. Do not pretend this path is `cancelled`.
3. **Active processing job.** There is no cancel route. Confirm dialog still applies. “Quit and cancel job” is not available (or is disabled / mapped to quit-anyway). SIGTERM + startup sweep already calls `reset_project_after_processing_failure`.

UI after next launch: show the existing **failed-job** recovery copy (`importTerminalStatusMessage` / `processingRecoveryMessage` plus `job.error_message`), not a bare status label `"Failed"`. `importLoadRecoveryMessage` is the API-down helper; use it only when the sidecar is actually unreachable. Do not invent a second cancel implementation inside the pytest.

### I1 — Alias the resolved `navigation.next` file, not the string `./navigation.next` (important)

**Why.** Review A2.6 is already in the breakdown: a barrel that re-exports `next/link` pulls Next into Vite. `navigation.ts` re-exporting `./navigation.next` is the right shape. Vite `resolve.alias` keyed as `"./navigation.next"` often **does not** match, because the importer is `apps/web/src/lib/navigation.ts` and Vite compares the resolved absolute id.

**Required change for 归档/开发.** D1.03a alias must map the **resolved path** of `apps/web/src/lib/navigation.next.tsx` (regex or `find`/`replacement`) to `apps/desktop/src/navigation.router.tsx`. Also alias `"@"` → `../web/src`. Do not re-export `next/link` from any module Vite loads. Adapter tests stay `navigation.test.tsx` (vitest). Drive the shipped adapter; do not mock `Link` / `useNavigator` inside that unit file. Component tests re-point mocks to `@/lib/navigation`.

### I2 — Dedupe React when Vite loads `apps/web/src` (important)

**Why.** Desktop will depend on `react` / `react-dom`. Shared components import `react`. If Vite also walks `apps/web/node_modules/react`, hooks throw “Invalid hook call” with a green typecheck.

**Required change for 归档/开发.** D1.03a Vite config: `resolve.dedupe: ["react", "react-dom"]` and/or alias both to `apps/desktop/node_modules/react` and `react-dom`. Desktop `tsconfig` must set `allowImportingTsExtensions` (or otherwise resolve `./api.ts` imports used by `processingProgress.ts` / `reviewFilters.ts`) so `typecheck:desktop` matches the web lib.

### I3 — `applyShellDataset()` must be SSR-safe (important)

**Why.** D1.02a calls `applyShellDataset()` from `Providers.tsx`. That file is `"use client"` but Next still pre-renders it. `npm run test:web` runs `next build`. An unguarded `document.documentElement.dataset.shell = ...` throws when `document` is missing.

**Required change for 归档/开发.** `isDesktopShell()` already must not throw without `window`. `applyShellDataset()` must no-op (or `useEffect`) when `document` is missing. True only for `window.__FRAMEPILOT_DESKTOP__ === true`. False for `undefined`, `"1"`, `0`, missing window. Desktop entry also calls it after injection.

### I4 — `tauri.conf.json` still points at the Phase 0 HTML folder (important)

**Why.** `frontendDist` is `".."`. After D1.03b that would ship the Vite source tree / placeholder HTML, not `dist/`. There is no `devUrl` for `:1420`.

**Required change for 归档/开发.** Add `apps/desktop/src-tauri/tauri.conf.json` to D1.03a or D1.07: `frontendDist` → Vite `../dist`; `devUrl` → `http://localhost:1420`; `beforeDevCommand` / `beforeBuildCommand` only when those npm scripts exist. Do not drop the locked CSP `img-src` / `connect-src` loopback sources. D1.06 still owns min size, window state, and single-instance (expect `tauri-plugin-window-state` and `tauri-plugin-single-instance` in `Cargo.toml` if cargo can be compiled).

### I5 — Ready-line parser must keep `data_dir` intact (important)

**Why.** macOS app-support is `~/Library/Application Support/FramePilot` (spaces). Naive `split_whitespace` after `data_dir=` truncates the path. Phase 0 `wait_for_ready_line` only checks a prefix and never compares the allocated port.

**Required change for 归档/开发.** `parse_ready_line()` accepts the exact Phase 0 string, extracts `host`, `port`, and **the remainder after `data_dir=`** (spaces allowed), and rejects a port that is `0` or that differs from the allocated port. Shipped spawn still binds `127.0.0.1:0` in Rust, **drops the listener**, passes `--port <n>` (never `--port 0`), required absolute `--data-dir`, and `FRAMEPILOT_DESKTOP=1`. Inject `window.__FRAMEPILOT_API_BASE__ = "http://127.0.0.1:<n>"` (no trailing slash) and `window.__FRAMEPILOT_DESKTOP__ = true` (literal boolean) **before** the WebView loads the UI (`initialization_script` or equivalent). `--port 0` remains test-only (D1.08 / 测试 dual sidecar).

### N1 — Shared Tailwind tokens need a named module (note)

Extract one module imported by both `apps/web/tailwind.config.ts` and `apps/desktop/tailwind.config.ts`. Suggested path: `apps/web/src/theme/tokens.ts` (or `apps/web/tailwind.tokens.ts`). Do not duplicate hex. Desktop `src/styles.css` is only `@import "../../web/src/app/globals.css";`.

### N2 — `lint:desktop` vs `verify` (note)

The implementation plan D1.03a says add both `typecheck:desktop` and `lint:desktop` to `verify`. The breakdown only adds `typecheck:desktop`. That is the safer rust-free gate. 归档: `typecheck:desktop` **must** be in `verify`. `lint:desktop` may exist; add it to `verify` only if it is TypeScript/ESLint and never invokes rustc/cargo/Tauri. `dev:desktop` stays out of `verify`.

### N3 — Drive shipped adapters; do not mock the unit under test (note)

`navigation.test.tsx`, `apiBase.test.ts`, and `shell.test.ts` import the real modules. Do not mock `resolveApiBase` when testing it. Do not hardcode unexpected hosts; the only baked default is `http://127.0.0.1:8000`. Existing `assetUrl` encoding assertions (`api.test.ts:79–93`) must still hold against whatever `resolveApiBase()` returns at call time (default or injected). Keep exporting `API_BASE` for those default assertions if useful, but `request` / `exportDownloadUrl` / `assetUrl` must not read the frozen constant.

### N4 — rustc stays `[~]` unless user-space rustup works (note)

No brew / apt / system packages. 开发 may try `curl https://sh.rustup.rs` into user space. If `cargo test` still cannot run, land the Rust **source** and unit tests anyway, keep D1.04 / D1.05 / D1.06 compile and WebView halves `[~]`, and capture exact `cargo --version` / `rustc --version` (command + error + exit) to scratch `tauri-toolchain.txt`. Missing rustc is not an excuse to skip TS adapters, Vite, HTTP smoke, or job tests. Do not add `cargo test` or `tauri` to `npm run verify`.

### N5 — Do not reopen locked fences (note)

Do not set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`. Do not migrate `apps/web` or add `output: 'export'`. Do not bump `APP_VERSION`. Do not start D2–D5. Do not remove ImportPanel file inputs. Do not tick §5.1 in 归档. Tracker ticks belong to `上线`. Stay on `feature/desktop-packaging`.

---

## 3. Required test list

This is the 测试-stage verification plan. It matches `.grok/workflows/desktop-phase1.rhai` and `docs/handoff/phase1-requirements.md` §6. 归档 must copy it. 开发 writes the failing tests first. 测试 drives the shipped code (no invented health/projects bodies).

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

## 4. Notes for 归档

- Start from `docs/handoff/phase1-requirements.md` plus this file. Do not reopen Electron vs Tauri, Next vs Vite, or `output: 'export'`.
- Each D1.01–D1.09 id in `docs/handoff/phase1-backlog.md`: depends-on, files, implement, tests-first, commit-hint, done-when.
- Fold **H1** into D1.03b files (extract shared Help component). Fold **H2** into D1.09 tests/implement (cancel vs kill vs processing). Fold **I1–I2** into D1.03a (resolved navigation alias + React dedupe + `.ts` extensions). Fold **I3** into D1.02a. Fold **I4** into D1.03a/D1.07 (`tauri.conf.json`). Fold **I5** into D1.04 ready-line parse + injection.
- 开发 may make extra per-task commits; it must still finish with the 开发 stage commit. Final §5.1 ticks belong to `上线`.
- Do not tick §5.1 in 归档. Do not implement production code in 归档.
- Do not start D2–D5. Do not bump to `2.1.0-desktop`. Do not set the allowlist to `$HOME`.
- Stay on `feature/desktop-packaging`. Do not open a PR or merge to `main`.
- English for the backlog. Local-first. Never modify original photos. `npm run verify` stays free of Rust/Tauri.

---

## 5. What the breakdown already got right

Do not re-litigate these:

- Scope is desktop Phase 1 (D1.01–D1.09) only, not `implement_goals.md` Phase 1 and not desktop Phases 2–5.
- Navigation: types + re-export point; Vite swaps `navigation.next`; tests are `navigation.test.tsx`; components drop direct Next navigation imports.
- `resolveApiBase()` at call time inside `request` / `assetUrl` / `exportDownloadUrl`. Window, then env, then `http://127.0.0.1:8000`.
- `isDesktopShell()` is literal `=== true` only.
- Shared Tailwind tokens; desktop CSS is an `@import` of `globals.css`; Vite `@` → `../web/src`; port 1420 `strictPort: true`.
- Shipped sidecar: allocate in Rust, drop listener, pass `--port <n>` never `0`; required absolute `--data-dir`; `FRAMEPILOT_DESKTOP=1`; parse ready line; inject both window globals before UI load; SIGTERM then kill after 5s.
- Packaged data dir is OS app-support, never CWD `.framepilot-data`.
- `npm run verify` stays rust-free; `typecheck:desktop` is TypeScript only; `dev:desktop` is not in `verify`.
- HTTP sidecar smoke can be `[x]` while WebView/compile stay dated `[~]`.
- rustc missing is inherited D0.07 `[~]`, not a Phase 1 start blocker and not the Electron trigger. User-space rustup only; never brew/apt.
- Do not migrate `apps/web`. Do not add `output: 'export'`. Do not bump `APP_VERSION`. Do not set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`.
- Tracker stays in the implementation plan §5.1; this docs stage does not tick boxes.
