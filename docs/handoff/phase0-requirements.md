# Desktop Phase 0 Requirements Breakdown

Handoff stage: `需求拆解`  
Date: 2026-08-19  
Branch for this pipeline: `refactor` (not `feature/desktop-packaging`)  
Scope fence: **desktop packaging Phase 0 only** — task ids **D0.00–D0.09** from `docs/plans/2026-08-18-desktop-packaging.md`.

This document is the implementation contract for later stages (`评审` → `归档` → `开发` → `测试` → `上线`). It does not implement production code.

**Not this document:**

- `implement_goals.md` Phase 0 (“Safety and repository baseline” for the older v2 web Goal Mode)
- Desktop Phases 1–5 (D1.01–D5.05): navigation adapter, Vite SPA, native FS, menus, installers, version bump to `2.1.0-desktop`

**Sources of truth (read in this order when implementing):**

1. `AGENTS.md` + `develop_plan.md` (local-first, original-file safety, English, tests)
2. `docs/plans/2026-08-18-desktop-packaging.md` (technical decisions, files, tests, commit messages; wins on technical conflict)
3. `docs/desktop_development_plan.md` (product why / 2.1.0-desktop DoD)
4. `docs/plans/2026-08-18-desktop-packaging-review.md` (defects already folded into the refined backlog)
5. This file (phase-bounded contract for the `refactor` pipeline)
6. `docs/desktop_goal_mode.md` (loop rules; tracker still lives in the implementation plan §5.1)

Conflict rule from the implementation plan: on any technical conflict that plan wins, and the product plan must be edited in the same commit that resolves the conflict. The product plan never introduces a new task id.

---

## 1. Goal

Prove that FramePilot `2.0.0-rc2` can be hosted as a localhost-only Python sidecar and that the APIs a Tauri 2 shell cannot live without exist, without shipping the desktop UI, installers, or a version bump.

Phase 0 must leave the tree able to:

- Run `npm run verify` in GitHub Actions without installing Rust or Playwright.
- Start a sidecar CLI on `127.0.0.1` with a required absolute `--data-dir`, a machine-readable ready line, and a real bound port (including `--port 0`).
- Answer `/health` and `/api/health` with `status`, `version`, and `service`.
- Allow current browser origins always, add Tauri origins only when `FRAMEPILOT_DESKTOP=1`, and reject non-loopback `Host` headers on every method.
- Import from absolute local paths in chunks of at most 100 expanded files, without mutating source files.
- Build a PyInstaller one-dir sidecar (or record why the smoke is blocked) and keep `npm run verify` green when Tauri PNG icons are later added.
- Record a Next.js `output: 'export'` spike as documentation only, then revert any Next config that would break the web app.
- Add a minimal Tauri hello **if** this host can compile and open a WebView; otherwise keep a verify-safe skeleton and mark D0.07 `[~]`.
- Write baselines and a go/no-go. Final tracker ticks and the written go/no-go are owned by the `上线` stage.

Product baseline today (verified against the live tree on `refactor`):

| Area | Live state | Phase 0 implication |
|------|------------|---------------------|
| Version | `2.0.0-rc2` in root/`apps/web`/`apps/api` and `FastAPI(version="2.0.0-rc2")` | Single source `apps/api/app/core/version.py` in D0.02; do not bump to `2.1.0-desktop` |
| CI | No `.github/` tree | D0.00 creates verify workflow first |
| Sidecar | None; `create_app()` runs at import (`apps/api/app/main.py:76`) | `--data-dir` must be set **before** `import app.main` |
| Health | `GET /health` and `GET /api/health` → `{"status": "ok"}`; pytest exact-equality at `test_projects_api.py:19` | Keep `status: "ok"` (Playwright only waits on `http://127.0.0.1:8000/health`); add `version` + `service` |
| Origins | Four web origins on `:3000` / `:3100`; mutation methods only; no Host check | Desktop origins 403 today; GET assets are open to DNS rebinding |
| Import | Multipart only; `IMPORT_MAX_FILES_PER_REQUEST = 100` | Path import must expand then chunk; never one HTTP call for 2000 files |
| `ImportResult` | No `remaining_paths` / `expanded_total` | Add both; browser multipart stays compatible (`remaining_paths: []`) |
| Project roots | `{data_dir}/projects` or `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST`; nonempty dirs need `acknowledge_nonempty` | D2.00 is **out of Phase 0**. Do not set the allowlist to `$HOME` |
| Artifact check | `scripts/check-release-artifacts.sh` blocks every tracked `*.png` | D0.07a exception **before** any Tauri icon commit |
| Frontend | Next.js 15 App Router; five `projects/[projectId]/...` routes have no `generateStaticParams` | D0.06 is docs-only; do not migrate `apps/web` |
| Desktop app | No `apps/desktop/`, no `packaging/` | Greenfield, verify-safe |
| `npm run verify` | `lint` + `typecheck` + `test` + `check:artifacts`; no Rust | Must stay free of rustc/cargo/Tauri |

