# FramePilot v2.0 Release Review

Review date: 2026-06-05.

## 1. Release Verdict

Ready for manual product-owner validation only.

The automated release gate is green for the current local MVP-plus scope: `npm run verify`, the default real browser-backend smoke, the 500-photo large-image real browser-backend smoke, and full Playwright E2E all passed on this branch. The repository clearly documents the local-first model, JPEG/PNG/WebP support, deferred RAW/HEIC work, in-process job limitations, cooperative cancellation, retry behavior, synthetic benchmark caveats, and heuristic face/eye-open signals.

Do not tag `v2.0.0-rc1` until the release owner either records manual validation notes from a non-private real-world photo set or explicitly waives that evidence for the first RC. This is an algorithm-confidence gate, not a request for new product features.

## 2. Current Branch and Git State

- Branch: `main`.
- Git status before review commands: clean.
- Git status after verification commands and before this document: clean.
- Recent commits:
  - `6238a75 (HEAD -> main) docs: add v2 release candidate checklist`
  - `f03cd49 v2: add cooperative import job cancellation`
  - `8ce1d11 v2: add stale import job retry flow`
  - `1e9425c (origin/main, origin/HEAD) docs: record import worker validation`
  - `170385a test: cover background import readiness`
  - `ade5d4c feat(web): poll import derivative jobs`
  - `00d18a5 feat(api): run import derivatives in background`
  - `a1b4cca (codex/v2-current-tasks-review) Merge pull request #1 from joe-cheung-cae/feature/v2-performance-iteration`
- Generated artifacts present in Git: none found by `git ls-files | rg "(node_modules|\\.venv|exports|cache|\\.zip$|\\.jpe?g$|\\.png$|\\.webp$|\\.arw$|\\.cr3$|\\.nef$|\\.dng$|\\.heic$|\\.sqlite$|\\.db$)"`.
- Expected working tree after this review: one intentional documentation file, `docs/v2_release_review.md`.

## 3. Implemented v2.0 Capabilities

- Local project workflow with managed or custom local project storage.
- JPEG, PNG, and WebP import with explicit unsupported-format messages for deferred HEIC and RAW files.
- Import split into upload/register and an in-process background derivative job.
- Progress polling for import and processing jobs.
- Stale import and processing job detection.
- Cooperative import cancellation.
- Retry for failed, `complete_with_errors`, stale-failed, and cancelled import jobs.
- Retry preserves Photo IDs, `user_status`, and `star_rating` while reusing valid derivatives.
- Deterministic technical scoring, perceptual hashing, lightweight embeddings, grouping, ranking, and explanations.
- Keyboard-first culling workspace with filters, groups, compare, zoom, status updates, ratings, bounded rendering, and load-all controls.
- CSV, ZIP, and folder export with export history and local path-safety checks.
- Backend, frontend unit, browser E2E, real browser-backend, synthetic performance, and seeded large-culling coverage.

## 4. Verified Workflows

Commands run on 2026-06-05:

| Command | Result | Evidence |
| ------- | ------ | -------- |
| `git status --short` | passed | Clean before verification and clean after verification. |
| `git branch --show-current` | passed | `main`. |
| `git log --oneline --decorate -n 20` | passed | Latest commit was `6238a75 docs: add v2 release candidate checklist`. |
| `npm run verify` | passed | Ruff API lint, web ESLint, TypeScript, 130 backend tests, 82 frontend unit tests, and Next production build passed. |
| `npm run test:e2e:real-browser` | passed | 1 Playwright test passed for 100 generated JPEGs through the real frontend/backend workflow. |
| `npm run test:e2e:real-browser:large` | passed | 1 Playwright test passed for 500 generated 3000x2000 JPEGs through the real frontend/backend workflow. |
| `npm run test:e2e` | passed | 41 Playwright tests passed, including the real local workflow, default real browser-backend smoke, import progress/cancel/retry UI coverage, and 2,000 seeded culling workspace smoke. |

Current run details:

- `npm run verify`: 130 backend tests passed with one known Starlette/TestClient deprecation warning; 82 frontend unit tests passed; Next build completed successfully.
- Default real browser-backend smoke: 100 generated 160x120 JPEGs, import ready `1736 ms`, process `2109 ms`, first preview `836 ms`, status update `54 ms`, filter switch `80 ms`, group navigation `32 ms`, export `55 ms`.
- Large real browser-backend smoke: 500 generated 3000x2000 JPEGs, image generation `8455 ms`, upload/register response `2297 ms`, import ready `100238 ms`, process `2605 ms`, first preview `834 ms`, status update `77 ms`, filter switch `49 ms`, group navigation `23 ms`, export `41 ms`. Import endpoint timing reported upload/register work at `1.966 s`.
- Full E2E: 41 tests passed in `27.5 s`. The seeded 2,000 culling smoke reported first preview `377 ms`, status update `86 ms`, filter switch `58 ms`, load-all `248 ms`, initial DOM nodes `941`, loaded DOM nodes `915`, and reported JS heap `54.17 MB`.

Observed non-blocking warnings:

- FastAPI/TestClient `StarletteDeprecationWarning`.
- Node `NO_COLOR`/`FORCE_COLOR` warning noise in Playwright server output.
- Next dev cross-origin warning for `_next/*` resources.

## 5. Performance Release Baseline

