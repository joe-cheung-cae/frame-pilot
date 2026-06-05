# FramePilot v2.0.0-rc2 Work Progress Summary

Date: 2026-06-05.

Branch: `codex/v2-next-iteration`.

Base commit before this rc2 work: `0415a87 docs: prepare real-world validation package`.

This document summarizes the rc2 blocker work, release hardening, verification evidence, and remaining release decision state for the current branch.

## Executive Summary

The current branch advances FramePilot v2.0.0 from the rc1 validation package toward a safer rc2 release candidate. The main rc2 code blocker from `docs/v2_rc1_full_code_review.md` has been addressed: FramePilot now prevents processing and culling from proceeding while an import derivative job is still active for the same project.

The work also hardens two adjacent release risks:

- Stale processing jobs can no longer leave partially committed groups visible as if processing completed.
- ZIP and folder exports now require selected source files to resolve inside the project `originals/` directory, so corrupted metadata cannot make file exports copy arbitrary local files.

Automated verification is green for the local MVP-plus scope. The remaining rc2 gate is not a code implementation issue: `docs/v2_rc2_validation_decision.md` is still pending and must be completed by a release owner with either non-private manual algorithm validation evidence or an explicit waiver.

## Commits Created

### `157eabb fix: harden rc2 workflow safety`

Purpose: close the rc2 workflow safety findings around active imports, stale processing cleanup, and export source containment.

Main files changed:

- `apps/api/app/api/routes.py`
- `apps/api/app/schemas/api.py`
- `apps/api/app/services/processing.py`
- `apps/api/app/services/exporting.py`
- `apps/api/tests/test_import_process_export_api.py`
- `apps/api/tests/test_ranking_export.py`
- `apps/web/src/components/ProcessingPanel.tsx`
- `apps/web/src/components/CullingWorkspace.tsx`
- `apps/web/src/components/ProjectDashboard.tsx`
- `apps/web/src/lib/projectRouting.ts`
- `apps/web/src/lib/projectRouting.test.ts`
- `tests/e2e/local-workflow.spec.ts`
- `docs/api.md`
- `docs/architecture.md`

Size:

- 15 files changed.
- 673 insertions.
- 69 deletions.

### `9b02f59 chore: prepare rc2 release gates`

Purpose: align release metadata and add automated release safety gates.

Main files changed:

- `package.json`
- `package-lock.json`
- `apps/web/package.json`
- `apps/web/package-lock.json`
- `apps/api/pyproject.toml`
- `apps/api/app/main.py`
- `apps/web/next.config.ts`
- `scripts/run-e2e.sh`
- `scripts/check-release-artifacts.sh`
- `scripts/check-validation-decision.sh`
- `scripts/test-release-checks.sh`

Size:

- 11 files changed.
- 300 insertions.
- 11 deletions.

### `9cf6f43 docs: record rc2 release readiness`

Purpose: record the rc2 release state, known limitations, review findings, verification status, and remaining validation decision gate.

Main files changed:

- `README.md`
- `docs/v2_known_limitations.md`
- `docs/v2_rc1_full_code_review.md`
- `docs/v2_rc2_validation_decision.md`
- `docs/v2_release_candidate_checklist.md`
- `docs/v2_release_review.md`

Size:

- 6 files changed.
- 602 insertions.
- 47 deletions.

### `7da3c0f docs: summarize rc2 work progress`

Purpose: add this work progress summary so the rc2 blocker work, release gates, verification evidence, and remaining release-owner decision state are easy to review from one document.

Main files changed:

- `docs/v2_rc2_work_progress_summary.md`

Latest workspace note:

- A privacy-safe Tier A validation preparation package is currently staged after this commit.
- The staged package adds the Tier A sanitized notes runner, local validation ignore rules, artifact-check coverage for local validation output directories, script-test coverage, and this summary update.
- The staged package does not include photos, generated project data, exports, ZIP files, SQLite databases, thumbnails, previews, browser traces, screenshots, test results, Playwright reports, `node_modules`, virtualenvs, the private source path, or original filenames.

