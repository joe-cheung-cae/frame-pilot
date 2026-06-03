# FramePilot v2 Architecture

FramePilot v2 is a local web application with a Next.js frontend and FastAPI backend. The browser talks to a local API, and the backend owns project metadata, local file derivatives, processing, grouping, ranking, and exports.

## System Shape

```text
apps/web  ->  local HTTP API  ->  apps/api
                              ->  SQLite metadata
                              ->  local project directories
```

There are no cloud services, user accounts, payment systems, or remote photo-processing dependencies in the v2.0 architecture.

## Backend Responsibilities

The FastAPI backend owns:

- project creation and project listing
- import validation and local copy-mode storage
- thumbnail and preview generation
- metadata extraction and file identity recording
- processing jobs and progress state
- deterministic scoring, grouping, ranking, and explanations
- photo status and rating updates
- export artifact creation and download safety
- SQLite compatibility migrations and performance indexes

The current route surface is documented in [API](api.md). Route organization can be split later, but route behavior should remain backward compatible unless tests and docs are updated in the same slice.

## Frontend Responsibilities

The Next.js frontend owns:

- project creation and workflow routing
- import, processing, culling, and export screens
- job polling, processing progress display, and paged local processing history
- keyboard-first review state
- optimistic status and rating updates
- bounded first-page loading plus bounded rendering for large photo, group, filmstrip, and compare views
- export selection summaries and paged export history with load-more controls

Reusable review and progress logic should live in `apps/web/src/lib` where practical so unit tests can cover behavior without requiring browser component tests for every small state rule.

## Storage Layout

FramePilot stores local project data under `.framepilot-data/projects/<project-id>/` by default:

```text
project-root/
  originals/
  thumbnails/
  previews/
  cache/
    hashes/
    embeddings/
    jobs/
  exports/
    csv/
    zip/
    folders/
  logs/
```

v2.0 uses copy mode: imported originals are copied into the project directory and then left untouched. `source_mode`, `source_root_path`, and `schema_version` are already recorded so reference mode can be introduced later without changing the current safety baseline.

## Data Model

Core tables:

- `Project`
- `Photo`
- `PhotoGroup`
- `ProcessingJob`
- `ExportRecord`

Photos record source identity, copied path, file metadata, perceptual hash, quality scores, processing state, review status, star rating, group id, and recommendation explanation.

Processing jobs record job type, status, current step, total items, processed items, failed items, progress percent, error message, start time, and completion time.

Export records store mode, status, selected statuses, selected count, output path, and creation time.

## Processing Architecture

Processing uses local FastAPI background tasks with durable SQLite job records:

1. Create or reuse a processing job.
2. Return the job id to the frontend.
3. Poll the job endpoint while queued or running.
4. Validate generated files and regenerate missing derivatives when possible.
5. Build grouping inputs from current photos.
6. Group, rank, explain, and persist results.
7. Mark completed, failed, or skipped photo states.

Rerunning an unchanged fully processed project completes without rebuilding groups. Stale active jobs are marked failed and replaced on the next process request.

## Algorithm Boundaries

Grouping and ranking are deterministic by default:

- grouping uses candidate windows, metadata compatibility, perceptual hash distance, embedding fallback, union-find, and time-span splitting
- ranking uses explainable quality signals with small context-aware weight adjustments
- group summaries persist confidence and recommendation counts

Optional AI models are deferred and must remain local and optional when introduced.

## Export Architecture

Exports write derived artifacts under the project export directory:

- CSV writes a selection manifest
- ZIP packages selected files
- folder mode copies selected files into a local export folder

CSV and ZIP have browser download endpoints after successful completion. Folder exports expose local paths. Failed exports keep history records and remove partial artifacts where possible.

Future sidecar exports should default to project-controlled export directories and must not write next to original source files without explicit user-selected workflow changes.

## Migration And Indexing

SQLite startup applies idempotent compatibility migrations for additive columns and indexes. Existing migrations cover project storage metadata, photo file identity fields, processing state, export status metadata, group score summaries, and large-project query indexes.

Further schema changes should follow the rules in [Migration Plan](v2_migration_plan.md).

## Deferred Architecture

Deferred until after the core local workflow is stable:

- reference-in-place storage mode
- RAW embedded preview extraction
- HEIC preview support
- XMP sidecar export
- desktop packaging
- optional local model registry
- separate worker process or external queue
