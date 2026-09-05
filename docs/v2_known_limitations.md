# FramePilot v2 Known Limitations

> Language: **English** | [中文](v2_known_limitations.zh.md)

This document lists the accepted v2.0 limitations for the local MVP-plus release candidate. These are product boundaries, validation caveats, and engineering constraints rather than hidden defects.

## Local-Only Scope

FramePilot v2.0 is a local web application backed by a local FastAPI server and SQLite database. It does not provide cloud sync, online collaboration, user accounts, payment, telemetry requirements, remote photo processing, or mobile access.

## Supported File Formats

v2.0 supports local import and processing for:

- JPEG
- PNG
- WebP
- HEIC / HEIF stills (local `pillow-heif` decode; WebP derivatives; original bytes exported)
- AVIF stills (`.avif` only; Pillow native `AvifImagePlugin`; WebP derivatives; original bytes exported)
- RAW with an embedded preview (`.dng`, `.arw`, `.cr3`, `.nef`; copy original bytes; LibRaw `extract_thumb` only; WebP derivatives from preview RGB; original bytes exported)

Unsupported files are reported locally instead of uploaded or decoded remotely.

## Deferred Formats

Full RAW develop (demosaic / `postprocess`) remains deferred. RAW files without an embedded preview are skipped with `RAW file has no embedded preview; FramePilot does not demosaic` and are not copied into `originals/`. Extra RAW extensions such as `.cr2`, `.raf`, `.orf`, and `.rw2` are not accepted. HEIC/HEIF and AVIF stills import locally; Live Photo `.mov` companions, `.avifs` sequences, and HDR/gain-map tone mapping are not implemented. XMP is not written on import, into `originals/`, beside camera files, or into image bytes.

`pillow-heif` is BSD-3-Clause. Its wheels ship **LGPL** `libheif` (and codecs) inside the API/sidecar runtime. FramePilot does not vendor libheif source into this MIT tree.

`rawpy` is MIT. Its wheels ship **LGPL-2.1 / CDDL** LibRaw inside the API/sidecar runtime. FramePilot does not vendor LibRaw source into this MIT tree.

## Background Job Durability

Import and processing work uses FastAPI `BackgroundTasks` in the local API process (or the optional local worker entrypoint). Jobs have visible progress, stale detection (lease heartbeat 2 minutes when set, otherwise `updated_at` 10 minutes), and retry paths. They are durable across API process exits by default: if the API process stops during work, the next startup marks leftover active jobs `interrupted` and automatically resumes them.

