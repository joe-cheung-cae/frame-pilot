import hashlib
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, select

from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo
from app.services.importing import IMPORT_MAX_FILES_PER_REQUEST, unsupported_image_reason


def _jpeg(color=(120, 150, 90)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (48, 36), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def _write_jpeg(path: Path, color=(120, 150, 90)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_jpeg(color))


def _source_fingerprint(path: Path) -> tuple[int, int, str]:
    st = path.stat()
    return st.st_size, st.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    return TestClient(create_app())


def test_import_from_paths_two_jpegs(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Paths"}).json()
    first = tmp_path / "card" / "one.jpg"
    second = tmp_path / "card" / "two.jpg"
    _write_jpeg(first, (10, 20, 30))
    _write_jpeg(second, (40, 50, 60))

    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(tmp_path / "card")], "finalize": True},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["expanded_total"] == 2
    assert payload["remaining_paths"] == []
    assert {item["filename"] for item in payload["imported"]} == {"one.jpg", "two.jpg"}
    originals = Path(project["root_path"]) / "originals"
    for item in payload["imported"]:
        copy_path = Path(item["project_copy_path"])
        assert copy_path.is_relative_to(originals)
        assert copy_path.is_file()


def test_import_from_paths_chunks_250_files_in_three_requests(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.routes.run_import_derivative_job", lambda *args, **kwargs: None)
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Chunked paths"}).json()
    folder = tmp_path / "burst"
    for index in range(250):
        _write_jpeg(folder / f"frame-{index:03d}.jpg", (index % 200, 40, 80))

    first = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(folder)], "finalize": False},
    )
    assert first.status_code == 201, first.text
    first_payload = first.json()
    assert first_payload["expanded_total"] == 250
    assert len(first_payload["imported"]) == IMPORT_MAX_FILES_PER_REQUEST
    assert len(first_payload["remaining_paths"]) == 150
    assert str(folder) not in first_payload["remaining_paths"]
    assert all(Path(path).is_file() for path in first_payload["remaining_paths"])
    job_id = first_payload["job"]["id"]
    assert first_payload["job"]["total_items"] == 250

    second = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={
            "paths": first_payload["remaining_paths"],
            "job_id": job_id,
            "expected_total": 250,
            "finalize": False,
        },
    )
    assert second.status_code == 201, second.text
    second_payload = second.json()
    assert second_payload["job"]["id"] == job_id
    assert len(second_payload["imported"]) == IMPORT_MAX_FILES_PER_REQUEST
    assert len(second_payload["remaining_paths"]) == 50
    assert all(Path(path).is_file() for path in second_payload["remaining_paths"])

    third = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={
            "paths": second_payload["remaining_paths"],
            "job_id": job_id,
            "expected_total": 250,
            "finalize": True,
        },
    )
    assert third.status_code == 201, third.text
    third_payload = third.json()
    assert third_payload["job"]["id"] == job_id
    assert len(third_payload["imported"]) == 50
    assert third_payload["remaining_paths"] == []

    imported_names = [
        item["filename"] for payload in (first_payload, second_payload, third_payload) for item in payload["imported"]
    ]
    assert len(imported_names) == 250
    originals = Path(project["root_path"]) / "originals"
    assert len(list(originals.glob("*.jpg"))) == 250


def test_import_from_paths_imports_500_files_beyond_single_request_limit(tmp_path, monkeypatch):
    """Path-import hundreds of files via chunked requests without 'Too many files' (#4)."""
    monkeypatch.setattr("app.api.routes.run_import_derivative_job", lambda *args, **kwargs: None)
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Large path import"}).json()
    folder = tmp_path / "card"
    total = 500
    for index in range(total):
        _write_jpeg(folder / f"frame-{index:04d}.jpg", (index % 200, 30, 90))

    remaining = [str(folder)]
    job_id = None
    imported_names: list[str] = []
    request_count = 0
    while remaining:
        request_count += 1
        payload = {
            "paths": remaining,
            "expected_total": total,
            "finalize": False,
        }
        if job_id is not None:
            payload["job_id"] = job_id
        response = client.post(f"/api/projects/{project['id']}/imports/from-paths", json=payload)
        assert response.status_code == 201, response.text
        body = response.json()
        assert "Too many files" not in response.text
        assert len(body["imported"]) <= IMPORT_MAX_FILES_PER_REQUEST
        imported_names.extend(item["filename"] for item in body["imported"])
        job_id = body["job"]["id"]
        remaining = body["remaining_paths"]
        assert body["expanded_total"] == total
        assert body["job"]["total_items"] == total

    finalize = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={
            "paths": [],
            "job_id": job_id,
            "expected_total": total,
            "finalize": True,
        },
    )
    assert finalize.status_code == 201, finalize.text
    assert finalize.json()["remaining_paths"] == []
    assert request_count >= total // IMPORT_MAX_FILES_PER_REQUEST
    assert len(imported_names) == total
    assert len(set(imported_names)) == total
    originals = Path(project["root_path"]) / "originals"
    assert len(list(originals.glob("*.jpg"))) == total
    with Session(get_engine()) as session:
        assert session.exec(select(Photo).where(Photo.project_id == project["id"])).all().__len__() == total


