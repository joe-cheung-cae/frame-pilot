# Desktop Phase 2 — handoff status

- current_stage: Test
- status: in progress
- next_stage: Review
- branch: feature/desktop-phase2
- base: origin/main `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- tests_run: `.venv/bin/pytest apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_from_paths_immutability.py apps/api/tests/test_path_import_process_export_workflow.py apps/api/tests/test_batched_import_api.py -q` (15 passed, including `test_import_from_paths_small_folder_finalize_only_follow_up_keeps_two_originals` which asserts `total_images==2` and originals `alt.jpg`/`hero.jpg`); `npm --prefix apps/web run test:unit` (222 node + 26 vitest passed; `importPhotosFromPaths finalizes a small folder after remaining_paths is empty` asserts second request `paths: []`)
- blockers: none
- live_HEAD: `b83eeceeb1d2d979b1b22fcb93cb0445f996f68e` `docs: record Fix SHA in Phase 2 handoff`
- draft_PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (ready-for-review allowed; **do not merge**)
- timestamp: 2026-08-21T10:39:18+08:00

## This stage

Test for the folder-import duplication fix. A 2-JPEG folder client sequence (`finalize: false` then `paths: []`/`finalize: true`) keeps `total_images==2` and originals named after sources. The web unit test asserts the second `importPhotosFromPaths` request uses `paths: []`. Do not merge. Do not start Phase 3. `APP_VERSION` stays `2.0.0-rc2`.

## Tracker (§5.1)

- [x] D2.00–D2.09
- [x] 测试 (`test: verify desktop Phase 2 behavior`)
- [x] 上线 (`docs: record Phase 2 close-out and tick desktop tracker`)
- [x] Fix (`fix: stop duplicating photos on small folder path import`)
- [x] Test (`test: verify small folder path import is not duplicated`)

## Next ids (serial)

Review.

## Prior

- Fix: `67505aa7ede3249d85f82e5b39920975fee17f1f` `fix: stop duplicating photos on small folder path import`
- 上线: `6105fbdaffeec6d214086cc763e6ac742ddea564` `docs: record Phase 2 close-out and tick desktop tracker`
- 开发-D2.08: `581efe8f13ed4b833e9e0b06abc74306ce037664` `test: cover path-import process export workflow`
- 开发-D2.09: `1742645cc45e0d6119ad0e827c37d93f54728b6b` `desktop: reveal export artifacts instead of downloading them`
- 测试: `17f071e40ed6016f0b2c29b2637e6d6fa4d330d1` `test: verify desktop Phase 2 behavior`

## Orchestration

Code-review fix workflow `phase2-code-review-fix`. Do not resume old paused runs `desktop-phase2` / `desktop-phase2-2`. Do not merge.

## GitHub

`git push -u origin HEAD` after this commit. One PR only: https://github.com/joe-cheung-cae/frame-pilot/pull/38. Do not merge. Do not squash. Do not force-push.
