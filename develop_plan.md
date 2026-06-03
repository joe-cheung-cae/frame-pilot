# FramePilot v2 Development Plan

## 1. Project Overview

FramePilot v2 is a local-first, desktop-like AI-assisted photo culling application for serious hobby photographers and semi-professional photographers. It evolves the v1 MVP from a proof-of-concept local web app into a more reliable, scalable, and workflow-oriented photo selection tool.

The goal of v2 is not to fully replace human aesthetic judgment. The goal is to remove obvious technical failures, group near-duplicate and burst sequences, rank candidates inside each group, explain why a photo is recommended, and provide a fast keyboard-first review experience.

Primary product statement:

> FramePilot v2 helps photographers turn hundreds or thousands of camera photos into a clean, reviewable shortlist with local-first processing, explainable recommendations, and professional culling workflow support.

## 2. v1 Status and Motivation for v2

FramePilot v1 already provides a usable MVP workflow:

- Local project creation.
- JPEG, PNG, and WebP import.
- Thumbnail and preview generation.
- Basic metadata extraction.
- Deterministic technical scoring.
- Lightweight face and eye-open heuristic signals.
- Simple near-duplicate grouping.
- Pick, Maybe, Reject, and Unreviewed statuses.
- Keyboard shortcuts.
- CSV, folder, and ZIP export.
- Basic API, frontend, and E2E test structure.

However, v1 is no longer enough for real photography workflows because:

- Processing is still too synchronous for large batches.
- Progress and resume behavior are limited.
- Similarity grouping is too weak for real burst and travel photo sets.
- Face and eye-open detection are heuristic and should not be treated as reliable portrait culling.
- The culling workspace is not yet fast enough or professional enough for thousands of photos.
- Export and interoperability need to be stronger.
- RAW and HEIC workflows are not supported yet.
- Real large-batch testing and performance validation are still insufficient.

v2 should preserve the working v1 foundation but redesign the processing architecture, workflow UX, export layer, and algorithm strategy.

## 3. Product Positioning

FramePilot v2 should be positioned as:

- A local-first photo culling tool.
- A privacy-respecting alternative to cloud photo culling services.
- A pre-editing workflow tool before Lightroom, Capture One, darktable, or manual editing.
- A fast keyboard-first review workspace inspired by professional photo culling tools.
- An explainable AI assistant, not an automatic judge of creative taste.

FramePilot v2 should not be positioned as:

- A cloud photo manager.
- A full RAW editor.
- A Lightroom replacement.
- A social gallery service.
- A fully automatic deletion tool.

## 4. v2 Product Goals

### 4.1 Core Goals

1. Support real local culling of 500 to 2,000 photos reliably.
2. Keep original photo files safe and never modify them.
3. Provide resumable background processing with visible progress.
4. Improve near-duplicate and burst grouping quality.
5. Improve ranking and recommendation explanations.
6. Provide a faster and more professional culling workspace.
7. Support robust CSV, ZIP, folder, and sidecar-oriented export workflows.
8. Improve test coverage for real local workflows and file safety.
9. Keep v2 realistic for a single developer assisted by Codex.

### 4.2 Stretch Goals

These goals are desirable but should not block the first v2 release:

- HEIC support.
- RAW embedded preview extraction.
- Lightroom-compatible XMP sidecar export.
- Optional lightweight local AI models.
- Browser-side ONNX Runtime Web inference.
- Local desktop packaging with Tauri or Electron.
- GPU acceleration for embedding generation.
- User preference learning.

## 5. Target Users and Workflows

### 5.1 Primary Users

- Hobby photographers who shoot travel, family, street, landscape, wildlife, or event photos.
- Semi-professional photographers who need a faster pre-selection workflow before editing.
- Users who care about privacy and prefer local processing.
- Users who want to keep creative control instead of letting AI make final decisions.

### 5.2 Core User Scenario

A user imports a folder containing 1,000 JPEG photos from a camera card. FramePilot v2 scans the folder, creates a local project, generates thumbnails and previews, computes image quality signals, groups similar frames, ranks photos inside each group, and presents a keyboard-first culling workspace. The user confirms Picks and Maybes, rejects obvious failures, and exports the selected results as CSV, ZIP, copied files, or future XMP sidecar ratings.

### 5.3 Future User Scenario

