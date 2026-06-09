# FramePilot User Workflow Improvements Progress Summary

Date: 2026-06-09.

Branch: `codex/user-workflow-improvements`.

Base comparison: `main..HEAD`.

This document summarizes the current branch's user workflow work relative to `main`. The branch contains 36 commits and is scoped to the web frontend under `apps/web`.

## Executive Summary

The current branch improves the clarity and resilience of FramePilot's browser-based workflow without changing backend behavior. The work focuses on actionable UI feedback, recovery guidance, culling ergonomics, export preference resilience, and frontend helper coverage.

The branch preserves FramePilot's local-first constraints:

- No backend endpoints, API schemas, database models, or local storage locations were changed.
- No cloud upload, login, payment, telemetry, remote processing, or model-file requirement was introduced.
- Original source photos remain untouched; the new copy repeatedly reinforces that local retries and recovery actions do not modify original files.
- The only API-client interface adjustment is frontend-local: `api.importPhotos` now accepts a readonly `File[]`, which allows the file input to be reset so users can reselect the same files.

## Workflow Improvements

### Project Creation, Dashboard, and Routing

Project creation now has clearer readiness and recovery states:

- The create action is blocked with a specific message when the project name is empty or project creation is already running.
- Project root path copy now explains whether FramePilot will use the managed local data folder or a custom local folder.
- Project creation failures include a recovery hint that keeps the user's local project data expectations explicit.

Project navigation now better reflects workflow readiness:

- Empty project lists show an actionable `Create Project` entry instead of a passive empty message.
- Project list and dashboard progress summaries distinguish empty projects, imported-but-unprocessed projects, processed projects, and active imports.
- Dashboard workflow cards route blocked `Process`, `Cull`, and `Export` actions back to the required earlier step and show concise hints such as finishing import or processing photos first.
- Project list and dashboard views poll while an import is active so active-import labels and progress summaries stay current.

### Import Workflow

Import feedback now explains what happened and what the user can safely do next:

- Import registration messages include both registered image counts and skipped-file counts, including the no-supported-images case.
- File inputs are disabled while import, retry, or cancellation work is active.
- The file input resets after selection so users can reselect the same files after an import attempt.
- Processing is blocked with specific import-state messages for running, failed, cancelled, or missing-import states.
- Failed and cancelled import terminal states now explain retry behavior and reiterate that original files are not modified.
- Import, retry, cancel, project-load, and job-status failures include recovery guidance tied to the local API and local project database.

### Processing Workflow

Processing feedback now separates blocked actions, active jobs, terminal jobs, and history:

- The grouping and ranking action is disabled through a single helper that explains whether processing is already running, import is still running, or no photos have been imported.
- Processing job history refreshes while any import, processing, export, or metadata job is active.
- Job history uses user-facing labels such as `Import`, `Grouping and ranking`, and `Export` instead of raw job type strings.
- Failed processing states include recovery guidance that explains whether retry can rebuild local grouping and ranking metadata.
- Project, current-job, and job-history load failures include local recovery messages.

### Culling Workspace

The culling workspace received the largest ergonomics pass:

- Large-preview layout now keeps the workspace height constrained on desktop so sidebars and preview areas scroll independently instead of stretching the page.
- Preview zoom changed from a boolean toggle to a clamped numeric zoom value from `25%` to `400%`.
- `Z` now fits the preview, and `+` / `-` zoom the preview in and out.
- Keyboard shortcuts now prevent browser defaults for in-workspace commands, reducing accidental browser scrolling or navigation while reviewing.
- Missing or failed local preview and thumbnail states show more specific messages, including whether a generated local asset is absent or failed to load.
- Partial-load empty states now clarify whether only a subset of project photos is loaded and offer a `Load all photos` action where appropriate.
- Batch marking now shows the exact scope being updated: active group, active filter, currently loaded photos, and partial-load caveats.
- Review save failures explain that the visible status was restored after the failed update.
- The action controls and star rating controls stay accessible in a sticky lower panel inside the metadata sidebar.

### Export Workflow

Export now has clearer readiness, history, and preference feedback:

- Selected counts and per-status counts show loading labels instead of fallback zeros while status counts are still loading.
- Export actions are blocked with a specific reason for running exports, loading counts, no selected statuses, or no matching photos.
- Export settings and mode controls are disabled while an export is running.
- Export history refreshes after both successful and failed export attempts.
- Failed export history entries show recovery guidance while keeping previous local export records visible.
- Export output paths use wrapping-safe text so long local paths do not break the layout.
- Copy-path failures explain the manual fallback when browser clipboard access is blocked.
- Export preference toggles now show whether the preference was saved locally, kept temporary, or not saved because the empty selection is invalid.

### Settings and Stored Preferences

Default export preferences are more resilient:

- Settings keep at least one default export status selected.
- The final selected default status is disabled instead of allowing an invalid empty default set.
- Preference saves report whether browser storage accepted the update.
- If browser storage is unavailable, the UI keeps the changed preference usable for the current session and reports that it was not persisted.

### Mobile Header

The shared shell header now uses a compact grid layout on small screens and keeps navigation buttons centered, reducing cramped wrapping on mobile.

## Helper and Test Coverage

The branch adds or expands frontend helper coverage for workflow copy, blocked-action decisions, and state normalization:

- `importWorkflow`: import registration, process blockers, file-selection blockers, terminal import guidance, and import recovery copy.
- `projectCreation`: project draft normalization, create-action blockers, data-folder hints, and creation recovery copy.
- `projectRouting`: active-import detection, workflow routing, progress summaries, workflow card hints, and project-load recovery copy.
- `processingProgress`: job labels, active-job detection, processing action blockers, processing recovery copy, and load recovery copy.
- `reviewNavigation`: batch scope summaries, partial-load empty states, save-failure messages, asset fallback messages, and culling load recovery copy.
- `reviewShortcuts`: preview zoom shortcuts and default-prevention behavior for in-workspace shortcuts.
- `reviewProgress` and `reviewStore`: numeric preview zoom persistence and clamping.
- `exportSelection`: loading labels, export block reasons, export history status labels, recovery copy, and running-export detection.
- `settings`: export preference toggles, non-empty preference enforcement, session-only fallback behavior, and save feedback.
- `queryInvalidation`: export-history invalidation after export attempts.

## Files Changed

The branch changes 31 frontend files with 2,137 insertions and 254 deletions relative to `main`.

Primary component areas:

- `apps/web/src/components/CullingWorkspace.tsx`
- `apps/web/src/components/ExportPanel.tsx`
- `apps/web/src/components/ImportPanel.tsx`
- `apps/web/src/components/ProcessingPanel.tsx`
- `apps/web/src/components/ProjectCreator.tsx`
- `apps/web/src/components/ProjectDashboard.tsx`
- `apps/web/src/components/ProjectList.tsx`
- `apps/web/src/components/SettingsPanel.tsx`
- `apps/web/src/components/Shell.tsx`

Primary helper and test areas:

- `apps/web/src/lib/importWorkflow.ts`
- `apps/web/src/lib/projectCreation.ts`
- `apps/web/src/lib/projectRouting.ts`
- `apps/web/src/lib/reviewNavigation.ts`
- `apps/web/src/lib/reviewShortcuts.ts`
- `apps/web/src/lib/settings.ts`
- `apps/web/src/lib/exportSelection.ts`
- `apps/web/src/lib/processingProgress.ts`
- Matching `*.test.ts` files for the helper behavior above.

## Verification Scope

This summary was prepared as a documentation-only update. The branch comparison was reviewed against:

- `git log --reverse main..HEAD`
- `git diff --stat main...HEAD`
- Existing progress-summary style in `docs/v2_development_progress_summary.md`
- Existing progress-summary style in `docs/v2_rc2_work_progress_summary.md`

Because this change only adds a markdown summary, frontend and backend test suites are not required for this document update.

Documentation verification completed for this summary:

- `git diff --check` returned no whitespace warnings for tracked changes.
- `git diff --no-index --check /dev/null docs/v2_user_workflow_improvements_progress_summary.md` returned no whitespace warnings for this new untracked file.
- The new-file diff was reviewed with `git diff --no-index /dev/null docs/v2_user_workflow_improvements_progress_summary.md`.

## Remaining Notes

This branch is a frontend user-workflow polish and resilience pass. It does not address backend processing architecture, durable worker design, algorithm quality, RAW/HEIC support, XMP sidecars, or real-world photo validation gaps from the broader v2 roadmap.
