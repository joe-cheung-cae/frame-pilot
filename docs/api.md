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
```

Generated thumbnails and previews are served from:

```text
GET /api/assets/{project_id}/{thumbnails|previews}/{filename}
```

## Import Response

`POST /api/projects/{project_id}/import` accepts multiple files under the `files` form field.

The response contains both imported photos and skipped files:

```json
{
  "imported": [
    {
      "id": "photo-id",
      "filename": "frame.jpg",
      "thumbnail_path": ".../thumbnails/frame.webp",
      "preview_path": ".../previews/frame.webp",
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

`POST /api/projects/{project_id}/process` runs synchronously in the MVP and returns a `ProcessingJob`. A completed job means grouping, ranking, and recommendation explanations have been rebuilt for the current imported photo set.

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
