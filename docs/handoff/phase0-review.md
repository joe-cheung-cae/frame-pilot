# Desktop Phase 0 Requirements Review

Handoff stage: `评审`  
Date: 2026-08-19  
Branch: `refactor`  
Reviewed: `docs/handoff/phase0-requirements.md` (需求拆解 commit `c615859`) against the live `2.0.0-rc2` tree  
Sources: `docs/plans/2026-08-18-desktop-packaging.md` D0.00–D0.09 and §5.1, `docs/plans/2026-08-18-desktop-packaging-review.md`, `AGENTS.md`, live API/tests/scripts

**Verdict: accept-with-notes**

The breakdown is a safe Phase 0 contract. It fences D0.00–D0.09, keeps the web app working, does not start D1–D5 or D2.00, and already folds in the refined-plan traps (`--port 0` bind-then-ready, chunked path import, Host on GET, one-dir PyInstaller, Next export revert, Tauri `[~]`, `verify` without Rust). It is not rejected.

归档 must fold the notes below into `docs/handoff/phase0-backlog.md` before 开发. The highest note is not a product-policy hole; it is a suite-breaking Host default in pytest.

No production code, tests, or build scripts were changed in this stage. §5.1 boxes stay `[ ]`.

---

## 1. Live-tree facts (verified)

| Claim in the breakdown | Live tree |
|------------------------|-----------|
| No `.github/` | Missing |
| No sidecar / `apps/desktop/` / `packaging/` / `docs/desktop_feasibility_notes.md` | Missing |
| `create_app()` at import (`apps/api/app/main.py:76`) | Confirmed; `get_settings()` defaults to CWD-relative `.framepilot-data` and `mkdir` (`apps/api/app/core/config.py:19`) |
| Health `{"status": "ok"}` on `/health` and `/api/health` | Confirmed; pytest exact-equality at `apps/api/tests/test_projects_api.py:19` |
| Origins: four web origins; mutation methods only; no Host check | Confirmed `ALLOWED_ORIGINS` in `main.py`; GET/OPTIONS unrestricted |
| `IMPORT_MAX_FILES_PER_REQUEST = 100` | `importing.py:43` |
| `ImportResult` has no `remaining_paths` / `expanded_total` | Confirmed `apps/api/app/schemas/api.py` |
| Multipart import only | `POST .../imports` and `.../import` in `routes.py` |
| `test_create_project_rejects_root_outside_allowlist` | Present at `test_projects_api.py:97`; D2.00 still required for picker roots |
| `scripts/check-release-artifacts.sh` blocks every tracked `*.png` | Confirmed; no icons exception; `.gitignore` lacks `target/` and `.framepilot-desktop-dev/` |
| `npm run verify` = lint + typecheck + test + check:artifacts; no Rust | Confirmed; Playwright is `test:e2e`, not `verify` |
| Next.js App Router; no `output: 'export'`; no `generateStaticParams` | `apps/web/next.config.ts`; five `projects/[projectId]/...` pages |
| Playwright probes `http://127.0.0.1:8000/health` as a URL | `playwright.config.ts:23` (2xx, not JSON equality) |
| ImportPanel file inputs remain | `ImportPanel.tsx` ~236 and ~255, including `webkitdirectory` |
| Version `2.0.0-rc2` | Root/`apps/web`/`apps/api` plus `FastAPI(version="2.0.0-rc2")` |
| No `apps/api/tests/conftest.py` | Missing |
| Starlette `TestClient` default `base_url` | `"http://testserver"` (installed Starlette in `.venv`) |
| This host | macOS; `cargo` / `rustc` are `command not found` |

---

## 2. Findings

### H1 — TestClient default Host is `testserver` (high)

**Why.** D0.03 requires a Host allowlist on **every** method and rejects a missing Host. FastAPI/Starlette `TestClient` defaults to `base_url="http://testserver"`, so every unconfigured client sends `Host: testserver`. That hostname is not `127.0.0.1`, `localhost`, `::1`, or `tauri.localhost`.

