from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.session import get_engine
from app.devtools.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_dataset
from app.main import create_app
from app.models.entities import Photo


def _wait_for_job(client: TestClient, project_id: str, job: dict) -> dict:
    current = job
    for _ in range(30):
        if current["status"] in {"complete", "failed"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


def test_photo_list_returns_2000_records_in_review_order(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Large batch"}).json()
    recommendation_cycle = ["Pick", "Maybe", "Unreviewed", "Reject"]

    with Session(get_engine()) as session:
        photos = [
            Photo(
                project_id=project["id"],
                original_path=f"/tmp/frame_{index:06d}.jpg",
                filename=f"frame_{index:06d}.jpg",
                ai_recommendation=recommendation_cycle[index % len(recommendation_cycle)],
                overall_score=index / 2000,
                processing_state="processed",
            )
            for index in range(2000)
        ]
        session.add_all(photos)
        session.commit()

    response = client.get(f"/api/projects/{project['id']}/photos")

    assert response.status_code == 200
    records = response.json()
    assert len(records) == 2000
    expected = sorted(
        records,
        key=lambda photo: (
            {"Pick": 0, "Maybe": 1, "Unreviewed": 2}.get(photo["ai_recommendation"], 3),
            -photo["overall_score"],
            photo["filename"],
        ),
    )
    assert [photo["filename"] for photo in records[:20]] == [photo["filename"] for photo in expected[:20]]
    assert [photo["filename"] for photo in records[-20:]] == [photo["filename"] for photo in expected[-20:]]


def test_100_synthetic_image_workflow_imports_and_processes(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Synthetic 100"}).json()
    source_dir = tmp_path / "source"
    paths = generate_synthetic_dataset(
        SyntheticDatasetConfig(output_dir=source_dir, count=100, width=64, height=48, burst_size=5)
    )

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", (path.name, path.read_bytes(), "image/jpeg")) for path in paths],
    )

    assert import_response.status_code == 201
    import_result = import_response.json()
    assert len(import_result["imported"]) == 100
    assert import_result["skipped"] == []

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code == 202
    job = _wait_for_job(client, project["id"], process_response.json())

    assert job["status"] == "complete"
    assert job["progress_percent"] == 100.0
    assert job["processed_items"] == 100
    assert job["failed_items"] == 0
    assert client.get(f"/api/projects/{project['id']}").json()["processed_images"] == 100
    groups = client.get(f"/api/projects/{project['id']}/groups").json()
    assert sum(group["photo_count"] for group in groups) == 100
