# Architecture

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
  cache/
```

The browser talks only to the local API. Original files are copied into the local project folder during import and are not modified after that.

Processing is synchronous in this first MVP scaffold. The API still creates `ProcessingJob` records so the workflow can be moved to background workers later without changing the UI contract.

