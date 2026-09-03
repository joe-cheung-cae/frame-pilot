# Phase 7 Implementation Plan — Processing Job Cancel (2026-09-03)

> Language: **English** | [中文](2026-09-03-phase7-processing-cancel.zh.md)

**Umbrella:** [#145](https://github.com/joe-cheung-cae/frame-pilot/issues/145)  
**This gate:** [#146](https://github.com/joe-cheung-cae/frame-pilot/issues/146) — implement J7.01–J7.06 (J7.07 pause is not DoD)  
**Related:** `develop_plan.md` §1.1, §10.5; import cancel in `apps/api/app/services/importing.py`; Phase 6 reclaim [2026-08-29-phase6-durable-jobs.md](2026-08-29-phase6-durable-jobs.md); known gap in `docs/v2_known_limitations.md`

For Goal Mode: implement **one task id at a time**. Do not start the next task until the current task is implemented, tested, reviewed, and committed.

---

## 1. Why this slice

Chosen next product slice (2026-09-03): **processing job cancel**, with pause as optional stretch.

Import jobs already support cooperative cancel (`POST /api/projects/{project_id}/jobs/{job_id}/cancel`, `cancellation_requested`, checkpoint checks, retry). Processing jobs on the same route return **422** `"Only import jobs can be cancelled"`. Desktop quit therefore omits “Quit and cancel” while grouping/ranking is running; quit-anyway SIGTERMs the sidecar and relies on Phase 6.1 reclaim or the fail-and-retry sweep.

That is the user-visible hole: a long grouping run cannot be stopped on purpose. Pause/resume is **not** required to close that hole.

---

## 2. Locked decisions

1. **Local-first only.** No Redis, Celery, Dramatiq, cloud queue, login, or remote workers.
2. **Reuse the import cancel contract.** Same route, same `cancellation_requested` / `cancelled_at` columns, same HTTP mapping:
   - queued or running → persist flag, `202 Accepted`
   - already terminal (`complete`, `complete_with_errors`, `failed`, `cancelled`) → safe no-op, `200 OK`
   - `interrupted` (no in-flight worker) → finalize `cancelled` immediately, `200 OK` (mirror import #104 fix 4)
3. **Cooperative, not a hard kill.** The worker observes the flag at safe checkpoints. It may finish the current CPU-bound step (especially `group_similar_photos`, which is one batch call with no per-item callback) before exiting.
4. **Cancel processing clears groups.** On finalize, call existing `reset_project_after_processing_failure` then mark the job `cancelled`. Partial or newly written groups must not remain reviewable. Photos in `processing` or `processed` return to `imported`. `user_status` and `star_rating` stay. Import derivatives stay. **Originals are never modified or deleted.**
5. **Re-run, do not add processing `/retry`.** After cancel, the existing “Run Grouping and Ranking” / `POST /process` path rebuilds groups. Do not extend `POST .../retry` beyond import jobs.
6. **Export jobs stay uncancellable** (`422`). Export restart behavior stays fail-and-cleanup (Phase 6 decision 6).
7. **Reclaim honors a pending cancel.** If `cancellation_requested` is set on an interrupted processing job, reclaim finalizes `cancelled` and resets groups; it must not re-queue. Same rule as import reclaim (#104 fix 3).
8. **Desktop quit gains “Quit and cancel processing”.** `CloseChoice::CancelAndQuit` + `CloseJobKind::Processing` becomes `CancelThenTerminate` (POST cancel, wait up to 10s, then SIGTERM). Hard kill is still not labelled `cancelled`.
9. **Pause/resume is not Phase 7 DoD.** Task **J7.07** stays `[ ]` or `[-]`. A pause that still clear-and-reruns is cancel with extra states. A pause that keeps partial groups contradicts Phase 6’s safe clear-and-rerun for grouping.
10. **Out of scope:** HEIC/RAW, XMP (#117 `not_planned`), signing, packaged GUI QA (#144), tray (D3.06), auto-update, version bump, 500/1000/2000 real-browser default CI.
11. **Bilingual living docs**; English code, comments, tests, commit messages.
12. **Tests first.** Invert `test_processing_job_has_no_cancel_route_and_startup_sweep_resets_photos` rather than deleting the startup-sweep coverage.

---

## 3. Status board

Phase 7 — processing job cancel (post Phase 6.1)

- [x] J7.01 Cancel route accepts processing jobs
- [x] J7.02 Cooperative checkpoints and cancel finalize
- [x] J7.03 Reclaim/interrupted honor processing cancel
- [x] J7.04 Processing UI cancel
- [x] J7.05 Desktop quit cancel processing
- [ ] J7.06 Docs close-out
- [ ] J7.07 Optional pause/resume — **not DoD**; leave `[ ]` or mark `[-]` after J7.06 unless explicitly pulled in

---

## 4. File map

| Path | Create / edit | Tasks |
| ---- | ------------- | ----- |
| `apps/api/app/api/routes.py` | Edit `cancel_job_endpoint` | J7.01 |
| `apps/api/app/services/processing.py` | Cancel request helper, checkpoints, finalize, reclaim branch | J7.01–J7.03 |
| `apps/api/app/services/importing.py` | Do not overload import helpers; processing stays in `processing.py` | — |
| `apps/api/tests/test_job_reliability.py` | Invert 422 test; keep reclaim-off startup sweep | J7.01–J7.03 |
| `apps/api/tests/test_import_process_export_api.py` | Processing cancel persist / noop / export still 422 | J7.01–J7.02 |
| `apps/web/src/components/ProcessingPanel.tsx` | Cancel button + in-flight copy | J7.04 |
| `apps/web/src/lib/processingProgress.ts` (+ tests) | `isCancelling` block message if needed | J7.04 |
| `apps/web/src/lib/api.ts` | Reuse `cancelJob` | J7.04 |
| `tests/e2e/local-workflow.spec.ts` | Mocked processing cancel | J7.04 |
| `apps/desktop/src-tauri/src/sidecar.rs` | Dialog + `close_decision` | J7.05 |
| `apps/desktop/README.md` (+ zh if present) | Quit copy | J7.05 |
| `docs/api.md`, `docs/architecture.md`, `docs/v2_known_limitations.md`, `docs/desktop_user_guide.md`, `docs/desktop_testing.md` (+ zh) | Behavior | J7.06 |
| `CHANGELOG.md` (+ zh) | Unreleased Phase 7 | J7.06 |
| This plan (+ zh) | Tick §3 per completed task | each |

---

## 5. Current code (do not regress)

| Behavior | Where |
| -------- | ----- |
| Import-only cancel | `cancel_job_endpoint` → 422 if `job_type != "import"` |
| Import cooperative checks | `importing.py` `_import_job_cancellation_requested` before/after each photo |
| Interrupted import cancel | `_cancel_interrupted_import_job` finalizes immediately |
| Reclaim skips resume if import cancel was requested | `prepare_interrupted_import_jobs_for_reclaim` |
| Processing group reset | `reset_project_after_processing_failure` (clears all groups, `processed_images = 0`) |
| Processing UI already has cancelled recovery copy | `processingRecoveryMessage` for `status === "cancelled"` |
| Desktop processing quit | `close_decision`: CancelAndQuit on processing → Terminate; dialog has no cancel button |
| Asserted limitation | `test_processing_job_has_no_cancel_route_and_startup_sweep_resets_photos` |

Safe processing checkpoints already exist as `_save_job` / lease heartbeats:

- after claim / `starting`
- `clearing stale groups`
- `validating generated files` (heartbeat every N photos)
- `validating similarity data`
- immediately before and after `group_similar_photos`
- each `ranking group i of n` after commit

**Do not** add a progress callback inside `group_similar_photos` in this phase.

---

## 6. Task specs

### J7.01 — Cancel route accepts processing jobs

**Depends on:** none

**Contract (this task only; leave §3 J7.01 `[ ]` until the implementation commit):**

Route: `POST /api/projects/{project_id}/jobs/{job_id}/cancel`

Files (J7.01 only):

- `apps/api/app/api/routes.py` — `cancel_job_endpoint` allows `job_type == "processing"`; dispatch import jobs to `request_import_job_cancellation` and processing jobs to `request_processing_job_cancellation`.
- `apps/api/app/services/processing.py` — add `request_processing_job_cancellation(session, job)` only. Do not change `process_project` checkpoints.
- `apps/api/tests/test_job_reliability.py` — invert the 422 assertion; keep reclaim-off startup-sweep coverage for a running processing job **without** a cancel flag (rename/split if needed).
- `apps/api/tests/test_import_process_export_api.py` — queued/running persist, terminal no-op, planted non-import/non-processing 422.
- This plan (+ zh) — tick §3 J7.01 only in the implementation commit.

HTTP mapping for `job_type == "processing"`:

| Job status | Persist | HTTP |
| ---------- | ------- | ---- |
| `queued` or `running` | `cancellation_requested=true`, `current_step="cancellation_requested"`; **do not** change `status` (J7.02 stops the worker) | `202 Accepted` |
| `complete`, `complete_with_errors`, `failed`, `cancelled` | no-op; do not set the flag on a completed success | `200 OK` |
| `interrupted` (no in-flight worker) | finalize `cancelled` (`status`, `current_step="cancelled"`, `cancellation_requested=true`, `cancelled_at`, `completed_at`, clear `worker_id` / `heartbeat_at` / `interrupted_at`) **and** `reset_project_after_processing_failure` | `200 OK` |
| missing job or wrong `project_id` | unchanged | `404` |
| `job_type` not `import` or `processing` | still reject; 422 detail may keep `"Only import jobs can be cancelled"` or name both allowed types | `422` |

Live exports are `ExportRecord` rows, not `ProcessingJob`. Do **not** add production `job_type="export"`. The 422 test plants a `ProcessingJob(job_type="export")` (or any other non-import/non-processing type). Posting this cancel route with an `ExportRecord.id` stays `404`.

Tests first:

- Processing queued/running cancel → 202, flag true, `status` unchanged, original photo bytes untouched.
- Terminal processing cancel → 200 no-op.
- Planted export (or other) `ProcessingJob` cancel → 422.
- Interrupted processing cancel → 200, `cancelled`, groups empty, photos `imported`, originals untouched.
- Existing import cancel tests stay green (including `test_import_process_export_api.py` and `test_job_review_fixes_104.py`).
- Reclaim-off startup sweep for a running processing job **without** a cancel flag still fails the job and resets photos.

**J7.01 non-goals:** no worker checkpoints (`process_project` / `_save_job` observers — J7.02); no reclaim branch (J7.03); no `ProcessingPanel` / web / e2e (J7.04); no `sidecar.rs` / desktop quit (J7.05); no living API/architecture/CHANGELOG close-out (J7.06); no pause (J7.07); do not send processing jobs through `request_import_job_cancellation`; do not expand `/retry`; do not bump `APP_VERSION`; do not sign or run packaged NSIS/DMG.

**Implement:**

- `cancel_job_endpoint`: allow `job_type == "processing"`; keep 422 for `export` and any other type.
- Add `request_processing_job_cancellation(session, job)` in `processing.py` (do not send processing jobs through `request_import_job_cancellation`).
- queued/running: set `cancellation_requested`, `current_step = "cancellation_requested"`, commit, return 202. Do not change `status` yet.
- terminal: 200 no-op, do not set the flag on a completed success.
- `interrupted`: finalize `cancelled` immediately (status, `cancelled_at`, `completed_at`, clear lease) **and** `reset_project_after_processing_failure`. Return 200.

**Tests (write first):**

- Processing queued/running cancel → 202, flag true, originals untouched.
- Terminal processing cancel → 200 no-op.
- Export cancel still 422.
- Interrupted processing cancel → 200, `cancelled`, groups cleared, photos `imported`.
- Existing import cancel tests still pass.

**Commit:** `v2: allow cooperative cancel on processing jobs`

---

### J7.02 — Cooperative checkpoints and cancel finalize

**Depends on:** J7.01

**Contract (this task only; leave §3 J7.02 `[ ]` until the implementation commit):**

J7.01 persists `cancellation_requested` on queued/running processing jobs. J7.02 makes the in-flight worker observe that flag at safe checkpoints and finalize `cancelled` (not `failed`).

Files (J7.02 only):

- `apps/api/app/services/processing.py` — add `_processing_job_cancellation_requested` (mirror `_import_job_cancellation_requested`), a worker finalize helper, and checkpoint checks in `run_processing_job` / `process_project` / `_save_job`. Do not change the J7.01 HTTP mapping in `request_processing_job_cancellation`. Do not change `prepare_interrupted_processing_jobs_for_reclaim` (J7.03).
- `apps/api/tests/test_job_reliability.py` — running-job checkpoint cancel; keep crash-handler-`failed` coverage and the reclaim-off startup sweep **without** a cancel flag.
- `apps/api/tests/test_import_process_export_api.py` — derivative-validation cancel keeps copied originals and import thumbnails (or put that case in the reliability file).
- This plan (+ zh) — tick §3 J7.02 only in the implementation commit.

Live checkpoints (all of these must observe the flag). Several §5 sites are **not** `_save_job` today:

| Site | Live code | Notes |
| ---- | --------- | ----- |
| After atomic claim | `run_processing_job` after `claim_job_atomic` + refresh | queued cancel must finalize and return; do not call `process_project` |
| After `starting` commit | `process_project` after the starting commit, **before** `_complete_unchanged_job` | starting is a direct commit, not `_save_job`; a requested cancel must not take the unchanged-complete success path |
| Each `_save_job` | start of `_save_job` (`session.refresh` first) | `clearing stale groups`, `validating generated files`, `validating similarity data`, `grouping photos`, `ranking group i of n` |
| Derivative heartbeat | every `DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL` photos and the post-loop heartbeat commit | heartbeat is `refresh_job_lease_heartbeat` + commit, not `_save_job` |
| Immediately before and after `group_similar_photos` | existing pre/post heartbeats | **do not** add a progress callback inside `group_similar_photos`; the current CPU-bound call may finish |
| After each ranking group commit | after the per-group `session.commit()` that writes ranked photos | `_save_job("ranking group i of n")` runs *before* rank; post-commit is a separate check so a newly written group is reset on cancel |

Unwind (critical): `process_project`'s `except Exception` rollbacks then marks `failed`. Cooperative cancel must **not** raise a generic exception through that path (rollback would also risk undoing an uncommitted finalize). Prefer: check helper returns bool; `_save_job` returns `False` after it finalized cancel; callers `return job` immediately. A dedicated cancel exception is allowed only if it is caught *before* `except Exception` and only after finalize is committed — still prefer the bool return so a missed except cannot overwrite `cancelled` with `failed`.

Finalize (same fields as J7.01 interrupted cancel): call `reset_project_after_processing_failure` **then** set `status="cancelled"`, `current_step="cancelled"`, `cancellation_requested=True`, `cancelled_at` / `completed_at`, clear `worker_id` / `heartbeat_at`, commit. Reason string may be `"Processing job was cancelled by user request"`. Do not set `status="failed"`. Originals are never modified or deleted. Import derivatives stay. `user_status` / `star_rating` stay. Groups empty, `processed_images == 0`, in-flight `processing` / `processed` photos return to `imported`.

`_processing_job_cancellation_requested(session, job)`: `session.refresh(job)`; true iff `job.cancellation_requested` and `job.status not in TERMINAL_JOB_STATUSES` (mirror `_import_job_cancellation_requested`). Interrupted is terminal for this helper; reclaim is J7.03.

`run_processing_job` crash handler stays `failed` + reset. Its existing `TERMINAL_JOB_STATUSES` guard already no-ops an already-cancelled row. Do not relabel crashes as `cancelled`.

Tests first:

- Running processing job observes the flag at a ranking or post-grouping checkpoint (monkeypatch `rank_group` / `group_similar_photos` / `_save_job` to set or POST the flag); job ends `cancelled` (not `failed`); groups empty; `processed_images == 0`; original photo bytes unchanged; `user_status` / `star_rating` preserved if set.
- Cancel during derivative validation: copied originals and import thumbnails remain; original bytes unchanged; job `cancelled`.
- Existing `run_processing_job` crash test still ends `failed`.
- Reclaim-off startup sweep without a cancel flag still fails the job (J7.01 coverage).
- Existing import cancel tests stay green.

**J7.02 non-goals:** no reclaim branch (`prepare_interrupted_processing_jobs_for_reclaim` — J7.03); no `ProcessingPanel` / web / e2e (J7.04); no `sidecar.rs` / desktop quit (J7.05); no living API/architecture/CHANGELOG close-out (J7.06); no pause (J7.07); do not add a progress callback inside `group_similar_photos`; do not expand `/retry`; do not bump `APP_VERSION`; do not sign or run packaged NSIS/DMG; do not work #144.

**Implement:**

- `_processing_job_cancellation_requested` (refresh job row; true only while not terminal).
- Check at the checkpoints above. On true: `reset_project_after_processing_failure`, then mark job `cancelled` with `cancelled_at` / `completed_at`, clear `worker_id` / `heartbeat_at`, return. Do not raise a generic failure path that marks `failed`.
- `run_processing_job` crash handler stays `failed` + reset; do not relabel crashes as `cancelled`.

**Tests (write first):**

- Running job observes the flag at a ranking (or post-grouping) checkpoint, ends `cancelled`, groups empty, `processed_images == 0`, photo bytes unchanged, `user_status` / `star_rating` preserved if set.
- Cancel during derivative validation still leaves copied originals and import thumbnails in place.

**Commit:** `v2: stop processing jobs at cooperative cancel checkpoints`

---

### J7.03 — Reclaim/interrupted honor processing cancel

**Depends on:** J7.02

**Contract (this task only; leave §3 J7.03 `[ ]` until the implementation commit):**

J7.01 interrupted HTTP cancel already finalizes `cancelled` when there is no in-flight worker. J7.03 covers the restart path: API/worker reclaim of an `interrupted` processing row that already has `cancellation_requested=true` (cancel was persisted while queued/running, then the process died before the worker finalized). Reclaim must not re-queue that row.

Live hole: `prepare_interrupted_processing_jobs_for_reclaim` always resets groups, sets `status="queued"` / `current_step="reclaim_queued"`, increments `reclaim_count`, and appends the id. Import reclaim already skips resume when the flag is set (`prepare_interrupted_import_jobs_for_reclaim` after claim → `_finalize_cancelled_reclaim_import`, #104 fix 3). Mirror that for processing.

Files (J7.03 only):

- `apps/api/app/services/processing.py` — cancel branch in `prepare_interrupted_processing_jobs_for_reclaim` after atomic claim + refresh. Reuse `_finalize_cancelled_processing_job` (reset groups, then cancelled fields). Also clear `interrupted_at` (J7.01 interrupted HTTP cancel and import reclaim both clear it; the J7.02 helper currently does not — extend the helper or set it in the reclaim branch). Do not change `request_processing_job_cancellation` HTTP mapping. Do not change worker checkpoints.
- `apps/api/tests/test_job_processing_reclaim.py` — interrupted + flag is not re-queued; keep existing no-flag reclaim tests.
- `apps/api/tests/test_job_reliability.py` — keep `test_processing_job_startup_sweep_resets_photos_without_cancel` (reclaim-off, no flag). Do not invert it.
- `apps/api/tests/test_job_reclaim_startup.py` — keep Phase 6.1 default-on / explicit-off coverage; no cancel-flag change required.
- This plan (+ zh) — tick §3 J7.03 only in the implementation commit.

Critical: do **not** call `_processing_job_cancellation_requested` here. That helper is false when `status == "interrupted"` because interrupted is in `TERMINAL_JOB_STATUSES` (J7.02). After `claim_job_atomic(..., from_statuses={"interrupted"})` + `session.refresh(job)`, inspect `job.cancellation_requested` directly (same as import reclaim).

Branch after a successful claim:

| Condition | Action | Prepared list |
| --------- | ------ | ------------- |
| `job.cancellation_requested` | `_finalize_cancelled_processing_job`; also clear `interrupted_at`. Do **not** increment `reclaim_count`. Do **not** set `status="queued"`. `continue` so a later non-cancelled interrupted job can still fill `limit`. | omit id |
| flag false | existing Phase 6.1 path: `reset_project_after_processing_failure`, `status="queued"`, `current_step="reclaim_queued"`, increment `reclaim_count`, append id | include id |

`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` is `start_reclaimable_jobs` in `main.py`: it skips `prepare_*` and the startup sweep fails running jobs. Do **not** change that path. Jobs without a cancel flag keep default reclaim and the reclaim-off fail-and-retry sweep.

Keep `release_stale_interrupted_lease` then `claim_job_atomic` order. Failed claim still `continue`. Do not double-reset on the cancel path (the finalize helper already calls `reset_project_after_processing_failure`). Originals are never modified or deleted. Import derivatives stay. `user_status` / `star_rating` stay. Groups empty, `processed_images == 0`, in-flight `processing` / `processed` photos return to `imported`. Do not set `status="failed"`.

Tests first:

- Interrupted processing with `cancellation_requested=true` → `prepare_*` omits that id (`[]` when it is the only candidate); job `cancelled` not `queued`/`failed`; groups empty; `processed_images == 0`; in-flight photos `imported`; `user_status`/`star_rating` preserved; original bytes unchanged; `reclaim_count` unchanged; `worker_id` is None; `cancelled_at` set.
- Existing `test_prepare_interrupted_processing_clears_partial_groups` and `test_reclaim_reruns_interrupted_processing_job` stay green (no flag → queued reclaim).
- `test_processing_job_startup_sweep_resets_photos_without_cancel` still fails the job when reclaim is off.
- Optional: two interrupted processing jobs, first with flag, second without, `limit=1` → first cancelled (not in list), second queued (id returned). Cancel must not consume the reclaim slot.

**J7.03 non-goals:** no `ProcessingPanel` / web / e2e (J7.04); no `sidecar.rs` / desktop quit (J7.05); no living API/architecture/CHANGELOG close-out (J7.06); no pause (J7.07); do not expand `/retry`; do not bump `APP_VERSION`; do not sign or run packaged NSIS/DMG; do not work #144; do not change import reclaim; do not change the `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` default.

**Implement:**

- In `prepare_interrupted_processing_jobs_for_reclaim`, after atomic claim: if `cancellation_requested`, finalize cancelled + reset groups; do not append the job id for re-run.
- Confirm startup reclaim (flag on, default) and fail-and-retry (`FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0`) still behave for processing jobs **without** a cancel flag.

**Tests (write first):**

- Interrupted processing with `cancellation_requested` is not re-queued; job is `cancelled`; groups cleared.
- Keep a renamed startup-sweep test for reclaim-off running processing **without** cancel (today’s fail-and-retry assertion).

**Commit:** `v2: finalize cancelled processing instead of reclaiming it`

---

### J7.04 — Processing UI cancel

**Depends on:** J7.02

**Contract (this task only; leave §3 J7.04 `[ ]` until the implementation commit):**

J7.01/J7.02 persist `cancellation_requested` and finalize `cancelled` at checkpoints. The processing page has no cancel control. Import already has the UI pattern in `ImportPanel` (`api.cancelJob`, StopCircle, pending copy). J7.04 adds that pattern for grouping/ranking only.

Live holes:

- `ProcessingPanel.tsx` has no cancel mutation. `isProcessing` already disables Run while queued/running; after POST cancel the job stays queued/running until the worker finalizes, so Run stays disabled — but there is no Cancel button and no pending-checkpoint copy.
- `processingRecoveryMessage` already returns cancelled copy; keep and show it. Do not invent a second cancelled string.
- `api.cancelJob` already POSTs `/jobs/{id}/cancel`. Reuse it. Do not add a second client helper.
- Shared mocked E2E `POST .../cancel` hardcodes `job_type: "import"` and immediately returns `status: "cancelled"`. Processing coverage must keep a processing job as `job_type: "processing"` after cancel (specialize the cancel route in the test, or update the shared mock without regressing import cancel). Instant terminal is OK for E2E (same as import); pending copy is unit-tested.

Files (J7.04 only):

- `apps/web/src/components/ProcessingPanel.tsx` — cancel mutation via `api.cancelJob`; Cancel control; pending copy; keep Run disabled while active or cancelling; show existing cancelled recovery copy; show cancel errors.
- `apps/web/src/lib/processingProgress.ts` (+ `processingProgress.test.ts`) — `canCancelProcessing` (or equivalent), pending-cancel copy helper, `isCancelling` on `processingActionBlockMessage`. Optional `processingLoadRecoveryMessage("cancel")`.
- `apps/web/src/lib/api.ts` — reuse `cancelJob`; do not add a new function.
- `apps/web/src/components/ProcessingPanel.test.tsx` — optional; current mock is coarse. Helpers + mocked E2E are enough unless a cheap panel assertion is easy.
- `tests/e2e/local-workflow.spec.ts` — mocked processing cancel request + cancelled terminal. Do not run `test:e2e:real-browser:large`.
- This plan (+ zh) — tick §3 J7.04 only in the implementation commit.

UI mapping (mirror `ImportPanel` `canCancelImport` / pending copy):

| Displayed job | Control | Copy |
| ------------- | ------- | ---- |
| processing, queued/running, flag false, mutation not pending | show **Cancel Grouping and Ranking** (StopCircle, same border button as import) | existing `current_step` / progress |
| processing, queued/running, `cancellation_requested` or mutation pending | hide Cancel | pending: `Cancellation requested. FramePilot will stop after a safe checkpoint.` (same sentence as import) |
| processing, `cancelled` | hide Cancel; enable **Run Grouping and Ranking** (`POST /process`, not `/retry`) | existing `processingRecoveryMessage` cancelled string |
| import / export / other, or terminal complete/failed | no processing cancel control | unchanged |

`canCancelProcessing(job, isCancelPending)` is true iff the job exists, `job_type === "processing"`, status is `queued` or `running`, `cancellation_requested` is false, and `isCancelPending` is false.

`processingActionBlockMessage` gains `isCancelling` (default false). If true, return `Cancellation is being requested. Wait for FramePilot to reach a safe checkpoint.` before the existing `isProcessing` message. The panel sets `isCancelling` from `cancelMutation.isPending` or (`job.cancellation_requested` and queued/running). Run stays disabled while `isProcessing` or `isCancelling`. After `cancelled`, both are false so Run is enabled (label stays “Run Grouping and Ranking”, not “Retry…”, which is only for `failed`).

Polling: keep 1000ms while status is queued/running, including when the flag is set. Do not treat cancelled as reviewable. Do not add `interrupted` to the frontend job status union.

Cancel mutation: `api.cancelJob(projectId, job.id)` only for the displayed processing job. onSuccess invalidate `project`, `projects`, `jobs`, and `job` queries (same as the process mutation). onError show the error; originals-unchanged recovery is enough (`processingLoadRecoveryMessage("cancel")` if added). Do not POST `/retry` for processing. Do not cancel import jobs from this panel.

Tests first:

- `canCancelProcessing` true only for processing queued/running without the flag; false when the flag is set, mutation pending, cancelled, or the job is import.
- `processingActionBlockMessage` with `isCancelling` returns the wait-for-checkpoint string and still blocks Run.
- Pending copy helper (if extracted) matches the import pending sentence.
- Existing cancelled recovery string unchanged.
- Mocked E2E: seed a running processing job on `/process`; Cancel visible; Run disabled; click Cancel; POST cancel; status Cancelled; recovery copy visible; Cancel gone; **Run Grouping and Ranking** enabled (not Retry). Keep import cancel E2E green.

**J7.04 non-goals:** no `sidecar.rs` / desktop quit (J7.05); no living API/architecture/CHANGELOG close-out (J7.06); no pause (J7.07); do not expand `/retry`; do not change `processing.py` / routes / reclaim; do not bump `APP_VERSION`; do not sign or run packaged NSIS/DMG; do not work #144; do not run `test:e2e:real-browser:large`; do not tick J7.05–J7.07.

**Implement:**

- `ProcessingPanel`: Cancel control while queued/running and flag not set; pending copy while `cancellation_requested` and status not yet `cancelled`.
- Reuse `api.cancelJob`.
- Keep “Run Grouping and Ranking” disabled while active or cancelling.
- Recovery copy for `cancelled` already exists; show it.
- Mocked E2E: processing cancel request + cancelled terminal state (follow import cancel coverage in `tests/e2e/local-workflow.spec.ts`).

**Tests (write first):**

- Helper coverage for can-cancel / `isCancelling` block / pending copy.
- Mocked E2E for cancel request + cancelled terminal; import cancel E2E stays green.

**Commit:** `v2: add cancel control to processing status UI`

---

### J7.05 — Desktop quit cancel processing

**Depends on:** J7.01 (route); J7.02 should be `[x]` so the 10s wait can observe `cancelled`

**Contract (this task only; leave §3 J7.05 `[ ]` until the implementation commit):**

J7.01 accepts processing cancel. J7.02 finalizes `cancelled` at checkpoints. Desktop quit still treats processing as uncancellable. Import already uses `CancelThenTerminate` → `request_cancel_then_wait` (POST cancel, wait up to `CANCEL_WAIT` 10s) in `lib.rs` `handle_close_requested`. J7.05 only flips processing onto that existing path.

Live holes:

- `close_decision`: `CloseChoice::CancelAndQuit` + `CloseJobKind::Processing` → `CloseDecision::Terminate` (`sidecar.rs`). Import already maps to `CancelThenTerminate`.
- `quit_dialog_script_with_reclaim` Processing arm: `extra_button` is `""`; body starts with `"This job cannot be cancelled."` Title `"Grouping and ranking is still running"` and Keep working / Quit anyway stay.
- Sidecar tests pin the limitation: `close_decision_cancels_import_only_and_maps_processing_to_terminate`, `quit_dialog_script_hides_cancel_for_processing_jobs`, `quit_dialog_script_processing_is_valid_javascript_without_cancel`, and the handshake case that maps processing `cancel_and_quit` to `Terminate`.
- `apps/desktop/README.md` “Quit while a job is running”: “Processing jobs cannot be cancelled; that dialog omits Quit and cancel.” `apps/desktop/README.zh.md` is not present.
- `lib.rs` already POSTs cancel when the decision is `CancelThenTerminate`. `request_cancel_then_wait` is job-type agnostic. Do not change those unless `close_decision` alone cannot reach POST-cancel.

Files (J7.05 only):

- `apps/desktop/src-tauri/src/sidecar.rs` — `close_decision`; Processing arm of `quit_dialog_script_with_reclaim`; invert the tests above (same `#[cfg(test)]` module).
- `apps/desktop/README.md` — quit copy. Do not create `README.zh.md` in J7.05 (file map: “+ zh if present”).
- This plan (+ zh) — tick §3 J7.05 only in the implementation commit, and only if `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib` ran.

Decision mapping:

| kind | choice | decision |
| ---- | ------ | -------- |
| Import or Processing | CancelAndQuit | CancelThenTerminate |
| None | CancelAndQuit | Terminate (unchanged; None has no dialog) |
| any | Stay | Stay |
| any | QuitAnyway | Terminate |

Do not change `close_job_kind` (unknown types already map to Processing). Do not change `find_active_job`, `request_cancel_then_wait`, `CANCEL_WAIT`, or `parse_quit_choice`. Hard kill after SIGTERM / 5s is still not labelled `cancelled`. If the 10s wait expires (for example `group_similar_photos` still running), still SIGTERM; a persisted `cancellation_requested` is honored by J7.03 reclaim.

Dialog (Processing; mirror Import `data-choice`):

| Reclaim | Title | extra_button | Body (drop “This job cannot be cancelled.”) |
| ------- | ----- | ------------ | ------------------------------------------- |
| on | Grouping and ranking is still running | same unquoted `data-choice=cancel_and_quit` as import, label **Quit and cancel processing** | `You can keep working, quit and cancel grouping and ranking, or quit anyway. Cancelled processing clears partial groups. Quit anyway SIGTERMs the sidecar; the next launch can interrupt and reclaim leftover processing (partial groups are cleared before rebuild). Original photos stay unchanged.` |
| off | same | same | `You can keep working, quit and cancel grouping and ranking, or quit anyway. Cancelled processing clears partial groups. Quit anyway SIGTERMs the sidecar; the next launch marks the job failed and keeps original photos unchanged (FRAMEPILOT_JOB_RECLAIM_ON_STARTUP is explicitly disabled).` |

Keep working / Quit anyway stay. Import dialog copy and button stay unchanged.

README (J7.05 only): replace the processing-cannot-cancel sentence so an active grouping/ranking job shows Keep working / Quit and cancel processing / Quit anyway, same POST cancel + 10s wait + SIGTERM as import. Keep the Phase 6.1 reclaim paragraph and “original photos are never modified.”

Tests first (invert; do not delete reclaim / `node --check` coverage):

- `close_decision(Processing, CancelAndQuit) == CancelThenTerminate`; QuitAnyway / Stay unchanged; Import CancelAndQuit still CancelThenTerminate. Rename `close_decision_cancels_import_only_and_maps_processing_to_terminate`.
- Processing script contains `Quit and cancel processing`, `data-choice=cancel_and_quit`, `Keep working`, `Quit anyway`; does **not** contain `cannot be cancelled`. Rename `quit_dialog_script_hides_cancel_for_processing_jobs` and `quit_dialog_script_processing_is_valid_javascript_without_cancel`.
- Handshake: processing + `cancel_and_quit` → CancelThenTerminate (today Terminate).
- `quit_dialog_script_mentions_reclaim_when_enabled` still distinguishes reclaim-on vs `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP is explicitly disabled` / `marks the job failed`.
- `node --check` still passes for the processing script.
- Import cancel-button tests stay green.

**J7.05 non-goals:** no living API / architecture / CHANGELOG / `desktop_user_guide` / `desktop_testing` close-out (J7.06); no pause (J7.07); do not change `processing.py` / routes / reclaim / `ProcessingPanel`; do not change import quit copy; do not bump `APP_VERSION`; do not sign or run packaged NSIS/DMG; do not work #144; do not tick J7.06–J7.07. If `rustc` / `cargo` is missing, record the exact command and error, set ok=false, do **not** tick §3 J7.05.

**Implement:**

- `close_decision`: processing + CancelAndQuit → `CancelThenTerminate`.
- `quit_dialog_script_with_reclaim`: add “Quit and cancel processing”; drop “This job cannot be cancelled.”
- Invert sidecar tests that assert processing dialog has no cancel button.
- Update `apps/desktop/README.md` (zh only if present).

**Tests (write first):** invert the processing no-cancel assertions; watch them fail; then implement.

**Verify:** `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib`

**Commit:** `desktop: allow quit and cancel during processing`

---

### J7.06 — Docs close-out

**Depends on:** J7.03, J7.04, J7.05

**Implement bilingual updates:**

- `docs/api.md` — cancel route covers import **and** processing; export still 422
- `docs/architecture.md` — processing cancel + group reset
- `docs/v2_known_limitations.md` — remove “processing jobs still have no cancel route”; keep export/pause limits
- `docs/desktop_user_guide.md`, `docs/desktop_testing.md` — quit + processing cancel row
- `CHANGELOG.md` Unreleased — Phase 7 section
- Tick this plan’s §3 and §8

**Commit:** `docs: close out Phase 7 processing job cancel`

---

### J7.07 — Optional pause/resume (not DoD)

**Depends on:** J7.06 if ever started

Do **not** implement in the default Phase 7 loop.

If pulled in later: needs a non-terminal `paused` status, a pause flag distinct from cancel, worker exit **without** treating pause as interrupt/reclaim, and a resume that does not leave corrupt groups. Phase 6 already chose clear-and-rerun for grouping; that makes in-place pause low value. Prefer `[-]` with a dated note over a partial pause.

---

## 7. Phase 7 Definition of Done

- [ ] `POST .../jobs/{id}/cancel` cooperatively cancels queued, running, and interrupted **processing** jobs
- [ ] Export cancel remains 422
- [ ] Cancelled processing clears groups and returns in-flight photos to `imported`; originals unchanged
- [ ] Processing UI can request cancel and show checkpoint copy
- [ ] Desktop quit can cancel an active processing job, then SIGTERM
- [ ] Reclaim does not resume a processing job that was asked to cancel
- [ ] Pause/resume is not required
- [ ] Bilingual docs match the new behavior
- [ ] `npm run test:api`, `npm run test:web`, and `npm run verify` green on the Phase 7 branch tip

---

## 8. Verification commands

```bash
npm run test:api
npm run lint:api
npm run test:web
npm run typecheck
npm run verify
```

Targeted while iterating:

```bash
.venv/bin/pytest apps/api/tests/test_job_reliability.py apps/api/tests/test_import_process_export_api.py -q -k cancel
npm run test:web
```

Do not launch packaged NSIS/DMG GUI. Do not sign. Do not treat #144 as this slice.

---

## 9. Explicit non-goals

- Pause/resume (J7.07)
- Export job cancel or export reclaim
- Changing Phase 6.1 reclaim default
- HEIC/RAW, XMP, local models
- Desktop 2.2 (tray, auto-update, detached preview, data-dir migration)
- Signed store release / `2.1.0-desktop` git tag
- Packaged GUI lifecycle QA ([#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144))

---

## 10. Workflow execution

Each J7.01–J7.06 task is a **separate** workflow (workflows cannot launch other workflows). Do not implement J7.07.

| Task | Workflow | Launch |
| ---- | -------- | ------ |
| J7.01 | `.grok/workflows/phase7-j7-01.rhai` | `/workflow phase7-j7-01` |
| J7.02 | `.grok/workflows/phase7-j7-02.rhai` | `/workflow phase7-j7-02` |
| J7.03 | `.grok/workflows/phase7-j7-03.rhai` | `/workflow phase7-j7-03` |
| J7.04 | `.grok/workflows/phase7-j7-04.rhai` | `/workflow phase7-j7-04` |
| J7.05 | `.grok/workflows/phase7-j7-05.rhai` | `/workflow phase7-j7-05` |
| J7.06 | `.grok/workflows/phase7-j7-06.rhai` | `/workflow phase7-j7-06` |

Serial order only. Each run uses the six stages 需求拆解 → 评审 → 归档 → 开发 → 测试 → 上线. Suggested `agent_budget`: 16. Watch progress in `/workflows`. Do not start the next id until the previous run `complete`s with `ok=true`.
