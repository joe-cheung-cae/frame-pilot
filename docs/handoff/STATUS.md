# Desktop Phase 2 — handoff status

- current_stage: 测试
- status: complete
- next_stage: 上线
- branch: feature/desktop-phase2
- base: origin/main `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- tests_run: `npm run test:api` 234 passed, 1 skipped; `npm run typecheck` exit 0; `npm run test:web` exit 0; `npm run typecheck:desktop` exit 0; desktop Vite build exit 0; rust-free `npm run verify` exit 0 (fail-if-invoked rustc/cargo/tauri wrappers not called); `npm run test:e2e -- --workers=1` 45 passed; D2.08 pytest twice 1 passed; `test_import_from_paths_immutability.py` 3 passed; `test_create_project_rejects_root_outside_allowlist` unchanged vs origin/main and 1 passed.
- blockers: none
- live_HEAD: this 测试 commit (SHA recorded in `$HOME/.cache/framepilot-desktop-phase2/git-github.txt` after push)
- draft_PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (draft; do not merge)
- timestamp: 2026-08-21T08:36:30+08:00

## This stage

测试 for desktop Phase 2. Fixed `ImportPanel.test.tsx` tsc spread error so `npm run typecheck` is green. Updated e2e selectors to the shipped culling/progress/export UI (listbox options, progress strings without zero-failed, browser download links, allowlisted project create). `webkitdirectory` coverage remains in `ImportExportPanels.test.tsx`. `APP_VERSION` stays `2.0.0-rc2`.

## Tracker (§5.1)

- [x] D2.00–D2.09
- [x] 测试 (`test: verify desktop Phase 2 behavior`)
- [ ] 上线 (`docs: record Phase 2 close-out and tick desktop tracker`)

## Next ids (serial)

1. **上线** tick remaining Phase 2 acceptance boxes `[x]` or dated `[~]`, keep PR #38 unmerged (ready-for-review allowed). Do not start Phase 3.

## Prior

- 开发-D2.08: `581efe8f13ed4b833e9e0b06abc74306ce037664` `test: cover path-import process export workflow`
- 开发-D2.09: `1742645cc45e0d6119ad0e827c37d93f54728b6b` `desktop: reveal export artifacts instead of downloading them`

## Orchestration

New workflow run `desktop-phase2` (`wf_01a02199eed97ef18dd51938a3d0e63b`) Inspect-skipped D2.00–D2.07. D2.08 landed by the workflow child. D2.09 and 测试 landed in the parent after the D2.09 child stalled. Workflow is paused at verification. Do not resume old paused runs. Do not merge.

## GitHub

`git push -u origin HEAD` after this commit. Do not open a second PR. Do not merge. Do not squash. Do not force-push.
