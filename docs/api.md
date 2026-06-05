# API

Base URL during development: `http://127.0.0.1:8000`.

Implemented endpoints:

```text
GET    /api/health

POST   /api/projects
GET    /api/projects
GET    /api/projects/{project_id}
DELETE /api/projects/{project_id}

POST   /api/projects/{project_id}/imports
POST   /api/projects/{project_id}/process
GET    /api/projects/{project_id}/jobs
GET    /api/projects/{project_id}/jobs/{job_id}
POST   /api/projects/{project_id}/jobs/{job_id}/cancel
POST   /api/projects/{project_id}/jobs/{job_id}/retry

GET    /api/projects/{project_id}/photos
GET    /api/projects/{project_id}/photos/status-counts
GET    /api/projects/{project_id}/photos/{photo_id}
PATCH  /api/projects/{project_id}/photos/{photo_id}
PATCH  /api/projects/{project_id}/photos/batch

GET    /api/projects/{project_id}/groups
GET    /api/projects/{project_id}/groups/{group_id}

POST   /api/projects/{project_id}/exports
GET    /api/projects/{project_id}/exports
GET    /api/projects/{project_id}/exports/{export_id}
GET    /api/projects/{project_id}/exports/{export_id}/download
```

Generated thumbnails and previews are served from:

```text
GET /api/assets/{project_id}/{thumbnails|previews}/{filename}
```

## Project Response

Project responses include image totals and processing metadata:

```json
{
  "id": "project-id",
  "name": "Weekend shoot",
  "root_path": ".../.framepilot-data/projects/project-id",
  "source_mode": "copy",
  "source_root_path": null,
  "total_images": 12,
  "processed_images": 10,
  "last_processed_at": "2026-06-02T12:00:00Z",
  "schema_version": 2,
  "active_import_job": null,
  "created_at": "2026-06-02T11:30:00Z",
  "updated_at": "2026-06-02T12:00:00Z"
}
```

`last_processed_at` is `null` until the first processing job completes. v2 currently uses `copy` mode, which copies imported photos into the local project directory without modifying original source files.
`active_import_job` is the newest non-stale queued or running import job for the project, or `null` when import derivative work is not active. The project list and dashboard use this lightweight field to route active-import projects back to import progress instead of processing or culling.
When `POST /api/projects` omits `root_path` or sends it blank, FramePilot uses the default managed project directory. The project creation UI exposes this as an optional local project data folder field. Custom `root_path` values must point to a usable local directory location. Invalid storage paths return `422` before project metadata is created.

`DELETE /api/projects/{project_id}` removes the project and related local metadata records from the app database. It does not delete the project folder, copied originals, generated previews, or exports from disk.

## Import Response

`POST /api/projects/{project_id}/imports` accepts multiple files under the `files` form field.

The response contains accepted photo records, synchronously skipped files, import counts, and the import job to poll. Newly accepted photos may still have `processing_state` set to `processing` and may not have thumbnail, preview, metadata, score, hash, or embedding fields populated until the background derivative job completes.

```json
{
  "imported": [
    {
      "id": "photo-id",
      "filename": "frame.jpg",
      "file_ext": ".jpg",
      "file_size": 2481203,
      "file_mtime": 1780411200.0,
      "content_hash": "sha256-hex",
      "project_copy_path": ".../originals/frame.jpg",
      "source_identity": "sha256:sha256-hex",
      "capture_time": null,
      "camera_model": null,
      "lens_model": null,
      "focal_length": null,
      "aperture": null,
      "shutter_speed": null,
      "iso": null,
      "perceptual_hash": null,
      "thumbnail_path": null,
      "preview_path": null,
      "processing_state": "processing",
      "processing_error": null,
      "user_status": "Unreviewed",
      "ai_recommendation": "Unreviewed"
    }
  ],
  "skipped": [
    {
      "filename": "notes.txt",
      "reason": "Only JPEG, PNG, and WebP files are supported"
    }
  ],
  "total_files": 2,
  "accepted_files": 1,
  "skipped_files": 1,
  "failed_files": 1,
  "job": {
    "id": "job-id",
    "project_id": "project-id",
    "job_type": "import",
    "status": "running",
    "current_step": "derivative_generation",
    "total_items": 2,
    "processed_items": 0,
    "failed_items": 1,
    "progress_percent": 50.0,
    "error_message": null,
    "cancellation_requested": false,
    "cancelled_at": null,
    "started_at": "2026-06-02T12:00:00Z",
    "completed_at": null,
    "retryable": false
  }
}
```

The import endpoint is upload/register-bound: it returns after supported files are copied into the project, file identity metadata is recorded, photo rows are created or safely reused, and an import job is created. Expensive derivative generation, metadata extraction, scoring, perceptual hashing, and embedding generation continue in a FastAPI in-process background task that opens a fresh database session. Poll `GET /api/projects/{project_id}/jobs/{job_id}` until the import job reaches `complete`, `complete_with_errors`, `failed`, or `cancelled`, then reload photos before assuming previews or scores are ready.

