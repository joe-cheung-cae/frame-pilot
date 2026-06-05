# FramePilot v2.0 RC2 Release Review

Review date: 2026-06-05.

## 1. Release Verdict

Ready for manual product-owner validation only.

The automated release gate is green for the current local MVP-plus scope after rc2 hardening: `npm run verify`, targeted E2E for the final local tooling cleanup, the default real browser-backend smoke, the 500-photo large-image real browser-backend smoke, and full Playwright E2E have passed on this branch. The repository clearly documents the local-first model, JPEG/PNG/WebP support, deferred RAW/HEIC work, in-process job limitations, cooperative cancellation, retry behavior, synthetic benchmark caveats, and heuristic face/eye-open signals.

Do not tag an unqualified `v2.0.0-rc2` until the release owner either records manual validation notes from a non-private real-world photo set or explicitly waives that evidence for rc2 in `docs/v2_rc2_validation_decision.md`. This is an algorithm-confidence gate, not a request for new product features.

## 2. Current Branch and Git State

- Branch: `codex/v2-next-iteration`.
- Git status during this rc2 review: intentional rc2 source, test, metadata, tooling, and documentation changes are present.
- Current base commit: `0415a87` (`v2.0.0-rc1`, `main`, `origin/main`).
- Recent commits:
  - `0415a87 (HEAD -> codex/v2-next-iteration, tag: v2.0.0-rc1, origin/main, main) docs: prepare real-world validation package`
  - `4ff3332 docs: add v2 release review`
  - `6238a75 docs: add v2 release candidate checklist`
  - `f03cd49 v2: add cooperative import job cancellation`
  - `8ce1d11 v2: add stale import job retry flow`
  - `1e9425c (origin/main, origin/HEAD) docs: record import worker validation`
  - `170385a test: cover background import readiness`
  - `ade5d4c feat(web): poll import derivative jobs`
  - `00d18a5 feat(api): run import derivatives in background`
  - `a1b4cca (codex/v2-current-tasks-review) Merge pull request #1 from joe-cheung-cae/feature/v2-performance-iteration`
- Generated artifacts present in Git: none found by `git ls-files | rg "(node_modules|\\.venv|exports|cache|\\.zip$|\\.jpe?g$|\\.png$|\\.webp$|\\.arw$|\\.cr3$|\\.nef$|\\.dng$|\\.heic$|\\.sqlite$|\\.db$)"`.
- Expected working tree after this review: intentional rc2 code, test, metadata, tooling, and documentation changes only.

## 3. Implemented v2.0 Capabilities

- Local project workflow with managed or custom local project storage.
- JPEG, PNG, and WebP import with explicit unsupported-format messages for deferred HEIC and RAW files.
- Import split into upload/register and an in-process background derivative job.
- Progress polling for import and processing jobs.
- Stale import and processing job detection.
- Direct processing requests are blocked with `409 Conflict` while the same project has an active import derivative job.
- Project routing, processing UI, and culling UI send active-import projects back to import progress instead of showing incomplete processing or review state.
- Stale processing cleanup clears partial groups and resets processed or in-progress photos to retryable imported state.
- Cooperative import cancellation.
- Retry for failed, `complete_with_errors`, stale-failed, and cancelled import jobs.
- Retry preserves Photo IDs, `user_status`, and `star_rating` while reusing valid derivatives.
- Deterministic technical scoring, perceptual hashing, lightweight embeddings, grouping, ranking, and explanations.
- Keyboard-first culling workspace with filters, groups, compare, zoom, status updates, ratings, bounded rendering, and load-all controls.
- CSV, ZIP, and folder export with export history, local path-safety checks, and ZIP/folder source containment under project `originals/`.
- Root package, web package, API package, npm lockfile root entries, and FastAPI OpenAPI metadata aligned to `2.0.0-rc2`.
- Backend, frontend unit, browser E2E, real browser-backend, synthetic performance, and seeded large-culling coverage.

## 4. Verified Workflows

Commands run on 2026-06-05:

| Command | Result | Evidence |
| ------- | ------ | -------- |
| `git status --short` | passed | Intentional rc2 source, test, metadata, tooling, and documentation changes were present. |
| `git branch --show-current` | passed | `codex/v2-next-iteration`. |
| `git log --oneline --decorate -n 8` | passed | Current base commit is `0415a87 docs: prepare real-world validation package`. |
| `npm run verify` | passed | Ruff API lint, web ESLint, TypeScript, 143 backend tests, 83 frontend unit tests, release script tests, and Next production build passed. |
| `npm run check:artifacts` | passed | No tracked generated or private release artifacts were found. This check is now included in `npm run verify`. |
| `npm run test:e2e` | passed | 44 Playwright tests passed during rc2 hardening, including the real local workflow, default real browser-backend smoke, active-import guard coverage, import progress/cancel/retry UI coverage, and 2,000 seeded culling workspace smoke. |
| `npm run test:e2e -- tests/e2e/local-workflow.spec.ts -g "creates a project and opens the import step" --project=chromium` | passed | Targeted E2E passed after local tooling cleanup and showed no Node color or Next `allowedDevOrigins` warning noise. |
| `npm run test:e2e:real-browser` | passed | 1 Playwright test passed for 100 generated JPEGs through the real frontend/backend workflow during rc2 hardening. |
| `npm run test:e2e:real-browser:large` | passed | 1 Playwright test passed for 500 generated 3000x2000 JPEGs through the real frontend/backend workflow during rc2 hardening. |

