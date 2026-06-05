# Algorithm Validation Notes Template

Use this template for non-private FramePilot v2 real-world algorithm validation. Do not paste private filenames, private paths, sensitive metadata, or generated project artifacts into this file.

## Dataset Summary

- Dataset name:
- Reviewer:
- Date:
- Privacy status:
- Photo count:
- Camera/source:
- Validation tier:
- FramePilot commit hash:
- Local project data location, if safe to record:
- Time spent reviewing:

## Commands Run

```bash
git status --short
npm run verify
```

Additional commands:

```bash

```

## Summary Verdict

- Verdict: pass / pass with notes / needs more validation / blocked / waived
- One-paragraph summary:
- Release decision impact:
- Suggested follow-up:

## Dataset Coverage

Mark each category covered by this dataset.

| Category | Covered? | Notes |
| -------- | -------- | ----- |
| Burst sequences |  |  |
| Near-duplicate travel photos |  |  |
| Landscape scenes |  |  |
| Portraits |  |  |
| Indoor low light |  |  |
| Underexposed images |  |  |
| Overexposed images |  |  |
| Intentionally blurred images |  |  |
| Repeated composition with small subject changes |  |  |
| Mixed orientation images |  |  |
| Images with no faces |  |  |
| Images with multiple faces, non-private only |  |  |
| Similar unrelated scenes that should not merge |  |  |
| Metadata-light images |  |  |

## Metrics

| Metric | Value | Notes |
| ------ | ----- | ----- |
| Total photo count |  |  |
| Group count |  |  |
| Singleton group count |  |  |
| Multi-photo group count |  |  |
| False merge count |  |  |
| Missed group count |  |  |
| Ranking mismatch count |  |  |
| Explanation mismatch count |  |  |
| Face-signal mismatch count |  |  |
| Export issue count |  |  |
| UI workflow issue count |  |  |

## Grouping Results

| Issue ID | Category | Group or photo IDs | Expected | Actual | Severity | Follow-up |
| -------- | -------- | ------------------ | -------- | ------ | -------- | --------- |
| RW-001 | false merge |  |  |  |  |  |
| RW-002 | missed group |  |  |  |  |  |

## Ranking Results

| Issue ID | Group ID | Manual choice | FramePilot choice | Score summary notes | Severity | Follow-up |
| -------- | -------- | ------------- | ----------------- | ------------------- | -------- | --------- |
| RW-003 |  |  |  |  |  |  |

## Explanation Results

| Issue ID | Photo or group ID | Expected explanation | Actual explanation | Severity | Follow-up |
| -------- | ----------------- | -------------------- | ------------------ | -------- | --------- |
| RW-004 |  |  |  |  |  |

## Export Results

- Export mode checked: CSV / ZIP / folder
- Statuses exported:
- Exported item count:
- Output inspected: yes/no
- Sensitive filenames present: yes/no
- Original source files unchanged: yes/no
- Export artifacts kept out of Git: yes/no

| Issue ID | Export mode | Expected | Actual | Severity | Follow-up |
| -------- | ----------- | -------- | ------ | -------- | --------- |
| RW-005 |  |  |  |  |  |

## Issue Log

Use categories from `docs/v2_real_world_validation.md`.

| Issue ID | Category | Photo or group IDs | Expected | Actual | Severity | Evidence | Suspected cause | Threshold concern? | Test required? | Follow-up |
| -------- | -------- | ------------------ | -------- | ------ | -------- | -------- | --------------- | ------------------ | -------------- | --------- |
| RW-001 |  |  |  |  |  |  |  |  | yes/no |  |

## Release Decision

- No critical data safety issue: yes/no
- No original file modification: yes/no
- No severe export corruption: yes/no
- No frequent false merges in Tier B, if applicable: yes/no/not applicable
- Ranking mismatches acceptable with honest explanations and user override: yes/no/not applicable
- Face/eye-open heuristic mismatches documented as experimental: yes/no/not applicable
- Threshold or code changes required before release: yes/no
- Final release decision:

## Follow-Up Tasks

| Priority | Task | Owner | Release blocking? |
| -------- | ---- | ----- | ----------------- |
|  |  |  |  |
