import threading
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, select

import app.services.processing as processing_module
from app.api import routes
from app.db.session import get_engine
from app.main import create_app, ensure_db_ready, reset_db_ready_flag
from app.models.entities import Photo, PhotoGroup, ProcessingJob, Project
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


def _wait_for_job(client: TestClient, project_id: str, job: dict) -> dict:
    current = job
    for _ in range(40):
        if current["status"] in {"complete", "complete_with_errors", "failed", "cancelled", "paused"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


def test_concurrent_import_and_status_polling_does_not_lock_database(tmp_path, monkeypatch):
    """Stress WAL/busy_timeout: poll project/job endpoints while an import holds the writer."""
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    import_client = TestClient(create_app())
    polling_client = TestClient(create_app())
    project = import_client.post("/api/projects", json={"name": "Concurrent poll"}).json()

    import_started = threading.Event()
    release_import = threading.Event()
    stop_polling = threading.Event()
    import_result: dict[str, object] = {}
    poll_errors: list[BaseException] = []
    poll_statuses: list[int] = []
    original_register_import_file = routes.register_import_file

    def held_register_import_file(*args, **kwargs):
        import_started.set()
        if not release_import.wait(timeout=15):
            raise RuntimeError("Timed out waiting to release held import")
        return original_register_import_file(*args, **kwargs)

    monkeypatch.setattr(routes, "register_import_file", held_register_import_file)

    def post_import() -> None:
        try:
            import_result["response"] = import_client.post(
                f"/api/projects/{project['id']}/imports",
                files=[
                    ("files", (f"frame-{index}.jpg", _jpeg_bytes((10 + index, 20, 30)), "image/jpeg"))
                    for index in range(4)
                ],
            )
        except Exception as error:  # pragma: no cover - surfaced by assertions below
            import_result["error"] = error

    def _record_lock_failure(response) -> None:
        body = response.text.lower()
        if response.status_code >= 500 or "database is locked" in body:
            poll_errors.append(RuntimeError(f"{response.status_code}: {response.text}"))

    def poll_status() -> None:
        while not stop_polling.is_set():
            try:
                project_response = polling_client.get(f"/api/projects/{project['id']}")
                jobs_response = polling_client.get(f"/api/projects/{project['id']}/jobs")
                poll_statuses.extend([project_response.status_code, jobs_response.status_code])
                _record_lock_failure(project_response)
                _record_lock_failure(jobs_response)
                if project_response.status_code == 200:
                    job = project_response.json().get("active_import_job")
                    if job and job.get("id"):
                        job_response = polling_client.get(f"/api/projects/{project['id']}/jobs/{job['id']}")
                        poll_statuses.append(job_response.status_code)
                        _record_lock_failure(job_response)
            except OperationalError as error:
                poll_errors.append(error)
            except Exception as error:  # pragma: no cover - lock failures may wrap
                if "database is locked" in str(error).lower():
                    poll_errors.append(error)

    import_thread = threading.Thread(target=post_import)
    poll_thread = threading.Thread(target=poll_status)
    import_thread.start()
    try:
        assert import_started.wait(timeout=10)
        poll_thread.start()
        # Hold the writer long enough for many concurrent polls against WAL readers.
        assert not stop_polling.wait(timeout=2.0)
    finally:
        release_import.set()
        import_thread.join(timeout=20)
        stop_polling.set()
        poll_thread.join(timeout=5)

    assert not import_thread.is_alive()
    assert "error" not in import_result, import_result.get("error")
    assert poll_errors == [], poll_errors
    assert len(poll_statuses) >= 20
    assert all(status == 200 for status in poll_statuses)

    response = import_result["response"]
    assert response.status_code == 201
    job = _wait_for_job(polling_client, project["id"], response.json()["job"])
    assert job["status"] in {"complete", "complete_with_errors"}
    assert "database is locked" not in (job.get("error_message") or "").lower()
    assert job["processed_items"] + job["failed_items"] >= 1


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
    # Phase 6.1 (#105): reclaim defaults to on; explicitly disable it to exercise the
    # legacy fail-and-retry startup sweep this test covers.
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "0")
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
    # Phase 6.1 (#105): reclaim defaults to on; explicitly disable it to exercise the
    # legacy fail-and-retry startup sweep this test covers.
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "0")
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


