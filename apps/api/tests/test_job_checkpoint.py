"""Tests for ProcessingJob durable checkpoint helpers (Phase 6 / J6.01)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import _ensure_processing_job_columns, get_engine
from app.main import create_app
from app.models.entities import ProcessingJob
from app.services.jobs import JobCheckpoint, apply_job_checkpoint, read_job_checkpoint


def test_job_checkpoint_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Checkpoint"}).json()

    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            total_items=3,
            processed_items=1,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

        assert read_job_checkpoint(job) == JobCheckpoint(photo_id=None, stage=None)

        apply_job_checkpoint(
            session,
            job,
            photo_id="photo-abc",
            stage="derivative_generation",
        )
        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        assert read_job_checkpoint(refreshed) == JobCheckpoint(
            photo_id="photo-abc",
            stage="derivative_generation",
        )
        assert refreshed.checkpoint_photo_id == "photo-abc"
        assert refreshed.checkpoint_stage == "derivative_generation"
        assert refreshed.interrupted_at is None
        assert refreshed.reclaim_count == 0


def test_job_read_exposes_checkpoint_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Checkpoint API"}).json()

    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            checkpoint_photo_id="photo-xyz",
            checkpoint_stage="hash_scoring",
            reclaim_count=2,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    response = client.get(f"/api/projects/{project['id']}/jobs/{job_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["checkpoint_photo_id"] == "photo-xyz"
    assert payload["checkpoint_stage"] == "hash_scoring"
    assert payload["interrupted_at"] is None
    assert payload["reclaim_count"] == 2


def test_processing_job_checkpoint_columns_migrate_on_existing_db(tmp_path):
    db_path = Path(tmp_path) / "legacy.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with engine.begin() as connection:
        # Fresh create_all already has model columns; rebuild a minimal pre-J6.01 table.
        connection.execute(text("DROP TABLE IF EXISTS processingjob"))
        connection.execute(
            text(
                """
                CREATE TABLE processingjob (
                    id VARCHAR NOT NULL PRIMARY KEY,
                    project_id VARCHAR NOT NULL,
                    job_type VARCHAR NOT NULL DEFAULT 'processing',
                    status VARCHAR NOT NULL,
                    current_step VARCHAR NOT NULL,
                    total_items INTEGER NOT NULL,
                    processed_items INTEGER NOT NULL,
                    failed_items INTEGER NOT NULL DEFAULT 0,
                    progress_percent FLOAT NOT NULL DEFAULT 0,
                    error_message VARCHAR,
                    cancellation_requested BOOLEAN NOT NULL DEFAULT 0,
                    cancelled_at DATETIME,
                    started_at DATETIME,
                    completed_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )

    _ensure_processing_job_columns(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("processingjob")}
    assert "checkpoint_photo_id" in columns
    assert "checkpoint_stage" in columns
    assert "interrupted_at" in columns
    assert "reclaim_count" in columns

    with Session(engine) as session:
        # Project FK is not enforced for this migration unit test.
        job = ProcessingJob(
            project_id="legacy-project",
            status="queued",
            current_step="queued",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job.checkpoint_photo_id is None
        assert job.checkpoint_stage is None
        assert job.interrupted_at is None
        assert job.reclaim_count == 0
        apply_job_checkpoint(session, job, photo_id="p1", stage="validate")
        assert read_job_checkpoint(job).photo_id == "p1"
        assert read_job_checkpoint(job).stage == "validate"


def test_fail_active_jobs_on_startup_unchanged_by_checkpoint_columns(tmp_path, monkeypatch):
    """J6.01 must not change default restart failure behavior."""
    from app.services.jobs import fail_active_jobs_on_startup

    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Restart default"}).json()

    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            checkpoint_photo_id="photo-keep",
            checkpoint_stage="derivative_generation",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id
        assert fail_active_jobs_on_startup(session) == 1
        failed = session.get(ProcessingJob, job_id)
        assert failed is not None
        assert failed.status == "failed"
        assert failed.current_step == "failed - restart"
        # Checkpoint cursor is retained for future reclaim diagnostics.
        assert failed.checkpoint_photo_id == "photo-keep"
        assert failed.checkpoint_stage == "derivative_generation"
