from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, select

from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo, ProcessingJob
from app.services.importing import IMPORT_MAX_FILES_PER_REQUEST


def _jpeg(color=(120, 150, 90)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (48, 36), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def _wait_for_job(client: TestClient, project_id: str, job: dict) -> dict:
    current = job
    for _ in range(40):
        if current["status"] in {"complete", "complete_with_errors", "failed", "cancelled"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


def test_import_rejects_more_than_max_files_per_request(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Too many"}).json()
    files = [
        ("files", (f"frame-{index}.jpg", _jpeg((index % 200, 40, 80)), "image/jpeg"))
        for index in range(IMPORT_MAX_FILES_PER_REQUEST + 1)
    ]
    response = client.post(f"/api/projects/{project['id']}/imports", files=files)
    assert response.status_code == 422
    assert str(IMPORT_MAX_FILES_PER_REQUEST) in response.json()["detail"]


def test_chunked_import_appends_to_one_job_and_finalizes(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Chunked"}).json()

    first = client.post(
        f"/api/projects/{project['id']}/imports",
        data={"expected_total": "3", "finalize": "false"},
        files=[
            ("files", ("a.jpg", _jpeg((10, 20, 30)), "image/jpeg")),
            ("files", ("b.jpg", _jpeg((40, 50, 60)), "image/jpeg")),
        ],
    )
    assert first.status_code == 201
    first_payload = first.json()
    job_id = first_payload["job"]["id"]
    assert first_payload["job"]["status"] == "running"
    assert first_payload["job"]["total_items"] == 3

    second = client.post(
        f"/api/projects/{project['id']}/imports",
        data={"job_id": job_id, "expected_total": "3", "finalize": "true"},
        files=[("files", ("c.jpg", _jpeg((70, 80, 90)), "image/jpeg"))],
    )
    assert second.status_code == 201
    second_payload = second.json()
    assert second_payload["job"]["id"] == job_id
    job = _wait_for_job(client, project["id"], second_payload["job"])
    assert job["status"] == "complete"

    photos = client.get(f"/api/projects/{project['id']}/photos", params={"limit": 50}).json()
    assert len(photos) == 3
    with Session(get_engine()) as session:
        jobs = session.exec(select(ProcessingJob).where(ProcessingJob.project_id == project["id"])).all()
        assert len(jobs) == 1
        assert {photo.filename for photo in session.exec(select(Photo).where(Photo.project_id == project["id"]))} == {
            "a.jpg",
            "b.jpg",
            "c.jpg",
        }


def test_overlapping_import_without_job_id_returns_409(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Overlap"}).json()

    first = client.post(
        f"/api/projects/{project['id']}/imports",
        data={"expected_total": "2", "finalize": "false"},
        files=[("files", ("a.jpg", _jpeg(), "image/jpeg"))],
    )
    assert first.status_code == 201
    active_job_id = first.json()["job"]["id"]

    second = client.post(
        f"/api/projects/{project['id']}/imports",
        files=[("files", ("b.jpg", _jpeg((1, 2, 3)), "image/jpeg"))],
    )
    assert second.status_code == 409
    detail = second.json()["detail"]
    assert detail["job_id"] == active_job_id
