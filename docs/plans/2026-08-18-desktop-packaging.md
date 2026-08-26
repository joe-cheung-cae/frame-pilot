# FramePilot Desktop Packaging Implementation Plan

> Language: **English** | [中文](2026-08-18-desktop-packaging.zh.md)

> **For Grok / Claude Goal Mode:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` (or this document's loop) to implement **one task id at a time**. Do not start the next task until the current task is implemented, tested, reviewed, and committed.
>
> **Opus 5 review (2026-08-18):** findings were folded into this plan; the review file was removed as redundant. Start at **D0.00**. Status lives in §5.1.

**Goal:** Ship FramePilot as an installable Windows and macOS desktop app that auto-starts a local Python sidecar, reuses the current v2.0.0-rc2 culling workflow, and never modifies original photos.

**Architecture:** Keep the existing FastAPI + SQLite backend as a localhost-only sidecar. Keep `apps/web` as the browser/E2E frontend. Add `apps/desktop` as a Tauri 2 shell plus a Vite SPA that reuses `apps/web/src/components` and `apps/web/src/lib`. Talk to the sidecar over `http://127.0.0.1:<port>` with runtime port injection. Add a chunked path-based import API so native folder pickers do not re-upload thousands of photo bytes through the browser File API.

**Tech Stack:** Tauri 2 (Rust), PyInstaller sidecar, FastAPI/Uvicorn, Vite + React 19 + TypeScript + Tailwind, existing SQLModel/SQLite/Pillow/imagehash stack.

**Source product plan:** `docs/desktop_development_plan.md`  
**Current product baseline:** FramePilot `2.0.0-rc2` local web app  
**Recommended branch:** `feature/desktop-packaging`  
**First desktop version:** `2.1.0-desktop` (keep `2.0.x` as the local web line)

---

## 0. Document Hierarchy

| Question                                                                    | Source of truth                              |
| --------------------------------------------------------------------------- | -------------------------------------------- |
| Why we ship desktop, scope, phases, UI intent, effort estimates             | `docs/desktop_development_plan.md` (product) |
| Every technical decision, task id, file path, test, command, acceptance box | this file (implementation)                   |
| What an agent may and may not do in a session                               | `docs/desktop_goal_mode.md` + `AGENTS.md`    |
| Measured results, blockers, go/no-go records                                | `docs/desktop_feasibility_notes.md`          |
| Repo-wide constraints (local-first, original-file safety, English, tests)   | `AGENTS.md`, then `develop_plan.md`          |

Conflict rule: on any technical conflict this implementation plan wins, and the product plan must be edited in the same commit that resolves the conflict. The product plan never introduces a new task id.

---

## How Goal Mode Must Work

Copy `docs/desktop_goal_mode.md` into Grok Build Goal Mode. The agent must follow this loop for **every** task id:

1. Read `develop_plan.md`, `AGENTS.md`, this plan (including §5.1), and `git status`.
2. Pick the lowest incomplete (`[ ]`) task id whose dependencies are `[x]`.
3. Write the tests named in the task **first** and watch them fail for the right reason.
4. Implement only that task, minimally, until those tests pass.
5. Run the listed commands. Fix until green.
6. Review `git diff`.
7. Tick the task in §5.1 (or mark `[~]` with a dated note in `docs/desktop_feasibility_notes.md`).
8. Commit implementation, tests, and the tracker tick together with the suggested message.
9. Only then start the next task.

Never mix Phase 0 packaging spikes with Phase 3 UI polish. Never commit failing tests. Never modify original photos. Never add cloud, login, payment, or bundled model files.

If a task cannot be finished safely: shrink it, commit a smaller green slice, and leave a blocker note in `docs/desktop_feasibility_notes.md` (create that file in D0.01 if missing).

Session budget: at most **5 task ids or one phase** per session, then stop and summarize.

---

## 1. Current Repository State (2026-08-18)

Verified against the live tree. Desktop packaging has **not** started.

