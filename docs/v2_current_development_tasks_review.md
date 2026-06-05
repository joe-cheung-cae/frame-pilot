# FramePilot v2 Current Development Tasks Review

Summary date: 2026-06-04

Review branch: `codex/v2-current-tasks-review`

Source baseline: `a1b4cca` (`main`, merged v2 performance iteration)

This document summarizes the current FramePilot v2 development tasks for review. It is a task-oriented review companion to `docs/v2_iteration_review.md` and `docs/v2_development_progress_summary.md`, not a new implementation plan and not a historical v1 review.

## Current Development State

FramePilot v2 is currently a local-first MVP-plus foundation for JPEG, PNG, and WebP photo culling. The repository includes job-based import and processing progress, stale job recovery, deterministic scoring/grouping/ranking, a keyboard-first culling workspace, CSV/ZIP/folder export, export history, local path safety, and opt-in large-batch validation coverage.

The project remains inside the v2 local-first constraints:

- No cloud upload, login, payment, telemetry, or remote photo processing requirement is present.
- Original source photos are not modified or deleted automatically.
- Generated thumbnails, previews, caches, metadata, and exports are written separately from source originals.
- No private photo datasets or large model files are tracked in the repository.
- Face and eye-open signals remain documented as experimental lightweight local heuristics, not professional face-detection results.

## Completed Development Task Groups

| task group                             | review status            | evidence                                                                                                                                                                                                                                                                    | remaining review concern                                                                     |
| -------------------------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| v2 foundation and documentation        | Mostly complete          | v2 product, architecture, migration, testing, algorithm, API, scoring, milestone, performance, and review docs exist                                                                                                                                                        | README and release-facing wording still need a final current-state pass                      |
| Import and processing progress         | Strong                   | import jobs expose stage/count progress, mixed-import outcomes, failed all-skipped jobs, same-file reuse, and polling-visible progress                                                                                                                                      | in-process jobs are accepted for v2.0 but are not durable across API process exits           |
| Stale job recovery                     | Strong                   | stale import and processing jobs are recovered through job polling/history and bounded failed counts                                                                                                                                                                        | separate worker remains deferred until real-scale evidence justifies it                      |
| Culling workspace                      | Mostly complete          | keyboard review, Pick/Maybe/Reject/Unreviewed status changes, star ratings, compare/zoom, filters, bounded large-list rendering, and tested helper modules are present                                                                                                      | `CullingWorkspace.tsx` remains large and should be reduced only where behavior can be tested |
| Export and interoperability            | Mostly complete          | CSV, ZIP, and folder exports, download endpoints, export history, empty-export rejection, and path safety tests are present                                                                                                                                                 | XMP sidecar export and queued exports remain planned rather than implemented                 |
| Deterministic algorithm quality        | Mostly complete for v2.0 | grouping uses capture-time and filename candidate windows, metadata compatibility, perceptual hash checks, embedding fallback, union-find, time-span splitting, conservative singleton recommendations, realistic in-memory fixture tests, and a manual validation protocol | needs completed non-private real-world/manual validation notes                               |
| Performance and reliability validation | Improved                 | API performance smoke, browser performance instrumentation, default 100-photo real browser-backend smoke, opt-in 500-photo large-image validation, opt-in 1,000-photo real browser-backend validation, and seeded 2,000-photo browser culling coverage are documented       | 2,000-photo real browser-backend import/process/review remains unattempted                   |
| Optional advanced support              | Deferred                 | HEIC, RAW, optional local AI models, desktop packaging, and XMP sidecars are documented as future work                                                                                                                                                                      | should stay deferred until the local JPEG/PNG/WebP workflow is stable at real scale          |

## Verification Evidence

Previously recorded verification from the current v2 review docs:

| command or check                                                       | recorded result                                                                   | review meaning                                                                                                                           |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `npm run verify`                                                       | passed                                                                            | API lint, web lint, TypeScript, backend tests, web unit tests, and Next production build passed                                          |
| `.venv/bin/pytest apps/api/tests`                                      | 123 passed, 1 warning                                                             | backend test suite covered API, import/process/export, grouping, ranking, scoring, status, and safety behavior                           |
| `npm --prefix apps/web run test:unit`                                  | 82 passed                                                                         | frontend helper coverage passed after culling state extractions                                                                          |
| deterministic culling fixture tests plus grouping/ranking/export tests | 28 passed                                                                         | missing-metadata grouping, lookalike non-merge protection, and technical-failure explanations passed                                     |
| seeded 2,000-photo culling E2E                                         | passed                                                                            | browser workspace handled bounded rendering and load-all behavior for seeded metadata records                                            |
| real browser-backend smoke                                             | documented at 100 default, 500 opt-in, and 1,000 opt-in generated-photo workloads | real backend, browser import, processing, asset serving, and CSV export are covered without private photos                               |
| tracked generated/private file check                                   | no matches recorded                                                               | no tracked generated folders, private photos, large datasets, archives, SQLite databases, virtualenv, or `node_modules` files were found |

Warnings currently treated as non-blocking:

- `StarletteDeprecationWarning` from the FastAPI/TestClient dependency stack.
- Node `NO_COLOR`/`FORCE_COLOR` warning noise in Playwright server output.
- Next dev cross-origin warning for `_next/*` resources.

## Remaining Development Tasks

| priority | task                                                                     | purpose                                                                                                   | suggested acceptance signal                                                                               |
| -------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| P1       | Record real-world/manual algorithm validation notes                      | Verify grouping, ranking, and explanations against non-private local photo sets or realistic review notes | completed validation notes record misses, false merges, ranking mismatches, and any threshold follow-up   |
| P1       | Run or document a 2,000-photo real browser-backend workflow              | Decide whether import/process/review scale is acceptable before reopening worker architecture             | measured import, process, first preview, status update, filter switch, export, memory, and failure counts |
| P1       | Keep durable worker decision evidence-based                              | Avoid adding worker complexity before measured local bottlenecks justify it                               | worker remains deferred or is reopened with benchmark evidence and concrete failure modes                 |
| P2       | Continue culling workspace maintainability work                          | Reduce regression risk in the largest frontend surface                                                    | extracted helper/controller logic has focused unit tests and unchanged E2E behavior                       |
| P2       | Clarify current v2 repository state in release-facing docs               | Prevent historical v1 and current v2 docs from being confused                                             | README and docs links clearly identify the current v2 MVP-plus state                                      |
| P2       | Improve route/test organization after behavior stabilizes                | Make backend API and workflow tests easier to review                                                      | route/test splits preserve existing API behavior and pass the same verification gates                     |
| P2       | Revisit export blocking only if scale validation shows user-visible cost | Keep export complexity proportional to measured workflow pain                                             | queued exports are added only after a large export case proves synchronous export is a problem            |
| P3       | Plan XMP sidecar export                                                  | Improve downstream editor interoperability                                                                | sidecar format, file-safety rules, and tests are specified before implementation                          |
| P3       | Keep HEIC, RAW, optional models, and desktop packaging deferred          | Protect the v2.0 local MVP-plus release from scope expansion                                              | unsupported formats still fail gracefully and no large models are committed                               |

## Recommended Next Review Order

1. Review this document together with `docs/v2_iteration_review.md` to confirm the current task inventory and risk order.
2. Run or manually document non-private real-world algorithm validation using `docs/v2_real_world_validation.md` before changing deterministic thresholds again.
3. Schedule a longer local validation window for 2,000-photo real browser-backend import/process/review, or explicitly defer that validation until import-stage bottlenecks are reduced.
4. Continue culling workspace maintainability only through testable helper/controller extraction, not broad UI rewrites.
5. Refresh release-facing documentation after the validation decision so the repository clearly presents the current v2 MVP-plus state.

## Review Verdict

The current repository is close to a v2.0 local MVP-plus release candidate, but it is not production-ready. The strongest completed work is local-first workflow coverage, job/progress visibility, deterministic algorithm hardening, path-safe exports, and bounded browser culling validation. The most important remaining work is real-world/manual algorithm validation, real browser-backend scale evidence, and controlled maintainability cleanup in the largest frontend and backend surfaces.

Future work should continue prioritizing validation, reliability, and reviewability over new product surface. Cloud services, accounts, payment, automatic deletion, large bundled models, full RAW decoding, and professional face-detection claims remain out of scope for this phase.
