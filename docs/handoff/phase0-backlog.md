# Desktop Phase 0 Accepted Backlog

Handoff stage: `归档`  
Date: 2026-08-19  
Branch: `refactor`  
Sources: `docs/handoff/phase0-requirements.md` (`c615859`), `docs/handoff/phase0-review.md` (`d15cf02`), `docs/plans/2026-08-18-desktop-packaging.md` D0.00–D0.09 and §5.1

**Verdict folded:** accept-with-notes. This file is the accepted implementation contract for **D0.00–D0.09 only**. Do not reopen Electron vs Tauri, Next vs Vite, or one-file PyInstaller.

This document does not implement production code. §5.1 boxes stay `[ ]` until `上线`. Do not start D1–D5. D2.00 is out of Phase 0. Do not bump to `2.1.0-desktop`.

---

## Process

- Implement **one id at a time**, tests first, then the smallest change that makes those tests pass.
- Suggested serial order: lowest incomplete id whose `depends-on` ids are done (table below).
- `开发` may make extra per-task commits using the `commit-hint` subjects. It **must** still finish with the `开发` stage commit.
- `测试` drives the verification plan in §Test-stage verification. Do not invent health bodies if a live sidecar launch fails.
- `上线` owns final §5.1 tracker ticks (`[x]` / `[~]`) and the written go/no-go. `开发` may draft D0.08/D0.09 notes; do not treat those drafts as final.
- Stay on `refactor`. Do not push, open a PR, or checkout `feature/desktop-packaging`.
- Local-first. Never modify original photos. English for code, comments, tests, docs, and commits.
- `npm run verify` stays free of rustc/cargo/Tauri/Playwright.

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

---

## Locked decisions (do not re-litigate)

1. Shell: Tauri 2 + Python sidecar. Electron only if D0.09 records that Tauri cannot spawn the sidecar or the WebView cannot reach loopback.
2. Backend packaging: PyInstaller **one-dir** named `framepilot-api` (not one-file).
3. Frontend: `apps/web` stays Next.js. `apps/desktop` is a future Vite SPA (Phase 1). Do not migrate `apps/web`.
4. IPC: HTTP to `127.0.0.1` only. No scoring/grouping rewrite onto Rust.
5. Bind: `127.0.0.1` only. Never `0.0.0.0`. Exit 2 if `--host` is not `127.0.0.1` or `localhost`. Prefer binding IPv4 `127.0.0.1` even if `--host localhost`, so the ready line `host=127.0.0.1` matches `getsockname()`.
6. Port: bind first, `getsockname()`, print ready line, then serve. Never guess or re-report port 0.
7. `--data-dir` / `FRAMEPILOT_DATA_DIR` is required and absolute. Set the env var **before** the first `import app.main`.
8. Ready line, `flush=True`: `FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>`. Pass the FastAPI **object** to uvicorn, not `"app.main:app"`. Logs to stderr.
9. Copy-mode storage unchanged. Sources are never modified or deleted.
10. Web app must keep working. `npm run verify` must not require Rust/Tauri.
11. `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` is never `$HOME`, `/`, a drive root, or any broad parent. Custom desktop roots are D2.00. `test_create_project_rejects_root_outside_allowlist` stays green **unchanged**.
12. Path import: expand first; one HTTP request consumes at most 100 expanded files; `remaining_paths` + `expanded_total`; client loops the same `job_id`.
13. GUI/toolchain blocked work is `[~]` with a dated command + error. `[~]` is never `[x]` without a recorded GUI/toolchain run.
14. Single version source: `apps/api/app/core/version.py` `APP_VERSION = "2.0.0-rc2"`. No extra version literals in `main.py`, `routes.py`, or tests. Do not bump package versions.
15. Artifact check: widen by exactly `allowed_pattern='^apps/desktop/src-tauri/icons/[^/]+\.(png|ico|icns)$'`. Do not broaden `blocked_pattern`.
16. D0.00 triggers: `pull_request` plus `push` to `main`, `feature/desktop-packaging`, **and `refactor`**. Do not drop `refactor`.
17. No cloud, login, payment, bundled models, HEIC/RAW/XMP. HEIC/RAW stay skipped with existing unsupported-format reasons.
18. Tracker lives in `docs/plans/2026-08-18-desktop-packaging.md` §5.1. `上线` ticks it.

