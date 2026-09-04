# Changelog

> Language: **English** | [中文](CHANGELOG.zh.md)

All notable FramePilot releases are listed here. Version strings for the API come from `apps/api/app/core/version.py` (`APP_VERSION`). The Python package version in `apps/api/pyproject.toml` uses the PEP 440 local form `2.1.0+desktop` so editable installs stay valid.

## Unreleased

### Docs — bilingual desktop shell pages

- Add Chinese counterparts for `apps/desktop/README.md` and `tests/desktop/workflow.md`
- Markdown link check now scans those living pages

### Phase 8 — HEIC preview

- Local HEIC/HEIF still import, decode with `pillow-heif`, WebP thumbnails/previews, and score/group on decoded RGB
- Original HEIC bytes are copied into `originals/` and exported (ZIP uses `ZIP_STORED`); source files are never modified
- Garbage HEIC fails that file after copy; RAW, AVIF, Live Photo `.mov`, HDR gain-map tone mapping, and XMP stay out of this slice
- Frozen sidecar collects `pillow_heif` / libheif; wheels ship LGPL libheif (documented in known limitations)
- No `APP_VERSION` bump, signing, or packaged GUI

### Phase 7 — processing job cancel

- Cooperative processing cancel on the existing `POST /api/projects/{project_id}/jobs/{job_id}/cancel` route (queued/running persist `cancellation_requested` with 202; terminal is a 200 no-op; interrupted finalizes `cancelled` and resets groups)
- Worker checkpoints then group reset: photos return to `imported`; `user_status` / `star_rating` and import derivatives stay; originals are never modified or deleted
- Processing UI can request **Cancel Grouping and Ranking** and shows checkpoint copy
- Desktop quit can **Quit and cancel processing** (POST cancel, wait up to 10s, then SIGTERM)
- Reclaim honors a pending processing cancel and does not re-queue
- Export cancel remains 422; pause/resume of in-flight grouping is not implemented
- No `APP_VERSION` bump, signing, or packaged GUI

### Desktop — direct @tauri-apps/api/webview dependency (L4)

- `apps/desktop/package.json` now lists `@tauri-apps/api` as a direct dependency so `nativeFs.ts` can import `@tauri-apps/api/webview` without relying on a plugin transitive install
- No version bump, signing, packaged GUI, or auto-update

### Desktop — return null from getNativeFs() outside Tauri (L3)

- Desktop `getNativeFs()` returns `null` when `window` has neither `__TAURI_INTERNALS__` nor `__TAURI__`, matching the D2.01 web stub
- Opening desktop Vite in a normal browser no longer takes native-picker branches that then fail plugin calls
- No L4 (`@tauri-apps/api/webview` direct dep), version bump, signing, packaged GUI, or auto-update

### Desktop — reject home directory when registering a project root (L2)

- `register_root` now rejects `Path.home()` / `$HOME` by name, including when Linux/WSL desktop-dev stores `data_dir` under the repo instead of under home
- Subdirectories of home can still be registered; D2.00 remains the widen path
- No L3 (`getNativeFs` never-null) or L4 (`@tauri-apps/api/webview` direct dep), version bump, signing, packaged GUI, or auto-update

### Desktop — strip inherited project-root allowlist at sidecar spawn (L1)

- Tauri sidecar spawn `env_remove`s `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` so a parent shell (for example `tauri dev`) cannot leak a wide allowlist into the sidecar
- D2.00 registration remains the widen path; API-side M1 filtering of leftover env entries is unchanged
- No L2–L4 work, version bump, signing, packaged GUI, or auto-update

### CI — desktop HTTP smoke gate

