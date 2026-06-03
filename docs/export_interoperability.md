# Export Interoperability

FramePilot v2.0 supports CSV, ZIP, and folder exports. XMP sidecar export is planned for a later v2.x slice after the deterministic processing, culling, and current export flows are stable.

## Current Modes

- `csv`: writes a local CSV artifact with selected photos, ratings, statuses, scores, group metadata, dimensions, and recommendation explanations.
- `zip`: writes a local ZIP containing selected original project copies, preserving duplicate filenames with deterministic suffixes.
- `folder`: copies selected original project copies into a local export folder and preserves duplicate filenames with deterministic suffixes.

All current exports are derived outputs under the project `exports/` directory. They do not modify original source files.

## Planned XMP Sidecar Scope

The first XMP sidecar implementation should be an explicit export mode, not an automatic write-back step. It should:

- Create sidecar files only inside a project export output directory by default.
- Keep original photos unchanged.
- Map FramePilot star ratings to XMP rating values `0` through `5`.
- Map FramePilot `Pick`, `Maybe`, `Reject`, and `Unreviewed` statuses to conservative labels or metadata fields that can be inspected by downstream tools.
- Include the source filename and project photo id in sidecar metadata where appropriate.
- Record an `ExportRecord` with mode, selected count, selected statuses, output path, and completion status.
- Add tests proving sidecar files are created separately from originals and that originals are not modified.

## Deferred Decisions

The exact Lightroom and Capture One metadata fields need validation before implementation. The first implementation should avoid claiming full compatibility until it has been tested against those applications. Writing sidecars next to original source files should remain deferred because it changes the file-safety model and needs explicit user consent.