---

## D0.00 — CI verify workflow

**depends-on:** none — do this first

**files:**
- create: `.github/workflows/verify.yml`
- modify: none
- test: none (CI config)

**implement:**
- Triggers: `pull_request`, and `push` to `main`, `feature/desktop-packaging`, **and `refactor`**. Keep `refactor` (review N1 / locked decision 16). Do not “fix” the workflow back to the original two-branch filter.
- Single job on `ubuntu-latest`: checkout, Python 3.11, Node 22, `npm run install:all`, `npm run verify`.
- Do not install Rust. Do not run Playwright.
- Concurrency group per ref with `cancel-in-progress: true`.

**tests-first:** none. If the tree is otherwise unchanged, run `npm run verify` locally before the commit.

**commit-hint:** `ci: run npm verify on pull requests`

**done-when:**
- `verify.yml` exists with the three push branches plus `pull_request`.
- Job does not install rustc/cargo and does not run Playwright.
- Local `npm run verify` is green if it was run.

---

## D0.01 — Sidecar CLI launcher

**depends-on:** none

**files:**
- create: `apps/api/app/sidecar_main.py`
- create: `docs/desktop_feasibility_notes.md` (stub: Blockers + Baselines) if missing
- modify: `apps/api/pyproject.toml` — add `[project.scripts] framepilot-api = "app.sidecar_main:main"`
- test: `apps/api/tests/test_sidecar_cli.py`

**implement:**
- argparse: `--host` (default `127.0.0.1`), `--port` (default `8000`, `0` = ephemeral), `--data-dir` (**required**, absolute), `--log-level` (default `info`).
- Exit 2 if `--host` is not `127.0.0.1` or `localhost`.
- Exit 2 if `--data-dir` is missing or relative. Never fall back to CWD-relative `.framepilot-data`.
- **`sidecar_main.py` must not import `app.main` at module top level** (review I3). `main()` parses args, rejects bad host / missing-or-relative `--data-dir` (exit 2), sets `os.environ["FRAMEPILOT_DATA_DIR"]`, **then** imports and passes the FastAPI **object** to uvicorn.
- Prefer binding IPv4 `127.0.0.1` even if `--host localhost`, so the ready line `host=127.0.0.1` matches `getsockname()`.
- Bind first; `getsockname()`; print exactly one stdout ready line, `flush=True`:  
  `FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>`  
  `<actual>` is never `0`.
- POSIX: set `SO_REUSEADDR` on the listen socket. Do **not** set it on Windows.
- `uvicorn.Server(config).run(sockets=[sock])`. All logs to stderr.
- Unit tests stay monkeypatched (no live server). Live bind/ready/health proof belongs to `测试`.

**tests-first:** write `apps/api/tests/test_sidecar_cli.py` first. Do **not** start a live server; monkeypatch `uvicorn.Server.run`.
- `parse_args` rejects `--host 0.0.0.0` and `--host 192.168.1.5` (exit 2).
- `parse_args` rejects missing or relative `--data-dir` (exit 2).
- `--help` exits 0.
- `bind_listen_socket("127.0.0.1", 0)` returns a socket bound to `127.0.0.1` with a **non-zero** port; close it.
- `ready_line(...)` is exactly `FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>` with `<actual>` from `getsockname()`, never `0`.
- `--data-dir` is applied before settings load; `app.main` is not imported at `sidecar_main` module import time.

**commit-hint:** `api: add localhost-only sidecar CLI`

**done-when:**
- Sidecar CLI exists, loopback-only, required absolute `--data-dir`.
- Ready line uses the bound port, not `0`.
- `app.main` is imported only after env is set.
- `apps/api/tests/test_sidecar_cli.py` passes under `.venv/bin/pytest`.

---

## D0.02 — Health payload with version

**depends-on:** D0.01

**files:**
- create: `apps/api/app/core/version.py` (`APP_VERSION = "2.0.0-rc2"`)
- modify: `apps/api/app/main.py` (`FastAPI(version=APP_VERSION)`, `/health`)
- modify: `apps/api/app/api/routes.py` (`/api/health`)
- modify: `docs/api.md`
- test: `apps/api/tests/test_projects_api.py` (replace exact `== {"status": "ok"}`)

