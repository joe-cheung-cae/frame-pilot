import hashlib
import json
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, create_engine, select

from app.core.project_roots import clear_registered_roots
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import ExportRecord, Photo, ProcessingJob, Project


def _jpeg(color: tuple[int, int, int] = (120, 150, 90)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (16, 12), color=color).save(buffer, format="JPEG", quality=40)
    return buffer.getvalue()


def _write_jpeg(path: Path, color: tuple[int, int, int] = (120, 150, 90)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_jpeg(color))


def _fingerprint(path: Path) -> tuple[int, int, str]:
    st = path.stat()
    return st.st_size, st.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_fingerprints(root: Path) -> dict[str, tuple[int, int, str]]:
    records: dict[str, tuple[int, int, str]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        # SQLite -wal/-shm can change on a read-only query; the db file must stay identical.
        if path.name.endswith("-wal") or path.name.endswith("-shm"):
            continue
        records[str(path.relative_to(root))] = _fingerprint(path)
    return records


def _dest_session(dest: Path) -> Session:
    engine = create_engine(f"sqlite:///{dest / 'framepilot.db'}", connect_args={"check_same_thread": False})
    return Session(engine)


def _wait_for_job(client: TestClient, project_id: str, job: dict) -> dict:
    current = job
    for _ in range(40):
        if current["status"] in {"complete", "complete_with_errors", "failed", "cancelled", "paused"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


def _desktop_client(data_dir: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(data_dir))
    monkeypatch.setenv("FRAMEPILOT_DESKTOP", "1")
    monkeypatch.delenv("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST", raising=False)
    clear_registered_roots()
    return TestClient(create_app())


def _web_client(data_dir: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(data_dir))
    monkeypatch.delenv("FRAMEPILOT_DESKTOP", raising=False)
    monkeypatch.delenv("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST", raising=False)
    return TestClient(create_app())


def _empty_outside(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def test_data_dir_relocate_404_without_desktop_env(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dest = _empty_outside(tmp_path, "dest")
    client = _web_client(data_dir, monkeypatch)

    response = client.post("/api/desktop/data-dir", json={"path": str(dest)})

    assert response.status_code == 404


def test_data_dir_relocate_422_unregistered_blocked_nested_nonempty(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    client = _desktop_client(data_dir, monkeypatch)
    unregistered = _empty_outside(tmp_path, "unregistered")
    nested = data_dir / "nested-copy"
    nested.mkdir()
    nonempty = _empty_outside(tmp_path, "nonempty")
    leftover = nonempty / "keep.txt"
    leftover.write_text("stay", encoding="utf-8")
    assert client.post("/api/desktop/project-roots", json={"path": str(nonempty)}).status_code == 201

    cases = [
        str(unregistered),
        "/",
        str(data_dir),
        str(nested),
        str(nonempty),
        str(tmp_path / "missing-dir"),
    ]
    for path in cases:
        response = client.post("/api/desktop/data-dir", json={"path": path})
        assert response.status_code == 422, path

    assert leftover.read_text(encoding="utf-8") == "stay"


def test_data_dir_relocate_409_when_job_is_blocking(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dest = _empty_outside(tmp_path, "dest-busy")
    client = _desktop_client(data_dir, monkeypatch)
    project = client.post("/api/projects", json={"name": "Busy"}).json()
    assert client.post("/api/desktop/project-roots", json={"path": str(dest)}).status_code == 201
    with Session(get_engine()) as session:
        session.add(ProcessingJob(project_id=project["id"], job_type="import", status="running"))
        session.commit()

    response = client.post("/api/desktop/data-dir", json={"path": str(dest)})

    assert response.status_code == 409
    assert list(dest.iterdir()) == []


def test_data_dir_relocate_copies_and_rewrites_managed_paths_only(tmp_path, monkeypatch):
    data_dir = (tmp_path / "data").resolve()
    data_dir.mkdir()
    dest = _empty_outside(tmp_path, "dest")
    camera_dir = tmp_path / "camera-card"
    camera = camera_dir / "IMG_0001.jpg"
    _write_jpeg(camera, (12, 34, 56))
    camera_before = _fingerprint(camera)
    custom_root = _empty_outside(tmp_path, "custom-project")
    client = _desktop_client(data_dir, monkeypatch)

    managed = client.post("/api/projects", json={"name": "Managed"}).json()
    assert client.post("/api/desktop/project-roots", json={"path": str(custom_root)}).status_code == 201
    custom = client.post(
        "/api/projects",
        json={"name": "Custom", "root_path": str(custom_root), "acknowledge_nonempty": True},
    ).json()
    imported = client.post(
        f"/api/projects/{managed['id']}/imports/from-paths",
        json={"paths": [str(camera_dir)], "finalize": True},
    )
    assert imported.status_code == 201
    job = _wait_for_job(client, managed["id"], imported.json()["job"])
    assert job["status"] == "complete"
    photos = client.get(f"/api/projects/{managed['id']}/photos").json()
    assert len(photos) == 1
    photo = photos[0]
    export_inside = Path(managed["root_path"]) / "exports" / "csv" / "selection.csv"
    export_inside.parent.mkdir(parents=True, exist_ok=True)
    export_inside.write_text("filename\nIMG_0001.jpg\n", encoding="utf-8")
    export_outside = tmp_path / "outside-export" / "selection.csv"
    export_outside.parent.mkdir()
    export_outside.write_text("filename\ncustom.jpg\n", encoding="utf-8")
    with Session(get_engine()) as session:
        session.add(
            Photo(
                project_id=managed["id"],
                original_path=str(camera.resolve()),
                project_copy_path=photo["project_copy_path"],
                filename="card-original.jpg",
            )
        )
        session.add(
            ExportRecord(
                project_id=managed["id"],
                mode="csv",
                output_path=str(export_inside),
                selected_count=1,
            )
        )
        session.add(
            ExportRecord(
                project_id=custom["id"],
                mode="csv",
                output_path=str(export_outside),
                selected_count=1,
            )
        )
        session.commit()

    assert client.post("/api/desktop/project-roots", json={"path": str(dest)}).status_code == 201
    old_tree = _tree_fingerprints(data_dir)
    old_db = _fingerprint(data_dir / "framepilot.db")

    response = client.post("/api/desktop/data-dir", json={"path": str(dest)})

    assert response.status_code == 200
    assert Path(response.json()["data_dir"]) == dest
    assert _tree_fingerprints(data_dir) == old_tree
    assert _fingerprint(data_dir / "framepilot.db") == old_db
    assert _fingerprint(camera) == camera_before
    assert (dest / "framepilot.db").is_file()
    copied_project = dest / "projects" / managed["id"]
    assert copied_project.is_dir()
    assert (copied_project / "originals" / "IMG_0001.jpg").is_file()
    assert not (dest / "camera-card").exists()
    registry = json.loads((dest / "desktop_project_roots.json").read_text(encoding="utf-8"))
    dest_keys = {str(Path(item).resolve()) for item in registry["roots"]}
    assert str(dest) not in dest_keys
    assert str(custom_root) in dest_keys

    with _dest_session(dest) as session:
        moved = session.get(Project, managed["id"])
        custom_row = session.get(Project, custom["id"])
        assert moved is not None
        assert custom_row is not None
        assert Path(moved.root_path).is_relative_to(dest)
        assert Path(moved.root_path) == copied_project
        assert moved.source_root_path == str(camera_dir.resolve())
        assert Path(custom_row.root_path) == custom_root
        copied_photo = session.exec(select(Photo).where(Photo.filename == "IMG_0001.jpg")).one()
        assert Path(copied_photo.project_copy_path).is_relative_to(dest)
        assert Path(copied_photo.thumbnail_path).is_relative_to(dest)
        assert Path(copied_photo.preview_path).is_relative_to(dest)
        assert Path(copied_photo.original_path).is_relative_to(dest)
        card_photo = session.exec(select(Photo).where(Photo.filename == "card-original.jpg")).one()
        assert card_photo.original_path == str(camera.resolve())
        inside_export = session.exec(select(ExportRecord).where(ExportRecord.project_id == managed["id"])).one()
        assert Path(inside_export.output_path).is_relative_to(dest)
        outside_export = session.exec(select(ExportRecord).where(ExportRecord.project_id == custom["id"])).one()
        assert Path(outside_export.output_path) == export_outside
    assert Path(custom["root_path"]) == custom_root
    assert (custom_root / "originals").is_dir()
