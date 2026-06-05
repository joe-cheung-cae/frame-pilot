#!/usr/bin/env python3
"""Generate privacy-safe local validation notes for FramePilot release review."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from pathlib import Path


SUPPORTED_SUFFIXES = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WebP",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate sanitized Tier A validation notes without copying or reading photos."
    )
    parser.add_argument("--photo-dir", required=True, help="Local input photo directory.")
    parser.add_argument("--output", required=True, help="Ignored local notes output path.")
    parser.add_argument("--tier", choices=["A"], required=True, help="Validation tier.")
    parser.add_argument("--max-photos", type=int, default=50, help="Maximum anonymized photos to list.")
    return parser.parse_args()


def supported_files(photo_dir: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in photo_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        ),
        key=lambda path: path.as_posix().lower(),
    )


def file_type_counts(files: list[Path]) -> Counter[str]:
    return Counter(SUPPORTED_SUFFIXES[path.suffix.lower()] for path in files)


def render_counts(counts: Counter[str]) -> str:
    rows = []
    for file_type in ("JPEG", "PNG", "WebP"):
        rows.append(f"| {file_type} | {counts.get(file_type, 0)} |")
    return "\n".join(rows)


def render_manifest(files: list[Path]) -> str:
    rows = []
    for index, path in enumerate(files, start=1):
        photo_id = f"photo_{index:04d}"
        rows.append(f"| {photo_id} | {SUPPORTED_SUFFIXES[path.suffix.lower()]} | pending manual review |")
    return "\n".join(rows)


def render_notes(tier: str, max_photos: int, files: list[Path], selected_files: list[Path]) -> str:
    counts = file_type_counts(files)
    manifest = render_manifest(selected_files)
    if not manifest:
        manifest = "| pending | no supported files found | pending manual review |"

    return f"""# FramePilot v2.0.0-rc2 Tier {tier} Sanitized Validation Notes

These notes were generated from a local input directory for release-owner review. The source path,
original filenames, EXIF metadata, project data, thumbnails, previews, exports, and photo bytes are
intentionally not recorded here.

## Dataset Summary

- Dataset name: anonymized local Tier {tier} dataset
- Reviewer: pending release owner review
- Date: {date.today().isoformat()}
- Privacy status: local private input; sanitized notes only
- Supported files found: {len(files)}
- Anonymized photo IDs listed: {len(selected_files)}
- Max photos requested: {max_photos}
- Camera/source: not recorded
- Validation tier: {tier}
- FramePilot commit hash: pending
- Local project data location, if safe to record: not recorded
- Time spent reviewing: pending

## Commands Run

```bash
git status --short
python scripts/run_tier_a_validation.py --photo-dir "[local input directory redacted]" --output ".local-validation-notes/rc2_tier_a_sanitized.md" --tier {tier} --max-photos {max_photos}
```

Additional commands:

```bash
# Release owner should record any FramePilot UI/API/export commands after manual review.
```

## File Type Counts

| File type | Count |
| --------- | ----- |
{render_counts(counts)}

## Anonymized Photo Manifest

| Photo ID | File type | Manual review notes |
| -------- | --------- | ------------------- |
{manifest}

## Manual Validation Checklist

The release owner must inspect actual FramePilot culling results before filling these fields.

| Category | Count | Notes |
| -------- | ----- | ----- |
| false merge | pending |  |
| missed group | pending |  |
| bad ranking | pending |  |
| misleading explanation | pending |  |
| export issue | pending |  |
| UI workflow issue | pending |  |

## Summary Verdict

- Verdict: pending release owner review
- One-paragraph summary: pending release owner review
- Release decision impact: pending release owner review
- Suggested follow-up: pending release owner review

## Dataset Coverage

Mark each category covered by this dataset after manual inspection.

| Category | Covered? | Notes |
| -------- | -------- | ----- |
| Burst sequences | pending |  |
| Near-duplicate travel photos | pending |  |
| Landscape scenes | pending |  |
| Portraits | pending |  |
| Indoor low light | pending |  |
| Underexposed images | pending |  |
| Overexposed images | pending |  |
| Intentionally blurred images | pending |  |
| Repeated composition with small subject changes | pending |  |
| Mixed orientation images | pending |  |
| Images with no faces | pending |  |
| Images with multiple faces, non-private only | pending |  |
| Similar unrelated scenes that should not merge | pending |  |
| Metadata-light images | pending |  |

