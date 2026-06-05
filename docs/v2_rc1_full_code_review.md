# FramePilot v2.0.0 RC1 Full Code Review

Review date: 2026-06-05.

Reviewed commit: `0415a87fa89594298b86c46565859b3b02d1019b`.

Reviewed branch: `codex/v2-next-iteration`.

Reviewed release: [FramePilot v2.0.0 RC1](https://github.com/joe-cheung-cae/frame-pilot/releases/tag/v2.0.0-rc1).

## 1. Executive Verdict

Verdict: **RC1 is acceptable but should produce rc2 before broader use.**

FramePilot v2.0.0 RC1 is technically coherent for a local-first JPEG, PNG, and WebP culling release candidate. The repository, release tag, release body, README, architecture docs, API docs, known limitations, and verification suite mostly tell the same story: local project workflow, upload/register import with in-process derivative jobs, deterministic scoring/grouping/ranking, keyboard-first review, manual override, CSV/ZIP/folder export, and explicit limits around RAW/HEIC, in-process job durability, synthetic validation, and heuristic face/eye signals.

No critical data-safety issue was found. Originals are copied into project storage, derivative and export artifacts are written separately, asset and export download paths are guarded, cloud upload/account/payment/telemetry requirements are absent, and the requested verification commands passed.

The main reason to cut rc2 before broader use is job-state correctness around interrupted or overlapping work:

- A project can still be processed while an import derivative job is active if the user enters the dashboard, project list next action, direct processing route, or culling route instead of waiting on the import page. The import page blocks this path, but the backend `POST /process` and other frontend entry points do not.
- A stale processing job can leave partially committed `PhotoGroup` records and processed photo state visible if the API process exits after one or more group commits. The stale-job failure path resets only photos still marked `processing`; it does not clear partial groups or force the culling workspace to require full group coverage.

Those are not proof that RC1 corrupts originals, but they can produce confusing or stale recommendations after realistic local interruptions. They should be fixed before rc2.

RC2 follow-up note, 2026-06-05: the active-import sequencing blocker is now addressed in code by exposing `active_import_job` on project responses, returning `409 Conflict` from `POST /api/projects/{project_id}/process` while import is queued/running, routing project list/dashboard actions back to import progress, disabling the processing run action, and showing an import-running guard in the culling workspace. The stale-processing partial-group blocker is also addressed by making project/jobs endpoints fail stale processing jobs, clear partial groups, remove photo group assignments, reset processed or in-progress photos to retryable imported state, reset the project processed count to zero, and allow a later processing run to rebuild groups cleanly.

RC2 export safety note, 2026-06-05: ZIP and folder exports now validate selected source files against the project `originals/` directory before copying or archiving. Missing originals still report the missing path for local diagnostics, while project-originals containment failures use a path-free safety message and remove partial export artifacts inside the project export root.

RC2 metadata note, 2026-06-05: visible release metadata is now aligned to `2.0.0-rc2` in the root package metadata, web package metadata, API package metadata, npm lockfile root package entries, and the FastAPI OpenAPI version.

RC2 tooling note, 2026-06-05: the E2E runner now removes the inherited `NO_COLOR`/`FORCE_COLOR` conflict, and the Next dev config explicitly allows the local `127.0.0.1` E2E origin for internal `/_next/*` assets. The Starlette/TestClient deprecation warning remains a dependency-level notice until the FastAPI/Starlette test client stack moves to `httpx2` or an equivalent supported client.

## 2. GitHub Release Consistency Review

Release evidence:

- `gh release view v2.0.0-rc1 --repo joe-cheung-cae/frame-pilot --json tagName,targetCommitish,name,isPrerelease,isDraft,publishedAt,body,url`
- Result: tag `v2.0.0-rc1`, target `main`, pre-release `true`, draft `false`, title `FramePilot v2.0.0 RC1`, published `2026-06-05T06:13:38Z`.
- Local tag `v2.0.0-rc1` points to `0415a87`, which is also current `HEAD`, `origin/main`, and `main`.

Consistent claims:

- Supported formats are JPEG, PNG, and WebP. Code accepts `.jpg`, `.jpeg`, `.png`, and `.webp` in `apps/api/app/services/importing.py:20`; HEIC/RAW planned extensions are skipped with explicit reasons in `apps/api/app/services/importing.py:231`.
- Local-first behavior is supported by code shape: the frontend API base defaults to `http://127.0.0.1:8000` in `apps/web/src/lib/api.ts:1`, backend CORS is local dev origins only in `apps/api/app/main.py:20`, and the remote-service search found no cloud upload, auth, payment, or telemetry code paths.
- Upload/register import plus background derivative generation is implemented in `apps/api/app/api/routes.py:177` and schedules `run_import_derivative_job` at `apps/api/app/api/routes.py:263`. The large real browser-backend run confirms the endpoint response was about `2.568 s` while import-ready completion was about `99.489 s`.
- Processing is backgrounded through FastAPI `BackgroundTasks` in `apps/api/app/api/routes.py:290`.
- Manual status and star rating override exists in `apps/api/app/api/routes.py:480` and batch updates in `apps/api/app/api/routes.py:450`.
- CSV, ZIP, and folder export exist in `apps/api/app/api/routes.py:524` and `apps/api/app/services/exporting.py:46`.
- The release body correctly records the waiver for non-private real-world algorithm validation and points to `docs/v2_real_world_validation.md` and `docs/templates/algorithm_validation_notes_template.md`.
- The release body correctly calls out in-process job durability, heuristic face/eye signals, synthetic benchmark caveats, and original-file immutability.

Questionable or incomplete claims:

- Release and tag names say `v2.0.0-rc1`, but RC1 root package metadata, web package metadata, API package metadata, and FastAPI OpenAPI metadata still exposed `0.1.0`. This is not a runtime bug, but it was visible metadata drift. The rc2 working tree now aligns these visible metadata fields to `2.0.0-rc2`.
- The release says import/background processing jobs are included. That is true, but the release note does not mention that process can be started while an import job is still active from routes other than the import page.
- The release note does not mention the stale-processing partial-group edge case described in this review.

Items to correct or clarify in rc2 release notes:

- State that rc2 blocks processing while import jobs are active, once fixed.
- State how stale processing cleanup handles partial groups, once fixed.
- State that visible package/OpenAPI version metadata now aligns with `2.0.0-rc2`.
- Keep the manual real-world validation waiver explicit until real notes are recorded.

## 3. Repository and Documentation Review

What is good:

- `README.md` is current for the RC1 scope. It names local-first behavior, JPEG/PNG/WebP support, background import jobs, cancellation/retry/stale limits, heuristic face/eye signals, and CSV/folder/ZIP export.
- `docs/architecture.md`, `docs/v2_architecture.md`, and `docs/api.md` match the implemented route surface and job model closely.
- `docs/scoring.md` and `docs/v2_algorithm_strategy.md` document deterministic scoring, grouping thresholds, ranking weights, and heuristic limits honestly.
- `docs/v2_known_limitations.md` is strong. It captures RAW/HEIC deferral, in-process job durability, cancellation/retry semantics, synthetic benchmark caveats, SQLite assumptions, and export limitations.
- `docs/v2_release_review.md` and `docs/v2_release_candidate_checklist.md` support the release body: verify passed, real browser-backend smoke passed, large generated smoke passed, full E2E passed, and manual real-world evidence was not recorded before the waiver.
- `docs/v2_real_world_validation.md` and the template give practical privacy rules and validation metrics.

Weaknesses and drift:

- Some current-state docs still contain historical branch names from pre-RC review work, including `feature/v2-performance-iteration` in `docs/v2_iteration_review.md:31` and `docs/v2_development_progress_summary.md:5`, plus `codex/v2-current-tasks-review` in `docs/v2_current_development_tasks_review.md:5`. Low risk, but confusing for a release audit.
- Version metadata is stale as described above.
- The docs do not explicitly warn that processing should be blocked while import derivative work is active. The import page UX implies this, but backend and other frontend routes do not enforce it.
- Stale processing cleanup docs say interrupted jobs are marked failed and later processing can retry, but they do not explain partial group visibility if a process exits after some group commits.
- `docs/v1_review_for_v2.md` remains valuable history but can look stale if read out of order. README links enough current docs that this is low risk.

RC2 recommendation:

- Add a short release-readiness note after the two job-state fixes land.
- Align version metadata or explicitly document why package/OpenAPI versions remain pre-1.0.
- Refresh branch names in current-state review docs or mark those docs as historical snapshots.

## 4. Backend Architecture Review

| Area | Evidence | What is good | Weakness | User impact | RC2 recommendation |
| --- | --- | --- | --- | --- | --- |
| Route organization | `apps/api/app/api/routes.py` | The API surface covers projects, imports, jobs, photos, groups, exports, and assets with plural routes and compatibility aliases. | `routes.py` is large at 659 lines. | Reviewability risk, not current behavior risk. | Split later only with behavior-preserving tests. |
| SQLModel models | `apps/api/app/models/entities.py` | Models cover projects, photos, groups, jobs, and exports with review and processing state fields. | Status fields are free strings rather than enums. | Invalid state is mostly guarded by schemas and service code, but DB edits can bypass. | Optional enum tightening after rc2 job fixes. |
| SQLite/session setup | `apps/api/app/db/session.py` | Additive compatibility migrations and indexes exist. Background workers open fresh sessions through `get_engine()`. | New engine per session and no WAL are accepted local MVP constraints. | Could limit concurrency under larger local workflows. | Defer WAL/concurrency tuning to v2.1 unless measured pain appears. |
| Project storage | `apps/api/app/services/projects.py:9` | Creates originals, derivatives, cache, export, and logs directories locally. | Custom `root_path` can be anywhere local and is trusted after creation. | Acceptable for a local app. | Keep explicit UI path display. |
| Original file safety | `apps/api/app/services/importing.py:623` and tests around `apps/api/tests/test_import_process_export_api.py:310` | Uploads are copied into project `originals/`; tests confirm external source bytes and mtimes stay unchanged. | Invalid image uploads keep the copied project original for retry evidence. | Good for source safety; copied project storage can accumulate failed originals. | Document or add cleanup/archive choices later. |
| Import upload/register | `apps/api/app/api/routes.py:177`, `apps/api/app/services/importing.py:610` | Request copies supported files and creates `Photo` rows in `processing` state. Same filename/hash with existing derivatives reuses the existing record. | New photo rows are counted in `total_images` before derivatives and analysis finish. | Enables progress, but other routes can see incomplete photos. | Block processing while active import exists. |
| Background derivative worker | `apps/api/app/services/importing.py:805` | Opens a fresh DB session, checks cancellation, generates derivatives, metadata, scores, hashes, embeddings, and marks terminal job states. | In-process only; no restart durability. | Accepted RC1 limitation. | Durable worker can wait for v2.1 after rc2 state guards. |
| Job progress model | `ProcessingJob` in `apps/api/app/models/entities.py:86` | Tracks type, status, step, totals, failed count, progress, cancellation, started/completed times, and retryable property. | Retryable is import-only, which is okay for current retry surface. | Clear enough for RC1. | Keep. |
| Stale import jobs | `apps/api/app/services/importing.py:178` | Stale active imports become failed and retryable. Failed counts are bounded. | Does not attempt automatic resume after process exit. | User must retry. | Accepted RC1, durable retry v2.1. |
| Stale processing jobs | `apps/api/app/services/processing.py:192` | Stale jobs become failed and in-progress photos return to imported state. | Partial groups committed before a crash are not cleared. `process_project` commits each group at `apps/api/app/services/processing.py:320`. | Direct culling can show stale partial recommendations after a process interruption. | Must fix before rc2: clear groups on stale processing failure or make culling require full valid coverage. |
| Retry flow | `apps/api/app/api/routes.py:345`, tests `apps/api/tests/test_import_process_export_api.py:1049` | Retry preserves photo ids, status, rating, existing derivatives, and copied originals. | Retry is import-only and does not re-register a source folder. | Honest and sufficient for RC1. | Keep. |
| Cancellation flow | `apps/api/app/api/routes.py:322`, `apps/api/app/services/importing.py:791` | Cooperative cancellation flag persists and is checked before and after photo-level work. Tests cover state and retry. | Not a hard kill and may finish current photo. | Documented and acceptable. | Keep; maybe expose current-photo wording in UI later. |
| Processing/group rebuild | `apps/api/app/services/processing.py:244` | Clears groups before a normal processing run, validates derivatives, groups, ranks, and stores summaries. | Does not reject when active import exists. | Race can produce stale scores/groups from incomplete import analysis. | Must fix before rc2. |
| Asset serving | `apps/api/app/api/routes.py:640` | Uses basename and resolved-root checks; tests cover symlink escapes. | Serves only thumbnails/previews, not original files. | Good for safety. | Keep. |
| Export service | `apps/api/app/services/exporting.py:46` | CSV, folder, ZIP, duplicate filename handling, missing-file failure. | Source path selection trusts DB `project_copy_path`/`original_path` without confirming it resolves inside project `originals`. | Normal API flow is safe, but corrupted DB could export arbitrary local files. | Should fix before rc2 as defense in depth. |
| Export downloads | `apps/api/app/api/routes.py:613` | Completed CSV/ZIP only, resolves output under export root, rejects symlink escapes. Tests cover failed/incomplete/outside artifacts. | Folder exports are path-only, not downloadable. | Expected. | Keep. |
| Error handling | routes and tests | HTTP 422/409/500 paths are tested for many workflows. | Export missing-file errors expose local paths in API detail. | Local app, but path disclosure should be understood. | Keep for local diagnostics, avoid uploading logs. |
| Logging | local logs directory exists | No remote logging found. | Minimal structured logging. | Debuggability gap, not release blocker. | Optional v2.1. |

## 5. Frontend Architecture and UX Review

| Area | Evidence | What is good | Weakness | User impact | RC2 recommendation |
| --- | --- | --- | --- | --- | --- |
| Project creation/opening | `ProjectCreator`, `ProjectList`, `ProjectDashboard` | Custom local data folder is exposed. Project cards link to the next workflow step. | `projectNextHref` only uses `total_images` and `processed_images` in `apps/web/src/lib/projectRouting.ts:3`; it does not account for active import jobs. | User can be routed to processing while derivatives are still running. | Must fix before rc2. |
| Import UI | `apps/web/src/components/ImportPanel.tsx` | Shows progress, skipped files, retry, cancel, recent thumbnails, project data path, and disables Process on failed/cancelled/running import. | Disabled fallback text always says "Import images before processing this project" even for failed/cancelled import. | Minor confusion. | Low-priority wording cleanup. |
| Progress polling | `ImportPanel`, `ProcessingPanel`, `processingProgress.ts` | Polls active import and processing jobs and formats counts. | Processing page does not poll import jobs. | Direct route can miss active import state. | Must fix with active import guard. |
| Stale/failed/retry/cancel states | `ImportPanel` tests in `tests/e2e/local-workflow.spec.ts:1331` | Import cancel/retry is visible and tested. Processing failed retry button exists. | Processing retry is "run processing again"; no separate process job retry endpoint, which is okay. | Mostly clear. | Keep. |
| Culling workspace | `apps/web/src/components/CullingWorkspace.tsx` | Keyboard-first review, filters, group sidebar, compare, zoom, failure filters, windowed rendering, localStorage review progress. | `CullingWorkspace.tsx` is 865 lines. The "Processing Needed" guard checks only no groups plus zero processed images at `apps/web/src/components/CullingWorkspace.tsx:424`; stale partial groups can bypass it. | Stale partial groups can become visible after interrupted processing. | Must fix with stronger coverage check or backend cleanup. |
| Keyboard shortcuts | `reviewShortcuts.ts`, help page, tests | Broad shortcuts are documented and covered. | Component-level shortcut integration remains mostly E2E. | Acceptable. | Keep. |
| Group navigation | `reviewNavigation.ts`, tests | Windowing and selection helpers are well covered. | Culling page can show partial group lists unless all groups loaded or data is valid. | Mostly OK, stale partial group is the exception. | Fix stale group guard. |
| Status/rating updates | `CullingWorkspace.tsx:193`, API tests and helper tests | Optimistic update with rollback and status count updates. | No conflict handling beyond last write wins. | Single-user local app, acceptable. | Keep. |
| Export UI | `ExportPanel.tsx` | Counts statuses through lightweight endpoint, exposes export folder, history, copy path, CSV/ZIP download. | Copy-to-clipboard can fail and is handled; no major issue. | Good for RC1. | Keep. |
| Loading/error/empty states | components and E2E | Many error states are covered. | Direct cull/process during active import remains under-covered. | See above. | Add targeted E2E/unit tests. |
| API client | `apps/web/src/lib/api.ts` | Centralized fetch, pagination helpers, error detail formatting. | `API_BASE` can be overridden to any URL. | Local-first default is safe; env override should be used carefully. | No change needed for RC1. |
| Large-list behavior | initial limit 500, load-all controls | Verified by 2,000 seeded culling smoke. | Real 2,000 browser-backend still unverified. | Accepted limitation. | Optional validation before final v2.0. |

## 6. Algorithm Review

| Area | Classification | Evidence | Notes |
| --- | --- | --- | --- |
| Sharpness/blur scoring | Acceptable for RC1 | `apps/api/app/image/scoring.py:137`, tests in `apps/api/tests/test_scoring.py` | Deterministic luminance/Laplacian scoring is simple and documented. |
| Exposure/contrast/noise scoring | Acceptable for RC1 | `apps/api/app/image/scoring.py:67` and `apps/api/app/image/scoring.py:142` | Suitable as MVP technical signals. Real camera diversity remains unvalidated. |
| Heuristic face/eye-open signals | Should not be claimed as reliable yet | `apps/api/app/image/scoring.py:75`, docs in `docs/scoring.md` | Correctly described as experimental local heuristics, not professional or biometric detection. |
| Embedding approximation | Acceptable with caveat | `apps/api/app/ai/embeddings.py`, grouping fallback in `apps/api/app/services/grouping.py:180` | Useful deterministic fallback, not semantic similarity. |
| Similarity grouping | Acceptable with caveat | `apps/api/app/services/grouping.py:161` | Conservative windows, metadata checks, pHash, embedding fallback, time-span splitting. Needs real-world notes. |
| Ranking formula | Acceptable with caveat | `apps/api/app/services/ranking.py:4` | Weights match docs and produce conservative singleton Maybe behavior. Real preference mismatch is expected. |
| Explanations | Acceptable with caveat | `apps/api/app/services/ranking.py:112` | Traceable and conservative. Face/eye wording includes "experimental" when relevant. |
| Deterministic fixture tests | Acceptable for RC1 | `apps/api/tests/test_deterministic_culling_fixtures.py` | Covers missing metadata, lookalike non-merge, blur/exposure explanations. |
| Real-world validation | Should be improved in rc2 | `docs/v2_real_world_validation.md` | The gate was waived for RC1. It should not be treated as complete confidence. |

No algorithm tuning is recommended from this review alone. The next algorithm work should record non-private manual validation notes first, then add deterministic tests before any threshold change.

## 7. Test and Benchmark Review

Commands run during this review:

| Command | Result | Duration | Summary | RC1-related? |
| --- | --- | ---: | --- | --- |
| `git status --short` | passed | n/a | Clean before documentation edits. | Yes |
| `git branch --show-current` | passed | n/a | `codex/v2-next-iteration`. | Yes |
| `git log --oneline --decorate -n 40` | passed | n/a | `0415a87` at HEAD/tag/main/origin. | Yes |
| `gh release view v2.0.0-rc1 --repo joe-cheung-cae/frame-pilot --json ...` | passed | <1s | Release body matches attached RC1 context. | Yes |
| `npm run verify` | passed | `real 22.65s` | Ruff passed, ESLint passed, TypeScript passed, 130 backend tests passed, 82 frontend unit tests passed, Next production build passed. | Yes |
| `npm run test:e2e:real-browser` | passed | `real 13.83s` | 100 generated JPEG real browser-backend workflow passed. Import ready `1763 ms`; process `2120 ms`; first preview `854 ms`; export `54 ms`. | Yes |
| `npm run test:e2e:real-browser:large` | passed | `real 120.49s` | 500 generated 3000x2000 JPEG workflow passed. Upload/register response `2568 ms`; import ready `99489 ms`; process `2611 ms`; first preview `838 ms`; export `53 ms`. | Yes |
| `npm run test:e2e` | passed | `real 28.92s` | 41 Playwright tests passed, including default real browser-backend smoke and 2,000 seeded culling workspace smoke. | Yes |

Warnings observed:

- `StarletteDeprecationWarning` from FastAPI/TestClient during backend tests.
- RC1 showed Node `NO_COLOR`/`FORCE_COLOR` warnings during Playwright runs; the rc2 runner now removes the inherited conflict before launching Playwright.
- RC1 showed a Next dev cross-origin warning for `/_next/*` resources; the rc2 web config now explicitly allows the local E2E origin.

Coverage assessment:

- Backend unit/API tests are strong for scoring, grouping, ranking, import, stale jobs, retry, cancellation, status updates, export, path safety, and migration/index compatibility.
- Frontend unit tests are strong for API helpers, export selection, processing progress, project routing, review filters/navigation/progress/scores/shortcuts, query invalidation, and settings.
- Mocked E2E covers many UI failure states and import/job controls.
- Real browser-backend smoke covers real frontend/backend import, processing, asset serving, status update, group navigation, and CSV export at 100 generated images by default and 500 large generated images through the large command.
- 2,000 seeded culling validates browser workspace scale but not real import/processing/large preview transfer.
- Real-world manual validation remains unrecorded and waived for RC1.

No requested verification command was skipped.

## 8. Safety and Privacy Review

Critical issues: none found.

High issues:

- Processing can start while import derivative work is still active. This is a workflow integrity problem, not original-file mutation, but it can create stale or misleading local recommendations.
- Stale processing jobs can leave partial groups visible after interruption.

Medium issues:

- ZIP/folder export source files are not revalidated to be under the project originals directory. Normal API-created records are safe, but DB tampering or corruption could make exports copy arbitrary local files.
- Real-world validation is waived, so algorithm quality claims must stay conservative.

Low issues:

- RC1 package and OpenAPI version metadata were still `0.1.0`; the rc2 working tree now aligns root, web, API package, lockfile root, and OpenAPI metadata to `2.0.0-rc2`.
- Historical/current review docs contain stale branch names.
- CSV exports intentionally include local paths and filenames. This is useful locally but can expose private paths if users share CSVs.
- Ignored generated artifacts exist locally: `.framepilot-data/`, `.framepilot-e2e-data/`, `.ruff_cache/`, `.venv/`, `apps/web/.next`, `apps/web/.next-e2e`, `test-results/`, and `framepilot-import-smoke.png`.

Safety evidence:

- No tracked generated/private artifacts were found by `git ls-files | rg '(node_modules|\\.venv|exports|cache|\\.zip$|\\.jpe?g$|\\.png$|\\.webp$|\\.arw$|\\.cr3$|\\.nef$|\\.dng$|\\.heic$|\\.sqlite$|\\.db$|test-results|playwright-report)'`.
- `git status --short` was clean before this review document was added.
- `.gitignore` covers the observed generated/cache artifacts.
- The app has no cloud upload, login, payment, remote processing, or telemetry requirement in application code.

## 9. Job System Reliability Review

What is sufficient for RC1:

- Import jobs are queryable and have visible progress.
- Import derivative work opens a fresh DB session and avoids reusing request-scoped sessions.
- Import cancellation is cooperative and safe at photo-level checkpoints.
- Import retry preserves existing photo ids, user statuses, star ratings, copied originals, and valid derivatives.
- Stale import and processing jobs are detected through job polling/history.
- Processing reruns are idempotent for unchanged fully processed projects.
- FastAPI `BackgroundTasks` durability limitations are honestly documented and included in the release note.

What needs rc2 work:

- `POST /api/projects/{project_id}/process` should reject or defer while an import job for the same project is queued/running. Evidence: processing only checks active processing jobs in `apps/api/app/api/routes.py:299`; active import jobs are only checked in import retry at `apps/api/app/api/routes.py:363`.
- Frontend routing and processing UI should also reflect active import jobs. Evidence: project routing uses only image counts in `apps/web/src/lib/projectRouting.ts:3`; ProcessingPanel enables Run based on `total_images` at `apps/web/src/components/ProcessingPanel.tsx:51`.
- Stale processing failure should clear partial groups and/or mark project group coverage invalid. Evidence: groups are committed per group in `apps/api/app/services/processing.py:320`, while `fail_stale_processing_job` at `apps/api/app/services/processing.py:192` does not delete groups.
- Culling should avoid opening a partial workspace when processed coverage is zero or incomplete. Evidence: `apps/web/src/components/CullingWorkspace.tsx:424` only blocks when there are no groups and zero processed images.

Durable queue recommendation:

- A durable local worker is not required before rc2 if the state guards above are fixed.
- A restart-safe worker or local queue should remain a v2.1 architecture task, informed by real 1,000 to 2,000 photo validation and interruption testing.

## 10. Export and Interoperability Review

RC1 sufficient behavior:

- CSV export includes status, rating, group, score, file identity, metadata, processing state, and error fields.
- ZIP and folder export preserve duplicate filenames with deterministic suffixes.
- Empty exports are rejected before artifacts are written.
- Failed exports record failed history and remove partial artifacts under the export root.
- CSV/ZIP downloads require `status="complete"` and reject symlink escapes outside the export root.
- Folder exports expose local output paths instead of pretending to be browser downloads.

RC2 fixes:

- Add a source-path guard for ZIP/folder exports. The selected source should resolve under the project root, preferably `originals/`, and reject symlink escapes.
- Add tests for DB-corrupted or symlinked `project_copy_path` values that point outside the project.
- Consider whether CSV export should keep both `original_path` and `project_copy_path` by default or offer a privacy-oriented export later.

v2.1 deferred:

- XMP sidecar export.
- Lightroom/Capture One compatibility validation.
- Queued export jobs only if large export validation shows synchronous exports block the UI.

## 11. Release Risk Register

| Risk ID | Severity | Area | Evidence | Description | User impact | Recommended mitigation | Target |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | High | Job sequencing | `routes.py:290`, `ProcessingPanel.tsx:51`, `projectRouting.ts:3` | Processing can start while import derivative work is active. | Stale or low-quality groups/recommendations from incomplete imported photos. | Backend 409/defer plus frontend route/UI guard and tests. | rc2 |
| R2 | High | Stale processing | `processing.py:320`, `processing.py:192`, `CullingWorkspace.tsx:424` | Interrupted processing can leave partial groups visible. | User may review/export stale partial recommendations. | Clear partial groups on stale failure or require full group coverage before culling. | rc2 |
| R3 | High | Real-world validation | Release body and `docs/v2_real_world_validation.md` | Manual non-private algorithm evidence was waived. | Grouping/ranking may disappoint on real camera sets. | Record Tier A/B validation notes before stronger release confidence. | rc2 |
| R4 | Medium | Job durability | `docs/v2_known_limitations.md`, FastAPI `BackgroundTasks` | Jobs do not survive API process exits. | User must retry interrupted local work. | Keep limitation in rc2; plan durable local worker for v2.1. | v2.1 |
| R5 | Medium | Face/eye heuristics | `scoring.py:75`, `docs/scoring.md` | Heuristic face and eye signals are not reliable detectors. | Misleading portrait hints if wording becomes overconfident. | Keep experimental wording and add real validation notes. | rc2/v2.1 |
| R6 | Medium | Synthetic benchmark limits | `docs/v2_performance_baseline.md` | Generated images underrepresent real camera diversity. | Performance/quality confidence may be overstated. | Keep caveats and add real non-private validation. | rc2 |
| R7 | Medium | 2,000 real browser-backend | `docs/v2_performance_baseline.md` | 2,000 real browser-backend import/process/review is unverified. | Unknown large real workflow cost. | Optional scheduled run after rc2 job guards. | v2.1 or final v2.0 gate |
| R8 | Medium | Export source path | `exporting.py:39` | ZIP/folder export trusts stored source paths. | DB corruption could copy arbitrary local files into exports. | Resolve source under project originals and test symlink escape. | rc2 |
| R9 | Low | Documentation drift | progress docs branch names, version metadata | Some historical docs still show old branches; RC1 metadata showed `0.1.0`. | Confusion during release audit. | Align visible metadata to `2.0.0-rc2` and keep historical branch references clearly scoped. | rc2 |
| R10 | Low | Private artifact risk | ignored local artifacts found | Local generated DBs, traces, images exist and are ignored. | Accidental force-add could leak data. | Keep ignore rules, run tracked artifact check before releases. | rc2/release |
| R11 | Low | Tooling warnings | verify/e2e output | Starlette/TestClient deprecation remains; Node color and Next allowedDevOrigins warnings were rc2 cleanup candidates. | Noise can hide real failures later. | Keep the dependency warning visible, but remove local runner/config warning noise. | optional rc2 |

## 12. RC2 Candidate Plan

### Must Fix Before rc2

Objective: Block processing while import jobs are active.

Why: Prevent processing from grouping photos before import derivative analysis, scores, hashes, and embeddings are complete.

Files likely to change: `apps/api/app/api/routes.py`, `apps/web/src/lib/projectRouting.ts`, `apps/web/src/components/ProcessingPanel.tsx`, `apps/web/src/components/ProjectList.tsx`, `apps/web/src/components/ProjectDashboard.tsx`, `apps/web/src/components/CullingWorkspace.tsx`, API and E2E tests.

Tests: backend test that active import returns 409 or equivalent from `/process`; frontend unit tests for next-route logic; E2E that processing page disables Run during active import.

Acceptance criteria: while an import job is queued/running, no UI path starts processing and the backend rejects direct process requests.

Suggested Codex prompt title: `Prevent processing while import jobs are active`.

Objective: Make stale processing cleanup remove or hide partial groups.

Why: A process exit after partial group commits can leave stale recommendations visible.

Files likely to change: `apps/api/app/services/processing.py`, possibly `apps/web/src/components/CullingWorkspace.tsx`, backend tests, E2E tests.

Tests: simulate a stale processing job with committed groups and verify stale detection clears groups or culling shows Processing Needed; verify rerun rebuilds cleanly.

Acceptance criteria: after stale processing failure, users cannot review partial groups as if processing completed.

Suggested Codex prompt title: `Harden stale processing cleanup and culling readiness`.

### Should Fix Before rc2

Objective: Add export source-path defense in depth.

Why: ZIP/folder exports should not trust corrupted DB source paths.

Files likely to change: `apps/api/app/services/exporting.py`, `apps/api/app/api/routes.py`, export tests.

Tests: DB photo with `project_copy_path` symlink/outside project is rejected; normal project copy export still works.

Acceptance criteria: ZIP/folder sources resolve under project originals or project root and cannot symlink escape.

Suggested Codex prompt title: `Guard export source paths inside project storage`.

Objective: Refresh release-facing metadata and docs.

Why: Reduce confusion around `0.1.0` metadata and old branch names.

Files likely to change: `package.json`, `apps/web/package.json`, `apps/api/app/main.py`, README/release docs if version policy changes.

Tests: `npm run verify`; check OpenAPI version if updated.

Acceptance criteria: release owner can explain version metadata and current docs no longer imply old review branches are current.

Suggested Codex prompt title: `Align rc2 release metadata and current-state docs`.

Objective: Record non-private real-world validation notes.

Why: RC1 waived the algorithm evidence gate; rc2 should improve confidence.

Files likely to change: a new validation notes document under `docs/`, maybe release review docs.

Tests: no code tests unless findings lead to algorithm changes.

Acceptance criteria: Tier A or Tier B notes record false merges, missed groups, ranking mismatches, explanation mismatches, export issues, and decision impact.

Suggested Codex prompt title: `Record rc2 real-world algorithm validation notes`.

### Optional Before rc2

- Keep Starlette/TestClient dependency deprecation visible; Node color and Next allowedDevOrigins warning noise are cleaned in rc2.
- Add a small docs note explaining copied failed originals and retry behavior.
- Add component-level tests for ImportPanel and ProcessingPanel once job-state logic changes.

### Defer To v2.1

- Durable local worker or restart-safe job queue.
- 2,000-photo real browser-backend benchmark as a scheduled validation run.
- XMP sidecar export and editor compatibility testing.
- HEIC/RAW embedded preview extraction.
- Optional local AI models.
- Desktop packaging.

## 13. Recommended Next Development Plan

Task 1: Prevent processing while import jobs are active.

Scope: Backend reject/defer active import conflicts, frontend route/processing/culling guards, tests.

Why it is next: It is the safest high-impact fix and closes the most likely confusing workflow race.

Expected files: `routes.py`, `processingProgress.ts` or new helper, `projectRouting.ts`, `ProcessingPanel.tsx`, `ProjectList.tsx`, `ProjectDashboard.tsx`, `CullingWorkspace.tsx`, backend tests, frontend unit/E2E tests.

Tests: targeted backend API test, frontend unit tests, `npm run verify`, targeted E2E for active import guard.

Docs: update `docs/api.md`, `docs/architecture.md`, `docs/v2_known_limitations.md` if behavior is visible.

Suggested commit message: `fix: block processing during active imports`.

Task 2: Harden stale processing cleanup.

Scope: Clear partial groups or mark group coverage invalid when stale processing fails; prevent culling from opening partial groups.

Why it is next: It closes the main restart/interruption correctness gap while keeping the in-process worker architecture.

Expected files: `apps/api/app/services/processing.py`, `apps/api/tests/test_import_process_export_api.py`, `apps/web/src/components/CullingWorkspace.tsx`, E2E if UI changes.

Tests: stale processing with existing partial groups; rerun rebuilds groups; culling shows Processing Needed or processing failure route.

Docs: update architecture and known limitations with exact stale cleanup semantics.

Suggested commit message: `fix: clear partial groups after stale processing`.

Task 3: Guard export source paths.

Scope: Require ZIP/folder source paths to resolve under project-controlled originals or project root.

Why it is next: It is a small safety hardening with clear tests.

Expected files: `apps/api/app/services/exporting.py`, `apps/api/app/api/routes.py`, export tests.

Tests: symlink/outside source rejection and normal export success.

Docs: update export path safety wording.

Suggested commit message: `fix: guard export source paths`.

Task 4: Record rc2 real-world validation notes.

Scope: Use non-private datasets and the existing template to record algorithm and export observations.

Why it is next: It turns the RC1 waiver into evidence before final release confidence.

Expected files: new docs validation note, release review updates.

Tests: no code tests unless findings trigger deterministic fixtures later.

Docs: validation notes plus any release risk update.

Suggested commit message: `docs: record rc2 algorithm validation notes`.

Task 5: Align rc2 metadata and docs.

Scope: Align visible version metadata, refresh stale branch names where they are current-state docs, update release docs.

Status: Package, web package, API package, npm lockfile root entries, and FastAPI OpenAPI metadata now use `2.0.0-rc2`.

Why it is next: It improves release clarity without changing behavior.

Expected files: `package.json`, `apps/web/package.json`, `apps/api/app/main.py`, current review docs, README if needed.

Tests: `npm run verify`.

Docs: release checklist/review update.

Suggested commit message: `docs: refresh rc2 release metadata`.

## 14. Final Checklist

- [x] Git status recorded
- [x] Release note consistency reviewed
- [x] Docs reviewed
- [x] Backend reviewed
- [x] Frontend reviewed
- [x] Algorithms reviewed
- [x] Tests/benchmarks reviewed
- [x] Safety/privacy reviewed
- [x] Job system reviewed
- [x] Export reviewed
- [x] Risks listed
- [x] RC2 plan proposed
- [x] Next Codex tasks proposed

Final review note: this document is intentionally review-only. No production code, algorithm tuning, API behavior, database model, frontend behavior, dependency, generated asset, photo, export, ZIP, SQLite database, trace, `node_modules`, or virtualenv file was modified by this task.