---

## 2. Locked decisions

These are binding for Phase 0. Do not re-litigate them unless D0.09 writes a go/no-go change in `docs/desktop_feasibility_notes.md`.

1. **Shell:** Tauri 2 + Python sidecar. Electron only if D0.09 records that Tauri cannot spawn the sidecar or the WebView cannot reach loopback.
2. **Backend packaging:** PyInstaller **one-dir** named `framepilot-api` (not one-file). numpy / scipy / Pillow load poorly from one-file extracts.
3. **Frontend:** Dual shell, single component library. `apps/web` stays Next.js for browser + Playwright. `apps/desktop` is a future Vite SPA (Phase 1). Phase 0 must not migrate `apps/web` off Next.js.
4. **IPC:** HTTP to `127.0.0.1` only. No rewrite of scoring / grouping onto Rust.
5. **Bind:** Sidecar listens on `127.0.0.1` only. Never `0.0.0.0`. Exit code 2 if `--host` is not `127.0.0.1` or `localhost`.
6. **Port:** Tauri (later) allocates a free loopback port and always passes `--port <n>`. Sidecar also supports `--port 0` for tests: bind first, `getsockname()`, print the ready line, then serve. Never guess or re-report port 0.
7. **Data dir:** `--data-dir` / `FRAMEPILOT_DATA_DIR` is **required** and must be absolute. Never fall back to CWD-relative `.framepilot-data`. Set the env var **before** the first `import app.main`.
8. **Ready line:** exactly one stdout line after bind and before serve, `flush=True`:
   `FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>`
   `<actual>` comes from `getsockname()`. All logs go to stderr. Pass the FastAPI **object** to uvicorn, not the string `"app.main:app"`.
9. **Safety:** Copy-mode storage unchanged. Originals are copied into the project; sources are never modified or deleted.
10. **Web app must keep working.** `npm run dev`, `npm run verify`, and Playwright file inputs in `ImportPanel.tsx` stay green. `npm run verify` must not install or require Rust/Tauri.
11. **Project roots:** `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` stays a deployment-level control and must **never** be set to `$HOME`, `/`, a drive root, or any broad parent. Custom desktop roots are D2.00, not Phase 0. `test_create_project_rejects_root_outside_allowlist` must stay green **unchanged**.
12. **Path import request shape:** one HTTP request consumes at most `IMPORT_MAX_FILES_PER_REQUEST` (100) expanded files and returns `remaining_paths` plus `expanded_total`. The client loops with the same `job_id`. A folder of 2000 photos is never one HTTP call.
13. **GUI-blocked tasks:** if remaining verification needs a real WebView or rustc/cargo and this host cannot provide them, mark `[~]`, append a dated command + error to `docs/desktop_feasibility_notes.md`, and continue. `[~]` is never `[x]` without a recorded GUI/toolchain run.
14. **Single version source:** `apps/api/app/core/version.py` defines `APP_VERSION = "2.0.0-rc2"`. `main.py` and both health endpoints read it. No extra version literals in `main.py`, `routes.py`, or tests. Do not bump `pyproject.toml` / `package.json` versions in Phase 0.
15. **Artifact check:** widen `scripts/check-release-artifacts.sh` by exactly one exception:

    `allowed_pattern='^apps/desktop/src-tauri/icons/[^/]+\.(png|ico|icns)$'`

    Do not broaden `blocked_pattern`. Do not add any other exception.
