# Architecture

> Language: **English** | [中文](architecture.zh.md)

FramePilot is a local web application split into two apps:

- `apps/web`: Next.js UI for project creation, import, processing, culling, and export.
- `apps/api`: FastAPI backend that owns SQLite metadata, image derivatives, scoring, grouping, recommendations, and export writing.

The backend stores each project under:

```text
.framepilot-data/projects/<project-id>/
  originals/
  thumbnails/
  previews/
  exports/
    csv/
    zip/
    folders/
  cache/
    hashes/
    embeddings/
    jobs/
  logs/
```

The browser talks only to the local API. Original files are copied into the local project folder during import and are not modified after that.

Projects record storage policy metadata with `source_mode`, `source_root_path`, and `schema_version`. v2 currently creates projects in `copy` mode; reference-mode metadata is reserved for later work and does not change the current copy-on-import safety behavior. During project creation, users can optionally choose a custom local project data folder; leaving it blank uses FramePilot's managed project directory.
The home project list and import screen show the local project data path so users can see where generated metadata, previews, and exports are stored.

Import is split into a synchronous upload/register phase and an in-process background derivative phase. The request receives selected local files, validates supported extensions (JPEG, PNG, WebP, HEIC, HEIF, AVIF), copies accepted files into the project `originals/` folder, records file identity metadata, creates or reuses `Photo` records, creates a `ProcessingJob` with `job_type` set to `import`, and returns while new photos are still marked `processing`. A FastAPI `BackgroundTasks` worker then opens a fresh database session, generates thumbnails and previews, extracts metadata, computes quality scores, perceptual hashes, and lightweight embeddings, updates per-photo state, and completes the import job as `complete`, `complete_with_errors`, `failed`, or `cancelled`. HEIC/HEIF stills are decoded with local `pillow-heif` (`register_heif_opener`); AVIF stills use Pillow’s native `AvifImagePlugin`; derivatives stay WebP; scoring and grouping use decoded RGB. Export copies the original HEIC/HEIF/AVIF bytes. RAW stays skipped.

The import page polls the returned job id after the response, so long imports show derivative progress and do not leave the user waiting on one opaque request. It also loads the latest import job history so stale, failed, `complete_with_errors`, `cancelled`, and reclaimable `interrupted` import jobs remain visible after navigation or page reload. Stale detection prefers a worker lease heartbeat (2 minutes) when present, otherwise `updated_at` (10 minutes). This remains a local in-process background task by default; with startup reclaim on (the default since Phase 6.1), derivative work resumes in-process after an API process restart instead of failing outright.

Import cancellation is cooperative. `POST /api/projects/{project_id}/jobs/{job_id}/cancel` persists `cancellation_requested` for a queued or running import job, and the background derivative worker checks that flag before each photo and after each completed photo-level derivative/scoring/hash pass. Cancellation is not a hard process kill. The worker exits only at a safe checkpoint, marks the job `cancelled`, records `cancelled_at`, keeps completed derivatives in place, leaves unprocessed photos in retryable state, and never deletes or modifies original files.

Failed, `complete_with_errors`, and `cancelled` import jobs are retryable through a local retry endpoint. Retry creates a new import job and reruns only recovery work for photos whose generated derivatives are missing or whose import state is still `processing` or `failed`. It preserves existing photo IDs, review status, star ratings, copied originals, and already valid thumbnail/preview files. Missing derivatives are regenerated from the local copied original when possible; unrecoverable photos stay in `failed` state with `processing_error` and are counted in the retry job. Retry does not introduce an external or cloud queue. With startup reclaim on (the default; set `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` to disable), interrupted import jobs also finish via in-process reclaim after restart without re-uploading.