def test_processing_job_cancel_route_accepts_running_job(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Processing cancel"}).json()
    original_path = tmp_path / "frame.jpg"
    original_bytes = _jpeg_bytes()
    original_path.write_bytes(original_bytes)

    with Session(get_engine()) as session:
        photo = Photo(
            project_id=project["id"],
            original_path=str(original_path),
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
        job_id = job.id

    response = client.post(f"/api/projects/{project['id']}/jobs/{job_id}/cancel")
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "running"
    assert body["cancellation_requested"] is True
    assert body["current_step"] == "cancellation_requested"
    assert body["cancelled_at"] is None
    assert original_path.read_bytes() == original_bytes


def test_processing_job_startup_sweep_resets_photos_without_cancel(tmp_path, monkeypatch):
    # Phase 6.1 (#105): reclaim defaults to on; explicitly disable it to exercise the
    # legacy fail-and-retry startup sweep this test covers. A running processing job
    # without a cancel flag still fails and resets photos (J7.01 keeps this coverage).
    monkeypatch.setenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", "0")
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

    reset_db_ready_flag()
    ensure_db_ready()

    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        photo = session.get(Photo, photo_id)
        assert job is not None
        assert job.status == "failed"
        assert job.current_step == "failed - restart"
        assert job.retryable is False
        assert job.cancellation_requested is False
        assert photo is not None
        assert photo.processing_state == "imported"
        assert photo.processing_state != "processing"


def test_running_processing_job_cancels_at_ranking_checkpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    cancel_client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Cancel at ranking"}).json()
    original_bytes = _jpeg_bytes((40, 80, 120))
    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", original_bytes, "image/jpeg"))],
    )
    assert import_response.status_code == 201
    import_job = _wait_for_job(client, project["id"], import_response.json()["job"])
    assert import_job["status"] in {"complete", "complete_with_errors"}
    photo_id = import_response.json()["imported"][0]["id"]
    client.patch(
        f"/api/projects/{project['id']}/photos/{photo_id}",
        json={"user_status": "Pick", "star_rating": 4},
    )

    with Session(get_engine()) as session:
        stored_photo = session.get(Photo, photo_id)
        assert stored_photo is not None
        original_path = Path(stored_photo.project_copy_path or stored_photo.original_path)
        stored_bytes = original_path.read_bytes()

    real_save_job = processing_module._save_job

    def save_job_then_request_cancel_at_ranking(
        session,
        job,
        current_step,
        processed_items=None,
        failed_items=None,
    ):
        result = real_save_job(session, job, current_step, processed_items, failed_items)
        if result is False:
            return result
        if str(current_step).startswith("ranking group") and not job.cancellation_requested:
            response = cancel_client.post(f"/api/projects/{project['id']}/jobs/{job.id}/cancel")
            assert response.status_code == 202
        return result

    monkeypatch.setattr(processing_module, "_save_job", save_job_then_request_cancel_at_ranking)

    process_job = _wait_for_job(
        client,
        project["id"],
        client.post(f"/api/projects/{project['id']}/process").json(),
    )
    assert process_job["status"] == "cancelled"
    assert process_job["status"] != "failed"
    assert process_job["current_step"] == "cancelled"
    assert process_job["cancellation_requested"] is True
    assert process_job["cancelled_at"] is not None
    assert process_job["completed_at"] is not None
    assert process_job["worker_id"] is None
    assert process_job["heartbeat_at"] is None

    project_after = client.get(f"/api/projects/{project['id']}").json()
    assert project_after["processed_images"] == 0
    assert client.get(f"/api/projects/{project['id']}/groups").json() == []

    photo_after = client.get(f"/api/projects/{project['id']}/photos/{photo_id}").json()
    assert photo_after["processing_state"] == "imported"
    assert photo_after["group_id"] is None
    assert photo_after["user_status"] == "Pick"
    assert photo_after["star_rating"] == 4
    assert original_path.read_bytes() == stored_bytes

    with Session(get_engine()) as session:
        assert session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project["id"])).all() == []


