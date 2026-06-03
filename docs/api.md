# API

Base URL during development: `http://127.0.0.1:8000`.

Implemented endpoints:

```text
POST   /api/projects
GET    /api/projects
GET    /api/projects/{project_id}
DELETE /api/projects/{project_id}

POST   /api/projects/{project_id}/import
POST   /api/projects/{project_id}/process
GET    /api/projects/{project_id}/jobs/{job_id}

GET    /api/projects/{project_id}/photos
GET    /api/projects/{project_id}/photos/{photo_id}
PATCH  /api/projects/{project_id}/photos/{photo_id}

GET    /api/projects/{project_id}/groups
GET    /api/projects/{project_id}/groups/{group_id}

POST   /api/projects/{project_id}/export
GET    /api/projects/{project_id}/export/{export_id}
GET    /api/projects/{project_id}/export/{export_id}/download
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
  "total_images": 12,
  "processed_images": 10,
  "last_processed_at": "2026-06-02T12:00:00Z",
  "created_at": "2026-06-02T11:30:00Z",
  "updated_at": "2026-06-02T12:00:00Z"
}
```

`last_processed_at` is `null` until the first processing job completes.

## Import Response

`POST /api/projects/{project_id}/import` accepts multiple files under the `files` form field.

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

## Processing

`POST /api/projects/{project_id}/process` creates a local background processing job and returns a `ProcessingJob` with `202 Accepted`. Poll `GET /api/projects/{project_id}/jobs/{job_id}` until the job reaches `complete` or `failed`.

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

Each photo also exposes local processing state:

- `imported`: the photo has been imported and is waiting for grouping/ranking.
- `processing`: a current processing job is working on the photo.
- `processed`: grouping/ranking completed for the photo.
- `failed`: the job skipped the photo and recorded `processing_error`.

`GET /api/projects/{project_id}/photos` returns photos ordered for review by group, AI recommendation priority, score, and filename.

`GET /api/projects/{project_id}/groups` returns groups in stable creation order for group-by-group review.

## Export

`POST /api/projects/{project_id}/export` accepts:

```json
{
  "mode": "csv",
  "statuses": ["Pick", "Maybe"]
}
```

Supported modes are `csv`, `folder`, and `zip`. Supported statuses are `Pick`, `Maybe`, `Reject`, and `Unreviewed`.

The response includes the number of exported photos and the local output path:

```json
{
  "id": "export-id",
  "project_id": "project-id",
  "mode": "csv",
  "status": "complete",
  "selected_count": 12,
  "statuses": "[\"Pick\", \"Maybe\"]",
  "output_path": ".../exports/selection-export-id.csv",
  "created_at": "2026-06-02T12:00:00Z"
}
```

Exports are written under the local project `exports/` directory. Repeated exports use unique paths. Requests with no matching photos return `422` and do not write an export artifact.

CSV exports include filename, original path, user status, star rating, group id, AI recommendation, overall and technical scores, face and eye-open signals, image dimensions, and the recommendation explanation.

CSV and ZIP exports can be downloaded from:

```text
GET /api/projects/{project_id}/export/{export_id}/download
```

Folder exports are available at their local output path and are not downloaded as a single artifact.

Experimental face and eye-open fields are local heuristic scores derived from simple color, shape, luminance, and sharpness checks. They are not generated by a bundled professional face detection model and should be treated as weak MVP ranking hints.
