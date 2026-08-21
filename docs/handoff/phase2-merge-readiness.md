# Desktop Phase 2 — merge readiness

- **Verdict:** ready-to-merge
- **Branch:** `feature/desktop-phase2`
- **HEAD:** `ad020a04de73f780889102606bd55849844ef783` (`docs: record Phase 2 code-review round-1`)
- **Base:** `origin/main` `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- **PR:** https://github.com/joe-cheung-cae/frame-pilot/pull/38 (do not merge from this close-out)
- **Recorded at:** 2026-08-21T11:16:00+08:00
- **APP_VERSION:** `2.0.0-rc2` (unchanged)

Code-review loop outcome: **clean**. **bugs=0.** Confirmed findings JSON: `[]`.

## Gating issues

| Issue | Severity | Status | Fix SHA |
|-------|----------|--------|---------|
| Issue 1 — small-folder path import duplication | bug | resolved | `67505aa7ede3249d85f82e5b39920975fee17f1f` |
| Issue 2 — unit test encoded the duplicating protocol | suggestion | resolved | `95e03fb39b0e04e44024e2367b2ab974f0a43e5d` (protocol in `67505aa`) |

No remaining gating bugs. Review round 1 confirmed the folder-import duplication fix and the finalize-only follow-up protocol. Next stage is none. Do not start Phase 3–5.

## Tests run

Recorded on Test `95e03fb39b0e04e44024e2367b2ab974f0a43e5d` and re-stated in Review `ad020a04de73f780889102606bd55849844ef783`:

- `.venv/bin/pytest apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_from_paths_immutability.py apps/api/tests/test_path_import_process_export_workflow.py apps/api/tests/test_batched_import_api.py -q` — 15 passed, including `test_import_from_paths_small_folder_finalize_only_follow_up_keeps_two_originals` (`total_images==2`, originals `alt.jpg` / `hero.jpg`).
- `npm --prefix apps/web run test:unit` — 222 node + 26 vitest passed; `importPhotosFromPaths finalizes a small folder after remaining_paths is empty` asserts the second request `paths: []`.

## Scope

D2.00–D2.09 plus the folder-import duplication fix. Local-first. Originals are copied, not mutated. One PR only. Do not merge to `main` from this document.
