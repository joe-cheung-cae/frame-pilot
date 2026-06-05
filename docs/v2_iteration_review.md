# FramePilot v2 Iteration Review

Review date: 2026-06-04

This document records the current FramePilot v2 repository state after the latest performance, import-progress, stale-job recovery, culling-state, worker-decision, and deterministic algorithm iterations. It is a current-state engineering review, not a historical v1 review.

## Summary

FramePilot is now a substantial local-first v2 foundation for JPEG, PNG, and WebP photo culling. The current branch has job-based processing, import job visibility, stale import and processing job recovery, deterministic scoring/grouping/ranking, a keyboard-first culling workspace, CSV/ZIP/folder export, export history, local path safety, and opt-in large-batch performance validation.

The repository is close to a v2.0 local MVP-plus release, but not yet production-ready. The main remaining risks are durable long-running work, real-photo validation, culling workspace maintainability, and advanced interoperability such as XMP sidecars.

Recent high-value changes:

- Import requests now create `job_type=import` records with stage/count progress, mixed-import `complete_with_errors`, failed all-skipped jobs, and same-file reuse.
- Import job progress is visible in the import UI while uploads are pending.
- Stale import and processing jobs are recovered from job polling/history, not only from a later process request.
- Stale job failed counts are bounded by remaining unprocessed items.
- Real browser-backend import/performance commands now cover 100 small images, 500 large generated images, and opt-in 1,000-photo generated-image workflows.
- Mocked browser culling validation covers a 2,000-photo seeded project with bounded rendering and load-all behavior.
- Culling workspace entry, selection, filter-reset, metadata row, score row, group summary, and header summary rules now live in tested helper modules.
- Grouping now considers filename-sorted candidate windows as well as capture-time order, which protects burst-like frames with missing capture metadata.
- Weak single-image groups now receive conservative Maybe recommendations instead of overconfident Pick recommendations.
- Deterministic grouping and ranking thresholds are documented in the algorithm and scoring docs.
- Non-private in-memory fixture families now validate missing-metadata burst grouping, lookalike scenes that should not over-merge, and blur/exposure explanation behavior.
- A manual real-world validation protocol and notes template now define how to record non-private grouping, ranking, and explanation review evidence.
- v2.0 accepts the current local in-process job architecture; a separate worker is deferred until real-scale validation proves it is needed.

## Repository State

Current branch: `feature/v2-performance-iteration`

Recent commits reviewed:

- `7cb8b61 docs: refresh deterministic threshold review`
- `63b34e9 docs: document deterministic culling thresholds`
- `c40c3b9 test: cover culling header summary`
- `7539d93 test: cover culling group summary rows`
- `8c6ae02 docs: refresh culling score row coverage`
- `cc6e3b3 test: cover culling score rows`
- `ad69e70 test: cover culling metadata rows`
- `bd486a9 v2: keep weak singletons as maybe`
- `6c77321 v2: use filename windows for grouping candidates`
- `cd48806 docs: record import worker decision`
- `5759a31 test: cover review filter progress reset`
- `91c4f4d test: cover culling selection state`
- `23f476b test: cover culling entry progress state`
- `07f00f9 test: bound stale job failure counts`
- `6a8d782 v2: recover stale processing jobs on poll`
- `70ab936 v2: fail stale import jobs`
- `3892053 test: cover live import job polling`
- `cfc292e test: cover active import progress`
- `0dd858f v2: show import job progress`
- `b447252 test: validate repeated and 1000-photo browser benchmarks`
- `8f6a599 perf: optimize preview generation path`
- `0153752 perf: optimize quality scoring path`
- `1249e3c perf: optimize preview webp encoding`

Working tree at review start:

- `docs/v2_iteration_review.md` was the only changed file before the fixture-validation slice.
- That review refresh is committed, and this iteration adds deterministic fixture validation plus these review updates.

Tracked generated/private-file check:

- Command: `git ls-files | rg "(node_modules|\\.venv|exports|cache|\\.zip$|\\.jpe?g$|\\.png$|\\.webp$|\\.arw$|\\.cr3$|\\.nef$|\\.dng$|\\.heic$|\\.sqlite$|\\.db$)"`
- Result: no tracked generated folders, private photos, large image datasets, archives, SQLite databases, `node_modules`, or virtualenv files were found.

## Milestone Status

