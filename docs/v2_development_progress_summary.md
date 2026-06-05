# FramePilot v2 Development Progress Summary

Summary date: 2026-06-04

Branch: `feature/v2-performance-iteration`

This document summarizes the current FramePilot v2 development state at the requested stop point. It records the final completed iteration and the remaining gaps without opening a new work slice.

## Current State

FramePilot v2 is a local-first MVP-plus foundation for JPEG, PNG, and WebP photo culling. The branch currently includes job-based processing, import and processing progress visibility, stale job recovery, deterministic scoring/grouping/ranking, keyboard-first culling, CSV/ZIP/folder export, export history, local path safety, and opt-in large-batch validation coverage through generated 1,000-photo real browser-backend workflows.

The project remains within the local-first constraints:

- No cloud upload, login, payment, telemetry, or remote photo processing was introduced.
- Original source photos are not modified or deleted.
- No private photo datasets or large model files were added.
- New validation uses small deterministic in-memory fixtures.

## Final Iteration Completed

The final iteration expanded deterministic culling validation with realistic, non-private in-memory fixture families:

- Missing-metadata burst grouping: similar frames still group when one frame lacks capture time and another lacks lens metadata.
- Lookalike non-merge protection: visually similar but unrelated scenes remain separate when perceptual hashes disagree.
- Technical failure ranking explanations: blur and blown-highlight fixtures produce Reject recommendations with sharpness and exposure explanations.

One stale processing test fixture was also updated so its face-led recommendation case is a true similar-photo group after conservative singleton recommendations were introduced.

## Documentation Updated

Updated documentation now records:

- Deterministic fixture coverage in `docs/v2_algorithm_strategy.md`.
- The latest v2 iteration review status in `docs/v2_iteration_review.md`.
- Backend verification count updated to 123 passing tests.
- Remaining algorithm risk narrowed from missing fixture coverage to real-world/manual validation notes.
- A manual real-world validation protocol and notes template define how to record non-private grouping, ranking, and explanation findings.
- The performance baseline records opt-in 1,000-photo real browser-backend validation for default generated JPEGs and 3000x2000 generated JPEGs.

## Verification At Stop Point

Commands run successfully:

| command                                                                                                                                        | result                |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `.venv/bin/pytest apps/api/tests`                                                                                                              | 123 passed, 1 warning |
| `.venv/bin/pytest apps/api/tests/test_deterministic_culling_fixtures.py apps/api/tests/test_grouping.py apps/api/tests/test_ranking_export.py` | 28 passed             |
| `.venv/bin/pytest apps/api/tests/test_import_process_export_api.py::test_processing_recommendation_explains_face_and_eye_quality`              | 1 passed, 1 warning   |
| `npm run lint`                                                                                                                                 | passed                |
| `npm run typecheck`                                                                                                                            | passed                |
| `git diff --check`                                                                                                                             | passed                |

Observed warning:

- `StarletteDeprecationWarning` from the FastAPI/TestClient dependency stack.

## Remaining Gaps

These items remain intentionally unfinished at the stop point:

- Completed real-world/manual algorithm validation notes are still needed from non-private local photo sets.
- 2,000-photo real browser-backend import/process/review validation.
- Further `CullingWorkspace.tsx` maintainability extraction.
- XMP sidecar export and advanced interoperability.
- Separate worker process for durable long-running jobs, deferred until scale validation proves it is needed.
- HEIC, RAW, and optional local AI model support, all still deferred.

## Stop Decision

Per the latest instruction, development stops here after this final iteration even though the broader v2 goal is not fully complete. The repository is left with a focused deterministic validation slice, updated documentation, and passing relevant checks.
