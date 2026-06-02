from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, select

from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo, PhotoGroup, ProcessingJob


def _image_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (80, 60), color=(120, 150, 90))
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
    assert process_response.json()["status"] == "complete"
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
