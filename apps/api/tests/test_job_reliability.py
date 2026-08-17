from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db.session import get_engine
from app.main import create_app, ensure_db_ready, reset_db_ready_flag
from app.models.entities import Photo, ProcessingJob, Project
from app.services import importing
from app.services.jobs import fail_active_jobs_on_startup
from app.services.processing import run_processing_job


def test_import_derivative_worker_marks_job_failed_on_unexpected_exception(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated worker crash")

    monkeypatch.setattr(importing, "process_registered_import_photo", boom)

    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Crash import"}).json()

    buffer = __import__("io").BytesIO()
    from PIL import Image

    Image.new("RGB", (32, 24), color=(10, 20, 30)).save(buffer, format="JPEG")
    response = client.post(
        f"/api/projects/{project['id']}/imports",
        files=[("files", ("crash.jpg", buffer.getvalue(), "image/jpeg"))],
    )
    assert response.status_code == 201
    payload = response.json()
    job_id = payload["job"]["id"]
    photo_id = payload["imported"][0]["id"]

    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        photo = session.get(Photo, photo_id)
        assert job is not None
        assert job.status == "failed"
        assert job.retryable is True
        assert "simulated worker crash" in (job.error_message or "")
        assert photo is not None
        assert photo.processing_state == "failed"


def test_startup_marks_preexisting_active_jobs_failed(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Restart sweep"}).json()

    with Session(get_engine()) as session:
        running_import = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            total_items=2,
            processed_items=1,
            failed_items=0,
            progress_percent=50.0,
            started_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        running_processing = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="queued",
            current_step="queued",
            total_items=2,
            processed_items=0,
            failed_items=0,
            progress_percent=0.0,
            updated_at=datetime.now(UTC),
        )
        session.add(running_import)
        session.add(running_processing)
        session.commit()
        import_job_id = running_import.id
        processing_job_id = running_processing.id

    reset_db_ready_flag()
    ensure_db_ready()

    with Session(get_engine()) as session:
        import_job = session.get(ProcessingJob, import_job_id)
        processing_job = session.get(ProcessingJob, processing_job_id)
        assert import_job is not None and import_job.status == "failed"
        assert import_job.current_step == "failed - restart"
        assert import_job.retryable is True
        assert processing_job is not None and processing_job.status == "failed"
        assert processing_job.current_step == "failed - restart"
        active = session.exec(
            select(ProcessingJob).where(ProcessingJob.status.in_(["queued", "running"]))
        ).all()
        assert active == []


def test_fail_active_jobs_on_startup_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Idempotent sweep"}).json()
    with Session(get_engine()) as session:
        job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="receive_files",
            total_items=1,
            processed_items=0,
            updated_at=datetime.now(UTC),
        )
        session.add(job)
        session.commit()
        job_id = job.id
        assert fail_active_jobs_on_startup(session) == 1
        assert fail_active_jobs_on_startup(session) == 0
        refreshed = session.get(ProcessingJob, job_id)
        assert refreshed is not None
        assert refreshed.status == "failed"


def test_processing_worker_marks_job_failed_on_unexpected_exception(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Crash process"}).json()

    with Session(get_engine()) as session:
        db_project = session.get(Project, project["id"])
        assert db_project is not None
        photo = Photo(
            project_id=project["id"],
            original_path=str(tmp_path / "missing.jpg"),
            filename="missing.jpg",
            processing_state="imported",
        )
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="queued",
            current_step="queued",
            total_items=1,
        )
        session.add(photo)
        session.add(job)
        db_project.total_images = 1
        session.add(db_project)
        session.commit()
        job_id = job.id

    def boom(*_args, **_kwargs):
        raise RuntimeError("processing boom")

    monkeypatch.setattr("app.services.processing.process_project", boom)
    run_processing_job(job_id)

    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        assert job is not None
        assert job.status == "failed"
        assert "processing boom" in (job.error_message or "")


def test_interrupted_export_is_failed_on_startup_and_not_left_running(tmp_path, monkeypatch):
    from datetime import UTC, datetime
    from pathlib import Path

    from app.models.entities import ExportRecord

    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Interrupted export"}).json()

    with Session(get_engine()) as session:
        record = ExportRecord(
            project_id=project["id"],
            mode="zip",
            status="running",
            selected_count=3,
            statuses='["Pick"]',
            output_path=str(Path(project["root_path"]) / "exports" / "zip" / "partial.zip"),
            created_at=datetime.now(UTC),
        )
        Path(record.output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(record.output_path).write_bytes(b"partial")
        session.add(record)
        session.commit()
        export_id = record.id

    reset_db_ready_flag()
    ensure_db_ready()

    with Session(get_engine()) as session:
        refreshed = session.get(ExportRecord, export_id)
        assert refreshed is not None
        assert refreshed.status == "failed"
        assert refreshed.completed_at is not None
        assert "restarted" in (refreshed.error_message or "").lower()
        assert not Path(refreshed.output_path).exists()
