# FramePilot v2 Codex Goal Mode 提示词

> 语言：[English](implement_goals.md) | **中文**

## 1. 目的

本文档汇集用于长时间运行的 FramePilot v2 开发的最终 Codex Goal Mode 提示词。

FramePilot v2 应把现有 v1 MVP 演进为可靠的本地优先照片筛选工具。开发工作流必须是迭代的、测试驱动的，并按需求逐条提交到 Git。

当你希望 Codex 自主但安全地继续开发本项目时，在 Codex Goal Mode 中使用这些提示词。

现行下一步指针是 `develop_plan.md` §1.1。第八阶段 HEIC 静帧预览（H8.01–H8.06）已经交付。交付第九阶段是剩余 stretch S9.00–S9.13（`docs/plans/2026-09-04-remaining-stretch.md`）；S9.00–S9.12 已落地。**每次运行只实现一个 S9 issue**，除非 §1.1 点名更靠后的未完成 id，否则从 S9.13 开始。不要发明第十阶段。长时提示词里的 Phase 0–7 / v2.0–v2.6 列表是历史产品排序。交付上的第七阶段是处理作业取消，已经交付；不要把 Goal Mode 的「Phase 7: v2.6」当成当前工作。

## 2. 长时间自动迭代提示词

将以下提示词复制到 Codex Goal Mode。

