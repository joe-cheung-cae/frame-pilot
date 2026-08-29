"""Tests for local job lease / heartbeat stale detection (Phase 6 / J6.06)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import reset_settings_cache
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import ProcessingJob
from app.services.jobs import (
    JOB_LEASE_STALE_AFTER,
    STALE_JOB_AFTER,
    acquire_job_lease,
    heartbeat_job_lease,
    job_is_stale,
)
from app.worker import claim_next_queued_processing_job


def test_job_is_stale_prefers_lease_heartbeat_over_updated_at(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Lease stale"}).json()
    now = datetime.now(UTC)
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            updated_at=now - STALE_JOB_AFTER - timedelta(minutes=1),
            heartbeat_at=now - timedelta(seconds=30),
            worker_id="worker-a",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        # updated_at is older than 10 minutes, but heartbeat is fresh → not stale.
        assert job_is_stale(job, now=now) is False

        job.heartbeat_at = now - JOB_LEASE_STALE_AFTER - timedelta(seconds=1)
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job_is_stale(job, now=now) is True


def test_job_is_stale_falls_back_to_updated_at_without_lease(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "No lease"}).json()
    now = datetime.now(UTC)
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="running",
            current_step="grouping",
            updated_at=now - STALE_JOB_AFTER - timedelta(seconds=1),
            heartbeat_at=None,
            worker_id=None,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job_is_stale(job, now=now) is True


def test_acquire_and_heartbeat_job_lease(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Acquire lease"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="queued",
            current_step="queued",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        acquire_job_lease(session, job, worker_id="worker-1")
        assert job.worker_id == "worker-1"
        assert job.heartbeat_at is not None
        first_beat = job.heartbeat_at
        heartbeat_job_lease(session, job, worker_id="worker-1")
        assert job.heartbeat_at >= first_beat


def test_claim_queued_job_sets_worker_lease(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Claim lease"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="queued",
            current_step="queued",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = claim_next_queued_processing_job(session, worker_id="worker-claim")
        assert job_id == job.id
        refreshed = session.get(ProcessingJob, job.id)
        assert refreshed is not None
        assert refreshed.worker_id == "worker-claim"
        assert refreshed.heartbeat_at is not None


def test_job_read_exposes_lease_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Lease API"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            worker_id="api-bg",
            heartbeat_at=datetime.now(UTC),
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id
    response = client.get(f"/api/projects/{project['id']}/jobs/{job_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["worker_id"] == "api-bg"
    assert payload["heartbeat_at"] is not None