The live suite constructs `TestClient(create_app())` in ~90 places (`test_projects_api.py`, `test_import_process_export_api.py`, `test_batched_import_api.py`, `test_job_reliability.py`, `test_large_batch_api.py`, `test_group_order_and_scores.py`, plus `app/devtools/performance_smoke.py`). There is no conftest. Implementing the Host policy as specified will 403 existing tests, including health, project create, import, and `test_create_project_rejects_root_outside_allowlist`.

Checking `request.client.host` would **not** fix DNS rebinding: TestClient’s peer is `("testclient", 50000)`, and a real rebinding client still connects on loopback. The check must use the **Host header** (parsed hostname). Allowing `testserver` in production would weaken the policy.

**Required change for 归档/开发.**

- D0.03 files list must include `apps/api/tests/conftest.py` (preferred) or a helper that every test client uses.
- Default test client `base_url` to a loopback URL (`http://127.0.0.1` or `http://127.0.0.1:8000`).
- Do **not** add `testserver` to the production Host allowlist.
- D0.03 tests must still set an explicit attacker Host and an explicit missing Host (override; do not use the TestClient default as the missing-Host case).
- Do not rewrite `test_create_project_rejects_root_outside_allowlist` assertions to paper over 403s.

### H2 — Missing Host is specified but not in the D0.03 tests-first table (high)

**Why.** Locked decision and D0.03 implement text say “Missing Host is rejected.” The tests-first row only names `Host: attacker.example` → 403 and `Host: 127.0.0.1:8000` → 200. After H1, a client with a loopback `base_url` always sends Host, so the missing-Host branch can ship untested.

**Required change for 归档/开发.** Add a D0.03 case that omits or blanks the Host header (raw ASGI / header override) and expects 403 on GET and POST. Keep Host-with-port (`127.0.0.1:8000`) as the happy path so implementers parse hostname instead of comparing the raw header to `"127.0.0.1"`.

### I1 — `remaining_paths` must be leftover expanded files, not the original folder (important)

**Why.** Review A2.4 and locked decision 12 are in the breakdown: expand, consume at most 100, return `remaining_paths` + `expanded_total`, client loops with the same `job_id`. The 250-file three-request test is the right size (100 + 100 + 50). What is missing is the object identity of `remaining_paths`.

If the first request is `{"paths": ["/abs/folder-of-250"]}` and `remaining_paths` echoes that folder, the next request re-walks 250 files, fights content-hash dedup in `register_import_file`, and is not a chunk loop. Multipart already 422s when `len(files) > 100`; path import must **not** 422 a single directory whose expansion exceeds 100.

**Required change for 归档/开发.**

- Expand first (D0.04a). One HTTP request then consumes at most `IMPORT_MAX_FILES_PER_REQUEST` (100) expanded regular files.
- `expanded_total` is the full expansion count (250 in the loop test).
- `remaining_paths` is the unconsumed expanded **file** paths, deterministic order, length 150 then 50 then `[]`.
- Client re-posts `remaining_paths` with the same `job_id`; `finalize: true` only on the last slice.
- `expected_total` / `job.total_items` follow `expanded_total`, not the first-slice size of 100.
- Multipart `ImportResult` adds `remaining_paths: []` and `expanded_total` (request file count is acceptable for multipart). Assert that on an existing multipart import so browser clients stay compatible.

### I2 — Host policy must parse hostname; GET is in scope (important)

**Why.** Browsers and Playwright send `Host: 127.0.0.1:8000`. Tauri may send `tauri.localhost` or loopback-with-port. A raw-string allowlist of `{"127.0.0.1", "localhost", "::1", "tauri.localhost"}` would 403 the real web app. TCP-peer checks would allow `Host: attacker.example`.

The origin guard today is mutations-only (`POST`/`PUT`/`PATCH`/`DELETE`). GET `/api/projects`, `/api/assets/...`, and export download stay open without Host. That matches the breakdown’s DNS-rebinding risk. D0.03 tests name GET `/api/projects` only.