- 100 real browser-backend: passed in the current run and in the recorded baseline.
- 500 real browser-backend: recorded baseline passes for generated images.
- 500 large-image repeated validation: recorded baseline passes 3 of 3 runs with stable import timing.
- 1000 real browser-backend: recorded baseline passes for generated small images and opt-in 3000x2000 generated JPEGs.
- 2000 seeded culling validation: full E2E current run passed the seeded 2,000-photo browser culling smoke.
- 2000 real browser-backend: deferred/manual. It was not run for this review and should not be treated as a default v2.0 release gate.

Synthetic benchmark caveat: generated JPEGs are useful for repeatability and regression checks, but they are not curated real-world validation and do not prove photographer-quality grouping/ranking.

## 6. Safety and Privacy Review

- Original source photos are copied into local project storage and are not modified after import.
- Original source photos are never automatically deleted.
- Generated thumbnails, previews, caches, logs, exports, databases, browser traces, generated photos, ZIP files, `node_modules`, and virtualenvs must stay out of Git.
- No generated or private artifacts were found in tracked files during this review.
- No cloud upload, remote processing, user account, login, payment, telemetry requirement, or online collaboration dependency is required.
- The app assumes local SQLite project metadata and single-user local operation.
- Asset and export serving/writing paths are documented as project-root checked, with path-safety coverage in tests.

## 7. Job System Review

- Import upload/register returns before expensive derivative work completes.
- Import derivative generation and processing jobs run through FastAPI `BackgroundTasks` in the local API process.
- Job progress is visible through polling and job history.
- Import cancellation is cooperative and stops at safe checkpoints. It is not a hard process kill.
- Stale queued or running jobs are detected and marked failed after the configured stale window.
- Retry creates a new import job, preserves existing Photo IDs, `user_status`, and `star_rating`, reuses valid derivatives, and regenerates missing derivatives from the local copied original when possible.
- The current job system is not durable across API process exits. A future durable local worker or restart-safe job queue is the main post-v2.0 architecture recommendation.

## 8. Algorithm Review

- Scoring is deterministic and explainable, using local sharpness, blur risk, exposure, contrast, noise risk, simple aesthetic, and experimental face/eye-open heuristic signals.
- Grouping uses deterministic candidate windows, metadata compatibility, perceptual hash distance, lightweight embedding fallback, union-find, and time-span splitting.
- Ranking is conservative inside groups and stores group `score_summary` JSON with best score, score gap, confidence, recommendation counts, and explanation text.
- Face and eye-open signals are heuristic and experimental. They are not professional face detection, landmark detection, eye-state detection, identity recognition, or biometric analysis.
- Manual real-world validation remains incomplete for this release review. No threshold, scoring, grouping, ranking, or explanation changes are currently recommended from this evidence.

## 9. Known Limitations

- RAW and HEIC support are deferred.
- AI models and large bundled model files are deferred.
- Desktop packaging is deferred.
- XMP sidecar export is deferred.
- 2,000 real browser-backend import/process/review is unverified.
- Real camera JPEG diversity is not yet validated with recorded non-private manual notes.
- Full browser process RSS, decoded image memory, GPU memory, and OS memory pressure are unverified.
- Import and processing jobs are in-process and not durable across API process exits.
- Generated and synthetic benchmarks do not replace real-world/manual algorithm validation.
- CSV, ZIP, and folder exports are local synchronous operations.

## 10. Release Blockers

Critical:

- None found in automated verification during this review.

High:

- Manual non-private real-world algorithm validation notes are not recorded yet. This blocks an unqualified RC tag unless the release owner explicitly waives it.

Medium:

- FastAPI `BackgroundTasks` are in-process and not durable across API restarts.
- 2,000 real browser-backend workflow remains deferred/manual.
- Full browser RSS, decoded image memory, GPU memory, and OS-level pressure are not measured.

Low:

- Starlette/TestClient deprecation warning.
- Node `NO_COLOR`/`FORCE_COLOR` warning noise in Playwright server output.
- Next dev cross-origin warning for `_next/*` resources.

## 11. Manual Validation Checklist

- Run non-private real-world photo validation, ideally 50 to 300 photos first.
- Inspect grouping false merges.
- Inspect missed groups.
- Inspect ranking mismatches against a human reviewer choice.
- Inspect bad or misleading explanations.
- Confirm CSV, ZIP, and folder export outputs with non-private data.
- Confirm retry and cancel behavior manually in the UI.
- Confirm README commands on a clean local setup.
- Keep all photos, generated project data, exports, ZIP files, traces, and SQLite databases out of Git.

## 12. Tagging Recommendation

Recommended tag name after acceptance: `v2.0.0-rc1`.

Recommendation: do not tag immediately from automation alone. Tag after manual product-owner validation is completed or explicitly waived in release notes.

Exact pre-tag commands:

```bash
git status --short
git branch --show-current
git log --oneline --decorate -n 20
npm run verify
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
npm run test:e2e
```

Optional manual benchmark, not a default release gate:

```bash
FRAMEPILOT_BROWSER_PERF_COUNT=2000 npm run test:e2e:real-browser
```

Exact post-tag next steps:

```bash
git tag v2.0.0-rc1
git status --short
```

Then record or link the manual validation notes, publish the RC decision, and open the first post-v2.0 iteration for durable jobs and real-world algorithm tuning.

## 13. Next Development Iterations

1. Durable local worker or restart-safe job queue.
2. Real-world algorithm threshold tuning from recorded non-private validation notes.
3. Optional XMP sidecar export.
4. Optional 2,000 real browser-backend manual benchmark.
5. Optional RAW/HEIC preview extraction after the v2.0 processing architecture is stable.
