# FramePilot v2 Release Candidate Checklist

This checklist is the release-candidate decision record for FramePilot v2.0. It summarizes what is implemented, what has been verified, what remains unverified, and what must be true before tagging a v2.0 release.

## Release Status Summary

FramePilot v2.0 is a local-first MVP-plus release candidate for JPEG, PNG, and WebP photo culling. The core workflow is implemented: local project creation, local import, queryable import and processing jobs, deterministic scoring, grouping, ranking, keyboard-first review, manual status/rating overrides, CSV export, ZIP export, folder export, and local export history.

Current RC decision: close, but not ready to tag until this checklist is reviewed, required verification is current, known limitations are accepted, and real-world/manual algorithm validation notes are recorded or explicitly waived for the first RC.

## Implemented v2.0 Features

- Local project creation with managed or custom local project storage.
- JPEG, PNG, and WebP import.
- Unsupported-format reporting for deferred HEIC and RAW formats.
- Upload/register import phase followed by an in-process background derivative phase.
- Import job polling with progress, terminal states, retry, stale detection, and cooperative cancellation.
- Processing job polling with progress, stale detection, and idempotent reruns for unchanged projects.
- Local thumbnail and preview generation.
- Metadata extraction, deterministic scoring, perceptual hashes, and lightweight embeddings.
- Deterministic grouping using capture-time or filename candidate windows, metadata compatibility, perceptual hash distance, embedding fallback, union-find, and time-span splitting.
- Deterministic ranking with conservative recommendation explanations.
- Experimental local face and eye-open heuristic signals.
- Keyboard-first culling workspace with filters, groups, compare mode, zoom, statuses, and star ratings.
- Bounded photo, group, filmstrip, and compare rendering for larger projects.
- CSV, ZIP, and folder exports with export history and local path-safety checks.

## Verified Workflows

- `npm run verify` has been recorded as passing in the current v2 review docs.
- Default 100-photo generated real browser-backend workflow is verified.
- 500-photo generated large-image real browser-backend workflow is verified and stable across repeated runs.
- 1,000-photo generated real browser-backend workflow is verified for small generated JPEGs.
- 1,000-photo generated 3000x2000 real browser-backend workflow is verified as an opt-in slow validation.
- 2,000-photo seeded metadata culling workspace validation is verified.
- Deterministic grouping, ranking, scoring, export, retry, cancellation, stale-job, and status-update tests are recorded as passing.

## Current RC Verification Run

Run date: 2026-06-05.

| Command | Result | Notes |
| ------- | ------ | ----- |
| `git status --short` | passed | Only intentional documentation changes were present. |
| `npm run verify` | passed | 130 backend tests, 82 frontend unit tests, lint, typecheck, and Next production build passed. |
| `npm run test:e2e:real-browser` | passed | 100 generated JPEG real browser-backend workflow passed. |
| `npm run test:e2e:real-browser:large` | passed | 500 generated 3000x2000 JPEG real browser-backend workflow passed. |
| `npm run test:e2e` | passed | 41 Playwright tests passed, including the 2,000 seeded culling workspace smoke. |

Observed non-blocking warnings: the FastAPI/TestClient Starlette deprecation warning, Node `NO_COLOR`/`FORCE_COLOR` warning noise in Playwright server output, and the Next dev cross-origin warning for `_next/*` resources.

## Required Test Commands

Run these before tagging v2.0:

```bash
git status --short
npm run verify
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
```

Run full browser E2E when feasible, especially after frontend workflow changes:

```bash
npm run test:e2e
```

If full E2E is skipped because it is too slow or blocked by the local browser environment, record the reason in the release notes and run the relevant targeted E2E command instead.

## Optional Benchmark Commands

Use these for opt-in local scale validation:

```bash
npm run perf:api -- --output /tmp/framepilot-perf-targets --counts 100 500 2000
FRAMEPILOT_BROWSER_PERF_COUNT=1000 npm run test:e2e:real-browser
FRAMEPILOT_BROWSER_PERF_COUNT=1000 FRAMEPILOT_BROWSER_PERF_WIDTH=3000 FRAMEPILOT_BROWSER_PERF_HEIGHT=2000 FRAMEPILOT_BROWSER_PERF_QUALITY=88 npm run test:e2e:real-browser
```

