# FramePilot v2 Real-World Algorithm Validation

## 1. Purpose

This document defines the release-blocking manual algorithm-confidence gate for FramePilot v2.0. Automated tests and generated-image benchmarks verify deterministic behavior, local workflow safety, and performance smoke coverage, but they do not prove that grouping, ranking, explanations, and exports behave well on real photographer-style photo sets.

Use this protocol before tagging an unqualified v2.0 release candidate. The product owner should validate non-private local photo sets, record observations with `docs/templates/algorithm_validation_notes_template.md`, and decide whether the release can proceed, needs more validation, or needs focused follow-up work.

This task is for validation evidence only. Do not change scoring, grouping, ranking, explanation rules, thresholds, supported formats, or product scope while collecting notes.

## 2. Privacy Rules

- Do not commit private photos.
- Do not commit generated project directories.
- Do not commit exports unless they contain no sensitive file names and the release owner explicitly wants them tracked.
- Do not commit generated thumbnails, previews, caches, SQLite databases, ZIP files, browser traces, or local benchmark output.
- Use non-private or disposable photo sets only, such as public-domain photos, purpose-shot test photos, or photos with no sensitive people, locations, filenames, or metadata.
- Validation notes may reference anonymized filenames, short IDs, local UI photo IDs, or reviewer-created aliases.
- If a dataset has unclear rights, private subjects, sensitive locations, or sensitive filenames, do not use it as release evidence.
- Never modify, delete, overwrite, or move original source photo files as part of validation.

## 3. Recommended Dataset Tiers

Tier A: 30-50 photos, quick sanity validation.

- Use for a first manual pass after automated gates are green.
- Include at least one burst or near-duplicate group and at least one technically weak image.
- Expected outcome: catch obvious false merges, missed groups, misleading explanations, or export problems before a larger review.

Tier B: 100-300 photos, release-candidate validation.

- Use as the primary v2.0 manual release gate.
- Include a realistic mix of scene types, lighting, orientations, metadata quality, and similar frames.
- Expected outcome: provide enough evidence to decide whether v2.0 can be tagged, needs more validation, or needs focused algorithm follow-up with tests.

Tier C: 500+ photos, stress/manual workflow validation.

- Use when the product owner wants extra confidence in long review sessions, large group lists, export behavior, or workflow ergonomics.
- This is useful release evidence, but it is not a replacement for careful Tier B algorithm review.
- Do not attempt a 2,000-photo real browser-backend benchmark for this documentation task unless it is separately scheduled and intentionally recorded.

Generated synthetic images are not real-world validation. They remain useful for repeatable automated regression and performance checks, but they do not satisfy this manual algorithm-confidence gate.

## 4. Recommended Photo Categories

Include as many of these categories as safely possible:

- Burst sequences.
- Near-duplicate travel photos.
- Landscape scenes.
- Portraits.
- Indoor low light.
- Underexposed images.
- Overexposed images.
- Intentionally blurred images.
- Repeated composition with small subject changes.
- Mixed orientation images.
- Images with no faces.
- Images with multiple faces if available and non-private.
- Visually similar but unrelated scenes that should not merge.
- Cropped, resized, or metadata-light images.
- Technically acceptable images where creative preference is ambiguous.

Do not force a category if it would require private subjects, sensitive locations, or unclear licensing.

## 5. Manual Review Workflow

1. Confirm the working tree is clean or contains only intentional documentation changes with `git status --short`.
2. Create a local FramePilot project for the validation dataset.
3. Import only non-private JPEG, PNG, or WebP photos.
4. Wait for the import job to reach a terminal state before judging thumbnails, previews, metadata, or scores.
5. Run processing if it does not start automatically for the workflow being tested.
6. Wait for processing job completion before judging groups, recommendations, and explanations.
7. Record total photo count and group count.
8. Review groups and record false merges, where unrelated or meaningfully separate scenes are placed in the same group.
9. Review nearby ungrouped or singleton photos and record missed groups, where similar frames should have been grouped.
10. Review each meaningful group and record ranking mismatches between the reviewer choice and the FramePilot representative or Pick recommendation.
11. Read recommendation explanations and record explanation mismatches where the explanation does not match the visible reason or score context.
12. Pay special attention to face and eye-open heuristic language. Record mismatches, but remember these signals are experimental.
13. Apply a few manual Pick, Maybe, Reject, Unreviewed, and star-rating updates to confirm user override still works.
14. Export CSV for at least one selected status set.
15. Inspect the CSV export output for expected rows, statuses, group information, recommendations, and sensitive filenames.
16. If ZIP or folder export is part of the validation pass, inspect the output count and confirm originals were not modified.
17. Record export issues separately from algorithm issues.
18. Avoid committing generated artifacts, private filenames, project folders, exports, ZIP files, databases, or photos.
19. Record a reviewer verdict and suggested follow-up in the notes template.

