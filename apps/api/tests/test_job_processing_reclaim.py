"""Tests for reclaim of interrupted processing jobs (Phase 6 / J6.04)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, select

from app.api import routes
from app.core.config import reset_settings_cache
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo, PhotoGroup, ProcessingJob, Project
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


def test_prepare_interrupted_processing_clears_partial_groups(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Prepare process reclaim"}).json()
    originals = Path(project["root_path"]) / "originals"
    originals.mkdir(parents=True, exist_ok=True)
    source = originals / "frame.jpg"
    source.write_bytes(_jpeg_bytes())

    with Session(get_engine()) as session:
        group = PhotoGroup(project_id=project["id"], group_type="burst", photo_count=1)
        session.add(group)
        session.commit()
        session.refresh(group)
        photo = Photo(
            project_id=project["id"],
            original_path=str(source),
            project_copy_path=str(source),
            filename="frame.jpg",
            processing_state="processed",
            group_id=group.id,
            user_status="Pick",
            star_rating=4,
            ai_recommendation="Pick",
        )
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            reclaim_count=0,
        )
        session.add(photo)
        session.add(job)
        session.commit()
        job_id = job.id
        photo_id = photo.id
        group_id = group.id

        prepared = prepare_interrupted_processing_jobs_for_reclaim(session)
        assert prepared == [job_id]
        refreshed = session.get(ProcessingJob, job_id)
        photo = session.get(Photo, photo_id)
        assert refreshed is not None
        assert refreshed.status == "queued"
        assert refreshed.current_step == "reclaim_queued"
        assert refreshed.reclaim_count == 1
        assert photo is not None
        assert photo.group_id is None
        assert photo.processing_state == "imported"
        assert photo.user_status == "Pick"
        assert photo.star_rating == 4
        assert session.get(PhotoGroup, group_id) is None


def test_prepare_interrupted_processing_finalizes_cancel_instead_of_reclaiming(tmp_path, monkeypatch):
    """Interrupted processing with cancellation_requested is cancelled, not re-queued (J7.03)."""
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Cancel wins over process reclaim"}).json()
    originals = Path(project["root_path"]) / "originals"
    originals.mkdir(parents=True, exist_ok=True)
    source = originals / "frame.jpg"
    original_bytes = _jpeg_bytes((12, 34, 56))
    source.write_bytes(original_bytes)
    thumbnail = Path(project["root_path"]) / "thumbnails" / "frame.jpg"
    thumbnail.parent.mkdir(parents=True, exist_ok=True)
    thumbnail_bytes = _jpeg_bytes((90, 80, 70))
    thumbnail.write_bytes(thumbnail_bytes)

    with Session(get_engine()) as session:
        stored_project = session.get(Project, project["id"])
        assert stored_project is not None
        stored_project.processed_images = 1
        stored_project.total_images = 1
        group = PhotoGroup(project_id=project["id"], group_type="burst", photo_count=1)
        session.add(group)
        session.commit()
        session.refresh(group)
        photo = Photo(
            project_id=project["id"],
            original_path=str(source),
            project_copy_path=str(source),
            filename="frame.jpg",
            processing_state="processed",
            group_id=group.id,
            user_status="Pick",
            star_rating=4,
            ai_recommendation="Pick",
            thumbnail_path=str(thumbnail),
        )
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=datetime.now(UTC),
            cancellation_requested=True,
            reclaim_count=2,
        )
        session.add(stored_project)
        session.add(photo)
        session.add(job)
        session.commit()
        job_id = job.id
        photo_id = photo.id
        group_id = group.id

        prepared = prepare_interrupted_processing_jobs_for_reclaim(session)
        assert prepared == []

        refreshed = session.get(ProcessingJob, job_id)
        photo = session.get(Photo, photo_id)
        stored_project = session.get(Project, project["id"])
        assert refreshed is not None
        assert refreshed.status == "cancelled"
        assert refreshed.status not in {"queued", "failed"}
        assert refreshed.current_step == "cancelled"
        assert refreshed.cancellation_requested is True
        assert refreshed.cancelled_at is not None
        assert refreshed.completed_at is not None
        assert refreshed.interrupted_at is None
        assert refreshed.worker_id is None
        assert refreshed.heartbeat_at is None
        assert refreshed.reclaim_count == 2
        assert photo is not None
        assert photo.group_id is None
        assert photo.processing_state == "imported"
        assert photo.user_status == "Pick"
        assert photo.star_rating == 4
        assert photo.thumbnail_path == str(thumbnail)
        assert stored_project is not None
        assert stored_project.processed_images == 0
        assert session.get(PhotoGroup, group_id) is None
        assert source.read_bytes() == original_bytes
        assert thumbnail.read_bytes() == thumbnail_bytes


def test_prepare_interrupted_processing_cancel_does_not_consume_reclaim_limit(tmp_path, monkeypatch):
    """A cancelled interrupted job must not consume the reclaim slot (J7.03)."""
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    cancelled_project = client.post("/api/projects", json={"name": "Cancel first"}).json()
    reclaim_project = client.post("/api/projects", json={"name": "Reclaim second"}).json()
    earlier = datetime.now(UTC) - timedelta(seconds=10)
    later = datetime.now(UTC)

    with Session(get_engine()) as session:
        cancelled_job = ProcessingJob(
            project_id=cancelled_project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=earlier,
            cancellation_requested=True,
            reclaim_count=0,
        )
        reclaim_job = ProcessingJob(
            project_id=reclaim_project["id"],
            job_type="processing",
            status="interrupted",
            current_step="interrupted - restart",
            interrupted_at=later,
            cancellation_requested=False,
            reclaim_count=0,
        )
        session.add(cancelled_job)
        session.add(reclaim_job)
        session.commit()
        cancelled_id = cancelled_job.id
        reclaim_id = reclaim_job.id

        prepared = prepare_interrupted_processing_jobs_for_reclaim(session, limit=1)
        assert prepared == [reclaim_id]

        cancelled = session.get(ProcessingJob, cancelled_id)
        reclaimed = session.get(ProcessingJob, reclaim_id)
        assert cancelled is not None
        assert cancelled.status == "cancelled"
        assert cancelled.reclaim_count == 0
        assert cancelled.id not in prepared
        assert reclaimed is not None
        assert reclaimed.status == "queued"
        assert reclaimed.current_step == "reclaim_queued"
        assert reclaimed.reclaim_count == 1


def test_reclaim_reruns_interrupted_processing_job(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "1")
    reset_settings_cache()
    scheduled = _capture_background_tasks(monkeypatch)
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Process reclaim"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/imports",
        files=[("files", ("one.jpg", _jpeg_bytes((20, 40, 60)), "image/jpeg"))],
    )
    assert import_response.status_code in {201, 202}
    assert "job" in import_response.json()
    assert len(scheduled) >= 1
    import_func, import_args, _import_kwargs = scheduled[-1]
    import_func(*import_args)

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code in {200, 202}
    process_job = process_response.json()
    job_id = process_job["id"]
    process_tasks = [item for item in scheduled if getattr(item[0], "__name__", "") == "run_processing_job"]
    assert process_tasks

    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        assert job is not None
        job.status = "interrupted"
        job.current_step = "interrupted - restart"
        job.interrupted_at = datetime.now(UTC)
        session.add(job)
        photo = session.exec(select(Photo).where(Photo.project_id == project["id"])).first()
        assert photo is not None
        photo.user_status = "Maybe"
        photo.star_rating = 2
        session.add(photo)
        session.commit()
        photo_id = photo.id

        prepared = prepare_interrupted_processing_jobs_for_reclaim(session, worker_id="reclaim-test-worker")
        assert prepared == [job_id]

    run_processing_job(job_id, worker_id="reclaim-test-worker")

    with Session(get_engine()) as session:
        finished = session.get(ProcessingJob, job_id)
        photo = session.get(Photo, photo_id)
        assert finished is not None
        assert finished.status == "complete"
        assert finished.reclaim_count == 1
        assert photo is not None
        assert photo.processing_state == "processed"
        assert photo.user_status == "Maybe"
        assert photo.star_rating == 2
        assert photo.group_id is not None
