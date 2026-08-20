from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, select

from app.api import routes
from app.db.session import get_engine
from app.main import create_app, ensure_db_ready, reset_db_ready_flag
from app.models.entities import Photo, ProcessingJob, Project
from app.services import importing
from app.services.jobs import fail_active_jobs_on_startup
from app.services.processing import run_processing_job


def _jpeg_bytes(color: tuple[int, int, int] = (10, 20, 30)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 24), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def _capture_background_tasks(monkeypatch) -> list[tuple[object, tuple, dict]]:
    scheduled: list[tuple[object, tuple, dict]] = []

    def capture_background_task(self, func, *args, **kwargs):
        scheduled.append((func, args, kwargs))

    monkeypatch.setattr(routes.BackgroundTasks, "add_task", capture_background_task)
    return scheduled


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
        active = session.exec(select(ProcessingJob).where(ProcessingJob.status.in_(["queued", "running"]))).all()
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


def test_cancel_then_retry_leaves_no_photo_processing_and_job_is_cancelled(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    scheduled_tasks = _capture_background_tasks(monkeypatch)
    client = TestClient(create_app())
    cancel_client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Cancel then retry"}).json()
    first_bytes = _jpeg_bytes((130, 150, 90))
    second_bytes = _jpeg_bytes((90, 130, 150))
    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[
            ("files", ("first.jpg", first_bytes, "image/jpeg")),
            ("files", ("second.jpg", second_bytes, "image/jpeg")),
        ],
    )
    assert import_response.status_code == 201
    import_result = import_response.json()
    original_job_id = import_result["job"]["id"]
    first_photo_id = import_result["imported"][0]["id"]
    second_photo_id = import_result["imported"][1]["id"]

    with Session(get_engine()) as session:
        first_photo = session.get(Photo, first_photo_id)
        second_photo = session.get(Photo, second_photo_id)
        assert first_photo is not None and second_photo is not None
        first_original = Path(first_photo.project_copy_path or first_photo.original_path)
        second_original = Path(second_photo.project_copy_path or second_photo.original_path)
        first_original_bytes = first_original.read_bytes()
        second_original_bytes = second_original.read_bytes()

    original_process = importing.process_registered_import_photo
    processed_calls = 0

    def cancel_after_first_photo(*args, **kwargs):
        nonlocal processed_calls
        result = original_process(*args, **kwargs)
        processed_calls += 1
        if processed_calls == 1:
            response = cancel_client.post(f"/api/projects/{project['id']}/jobs/{original_job_id}/cancel")
            assert response.status_code == 202
        return result

    monkeypatch.setattr(importing, "process_registered_import_photo", cancel_after_first_photo)
    task, args, kwargs = scheduled_tasks[-1]
    task(*args, **kwargs)

    cancelled_job = client.get(f"/api/projects/{project['id']}/jobs/{original_job_id}").json()
    assert cancelled_job["status"] == "cancelled"
    assert cancelled_job["status"] != "failed"
    assert cancelled_job["retryable"] is True

    with Session(get_engine()) as session:
        assert fail_active_jobs_on_startup(session) == 0
        still_cancelled = session.get(ProcessingJob, original_job_id)
        assert still_cancelled is not None
        assert still_cancelled.status == "cancelled"
        assert still_cancelled.status != "failed"

    retry_response = client.post(f"/api/projects/{project['id']}/jobs/{original_job_id}/retry")
    assert retry_response.status_code == 202
    monkeypatch.setattr(importing, "process_registered_import_photo", original_process)
    task, args, kwargs = scheduled_tasks[-1]
    task(*args, **kwargs)

    photos = client.get(f"/api/projects/{project['id']}/photos").json()
    assert {photo["processing_state"] for photo in photos} == {"imported"}
    assert all(photo["processing_state"] != "processing" for photo in photos)
    assert {photo["id"] for photo in photos} == {first_photo_id, second_photo_id}
    assert first_original.read_bytes() == first_original_bytes
    assert second_original.read_bytes() == second_original_bytes