Do not make the 2,000-photo real browser-backend workflow a v2.0 release gate unless it is manually run and documented during the release window.

## Safety And Privacy Checklist

- Original source photos are never modified.
- Original source photos are never automatically deleted.
- Imported photos are copied into local project storage before derivatives are generated.
- Generated thumbnails, previews, caches, logs, exports, project databases, browser traces, generated photos, and test artifacts must not be committed.
- No cloud upload, login, payment, telemetry requirement, remote photo processing, or collaboration service is required for v2.0.
- No large model files are committed.
- HEIC, RAW, optional AI models, desktop packaging, and XMP sidecar writing are deferred.

## Job System Limitations

- FastAPI `BackgroundTasks` run in the local API process and are not durable across API process exits.
- Stale job detection marks interrupted queued or running jobs as failed after the configured stale window.
- Import cancellation is cooperative, not a hard process kill.
- Cancellation stops at safe checkpoints, keeps completed derivatives, leaves remaining photos retryable, and does not delete originals.
- Import retry preserves Photo IDs, `user_status`, and `star_rating`.
- Retry reuses existing valid derivatives and regenerates missing derivatives from the local copied original when possible.

## Performance Validation Status

- 100, 500, and 1,000 generated real browser-backend validations pass.
- Repeated 500 large-image validation is stable.
- 2,000 seeded metadata culling validation passes.
- 2,000 real browser-backend import/process/review validation is not yet verified and is not a default release gate.
- Large imports remain compute-heavy, especially derivative generation and scoring, but the upload/register response is no longer blocked on all derivative work.
- Browser memory numbers are smoke signals only; they do not measure full process RSS, decoded image memory, GPU memory, or OS memory pressure.

## Algorithm Validation Status

- Deterministic tests cover burst grouping, missing metadata, non-merge lookalikes, blur/exposure penalties, conservative singleton recommendations, and explanations.
- Generated synthetic benchmarks do not prove real photographer-quality ranking.
- Real-world/manual algorithm validation still needs notes from non-private datasets unless the release owner explicitly waives that evidence for the first RC.
- Any threshold, scoring, grouping, ranking, or explanation change requires focused tests.

## Deferred Features

- HEIC support.
- RAW and embedded RAW preview extraction.
- XMP sidecar export.
- Optional local AI models.
- Durable external or separate local worker process.
- Desktop packaging.
- Cloud sync, accounts, payment, remote processing, and collaboration.
- Automatic deletion of original source photos.

## Release Blockers

- Required verification commands fail.
- Generated or private photos, project databases, exports, ZIP files, browser traces, or large artifacts are tracked by Git.
- Documentation claims RAW, HEIC, XMP, cloud workflows, durable jobs, or professional face/eye detection are implemented.
- Known limitations are not linked from README.
- Release owner cannot explain what is implemented, verified, unverified, deferred, and locally safe.

## Pre-Tag Checklist

- Review `README.md`, `docs/architecture.md`, `docs/api.md`, `docs/scoring.md`, `docs/v2_performance_baseline.md`, `docs/v2_known_limitations.md`, and this checklist.
- Run required verification commands.
- Run or explicitly skip full E2E with a documented reason.
- Confirm `git status --short` contains only intentional release changes.
- Confirm no generated images, private datasets, exports, ZIP files, traces, databases, cache folders, virtualenvs, or `node_modules` files are tracked.
- Record the final release decision and any skipped optional benchmarks.

## Post-Release Next Steps

- Record manual non-private real-world algorithm validation notes.
- Decide whether a 2,000-photo real browser-backend run is needed before the next milestone.
- Revisit durable local worker architecture with measured failure modes.
- Continue culling workspace maintainability only through focused, tested extractions.
- Plan XMP sidecar export and HEIC/RAW preview support as separate scoped milestones.
