# Desktop Phase 2 — handoff status

- current_stage: 开发-D2.02
- status: complete
- next_stage: 开发-D2.03
- branch: feature/desktop-phase2
- base: origin/main `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- tests_run: `npm run test:web` (green; 195 node:test + 10 vitest + Next build); `apps/api/tests/test_desktop_project_roots.py` including nonempty-root case (green; 6 tests); `test_create_project_rejects_root_outside_allowlist` (green, unchanged)
- blockers: none. Live native picker clicks are not required for D2.02; Browse is covered with a mocked `getNativeFs()`.
- live_HEAD: this 开发-D2.02 commit (SHA recorded in `$HOME/.cache/framepilot-desktop-phase2/git-github.txt` after push)
- draft_PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (draft; do not merge)
- timestamp: 2026-08-20T21:46:51+08:00

## This stage

D2.02 project create with native picker. `api.createProject` sends `acknowledge_nonempty` only when `acknowledgeNonempty` is true. `ProjectCreator` shows Browse when `getNativeFs()` is non-null: pick directory, `POST /api/desktop/project-roots`, then fill `root_path`. Browser text field stays when `getNativeFs()` is null. Nonempty roots confirm with the exact English copy; 422 detail is surfaced verbatim. Registered nonempty roots 422 without the flag and 201 with it; existing files remain. §5.1 D2.02 is `[x]`. Do not start D2.03 in this commit.

Files in this commit:

- `apps/web/src/lib/api.ts`
- `apps/web/src/lib/api.test.ts`
- `apps/web/src/lib/projectCreation.ts`
- `apps/web/src/lib/projectCreation.test.ts`
- `apps/web/src/components/ProjectCreator.tsx`
- `apps/web/src/components/ProjectCreator.test.tsx`
- `apps/api/tests/test_desktop_project_roots.py`
- `docs/plans/2026-08-18-desktop-packaging.md`
- `docs/handoff/STATUS.md`

## Prior

- 需求拆解: `9e5416ad650d285378d01f588d1ca04aac196d2a` `docs: break down desktop Phase 2 requirements`
- 评审: `2cba9bf08b5d7bc22ec24630f07d2f01004cef7b` `docs: review desktop Phase 2 requirements`
- 归档: `58db4aa260fe623bd9d1f3051b3ef2d081d3867a` `docs: archive accepted desktop Phase 2 backlog`
- 开发-D2.00: `36e5777c7125a2ce87d522464a1b4fea68c6419e` `api: register desktop project roots before use`
- 开发-D2.01: `c5be41bff790a7dbd9e88eb71891f7c1d27d5c21` `desktop: add native file dialog adapters`

## Orchestration

Named workflow run `desktop-phase2` remains paused; do not resume. Continue serial parent/subagents. Never two D2 ids in one agent.

## GitHub

`git push -u origin HEAD` after this commit. Do not open a second PR. Do not merge. Do not squash. Do not force-push.