## 6. Metrics to Record

Record these fields for every dataset:

- Dataset name or anonymized dataset ID.
- Validation tier.
- Total photo count.
- Group count.
- False merge count.
- Missed group count.
- Ranking mismatch count.
- Explanation mismatch count.
- Export issues.
- Reviewer verdict.
- Suggested follow-up.

Optional but useful metrics:

- Number of singleton groups.
- Number of multi-photo groups.
- Number of photos marked Pick, Maybe, Reject, and Unreviewed after review.
- Number of face-signal mismatches.
- Number of UI workflow issues.
- Time spent reviewing.

## 7. Issue Categories

False merge:

- FramePilot places unrelated photos, different moments, or meaningfully separate compositions in one group.

Missed group:

- FramePilot leaves similar burst or near-duplicate photos separate when the reviewer expected one group.

Bad ranking:

- FramePilot recommends a weaker candidate inside a group when a clearly better technical candidate is available.

Misleading explanation:

- The explanation emphasizes the wrong visible issue, overstates confidence, or fails to mention the main reason for a recommendation.

Face-signal mismatch:

- Experimental face or eye-open signals appear to influence ranking or explanation incorrectly.

Exposure/contrast mismatch:

- Exposure or contrast scoring conflicts with the visible image quality in a repeated pattern.

Sharpness/blur mismatch:

- Sharpness or blur scoring conflicts with visible focus or motion blur in a repeated pattern.

Export mismatch:

- CSV, ZIP, or folder export contains wrong rows, wrong statuses, missing selected photos, corrupt output, unsafe paths, or confusing local output behavior.

UI workflow issue:

- The reviewer cannot efficiently inspect groups, apply overrides, navigate photos, understand progress, or confirm export results.

## 8. Release Decision Guidance

Suggested release gates:

- No critical data safety issue.
- No original file modification.
- No automatic deletion of source photos.
- No private or generated artifacts committed.
- No severe export corruption.
- No frequent false merges in Tier B validation.
- No misleading claims that face or eye-open heuristics are professional detection, identity recognition, biometric analysis, or reliable portrait judgment.
- Ranking mismatches are acceptable when explanations are honest, confidence is conservative, and user override works.
- Face and eye-open heuristic mismatches are acceptable only if documented as experimental limitations and not release-blocking for the validated workflow.
- Threshold or code changes require focused tests before release.

Suggested verdicts:

- Pass: validation supports tagging the release candidate with known limitations accepted.
- Pass with notes: validation supports tagging, but follow-up issues should be tracked after release.
- Needs more validation: evidence is too small, too synthetic, too private, or too ambiguous to decide.
- Blocked: a data safety issue, severe export issue, frequent false merge pattern, or misleading explanation pattern must be fixed before release.
- Waived: the release owner explicitly accepts shipping without this evidence and records the waiver in release notes.

Do not require FramePilot to match every subjective creative choice. The v2.0 goal is conservative, explainable assistance with human override, not fully automatic creative selection.

## 9. When to Tune Algorithms

Do not tune thresholds from a single anecdotal example.

Tune grouping, ranking, scoring, or explanation behavior only after repeated patterns are observed across non-private validation evidence or deterministic realistic fixtures. Before changing thresholds or logic:

- Confirm the expected behavior is clear enough to encode in a deterministic test.
- Add or update focused tests for the affected scoring, grouping, ranking, explanation, export, or status-update behavior.
- Check that the change does not increase false merges, overconfident Picks, misleading face/eye-open language, or export risk.
- Keep the implementation local-first and deterministic for v2.0.
- Update `docs/scoring.md` when scoring semantics, weights, confidence labels, or explanation meanings change.
- Update release review or known limitations docs when the change affects release risk.

If evidence is mixed, record the issue as a validation note, keep thresholds unchanged, and collect more non-private examples.
