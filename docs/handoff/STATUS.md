# Desktop Phase 2 — handoff status

- current_stage: 开发-D2.04
- status: complete
- next_stage: 开发-D2.05
- branch: feature/desktop-phase2
- base: origin/main `69f41bcfb35948c9921e10a41ffd0f505ba49dad`
- tests_run: `npm run test:web` (green; 210 node:test + 20 vitest + Next build). `npm run typecheck:desktop` green. Desktop `nativeFs` unit tests green.
- blockers: none. Live WebView drop clicks are not required for D2.04; `collectDroppedPaths`, overlay `pointer-events`, HTML5 from-paths, and Tauri fallback are unit-tested. Live GUI drop may stay `[~]` until 上线 if this host has no WebView. Note E2E in Phase 2 close.
- live_HEAD: this 开发-D2.04 commit (SHA recorded in `$HOME/.cache/framepilot-desktop-phase2/git-github.txt` after push)
- draft_PR: https://github.com/joe-cheung-cae/frame-pilot/pull/38 (draft; do not merge)
- timestamp: 2026-08-20T22:14:16+08:00

## This stage

D2.04 Drag and drop. Dropped filesystem paths feed `from-paths` only (never multipart). `collectDroppedPaths(event)` reads `File.path`, dataTransfer items, and `file://` / absolute `text/plain` lists. Import-page overlay uses `pointer-events: none` unless a drag is active so Playwright file inputs stay clickable. HTML5 listeners and Tauri `subscribeDragDrop` are attached only while `ImportPanel` is mounted, so drops outside the import page do not start import. If HTML5 drop has no filesystem paths, Tauri `onDragDropEvent` paths are used. Browser file inputs are unchanged when `isDesktopShell()` is false. §5.1 D2.04 is `[x]`. Do not start D2.05 in this commit.

Files in this commit:

- `apps/web/src/lib/droppedPaths.ts`
- `apps/web/src/lib/droppedPaths.test.ts`
- `apps/web/src/lib/nativeFs.ts`
- `apps/web/src/lib/nativeFs.test.ts`
- `apps/web/src/components/ImportPanel.tsx`
- `apps/web/src/components/ImportPanel.test.tsx`
- `apps/desktop/src/lib/nativeFs.ts`
- `apps/desktop/src/lib/nativeFs.test.ts`
- `docs/plans/2026-08-18-desktop-packaging.md`
- `docs/handoff/STATUS.md`

## Prior

- 需求拆解: `9e5416ad650d285378d01f588d1ca04aac196d2a` `docs: break down desktop Phase 2 requirements`
- 评审: `2cba9bf08b5d7bc22ec24630f07d2f01004cef7b` `docs: review desktop Phase 2 requirements`
- 归档: `58db4aa260fe623bd9d1f3051b3ef2d081d3867a` `docs: archive accepted desktop Phase 2 backlog`
- 开发-D2.00: `36e5777c7125a2ce87d522464a1b4fea68c6419e` `api: register desktop project roots before use`
- 开发-D2.01: `c5be41bff790a7dbd9e88eb71891f7c1d27d5c21` `desktop: add native file dialog adapters`
- 开发-D2.02: `faddfadf0c3738bf43caf34a9ba543cc78497ac0` `web: use native directory picker when desktop APIs exist`
- 开发-D2.03: `1e0af754fa30de4cf1df6719baeb3a7b8c4c6b66` `web: import from local paths in desktop mode`

## Orchestration

Named workflow run `desktop-phase2` remains paused; do not resume. Continue serial parent/subagents. Never two D2 ids in one agent.

## GitHub

`git push -u origin HEAD` after this commit. Do not open a second PR. Do not merge. Do not squash. Do not force-push.
