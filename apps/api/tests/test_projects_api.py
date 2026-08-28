import shutil
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, select

from app.core.version import APP_VERSION
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import ExportRecord, Photo, PhotoGroup, ProcessingJob


def test_api_health_returns_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "framepilot-api"
    assert payload["version"] == APP_VERSION


def test_unprefixed_health_returns_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "framepilot-api"
    assert payload["version"] == APP_VERSION


def test_create_app_version_matches_app_version(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    assert create_app().version == APP_VERSION


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


def test_list_projects_stale_job_handling_query_count_is_bounded(tmp_path, monkeypatch):
    """Listing N projects with active jobs must not issue O(N) per-project stale sweeps (#25)."""
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project_count = 12
    projects = [client.post("/api/projects", json={"name": f"Project {index}"}).json() for index in range(project_count)]

    with Session(get_engine()) as session:
        now = datetime.now(UTC)
        for project in projects:
            session.add(
                ProcessingJob(
                    project_id=project["id"],
                    job_type="import",
                    status="running",
                    current_step="derivative_generation",
                    total_items=2,
                    processed_items=1,
                    failed_items=0,
                    progress_percent=50.0,
                    started_at=now,
                    updated_at=now,
                )
            )
            session.add(
                ProcessingJob(
                    project_id=project["id"],
                    job_type="processing",
                    status="queued",
                    current_step="queued",
                    total_items=2,
                    processed_items=0,
                    failed_items=0,
                    progress_percent=0.0,
                    updated_at=now,
                )
            )
        session.commit()

    engine = get_engine()
    statements: list[str] = []

    def before_cursor_execute(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(str(statement))

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        response = client.get("/api/projects")
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    assert response.status_code == 200
    listed = response.json()
    assert len(listed) == project_count
    assert all(item["active_import_job"] is not None for item in listed)
    # Constant-ish job handling: one projects query + batched active import job query,
    # not a per-project stale sweep (which would be ~3N+).
    assert len(statements) <= 12
    assert len(statements) < project_count * 3


def test_list_projects_get_does_not_write_when_jobs_are_stale(tmp_path, monkeypatch):
    """GET /api/projects must stay read-only even when stale jobs exist (#76)."""
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Stale list read"}).json()
    stale_updated_at = datetime.now(UTC).replace(year=2020)

    with Session(get_engine()) as session:
        stale_job = ProcessingJob(
            project_id=project["id"],
            job_type="import",
            status="running",
            current_step="derivative_generation",
            total_items=2,
            processed_items=1,
            failed_items=0,
            progress_percent=50.0,
            started_at=stale_updated_at,
            updated_at=stale_updated_at,
        )
        session.add(stale_job)
        session.commit()
        stale_job_id = stale_job.id

    engine = get_engine()
    write_statements: list[str] = []

    def before_cursor_execute(_conn, _cursor, statement, _parameters, _context, _executemany):
        normalized = " ".join(str(statement).lower().split())
        if normalized.startswith(("insert ", "update ", "delete ")):
            write_statements.append(normalized)

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        response = client.get("/api/projects")
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    assert response.status_code == 200
    listed = next(item for item in response.json() if item["id"] == project["id"])
    assert listed["active_import_job"] is None
    assert write_statements == []

    with Session(get_engine()) as session:
        still_running = session.get(ProcessingJob, stale_job_id)
        assert still_running is not None
        assert still_running.status == "running"
        assert still_running.current_step == "derivative_generation"

    # Stale failure remains prompt on the project detail / jobs path.
    detail = client.get(f"/api/projects/{project['id']}")
    assert detail.status_code == 200
    assert detail.json()["active_import_job"] is None
    with Session(get_engine()) as session:
        failed = session.get(ProcessingJob, stale_job_id)
        assert failed is not None
        assert failed.status == "failed"
        assert failed.current_step == "failed - stale"


def test_create_project_rejects_empty_name(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.post("/api/projects", json={"name": "  "})

    assert response.status_code == 422


def test_create_project_treats_blank_root_path_as_default(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.post("/api/projects", json={"name": "Default storage", "root_path": "  "})

    assert response.status_code == 201
    project = response.json()
    assert Path(project["root_path"]).parent == tmp_path / "projects"
    assert Path(project["root_path"]).is_dir()


def test_create_project_rejects_unusable_root_path_without_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    blocked_root = tmp_path / "projects" / "blocked-root"
    blocked_root.parent.mkdir(parents=True, exist_ok=True)
    blocked_root.write_text("not a directory")

    response = client.post("/api/projects", json={"name": "Bad storage", "root_path": str(blocked_root)})

    assert response.status_code == 422
    assert response.json()["detail"] == "Project root path must be a usable local directory"
    assert client.get("/api/projects").json() == []


def test_create_project_rejects_root_outside_allowlist(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    outside = tmp_path.parent / "outside-project-root"
    outside.mkdir(parents=True, exist_ok=True)

    response = client.post("/api/projects", json={"name": "Outside", "root_path": str(outside)})

    assert response.status_code == 422
    assert "allowlisted" in response.json()["detail"]
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


def test_generated_asset_directory_symlinks_cannot_escape_project_root(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Asset root safety"}).json()
    thumbnail_dir = Path(project["root_path"]) / "thumbnails"
    outside_dir = tmp_path / "outside-thumbnails"
    outside_dir.mkdir()
    (outside_dir / "frame.webp").write_bytes(b"outside")
    shutil.rmtree(thumbnail_dir)
    thumbnail_dir.symlink_to(outside_dir, target_is_directory=True)

    response = client.get(f"/api/assets/{project['id']}/thumbnails/frame.webp")

    assert response.status_code == 404