Verification details:

- `npm run verify`: 143 backend tests passed with one known Starlette/TestClient deprecation warning; 83 frontend unit tests passed; release script tests passed; Next build completed successfully; tracked release artifact check passed.
- Full E2E during rc2 hardening: 44 tests passed. The seeded 2,000 culling smoke remained covered, and new active-import routing, processing, and culling guards were included.
- Real browser-backend smoke coverage during rc2 hardening included the default 100 generated JPEG workflow and the opt-in 500 generated 3000x2000 JPEG workflow.
- Detailed timing baselines remain in `docs/v2_performance_baseline.md`; generated-image timings are regression smoke evidence, not real-world algorithm validation.

Observed non-blocking warnings:

- FastAPI/TestClient `StarletteDeprecationWarning`.

The rc2 working tree cleaned the earlier Node `NO_COLOR`/`FORCE_COLOR` warning noise and the Next dev cross-origin warning for `/_next/*` resources.

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
- ZIP and folder exports now require selected source files to resolve inside the project `originals/` directory, so corrupted metadata cannot make file exports copy arbitrary local files.

## 7. Job System Review

- Import upload/register returns before expensive derivative work completes.
- Import derivative generation and processing jobs run through FastAPI `BackgroundTasks` in the local API process.
- Job progress is visible through polling and job history.
- Active import jobs block direct processing requests and route the project list, dashboard, processing page, and culling workspace back to import progress.
- Import cancellation is cooperative and stops at safe checkpoints. It is not a hard process kill.
- Stale queued or running jobs are detected and marked failed after the configured stale window.
- Stale processing failure now clears partial groups, removes photo group assignments, resets processed or in-progress photos to retryable imported state, and resets the project processed count to zero.
- Retry creates a new import job, preserves existing Photo IDs, `user_status`, and `star_rating`, reuses valid derivatives, and regenerates missing derivatives from the local copied original when possible.
- The current job system is not durable across API process exits. A future durable local worker or restart-safe job queue is the main post-v2.0 architecture recommendation.

## 8. Algorithm Review

- Scoring is deterministic and explainable, using local sharpness, blur risk, exposure, contrast, noise risk, simple aesthetic, and experimental face/eye-open heuristic signals.
- Grouping uses deterministic candidate windows, metadata compatibility, perceptual hash distance, lightweight embedding fallback, union-find, and time-span splitting.
- Ranking is conservative inside groups and stores group `score_summary` JSON with best score, score gap, confidence, recommendation counts, and explanation text.
- Face and eye-open signals are heuristic and experimental. They are not professional face detection, landmark detection, eye-state detection, identity recognition, or biometric analysis.
- Manual real-world validation remains incomplete for this release review. No threshold, scoring, grouping, ranking, or explanation changes are currently recommended from this evidence.
- `docs/v2_rc2_validation_decision.md` is present as the pending release-owner record for validation notes or an explicit waiver.

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
- `docs/v2_rc2_validation_decision.md` currently records this gate as pending and not waived.

Medium:

- FastAPI `BackgroundTasks` are in-process and not durable across API restarts.
- 2,000 real browser-backend workflow remains deferred/manual.
- Full browser RSS, decoded image memory, GPU memory, and OS-level pressure are not measured.

Low:

- Starlette/TestClient deprecation warning remains visible until the FastAPI/Starlette test client stack moves to `httpx2` or an equivalent supported client.

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

Recommended tag name after acceptance: `v2.0.0-rc2`.

Recommendation: do not tag immediately from automation alone. Tag after manual product-owner validation is completed or explicitly waived in release notes.

The release notes should link `docs/v2_rc2_validation_decision.md`, plus the completed validation notes file if validation is performed.

Exact pre-tag commands:

```bash
git status --short
git branch --show-current
git log --oneline --decorate -n 20
npm run check:pretag
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
npm run test:e2e
```

`npm run check:pretag` includes `npm run verify`, the tracked artifact check, and the validation-decision check. It must fail while `docs/v2_rc2_validation_decision.md` is still pending and not waived.

Optional manual benchmark, not a default release gate:

```bash
FRAMEPILOT_BROWSER_PERF_COUNT=2000 npm run test:e2e:real-browser
```

Exact post-tag next steps:

```bash
git tag v2.0.0-rc2
git status --short
```

Then record or link the manual validation notes, publish the RC decision, and open the first post-v2.0 iteration for durable jobs and real-world algorithm tuning.

## 13. Next Development Iterations

1. Durable local worker or restart-safe job queue.
2. Real-world algorithm threshold tuning from recorded non-private validation notes.
3. Optional XMP sidecar export.
4. Optional 2,000 real browser-backend manual benchmark.
5. Optional RAW/HEIC preview extraction after the v2.0 processing architecture is stable.
