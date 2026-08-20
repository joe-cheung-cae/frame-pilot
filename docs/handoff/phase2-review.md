# Desktop Phase 2 Requirements Review

Handoff stage: `评审`  
Date: 2026-08-20T21:05:00+08:00  
Branch: `feature/desktop-phase2`  
Reviewed: `docs/handoff/phase2-requirements.md` (`9e5416a`) against the live `2.0.0-rc2` tree on `feature/desktop-phase2`  
Sources: `docs/plans/2026-08-18-desktop-packaging.md` D2.00–D2.09 and §5.1, `docs/plans/2026-08-18-desktop-packaging-review.md` **A2.3**, `AGENTS.md`, live files named in the breakdown  
Draft PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (do not merge)

**Verdict: accept-with-notes**

The breakdown is a safe Phase 2 contract. It fences **D2.00–D2.09** only, keeps `apps/web` on Next.js, does not start Phases 3–5, does not bump `APP_VERSION`, and already folds the Phase 2 trap **A2.3** (native picker vs allowlist + nonempty ack) into D2.00 first. GitHub protocol (one draft PR, push after every id) is present. It is not rejected.

归档 must fold the notes below into `docs/handoff/phase2-backlog.md` before 开发. Highest notes: reuse `desktop_mode_enabled()`, never put the registry in `Settings`, resolved-path Vite alias for `nativeFs`, keep Tauri plugins out of `apps/web` test collection, and do not mock `ExportPanel` itself when proving reveal vs download.

No production code, tests, or build scripts were changed in this stage. §5.1 Phase 2 boxes stay `[ ]`.

---

## 1. Live-tree facts (verified 2026-08-20T21:05:00+08:00)

| Claim in the breakdown | Live tree |
|------------------------|-----------|
| `APP_VERSION` is `2.0.0-rc2` | Confirmed `apps/api/app/core/version.py`, `apps/desktop/package.json`, `Cargo.toml` |
| Allowed roots = data-dir projects + env allowlist only | `projects.py:30-37`. Error string contains `allowlisted` |
| `test_create_project_rejects_root_outside_allowlist` | `test_projects_api.py:119-129`. Asserts 422 and `"allowlisted"` in `detail`. **Do not change** |
| `acknowledge_nonempty` on API, not on web client | Schema `api.py:9`; `routes.py:284`; `api.createProject` posts `{name, root_path?}` only |
| `ProjectCreator` is a typed text field | `ProjectCreator.tsx` name + root path inputs; no Browse, no confirm |
| Path import endpoint + 100 cap | `POST /imports/from-paths`; `IMPORT_MAX_FILES_PER_REQUEST = 100`; `remaining_paths` / `expanded_total` in `ImportResult` |
| Client path-import loop missing | `api.ts` has multipart `importPhotos` / `importPhotosBatch` only |
| ImportPanel browser inputs | Files `234-241`; folder `253-261` with `webkitdirectory` at 260 |
| No `nativeFs` | No `apps/web/src/lib/nativeFs.ts`. No `apps/desktop/src/lib/` |
| No dialog/opener plugins | `Cargo.toml`: window-state + single-instance only. `package.json` desktop: no `@tauri-apps/plugin-*`. Capabilities: `core:default`, window show/unminimize/set-focus, `window-state:default`. **No `fs:` / `shell:`** |
| Vite alias | Resolved-path plugin for `navigation.next` only. `"@"` → `apps/web/src` |
| Export download anchors | `ExportPanel.tsx` 241 and 308 `href={exportDownloadUrl(...)}`. Folder not downloadable |
| Dashboard prints `root_path` | `ProjectDashboard.tsx:62`. No reveal |
| Project list | `ProjectList` `queryFn: api.listProjects`. Newest-first on API |
| `isDesktopShell()` | Literal `window.__FRAMEPILOT_DESKTOP__ === true` only |
| Sidecar already sets desktop env | `sidecar.rs` `.env("FRAMEPILOT_DESKTOP", "1")` and injects `__FRAMEPILOT_DESKTOP__ = true` |
| `desktop_mode_enabled()` | `origins.py:27-29` — `FRAMEPILOT_DESKTOP == "1"`. Reuse for D2.00 404 |
| Settings is lru_cache; mutation resets DB | `config.py` `get_settings` `@lru_cache`; `reset_settings_cache()` also `reset_engine_cache()`. Registry **must not** live in Settings |
| `create_app()` resets settings every call | `main.py:41`. File-backed roots survive; a process-memory-only registry would not |
| `npm run verify` | Root `lint && typecheck && typecheck:desktop && test && check:artifacts`. No rustc/cargo/tauri |
| Web tests | `node --test src/lib/*.test.ts && vitest run`. `nativeFs.test.ts` in `apps/web/src/lib/` **is** collected. A file that imports `@tauri-apps/plugin-*` under that glob would put Tauri in Next |
| `ImportExportPanels.test.tsx` | Only load-error cases. `useQuery` mocked to `isError: true`. Cannot prove download vs reveal without a success-path harness |
| CI | `verify.yml` `pull_request` + push `main` / `feature/desktop-packaging` / `refactor`. Draft PR #38 is what runs CI |
| `next.config.ts` | No `output: 'export'` |
| Apps/web `@tauri-apps/plugin-*` | **Zero** matches |
| Draft PR | One open draft: #38, title exact, base `main`, head `feature/desktop-phase2` |

