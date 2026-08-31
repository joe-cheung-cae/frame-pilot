"""Tests for feature-flagged reclaimable job interrupt on startup (Phase 6 / J6.02)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import reset_settings_cache
from app.db.session import get_engine
from app.main import create_app, ensure_db_ready, reset_db_ready_flag
from app.models.entities import Photo, ProcessingJob
from app.services.jobs import (
    fail_active_jobs_on_startup,
    interrupt_active_jobs_for_reclaim_on_startup,
    reconcile_active_jobs_on_startup,
)


def test_default_startup_still_fails_active_jobs(tmp_path, monkeypatch):
    monkeypatch.delenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", raising=False)
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Default fail"}).json()

    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            checkpoint_photo_id="photo-1",
            checkpoint_stage="derivative_generation",
            updated_at=datetime.now(UTC),
        )
        photo = Photo(
            project_id=project["id"],
            original_path=str(tmp_path / "a.jpg"),
            filename="a.jpg",
            processing_state="processing",
        )
        session.add(job)
        session.add(photo)
        session.commit()
        job_id = job.id
        photo_id = photo.id

    reset_db_ready_flag()
    ensure_db_ready()

    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        photo = session.get(Photo, photo_id)
        assert job is not None
        assert job.status == "failed"
        assert job.current_step == "failed - restart"
        assert photo is not None
        # Fail path resets interrupted import photos for manual retry.
        assert photo.processing_state in {"failed", "imported"}


def test_reclaim_flag_marks_jobs_interrupted_without_photo_reset(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "1")
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Reclaim interrupt"}).json()

    with Session(get_engine()) as session:
        import_job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            checkpoint_photo_id="photo-keep",
            checkpoint_stage="derivative_generation",
            total_items=2,
            processed_items=1,
            updated_at=datetime.now(UTC),
        )
        processing_job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="queued",
            current_step="queued",
            updated_at=datetime.now(UTC),
        )
        photo = Photo(
            project_id=project["id"],
            original_path=str(tmp_path / "b.jpg"),
            filename="b.jpg",
            processing_state="processing",
            user_status="Maybe",
            star_rating=3,
        )
        session.add(import_job)
        session.add(processing_job)
        session.add(photo)
        session.commit()
        import_job_id = import_job.id
        processing_job_id = processing_job.id
        photo_id = photo.id

    reset_db_ready_flag()
    ensure_db_ready()

    with Session(get_engine()) as session:
        import_job = session.get(ProcessingJob, import_job_id)
        processing_job = session.get(ProcessingJob, processing_job_id)
        photo = session.get(Photo, photo_id)
        assert import_job is not None
        assert import_job.status == "interrupted"
        assert import_job.current_step == "interrupted - restart"
        assert import_job.interrupted_at is not None
        assert import_job.completed_at is None
        assert import_job.checkpoint_photo_id == "photo-keep"
        # Interrupted imports are not retryable while reclaim can still resume this row
        # (#104 fix 6); retry becomes available again once reclaim/cancel finalizes it.
        assert import_job.retryable is False
        assert processing_job is not None
        assert processing_job.status == "interrupted"
        assert processing_job.current_step == "interrupted - restart"
        assert photo is not None
        assert photo.processing_state == "processing"
        assert photo.user_status == "Maybe"
        assert photo.star_rating == 3
        active = session.exec(select(ProcessingJob).where(ProcessingJob.status.in_(["queued", "running"]))).all()
        assert active == []


def test_reclaim_interrupt_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "true")
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Idempotent interrupt"}).json()

    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            updated_at=datetime.now(UTC),
        )
        session.add(job)
        session.commit()
        job_id = job.id
        assert interrupt_active_jobs_for_reclaim_on_startup(session) == 1
        assert interrupt_active_jobs_for_reclaim_on_startup(session) == 0
        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        assert refreshed.status == "interrupted"


def test_reconcile_helper_respects_reclaim_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Reconcile helper"}).json()

    with Session(get_engine()) as session:
        fail_job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            updated_at=datetime.now(UTC),
        )
        session.add(fail_job)
        session.commit()
        fail_id = fail_job.id
        assert reconcile_active_jobs_on_startup(session, reclaim=False) == 1
        assert session.get(ProcessingJob, fail_id).status == "failed"

        reclaim_job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            updated_at=datetime.now(UTC),
        )
        session.add(reclaim_job)
        session.commit()
        reclaim_id = reclaim_job.id
        assert reconcile_active_jobs_on_startup(session, reclaim=True) == 1
        assert session.get(ProcessingJob, reclaim_id).status == "interrupted"


def test_fail_path_helper_still_available(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Fail helper"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="running",
            current_step="grouping",
            updated_at=datetime.now(UTC),
        )
        session.add(job)
        session.commit()
        assert fail_active_jobs_on_startup(session) == 1
