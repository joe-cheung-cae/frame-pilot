"""Tests for GitHub issue #104 (PR #103 review findings: reclaim/lease/cancel).

Covers all six required fixes:
1. Heartbeat during long jobs
2. No duplicate processing between API reclaim and the local worker
3. Preserve cancel intent on reclaim
4. Allow cancel of interrupted imports
5. "interrupted" blocks new import/process workflow
6. Retry vs reclaim race (interrupted is not retryable)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.core.config import reset_settings_cache
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import ProcessingJob
from app.services.importing import (
    prepare_interrupted_import_jobs_for_reclaim,
    run_import_derivative_job,
    update_import_job,
)
from app.services.jobs import (
    JOB_LEASE_STALE_AFTER,
    as_utc,
    claim_job_atomic,
    job_is_stale,
    refresh_job_lease_heartbeat,
)
from app.services.processing import (
    _save_job,
    prepare_interrupted_processing_jobs_for_reclaim,
    run_processing_job,
)
from app.worker import claim_next_queued_processing_job


def _jpeg_bytes(color: tuple[int, int, int] = (10, 20, 30)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 24), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def _new_app(tmp_path, monkeypatch, *, reclaim: bool = False) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    if reclaim:
        monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "1")
    else:
        monkeypatch.delenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", raising=False)
    reset_settings_cache()
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Fix 1: heartbeat during long jobs
# ---------------------------------------------------------------------------


def test_refresh_job_lease_heartbeat_noop_without_worker(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Heartbeat noop"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(project_id=project["id"], job_type="import", status="running")
        session.add(job)
        session.commit()
        session.refresh(job)
        before = job.updated_at
        refresh_job_lease_heartbeat(session, job)
        assert job.heartbeat_at is None
        assert job.updated_at == before


def test_import_progress_updates_refresh_heartbeat_and_prevent_false_stale(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Import heartbeat"}).json()
    stale_heartbeat = datetime.now(UTC) - JOB_LEASE_STALE_AFTER - timedelta(seconds=5)
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            total_items=3,
            worker_id="worker-import",
            heartbeat_at=stale_heartbeat,
            updated_at=stale_heartbeat,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        # A lease that has not been refreshed for over JOB_LEASE_STALE_AFTER looks stale.
        assert job_is_stale(job) is True

        # Simulate ongoing progress from the import loop; each update must refresh the lease.
        update_import_job(session, job, "derivative_generation 1 of 3", 1, 0, force=True)
        assert job.heartbeat_at is not None
        assert as_utc(job.heartbeat_at) > as_utc(stale_heartbeat)
        assert job_is_stale(job) is False


def test_processing_stage_updates_refresh_heartbeat_and_prevent_false_stale(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Processing heartbeat"}).json()
    stale_heartbeat = datetime.now(UTC) - JOB_LEASE_STALE_AFTER - timedelta(seconds=5)
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="running",
            current_step="grouping",
            total_items=2,
            worker_id="worker-process",
            heartbeat_at=stale_heartbeat,
            updated_at=stale_heartbeat,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job_is_stale(job) is True

        _save_job(session, job, "ranking group 1 of 2", 1)
        assert job.heartbeat_at is not None
        assert as_utc(job.heartbeat_at) > as_utc(stale_heartbeat)
        assert job_is_stale(job) is False


def test_unleased_job_progress_updates_do_not_set_heartbeat(tmp_path, monkeypatch):
    """Jobs run directly via BackgroundTasks (no lease) must not gain a heartbeat."""
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "No lease heartbeat"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            total_items=1,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        update_import_job(session, job, "derivative_generation 1 of 1", 1, 0, force=True)
        assert job.worker_id is None
        assert job.heartbeat_at is None


# ---------------------------------------------------------------------------
# Fix 2: no duplicate processing between API reclaim and the local worker
# ---------------------------------------------------------------------------


def test_claim_job_atomic_blocks_a_second_different_owner(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Atomic claim"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(project_id=project["id"], job_type="processing", status="queued")
        session.add(job)
        session.commit()
        job_id = job.id

        # First caller (e.g. the local worker) claims successfully.
        assert claim_job_atomic(session, job_id, worker_id="owner-a", from_statuses=frozenset({"queued"})) is True

        # A second caller with a different identity (e.g. the API's reclaim thread)
        # racing the same row must not also succeed.
        assert claim_job_atomic(session, job_id, worker_id="owner-b", from_statuses=frozenset({"queued"})) is False

        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        assert refreshed.worker_id == "owner-a"


def test_claim_job_atomic_is_idempotent_for_the_same_owner(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Idempotent claim"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(project_id=project["id"], job_type="processing", status="queued")
        session.add(job)
        session.commit()
        job_id = job.id

        assert claim_job_atomic(session, job_id, worker_id="owner-a", from_statuses=frozenset({"queued"})) is True
        assert claim_job_atomic(session, job_id, worker_id="owner-a", from_statuses=frozenset({"queued"})) is True


def test_worker_cannot_claim_job_already_leased_by_another_owner(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Worker vs reclaim"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(project_id=project["id"], job_type="processing", status="queued")
        session.add(job)
        session.commit()
        job_id = job.id

        # Simulate the API's own reclaim thread already owning this queued row.
        assert claim_job_atomic(session, job_id, worker_id="api-reclaim-1", from_statuses=frozenset({"queued"}))

        # A separately running local worker polling for queued work must not claim it too.
        assert claim_next_queued_processing_job(session, worker_id="local-worker-1") is None
        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        assert refreshed.worker_id == "api-reclaim-1"


def test_run_processing_job_refuses_when_leased_by_another_worker(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Run refuses"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(project_id=project["id"], job_type="processing", status="queued", total_items=0)
        session.add(job)
        session.commit()
        job_id = job.id
        # Another executor already holds the lease (e.g. claimed by the local worker).
        claim_job_atomic(session, job_id, worker_id="other-worker", from_statuses=frozenset({"queued"}))

    # The API's own execution path (e.g. BackgroundTasks) must not also run this job.
    run_processing_job(job_id)

    with Session(get_engine()) as session:
        untouched = session.get(ProcessingJob, job_id)
        assert untouched is not None
        assert untouched.worker_id == "other-worker"
        assert untouched.status == "queued"


def test_run_import_derivative_job_refuses_when_leased_by_another_worker(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Run import refuses"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(project_id=project["id"], job_type="import", status="running", total_items=0)
        session.add(job)
        session.commit()
        job_id = job.id
        claim_job_atomic(session, job_id, worker_id="other-worker", from_statuses=frozenset({"running"}))

    run_import_derivative_job(job_id, [], [])

    with Session(get_engine()) as session:
        untouched = session.get(ProcessingJob, job_id)
        assert untouched is not None
        assert untouched.worker_id == "other-worker"
        assert untouched.status == "running"


def test_prepare_interrupted_processing_reclaim_race_only_one_side_wins(tmp_path, monkeypatch):
    """Two concurrent reclaimers (API lifespan vs. local worker) must not both prepare
    the same interrupted processing row (#104 fix 2)."""
    client = _new_app(tmp_path, monkeypatch, reclaim=True)
    project = client.post("/api/projects", json={"name": "Reclaim race"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
        )
        session.add(job)
        session.commit()
        job_id = job.id

        first = prepare_interrupted_processing_jobs_for_reclaim(session, worker_id="api-reclaim")
        second = prepare_interrupted_processing_jobs_for_reclaim(session, worker_id="local-worker")

        assert first == [job_id]
        assert second == []
        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        assert refreshed.worker_id == "api-reclaim"
        assert refreshed.reclaim_count == 1


# ---------------------------------------------------------------------------
# Fix 3: preserve cancel intent on reclaim
# ---------------------------------------------------------------------------


def test_reclaim_finalizes_cancelled_import_instead_of_resuming(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch, reclaim=True)
    project = client.post("/api/projects", json={"name": "Cancel wins over reclaim"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            cancellation_requested=True,
            total_items=1,
        )
        session.add(job)
        session.commit()
        job_id = job.id

        prepared = prepare_interrupted_import_jobs_for_reclaim(session)
        assert prepared == []

        finalized = session.get(ProcessingJob, job_id)
        assert finalized is not None
        assert finalized.status == "cancelled"
        assert finalized.cancellation_requested is True
        assert finalized.cancelled_at is not None
        assert finalized.worker_id is None
        # Cancelled is retryable again: the user is not stuck on a dead row.
        assert finalized.retryable is True


def test_reclaim_resumes_when_cancellation_was_not_requested(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch, reclaim=True)
    project = client.post("/api/projects", json={"name": "Reclaim resumes"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            cancellation_requested=False,
            total_items=0,
        )
        session.add(job)
        session.commit()
        job_id = job.id

        prepared = prepare_interrupted_import_jobs_for_reclaim(session)
        assert prepared == [(job_id, [])]
        resumed = session.get(ProcessingJob, job_id)
        assert resumed is not None
        assert resumed.status == "running"


# ---------------------------------------------------------------------------
# Fix 4: allow cancel of interrupted imports
# ---------------------------------------------------------------------------


def test_cancel_interrupted_import_persists_and_returns_200(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Cancel interrupted"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            total_items=1,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    response = client.post(f"/api/projects/{project['id']}/jobs/{job_id}/cancel")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "cancelled"
    assert body["cancellation_requested"] is True

    # Must be persisted, not a silent no-op: a fresh read shows the same result.
    persisted = client.get(f"/api/projects/{project['id']}/jobs/{job_id}").json()
    assert persisted["status"] == "cancelled"
    assert persisted["cancelled_at"] is not None


def test_cancel_already_terminal_job_is_still_a_200_noop(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Cancel terminal noop"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(project_id=project["id"], job_type="import", status="failed", total_items=1)
        session.add(job)
        session.commit()
        job_id = job.id

    response = client.post(f"/api/projects/{project['id']}/jobs/{job_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "failed"


# ---------------------------------------------------------------------------
# Fix 5: "interrupted" blocks import/process workflow like in-flight work
# ---------------------------------------------------------------------------


def test_interrupted_import_blocks_new_import_request(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Interrupted blocks import"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            total_items=1,
        )
        session.add(job)
        session.commit()

    response = client.post(
        f"/api/projects/{project['id']}/imports",
        files=[("files", ("new.jpg", _jpeg_bytes(), "image/jpeg"))],
    )
    assert response.status_code == 409
    assert "already running" in response.json()["detail"]["message"].lower()


def test_interrupted_import_blocks_new_process_request(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Interrupted blocks process"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            total_items=1,
        )
        session.add(job)
        session.commit()

    response = client.post(f"/api/projects/{project['id']}/process")
    assert response.status_code == 409
    assert "import" in response.json()["detail"]["message"].lower()


def test_interrupted_processing_blocks_new_process_request_without_duplicating(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Interrupted blocks reprocess"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            total_items=1,
        )
        session.add(job)
        session.commit()
        job_id = job.id

    with Session(get_engine()) as session:
        from app.models.entities import Project

        project_row = session.get(Project, project["id"])
        assert project_row is not None
        project_row.total_images = 1
        session.add(project_row)
        session.commit()

    response = client.post(f"/api/projects/{project['id']}/process")
    assert response.status_code == 202
    body = response.json()
    # The endpoint must reuse the existing interrupted row, not spawn a second job.
    assert body["id"] == job_id
    assert body["status"] == "interrupted"

    jobs = client.get(f"/api/projects/{project['id']}/jobs").json()
    processing_jobs = [item for item in jobs if item["job_type"] == "processing"]
    assert len(processing_jobs) == 1


def test_project_read_surfaces_interrupted_import_as_active(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Interrupted visible"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            total_items=1,
        )
        session.add(job)
        session.commit()

    detail = client.get(f"/api/projects/{project['id']}").json()
    assert detail["active_import_job"] is not None
    assert detail["active_import_job"]["status"] == "interrupted"

    listing = client.get("/api/projects").json()
    listed = next(item for item in listing if item["id"] == project["id"])
    assert listed["active_import_job"] is not None
    assert listed["active_import_job"]["status"] == "interrupted"


# ---------------------------------------------------------------------------
# Fix 6: retry vs reclaim race
# ---------------------------------------------------------------------------


def test_interrupted_import_job_is_not_retryable() -> None:
    job = ProcessingJob(project_id="p", job_type="import", status="interrupted")
    assert job.retryable is False


def test_retry_endpoint_refuses_interrupted_import(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Retry refuses interrupted"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            total_items=1,
        )
        session.add(job)
        session.commit()
        job_id = job.id

    response = client.post(f"/api/projects/{project['id']}/jobs/{job_id}/retry")
    assert response.status_code == 409
    assert response.json()["detail"] == "Import job is not in a retryable state"


def test_retry_becomes_available_again_after_reclaim_finalizes_cancel(tmp_path, monkeypatch):
    """Once reclaim (or cancel) finalizes an interrupted job to a terminal status, it is
    retryable again - there is no longer a row reclaim could still resume (#104 fix 6)."""
    client = _new_app(tmp_path, monkeypatch, reclaim=True)
    project = client.post("/api/projects", json={"name": "Retry after finalize"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            cancellation_requested=True,
            total_items=1,
        )
        session.add(job)
        session.commit()
        job_id = job.id

        assert prepare_interrupted_import_jobs_for_reclaim(session) == []
        finalized = session.get(ProcessingJob, job_id)
        assert finalized is not None
        assert finalized.status == "cancelled"

    response = client.post(f"/api/projects/{project['id']}/jobs/{job_id}/retry")
    assert response.status_code == 202