**implement:**
- Both `/health` and `/api/health` return:

```json
{"status": "ok", "version": "2.0.0-rc2", "service": "framepilot-api"}
```

- `version` is `APP_VERSION` from `apps/api/app/core/version.py`. Keep `status` as `"ok"` (Playwright probes `http://127.0.0.1:8000/health` as a 2xx URL).
- No extra version literals in `main.py`, `routes.py`, or tests.
- Do not bump `pyproject.toml` / `package.json` versions in Phase 0 (review N6).

**tests-first:** update `test_api_health_returns_ok` (and the unprefixed `/health` case) **before** relying on a green implementation.
- `GET /api/health` and `GET /health` return 200 with `status == "ok"`, `service == "framepilot-api"`, `version == APP_VERSION`.
- `create_app().version == APP_VERSION`.
- No extra version literals.

**commit-hint:** `api: extend health payload with version`

**done-when:**
- Both health endpoints return `status`, `version`, `service`.
- Existing exact-equality assertion is replaced; Playwright still sees `status: "ok"`.
- `create_app().version == APP_VERSION`.

---

## D0.03 — Origin and Host policy

**depends-on:** none (can follow D0.01 / D0.02)

**files:**
- create: `apps/api/app/core/origins.py`
- create: `apps/api/tests/conftest.py` — set default `TestClient` `base_url` to `http://127.0.0.1` (review H1). A shared helper every test client uses is acceptable only if the existing suite no longer sends `Host: testserver`.
- modify: `apps/api/app/main.py` (allowlist, CORS, mutation guard, Host check)
- test: `apps/api/tests/test_desktop_origins.py`
- do **not** rewrite `apps/api/tests/test_projects_api.py::test_create_project_rejects_root_outside_allowlist`

**implement:**
- `allowed_origins()` always includes the four web origins: `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3100`, `http://127.0.0.1:3100`.
- When `FRAMEPILOT_DESKTOP=1` **only**, also: `http://localhost:1420`, `http://127.0.0.1:1420`, `http://tauri.localhost`, `https://tauri.localhost`, `tauri://localhost`.
- Compute the set **inside `create_app()`** (no stale `lru_cache` across env changes). Feed CORS and the mutation guard the same set. `allow_credentials=True`. No wildcard.
- Host check on **GET, POST, and OPTIONS** (all methods, including preflight). Parse Host: strip port and IPv6 brackets; compare **hostname only**. Allowed hostnames: `127.0.0.1`, `localhost`, `::1`, `tauri.localhost`.
- Missing Host is rejected (403).
- **Do not** add `testserver` to the production Host allowlist.
- Checking `request.client.host` is not a Host policy; the check must use the Host header hostname.
- GET with an evil Origin and a loopback Host remains 200 (origin guard stays mutation-only).
- Attacker Host still 403 when desktop mode is on.
- Do not implement `POST /api/desktop/project-roots`. Do not set the project-root allowlist to `$HOME` / `/` / a drive root.

**tests-first:** write `apps/api/tests/test_desktop_origins.py` and `apps/api/tests/conftest.py` first. Existing suite stays green via loopback TestClient (H1).
- POST `/api/projects` Origin `http://localhost:3000` → 201 (web origins always allowed).
- POST Origin `https://evil.example` → 403 with existing detail `"Origin not allowed for local FramePilot API"`.
- POST Origin `tauri://localhost` or `http://localhost:1420` → 403 unless `FRAMEPILOT_DESKTOP=1`.
- With `FRAMEPILOT_DESKTOP=1`, POST Origin `tauri://localhost` (and the other desktop origins) → 201; CORS preflight for `tauri://localhost` succeeds.
- POST with **no** Origin and loopback Host → 201.
- GET `/api/projects` `Host: attacker.example` → 403 (all methods, including GET).
- GET `Host: 127.0.0.1:8000` → 200. **Host-with-port is the happy path** so implementers parse hostname instead of comparing the raw header to `"127.0.0.1"`.
- **Missing Host → 403 on GET and POST**, via raw ASGI / header override. Do **not** use the TestClient default as the missing-Host case (after conftest, the default always sends Host).
- Desktop mode does not allow attacker Host.
- Default TestClient Host `testserver` is **not** allowed in production; tests use loopback `base_url`.
- Keep `test_create_project_rejects_root_outside_allowlist` body and assertions **unchanged**. Host loopback is an implicit client setting only. Do not rewrite that test to paper over 403s.