**Required change for 归档/开发.** Parse Host (strip port, IPv6 brackets). Compare hostname only. Origin allowlist: the four web origins **always**; `http://localhost:1420`, `http://127.0.0.1:1420`, `http://tauri.localhost`, `https://tauri.localhost`, `tauri://localhost` **only** when `FRAMEPILOT_DESKTOP=1`. Compute the set inside `create_app()` (no stale `lru_cache` across env changes). Feed CORS and the mutation guard the same set; `allow_credentials=True`; no wildcard. Host check on GET, POST, and OPTIONS (preflight). Attacker Host still 403 when desktop mode is on. GET with an evil Origin and a loopback Host remains 200.

### I3 — `create_app()` import-time settings vs required `--data-dir` (important)

**Why.** `app = create_app()` at `main.py:76` freezes `get_settings()` on first import. Default data dir is CWD-relative `.framepilot-data`. After PyInstaller, CWD is the wrong place. The breakdown already says set `FRAMEPILOT_DATA_DIR` before `import app.main`. A top-level `from app.main import app` in `sidecar_main.py` would still freeze whatever env existed at import, and pytest collection that imported `app.main` first would not re-run module body.

**Required change for 归档/开发.** `sidecar_main.py` must not import `app.main` at module top level. `main()` parses args, rejects non-loopback host and missing/relative `--data-dir` (exit 2), sets `FRAMEPILOT_DATA_DIR`, then imports and passes the FastAPI **object** to uvicorn. Prefer binding IPv4 `127.0.0.1` even if `--host localhost`, so the ready line `host=127.0.0.1` matches `getsockname()`. D0.01 unit tests stay monkeypatched (no live server). The 测试 stage live launches are the real bind/ready/health proof.

### I4 — Do not weaken the allowlist test; D2.00 stays out of Phase 0 (important)

**Why.** `create_project` still 422s roots outside `{data_dir}/projects` or `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` (`projects.py:33-37`). Native pickers cannot produce a legal `root_path` today. The breakdown already parks this in D2.00 and forbids `$HOME`. The risk in 开发 is “fixing” 403/422 by relaxing that test after the Host conftest lands.

**Required change for 归档/开发.** Keep `test_create_project_rejects_root_outside_allowlist` body and assertions unchanged. Host loopback is an implicit client setting only. Do not set the allowlist to `$HOME` / `/` / a drive root. Do not implement `POST /api/desktop/project-roots`.

### N1 — D0.00 push filter must keep `refactor` (note)

The implementation plan’s D0.00 trigger omits `refactor`. Conflict rule says that plan wins on technical disputes, but this pipeline **is** `refactor`. Locked decision 16 is the correct exception. 归档 must keep `pull_request` plus `push` to `main`, `feature/desktop-packaging`, **and `refactor`**. Do not “fix” the workflow back to the original two-branch filter.

### N2 — Next `output: 'export'` spike must be reverted if it breaks the web app (note)

Live `next.config.ts` has no `output: 'export'`. Five `projects/[projectId]` routes have no `generateStaticParams`. `npm run test:web` runs `next build`. D0.06 is docs-only; if the throwaway config breaks the web app, revert `apps/web/next.config.ts` in the same work. Locked follow-up remains Vite SPA (Phase 1). Do not migrate `apps/web`.

### N3 — Tauri GUI is `[~]` on this host unless a dated toolchain/WebView run succeeds (note)

`cargo` and `rustc` are `command not found` here. D0.07 may keep a verify-safe skeleton. `[~]` requires a dated command + error in `docs/desktop_feasibility_notes.md`. Do not install a system Rust toolchain unless rustup is already present and unused. Do not add `cargo test` / `tauri build` to `npm run verify`. Missing GUI is not an excuse to skip API, path-import, PyInstaller, CI, or docs.

### N4 — PyInstaller is one-dir `framepilot-api` (note)

Keep one-dir (not one-file). Smoke prefers the built binary if present, else `.venv/bin/python -m app.sidecar_main`. Do not commit `dist/` or `build/` (already gitignored). Do not put the smoke pytest under repo-root `tests/desktop/` if that would skip `npm run test:api` collection — `scripts/sidecar-smoke.sh` is correct.

### N5 — D0.07a tests are new coverage (note)