## Backend Work

### Active Import Guard

The backend now exposes the newest current active import job in project responses through `active_import_job`. This field is included in both project detail and project list responses.

Implemented behavior:

- Active import jobs are defined as non-stale import jobs with status `queued` or `running`.
- Stale import jobs are marked failed before active-import workflow decisions are made.
- `POST /api/projects/{project_id}/process` now rejects direct processing while the same project has an active import job.
- The preferred response shape is implemented:

```json
{
  "detail": {
    "message": "Import is still running for this project. Wait for the import job to finish before processing.",
    "job_id": "import-job-id"
  }
}
```

Important semantics preserved:

- Completed import jobs allow processing.
- `complete_with_errors` import jobs allow processing.
- Failed import jobs allow processing.
- Cancelled import jobs allow processing.
- Stale queued or running import jobs are marked failed and then stop blocking processing.
- Existing active processing job behavior is preserved; processing still returns the active processing job instead of creating a duplicate.

### Stale Processing Cleanup

The stale processing failure path now cleans up partial processing state more thoroughly.

Implemented behavior:

- Partial `PhotoGroup` records for the project are deleted.
- Photo `group_id` values are cleared.
- Photos in `processing` or `processed` state are reset to retryable `imported`.
- Processing interruption text is stored in `processing_error`.
- AI recommendation state is reset to `Unreviewed`.
- Project `processed_images` is reset to zero.
- A later processing run can rebuild groups cleanly.

This prevents users from seeing stale partial groups or stale recommendations in the culling workspace after a processing interruption.

### Export Source Containment

ZIP and folder exports now validate selected source files more defensively.

Implemented behavior:

- Selected source paths are resolved with `strict=True`.
- Missing source files still report the missing path.
- ZIP and folder export sources must resolve inside the project `originals/` directory.
- Source paths outside project `originals/` fail with a path-free safety message:

```text
Export source file must stay inside the project originals directory
```

- Partial failed export artifacts are removed when possible.
- Failed export records remain visible in export history with the safety error.

CSV export behavior was intentionally left unchanged because CSV records metadata rather than copying source files.

## Frontend Work

### Project Routing

Project routing now uses the lightweight `active_import_job` field.

Implemented behavior:

- Active-import projects route to `/projects/{project_id}/import`.
- Recent project cards show `Import in progress`.
- Imported but unprocessed projects still route to processing when no import is active.
- Processed projects still route to culling when no import is active.

This avoids overfetching photo lists just to detect active imports.

### Project Dashboard

The dashboard now makes active import state visible before users enter processing or culling.

Implemented behavior:

- The dashboard shows a clear active import message:

```text
Import is still running. Finish import progress before processing or culling.
```

- Process and cull dashboard links are redirected to import progress while import is active.
- Normal dashboard links remain available when import reaches a terminal state.

### Processing Page

The processing page now detects active imports from project data or job history.

Implemented behavior:

- The run button is disabled while import is active.
- The page displays the active import current step and progress summary.
- The page links back to import progress.
- Normal processing, retry, and job history behavior remains intact after import completes.

### Culling Workspace

The culling workspace now avoids showing review UI based on incomplete derivative data.

Implemented behavior:

- Photo and group queries are disabled while import is active.
- The normal culling workspace is not rendered during active import.
- A clear `Import Still Running` state is shown.
- The state includes current import step and progress.
- Users can return to import progress.

## API And Schema Changes

`ProjectRead` now includes:

```text
active_import_job: JobRead | null
```

This is a small workflow-state addition to avoid large frontend overfetching.

The process endpoint now has one additional conflict condition:

- `409 Conflict` when import derivative work is still active for the same project.

Existing `422` behavior for projects with no imported photos remains unchanged.

## Release Metadata And Tooling

### Version Alignment

Visible release metadata is now aligned to `2.0.0-rc2` in:

- Root `package.json`.
- Root `package-lock.json`.
- Web `package.json`.
- Web `package-lock.json`.
- API `pyproject.toml`.
- FastAPI OpenAPI metadata in `apps/api/app/main.py`.

