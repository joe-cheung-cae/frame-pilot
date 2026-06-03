import csv
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFilter
from sqlmodel import Session, select

from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo, PhotoGroup, ProcessingJob, Project


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
    assert photo["thumbnail_path"]
    assert photo["preview_path"]
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

    groups = client.get(f"/api/projects/{project['id']}/groups").json()
    assert len(groups) == 1
    assert groups[0]["representative_photo_id"] == photo["id"]

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
    assert imported_original != sharp_source
    assert imported_original.read_bytes() == sharp_bytes
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
    assert csv_path.exists()
    with csv_path.open(newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert [row["status"] for row in csv_rows] == ["Pick"]

    csv_download_response = client.get(f"/api/projects/{project['id']}/export/{csv_export['id']}/download")
    assert csv_download_response.status_code == 200
    assert "filename" in csv_download_response.headers["content-disposition"]
    assert b"filename,original_path,status" in csv_download_response.content

    zip_export_response = client.post(
        f"/api/projects/{project['id']}/export",
        json={"mode": "zip", "statuses": ["Pick"]},
    )
    assert zip_export_response.status_code == 201
    zip_export = zip_export_response.json()
    zip_path = Path(zip_export["output_path"])
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
    folder_download_response = client.get(
        f"/api/projects/{project['id']}/export/{folder_export_response.json()['id']}/download",
    )
    assert folder_download_response.status_code == 422


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
        invalid_photo = Photo(
            project_id=project["id"],
            original_path=str(tmp_path / "missing.jpg"),
            filename="invalid.jpg",
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
    assert "stored similarity data is invalid" in invalid_after_processing["recommendation_explanation"]


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
        session.add(second)
        session.add(first)
        session.commit()

    groups = client.get(f"/api/projects/{project['id']}/groups").json()

    assert [group["photo_count"] for group in groups] == [2, 1]


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


def test_processing_recommendation_explains_face_and_eye_quality(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Face ranking"}).json()

    with Session(get_engine()) as session:
        photos = [
            Photo(
                project_id=project["id"],
                original_path="/tmp/face.jpg",
                filename="face.jpg",
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


def test_export_rejects_invalid_status(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Export validation"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/export",
        json={"mode": "csv", "statuses": ["Favorite"]},
    )

    assert response.status_code == 422


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
    assert list(export_root.iterdir()) == []


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