16. **This pipeline’s branch:** land on `refactor`. Do not checkout `feature/desktop-packaging`, do not push, do not open a PR. D0.00 must therefore trigger on `push` to `main`, `feature/desktop-packaging`, **and `refactor`**, plus `pull_request` (the refined develop prompt; the original plan omitted `refactor` because it assumed a different branch).
17. **No cloud, login, payment, bundled models, HEIC/RAW/XMP.** HEIC/RAW remain skipped with the existing unsupported-format reasons.
18. **Tracker:** `docs/plans/2026-08-18-desktop-packaging.md` §5.1 remains the status source of truth. `开发` may make extra per-task commits. Final Phase 0 ticks and go/no-go are owned by `上线`. Do not start D1–D5.

---

## 3. In-scope ids

Implement **only** these ids, in dependency order. Session rule from the plan: one id at a time, tests first, then implementation. This pipeline allows extra per-task commits during `开发` and requires a final `开发` stage commit.

Suggested serial order (lowest incomplete id whose dependencies are done):

| ID | Title | Depends on |
|----|-------|------------|
| D0.00 | CI verify workflow | none — do this first |
| D0.01 | Sidecar CLI launcher | none |
| D0.02 | Health payload with version | D0.01 |
| D0.03 | Origin and Host policy | none (can follow D0.01/D0.02) |
| D0.04a | Import path expansion helper | none |
| D0.04b | Path-based import endpoint | D0.04a |
| D0.04c | Path import immutability tests | D0.04b |
| D0.05 | PyInstaller spec and sidecar smoke | D0.01, D0.02 |
| D0.06 | Next static export spike (docs) | none |
| D0.07a | Tauri artifact/gitignore hygiene | D0.00 |
| D0.07 | Minimal Tauri shell with sidecar health | D0.01, D0.03, D0.05, D0.07a |
| D0.08 | Baselines | D0.05, D0.07 |
| D0.09 | Go / no-go | D0.06, D0.08 |

Current §5.1 Phase 0 boxes (all `[ ]` as of this breakdown):

- [ ] D0.00 CI verify workflow
- [ ] D0.01 Sidecar CLI launcher
- [ ] D0.02 Health payload with version
- [ ] D0.03 Origin and Host policy
- [ ] D0.04a Import path expansion helper
- [ ] D0.04b Path-based import endpoint
- [ ] D0.04c Path import immutability tests
- [ ] D0.05 PyInstaller spec and sidecar smoke
- [ ] D0.06 Next static export spike (docs)
- [ ] D0.07a Tauri artifact/gitignore hygiene
- [ ] D0.07 Minimal Tauri shell with sidecar health
- [ ] D0.08 Baselines
- [ ] D0.09 Go / no-go

Do not tick a box in this documentation stage.

---

## 4. Out of scope

Explicitly **not** Phase 0:

- **`implement_goals.md` Phase 0** (v2 web “Safety and repository baseline”). Do not redo install/script baseline work unless a desktop task cannot run without `npm run install:all`.
- **Desktop Phase 1:** D1.01 navigation adapter, D1.02 runtime API base, D1.02a shell flag, D1.03a/b Vite + router, D1.04–D1.09 sidecar lifecycle in Rust, window state, `dev:desktop` verify wiring, graceful quit.
- **Desktop Phase 2:** D2.00 registered project roots, native pickers, drag-drop, reveal-in-folder, recent projects, full workflow E2E.
- **Desktop Phase 3:** native menus, status bar, settings `GET /api/meta`, system theme, tray.
- **Desktop Phase 4:** bundling sidecar into Tauri resources, NSIS/DMG, desktop CI matrix, signing. D4.03 is already moved to D0.00 (`[-]`); do not implement it twice.
- **Desktop Phase 5:** test matrix, user docs, performance notes, **version bump to `2.1.0-desktop`**, known-limitations closeout.
- Detached preview window, concurrency/cache knobs, auto-update (all deferred to 2.2).
- Setting `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME` as a shortcut for native pickers.
- Migrating `apps/web` off Next.js or deleting the two `ImportPanel.tsx` file inputs.
- Replacing scoring/grouping with Rust.
- HEIC / RAW / XMP / bundled neural models / cloud / login / payment.
- Installing a system Rust toolchain when rustc/cargo are missing (unless rustup is already present and unused).
- Making `npm run verify` require Rust, Tauri, or Playwright.
- Pushing, opening a PR, or switching off `refactor`.
- Publishing installers.

