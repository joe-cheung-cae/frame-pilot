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

GET    /api/projects/{project_id}/photos
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
  "created_at": "2026-06-02T11:30:00Z",
  "updated_at": "2026-06-02T12:00:00Z"
}
```

`last_processed_at` is `null` until the first processing job completes. v2 currently uses `copy` mode, which copies imported photos into the local project directory without modifying original source files.

`DELETE /api/projects/{project_id}` removes the project and related local metadata records from the app database. It does not delete the project folder, copied originals, generated previews, or exports from disk.

## Import Response

`POST /api/projects/{project_id}/imports` accepts multiple files under the `files` form field.

The response contains both imported photos and skipped files:

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
      "capture_time": "2026-01-02T03:04:05",
      "camera_model": "FramePilotCam",
      "lens_model": "FramePilot 35mm",
      "focal_length": "35",
      "aperture": "2.8",
      "shutter_speed": "1/125",
      "iso": 400,
      "perceptual_hash": "ff00ff00ff00ff00",
      "thumbnail_path": ".../thumbnails/frame.webp",
      "preview_path": ".../previews/frame.webp",
      "processing_state": "imported",
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
  ]
}
```

If every file is skipped, the endpoint returns `422`. Importing new photos invalidates previous groups and AI recommendations, so processing should be run again.
The singular `/api/projects/{project_id}/import` route remains available as a backward-compatible alias.
When EXIF data is available, import records basic capture time, camera, lens, focal length, aperture, shutter speed, and ISO metadata. Numeric EXIF rationals are normalized into stable display strings.
HEIC and RAW extensions such as `.heic`, `.dng`, `.arw`, `.cr3`, and `.nef` are recognized as planned future formats, but v2 currently skips them with explicit unsupported-format reasons instead of attempting local decoding.

## Processing

`POST /api/projects/{project_id}/process` creates a local background processing job and returns a `ProcessingJob` with `202 Accepted`. Poll `GET /api/projects/{project_id}/jobs/{job_id}` until the job reaches `complete` or `failed`.
If an earlier queued or running processing job has not updated for more than 30 minutes, the next process request marks that stale job as failed and starts a replacement job.

`GET /api/projects/{project_id}/jobs` returns processing jobs newest-first. The processing UI uses this to resume polling a queued or running job after page reloads or navigation.

A processing job includes:

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
  "started_at": "2026-06-02T12:00:00Z",
  "completed_at": null
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
If a whole processing job fails before individual photos complete, photos still marked as in-progress are returned to `imported` with the interruption reason so the next processing run can retry them.

`GET /api/projects/{project_id}/photos` returns photos ordered for review by group, AI recommendation priority, score, and filename. Optional `limit` and `offset` query parameters can page large projects; omitting them preserves the full-list response.

`PATCH /api/projects/{project_id}/photos/{photo_id}` and `PATCH /api/projects/{project_id}/photos/batch` update review status and star rating. Requests must include at least one of `user_status` or `star_rating`.

`GET /api/projects/{project_id}/groups` returns groups in stable creation order for group-by-group review. Each group includes a JSON `score_summary` string with the top photo id, best score, score gap, confidence label, recommendation counts, and a short deterministic explanation.

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

Exports are written under mode-specific local project directories: `exports/csv/`, `exports/zip/`, and `exports/folders/`. Repeated exports use unique paths. Requests with no matching photos return `422` and do not write an export artifact. ZIP and folder exports fail if any selected local original copy is missing. If artifact creation fails, the API returns `500`, removes partial output when possible, and keeps a local export history record with `status` set to `failed` and `error_message` set.

CSV exports include filename, original path, capture and camera metadata, user status, star rating, group id, AI recommendation, overall and technical scores, face and eye-open signals, image dimensions, and the recommendation explanation.

Export records can be listed newest-first:

```text
GET /api/projects/{project_id}/exports
```

The response is an array of export records with the same shape as the creation response. The web export page uses this endpoint to show local export history, selected counts, status summaries, output paths, and download links for CSV and ZIP records.

Completed CSV and ZIP exports can be downloaded from:

```text
GET /api/projects/{project_id}/exports/{export_id}/download
```

Folder exports are available at their local output path and are not downloaded as a single artifact.
Failed or still-running export records return `409` from the download endpoint.
The singular `/api/projects/{project_id}/export` routes remain available as backward-compatible aliases.

XMP sidecar export is not implemented in v2.0. The planned approach is documented in [Export Interoperability](export_interoperability.md).

Experimental face and eye-open fields are local heuristic scores derived from simple color, shape, luminance, and sharpness checks. They are not generated by a bundled professional face detection model and should be treated as weak MVP ranking hints.
