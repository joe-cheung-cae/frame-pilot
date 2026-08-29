"""Local SQLite-polled job worker (Phase 6 / J6.05).

Run with the editable API install::

    .venv/bin/python -m app.worker

This process acquires a single-machine lock under the data directory, optionally
reclaims interrupted jobs when ``FRAMEPILOT_JOB_RECLAIM_ON_STARTUP`` is enabled,
then executes ``queued`` processing jobs. The FastAPI ``BackgroundTasks`` path
remains the default until an explicit cutover; this entrypoint is for local
durable reclaim and future enqueue/cutover work.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from sqlmodel import Session, select

from app.core.config import get_settings, reset_settings_cache
from app.db.session import get_engine, init_db
from app.models.entities import ProcessingJob
from app.services.importing import prepare_interrupted_import_jobs_for_reclaim, run_import_derivative_job
from app.services.processing import prepare_interrupted_processing_jobs_for_reclaim, run_processing_job

WORKER_LOCK_NAME = "framepilot-worker.lock"


class WorkerLockError(RuntimeError):
    """Raised when another local worker already holds the lock."""


class WorkerLock:
    """Exclusive lock for a single local worker process (best-effort, single-user)."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._fd: int | None = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            if sys.platform == "win32":  # pragma: no cover - CI/dev primarily POSIX
                import msvcrt

                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            os.close(fd)
            raise WorkerLockError(f"Another FramePilot worker holds {self.lock_path}") from error
        os.write(fd, f"{os.getpid()}\n".encode())
        self._fd = fd

    def release(self) -> None:
        if self._fd is None:
            return
        fd = self._fd
        self._fd = None
        try:
            if sys.platform != "win32":
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def worker_lock_path(data_dir: Path | None = None) -> Path:
    root = data_dir or get_settings().data_dir
    return Path(root) / WORKER_LOCK_NAME


def reclaim_interrupted_jobs(session: Session) -> dict[str, list]:
    """Reclaim interrupted import/processing work (same policy as API lifespan)."""
    if not get_settings().job_reclaim_on_startup:
        return {"import": [], "processing": []}
    import_targets = prepare_interrupted_import_jobs_for_reclaim(session)
    processing_ids: list[str] = []
    if not import_targets:
        processing_ids = prepare_interrupted_processing_jobs_for_reclaim(session)
    for job_id, photo_ids in import_targets:
        run_import_derivative_job(job_id, photo_ids, [])
    for job_id in processing_ids:
        run_processing_job(job_id)
    return {"import": import_targets, "processing": processing_ids}


def claim_next_queued_processing_job(session: Session) -> str | None:
    job = session.exec(
        select(ProcessingJob)
        .where(ProcessingJob.job_type == "processing")
        .where(ProcessingJob.status == "queued")
        .order_by(ProcessingJob.created_at, ProcessingJob.id)
    ).first()
    return None if job is None else job.id


def run_worker_once(session: Session) -> bool:
    """Run one unit of work. Returns True when work was performed."""
    reclaimed = reclaim_interrupted_jobs(session)
    if reclaimed["import"] or reclaimed["processing"]:
        return True
    job_id = claim_next_queued_processing_job(session)
    if job_id is None:
        return False
    run_processing_job(job_id)
    return True


def run_worker_loop(*, poll_seconds: float = 1.0, max_iterations: int | None = None) -> int:
    reset_settings_cache()
    init_db()
    lock = WorkerLock(worker_lock_path())
    lock.acquire()
    iterations = 0
    try:
        while max_iterations is None or iterations < max_iterations:
            iterations += 1
            with Session(get_engine()) as session:
                worked = run_worker_once(session)
            if max_iterations is not None and iterations >= max_iterations:
                break
            if not worked:
                time.sleep(poll_seconds)
    finally:
        lock.release()
    return iterations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FramePilot local SQLite job worker")
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=1.0,
        help="Sleep between idle polls (default: 1.0)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single reclaim/queue pass and exit",
    )
    args = parser.parse_args(argv)
    try:
        run_worker_loop(
            poll_seconds=max(0.05, args.poll_seconds),
            max_iterations=1 if args.once else None,
        )
    except WorkerLockError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
