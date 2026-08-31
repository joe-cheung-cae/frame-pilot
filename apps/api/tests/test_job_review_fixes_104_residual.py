"""Tests for the residual GitHub issue #104 findings left after commit 919ae74.

Covers the two remaining fixes:
1. An ``interrupted`` job whose lease claim crashed before the reclaimer finished
   flipping it back to a working status can be left with a foreign, abandoned
   ``worker_id`` forever, since ``job_is_stale`` only looks at active statuses. A later
   reclaimer with a new worker id must still be able to take over once that lease's
   heartbeat has expired.
2. ``group_similar_photos`` is a single CPU-bound call with no per-item progress
   callback; the lease heartbeat must be refreshed immediately before and after the
   call so a concurrent stale sweep cannot fail_stale a still-running processing job.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

import app.services.processing as processing_module
from app.api import routes
from app.core.config import reset_settings_cache
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo, ProcessingJob
from app.services.importing import prepare_interrupted_import_jobs_for_reclaim
from app.services.jobs import (
    JOB_LEASE_STALE_AFTER,
    as_utc,
    job_lease_is_stale,
    release_stale_interrupted_lease,
)
from app.services.processing import prepare_interrupted_processing_jobs_for_reclaim, run_processing_job


def _jpeg_bytes(color: tuple[int, int, int] = (10, 20, 30)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (48, 32), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def _capture_background_tasks(monkeypatch) -> list[tuple[object, tuple, dict]]:
    scheduled: list[tuple[object, tuple, dict]] = []

    def capture_background_task(self, func, *args, **kwargs):
        scheduled.append((func, args, kwargs))

    monkeypatch.setattr(routes.BackgroundTasks, "add_task", capture_background_task)
    return scheduled


def _new_app(tmp_path, monkeypatch, *, reclaim: bool = False) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    if reclaim:
        monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "1")
    else:
        monkeypatch.delenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", raising=False)
    reset_settings_cache()
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Residual fix 1: interrupted job stuck with a foreign, abandoned worker lease
# ---------------------------------------------------------------------------


def test_job_lease_is_stale_ignores_job_status(tmp_path, monkeypatch):
    """Unlike ``job_is_stale``, lease staleness must not depend on ``status``."""
    _new_app(tmp_path, monkeypatch)
    now = datetime.now(UTC)
    stale = ProcessingJob(
        project_id="p",
        job_type="import",
        status="interrupted",
        worker_id="dead-reclaimer",
        heartbeat_at=now - JOB_LEASE_STALE_AFTER - timedelta(seconds=1),
    )
    assert job_lease_is_stale(stale, now=now) is True

    fresh = ProcessingJob(
        project_id="p",
        job_type="import",
        status="interrupted",
        worker_id="live-reclaimer",
        heartbeat_at=now - timedelta(seconds=5),
    )
    assert job_lease_is_stale(fresh, now=now) is False

    unleased = ProcessingJob(project_id="p", job_type="import", status="interrupted", worker_id=None)
    assert job_lease_is_stale(unleased, now=now) is False

    no_heartbeat = ProcessingJob(project_id="p", job_type="import", status="interrupted", worker_id="ghost")
    assert job_lease_is_stale(no_heartbeat, now=now) is True


def test_release_stale_interrupted_lease_clears_expired_foreign_lease(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Release stale lease"}).json()
    stale_heartbeat = datetime.now(UTC) - JOB_LEASE_STALE_AFTER - timedelta(seconds=5)
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            worker_id="dead-reclaimer",
            heartbeat_at=stale_heartbeat,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        released = release_stale_interrupted_lease(session, job)
        assert released.worker_id is None
        assert released.heartbeat_at is None
        assert released.status == "interrupted"

        refreshed = session.get(ProcessingJob, job.id)
        assert refreshed is not None
        assert refreshed.worker_id is None
        assert refreshed.heartbeat_at is None


def test_release_stale_interrupted_lease_noop_when_lease_is_fresh(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Fresh lease noop"}).json()
    fresh_heartbeat = datetime.now(UTC) - timedelta(seconds=5)
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            worker_id="live-reclaimer",
            heartbeat_at=fresh_heartbeat,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        released = release_stale_interrupted_lease(session, job)
        assert released.worker_id == "live-reclaimer"
        assert released.heartbeat_at is not None
        assert as_utc(released.heartbeat_at) == as_utc(fresh_heartbeat)


def test_release_stale_interrupted_lease_noop_for_non_interrupted_status(tmp_path, monkeypatch):
    """Active (queued/running) jobs keep their own staleness handling; this helper must
    not touch them even if their heartbeat looks expired."""
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Active job noop"}).json()
    stale_heartbeat = datetime.now(UTC) - JOB_LEASE_STALE_AFTER - timedelta(seconds=5)
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="running",
            worker_id="worker-a",
            heartbeat_at=stale_heartbeat,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        released = release_stale_interrupted_lease(session, job)
        assert released.worker_id == "worker-a"
        assert released.heartbeat_at is not None


def test_prepare_interrupted_import_reclaim_recovers_from_dead_reclaimer(tmp_path, monkeypatch):
    """A second reclaimer with a new worker id must be able to take over an
    ``interrupted`` import job once the previous (crashed) reclaimer's lease heartbeat
    has expired, even though its ``worker_id`` is still set on the row."""
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Import lease recovery"}).json()
    originals = Path(project["root_path"]) / "originals"
    originals.mkdir(parents=True, exist_ok=True)
    source = originals / "frame.jpg"
    source.write_bytes(_jpeg_bytes())
    stale_heartbeat = datetime.now(UTC) - JOB_LEASE_STALE_AFTER - timedelta(seconds=5)

    with Session(get_engine()) as session:
        photo = Photo(
            project_id=project["id"],
            original_path=str(source),
            project_copy_path=str(source),
            filename="frame.jpg",
            processing_state="processing",
        )
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            # A previous reclaimer claimed this row (worker_id/heartbeat_at set by
            # claim_job_atomic) but crashed before finishing the reclaim, so status
            # never flipped away from "interrupted".
            worker_id="dead-reclaimer",
            heartbeat_at=stale_heartbeat,
            total_items=1,
        )
        session.add(photo)
        session.add(job)
        session.commit()
        job_id = job.id
        photo_id = photo.id

        prepared = prepare_interrupted_import_jobs_for_reclaim(session, worker_id="new-reclaimer")
        assert prepared == [(job_id, [photo_id])]

        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        assert refreshed.status == "running"
        assert refreshed.worker_id == "new-reclaimer"
        assert refreshed.reclaim_count == 1


def test_prepare_interrupted_processing_reclaim_recovers_from_dead_reclaimer(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Processing lease recovery"}).json()
    stale_heartbeat = datetime.now(UTC) - JOB_LEASE_STALE_AFTER - timedelta(seconds=5)

    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            worker_id="dead-reclaimer",
            heartbeat_at=stale_heartbeat,
        )
        session.add(job)
        session.commit()
        job_id = job.id

        prepared = prepare_interrupted_processing_jobs_for_reclaim(session, worker_id="new-reclaimer")
        assert prepared == [job_id]

        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        assert refreshed.status == "queued"
        assert refreshed.worker_id == "new-reclaimer"
        assert refreshed.reclaim_count == 1


def test_prepare_interrupted_reclaim_still_blocked_by_a_fresh_foreign_lease(tmp_path, monkeypatch):
    """Regression guard for #104 fix 2: a foreign lease that has *not* expired yet must
    still block a second reclaimer, e.g. a genuinely concurrent in-flight claim."""
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Fresh lease still blocks"}).json()
    fresh_heartbeat = datetime.now(UTC) - timedelta(seconds=5)

    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            worker_id="live-reclaimer",
            heartbeat_at=fresh_heartbeat,
        )
        session.add(job)
        session.commit()
        job_id = job.id

        prepared = prepare_interrupted_processing_jobs_for_reclaim(session, worker_id="impatient-reclaimer")
        assert prepared == []

        untouched = session.get(ProcessingJob, job_id)
        assert untouched is not None
        assert untouched.status == "interrupted"
        assert untouched.worker_id == "live-reclaimer"


# ---------------------------------------------------------------------------
# Residual fix 2: heartbeat around the long, uncallback'd group_similar_photos call
# ---------------------------------------------------------------------------


def test_group_similar_photos_heartbeat_refreshed_immediately_before_and_after(tmp_path, monkeypatch):
    scheduled = _capture_background_tasks(monkeypatch)
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Grouping heartbeat"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/imports",
        files=[("files", ("one.jpg", _jpeg_bytes((20, 40, 60)), "image/jpeg"))],
    )
    assert import_response.status_code in {201, 202}
    import_func, import_args, _import_kwargs = scheduled[-1]
    import_func(*import_args)

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code in {200, 202}
    job_id = process_response.json()["id"]

    events: list[str] = []
    real_refresh = processing_module.refresh_job_lease_heartbeat
    real_group_similar_photos = processing_module.group_similar_photos

    def spy_refresh(session, job):
        events.append("refresh")
        return real_refresh(session, job)

    def spy_group_similar_photos(group_inputs):
        events.append("group_start")
        result = real_group_similar_photos(group_inputs)
        events.append("group_end")
        return result

    monkeypatch.setattr(processing_module, "refresh_job_lease_heartbeat", spy_refresh)
    monkeypatch.setattr(processing_module, "group_similar_photos", spy_group_similar_photos)

    run_processing_job(job_id)

    with Session(get_engine()) as session:
        finished = session.get(ProcessingJob, job_id)
        assert finished is not None
        assert finished.status == "complete"

    assert "group_start" in events
    assert "group_end" in events
    group_start_index = events.index("group_start")
    group_end_index = events.index("group_end")
    assert events[group_start_index - 1] == "refresh"
    assert events[group_end_index + 1] == "refresh"