### E2E Warning Cleanup

The E2E runner now unsets `NO_COLOR` before launching Playwright. This removes the Node color warning noise that appeared during Playwright runs.

Next.js dev configuration now includes:

```ts
allowedDevOrigins: ["127.0.0.1"]
```

This removes the local E2E cross-origin warning for Next dev resources.

The FastAPI/TestClient Starlette deprecation warning remains visible and documented.

## Release Gates Added

### `npm run check:artifacts`

Added `scripts/check-release-artifacts.sh`.

Purpose:

- Fail if tracked files include generated or private release artifacts.
- Protect against accidentally committing photos, exports, project databases, browser traces, cache folders, `node_modules`, or virtualenv content.

This check is now included in `npm run verify`.

### `npm run check:validation-decision`

Added `scripts/check-validation-decision.sh`.

Purpose:

- Fail while `docs/v2_rc2_validation_decision.md` is still pending.
- Pass only when the decision record contains either completed validation evidence or an explicit release-owner waiver.

The script checks these validation-evidence fields:

- Validation notes file.
- Validation verdict.
- Release decision impact.
- The referenced validation notes file exists.

The script checks these waiver fields when waiver status is `waived`:

- Waiver owner.
- Waiver date.
- Reason.
- Accepted risk.
- Follow-up task.

### `npm run check:pretag`

Added as the release pre-tag gate:

```bash
npm run verify && npm run check:validation-decision
```

Expected current behavior:

- `npm run verify` passes.
- `npm run check:validation-decision` fails because the release decision is still pending.
- Therefore `npm run check:pretag` must fail until the release owner records validation evidence or a waiver.

### Release Script Tests

Added `scripts/test-release-checks.sh`.

Covered cases:

- Completed validation evidence closes the decision gate.
- Explicit waiver closes the decision gate.
- Pending status keeps the gate open.
- Missing validation notes file keeps the gate open.
- Incomplete waiver keeps the gate open.

These script tests are now part of `npm run test`.

### Privacy-Safe Tier A Validation Preparation

Added `scripts/run_tier_a_validation.py`.

Purpose:

- Prepare sanitized local Tier A validation notes from a release-owner-provided local photo directory.
- Keep FramePilot local-first and avoid copying or modifying any source photos.
- Avoid reading or dumping EXIF metadata.
- Avoid writing absolute input paths or original filenames into the generated notes.
- Generate anonymized photo IDs such as `photo_0001`.
- Record supported file type counts for JPEG, PNG, and WebP.
- Leave all algorithm and release verdict fields pending for manual release-owner review.

The runner accepts:

```bash
python scripts/run_tier_a_validation.py \
  --photo-dir "[local input directory redacted]" \
  --output ".local-validation-notes/rc2_tier_a_sanitized.md" \
  --tier A \
  --max-photos 50
```

The generated notes are intentionally local-only and ignored by Git.

Additional ignore and artifact protections were added for:

- `.local-validation/`
- `.local-validation-notes/`
- `.framepilot-validation/`

`scripts/check-release-artifacts.sh` now also fails if any of those local validation directories are tracked.

`scripts/test-release-checks.sh` now covers the Tier A runner and verifies that generated notes include anonymized IDs and file type counts while omitting the input path and original filenames.

## Documentation Updates

### README

README now documents:

- Active import processing guards.
- Project-originals containment for file exports.
- `npm run check:artifacts`.
- `npm run check:pretag`.
- The rc2 validation decision record.

### API Documentation

`docs/api.md` now documents:

- `active_import_job` in project responses.
- `409 Conflict` from processing during active import.
- Terminal import job states that allow processing.
- Stale processing cleanup behavior.
- ZIP/folder source containment under project `originals/`.

### Architecture Documentation

`docs/architecture.md` now documents:

- Active import routing and processing guards.
- Stale processing cleanup.
- ZIP/folder export source containment.
- Processing page active import behavior.
- Project card routing during active import.

### Known Limitations

`docs/v2_known_limitations.md` now clarifies:

- Jobs remain local in-process and non-durable.
- Processing is blocked during active import.
- Stale partial processing state is cleaned up.
- Real-world/manual algorithm validation is still open until the rc2 decision record is completed.
- ZIP/folder exports require source files to resolve inside project `originals/`.

### Release Review And Checklist

`docs/v2_release_candidate_checklist.md` and `docs/v2_release_review.md` now record:

- rc2 status.
- Verification commands and current results.
- Active-import, stale-processing, export containment, metadata, and tooling cleanup.
- Pre-tag command expectations.
- Remaining blocker: manual algorithm validation evidence or explicit waiver.

### RC1 Full Review

`docs/v2_rc1_full_code_review.md` records:

- RC1 review verdict.
- High-priority rc2 blockers.
- RC2 follow-up notes for fixed items.
- Risk register and suggested next tasks.

### RC2 Validation Decision

`docs/v2_rc2_validation_decision.md` records the remaining release-owner gate.

Current state:

- Decision date: pending.
- Release owner: pending.
- Status: pending.
- Waiver status: not waived.

## Verification Performed

The following commands were run during this work.

### Backend Targeted Tests

```bash
.venv/bin/pytest apps/api/tests/test_import_process_export_api.py -q
```

Result:

- Passed.
- 76 tests passed.
- 1 known Starlette/TestClient deprecation warning.

Coverage strengthened:

- Active import `queued` and `running` jobs reject processing with `409`.
- Terminal import jobs allow processing.
- Stale import jobs are marked failed and then stop blocking processing.
- Existing active processing jobs do not create duplicates.
- Stale processing cleanup clears partial groups and rebuilds cleanly.

### Frontend Unit Tests

```bash
npm --prefix apps/web run test:unit -- src/lib/projectRouting.test.ts
```

Result:

- Passed.
- The web unit runner executed the local `src/lib/*.test.ts` suite.
- 83 tests passed.

Project routing coverage includes:

- Empty projects route to import.
- Imported but unprocessed projects route to processing.
- Processed projects route to culling.
- Active-import projects route back to import progress.

### Release Script Tests

```bash
npm run test:scripts
```

Result:

- Passed.

Covered release decision gate pass and fail paths.
Also covered the privacy-safe Tier A validation runner.

### Privacy-Safe Tier A Notes Generation

```bash
python scripts/run_tier_a_validation.py \
  --photo-dir "[local input directory redacted]" \
  --output ".local-validation-notes/rc2_tier_a_sanitized.md" \
  --tier A \
  --max-photos 50
```

Result:

- Passed.
- 45 supported files found.
- 45 anonymized photo IDs listed.
- Sanitized local notes written to `.local-validation-notes/rc2_tier_a_sanitized.md`.

The generated local notes were inspected and verified to:

- Omit the private input path.
- Omit private path terms.
- Omit absolute paths.
- Omit original filenames.
- Omit EXIF dumps.
- Include anonymized photo IDs.
- Include file type counts.
- Include manual review placeholders for false merge, missed group, bad ranking, misleading explanation, export issue, and UI workflow issue.
- Keep the verdict and release decision impact pending.

Tracked-file scans also verified that the private input path terms and original filenames were not written into tracked files.

### Full Verify

```bash
npm run verify
```

Result:

- Passed.
- API lint passed.
- Web lint passed.
- TypeScript passed.
- 143 backend tests passed.
- 83 frontend unit tests passed.
- Release script tests passed.
- Next production build passed.
- Tracked artifact check passed.
- 1 known Starlette/TestClient warning remained.

### Targeted Active-Import E2E

```bash
npm run test:e2e -- tests/e2e/local-workflow.spec.ts -g "active import|import is active|culling not-ready" --project=chromium
```

Result:

- Passed.
- 4 Playwright tests passed.

Covered:

- Project list and dashboard route active-import projects back to import progress.
- Processing page disables grouping/ranking while import is active.
- Culling workspace shows not-ready/import-running state.
- Import page shows active import progress while upload is pending.

### Real Browser-Backend Smoke

```bash
npm run test:e2e:real-browser
```

