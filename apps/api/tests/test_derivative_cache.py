import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo, PhotoGroup, ProcessingJob, Project


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    return TestClient(create_app())


def _fingerprint(path: Path) -> tuple[int, int, str]:
    st = path.stat()
    return st.st_size, st.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_derivative_files(root: Path) -> dict[str, Path]:
    originals = root / "originals"
    thumbnails = root / "thumbnails"
    previews = root / "previews"
    exports = root / "exports" / "csv"
    hashes = root / "cache" / "hashes"
    originals.mkdir(parents=True, exist_ok=True)
    thumbnails.mkdir(parents=True, exist_ok=True)
    previews.mkdir(parents=True, exist_ok=True)
    exports.mkdir(parents=True, exist_ok=True)
    hashes.mkdir(parents=True, exist_ok=True)
    original = originals / "shot.jpg"
    original.write_bytes(b"original-bytes-keep")
    thumb = thumbnails / "shot.webp"
    thumb.write_bytes(b"thumb")
    preview = previews / "shot.webp"
    preview.write_bytes(b"preview-bytes")
    export = exports / "picks.csv"
    export.write_bytes(b"export-keep")
    hash_file = hashes / "x.bin"
    hash_file.write_bytes(b"hash-keep")
    return {
        "original": original,
        "thumb": thumb,
        "preview": preview,
        "export": export,
        "hash": hash_file,
    }


def test_empty_cache_is_zero(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = client.get("/api/cache")

    assert response.status_code == 200
    assert response.json() == {
        "derivative_bytes": 0,
        "file_count": 0,
        "project_count": 0,
        "deleted_files": 0,
    }


def test_cache_measures_thumbnails_and_previews_not_originals(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Cache"}).json()
    files = _seed_derivative_files(Path(project["root_path"]))
    before = _fingerprint(files["original"])

    response = client.get("/api/cache")

    assert response.status_code == 200
    body = response.json()
    assert body["file_count"] == 2
    assert body["project_count"] == 1
    assert body["derivative_bytes"] == len(b"thumb") + len(b"preview-bytes")
    assert _fingerprint(files["original"]) == before
    assert files["export"].exists()
    assert files["hash"].exists()


def test_clear_derivatives_deletes_cache_and_keeps_originals(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Clear cache"}).json()
    files = _seed_derivative_files(Path(project["root_path"]))
    before = _fingerprint(files["original"])
    export_before = _fingerprint(files["export"])
    hash_before = _fingerprint(files["hash"])
    with Session(get_engine()) as session:
        row = session.exec(select(Project).where(Project.id == project["id"])).one()
        group = PhotoGroup(project_id=row.id, group_type="burst", sequence=1)
        session.add(group)
        session.commit()
        session.refresh(group)
        photo = Photo(
            project_id=row.id,
            original_path=str(files["original"]),
            project_copy_path=str(files["original"]),
            filename="shot.jpg",
            thumbnail_path=str(files["thumb"]),
            preview_path=str(files["preview"]),
            user_status="Pick",
            star_rating=4,
            group_id=group.id,
        )
        session.add(photo)
        session.commit()
        photo_id = photo.id
        group_id = group.id

    response = client.post("/api/cache/clear-derivatives")

    assert response.status_code == 200
    body = response.json()
    assert body["deleted_files"] == 2
    assert body["file_count"] == 0
    assert body["derivative_bytes"] == 0
    assert not files["thumb"].exists()
    assert not files["preview"].exists()
    assert files["original"].exists()
    assert _fingerprint(files["original"]) == before
    assert files["export"].exists()
    assert _fingerprint(files["export"]) == export_before
    assert files["hash"].exists()
    assert _fingerprint(files["hash"]) == hash_before
    with Session(get_engine()) as session:
        photo = session.get(Photo, photo_id)
        assert photo is not None
        assert photo.thumbnail_path is None
        assert photo.preview_path is None
        assert photo.user_status == "Pick"
        assert photo.star_rating == 4
        assert photo.project_copy_path == str(files["original"])
        assert photo.group_id == group_id
        assert session.get(PhotoGroup, group_id) is not None


@pytest.mark.parametrize("job_type", ["import", "processing"])
def test_clear_derivatives_conflicts_when_job_is_running(tmp_path, monkeypatch, job_type):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Busy cache"}).json()
    with Session(get_engine()) as session:
        session.add(
            ProcessingJob(
                project_id=project["id"],
                job_type=job_type,
                status="running",
                current_step="Generating previews",
            )
        )
        session.commit()

    response = client.post("/api/cache/clear-derivatives")

    assert response.status_code == 409
    assert "import or processing" in response.json()["detail"]


def test_clear_derivatives_allowed_when_job_is_paused(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Paused cache"}).json()
    files = _seed_derivative_files(Path(project["root_path"]))
    with Session(get_engine()) as session:
        session.add(
            ProcessingJob(
                project_id=project["id"],
                job_type="processing",
                status="paused",
                current_step="Grouping",
            )
        )
        session.commit()

    response = client.post("/api/cache/clear-derivatives")

    assert response.status_code == 200
    assert response.json()["deleted_files"] == 2
    assert not files["thumb"].exists()
    assert files["original"].exists()
