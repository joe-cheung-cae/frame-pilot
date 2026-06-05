# FramePilot v2 Real-World Algorithm Validation

This document defines the manual validation protocol for non-private photo sets. It is a release-readiness artifact for checking grouping, ranking, and explanations before changing deterministic thresholds or reopening larger architecture work.

## Purpose

FramePilot v2 uses deterministic local heuristics for JPEG, PNG, and WebP culling. Synthetic fixtures and generated browser benchmarks prove repeatable behavior, but they do not prove photographer-quality grouping and ranking on real scenes. Manual validation fills that gap without committing private photos or large datasets.

Use this protocol to record evidence from non-private, locally processed photo sets. Record observations in a separate notes file based on `docs/templates/algorithm_validation_notes_template.md`.

## Dataset Requirements

Use datasets that can be legally and safely reviewed locally:

- Use non-private photos only, such as public-domain images, personal test photos with no sensitive people or locations, or purpose-shot validation images.
- Prefer original-like camera JPEGs when possible, but downsampled public sets are acceptable if the source is recorded.
- Include at least one burst or near-duplicate sequence.
- Include at least one visually similar but unrelated scene that should not merge.
- Include at least one weak or technically flawed frame.
- Include at least one scene where ranking is ambiguous and manual judgment may differ from FramePilot.
- Keep the initial validation set small enough for careful review, usually 50 to 300 photos, before scaling up.

Do not treat generated synthetic images as real-world validation. They are useful for regression and performance checks, but they do not replace manual review.

## Privacy And File-Safety Rules

- Do not commit private photos, generated photo sets, exports, ZIP files, SQLite databases, browser traces, or local project data.
- Do not modify or delete original photo files during validation.
- Store generated thumbnails, previews, metadata, and exports only in local project data or ignored temporary directories.
- If a dataset has uncertain rights or privacy status, do not use it for release evidence.
- Record dataset names and sources, but avoid writing personally identifying details into repository documentation.

## Suggested Photo Categories

Cover a mix of these categories when possible:

- Burst sequences with small subject or camera movement.
- Travel and landscape scenes.
- Portrait-like frames where face and eye-open signals may influence ranking.
- Indoor low light and high-ISO scenes.
- Overexposed and underexposed frames.
- Near-duplicates with small composition, focus, exposure, or subject-expression differences.
- Intentionally blurred images, motion blur, and missed-focus frames.
- Similar compositions separated by time or location that should remain separate groups.
- Street, family-safe, event-like, and object-detail scenes.
- Cropped or resized images with missing camera metadata.
- Mixed orientation and mixed aspect-ratio sets.

## Manual Review Checklist

For each dataset:

1. Import the dataset into a local FramePilot project.
2. Run processing and wait for the job to complete.
3. Review the group list and record false merges.
4. Review nearby ungrouped photos and record missed groups.
5. Open each meaningful group and compare FramePilot's recommended Pick with a manual reviewer choice.
6. Check whether Maybe and Reject recommendations are conservative enough.
7. Read explanations for each mismatch and note whether the explanation matches the visible issue.
8. Apply a few Pick, Maybe, Reject, Unreviewed, and star-rating updates to confirm manual override workflow remains usable.
9. Export a small selected subset to CSV or ZIP and confirm validation artifacts stay outside Git.
10. Decide whether observations justify code changes, documentation changes, more data, or no action.

## Issue Fields

Record each issue with these fields:

- Issue ID.
- Dataset name.
- Photo IDs or filenames, using non-sensitive names only.
- Category: false merge, missed group, bad ranking, bad explanation, performance, UI review issue, or other.
- Expected behavior.
- Actual behavior.
- Severity: blocker, high, medium, low, or note.
- Evidence: short manual observation, not a private image.
- Suspected cause, such as capture-time gap, filename gap, perceptual hash distance, embedding fallback, score weighting, face heuristic, or explanation rule.
- Recommended follow-up.
- Whether a threshold or source-code change is justified.
- Test requirement before any source-code change.

## Issue Log Template

Use this table shape in validation notes, expanding rows as needed:

| Issue ID | Dataset | Category | Photo IDs or filenames | Expected | Actual | Severity | Evidence | Suspected cause | Follow-up | Threshold concern? | Test required? |
| -------- | ------- | -------- | ---------------------- | -------- | ------ | -------- | -------- | --------------- | --------- | ------------------ | -------------- |
| RW-001   |         | false merge |                        |          |        |          |          |                 |           |                    | yes            |
| RW-002   |         | missed group |                        |          |        |          |          |                 |           |                    | yes            |
| RW-003   |         | bad ranking |                        |          |        |          |          |                 |           |                    | yes            |
| RW-004   |         | bad explanation |                    |          |        |          |          |                 |           |                    | yes            |
| RW-005   |         | threshold concern |                 |          |        |          |          |                 |           |                    | yes            |

## Example Issue Types

False merge:

- Expected: two similar skyline photos from different times should remain in separate groups.
- Actual: FramePilot places them in one group because filename proximity and visual similarity are high.
- Follow-up: check capture-time span, metadata compatibility, and perceptual hash distance before considering any threshold change.

Missed group:

- Expected: three burst frames of the same subject should appear in one group.
- Actual: one frame remains a singleton because capture time is missing and filename sequence is outside the current filename gap.
- Follow-up: confirm whether the filename sequence rule or metadata fallback should change, then add a deterministic grouping test before changing thresholds.

Bad ranking:

- Expected: the sharper frame with better exposure should be recommended as Pick.
- Actual: a slightly blurrier frame wins because experimental face quality dominates the final score.
- Follow-up: record the score summary and add a focused ranking fixture before changing weights.

Bad explanation:

- Expected: a rejected frame with motion blur should mention weaker sharpness or blur risk.
- Actual: the explanation emphasizes exposure even though exposure is acceptable.
- Follow-up: add an explanation test that covers the visible reason mismatch.

## Threshold-Change Policy

Do not change grouping, ranking, scoring, or explanation thresholds from a single anecdote. A threshold change is justified only when all of these are true:

- The issue appears in a non-private validation set or in a realistic deterministic fixture.
- The expected behavior is clear enough to encode in a test.
- The change does not increase false merges, overconfident Picks, or misleading face/eye-open claims.
- The change keeps FramePilot local-first and deterministic.
- Backend or frontend tests are added or updated before the behavior change is accepted.
- Documentation is updated when user-facing behavior or release risk changes.

If evidence is mixed, record the issue as a validation note and keep thresholds unchanged.

## Current Release Decision

As of 2026-06-04, this repository has deterministic fixture coverage and generated browser-backend validation, but still needs recorded notes from a curated non-private real-world photo set before treating v2 as a stronger release candidate. This is a release-readiness blocker for algorithm confidence, not a reason to add AI models, RAW support, HEIC support, cloud processing, or broad refactors.