**commit-hint:** `api: allow Tauri origins and reject non-loopback hosts in desktop mode`

**done-when:**
- Web origins always work; desktop origins only when `FRAMEPILOT_DESKTOP=1`.
- Host allowlist is hostname-parsed; ported loopback is 200; missing Host and attacker Host are 403 on GET and POST.
- Production allowlist does not include `testserver`.
- Existing pytest suite is green because TestClient defaults to loopback, not because the policy was weakened.
- `test_create_project_rejects_root_outside_allowlist` is unchanged and still 422s illegal roots.

---

## D0.04a — Import path expansion helper

**depends-on:** none

**files:**
- modify: `apps/api/app/services/importing.py`
- test: `apps/api/tests/test_import_path_expansion.py`

**implement:**
- Add next to `IMPORT_MAX_FILES_PER_REQUEST`:

```python
PATH_IMPORT_MAX_INPUT_ENTRIES = 5000
PATH_IMPORT_MAX_EXPANDED_FILES = 20000
```

- `expand_import_paths(paths, project_root) -> ExpandedImportPaths` with `files` and `skipped`.
- `ValueError` for empty list, too many input entries, any non-absolute path, missing path, or expansion over the cap.
- Directories: `os.walk(followlinks=False)`; drop entries whose `resolve()` is not under the walked root.
- Regular files only (`stat.S_ISREG`). Skip FIFOs/devices.
- Extension filter reuses existing supported/unsupported helpers (HEIC/RAW skip reasons match upload).
- Skip sources under `project_root.resolve()` (`"Source is inside the project folder"`).
- Deduplicate by resolved path; sort for determinism.
- This helper expands only. HTTP consumption of 100 files is D0.04b.

**tests-first:** write `apps/api/tests/test_import_path_expansion.py` first.
- Nested JPEGs + txt + heic.
- Relative / missing / empty errors.
- Symlink-out not followed (POSIX).
- FIFO skipped (POSIX).
- Source inside `project_root` skipped.
- Deterministic order.
- Caps `PATH_IMPORT_MAX_INPUT_ENTRIES` / `PATH_IMPORT_MAX_EXPANDED_FILES`.

**commit-hint:** `api: add import path expansion helper`

**done-when:**
- Helper expands directories to regular files with the listed skip/error rules.
- Tests pass on POSIX skip cases and deterministic order.
- No HTTP route yet.

---

## D0.04b — Path-based import endpoint

**depends-on:** D0.04a

**files:**
- modify: `apps/api/app/schemas/api.py`, `apps/api/app/api/routes.py`
- test: `apps/api/tests/test_import_from_paths.py`
- docs: `docs/api.md`

**implement:**

```text
POST /api/projects/{project_id}/imports/from-paths
{"paths": ["/abs/folder", "/abs/file.jpg"], "job_id": null, "expected_total": null, "finalize": true}
```

- **Expand first** (D0.04a). One HTTP request then consumes at most `IMPORT_MAX_FILES_PER_REQUEST` (100) expanded regular files.
- Do **not** 422 a single directory whose expansion exceeds 100. Multipart already 422s when `len(files) > 100`; path import must not.
- `expanded_total` is the **full expansion count** (250 in the loop test), not the first-slice size of 100.
- `remaining_paths` is the **unconsumed leftover expanded FILE paths**, deterministic order — **not** the original folder path. After a folder of 250 files: length 150, then 50, then `[]`. If the first request is `{"paths": ["/abs/folder-of-250"]}` and `remaining_paths` echoes that folder, the next request re-walks 250 files and is not a chunk loop.
- Client re-posts `remaining_paths` with the **same `job_id`**. `finalize: true` only on the last slice.
- `expected_total` / `job.total_items` follow `expanded_total`, not the first-slice size of 100.
- `ValueError` from expansion → 422.
- Reuse multipart control flow (active-import 409, stale-job, `expected_total`).
- Per file: `source.open("rb")` then existing `register_import_file`. Do not add a second copy path.
- Queue derivative job on the same `finalize` terms as multipart.
- When finalize, a single input directory was given, and `source_root_path` is empty, record it as read-only metadata. No rescan.
- Multipart `ImportResult` gains `remaining_paths: []` and `expanded_total` (request file count is acceptable for multipart). Assert that on an existing multipart import so browser clients stay compatible.