Processing also uses local FastAPI background tasks. `POST /api/projects/{project_id}/process` creates a `ProcessingJob` and returns it immediately, then the worker updates status, current step, item counts, failure counts, progress percentage, start time, and completion time in SQLite. The processing screen polls `GET /api/projects/{project_id}/jobs/{job_id}` until the job completes, fails, is cancelled, or is paused.
Processing cancellation uses the same `POST /api/projects/{project_id}/jobs/{job_id}/cancel` route and is cooperative, not a hard process kill. Cancelled processing clears groups and returns in-flight photos to `imported`; originals, import derivatives, `user_status`, and `star_rating` stay. Reclaim honors a pending cancel and does not re-queue. Re-run grouping with `POST /process`; `/retry` remains import-only. Processing pause uses a distinct `POST /api/projects/{project_id}/jobs/{job_id}/pause` route and `pause_requested` flag. The worker exits at the same checkpoints without a `cancelled` finalize, clears partial groups, and marks the job `paused`. Resume is a new `POST /process` (clear-and-rerun), not in-place continue. Export cancellation uses the same cancel route: create persists a `ProcessingJob` with `job_type="export"` and the same id as the `ExportRecord`; checkpoints abort then fail-and-cleanup partial artifacts under the project export root. Export jobs are not reclaimed.
Processing is blocked while the same project has a queued or running import job. Project detail/list responses expose the active import job as lightweight workflow state, the processing endpoint returns `409 Conflict` for direct requests during active import, and the project list, dashboard, processing page, and culling workspace route users back to import progress until derivative generation reaches a terminal state.
If a queued or running processing job goes stale (lease heartbeat older than 2 minutes when set, otherwise `updated_at` older than 10 minutes), the project and jobs endpoints mark it failed, clear any partial groups, remove photo group assignments, reset processed or in-progress photos to retryable imported state, and set the project processed count back to zero. A later process request can then start a replacement job and rebuild groups cleanly. API process startup fails leftover queued/running/interrupted jobs immediately only when reclaim is explicitly disabled (`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0`); by default (see the Phase 6.1 update below) leftover work is marked `interrupted` and reclaimed instead, so a restart cannot leave the workspace blocked for the full stale window either way.

Decision as of 2026-06-04: v2.0 kept local in-process jobs rather than a separate worker before release, for visible progress, stale recovery, retryable state, and simpler packaging.

Update 2026-08-29 (Phase 6 complete as opt-in): durable local reclaim was delivered behind `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=1`. Checkpoint and lease fields live on `ProcessingJob`; startup marks leftover import/processing jobs `interrupted` and reclaims them in-process (imports resume derivative work; processing clears partial groups then re-queues). A local `npm run worker` / `python -m app.worker` entrypoint can reclaim with a file lock. Reclaim never runs on `GET /api/projects`. Exports stay fail-on-restart. See `docs/plans/2026-08-29-phase6-durable-jobs.md`.

