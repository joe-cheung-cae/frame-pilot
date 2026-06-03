# FramePilot v2 Migration Plan

FramePilot v2 should evolve existing local projects without requiring users to reimport photo libraries or risk original files. Migrations must be local, deterministic, and reversible through normal file backups of the project directory.

## Migration Principles

- Never modify or delete original source photo files.
- Keep derived outputs, metadata, caches, and exports inside the project-controlled data directory.
- Prefer additive SQLite changes with defaults over destructive rewrites.
- Make compatibility migrations idempotent so app startup can safely run them more than once.
- Preserve v1 project data whenever the required source files and generated artifacts still exist.
- Keep unsupported RAW, HEIC, and optional model workflows disabled unless they are explicitly implemented in later v2.x slices.

## Current Baseline

The current v2 baseline uses local SQLite metadata and a project layout under `.framepilot-data/projects/<project-id>/` with:

- copied originals
- thumbnails
- previews
- cache data
- exports

Projects record `schema_version`, `source_mode`, and `source_root_path`. v2 currently creates projects in `copy` mode; reference mode remains a planned future storage mode.

Startup database initialization already applies small compatibility migrations for fields such as export record status and processing job failure counts. New compatibility migrations should follow that explicit, idempotent style unless the schema grows enough to justify a dedicated migration runner.

## SQLite Schema Evolution

Use additive migrations for:

- new nullable columns
- new columns with safe defaults
- indexes for large-project review, export, and job queries
- new tables for future sidecar, model, or job artifact metadata

Avoid migrations that:

- rewrite original paths without validation
- drop user review decisions
- delete export history
- assume generated thumbnails, previews, or cache files are still present

When a derived file is missing, processing should attempt local regeneration from the copied original. If regeneration is impossible, the photo should receive a retryable or failed processing state rather than breaking the project migration.

## Project Storage Evolution

Copy mode is the v2.0 safety baseline. Reference mode should be introduced only after these behaviors are tested:

- original source paths are stored as references only
- FramePilot never writes to referenced originals
- missing referenced originals produce clear, retryable local errors
- exports still write to project-controlled output directories

Future sidecar export should default to project export directories, not next to original files. Writing sidecars beside source originals should require a separate user-selected workflow and additional file-safety tests.

## API Compatibility

Prefer extending existing responses over breaking route shapes. When route behavior changes:

- update `docs/api.md`
- add or update API tests
- keep existing v1 workflow behavior working where practical
- return explicit validation errors instead of silently ignoring unsupported input

New status values should be reflected in backend schemas, frontend TypeScript types, UI states, and tests in the same slice.

## Frontend State Migration

Browser-local review state is per project. Frontend persistence should tolerate:

- missing stored values
- malformed stored values
- stale filter, photo, or group references
- new workspace flags added in later releases

When persisted state cannot be trusted, the UI should fall back to a valid default and keep the project usable.

## Validation Checklist

Before committing a migration-related change:

- add a test for idempotent migration behavior when applicable
- verify existing project creation, import, processing, review, and export tests still pass
- run `npm run verify`
- document user-visible behavior changes
- confirm no private photos, generated datasets, or large model files were added
