import csv
import hashlib
import os
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app


def _jpeg(color: tuple[int, int, int]) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 48), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def _fingerprint(path: Path) -> tuple[int, int, str]:
    st = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return st.st_size, st.st_mtime_ns, digest


def _wait_for_job(client: TestClient, project_id: str, job: dict) -> dict:
    current = job
    for _ in range(40):
        if current["status"] in {"complete", "complete_with_errors", "failed", "cancelled"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


def _wait_for_export(client: TestClient, project_id: str, export_record: dict) -> dict:
    current = export_record
    for _ in range(40):
        if current["status"] in {"complete", "failed"}:
            return current
        response = client.get(f"/api/projects/{project_id}/exports/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


def test_path_import_process_pick_and_export_leaves_originals_unchanged(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(create_app())

    source_dir = tmp_path / "camera-card"
    source_dir.mkdir()
    pick_source = source_dir / "hero.jpg"
    other_source = source_dir / "alt.jpg"
    pick_bytes = _jpeg((210, 180, 40))
    other_bytes = _jpeg((30, 40, 90))
    pick_source.write_bytes(pick_bytes)
    other_source.write_bytes(other_bytes)
    before = {path: _fingerprint(path) for path in (pick_source, other_source)}
    source_names_before = sorted(path.name for path in source_dir.iterdir())

    def assert_originals_unchanged() -> None:
        assert sorted(path.name for path in source_dir.iterdir()) == source_names_before
        for path, expected in before.items():
            assert _fingerprint(path) == expected

    created = client.post("/api/projects", json={"name": "Path workflow"})
    assert created.status_code == 201
    project = created.json()
    assert_originals_unchanged()

    import_response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(source_dir)], "finalize": True},
    )
    assert import_response.status_code == 201, import_response.text
    import_result = import_response.json()
    assert import_result["remaining_paths"] == []
    assert import_result["expanded_total"] == 2
    assert {item["filename"] for item in import_result["imported"]} == {"hero.jpg", "alt.jpg"}
    import_job = _wait_for_job(client, project["id"], import_result["job"])
    assert import_job["status"] == "complete"
    assert import_job["processed_items"] == 2
    assert_originals_unchanged()

    originals = Path(project["root_path"]) / "originals"
    for item in import_result["imported"]:
        copy_path = Path(item["project_copy_path"])
        assert copy_path.is_relative_to(originals)
        assert copy_path.is_file()
        source = source_dir / item["filename"]
        assert copy_path.resolve() != source.resolve()
        assert copy_path.read_bytes() == source.read_bytes()
        if os.name != "nt":
            source_stat = source.stat()
            copy_stat = copy_path.stat()
            assert not (source_stat.st_ino == copy_stat.st_ino and source_stat.st_dev == copy_stat.st_dev)

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code == 202
    process_job = _wait_for_job(client, project["id"], process_response.json())
    assert process_job["status"] == "complete"
    assert process_job["processed_items"] == 2
    processed_project = client.get(f"/api/projects/{project['id']}").json()
    assert processed_project["processed_images"] == 2
    photos = client.get(f"/api/projects/{project['id']}/photos").json()
    assert len(photos) == 2
    assert all(photo["processing_state"] == "processed" for photo in photos)
    assert_originals_unchanged()

    pick_photo = next(photo for photo in photos if photo["filename"] == "hero.jpg")
    pick_response = client.patch(
        f"/api/projects/{project['id']}/photos/{pick_photo['id']}",
        json={"user_status": "Pick", "star_rating": 5},
    )
    assert pick_response.status_code == 200
    assert pick_response.json()["user_status"] == "Pick"
    assert_originals_unchanged()

    csv_response = client.post(
        f"/api/projects/{project['id']}/exports",
        json={"mode": "csv", "statuses": ["Pick"]},
    )
    assert csv_response.status_code == 201
    csv_export = _wait_for_export(client, project["id"], csv_response.json())
    assert csv_export["status"] == "complete"
    assert csv_export["selected_count"] == 1
    csv_path = Path(csv_export["output_path"])
    assert csv_path.parent == Path(project["root_path"]) / "exports" / "csv"
    assert csv_path.is_file()
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["filename"] for row in rows] == ["hero.jpg"]
    assert [row["status"] for row in rows] == ["Pick"]
    assert rows[0]["photo_id"] == pick_photo["id"]
    assert_originals_unchanged()

    zip_response = client.post(
        f"/api/projects/{project['id']}/exports",
        json={"mode": "zip", "statuses": ["Pick"]},
    )
    assert zip_response.status_code == 201
    zip_export = _wait_for_export(client, project["id"], zip_response.json())
    assert zip_export["status"] == "complete"
    zip_path = Path(zip_export["output_path"])
    assert zip_path.parent == Path(project["root_path"]) / "exports" / "zip"
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.namelist() == ["hero.jpg"]
        assert archive.read("hero.jpg") == pick_bytes
    assert_originals_unchanged()

    folder_response = client.post(
        f"/api/projects/{project['id']}/exports",
        json={"mode": "folder", "statuses": ["Pick"]},
    )
    assert folder_response.status_code == 201
    folder_export = _wait_for_export(client, project["id"], folder_response.json())
    assert folder_export["status"] == "complete"
    folder_path = Path(folder_export["output_path"])
    assert folder_path.parent == Path(project["root_path"]) / "exports" / "folders"
    assert folder_path.is_dir()
    exported_file = folder_path / "hero.jpg"
    assert exported_file.is_file()
    assert exported_file.read_bytes() == pick_bytes
    assert exported_file.resolve() != pick_source.resolve()
    assert_originals_unchanged()

    history = client.get(f"/api/projects/{project['id']}/exports")
    assert history.status_code == 200
    modes = {record["mode"] for record in history.json()}
    assert modes == {"csv", "zip", "folder"}
    assert pick_source.read_bytes() == pick_bytes
    assert other_source.read_bytes() == other_bytes