```text
You are working in the FramePilot repository.

This is a long-running Codex Goal Mode task.

Your mission is to automatically and iteratively develop FramePilot v2 based on the current `develop_plan.md`.

FramePilot v2 is a local-first, desktop-like AI-assisted photo culling application. It should evolve the existing v1 MVP into a reliable local photo culling tool with job-based processing, visible progress, resumable workflows, stronger grouping/ranking, a better culling workspace, robust export, and real integration/E2E coverage.

You must work in repeated development loops.

IMPORTANT LOOP RULE:
For every single requirement or coherent development unit:
1. Inspect the current repository state.
2. Choose exactly one focused requirement from `develop_plan.md`.
3. Implement only that requirement.
4. Add or update tests for that requirement.
5. Run the relevant tests/checks.
6. If tests fail, fix the code and rerun tests until they pass.
7. Review your own diff.
8. Commit the completed requirement to Git.
9. Only after the commit is created, start the next requirement.

Do not start the next requirement before the previous requirement has:
- implementation completed
- relevant tests added or updated
- tests passing
- diff reviewed
- committed to Git

If a requirement cannot be completed safely, do not partially merge it into unrelated work. Either:
- reduce the scope and commit a smaller working slice, or
- document the blocker and commit only safe documentation/test improvements if appropriate.

Read these files first:
- develop_plan.md
- AGENTS.md
- README.md
- docs/v1_review_for_v2.md, if it exists
- docs/architecture.md
- docs/api.md
- docs/scoring.md
- package.json
- apps/api source code
- apps/api tests
- apps/web source code
- tests/e2e
- scripts

Hard constraints:
- Do not restart the project from scratch.
- Preserve the existing working v1 functionality.
- Keep FramePilot local-first.
- Do not add cloud upload.
- Do not add user accounts.
- Do not add payment.
- Do not add remote photo processing.
- Do not modify original photo files.
- Do not delete original photo files.
- Do not commit private photos.
- Do not commit large model files.
- Do not implement full RAW decoding in this long-running task unless all earlier v2 core milestones are already complete.
- Do not implement heavy AI model integration before deterministic v2 processing, grouping, export, and tests are stable.
- Use English for all code, comments, tests, commit messages, and UI text unless existing UI text requires otherwise. Living documentation is bilingual (English page plus matching Chinese `*.zh.md`).
- Prefer small deterministic algorithms before optional AI models.
- Keep each Git commit focused and reviewable.
- Do not mix unrelated changes in one commit.
- Do not skip tests before commit.
- Do not commit failing tests.
- Do not ignore type errors, lint errors, or failing E2E unless the failure is clearly unrelated and documented in the commit summary.

Recommended branch:
Create or use this branch:

feature/v2-auto-iteration

If the branch already exists, continue from it.

Before starting implementation:
1. Run `git status`.
2. If there are uncommitted user changes, inspect them.
3. Do not overwrite user changes.
4. If the working tree is dirty because of previous Codex work, either continue from it safely or commit only after tests pass.
5. Read `develop_plan.md` §1.1 first. That subsection is the living next-slice pointer. Stretch lists later in `develop_plan.md` and the Phase 0–7 / v2.0–v2.6 list below are historical product sequencing. Do not reopen a shipped item.
6. The current numbered Goal Mode target is **Phase 9 remaining stretch**, one S9 issue at a time. Phase 8 HEIC still preview is shipped; do not re-implement it. Do not invent Phase 10. Implement only the slice §1.1 names next (S9.13 docs leftover repair until that box is `[x]`). Do not implement later S9 ids in the same run. If §1.1 has no unfinished S9 id, stop rather than picking from historical lists.

Numbering warning:
- Goal Mode “Phase 7: v2.6 Optional Advanced Support” is **not** delivery Phase 7. Delivery Phase 7 is processing job cancel (J7.01–J7.06) and already shipped.
- HEIC still preview is delivery **Phase 8** and already shipped, not a v2.6 bundle with RAW and optional models.

Overall historical order (shipped unless noted):

Phase 0: Safety and repository baseline
- Confirm repository can install dependencies and run existing tests.
- Confirm existing scripts in package.json.
- If missing, add safe root-level scripts for test, e2e, lint, typecheck, format, and verify.
- Do not do broad formatting unless it is a dedicated requirement with tests/checks passing.
- Commit baseline tooling only after tests/checks pass.

Phase 1: v2.0 Foundation
Goal:
Make the repository maintainable and ready for structured v2 development.

Requirements:
- Ensure developer commands are clear.
- Ensure README documents local setup, run, test, and E2E commands.
- Ensure AGENTS.md matches v2 rules.
- Ensure v2 planning docs are referenced.
- Ensure formatting/lint/typecheck/test commands are documented.
- Add or improve tests only where needed.

Commit rule:
Commit each coherent documentation/tooling improvement separately.

Phase 2: v2.1 Processing and Progress
Goal:
Replace synchronous user-facing processing with job-based processing and progress polling.

Requirements:
- Make `/process` return a job id quickly if practical.
- Ensure `ProcessingJob` records:
  - job_type
  - status
  - current_step
  - total_items
  - processed_items
  - failed_items
  - progress_percent
  - error_message
  - started_at
  - completed_at
- Add or improve `/jobs/{job_id}` polling.
- Split processing into clear stages:
  - scan/register
  - validate
  - thumbnail generation
  - preview generation
  - metadata extraction
  - hash/scoring
  - grouping
  - ranking
  - explanation
  - complete
- Add idempotent behavior where practical.
- Skip already processed or unchanged files where practical.
- Record failed items without crashing the whole job.
- Update frontend processing UI to show real stage progress.
- Add backend integration tests using generated synthetic images.
- Add tests for failed or unsupported files.

Acceptance criteria:
- Processing progress is visible in the UI.
- Job status can be polled.
- Failed files do not crash the full job.
- Existing v1 workflow still works.
- Relevant backend tests pass.
- Relevant frontend tests pass if UI changed.
- Commit after tests pass.

Phase 3: v2.2 Culling Workspace Upgrade
Goal:
Make the review workspace fast and comfortable for real culling.

Requirements:
- Improve group navigation.
- Improve keyboard-first workflow.
- Add or improve:
  - previous/next photo
  - previous/next group
  - Pick/Maybe/Reject/Unreviewed
  - 1-5 star rating
  - 0 clear rating
  - zoom toggle
  - compare mode if feasible
- Add virtualized filmstrip or grid if needed for large projects.
- Avoid refetching all photos after each status change.
- Use optimistic updates where safe.
- Add persistent review progress.
- Improve loading, empty, and error states.
- Add frontend tests for shortcuts and status updates.
- Add or update mocked E2E coverage for culling actions.

Acceptance criteria:
- User can review mostly by keyboard.
- UI remains responsive with large photo lists.
- Status changes are reliable.
- Tests pass.
- Commit after tests pass.

Phase 4: v2.3 Export and Interoperability
Goal:
Make export reliable and useful for downstream editing tools.

Requirements:
- Improve CSV export.
- Improve ZIP export.
- Improve folder copy export.
- Ensure CSV and ZIP have browser download endpoints.
- Show selected_count, export type, and output path in UI.
- Prevent empty export requests.
- Add export history if practical.
- Plan, but do not necessarily implement, XMP sidecar export.
- Add tests verifying:
  - file exists
  - file content is correct
  - selected status filter is respected
  - original files are not modified
  - download endpoint works

Acceptance criteria:
- CSV and ZIP can be downloaded from browser.
- Folder export clearly shows local output path.
- Export tests pass.
- Commit after tests pass.

Phase 5: v2.4 Algorithm Quality Upgrade
Goal:
Improve deterministic grouping, ranking, and explanations.

Requirements:
- Add or improve perceptual hash storage.
- Add union-find grouping.
- Combine:
  - capture time proximity
  - filename sequence proximity
  - perceptual hash distance
  - dimensions
  - camera model
  - focal length
- Split groups when time gaps are too large.
- Add group confidence if practical.
- Improve ranking formula.
- Improve conservative rule-based explanations.
- Make face and eye-open signals clearly experimental.
- Add deterministic tests for:
  - sharp image beats blurry similar image
  - overexposed/underexposed image is penalized
  - burst-like sequence groups correctly
  - unrelated images are not over-merged
  - explanations match ranking reasons

Acceptance criteria:
- Similar burst photos group more reliably.
- Clearer images rank above blurry similar images.
- Explanations are conservative and traceable.
- Tests pass.
- Commit after tests pass.

Phase 6: v2.5 Performance and Reliability
Goal:
Validate large-batch behavior.

Requirements:
- Add synthetic dataset generation scripts for:
  - 100 photos
  - 500 photos
  - 2,000 photos
- Add performance smoke tests where feasible.
- Profile obvious bottlenecks.
- Improve database query patterns.
- Improve frontend large-list rendering.
- Add recovery tests for interrupted or repeated processing.
- Ensure processing can be rerun safely without corrupting data.

Acceptance criteria:
- 100-photo workflow is covered.
- 500-photo workflow is documented or tested.
- 2,000-photo workflow does not crash in intended environment or is documented with measured limits.
- Tests/checks pass.
- Commit after tests pass.

Phase 7: v2.6 Optional Advanced Support (historical Goal Mode label — do not execute as one phase)
This list bundled HEIC, RAW, and optional models. That numbering is not the living pointer.
- Delivery Phase 7 is cooperative processing job cancel (J7.01–J7.06) and already shipped. Pause/resume (J7.07) is not DoD.
- HEIC still preview is delivery Phase 8 (shipped). Do not follow this v2.6 bundle.
- RAW preview, AVIF, and XMP are Phase 9 issues (S9.03–S9.05); optional models remain deferred. Do not start them unless §1.1 names that id as next.

Rules:
- Do not bundle large model files.
- Models must be optional.
- Local inference only.
- Existing JPEG workflow must remain stable.

Phase 8: HEIC still preview (shipped — do not re-implement)
Goal:
Local HEIC/HEIF still preview only. Already on `main` (H8.01–H8.06).

Requirements:
- Do not re-run `docs/plans/2026-09-04-heic-preview.md`.
- Do not invent Phase 10.
- Do not implement RAW preview, AVIF, XMP, signing, export cancel, D3.06 tray, or J7.07 pause unless `develop_plan.md` §1.1 names that S9 id as the next slice.

Acceptance criteria:
- The Phase 8 Definition of Done in that plan is already ticked.
- If §1.1 has no unfinished S9 id, do not start a new implementation loop.

Per-iteration workflow details:

At the start of each iteration:
- Print or record the selected requirement.
- Identify expected files to change.
- Identify tests to run.
- Keep the scope small.

During implementation:
- Prefer minimal changes.
- Keep APIs backward compatible where possible.
- Update docs when behavior changes.
- Update tests alongside implementation.
- Avoid broad unrelated refactors.

Before each commit:
Run the relevant checks.

Use these commands when available:
- `npm run test`
- `npm run test:e2e` when UI or workflow changes affect E2E
- `npm run lint` if available
- `npm run typecheck` if available
- `npm run verify` if available
- backend pytest command if root script is unavailable
- frontend test/build command if root script is unavailable

If a command is missing:
- Add it only if doing so is within the current requirement.
- Otherwise document the exact fallback command used.

If tests fail:
- Do not commit.
- Fix the failure.
- Rerun the failed tests.
- Repeat until green.

If a test is flaky or environment-dependent:
- Rerun once.
- If still failing, inspect the cause.
- Fix if it is related to your changes.
- If unrelated, document it clearly and avoid committing unrelated hacks.

Git commit rules:
- Commit only after tests pass.
- Use a focused commit message.
- Use this style:
  - `v2: add job progress polling`
  - `v2: improve export download workflow`
  - `v2: add deterministic grouping tests`
  - `docs: update v2 processing architecture`
  - `test: add real local smoke workflow`
- Do not create one huge commit for multiple milestones.
- Do not commit generated caches, private photos, temporary exports, node_modules, virtualenvs, or large binary files.
- Run `git status` before every commit.
- Review `git diff --stat` and relevant `git diff` before every commit.
- After committing, run `git status` again and confirm the working tree is clean or only contains intentional files for the next iteration.

Suggested command pattern before commit:

```bash
git status
npm run test
npm run test:e2e
git diff --stat
git diff
git add <only relevant files>
git commit -m "v2: <focused summary>"
git status
```

If `npm run test:e2e` is too slow for every small backend-only change:
- Run it after UI/workflow changes.
- Run it at least once before finishing the long-running task.
- Document when it was skipped and why.
- Still run the relevant backend/frontend tests for the current requirement.

Documentation requirements:
Keep these documents synchronized when behavior changes:
- README.md
- develop_plan.md
- docs/architecture.md
- docs/api.md
- docs/scoring.md
- docs/v2_testing_strategy.md if it exists
- AGENTS.md if project rules change

Do not over-document every minor change, but keep user-facing setup, API behavior, processing flow, and testing instructions accurate.

Stop conditions:
Stop the long-running iteration and summarize if:
- all v2.0 Definition of Done items in `develop_plan.md` are complete, or
- a blocking architectural decision requires product owner input, or
- an external dependency or environment issue prevents safe progress, or
- tests cannot be made green after reasonable focused debugging.

Final response after stopping:
Provide a concise but complete summary:
1. Branch name.
2. Commits created.
3. Requirements completed.
4. Tests/checks run and results.
5. Remaining v2 gaps.
6. Known risks.
7. Recommended next Codex goal prompt.

Most important instruction:
Never move to the next requirement until the current requirement is implemented, tested, passing, reviewed, and committed to Git.
```