| milestone                        | current status                        | evidence                                                                                                                                                                                     | remaining gap                                                                                    |
| -------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| v2.0 Foundation                  | Mostly complete                       | `README.md`, `AGENTS.md`, root scripts, v2 docs, passing verify                                                                                                                              | Release-oriented docs and packaging remain outside this branch                                   |
| v2.1 Processing and Progress     | Strong                                | `ProcessingJob`, `/jobs`, import progress, stale recovery tests                                                                                                                              | In-process jobs are accepted for v2.0; a separate worker is deferred pending real-scale evidence |
| v2.2 Culling Workspace           | Mostly complete                       | keyboard shortcuts, compare/zoom, bounded filmstrip/group windows, tested state helpers, 2,000 seeded E2E                                                                                    | `CullingWorkspace.tsx` remains large and not component-tested                                    |
| v2.3 Export and Interoperability | Mostly complete                       | CSV/ZIP/folder export, history, download endpoints, path safety tests                                                                                                                        | XMP sidecar export remains planned only; exports are synchronous                                 |
| v2.4 Algorithm Quality           | Mostly complete for deterministic MVP | grouping/ranking/scoring tests and docs, filename-window grouping, conservative singleton ranking, documented thresholds, realistic in-memory fixture validation, manual validation protocol | Needs completed real-world/manual validation notes                                               |
| v2.5 Performance and Reliability | Improved                              | API perf smoke, browser perf instrumentation, stale recovery, 100/500/1,000 real browser-backend runs                                                                                        | 2,000 real browser-backend run remains unattempted                                               |
| v2.6 Optional Advanced Support   | Deferred                              | unsupported HEIC/RAW messages and docs                                                                                                                                                       | HEIC/RAW/model support intentionally not implemented                                             |

Approximate v2.0 readiness: 86%.

Production readiness: about 60%, mainly limited by real-world validation, accepted in-process job limits, and UI maintainability.

## Verification

Commands run for this review:

| command                                                                                                                                              | result | summary                                                                                               |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| `npm run verify`                                                                                                                                     | passed | API lint, web lint, TypeScript, all backend tests, web unit tests, and Next production build passed   |
| `npm --prefix apps/web run test:unit`                                                                                                                | passed | 82 frontend helper/unit tests passed after culling state extractions                                  |
| `npm run typecheck`                                                                                                                                  | passed | TypeScript passed after culling state extractions                                                     |
| `npm run lint`                                                                                                                                       | passed | API ruff and web ESLint passed after culling state extractions                                        |
| `.venv/bin/pytest apps/api/tests/test_grouping.py apps/api/tests/test_ranking_export.py`                                                             | passed | 24 deterministic grouping, ranking, and export tests passed after grouping candidate changes          |
| `.venv/bin/pytest apps/api/tests/test_deterministic_culling_fixtures.py apps/api/tests/test_grouping.py apps/api/tests/test_ranking_export.py`       | passed | 28 deterministic fixture, grouping, ranking, and export tests passed after realistic fixture coverage |
| `.venv/bin/pytest apps/api/tests/test_ranking_export.py apps/api/tests/test_import_process_export_api.py::test_import_process_update_and_export_csv` | passed | 16 ranking/export and workflow tests passed after singleton recommendation changes                    |
| `npm run test:e2e -- tests/e2e/local-workflow.spec.ts --project=chromium --grep "filters culling photos with processing failures"`                   | passed | URL-filtered culling entry smoke passed                                                               |
| `npm run test:e2e -- tests/e2e/local-workflow.spec.ts --project=chromium --grep "validates the culling workspace with 2,000 seeded photos"`          | passed | Seeded 2,000-photo culling browser smoke passed                                                       |

Current verification details:

- Backend tests: 123 passed.
- Frontend unit tests: 82 passed.
- Next build: passed.
- Seeded 2,000-photo browser culling smoke: 1 passed.
- Latest 2,000-photo smoke timings: first preview `1446 ms`, status update `110 ms`, filter switch `28 ms`, load-all `247 ms`.
- Latest 2,000-photo smoke DOM/heap signals: initial DOM nodes `941`, loaded DOM nodes `915`, reported JS heap `42.63 MB`.

Warnings observed:

- `StarletteDeprecationWarning` from FastAPI/TestClient dependency stack.
- Node `NO_COLOR`/`FORCE_COLOR` warnings in Playwright server output.
- Next dev cross-origin warning for `_next/*` resources.

