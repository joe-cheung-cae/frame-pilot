# Desktop Phase 2 code review findings

- **Mode**: branch
- **Target**: `feature/desktop-phase2` vs `origin/main`
- **Merge-base**: `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- **Head**: `6105fbdaffeec6d214086cc763e6ac742ddea564`
- **PR**: [joe-cheung-cae/frame-pilot#38](https://github.com/joe-cheung-cae/frame-pilot/pull/38) (reviewed in branch mode; no GitHub review posted)
- **Diff stats**: 55 files changed, 5231 insertions(+), 261 deletions(-)
- **Issue counts**: 1 bug, 1 suggestion, 0 nits
- **Reviewed at**: 2026-08-21T09:13:24+08:00
- **Reviewer subagent**: `01a021d2-9688-7d51-a43b-ed750a6a3b0c`

This is an implementation review of committed Phase 2 work (D2.00–D2.09). It is not the requirements review in `docs/handoff/phase2-review.md`. Findings were not posted to GitHub.

## Summary

Desktop Phase 2 (D2.00–D2.09) is a coherent native-FS and path-import slice: registered roots are file-backed (not Settings), desktop routes 404 unless `FRAMEPILOT_DESKTOP=1`, Tauri stays on dialog + opener with no `fs:`/`shell:`, originals are copied not mutated, nonempty-root ack uses the locked English confirm copy, and browser file inputs / download hrefs remain when the desktop shell is off. Path hardening (NUL, trailing separators, `os.pathsep` allowlist, blocked system/data-dir roots) and the >100-file `remaining_paths` loop look correct.

The dominant defect is the default desktop folder import. `importPhotosFromPaths` treats a directory as a non-final slice, then re-POSTs that same folder with `finalize: true`. The from-paths API expands and `register_import_file`s again; in-progress photos are not treated as duplicates until derivatives exist. A 2-JPEG folder becomes 4 project copies (`hero.jpg` + `hero-1.jpg`, …). That is the “Choose a folder” / drop-a-folder path.

## Issues

### Issue 1 -- Severity: bug
- File: apps/web/src/lib/api.ts:428
- Description: `isLastPathImportSlice` (`api.ts:171`) returns false for a directory (it does not look like `.jpg`/`.png`/`.webp`), so the first from-paths request is sent with `finalize: false`. When the folder has ≤100 images, the API returns `remaining_paths: []` after registering every file without starting derivatives. The client then calls `importPhotosFromPathsBatch` again with the **original folder path** and `finalize: true` (`api.ts:426-432`). `POST /imports/from-paths` always re-expands `payload.paths` (`routes.py:585-591`) and `register_import_file` only short-circuits when a same-hash photo already has derivatives (`importing.py:751-754`). Before finalize, those photos are still `processing` with no thumbnails, so the second request copies each source again as `name-1.jpg` and inserts extra Photo rows. Live TestClient check: folder with `hero.jpg` + `alt.jpg` ended at `total_images == 4` and originals `hero.jpg`, `hero-1.jpg`, `alt.jpg`, `alt-1.jpg`. This is what `ImportPanel.onPickFolder` (`ImportPanel.tsx:237`) and folder drag-and-drop invoke. Folders with 101+ files are fine because leftover expanded files are sent instead of the directory.
- Suggestion: Do not re-POST the directory. After `remaining_paths` is empty, either (a) POST `finalize: true` with `job_id` and no new source paths (API should accept empty `paths` on a finalize-only follow-up), or (b) treat already-registered `source_identity` / content-hash as a hit even when derivatives are still missing, so a finalize follow-up is idempotent. A first request that already consumed the whole expansion should be the finalize request only if the API can start derivatives without a second expansion. Add a TestClient (or pytest) that runs the client’s small-folder HTTP sequence and asserts photo count and `originals/` names stay at the source set.
- Status: open

### Issue 2 -- Severity: suggestion
- File: apps/web/src/lib/importWorkflow.test.ts:347
- Description: `importPhotosFromPaths finalizes a small folder after remaining_paths is empty` mocks fetch and **requires** two requests, the second with `paths: [folder]` and `finalize: true` (`importWorkflow.test.ts:370-377`). That is exactly the protocol that duplicates files on the live API. CI cannot catch Issue 1; changing the client to a finalize-only follow-up would fail this test. D2.08 (`test_path_import_process_export_workflow.py`) uses a single `finalize: true` request, so it never exercises this client loop.
- Suggestion: Replace the assertion with the intended wire protocol (one finalized request when expansion fits, or a finalize-only second call that does not re-expand the folder). Cover the sequence against the real from-paths endpoint, not only mocked fetch.
- Status: open