`scripts/test-release-checks.sh` does not currently exercise `check-release-artifacts.sh`. D0.07a must add: tracked `apps/desktop/src-tauri/icons/128x128.png` passes; tracked `apps/desktop/other.png` still fails. Widen by exactly `allowed_pattern='^apps/desktop/src-tauri/icons/[^/]+\.(png|ico|icns)$'`. Do not broaden `blocked_pattern`. `.gitignore`: `target/` and `.framepilot-desktop-dev/`.

### N6 — Health JSON exact-equality and version literals (note)

D0.02 correctly replaces `== {"status": "ok"}`. Keep `status` as `"ok"` for Playwright. `version` is `APP_VERSION` from `apps/api/app/core/version.py` (`"2.0.0-rc2"`). No extra version literals in `main.py`, `routes.py`, or tests. Do not bump package versions in Phase 0.

---

## 3. Required test list

This is the 测试-stage verification plan. 归档 must copy it. 开发 writes the pytest files first. 测试 drives the shipped code (no invented health bodies).

### 3.1 Sidecar args, ready line, port bind

File: `apps/api/tests/test_sidecar_cli.py` (write first; do **not** start a live server; monkeypatch `uvicorn.Server.run`).

- `parse_args` rejects `--host 0.0.0.0` and `--host 192.168.1.5` (exit 2).
- `parse_args` rejects missing or relative `--data-dir` (exit 2).
- `--help` exits 0.
- `bind_listen_socket("127.0.0.1", 0)` returns a socket bound to `127.0.0.1` with a **non-zero** port; close it.
- `ready_line(...)` is exactly  
  `FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>`  
  with `<actual>` from `getsockname()`, never `0`.
- `--data-dir` is applied before settings load; `app.main` is not imported at `sidecar_main` module import time.

Live (测试 stage, twice): launch the real sidecar entry with an **absolute** temp `--data-dir` and `--port 0`. Parse the ready line (host/port/data_dir). Port in the line is the bound port, not 0.

### 3.2 Health `status` / `version` / `service`

Files: `apps/api/tests/test_projects_api.py` plus the live sidecar runs.

- `GET /api/health` and `GET /health` return 200 with `status == "ok"`, `service == "framepilot-api"`, `version == APP_VERSION`.
- `create_app().version == APP_VERSION`.
- No extra version literals in `main.py`, `routes.py`, or tests.
- Live sidecar: `GET /health` and once `GET /api/health` after the ready line; same JSON fields; SIGTERM; process exits. Do not invent a body if launch fails.

### 3.3 Origin / Host policy (web always; desktop origins only in desktop mode)

File: `apps/api/tests/test_desktop_origins.py` (write first). Existing suite stays green via loopback TestClient (H1).

- POST `/api/projects` Origin `http://localhost:3000` → 201 (web origins always allowed).
- POST Origin `https://evil.example` → 403 with existing detail `"Origin not allowed for local FramePilot API"`.
- POST Origin `tauri://localhost` or `http://localhost:1420` → 403 unless `FRAMEPILOT_DESKTOP=1`.
- With `FRAMEPILOT_DESKTOP=1`, POST Origin `tauri://localhost` (and the other desktop origins) → 201; CORS preflight for `tauri://localhost` succeeds.
- POST with **no** Origin and loopback Host → 201.
- GET `/api/projects` `Host: attacker.example` → 403 (all methods, including GET).
- GET `Host: 127.0.0.1:8000` → 200 (hostname parse, port allowed).
- Missing Host → 403 (GET and POST).
- Desktop mode does not allow attacker Host.
- Default TestClient Host `testserver` is **not** allowed in production; tests use loopback `base_url`.

### 3.4 Path-import loop of 100 (`remaining_paths` + `expanded_total`)

Files: `apps/api/tests/test_import_path_expansion.py`, `apps/api/tests/test_import_from_paths.py`.

- D0.04a: nested JPEGs + txt + heic; relative/missing/empty errors; symlink-out not followed (POSIX); FIFO skipped (POSIX); source inside `project_root` skipped; deterministic order; caps `PATH_IMPORT_MAX_INPUT_ENTRIES` / `PATH_IMPORT_MAX_EXPANDED_FILES`.
- D0.04b: two JPEGs copy under `originals/`; unsupported skip reason matches upload helpers.
- **250-file three-request client loop**, one `job_id`: first response consumes 100, `expanded_total == 250`, `len(remaining_paths) == 150`; second consumes 100, remaining 50; third consumes 50, `remaining_paths == []`; `finalize: true` only on the last slice; destinations under `originals/`.
- Relative/empty paths → 422; concurrent import without that `job_id` → 409.
- Multipart import still works and returns `remaining_paths: []`.
- `docs/api.md` documents the loop.

