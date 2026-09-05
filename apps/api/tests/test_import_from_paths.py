import hashlib
import os
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, select

from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo
from app.services.importing import IMPORT_COPY_CHUNK_SIZE, IMPORT_MAX_FILES_PER_REQUEST, unsupported_image_reason
from tests.avif_helpers import tiny_avif_bytes
from tests.heic_helpers import tiny_heic_bytes


def _jpeg(color=(120, 150, 90)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (16, 12), color=color).save(buffer, format="JPEG", quality=40)
    return buffer.getvalue()


def _write_jpeg(path: Path, color=(120, 150, 90)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_jpeg(color))


def _source_fingerprint(path: Path) -> tuple[int, int, str]:
    st = path.stat()
    return st.st_size, st.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def _open_fd_count() -> int:
    fd_dir = Path("/proc/self/fd")
    if fd_dir.is_dir():
        return len(list(fd_dir.iterdir()))
    return len(os.listdir("/dev/fd")) if Path("/dev/fd").is_dir() else 0


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    return TestClient(create_app())


def _wait_for_job(client: TestClient, project_id: str, job: dict) -> dict:
    current = job
    for _ in range(20):
        if current["status"] in {"complete", "complete_with_errors", "failed", "cancelled"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


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


def test_import_from_paths_imports_2000_files_beyond_single_request_limit(tmp_path, monkeypatch):
    """Chunked path-import of 2000 tiny JPEGs without 'Too many files' (#68 / legacy #4).

    Asserts mid-job progress advances between chunks and peak open FDs stay bounded
    (register path uses chunked copy + context-managed closes; opens must not scale with N).
    """
    monkeypatch.setattr("app.api.routes.run_import_derivative_job", lambda *args, **kwargs: None)
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Large path import"}).json()
    folder = tmp_path / "card"
    total = 2000
    for index in range(total):
        _write_jpeg(folder / f"frame-{index:04d}.jpg", (index % 200, 30, 90))

    baseline_fds = _open_fd_count()
    peak_fds = baseline_fds
    concurrent_opens = 0
    peak_concurrent_opens = 0
    original_open = Path.open

    def tracking_open(self, *args, **kwargs):
        nonlocal concurrent_opens, peak_concurrent_opens
        handle = original_open(self, *args, **kwargs)
        concurrent_opens += 1
        peak_concurrent_opens = max(peak_concurrent_opens, concurrent_opens)
        close = handle.close

        def tracked_close() -> None:
            nonlocal concurrent_opens
            if not getattr(handle, "_fp_tracked_closed", False):
                handle._fp_tracked_closed = True  # type: ignore[attr-defined]
                concurrent_opens = max(0, concurrent_opens - 1)
            close()

        handle.close = tracked_close  # type: ignore[method-assign]
        return handle

    monkeypatch.setattr(Path, "open", tracking_open)

    remaining = [str(folder)]
    job_id = None
    imported_names: list[str] = []
    request_count = 0
    previous_processed = 0
    progress_samples: list[int] = []
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
        assert "400" not in str(response.status_code)
        assert len(body["imported"]) <= IMPORT_MAX_FILES_PER_REQUEST
        imported_names.extend(item["filename"] for item in body["imported"])
        job_id = body["job"]["id"]
        remaining = body["remaining_paths"]
        assert body["expanded_total"] == total
        assert body["job"]["total_items"] == total
        processed = body["job"]["processed_items"]
        progress_samples.append(processed)
        assert processed > previous_processed, (
            f"progress must advance during chunks; was {previous_processed}, now {processed}"
        )
        previous_processed = processed
        peak_fds = max(peak_fds, _open_fd_count())

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
    assert request_count > 1
    assert len(imported_names) == total
    assert len(set(imported_names)) == total
    assert len(progress_samples) >= 2
    assert progress_samples[-1] == total
    originals = Path(project["root_path"]) / "originals"
    assert len(list(originals.glob("*.jpg"))) == total
    # Temp disk: register writes straight into project originals; no orphan staging tree.
    staging = tmp_path / "staging"
    assert not staging.exists()
    assert peak_concurrent_opens <= 4, (
        f"open handles must stay O(1) via chunked copy ({IMPORT_COPY_CHUNK_SIZE} bytes); "
        f"peak concurrent Path.open={peak_concurrent_opens}"
    )
    assert peak_fds - baseline_fds < 64, (
        f"peak FD growth must stay bounded, not scale with N={total}; "
        f"baseline={baseline_fds} peak={peak_fds}"
    )
    with Session(get_engine()) as session:
        assert session.exec(select(Photo).where(Photo.project_id == project["id"])).all().__len__() == total


def test_copy_file_to_path_uses_bounded_chunks_and_closes_handles(tmp_path, monkeypatch):
    """Structural FD/temp bound: one destination open, chunked reads, handle closed (#68)."""
    from app.services import importing

    source = BytesIO(b"x" * (IMPORT_COPY_CHUNK_SIZE * 3 + 17))
    destination = tmp_path / "copy.bin"
    open_counts: list[int] = []
    concurrent = 0
    original_open = Path.open

    def tracking_open(self, *args, **kwargs):
        nonlocal concurrent
        handle = original_open(self, *args, **kwargs)
        concurrent += 1
        open_counts.append(concurrent)
        close = handle.close

        def tracked_close() -> None:
            nonlocal concurrent
            if not getattr(handle, "_fp_tracked_closed", False):
                handle._fp_tracked_closed = True  # type: ignore[attr-defined]
                concurrent -= 1
            close()

        handle.close = tracked_close  # type: ignore[method-assign]
        return handle

    monkeypatch.setattr(Path, "open", tracking_open)
    importing._copy_file_to_path(source, destination)
    assert destination.read_bytes() == b"x" * (IMPORT_COPY_CHUNK_SIZE * 3 + 17)
    assert max(open_counts) == 1
    assert concurrent == 0


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
    heif = tmp_path / "frame.heif"
    heic_payload = tiny_heic_bytes(color=(12, 34, 56))
    heif_payload = tiny_heic_bytes(color=(90, 12, 40))
    _write_jpeg(jpeg)
    txt.write_text("nope", encoding="utf-8")
    heic.write_bytes(heic_payload)
    heif.write_bytes(heif_payload)
    before = _source_fingerprint(heic)
    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(jpeg), str(txt), str(heic), str(heif)]},
    )
    assert response.status_code == 201
    body = response.json()
    assert {item["filename"] for item in body["imported"]} == {"keep.jpg", "shot.heic", "frame.heif"}
    reasons = {item["filename"]: item["reason"] for item in body["skipped"]}
    assert reasons["notes.txt"] == unsupported_image_reason("notes.txt")
    assert "shot.heic" not in reasons
    originals = Path(project["root_path"]) / "originals"
    assert (originals / "shot.heic").read_bytes() == heic_payload
    assert (originals / "frame.heif").read_bytes() == heif_payload
    assert _source_fingerprint(heic) == before
    job = _wait_for_job(client, project["id"], body["job"])
    assert job["status"] in {"complete", "complete_with_errors"}
    photos = {photo["filename"]: photo for photo in client.get(f"/api/projects/{project['id']}/photos").json()}
    assert photos["shot.heic"]["processing_state"] == "imported"
    assert photos["frame.heif"]["processing_state"] == "imported"
    assert Path(photos["shot.heic"]["thumbnail_path"]).suffix == ".webp"