## 3. 简短继续提示词

在 Codex 已经开始 v2 开发、你只希望它继续同一循环时，使用这个更短的提示词。

```text
Continue FramePilot v2 development on the current branch.

Read `develop_plan.md`, `AGENTS.md`, and the latest Git history first.

Pick exactly one focused remaining requirement from the v2 plan. Implement it, add or update tests, run the relevant checks, fix failures until green, review the diff, commit the completed requirement to Git, and only then proceed to the next requirement.

Do not skip tests. Do not commit failing tests. Do not mix unrelated changes in one commit. Keep FramePilot local-first. Do not modify or delete original photos. Do not add cloud upload, login, payment, remote photo processing, or large bundled model files.

At the end, summarize the commits created, tests run, completed requirements, remaining gaps, and the next recommended requirement.
```

## 4. 仅文档审阅提示词

当你希望 Codex 审阅当前仓库并只更新规划文档时，使用此提示词。

```text
You are working in the FramePilot repository.

This is a documentation-only review task.

Only create or update documentation files explicitly mentioned in this prompt. Do not modify production source code, tests, dependencies, build scripts, or formatting across the repository.

Review the current project state against `develop_plan.md`, `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/api.md`, `docs/scoring.md`, the backend source, frontend source, and tests.

Update or create the requested review document with:
- current implementation status
- completed v2 requirements
- remaining v2 gaps
- risks
- test status
- recommended next iteration

If tests are safe to run, run the relevant tests and record results. If tests cannot be run, document why.

Do not implement features in this task.
```

