# Desktop Phase 2 Requirements Breakdown

Handoff stage: `需求拆解`  
Date: 2026-08-20T20:59:44+08:00  
Branch for this pipeline: `feature/desktop-phase2` (checked out from `origin/main` `69f41bc`; do **not** reuse the merged `feature/desktop-packaging` branch)  
Scope fence: **desktop packaging Phase 2 only** — task ids **D2.00–D2.09** from `docs/plans/2026-08-18-desktop-packaging.md`.

This document is the implementation contract for later stages (`评审` → `归档` → `开发` → `测试` → `上线`). It does not implement production code.

**Not this document:**

- `implement_goals.md` Phase 2 (older v2 web Goal Mode)
- Desktop Phase 0 (D0.00–D0.09) — closed
- Desktop Phase 1 (D1.01–D1.09) — closed and merged in [PR #37](https://github.com/joe-cheung-cae/frame-pilot/pull/37)
- Desktop Phases 3–5: native menus, status bar, installers, `2.1.0-desktop` version bump

**Sources of truth (read in this order when implementing):**

1. `AGENTS.md` + `develop_plan.md` (local-first, original-file safety, English, tests)
2. `docs/plans/2026-08-18-desktop-packaging.md` (technical decisions, files, tests, commit messages; wins on technical conflict)
3. `docs/desktop_development_plan.md` §6 Phase 2 (product why; this file does not add task ids)
4. `docs/plans/2026-08-18-desktop-packaging-review.md` (A2.3 native picker vs allowlist is the Phase 2 trap)
5. This file (phase-bounded contract)
6. `docs/desktop_goal_mode.md` §7 (Goal Mode prompt; tracker still lives in the implementation plan §5.1)
7. `docs/desktop_feasibility_notes.md` (Phase 1 GO)

Conflict rule: on any technical conflict the implementation plan wins, and the product plan must be edited in the same commit that resolves the conflict. The product plan never introduces a new task id.

---

## 1. Goal

Import → Process → Cull → Export works in the desktop shell using **native folder pickers and path import**, without uploading photo bytes through the WebView File API. Originals stay immutable. The browser multipart workflow and Playwright file inputs keep working.

Phase 2 must leave the tree able to:

- Register a user-chosen project root **after** sidecar spawn, without setting `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME`.
- Pick directories and image files through Tauri dialogs; reveal folders in the OS file manager.
- Create a project from a native picker, including nonempty-folder confirmation (`acknowledge_nonempty`).
- Import on desktop via `POST /api/projects/{id}/imports/from-paths`, looping `remaining_paths` in chunks of 100, `finalize: true` only on the last slice.
- Drag-and-drop folders/files onto the **import page only**.
- Remember the last-opened project in `localStorage` (not a second database).
- Harden Windows/POSIX path handling (drive letters, spaces, non-ASCII, trailing separators, reject NUL).
- On desktop, reveal CSV/ZIP/folder artifacts instead of `<a download>`.
- Prove the full path-import → process → Pick → CSV/ZIP/folder export loop with synthetic JPEGs and unchanged sources.

Product baseline today (re-verified against live tree on `feature/desktop-phase2` / `origin/main` `69f41bc` at 2026-08-20T20:59:44+08:00):

| Area | Live state | Phase 2 implication |
|------|------------|---------------------|
| Version | `APP_VERSION = "2.0.0-rc2"` (`apps/api/app/core/version.py`, `apps/desktop/package.json`, `apps/desktop/src-tauri/Cargo.toml`) | Do not bump. D5.04 is out |
| Branch | `main` includes Phase 1 via PR #37. This pipeline is on `feature/desktop-phase2` from `origin/main` `69f41bc` | Do not commit Phase 2 on `main`. Do not reuse `feature/desktop-packaging` |
| Project roots | `create_project` allows `{data_dir}/projects` or `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` only (`projects.py:30-37`). `test_create_project_rejects_root_outside_allowlist` at `test_projects_api.py:119` 422s an outside folder and asserts `"allowlisted"` in `detail` | D2.00 process-level registry. Never widen the env allowlist. **Do not change that test's assertions** |
| Desktop env | Sidecar spawn already sets `FRAMEPILOT_DESKTOP=1` (`sidecar.rs`). No `/api/desktop/project-roots` routes exist | D2.00 endpoints 404 unless that env is set; 404 today because the routes are missing |
| Nonempty roots | API already has `acknowledge_nonempty` (`schemas/api.py:9`, `routes.py:284`). Frontend `api.createProject(name, rootPath?)` **does not send it**. `ProjectCreator` is a typed text field | D2.02 must extend the client and confirm UI |
| Path import API | `POST /imports/from-paths` exists; `IMPORT_MAX_FILES_PER_REQUEST = 100`; `ImportResult.remaining_paths` + `expanded_total` exist; immutability tests exist | Client loop is missing. D2.03 |
| Frontend import | `api.importPhotos` / `importPhotosBatch` multipart only. `ImportPanel.tsx` file inputs at 234–241 and 253–261 (`webkitdirectory` on the second at 260) | Browser inputs stay when `isDesktopShell()` is false. Desktop uses native pick + `from-paths` |
| Native FS | No `apps/web/src/lib/nativeFs.ts`. No `apps/desktop/src/lib/`. No `@tauri-apps/plugin-dialog` / opener in `apps/desktop/package.json` or `Cargo.toml`. Capabilities: `core:default` + window-state only. No `fs:` / `shell:` | D2.01. Keep **no** `fs:` / `shell:`. Dialog + opener only |
| Vite alias | Only `navigation.next` is swapped via resolved-path plugin. `"@"` → `apps/web/src` | Add a **resolved-path** alias for `nativeFs` the same way as navigation (do not barrel-import Tauri into Next) |
| Export UI | `ExportPanel.tsx` 241 and 308: `<a href={exportDownloadUrl(...)}>` for complete CSV/ZIP. Folder mode is not downloadable (`isExportDownloadable`). Copy-path buttons already exist | D2.09 replaces download anchors on desktop with reveal. Browser keeps anchors |
| Reveal | No `revealInFileManager`. Dashboard only prints `root_path` (`ProjectDashboard.tsx:62`) | D2.05 |
| Recent projects | `ProjectList` is `GET /api/projects` newest-first (`api.listProjects`). No last-opened marker | D2.06 `localStorage` only |
| Drag-drop | Not implemented. Import labels are click-to-file-input | D2.04. Overlay `pointer-events: none` unless a drag is active so Playwright inputs stay clickable |
| Jobs / quit | Phase 1 quit dialog + import cancel exist | Do not rework D1.09 |
| Shell flag | `isDesktopShell()` is true only for literal `window.__FRAMEPILOT_DESKTOP__ === true` | All desktop UI branches use this helper, never inline `window` checks |
| `npm run verify` | `lint && typecheck && typecheck:desktop && test && check:artifacts`; rust-free | Must stay rust-free |
| CI | `.github/workflows/verify.yml` on `pull_request` and push to `main` / `feature/desktop-packaging` / `refactor` | Opening a PR is what runs CI for `feature/desktop-phase2`. Do not add a new workflow in Phase 2 |
| Orchestration | `.grok/workflows/desktop-phase2.rhai` exists (this commit). Named run `desktop-phase2` paused after a 0-token 需求拆解 agent | Parent continues the same serial stages as subagents. Do not resume that paused run (`pause()` would re-fire). No production D2 code in this stage |

---

## 2. Locked decisions

Do not re-litigate these unless `docs/desktop_feasibility_notes.md` records a dated go/no-go change.

1. **Shell:** Tauri 2 + Python sidecar. Electron stays off the table.
2. **Frontend:** Dual shell, single component library. `apps/web` stays Next.js. No `output: 'export'`. Shared components live under `apps/web/src/components`, `lib`, `store`.
3. **IPC:** Photo bytes and culling stay on HTTP to `127.0.0.1`. Tauri IPC is **only** dialogs, picked paths, and reveal-in-folder.
4. **Native FS adapter:** same swap pattern as D1.01.
   - Create `apps/web/src/lib/nativeFs.ts`: `getNativeFs()` returns `null`.
   - Create `apps/desktop/src/lib/nativeFs.ts`: real `pickDirectory()`, `pickImageFiles()`, `revealInFileManager()`.
   - Shared UI imports `@/lib/nativeFs` only.
   - Desktop Vite aliases the **resolved file** `apps/web/src/lib/nativeFs.ts` → `apps/desktop/src/lib/nativeFs.ts` (copy the navigation.next plugin style; a string alias of `"./nativeFs"` will miss).
   - Next / Playwright must never import `@tauri-apps/plugin-*`.
5. **Capabilities:** add `dialog` + `opener` (or equivalent reveal plugin) only. **No** `fs:` **No** `shell:`.
6. **Project roots:** `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` is deployment-level. Tauri must **never** set it to `$HOME`, `/`, a drive root, or any broad parent. User-chosen roots become legal only after D2.00 `POST /api/desktop/project-roots` persisted in `{data_dir}/desktop_project_roots.json` (cap 50). Registry is **not** inside `Settings` (mutating settings resets the DB engine).
7. **Register endpoint:** only when `FRAMEPILOT_DESKTOP=1`; otherwise **404**. Flow: pick → register → `POST /api/projects` with `root_path`. Do not change existing allowlist error message strings.
8. **Path import:** one HTTP request consumes at most `IMPORT_MAX_FILES_PER_REQUEST` (100) expanded files and returns `remaining_paths` + `expanded_total`. Client loops with the same `job_id`. `finalize: true` only on the last slice. A 2000-file folder is never one HTTP call.
9. **Browser import invariant:** when `isDesktopShell()` is false, both `<input type="file">` elements in `ImportPanel.tsx` keep current DOM position, labels, and disabled semantics. `tests/e2e/local-workflow.spec.ts` depends on them.
10. **Desktop downloads:** desktop does not download API blobs through the WebView. Every export mode already returns `output_path`; desktop reveals it. Browser keeps `<a download>` / `exportDownloadUrl`.
11. **Safety:** copy-mode unchanged. Originals are never modified or deleted. Keep `test_import_from_paths_immutability.py` and export path-escape tests green.
12. **Web app must keep working.** `npm run dev` on `:3000`/`:8000`, `npm run verify`, and Playwright stay green. `npm run verify` must not require rustc/cargo/Tauri.
13. **Version:** `APP_VERSION` stays `2.0.0-rc2`.
14. **No cloud, login, payment, bundled models, HEIC/RAW/XMP.**
15. **Tracker:** `docs/plans/2026-08-18-desktop-packaging.md` §5.1 is the status source of truth. Tick **exactly one** D2.xx box per product commit, in the same commit as that id's code and tests.
16. **GitHub submission (Phase 2 requirement):** after **every** finished D2.00–D2.09 task: commit, `git push -u origin HEAD`, and ensure one draft PR against `main` exists and updates. Docs stages (`需求拆解` / `评审` / `归档` / `测试` / `上线`) also push. Do **not** merge. Do **not** squash. Do **not** force-push. Do **not** open a second PR.

---

## 3. In-scope ids

Implement **only** these ids, one at a time, tests first. Suggested serial order is tracker order; it already satisfies depends-on once earlier ids are done.

| ID | Title | Depends on | Commit hint |
|----|-------|------------|-------------|
| D2.00 | Registered project roots | D0.03 (done) | `api: register desktop project roots before use` |
| D2.01 | Native file dialog adapters | Phase 1 (done) | `desktop: add native file dialog adapters` |
| D2.02 | Project create with native picker | D2.00, D2.01 | `web: use native directory picker when desktop APIs exist` |
| D2.03 | Import panel path import | D0.04b (done), D2.01 | `web: import from local paths in desktop mode` |
| D2.04 | Drag and drop | D2.03 | `desktop: add import drag-and-drop` |
| D2.05 | Reveal project and export folders | D2.01 | `desktop: reveal project and export paths in the OS file manager` |
| D2.06 | Recent projects | D1.05 (done) | `desktop: remember last opened project` |
| D2.07 | Cross-platform path hardening | D0.04a (done) | `api: harden desktop import paths` |
| D2.08 | Full workflow verification | D2.03, D2.05 | `test: cover path-import process export workflow` |
| D2.09 | Reveal exports instead of downloading | D2.01, D2.05 | `desktop: reveal export artifacts instead of downloading them` |

Current §5.1 Phase 2 boxes (all `[ ]` as of this breakdown). Do not tick them in this documentation stage.

---

## 4. Out of scope

- Desktop Phase 0/1 redo, including sidecar lifecycle, quit dialog, Vite SPA, navigation adapter.
- Desktop Phase 3–5: menus, status bar, `GET /api/meta`, theme, tray, NSIS/DMG, desktop CI matrix, signing, version bump, README overhaul beyond what a task already names.
- Setting `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME` / `/` / a drive root.
- Removing or relocating the two browser file inputs when `isDesktopShell()` is false.
- Migrating `apps/web` off Next.js or adding `output: 'export'`.
- Replacing scoring/grouping with Rust.
- HEIC / RAW / XMP / bundled models / cloud / login / payment.
- Making `npm run verify` require Rust, Tauri, or Playwright.
- Merging to `main`, publishing installers, bumping to `2.1.0-desktop`.
- Detached preview window, auto-update, changing the data directory.

---

## 5. Files to create / modify (per id)

### D2.00 — Registered project roots

- **Create:** `apps/api/app/core/project_roots.py`
- **Modify:** `apps/api/app/services/projects.py` (`allowed_roots = [projects_root, *allowlist, *registered_roots()]`). Do **not** change error message strings.
- **Modify:** `apps/api/app/api/routes.py` — `POST` and `GET` `/api/desktop/project-roots` only when `FRAMEPILOT_DESKTOP=1`; else 404
- **Docs:** `docs/api.md` (`root_path` currently omits the allowlist / registration)
- **Test:** `apps/api/tests/test_desktop_project_roots.py`
- **Fixture:** `clear_registered_roots()` so tests do not leak JSON across cases

`register_root`: absolute, exists, directory, resolved. Reject `BLOCKED_ROOT_NAMES`, filesystem anchors (`project_root.anchor`), the data dir, and parents of the data dir. Persist `{data_dir}/desktop_project_roots.json`, cap 50. Survive `create_app()` restart (file, not process memory only).

**Tests (write first):**

- `test_create_project_rejects_root_outside_allowlist` still 422 with the same detail (unchanged).
- Outside root 422 until registered, then create succeeds.
- `/`, `/etc`, `C:\Windows`, data dir, relative path, file-not-dir → 422.
- Endpoints 404 when `FRAMEPILOT_DESKTOP` unset.
- Roots survive `create_app()` restart.
- Cap 50.

### D2.01 — Native file dialog adapters

- **Create:** `apps/web/src/lib/nativeFs.ts` (`getNativeFs(): NativeFs | null` → `null`)
- **Create:** `apps/desktop/src/lib/nativeFs.ts` (Tauri dialog + opener)
- **Modify:** `apps/desktop/vite.config.ts` — resolved-path alias like `navigation.next`
- **Modify:** `apps/desktop/src-tauri/Cargo.toml`, `capabilities/default.json`, `lib.rs` plugin init
- **Modify:** `apps/desktop/package.json` — `@tauri-apps/plugin-dialog` and opener
- **Test:** `apps/web/src/lib/nativeFs.test.ts` (null in browser / without window). Desktop wrappers unit-tested with mocked plugins, not live dialogs.

### D2.02 — Project create with native picker

- **Modify:** `apps/web/src/lib/api.ts` `createProject` — optional `acknowledgeNonempty`
- **Modify:** `apps/web/src/lib/projectCreation.ts` — `acknowledgeNonempty` only after confirmation
- **Modify:** `ProjectCreator.tsx` — if `getNativeFs()`, Browse fills `root_path` after register; surface 422 verbatim
- **Confirm copy (English):** `This folder already contains files. FramePilot will create its project folders inside it and will not modify existing files. Continue?`
- **Browser:** text field stays; no acknowledge flag unless the user confirmed
- **Test:** `projectCreation.test.ts`; API tests for registered nonempty root without/with the flag; existing files still present

### D2.03 — Import panel path import

- **Modify:** `apps/web/src/lib/api.ts` — `importPhotosFromPaths` looping `remaining_paths` with the same `job_id`
- **Modify:** `apps/web/src/lib/importWorkflow.ts` — progress uses `expanded_total`
- **Modify:** `ImportPanel.tsx` — desktop: pick folder/files → path import. Browser: existing multipart
- **Invariant:** `isDesktopShell() === false` keeps both file inputs
- **Test:** `importWorkflow.test.ts` remaining-paths loop. Run `npm run test:e2e` before Phase 2 close (D2.08 / `测试`)

### D2.04 — Drag and drop

- **Modify:** `ImportPanel.tsx`; Tauri drag-drop if HTML5 drop has no filesystem paths
- Overlay `pointer-events: none` unless a drag is active
- Do not start import on drop outside the import page
- **Test:** `collectDroppedPaths(event)` unit test. `npm run test:web`

### D2.05 — Reveal project / export folders

- **Modify:** `ProjectDashboard.tsx`, `ExportPanel.tsx`
- Buttons: “Open project folder”, “Open export folder” via `revealInFileManager(output_path | root_path)`
- **Test:** helper that the reveal callback is invoked with `output_path`

### D2.06 — Recent projects

- **Create:** helper e.g. `apps/web/src/lib/recentProjects.ts` (localStorage last-opened id)
- **Modify:** `ProjectList.tsx` (and dashboard open path) to record last opened
- `GET /api/projects` remains the list. Do not invent a second database
- **Test:** `recentProjects.test.ts` or `.test.tsx`

### D2.07 — Cross-platform path hardening

- **Modify:** `importing.py`, `projects.py`, D2.00 registry if needed
- **Test:** Windows drive letters, spaces, non-ASCII, trailing separators, reject NUL; keep `os.pathsep` allowlist parsing. Skip live Win32-only cases on POSIX

### D2.08 — Full workflow verification

- **Create:** `tests/desktop/workflow.md` (manual GUI checklist: pick folder, cull with keyboard, export, reveal)
- **Create:** pytest using `from-paths` then process + Pick + CSV/ZIP/folder export + source `st_size` / mtime / hash unchanged
- Run: `npm run test:api` and `npm run test:e2e` if ImportPanel changed

### D2.09 — Reveal instead of download on desktop

- **Modify:** `ExportPanel.tsx` (`<a>` around the complete CSV/ZIP actions, live 241 and 308)
- **Modify:** `ImportExportPanels.test.tsx`
- Branch on `isDesktopShell()`. Flag unset → current href. Flag true → reveal button, **no** `<a download>` / `exportDownloadUrl` anchor
- If macOS WKWebView blocks loopback HTTP **images**, record it in feasibility notes — do **not** redesign the asset pipeline here

---

## 6. Tests-first list (required)

| ID | Write first | Command after green |
|----|-------------|---------------------|
| D2.00 | `apps/api/tests/test_desktop_project_roots.py` | `npm run test:api` (or the new file + `test_projects_api.py::test_create_project_rejects_root_outside_allowlist`) |
| D2.01 | `apps/web/src/lib/nativeFs.test.ts` | `npm run test:web` + `npm run typecheck:desktop` |
| D2.02 | extend `projectCreation.test.ts` | `npm run test:web` + API nonempty-root cases |
| D2.03 | extend `importWorkflow.test.ts` / `api.test.ts` | `npm run test:web` |
| D2.04 | `collectDroppedPaths` unit test | `npm run test:web` |
| D2.05 | reveal-callback helper test | `npm run test:web` |
| D2.06 | `recentProjects.test.ts` | `npm run test:web` |
| D2.07 | path hardening pytest | `npm run test:api` |
| D2.08 | path-import process export pytest | `npm run test:api`; `npm run test:e2e` before close |
| D2.09 | `ImportExportPanels.test.tsx` desktop vs browser | `npm run test:web` |

Drive shipped functions. Do not mock the unit under test. Do not invent HTTP bodies if a live sidecar launch fails.

Original-file safety is always in scope: keep `test_import_from_paths_immutability.py` and export containment green.

---

## 7. GitHub submission protocol

This is a Phase 2 pipeline requirement, not an optional nicety.

**Branch:** `feature/desktop-phase2` from current `origin/main`. If the branch is missing, create it. Do not commit Phase 2 work on `main`.

**After every D2.00–D2.09 product commit (mandatory):**

1. Working tree for that id is committed (code + tests + §5.1 tick + related docs).
2. `git status` is clean except unrelated files you did not touch.
3. `git push -u origin HEAD`.
4. If no open PR for this head exists, create **one draft PR**:
   - repo: `joe-cheung-cae/frame-pilot`
   - base: `main`
   - head: `feature/desktop-phase2`
   - title: `desktop: Phase 2 native filesystem and core workflow`
   - body: list of D2.00–D2.09, what landed so far, `APP_VERSION` stays `2.0.0-rc2`, does not merge itself
   - Prefer `gh pr create --draft ...`. Fallback: GitHub MCP `create_pull_request` with `draft: true`.
5. Append to scratch `git-github.txt`: SHA, subject, push result, PR URL.
6. Update `docs/handoff/STATUS.md` notes with the latest SHA and PR URL (may be the same commit or the next docs-stage commit — do not skip the push of the product commit itself).

**Docs stages** (`需求拆解`, `评审`, `归档`, `测试`, `上线`) also `git push -u origin HEAD` after their commit.

**Forbidden:** merge to `main`; squash; force-push; second PR; rewriting already-pushed D2.xx history; skipping push because CI is red (push anyway so GitHub has the commit; fix forward).

If push fails: capture the exact git/gh error to scratch, retry **once**, then continue product work and report the blocker in `STATUS.md`. Do not pretend the task was submitted.

---

## 8. Acceptance (Phase 2)

From the implementation plan, plus GitHub:

- [ ] Desktop (or API-equivalent) completes Import → Process → Cull → Export
- [ ] Source files unmodified
- [ ] Multipart browser import and E2E file inputs still work
- [ ] `npm run verify` green
- [ ] Each D2.00–D2.09 id is a distinct commit on `origin/feature/desktop-phase2`
- [ ] One draft PR against `main` is open and contains those commits
- [ ] `APP_VERSION` is still `2.0.0-rc2`
- [ ] `test_create_project_rejects_root_outside_allowlist` unchanged and green

`上线` ticks §5.1 Phase 2 boxes to `[x]` or dated `[~]`. `[~]` is only for live WebView picker/drag clicks this host cannot exercise. HTTP/API/unit coverage must still be `[x]`.

---

## 9. Environment and risks

| Risk | Mitigation |
|------|------------|
| Native picker vs allowlist (review A2.3) | D2.00 first. Never `$HOME` allowlist |
| Vite alias misses `nativeFs` the way `"./navigation.next"` did | Resolved-path plugin, copy D1.03a |
| Tauri in the Next bundle | `getNativeFs()` null on web; no plugin import under `apps/web` |
| Playwright file inputs blocked by a drop overlay | `pointer-events: none` unless drag active |
| WKWebView download / image quirks | D2.09 reveal; do not redesign assets |
| This host may lack rustc | User-space rustup only. Dialog source still lands. Live picker clicks may be `[~]` |
| `verify.yml` does not list `feature/desktop-phase2` | Draft PR is what runs `pull_request` CI |
| Hardcoded Phase 0/1 repo paths (`/Users/chao/...`) | Resolve repo with `git rev-parse --show-toplevel`. Scratch: `$HOME/.cache/framepilot-desktop-phase2` `chmod 700`. Never `/tmp` |

Do not start D3–D5 from this pipeline. Do not bump the version. Do not merge.
