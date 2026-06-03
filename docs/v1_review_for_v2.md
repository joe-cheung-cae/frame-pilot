# FramePilot v1 Review for v2 Planning

## 1. Executive Summary

- FramePilot v1 is a usable MVP, not production-ready software. It demonstrates the complete local-first culling loop, but it has not yet been validated for real photographer-scale batches, long-running processing, or professional workflow expectations.
- v1 already does the most important MVP things well: project creation, local image import, copy-on-import safety, generated thumbnails/previews, deterministic scoring, simple grouping, recommendation explanations, manual review statuses, star ratings, and CSV/folder/ZIP export.
- The backend is compact and understandable. The main implementation is in `apps/api/app/api/routes.py`, `apps/api/app/services/importing.py`, `apps/api/app/services/processing.py`, `apps/api/app/services/grouping.py`, `apps/api/app/services/ranking.py`, and `apps/api/app/services/exporting.py`.
- The frontend covers the intended page flow from home to import, processing, culling, and export. The primary workspace is `apps/web/src/components/CullingWorkspace.tsx`.
- v1 is no longer enough for v2 because processing is synchronous, image analysis is heuristic-only, similarity grouping is too shallow, large-batch performance is unproven, and the UI is still a browser MVP rather than a serious high-volume culling workspace.
- Preserve the local-first posture, original-file safety, deterministic baseline algorithms, transparent scoring, simple API shape, and focused test coverage around scoring, grouping, status updates, and exports.
- Redesign processing orchestration, progress reporting, import model, grouping quality, review-state architecture, export/interoperability behavior, and the test strategy for real local workflows.
- v2 should evolve v1 on a structured branch instead of discarding the repository. The existing code is a good scaffold, but several core areas should be refactored before adding major product features.

## 2. Repository Structure Review

Root-level structure:

- `README.md` explains the current MVP, local setup, privacy stance, workflow, and verification commands.
- `develop_plan.md` defines the product scope, MVP workflow, local-first constraints, scoring formula, UI requirements, and out-of-scope areas.
- `AGENTS.md` contains repository-specific implementation constraints.
- `package.json` owns monorepo-style scripts for backend, frontend, tests, lint, typecheck, and E2E.
- `docs/` currently contains `architecture.md`, `api.md`, and `scoring.md`.
- `apps/api/` contains the FastAPI backend.
- `apps/web/` contains the Next.js frontend.
- `tests/e2e/` contains Playwright tests.
- `scripts/run-e2e.sh` wraps Playwright execution.

Frontend structure:

- `apps/web/src/app/` defines Next.js pages for home, project creation, import, processing, culling, and export.
- `apps/web/src/components/` contains the main UI components: `ProjectCreator`, `ProjectList`, `ImportPanel`, `ProcessingPanel`, `CullingWorkspace`, `ExportPanel`, `Shell`, and `Providers`.
- `apps/web/src/lib/` contains API client types/helpers plus small tested utilities for project routing, review navigation, and export status counting.
- `apps/web/src/store/reviewStore.ts` contains a small Zustand store for culling UI state.

Backend structure:

- `apps/api/app/main.py` creates the FastAPI application, CORS policy, health route, and API router.
- `apps/api/app/api/routes.py` contains all HTTP route handlers.
- `apps/api/app/models/entities.py` defines SQLModel tables for `Project`, `Photo`, `PhotoGroup`, `ProcessingJob`, and `ExportRecord`.
- `apps/api/app/schemas/api.py` defines Pydantic request/response schemas and validators.
- `apps/api/app/services/` contains project creation, importing, processing, grouping, ranking, and export services.
- `apps/api/app/image/scoring.py` contains deterministic technical scoring and face/eye heuristics.
- `apps/api/app/ai/embeddings.py` contains the current perceptual-hash/color embedding approximation.
- `apps/api/app/db/session.py` owns SQLite engine/session creation and one compatibility migration for export records.

Test structure:

- `apps/api/tests/` contains backend unit and API tests for projects, scoring, grouping, ranking, import/process/export workflows, export safety, and status updates.
- `apps/web/src/lib/*.test.ts` contains lightweight Node tests for frontend pure helpers.
- `tests/e2e/local-workflow.spec.ts` uses mocked API routes for a browser workflow.
- `tests/e2e/real-local-smoke.spec.ts` uses the real local API and web app for a small import/process/pick/export smoke flow.

Documentation structure:

- `docs/architecture.md` accurately describes the current two-app architecture and local project storage layout.
- `docs/api.md` documents implemented API endpoints and response shapes.
- `docs/scoring.md` documents the deterministic scoring and experimental face/eye heuristic.

Scripts and developer workflow:

- `npm run dev` starts backend and frontend together through `concurrently`.
- `npm run test` runs backend pytest plus frontend unit tests and production build.
- `npm run test:e2e` runs Playwright through `scripts/run-e2e.sh`.
- `npm run verify` runs lint, typecheck, and tests.

The structure is suitable for v2 foundation work, but v2 should reorganize around clearer boundaries: background jobs, storage services, import sources, analysis pipelines, API versioning, and larger frontend workspace components. The current layout is still understandable enough to evolve incrementally.

## 3. Current Feature Inventory