| Area           | Current state                                                                                                                                                         | Desktop implication                                                                    |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Version        | `2.0.0-rc2` in root/`apps/web`/`apps/api` plus `FastAPI(version=...)`                                                                                                 | Single source `apps/api/app/core/version.py` in D0.02; bump only in D5.04              |
| Frontend       | Next.js 15 App Router, React 19, client-side fetch                                                                                                                    | No Server Actions, middleware, or `next/image`                                         |
| API base       | `NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"` in `apps/web/src/lib/api.ts:1`                                                                                  | Module-level constant cannot see a port injected after load                            |
| Import         | Multipart `UploadFile` only (`apps/api/app/api/routes.py:281-299`); max 100 files (`importing.py:43`)                                                                 | Path import must chunk expansion; never copy 2000 files in one HTTP call               |
| Project path   | Typed text field; API rejects roots outside `{data_dir}/projects` or allowlist (`projects.py:33-37`); nonempty dirs need `acknowledge_nonempty` (`projects.py:40-43`) | Native picker needs D2.00 registration + confirm UI                                    |
| Drag-drop      | Not implemented                                                                                                                                                       | New desktop work                                                                       |
| CORS/origin    | Mutating requests must come from `localhost:3000` or `:3100` (`apps/api/app/main.py:14-65`); GET has no Host check                                                    | Tauri origins 403; DNS rebinding on GET assets                                         |
| Data dir       | `FRAMEPILOT_DATA_DIR` or CWD-relative `.framepilot-data`; `create_app()` runs at import (`main.py:76`)                                                                | Frozen CWD is unusable; `--data-dir` required; set env **before** importing `app.main` |
| Jobs           | In-process FastAPI `BackgroundTasks`                                                                                                                                  | Quit during import looks like data loss without D1.09                                  |
| Health         | `GET /health` and `GET /api/health` → `{"status": "ok"}`; test exact-equality at `test_projects_api.py:19`                                                            | Keep `status`; add version from one source                                             |
| CI             | No `.github/workflows`                                                                                                                                                | D0.00 first                                                                            |
| Artifact check | `scripts/check-release-artifacts.sh` blocks all tracked `*.png`                                                                                                       | Tauri icons need D0.07a **before** any icon commit                                     |
| Tauri/Electron | Docs only                                                                                                                                                             | Greenfield `apps/desktop` + `packaging/`                                               |
| E2E            | Playwright against Next `:3100` + API `:8000`; `ImportPanel.tsx` file inputs at 234–261                                                                               | Desktop must not remove browser file inputs                                            |
| Test runners   | `src/lib/*.test.ts` = node `--test`; vitest collects `src/**/*.test.tsx` only                                                                                         | React adapter tests must be `.test.tsx`                                                |

### Frontend export spike expectation

`output: 'export'` is **not drop-in**. Five `projects/[projectId]/...` routes have no `generateStaticParams`. **Do not migrate `apps/web` off Next.js.** D0.06 is documentation-only.

### Environment note (this machine)

The current workspace is **Linux WSL2**. PyInstaller sidecar work can proceed here. A Tauri window may fail inside WSL. Do not block backend/API tasks on a GUI. `[~]` in §5.1 is never upgraded to `[x]` without a recorded GUI run (Windows host, macOS, or CI).

---

## 2. Locked Decisions

These are not re-litigated during Goal Mode unless Phase 0 produces a written go/no-go change in `docs/desktop_feasibility_notes.md`.

1. **Shell:** Tauri 2 + Python sidecar. Electron only if Tauri is blocked in writing after D0.09.
2. **Backend:** Keep FastAPI. Package with PyInstaller one-dir (not one-file) because numpy/scipy/Pillow load poorly from one-file extracts.
3. **Frontend:** Dual shell, single component library.
   - `apps/web` = Next.js for browser + Playwright.
   - `apps/desktop` = Tauri + Vite SPA.
   - Shared: `apps/web/src/components/*`, `apps/web/src/lib/*`, `apps/web/src/store/*`.
   - Navigation adapter is swapped by **Vite alias**, not a barrel that re-exports `next/link`.
4. **IPC:** HTTP to sidecar for v2.1. No rewrite of scoring/grouping onto Rust. Optional Tauri IPC for dialogs, paths, and reveal-in-folder only.
5. **Import:** Path-based import is the desktop primary path. Keep multipart for browser parity.
6. **Bind:** Sidecar listens on `127.0.0.1` only. Never `0.0.0.0`.
7. **Port:** Tauri allocates a free loopback TCP port and always passes an explicit `--port <n>`. The sidecar also supports `--port 0` for tests and standalone use; in that mode it binds the socket itself, resolves the real port via `getsockname()`, prints the ready line, and only then serves. The sidecar never guesses or re-reports port 0.
8. **Data dir:** Tauri sets `--data-dir` / `FRAMEPILOT_DATA_DIR` to OS app-support:
   - macOS: `~/Library/Application Support/FramePilot`
   - Windows: `%APPDATA%\FramePilot`
   - Linux (dev only): `~/.local/share/FramePilot`
     Sidecar `--data-dir` is **required**. Never fall back to CWD-relative `.framepilot-data`.