**tests-first:** write `apps/api/tests/test_import_from_paths.py` first.
- Two JPEGs copy under `originals/`.
- Unsupported skip reason matches upload helpers.
- **250-file three-request client loop**, one `job_id`: first response consumes 100, `expanded_total == 250`, `len(remaining_paths) == 150`; second consumes 100, remaining 50; third consumes 50, `remaining_paths == []`; `finalize: true` only on the last slice; destinations under `originals/`.
- Relative/empty paths → 422.
- Concurrent import without that `job_id` → 409.
- Multipart import still works and returns `remaining_paths: []` (and `expanded_total`).
- `docs/api.md` documents the loop.

**commit-hint:** `api: add path-based local import`

**done-when:**
- Path import expands, chunks at 100 leftover **files**, and loops with one `job_id`.
- `remaining_paths` never re-submits the original folder as the remainder.
- Multipart stays compatible.
- `docs/api.md` documents the client loop.

---

## D0.04c — Path import immutability tests

**depends-on:** D0.04b

**files:**
- create / test: `apps/api/tests/test_import_from_paths_immutability.py`
- modify: production service **only if a test fails** — fix the service, not the test

**implement:**
- No production change expected.
- Sources stay copy-mode: never modify, delete, or hard-link originals.

**tests-first:** write `apps/api/tests/test_import_from_paths_immutability.py` first. If it fails, fix the service, not the test.
- Source `st_size`, `st_mtime_ns`, and SHA-256 unchanged after path import.
- Source directory entry count unchanged.
- Project copy is **not** a hard link to the source (POSIX).
- Read-only source dir still imports (POSIX; skip as root).
- Cancel mid-import leaves sources untouched.
- Keep existing multipart immutability (`test_import_process_export_api.py` mtime/bytes) and `test_ranking_export.py` green.

**commit-hint:** `test: assert path import never mutates source files`

**done-when:**
- Immutability tests pass: size, mtime_ns, SHA-256, entry count, no hard link, cancel-safe.
- Existing multipart immutability and ranking-export tests stay green.

---

## D0.05 — PyInstaller spec and sidecar smoke

**depends-on:** D0.01, D0.02

**files:**
- create: `packaging/pyinstaller/framepilot-api.spec`, `packaging/pyinstaller/build.sh`, `packaging/pyinstaller/hooks/hook-app.py` if needed
- create: `scripts/sidecar-smoke.sh` (not a pytest file under repo-root `tests/desktop/` — `npm run test:api` only collects `apps/api/tests`)
- modify: root `package.json` (`packaging:sidecar`, `test:sidecar`)

**implement:**
- One-dir build named `framepilot-api` (not one-file; review N4).
- Hiddenimports must include: `app.main`, `app.sidecar_main`, `uvicorn.loops.auto`, `uvicorn.protocols.http.auto`, `uvicorn.protocols.websockets.auto`, `uvicorn.lifespan.on`, `uvicorn.lifespan.off`, `httptools`, `sqlalchemy.dialects.sqlite`, `PIL.JpegImagePlugin`, `PIL.PngImagePlugin`, `PIL.WebPImagePlugin`, `imagehash`, `numpy`, and scipy submodules pulled by imagehash.
- Pass the FastAPI object, not `"app.main:app"`.
- Windows: document `--loop asyncio` if uvloop is absent.
- `build.sh` must fail if `/health` is not OK after start.
- Smoke: tmp absolute `--data-dir`, `--port 0`, parse ready line, curl `/health` for `version`, SIGTERM, exit within 5s, no leftover children. Prefer the built binary if present, else `.venv/bin/python -m app.sidecar_main`.
- Do not commit `dist/` or `build/` (already gitignored).
- PyInstaller may be installed into `.venv` (`pip install pyinstaller`). Do not commit it as a repo artifact.

**tests-first:** write `scripts/sidecar-smoke.sh` first (shell smoke, not a skipped pytest collector).
- Tmp `--data-dir`, `--port 0`, parse ready line, curl `/health` for `version`, SIGTERM, exit within 5s, no leftover children.