A user imports a mixed folder containing JPEG, HEIC, and RAW files. FramePilot extracts embedded previews from RAW files, performs local culling on previews, writes XMP sidecar ratings, and allows the user to continue editing in Lightroom or another RAW workflow tool.

## 6. v2 Scope

### 6.1 In Scope for v2.0

v2.0 should focus on a reliable local MVP-plus workflow:

1. Project creation and opening.
2. Folder-oriented import and multi-file import.
3. Safer project storage and path management.
4. Background or pseudo-background processing jobs.
5. Resumable processing state.
6. Incremental thumbnail and preview generation.
7. Deterministic technical scoring improvements.
8. Stronger perceptual hash and metadata-based grouping.
9. Improved group ranking.
10. Recommendation explanations that are conservative and transparent.
11. Professional culling workspace improvements.
12. Virtualized photo lists for larger projects.
13. CSV, ZIP, folder export, and download endpoints.
14. Real integration tests and real local smoke E2E tests.
15. Documentation for architecture, algorithms, testing, and migration.

### 6.2 Deferred from v2.0

The following should be planned but not required for v2.0:

- Full RAW decoding.
- Full color-managed RAW rendering.
- Cloud sync.
- User accounts.
- Payment system.
- Online collaboration.
- Mobile version.
- Heavy bundled AI models.
- Automatic deletion of original photos.

## 7. Supported File Types

### 7.1 v2.0 Required File Types

Support and test:

- JPEG
- PNG
- WebP

### 7.2 v2.x Planned File Types

Add later as separate milestones:

- HEIC
- DNG
- Sony ARW
- Canon CR3
- Nikon NEF

RAW and HEIC support should be implemented only after the v2 processing architecture is stable. RAW support should initially focus on embedded preview extraction rather than full RAW development.

## 8. Local-First and Privacy Requirements

FramePilot v2 must remain local-first.

Requirements:

- Original photos must never be modified.
- Original photos must never be deleted automatically.
- No photo should be uploaded to any remote server in v2.0.
- Project metadata must be stored locally.
- Generated thumbnails, previews, cache files, and exports must be stored locally.
- Optional AI models must run locally.
- If future optional model downloads are added, the user must explicitly opt in.
- The UI must clearly explain where project data and exports are stored.

Browser-based folder access may use the File System Access API where supported. The File System Access API allows web apps to interact with local files and directories after user permission, and browser support should be checked before relying on it in production.

## 9. v2 Architecture Direction

### 9.1 Preserve from v1

Keep the following v1 foundations:

- Monorepo structure.
- Next.js, React, TypeScript frontend.
- FastAPI backend.
- SQLite local metadata database.
- Existing Project, Photo, PhotoGroup, ProcessingJob concepts.
- Existing import, scoring, grouping, review, and export concepts.
- Existing local-first safety rules.
- Existing English-only code and documentation convention.

### 9.2 Refactor in v2

Refactor these areas:

- Processing pipeline organization.
- Job progress state model.
- File path and storage layout handling.
- Grouping and ranking services.
- Export service and download handling.
- Frontend data-fetching and culling workspace state.
- Test organization.
- Documentation structure.

### 9.3 Redesign in v2

Redesign these areas more deeply:

- Long-running processing architecture.
- Resume and incremental processing.
- Similarity grouping strategy.
- Professional culling workspace UX.
- Large-batch rendering and virtualization.
- Export interoperability strategy.
- Algorithm configuration and explainability.

## 10. Backend Architecture

### 10.1 API Layer

The backend should continue using FastAPI.

Recommended API groups:

```text
/api/projects
/api/projects/{project_id}/imports
/api/projects/{project_id}/jobs
/api/projects/{project_id}/photos
/api/projects/{project_id}/groups
/api/projects/{project_id}/exports
/api/assets
/api/health
```

v2 should avoid unnecessary breaking changes, but API routes may be reorganized if tests and documentation are updated.

### 10.2 Data Model

The core data model should include:

#### Project

- id
- name
- root_path
- source_mode
- source_root_path
- created_at
- updated_at
- total_images
- processed_images
- last_processed_at
- schema_version

#### Photo

