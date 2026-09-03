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

- [ ] J7.01 Cancel route accepts processing jobs
- [ ] J7.02 Cooperative checkpoints and cancel finalize
- [ ] J7.03 Reclaim/interrupted honor processing cancel
- [ ] J7.04 Processing UI cancel
- [ ] J7.05 Desktop quit cancel processing
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

**Implement:**

- `_processing_job_cancellation_requested` (refresh job row; true only while not terminal).
- Check at the checkpoints in §5. On true: `reset_project_after_processing_failure`, then mark job `cancelled` with `cancelled_at` / `completed_at`, clear `worker_id` / `heartbeat_at`, return. Do not raise a generic failure path that marks `failed`.
- `run_processing_job` crash handler stays `failed` + reset; do not relabel crashes as `cancelled`.

**Tests (write first):**

- Running job observes the flag at a ranking (or post-grouping) checkpoint, ends `cancelled`, groups empty, `processed_images == 0`, photo bytes unchanged, `user_status` / `star_rating` preserved if set.
- Cancel during derivative validation still leaves copied originals and import thumbnails in place.

**Commit:** `v2: stop processing jobs at cooperative cancel checkpoints`

---

### J7.03 — Reclaim/interrupted honor processing cancel

**Depends on:** J7.02

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

**Implement:**

- `ProcessingPanel`: Cancel control while queued/running and flag not set; pending copy while `cancellation_requested` and status not yet `cancelled`.
- Reuse `api.cancelJob`.
- Keep “Run Grouping and Ranking” disabled while active or cancelling.
- Recovery copy for `cancelled` already exists; show it.
- Mocked E2E: processing cancel request + cancelled terminal state (follow import cancel coverage in `tests/e2e/local-workflow.spec.ts`).

**Commit:** `v2: add cancel control to processing status UI`

---

### J7.05 — Desktop quit cancel processing

**Depends on:** J7.01 (route); ideally J7.02 so the 10s wait can observe `cancelled`

**Implement:**

- `close_decision`: processing + CancelAndQuit → `CancelThenTerminate`.
- `quit_dialog_script_with_reclaim`: add “Quit and cancel processing”; drop “This job cannot be cancelled.”
- Invert sidecar tests that assert processing dialog has no cancel button.
- Update `apps/desktop/README.md` (+ zh).

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
