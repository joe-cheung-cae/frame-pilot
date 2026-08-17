"""Shared processing-job lifecycle helpers for import, processing, and future job types."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlmodel import Session, select

from app.models.entities import ExportRecord, ProcessingJob, Project, utc_now

ACTIVE_JOB_STATUSES = frozenset({"queued", "running"})
TERMINAL_JOB_STATUSES = frozenset({"complete", "complete_with_errors", "failed", "cancelled"})
STALE_JOB_AFTER = timedelta(minutes=10)


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
    return current_time - as_utc(job.updated_at) >= STALE_JOB_AFTER


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
        reason = "Import job was interrupted before completion"
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
            reason = "API process restarted while this import job was still active"
            mark_job_failed(session, job, reason, current_step="failed - restart")
        else:
            reason = f"API process restarted while this {job.job_type} job was still active"
            mark_job_failed(session, job, reason, current_step="failed - restart")

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

    return len(active_jobs) + len(running_exports)
