"""Tests for the local SQLite job worker entrypoint (Phase 6 / J6.05)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import reset_settings_cache
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import ProcessingJob
from app.worker import WorkerLock, WorkerLockError, claim_next_queued_processing_job, run_worker_once, worker_lock_path


def test_worker_lock_is_exclusive(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    lock_path = worker_lock_path(tmp_path)
    first = WorkerLock(lock_path)
    second = WorkerLock(lock_path)
    first.acquire()
    try:
        try:
            second.acquire()
            raised = False
        except WorkerLockError:
            raised = True
        assert raised is True
    finally:
        first.release()
    second.acquire()
    second.release()


def test_claim_next_queued_processing_job_orders_by_created_at(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Worker queue"}).json()
    with Session(get_engine()) as session:
        older = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="queued",
            current_step="queued",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        newer = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="queued",
            current_step="queued",
            created_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
        session.add(older)
        session.add(newer)
        session.commit()
        session.refresh(older)
        assert claim_next_queued_processing_job(session, worker_id="worker-order") == older.id
        session.refresh(older)
        assert older.worker_id == "worker-order"
        assert older.heartbeat_at is not None


def test_run_worker_once_reclaims_interrupted_import_when_flag_on(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "1")
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Worker reclaim"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            total_items=0,
        )
        session.add(job)
        session.commit()
        job_id = job.id
        assert run_worker_once(session) is True

    with Session(get_engine()) as session:
        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        # Empty project has nothing to import; reclaim still finishes the job row.
        assert refreshed.status == "failed"
        assert refreshed.reclaim_count == 1
        assert refreshed.current_step == "failed"