These warnings are not current failures, but they remain useful cleanup candidates.

## Current Strengths

- Local-first behavior remains intact. No cloud upload, login, payment, telemetry, or remote photo processing is present.
- Original photos are copied into project storage and source originals are not modified.
- Processing jobs can be started, polled, recovered from stale state, and retried.
- Import jobs now provide visible local progress and failure accounting.
- Mixed imports are tolerant: supported images proceed while skipped files are reported.
- Reimporting the same uploaded filename and SHA-256 content can reuse existing records and derivatives.
- Deterministic grouping is stronger than v1: capture-time and filename candidate windows, metadata compatibility, perceptual hash, embedding fallback, union-find, and time-span splitting are present.
- Ranking explanations are conservative and traceable to scoring factors.
- Export paths and asset paths are guarded by local path resolution checks and tests.
- The frontend supports keyboard-first review, status/rating updates, zoom, compare mode, filters, persistent review progress, and bounded large-list rendering.

## Current Risks

| priority | area                      | risk                                                                                                                                                        | next mitigation                                                                                                                        |
| -------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| P1       | Durable jobs              | Import and processing work can still be interrupted by local API process exits                                                                              | v2.0 accepts in-process jobs; revisit a worker after 2,000-photo real browser-backend validation or import-stage optimization evidence |
| P1       | Real-photo validation     | Generated fixtures do not prove photographer-quality grouping/ranking                                                                                       | Complete validation notes from non-private manual or real-world-like local sets                                                        |
| P1       | Real browser scale        | Seeded 2,000-photo UI passes and opt-in 1,000-photo real browser-backend workflows pass, but 2,000 real browser-backend import/process/review is unmeasured | Run/manual-document a 2,000 real browser-backend validation after import bottlenecks are acceptable                                    |
| P2       | Workspace maintainability | `CullingWorkspace.tsx` is still 865 lines                                                                                                                   | Extract controller/helper logic and add focused tests                                                                                  |
| P2       | Route/test size           | `routes.py`, `processing.py`, API tests, and E2E tests are large                                                                                            | Split by route/workflow only after behavior stabilizes                                                                                 |
| P2       | Export blocking           | CSV/ZIP/folder exports are synchronous                                                                                                                      | Queue exports only if larger export validation shows user-visible blocking                                                             |
| P3       | Docs drift                | Historical v1 docs can be confused with current state                                                                                                       | Keep current-state review and API/architecture docs updated                                                                            |

## File Size Signals

Current large files:

- `apps/web/src/components/CullingWorkspace.tsx`: 865 lines.
- `apps/api/app/api/routes.py`: 572 lines.
- `apps/api/app/services/processing.py`: 416 lines.
- `apps/api/tests/test_import_process_export_api.py`: 2182 lines.
- `tests/e2e/local-workflow.spec.ts`: 1336 lines.

These are not blockers by themselves, but they explain where future regressions are most likely.

## Recommended Next Iterations

1. Continue culling workspace maintainability
   - Extract remaining rendering/controller logic only where it creates testable behavior or reduces regression risk.
   - Suggested commit: `test: harden culling workspace state coverage`

2. Real-world/manual algorithm validation notes
   - Document outcomes from non-private local culling sets using `docs/v2_real_world_validation.md`, especially grouping misses and explanation mismatches.
   - Suggested commit: `docs: record algorithm validation notes`

3. Real browser-backend scale decision
   - Run or manually document a 2,000-photo real browser-backend import/process/review validation before reopening the worker decision.
   - Suggested commit: `docs: record real scale validation`

4. Current README wording
   - Clarify that the branch is a v2 local MVP-plus foundation, while historical v1 docs remain historical.
   - Suggested commit: `docs: clarify current v2 repository state`

5. Route/test organization
   - Split large route/test modules only after the next validation slices, preserving API behavior and tests.
   - Suggested commit: `refactor: split project job routes`

## Verdict

Continue automatic Codex iteration.

The branch is moving in the right direction: verification is green, stale-job recovery is stronger, import progress is visible, and seeded large-browser culling is measured. The next work should keep prioritizing validation, reliability, and maintainability over new feature surface. RAW, HEIC preview extraction, optional AI models, desktop packaging, accounts, cloud sync, and payment features should remain deferred.
