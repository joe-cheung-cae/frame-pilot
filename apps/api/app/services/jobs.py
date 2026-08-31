"""Shared processing-job lifecycle helpers for import, processing, and future job types."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlmodel import Session, or_, select, update

from app.models.entities import ExportRecord, ProcessingJob, Project, utc_now

ACTIVE_JOB_STATUSES = frozenset({"queued", "running"})
# "interrupted" is reclaimable (Phase 6); not active work and not a successful terminal state.
TERMINAL_JOB_STATUSES = frozenset({"complete", "complete_with_errors", "failed", "cancelled", "interrupted"})
# Workflow guards (new import/process acceptance) must treat "interrupted" as in-flight too,
# so a fresh import/process cannot race a pending reclaim of the same project (#104 fix 5).
BLOCKING_JOB_STATUSES = ACTIVE_JOB_STATUSES | frozenset({"interrupted"})
STALE_JOB_AFTER = timedelta(minutes=10)
# When a worker lease heartbeat is present, prefer this shorter expiry over updated_at.
JOB_LEASE_STALE_AFTER = timedelta(minutes=2)


@dataclass(frozen=True, slots=True)
class JobCheckpoint:
    """Durable work cursor for restart-safe reclaim (Phase 6 / J6.01)."""

    photo_id: str | None = None
    stage: str | None = None


def read_job_checkpoint(job: ProcessingJob) -> JobCheckpoint:
    return JobCheckpoint(photo_id=job.checkpoint_photo_id, stage=job.checkpoint_stage)


def apply_job_checkpoint(
    session: Session,
    job: ProcessingJob,
    *,
    photo_id: str | None,
    stage: str | None,
    commit: bool = True,
) -> ProcessingJob:
    """Persist the last successfully completed photo/stage cursor on a job."""
    now = utc_now()
    job.checkpoint_photo_id = photo_id
    job.checkpoint_stage = stage
    job.updated_at = now
    session.add(job)
    if commit:
        session.commit()
        session.refresh(job)
    return job


def acquire_job_lease(
    session: Session,
    job: ProcessingJob,
    *,
    worker_id: str,
    commit: bool = True,
) -> ProcessingJob:
    """Claim a local worker lease on an active job (Phase 6 / J6.06)."""
    now = utc_now()
    job.worker_id = worker_id
    job.heartbeat_at = now
    job.updated_at = now
    session.add(job)
    if commit:
        session.commit()
        session.refresh(job)
    return job


def heartbeat_job_lease(
    session: Session,
    job: ProcessingJob,
    *,
    worker_id: str,
    commit: bool = True,
) -> ProcessingJob:
    """Refresh lease heartbeat when the same worker still owns the job."""
    if job.worker_id not in {None, worker_id}:
        return job
    now = utc_now()
    job.worker_id = worker_id
    job.heartbeat_at = now
    job.updated_at = now
    session.add(job)
    if commit:
        session.commit()
        session.refresh(job)
    return job


def clear_job_lease(
    session: Session,
    job: ProcessingJob,
    *,
    commit: bool = True,
) -> ProcessingJob:
    job.worker_id = None
    job.heartbeat_at = None
    job.updated_at = utc_now()
    session.add(job)
    if commit:
        session.commit()
        session.refresh(job)
    return job


def refresh_job_lease_heartbeat(session: Session, job: ProcessingJob) -> None:
    """Bump the lease heartbeat alongside routine progress writes (Phase 6 / #104 fix 1).

    ``acquire_job_lease`` previously set ``heartbeat_at`` once; long-running jobs with a
    lease would then look stale after ``JOB_LEASE_STALE_AFTER`` even while still making
    progress. Call this from every progress-update touchpoint (import stage callbacks,
    processing stage saves) so a still-executing owner keeps its lease fresh. No-op when
    the job has no lease (``worker_id`` unset); does not commit — callers control commit
    timing to match their existing throttling behavior.
    """
    if job.worker_id is None:
        return
    now = utc_now()
    job.heartbeat_at = now
    job.updated_at = now
    session.add(job)


def claim_job_atomic(
    session: Session,
    job_id: str,
    *,
    worker_id: str,
    from_statuses: frozenset[str],
    to_status: str | None = None,
) -> bool:
    """Atomically claim a job's lease with a single guarded ``UPDATE`` (Phase 6 / #104 fix 2).

    A read-then-write claim (select a row, then write it back) lets two executors -
    e.g. the API's in-process reclaim thread and a separately running ``python -m
    app.worker`` - both believe they own the same row before either commits. Folding the
    status/ownership check into the ``UPDATE ... WHERE`` clause makes the claim atomic
    from SQLite's perspective: only one caller's statement can match and update the row,
    and the caller must check the resulting row count to know whether it actually won.

    Returns ``True`` (and commits) only when exactly one row matched: the job was in
    ``from_statuses`` and unleased or already leased by this same ``worker_id``.
    """
    now = utc_now()
    values: dict[str, object] = {"worker_id": worker_id, "heartbeat_at": now, "updated_at": now}
    if to_status is not None:
        values["status"] = to_status
    table = ProcessingJob.__table__
    statement = (
        update(table)
        .where(table.c.id == job_id)
        .where(table.c.status.in_(list(from_statuses)))
        .where(or_(table.c.worker_id.is_(None), table.c.worker_id == worker_id))
        .values(**values)
    )
    result = session.execute(statement)
    session.commit()
    return result.rowcount == 1


def progress_percent(processed_items: int, failed_items: int, total_items: int) -> float:
    if total_items <= 0:
        return 100.0
    return round(min(100.0, ((processed_items + failed_items) / total_items) * 100), 2)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def remaining_failed_items(job: ProcessingJob) -> int:
    if job.total_items:
        return max(0, job.total_items - job.processed_items)
    return 1


def job_is_stale(job: ProcessingJob, now: datetime | None = None) -> bool:
    if job.status not in ACTIVE_JOB_STATUSES:
        return False
    current_time = as_utc(now or utc_now())
    # Prefer lease heartbeat expiry when a worker has claimed the job.
    if job.heartbeat_at is not None:
        return current_time - as_utc(job.heartbeat_at) >= JOB_LEASE_STALE_AFTER
    return current_time - as_utc(job.updated_at) >= STALE_JOB_AFTER


def job_lease_is_stale(job: ProcessingJob, now: datetime | None = None) -> bool:
    """Whether a job's worker lease heartbeat has expired, independent of ``status``.

    ``job_is_stale`` only ever looks at ``ACTIVE_JOB_STATUSES`` (queued/running), so an
    ``interrupted`` row that was claimed (worker_id/heartbeat_at set by
    ``claim_job_atomic``) but never finished flipping to a working status - e.g. the
    reclaimer process crashed between the claim and the follow-up commit - is invisible
    to every staleness sweep forever. This helper checks the lease alone so callers that
    reclaim ``interrupted`` jobs can recognize and release an abandoned lease on such a
    row (#104 residual fix 1).
    """
    if job.worker_id is None:
        return False
    if job.heartbeat_at is None:
        return True
    current_time = as_utc(now or utc_now())
    return current_time - as_utc(job.heartbeat_at) >= JOB_LEASE_STALE_AFTER


def release_stale_interrupted_lease(session: Session, job: ProcessingJob) -> ProcessingJob:
    """Clear an abandoned worker lease on an ``interrupted`` job so it can be reclaimed.

    ``claim_job_atomic``'s guarded ``UPDATE`` only matches rows that are unleased or
    already leased by the calling worker id. Without this, a job stuck with a foreign,
    expired ``worker_id`` (see ``job_lease_is_stale``) could never be claimed by a new
    reclaimer and would stay ``status=interrupted`` permanently. Clearing is itself a
    guarded ``UPDATE`` keyed on the exact ``worker_id`` observed on ``job``, so two
    concurrent releasers racing the same abandoned lease cannot both "win" (#104
    residual fix 1). No-op (and no commit) when the lease is not actually stale.
    """
    if job.status != "interrupted" or not job_lease_is_stale(job):
        return job
    stale_worker_id = job.worker_id
    table = ProcessingJob.__table__
    statement = (
        update(table)
        .where(table.c.id == job.id)
        .where(table.c.status == "interrupted")
        .where(table.c.worker_id == stale_worker_id)
        .values(worker_id=None, heartbeat_at=None, updated_at=utc_now())
    )
    session.execute(statement)
    session.commit()
    session.refresh(job)
    return job


def mark_job_failed(
    session: Session,
    job: ProcessingJob,
    reason: str,
    *,
    current_step: str = "failed",
) -> ProcessingJob:
    now = utc_now()
    job.status = "failed"
    job.current_step = current_step
    job.error_message = reason
    job.failed_items = remaining_failed_items(job)
    job.progress_percent = progress_percent(job.processed_items, job.failed_items, job.total_items)
    job.worker_id = None
    job.heartbeat_at = None
    job.completed_at = now
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def fail_stale_job(session: Session, job: ProcessingJob) -> ProcessingJob:
    if job.job_type == "processing":
        from app.services.processing import reset_project_after_processing_failure

        reason = "Processing job was interrupted before completion"
        reset_project_after_processing_failure(session, job.project_id, reason)
        return mark_job_failed(session, job, reason, current_step="failed - stale")

    if job.job_type == "import":
        from app.services.importing import reset_import_photos_after_interrupt

        reason = "Import job was interrupted before completion"
        reset_import_photos_after_interrupt(session, job.project_id, reason)
        return mark_job_failed(session, job, reason, current_step="failed - stale")

    reason = f"{job.job_type.title()} job was interrupted before completion"
    return mark_job_failed(session, job, reason, current_step="failed - stale")


def fail_stale_jobs_for_project(session: Session, project_id: str) -> None:
    active_jobs = session.exec(
        select(ProcessingJob)
        .where(ProcessingJob.project_id == project_id)
        .where(ProcessingJob.status.in_(list(ACTIVE_JOB_STATUSES)))
    ).all()
    for job in active_jobs:
        if job_is_stale(job):
            fail_stale_job(session, job)


def fail_active_jobs_on_startup(session: Session) -> int:
    """Mark any queued/running jobs and exports as failed after an API process restart."""
    active_jobs = list(
        session.exec(select(ProcessingJob).where(ProcessingJob.status.in_(list(ACTIVE_JOB_STATUSES)))).all()
    )
    for job in active_jobs:
        if job.job_type == "processing":
            from app.services.processing import reset_project_after_processing_failure

            reason = "API process restarted while this processing job was still active"
            reset_project_after_processing_failure(session, job.project_id, reason)
            mark_job_failed(session, job, reason, current_step="failed - restart")
        elif job.job_type == "import":
            from app.services.importing import reset_import_photos_after_interrupt

            reason = "API process restarted while this import job was still active"
            reset_import_photos_after_interrupt(session, job.project_id, reason)
            mark_job_failed(session, job, reason, current_step="failed - restart")
        else:
            reason = f"API process restarted while this {job.job_type} job was still active"
            mark_job_failed(session, job, reason, current_step="failed - restart")

    export_failures = _fail_running_exports_on_startup(session)
    return len(active_jobs) + export_failures


def mark_job_interrupted_for_reclaim(session: Session, job: ProcessingJob) -> ProcessingJob:
    """Mark an active job interrupted so a later reclaim pass can resume it (Phase 6 / J6.02)."""
    now = utc_now()
    job.status = "interrupted"
    job.current_step = "interrupted - restart"
    job.error_message = "API process restarted while this job was still active; waiting for local reclaim"
    job.interrupted_at = now
    job.worker_id = None
    job.heartbeat_at = None
    job.completed_at = None
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def interrupt_active_jobs_for_reclaim_on_startup(session: Session) -> int:
    """Leave import/processing work reclaimable; still fail running exports (Phase 6 decision)."""
    active_jobs = list(
        session.exec(select(ProcessingJob).where(ProcessingJob.status.in_(list(ACTIVE_JOB_STATUSES)))).all()
    )
    interrupted = 0
    for job in active_jobs:
        if job.job_type in {"import", "processing"}:
            mark_job_interrupted_for_reclaim(session, job)
            interrupted += 1
        else:
            reason = f"API process restarted while this {job.job_type} job was still active"
            mark_job_failed(session, job, reason, current_step="failed - restart")
            interrupted += 1

    export_failures = _fail_running_exports_on_startup(session)
    return interrupted + export_failures


def reconcile_active_jobs_on_startup(session: Session, *, reclaim: bool) -> int:
    if reclaim:
        return interrupt_active_jobs_for_reclaim_on_startup(session)
    return fail_active_jobs_on_startup(session)


def _fail_running_exports_on_startup(session: Session) -> int:
    running_exports = list(session.exec(select(ExportRecord).where(ExportRecord.status == "running")).all())
    for record in running_exports:
        project = session.get(Project, record.project_id)
        if project is not None:
            try:
                from app.services.processing import project_export_root

                export_root = project_export_root(project)
                target = Path(record.output_path)
                try:
                    resolved_target = target.resolve(strict=True)
                    resolved_export_root = export_root.resolve(strict=True)
                except FileNotFoundError:
                    pass
                else:
                    if resolved_target.is_relative_to(resolved_export_root):
                        if target.is_symlink():
                            target.unlink()
                        elif resolved_target.is_dir():
                            shutil.rmtree(resolved_target)
                        else:
                            resolved_target.unlink()
            except Exception:
                pass
        record.status = "failed"
        record.error_message = "API process restarted while this export was still running"
        record.completed_at = utc_now()
        session.add(record)
    if running_exports:
        session.commit()
    return len(running_exports)