| Feature | Current status | Implementation location | Quality level | v2 action |
|---|---|---|---|---|
| Project creation | Implemented with local project directories | `create_project` in `apps/api/app/services/projects.py`; `ProjectCreator` | MVP solid | keep |
| Image import | Implemented for JPEG, PNG, WebP uploads/folder input via browser file picker | `import_image_file`; `ImportPanel` | MVP solid, browser-limited | improve |
| Local storage | Implemented under `.framepilot-data/projects/<project-id>/` by default | `create_project`; `project_export_root`; docs | Good MVP | keep |
| Thumbnail generation | Implemented as WebP derivatives | `_save_derivatives` in `importing.py` | Good MVP | keep/improve |
| Preview generation | Implemented as max 1800px WebP previews | `_save_derivatives` in `importing.py` | Good MVP | keep/improve |
| Metadata extraction | Basic EXIF fields only | `_extract_metadata` in `importing.py` | Limited | improve |
| Technical scoring | Deterministic sharpness, blur, exposure, contrast, noise, aesthetic | `compute_quality_scores` | Useful MVP baseline | improve |
| Face/eye-open heuristic | Skin-mask and luminance heuristic | `_detect_face_signals` | Weak/experimental | replace or make optional |
| Similarity grouping | Sequential nearest-neighbor grouping by similarity and capture-time gap | `group_similar_photos` | Weak for real shoots | redesign |
| Group ranking | Weighted transparent formula | `rank_group`; `final_score` | Useful baseline | improve |
| Recommendation explanation | Rule-based explanations | `ranking.py` | Good MVP transparency | improve |
| Culling workspace | Implemented with filters, group list, preview, score panel, filmstrip | `CullingWorkspace.tsx` | Usable MVP | redesign/improve |
| Keyboard shortcuts | Implemented for arrows, P/M/X/U, 1-5, Space, G | `CullingWorkspace.tsx` | Good MVP | improve |
| Status update | Implemented with validation | `PATCH /photos/{photo_id}`; `PhotoUpdate` | Good MVP | keep |
| Star rating | Implemented 0-5 API validation and UI | `PhotoUpdate`; `CullingWorkspace.tsx` | Basic | improve |
| Export CSV | Implemented with selected statuses and score fields | `write_selection_csv` | Good MVP | improve |
| Export folder | Implemented local copy preserving duplicate names | `copy_selected_files` | Useful but UX-limited | improve |
| Export ZIP | Implemented with download endpoint | `zip_selected_files`; download route | Good MVP | improve |
| Generated asset serving | Implemented for thumbnails/previews | `get_generated_asset` | Basic | improve safety/caching |
| API tests | Broad unit/API coverage | `apps/api/tests/` | Strong for MVP | keep/expand |
| Frontend tests | Pure helper tests only | `apps/web/src/lib/*.test.ts` | Thin | improve |
| E2E tests | Mocked workflow plus one real local smoke flow | `tests/e2e/` | Useful but insufficient | improve |
| Documentation | Architecture, API, scoring, README | `docs/`, `README.md` | Good MVP | expand |

## 4. Backend Review

FastAPI route design:

- What exists: `apps/api/app/api/routes.py` exposes project, import, process, job, photo, group, export, download, and generated asset routes under `/api`. The route set matches `docs/api.md`.
- Weakness: all routes are in one file, export creation writes artifacts synchronously, processing starts and completes inside one request, and there is no API version prefix.
- User risk: large imports, processing, or exports can block requests and make the UI appear stuck or failed.
- v2 action: split route modules by resource, introduce `/api/v2` or versioned contracts for changed behavior, and move processing/export work to background jobs.

SQLModel data models:

- What exists: `Project`, `Photo`, `PhotoGroup`, `ProcessingJob`, and `ExportRecord` are defined in `apps/api/app/models/entities.py`.
- Weakness: status fields are plain strings, embeddings and export statuses are JSON strings, and migrations are limited to `_ensure_export_record_columns` in `apps/api/app/db/session.py`.
- User risk: string drift, weak validation at the database boundary, and fragile schema changes as v2 evolves.
- v2 action: introduce enums, structured JSON helpers or normalized records where useful, and a simple migration plan suitable for SQLite.

Project storage layout:

- What exists: each project has `originals/`, `thumbnails/`, `previews/`, `exports/`, and `cache/`, created by `create_project`.
- Weakness: v1 always copies uploads into the project when importing through the browser. There is no reference-in-place mode, sidecar metadata directory, resumable derivative cache, or source folder tracking.
- User risk: large shoots consume duplicate disk space, and users cannot easily understand whether FramePilot is copying or referencing originals.
- v2 action: decide product policy for copy-vs-reference, then encode it explicitly in project metadata and UI.

Import pipeline:

- What exists: `import_image_file` validates extensions, writes the uploaded file, opens it with Pillow, extracts metadata, creates derivatives, scores the image, computes an embedding, invalidates stale processing, and commits a `Photo`.
- Weakness: import is synchronous and per-file. It reads the upload into memory/file in one request, computes all analysis during import, and invalidates all group/recommendation metadata after each file.
- User risk: big batches can time out or feel frozen; partial progress and retries are limited.
- v2 action: separate import registration, derivative generation, scoring, embedding, grouping, and ranking into resumable job steps.

Image derivative generation:

- What exists: thumbnails and previews are generated as WebP in `_save_derivatives`.
- Weakness: derivative generation is immediate, non-resumable, and not independently tracked. There is no cache invalidation model beyond unique output paths.
- User risk: failed or interrupted batches may require rework; progress cannot show derivative-level detail.
- v2 action: make derivative records or processing state explicit, and process derivatives in bounded batches.

Metadata extraction:

- What exists: `_extract_metadata` reads common EXIF values such as capture time, camera model, lens, focal length, aperture, shutter speed, and ISO.
- Weakness: it does not handle richer EXIF variants, time zones, sidecar data, RAW metadata, or camera-specific quirks.
- User risk: grouping by capture time/camera can be wrong or missing for real shoots.
- v2 action: improve metadata parsing and record confidence/source of metadata.

Scoring pipeline:

- What exists: `compute_quality_scores` calculates deterministic values from NumPy arrays.
- Weakness: the scoring calibration is global and synthetic-test driven. Noise scoring is simplistic, aesthetic score is exposure/contrast average, and face scoring is experimental.
- User risk: recommendations may be misleading for portraits, low-light work, high-ISO images, intentionally blurred shots, or creative exposure.
- v2 action: keep deterministic technical metrics as explainable baselines, add calibration tests with synthetic and real sample sets, and consider optional local models later.

Grouping pipeline:

- What exists: `group_similar_photos` sorts by capture time or filename and compares only the previous item with a cosine similarity threshold.
- Weakness: it does not use filename sequence proximity beyond sorting, does not use camera/lens/dimensions, and can split or merge incorrectly when related frames are not adjacent.
- User risk: users lose trust when bursts are split, unrelated scenes are grouped, or representative choices are poor.
- v2 action: redesign grouping around candidate windows, metadata features, perceptual hashes, and calibrated thresholds.

Recommendation pipeline:

- What exists: `rank_group` applies transparent weights and assigns Pick/Maybe/Reject with rule-based explanations.
- Weakness: the duplicate penalty is flat for all non-single groups, face quality can dominate when the heuristic is wrong, and user preferences do not influence ranking.
- User risk: wrong automated recommendations can slow review instead of speeding it up.
- v2 action: keep explanations but improve ranking inputs, group-aware penalties, and allow configurable ranking profiles.

Export pipeline:

- What exists: CSV, folder copy, and ZIP export are implemented in `exporting.py`; the download route checks that CSV/ZIP artifacts resolve inside the project export root.
- Weakness: folder exports only show a local output path, CSV format is not yet sidecar/XMP oriented, and exports run synchronously.
- User risk: large exports can block; professional interoperability is limited.
- v2 action: add queued exports, sidecar metadata formats, clearer download/open-folder UX, and export history management.

Job/progress model:

- What exists: `ProcessingJob` records are created, updated, and returned by `process_project`.
- Weakness: jobs are synchronous despite the model. The frontend receives the final job after the request completes, so progress is not truly live.
- User risk: processing thousands of images may look broken.
- v2 action: implement a background queue with polling or server-sent events; store step-level progress and resumable state.

Error handling:

- What exists: imports catch unsupported/unreadable images and clean up written files. Processing catches exceptions and marks the job failed. API validation returns 422/404 as appropriate.
- Weakness: processing swallows detailed structured errors into `error_message`; multi-file imports return skipped reasons but not retry IDs; export failures after record creation are not handled with a failed export status.
- User risk: users may not know which file caused failure or how to retry.
- v2 action: add structured errors and failed-item records for imports, processing, and exports.

Data validation:

- What exists: Pydantic validates project names, status updates, star ratings, export modes, and export statuses.
- Weakness: DB model string fields still allow invalid values if written internally, and project `root_path` is not heavily constrained.
- User risk: inconsistent data can appear after internal bugs or future migrations.
- v2 action: add enums, path policy validation, and stronger storage safety checks.

File safety:

- What exists: filenames are normalized with `Path(filename).name`, duplicate names get suffixes, originals are copied instead of modified, import cleanup is tested, and export downloads are constrained to the export root.
- Weakness: generated asset serving builds paths from `project.root_path`, `kind`, and basename but only checks existence, not `resolve().is_relative_to(...)`. Project deletion removes DB records but does not remove files.
- User risk: low-to-medium file exposure risk if project metadata is corrupted; disk accumulation after deletes.
- v2 action: apply consistent resolved-root checks to all file-serving paths, define project deletion/archive semantics, and test path traversal cases.

Test coverage:

- What exists: backend tests cover a substantial MVP surface, including file safety, duplicate filenames, exports, processing invalidation, ranking explanations, and status updates.
- Weakness: no performance tests, no large-batch tests, limited real E2E, limited frontend component tests, and no realistic photo dataset.
- User risk: v2 regressions can hide in UX and scale behavior.
- v2 action: keep current tests and add fixture datasets, real E2E flows, performance smoke checks, and component-level workspace tests.

## 5. Frontend Review

Page flow:

- What exists: Next.js pages cover home, `/projects/new`, import, process, cull, and export.
- Weakness: the flow is linear and simple; returning to partially completed work or managing many projects is basic.
- User risk: real users with multiple shoots may find navigation shallow.
- v2 action: add a project dashboard, clearer project state, and resumable workflow links.

Project creation UX:

- What exists: `ProjectCreator` collects a project name and redirects to import.
- Weakness: no root path selection in the UI despite backend accepting `root_path`; no explicit copy/reference policy.
- User risk: users may not know where project data is stored.
- v2 action: expose storage choices once product policy is decided.

Import UX:

- What exists: `ImportPanel` supports file selection and browser folder selection via `webkitdirectory`, shows skipped files, and previews recent imports.
- Weakness: browser folder import is not the same as a desktop-like folder reference; no batch queue, per-file progress, retry, or folder rescan.
- User risk: large folder imports may be slow, opaque, and hard to recover.
- v2 action: move to queued import with progress and, if the product stays browser-based, document browser limitations clearly.

Processing UX:

- What exists: `ProcessingPanel` triggers processing and shows job state from the completed response.
- Weakness: because the backend is synchronous, the progress bar is not live during actual processing.
- User risk: the UI will feel frozen for large batches.
- v2 action: poll background jobs and display current file/step, ETA if available, pause/cancel/retry, and failure details.

Culling workspace UX:

- What exists: `CullingWorkspace` has a left filter/group panel, center preview, right score/explanation panel, top toolbar, and bottom filmstrip.
- Weakness: the component is 414 lines and owns data fetching, filtering, keyboard handling, mutation, selection, and layout. It has no virtualization and limited compare/zoom behavior.
- User risk: performance and maintainability issues will grow quickly for thousands of photos.
- v2 action: split into workspace shell, group list, filmstrip, preview, detail panel, keyboard controller, and review state modules; add virtualization.

Group navigation:

- What exists: group buttons and `G` cycle through groups.
- Weakness: there is no robust burst comparison mode, no group collapse/expand, and filtering can make selected group states confusing.
- User risk: users may lose context while reviewing groups.
- v2 action: design group-first navigation around representative, alternatives, and status counts.

Preview display:

- What exists: previews and thumbnails are loaded through `assetUrl`; large preview mode hides the right panel.
- Weakness: no zoom/pan, no before/after compare, no loading skeleton per image, and no failure-specific image state beyond missing preview text.
- User risk: users cannot judge sharpness confidently.
- v2 action: add zoom to 100%, fit/fill controls, quick compare, and image loading/error states.

Score and explanation panel:

- What exists: scores and recommendation explanation are visible.
- Weakness: score values are raw numeric cards; no confidence, no caveat around weak face heuristic inside the panel beyond a simple signal message.
- User risk: users may over-trust weak signals.
- v2 action: show clearer metric labels, confidence/caveats, and group comparison context.

Keyboard shortcuts:

- What exists: arrows, P, M, X, U, number ratings, Space, and G are implemented.
- Weakness: shortcuts are hardcoded in `CullingWorkspace`; there is no command model or conflict management.
- User risk: adding v2 shortcuts may become brittle.
- v2 action: centralize shortcut definitions and test keyboard behavior.

Export UX:

- What exists: `ExportPanel` supports status selection and CSV/folder/ZIP mode selection, with CSV/ZIP download links.
- Weakness: folder exports expose a path string rather than an open-folder action; no export presets, no sidecar export, no export history view.
- User risk: professional workflows remain awkward.
- v2 action: add export presets, XMP/sidecar options if required, and queued export status.

Error states:

- What exists: basic API errors display on creation, import, processing, loading, and export.
- Weakness: errors are generic and not always actionable.
- User risk: users may be stuck after large import or processing failures.
- v2 action: show file-level errors, retry actions, and support diagnostics.

Loading states:

- What exists: query loading spinners and mutation pending labels exist.
- Weakness: no long-running progress during synchronous backend operations and no per-image loading placeholders in the workspace.
- User risk: poor perceived performance.
- v2 action: implement real progress and image-level loading state.

Accessibility:

- What exists: labels are present for forms, image alt text exists, and icon buttons have aria labels in the filmstrip controls.
- Weakness: many status/filter/group buttons rely on visual state only, keyboard focus flow for the dense workspace is not deeply tested, and color contrast should be audited.
- User risk: accessibility regressions in v2 workspace.
- v2 action: add accessibility checks in E2E and component tests.

Maintainability:

- What exists: most components are readable, but `CullingWorkspace` is already large.
- Weakness: workspace behavior is concentrated in one component, while API types and client behavior are handwritten in `api.ts`.
- User risk: v2 features will make the frontend harder to modify safely.
- v2 action: split components and consider generated or schema-aligned API types.

## 6. Algorithm Review

Sharpness score:

- Current method: variance of a simple Laplacian over luminance in `compute_quality_scores`.
- Keep: useful deterministic baseline for obvious blur.
- v2 concern: not calibrated for sensor size, resizing, sharpening, noise, or subject-region sharpness.

Blur score:

- Current method: inverse of normalized sharpness.
- Keep: simple explainable risk indicator.
- v2 concern: global blur can punish intentional motion or shallow depth of field.

Exposure score:

- Current method: distance of mean luminance from middle gray.
- Keep: useful for obvious exposure failures.
- v2 concern: mean luminance is weak for high-key, low-key, backlit, night, and stage photography.

Contrast score:

- Current method: normalized luminance standard deviation.
- Keep: simple technical signal.
- v2 concern: can reward harsh contrast or punish intentionally flat scenes.

Noise score:

- Current method: high-frequency luminance deviation estimate.
- Keep only as a weak heuristic.
- v2 concern: it confounds detail, texture, sharpening, and noise.

Face/eye-open heuristic:

- Current method: skin-color mask, candidate bounding box checks, face-region sharpness, and dark detail in an eye region.
- Keep only as an explicitly experimental MVP signal.
- v2 concern: too weak for production portrait culling and likely biased by lighting, skin tone, color grading, pose, scale, and occlusion.
- v2 action: replace with optional local face/landmark/eye model later, or remove from ranking until reliable.

Aesthetic score:

- Current method: average of exposure and contrast.
- Keep as a placeholder only.
- v2 concern: it is not a real aesthetic model.
- v2 action: rename or recalibrate if kept; optional lightweight local aesthetic model can be introduced later without bundling large model files.

Embedding or similarity approximation:

- Current method: `image_embedding` combines a 64-bit perceptual hash with an 8x8 RGB sample and normalizes the vector.
- Keep: useful for small deterministic near-duplicate experiments.
- v2 concern: too weak for robust burst grouping, crop/pose variation, exposure variation, and non-adjacent duplicates.
- v2 action: combine perceptual hashes, color/layout descriptors, metadata, and candidate windowing before optional local model embeddings.

Grouping threshold strategy:

- Current method: compare adjacent sorted photos with cosine similarity threshold `0.96` and max time gap of 30 seconds.
- Keep: deterministic baseline tests.
- v2 concern: adjacent-only comparison is fragile and thresholds are not calibrated against real datasets.
- v2 action: build a tested grouping strategy with configurable thresholds, metadata features, and quality metrics.

Ranking formula:

- Current method: `final_score = 0.30 * sharpness + 0.20 * exposure + 0.20 * face_quality + 0.20 * aesthetic - 0.10 * duplicate_penalty`.
- Keep: transparent code-configurable weighting.
- v2 concern: inputs are weak and duplicate penalty is simplistic.
- v2 action: retain transparent ranking but improve metrics and allow genre/profile configuration.

Recommendation explanation:

- Current method: rule-based strongest/weakest metric text in `ranking.py`.
- Keep: good product principle and local-first.
- v2 concern: explanation quality depends on weak metrics.
- v2 action: continue rule-based explanations; do not require an LLM for MVP/v2.

Optional AI models:

- Good candidates later: lightweight local face/landmark/eye state, aesthetic quality, semantic blur/subject detection, or better embeddings.
- Constraint: do not add large bundled model files to the repository. If models are allowed, make them optional local downloads or user-provided assets.

Model-free algorithms still preferable:

- Derivative generation, EXIF parsing, file safety, basic sharpness/exposure/contrast, perceptual hashing, filename sequence analysis, and export logic should remain deterministic and testable.

## 7. Performance and Scalability Review

100 photos:

- v1 should probably handle this for JPEG/PNG/WebP on a normal machine.
- Risk areas are mostly UX polish and synchronous request duration.

500 photos:

- v1 may work but becomes uncomfortable. Import does scoring, derivatives, and embeddings during upload handling. Processing is synchronous and commits repeatedly while creating groups.
- Frontend filmstrip and photo arrays are not virtualized.

2,000 photos:

- v1 is not realistically validated for this target despite the product scenario in `develop_plan.md`.
- Synchronous import/process/export is a major limitation. The browser workspace may render too many thumbnails and group buttons.

10,000 photos:

- v1 is not suitable. Disk usage, derivative generation time, SQLite access patterns, memory, frontend rendering, export duration, and recovery behavior all need v2 design work.

Synchronous processing limitations:

- `process_project` runs entirely inside the request. The job model exists but does not provide live progress.
- v2 should use background workers or an in-process queue with durable job records before considering more complex systems.

Memory usage risks:

- Imports convert each image to RGB and NumPy arrays. This is fine one at a time, but large images and concurrent uploads can pressure memory.
- Frontend loads all photos/groups through API queries and renders all visible thumbnails.

Thumbnail generation costs:

- Thumbnail and preview generation happen immediately during import.
- v2 should process derivatives with bounded concurrency and resumable item status.

Database query risks:

- v1 uses simple SQLModel queries and should be fine at small scale.
- For thousands of photos, v2 needs indexes for project/group/status/recommendation ordering and careful pagination or filtered queries.

Frontend rendering risks:

- `CullingWorkspace` maps all groups and all visible photos directly.
- v2 should virtualize filmstrip and group lists, and avoid refetching full photo sets after each status update when possible.

Export risks:

- CSV, ZIP, and folder exports are synchronous. ZIP creation for thousands of originals can take a long time.
- v2 should queue exports and show export progress/history.

Long-running task UX:

- v1 status UI cannot show real progress while a request is still pending.
- v2 should expose durable progress and allow retry/resume.

Practical v2 architecture improvements:

- Add a simple local job queue, item-level processing states, bounded concurrency, polling endpoints, pagination/filtering, and virtualized UI lists.
- Avoid overengineering with distributed queues or cloud services. A single-process local worker is enough for an early v2.

## 8. Testing and Quality Review

Backend tests:

- Good coverage exists in `apps/api/tests/`. Tests verify project creation, invalid names, import/process/update/export flow, duplicate filename handling, import cleanup, mixed import skips, processing invalidation, group ordering, recommendation ordering, export validation, and legacy export column migration.
- Gaps: large-batch behavior, path traversal on generated assets, failed export status handling, structured job errors, richer metadata parsing, and performance thresholds.

Frontend tests:

- Current tests cover `projectNextHref`, `nextPhotoIdAfterMark`, and export status counting.
- Gaps: no component tests for import, processing, culling, export, keyboard handling, loading states, or errors.

Mocked E2E tests:

- `tests/e2e/local-workflow.spec.ts` mocks API routes and verifies the browser flow from project list through process, culling, status update, and export.
- This is useful for UI routing but does not validate backend integration or real file behavior.

Real local E2E:

- `tests/e2e/real-local-smoke.spec.ts` creates a project, imports two generated PNG fixtures, processes, marks a pick, and exports CSV against the real local API/web servers.
- This is valuable but minimal. It does not cover large batches, skipped files, duplicate names, ZIP/folder export, download content, restart/resume, or error recovery.

Synthetic image datasets:

- Synthetic images exist inside tests through generated Pillow images and inline PNG buffers.
- There is no named dataset for grouping/scoring calibration.

Export tests:

- CSV/folder/ZIP service tests and API tests are good for MVP.
- Gaps: large export, missing original behavior, export progress, sidecar formats, and user-facing download/open-folder behavior.

File safety tests:

- Good tests exist for original preservation, cleanup on invalid imports, duplicate filenames, and export-root download checks.
- Add tests for generated asset path traversal and project deletion/archive semantics in v2.

Performance tests:

- None found.
- v2 should add smoke-level tests for 100/500 synthetic images and non-test benchmark scripts for 2,000+ photos.

Formatting/lint/typecheck scripts:

- Root scripts include `lint`, `typecheck`, `test`, `verify`, and `format`.
- Avoid running `format` during documentation-only tasks because it would modify files outside this document.

Recommended v2 test strategy:

- Keep current backend tests as regression coverage.
- Add item-level job tests, file safety tests, migration tests, and export queue tests.
- Add frontend component tests for workspace controls and error/loading states.
- Expand real E2E to cover import with skipped files, process progress, status updates, CSV download content, ZIP export, and restart/resume behavior.
- Add synthetic fixture datasets for blur, exposure, grouping, duplicate filenames, and portrait heuristic validation.
- Add performance smoke commands that are documented but not necessarily run on every commit.

Verification note for this review:

- `npm run test` passed during this review: 31 backend tests passed, 11 frontend helper tests passed, and the Next.js production build completed successfully.
- `npm run test:e2e` passed during this review: 5 Playwright tests passed, including the real local import/process/pick/CSV export smoke flow.

## 9. Documentation Review

README:

- Good: accurately states local-first behavior, current stack, supported formats, workflow, verification commands, and privacy notes.
- Missing for v2: desktop/browser direction, large-batch expectations, troubleshooting, storage policy details, and known limitations.

develop_plan.md:

- Good: clearly defines MVP goals, supported formats, scoring, grouping, UI pages, and local-first constraints.
- Missing for v2: updated product requirements, target scale, performance criteria, desktop workflow decisions, RAW/HEIC policy, and model strategy.

AGENTS.md:

- Good: defines repository constraints that matter, including local-first, original-file safety, no large models, English-only, deterministic MVP algorithms, and test expectations.
- Missing for v2: no v2-specific branch/migration policy yet.

docs/architecture.md:

- Good: concise and accurate for v1, including storage layout and synchronous processing.
- Missing for v2: background job architecture, queue model, storage modes, migrations, API versioning, and frontend state architecture.

docs/api.md:

- Good: endpoint list and import/export behavior are documented.
- Missing for v2: API versioning, job polling, pagination, error schemas, item-level processing status, and export history.

docs/scoring.md:

- Good: explains deterministic scoring and face/eye heuristic limitations.
- Missing for v2: algorithm strategy, calibration datasets, metric confidence, optional model policy, and grouping evaluation metrics.

## 10. v1 Limitations

- Critical: synchronous processing in `process_project` blocks long-running work and prevents real live progress.
- Critical: insufficient validation for large batches such as 2,000 to 10,000 photos.
- High: similarity grouping in `group_similar_photos` is too weak for real burst and near-duplicate workflows.
- High: face/eye-open heuristic in `_detect_face_signals` is too weak to drive serious portrait ranking.
- High: culling workspace maintainability and rendering performance risk in `CullingWorkspace.tsx`.
- High: insufficient real E2E validation; current real local smoke test is useful but narrow.
- High: limited progress and resume behavior for import, processing, and export.
- Medium: limited file format support; JPEG/PNG/WebP only, with no RAW or HEIC workflow.
- Medium: metadata extraction is basic and may miss real camera data.
- Medium: export/download UX is limited, especially folder export and professional sidecar formats.
- Medium: current job model exists but is not truly asynchronous or resumable.
- Medium: generated asset serving should use stricter resolved-root path checks.
- Medium: frontend test coverage is thin outside pure helper functions.
- Medium: no performance tests or calibrated synthetic/real image datasets.
- Low: documentation is good for v1 but missing v2 product, architecture, algorithm, testing, and migration documents.
- Low: all backend routes live in a single route file, which is manageable now but should be split for v2.