def test_run_processing_job_finalizes_queued_cancel_without_process_project(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Queued cancel claim"}).json()
    original_path = tmp_path / "frame.jpg"
    original_bytes = _jpeg_bytes()
    original_path.write_bytes(original_bytes)

    with Session(get_engine()) as session:
        photo = Photo(
            project_id=project["id"],
            original_path=str(original_path),
            project_copy_path=str(original_path),
            filename="frame.jpg",
            processing_state="processing",
            user_status="Maybe",
            star_rating=2,
        )
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="queued",
            current_step="cancellation_requested",
            cancellation_requested=True,
            total_items=1,
        )
        stored_project = session.get(Project, project["id"])
        assert stored_project is not None
        stored_project.total_images = 1
        stored_project.processed_images = 1
        session.add(photo)
        session.add(job)
        session.add(stored_project)
        session.commit()
        job_id = job.id
        photo_id = photo.id

    def boom(*_args, **_kwargs):
        raise AssertionError("process_project must not run after a queued cancel is claimed")

    monkeypatch.setattr(processing_module, "process_project", boom)
    run_processing_job(job_id)

    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        photo = session.get(Photo, photo_id)
        stored_project = session.get(Project, project["id"])
        assert job is not None
        assert job.status == "cancelled"
        assert job.status != "failed"
        assert job.current_step == "cancelled"
        assert job.cancellation_requested is True
        assert job.cancelled_at is not None
        assert job.worker_id is None
        assert photo is not None
        assert photo.processing_state == "imported"
        assert photo.user_status == "Maybe"
        assert photo.star_rating == 2
        assert stored_project is not None
        assert stored_project.processed_images == 0
        assert original_path.read_bytes() == original_bytes


def test_processing_job_pause_route_accepts_running_job(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Processing pause"}).json()
    original_path = tmp_path / "frame.jpg"
    original_bytes = _jpeg_bytes()
    original_path.write_bytes(original_bytes)

    with Session(get_engine()) as session:
        photo = Photo(
            project_id=project["id"],
            original_path=str(original_path),
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
        job_id = job.id

    response = client.post(f"/api/projects/{project['id']}/jobs/{job_id}/pause")
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "running"
    assert body["pause_requested"] is True
    assert body["cancellation_requested"] is False
    assert body["current_step"] == "pause_requested"
    assert body["cancelled_at"] is None
    assert original_path.read_bytes() == original_bytes


def test_running_processing_job_pauses_at_ranking_checkpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    pause_client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Pause at ranking"}).json()
    original_bytes = _jpeg_bytes((40, 80, 120))
    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", original_bytes, "image/jpeg"))],
    )
    assert import_response.status_code == 201
    import_job = _wait_for_job(client, project["id"], import_response.json()["job"])
    assert import_job["status"] in {"complete", "complete_with_errors"}
    photo_id = import_response.json()["imported"][0]["id"]
    client.patch(
        f"/api/projects/{project['id']}/photos/{photo_id}",
        json={"user_status": "Pick", "star_rating": 4},
    )

    with Session(get_engine()) as session:
        stored_photo = session.get(Photo, photo_id)
        assert stored_photo is not None
        original_path = Path(stored_photo.project_copy_path or stored_photo.original_path)
        stored_bytes = original_path.read_bytes()

    real_save_job = processing_module._save_job

    def save_job_then_request_pause_at_ranking(
        session,
        job,
        current_step,
        processed_items=None,
        failed_items=None,
    ):
        result = real_save_job(session, job, current_step, processed_items, failed_items)
        if result is False:
            return result
        if str(current_step).startswith("ranking group") and not job.pause_requested:
            response = pause_client.post(f"/api/projects/{project['id']}/jobs/{job.id}/pause")
            assert response.status_code == 202
        return result

    monkeypatch.setattr(processing_module, "_save_job", save_job_then_request_pause_at_ranking)

    process_job = _wait_for_job(
        client,
        project["id"],
        client.post(f"/api/projects/{project['id']}/process").json(),
    )
    assert process_job["status"] == "paused"
    assert process_job["status"] not in {"cancelled", "failed"}
    assert process_job["current_step"] == "paused"
    assert process_job["pause_requested"] is True
    assert process_job["cancellation_requested"] is False
    assert process_job["cancelled_at"] is None
    assert process_job["completed_at"] is not None
    assert process_job["worker_id"] is None
    assert process_job["heartbeat_at"] is None

    project_after = client.get(f"/api/projects/{project['id']}").json()
    assert project_after["processed_images"] == 0
    assert client.get(f"/api/projects/{project['id']}/groups").json() == []

    photo_after = client.get(f"/api/projects/{project['id']}/photos/{photo_id}").json()
    assert photo_after["processing_state"] == "imported"
    assert photo_after["group_id"] is None
    assert photo_after["user_status"] == "Pick"
    assert photo_after["star_rating"] == 4
    assert original_path.read_bytes() == stored_bytes

    with Session(get_engine()) as session:
        assert session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project["id"])).all() == []