- id
- project_id
- original_path
- project_copy_path
- source_identity
- filename
- file_ext
- file_size
- file_mtime
- content_hash
- width
- height
- capture_time
- camera_model
- lens_model
- focal_length
- aperture
- shutter_speed
- iso
- thumbnail_path
- preview_path
- perceptual_hash
- embedding_path
- sharpness_score
- blur_score
- exposure_score
- contrast_score
- noise_score
- face_signal_score
- eye_open_signal_score
- aesthetic_score
- overall_score
- ai_recommendation
- recommendation_explanation
- user_status
- star_rating
- group_id
- processing_state
- processing_error
- created_at
- updated_at

#### PhotoGroup

- id
- project_id
- group_type
- representative_photo_id
- photo_count
- score_summary
- created_at
- updated_at

#### ProcessingJob

- id
- project_id
- job_type
- status
- current_step
- total_items
- processed_items
- failed_items
- progress_percent
- error_message
- started_at
- completed_at
- created_at
- updated_at

#### ExportRecord

- id
- project_id
- export_type
- status_filter
- output_path
- download_path
- selected_count
- created_at
- completed_at
- error_message

### 10.3 Storage Layout

Use a local project layout such as:

```text
frame-pilot-project/
  project.db
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

v2 should support two storage modes:

1. Copy mode: copy originals into the project directory.
2. Reference mode: keep originals in place and store references only.

Copy mode is safer for self-contained projects. Reference mode is more efficient for large photo libraries. v2.0 may implement copy mode first and design the data model for reference mode later.

### 10.4 Processing Pipeline

The v2 pipeline should be stage-based:

1. Scan source files.
2. Register or update photo records.
3. Validate supported file types.
4. Generate or reuse thumbnails.
5. Generate or reuse previews.
6. Extract or update metadata.
7. Compute or reuse hashes.
8. Compute technical scores.
9. Compute optional embeddings.
10. Group similar photos.
11. Rank photos inside groups.
12. Generate explanations.
13. Persist results and update job state.

Each stage should update `ProcessingJob.current_step`, `processed_items`, `total_items`, and `error_message` when applicable.

### 10.5 Background Processing Strategy

v2 should not immediately introduce a heavy distributed queue.

Recommended v2.0 approach:

- Use FastAPI background tasks or an in-process worker abstraction.
- Keep job records in SQLite.
- Poll job status from the frontend.
- Make each processing step idempotent where possible.
- Support reprocessing only missing or stale derived data.
- Avoid long request timeouts by returning a job id quickly.

Future v2.x approach:

- Add a lightweight worker process.
- Consider RQ, Dramatiq, or Celery only if needed.
- Add cancellation and pause/resume.

## 11. Frontend Architecture

### 11.1 Framework

Continue using:

- Next.js
- React
- TypeScript
- Tailwind CSS
- TanStack Query
- Zustand or Jotai for local workspace state

### 11.2 Main Pages

v2 should provide:

1. Home page.
2. Project dashboard.
3. Project creation page.
4. Import and scan page.
5. Processing monitor page.
6. Culling workspace.
7. Export page.
8. Settings page.
9. Help and keyboard shortcuts page.

### 11.3 Culling Workspace Requirements

The culling workspace is the most important v2 frontend area.

It should include:

- Left sidebar with groups, filters, and project progress.
- Center preview area.
- Bottom virtualized filmstrip.
- Right score and explanation panel.
- Top toolbar with status, export, and view controls.
- Fast keyboard navigation.
- Group-aware navigation.
- Zoom controls.
- Compare mode for similar frames.
- Clear Pick, Maybe, Reject, and Unreviewed indicators.
- Star rating support.
- Batch actions.
- Persistent review progress.

### 11.4 Keyboard Shortcuts

Required shortcuts:

- Left arrow: previous photo.
- Right arrow: next photo.
- Up arrow: previous group.
- Down arrow: next group.
- P: mark Pick.
- M: mark Maybe.
- X: mark Reject.
- U: mark Unreviewed.
- 1 to 5: assign star rating.
- 0: clear star rating.
- Space: toggle large preview.
- Z: toggle zoom.
- C: compare mode.
- G: group view.
- F: filter menu.
- E: export.

### 11.5 Large-Batch UI Requirements

For 2,000+ photos, the frontend must avoid rendering everything at once.

Requirements:

- Use virtualized lists or grids.
- Lazy-load previews.
- Cache active group data.
- Avoid refetching all photos after every status change.
- Use optimistic updates for status and rating changes.
- Provide clear loading and error states.

## 12. Algorithm Strategy

### 12.1 Deterministic First

v2 should keep deterministic algorithms as the baseline because they are transparent, fast, and testable.

Required deterministic signals:

- Sharpness score.
- Blur risk score.
- Exposure score.
- Contrast score.
- Noise risk score.
- Perceptual hash.
- Time and filename proximity.
- Metadata similarity.

### 12.2 Similarity Grouping v2

The grouping strategy should combine:

- Capture time proximity.
- Filename sequence proximity.
- Perceptual hash distance.
- Image dimensions.
- Camera model.
- Lens and focal length.
- Optional embedding similarity.

Recommended first v2 algorithm:

1. Sort photos by capture time, falling back to filename.
2. Build candidate windows using time and filename proximity.
3. Compute perceptual hash distance inside candidate windows.
4. Merge photos into groups using union-find.
5. Split groups if time gaps are too large.
6. Select representative photo by group ranking.
7. Persist group confidence and explanation.

### 12.3 Ranking v2

Ranking should be configurable and explainable.

Initial formula:

```text
final_score =
    0.30 * sharpness_score
  + 0.20 * exposure_score
  + 0.15 * contrast_score
  + 0.10 * noise_quality_score
  + 0.15 * face_signal_score
  + 0.10 * aesthetic_score
