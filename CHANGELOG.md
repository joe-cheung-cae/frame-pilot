# Changelog

> Language: **English** | [中文](CHANGELOG.zh.md)

All notable FramePilot releases are listed here. Version strings for the API come from `apps/api/app/core/version.py` (`APP_VERSION`). The Python package version in `apps/api/pyproject.toml` uses the PEP 440 local form `2.1.0+desktop` so editable installs stay valid.

## Unreleased

### Phase 9 — S9.07 detached preview window

- Desktop View → Detached preview (no accelerator) and the culling toolbar toggle open a second WebView labeled `preview`
- Selection is shared with the main culling workspace; the satellite window shows derivative previews only (no `fs:` read of originals)
- Bare culling keys apply to the focused window; preview forwards commands to main and does not call `api.updatePhoto`
- Create failure is non-fatal and keeps the in-shell preview; closing the preview window does not quit the app or shut down the sidecar
- No extra `fs:` or `shell:` capabilities; no auto-reopen on launch; Space and Eye still toggle in-shell preview
- No `APP_VERSION` bump or signing

### Phase 9 — S9.06 optional system tray

- Desktop shell always attempts a system tray icon (Show + Quit); create failure is non-fatal on headless or some Linux desktops
- Tooltip (and tray title where the host shows one) reports active job progress: `Import · {step} · {n}%`, grouping and ranking, or export; idle is `No active job`
- Show or a primary click restores the main window; Quit uses the same running-job dialog as File → Quit
- Window close and minimize are unchanged (not hide-to-tray)
- No extra `fs:` or `shell:` capabilities; no Settings toggle; no OS notifications
- No `APP_VERSION` bump or signing

### Phase 9 — S9.05 XMP sidecar export

- Optional `include_xmp` on CSV/ZIP/folder export (default off); not a fourth export mode
- Folder and ZIP write `{exported_filename}.xmp` only under the project export directory (ZIP XML uses `ZIP_DEFLATED`; images stay `ZIP_STORED`)
- CSV stores the flag but writes no `.xmp` files; cancel/fail still fail-and-cleanup the export artifact
- Sidecars never land in `originals/`, beside camera originals, or inside image bytes; original bytes stay identical
- Mapping: `xmp:Rating` is stars 0–5; Pick/Maybe/Reject use Green/Yellow/Red `xmp:Label`; Unreviewed omits the label; Reject does not use `xmp:Rating = -1`
- Export UI checkbox **Write XMP sidecars** is unchecked by default and is not persisted in `localStorage`
- No `APP_VERSION` bump, signing, Lightroom/Capture One GUI certification, or write-back on import/review

### Phase 9 — S9.04 RAW embedded preview

- Local RAW import for `.dng`, `.arw`, `.cr3`, and `.nef` when an embedded preview exists: copy original bytes, extract with `rawpy.extract_thumb` only, WebP thumbnails/previews, and score/group on preview RGB
- RAW without an embedded preview is skipped with `RAW file has no embedded preview; FramePilot does not demosaic`; no Photo row and no leftover copy under `originals/`
- Original RAW bytes are exported (ZIP uses `ZIP_STORED`); source files are never modified; no demosaic / `postprocess`
- Frozen sidecar collects `rawpy` / LibRaw; `rawpy` is MIT and its wheels ship LGPL-2.1 / CDDL LibRaw (documented in known limitations)
- No `APP_VERSION` bump, signing, XMP, extra RAW extensions, or camera fixtures in git

### Phase 9 — S9.03 AVIF still preview

- Local AVIF still import (`.avif` only, not `.avifs` sequences), decode with Pillow’s native `AvifImagePlugin`, WebP thumbnails/previews, and score/group on decoded RGB
- Original AVIF bytes are copied into `originals/` and exported (ZIP uses `ZIP_STORED`); source files are never modified
- Garbage AVIF fails that file after copy; RAW, Live Photo `.mov`, HDR gain-map tone mapping, and XMP stay out of this slice
- Frozen sidecar collects `PIL.AvifImagePlugin` / `PIL._avif`; HEIC still uses `pillow-heif`
- No `APP_VERSION` bump, signing, or packaged GUI

### Phase 9 — S9.02 processing job pause

- Cooperative processing pause on `POST /api/projects/{project_id}/jobs/{job_id}/pause` with a distinct `pause_requested` flag (queued/running persist the flag with 202; terminal is a 200 no-op; interrupted finalizes `paused` and resets groups)
- Worker checkpoints then group reset without a `cancelled` finalize; originals, import derivatives, `user_status`, and `star_rating` stay
- Resume is clear-and-rerun via a new `POST /process`; `paused` does not block a replacement job
- Processing UI can request **Pause Grouping and Ranking** and shows checkpoint copy
- Reclaim honors a pending processing pause and does not re-queue; cancel still wins if both flags are set
- Import and export jobs cannot be paused; in-place continue-hash-mid-batch is not implemented
- No `APP_VERSION` bump, signing, or packaged GUI

### Phase 9 — S9.01 export job cancel

- Cooperative export cancel on the existing `POST /api/projects/{project_id}/jobs/{job_id}/cancel` route (queued/running persist `cancellation_requested` with 202; terminal is a 200 no-op; interrupted finalizes `cancelled`)
- Create export also persists `ProcessingJob` `job_type="export"` with the same id as the `ExportRecord`
- Checkpoints abort CSV/ZIP/folder writers; partial artifacts under the project export root are fail-and-cleanup; originals are never modified or deleted
- Desktop quit can **Quit and cancel export** (POST cancel, wait up to 10s, then SIGTERM)
- Export jobs are still not reclaimed on startup
- No `APP_VERSION` bump, signing, or packaged GUI

### Docs — schedule remaining stretch (S9.00)

- Name Phase 9 remaining-stretch close-out in `develop_plan.md` §1.1 (one GitHub issue per run; do not invent Phase 10)
- Living plan: `docs/plans/2026-09-04-remaining-stretch.md`; umbrella [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160); next product issue is S9.01 export cancel ([#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164))
- No `APP_VERSION` bump, signing, or product behavior change in S9.00

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