Update 2026-08-31 (Phase 6.1, [#105](https://github.com/joe-cheung-cae/frame-pilot/issues/105)): startup reclaim is now the default. `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` unset (or any truthy value) enables reclaim; set it to `0`/`false`/`no`/`off` to opt back into the legacy fail-and-retry startup sweep. All other Phase 6 behavior (checkpoints, leases, worker entrypoint, export fail-on-restart) is unchanged.

Update 2026-09-03 (Phase 7, [#145](https://github.com/joe-cheung-cae/frame-pilot/issues/145) / [#146](https://github.com/joe-cheung-cae/frame-pilot/issues/146)): the same cancel route cooperatively cancels processing jobs as well as imports. Cancelled processing clears groups; originals stay unchanged.

Update 2026-09-05 (Phase 9 S9.01, [#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164)): the same cancel route cooperatively cancels export jobs. Partial CSV/ZIP/folder output is fail-and-cleanup; originals stay unchanged; leftover exports are still not reclaimed.

Update 2026-09-05 (Phase 9 S9.02, [#161](https://github.com/joe-cheung-cae/frame-pilot/issues/161)): processing jobs can be paused with a distinct `pause_requested` flag. The worker exits at existing checkpoints without a `cancelled` finalize and without reviewable partial groups. Resume is `POST /process` clear-and-rerun, not in-place.

Processing is idempotent for unchanged completed projects: if all photos are already marked `processed`, project counts match, generated thumbnails and previews still exist, and groups cover the full photo set, a new processing job completes without clearing or rebuilding groups. New imports or missing generated files still invalidate the shortcut and require local validation before grouping/ranking completes. Import is idempotent for the conservative same-upload case: if a selected file has the same uploaded filename and SHA-256 content hash as an existing project photo, and that photo's thumbnail and preview still exist, the existing record and derivatives are reused without resetting user status or creating another copy. Different filenames with identical bytes are still treated as distinct imports.

Photos keep their own local `processing_state` and `processing_error` fields so incomplete or skipped items can be inspected without modifying original files. Import registration creates new photos in the `processing` state until derivative generation finishes, then marks successful photos `imported`; later grouping/ranking moves them through `processing` to `processed` or `failed`.

The processing validation stage checks that generated thumbnails and previews still exist before grouping. Missing derived files are regenerated from the local copied original when possible. If the copied original is unavailable or regeneration fails, the error is recorded on the affected photo and counted as a failed item.

Import is tolerant of mixed file selections: supported extensions are copied into `originals/`, derivatives are generated in `thumbnails/` and `previews/`, and unsupported extensions or derivative failures are reported through skipped-file lists and import job failure counts. If at least one file succeeds and at least one file is skipped or fails during derivative work, the import job completes with `complete_with_errors`; if every accepted file fails, the job completes as `failed`. Browser folder selection imports file copies through the upload flow; source folders are not tracked for automatic rescan yet. Adding new imports invalidates existing grouping and recommendation metadata because the review set has changed.

Imported photos record deterministic local file identity metadata for the copied original: extension, file size, copy modification time, SHA-256 content hash, project copy path, and source identity. This supports future resumable processing without changing or deleting original photo files.

Grouping uses deterministic candidate windows and union-find. Candidate pairs are limited by capture-time or filename proximity, checked for compatible dimensions, camera model, and focal length when those fields are available, then merged when their stored perceptual hashes are close enough or, when hashes are unavailable, their local embedding similarity meets the grouping threshold. After merging, groups with capture-time spans larger than the burst window are split into smaller review groups.

Ranking persists a deterministic `score_summary` JSON string on each group. The summary records the representative photo, best score, gap to the next candidate, recommendation counts, and a low, medium, or high confidence label so the review UI can inspect group-level ranking strength without recalculating scores.

Exports are local artifacts written under `exports/`. Each export record has a unique output path and records the selected statuses plus selected photo count. Empty exports are rejected before an artifact is written. CSV and ZIP artifacts can be downloaded through the local API; export output paths can be copied from the web UI, and folder exports expose the local output path. Export creation and download resolve the export root and mode directories before writing or serving artifacts, and reject symlink escapes outside the local project root. ZIP and folder exports also resolve selected source files and require them to stay inside the project `originals/` directory, so corrupted metadata cannot make file exports copy arbitrary local files. Export records remain in SQLite and can be listed for local export history.

Future sidecar-oriented export should write derived metadata files under project-controlled output directories, never next to or over original source files unless the user explicitly chooses that workflow in a later release.

SQLite initialization also creates indexes for large-project review and export queries: photo review ordering by project, status-filtered export selection, processing-state recovery scans, project group listing, active processing-job lookup, newest-first processing history, and newest-first export history.
SQLite is used as a single-user local database with one cached SQLAlchemy engine per resolved database URL. New connections enable `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`, and a bounded `busy_timeout` so background import/processing writers can coexist with status polling readers. Engine and settings caches are cleared together when `FRAMEPILOT_DATA_DIR` changes so tests and local reconfiguration get a fresh engine.

The culling workspace keeps large projects responsive by requesting bounded first pages for photos and groups, then rendering bounded windows for the group sidebar, filmstrip, and compare-mode candidates instead of mounting every matching thumbnail or preview at once. Users can explicitly load the full photo or group list when a review task needs complete in-browser context.
If a generated preview or thumbnail asset fails to load, the workspace records the failed asset URL and renders an explicit local fallback instead of leaving a broken image in the review surface.
Generated asset serving resolves the project root, the asset directory, and the requested file before responding, and rejects symlink escapes outside the local project root.
Dense culling controls expose active filter, group, photo, status, rating, compare, zoom, and preview states with ARIA attributes so keyboard and assistive-technology users can confirm the current review context. The culling filters include processing failures, and the detail panel shows per-photo processing errors when a record could not be fully processed.

The processing page shows active import progress when import derivative work is still running, disables grouping/ranking, and links back to import progress. It also shows current and historical failed-item notices even when the overall job completed, so recoverable per-photo failures are visible before culling or export. Current failed-item notices link directly to the culling workspace with the processing-failures filter selected. It also shows recent local job history from a bounded newest-first query and can increase that limit when the user requests older jobs.

The export page shows the local exports folder before export, keeps status totals lightweight through the status-count API, and keeps export history bounded by loading the most recent records first, with an explicit load-more action for older local export records.

The shell links to a local help page that lists the keyboard shortcuts supported by the culling workspace.

Recent project cards link to the next resumable workflow step and show whether the project should continue with import, processing, or culling. Active-import projects are sent back to import progress rather than processing or culling. Each project also has a dashboard route at `/projects/{project_id}` with local storage details, processing counts, and direct links to import, processing, culling, and export.

The settings page stores browser-local preferences in `localStorage`. The current preference controls the default export status selection and does not require an account or remote service.