## 5. 首次 v2 迭代提示词

如果你希望 Codex 只聚焦第一个 v2 实现里程碑，使用此提示词。

```text
You are working in the FramePilot repository.

Focus only on the first v2 implementation iteration: job-based processing progress and real integration coverage.

Read `develop_plan.md`, `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/api.md`, backend source, frontend source, and tests first.

Objective:
Implement job-based processing progress and real integration coverage without changing the product scope.

Tasks:
1. Review current processing code.
2. Ensure `ProcessingJob` records all required stages and progress fields.
3. Make `/process` return a job id quickly if practical.
4. Add or improve `/jobs/{job_id}` polling.
5. Update frontend processing UI to show real progress.
6. Add backend integration tests using generated synthetic images.
7. Add tests for failed or unsupported files.
8. Document the updated processing flow.

Hard constraints:
- Preserve v1 workflow.
- Keep FramePilot local-first.
- Do not modify or delete original photos.
- Do not add cloud upload, login, payment, or large model files.
- Do not implement RAW/HEIC or heavy AI models in this iteration.
- Use English for code, tests, and commit messages. Living documentation is bilingual (English page plus matching Chinese `*.zh.md`).

Before committing:
- Run relevant backend tests.
- Run frontend tests/build if frontend changed.
- Run E2E if workflow changes require it.
- Fix failures until green.
- Review the diff.

Commit only after tests pass.

Use a focused commit message such as:
`v2: add job-based processing progress`

After committing, summarize changed files, tests run, results, and the next recommended v2 requirement.
```

## 6. 说明

- 把长时间运行提示词作为主要的自主开发提示词。
- 后续会话使用简短继续提示词。
- 当你希望 Codex 审阅进度且不触及实现时，使用仅文档提示词。
- 当你希望一个范围收紧的实现任务时，使用首次 v2 迭代提示词。
- Codex 应在工作前阅读 `AGENTS.md`；OpenAI 的 Codex 文档把 `AGENTS.md` 描述为 Codex 开始工作前阅读的项目特定说明位置。
- AGENTS.md 被广泛用作面向编码代理的仓库级说明文件，类似于面向代理的 README。