def test_import_from_paths_garbage_heic_fails_that_file(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Garbage HEIC path"}).json()
    jpeg = tmp_path / "keep.jpg"
    heic = tmp_path / "shot.heic"
    _write_jpeg(jpeg)
    heic.write_bytes(b"not-heic")
    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(jpeg), str(heic)]},
    )
    assert response.status_code == 201
    body = response.json()
    assert {item["filename"] for item in body["imported"]} == {"keep.jpg", "shot.heic"}
    assert body["skipped"] == []
    job = _wait_for_job(client, project["id"], body["job"])
    assert job["status"] == "complete_with_errors"
    assert job["failed_items"] == 1
    photos = {photo["filename"]: photo for photo in client.get(f"/api/projects/{project['id']}/photos").json()}
    assert photos["keep.jpg"]["processing_state"] == "imported"
    assert photos["shot.heic"]["processing_state"] == "failed"


def test_import_from_paths_accepts_avif_and_still_skips_raw(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "AVIF path"}).json()
    jpeg = tmp_path / "keep.jpg"
    avif = tmp_path / "still.avif"
    raw = tmp_path / "frame.dng"
    avif_payload = tiny_avif_bytes(color=(12, 34, 56))
    _write_jpeg(jpeg)
    avif.write_bytes(avif_payload)
    raw.write_bytes(b"not-raw")
    before = _source_fingerprint(avif)
    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(jpeg), str(avif), str(raw)]},
    )
    assert response.status_code == 201
    body = response.json()
    assert {item["filename"] for item in body["imported"]} == {"keep.jpg", "still.avif"}
    reasons = {item["filename"]: item["reason"] for item in body["skipped"]}
    assert reasons["frame.dng"] == unsupported_image_reason("frame.dng")
    originals = Path(project["root_path"]) / "originals"
    assert (originals / "still.avif").read_bytes() == avif_payload
    assert _source_fingerprint(avif) == before
    job = _wait_for_job(client, project["id"], body["job"])
    assert job["status"] in {"complete", "complete_with_errors"}
    photos = {photo["filename"]: photo for photo in client.get(f"/api/projects/{project['id']}/photos").json()}
    assert photos["still.avif"]["processing_state"] == "imported"
    assert Path(photos["still.avif"]["thumbnail_path"]).suffix == ".webp"


def test_import_from_paths_garbage_avif_fails_that_file(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Garbage AVIF path"}).json()
    jpeg = tmp_path / "keep.jpg"
    avif = tmp_path / "shot.avif"
    _write_jpeg(jpeg)
    avif.write_bytes(b"not-a-real-avif")
    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(jpeg), str(avif)]},
    )
    assert response.status_code == 201
    body = response.json()
    assert {item["filename"] for item in body["imported"]} == {"keep.jpg", "shot.avif"}
    assert body["skipped"] == []
    job = _wait_for_job(client, project["id"], body["job"])
    assert job["status"] == "complete_with_errors"
    assert job["failed_items"] == 1
    photos = {photo["filename"]: photo for photo in client.get(f"/api/projects/{project['id']}/photos").json()}
    assert photos["keep.jpg"]["processing_state"] == "imported"
    assert photos["shot.avif"]["processing_state"] == "failed"


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
