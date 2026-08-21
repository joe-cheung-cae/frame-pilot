# Desktop Phase 2 — handoff status

- current_stage: Fix
- status: in progress
- next_stage: Test
- branch: feature/desktop-phase2
- base: origin/main `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- tests_run: `.venv/bin/pytest apps/api/tests/test_import_from_paths.py apps/api/tests/test_import_from_paths_immutability.py apps/api/tests/test_path_import_process_export_workflow.py -q`; `cd apps/web && NODE_OPTIONS=--disable-warning=MODULE_TYPELESS_PACKAGE_JSON node --experimental-strip-types --test src/lib/importWorkflow.test.ts`
- blockers: none
- live_HEAD: `67505aa7ede3249d85f82e5b39920975fee17f1f` `fix: stop duplicating photos on small folder path import`
- draft_PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (ready-for-review allowed; **do not merge**)
- timestamp: 2026-08-21T10:26:40+08:00

## This stage

Fix for Phase 2 folder-import duplication (Issue 1) and the client protocol test (Issue 2). Small-folder path import no longer re-POSTs the directory after `remaining_paths` is empty; the client sends `paths: []` with `finalize: true`, `job_id`, and `expected_total`. The API accepts that finalize-only follow-up, records `source_root_path` on the first single-directory request even when `finalize` is false, and treats in-progress same-hash same-filename photos as already registered. Do not merge. Do not start Phase 3. `APP_VERSION` stays `2.0.0-rc2`.

## Tracker (§5.1)

- [x] D2.00–D2.09
- [x] 测试 (`test: verify desktop Phase 2 behavior`)
- [x] 上线 (`docs: record Phase 2 close-out and tick desktop tracker`)
- [x] Fix (`fix: stop duplicating photos on small folder path import`)
- [ ] Test

## Next ids (serial)

Test (code-review fix verification), then Review.

## Prior

- 上线: `6105fbdaffeec6d214086cc763e6ac742ddea564` `docs: record Phase 2 close-out and tick desktop tracker`
- 开发-D2.08: `581efe8f13ed4b833e9e0b06abc74306ce037664` `test: cover path-import process export workflow`
- 开发-D2.09: `1742645cc45e0d6119ad0e827c37d93f54728b6b` `desktop: reveal export artifacts instead of downloading them`
- 测试: `17f071e40ed6016f0b2c29b2637e6d6fa4d330d1` `test: verify desktop Phase 2 behavior`

## Orchestration

Code-review fix workflow `phase2-code-review-fix`. Do not resume old paused runs `desktop-phase2` / `desktop-phase2-2`. Do not merge.

## GitHub

`git push -u origin HEAD` after this commit. One PR only: https://github.com/joe-cheung-cae/frame-pilot/pull/38. Do not merge. Do not squash. Do not force-push.
