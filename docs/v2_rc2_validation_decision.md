# FramePilot v2.0 Validation Decision

> Language: **English** | [中文](v2_rc2_validation_decision.zh.md)

Decision date: 2026-08-17.

Release owner: Joe (joe-cheung-cae), with validation notes recorded by a Cursor cloud agent.

Status: completed.

This file is the release-owner decision record for the real-world algorithm-confidence gate.
A Tier B non-private photograph pass was completed on 2026-08-17 and supersedes the
2026-06-05 rc2 waiver for this gate.

## Current Gate

Manual non-private real-world algorithm validation is recorded in
`docs/v2_real_world_validation_notes.md`.

The protocol remains:

- `docs/v2_real_world_validation.md`
- `docs/v2_release_candidate_checklist.md`

Do not use private photos, sensitive filenames, generated project directories, exports, ZIP files,
traces, SQLite databases, thumbnails, previews, or local cache files as tracked release evidence.

## Validation Evidence

Validation notes file: docs/v2_real_world_validation_notes.md.

Validation tier: B.

Dataset privacy status: published CC0/PDM Openverse photographs with sanitized local aliases.

Summary metrics:

| Metric | Value |
| ------ | ----- |
| Total photo count | 138 |
| Group count | 137 |
| False merge count | 0 |
| Missed group count | 0 |
| Ranking mismatch count | 0 |
| Explanation mismatch count | 2 |
| Export issue count | 0 |

Validation verdict: pass with notes.

Release decision impact: The real-world algorithm gate now has completed Tier B evidence. Face/eye-open mismatches remain documented experimental limitations. Tag `v2.0.0` only after `npm run check:pretag` passes on the commit to be tagged. `npm run verify` includes `check:validation-decision`, so the default PR+main gate already runs this subset; GitHub Actions workflow YAML does not need a separate `check:pretag` job.

## Waiver Record

Waiver status: superseded by validation evidence.

Historical rc2 note (2026-06-05): Chao Zhang waived this gate so `v2.0.0-rc2` could ship as an engineering pre-release without real-world photograph notes. That waiver is retained only as history. The 2026-08-17 pass replaces it for v2.0 acceptance.

- Historical waiver owner: Chao Zhang
- Historical waiver date: 2026-06-05
- Reason: rc2 shipped as an engineering pre-release after automated hardening; real-world notes were deferred.
- Accepted risk at that time: grouping, ranking, explanation, or face/eye-open issues on real photo sets might be unseen.
- Follow-up task: completed by the 2026-08-17 Openverse CC0/PDM portrait-query pass recorded in `docs/v2_real_world_validation_notes.md`.

## Required Pre-Tag Confirmation

- `npm run verify` passes from the commit to be tagged. This includes `npm run check:validation-decision`.
- `npm run check:artifacts` passes from the commit to be tagged.
- `npm run check:pretag` passes from the commit to be tagged. This is the release-time command (`verify` plus the same validation-decision check).
- `git status --short` contains only intentional release changes.
- No generated/private photos, project data, exports, ZIP files, traces, SQLite databases, cache folders, virtualenvs, or `node_modules` files are tracked.
- README and release docs do not claim RAW, HEIC, XMP, cloud workflows, durable jobs, or professional face/eye detection are implemented.
- Release notes should link `docs/v2_real_world_validation_notes.md` and this decision file.