---

## 5. Files to create / modify

### D0.00 — CI verify workflow

- **Create:** `.github/workflows/verify.yml`
- Triggers: `pull_request`, and `push` to `main`, `feature/desktop-packaging`, **and `refactor`**.
- Single job `ubuntu-latest`: checkout, Python 3.11, Node 22, `npm run install:all`, `npm run verify`.
- Do not install Rust. Do not run Playwright. Concurrency group per ref with `cancel-in-progress: true`.

### D0.01 — Sidecar CLI launcher

- **Create:** `apps/api/app/sidecar_main.py`
- **Create:** `docs/desktop_feasibility_notes.md` (stub: Blockers + Baselines) if missing
- **Modify:** `apps/api/pyproject.toml` — add `[project.scripts] framepilot-api = "app.sidecar_main:main"`
- **Test:** `apps/api/tests/test_sidecar_cli.py`
- argparse: `--host` (default `127.0.0.1`), `--port` (default `8000`, `0` = ephemeral), `--data-dir` (**required**, absolute), `--log-level` (default `info`).
- Exit 2 if host is not loopback or `--data-dir` is missing/relative.
- POSIX: set `SO_REUSEADDR` on the listen socket. Do **not** set it on Windows (port hijacking).
- `uvicorn.Server(config).run(sockets=[sock])` with the FastAPI object.

### D0.02 — Health payload

- **Create:** `apps/api/app/core/version.py` (`APP_VERSION = "2.0.0-rc2"`)
- **Modify:** `apps/api/app/main.py` (`FastAPI(version=APP_VERSION)`, `/health`)
- **Modify:** `apps/api/app/api/routes.py` (`/api/health`)
- **Modify:** `docs/api.md`
- **Test:** `apps/api/tests/test_projects_api.py` (replace exact `== {"status": "ok"}`)

Both health endpoints return:

```json
{"status": "ok", "version": "2.0.0-rc2", "service": "framepilot-api"}
```

`version` is `APP_VERSION`. Keep `status` as `"ok"`.

### D0.03 — Origin and Host policy

- **Create:** `apps/api/app/core/origins.py`
- **Modify:** `apps/api/app/main.py` (allowlist, CORS, mutation guard, Host check)
- **Test:** `apps/api/tests/test_desktop_origins.py`

`allowed_origins()` always includes the current four web origins (`http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3100`, `http://127.0.0.1:3100`). When `FRAMEPILOT_DESKTOP=1`, also:

- `http://localhost:1420`
- `http://127.0.0.1:1420`
- `http://tauri.localhost`
- `https://tauri.localhost`
- `tauri://localhost`

Compute the set **inside `create_app()`**. Feed both `CORSMiddleware` and the mutating-origin guard. `allow_credentials=True`; wildcard forbidden.

Host check on **all** methods: 403 unless hostname is `127.0.0.1`, `localhost`, `::1`, or `tauri.localhost`. Missing Host is rejected. Do not disable the origin guard globally.

### D0.04a — Path expansion helper (no HTTP)

- **Modify:** `apps/api/app/services/importing.py`
- **Test:** `apps/api/tests/test_import_path_expansion.py`

Add next to `IMPORT_MAX_FILES_PER_REQUEST`:

```python
PATH_IMPORT_MAX_INPUT_ENTRIES = 5000
PATH_IMPORT_MAX_EXPANDED_FILES = 20000
```

`expand_import_paths(paths, project_root) -> ExpandedImportPaths` with `files` and `skipped`.

Rules:

- `ValueError` for empty list, too many input entries, any non-absolute path, missing path, or expansion over the cap.
- Directories: `os.walk(followlinks=False)`; drop entries whose `resolve()` is not under the walked root.
- Regular files only (`stat.S_ISREG`). Skip FIFOs/devices.
- Extension filter reuses existing supported/unsupported helpers (HEIC/RAW skip reasons match upload).
- Skip sources under `project_root.resolve()` (`"Source is inside the project folder"`).
- Deduplicate by resolved path; sort for determinism.

### D0.04b — Path-based import endpoint

- **Modify:** `apps/api/app/schemas/api.py`, `apps/api/app/api/routes.py`
- **Test:** `apps/api/tests/test_import_from_paths.py`
- **Docs:** `docs/api.md`

