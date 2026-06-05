# FramePilot v2.0.0-rc2 Validation Decision

Decision date: pending.

Release owner: pending.

Status: **pending**.

This file is the release-owner decision record for the remaining rc2 algorithm-confidence gate. It must be completed before tagging an unqualified `v2.0.0-rc2`.

## Current Gate

Manual non-private real-world algorithm validation is not recorded yet, and no rc2 waiver is recorded yet.

Acceptable ways to close this gate:

1. Record Tier A or Tier B validation notes from non-private local JPEG, PNG, or WebP photo sets using `docs/templates/algorithm_validation_notes_template.md`.
2. Record an explicit release-owner waiver in this file, accepting that rc2 ships without real-world/manual algorithm evidence beyond deterministic tests and generated-image smoke coverage.

Do not use private photos, sensitive filenames, generated project directories, exports, ZIP files, traces, SQLite databases, thumbnails, previews, or local cache files as tracked release evidence.

## Validation Evidence

Validation notes file: pending.

Validation tier: pending.

Dataset privacy status: pending.

Summary metrics:

| Metric | Value |
| ------ | ----- |
| Total photo count | pending |
| Group count | pending |
| False merge count | pending |
| Missed group count | pending |
| Ranking mismatch count | pending |
| Explanation mismatch count | pending |
| Export issue count | pending |

Validation verdict: pending.

Release decision impact: pending.

## Waiver Record

Waiver status: not waived.

If waived, replace this section with:

- Waiver owner:
- Waiver date:
- Reason:
- Accepted risk:
- Follow-up task:

## Required Pre-Tag Confirmation

- `npm run verify` passes from the commit to be tagged.
- `npm run check:artifacts` passes from the commit to be tagged.
- `npm run check:pretag` passes from the commit to be tagged.
- `git status --short` contains only intentional release changes.
- No generated/private photos, project data, exports, ZIP files, traces, SQLite databases, cache folders, virtualenvs, or `node_modules` files are tracked.
- README and release docs do not claim RAW, HEIC, XMP, cloud workflows, durable jobs, or professional face/eye detection are implemented.
- The final release notes either link completed validation notes or link the explicit waiver above.