Result:

- Passed.
- 1 Playwright test passed.
- Default generated photo count: 100.

This validates a real frontend/backend workflow with generated JPEGs.

### Full E2E

```bash
npm run test:e2e
```

Result:

- Passed on sequential rerun.
- 44 Playwright tests passed.

Important note:

- A first parallel attempt to run full E2E at the same time as `test:e2e:real-browser` failed because both runs tried to bind the local API server on port `8000`.
- The full suite passed when rerun sequentially.
- This was an environment/port collision, not an application test failure.

Full E2E coverage includes:

- Real local import/process/pick/CSV export smoke.
- Default real browser-backend generated JPEG smoke.
- Active import routing and processing guards.
- Import progress, cancel, retry, skipped-file UI, and failure states.
- Processing retry, polling, failed-item notices, and history loading.
- Culling workspace errors, filtering, keyboard-oriented review flow, and 2,000 seeded-photo browser validation.
- Export history, export status preferences, and folder export output path handling.

### Artifact Check

```bash
npm run check:artifacts
```

Result:

- Passed.
- No tracked generated or private release artifacts found.

### Validation Decision Check

```bash
npm run check:validation-decision
```

Result:

- Failed as expected.

Failure reason:

```text
docs/v2_rc2_validation_decision.md still has pending status.
```

This is the intended current state until a release owner records validation evidence or an explicit waiver.

### Whitespace Diff Check

```bash
git diff --check
```

Result:

- Passed.

### Generated Artifact Cleanup

Generated E2E directories were removed after browser test runs:

- `test-results`
- `apps/web/.next-e2e`
- `playwright-report`

Final inspection found no remaining generated E2E artifact directories.

## Current Git State After Commits

Recent commits:

```text
7da3c0f docs: summarize rc2 work progress
9cf6f43 docs: record rc2 release readiness
9b02f59 chore: prepare rc2 release gates
157eabb fix: harden rc2 workflow safety
0415a87 docs: prepare real-world validation package
```

The worktree was clean immediately after the three rc2 commits were created.

This document was added afterward to provide a detailed progress record.

Current staged changes after the latest summary commit:

- `.gitignore`
- `docs/v2_rc2_work_progress_summary.md`
- `scripts/check-release-artifacts.sh`
- `scripts/run_tier_a_validation.py`
- `scripts/test-release-checks.sh`

These staged changes represent the privacy-safe Tier A validation preparation package. They remain sanitized and keep the release decision pending.

## Requirements Coverage

### Local-First And Original File Safety

Status: preserved.

Evidence:

- No cloud upload, login, payment, remote processing, desktop packaging, RAW support, HEIC support, or bundled model work was added.
- Export source containment was strengthened for ZIP and folder export.
- Generated artifact checks were added and passed.
- E2E-generated output directories were cleaned after runs.

### Active Import Guard

Status: complete.

Evidence:

- Backend rejects direct processing during active import with `409`.
- Project list and dashboard route active imports to import progress.
- Processing page disables run and shows import progress.
- Culling workspace blocks normal review UI during active import.
- Backend, frontend unit, and E2E tests cover the behavior.

### Normal Workflow After Import Completion

Status: preserved.

Evidence:

- Terminal import job states allow processing.
- Full verify passed.
- Full E2E passed.
- Real browser-backend smoke passed.

### Stale Processing Cleanup

Status: complete.

Evidence:

- Tests verify stale processing jobs clear partial groups, reset group assignments, reset processed/in-progress photos, and allow clean rebuild.
- API and architecture docs were updated.

### Export Safety

Status: improved.

Evidence:

- ZIP and folder export source files must resolve inside project `originals/`.
- Tests cover outside-source rejection.
- Missing originals still report missing paths.
- Partial failed artifacts are removed.

### Release Metadata

Status: complete for rc2.

Evidence:

- Root, web, API, lockfile root entries, and FastAPI OpenAPI metadata expose `2.0.0-rc2`.

### Release Artifact Safety Gate

Status: complete.

Evidence:

- `npm run check:artifacts` exists.
- `npm run verify` includes it.
- Check passed.
- Local validation output directories are ignored and blocked from tracking by the artifact check.

### Privacy-Safe Tier A Validation Preparation

Status: prepared, manual review still pending.

Evidence:

- `scripts/run_tier_a_validation.py` exists.
- The runner generated sanitized local notes for 45 supported files.
- Generated notes were written to `.local-validation-notes/rc2_tier_a_sanitized.md`.
- The generated notes contain anonymized IDs and file type counts only.
- Privacy scans confirmed that the private input path, private path terms, absolute paths, original filenames, and EXIF dumps were not written into the generated local notes.
- Tracked-file scans confirmed that the private input path terms and original filenames were not written into tracked files.

### Validation Decision Gate

Status: automated but intentionally open.

Evidence:

- `npm run check:validation-decision` exists and is tested.
- `npm run check:pretag` includes it.
- The current decision file remains pending and not waived.

## Remaining RC2 Blocker

The only remaining rc2 blocker is the release-owner algorithm-confidence gate.

Local Tier A sanitized notes have been prepared in an ignored local path, but they do not close the gate by themselves. The release owner must manually inspect the actual FramePilot culling results, fill the pending metrics and verdict fields, and then choose one of these paths:

1. Record completed, sanitized Tier A or Tier B validation notes using `docs/templates/algorithm_validation_notes_template.md`.
2. Record an explicit waiver in `docs/v2_rc2_validation_decision.md`, accepting that rc2 ships without real-world/manual algorithm evidence beyond deterministic tests and generated-image smoke coverage.

Until that happens:

- `npm run check:validation-decision` must fail.
- `npm run check:pretag` must fail.
- The branch should not be tagged as an unqualified `v2.0.0-rc2`.

## Recommended Next Tasks

### 1. Complete RC2 Validation Decision

Recommended owner: release owner.

Scope:

- Fill `docs/v2_rc2_validation_decision.md`.
- Either link completed validation notes or record an explicit waiver.
- If using the prepared local Tier A notes, first complete all pending manual review fields in `.local-validation-notes/rc2_tier_a_sanitized.md`.
- Move a sanitized copy into a tracked docs path only after the release owner completes the manual review fields and confirms it contains no private paths, original filenames, generated artifacts, or sensitive metadata.
- Keep all private photos, generated project data, exports, ZIP files, traces, SQLite databases, thumbnails, previews, and cache files out of Git.

Suggested command after completion:

```bash
npm run check:pretag
```

### 2. Run Final Pre-Tag Checks From The Commit To Be Tagged

Suggested commands:

```bash
git status --short
git branch --show-current
git log --oneline --decorate -n 20
npm run check:pretag
npm run test:e2e:real-browser
npm run test:e2e:real-browser:large
npm run test:e2e
```

### 3. Tag RC2 Only After The Decision Gate Closes

Suggested tag:

```bash
git tag v2.0.0-rc2
```

Do not tag while `docs/v2_rc2_validation_decision.md` remains pending.

### 4. Plan Post-RC2 Work

Recommended follow-up areas:

- Durable local worker or restart-safe local queue.
- Real-world algorithm threshold tuning from recorded non-private validation notes.
- Optional XMP sidecar export.
- Optional 2,000-photo real browser-backend manual benchmark.
- Optional RAW/HEIC preview extraction after the v2.0 processing architecture remains stable.

## Final Current State

Automated rc2 hardening is in good shape:

- The original active-import rc2 blocker is fixed and tested.
- Stale processing cleanup is fixed and tested.
- Export source containment is strengthened and tested.
- Version metadata is aligned to rc2.
- Release artifact and validation-decision checks exist.
- Full verify and browser E2E are green.
- Generated artifacts were kept out of Git.

Release readiness is still conditional:

- The branch is ready for release-owner validation.
- Privacy-safe local Tier A notes have been prepared for 45 supported files, but the release owner verdict remains pending.
- It is not ready for an unqualified rc2 tag until the validation decision file records completed evidence or an explicit waiver.
