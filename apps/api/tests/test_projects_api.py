from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db.session import get_engine
from app.main import create_app
from app.models.entities import ExportRecord, Photo, PhotoGroup, ProcessingJob


def test_api_health_returns_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.post("/api/projects", json={"name": "Wedding selects"})

    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Wedding selects"
    assert created["source_mode"] == "copy"
    assert created["source_root_path"] is None
    assert created["schema_version"] == 2
    assert created["total_images"] == 0
    assert created["processed_images"] == 0
    assert created["last_processed_at"] is None
    project_root = Path(created["root_path"])
    for child in (
        "originals",
        "thumbnails",
        "previews",
        "exports",
        "exports/csv",
        "exports/zip",
        "exports/folders",
        "cache",
        "cache/hashes",
        "cache/embeddings",
        "cache/jobs",
        "logs",
    ):
        assert (project_root / child).is_dir()

    list_response = client.get("/api/projects")

    assert list_response.status_code == 200
    projects = list_response.json()
    assert len(projects) == 1
    assert projects[0]["id"] == created["id"]


def test_create_project_rejects_empty_name(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.post("/api/projects", json={"name": "  "})

    assert response.status_code == 422


def test_create_project_rejects_unusable_root_path_without_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    blocked_root = tmp_path / "blocked-root"
    blocked_root.write_text("not a directory")

    response = client.post("/api/projects", json={"name": "Bad storage", "root_path": str(blocked_root)})

    assert response.status_code == 422
    assert response.json()["detail"] == "Project root path must be a usable local directory"
    assert client.get("/api/projects").json() == []


def test_get_project_returns_404_for_missing_project(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.get("/api/projects/missing")

    assert response.status_code == 404


def test_delete_project_removes_metadata_without_deleting_local_files(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Delete metadata"}).json()
    root = Path(project["root_path"])
    copied_original = root / "originals" / "frame.jpg"
    copied_original.write_bytes(b"original")

    with Session(get_engine()) as session:
        group = PhotoGroup(project_id=project["id"], photo_count=1)
        photo = Photo(project_id=project["id"], original_path=str(copied_original), filename="frame.jpg")
        job = ProcessingJob(project_id=project["id"], status="complete")
        export = ExportRecord(
            project_id=project["id"],
            mode="csv",
            status="complete",
            selected_count=1,
            statuses='["Pick"]',
            output_path=str(root / "exports" / "selection.csv"),
        )
        session.add(group)
        session.add(photo)
        session.add(job)
        session.add(export)
        session.commit()

    response = client.delete(f"/api/projects/{project['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/projects/{project['id']}").status_code == 404
    assert root.exists()
    assert copied_original.exists()
    with Session(get_engine()) as session:
        assert list(session.exec(select(Photo).where(Photo.project_id == project["id"])).all()) == []
        assert list(session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project["id"])).all()) == []
        assert list(session.exec(select(ProcessingJob).where(ProcessingJob.project_id == project["id"])).all()) == []
        assert list(session.exec(select(ExportRecord).where(ExportRecord.project_id == project["id"])).all()) == []


def test_generated_assets_cannot_escape_project_asset_directories(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Asset safety"}).json()
    thumbnail_dir = Path(project["root_path"]) / "thumbnails"
    valid_asset = thumbnail_dir / "frame.webp"
    valid_asset.write_bytes(b"thumbnail")
    outside_asset = tmp_path / "outside.webp"
    outside_asset.write_bytes(b"outside")
    (thumbnail_dir / "leak.webp").symlink_to(outside_asset)

    valid_response = client.get(f"/api/assets/{project['id']}/thumbnails/frame.webp")
    escape_response = client.get(f"/api/assets/{project['id']}/thumbnails/leak.webp")
    invalid_kind_response = client.get(f"/api/assets/{project['id']}/originals/frame.webp")

    assert valid_response.status_code == 200
    assert valid_response.content == b"thumbnail"
    assert escape_response.status_code == 404
    assert invalid_kind_response.status_code == 404