- `.github/workflows/verify.yml` runs an independent job on pull requests and `main`: `npm run test:desktop:smoke` (`tests/desktop/smoke.sh`: sidecar ready line, `GET /health`, `GET /api/projects`, desktop Origin CORS preflight, attacker `Host` → 403)
- Uses the venv sidecar when no frozen binary is present. HTTP-only: does not launch a packaged NSIS/DMG GUI or add code signing / notarization
- Large real-browser (`test:e2e:real-browser:large`) stays opt-in and is not part of the default gate
- `tests/desktop/smoke.sh` leftover check only flags leftover sidecar/uvicorn processes (Linux `pgrep -P $$` includes pgrep itself)

### CI — validation-decision default gate

- `npm run verify` now includes `npm run check:validation-decision` (`scripts/check-validation-decision.sh` / `docs/v2_rc2_validation_decision.md`)
- Checked on `main` @ `1b6c15b1ca4faca4366a7b9a9d105b1b7c1d4961`: the decision file is completed with existing notes, so this subset does not false-red
- GitHub Actions workflow YAML is unchanged; the check rides along with the existing `verify` job. No separate `check:pretag` job is required
- `npm run check:pretag` remains the release-time command (`verify` plus the same validation-decision check)
- Large real-browser (`test:e2e:real-browser:large`) stays opt-in and is not part of the default gate

### CI — Playwright E2E gate

- `.github/workflows/verify.yml` runs an independent job on pull requests and `main`: `npm run test:e2e` (Playwright mocked E2E plus `tests/e2e/real-local-smoke.spec.ts`)
- `.github/workflows/verify.yml` also runs an independent job: `npm run test:e2e:real-browser` (100 generated JPEGs, Chromium)
- Large real-browser (`test:e2e:real-browser:large`, 500/1000/2000) stays opt-in and is not part of the default gate
- These E2E jobs do not launch a packaged NSIS/DMG GUI or add code signing / notarization
- Mocked culling E2E now asserts first-page load (`0/500 loaded reviewed` plus `500 of 501 loaded`) before Load all photos
- Playwright uses one worker in CI so real-local-smoke and real-browser smokes do not share the E2E API data dir in parallel

### CI — frozen sidecar `/health` gate

- `.github/workflows/verify.yml` runs an independent job on pull requests and `main`: `npm run packaging:sidecar` then `npm run test:sidecar` (frozen `GET /health` with `PYTHONPATH` unset)
- `.github/workflows/desktop.yml` runs the same smoke after PyInstaller and still does not launch the packaged GUI or sign installers
- `scripts/sidecar-smoke.sh` leftover check only flags leftover sidecar/uvicorn processes (Linux `pgrep -P $$` includes pgrep itself)

### Phase 6.1 — job reclaim on by default

- `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` now defaults to **on**; set it to `0`/`false`/`no`/`off` to opt back into fail-and-retry startup behavior
- Desktop quit copy updated to reflect reclaim as the default, with wording for the explicit opt-out case

### Phase 6 — durable local job reclaim (opt-in)

- Optional startup reclaim via `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=1` (default was fail-and-retry; flipped in Phase 6.1 above)
- Job checkpoint / lease fields on `JobRead`; status `interrupted` for reclaimable leftovers
- Local worker entrypoint: `npm run worker` / `python -m app.worker`
- Desktop quit copy aligned with reclaim vs fail-and-retry

## 2.1.0-desktop (RC)

Desktop packaging track release candidate.

- Tauri 2 desktop shell with localhost Python sidecar (no manual uvicorn for end users)
- Native folder/file pickers and path-based import (copies into project `originals/`; originals never modified)
- Windows NSIS and macOS DMG installers via CI (may be **unsigned** for internal testing; see [docs/desktop_signing.md](docs/desktop_signing.md))
- Desktop user guide, testing matrix, and performance notes under `docs/`
- Web contributor workflow (`npm run dev`) unchanged

Do not treat this RC as a signed public store release until certificates are configured.

## 2.0.0-rc2

Local web MVP-plus foundation: job-based import/processing, culling workspace, CSV/ZIP/folder export, and Tier B real-world validation evidence. Desktop packaging was deferred until the 2.1.0-desktop track.
