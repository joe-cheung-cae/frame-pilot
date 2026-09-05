# FramePilot v2 Release Candidate Checklist

> Language: **English** | [中文](v2_release_candidate_checklist.zh.md)

This checklist is the release-candidate decision record for FramePilot v2.0. It summarizes what is implemented, what has been verified, what remains unverified, and what must be true before tagging a v2.0 release.

## Release Status Summary

FramePilot v2.0 is a local-first MVP-plus release candidate for JPEG, PNG, and WebP photo culling. The core workflow is implemented: local project creation, local import, queryable import and processing jobs, deterministic scoring, grouping, ranking, keyboard-first review, manual status/rating overrides, CSV export, ZIP export, folder export, and local export history.

Current RC decision: real-world/manual algorithm validation notes are recorded in `docs/v2_real_world_validation_notes.md` (2026-08-17, pass with notes). An unqualified `v2.0.0` tag still requires `npm run check:pretag` from the commit to be tagged.

This file remains the **v2.0 RC decision record** (verification run dated 2026-06-05). It is not the living next-slice pointer. After rc2, `main` also shipped:

- `2.1.0-desktop` unsigned Tauri sidecar RC (desktop packaging Phases 0–5)
- Phase 6 / 6.1 durable local job reclaim (`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` defaults on)
- Phase 7 cooperative processing job cancel (J7.01–J7.06)
- Unsigned Windows NSIS GUI lifecycle QA ([#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144), Windows-only)
- Phase 8 local HEIC/HEIF still preview (H8.01–H8.06)

**Next on `main`:** Phase 9 remaining-stretch close-out (S9.00–S9.13), one GitHub issue per run. S9.00–S9.05 are landed; start at S9.06. Do not invent Phase 10. Job durability, desktop packaging, processing cancel, and HEIC preview in the sections below describe the 2026-06-05 rc2 product unless a later-slice note says otherwise. See `develop_plan.md` §1.1 and `docs/plans/2026-09-04-remaining-stretch.md`.

## Implemented v2.0 Features

- Local project creation with managed or custom local project storage.
- JPEG, PNG, and WebP import.
- Unsupported-format reporting for deferred HEIC and RAW formats.
- Upload/register import phase followed by an in-process background derivative phase.
- Import job polling with progress, terminal states, retry, stale detection, and cooperative cancellation.
- Processing job polling with progress, active-import conflict rejection, stale detection, partial-group cleanup after stale failures, and idempotent reruns for unchanged projects.
- Local thumbnail and preview generation.
- Metadata extraction, deterministic scoring, perceptual hashes, and lightweight embeddings.
- Deterministic grouping using capture-time or filename candidate windows, metadata compatibility, perceptual hash distance, embedding fallback, union-find, and time-span splitting.
- Deterministic ranking with conservative recommendation explanations.
- Experimental local face and eye-open heuristic signals.
- Keyboard-first culling workspace with filters, groups, compare mode, zoom, statuses, and star ratings.
- Bounded photo, group, filmstrip, and compare rendering for larger projects.
- CSV, ZIP, and folder exports with export history, local path-safety checks, and ZIP/folder source containment under project `originals/`.
- Release-facing root, web, API package, lockfile root, and FastAPI OpenAPI metadata aligned to `2.0.0-rc2`.

## Verified Workflows

- `npm run verify` has been recorded as passing in the current rc2 working tree.
- Active-import, stale-processing cleanup, export source containment, and project routing regressions are covered by backend, frontend unit, and E2E tests.
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
| `git status --short` | passed | Intentional rc2 source, test, metadata, tooling, and documentation changes were present. |
| `npm run verify` | passed | 143 backend tests, 83 frontend unit tests, lint, typecheck, release script tests, and Next production build passed. |
| `npm run check:artifacts` | passed | No tracked generated or private release artifacts were found. This check is now included in `npm run verify`. |
| `npm run test:e2e` | passed | 44 Playwright tests passed during rc2 hardening, including active-import guards, the real local workflow, the default real browser-backend smoke, and the 2,000 seeded culling workspace smoke. |
| `npm run test:e2e -- tests/e2e/local-workflow.spec.ts -g "creates a project and opens the import step" --project=chromium` | passed | Targeted E2E confirmed the Node color and Next `allowedDevOrigins` warning cleanup. |
| `npm run test:e2e:real-browser` | passed | 100 generated JPEG real browser-backend workflow passed during rc2 hardening. |
| `npm run test:e2e:real-browser:large` | passed | 500 generated 3000x2000 JPEG real browser-backend workflow passed during rc2 hardening. |

Observed non-blocking warning: the FastAPI/TestClient Starlette deprecation warning remains visible. The Node `NO_COLOR`/`FORCE_COLOR` warning noise and the Next dev cross-origin warning for `/_next/*` resources were cleaned in the rc2 working tree.

## Required Test Commands

Run these before tagging v2.0:

```bash
git status --short
npm run check:pretag
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
```

`npm run check:pretag` includes `npm run verify`, the tracked artifact check, and the rc2 validation-decision gate. The 2026-08-17 decision closed that gate; `scripts/check-validation-decision.sh` is green on current main. `npm run verify` now includes `check:validation-decision`, so the default PR+main CI job fails if the decision file is reopened without completed evidence or an explicit waiver. Workflow YAML does not need a separate `check:pretag` job. `npm run check:pretag` remains the release-time command.

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
- Processing cannot start while the same project has an active import derivative job.
- ZIP and folder exports require selected source files to resolve inside the project `originals/` directory.
- Generated thumbnails, previews, caches, logs, exports, project databases, browser traces, generated photos, and test artifacts must not be committed.
- No cloud upload, login, payment, telemetry requirement, remote photo processing, or collaboration service is required for v2.0.
- No large model files are committed.
- HEIC, RAW, optional AI models, desktop packaging, and XMP sidecar writing are deferred in this **rc2** record. Desktop packaging later shipped as `2.1.0-desktop`. HEIC still preview later shipped as Phase 8. RAW, optional models, and XMP remain deferred.

## Job System Limitations

The following bullets are the **2026-06-05 rc2** job contract. On current `main`, leftover active import/processing jobs are reclaimed by default (Phase 6.1), and processing jobs are cooperatively cancellable (Phase 7). Export jobs stay uncancellable.

- FastAPI `BackgroundTasks` run in the local API process and are not durable across API process exits.
- Stale job detection marks interrupted queued or running jobs as failed after the configured stale window.
- Stale processing cleanup clears partial groups, removes photo group assignments, returns processed or in-progress photos to retryable imported state, and resets the project processed count to zero.
- Active import jobs route users back to import progress and make direct processing requests return `409 Conflict`.
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
- Real-world/manual algorithm validation notes from a non-private Openverse CC0/PDM photograph set are recorded in `docs/v2_real_world_validation_notes.md` (2026-08-17, pass with notes).
- `docs/v2_rc2_validation_decision.md` is the release-owner record for that evidence. The 2026-06-05 rc2 waiver is historical only.
- Any threshold, scoring, grouping, ranking, or explanation change requires focused tests.

## Deferred Features

Historical rc2 list. Later slices on `main` are noted in parentheses.

- HEIC support. (Phase 8, H8.01–H8.06; shipped)
- RAW and embedded RAW preview extraction.
- XMP sidecar export.
- Optional local AI models.
- Durable external or separate local worker process. (Phase 6 shipped a local SQLite-polled worker and in-process reclaim; not an external queue)
- Desktop packaging. (shipped as unsigned `2.1.0-desktop` RC)
- Cloud sync, accounts, payment, remote processing, and collaboration.
- Automatic deletion of original source photos.

## Release Blockers

- Required verification commands fail.
- Generated or private photos, project databases, exports, ZIP files, browser traces, or large artifacts are tracked by Git.
- Documentation claims RAW, HEIC, XMP, cloud workflows, durable jobs, or professional face/eye detection are implemented.
- Known limitations are not linked from README.
- Release owner cannot explain what is implemented, verified, unverified, deferred, and locally safe.
- Manual non-private real-world algorithm validation notes are absent and the release owner has not recorded replacement evidence or an explicit waiver.

## Pre-Tag Checklist

- Review `README.md`, `docs/architecture.md`, `docs/api.md`, `docs/scoring.md`, `docs/v2_performance_baseline.md`, `docs/v2_known_limitations.md`, and this checklist.
- Confirm `docs/v2_rc2_validation_decision.md` records completed validation evidence or an explicit release-owner waiver.
- Run `npm run check:pretag`.
- Confirm `npm run check:artifacts` passes, or rely on the same check through `npm run verify`.
- Run or explicitly skip full E2E with a documented reason.
- Confirm `git status --short` contains only intentional release changes.
- Confirm no generated images, private datasets, exports, ZIP files, traces, databases, cache folders, virtualenvs, or `node_modules` files are tracked.
- Record the final release decision and any skipped optional benchmarks.

## Post-Release Next Steps

- Optional: a license-clear photographer burst/session set, and a 2,000-photo real browser-backend run, before later milestones.
- Revisit durable local worker architecture with measured failure modes.
- Continue culling workspace maintainability only through focused, tested extractions.
- XMP sidecar export and RAW preview are Phase 9 issues S9.05 and S9.04 (`docs/plans/2026-09-04-remaining-stretch.md`). HEIC still preview shipped as Phase 8 (`docs/plans/2026-09-04-heic-preview.md`). Do not invent Phase 10.