## 11. Recommended v2 Product Direction

v2 should become a serious local photo culling tool, not just a demo. The main direction should be local-first, high-volume, resumable, and photographer-oriented.

Recommended now:

- Local-first desktop-like workflow while preserving the current local web architecture until a desktop wrapper decision is made.
- Better batch import with explicit project storage policy.
- Background processing with durable progress and retry.
- Stronger duplicate/burst grouping.
- Better culling workspace ergonomics, including zoom, compare, group-first review, and virtualization.
- Better export workflow with queued exports and clearer output handling.
- Expanded real local E2E and performance validation.

Recommended after foundation:

- Sidecar metadata export, likely XMP if product owner confirms Lightroom/Capture One interoperability.
- Optional HEIC and RAW preview support if required.
- Optional lightweight local AI models for face/eye, embeddings, or aesthetics.
- User preference learning only after ranking and workflow basics are reliable.

Defer:

- Cloud sync, accounts, payments, collaboration, mobile, and large bundled models.
- Advanced personalized model training until v2 has stable datasets and user workflows.

## 12. v2 Architecture Proposal

Keep from v1:

- Local-first project storage.
- Copy-on-import safety unless product owner chooses reference-in-place.
- SQLite as the local metadata database.
- FastAPI and SQLModel for the backend.
- Next.js/React for the frontend, unless the product owner chooses a desktop wrapper.
- Deterministic baseline metrics and rule-based explanations.
- Current export modes as baseline functionality.

Refactor:

- Split `routes.py` into resource modules.
- Split `CullingWorkspace.tsx` into smaller components and controllers.
- Extract import, derivative, scoring, embedding, grouping, ranking, and export steps into job operations.
- Replace JSON strings for embeddings/statuses where appropriate with typed helpers or normalized records.

Redesign:

- Processing architecture, progress model, grouping strategy, workspace state, export UX, and large-list rendering.

Backend processing architecture:

- Use a simple local job queue first. A single-process worker with durable SQLite job/item state is enough for v2.0/v2.1.
- Model jobs as import, derivative, score, group, rank, and export tasks.
- Store item-level status so interrupted runs can resume.
- Use bounded concurrency for image work.

Frontend state architecture:

- Keep React Query for server data.
- Keep a small local store for view state, but split selection, filter, keyboard, and preview state.
- Use optimistic updates carefully for status/rating changes.
- Add virtualized group and filmstrip lists.

Storage layout:

- Keep project subdirectories but add explicit `sidecars/`, structured `cache/`, and job artifacts if needed.
- Decide whether `originals/` means copied originals only or whether reference-in-place projects are allowed.

Job queue/background processing approach:

- Start with in-process local workers and polling endpoints.
- Avoid Celery/cloud queues for early v2.
- Add cancellation/retry/resume before advanced scheduling.

Database migration approach:

- Add a documented SQLite migration system. A small Alembic setup or explicit migration runner is acceptable.
- Record schema version in the database.

API versioning approach:

- Preserve v1 endpoints during transition if possible.
- Add `/api/v2` for job-oriented contracts if request/response shapes change substantially.

Testing approach:

- Expand backend tests first for jobs and storage safety.
- Add real E2E flows that use local generated images.
- Add performance smoke tests outside the default fast test suite.

Documentation approach:

- Create product requirements, architecture, milestones, algorithm strategy, testing strategy, and migration plan before major code changes.

## 13. v2 Milestone Proposal

### v2.0 Foundation

- Objective: make the codebase ready for v2 changes without changing core behavior.
- Tasks: split route modules, split culling workspace components, add schema versioning plan, document storage policy, add missing file safety tests.
- Acceptance criteria: existing v1 behavior still passes; final diff is understandable and low risk.
- Test requirements: `npm run test`, relevant E2E smoke, lint, typecheck.
- Risks: refactor churn without product improvement.

### v2.1 Processing and Progress

- Objective: replace synchronous processing with durable background jobs.
- Tasks: add job/item tables, worker loop, polling endpoints, processing resume, structured errors, and frontend progress polling.
- Acceptance criteria: processing shows live progress and can recover from interruption.
- Test requirements: backend job tests, API processing tests, real E2E process flow.
- Risks: concurrency bugs and SQLite locking.

### v2.2 Culling Workspace Upgrade

- Objective: improve high-volume review UX.
- Tasks: virtualized filmstrip/group list, split workspace components, zoom/fit controls, compare mode, stronger keyboard controller, better loading/error states.
- Acceptance criteria: workspace remains responsive with at least 2,000 synthetic photos.
- Test requirements: component tests, E2E keyboard/status tests, accessibility checks.
- Risks: UI complexity and state synchronization bugs.

### v2.3 Export and Interoperability

- Objective: make exports professional and resilient.
- Tasks: queued exports, export history, folder/open-path UX, CSV improvements, optional sidecar/XMP if required.
- Acceptance criteria: large exports show progress, can be retried, and produce validated artifacts.
- Test requirements: export queue tests, CSV/ZIP/folder tests, E2E download validation.
- Risks: platform-specific folder behavior and interoperability scope creep.

### v2.4 Algorithm Quality Upgrade

