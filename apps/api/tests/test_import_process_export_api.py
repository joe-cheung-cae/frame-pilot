import csv
import hashlib
import json
import zipfile
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import ExifTags, Image, ImageDraw, ImageFilter
from sqlmodel import Session, select

from app.api import routes
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import ExportRecord, Photo, PhotoGroup, ProcessingJob, Project
from app.services.grouping import SimilarPhotoGroup
from app.services.importing import import_image_file, invalidate_project_processing


def _wait_for_job(client: TestClient, project_id: str, job: dict) -> dict:
    current = job
    for _ in range(20):
        if current["status"] in {"complete", "failed"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


def _image_bytes(color: tuple[int, int, int] = (120, 150, 90), blur: bool = False) -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (96, 72), color=color)
    draw = ImageDraw.Draw(image)
    for offset in range(0, 96, 8):
        draw.line((offset, 0, 95 - offset, 71), fill=(240, 240, 240), width=2)
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(radius=4))
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def _image_bytes_with_exif() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (96, 72), color=(120, 150, 90))
    exif = Image.Exif()
    exif[ExifTags.Base.DateTimeOriginal] = "2026:01:02 03:04:05"
    exif[ExifTags.Base.Model] = "FramePilotCam"
    exif[ExifTags.Base.LensModel] = "FramePilot 35mm"
    exif[ExifTags.Base.FocalLength] = (35, 1)
    exif[ExifTags.Base.FNumber] = (28, 10)
    exif[ExifTags.Base.ExposureTime] = (1, 125)
    exif[ExifTags.Base.ISOSpeedRatings] = 400
    image.save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


def _write_test_derivatives(tmp_path: Path, stem: str) -> tuple[str, str]:
    thumbnail_path = tmp_path / f"{stem}-thumb.webp"
    preview_path = tmp_path / f"{stem}-preview.webp"
    thumbnail_path.write_bytes(b"thumbnail")
    preview_path.write_bytes(b"preview")
    return str(thumbnail_path), str(preview_path)


class ChunkOnlyReader(BytesIO):
    def read(self, size: int = -1) -> bytes:
        if size < 0:
            raise AssertionError("Import should read uploaded files in bounded chunks")
        return super().read(size)


def test_import_process_update_and_export_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Smoke test"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )

    assert import_response.status_code == 201
    import_result = import_response.json()
    assert import_result["skipped"] == []
    photo = import_result["imported"][0]
    assert photo["filename"] == "frame.jpg"
    assert photo["file_ext"] == ".jpg"
    assert photo["file_mtime"] is not None
    assert photo["content_hash"] == hashlib.sha256(_image_bytes()).hexdigest()
    assert photo["source_identity"] == f"sha256:{photo['content_hash']}"
    assert photo["project_copy_path"]
    assert len(photo["perceptual_hash"]) == 16
    assert photo["thumbnail_path"]
    assert photo["preview_path"]
    assert photo["processing_state"] == "imported"
    assert photo["processing_error"] is None
    imported_project = client.get(f"/api/projects/{project['id']}").json()
    assert imported_project["total_images"] == 1
    assert imported_project["processed_images"] == 0

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code == 202
    started_job = process_response.json()
    assert started_job["job_type"] == "processing"
    assert started_job["status"] in {"queued", "complete"}
    job = _wait_for_job(client, project["id"], started_job)
    assert job["status"] == "complete"
    assert job["progress_percent"] == 100.0
    assert job["failed_items"] == 0
    assert job["started_at"] is not None
    assert job["completed_at"] is not None
    processed_project = client.get(f"/api/projects/{project['id']}").json()
    assert processed_project["processed_images"] == 1
    assert processed_project["last_processed_at"] is not None
    processed_photo = client.get(f"/api/projects/{project['id']}/photos/{photo['id']}").json()
    assert processed_photo["processing_state"] == "processed"
    assert processed_photo["processing_error"] is None

    groups = client.get(f"/api/projects/{project['id']}/groups").json()
    assert len(groups) == 1
    assert groups[0]["representative_photo_id"] == photo["id"]
    score_summary = json.loads(groups[0]["score_summary"])
    assert score_summary["confidence"] == "low"
    assert score_summary["top_photo_id"] == photo["id"]
    assert score_summary["recommendation_counts"]["Pick"] == 1

    update_response = client.patch(
        f"/api/projects/{project['id']}/photos/{photo['id']}",
        json={"user_status": "Pick", "star_rating": 5},
    )
    assert update_response.status_code == 200
    assert update_response.json()["user_status"] == "Pick"

    export_response = client.post(
        f"/api/projects/{project['id']}/export",
        json={"mode": "csv", "statuses": ["Pick"]},
    )
    assert export_response.status_code == 201
    export_record = export_response.json()
    assert export_record["output_path"].endswith(".csv")
    assert export_record["selected_count"] == 1
    assert export_record["statuses"] == '["Pick"]'
    assert export_record["completed_at"] is not None
    export_history = client.get(f"/api/projects/{project['id']}/export")
    assert export_history.status_code == 200
    assert [record["id"] for record in export_history.json()] == [export_record["id"]]


def test_import_extracts_basic_exif_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Metadata import"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("metadata.jpg", _image_bytes_with_exif(), "image/jpeg"))],
    )

    assert import_response.status_code == 201
    photo = import_response.json()["imported"][0]
    assert photo["capture_time"] == "2026-01-02T03:04:05"
    assert photo["camera_model"] == "FramePilotCam"
    assert photo["lens_model"] == "FramePilot 35mm"
    assert photo["focal_length"] == "35"
    assert photo["aperture"] == "2.8"
    assert photo["shutter_speed"] == "1/125"
    assert photo["iso"] == 400