This background path improves request responsiveness and visible progress, but it is not durable across API process exits. A durable local worker would be needed before interrupted derivative jobs can resume automatically after a backend restart.

Import job statuses are:

- `complete`: all selected files imported or were safely reused.
- `complete_with_errors`: at least one file imported or was safely reused, and at least one file was skipped or failed during derivative generation.
- `failed`: every selected file was skipped or every accepted file failed derivative generation.
- `cancelled`: the user requested cooperative cancellation and the local background worker stopped at a safe checkpoint.

If every file is skipped during synchronous validation, the endpoint returns `422` and the failed import job remains visible through `GET /api/projects/{project_id}/jobs`. Importing new photos invalidates previous groups and AI recommendations, so processing should be run again after the import job reaches a terminal state. Re-importing a file with the same uploaded filename and SHA-256 content hash reuses the existing project photo record and existing generated thumbnail/preview when they are still present; this does not create a duplicate record or reset user review status.
The singular `/api/projects/{project_id}/import` route remains available as a backward-compatible alias.
When EXIF data is available, the background derivative job records basic capture time, camera, lens, focal length, aperture, shutter speed, and ISO metadata. Numeric EXIF rationals are normalized into stable display strings.
HEIC and RAW extensions such as `.heic`, `.dng`, `.arw`, `.cr3`, and `.nef` are recognized as planned future formats, but v2 currently skips them with explicit unsupported-format reasons instead of attempting local decoding.

## Jobs

`POST /api/projects/{project_id}/process` creates a local background processing job and returns a `ProcessingJob` with `202 Accepted`. Poll `GET /api/projects/{project_id}/jobs/{job_id}` until the job reaches `complete` or `failed`.
If the same project has a queued or running import job, the process endpoint returns `409 Conflict` instead of starting processing:

```json
{
  "detail": {
    "message": "Import is still running for this project. Wait for the import job to finish before processing.",
    "job_id": "import-job-id"
  }
}
```

Processing can start after the import job reaches a terminal state such as `complete`, `complete_with_errors`, `failed`, or `cancelled`.
If an earlier queued or running processing job has not updated for more than 30 minutes, project and jobs endpoints mark that stale job as failed. Stale processing cleanup clears partial groups, removes photo group assignments, returns processed or in-progress photos to retryable `imported` state with the interruption reason, and resets the project processed count to zero. A later process request can then start a replacement job and rebuild groups from the imported photo set.

`GET /api/projects/{project_id}/jobs` returns project jobs newest-first, including `import` and `processing` jobs. Optional `limit` and `offset` query parameters can page large job histories. The import UI polls the returned import job after upload/register returns, and the processing UI uses job history to resume polling a queued or running processing job after page reloads or navigation. If a queued or running import job has not updated for more than 30 minutes, the jobs endpoints mark it failed with `current_step` set to `failed - stale`; this keeps interrupted local imports from remaining active forever without retrying or modifying photos.

`POST /api/projects/{project_id}/jobs/{job_id}/cancel` requests cooperative cancellation for a queued or running import job. It sets `cancellation_requested` and returns the updated job with `202 Accepted`; terminal import jobs return as a safe no-op with `200 OK`. This endpoint does not kill the API process, delete original files, delete copied originals, or remove generated derivatives. The background worker checks the request before each photo and after each photo-level derivative/scoring/hash pass, then marks the job `cancelled` with `cancelled_at` and `completed_at` once it reaches a safe checkpoint. Already completed photo derivatives remain cached, while unprocessed photos stay retryable.

`POST /api/projects/{project_id}/jobs/{job_id}/retry` retries failed, `complete_with_errors`, or `cancelled` import jobs. It creates a new local import job and reruns derivative/scoring/hash/embedding work for project photos whose generated thumbnail or preview is missing, or whose import state is still `processing` or `failed`. It does not re-register uploaded files, duplicate photo records, reset `user_status`, reset `star_rating`, delete generated derivatives, delete copied originals, or modify source photos. Existing valid thumbnail and preview files are reused; missing derivatives are regenerated from the local copied original when possible. If some photos recover and others cannot be rebuilt, the retry job finishes as `complete_with_errors` and records failed items on the affected photos. If another import job is already queued or running, retry returns `409`.

A job includes:

```json
{
  "id": "job-id",
  "project_id": "project-id",
  "job_type": "processing",
  "status": "running",
  "current_step": "ranking group 1 of 3",
  "total_items": 12,
  "processed_items": 4,
  "failed_items": 0,
  "progress_percent": 33.33,
  "error_message": null,
  "cancellation_requested": false,
  "cancelled_at": null,
  "started_at": "2026-06-02T12:00:00Z",
  "completed_at": null,
  "retryable": false
}
```

A completed job means grouping, ranking, and recommendation explanations have been rebuilt for the current imported photo set.
If the project is already fully processed and unchanged, a new processing job completes with `current_step` set to `complete - no changes` and leaves existing groups untouched.

Each photo also exposes local processing state:

- `imported`: the photo has been imported and is waiting for grouping/ranking.
- `processing`: a current processing job is working on the photo.
- `processed`: grouping/ranking completed for the photo.
- `failed`: the job skipped the photo and recorded `processing_error`.

Processing validates generated thumbnail and preview files before grouping. Missing derivatives are regenerated from the local copied original when possible; unrecoverable derivative failures are recorded as failed photo items instead of failing the whole job.
If a whole processing job fails before individual photos complete, partial groups are cleared and photos already marked `processed` or still in progress are returned to `imported` with the interruption reason so the next processing run can retry them.

`GET /api/projects/{project_id}/photos` returns photos ordered for review by group, AI recommendation priority, score, and filename. Optional `limit` and `offset` query parameters can page large projects; omitting them preserves the full-list response. The culling workspace requests an initial bounded page for faster first render and exposes an explicit full-load action when complete in-browser context is needed.

`GET /api/projects/{project_id}/photos/status-counts` returns lightweight review status totals without hydrating full photo records:

```json
{
  "Pick": 12,
  "Maybe": 8,
  "Reject": 20,
  "Unreviewed": 60
}
```

The export UI uses this endpoint to calculate selected counts for large projects before submitting an export request.

`PATCH /api/projects/{project_id}/photos/{photo_id}` and `PATCH /api/projects/{project_id}/photos/batch` update review status and star rating. Requests must include at least one of `user_status` or `star_rating`.

`GET /api/projects/{project_id}/groups` returns groups in stable creation order for group-by-group review. Optional `limit` and `offset` query parameters can page large group lists. The culling workspace requests an initial bounded page and exposes an explicit full-load action if the group list may continue. Each group includes a JSON `score_summary` string with the top photo id, best score, score gap, confidence label, recommendation counts, and a short deterministic explanation.

Example group response:

```json
{
  "id": "group-id",
  "project_id": "project-id",
  "group_type": "duplicate",
  "representative_photo_id": "photo-id",
  "photo_count": 2,
  "score_summary": "{\"best_score\": 0.82, \"confidence\": \"medium\", \"explanation\": \"Medium confidence because the top photo leads the next candidate by 0.07.\", \"recommendation_counts\": {\"Maybe\": 1, \"Pick\": 1, \"Reject\": 0, \"Unreviewed\": 0}, \"score_gap\": 0.07, \"top_photo_id\": \"photo-id\"}"
}
```

## Export

`POST /api/projects/{project_id}/exports` accepts:

```json
{
  "mode": "csv",
  "statuses": ["Pick", "Maybe"]
}
```

Supported modes are `csv`, `folder`, and `zip`. Supported statuses are `Pick`, `Maybe`, `Reject`, and `Unreviewed`. Status filters are stored without duplicates in that supported order.

The response includes the number of exported photos and the local output path:

```json
{
  "id": "export-id",
  "project_id": "project-id",
  "mode": "csv",
  "status": "complete",
  "selected_count": 12,
  "statuses": "[\"Pick\", \"Maybe\"]",
  "output_path": ".../exports/csv/selection-export-id.csv",
  "error_message": null,
  "completed_at": "2026-06-02T12:00:01Z",
  "created_at": "2026-06-02T12:00:00Z"
}
```

Exports are written under mode-specific local project directories: `exports/csv/`, `exports/zip/`, and `exports/folders/`. Repeated exports use unique paths. Requests with no matching photos return `422` and do not write an export artifact. ZIP and folder exports fail if any selected local original copy is missing, or if the selected source path resolves outside the project's local `originals/` directory. Missing-file failures keep the missing path in the response detail and export history error message; project-originals containment failures use a path-free safety message. If artifact creation fails, the API returns `500`, removes partial output inside the project export directory when possible, and keeps a local export history record with `status` set to `failed` and `error_message` set.

CSV exports include filename, project photo id, original path, project copy path, source identity, content hash, file size, file mtime, capture and camera metadata, user status, star rating, group id, AI recommendation, overall and technical scores, face and eye-open signals, image dimensions, recommendation explanation, processing state, and processing error.

Export records can be listed newest-first:

```text
GET /api/projects/{project_id}/exports
```

The response is an array of export records with the same shape as the creation response, ordered newest-first. Optional `limit` and `offset` query parameters can page large export histories. The web export page uses this endpoint to show local export history, selected counts, status summaries, output paths, and download links for CSV and ZIP records, loading the most recent records first and increasing the bounded limit when the user requests older exports.

Completed CSV and ZIP exports can be downloaded from:

```text
GET /api/projects/{project_id}/exports/{export_id}/download
```

Folder exports are available at their local output path and are not downloaded as a single artifact.
Failed or still-running export records return `409` from the download endpoint.
The singular `/api/projects/{project_id}/export` routes remain available as backward-compatible aliases.

XMP sidecar export is not implemented in v2.0. The planned approach is documented in [Export Interoperability](export_interoperability.md).

Experimental face and eye-open fields are local heuristic scores derived from simple color, shape, luminance, and sharpness checks. They are not generated by a bundled professional face detection model and should be treated as weak MVP ranking hints.
