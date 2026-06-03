# FramePilot v2 Milestones

This document turns the v2 plan into practical development checkpoints. Each milestone should be implemented as small, reviewable commits with tests and documentation updated in the same slice.

## v2.0 Foundation

Goal: keep the repository maintainable and ready for structured v2 development.

Required outcomes:

- root scripts for setup, dev, lint, typecheck, test, E2E, and verify are documented
- v2 product, architecture, testing, algorithm, and migration docs exist or are linked from the README
- local-first and original-file safety rules are preserved
- existing v1 workflow still runs

Validation:

```bash
npm run verify
```

Run `npm run test:e2e` when browser workflow changes are included.

## v2.1 Processing And Progress

Goal: make processing job-based, visible, and retryable.

Required outcomes:

- processing creates a job record and returns quickly
- frontend polls job status
- progress exposes current step, total items, processed items, failed items, and percent
- failed items are recorded without crashing the full job
- stale or interrupted jobs can be retried
- rerunning unchanged projects avoids unnecessary regrouping

Validation:

- backend processing integration tests
- processing progress frontend tests
- `npm run verify`

## v2.2 Culling Workspace

Goal: make review efficient for real culling sessions.

Required outcomes:

- keyboard-first navigation for photos and groups
- Pick, Maybe, Reject, Unreviewed, and 0-5 star updates
- zoom and compare modes
- persistent review progress per project
- optimistic status and rating updates where safe
- bounded rendering for large filmstrip, group, and compare lists
- useful loading, empty, and error states

Validation:

- frontend unit tests for navigation and progress helpers
- mocked E2E culling workflow
- real local smoke E2E when workflow changes affect the browser/API flow
- `npm run verify`

## v2.3 Export And Interoperability

Goal: make local exports reliable for downstream editing workflows.

Required outcomes:

- CSV, ZIP, and folder exports write local artifacts
- empty export requests are rejected before writing artifacts
- failed exports are recorded and partial artifacts are removed where possible
- completed CSV and ZIP artifacts are downloadable
- folder exports clearly show local output paths
- export history shows mode, status, selected statuses, selected count, and output path
- XMP sidecar export remains planned and file-safe until implemented

Validation:

- export unit/API tests for content, file existence, status filters, downloads, and file safety
- frontend export selection tests
- E2E export workflow when UI changes are included
- `npm run verify`

## v2.4 Algorithm Quality

Goal: improve deterministic grouping, ranking, confidence, and explanations.

Required outcomes:

- perceptual hashes are stored for imported photos
- grouping uses candidate windows, metadata compatibility, hash distance, embedding fallback, and union-find
- oversized capture-time spans are split after grouping
- ranking uses deterministic baseline and context-aware weights
- group confidence summaries are persisted
- explanations name actual ranking reasons and mark face/eye signals as experimental

Validation:

- grouping tests for bursts, metadata mismatch, filename fallback, hash distance, and time-span splitting
- ranking tests for sharpness, exposure, noise, context weights, and explanation text
- `npm run verify`

## v2.5 Performance And Reliability

Goal: validate large local workflows without making the default test suite slow.

Required outcomes:

- synthetic dataset generator exists
- 100-photo workflow is covered by automated tests
- 500 and 2,000 photo workflows are documented or validated with opt-in smoke commands
- backend indexes support common large-project queries
- frontend avoids rendering thousands of images at once
- interrupted or repeated processing is recoverable

Validation:

```bash
npm run perf:api -- --output /tmp/framepilot-perf-targets --counts 100 500 2000
```

The smoke should report timings, failed item counts, group counts, exports, and peak memory.

## v2.6 Optional Advanced Support

Goal: prepare advanced formats and models only after the core workflow is stable.

Allowed later:

- HEIC preview support
- RAW embedded preview extraction
- optional local model registry
- optional local face, eye, embedding, or aesthetic models
- model source, license, size, and performance documentation

Release rules:

- no large model files committed
- no cloud processing requirement
- unsupported formats must continue to fail gracefully
- JPEG, PNG, and WebP baseline workflow must remain stable