9. **Safety:** Copy-mode storage unchanged. Originals are copied into the project; sources are never modified or deleted. Asset/export path containment tests must stay green.
10. **Web app must keep working.** `npm run dev`, `npm run verify`, and Playwright must remain green after every desktop commit that touches shared code.
11. **Project roots on desktop:** `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` stays a deployment-level control and must NEVER be set to `$HOME`, `/`, a drive root, or any broad parent by the Tauri shell. A user-chosen project root becomes legal only after D2.00 registration persisted in `{data_dir}/desktop_project_roots.json`. `test_create_project_rejects_root_outside_allowlist` must stay green unchanged.
12. **Path import request shape:** one HTTP request consumes at most `IMPORT_MAX_FILES_PER_REQUEST` (100) expanded files and returns `remaining_paths` plus `expanded_total`. The client loops with the same `job_id`. A folder of 2000 photos is never one HTTP call.
13. **GUI-blocked tasks:** when remaining verification needs a real WebView and the host cannot open one, mark `[~]`, append a dated feasibility note, and continue with unblocked work. `[~]` is never `[x]` without a recorded GUI run.
14. **Desktop downloads:** the desktop shell does not download API responses through the WebView. Every export mode already returns `output_path`; desktop reveals the artifact. Browser keeps `<a download>`.
15. **Single version source:** `apps/api/app/core/version.py` defines `APP_VERSION`. `main.py` and both health endpoints read it. `pyproject.toml` and both `package.json` files are updated only in D5.04.
16. **Shell detection:** `window.__FRAMEPILOT_DESKTOP__ === true`, injected by Tauri before frontend load. Shared code reads it only through `isDesktopShell()` in `apps/web/src/lib/shell.ts`.

---

## 3. Hard Constraints

Copied from `AGENTS.md` and `develop_plan.md`; they apply to every desktop task:

- Local-first only. No cloud upload, accounts, payment, telemetry requirement, or remote processing.
- Never modify or delete original photo files.
- Do not commit private photos, generated datasets, SQLite files, installers, or large model files.
- English for code, comments, tests, docs, commits, and new UI strings.
- Prefer small deterministic algorithms. Do not add HEIC/RAW/XMP/models in this desktop track.
- Do not restart the product from scratch.
- Do not weaken export/asset path-escape tests.
- Use English commit messages. Preferred prefixes: `desktop:`, `api:`, `web:`, `test:`, `docs:`, `ci:`.
- Do not widen `scripts/check-release-artifacts.sh` beyond a single explicit `apps/desktop/src-tauri/icons/` exception (D0.07a).
- Do not weaken `apps/api/tests/test_projects_api.py::test_create_project_rejects_root_outside_allowlist`.
- Every task carries Depends on / Files / Implement / Tests / Commit.

---

## 4. Target Tree

```text
frame-pilot/
├── apps/
│   ├── api/                      # existing FastAPI; add sidecar CLI
│   ├── web/                      # existing Next.js browser app
│   └── desktop/                  # NEW
│       ├── package.json
│       ├── vite.config.ts
│       ├── index.html
│       ├── src/                  # Vite entry, router, desktop adapters
│       └── src-tauri/
│           ├── Cargo.toml
│           ├── tauri.conf.json
│           ├── capabilities/
│           ├── icons/            # allowed by D0.07a exception only
│           └── src/lib.rs
├── packaging/
│   ├── pyinstaller/
│   │   ├── framepilot-api.spec
│   │   ├── hooks/
│   │   └── build.sh
│   └── scripts/
│       └── stage-sidecar.sh
├── tests/
│   ├── e2e/                      # existing Playwright (keep)
│   └── desktop/                  # NEW sidecar/lifecycle smokes (shell, not pytest under apps/api)
├── docs/
│   ├── desktop_development_plan.md
│   ├── desktop_goal_mode.md
│   ├── desktop_feasibility_notes.md
│   └── plans/2026-08-18-desktop-packaging.md
└── .github/workflows/
    ├── verify.yml                # D0.00
    └── desktop.yml               # D4.04
```

---

## 5. Shared Acceptance Gates

Run these unless a task lists a narrower command:

```bash
npm run lint:api
npm run test:api
npm run typecheck # if web/desktop TS changed
npm run test:web  # if apps/web changed
npm run verify    # before finishing a phase; must not require Rust
```

Desktop-only extras, added over the phases:

```bash
npm run test:sidecar       # D0.05+
npm run typecheck:desktop  # D1.03a+
npm run test:desktop:smoke # D1.08+
```

Original-file safety is always in scope: any import/export change must keep `apps/api/tests/test_ranking_export.py` and import immutability coverage passing.

### 5.1 Task Tracker

Status keys: `[ ]` not started, `[x]` done and committed, `[~]` blocked on a GUI or signing capability (locked decision 13), `[-]` cancelled or moved.

Update this list **in the same commit** as the task it describes.

Phase 0 — closed `上线` 2026-08-19 on `refactor` (GO; Phase 1 not started)

- [x] D0.00 CI verify workflow
- [x] D0.01 Sidecar CLI launcher
- [x] D0.02 Health payload with version
- [x] D0.03 Origin and Host policy
- [x] D0.04a Import path expansion helper
- [x] D0.04b Path-based import endpoint
- [x] D0.04c Path import immutability tests
- [x] D0.05 PyInstaller spec and sidecar smoke
- [x] D0.06 Next static export spike (docs)
- [x] D0.07a Tauri artifact/gitignore hygiene
- [~] D0.07 Minimal Tauri shell with sidecar health — Phase 0 (2026-08-19T08:26:40Z) `cargo --version` / `rustc --version`: `zsh:1: command not found: cargo` / `zsh:1: command not found: rustc` (exit 127). Box stays `[~]` as the Phase 0 close-out. Phase 1 later installed user-space rustup and opened a FramePilot window (see D1.08). Compile-blocked was not the Electron trigger; sidecar was spawned. See `docs/desktop_feasibility_notes.md`.
- [x] D0.08 Baselines
- [x] D0.09 Go / no-go

Phase 1 — closed `上线` 2026-08-19 on `feature/desktop-packaging` (GO; Phase 2 not started)

- [x] D1.01 Navigation adapter
- [x] D1.02 Runtime API base
- [x] D1.02a Desktop shell flag
- [x] D1.03a Vite build, aliases, Tailwind
- [x] D1.03b Desktop router
- [x] D1.04 Sidecar lifecycle in Rust
- [x] D1.05 App-support data directory
- [x] D1.06 Window basics and single instance
- [x] D1.07 Dev scripts and verify wiring
- [x] D1.08 Desktop smoke: health + project list — HTTP `[x]` (`npm run test:desktop:smoke` twice, 2026-08-19T18:54:03+08:00 / 18:54:04+08:00). WebView `[x]` 2026-08-19T18:54:32+08:00 `npm run dev:desktop` opened window title `FramePilot`; sidecar `127.0.0.1:54451` `GET /health` and WebView `OPTIONS`+`GET /api/projects` 200 (empty list OK).
- [x] D1.09 Graceful quit with a running job

Phase 2

- [x] D2.00 Registered project roots
- [x] D2.01 Native file dialog adapters
- [x] D2.02 Project create with native picker
- [x] D2.03 Import panel path import
- [x] D2.04 Drag and drop
- [x] D2.05 Reveal project and export folders
- [x] D2.06 Recent projects
- [x] D2.07 Cross-platform path hardening
- [x] D2.08 Full workflow verification
- [x] D2.09 Reveal exports instead of downloading

Phase 3

- [~] D3.01 Native menu bar — `npm run test:web` green 2026-08-23; GUI/`cargo test` unverified (`rustc` 1.85 cannot compile current Tauri lockfile). See `docs/desktop_feasibility_notes.md`.
- [~] D3.02 Status bar — `npm run test:web` green 2026-08-26; GUI/`cargo test` unverified (`rustc` 1.85 cannot compile current Tauri lockfile). See `docs/desktop_feasibility_notes.md`.
- [ ] D3.03 Settings data directory (`GET /api/meta`)
- [ ] D3.04 System theme follow
- [ ] D3.05 Empty and error copy
- [ ] D3.06 Optional tray (may end `[-]`)
- [ ] D3.07 Shortcut vs menu accelerator pass

Phase 4

- [ ] D4.01 Bundle sidecar into Tauri resources
- [ ] D4.02 NSIS and DMG config
- [-] D4.03 Moved to D0.00
- [ ] D4.04 Desktop CI matrix
- [ ] D4.05 Signing runbook
- [ ] D4.06 Size pass

Phase 5

- [ ] D5.01 Desktop test matrix
- [ ] D5.02 README and user docs
- [ ] D5.03 Desktop performance notes
- [ ] D5.04 Version bump to 2.1.0-desktop
- [ ] D5.05 Known limitations
