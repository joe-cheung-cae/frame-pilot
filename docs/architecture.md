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

Projects record storage policy metadata with `source_mode`, `source_root_path`, and `schema_version`. v2 currently creates projects in `copy` mode; reference-mode metadata is reserved for later work and does not change the current copy-on-import safety behavior.

Processing uses local FastAPI background tasks. `POST /api/projects/{project_id}/process` creates a `ProcessingJob` and returns it immediately, then the worker updates status, current step, item counts, failure counts, progress percentage, start time, and completion time in SQLite. The processing screen polls `GET /api/projects/{project_id}/jobs/{job_id}` until the job completes or fails.

Processing is idempotent for unchanged completed projects: if all photos are already marked `processed`, project counts match, and groups cover the full photo set, a new processing job completes without clearing or rebuilding groups. New imports still invalidate processing state and require a full grouping/ranking run.

Photos keep their own local `processing_state` and `processing_error` fields so incomplete or skipped items can be inspected without modifying original files. Import creates photos in the `imported` state, processing moves them through `processing`, and the job records each photo as `processed` or `failed`.

The processing validation stage checks that generated thumbnails and previews still exist before grouping. Missing derived files are regenerated from the local copied original when possible. If the copied original is unavailable or regeneration fails, the error is recorded on the affected photo and counted as a failed item.

Import is tolerant of mixed file selections: supported images are copied into `originals/`, derivatives are generated in `thumbnails/` and `previews/`, and unsupported or unreadable files are reported as skipped. Adding new imports invalidates existing grouping and recommendation metadata because the review set has changed.

Imported photos record deterministic local file identity metadata for the copied original: extension, file size, copy modification time, SHA-256 content hash, project copy path, and source identity. This supports future resumable processing without changing or deleting original photo files.

Grouping uses deterministic candidate windows and union-find. Candidate pairs are limited by capture-time or filename proximity, checked for compatible dimensions, camera model, and focal length when those fields are available, then merged when their stored perceptual hashes are close enough or, when hashes are unavailable, their local embedding similarity meets the grouping threshold.

Ranking persists a deterministic `score_summary` JSON string on each group. The summary records the representative photo, best score, gap to the next candidate, recommendation counts, and a low, medium, or high confidence label so the review UI can inspect group-level ranking strength without recalculating scores.

Exports are local artifacts written under `exports/`. Each export record has a unique output path and records the selected statuses plus selected photo count. Empty exports are rejected before an artifact is written. CSV and ZIP artifacts can be downloaded through the local API; folder exports expose the local output path. Export records remain in SQLite and can be listed for local export history.

Future sidecar-oriented export should write derived metadata files under project-controlled output directories, never next to or over original source files unless the user explicitly chooses that workflow in a later release.

SQLite initialization also creates indexes for large-project review and export queries: photo review ordering by project, status-filtered export selection, project group listing, and active processing-job lookup.
