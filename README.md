# FramePilot

> Language: **English** | [中文](README.zh.md)

FramePilot is a local-first AI-assisted photo culling web app. The current v2 local MVP-plus foundation keeps originals on the user's machine, generates local previews, computes explainable technical scores, groups similar frames, recommends the strongest image in each group, and lets the user override every decision.

## Current v2 Foundation

- Next.js, React, TypeScript, Tailwind CSS frontend.
- FastAPI, Pydantic, SQLModel, SQLite backend.
- Local project folders with originals, thumbnails, previews, structured export/cache subdirectories, and logs.
- JPEG, PNG, WebP, and HEIC/HEIF still imports. Originals are copied unchanged; thumbnails and previews are WebP; scoring and grouping run on decoded RGB via local `pillow-heif`. RAW files are still skipped with explicit local messages.
- Import jobs return after local upload/register work and continue derivative generation in a queryable, cooperatively cancellable local background task.
- Processing is blocked while import derivative work is still active, and project navigation routes users back to import progress until the import job reaches a terminal state.
- Processing (grouping and ranking) and export jobs are cooperatively cancellable on the same job cancel route. Desktop quit can cancel an active processing or export job, then SIGTERM the sidecar.
- Deterministic thumbnail and preview generation.
- Basic metadata extraction and explainable image quality scoring.
- Experimental local face and eye-open heuristic signals.
- Lightweight embedding approximation for near-duplicate grouping.
- Group-focused culling with recommendation-first review ordering.
- Pick, Maybe, Reject, and Unreviewed statuses.
- Keyboard review shortcuts: arrows, P, M, X, U, 1-5, 0, Space, Z, C, G, F, and E.
- CSV, folder, and ZIP export modes with unique local export outputs, export history, and project-originals source containment for file exports.

Known v2.0 limitations:

- RAW files such as DNG, ARW, CR3, and NEF are skipped with explicit local messages. HEIC/HEIF stills import locally; Live Photo `.mov` companions, AVIF, HDR gain-map tone mapping, and XMP writes are not implemented.
- Import and processing jobs run in the local API process or the optional local worker (`npm run worker`). Progress, cooperative import, processing, and export cancellation, stale-job detection, active-import processing guards, safe import retry, and stale-processing cleanup are available. By default leftover active import/processing jobs are marked `interrupted` on the next startup and reclaimed (`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` defaults on; set `0`/`false`/`no`/`off` for fail-and-retry). Export jobs are cancellable and are not reclaimed (fail-and-cleanup).
- Experimental face and eye-open signals are deterministic local heuristics, not professional face detection, eye-state detection, identity recognition, or biometric analysis.
- Grouping and ranking remain recommendation aids. The user keeps final control through manual statuses and star ratings.

## Setup

```bash
npm run install:all
```

## Run Locally

```bash
npm run dev
```

The web app runs at `http://localhost:3000`. The local API runs at `http://127.0.0.1:8000`.

Backend data is written to `.framepilot-data` by default. Set `FRAMEPILOT_DATA_DIR` to use another local project data location.

## Desktop app

Installable Windows (NSIS) and macOS (DMG) builds start the UI and a local API sidecar for you. Prefer the [Desktop User Guide](docs/desktop_user_guide.md) for install, data directory, path import (copies not moves), and export reveal. Contributor day-to-day work can stay on `npm run dev` (web + API above). Desktop shell development uses `npm run dev:desktop` (requires Rust); see [apps/desktop/README.md](apps/desktop/README.md).

Typical workflow:

1. Create a project.
2. Import JPEG, PNG, WebP, or HEIC/HEIF stills. Valid files are registered locally, preview generation continues through a visible import job, and a running import can be cancelled at safe checkpoints without deleting originals or completed previews. Same-file reimports or import retries can reuse existing local records and generated previews. RAW stays skipped.
3. Run processing after the import job completes. If import is still running, FramePilot keeps the project on import progress and rejects direct process requests.
4. Review photos by group and mark Pick, Maybe, Reject, or Unreviewed.
5. Export one or more selected statuses to CSV, folder, or ZIP. CSV and ZIP exports can be downloaded from the browser, and previous exports remain visible in export history.

## Verify

```bash
npm run verify
```

This runs API lint, web lint, TypeScript checks, backend tests, frontend unit tests, and a frontend production build.
It also runs `npm run check:artifacts` to fail if generated or private release artifacts are tracked by Git,
and `npm run check:validation-decision` so the default PR+main gate fails if the release-owner decision
in `docs/v2_rc2_validation_decision.md` is pending, waived without required fields, or missing its notes file.
That subset is green on current main; it does not need a separate GitHub Actions job.

GitHub Actions (`.github/workflows/verify.yml`) runs `npm run verify`, an independent Playwright job (`npm run test:e2e`: mocked E2E plus `tests/e2e/real-local-smoke.spec.ts`), an independent 100-photo real-browser job (`npm run test:e2e:real-browser`), a separate frozen-sidecar job (`npm run packaging:sidecar` then `npm run test:sidecar` so `GET /health` must pass without `PYTHONPATH`), and an independent desktop HTTP smoke (`npm run test:desktop:smoke`: `/health`, `/api/projects`, desktop Origin CORS, attacker `Host` → 403). Those jobs do not install Rust, sign, launch a packaged GUI, or run `test:e2e:real-browser:large`. Workflow YAML does not need a dedicated `check:pretag` job; `npm run verify` already includes the validation-decision check.