```

The formula must be adjusted by photo type:

- Portrait-like photos: increase face signal weight, but label it as experimental unless a real model is used.
- Landscape-like photos: increase exposure, contrast, and sharpness weights.
- Low-confidence groups: avoid aggressive Reject recommendations.

### 12.4 Recommendation Explanations

Explanations should be rule-based and conservative.

Examples:

```text
Recommended because it is the sharpest image in this similar-photo group and has balanced exposure.
```

```text
Marked as Maybe because it is a single-image group with acceptable sharpness but low contrast.
```

```text
Rejected because it is visually similar to a sharper frame and has a higher blur risk.
```

```text
Face signal is experimental and should be reviewed manually.
```

### 12.5 Optional AI Models

Optional AI models may be added only after deterministic v2 is stable.

Possible model areas:

- Image embeddings.
- Face detection.
- Eye-open detection.
- Aesthetic scoring.
- Subject detection.

Rules:

- Do not commit large model files to the repository.
- Models must be optional downloads or separately configured assets.
- Local inference only.
- Provide CPU fallback.
- Clearly document model source, license, size, and expected performance.

ONNX Runtime Web may be used later for browser-side inference, while backend-side ONNX Runtime may be simpler for v2.0. ONNX Runtime Web supports in-browser inference through the `onnxruntime-web` package.

## 13. Export and Interoperability

### 13.1 Required v2 Export Modes

v2 should support:

1. CSV export.
2. ZIP export.
3. Copy selected photos to folder.
4. Download endpoint for CSV and ZIP exports.
5. Export status summary in UI.

### 13.2 Future Export Modes

Plan for:

- XMP sidecar ratings.
- Lightroom-compatible selection workflow.
- Capture One compatible metadata workflow.
- Export selected filenames only.
- Export rejected filenames for manual deletion outside FramePilot.

FramePilot must never delete originals automatically. If deletion support is ever added, it must be a clearly separate manual workflow with confirmations.

## 14. Testing Strategy

### 14.1 Backend Unit Tests

Test:

- Metadata parsing.
- Score normalization.
- Perceptual hash generation.
- Similarity distance.
- Group creation.
- Group splitting.
- Ranking formula.
- Recommendation explanation.
- Export file generation.
- File safety.

### 14.2 Backend Integration Tests

Use temporary directories and generated synthetic images.

Test:

- Project creation.
- Import.
- Thumbnail generation.
- Preview generation.
- Processing job creation.
- Job status polling.
- Photo listing.
- Group listing.
- Status update.
- CSV export.
- ZIP export.
- Export download endpoint.
- Unsupported file handling.
- Original file immutability.

### 14.3 Frontend Tests

Test:

- Project creation UI.
- Import UI.
- Processing progress UI.
- Culling workspace filters.
- Keyboard shortcuts.
- Status updates.
- Export panel.
- Error and empty states.

### 14.4 E2E Tests

Keep both kinds of E2E tests:

1. Mocked E2E for fast UI regression.
2. Real local smoke E2E for full frontend/backend workflow validation.

Real smoke E2E should use generated synthetic photos only.

### 14.5 Performance Tests

Add script-level performance checks for:

- 100 photos.
- 500 photos.
- 2,000 photos.

The first target is not perfect speed; the first target is no crash, no memory explosion, visible progress, and recoverable errors.

## 15. Documentation Plan

v2 should create or update these documents:

```text
docs/v1_review_for_v2.md
docs/v2_product_requirements.md
docs/v2_architecture.md
docs/v2_milestones.md
docs/v2_algorithm_strategy.md
docs/v2_testing_strategy.md
docs/v2_migration_plan.md
docs/api.md
docs/scoring.md
README.md
AGENTS.md
```

Documentation must remain practical and implementation-oriented.

## 16. Development Milestones

### 16.1 v2.0 Foundation

Objective:

Make the repository maintainable and ready for structured v2 development.

Tasks:

- Review and preserve v1 functionality.
- Ensure formatting, linting, type checking, and tests are available.
- Create or update v2 planning documents.
- Stabilize developer commands.
- Confirm local run instructions.

Acceptance criteria:

- `npm run test` passes.
- `npm run test:e2e` is documented and passes when feasible.
- Formatting and linting commands are documented.
- v2 planning documents exist.

### 16.2 v2.1 Processing and Progress

Objective:

Replace synchronous user-facing processing with job-based processing and progress polling.

Tasks:

- Add job start endpoint that returns quickly.
- Add processing stages and progress updates.
- Add job polling UI.
- Add resumable processing state.
- Skip already processed or unchanged files.
- Add error recovery behavior.

Acceptance criteria:

- A 500-photo project shows stage progress.
- Failed items are recorded without crashing the whole job.
- Reprocessing does not redo unchanged work unnecessarily.
- Integration tests cover job progress and failure paths.

### 16.3 v2.2 Culling Workspace Upgrade

Objective:

Make the review workspace fast and comfortable for real culling.

Tasks:

- Add virtualized filmstrip or grid.
- Add zoom mode.
- Add compare mode.
- Improve group navigation.
- Add batch actions.
- Improve keyboard shortcuts.
- Improve score and explanation panel.
- Add persistent review progress.

Acceptance criteria:

- User can review photos mostly by keyboard.
- UI remains responsive with 2,000 photo records.
- Status changes are optimistic and reliable.
- Mocked and real E2E tests cover culling actions.

### 16.4 v2.3 Export and Interoperability

Objective:

Make export reliable and useful for downstream editing tools.

Tasks:

- Improve CSV export.
- Improve ZIP export.
- Improve folder copy export.
- Add download endpoints.
- Add export history.
- Add selected count and status summary.
- Plan XMP sidecar export.

Acceptance criteria:

- CSV and ZIP can be downloaded from the browser.
- Folder export clearly shows local output path.
- Export tests verify file existence and content.
- Original files are never modified.

### 16.5 v2.4 Algorithm Quality Upgrade

Objective:

Improve deterministic grouping, ranking, and explanations.

Tasks:

- Add perceptual hash storage.
- Add union-find grouping.
- Add metadata-aware group splitting.
- Add confidence scores.
- Improve ranking formula.
- Improve explanation rules.
- Add test datasets for blur, exposure, and burst-like sequences.

Acceptance criteria:

- Similar burst photos group more reliably.
- Clearer images rank above blurry similar images.
- Overexposed or underexposed frames are penalized.
- Explanations match the actual score differences.

### 16.6 v2.5 Performance and Reliability

Objective:

Validate large-batch behavior.

Tasks:

- Add synthetic performance dataset generation.
- Test 100, 500, and 2,000 photo workflows.
- Profile processing bottlenecks.
- Improve database query patterns.
- Improve frontend rendering performance.
- Add recovery tests for interrupted processing.

Acceptance criteria:

- 2,000 photo workflow does not crash.
- UI remains responsive.
- Processing progress remains visible.
- Memory usage is acceptable for local machines.

### 16.7 v2.6 Optional RAW, HEIC, and AI Model Support

Objective:

Add advanced format and model support only after v2 core is stable.

Tasks:

- Add HEIC preview support.
- Add RAW embedded preview extraction.
- Add optional model registry.
- Add optional local face detection model.
- Add optional embedding model.
- Add documentation for model downloads and licenses.

Acceptance criteria:

- Advanced features are optional.
- No large model files are committed.
- Existing JPEG workflow remains stable.
- Unsupported formats fail gracefully.

## 17. First v2 Iteration

The first v2 implementation iteration should be small but meaningful.

### Objective

Implement job-based processing progress and real integration coverage without changing the product scope.

### Recommended Branch

```text
feature/v2-processing-progress
```

### Tasks

1. Review current processing code.
2. Ensure `ProcessingJob` records all stages.
3. Make `/process` return a job id quickly if practical.
4. Add or improve `/jobs/{job_id}` polling.
5. Update frontend processing UI to show real progress.
6. Add backend integration tests using generated synthetic images.
7. Add tests for failed or unsupported files.
8. Document the updated processing flow.

### Files Likely to Change

```text
apps/api/app/api/routes.py
apps/api/app/models/entities.py
apps/api/app/services/processing.py
apps/api/app/services/importing.py
apps/api/app/services/exporting.py
apps/web/src/components/ProcessingPanel.tsx
apps/web/src/lib/api.ts
docs/architecture.md
docs/api.md
tests or apps/api tests
```

### Definition of Done

- Processing progress is visible in the UI.
- Job status can be polled.
- Failed files do not crash the full job.
- Existing v1 workflow still works.
- Backend integration tests pass.
- Documentation is updated.
- Original photos are not modified.

## 18. Implementation Rules for Codex

When using Codex to implement v2, follow these rules:

1. Read `develop_plan.md`, `AGENTS.md`, and v2 docs before coding.
2. Do not restart the project from scratch.
3. Keep FramePilot local-first.
4. Do not add cloud upload, user accounts, payment, or remote photo processing.
5. Do not modify or delete original photos.
6. Do not commit large model files.
7. Use English for all code, comments, tests, docs, and commit messages.
8. Prefer small, deterministic, testable algorithms before optional AI models.
9. Add or update tests for scoring, grouping, jobs, export, and file safety.
10. Run relevant tests before finishing.
11. Review the final diff before summarizing.
12. Keep each iteration focused on one coherent milestone.

## 19. Risks and Mitigations

### Risk: v2 becomes too large

Mitigation:

- Keep v2.0 focused on processing, progress, export, and workspace reliability.
- Defer RAW, HEIC, and AI model support.

### Risk: local browser file access is inconsistent

Mitigation:

- Keep standard upload as fallback.
- Use File System Access API only where supported.
- Clearly document browser limitations.

### Risk: AI model integration complicates deployment

Mitigation:

- Keep deterministic algorithms as baseline.
- Make models optional.
- Do not bundle large models.

### Risk: large batch processing is slow

Mitigation:

- Use incremental processing.
- Cache generated derivatives and scores.
- Add performance tests.
- Use background jobs and progress polling.

### Risk: recommendation quality is overtrusted

Mitigation:

- Use conservative labels.
- Explain recommendations.
- Keep user override as the source of truth.
- Mark heuristic face signals as experimental.

## 20. References and Technical Notes

The following technical facts influence the v2 direction:

- Browser apps can request user-selected file or directory access through File System Access API methods such as file and directory pickers, but production browser compatibility must be checked.
- Chrome documentation describes the File System Access API as suitable for powerful local-file web apps such as photo editors, after explicit user permission.
- ONNX Runtime Web supports browser-side inference through `onnxruntime-web`, which may be useful for future optional local model inference.
- Professional photo workflows commonly rely on nondestructive metadata, ratings, and downstream editor interoperability; v2 should therefore plan CSV and future XMP sidecar export instead of modifying originals.

## 21. Definition of Done for v2.0

FramePilot v2.0 is complete when:

- A user can create or open a local project.
- A user can import a folder or a large batch of JPEG/PNG/WebP photos.
- The app processes photos through visible job stages.
- Processing can be resumed or safely rerun without unnecessary duplicate work.
- The system generates thumbnails and previews incrementally.
- The system computes deterministic quality scores.
- The system groups similar images more reliably than v1.
- The system recommends representative photos with conservative explanations.
- The culling workspace remains responsive for at least 2,000 photo records.
- The user can mark Pick, Maybe, Reject, or Unreviewed efficiently with keyboard shortcuts.
- The user can export CSV and ZIP results from the browser.
- Folder export clearly shows where files are copied.
- Original photos are never modified or deleted.
- Real backend integration tests pass.
- Real local smoke E2E is available or clearly documented.
- README and v2 documentation explain how to run, test, and use the application.
