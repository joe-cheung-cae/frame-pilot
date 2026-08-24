# FramePilot 桌面 Goal Mode 提示词

> 语言：[English](desktop_goal_mode.md) | **中文**

## 1. 目的

本文档是桌面打包轨道的 Grok Build / Codex Goal Mode 入口。

产品计划是 [`docs/desktop_development_plan.md`](desktop_development_plan.zh.md)。
可执行待办与活跟踪器是 [`docs/plans/2026-08-18-desktop-packaging.md`](plans/2026-08-18-desktop-packaging.zh.md)（从 **D0.00** 开始；状态见 §5.1）。
2026-08-18 的 Opus 5 审阅结论已并入该计划；审阅文件因冗余已删除。

Phase 0–2 已在 `main` 上。剩余桌面工作是 Phase 3–5。不要重建 `docs/handoff/*`（包括 `STATUS.md`）。`docs/handoff` 已退役。

FramePilot 当前是本地 Web 应用（`2.0.0-rc2`）：Next.js 在 port 3000，FastAPI 在 port 8000。桌面轨道把该栈包装为带 PyInstaller sidecar 的 Tauri 2 应用。必须保持本地优先，且永不修改原片。

新的长时会话使用长提示词。续跑使用短提示词。只更新说明、不改代码时使用仅文档提示词。

## 2. 长时 Goal Mode 提示词

将下面围栏内的全部内容复制到 Goal Mode。

