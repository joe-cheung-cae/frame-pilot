# Desktop Phase 2 — handoff status

- current_stage: 开发-D2.00
- status: complete
- next_stage: 开发-D2.01
- branch: feature/desktop-phase2
- base: origin/main `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- tests_run: `.venv/bin/pytest apps/api/tests/test_desktop_project_roots.py apps/api/tests/test_projects_api.py::test_create_project_rejects_root_outside_allowlist` (green); allowlist test re-run (green); `apps/api/tests` 219 passed
- blockers: none
- live_HEAD: this 开发-D2.00 commit (SHA recorded in `$HOME/.cache/framepilot-desktop-phase2/git-github.txt` after push)
- draft_PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (draft; do not merge)
- timestamp: 2026-08-20T21:23:08+08:00

## This stage

D2.00 registered project roots. Desktop `POST`/`GET /api/desktop/project-roots` persist `{data_dir}/desktop_project_roots.json` (cap 50) and `create_project` allows `[projects_root, *allowlist, *registered_roots()]`. Endpoints 404 unless `desktop_mode_enabled()`. Registry is not Settings. §5.1 D2.00 is `[x]`. Do not start D2.01 in this commit.

Files in this commit:

- `apps/api/app/core/project_roots.py`
- `apps/api/app/services/projects.py`
- `apps/api/app/api/routes.py`
- `apps/api/app/schemas/api.py`
- `apps/api/tests/test_desktop_project_roots.py`
- `docs/api.md`
- `docs/plans/2026-08-18-desktop-packaging.md`
- `docs/handoff/STATUS.md`

## Prior

- 需求拆解: `9e5416ad650d285378d01f588d1ca04aac196d2a` `docs: break down desktop Phase 2 requirements`
- 评审: `2cba9bf08b5d7bc22ec24630f07d2f01004cef7b` `docs: review desktop Phase 2 requirements`
- 归档: `58db4aa260fe623bd9d1f3051b3ef2d081d3867a` `docs: archive accepted desktop Phase 2 backlog`

## Orchestration

Named workflow run `desktop-phase2` remains paused; do not resume. Continue serial parent/subagents. Never two D2 ids in one agent.

## GitHub

`git push -u origin HEAD` after this commit. Do not open a second PR. Do not merge. Do not squash. Do not force-push.
