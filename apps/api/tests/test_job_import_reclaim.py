"""Tests for in-process reclaim of interrupted import jobs (Phase 6 / J6.03)."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, select

from app.api import routes
from app.core.config import reset_settings_cache
from app.db.session import get_engine
from app.main import create_app, reset_db_ready_flag, start_reclaimable_import_jobs
from app.models.entities import Photo, ProcessingJob
from app.services.importing import prepare_interrupted_import_jobs_for_reclaim, run_import_derivative_job


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


def test_prepare_interrupted_import_reactivates_and_lists_retry_photos(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Prepare reclaim"}).json()
    originals = Path(project["root_path"]) / "originals"
    originals.mkdir(parents=True, exist_ok=True)
    source = originals / "frame.jpg"
    source.write_bytes(_jpeg_bytes())

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
            checkpoint_photo_id=None,
            checkpoint_stage=None,
            reclaim_count=0,
            total_items=1,
            processed_items=0,
        )
        session.add(photo)
        session.add(job)
        session.commit()
        job_id = job.id
        photo_id = photo.id

        prepared = prepare_interrupted_import_jobs_for_reclaim(session)
        assert len(prepared) == 1
        assert prepared[0][0] == job_id
        assert prepared[0][1] == [photo_id]
        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        assert refreshed.status == "running"
        assert refreshed.reclaim_count == 1
        assert refreshed.interrupted_at is None
        assert refreshed.current_step == "reclaim_derivative_generation"


def test_reclaim_completes_interrupted_import_without_reupload(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "1")
    reset_settings_cache()
    scheduled = _capture_background_tasks(monkeypatch)
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Reclaim import"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/imports",
        files=[
            ("files", ("one.jpg", _jpeg_bytes((20, 30, 40)), "image/jpeg")),
            ("files", ("two.jpg", _jpeg_bytes((50, 60, 70)), "image/jpeg")),
        ],
    )
    assert response.status_code in {201, 202}
    payload = response.json()
    job = payload["job"]
    assert len(scheduled) == 1
    assert job["status"] == "running"

    with Session(get_engine()) as session:
        db_job = session.get(ProcessingJob, job["id"])
        assert db_job is not None
        db_job.status = "interrupted"
        db_job.current_step = "interrupted - restart"
        db_job.interrupted_at = datetime.now(UTC)
        db_job.error_message = "simulated restart"
        session.add(db_job)
        photos = list(session.exec(select(Photo).where(Photo.project_id == project["id"])).all())
        assert len(photos) == 2
        copy_paths: list[Path] = []
        mtimes: list[float] = []
        for photo in photos:
            assert photo.processing_state == "processing"
            assert photo.project_copy_path
            path = Path(photo.project_copy_path)
            assert path.is_file()
            copy_paths.append(path)
            mtimes.append(path.stat().st_mtime)
        session.commit()
        job_id = db_job.id
        photo_ids = [photo.id for photo in photos]

        prepared = prepare_interrupted_import_jobs_for_reclaim(session, worker_id="reclaim-test-worker")
        assert prepared == [(job_id, photo_ids)]

    run_import_derivative_job(job_id, photo_ids, [], worker_id="reclaim-test-worker")

    with Session(get_engine()) as session:
        finished = session.get(ProcessingJob, job_id)
        assert finished is not None
        assert finished.status == "complete"
        assert finished.reclaim_count == 1
        assert finished.checkpoint_photo_id in photo_ids
        assert finished.checkpoint_stage == "derivative_generation"
        for photo_id, copy_path, mtime in zip(photo_ids, copy_paths, mtimes, strict=True):
            photo = session.get(Photo, photo_id)
            assert photo is not None
            assert photo.processing_state == "imported"
            assert photo.thumbnail_path and Path(photo.thumbnail_path).is_file()
            assert photo.preview_path and Path(photo.preview_path).is_file()
            assert copy_path.stat().st_mtime == mtime


def test_start_reclaimable_import_jobs_noops_when_flag_off(tmp_path, monkeypatch):
    # Phase 6.1 (#105): reclaim defaults to on; explicitly disable it here.
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "0")
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "No reclaim"}).json()
    with Session(get_engine()) as session:
        session.add(
            ProcessingJob(
                project_id=project["id"],
                job_type="import",
                status="interrupted",
                current_step="interrupted - restart",
                interrupted_at=datetime.now(UTC),
            )
        )
        session.commit()
    assert start_reclaimable_import_jobs() == []


def test_start_reclaimable_import_jobs_runs_by_default_when_flag_unset(tmp_path, monkeypatch):
    """Phase 6.1 (#105): with the env var unset, reclaim scheduling now runs by default."""
    monkeypatch.delenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", raising=False)
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    reset_settings_cache()
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Default reclaim scheduling"}).json()
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

    # The returned targets prove reclaim scheduling ran (flag defaults to on); the
    # scheduled background thread's own completion is covered by other reclaim tests.
    scheduled = start_reclaimable_import_jobs()
    assert scheduled == [(job_id, [])]


def test_lifespan_reclaim_finishes_interrupted_import(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "1")
    reset_settings_cache()
    scheduled = _capture_background_tasks(monkeypatch)
    with TestClient(create_app()) as client:
        project = client.post("/api/projects", json={"name": "Lifespan reclaim"}).json()
        response = client.post(
            f"/api/projects/{project['id']}/imports",
            files=[("files", ("only.jpg", _jpeg_bytes((11, 22, 33)), "image/jpeg"))],
        )
        assert response.status_code in {201, 202}
        payload = response.json()
        job = payload["job"]
        assert len(scheduled) == 1
        job_id = job["id"]
        project_id = project["id"]

        with Session(get_engine()) as session:
            db_job = session.get(ProcessingJob, job_id)
            assert db_job is not None
            db_job.status = "interrupted"
            db_job.current_step = "interrupted - restart"
            db_job.interrupted_at = datetime.now(UTC)
            session.add(db_job)
            session.commit()

    reset_db_ready_flag()
    reset_settings_cache()
    with TestClient(create_app()) as reclaim_client:
        deadline = time.time() + 15
        finished = None
        while time.time() < deadline:
            response = reclaim_client.get(f"/api/projects/{project_id}/jobs/{job_id}")
            assert response.status_code == 200
            finished = response.json()
            if finished["status"] in {"complete", "complete_with_errors", "failed", "cancelled"}:
                break
            time.sleep(0.1)
        assert finished is not None
        assert finished["status"] == "complete"
        assert finished["reclaim_count"] >= 1
