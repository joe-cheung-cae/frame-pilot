# FramePilot v2.0.0-rc2 Validation Decision

Decision date: 2026-06-05.

Release owner: Chao Zhang.

Status: waived.

This file is the release-owner decision record for the remaining rc2 algorithm-confidence gate.
For `v2.0.0-rc2`, the manual non-private real-world algorithm validation gate is explicitly
waived so the release can proceed as an engineering pre-release.

## Current Gate

Manual non-private real-world algorithm validation was not completed for rc2.

The release owner chose the waiver path described in:

- `docs/v2_real_world_validation.md`
- `docs/v2_release_candidate_checklist.md`
- `docs/v2_rc2_work_progress_summary.md`

This waiver does not claim that manual real-world grouping, ranking, explanation, or export
quality has been validated on a non-private release dataset. It records that rc2 can still be
tagged as an engineering pre-release after the automated hardening and verification work already
completed on the branch.

Do not use private photos, sensitive filenames, generated project directories, exports, ZIP files,
traces, SQLite databases, thumbnails, previews, or local cache files as tracked release evidence.

## Validation Evidence

Validation notes file: not applicable.

Validation tier: not completed.

Dataset privacy status: not applicable.

Summary metrics:

| Metric | Value |
| ------ | ----- |
| Total photo count | not completed |
| Group count | not completed |
| False merge count | not completed |
| Missed group count | not completed |
| Ranking mismatch count | not completed |
| Explanation mismatch count | not completed |
| Export issue count | not completed |

Validation verdict: not completed.

Release decision impact: v2.0.0-rc2 may be tagged as an engineering pre-release with the manual non-private real-world algorithm validation gate explicitly waived.

## Waiver Record

Waiver status: waived.

- Waiver owner: Chao Zhang
- Waiver date: 2026-06-05
- Reason: The release owner decided to publish v2.0.0-rc2 as an engineering pre-release after rc2 automated hardening, release artifact checks, backend/frontend tests, real browser smoke tests, and full E2E passed. Manual non-private real-world algorithm validation remains deferred.
- Accepted risk: v2.0.0-rc2 may still contain grouping, ranking, explanation, or heuristic face/eye-open quality issues on real-world photo sets that are not covered by deterministic fixtures, generated-image smoke tests, or synthetic benchmarks.
- Follow-up task: Complete Tier A or Tier B non-private real-world algorithm validation before v2.0.0 final. Add deterministic fixture tests before any threshold, grouping, ranking, scoring, or explanation tuning.

## Required Pre-Tag Confirmation

- `npm run verify` passes from the commit to be tagged.
- `npm run check:artifacts` passes from the commit to be tagged.
- `npm run check:pretag` passes from the commit to be tagged.
- `git status --short` contains only intentional release changes.
- No generated/private photos, project data, exports, ZIP files, traces, SQLite databases, cache folders, virtualenvs, or `node_modules` files are tracked.
- README and release docs do not claim RAW, HEIC, XMP, cloud workflows, durable jobs, or professional face/eye detection are implemented.
- The final release notes link this explicit waiver and clearly state that real-world/manual algorithm validation remains a known follow-up before `v2.0.0` final.