```text
POST /api/projects/{project_id}/imports/from-paths
{"paths": ["/abs/folder", "/abs/file.jpg"], "job_id": null, "expected_total": null, "finalize": true}
```

- Expand; `ValueError` → 422.
- Consume at most 100 expanded files. Return `remaining_paths` + `expanded_total`. Client re-posts remainder with the same `job_id`; `finalize: true` only on the last slice.
- Reuse multipart control flow (active-import 409, stale-job, `expected_total`).
- Per file: `source.open("rb")` then existing `register_import_file`. Do not add a second copy path.
- Queue derivative job on the same `finalize` terms as multipart.
- When finalize, a single input directory was given, and `source_root_path` is empty, record it as read-only metadata. No rescan.
- Multipart `ImportResult` gains `remaining_paths: []` and `expanded_total`.

### D0.04c — Original-file immutability

- **Test:** `apps/api/tests/test_import_from_paths_immutability.py`
- No production change expected. If a test fails, fix the service, not the test.

### D0.05 — PyInstaller + sidecar smoke

- **Create:** `packaging/pyinstaller/framepilot-api.spec`, `packaging/pyinstaller/build.sh`, `packaging/pyinstaller/hooks/hook-app.py` if needed
- **Create:** `scripts/sidecar-smoke.sh` (not a pytest file under repo-root `tests/desktop/` — `npm run test:api` only collects `apps/api/tests`)
- **Modify:** root `package.json` (`packaging:sidecar`, `test:sidecar`)

Hiddenimports must include: `app.main`, `app.sidecar_main`, `uvicorn.loops.auto`, `uvicorn.protocols.http.auto`, `uvicorn.protocols.websockets.auto`, `uvicorn.lifespan.on`, `uvicorn.lifespan.off`, `httptools`, `sqlalchemy.dialects.sqlite`, `PIL.JpegImagePlugin`, `PIL.PngImagePlugin`, `PIL.WebPImagePlugin`, `imagehash`, `numpy`, and scipy submodules pulled by imagehash.

Smoke: tmp absolute `--data-dir`, `--port 0`, parse ready line, curl `/health` for `version`, SIGTERM, exit within 5s, no leftover children. Prefer the built binary if present, else `.venv/bin/python -m app.sidecar_main`. Do not commit `dist/` or `build/` (already gitignored).

### D0.06 — Next static export spike (docs only)

- **Modify:** `docs/desktop_feasibility_notes.md`
- Attempt `output: 'export'` in a **throwaway** change. Record whether `next build` succeeds, what happens to `projects/[projectId]` routes, and `useSearchParams` Suspense warnings. Revert any Next config that breaks `npm run test:web`. Locked follow-up is Vite SPA.

### D0.07a — Artifact / gitignore hygiene

- **Modify:** `scripts/check-release-artifacts.sh`, `.gitignore`
- **Test:** `scripts/test-release-checks.sh`
- `.gitignore`: add `target/` and `.framepilot-desktop-dev/`.

### D0.07 — Minimal Tauri 2 hello + sidecar spawn

- **Create:** `apps/desktop/**` skeleton plus `apps/desktop/src-tauri/icons/` (`32x32.png`, `128x128.png`, `128x128@2x.png`, `icon.icns`, `icon.ico`) **only after D0.07a**
- **Modify:** root `package.json` (`dev:desktop`) only if it does not make `verify` require Rust
- Locked CSP from the implementation plan (must include `img-src` for `http://127.0.0.1:*` because `assetUrl` returns absolute loopback URLs).
- If this host has no rustc/cargo or cannot open a WebView: keep a verify-safe skeleton, run sidecar smoke without GUI, mark `[~]` with dated command + error. Do not install a system Rust toolchain unless rustup is already present and unused.

### D0.08 — Baselines (docs)

- **Modify:** `docs/desktop_feasibility_notes.md`
- Record even if only the sidecar ran: dist size, RSS after `/health`, time to `/health`, Tauri hello RSS or “blocked on missing rustc/WebView”, scipy/pywavelets presence.

### D0.09 — Go / no-go (docs)