**commit-hint:** `desktop: add PyInstaller sidecar spec and smoke`

**done-when:**
- One-dir spec and `scripts/sidecar-smoke.sh` exist.
- Smoke prefers the built binary, else the venv module.
- `dist/` / `build/` stay untracked.

---

## D0.06 — Next static export spike (docs)

**depends-on:** none

**files:**
- modify: `docs/desktop_feasibility_notes.md`
- throwaway only: `apps/web/next.config.ts` — **must be reverted** if it breaks the web app

**implement:**
- Attempt Next `output: 'export'` in a **throwaway** change.
- Record whether `next build` succeeds, what happens to `projects/[projectId]` routes (five pages, no `generateStaticParams` today), and `useSearchParams` Suspense warnings.
- **If the throwaway config breaks the web app, revert `apps/web/next.config.ts` in the same work** (review N2). After revert, run `npm run test:web` if any Next config was touched.
- Locked follow-up remains Vite SPA (Phase 1). Do not migrate `apps/web`. Do not leave a broken `output: 'export'` committed.

**tests-first:** none (docs). After revert: `npm run test:web` if Next config was touched.

**commit-hint:** `docs: record Next static export spike`

**done-when:**
- Feasibility notes record the spike result.
- `apps/web` still works; any breaking Next config is reverted.
- No frontend migration started.

---

## D0.07a — Tauri artifact / gitignore hygiene

**depends-on:** D0.00

**files:**
- modify: `scripts/check-release-artifacts.sh`, `.gitignore`
- test: `scripts/test-release-checks.sh` (this is **new coverage**; the script does not currently exercise `check-release-artifacts.sh`)

**implement:**
- Widen by **exactly** one exception after the blocked-pattern match:

```bash
allowed_pattern='^apps/desktop/src-tauri/icons/[^/]+\.(png|ico|icns)$'
```

- Do not broaden `blocked_pattern`. Do not add any other exception.
- `.gitignore`: add `target/` and `.framepilot-desktop-dev/`.
- Land this **before** any Tauri icon files (D0.07).

**tests-first:** extend `scripts/test-release-checks.sh` first (review N5).
- Tracked `apps/desktop/src-tauri/icons/128x128.png` passes.
- Tracked `apps/desktop/other.png` still fails.

**commit-hint:** `desktop: allow tauri icons in the release artifact check`

**done-when:**
- Single icons exception is in place.
- `bash scripts/test-release-checks.sh` covers both the allow and still-blocked PNG cases.
- `.gitignore` has `target/` and `.framepilot-desktop-dev/`.

---

## D0.07 — Minimal Tauri shell with sidecar health

**depends-on:** D0.01, D0.03, D0.05, D0.07a

**files:**
- create: `apps/desktop/**` skeleton plus `apps/desktop/src-tauri/icons/` (`32x32.png`, `128x128.png`, `128x128@2x.png`, `icon.icns`, `icon.ico`) **only after D0.07a**
- modify: root `package.json` (`dev:desktop`) only if it does **not** make `verify` require Rust
- modify: `docs/desktop_feasibility_notes.md` when GUI/toolchain is blocked

**implement:**
- Tauri 2 blank window.
- Spawn sidecar (dev: venv uvicorn via sidecar CLI; prod later) with `--host 127.0.0.1 --port <free> --data-dir <app-support>`.
- Set `FRAMEPILOT_DESKTOP=1`.
- Poll `/health` (15s timeout). Show “API ready” or the error.
- On exit: SIGTERM, then kill after 5s.
- Locked CSP (`app.security.csp`):

```text
default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
img-src 'self' data: blob: http://127.0.0.1:* http://localhost:*;
connect-src 'self' http://127.0.0.1:* http://localhost:* ipc: http://ipc.localhost;
font-src 'self' data:; object-src 'none'; frame-ancestors 'none'
```

- `assetUrl` returns absolute loopback URLs used in `<img src>`. Missing `img-src` looks like a backend bug.
- **This host: rustc/cargo missing is `[~]`.** Run `cargo --version` (and `rustc --version` if useful), capture the exact error, and append a **dated command + error** to `docs/desktop_feasibility_notes.md`. Do **not** install a system Rust toolchain unless rustup is already present and unused. Keep a verify-safe skeleton. Run sidecar smoke without GUI. Do not add `cargo test` / `tauri build` to `npm run verify`.
- Missing GUI is **not** an excuse to skip API, path-import, PyInstaller, CI, or docs.

