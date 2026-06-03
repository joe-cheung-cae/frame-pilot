

# FramePilot v2 Codex Goal Mode Prompts

## 1. Purpose

This document collects the final Codex Goal Mode prompts for long-running FramePilot v2 development.

FramePilot v2 should evolve the existing v1 MVP into a reliable local-first photo culling tool. The development workflow must be iterative, test-driven, and Git-committed requirement by requirement.

Use these prompts in Codex Goal Mode when you want Codex to continue developing the project autonomously but safely.

## 2. Long-Running Auto-Iteration Prompt

Copy the following prompt into Codex Goal Mode.

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
- Use English for all code, comments, tests, docs, commit messages, and UI text unless existing UI text requires otherwise.
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
5. Read `develop_plan.md` and build an internal ordered backlog from the v2 milestones.

Overall priority order:

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

Phase 7: v2.6 Optional Advanced Support
Goal:
Only after the v2 core is stable, prepare optional advanced support.

Allowed only after earlier phases are substantially complete:
- HEIC preview support.
- RAW embedded preview extraction.
- Optional model registry.
- Optional local face detection model.
- Optional local embedding model.
- Documentation for model download, license, size, and performance.

Rules:
- Do not bundle large model files.
- Models must be optional.
- Local inference only.
- Existing JPEG workflow must remain stable.

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

## 3. Short Continue Prompt

Use this shorter prompt after Codex has already started v2 development and you only want it to continue the same loop.

```text
Continue FramePilot v2 development on the current branch.

Read `develop_plan.md`, `AGENTS.md`, and the latest Git history first.

Pick exactly one focused remaining requirement from the v2 plan. Implement it, add or update tests, run the relevant checks, fix failures until green, review the diff, commit the completed requirement to Git, and only then proceed to the next requirement.

Do not skip tests. Do not commit failing tests. Do not mix unrelated changes in one commit. Keep FramePilot local-first. Do not modify or delete original photos. Do not add cloud upload, login, payment, remote photo processing, or large bundled model files.

At the end, summarize the commits created, tests run, completed requirements, remaining gaps, and the next recommended requirement.
```

## 4. Documentation-Only Review Prompt

Use this prompt when you want Codex to review the current repository and update planning documentation only.

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

## 5. First v2 Iteration Prompt

Use this prompt if you want Codex to focus only on the first v2 implementation milestone.

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
- Use English for code, tests, docs, and commit messages.

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

## 6. Notes

- Keep the long-running prompt as the main autonomous development prompt.
- Use the short continue prompt for follow-up sessions.
- Use the documentation-only prompt when you want Codex to review progress without touching implementation.
- Use the first v2 iteration prompt when you want a tightly scoped implementation task.
- Codex should read `AGENTS.md` before work; OpenAI's Codex documentation describes `AGENTS.md` as the place for project-specific instructions that Codex reads before starting work.
- AGENTS.md is broadly used as a repository-level instruction file for coding agents, similar to a README for agents.