def test_import_from_paths_rejects_relative_and_empty(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Bad paths"}).json()
    empty = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": []},
    )
    assert empty.status_code == 422
    empty_without_job = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [], "finalize": True},
    )
    assert empty_without_job.status_code == 422
    empty_not_finalize = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [], "finalize": False, "job_id": "job-1"},
    )
    assert empty_not_finalize.status_code == 422
    relative = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": ["relative.jpg"]},
    )
    assert relative.status_code == 422


def test_import_from_paths_small_folder_finalize_only_follow_up_keeps_two_originals(tmp_path, monkeypatch):
    monkeypatch.setattr("app.api.routes.run_import_derivative_job", lambda *args, **kwargs: None)
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Small folder"}).json()
    folder = tmp_path / "card"
    hero = folder / "hero.jpg"
    alt = folder / "alt.jpg"
    _write_jpeg(hero, (210, 180, 40))
    _write_jpeg(alt, (30, 40, 90))
    before = {path: _source_fingerprint(path) for path in (hero, alt)}

    first = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(folder)], "finalize": False},
    )
    assert first.status_code == 201, first.text
    first_payload = first.json()
    assert first_payload["remaining_paths"] == []
    assert {item["filename"] for item in first_payload["imported"]} == {"hero.jpg", "alt.jpg"}
    job_id = first_payload["job"]["id"]

    second = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={
            "paths": [],
            "job_id": job_id,
            "expected_total": 2,
            "finalize": True,
        },
    )
    assert second.status_code == 201, second.text

    loaded = client.get(f"/api/projects/{project['id']}").json()
    assert loaded["total_images"] == 2
    assert loaded["source_root_path"] == str(folder.resolve())

    originals = Path(project["root_path"]) / "originals"
    assert sorted(path.name for path in originals.iterdir()) == ["alt.jpg", "hero.jpg"]

    with Session(get_engine()) as session:
        photos = session.exec(select(Photo).where(Photo.project_id == project["id"])).all()
        assert len(photos) == 2
        assert {photo.filename for photo in photos} == {"alt.jpg", "hero.jpg"}

    for path, expected in before.items():
        assert _source_fingerprint(path) == expected


def test_import_from_paths_concurrent_returns_409(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Overlap paths"}).json()
    first_file = tmp_path / "a.jpg"
    second_file = tmp_path / "b.jpg"
    _write_jpeg(first_file)
    _write_jpeg(second_file)
    first = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(first_file)], "finalize": False},
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(second_file)]},
    )
    assert second.status_code == 409


def test_import_from_paths_skips_unsupported(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Skip"}).json()
    jpeg = tmp_path / "keep.jpg"
    txt = tmp_path / "notes.txt"
    heic = tmp_path / "shot.heic"
    _write_jpeg(jpeg)
    txt.write_text("nope", encoding="utf-8")
    heic.write_bytes(b"not-heic")
    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(jpeg), str(txt), str(heic)]},
    )
    assert response.status_code == 201
    payload = response.json()
    assert [item["filename"] for item in payload["imported"]] == ["keep.jpg"]
    reasons = {item["filename"]: item["reason"] for item in payload["skipped"]}
    assert reasons["notes.txt"] == unsupported_image_reason("notes.txt")
    assert reasons["shot.heic"] == unsupported_image_reason("shot.heic")


def test_import_from_paths_records_source_root(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Source root"}).json()
    folder = tmp_path / "card"
    _write_jpeg(folder / "one.jpg")
    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(folder)], "finalize": True},
    )
    assert response.status_code == 201
    loaded = client.get(f"/api/projects/{project['id']}").json()
    assert loaded["source_root_path"] == str(folder.resolve())

    with Session(get_engine()) as session:
        photos = session.exec(select(Photo).where(Photo.project_id == project["id"])).all()
        assert photos


def test_multipart_import_returns_remaining_paths_and_expanded_total(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Multipart remaining"}).json()
    response = client.post(
        f"/api/projects/{project['id']}/imports",
        files=[("files", ("frame.jpg", _jpeg(), "image/jpeg"))],
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["remaining_paths"] == []
    assert payload["expanded_total"] == 1