---

## 2. Adversarial checks (required)

| Fence | Result |
|-------|--------|
| D2.00 vs `$HOME` allowlist | Pass in contract. Tauri must never set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`, `/`, or a drive root. User roots legal only after `POST /api/desktop/project-roots` |
| Registry not in Settings | Pass in contract. Required: `{data_dir}/desktop_project_roots.json`, cap 50. Mutating Settings would reset the DB engine |
| 404 unless `FRAMEPILOT_DESKTOP=1` | Pass in contract. 归档: call existing `desktop_mode_enabled()`, do not invent a second env helper. `"1"` string only |
| Unchanged allowlist test | Pass. 开发 must not edit `test_projects_api.py::test_create_project_rejects_root_outside_allowlist` body or the `allowlisted` error string in `projects.py` |
| nativeFs Vite resolved-path alias | Pass in contract. Copy `aliasNavigationNext` / resolved file path. A find of `"./nativeFs"` will miss `@/lib/nativeFs` |
| No Tauri in Next | Pass today. 归档: web stub returns `null`; desktop impl only under `apps/desktop`; no plugin import in `apps/web` |
| Browser file-input invariant | Pass in contract. Both inputs stay when `isDesktopShell()` is false (DOM position, labels, disabled semantics) |
| `remaining_paths` loop of 100 | API already slices. Client must loop same `job_id`, `finalize: true` only on last slice. Never one HTTP call for 2000 files |
| Drag overlay `pointer-events` | Pass in contract. `none` unless a drag is active so Playwright clicks still work |
| Reveal instead of download | Desktop `isDesktopShell() === true` → reveal `output_path`, no `<a download>` / `exportDownloadUrl`. Browser keeps current href |
| No `fs:` / `shell:` capabilities | Pass today. Add **dialog + opener only** |
| GitHub push-per-task + one draft PR | Pass. PR #38 exists. Later stages only push. Do not open a second PR. Do not merge |

---

## 3. Findings

### H1 — A2.3: picker cannot create a project until D2.00 (high)

**Why.** `create_project` still rejects any root outside `{data_dir}/projects` or the env allowlist (`projects.py:33-37`). A native directory picker returns an arbitrary user folder. Widening `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME` voids the control. Nonempty folders also 422 without `acknowledge_nonempty`.

**Required for 归档/开发.** D2.00 first. Persist registered roots in `{data_dir}/desktop_project_roots.json` (cap 50). `create_project` allowed roots = `[projects_root, *allowlist, *registered_roots()]`. D2.02 flow: pick → register → confirm if nonempty → `POST /api/projects` with `acknowledge_nonempty` only after the exact English confirm copy. Do not set the env allowlist in the Tauri spawn.

### H2 — Do not put the registry in Settings (high)

**Why.** `get_settings` is `@lru_cache`. `reset_settings_cache()` clears the cache **and** `reset_engine_cache()`. `create_app()` calls that on every construction. A Settings-backed registry would reset the DB engine and would not be the right persistence.

**Required.** File-backed JSON only. Re-read (or a dedicated cache that is **not** Settings) on register/list/`create_project`. Survive `create_app()` restart because the file exists, not because a process list survived.

### H3 — `nativeFs` tests must not import Tauri under `apps/web/src/lib/*.test.ts` (high)

**Why.** `npm run test:web` runs `node --test src/lib/*.test.ts`. Any test next to the web stub that imports `@tauri-apps/plugin-dialog` pulls Tauri into the Next/Node test graph.

**Required.** `apps/web/src/lib/nativeFs.test.ts` covers `getNativeFs() === null` without window and in browser. Desktop wrapper tests live under `apps/desktop` (mocked plugins only). Vite aliases the **resolved path** of `apps/web/src/lib/nativeFs.ts` → `apps/desktop/src/lib/nativeFs.ts`, same plugin style as `navigation.next`.

### H4 — D2.09 tests cannot reuse the current error-only ExportPanel harness as-is (medium)

**Why.** `ImportExportPanels.test.tsx` mocks `useQuery` to `isError: true` and never renders download anchors. A test that only inspects source text is not enough; a test that mocks `ExportPanel` is theater.

**Required.** Add a success-path render (real `ExportPanel`, mock **data** / `getNativeFs` / `isDesktopShell` — not the panel). Flag unset → `href` uses `exportDownloadUrl`. `__FRAMEPILOT_DESKTOP__ === true` → reveal control with `output_path`, no download anchor.

### N1 — Reuse `desktop_mode_enabled()`

Do not fork a second `FRAMEPILOT_DESKTOP` parser. 404 when it is false. `"1"` only; `"true"` / `1` stay off (matches `isDesktopShell`).

### N2 — Reject data dir and its parents, not only `/`

`BLOCKED_ROOT_NAMES` does not include the app data dir. `register_root` must still 422 the data dir, parents of the data dir, `/`, `/etc`, `C:\Windows`, relative paths, and file-not-dir. `C:\Windows` may be skipped as a live filesystem on POSIX; the validator still rejects the path string / resolved Windows form.

### N3 — Drag-and-drop only on the import page

Do not attach a global Tauri drop handler that starts import from dashboard/cull/export. Overlay `pointer-events: none` unless a drag is active.

### N4 — GitHub / orchestration

One draft PR already exists (#38). 归档 and 开发 only push. The named workflow run `desktop-phase2` paused after a 0-token 需求拆解 agent; do not resume it (`pause()` re-fires). Continue serial parent/subagents with the same fences.

---

## 4. Required test list (fold into 归档)

| ID | Write first | Drive shipped code | Command |
|----|-------------|--------------------|---------|
| D2.00 | `apps/api/tests/test_desktop_project_roots.py` + fixture `clear_registered_roots()` | Register/list endpoints, `create_project` after register, 404 when desktop unset | New file + **unchanged** `test_create_project_rejects_root_outside_allowlist` (twice) |
| D2.01 | `apps/web/src/lib/nativeFs.test.ts` | `getNativeFs()` null without window and in browser | `npm run test:web` + `npm run typecheck:desktop` |
| D2.02 | extend `projectCreation.test.ts` | `acknowledgeNonempty` only after exact confirm copy | `npm run test:web` + API nonempty registered root without/with flag |
| D2.03 | extend `importWorkflow.test.ts` / `api` path-import helper | Client loops `remaining_paths`, max 100, `finalize` last slice only | `npm run test:web` |
| D2.04 | `collectDroppedPaths(event)` unit test | Dropped paths feed from-paths; overlay pointer-events | `npm run test:web` |
| D2.05 | reveal-callback helper | Callback invoked with `output_path` / `root_path` | `npm run test:web` |
| D2.06 | `recentProjects.test.ts` | last-opened id in `localStorage`; list still `GET /api/projects` | `npm run test:web` |
| D2.07 | path-hardening pytest | Drive letters, spaces, non-ASCII, trailing sep, reject NUL; `os.pathsep` allowlist | `npm run test:api` |
| D2.08 | path-import → process → Pick → CSV/ZIP/folder pytest + `tests/desktop/workflow.md` | Synthetic JPEGs; source `st_size` / mtime / hash unchanged | `npm run test:api`; `npm run test:e2e` before close |
| D2.09 | `ImportExportPanels.test.tsx` desktop vs browser | Real panel; desktop reveal, browser href | `npm run test:web` |

Keep `test_import_from_paths_immutability.py` and export path-escape tests green. Do not mock the unit under test. Do not invent HTTP bodies if a live sidecar launch fails.

---

## 5. Out of scope (do not reopen)

- Phase 0/1 redo, Electron, Next migration, `output: 'export'`, Rust scoring
- `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME` / `/` / drive root
- Removing browser ImportPanel file inputs
- `fs:` / `shell:` capabilities
- Widening `scripts/check-release-artifacts.sh`
- Version bump to `2.1.0-desktop`, installers, menus, merge to `main`
- Phase 3–5