Before tagging a release candidate, run the pre-tag gate:

```bash
npm run check:pretag
```

This is the release-time command: `npm run verify` plus `npm run check:validation-decision` (the second half is already inside `verify`).

For the shorter test-only path:

```bash
npm run test
```

CI already runs browser E2E on pull requests and `main`. Run the same coverage locally when you change project creation, import, processing, culling, or export flows:

```bash
npm run test:e2e
```

CI also runs the 100-photo real browser-backend smoke on pull requests and `main`. Run the same command locally for that workflow:

```bash
npm run test:e2e:real-browser
```

The default real browser-backend smoke uses 100 generated JPEGs so normal local validation stays practical. Larger runs are opt-in and are **not** part of the default CI gate:

```bash
npm run test:e2e:real-browser:large
FRAMEPILOT_BROWSER_PERF_COUNT=1000 npm run test:e2e:real-browser
FRAMEPILOT_BROWSER_PERF_COUNT=1000 FRAMEPILOT_BROWSER_PERF_WIDTH=3000 FRAMEPILOT_BROWSER_PERF_HEIGHT=2000 FRAMEPILOT_BROWSER_PERF_QUALITY=88 npm run test:e2e:real-browser
```

These commands generate non-private local test images and project data under ignored test output directories. Do not commit generated photos, project databases, exports, ZIP files, browser traces, or private datasets.

Generate deterministic local image sets for performance validation:

```bash
npm run generate:synthetic -- --output /tmp/framepilot-500 --count 500
```

Generated files are local test fixtures and should not be committed.

Run a local synthetic import/process performance smoke:

```bash
npm run perf:api -- --output /tmp/framepilot-perf-500 --count 500
```

The smoke command reports generation, upload/register import time, import derivative completion time, processing time, and peak memory for the local process.
It also marks the synthetic photos as Pick and records CSV, ZIP, and folder export timings by default.

Run the v2.5 large-batch targets as an explicit local validation step:

```bash
npm run perf:api -- --output /tmp/framepilot-perf-targets --counts 100 500 2000
```

Each count writes generated sources, local metadata, and exports under a separate `count-*` subdirectory.

See [FramePilot v2 Product Requirements](docs/v2_product_requirements.md) for target users, scope, workflows, and release boundaries.
See [Architecture](docs/architecture.md) for current backend, frontend, storage, processing, desktop sidecar, and export boundaries.
See [FramePilot v2 Architecture](docs/v2_architecture.md) for the older v2.0-shaped architecture snapshot.
See [FramePilot v2 Milestones](docs/v2_milestones.md) for release checkpoints and validation gates.
See [FramePilot v2 Testing Strategy](docs/v2_testing_strategy.md) for the expected unit, integration, E2E, and performance validation layers.
See [FramePilot v2 Performance Baseline](docs/v2_performance_baseline.md) for the latest recorded synthetic large-batch smoke result.
See [FramePilot v2 Release Candidate Checklist](docs/v2_release_candidate_checklist.md) for the current release-readiness checklist, required commands, release blockers, and pre-tag checks.
See [FramePilot v2 Known Limitations](docs/v2_known_limitations.md) for accepted local MVP-plus limitations.
See [FramePilot v2 Real-World Algorithm Validation](docs/v2_real_world_validation.md) for the manual validation protocol for non-private photo sets.
See [FramePilot v2 Real-World Validation Notes](docs/v2_real_world_validation_notes.md) for the 2026-08-17 non-private Openverse photograph pass.
See [FramePilot v2 Validation Decision](docs/v2_rc2_validation_decision.md) for the current release-owner record of that evidence (the earlier rc2 waiver is historical only).
See [FramePilot v2 Migration Plan](docs/v2_migration_plan.md) for schema, storage, API, and project data migration rules.
See [FramePilot v2 Algorithm Strategy](docs/v2_algorithm_strategy.md) for grouping, ranking, explanation, and optional model policy.

## Desktop packaging

CI may upload **unsigned** Windows NSIS and macOS DMG installers for internal testing. Expect SmartScreen / Gatekeeper warnings; do not treat unsigned packages as public releases. See [Desktop Code Signing Runbook](docs/desktop_signing.md) and the [Desktop User Guide](docs/desktop_user_guide.md). Missing certificates must not block the first desktop RC. Manual checks: [Desktop Testing Matrix](docs/desktop_testing.md).

## Privacy

The v2 foundation does not upload originals or generated previews to any remote service. Imported images are copied into the local project directory so originals are never modified.

Experimental face and eye-open scores are computed locally with a deterministic color and luminance heuristic. They are local ranking hints, not a bundled professional face detection or biometric model.

## License

FramePilot is released under the [MIT License](LICENSE).
