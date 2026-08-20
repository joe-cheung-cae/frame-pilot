# Desktop Phase 2 — handoff status

- current_stage: 开发 (paused overnight)
- status: in_progress
- next_stage: 开发-D2.08
- branch: feature/desktop-phase2
- base: origin/main `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- live_HEAD: `ad50c7add20e55b7af79bb13205d37fc12fde09a` `api: harden desktop import paths` (synced to `origin/feature/desktop-phase2`)
- draft_PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (draft; do not merge)
- tests_run: per-id tests for D2.00–D2.07 (see those commits). Full `测试` stage not run yet.
- blockers: none product; overnight stop for schedule. Do not start Phase 3.
- timestamp: 2026-08-20T22:50:00+08:00

## Stopped here

Workflow `desktop-phase2-2` was user-paused during **开发** after D2.07 landed and D2.08 had been started in the orchestrator (no D2.08 commit). Same-process resume will not survive a new device. **Do not resume** the old paused run `desktop-phase2` (`pause()` re-fires). **Do not resume** `desktop-phase2-2` on another machine.

Tomorrow: checkout `feature/desktop-phase2` at `ad50c7a` (or latest `origin/feature/desktop-phase2`), launch a **new** `desktop-phase2` workflow (Inspect will skip docs + D2.00–D2.07). Implement **D2.08 next**, then D2.09, then 测试, then 上线. Never two D2 ids in one agent. Do not merge.

## Tracker (§5.1)

- [x] D2.00 Registered project roots
- [x] D2.01 Native file dialog adapters
- [x] D2.02 Project create with native picker
- [x] D2.03 Import panel path import
- [x] D2.04 Drag and drop
- [x] D2.05 Reveal project and export folders
- [x] D2.06 Recent projects
- [x] D2.07 Cross-platform path hardening
- [ ] D2.08 Full workflow verification
- [ ] D2.09 Reveal exports instead of downloading
- [ ] 测试 (`test: verify desktop Phase 2 behavior`)
- [ ] 上线 (`docs: record Phase 2 close-out and tick desktop tracker`)

## Next ids (serial)

1. **D2.08** commit `test: cover path-import process export workflow` — pytest from-paths → process → Pick → CSV/ZIP/folder export; originals unmodified; `tests/desktop/workflow.md`
2. **D2.09** commit `desktop: reveal export artifacts instead of downloading them` — desktop reveal, browser keeps download anchors
3. **测试** `npm run test:api`, `typecheck`+`test:web`, `typecheck:desktop`, rust-free `verify`, `test:e2e`
4. **上线** tick remaining boxes, keep PR draft or ready-for-review, **do not merge**

## Commits on this branch (all pushed)

- `9e5416a` docs: break down desktop Phase 2 requirements
- `2cba9bf` docs: review desktop Phase 2 requirements
- `58db4aa` docs: archive accepted desktop Phase 2 backlog
- `f90e446` docs: make desktop Phase 2 workflow resume-safe
- `36e5777` api: register desktop project roots before use
- `c5be41b` desktop: add native file dialog adapters
- `faddfad` web: use native directory picker when desktop APIs exist
- `1e0af75` web: import from local paths in desktop mode
- `2eefae0` desktop: add import drag-and-drop
- `c3e05b3` desktop: reveal project and export paths in the OS file manager
- `488b967` desktop: remember last opened project
- `ad50c7a` api: harden desktop import paths

## Orchestration

- Contract: `docs/handoff/phase2-backlog.md`
- Workflow: `.grok/workflows/desktop-phase2.rhai` (Inspect skips finished stages)
- Goal prompt: `docs/desktop_goal_mode.md` §5
- One draft PR only. `APP_VERSION` stays `2.0.0-rc2`.