def test_plural_import_route_imports_photos(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Plural imports"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/imports",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )

    assert import_response.status_code == 201
    import_result = import_response.json()
    assert import_result["skipped"] == []
    assert import_result["imported"][0]["filename"] == "frame.jpg"
    imported_project = client.get(f"/api/projects/{project['id']}").json()
    assert imported_project["total_images"] == 1
    assert imported_project["processed_images"] == 0


def test_full_local_api_workflow_with_generated_images_and_downloads(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(create_app())
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    sharp_source = source_dir / "sharp.jpg"
    dark_source = source_dir / "dark.jpg"
    unsupported_source = source_dir / "notes.txt"
    sharp_bytes = _image_bytes()
    dark_bytes = _image_bytes(color=(18, 20, 22), blur=True)
    sharp_source.write_bytes(sharp_bytes)
    dark_source.write_bytes(dark_bytes)
    unsupported_source.write_text("not a photo")
    original_source_stat = sharp_source.stat()

    project_response = client.post("/api/projects", json={"name": "Generated workflow"})
    assert project_response.status_code == 201
    project = project_response.json()

    with (
        sharp_source.open("rb") as sharp_file,
        dark_source.open("rb") as dark_file,
        unsupported_source.open(
            "rb",
        ) as unsupported_file,
    ):
        import_response = client.post(
            f"/api/projects/{project['id']}/import",
            files=[
                ("files", ("sharp.jpg", sharp_file, "image/jpeg")),
                ("files", ("dark.jpg", dark_file, "image/jpeg")),
                ("files", ("notes.txt", unsupported_file, "text/plain")),
            ],
        )

    assert import_response.status_code == 201
    import_result = import_response.json()
    assert [item["filename"] for item in import_result["imported"]] == ["sharp.jpg", "dark.jpg"]
    assert import_result["skipped"] == [
        {
            "filename": "notes.txt",
            "reason": "Only JPEG, PNG, and WebP files are supported",
        },
    ]
    assert sharp_source.read_bytes() == sharp_bytes
    assert sharp_source.stat().st_mtime_ns == original_source_stat.st_mtime_ns

    imported_photo = import_result["imported"][0]
    with Session(get_engine()) as session:
        stored_photo = session.get(Photo, imported_photo["id"])
        assert stored_photo is not None
        imported_original = Path(stored_photo.original_path)
        imported_copy_path = Path(stored_photo.project_copy_path)
    assert imported_original != sharp_source
    assert imported_copy_path == imported_original
    assert imported_original.read_bytes() == sharp_bytes
    assert imported_photo["content_hash"] == hashlib.sha256(sharp_bytes).hexdigest()
    assert imported_photo["source_identity"] == f"sha256:{imported_photo['content_hash']}"
    assert Path(imported_photo["thumbnail_path"]).exists()
    assert Path(imported_photo["preview_path"]).exists()

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code == 202
    job = _wait_for_job(client, project["id"], process_response.json())
    assert job["status"] == "complete"
    assert job["current_step"] == "complete"
    assert job["processed_items"] == 2
    assert job["total_items"] == 2
    assert job["failed_items"] == 0
    assert job["progress_percent"] == 100.0
    assert job["error_message"] is None

    photos = client.get(f"/api/projects/{project['id']}/photos").json()
    assert len(photos) == 2
    assert all(photo["group_id"] for photo in photos)
    assert all(photo["processing_state"] == "processed" for photo in photos)
    assert all(photo["processing_error"] is None for photo in photos)
    groups = client.get(f"/api/projects/{project['id']}/groups").json()
    assert groups
    assert sum(group["photo_count"] for group in groups) == 2

    pick_response = client.patch(
        f"/api/projects/{project['id']}/photos/{photos[0]['id']}",
        json={"user_status": "Pick", "star_rating": 4},
    )
    assert pick_response.status_code == 200
    assert pick_response.json()["user_status"] == "Pick"

    csv_export_response = client.post(
        f"/api/projects/{project['id']}/export",
        json={"mode": "csv", "statuses": ["Pick"]},
    )
    assert csv_export_response.status_code == 201
    csv_export = csv_export_response.json()
    assert csv_export["selected_count"] == 1
    csv_path = Path(csv_export["output_path"])
    assert csv_path.parent == Path(project["root_path"]) / "exports" / "csv"
    assert csv_path.exists()
    with csv_path.open(newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert [row["status"] for row in csv_rows] == ["Pick"]

    csv_download_response = client.get(f"/api/projects/{project['id']}/export/{csv_export['id']}/download")
    assert csv_download_response.status_code == 200
    assert "filename" in csv_download_response.headers["content-disposition"]
    assert b"filename,original_path,capture_time,camera_model,lens_model" in csv_download_response.content

    zip_export_response = client.post(
        f"/api/projects/{project['id']}/export",
        json={"mode": "zip", "statuses": ["Pick"]},
    )
    assert zip_export_response.status_code == 201
    zip_export = zip_export_response.json()
    zip_path = Path(zip_export["output_path"])
    assert zip_path.parent == Path(project["root_path"]) / "exports" / "zip"
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.namelist() == [photos[0]["filename"]]

    zip_download_response = client.get(f"/api/projects/{project['id']}/export/{zip_export['id']}/download")
    assert zip_download_response.status_code == 200
    assert zip_download_response.content == zip_path.read_bytes()

    folder_export_response = client.post(
        f"/api/projects/{project['id']}/export",
        json={"mode": "folder", "statuses": ["Pick"]},
    )
    assert folder_export_response.status_code == 201
    folder_path = Path(folder_export_response.json()["output_path"])
    assert folder_path.parent == Path(project["root_path"]) / "exports" / "folders"
    assert folder_path.is_dir()
    folder_download_response = client.get(
        f"/api/projects/{project['id']}/export/{folder_export_response.json()['id']}/download",
    )
    assert folder_download_response.status_code == 422


def test_import_copies_uploaded_file_in_bounded_chunks(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Chunked import"}).json()
    image = _image_bytes()

    with Session(get_engine()) as session:
        stored_project = session.get(Project, project["id"])
        assert stored_project is not None
        photo = import_image_file(session, stored_project, "chunked.jpg", ChunkOnlyReader(image))

    assert Path(photo.original_path).read_bytes() == image


def test_plural_export_routes_create_list_get_and_download(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Plural exports"}).json()
    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    photo = import_response.json()["imported"][0]
    client.patch(
        f"/api/projects/{project['id']}/photos/{photo['id']}",
        json={"user_status": "Pick"},
    )

    create_response = client.post(f"/api/projects/{project['id']}/exports", json={"mode": "csv", "statuses": ["Pick"]})

    assert create_response.status_code == 201
    export_record = create_response.json()
    list_response = client.get(f"/api/projects/{project['id']}/exports")
    assert list_response.status_code == 200
    assert [record["id"] for record in list_response.json()] == [export_record["id"]]
    get_response = client.get(f"/api/projects/{project['id']}/exports/{export_record['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == export_record["id"]
    download_response = client.get(f"/api/projects/{project['id']}/exports/{export_record['id']}/download")
    assert download_response.status_code == 200
    assert b"filename,original_path,capture_time,camera_model,lens_model" in download_response.content


def test_export_history_supports_newest_first_pagination(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Paged export history"}).json()
    base_time = datetime(2026, 1, 1, tzinfo=UTC)

    with Session(get_engine()) as session:
        records = [
            ExportRecord(
                id=f"export-{index}",
                project_id=project["id"],
                mode="csv",
                status="complete",
                selected_count=index,
                statuses='["Pick"]',
                output_path=str(tmp_path / f"selection-{index}.csv"),
                created_at=base_time + timedelta(minutes=index),
            )
            for index in range(5)
        ]
        session.add_all(records)
        session.commit()

    full_response = client.get(f"/api/projects/{project['id']}/exports")
    page_response = client.get(f"/api/projects/{project['id']}/exports?limit=2&offset=1")

    assert full_response.status_code == 200
    assert [record["id"] for record in full_response.json()] == [
        "export-4",
        "export-3",
        "export-2",
        "export-1",
        "export-0",
    ]
    assert page_response.status_code == 200
    assert [record["id"] for record in page_response.json()] == ["export-3", "export-2"]


def test_multi_file_import_invalidates_processing_once(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    invalidate_calls = 0

    def counted_invalidation(session, project):
        nonlocal invalidate_calls
        invalidate_calls += 1
        invalidate_project_processing(session, project)

    monkeypatch.setattr("app.api.routes.invalidate_project_processing", counted_invalidation)
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Batch import invalidation"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[
            ("files", ("first.jpg", _image_bytes(), "image/jpeg")),
            ("files", ("second.jpg", _image_bytes(color=(40, 80, 120)), "image/jpeg")),
        ],
    )

    assert response.status_code == 201
    assert len(response.json()["imported"]) == 2
    assert invalidate_calls == 1
    updated_project = client.get(f"/api/projects/{project['id']}").json()
    assert updated_project["total_images"] == 2
    assert updated_project["processed_images"] == 0


def test_process_rejects_project_with_no_imported_photos(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Empty process"}).json()

    response = client.post(f"/api/projects/{project['id']}/process")

    assert response.status_code == 422
    assert "Import photos before processing" in response.text
    with Session(get_engine()) as session:
        jobs = list(session.exec(select(ProcessingJob).where(ProcessingJob.project_id == project["id"])).all())
    assert jobs == []
    assert client.get(f"/api/projects/{project['id']}").json()["processed_images"] == 0


def test_process_returns_existing_active_job_without_creating_duplicate(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Active job"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    assert import_response.status_code == 201

    with Session(get_engine()) as session:
        active_job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="running",
            current_step="grouping photos",
            total_items=1,
        )
        session.add(active_job)
        session.commit()
        active_job_id = active_job.id

    response = client.post(f"/api/projects/{project['id']}/process")

    assert response.status_code == 202
    assert response.json()["id"] == active_job_id
    with Session(get_engine()) as session:
        jobs = list(session.exec(select(ProcessingJob).where(ProcessingJob.project_id == project["id"])).all())
    assert len(jobs) == 1


def test_list_jobs_returns_project_jobs_newest_first(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Job history"}).json()
    other_project = client.post("/api/projects", json={"name": "Other job history"}).json()

    with Session(get_engine()) as session:
        older_job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="complete",
            current_step="complete",
            created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
        )
        newer_job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="failed",
            current_step="failed",
            created_at=datetime(2026, 1, 1, 11, 0, 0, tzinfo=UTC),
        )
        newest_job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="complete",
            current_step="complete",
            created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        )
        other_job = ProcessingJob(project_id=other_project["id"], job_type="processing", status="running")
        session.add(older_job)
        session.add(newer_job)
        session.add(newest_job)
        session.add(other_job)
        session.commit()
        older_job_id = older_job.id
        newer_job_id = newer_job.id
        newest_job_id = newest_job.id

    response = client.get(f"/api/projects/{project['id']}/jobs")
    page_response = client.get(f"/api/projects/{project['id']}/jobs?limit=1&offset=1")

    assert response.status_code == 200
    assert [job["id"] for job in response.json()] == [newest_job_id, newer_job_id, older_job_id]
    assert page_response.status_code == 200
    assert [job["id"] for job in page_response.json()] == [newer_job_id]


def test_process_fails_stale_active_job_and_starts_replacement(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(routes, "run_processing_job", lambda _job_id: None)
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Stale active job"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    assert import_response.status_code == 201
    photo_id = import_response.json()["imported"][0]["id"]
    stale_time = datetime.now(UTC) - timedelta(hours=1)

    with Session(get_engine()) as session:
        stale_job = ProcessingJob(
            project_id=project["id"],
            job_type="processing",
            status="running",
            current_step="ranking group 1 of 1",
            total_items=1,
            updated_at=stale_time,
        )
        photo = session.get(Photo, photo_id)
        assert photo is not None
        photo.processing_state = "processing"
        session.add(stale_job)
        session.add(photo)
        session.commit()
        stale_job_id = stale_job.id

    response = client.post(f"/api/projects/{project['id']}/process")

    assert response.status_code == 202
    replacement_job = response.json()
    assert replacement_job["id"] != stale_job_id
    assert replacement_job["status"] == "queued"
    with Session(get_engine()) as session:
        jobs = list(session.exec(select(ProcessingJob).where(ProcessingJob.project_id == project["id"])).all())
        stale_after_retry = session.get(ProcessingJob, stale_job_id)
        photo_after_retry = session.get(Photo, photo_id)

    assert len(jobs) == 2
    assert stale_after_retry is not None
    assert stale_after_retry.status == "failed"
    assert stale_after_retry.current_step == "failed - stale"
    assert stale_after_retry.error_message == "Processing job was interrupted before completion"
    assert photo_after_retry is not None
    assert photo_after_retry.processing_state == "imported"
    assert photo_after_retry.processing_error == "Processing job was interrupted before completion"


def test_process_skips_unchanged_project_without_rebuilding_groups(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Already processed"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    assert import_response.status_code == 201

    first_job = _wait_for_job(client, project["id"], client.post(f"/api/projects/{project['id']}/process").json())
    assert first_job["status"] == "complete"
    first_groups = client.get(f"/api/projects/{project['id']}/groups").json()
    assert len(first_groups) == 1
    first_last_processed_at = client.get(f"/api/projects/{project['id']}").json()["last_processed_at"]

    second_job = _wait_for_job(client, project["id"], client.post(f"/api/projects/{project['id']}/process").json())

    assert second_job["status"] == "complete"
    assert second_job["current_step"] == "complete - no changes"
    assert second_job["processed_items"] == 1
    assert second_job["failed_items"] == 0
    assert second_job["progress_percent"] == 100.0
    assert client.get(f"/api/projects/{project['id']}/groups").json() == first_groups
    assert client.get(f"/api/projects/{project['id']}").json()["last_processed_at"] == first_last_processed_at


def test_processing_can_recover_after_failed_job(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Recover processing"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    assert import_response.status_code == 201
    photo_id = import_response.json()["imported"][0]["id"]

    def fail_grouping(_inputs):
        raise RuntimeError("grouping interrupted")

    with monkeypatch.context() as failure_patch:
        failure_patch.setattr("app.services.processing.group_similar_photos", fail_grouping)
        failed_job = _wait_for_job(client, project["id"], client.post(f"/api/projects/{project['id']}/process").json())

    assert failed_job["status"] == "failed"
    assert failed_job["current_step"] == "failed"
    assert "grouping interrupted" in failed_job["error_message"]
    interrupted_photo = client.get(f"/api/projects/{project['id']}/photos/{photo_id}").json()
    assert interrupted_photo["processing_state"] == "imported"
    assert interrupted_photo["processing_error"] == "grouping interrupted"
    assert "Processing was interrupted" in interrupted_photo["recommendation_explanation"]

    recovered_job = _wait_for_job(client, project["id"], client.post(f"/api/projects/{project['id']}/process").json())

    assert recovered_job["status"] == "complete"
    assert recovered_job["processed_items"] == 1
    assert recovered_job["failed_items"] == 0
    recovered_photo = client.get(f"/api/projects/{project['id']}/photos/{photo_id}").json()
    assert recovered_photo["processing_state"] == "processed"
    assert recovered_photo["processing_error"] is None
    assert len(client.get(f"/api/projects/{project['id']}/groups").json()) == 1


def test_processing_skips_photo_with_invalid_similarity_data(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Invalid similarity data"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("valid.jpg", _image_bytes(), "image/jpeg"))],
    )
    assert import_response.status_code == 201

    with Session(get_engine()) as session:
        stored_project = session.get(Project, project["id"])
        assert stored_project is not None
        invalid_thumbnail, invalid_preview = _write_test_derivatives(tmp_path, "invalid")
        invalid_photo = Photo(
            project_id=project["id"],
            original_path=str(tmp_path / "missing.jpg"),
            filename="invalid.jpg",
            thumbnail_path=invalid_thumbnail,
            preview_path=invalid_preview,
            embedding="{not-json",
        )
        session.add(invalid_photo)
        stored_project.total_images += 1
        session.add(stored_project)
        session.commit()
        invalid_photo_id = invalid_photo.id

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code == 202
    job = _wait_for_job(client, project["id"], process_response.json())

    assert job["status"] == "complete"
    assert job["processed_items"] == 1
    assert job["failed_items"] == 1
    assert job["progress_percent"] == 100.0
    assert "1 photo could not be processed" in job["error_message"]
    assert client.get(f"/api/projects/{project['id']}").json()["processed_images"] == 1
    groups = client.get(f"/api/projects/{project['id']}/groups").json()
    assert sum(group["photo_count"] for group in groups) == 1
    invalid_after_processing = client.get(f"/api/projects/{project['id']}/photos/{invalid_photo_id}").json()
    assert invalid_after_processing["processing_state"] == "failed"
    assert invalid_after_processing["processing_error"] == "Stored similarity data is invalid"
    assert "stored similarity data is invalid" in invalid_after_processing["recommendation_explanation"]


def test_processing_regenerates_missing_generated_derivative(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Missing derivative"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    assert import_response.status_code == 201
    photo = import_response.json()["imported"][0]
    old_thumbnail_path = Path(photo["thumbnail_path"])
    old_preview_path = Path(photo["preview_path"])
    Path(photo["thumbnail_path"]).unlink()

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code == 202
    job = _wait_for_job(client, project["id"], process_response.json())

    assert job["status"] == "complete"
    assert job["processed_items"] == 1
    assert job["failed_items"] == 0
    assert job["progress_percent"] == 100.0
    assert job["error_message"] is None
    assert client.get(f"/api/projects/{project['id']}").json()["processed_images"] == 1
    processed_photo = client.get(f"/api/projects/{project['id']}/photos/{photo['id']}").json()
    assert processed_photo["processing_state"] == "processed"
    assert processed_photo["processing_error"] is None
    assert Path(processed_photo["thumbnail_path"]).exists()
    assert Path(processed_photo["thumbnail_path"]) == old_thumbnail_path
    assert Path(processed_photo["preview_path"]) == old_preview_path


def test_processing_records_missing_derivative_when_original_copy_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Missing original copy"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    assert import_response.status_code == 201
    photo = import_response.json()["imported"][0]
    Path(photo["thumbnail_path"]).unlink()
    Path(photo["project_copy_path"]).unlink()

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code == 202
    job = _wait_for_job(client, project["id"], process_response.json())

    assert job["status"] == "complete"
    assert job["processed_items"] == 0
    assert job["failed_items"] == 1
    assert "1 photo could not be processed" in job["error_message"]
    failed_photo = client.get(f"/api/projects/{project['id']}/photos/{photo['id']}").json()
    assert failed_photo["processing_state"] == "failed"
    assert failed_photo["processing_error"] == "Missing generated thumbnail"
    assert "generated files could not be rebuilt" in failed_photo["recommendation_explanation"]


def test_import_renames_duplicate_filenames_without_overwriting(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Duplicate names"}).json()

    first = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    second = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )

    assert first.status_code == 201
    assert second.status_code == 201
    filenames = [first.json()["imported"][0]["filename"], second.json()["imported"][0]["filename"]]
    assert filenames == ["frame.jpg", "frame-1.jpg"]

    root = Path(project["root_path"])
    assert (root / "originals" / "frame.jpg").exists()
    assert (root / "originals" / "frame-1.jpg").exists()
    assert (root / "thumbnails" / "frame.webp").exists()
    assert (root / "thumbnails" / "frame-1.webp").exists()


def test_import_after_processing_invalidates_stale_groups_and_recommendations(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Re-import"}).json()

    first_import = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("first.jpg", _image_bytes(), "image/jpeg"))],
    )
    first_photo = first_import.json()["imported"][0]
    process_response = client.post(f"/api/projects/{project['id']}/process")

    assert process_response.status_code == 202
    job = _wait_for_job(client, project["id"], process_response.json())
    assert job["status"] == "complete"
    assert client.get(f"/api/projects/{project['id']}/groups").json()
    assert client.get(f"/api/projects/{project['id']}/photos/{first_photo['id']}").json()["ai_recommendation"] == "Pick"

    second_import = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("second.jpg", _image_bytes(), "image/jpeg"))],
    )

    assert second_import.status_code == 201
    updated_project = client.get(f"/api/projects/{project['id']}").json()
    assert updated_project["total_images"] == 2
    assert updated_project["processed_images"] == 0
    assert updated_project["last_processed_at"] is not None
    assert client.get(f"/api/projects/{project['id']}/groups").json() == []
    updated_first = client.get(f"/api/projects/{project['id']}/photos/{first_photo['id']}").json()
    assert updated_first["group_id"] is None
    assert updated_first["ai_recommendation"] == "Unreviewed"


def test_group_list_returns_groups_in_creation_order(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Group order"}).json()

    with Session(get_engine()) as session:
        second = PhotoGroup(project_id=project["id"], photo_count=2)
        first = PhotoGroup(project_id=project["id"], photo_count=1)
        third = PhotoGroup(project_id=project["id"], photo_count=3)
        session.add(second)
        session.add(first)
        session.add(third)
        session.commit()

    groups = client.get(f"/api/projects/{project['id']}/groups").json()

    assert [group["photo_count"] for group in groups] == [2, 1, 3]

    page = client.get(f"/api/projects/{project['id']}/groups?limit=1&offset=1").json()

    assert [group["id"] for group in page] == [groups[1]["id"]]


def test_photo_list_prioritizes_recommended_and_high_scoring_photos(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Photo order"}).json()

    with Session(get_engine()) as session:
        group = PhotoGroup(project_id=project["id"], photo_count=3)
        session.add(group)
        session.commit()
        session.refresh(group)
        photos = [
            Photo(
                project_id=project["id"],
                original_path="/tmp/reject.jpg",
                filename="reject.jpg",
                group_id=group.id,
                ai_recommendation="Reject",
                overall_score=0.99,
            ),
            Photo(
                project_id=project["id"],
                original_path="/tmp/maybe.jpg",
                filename="maybe.jpg",
                group_id=group.id,
                ai_recommendation="Maybe",
                overall_score=0.8,
            ),
            Photo(
                project_id=project["id"],
                original_path="/tmp/pick.jpg",
                filename="pick.jpg",
                group_id=group.id,
                ai_recommendation="Pick",
                overall_score=0.7,
            ),
        ]
        session.add_all(photos)
        session.commit()

    response = client.get(f"/api/projects/{project['id']}/photos")

    assert response.status_code == 200
    assert [photo["filename"] for photo in response.json()] == ["pick.jpg", "maybe.jpg", "reject.jpg"]


def test_photo_status_counts_include_zeroes_and_exclude_other_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Status counts"}).json()
    other_project = client.post("/api/projects", json={"name": "Other status counts"}).json()

    with Session(get_engine()) as session:
        photos = [
            Photo(project_id=project["id"], original_path="/tmp/pick-a.jpg", filename="pick-a.jpg", user_status="Pick"),
            Photo(project_id=project["id"], original_path="/tmp/pick-b.jpg", filename="pick-b.jpg", user_status="Pick"),
            Photo(project_id=project["id"], original_path="/tmp/maybe.jpg", filename="maybe.jpg", user_status="Maybe"),
            Photo(
                project_id=other_project["id"],
                original_path="/tmp/other-reject.jpg",
                filename="other-reject.jpg",
                user_status="Reject",
            ),
        ]
        session.add_all(photos)
        session.commit()

    response = client.get(f"/api/projects/{project['id']}/photos/status-counts")

    assert response.status_code == 200
    assert response.json() == {"Pick": 2, "Maybe": 1, "Reject": 0, "Unreviewed": 0}


def test_photo_update_rejects_empty_patch(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Empty patch"}).json()

    with Session(get_engine()) as session:
        photo = Photo(project_id=project["id"], original_path="/tmp/frame.jpg", filename="frame.jpg")
        session.add(photo)
        session.commit()
        photo_id = photo.id

    response = client.patch(f"/api/projects/{project['id']}/photos/{photo_id}", json={})

    assert response.status_code == 422
    unchanged = client.get(f"/api/projects/{project['id']}/photos/{photo_id}").json()
    assert unchanged["user_status"] == "Unreviewed"
    assert unchanged["star_rating"] == 0


def test_batch_photo_update_changes_requested_project_photos(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Batch status"}).json()

    with Session(get_engine()) as session:
        photos = [
            Photo(project_id=project["id"], original_path="/tmp/first.jpg", filename="first.jpg"),
            Photo(project_id=project["id"], original_path="/tmp/second.jpg", filename="second.jpg"),
        ]
        session.add_all(photos)
        session.commit()
        photo_ids = [photo.id for photo in photos]

    response = client.patch(
        f"/api/projects/{project['id']}/photos/batch",
        json={"photo_ids": photo_ids, "user_status": "Reject", "star_rating": 2},
    )

    assert response.status_code == 200
    updated = response.json()
    assert [photo["id"] for photo in updated] == photo_ids
    assert {photo["user_status"] for photo in updated} == {"Reject"}
    assert {photo["star_rating"] for photo in updated} == {2}


def test_batch_photo_update_rejects_missing_project_photo_without_partial_update(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Batch source"}).json()
    other_project = client.post("/api/projects", json={"name": "Batch other"}).json()

    with Session(get_engine()) as session:
        project_photo = Photo(project_id=project["id"], original_path="/tmp/project.jpg", filename="project.jpg")
        other_photo = Photo(project_id=other_project["id"], original_path="/tmp/other.jpg", filename="other.jpg")
        session.add_all([project_photo, other_photo])
        session.commit()
        project_photo_id = project_photo.id
        other_photo_id = other_photo.id

    response = client.patch(
        f"/api/projects/{project['id']}/photos/batch",
        json={"photo_ids": [project_photo_id, other_photo_id], "user_status": "Pick"},
    )

    assert response.status_code == 404
    assert "Photo not found" in response.text
    assert client.get(f"/api/projects/{project['id']}/photos/{project_photo_id}").json()["user_status"] == "Unreviewed"


def test_processing_recommendation_explains_face_and_eye_quality(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Face ranking"}).json()

    with Session(get_engine()) as session:
        face_thumbnail, face_preview = _write_test_derivatives(tmp_path, "face")
        plain_thumbnail, plain_preview = _write_test_derivatives(tmp_path, "plain")
        photos = [
            Photo(
                project_id=project["id"],
                original_path="/tmp/face.jpg",
                filename="face.jpg",
                thumbnail_path=face_thumbnail,
                preview_path=face_preview,
                sharpness_score=0.4,
                exposure_score=0.4,
                face_presence=True,
                face_quality_score=1.0,
                eye_open_confidence=0.85,
                aesthetic_score=0.4,
                embedding="[1, 0]",
            ),
            Photo(
                project_id=project["id"],
                original_path="/tmp/plain.jpg",
                filename="plain.jpg",
                thumbnail_path=plain_thumbnail,
                preview_path=plain_preview,
                sharpness_score=0.45,
                exposure_score=0.45,
                face_quality_score=0.0,
                aesthetic_score=0.45,
                embedding="[0, 1]",
            ),
        ]
        session.add_all(photos)
        project_model = session.get(Project, project["id"])
        assert project_model is not None
        project_model.total_images = 2
        session.add(project_model)
        session.commit()

    response = client.post(f"/api/projects/{project['id']}/process")

    assert response.status_code == 202
    processed = client.get(f"/api/projects/{project['id']}/photos").json()
    face_photo = next(photo for photo in processed if photo["filename"] == "face.jpg")
    assert face_photo["ai_recommendation"] == "Pick"
    assert "experimental face and open-eye signals" in face_photo["recommendation_explanation"]


def test_processing_passes_lens_metadata_to_grouping(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Lens grouping payload"}).json()
    captured_inputs = []

    with Session(get_engine()) as session:
        thumbnail_path, preview_path = _write_test_derivatives(tmp_path, "lens")
        photo = Photo(
            project_id=project["id"],
            original_path="/tmp/lens.jpg",
            filename="lens.jpg",
            thumbnail_path=thumbnail_path,
            preview_path=preview_path,
            width=6000,
            height=4000,
            camera_model="Camera A",
            lens_model="Prime 35mm",
            focal_length="35",
            sharpness_score=0.8,
            exposure_score=0.8,
            contrast_score=0.7,
            noise_score=0.2,
            aesthetic_score=0.7,
            embedding="[1, 0]",
        )
        session.add(photo)
        project_model = session.get(Project, project["id"])
        assert project_model is not None
        project_model.total_images = 1
        session.add(project_model)
        session.commit()
        photo_id = photo.id

    def capture_group_inputs(group_inputs):
        captured_inputs.extend(group_inputs)
        return [SimilarPhotoGroup(photo_ids=[photo_id], group_type="single")]

    monkeypatch.setattr("app.services.processing.group_similar_photos", capture_group_inputs)

    response = client.post(f"/api/projects/{project['id']}/process")

    assert response.status_code == 202
    job = _wait_for_job(client, project["id"], response.json())
    assert job["status"] == "complete"
    assert captured_inputs[0]["lens_model"] == "Prime 35mm"


def test_processing_persists_duplicate_group_score_summary(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Group confidence"}).json()

    with Session(get_engine()) as session:
        best_thumbnail, best_preview = _write_test_derivatives(tmp_path, "best")
        weak_thumbnail, weak_preview = _write_test_derivatives(tmp_path, "weak")
        photos = [
            Photo(
                project_id=project["id"],
                original_path="/tmp/IMG_0001.jpg",
                filename="IMG_0001.jpg",
                thumbnail_path=best_thumbnail,
                preview_path=best_preview,
                sharpness_score=1.0,
                exposure_score=1.0,
                contrast_score=1.0,
                noise_score=0.0,
                aesthetic_score=1.0,
                embedding="[1, 0]",
            ),
            Photo(
                project_id=project["id"],
                original_path="/tmp/IMG_0002.jpg",
                filename="IMG_0002.jpg",
                thumbnail_path=weak_thumbnail,
                preview_path=weak_preview,
                sharpness_score=0.0,
                exposure_score=0.0,
                contrast_score=0.0,
                noise_score=1.0,
                aesthetic_score=0.0,
                embedding="[1, 0]",
            ),
        ]
        session.add_all(photos)
        project_model = session.get(Project, project["id"])
        assert project_model is not None
        project_model.total_images = 2
        session.add(project_model)
        session.commit()
        best_photo_id = photos[0].id

    response = client.post(f"/api/projects/{project['id']}/process")

    assert response.status_code == 202
    job = _wait_for_job(client, project["id"], response.json())
    assert job["status"] == "complete"
    groups = client.get(f"/api/projects/{project['id']}/groups").json()
    assert len(groups) == 1
    assert groups[0]["group_type"] == "duplicate"
    assert groups[0]["representative_photo_id"] == best_photo_id
    score_summary = json.loads(groups[0]["score_summary"])
    assert score_summary["confidence"] == "high"
    assert score_summary["top_photo_id"] == best_photo_id
    assert score_summary["best_score"] >= score_summary["score_gap"] > 0.1
    assert score_summary["recommendation_counts"] == {"Maybe": 0, "Pick": 1, "Reject": 1, "Unreviewed": 0}
    assert "top photo leads" in score_summary["explanation"]


def test_import_rejects_invalid_image_and_cleans_written_file(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Bad upload"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("broken.jpg", b"not an image", "image/jpeg"))],
    )

    assert response.status_code == 422
    assert not (Path(project["root_path"]) / "originals" / "broken.jpg").exists()


def test_import_cleans_original_and_derivatives_when_processing_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Derivative cleanup"}).json()

    def fail_scoring(_image):
        raise RuntimeError("scoring failed")

    monkeypatch.setattr("app.services.importing.compute_quality_scores", fail_scoring)

    response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )

    assert response.status_code == 422
    root = Path(project["root_path"])
    assert list((root / "originals").iterdir()) == []
    assert list((root / "thumbnails").iterdir()) == []
    assert list((root / "previews").iterdir()) == []
    assert client.get(f"/api/projects/{project['id']}").json()["total_images"] == 0
    assert client.get(f"/api/projects/{project['id']}/photos").json() == []


def test_import_skips_invalid_files_when_other_images_import_successfully(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Mixed import"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[
            ("files", ("good.jpg", _image_bytes(), "image/jpeg")),
            ("files", ("notes.txt", b"not an image", "text/plain")),
            ("files", ("broken.jpg", b"not an image", "image/jpeg")),
        ],
    )

    assert response.status_code == 201
    result = response.json()
    assert [photo["filename"] for photo in result["imported"]] == ["good.jpg"]
    assert {item["filename"] for item in result["skipped"]} == {"notes.txt", "broken.jpg"}
    assert client.get(f"/api/projects/{project['id']}").json()["total_images"] == 1
    root = Path(project["root_path"])
    assert (root / "originals" / "good.jpg").exists()
    assert not (root / "originals" / "notes.txt").exists()
    assert not (root / "originals" / "broken.jpg").exists()


def test_import_reports_heic_and_raw_as_planned_unsupported_formats(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Planned formats"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[
            ("files", ("good.jpg", _image_bytes(), "image/jpeg")),
            ("files", ("camera.heic", b"not decoded in v2", "image/heic")),
            ("files", ("frame.dng", b"not decoded in v2", "image/x-adobe-dng")),
        ],
    )

    assert response.status_code == 201
    result = response.json()
    assert [photo["filename"] for photo in result["imported"]] == ["good.jpg"]
    assert result["skipped"] == [
        {
            "filename": "camera.heic",
            "reason": "HEIC files are not supported yet; import JPEG, PNG, or WebP files for this release",
        },
        {
            "filename": "frame.dng",
            "reason": "RAW files are not supported yet; import JPEG, PNG, or WebP files for this release",
        },
    ]
    originals = Path(project["root_path"]) / "originals"
    assert (originals / "good.jpg").exists()
    assert not (originals / "camera.heic").exists()
    assert not (originals / "frame.dng").exists()


def test_export_rejects_invalid_status(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Export validation"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/export",
        json={"mode": "csv", "statuses": ["Favorite"]},
    )

    assert response.status_code == 422


def test_export_normalizes_duplicate_status_filters(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Normalized export"}).json()

    with Session(get_engine()) as session:
        photos = [
            Photo(project_id=project["id"], original_path="/tmp/pick.jpg", filename="pick.jpg", user_status="Pick"),
            Photo(project_id=project["id"], original_path="/tmp/maybe.jpg", filename="maybe.jpg", user_status="Maybe"),
        ]
        session.add_all(photos)
        session.commit()

    response = client.post(
        f"/api/projects/{project['id']}/export",
        json={"mode": "csv", "statuses": ["Maybe", "Pick", "Maybe"]},
    )

    assert response.status_code == 201
    record = response.json()
    assert record["selected_count"] == 2
    assert record["statuses"] == '["Pick", "Maybe"]'


def test_export_rejects_when_no_photos_match_selected_statuses(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Empty export"}).json()
    client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )

    response = client.post(f"/api/projects/{project['id']}/export", json={"mode": "zip", "statuses": ["Pick"]})

    assert response.status_code == 422
    assert "No photos match" in response.text
    export_root = Path(project["root_path"]) / "exports"
    assert list((export_root / "csv").iterdir()) == []
    assert list((export_root / "zip").iterdir()) == []
    assert list((export_root / "folders").iterdir()) == []


def test_repeated_exports_write_unique_records_and_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Repeated exports"}).json()
    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    photo = import_response.json()["imported"][0]
    client.patch(
        f"/api/projects/{project['id']}/photos/{photo['id']}",
        json={"user_status": "Pick"},
    )

    first = client.post(f"/api/projects/{project['id']}/export", json={"mode": "csv", "statuses": ["Pick"]})
    second = client.post(f"/api/projects/{project['id']}/export", json={"mode": "csv", "statuses": ["Pick"]})

    assert first.status_code == 201
    assert second.status_code == 201
    first_record = first.json()
    second_record = second.json()
    assert first_record["id"] != second_record["id"]
    assert first_record["output_path"] != second_record["output_path"]
    assert first_record["selected_count"] == 1
    assert second_record["selected_count"] == 1
    assert Path(first_record["output_path"]).exists()
    assert Path(second_record["output_path"]).exists()


def test_failed_export_records_failed_history_and_removes_partial_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Failed export"}).json()
    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    photo = import_response.json()["imported"][0]
    client.patch(
        f"/api/projects/{project['id']}/photos/{photo['id']}",
        json={"user_status": "Pick"},
    )

    def fail_after_partial_write(target: Path, photos: list[dict]) -> Path:
        assert len(photos) == 1
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("partial export")
        raise RuntimeError("simulated export failure")

    monkeypatch.setattr(routes, "write_selection_csv", fail_after_partial_write)

    response = client.post(f"/api/projects/{project['id']}/export", json={"mode": "csv", "statuses": ["Pick"]})

    assert response.status_code == 500
    assert response.json()["detail"] == "Export failed"
    history = client.get(f"/api/projects/{project['id']}/export").json()
    assert len(history) == 1
    record = history[0]
    assert record["mode"] == "csv"
    assert record["status"] == "failed"
    assert record["selected_count"] == 1
    assert record["error_message"] == "Export failed"
    assert record["completed_at"] is not None
    assert record["output_path"].endswith(".csv")
    assert not Path(record["output_path"]).exists()


def test_failed_export_cleanup_does_not_remove_artifact_outside_export_root(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Failed outside cleanup"}).json()
    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )
    photo = import_response.json()["imported"][0]
    client.patch(
        f"/api/projects/{project['id']}/photos/{photo['id']}",
        json={"user_status": "Pick"},
    )
    outside_artifact = tmp_path / "outside.csv"

    def outside_export_target(_export_root: Path, _export_id: str, _mode: str) -> Path:
        return outside_artifact

    def fail_after_outside_partial_write(target: Path, photos: list[dict]) -> Path:
        assert target == outside_artifact
        assert len(photos) == 1
        target.write_text("outside partial export")
        raise RuntimeError("simulated export failure")

    monkeypatch.setattr(routes, "_export_target", outside_export_target)
    monkeypatch.setattr(routes, "write_selection_csv", fail_after_outside_partial_write)

    response = client.post(f"/api/projects/{project['id']}/export", json={"mode": "csv", "statuses": ["Pick"]})

    assert response.status_code == 500
    assert outside_artifact.read_text() == "outside partial export"


def test_file_export_fails_when_selected_original_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Missing export original"}).json()
    missing_original = tmp_path / "missing.jpg"

    with Session(get_engine()) as session:
        photo = Photo(
            project_id=project["id"],
            original_path=str(missing_original),
            filename="missing.jpg",
            user_status="Pick",
        )
        session.add(photo)
        session.commit()

    response = client.post(f"/api/projects/{project['id']}/exports", json={"mode": "zip", "statuses": ["Pick"]})

    assert response.status_code == 500
    assert response.json()["detail"] == "Export failed"
    history = client.get(f"/api/projects/{project['id']}/exports").json()
    assert len(history) == 1
    record = history[0]
    assert record["mode"] == "zip"
    assert record["status"] == "failed"
    assert record["selected_count"] == 1
    assert record["error_message"] == "Export failed"
    assert record["output_path"].endswith(".zip")
    assert not Path(record["output_path"]).exists()


def test_download_rejects_incomplete_export_records_even_when_artifact_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Incomplete export"}).json()
    export_path = Path(project["root_path"]) / "exports" / "failed.csv"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text("partial export")

    with Session(get_engine()) as session:
        record = ExportRecord(
            project_id=project["id"],
            mode="csv",
            status="failed",
            selected_count=1,
            statuses='["Pick"]',
            output_path=str(export_path),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        export_id = record.id

    response = client.get(f"/api/projects/{project['id']}/export/{export_id}/download")

    assert response.status_code == 409
    assert response.json()["detail"] == "Export artifact is not ready for download"
