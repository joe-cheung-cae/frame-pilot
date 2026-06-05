# FramePilot

FramePilot is a local-first AI-assisted photo culling web app. The current v2 local MVP-plus foundation keeps originals on the user's machine, generates local previews, computes explainable technical scores, groups similar frames, recommends the strongest image in each group, and lets the user override every decision.

## Current v2 Foundation

- Next.js, React, TypeScript, Tailwind CSS frontend.
- FastAPI, Pydantic, SQLModel, SQLite backend.
- Local project folders with originals, thumbnails, previews, structured export/cache subdirectories, and logs.
- JPEG, PNG, and WebP imports. HEIC and RAW files are skipped with explicit local messages until preview extraction is added in a later v2.x slice.
- Import jobs return after local upload/register work and continue derivative generation in a queryable, cooperatively cancellable local background task.
- Deterministic thumbnail and preview generation.
- Basic metadata extraction and explainable image quality scoring.
- Experimental local face and eye-open heuristic signals.
- Lightweight embedding approximation for near-duplicate grouping.
- Group-focused culling with recommendation-first review ordering.
- Pick, Maybe, Reject, and Unreviewed statuses.
- Keyboard review shortcuts: arrows, P, M, X, U, 1-5, 0, Space, Z, C, G, F, and E.
- CSV, folder, and ZIP export modes with unique local export outputs and export history.

Known v2.0 limitations:

- HEIC and RAW files are deferred and are skipped with explicit local messages.
- Import and processing jobs run in the local API process. Progress, cooperative import cancellation, stale-job detection, and safe import retry are available, but jobs are not durable across API process restarts.
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

Typical workflow:

1. Create a project.
2. Import JPEG, PNG, or WebP files. Valid files are registered locally, preview generation continues through a visible import job, and a running import can be cancelled at safe checkpoints without deleting originals or completed previews. Same-file reimports or import retries can reuse existing local records and generated previews.
3. Run processing to rebuild groups and recommendations.
4. Review photos by group and mark Pick, Maybe, Reject, or Unreviewed.
5. Export one or more selected statuses to CSV, folder, or ZIP. CSV and ZIP exports can be downloaded from the browser, and previous exports remain visible in export history.

## Verify

```bash
npm run verify
```

This runs API lint, web lint, TypeScript checks, backend tests, frontend unit tests, and a frontend production build.

For the shorter test-only path:

```bash
npm run test
```

Run browser E2E coverage separately:

```bash
npm run test:e2e
```

Run the real browser-backend validation smoke:

```bash
npm run test:e2e:real-browser
```

The default real browser-backend smoke uses 100 generated JPEGs so normal local validation stays practical. Larger runs are opt-in:

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
See [FramePilot v2 Architecture](docs/v2_architecture.md) for backend, frontend, storage, processing, and export boundaries.
See [FramePilot v2 Milestones](docs/v2_milestones.md) for release checkpoints and validation gates.
See [FramePilot v2 Testing Strategy](docs/v2_testing_strategy.md) for the expected unit, integration, E2E, and performance validation layers.
See [FramePilot v2 Performance Baseline](docs/v2_performance_baseline.md) for the latest recorded synthetic large-batch smoke result.
See [FramePilot v2 Release Candidate Checklist](docs/v2_release_candidate_checklist.md) for the current release-readiness checklist, required commands, release blockers, and pre-tag checks.
See [FramePilot v2 Release Review](docs/v2_release_review.md) for the current release verdict, verified workflows, blockers, and tagging recommendation.
See [FramePilot v2 Known Limitations](docs/v2_known_limitations.md) for accepted local MVP-plus limitations.
See [FramePilot v2 Real-World Algorithm Validation](docs/v2_real_world_validation.md) for the manual validation protocol for non-private photo sets.
See [FramePilot v2 Migration Plan](docs/v2_migration_plan.md) for schema, storage, API, and project data migration rules.
See [FramePilot v2 Algorithm Strategy](docs/v2_algorithm_strategy.md) for grouping, ranking, explanation, and optional model policy.
See [FramePilot v2 Iteration Review](docs/v2_iteration_review.md) for the latest repository status, verification notes, and remaining risks.

## Privacy

The v2 foundation does not upload originals or generated previews to any remote service. Imported images are copied into the local project directory so originals are never modified.

Experimental face and eye-open scores are computed locally with a deterministic color and luminance heuristic. They are local ranking hints, not a bundled professional face detection or biometric model.
