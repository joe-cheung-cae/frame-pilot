# Phase 6 Requirements Inventory — Durable Local Job Reclaim (2026-08-29)

> Language: **English** | [中文](2026-08-29-phase6-requirements.zh.md)

**Umbrella:** [#100](https://github.com/joe-cheung-cae/frame-pilot/issues/100)  
**This gate:** [#101](https://github.com/joe-cheung-cae/frame-pilot/issues/101) — requirement research only  
**Source of truth for task ids:** [2026-08-29-phase6-durable-jobs.md](2026-08-29-phase6-durable-jobs.md)

This document inventories what Phase 6 must deliver after desktop `2.1.0-desktop` RC. It does **not** change runtime behavior, flip startup policy, or tick J6.01–J6.08.

---

## 1. Why Phase 6 now

Desktop Phase 5 and issues [#96](https://github.com/joe-cheung-cae/frame-pilot/issues/96)–[#98](https://github.com/joe-cheung-cae/frame-pilot/issues/98) are closed on `main`. Open product work from `develop_plan.md` that still fails the “resumable” bar:

| Plan ask | Today on `main` |
| -------- | --------------- |
| Resumable background processing with visible progress (`develop_plan` §4.1 #3, §16.2) | Progress + stale fail + **manual** import retry; **no auto-resume after process exit** |
| Future lightweight worker (`develop_plan` §10.5) | Explicitly deferred; FastAPI `BackgroundTasks` only |
| Known limitation honesty | Documented: fail-on-restart (`docs/v2_known_limitations.md`) |

Release review and architecture both name a **local durable worker / restart-safe reclaim** as the main post-v2.0 architecture follow-up. Desktop 2.2 UI polish (tray, auto-update, detached preview) and v2.6 HEIC/RAW/XMP/models are **not** this phase.

---

## 2. Current architecture inventory

| Path | Role today |
| ---- | ---------- |
| `apps/api/app/models/entities.py` | `ProcessingJob` progress fields; import-only `retryable` |
| `apps/api/app/services/jobs.py` | Stale window (10 min); `fail_active_jobs_on_startup` |
| `apps/api/app/services/importing.py` | Derivative job, cancel, retry, interrupt photo reset |
| `apps/api/app/services/processing.py` | Process job; partial-group reset on fail |
| `apps/api/app/api/routes.py` | Schedules `BackgroundTasks`; cancel/retry routes |
| `apps/api/app/main.py` | Startup sweep → fail leftover actives |
| `apps/api/tests/test_job_reliability.py` | Restart / cancel / retry semantics |
| Project `cache/jobs/` | Directory exists; **unused as a queue** |

**Lifecycle summary:** import registers synchronously then runs derivatives in-process; processing enqueues then runs in-process; restart marks active jobs `failed - restart` and resets photos/groups so the UI is not blocked for 10 minutes. User must retry import or re-`POST /process`.

---

## 3. J6.01–J6.08 acceptance intent

| Id | Intent | Depends on | Planned primary files | Commit message |
| ---- | ------ | ---------- | --------------------- | -------------- |
| **J6.01** | Persist durable work cursor on `ProcessingJob` (photo id + stage + helpers); schema migration; unit tests for apply/read; **no startup behavior change** | — | `entities.py`, `jobs.py`, `session.py` migration, `schemas/api.py`, tests | `v2: add processing job checkpoint fields` |
| **J6.02** | Feature-flagged startup interrupt: mark reclaimable instead of fail when flag on; default remains fail-and-retry | J6.01 | `jobs.py`, `config.py`, `main.py`, tests | `v2: add optional reclaimable job interrupt on startup` |
| **J6.03** | In-process reclaim runner for interrupted **import** jobs (re-enter derivative worker for retryable photos) | J6.02 | `importing.py`, `jobs.py`, `main.py` or routes lifespan, tests | `v2: reclaim interrupted import jobs on startup` |
| **J6.04** | In-process reclaim for interrupted **processing** jobs from a safe stage (or clear partial groups then continue) | J6.03 | `processing.py`, `jobs.py`, tests | `v2: reclaim interrupted processing jobs on startup` |
| **J6.05** | Local worker entrypoint that polls SQLite for queued jobs and runs the same service functions; API may still schedule BackgroundTasks until cutover | J6.04 | `app/worker.py` (or module), docs | `v2: add local SQLite job worker entrypoint` |
| **J6.06** | Lease / heartbeat (`worker_id`, `heartbeat_at`) so stale = lease expiry, not “any restart fails” | J6.05 | `entities.py`, `jobs.py`, tests | `v2: add local job lease and heartbeat` |
| **J6.07** | Wire desktop sidecar start/stop with reclaim-safe quit docs; keep cooperative import cancel | J6.06 | desktop Rust lifecycle, desktop README, known limitations | `desktop: align quit with durable job reclaim` |
| **J6.08** | Docs close-out: architecture, known limitations, API notes; tick Phase 6 DoD | J6.03+ (full reclaim path) | bilingual architecture / limitations / api | `docs: close out Phase 6 durable job reclaim` |

Optional later (not Phase 6 DoD): processing cancel route; pause/resume; Dramatiq/RQ only if measured need.

---

## 4. Gaps vs develop_plan “resumable”

| Goal | Status |
| ---- | ------ |
| Job records + stage progress | Done |
| Return job id quickly; poll UI | Done |
| Idempotent skip of derivatives / processed photos | Mostly done |
| Fail items without killing whole job | Done |
| Manual retry after interrupt | Import yes; processing via re-process |
| Survive API/sidecar exit and continue | **Not done** |
| Separate local worker / queue | Deferred |
| Pause/resume | Not implemented |
| Processing cancel | Not implemented |
| Auto-resume interrupted jobs | Opposite: fail leftover actives |

---

## 5. Non-goals (Phase 6)

- HEIC / RAW decoding, XMP sidecar export, bundled neural models
- Cloud queues, Redis, Celery, multi-machine workers
- Desktop 2.2: tray, auto-update, detached preview, concurrency UI knobs, changing data directory
- Changing default behavior to auto-reclaim before J6.02+J6.03 are green behind a flag (or explicit default flip only after tests)
- Reopening closed desktop Phase 5 DoD as incomplete

---

## 6. Suggested gate order

1. This research (Gate 1 / #101) → merge  
2. Design plan (Gate 2 / #102) → review until accepted  
3. Dev PRs: J6.01 → J6.02 → J6.03 → … (one task id per commit where practical)  
4. Close-out: J6.08 + umbrella #100  

---

## 7. Risks (inventory only)

- Second process + SQLite WAL contention → keep one active worker initially  
- Desktop SIGTERM today relies on fail-on-restart; auto-resume must not show half-built groups as complete  
- Hard kill mid-encode still needs existing idempotent derivative checks  
- `GET` project list must stay free of heavy reclaim side effects (reclaim on lifespan / explicit runner, not list endpoints)