- **Modify:** `docs/desktop_feasibility_notes.md`
- Write: Shell stays Tauri 2 (or Electron only if Tauri cannot spawn sidecar / WebView cannot reach loopback). Frontend follow-up is Vite SPA. Keep imagehash/scipy unless unpacked sidecar **>250 MB**.
- `开发` may draft this; `上线` owns the final text and §5.1 ticks.

### Shared docs in this pipeline (already started)

- `docs/handoff/phase0-requirements.md` (this file)
- `docs/handoff/STATUS.md`
- `.grok/workflows/desktop-phase0.rhai` (pipeline definition; include in the breakdown commit if untracked)

---

## 6. Tests-first list

Write the failing test **before** the implementation. A test written after a green implementation does not count for import, export, scoring, status updates, or path validation.

| ID | Write first | Must assert | Run |
|----|-------------|-------------|-----|
| D0.00 | none (CI config) | Workflow exists; locally `npm run verify` before commit if the tree is otherwise unchanged | `npm run verify` |
| D0.01 | `apps/api/tests/test_sidecar_cli.py` | `parse_args` rejects `--host 0.0.0.0` and `--host 192.168.1.5` (exit 2); rejects missing or relative `--data-dir`; `bind_listen_socket("127.0.0.1", 0)` returns a socket whose port is non-zero and address is `127.0.0.1` (close it); `ready_line(...)` is the exact string; `--data-dir` applied before settings load; `--help` exits 0; **do not** start a live server — monkeypatch `uvicorn.Server.run` | `.venv/bin/pytest apps/api/tests/test_sidecar_cli.py` then `npm run test:api` when API changes settle |
| D0.02 | `apps/api/tests/test_projects_api.py` | `test_api_health_returns_ok` asserts `status`, `service`, and `version == APP_VERSION` (not exact equality to `{"status": "ok"}` only); same for unprefixed `/health`; `create_app().version == APP_VERSION`; no extra version literals | pytest those cases |
| D0.03 | `apps/api/tests/test_desktop_origins.py` | POST `/api/projects` Origin `http://localhost:3000` → 201; Origin `https://evil.example` → 403 with existing detail; Origin `tauri://localhost` → 403 unless `FRAMEPILOT_DESKTOP=1`; POST with **no** Origin → 201 (Host check makes this safe); GET `/api/projects` `Host: attacker.example` → 403; `Host: 127.0.0.1:8000` → 200; desktop-mode CORS preflight for `tauri://localhost` | pytest that file |
| D0.04a | `apps/api/tests/test_import_path_expansion.py` | Nested JPEGs + txt + heic; relative/missing/empty errors; symlink-out not followed (POSIX); FIFO skipped (POSIX); file inside project originals skipped; deterministic order | pytest that file |
| D0.04b | `apps/api/tests/test_import_from_paths.py` | Two JPEGs; **250-file three-request client loop** with one `job_id`; relative/empty 422; concurrent 409; destinations under `originals/`; unsupported skip reason; `docs/api.md` documents the loop | pytest that file |
| D0.04c | `apps/api/tests/test_import_from_paths_immutability.py` | Source `st_size` / `st_mtime_ns` / SHA-256 unchanged; directory entry count unchanged; copy is **not** a hard link to the source (POSIX); read-only source dir still imports (POSIX, skip as root); cancel mid-import leaves sources untouched | pytest that file |
| D0.05 | `scripts/sidecar-smoke.sh` | Tmp `--data-dir`, `--port 0`, parse ready line, curl `/health` for `version`, SIGTERM, exit within 5s, no leftover children | `bash scripts/sidecar-smoke.sh` (and `npm run test:sidecar` once wired) |
| D0.06 | none (docs) | After revert: `npm run test:web` if any Next config was touched | docs + optional `npm run test:web` |
| D0.07a | `scripts/test-release-checks.sh` | Tracked `apps/desktop/src-tauri/icons/128x128.png` passes; tracked `apps/desktop/other.png` still fails | `npm run test:scripts` / `bash scripts/test-release-checks.sh` |
| D0.07 | none (Rust/config) | `npm run verify` still green without rustc; sidecar smoke still passes | `npm run verify`, `bash scripts/sidecar-smoke.sh`; record WebView/`cargo --version` result |
| D0.08 | none (docs) | Notes committed | none |
| D0.09 | none (docs) | Notes committed; `npm run test:api` | `npm run test:api` |

**`测试` stage verification plan** (must match what `评审` requires):