### 3.5 Original-file immutability (`st_size` / `st_mtime_ns` / SHA-256)

File: `apps/api/tests/test_import_from_paths_immutability.py` (write first; if it fails, fix the service, not the test).

- Source `st_size`, `st_mtime_ns`, and SHA-256 unchanged after path import.
- Source directory entry count unchanged.
- Project copy is **not** a hard link to the source (POSIX).
- Read-only source dir still imports (POSIX; skip as root).
- Cancel mid-import leaves sources untouched.
- Keep existing multipart immutability (`test_import_process_export_api.py` mtime/bytes) and `test_ranking_export.py` green.

### 3.6 Commands the 测试 stage must run

1. `.venv/bin/pytest` on  
   `test_sidecar_cli.py`, `test_projects_api.py`, `test_desktop_origins.py`,  
   `test_import_path_expansion.py`, `test_import_from_paths.py`,  
   `test_import_from_paths_immutability.py`.
2. Real sidecar entry **twice** (absolute temp `--data-dir`, `--port 0`, ready line, `/health` and once `/api/health`, SIGTERM).
3. `bash scripts/sidecar-smoke.sh` if present.
4. `npm run test:api` exits 0.
5. `npm run verify` exits 0 and must **not** require Rust.

D0.00 has no pytest file; locally `npm run verify` before that commit if the tree is otherwise unchanged. D0.07a: `bash scripts/test-release-checks.sh`. D0.06: `npm run test:web` if Next config was touched, after revert.

---

## 4. Notes for 归档

- Start from `docs/handoff/phase0-requirements.md` plus this file. Do not reopen Electron vs Tauri, Next vs Vite, or one-file PyInstaller.
- Each D0.00–D0.09 id in `docs/handoff/phase0-backlog.md`: depends-on, files, implement, tests-first, commit-hint, done-when.
- Fold **H1** into D0.03 files (conftest / loopback `TestClient`) and tests-first. Fold **I1** into D0.04b (`remaining_paths` = leftover expanded files). Fold **I3** into D0.01 (`sidecar_main` defers `import app.main`).
- 开发 may make extra per-task commits; it must still finish with the 开发 stage commit. Final §5.1 ticks and go/no-go belong to `上线`.
- Do not tick §5.1 in 归档. Do not implement production code in 归档.
- Do not start D1–D5. D2.00 is out of Phase 0. Do not bump to `2.1.0-desktop`.
- Stay on `refactor`. Do not push, open a PR, or checkout `feature/desktop-packaging`.
- English for the backlog. Local-first. Never modify original photos. `npm run verify` stays free of Rust/Tauri.

---

## 5. What the breakdown already got right

Do not re-litigate these:

- Scope is desktop Phase 0 (D0.00–D0.09) only, not `implement_goals.md` Phase 0.
- Sidecar: `127.0.0.1` only, required absolute `--data-dir`, bind-then-`getsockname()`, one stdout ready line, FastAPI object not `"app.main:app"`, POSIX `SO_REUSEADDR` only.
- Health keeps `status: "ok"` and adds `version` + `service`.
- Web origins always; desktop origins gated on `FRAMEPILOT_DESKTOP=1`; Host on all methods.
- Path import chunks at 100; D0.04c size/mtime/hash; copy via existing `register_import_file`.
- CI without Rust/Playwright; PyInstaller one-dir; Next spike revert; Tauri `[~]` with dated command+error.
- `test_create_project_rejects_root_outside_allowlist` stays green; D2.00 is out; allowlist never `$HOME`.
- `create_app()` import-time settings vs `--data-dir`.
- Artifact-check exception is a single icons pattern after D0.07a, before icon files.
- Tracker stays in the implementation plan §5.1; this docs stage does not tick boxes.