def test_killed_import_worker_is_failed_retryable_and_photos_leave_processing(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    scheduled_tasks = _capture_background_tasks(monkeypatch)
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Killed import"}).json()
    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[
            ("files", ("done.jpg", _jpeg_bytes((20, 30, 40)), "image/jpeg")),
            ("files", ("stuck.jpg", _jpeg_bytes((40, 50, 60)), "image/jpeg")),
        ],
    )
    assert import_response.status_code == 201
    import_result = import_response.json()
    job_id = import_result["job"]["id"]
    done_id = import_result["imported"][0]["id"]
    stuck_id = import_result["imported"][1]["id"]
    assert scheduled_tasks, "import must schedule the shipped derivative worker"

    with Session(get_engine()) as session:
        done_photo = session.get(Photo, done_id)
        stuck_photo = session.get(Photo, stuck_id)
        job = session.get(ProcessingJob, job_id)
        assert done_photo is not None and stuck_photo is not None and job is not None
        assert job.status == "running"
        stuck_original = Path(stuck_photo.project_copy_path or stuck_photo.original_path)
        stuck_original_bytes = stuck_original.read_bytes()
        thumb = Path(project["root_path"]) / "thumbnails" / "done.webp"
        preview = Path(project["root_path"]) / "previews" / "done.webp"
        thumb.parent.mkdir(parents=True, exist_ok=True)
        preview.parent.mkdir(parents=True, exist_ok=True)
        thumb.write_bytes(b"thumb")
        preview.write_bytes(b"preview")
        done_photo.thumbnail_path = str(thumb)
        done_photo.preview_path = str(preview)
        done_photo.processing_state = "processing"
        session.add(done_photo)
        session.commit()

    reset_db_ready_flag()
    ensure_db_ready()

    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        done_photo = session.get(Photo, done_id)
        stuck_photo = session.get(Photo, stuck_id)
        assert job is not None
        assert job.status == "failed"
        assert job.status != "cancelled"
        assert job.retryable is True
        assert job.current_step == "failed - restart"
        assert done_photo is not None and stuck_photo is not None
        assert done_photo.processing_state != "processing"
        assert stuck_photo.processing_state != "processing"
        processing = session.exec(select(Photo).where(Photo.processing_state == "processing")).all()
        assert processing == []

    retry_response = client.post(f"/api/projects/{project['id']}/jobs/{job_id}/retry")
    assert retry_response.status_code == 202
    task, args, kwargs = scheduled_tasks[-1]
    task(*args, **kwargs)
    photos = client.get(f"/api/projects/{project['id']}/photos").json()
    assert all(photo["processing_state"] != "processing" for photo in photos)
    by_id = {photo["id"]: photo for photo in photos}
    assert by_id[stuck_id]["processing_state"] == "imported"
    assert Path(by_id[stuck_id]["thumbnail_path"]).is_file()
    assert stuck_original.read_bytes() == stuck_original_bytes


def test_processing_job_has_no_cancel_route_and_startup_sweep_resets_photos(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Processing interrupt"}).json()

    with Session(get_engine()) as session:
        photo = Photo(
            project_id=project["id"],
            original_path=str(tmp_path / "frame.jpg"),
            filename="frame.jpg",
            processing_state="processing",
        )
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="running",
            current_step="grouping",
            total_items=1,
            processed_items=0,
            started_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(photo)
        session.add(job)
        session.commit()
        photo_id = photo.id
        job_id = job.id

    denied = client.post(f"/api/projects/{project['id']}/jobs/{job_id}/cancel")
    assert denied.status_code == 422
    assert denied.json()["detail"] == "Only import jobs can be cancelled"

    reset_db_ready_flag()
    ensure_db_ready()

    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        photo = session.get(Photo, photo_id)
        assert job is not None
        assert job.status == "failed"
        assert job.current_step == "failed - restart"
        assert job.retryable is False
        assert photo is not None
        assert photo.processing_state == "imported"
        assert photo.processing_state != "processing"
