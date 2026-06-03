# FramePilot v2 Testing Strategy

FramePilot v2 testing should prove the local photo workflow works end to end without making the default developer loop too slow. Fast deterministic tests should cover core behavior on every commit. Larger local workflows should remain explicit smoke or performance commands.

## Test Layers

### Backend Unit And Service Tests

Use `apps/api/tests` for deterministic backend behavior:

- scoring normalization and image-quality penalties
- perceptual hash and grouping decisions
- group ranking and recommendation explanations
- import validation, skipped files, duplicate filenames, and file safety
- processing job progress, retry, stale-job recovery, and failed item handling
- CSV, ZIP, folder export content and artifact safety
- SQLite compatibility migrations and query indexes

These tests should use temporary directories and generated images. They must not require private photo datasets, network access, cloud services, or large model files.

### Backend Integration Tests

Integration tests should exercise the local API workflow through `TestClient`:

- create project
- import JPEG, PNG, or WebP fixtures
- poll processing jobs to completion or failure
- list photos and groups in review order
- update user status and star ratings
- create CSV, ZIP, and folder exports
- download completed CSV and ZIP artifacts
- verify original source files are not modified

Unsupported HEIC and RAW files should be covered as skipped imports until preview extraction is implemented in a later v2.x slice.

### Frontend Unit Tests

Frontend unit tests should keep workspace state and large-list logic stable:

- project routing decisions
- review progress persistence parsing
- keyboard and group navigation helpers
- filmstrip, group sidebar, and compare-mode windowing
- export status summaries and download eligibility

Component-level tests should be added when UI behavior grows beyond pure helper logic, especially for import, processing progress, culling status updates, and export history.

### E2E Tests

Keep both E2E tiers:

- mocked E2E for fast UI regression
- real local smoke E2E with generated synthetic images for browser plus API workflow validation

Real smoke E2E must use generated local images only. It should cover project creation, import, processing progress, review status updates, export creation, and browser-downloadable artifacts where the test environment supports downloads reliably.

### Performance And Reliability Smokes

Large-batch validation should stay opt-in:

```bash
npm run perf:api -- --output /tmp/framepilot-perf-targets --counts 100 500 2000
```

The performance smoke should report generation, import, processing, export timings, failed item counts, group counts, and peak RSS. The initial target is reliability: no crash, bounded memory growth, visible progress, retryable failures, and intact original files.

## Required Checks Before Commits

Use the narrowest relevant checks while developing, then run the repository gate before committing a completed slice:

```bash
npm run verify
```

Run `npm run test:e2e` when frontend workflow changes affect project creation, import, processing, culling, or export flows.

## Test Data Rules

- Generate synthetic images with `npm run generate:synthetic`.
- Store temporary images under `/tmp` or pytest temp directories.
- Do not commit private photos, generated photo datasets, or large model files.
- Never write tests that modify or delete original source photo files.
