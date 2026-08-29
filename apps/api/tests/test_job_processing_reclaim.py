"""Tests for reclaim of interrupted processing jobs (Phase 6 / J6.04)."""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, select

from app.api import routes
from app.core.config import reset_settings_cache
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo, PhotoGroup, ProcessingJob
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

        prepared = prepare_interrupted_processing_jobs_for_reclaim(session)
        assert prepared == [job_id]

    run_processing_job(job_id)

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