1. `.venv/bin/pytest` on `test_sidecar_cli.py`, `test_projects_api.py`, `test_desktop_origins.py`, `test_import_path_expansion.py`, `test_import_from_paths.py`, `test_import_from_paths_immutability.py`.
2. Launch the real sidecar entry **twice** with an absolute temp `--data-dir` and `--port 0`. Parse the ready line, `GET /health` and once `/api/health`, assert JSON has `status=ok` plus `version` and `service`, SIGTERM, process exits. Do not invent a health body if launch fails.
3. `bash scripts/sidecar-smoke.sh` if present.
4. `npm run test:api` must exit 0.
5. `npm run verify` must exit 0 and must not require Rust.

Keep existing `apps/api/tests/test_ranking_export.py` and import-immutability coverage green whenever import/export code changes.

---

## 7. Acceptance boxes

Copied from the implementation plan D0.09 / product Phase 0, plus this pipeline’s host split.

**Phase 0 acceptance (must all hold at `上线`, as `[x]` or `[~]` per locked decision 13):**

- [ ] Sidecar starts, answers `/health`, exits on SIGTERM
- [ ] Origin + Host policy rejects random sites and attacker Host headers
- [ ] Path-based import exists, chunks at 100, does not mutate sources
- [ ] Feasibility notes committed
- [ ] `npm run test:api` and `npm run verify` green
- [ ] Browser web app still runs (`npm run dev` / Playwright inputs untouched)
- [ ] GUI shell is `[x]` or `[~]` with a recorded command/error

**No-GUI / no-Rust host (likely this machine):**

- Sidecar CLI and packaged-or-venv smoke work.
- Path import does not modify original files (`st_size` / `st_mtime_ns` / SHA-256).
- `npm run test:api` and `npm run verify` pass and do not invoke rustc/cargo.
- D0.07 is `[~]` if `cargo --version` or WebView fails; dated command + error in `docs/desktop_feasibility_notes.md`.
- Missing GUI is **not** an excuse to skip API, path-import, PyInstaller, CI, or docs work.

**GUI host (Windows / macOS with WebView + Rust, or CI):**

- At least one platform shows a blank Tauri window and “API ready”.
- Dual-platform installer evidence is **not** a Phase 0 requirement (Phase 4).

**`2.1.0-desktop` product DoD is out of Phase 0.** Phase 0 only proves feasibility + desktop-critical APIs.

---

## 8. Environment notes

- **OBJECTIVE branch is `refactor`.** `main` is an ancestor. Do not checkout other branches. Do not push. Do not open a PR. `isolation_worktree` is false; edit the shared workspace.
- **This host is macOS** (`user_info`). The 2026-08-18 plan text still describes the author’s Linux WSL2 machine; do not copy that as fact for this run.
- **rustc / cargo are likely absent.** D0.07 must run `cargo --version` (and `rustc --version` if useful), capture the exact error, and must **not** install a system Rust toolchain unless rustup is already present and unused. A missing toolchain is a recorded `[~]`, not a reason to fail Phase 0.
- **`npm run verify` must stay Rust-free.** D0.07a exists so later icon files do not fail `scripts/check-release-artifacts.sh`. Do not add `cargo test` or `tauri build` to `verify`.
- Python 3.11+ and Node 22 are the CI versions. Local `.venv` is created by `npm run install:all`. If `.venv` is missing at `开发`, run `npm run install:all`. Do not set `HOME` or package-manager homes to the scratch directory.
- Scratch for later stages: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-a63c25686341/implementer`. Never use `/tmp` for handoff captures.
- PyInstaller may be installed into `.venv` during D0.05 (`pip install pyinstaller`). Do not commit `dist/`, `build/`, installers, `.venv`, `node_modules`, SQLite files, private photos, or model weights.
- Sidecar live launches in tests must use an **absolute** temp `--data-dir`. Never rely on CWD-relative `.framepilot-data` after freeze.
- Playwright `webServer` probes `http://127.0.0.1:8000/health` as a URL (2xx), not JSON exact-equality. Adding `version`/`service` is safe if `status` remains `"ok"`. The exact-equality trap is `apps/api/tests/test_projects_api.py:19`.
- `create_app()` at module import (`apps/api/app/main.py:76`) freezes settings from `FRAMEPILOT_DATA_DIR`. Sidecar **must** set the env var before importing `app.main`.
- Native folder pickers are **not** Phase 0. Current `projects.py` allowlist would 422 a user-chosen folder outside `{data_dir}/projects`. That is D2.00.
- English only for code, comments, tests, docs, and commit messages.
- Suggested per-task commit subjects stay those in the implementation plan (`ci:`, `api:`, `desktop:`, `test:`, `docs:`). Final stage commits are named in `.grok/workflows/desktop-phase0.rhai`.

