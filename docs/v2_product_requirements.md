# FramePilot v2 Product Requirements

FramePilot v2 is a local-first photo culling workflow for photographers who want faster review without giving up manual control. It should help users reduce hundreds or thousands of local images into a reviewable shortlist while keeping original files safe.

## Product Goals

- Support reliable local culling for 500 to 2,000 photos.
- Preserve original photo files and never modify or delete them.
- Provide visible processing progress and retryable failure states.
- Group near-duplicate and burst-like frames conservatively.
- Rank photos with deterministic, explainable quality signals.
- Keep review keyboard-first, fast, and usable for repeated culling sessions.
- Export user decisions to local CSV, ZIP, and copied-folder outputs.
- Keep optional RAW, HEIC, sidecar, and model workflows planned but outside the v2.0 core unless implemented in focused later slices.

## Target Users

Primary users:

- hobby photographers reviewing travel, family, street, landscape, wildlife, or event shoots
- semi-professional photographers preparing selects before editing
- privacy-sensitive users who prefer local processing
- users who want AI assistance but keep final creative control

Non-goals:

- cloud photo management
- full RAW editing
- Lightroom or Capture One replacement
- automatic deletion workflow
- social galleries, accounts, payments, or collaboration

## Core Workflow

The v2.0 workflow is:

1. Create a local project.
2. Import JPEG, PNG, or WebP images.
3. Generate local thumbnails and previews.
4. Run local processing with visible job progress.
5. Group similar frames and rank candidates inside each group.
6. Review by keyboard using Pick, Maybe, Reject, Unreviewed, and 0-5 star ratings.
7. Export selected statuses as CSV, ZIP, or copied files.

All generated thumbnails, previews, metadata, caches, and exports are stored under local project-controlled directories.

## Supported Inputs

Required for v2.0:

- JPEG
- PNG
- WebP

Planned for later v2.x slices:

- HEIC preview support
- RAW embedded preview extraction for DNG, ARW, CR3, NEF, and similar camera formats

Unsupported HEIC and RAW inputs should fail gracefully with explicit local messages until support is implemented.

## Review Workspace Requirements

The culling workspace should provide:

- group-aware previous and next navigation
- previous and next photo navigation
- Pick, Maybe, Reject, and Unreviewed status updates
- 1-5 star ratings and 0 to clear rating
- zoom and compare modes
- persistent review progress per project
- bounded rendering for large group, filmstrip, and compare lists
- optimistic status updates where safe
- loading, empty, and error states that preserve a clear next action

## Export Requirements

v2.0 exports should:

- write only local artifacts under the project export directory
- support CSV, ZIP, and copied-folder outputs
- record export mode, selected statuses, selected count, output path, status, and creation time
- reject empty export requests
- allow browser downloads for completed CSV and ZIP exports
- keep folder exports available through their local output path
- preserve original files without modifying them

XMP sidecar export is planned separately and should default to project export directories when implemented.

## Performance Requirements

The first performance target is reliability, not perfect speed:

- 100-photo workflow covered by automated tests
- 500-photo workflow documented or validated with opt-in smoke commands
- 2,000-photo workflow should not crash in the intended local environment, or measured limits should be documented
- processing progress should remain visible
- failed or unsupported files should not crash the full project workflow
- frontend review should avoid mounting thousands of thumbnails or previews at once

## Privacy And Safety

FramePilot v2 must remain local-first:

- no cloud upload
- no remote photo processing
- no accounts, payment, or collaboration requirements
- no large bundled model files
- optional future models must run locally and require explicit user setup or download
- original source files must not be modified or deleted

## Release Boundaries

v2.0 can ship when the local JPEG/PNG/WebP workflow is stable, tested, and documented. Advanced formats, sidecar interoperability, desktop packaging, and optional models should be separate v2.x milestones after the core workflow remains reliable.
