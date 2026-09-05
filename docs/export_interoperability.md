# Export Interoperability

> Language: **English** | [中文](export_interoperability.zh.md)

FramePilot v2.0 supports CSV, ZIP, and folder exports. Optional XMP sidecar files can be written under the project export directory when `include_xmp` is enabled. Sidecars are never written next to camera originals, into `originals/`, or into image bytes.

## Current Modes

- `csv`: writes a local CSV artifact with selected photos, project photo ids, source identity fields (`original_path`, `project_copy_path`, `source_identity`, `content_hash`, size, and mtime), imported capture and camera metadata, ratings, statuses, scores, group metadata, dimensions, processing state/error fields, and recommendation explanations. `include_xmp` is stored on the export record; CSV writes no `.xmp` files because the CSV already includes `status` and `star_rating`.
- `zip`: writes a local ZIP containing selected original project copies, preserving duplicate filenames with deterministic suffixes. When `include_xmp` is true, matching `{exported_filename}.xmp` members are included (XML uses `ZIP_DEFLATED`; images stay `ZIP_STORED`).
- `folder`: copies selected original project copies into a local export folder and preserves duplicate filenames with deterministic suffixes. When `include_xmp` is true, `{exported_filename}.xmp` is written next to each copy.

All current exports are derived outputs under the project `exports/` directory. They do not modify original source files.
ZIP and folder exports require the selected local project copies to exist. If a selected copy is missing, the export is marked failed and partial output is removed when possible.

## XMP Sidecar Mapping

Sidecar packets are UTF-8 RDF/XML with `x:xmpmeta` / `rdf:RDF` / `rdf:Description`. `xmp:Rating` is the star rating clamped to `0`–`5` (Reject does **not** use `xmp:Rating = -1`). `xmp:Label` uses Adobe color-label strings so Pick/Maybe/Reject stay inspectable without clobbering stars. `dc:subject` repeats the FramePilot status. `dc:title` is the exported filename and `dc:identifier` is the project photo id.

| `user_status` | `xmp:Rating` | `xmp:Label` | `dc:subject` |
| -- | -- | -- | -- |
| Pick | stars 0–5 | Green | Pick |
| Maybe | stars 0–5 | Yellow | Maybe |
| Reject | stars 0–5 | Red | Reject |
| Unreviewed | stars 0–5 | omitted | Unreviewed |

Filenames append `.xmp` to the unique exported basename (`hero.jpg.xmp`, not `hero.xmp`) so JPEG+RAW pairs that share a stem do not collide. Lightroom Classic auto-sidecar discovery often looks for `{stem}.xmp`; this slice guarantees unambiguous pairing and a Lightroom-readable **field**, not auto-discovery. FramePilot has not tested a Lightroom or Capture One GUI round-trip and does not claim certification.

## Deferred

Writing sidecars next to original source files or embedding XMP packets in image bytes remains out of scope: it changes the file-safety model and needs explicit user consent. Import and review never write XMP.
