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

Unsupported files are reported locally instead of uploaded or decoded remotely.

## Deferred Formats

HEIC and RAW formats such as DNG, ARW, CR3, and NEF are deferred. v2.0 may recognize these extensions enough to show explicit unsupported-format messages, but it does not decode them, extract embedded RAW previews, or write RAW sidecars.

## Background Job Durability

Import and processing work uses FastAPI `BackgroundTasks` in the local API process. Jobs have visible progress, stale detection, and retry paths, but they are not durable across API process exits. If the API process stops during work, polling later marks stale queued or running jobs as failed so the user can retry when possible.

Processing is intentionally blocked while the same project has an active import derivative job. Direct process requests return `409 Conflict`, and the project list, dashboard, processing page, and culling workspace send users back to import progress until the import job reaches a terminal state.

If a processing job becomes stale after committing partial groups, cleanup clears partial groups, removes group assignments, returns processed or in-progress photos to retryable imported state, and resets the project processed count to zero. This prevents stale partial recommendations from being reviewed as if processing completed.

## Cancellation Semantics

Import cancellation is cooperative. A cancel request persists a flag and the background worker checks it at safe checkpoints. Cancellation is not a hard process kill, may not stop immediately, keeps completed derivatives, leaves unprocessed photos retryable, and never modifies or deletes source originals.

Desktop close with an active import can POST that same cancel route, wait up to 10 seconds, then SIGTERM the sidecar. Close with an active processing job cannot cancel it (`POST .../cancel` returns 422); quit-anyway SIGTERMs the sidecar and the next launch marks the job `failed` via the startup sweep. A hard kill is not labelled `cancelled`. Processing jobs still have no cancel route.

## Retry Semantics

Import retry is for failed, `complete_with_errors`, stale-failed, and cancelled import jobs. Retry creates a new import job, preserves existing Photo IDs, `user_status`, and `star_rating`, reuses valid derivatives, and regenerates missing derivatives from the local copied original when possible. Retry does not make jobs durable across API restarts and does not re-register a new external source folder.

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

CSV, ZIP, and folder exports run as local background jobs with progress and stale detection. XMP sidecar export is planned but not implemented. Folder exports expose a local output path rather than a browser download artifact. Exported files and ZIPs are generated artifacts and must not be committed.

ZIP and folder exports require selected source files to resolve inside the project `originals/` directory. This is a defense-in-depth guard for corrupted metadata; it also means file exports can fail if the local copied original is missing or no longer resolves inside project storage.

## Filesystem And Path Assumptions

Projects are stored in local project directories. v2.0 copies imported originals into project storage, writes derivatives and exports separately, and guards asset/export paths against escaping the project root. It does not automatically rescan external source folders, track removable-drive lifecycle, or manage network-share consistency.

## SQLite Assumptions

The app assumes single-user local SQLite access. It is not designed for multi-user concurrent editing, shared remote databases, or distributed project state. The app enables SQLite WAL with a bounded busy timeout for local reader/writer concurrency during import and processing; this remains a single-process local tuning choice, not multi-user database support.

## Unsupported Scenarios

v2.0 does not support cloud libraries, shared team projects, automatic original deletion, remote AI processing, large bundled AI models, online galleries, Lightroom replacement editing, or mobile-first workflows.