**tests-first:** none (Rust/config). Run: `npm run verify` (must stay green without rustc), `bash scripts/sidecar-smoke.sh`. Record WebView / `cargo --version` result.

**commit-hint:** `desktop: add minimal Tauri shell with sidecar health`

**done-when:**
- Either a blank Tauri window shows “API ready”, or D0.07 is `[~]` with a dated `cargo`/`rustc`/WebView command + error in feasibility notes.
- `npm run verify` still does not require Rust.
- Sidecar smoke still passes.
- `上线` is the stage that ticks `[~]` / `[x]` in §5.1.

---

## D0.08 — Baselines

**depends-on:** D0.05, D0.07

**files:**
- modify: `docs/desktop_feasibility_notes.md`

**implement:**
- Record even if only the sidecar ran: dist size, RSS after `/health`, time to `/health`, Tauri hello RSS or “blocked on missing rustc/WebView”, scipy/pywavelets presence.
- This host is macOS. Do not copy the implementation plan’s WSL2 language as a measured fact.

**tests-first:** none (docs).

**commit-hint:** `docs: record desktop feasibility baselines`

**done-when:**
- Notes committed with the measured sidecar numbers and a GUI/toolchain blocked line if applicable.
- Draft is allowed in `开发`; `上线` owns the final record.

---

## D0.09 — Go / no-go

**depends-on:** D0.06, D0.08

**files:**
- modify: `docs/desktop_feasibility_notes.md`

**implement:**
- Write: Shell stays Tauri 2 (or Electron only if Tauri cannot spawn sidecar / WebView cannot reach loopback). Frontend follow-up is Vite SPA. Keep imagehash/scipy unless unpacked sidecar **>250 MB**.
- `开发` may draft this text. **`上线` owns the final go/no-go and the §5.1 ticks.** Do not start Phase 1 from this id.

**tests-first:** none (docs). Run: `npm run test:api`.

**commit-hint:** `docs: record desktop phase 0 go/no-go`

**done-when:**
- Draft or final notes exist; final wording and tracker ticks belong to `上线`.
- Phase 0 acceptance boxes below are evidence-ready (not ticked in `开发` / `归档`).

**Phase 0 acceptance (must all hold at `上线`, as `[x]` or `[~]` per locked decision 13):**

- [ ] Sidecar starts, answers `/health`, exits on SIGTERM
- [ ] Origin + Host policy rejects random sites and attacker Host headers
- [ ] Path-based import exists, chunks at 100, does not mutate sources
- [ ] Feasibility notes committed
- [ ] `npm run test:api` and `npm run verify` green
- [ ] Browser web app still runs (`npm run dev` / Playwright inputs untouched)
- [ ] GUI shell is `[x]` or `[~]` with a recorded command/error

**No-GUI / no-Rust host (this machine unless a toolchain appears):**

- Sidecar CLI and packaged-or-venv smoke work.
- Path import does not modify original files (`st_size` / `st_mtime_ns` / SHA-256).
- `npm run test:api` and `npm run verify` pass and do not invoke rustc/cargo.
- D0.07 is `[~]` if `cargo --version` or WebView fails; dated command + error in `docs/desktop_feasibility_notes.md`.
- Missing GUI is **not** an excuse to skip API, path-import, PyInstaller, CI, or docs work.

---

## Test-stage verification

`开发` writes the pytest files first. `测试` drives the shipped code (no invented health bodies).

### Sidecar args, ready line, port bind

File: `apps/api/tests/test_sidecar_cli.py` (write first; do **not** start a live server; monkeypatch `uvicorn.Server.run`).

- `parse_args` rejects `--host 0.0.0.0` and `--host 192.168.1.5` (exit 2).
- `parse_args` rejects missing or relative `--data-dir` (exit 2).
- `--help` exits 0.
- `bind_listen_socket("127.0.0.1", 0)` returns a socket bound to `127.0.0.1` with a **non-zero** port; close it.
- `ready_line(...)` is exactly  
  `FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>`  
  with `<actual>` from `getsockname()`, never `0`.
