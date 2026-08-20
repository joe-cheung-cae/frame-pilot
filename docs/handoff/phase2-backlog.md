# Desktop Phase 2 Accepted Backlog

Handoff stage: `归档`  
Date: 2026-08-20T21:08:00+08:00  
Branch: `feature/desktop-phase2`  
Sources: `docs/handoff/phase2-requirements.md` (`9e5416a`), `docs/handoff/phase2-review.md` (`2cba9bf`), `docs/plans/2026-08-18-desktop-packaging.md` D2.00–D2.09 and §5.1  
Draft PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (do not merge)

**Verdict folded:** accept-with-notes. This file is the accepted implementation contract for **D2.00–D2.09 only**. Do not reopen Electron vs Tauri, Next vs Vite, or `output: 'export'`.

This document does not implement production code. Do not start Phase 3–5. Do not bump `APP_VERSION`.

---

## Process

- Implement **one id at a time**, tests first, then the smallest change that makes those tests pass.
- **Never start the next D2 id until the current id is implemented, tested, passing, committed, AND pushed to GitHub.**
- 开发 **MUST** make **one product commit per id**, tick **that one** box in `docs/plans/2026-08-18-desktop-packaging.md` §5.1 in the **same commit**, then `git push -u origin HEAD`.
- Commit subject must match **commit-hint**.
- Do not tick a box whose tests you did not run and see pass in this session.
- Drive shipped code. Do not mock the unit under test.
- `测试` runs `test:api`, `test:web`, `typecheck:desktop`, rust-free `verify`, `test:e2e`.
- `上线` confirms §5.1 Phase 2 boxes `[x]` or dated `[~]`, close-out STATUS, push, does **not** merge. Ready-for-review is allowed.
- Stay on `feature/desktop-phase2`. One draft PR (#38). Later tasks only push. Do not merge. Do not squash. Do not force-push. Do not open a second PR.
- Local-first. Never modify original photos. English for code, comments, tests, docs, and commits.
- `npm run verify` stays free of rustc/cargo/Tauri.
- Do not resume the paused named workflow run `desktop-phase2` (`pause()` re-fires). Continue as serial parent/subagents.

| ID | Title | Depends on |
|----|-------|------------|
| D2.00 | Registered project roots | D0.03 (done) |
| D2.01 | Native file dialog adapters | Phase 1 (done) |
| D2.02 | Project create with native picker | D2.00, D2.01 |
| D2.03 | Import panel path import | D0.04b (done), D2.01 |
| D2.04 | Drag and drop | D2.03 |
| D2.05 | Reveal project and export folders | D2.01 |
| D2.06 | Recent projects | D1.05 (done) |
| D2.07 | Cross-platform path hardening | D0.04a (done) |
| D2.08 | Full workflow verification | D2.03, D2.05 |
| D2.09 | Reveal exports instead of downloading | D2.01, D2.05 |

Serial order is tracker order above.

---

## Folded review notes

| Id | Finding | Folded into |
|----|---------|-------------|
| H1 | A2.3: picker cannot create a project until registration | D2.00 then D2.02. Never `$HOME` allowlist |
| H2 | Registry must not live in Settings (`reset_settings_cache` resets DB engine) | D2.00 file `{data_dir}/desktop_project_roots.json` |
| H3 | Tauri plugin imports must not sit under `apps/web/src/lib/*.test.ts` | D2.01 web stub tests vs desktop wrapper tests |
| H4 | Current ExportPanel test is error-only | D2.09 success-path harness |
| N1 | Reuse `desktop_mode_enabled()` | D2.00 404 |
| N2 | Reject data dir and parents, `/`, `/etc`, `C:\Windows` | D2.00 `register_root` |
| N3 | Drop only on the import page; overlay `pointer-events: none` unless drag active | D2.04 |
| N4 | One draft PR #38; do not resume paused workflow | github-submit on every id |

---

## Locked decisions (do not re-litigate)

1. **Shell:** Tauri 2 + Python sidecar. Dual shell. `apps/web` stays Next.js. No `output: 'export'`.
2. **IPC:** Photo bytes stay on HTTP to `127.0.0.1`. Tauri IPC is **only** dialogs, picked paths, and reveal.
3. **nativeFs:** `apps/web/src/lib/nativeFs.ts` `getNativeFs()` returns `null`. Desktop implementation aliased by **resolved path** like `navigation.next`. Next must not import `@tauri-apps/plugin-*`.
4. **Capabilities:** dialog + opener only. **No** `fs:`. **No** `shell:`.
5. **Project roots:** Never set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`, `/`, or a drive root. Registry in `{data_dir}/desktop_project_roots.json`, cap 50, not Settings. Endpoints 404 unless `FRAMEPILOT_DESKTOP=1` (`desktop_mode_enabled()`).
6. **Allowlist test:** Do not change `test_create_project_rejects_root_outside_allowlist` assertions or allowlist error strings.
7. **Path import:** Client loops `remaining_paths`; max 100 expanded files per request; `finalize: true` only on last slice.
8. **Browser import:** When `isDesktopShell()` is false, both ImportPanel file inputs (including `webkitdirectory`) keep current DOM position, labels, and disabled semantics.
9. **Downloads:** Desktop reveals export `output_path`; browser keeps `<a href=exportDownloadUrl>`.
10. **Version:** `APP_VERSION` stays `2.0.0-rc2`. `npm run verify` stays rust-free.
11. **Safety:** Copy-mode unchanged. Originals are never modified or deleted.
12. **No cloud, login, payment, bundled models, HEIC/RAW/XMP.** Do not start Phase 3–5.

**github-submit (every D2 id and every docs stage):**

1. Commit only that id (code + tests + §5.1 tick of that one box + related docs).
2. `git push -u origin HEAD`.
3. PR already exists: https://github.com/joe-cheung-cae/frame-pilot/pull/38 — do not create another.
4. Append SHA, subject, push result, PR URL to `$HOME/.cache/framepilot-desktop-phase2/git-github.txt`.
5. If push fails: capture the exact error, retry once, continue product work, report in `docs/handoff/STATUS.md`. Do not claim the task was submitted.

---

## D2.00 — Registered project roots

**depends-on:** D0.03 (done)

**files:**
- create: `apps/api/app/core/project_roots.py`
- modify: `apps/api/app/services/projects.py` — `allowed_roots = [projects_root, *allowlist, *registered_roots()]`. Do **not** change error message strings.
- modify: `apps/api/app/api/routes.py` — `POST` and `GET` `/api/desktop/project-roots` only when `desktop_mode_enabled()`; else 404
- docs: `docs/api.md` (`root_path` currently omits allowlist / registration)
- test: `apps/api/tests/test_desktop_project_roots.py`
- fixture: `clear_registered_roots()` so tests do not leak JSON across cases

**implement:**
- `register_root`: absolute, exists, directory, resolved. Reject `BLOCKED_ROOT_NAMES`, filesystem anchors (`project_root.anchor`), the data dir, and parents of the data dir. Persist `{data_dir}/desktop_project_roots.json`, cap 50.
- Survive `create_app()` restart (file, not process memory only).
- Reuse `desktop_mode_enabled()` from `origins.py`. Do not fork a second env parser.
- Registry is **not** inside `Settings`.
- Endpoints: `POST {"path"}` and `GET` list. 404 when `FRAMEPILOT_DESKTOP` is unset or not `"1"`.
- Never set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`, `/`, or a drive root in shipped desktop spawn.

**tests-first:** write `apps/api/tests/test_desktop_project_roots.py` first. Watch it fail for the right reason (routes missing / root still 422). Then implement.
- `test_create_project_rejects_root_outside_allowlist` still 422 with the same detail (**file body unchanged**). Run it twice.
- Outside root 422 until registered, then create succeeds.
- `/`, `/etc`, `C:\Windows`, data dir, relative path, file-not-dir → 422.
- Endpoints 404 when `FRAMEPILOT_DESKTOP` unset.
- Roots survive `create_app()` restart.
- Cap 50.

Run: new file + `apps/api/tests/test_projects_api.py::test_create_project_rejects_root_outside_allowlist`.

**commit-hint:** `api: register desktop project roots before use`

**github-submit:** commit (tick D2.00 only) → `git push -u origin HEAD` → append git-github.txt (PR #38).

**done-when:**
- Registered root is legal for `create_project`.
- Unregistered outside root still 422 with unchanged allowlist wording.
- Endpoints 404 unless desktop mode.
- JSON cap 50, survives app restart.
- §5.1 D2.00 `[x]` in the same commit. Pushed.

---

## D2.01 — Native file dialog adapters

**depends-on:** Phase 1 (done)

**files:**
- create: `apps/web/src/lib/nativeFs.ts` — `getNativeFs(): NativeFs | null` returns `null`
- create: `apps/desktop/src/lib/nativeFs.ts` — `pickDirectory()`, `pickImageFiles()`, `revealInFileManager()` via Tauri dialog + opener
- modify: `apps/desktop/vite.config.ts` — resolved-path alias like `navigation.next`
- modify: `apps/desktop/src-tauri/Cargo.toml`, `capabilities/default.json`, `lib.rs` plugin init
- modify: `apps/desktop/package.json` — `@tauri-apps/plugin-dialog` and opener
- test: `apps/web/src/lib/nativeFs.test.ts` (null without window and in browser). Desktop wrappers tested under `apps/desktop` with **mocked plugins**, not live dialogs. Do **not** import `@tauri-apps/plugin-*` from `apps/web`.

**implement:**
- Shared UI imports `@/lib/nativeFs` only.
- Vite aliases the **resolved file** `apps/web/src/lib/nativeFs.ts` → `apps/desktop/src/lib/nativeFs.ts`. Copy the navigation.next plugin; a string alias of `"./nativeFs"` will miss `@/lib/nativeFs`.
- Capabilities: **dialog + opener only**. No `fs:`. No `shell:`.
- Next / Playwright must never import `@tauri-apps/plugin-*`.

**tests-first:** write `nativeFs.test.ts` first (expect `null`). Then add the stub. Desktop wrappers: mock plugin modules only.
- `getNativeFs()` is `null` without `window` and when `__FRAMEPILOT_DESKTOP__` is not the desktop alias.
- `apps/web` source has no `@tauri-apps/plugin-*` import.
- Capabilities JSON has dialog + opener and no `fs:` / `shell:`.

Run: `npm run test:web` + `npm run typecheck:desktop`.

**commit-hint:** `desktop: add native file dialog adapters`

**github-submit:** commit (tick D2.01 only) → push → git-github.txt (PR #38).

**done-when:**
- Web stub is null; desktop Vite swap is resolved-path.
- Dialog + opener plugins registered. No fs/shell.
- Tests green. §5.1 D2.01 `[x]`. Pushed.

---

## D2.02 — Project create with native picker

**depends-on:** D2.00, D2.01 (must already be committed and pushed)

**files:**
- modify: `apps/web/src/lib/api.ts` `createProject` — optional `acknowledgeNonempty`
- modify: `apps/web/src/lib/projectCreation.ts` — `acknowledgeNonempty` only after confirmation
- modify: `ProjectCreator.tsx` — if `getNativeFs()`, Browse fills `root_path` after register; surface 422 verbatim
- test: `projectCreation.test.ts`; API tests for registered nonempty root without/with the flag; existing files still present

**implement:**
- Confirm copy **exactly**: `This folder already contains files. FramePilot will create its project folders inside it and will not modify existing files. Continue?`
- Browser text field stays; no acknowledge flag unless the user confirmed.
- Flow: pick → `POST /api/desktop/project-roots` → create with `root_path`.

**tests-first:** extend `projectCreation.test.ts` first.
- `acknowledgeNonempty` only after confirmation.
- Registered nonempty root 422 without flag, 201 with flag; existing files remain.

Run: `npm run test:web` + the API nonempty-root cases.

**commit-hint:** `web: use native directory picker when desktop APIs exist`

**github-submit:** commit (tick D2.02 only) → push → git-github.txt (PR #38).

**done-when:**
- Native picker path registers then creates.
- Confirm copy exact; 422 surfaced verbatim.
- Browser text field unchanged when `getNativeFs()` is null.
- §5.1 D2.02 `[x]`. Pushed.

---

## D2.03 — Import panel path import

**depends-on:** D0.04b (done), D2.01

**files:**
- modify: `apps/web/src/lib/api.ts` — `importPhotosFromPaths` looping `remaining_paths` with the same `job_id`
- modify: `apps/web/src/lib/importWorkflow.ts` — progress uses `expanded_total`
- modify: `ImportPanel.tsx` — desktop: pick folder/files → path import. Browser: existing multipart
- test: `importWorkflow.test.ts` remaining-paths loop

**implement:**
- One HTTP request consumes at most 100 expanded files. Client loops. `finalize: true` only on the last slice.
- **Invariant:** `isDesktopShell() === false` keeps both `<input type="file">` elements (files at 234–241, folder at 253–261 including `webkitdirectory`) at current DOM position, labels, and disabled semantics.

**tests-first:** remaining-paths loop test that drives the shipped client helper (max 100, `finalize` last only). Then wire ImportPanel.
- Browser inputs still present in source when not desktop.

Run: `npm run test:web`. (`npm run test:e2e` before Phase 2 close.)

**commit-hint:** `web: import from local paths in desktop mode`

**github-submit:** commit (tick D2.03 only) → push → git-github.txt (PR #38).

**done-when:**
- Desktop import uses `from-paths` loop.
- Browser multipart + both file inputs unchanged when not desktop.
- §5.1 D2.03 `[x]`. Pushed.

---

## D2.04 — Drag and drop

**depends-on:** D2.03

**files:**
- modify: `ImportPanel.tsx`; Tauri drag-drop if HTML5 drop has no filesystem paths
- test: `collectDroppedPaths(event)` unit test (shipped function)

**implement:**
- Dropped paths feed `from-paths` only.
- Overlay `pointer-events: none` unless a drag is active (Playwright file inputs must stay clickable).
- Do not start import on drop outside the import page.

**tests-first:** write `collectDroppedPaths` tests first.

Run: `npm run test:web`.

**commit-hint:** `desktop: add import drag-and-drop`

**github-submit:** commit (tick D2.04 only) → push → git-github.txt (PR #38).

**done-when:**
- Drop on import page feeds path import.
- Overlay does not block Playwright when idle.
- §5.1 D2.04 `[x]`. Pushed. Live GUI drop may stay `[~]` until 上线 if this host has no WebView.

---

## D2.05 — Reveal project / export folders

**depends-on:** D2.01

**files:**
- modify: `ProjectDashboard.tsx`, `ExportPanel.tsx`
- test: helper that the reveal callback is invoked with `output_path`

**implement:**
- Buttons: “Open project folder”, “Open export folder” via `revealInFileManager(output_path | root_path)`.
- Folder export already returns `output_path`.

**tests-first:** reveal-callback helper test driving shipped wiring.

Run: `npm run test:web`.

**commit-hint:** `desktop: reveal project and export paths in the OS file manager`

**github-submit:** commit (tick D2.05 only) → push → git-github.txt (PR #38).

**done-when:**
- Reveal callback receives `output_path` / `root_path`.
- §5.1 D2.05 `[x]`. Pushed. Live OS file manager click may stay `[~]` on this host.

---

## D2.06 — Recent projects

**depends-on:** D1.05 (done)

**files:**
- create: `apps/web/src/lib/recentProjects.ts` (localStorage last-opened id)
- modify: `ProjectList.tsx` (and dashboard open path) to record last opened
- test: `recentProjects.test.ts` or `.test.tsx`

**implement:**
- Last-opened project id in `localStorage`.
- `GET /api/projects` remains the list. Do not invent a second database.

**tests-first:** write `recentProjects.test.ts` first, drive the shipped helper.

Run: `npm run test:web`.

**commit-hint:** `desktop: remember last opened project`

**github-submit:** commit (tick D2.06 only) → push → git-github.txt (PR #38).

**done-when:**
- Helper reads/writes last-opened id.
- List endpoint unchanged.
- §5.1 D2.06 `[x]`. Pushed.

---

## D2.07 — Cross-platform path hardening

**depends-on:** D0.04a (done)

**files:**
- modify: `importing.py`, `projects.py`, D2.00 registry if needed
- test: path-hardening pytest

**implement / test:**
- Windows drive letters, spaces, non-ASCII, trailing separators, reject NUL.
- Keep `os.pathsep` allowlist parsing.
- Skip live Win32-only cases on POSIX.

**tests-first:** write the pytest first (fail on NUL / trailing sep if unimplemented). Drive shipped path helpers, not a re-implementation.

Run: `npm run test:api`.

**commit-hint:** `api: harden desktop import paths`

**github-submit:** commit (tick D2.07 only) → push → git-github.txt (PR #38).

**done-when:**
- Hardening tests green. Allowlist `os.pathsep` still works.
- §5.1 D2.07 `[x]`. Pushed.

---

## D2.08 — Full workflow verification

**depends-on:** D2.03, D2.05

**files:**
- create: `tests/desktop/workflow.md` (manual GUI checklist: pick folder, cull with keyboard, export, reveal)
- create: pytest using `from-paths` then process + Pick + CSV/ZIP/folder export + source `st_size` / mtime / hash unchanged

**implement:**
- Automated: create project, import synthetic JPEGs via `from-paths`, process, mark Pick, CSV/ZIP/folder export, originals unchanged.
- Keep `test_import_from_paths_immutability.py` green.

**tests-first:** write the pytest first against shipped `from-paths` + process + export. Run it twice.

Run: `npm run test:api`; `npm run test:e2e` if ImportPanel changed (required before Phase 2 close).

**commit-hint:** `test: cover path-import process export workflow`

**github-submit:** commit (tick D2.08 only) → push → git-github.txt (PR #38).

**done-when:**
- Pytest green twice. Sources unmodified.
- Manual checklist exists for GUI.
- §5.1 D2.08 `[x]`. Pushed.

---

## D2.09 — Reveal instead of download on desktop

**depends-on:** D2.01, D2.05

**files:**
- modify: `ExportPanel.tsx` (`<a>` at live 241 and 308)
- modify: `ImportExportPanels.test.tsx` — success-path harness (do not keep error-only mock as the only proof)

**implement:**
- Branch on `isDesktopShell()`. Flag unset → current href. Flag true → reveal button, **no** `<a download>` / `exportDownloadUrl` anchor.
- If macOS WKWebView blocks loopback HTTP images, record it in feasibility notes — do **not** redesign the asset pipeline here.

**tests-first:** desktop vs browser render of real `ExportPanel`. Mock query data / `getNativeFs` / shell flag, **not** the panel.

Run: `npm run test:web`.

Then write/update `docs/handoff/STATUS.md` `current_stage=开发`, `status=complete`, `next_stage=测试`. A small `docs: record Phase 2 development stage` commit is allowed if STATUS would otherwise be uncommitted, then push that too.

**commit-hint:** `desktop: reveal export artifacts instead of downloading them`

**github-submit:** commit (tick D2.09 only) → push → git-github.txt (PR #38).

**done-when:**
- Desktop reveal, browser download anchors.
- Tests both branches. §5.1 D2.09 `[x]`. Pushed. 开发 complete.

---

## 测试 / 上线 (after 开发)

**测试 commit-hint:** `test: verify desktop Phase 2 behavior`  
Commands: `npm run test:api`; `npm run typecheck && npm run test:web`; `npm run typecheck:desktop` (+ desktop build if possible); rust-free `npm run verify`; `npm run test:e2e`; re-run D2.08 pytest and unchanged allowlist test. Logs under `$HOME/.cache/framepilot-desktop-phase2` and `{SCRATCH}`. Push.

**上线 commit-hint:** `docs: record Phase 2 close-out and tick desktop tracker`  
Confirm every Phase 2 id `[x]` or dated `[~]` (live picker/drag clicks only). Do not merge. Ready-for-review allowed. `next_stage=none` (Phase 3 not started). Push.
