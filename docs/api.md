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