```text
You are working in the FramePilot repository.

This is a long-running Goal Mode task for FramePilot DESKTOP packaging.

Your mission is to automatically and iteratively implement the desktop track using the current repository state and these documents, in this order:
1. AGENTS.md
2. develop_plan.md
3. docs/desktop_development_plan.md
4. docs/plans/2026-08-18-desktop-packaging.md (read §5.1 Task Tracker first)
5. docs/desktop_goal_mode.md
6. README.md
7. docs/architecture.md
8. docs/api.md
9. docs/v2_architecture.md
10. docs/v2_known_limitations.md

Do not invent a second architecture. The locked decisions in docs/plans/2026-08-18-desktop-packaging.md §2 are binding:
- Tauri 2 + Python sidecar (not Electron unless D0.09 records that Tauri failed)
- Keep apps/web as Next.js for browser + Playwright
- Add apps/desktop as Tauri + Vite SPA that reuses apps/web/src/components, lib, and store
- HTTP to 127.0.0.1 only; Tauri allocates the port and passes --port; sidecar --data-dir is required
- Path-based import is the desktop primary import, chunked at 100 expanded files; keep multipart for the browser
- Custom project roots only via D2.00 registration; never set FRAMEPILOT_PROJECT_ROOT_ALLOWLIST to $HOME
- Host header must be loopback; Origin allowlist grows only when FRAMEPILOT_DESKTOP=1
- No cloud, login, payment, original-file mutation, HEIC/RAW/XMP, or bundled models

IMPORTANT LOOP RULE:
For every single task id in docs/plans/2026-08-18-desktop-packaging.md (D0.00, D0.01, ...):
1. Inspect git status and the current tree. Read §5.1 Task Tracker.
2. Choose the lowest incomplete ([ ]) task id whose dependencies are [x].
3. Write the tests named in that task FIRST and watch them fail for the right reason.
4. Implement only that task, minimally, until those tests pass.
5. Run the commands named in that task (or npm run test:api / npm run verify as specified).
6. If tests fail, fix and rerun until they pass.
7. Review git diff --stat and the relevant diff.
8. Tick the tracker box in §5.1 (or mark [~] with a dated feasibility note).
9. Commit that task (code + tests + tracker tick) to Git with the suggested message (English).
10. Only after the commit exists, start the next task id.

TASK COMPLETION PROTOCOL:
The authoritative task list is docs/plans/2026-08-18-desktop-packaging.md §5.1
"Task Tracker". Statuses: [ ] not started, [x] done, [~] blocked on GUI/signing,
[-] cancelled or moved.

- Before doing anything, read §5.1. Any id marked [x] is finished: do not redo it,
  do not "improve" it, do not re-run its tests as new work.
- If §5.1 says [ ] but the tree already contains the change, verify with git log,
  then tick the box in a docs-only commit and move on.
- Tick exactly one box per commit, in the same commit as the code and tests.
- Never tick a box whose tests you did not run and see pass in this session.

TEST-FIRST RULE:
Write the failing test before the implementation. A test written after a green
implementation does not count for tasks touching import, export, scoring, status
updates, or path validation.

WSL / MISSING-GUI RULES:
This machine may be Linux WSL2 with no working WebView.
- Backend, API, path-import, PyInstaller, CI, docs, and any pure TS/unit work must
  be completed normally. A GUI blocker is never an excuse to skip these.
- If a task's remaining verification requires a real window:
  1. Implement and commit the code and all non-GUI tests.
  2. Run the command once, capture the exact error.
  3. Mark the tracker entry [~] and append a dated entry to
     docs/desktop_feasibility_notes.md with the command, the error, and what is
     still unverified.
  4. Continue with the next unblocked id, including dependents whose non-GUI parts
     can be verified.
- Never mark [~] as [x] without a recorded run on a Windows host, macOS, or CI.
- Never install a display server, a WebView, or system packages to force a GUI.

SESSION BUDGET:
Complete at most 5 task ids or one phase per session, whichever comes first. Then
stop and summarize even if more work is available.

SCOPE FENCES:
- Do not set FRAMEPILOT_PROJECT_ROOT_ALLOWLIST to $HOME, /, or a drive root.
- Do not widen scripts/check-release-artifacts.sh beyond the single icons exception
  in D0.07a.
- Do not weaken test_create_project_rejects_root_outside_allowlist.
- Do not change apps/web/src/app/** routing or delete the two file inputs in
  ImportPanel.tsx.
- Do not add a version literal outside apps/api/app/core/version.py.

Do not start the next task before the previous task has:
- implementation completed
- relevant tests added or updated
- tests passing
- diff reviewed
- committed to Git

If a task cannot be completed safely:
- shrink the scope and commit a smaller green slice, or
- document the blocker in docs/desktop_feasibility_notes.md and continue with the next unblocked task that does not depend on it.

Recommended branch:
feature/desktop-packaging

If the branch already exists, continue from it. Do not overwrite unrelated user changes.

Before starting:
1. Run git status.
2. If the working tree is dirty with user edits, inspect them and do not clobber them.
3. Scan the plan and mark which task ids are already done in the tree (do not redo them).

Overall priority (do not skip ahead):
Phase 0 feasibility (D0.00–D0.09) — already on main
Phase 1 shell + sidecar (D1.01–D1.09) — already on main
Phase 2 native FS + workflow (D2.00–D2.09) — already on main
Phase 3 desktop UI (D3.01–D3.07)
Phase 4 installers + CI (D4.01–D4.06; D4.03 is moved)
Phase 5 docs + stabilize (D5.01–D5.05)

Read §5.1 first. Skip every `[x]` id. Remaining work is Phase 3–5. Do not recreate `docs/handoff/*`.

Environment:
This repo may be developed on Linux WSL2. PyInstaller and API tests can run there. A Tauri WebView may not open in WSL. Do not block API/sidecar tasks on a GUI. Record GUI blockers in docs/desktop_feasibility_notes.md and keep going with headless tests.

Hard constraints:
- Do not restart the project from scratch.
- Preserve the existing v2 local web workflow.
- Keep FramePilot local-first.
- Do not add cloud upload, user accounts, payment, or remote photo processing.
- Do not modify or delete original photo files.
- Do not commit private photos, generated datasets, SQLite files, installers, node_modules, .venv, or large model files.
- Do not listen on 0.0.0.0.
- Do not disable origin checks globally; only add explicit desktop origins when FRAMEPILOT_DESKTOP=1.
- Do not migrate apps/web off Next.js.
- Do not replace scoring/grouping with Rust.
- Do not implement HEIC, RAW, XMP, or neural models in this track.
- Use English for code, comments, tests, commits, and new UI strings. Living documentation is bilingual (English page plus matching Chinese `*.zh.md`).
- Keep npm run verify green for non-desktop CI. Do not make verify require Rust/Tauri.
- Keep Playwright E2E working when you change shared import/culling UI.
- Do not mix unrelated changes in one commit.
- Do not skip tests before commit.
- Do not commit failing tests.

Per-iteration workflow:
At the start of each iteration:
- Print the selected task id and title.
- List expected files.
- List the test command you will run.

During implementation:
- Prefer minimal changes.
- Keep the HTTP API backward compatible for the browser app.
- Update docs/api.md when routes change.
- Put desktop-only code in apps/desktop or clearly gated adapters.

Before each commit, run the relevant checks. Prefer:
- npm run test:api when apps/api changes
- npm run test:web when apps/web changes
- npm run lint:api and typecheck when those areas change
- npm run verify at the end of each phase
- npm run test:e2e when ImportPanel, CullingWorkspace, or workflow routing changes
- sidecar/desktop smokes when those scripts exist

If npm run test:e2e is too slow for a backend-only change:
- Skip it for that commit
- Say so in the commit body
- Run it at least once before finishing a phase that touched the UI

Git commit rules:
- Commit only after tests pass.
- Use the suggested message from the task, or this style:
  - api: add path-based local import
  - desktop: manage sidecar lifecycle
  - web: isolate Next navigation behind an adapter
  - test: cover path-import process export workflow
  - docs: record desktop feasibility baselines
  - ci: run npm verify on pull requests
- Run git status, git diff --stat, and git add only relevant files.
- After commit, git status again.

Stop conditions:
Stop and summarize if:
- all Phase 5 Definition of Done items are complete, or
- D0.09 needs a product owner decision and the notes are committed, or
- an environment/WebView/signing blocker prevents safe GUI work and remaining work is documented, or
- tests cannot be made green after reasonable focused debugging.

Final response after stopping:
1. Branch name
2. Commits created (hash + subject)
3. Task ids completed
4. Tests/checks run and results
5. Remaining task ids
6. Known risks
7. Recommended next Goal prompt (use the short continue prompt)

Most important instruction:
Never move to the next task id until the current task is implemented, tested, passing, reviewed, and committed to Git.
```

## 3. 短续跑提示词

```text
Continue FramePilot desktop packaging on the current branch.

Read AGENTS.md, develop_plan.md, docs/plans/2026-08-18-desktop-packaging.md §5.1, and git log first.

Read §5.1 Task Tracker first. Do not redo any [x] task. Write the failing test before the implementation. Tick the tracker box in the same commit. If a task needs a GUI this host cannot open, commit the non-GUI parts, mark it [~] with a dated note in docs/desktop_feasibility_notes.md, and move to the next unblocked id. Stop after 5 task ids and summarize.

Pick the lowest incomplete task id whose dependencies are done. Implement only that task, add or update its tests, run the named checks, fix until green, review the diff, commit, and only then continue.

Do not skip tests. Do not commit failing tests. Do not mix unrelated changes. Keep FramePilot local-first. Do not modify or delete original photos. Do not add cloud, login, payment, remote processing, or large bundled models. Keep apps/web on Next.js. Keep npm run verify free of a Tauri requirement.

At the end, summarize commits, tests, completed task ids, remaining task ids, and the next recommended task.
```

## 4. 仅文档审阅提示词

```text
You are working in the FramePilot repository.

This is a documentation-only desktop review. Only update documentation files. Do not modify production source, tests, dependencies, or build scripts.

Read the current tree against docs/desktop_development_plan.md and docs/plans/2026-08-18-desktop-packaging.md.

Update docs/desktop_feasibility_notes.md and, if needed, docs/v2_known_limitations.md with:
- which task ids are done
- remaining gaps
- measured sidecar size/startup/memory if available
- WSL/WebView/signing blockers
- recommended next task id

If tests are safe to run, run npm run test:api and record results. Do not implement features.
```

## 5. 剩余工作提示词（Phase 3–5）

在 Phase 0–2 已在 `main` 上之后使用。将下面围栏内的全部内容复制到 Grok Build Goal Mode。**不要**重建 `docs/handoff/*`（包括 `STATUS.md`）。

活跟踪器是 [`docs/plans/2026-08-18-desktop-packaging.md`](plans/2026-08-18-desktop-packaging.zh.md) §5.1。`.grok/workflows/` 下历史的 Phase 0–2 / review-fix 工作流可以保留为已完成阶段的脚本；它们不得写入已退役的 handoff 文件。

```text
You are working in the FramePilot repository.

This is a long-running Grok Build Goal Mode task for remaining FramePilot DESKTOP work (Phase 3–5).

Mission: implement the lowest incomplete task ids in docs/plans/2026-08-18-desktop-packaging.md §5.1. Phase 0–2 are already on main. Remaining work is Phase 3–5 (D3.01–D5.05). Do not recreate docs/handoff/* (including STATUS.md). docs/handoff is retired.

Read first, in this order, with tools (do not answer from memory):
1. AGENTS.md
2. develop_plan.md
3. docs/desktop_development_plan.md Phases 3–5
4. docs/plans/2026-08-18-desktop-packaging.md (D3.01–D5.05 and §5.1 Task Tracker)
5. docs/desktop_goal_mode.md §5
6. docs/api.md, docs/desktop_feasibility_notes.md

Do not treat docs/handoff/* as a live contract. If a historical workflow still names those paths, ignore write instructions for them and use §5.1 instead.

BRANCH:
Stay on the current feature branch for remaining desktop work. Do not commit on main.
Do not merge. Do not squash. Do not force-push.

TASK COMPLETION PROTOCOL:
Authoritative list: docs/plans/2026-08-18-desktop-packaging.md §5.1.
Statuses: [ ] not started, [x] done, [~] blocked on GUI/signing, [-] cancelled.
- Do not redo [x] Phase 0–2 ids.
- One remaining id per product commit. Tick that box in the same commit.
- Tests first. Watch the new test fail for the right reason, then implement.
- Never tick a box whose tests you did not run and see pass in this session.
- Drive shipped code. Do not mock the unit under test.
- If push fails: capture the exact error, retry once, continue product work, and report the blocker in the session summary. Do not write docs/handoff/STATUS.md.

REMAINING IDS (serial; skip any already [x] or [-]):
D3.01 Native menu bar
D3.02 Status bar
D3.03 Settings data directory (GET /api/meta)
D3.04 System theme follow
D3.05 Empty and error copy
D3.06 Optional tray (may end [-])
D3.07 Shortcut vs menu accelerator pass
D4.01 Bundle sidecar into Tauri resources
D4.02 NSIS and DMG config
D4.03 Moved to D0.00 (already [-])
D4.04 Desktop CI matrix
D4.05 Signing runbook
D4.06 Size pass
D5.01 Desktop test matrix
D5.02 README and user docs
D5.03 Desktop performance notes
D5.04 Version bump to 2.1.0-desktop
D5.05 Known limitations

LOCKED DECISIONS (do not re-litigate):
- Tauri 2 + Python sidecar. Dual shell. apps/web stays Next.js. No output: export.
- HTTP to 127.0.0.1 for photos. Tauri IPC only for dialogs, paths, reveal.
- nativeFs: apps/web/src/lib/nativeFs.ts getNativeFs() returns null; desktop implementation aliased by RESOLVED path like navigation.next. Next must not import @tauri-apps/plugin-*.
- Capabilities: dialog + opener only. No fs:. No shell:.
- Never set FRAMEPILOT_PROJECT_ROOT_ALLOWLIST to $HOME, /, or a drive root. D2.00 registry in {data_dir}/desktop_project_roots.json, cap 50, not inside Settings. Endpoints 404 unless FRAMEPILOT_DESKTOP=1.
- Do not change test_create_project_rejects_root_outside_allowlist assertions or allowlist error strings.
- Path import client loops remaining_paths; max 100 expanded files per request; finalize true only on last slice.
- When isDesktopShell() is false, both ImportPanel file inputs (including webkitdirectory) keep current DOM position, labels, and disabled semantics.
- Desktop reveals export output_path; browser keeps <a href=exportDownloadUrl>.
- APP_VERSION stays 2.0.0-rc2 until D5.04. npm run verify stays rust-free.
- No cloud, login, payment, original-file mutation, HEIC/RAW/XMP, bundled models.

SCOPE FENCES:
- Do not restart the product.
- Do not migrate apps/web off Next.js.
- Do not replace scoring/grouping with Rust.
- Do not widen scripts/check-release-artifacts.sh.
- Resolve repo with git rev-parse --show-toplevel. Do not hardcode /Users/chao/workspace/repo/frame-pilot.
- Do not recreate docs/handoff files.

开发: one id, tests first, tick §5.1, commit.
测试: run the commands named in that task; npm run verify stays rust-free.
上线: do not merge to main.

Stop and summarize if a remaining id cannot be made green, or Phase 5 acceptance is complete.

Final response:
1. Branch name
2. Commits created (hash + subject), in order
3. Task ids completed vs remaining
4. Tests/checks run and results
5. Known risks / [~] items
6. Recommended next Goal prompt

Most important instructions:
Never start the next task id until the current id is implemented, tested, passing, reviewed, and committed.
Never merge to main.
Never write docs/handoff/STATUS.md.
```

## 6. 仅 Phase 0 提示词

Phase 0 已在 `main` 上。仅把本提示词保留为历史有界 spike 模板；不要重跑它，也不要重建 `docs/handoff/*`。

```text
You are working in the FramePilot repository on branch feature/desktop-packaging.

Implement only Phase 0 from docs/plans/2026-08-18-desktop-packaging.md, task ids D0.00 through D0.09, one commit per task.

Phase 0 must prove: CI verify, sidecar CLI, health version payload, desktop origin+Host allowlist, chunked path-based import API, PyInstaller smoke, Next export spike notes, artifact-check exception for Tauri icons, minimal Tauri hello if the environment can open a WebView, baselines, and a written go/no-go.

Hard constraints from AGENTS.md apply. Keep the Next.js web app working. Do not require Tauri inside npm run verify.

Stop after D0.09 is committed and summarize.
```

## 7. 说明

- 长提示词是整条桌面轨道的主要自主桌面提示词。Phase 0–2 已在 `main` 上；剩余工作是 Phase 3–5。
- 剩余 Phase 3–5 工作请使用 §5，不要重跑已完成的 Phase 0–2 工作流。
- 详细文件路径、测试和验收框在 [`docs/plans/2026-08-18-desktop-packaging.md`](plans/2026-08-18-desktop-packaging.zh.md) §5.1。不要重建 `docs/handoff/*`。
- 把 [`implement_goals.md`](../implement_goals.zh.md) 留给更早的 v2 Web Goal Mode。除非桌面计划的当前任务需要极小的共享代码修复，否则不要把 v2 算法工作混进桌面 Goal Mode 会话。
- 首个桌面产品版本：`2.1.0-desktop`。`3.0.0` 不在讨论范围内。
- 执行顺序最初从 D0.00（CI verify）开始。新会话从最低未完成的 §5.1 id 开始（Phase 3–5）。
- 任务状态的唯一事实来源是实施计划的 §5.1。