## Metrics

Do not fill these fields until the release owner manually inspects actual FramePilot culling results.

| Metric | Value | Notes |
| ------ | ----- | ----- |
| Total photo count | pending |  |
| Group count | pending |  |
| Singleton group count | pending |  |
| Multi-photo group count | pending |  |
| False merge count | pending |  |
| Missed group count | pending |  |
| Ranking mismatch count | pending |  |
| Explanation mismatch count | pending |  |
| Face-signal mismatch count | pending |  |
| Export issue count | pending |  |
| UI workflow issue count | pending |  |

## Grouping Results

| Issue ID | Category | Group or photo IDs | Expected | Actual | Severity | Follow-up |
| -------- | -------- | ------------------ | -------- | ------ | -------- | --------- |
| RW-001 | false merge | pending | pending | pending | pending | pending |
| RW-002 | missed group | pending | pending | pending | pending | pending |

## Ranking Results

| Issue ID | Group ID | Manual choice | FramePilot choice | Score summary notes | Severity | Follow-up |
| -------- | -------- | ------------- | ----------------- | ------------------- | -------- | --------- |
| RW-003 | pending | pending | pending | pending | pending | pending |

## Explanation Results

| Issue ID | Photo or group ID | Expected explanation | Actual explanation | Severity | Follow-up |
| -------- | ----------------- | -------------------- | ------------------ | -------- | --------- |
| RW-004 | pending | pending | pending | pending | pending |

## Export Results

- Export mode checked: pending
- Statuses exported: pending
- Exported item count: pending
- Output inspected: pending
- Sensitive filenames present: pending
- Original source files unchanged: pending
- Export artifacts kept out of Git: pending

| Issue ID | Export mode | Expected | Actual | Severity | Follow-up |
| -------- | ----------- | -------- | ------ | -------- | --------- |
| RW-005 | pending | pending | pending | pending | pending |

## UI Workflow Results

| Issue ID | Workflow area | Expected | Actual | Severity | Follow-up |
| -------- | ------------- | -------- | ------ | -------- | --------- |
| RW-006 | UI workflow issue | pending | pending | pending | pending |

## Issue Log

Use categories from `docs/v2_real_world_validation.md`.

| Issue ID | Category | Photo or group IDs | Expected | Actual | Severity | Evidence | Suspected cause | Threshold concern? | Test required? | Follow-up |
| -------- | -------- | ------------------ | -------- | ------ | -------- | -------- | --------------- | ------------------ | -------------- | --------- |
| RW-001 | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending |

## Release Decision

- No critical data safety issue: pending
- No original file modification: pending
- No severe export corruption: pending
- No frequent false merges in Tier B, if applicable: not applicable for Tier {tier}
- Ranking mismatches acceptable with honest explanations and user override: pending
- Face/eye-open heuristic mismatches documented as experimental: pending
- Threshold or code changes required before release: pending
- Final release decision: pending

## Decision Impact

- Release decision impact: pending release owner review
- Required follow-up before tagging: pending release owner review
- Waiver needed: pending release owner review

## Follow-Up Tasks

| Priority | Task | Owner | Release blocking? |
| -------- | ---- | ----- | ----------------- |
| pending | pending | pending | pending |
"""


def main() -> int:
    args = parse_args()
    if args.max_photos < 1:
        raise SystemExit("--max-photos must be at least 1.")

    photo_dir = Path(args.photo_dir).expanduser().resolve()
    if not photo_dir.exists():
        raise SystemExit("Photo directory does not exist.")
    if not photo_dir.is_dir():
        raise SystemExit("Photo directory is not a directory.")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    files = supported_files(photo_dir)
    selected_files = files[: args.max_photos]
    output.write_text(
        render_notes(args.tier, args.max_photos, files, selected_files),
        encoding="utf-8",
    )

    print(f"Supported files found: {len(files)}")
    print(f"Anonymized photo IDs listed: {len(selected_files)}")
    print(f"Sanitized notes written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