- Objective: improve grouping and ranking trust.
- Tasks: better perceptual descriptors, metadata-aware grouping, threshold calibration, ranking profiles, confidence-aware explanations.
- Acceptance criteria: grouping/ranking improves on a defined synthetic and real sample set.
- Test requirements: dataset-driven tests and algorithm regression reports.
- Risks: overfitting to small datasets.

### v2.5 Performance and Reliability

- Objective: validate and tune for thousands of photos.
- Tasks: pagination/filtering, query indexes, bounded image concurrency, export performance, memory monitoring, restart/resume tests.
- Acceptance criteria: documented performance for 500, 2,000, and target max batch size.
- Test requirements: performance smoke scripts and reliability E2E.
- Risks: machine-dependent measurements.

### v2.6 Optional RAW/HEIC and AI Model Support

- Objective: add advanced format/model support only if product owner confirms need.
- Tasks: RAW/HEIC preview extraction, optional model download/config, model-free fallback, documentation.
- Acceptance criteria: no large models committed; unsupported systems still run the baseline workflow.
- Test requirements: format fixtures, optional dependency tests, fallback tests.
- Risks: dependency weight, platform differences, and support burden.

## 14. Recommended First v2 Iteration

Exact development objective:

- Implement a documentation-backed v2 foundation refactor plan and add targeted safety tests for generated asset path handling, without changing product behavior.

Files likely to change:

- `docs/v2_product_requirements.md`
- `docs/v2_architecture.md`
- `docs/v2_testing_strategy.md`
- `apps/api/app/api/routes.py` or new route modules if the branch includes small refactoring
- `apps/api/tests/test_import_process_export_api.py` or a new file safety test module

Tests to add:

- Generated asset route rejects unsupported kinds.
- Generated asset route cannot escape `thumbnails/` or `previews/` through crafted filenames or corrupted paths.
- Existing import/process/export smoke remains passing.

Commands to run:

- `npm run test`
- `npm run lint`
- `npm run typecheck`
- `npm run test:e2e` if local Playwright/browser dependencies are available.

Definition of done:

- v2 product and architecture decisions are documented enough to guide implementation.
- No v1 behavior regresses.
- File-serving safety tests pass.
- The next branch can start background job implementation with clear acceptance criteria.

This is small enough for one Codex Goal Mode session if limited to documentation plus safety tests. If route refactoring is included, keep it mechanical and behavior-preserving.

## 15. Questions for Product Owner

- Should v2 remain a browser app, become a local desktop app, or use a hybrid local web app with a desktop wrapper?
- Is RAW support mandatory for v2, or can v2 start with JPEG/PNG/WebP plus optional HEIC?
- Is Lightroom/Capture One interoperability mandatory, especially XMP sidecar export?
- What target batch size should v2 optimize for: 500, 2,000, 10,000, or another number?
- Which operating systems must be supported first?
- Must FramePilot always copy originals, or should it support reference-in-place projects?
- Are optional AI models allowed as local downloads or user-provided files?
- Is user preference learning required in v2, or should it be deferred?
- Does GPU acceleration matter for the first v2 release?
- How strict are privacy requirements around face/eye analysis and metadata storage?
- Should project deletion remove copied originals and generated outputs, or only archive/delete database records?
- Should v2 prioritize speed, ranking quality, export interoperability, or UI ergonomics first?

## 16. Suggested New Documents

Create these later; do not create them as part of this v1 review task.

- `docs/v1_review_for_v2.md`: this review document.
- `docs/v2_product_requirements.md`: product decisions, target users, target batch sizes, platform direction, and supported workflows.
- `docs/v2_architecture.md`: backend/frontend/storage/job architecture.
- `docs/v2_milestones.md`: milestone plan with acceptance criteria.
- `docs/v2_algorithm_strategy.md`: grouping, ranking, scoring, optional model, and calibration strategy.
- `docs/v2_testing_strategy.md`: unit/API/component/E2E/performance test plan.
- `docs/v2_migration_plan.md`: schema, storage, API, and project data migration approach.

## 17. Final Recommendation

FramePilot should evolve v1 incrementally on a structured v2 branch, not start over. The current repository has enough correct local-first behavior, tests, and documentation to be a strong base. However, v2 should not simply add features on top of the current synchronous MVP.

Recommended first branch name:

- `codex/v2-foundation-review`

What should not be done yet:

- Do not implement RAW/HEIC support before product owner confirmation.
- Do not add large bundled AI models.
- Do not add cloud sync, login, payments, or remote-service requirements.
- Do not rewrite the frontend or backend wholesale.
- Do not create all v2 documents at once unless the product owner has approved the v2 direction.

What should be done immediately after this review:

- Confirm product owner answers for platform, target batch size, copy-vs-reference storage, RAW/HEIC, XMP export, and optional AI model policy.
- Create the v2 product requirements and architecture documents.
- Start v2.0 foundation work with behavior-preserving refactors and safety tests.
- Then implement background processing and real progress before deeper algorithm or UI upgrades.

Concise review summary:

- v1 is a usable local-first MVP with solid backend tests and a complete workflow.
- v1 is not production-ready for serious photo culling because processing, grouping, ranking quality, UI scale, and real E2E/performance validation need v2 work.
- Preserve the local-first architecture, original safety, deterministic baseline metrics, transparent recommendations, and current export baseline.
- Redesign processing/progress, grouping, workspace architecture, export interoperability, and test coverage for real batches.
