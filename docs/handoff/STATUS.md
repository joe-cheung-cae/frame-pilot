# Desktop Phase 2 — handoff status

- current_stage: 开发-D2.08
- status: complete
- next_stage: 开发-D2.09
- branch: feature/desktop-phase2
- base: origin/main `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- tests_run: D2.08 pytest first then twice (green). `npm run test:api` twice (234 passed, 1 skipped Win32-only live drive-letter case on POSIX). `test_import_from_paths_immutability.py` green. ImportPanel not changed; `test:e2e` not required for this id.
- blockers: none
- live_HEAD: this 开发-D2.08 commit (SHA recorded in `$HOME/.cache/framepilot-desktop-phase2/git-github.txt` after push)
- draft_PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (draft; do not merge)
- timestamp: 2026-08-21T08:00:36+08:00

## This stage

D2.08 Full workflow verification. Pytest `test_path_import_process_pick_and_export_leaves_originals_unchanged` drives shipped `POST /imports/from-paths` → process → Pick → CSV/ZIP/folder export and asserts source `st_size` / `st_mtime_ns` / SHA-256 plus directory listing are unchanged. Manual GUI checklist is `tests/desktop/workflow.md` (pick folder, keyboard cull, export, reveal). `test_import_from_paths_immutability.py` stays in `test:api`. No product API change: the loop already existed after D2.03/D2.05. §5.1 D2.08 is `[x]`. Do not start D2.09 in this commit.

Files in this commit:

- `apps/api/tests/test_path_import_process_export_workflow.py`
- `tests/desktop/workflow.md`
- `docs/plans/2026-08-18-desktop-packaging.md`
- `docs/handoff/STATUS.md`

## Tracker (§5.1)

- [x] D2.00–D2.08
- [ ] D2.09 Reveal exports instead of downloading
- [ ] 测试 (`test: verify desktop Phase 2 behavior`)
- [ ] 上线 (`docs: record Phase 2 close-out and tick desktop tracker`)

## Next ids (serial)

1. **D2.09** commit `desktop: reveal export artifacts instead of downloading them` — desktop reveal, browser keeps download anchors
2. **测试** `npm run test:api`, `typecheck`+`test:web`, `typecheck:desktop`, rust-free `verify`, `test:e2e`
3. **上线** tick remaining boxes, keep PR draft or ready-for-review, **do not merge**

## Prior

- 需求拆解: `9e5416ad650d285378d01f588d1ca04aac196d2a` `docs: break down desktop Phase 2 requirements`
- 评审: `2cba9bf08b5d7bc22ec24630f07d2f01004cef7b` `docs: review desktop Phase 2 requirements`
- 归档: `58db4aa260fe623bd9d1f3051b3ef2d081d3867a` `docs: archive accepted desktop Phase 2 backlog`
- 开发-D2.00: `36e5777c7125a2ce87d522464a1b4fea68c6419e` `api: register desktop project roots before use`
- 开发-D2.01: `c5be41bff790a7dbd9e88eb71891f7c1d27d5c21` `desktop: add native file dialog adapters`
- 开发-D2.02: `faddfadf0c3738bf43caf34a9ba543cc78497ac0` `web: use native directory picker when desktop APIs exist`
- 开发-D2.03: `1e0af754fa30de4cf1df6719baeb3a7b8c4c6b66` `web: import from local paths in desktop mode`
- 开发-D2.04: `2eefae0c5c50c664f66babde930f25954f85a3c6` `desktop: add import drag-and-drop`
- 开发-D2.05: `c3e05b35302080b7b6b92d1b2811c7be776caccd` `desktop: reveal project and export paths in the OS file manager`
- 开发-D2.06: `488b967b7feb4d94f32d3824dcc027b208ce56e6` `desktop: remember last opened project`
- 开发-D2.07: `ad50c7add20e55b7af79bb13205d37fc12fde09a` `api: harden desktop import paths`

## Orchestration

Named workflow run `desktop-phase2` remains paused; do not resume (`pause()` re-fires). Continue serial parent/subagents. Never two D2 ids in one agent. Do not merge. `APP_VERSION` stays `2.0.0-rc2`.

## GitHub

`git push -u origin HEAD` after this commit. Do not open a second PR. Do not merge. Do not squash. Do not force-push.