def test_running_processing_job_cancel_wins_over_pause_at_ranking_checkpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    control_client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Cancel wins over pause"}).json()
    original_bytes = _jpeg_bytes((12, 34, 56))
    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", original_bytes, "image/jpeg"))],
    )
    assert import_response.status_code == 201
    import_job = _wait_for_job(client, project["id"], import_response.json()["job"])
    assert import_job["status"] in {"complete", "complete_with_errors"}
    photo_id = import_response.json()["imported"][0]["id"]

    with Session(get_engine()) as session:
        stored_photo = session.get(Photo, photo_id)
        assert stored_photo is not None
        original_path = Path(stored_photo.project_copy_path or stored_photo.original_path)
        stored_bytes = original_path.read_bytes()

    real_save_job = processing_module._save_job

    def save_job_then_request_pause_and_cancel(
        session,
        job,
        current_step,
        processed_items=None,
        failed_items=None,
    ):
        result = real_save_job(session, job, current_step, processed_items, failed_items)
        if result is False:
            return result
        if str(current_step).startswith("ranking group") and not job.pause_requested:
            pause_response = control_client.post(f"/api/projects/{project['id']}/jobs/{job.id}/pause")
            assert pause_response.status_code == 202
            cancel_response = control_client.post(f"/api/projects/{project['id']}/jobs/{job.id}/cancel")
            assert cancel_response.status_code == 202
        return result

    monkeypatch.setattr(processing_module, "_save_job", save_job_then_request_pause_and_cancel)

    process_job = _wait_for_job(
        client,
        project["id"],
        client.post(f"/api/projects/{project['id']}/process").json(),
    )
    assert process_job["status"] == "cancelled"
    assert process_job["status"] != "paused"
    assert process_job["status"] != "failed"
    assert process_job["cancellation_requested"] is True
    assert process_job["cancelled_at"] is not None
    assert original_path.read_bytes() == stored_bytes
    assert client.get(f"/api/projects/{project['id']}/groups").json() == []


def test_run_processing_job_finalizes_queued_pause_without_process_project(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Queued pause claim"}).json()
    original_path = tmp_path / "frame.jpg"
    original_bytes = _jpeg_bytes()
    original_path.write_bytes(original_bytes)

    with Session(get_engine()) as session:
        photo = Photo(
            project_id=project["id"],
            original_path=str(original_path),
            project_copy_path=str(original_path),
            filename="frame.jpg",
            processing_state="processing",
            user_status="Maybe",
            star_rating=2,
        )
        job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="queued",
            current_step="pause_requested",
            pause_requested=True,
            total_items=1,
        )
        stored_project = session.get(Project, project["id"])
        assert stored_project is not None
        stored_project.total_images = 1
        stored_project.processed_images = 1
        session.add(photo)
        session.add(job)
        session.add(stored_project)
        session.commit()
        job_id = job.id
        photo_id = photo.id

    def boom(*_args, **_kwargs):
        raise AssertionError("process_project must not run after a queued pause is claimed")

    monkeypatch.setattr(processing_module, "process_project", boom)
    run_processing_job(job_id)

    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        photo = session.get(Photo, photo_id)
        stored_project = session.get(Project, project["id"])
        assert job is not None
        assert job.status == "paused"
        assert job.status != "cancelled"
        assert job.status != "failed"
        assert job.current_step == "paused"
        assert job.pause_requested is True
        assert job.cancellation_requested is False
        assert job.cancelled_at is None
        assert job.worker_id is None
        assert photo is not None
        assert photo.processing_state == "imported"
        assert photo.user_status == "Maybe"
        assert photo.star_rating == 2
        assert stored_project is not None
        assert stored_project.processed_images == 0
        assert original_path.read_bytes() == original_bytes
