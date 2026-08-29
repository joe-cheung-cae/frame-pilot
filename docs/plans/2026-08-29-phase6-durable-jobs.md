# Phase 6 Implementation Plan — Durable Local Job Reclaim (2026-08-29)

> Language: **English** | [中文](2026-08-29-phase6-durable-jobs.zh.md)

**Umbrella:** [#100](https://github.com/joe-cheung-cae/frame-pilot/issues/100)  
**This gate:** [#102](https://github.com/joe-cheung-cae/frame-pilot/issues/102) — design only until accepted  
**Research input:** [2026-08-29-phase6-requirements.md](2026-08-29-phase6-requirements.md)  
**Related:** `develop_plan.md` §4.1 #3, §10.5, §16.2; `docs/architecture.md` job decision (2026-06-04)

For Goal Mode: implement **one task id at a time**. Do not start the next task until the current task is implemented, tested, reviewed, and committed.

---

## 1. Locked decisions

1. **Local-first only.** No Redis, Celery, Dramatiq, cloud queue, login, or remote workers in Phase 6.
2. **Default remains fail-and-retry** until reclaim is proven. Auto-reclaim starts behind `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=1` (J6.02); default flip is a separate explicit commit after J6.03/J6.04 are green.
3. **One active import-or-processing worker per machine** initially. Do not run parallel derivative workers against the same SQLite DB in Phase 6.
4. **Never modify or delete original photos.** Reclaim only rewrites derivatives, metadata, groups, job rows, and exports under project storage.
5. **Reclaim does not run on `GET /api/projects`.** Startup lifespan or an explicit reclaim runner owns recovery writes.
6. **Exports stay fail-on-restart** in Phase 6 (partial artifacts already cleaned). Export durable resume is out of scope.
7. **Bilingual living docs**; English code, comments, tests, commit messages.
8. **No HEIC/RAW/XMP/models** in this track.

---

## 2. Status board (§5.1 style)

Phase 6 — durable local job reclaim (post `2.1.0-desktop`)

- [x] J6.01 Checkpoint fields and helpers
- [x] J6.02 Feature-flagged reclaimable interrupt on startup
- [x] J6.03 In-process reclaim for interrupted import jobs
- [ ] J6.04 In-process reclaim for interrupted processing jobs
- [ ] J6.05 Local SQLite-polled worker entrypoint
- [ ] J6.06 Lease / heartbeat
- [ ] J6.07 Desktop sidecar quit alignment
- [ ] J6.08 Docs close-out

---

## 3. File map

| Path | Create / edit | Tasks |
| ---- | ------------- | ----- |
| `apps/api/app/models/entities.py` | Edit | J6.01, J6.06 |
| `apps/api/app/services/jobs.py` | Edit | J6.01–J6.06 |
| `apps/api/app/db/session.py` | Edit | J6.01, J6.06 migrations |
| `apps/api/app/schemas/api.py` | Edit | J6.01 (+ later lease fields) |
| `apps/api/app/api/routes.py` | Edit | J6.01 `_job_read`; J6.05 enqueue cutover later |
| `apps/api/app/core/config.py` | Edit | J6.02 flag |
| `apps/api/app/main.py` | Edit | J6.02–J6.04 reclaim hook |
| `apps/api/app/services/importing.py` | Edit | J6.01 write checkpoints; J6.03 reclaim |
| `apps/api/app/services/processing.py` | Edit | J6.01/J6.04 |
| `apps/api/app/worker.py` (or `app/devtools`/`app/services/worker_loop.py`) | Create | J6.05 |
| `apps/api/tests/test_job_checkpoint.py` | Create | J6.01 |
| `apps/api/tests/test_job_reliability.py` | Edit | J6.02–J6.04 |
| `apps/desktop/src-tauri/...` | Edit | J6.07 |
| `docs/architecture.md` (+ zh), `docs/api.md` (+ zh), `docs/v2_known_limitations.md` (+ zh) | Edit | J6.08 (and light notes earlier if behavior ships) |
| This plan (+ zh) | Edit | Tick §2 per completed task |

---

## 4. Task specs

### J6.01 — Checkpoint fields and helpers

**Depends on:** none  

**Implement:**

- Add nullable columns on `ProcessingJob`:
  - `checkpoint_photo_id: str | None`
  - `checkpoint_stage: str | None`
  - `interrupted_at: datetime | None` (unused until J6.02; column present)
  - `reclaim_count: int = 0`
- SQLite `ALTER TABLE` via existing `_ensure_processing_job_columns`
- Helpers in `jobs.py`:
  - `JobCheckpoint` (dataclass or NamedTuple)
  - `read_job_checkpoint(job) -> JobCheckpoint`
  - `apply_job_checkpoint(session, job, *, photo_id, stage) -> ProcessingJob` (updates fields + `updated_at`, commits or caller-commits — match existing job helper style)
- Expose optional fields on `JobRead` / `_job_read` for observability
- **Do not** change `fail_active_jobs_on_startup` yet
- **Do not** require import/processing workers to write checkpoints yet (optional thin write in import loop is OK if tests stay focused; preferred: helpers + migration only, writers in J6.03)

**Tests:** serialize/apply/read round-trip; migration adds columns on existing DB; JobRead includes new fields (null defaults).  

**Run:** `npm run test:api` (or targeted pytest) + `npm run lint:api`  

**Commit:** `v2: add processing job checkpoint fields`

---

### J6.02 — Feature-flagged reclaimable interrupt

**Depends on:** J6.01  

**Implement:**

- Settings: `job_reclaim_on_startup: bool` from `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` (`1`/`true`/`yes`)
- When flag **off** (default): keep today’s `fail_active_jobs_on_startup`
- When flag **on**: for active import/processing jobs, set status to a reclaimable interrupted state **or** keep `running`/`queued` with `interrupted_at` set and `current_step` like `interrupted - restart`, without clearing photos the way fail does — document exact status vocabulary in this plan before coding:
  - **Locked vocabulary:** keep `status` in `{"queued","running"}` only for truly active work; introduce terminal-adjacent status `interrupted` for reclaimable leftovers (add to `ACTIVE`/`TERMINAL` sets carefully so UI does not treat as complete). Polling must show the job as recoverable. Prefer `status="interrupted"` + `current_step="interrupted - restart"` + set `interrupted_at`.
- Exports: still fail-and-cleanup (decision 6)

**Tests:** default path unchanged; flag path marks `interrupted` and does **not** wipe import photo state the same as fail-restart; idempotent second startup.  

**Commit:** `v2: add optional reclaimable job interrupt on startup`

---

### J6.03 — Reclaim interrupted import jobs

**Depends on:** J6.02  

**Implement:**

- On startup (when flag on), after marking interrupted, schedule `run_import_derivative_job` (or shared reclaim entry) for each interrupted import using existing `photo_needs_import_retry` / derivative reuse paths
- Import worker writes `apply_job_checkpoint` after each successfully completed photo
- Cooperative cancel still wins over reclaim
- Cap concurrent reclaim to one import job globally

**Tests:** simulate restart mid-import with flag on → derivatives complete without new upload; originals untouched; cancel still works.  

**Commit:** `v2: reclaim interrupted import jobs on startup`

---

### J6.04 — Reclaim interrupted processing jobs

**Depends on:** J6.03  

**Implement:**

- Safe policy: if partial groups exist, clear via existing `reset_project_after_processing_failure` **then** start a fresh processing run for that project **or** resume only when no partial groups and checkpoint stage is before grouping — pick the safer clear-and-rerun for v1 reclaim unless tests prove resume-from-stage is clean
- **Locked for J6.04:** clear partial groups + re-queue processing (same as fail cleanup + new run), but automatically, when flag on. True mid-stage resume is optional later.

**Tests:** interrupted processing with partial groups → clean reprocess; review statuses preserved on photos.  

**Commit:** `v2: reclaim interrupted processing jobs on startup`

---

### J6.05 — Local worker entrypoint

**Depends on:** J6.04  

**Implement:** `python -m app.worker` (or documented module) polling SQLite for `queued` jobs; runs same service functions; single-worker lock file under data dir; API BackgroundTasks path remains until an explicit cutover flag.

**Commit:** `v2: add local SQLite job worker entrypoint`

---

### J6.06 — Lease / heartbeat

**Depends on:** J6.05  

**Implement:** `worker_id`, `heartbeat_at` columns; stale detection prefers lease expiry when set; single-user local only.

**Commit:** `v2: add local job lease and heartbeat`

---

### J6.07 — Desktop quit alignment

**Depends on:** J6.06 (or J6.03 if reclaim-only without separate worker — may start after J6.03 if quit docs only)

**Implement:** document and align quit: cooperative cancel import; with reclaim flag, SIGTERM may leave `interrupted` instead of relying solely on fail-restart messaging; update known limitations when default flips.

**Commit:** `desktop: align quit with durable job reclaim`

---

### J6.08 — Docs close-out

**Depends on:** reclaim path usable (J6.03+)  

**Implement:** update architecture job decision, known limitations, API docs; tick §2; close #100 when DoD met.

**Commit:** `docs: close out Phase 6 durable job reclaim`

---

## 5. Phase 6 Definition of Done

- [ ] Checkpoint fields exist and are covered by tests
- [ ] Fail-and-retry remains default **or** reclaim is default only after explicit flip commit with green tests
- [ ] With reclaim flag on, interrupted **import** can finish after API restart without re-uploading
- [ ] With reclaim flag on, interrupted **processing** recovers without leaving corrupt groups as complete
- [ ] Originals never modified
- [ ] No cloud/queue dependency
- [ ] Bilingual docs describe the new behavior and remaining limits
- [ ] `npm run verify` green on the Phase 6 branch tip

---

## 6. Verification commands

```bash
npm run test:api
npm run lint:api
npm run verify   # before close-out / large merges
```

Targeted while iterating:

```bash
.venv/bin/pytest apps/api/tests/test_job_checkpoint.py apps/api/tests/test_job_reliability.py -q
```