- `--data-dir` is applied before settings load; `app.main` is not imported at `sidecar_main` module import time.

Live (`测试` stage, twice): launch the real sidecar entry with an **absolute** temp `--data-dir` and `--port 0`. Parse the ready line (host/port/data_dir). Port in the line is the bound port, not 0.

### Health `status` / `version` / `service`

Files: `apps/api/tests/test_projects_api.py` plus the live sidecar runs.

- `GET /api/health` and `GET /health` return 200 with `status == "ok"`, `service == "framepilot-api"`, `version == APP_VERSION`.
- `create_app().version == APP_VERSION`.
- No extra version literals in `main.py`, `routes.py`, or tests.
- Live sidecar: `GET /health` and once `GET /api/health` after the ready line; same JSON fields; SIGTERM; process exits. Do not invent a body if launch fails.

### Origin / Host policy

File: `apps/api/tests/test_desktop_origins.py` (write first). Existing suite stays green via loopback TestClient.

- POST `/api/projects` Origin `http://localhost:3000` → 201.
- POST Origin `https://evil.example` → 403 with existing detail `"Origin not allowed for local FramePilot API"`.
- POST Origin `tauri://localhost` or `http://localhost:1420` → 403 unless `FRAMEPILOT_DESKTOP=1`.
- With `FRAMEPILOT_DESKTOP=1`, POST Origin `tauri://localhost` (and the other desktop origins) → 201; CORS preflight for `tauri://localhost` succeeds.
- POST with **no** Origin and loopback Host → 201.
- GET `/api/projects` `Host: attacker.example` → 403.
- GET `Host: 127.0.0.1:8000` → 200.
- Missing Host → 403 (GET and POST) via raw ASGI / header override.
- Desktop mode does not allow attacker Host.
- Default TestClient Host `testserver` is **not** allowed in production; tests use loopback `base_url`.

### Path-import loop of 100

Files: `apps/api/tests/test_import_path_expansion.py`, `apps/api/tests/test_import_from_paths.py`.

- D0.04a: nested JPEGs + txt + heic; relative/missing/empty errors; symlink-out not followed (POSIX); FIFO skipped (POSIX); source inside `project_root` skipped; deterministic order; caps.
- D0.04b: two JPEGs copy under `originals/`; unsupported skip reason matches upload helpers.
- 250-file three-request client loop, one `job_id`: 100 / remaining 150 / `expanded_total == 250`; then remaining 50; then `remaining_paths == []`; `finalize: true` only on the last slice.
- Relative/empty paths → 422; concurrent import without that `job_id` → 409.
- Multipart import still works and returns `remaining_paths: []`.
- `docs/api.md` documents the loop.

### Original-file immutability

File: `apps/api/tests/test_import_from_paths_immutability.py` (write first; if it fails, fix the service, not the test).

- Source `st_size`, `st_mtime_ns`, and SHA-256 unchanged after path import.
- Source directory entry count unchanged.
- Project copy is **not** a hard link to the source (POSIX).
- Read-only source dir still imports (POSIX; skip as root).
- Cancel mid-import leaves sources untouched.
- Keep existing multipart immutability and `test_ranking_export.py` green.

### Commands `测试` must run

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

## Out of scope

- `implement_goals.md` Phase 0 (v2 web “Safety and repository baseline”).
- Desktop Phases 1–5 (D1.01–D5.05), including navigation adapter, Vite SPA, native FS, menus, installers, and version bump to `2.1.0-desktop`.
- D2.00 registered project roots / `POST /api/desktop/project-roots`.
- Setting `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`.
- Migrating `apps/web` off Next.js or deleting `ImportPanel.tsx` file inputs.
- Replacing scoring/grouping with Rust.
- HEIC / RAW / XMP / bundled neural models / cloud / login / payment.
- Installing a system Rust toolchain when rustc/cargo are missing (unless rustup is already present and unused).
- Making `npm run verify` require Rust, Tauri, or Playwright.
- Adding `testserver` to the production Host allowlist.
- Weakening `test_create_project_rejects_root_outside_allowlist`.
- Pushing, opening a PR, or switching off `refactor`.
- Ticking §5.1 in this archive or in `开发`.
- Publishing installers.