---

## 9. Risks

| Risk | Why it bites | Mitigation |
|------|--------------|------------|
| `--port 0` ready-line is unimplementable if uvicorn is started first | Review A2.1; `uvicorn.run` blocks before the port is known | Bind a socket, `getsockname()`, print ready line, then `Server.run(sockets=[sock])`. Tests assert non-zero port and exact ready string without a live server |
| Health pytest exact-equality | `test_api_health_returns_ok` currently `== {"status": "ok"}` | Update that assertion in D0.02; keep `status` for Playwright |
| Missing Host check on GET | DNS rebinding against `/api/projects`, `/api/assets/...`, export download | Host allowlist on **all** methods; missing Host rejected |
| Desktop origins 403 | Tauri uses `:1420` and `tauri.localhost` / `tauri://localhost` | Gate extra origins on `FRAMEPILOT_DESKTOP=1`; never wildcard; never disable the mutation origin guard |
| 2000-file folder vs 100-file cap | `IMPORT_MAX_FILES_PER_REQUEST = 100`; review A2.4 | Expand first, consume 100, return `remaining_paths` + `expanded_total`; 250-file three-request test |
| Path import mutates originals | Copy-mode must copy, not move/link/write-back | D0.04c: size/mtime/hash, entry count, no hard link, cancel-safe |
| FIFO / symlink / in-project source | `mkfifo photo.jpg` would block copy; walk following links escapes | Skip non-regular files; `followlinks=False`; drop resolved paths outside the walked root; skip sources under `project_root` |
| `create_app()` import-time settings | Frozen CWD data dir after PyInstaller | Required absolute `--data-dir`; set env before `import app.main` |
| PyInstaller one-file extract + numpy/Pillow | Broken or huge startup | One-dir only; listed hiddenimports including uvicorn lifespan/websocket |
| Next `output: 'export'` | Dynamic `projects/[projectId]` routes have no `generateStaticParams` | D0.06 docs-only; revert config; Vite SPA is the locked Phase 1 follow-up |
| Tauri icons fail `check:artifacts` | Script blocks all tracked `*.png` | D0.07a **before** D0.07; single icons exception only |
| rustc/cargo missing on this host | D0.07 cannot compile | Record `cargo --version` error; `[~]`; do not install Rust; do not fail Phase 0 |
| WSL/WebView language in old plan | Plan still says “this machine is WSL2” | This run is macOS; treat GUI/toolchain as a measured fact, not a copied WSL note |
| Broad allowlist temptation | Native picker cannot produce a legal `root_path` today | Leave D2.00 out; never set allowlist to `$HOME` |
| `verify` accidentally requires Tauri | Root scripts start calling `cargo` / desktop build | `install:all` / `verify` stay web+api; desktop scripts are additive and optional |
| Mixing v2 algorithm Goal Mode | `implement_goals.md` Phase 0 is a different track | Do not touch scoring/grouping/HEIC unless a tiny shared-code fix is required by a D0 test |
| Branch confusion | Plan recommends `feature/desktop-packaging` | Stay on `refactor`; add `refactor` to the D0.00 push filter so CI is real for this pipeline |
| Ticking tracker too early | §5.1 is the only status source | This docs stage does not tick boxes; `上线` ticks `[x]` / `[~]` after measured evidence |

---

## 10. Definition of done for this breakdown

- This file decomposes D0.00–D0.09 only.
- Locked decisions, files, tests-first list, acceptance boxes, environment notes, and risks are explicit enough for an adversarial `评审`.
- No production code, tests, or build scripts were changed in the `需求拆解` commit except documentation (and the existing `.grok/workflows/desktop-phase0.rhai` if it was untracked).
- Next stage: `评审` writes `docs/handoff/phase0-review.md`.