**Reclaim on by default (Phase 6.1, [#105](https://github.com/joe-cheung-cae/frame-pilot/issues/105)):** on startup, leftover active import/processing jobs are marked `interrupted` and automatically resume import derivatives (and clear/rebuild interrupted processing) in-process. A local worker entrypoint is also available via `npm run worker` / `python -m app.worker`. Set `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` (or `false`/`no`/`off`) to opt back into the legacy fail-and-retry behavior, where leftover active jobs are marked failed on the next startup so the user can retry manually. Export jobs still fail-and-cleanup on restart either way. See [Phase 6 plan](plans/2026-08-29-phase6-durable-jobs.md).

Processing is intentionally blocked while the same project has an active import derivative job. Direct process requests return `409 Conflict`, and the project list, dashboard, processing page, and culling workspace send users back to import progress until the import job reaches a terminal state.

If a processing job becomes stale after committing partial groups, cleanup clears partial groups, removes group assignments, returns processed or in-progress photos to retryable imported state, and resets the project processed count to zero. This prevents stale partial recommendations from being reviewed as if processing completed.

## Cancellation Semantics

Import, processing, and export cancellation is cooperative. A cancel request persists a flag and the background worker checks it at safe checkpoints. Cancellation is not a hard process kill, may not stop immediately, and never modifies or deletes source originals. Import cancel keeps completed derivatives and leaves unprocessed photos retryable. Processing cancel then resets groups: in-flight photos return to `imported`, `user_status` and `star_rating` stay, and import derivatives stay. Re-run grouping with `POST /process`; `/retry` remains import-only. Export cancel finalizes the job as `cancelled` and fail-and-cleanup the linked export record (`failed`): partial CSV/ZIP/folder artifacts under the project export root are removed; paths outside that root stay. Re-run export with a new `POST /export`. Export jobs are not reclaimed.

Desktop close with an active import, processing, or export job can POST that same cancel route, wait up to 10 seconds, then SIGTERM the sidecar (Keep working / Quit and cancel import or processing or export / Quit anyway). By default the next launch marks leftover import/processing jobs `interrupted` and reclaims them; leftover exports still fail-and-cleanup. With `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` leftover import/processing jobs are instead marked `failed` via the legacy startup sweep. A hard kill is not labelled `cancelled`.

Processing pause is cooperative and distinct from cancel (`POST .../jobs/{job_id}/pause`, `pause_requested`). The worker stops at a safe checkpoint without a `cancelled` finalize, clears partial groups, and marks the job `paused`. Resume is clear-and-rerun via a new `POST /process`; in-place continue-hash-mid-batch is not implemented. Import and export jobs cannot be paused. Desktop quit still cancels rather than pauses.

## Retry Semantics

Import retry is for failed, `complete_with_errors`, stale-failed, and cancelled import jobs. Retry creates a new import job, preserves existing Photo IDs, `user_status`, and `star_rating`, reuses valid derivatives, and regenerates missing derivatives from the local copied original when possible. Retry does not introduce an external queue or re-register a new external source folder; with startup reclaim on (the default), interrupted imports also finish in-process after restart.

## Performance Caveats

Large imports remain compute-heavy. Generated 100, 500, and 1,000 photo real browser-backend workflows pass on the recorded local machine, and 2,000 seeded metadata culling passes, but 2,000 real browser-backend import/process/review is not verified by default. Full-resolution camera JPEG diversity, long review sessions, and operating-system memory pressure remain under-measured.

## Browser Memory Measurement Caveats

Browser benchmark heap values come from Chromium smoke metrics such as `performance.memory` or CDP metrics when available. They are not full browser process RSS, decoded image memory, GPU memory, cross-browser memory, or operating-system pressure metrics.

## Synthetic Benchmark Caveats

Generated JPEG benchmarks are useful for repeatability and regression detection. They do not replace real-world/manual algorithm validation with non-private camera-like photo sets. Synthetic images can underrepresent realistic noise, lens behavior, subject movement, lighting, compression artifacts, and creative intent.

The release-owner decision record is `docs/v2_rc2_validation_decision.md`. A Tier B non-private Openverse CC0/PDM photograph pass is recorded in `docs/v2_real_world_validation_notes.md` (2026-08-17) and supersedes the earlier rc2 waiver. Synthetic JPEG benchmarks still do not replace that manual review.

## Grouping And Ranking Heuristic Limits

Grouping and ranking are deterministic recommendation aids. They can false-merge visually similar but unrelated scenes, miss groups with sparse metadata or large filename gaps, rank a technically clean but less meaningful frame above a better creative choice, or produce low-confidence recommendations for ambiguous sets. Users must keep final control through manual statuses and star ratings.

## Face And Eye-Open Heuristic Limits

Face and eye-open scores are lightweight local heuristics, not professional face detection, landmark detection, eye-state detection, identity recognition, or biometric analysis. They can miss faces, misread unusual lighting or skin tones, fail with profiles or occlusion, and create false positives on skin-colored objects.

## Export Limitations

CSV, ZIP, and folder exports run as local background jobs with progress and stale detection. Optional XMP sidecars (`include_xmp`, default off) are written only under the project export directory: next to folder copies and as ZIP members. CSV stores the flag but writes no `.xmp` files. Sidecars are never written into `originals/`, beside camera originals, or into image bytes. This is not a tested Lightroom/Capture One GUI round-trip. Folder exports expose a local output path rather than a browser download artifact. Exported files and ZIPs are generated artifacts and must not be committed.

ZIP and folder exports require selected source files to resolve inside the project `originals/` directory. This is a defense-in-depth guard for corrupted metadata; it also means file exports can fail if the local copied original is missing or no longer resolves inside project storage.

## Filesystem And Path Assumptions

Projects are stored in local project directories. v2.0 copies imported originals into project storage, writes derivatives and exports separately, and guards asset/export paths against escaping the project root. It does not automatically rescan external source folders, track removable-drive lifecycle, or manage network-share consistency.

## SQLite Assumptions

The app assumes single-user local SQLite access. It is not designed for multi-user concurrent editing, shared remote databases, or distributed project state. The app enables SQLite WAL with a bounded busy timeout for local reader/writer concurrency during import and processing; this remains a single-process local tuning choice, not multi-user database support.

## Unsupported Scenarios

v2.0 does not support cloud libraries, shared team projects, automatic original deletion, remote AI processing, large bundled AI models, online galleries, Lightroom replacement editing, or mobile-first workflows.

## Desktop 2.1

The installable desktop app (`2.1.0-desktop`) shares the same local API and culling UI with extra shell constraints:

- Import and processing jobs are durable by default across sidecar kill or app quit: leftover jobs are marked `interrupted` and reclaimed on the next launch. Set `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` to opt back into marking stale jobs failed on the next launch instead (exports still fail-and-cleanup either way).
- HEIC/HEIF stills and RAW with an embedded preview import locally (same as the web app). RAW without a preview is skipped with a local message.
- **Check for updates** is Help-menu only (no launch-time network). It queries GitHub Releases and does not download or install. A missing manifest is a non-fatal no-op. Unsigned builds still launch. Users still install new builds manually.
- CI is **signing-ready**: Authenticode / Developer ID + notarization run when the full GitHub Actions secret set is present. Missing secrets keep the **unsigned** upload green. See [Desktop Code Signing Runbook](desktop_signing.md).
- **Packaged macOS DMG GUI lifecycle is skip, not pass** (S9.12, [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172), `2026-09-05T12:31:10Z`). The 开发 host was Linux/WSL2 (`uname -s` not Darwin); the DMG was not mounted or launched. Skip is not a macOS pass. Windows NSIS GUI lifecycle is recorded on [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) (Windows-only). See [Desktop Testing Matrix](desktop_testing.md).
- **WSL may not run the GUI** (needs rustc ≥1.88 and a display); HTTP/API smoke still works. See [Desktop Testing Matrix](desktop_testing.md).
- Storage is **copy mode only** (no reference-in-place of camera cards).
- Desktop **detached preview** (View → Detached preview, or the culling toolbar) opens a second WebView for the current culling photo and shared selection. Bare culling keys apply to the focused window only. Create failure is non-fatal and keeps the in-shell preview. Closing the preview window does not quit the app. No extra `fs:` / `shell:` capabilities were added.
- Import derivative workers default to **1**. Settings may raise that to **2–4** for the next import job (`GET`/`PATCH /api/settings`, `{data_dir}/app_settings.json`). Processing stays one job per project. There is no processing-worker pool, Redis, or Celery.
- Desktop **Change data directory** copies the current app data directory into an empty D2.00-authorized folder and rewrites stored paths whose prefix is the old data dir. The old tree is not deleted. Camera cards and other source folders are not moved or modified. `FRAMEPILOT_DATA_DIR` still wins over `{anchor}/data_dir.json`. No extra `fs:` / `shell:` capabilities.
- Optional **system tray** (D3.06) shows job progress in the tooltip. **Show** restores the main window; **Quit** uses the same running-job dialog as File → Quit. Window close is still quit, not hide-to-tray. Tray create may fail on headless or some Linux desktops and is non-fatal. No tray-related `fs:` / `shell:` capabilities were added.

End-user steps: [Desktop User Guide](desktop_user_guide.md).
