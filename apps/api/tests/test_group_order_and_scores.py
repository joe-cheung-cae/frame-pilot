from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo, PhotoGroup


def _jpeg(color=(100, 120, 140)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 48), color=color).save(buffer, format="JPEG")
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


def test_photo_list_follows_group_sequence_not_random_uuid(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Group order"}).json()

    with Session(get_engine()) as session:
        early = PhotoGroup(
            id="ffffffffffffffffffff",
            project_id=project["id"],
            group_type="duplicate",
            sequence=1,
            photo_count=2,
        )
        late = PhotoGroup(
            id="00000000000000000000",
            project_id=project["id"],
            group_type="duplicate",
            sequence=2,
            photo_count=1,
        )
        session.add(early)
        session.add(late)
        session.commit()
        session.add_all(
            [
                Photo(
                    project_id=project["id"],
                    original_path="/tmp/a.jpg",
                    filename="a.jpg",
                    group_id=early.id,
                    ai_recommendation="Maybe",
                    overall_score=0.4,
                    processing_state="processed",
                ),
                Photo(
                    project_id=project["id"],
                    original_path="/tmp/b.jpg",
                    filename="b.jpg",
                    group_id=early.id,
                    ai_recommendation="Pick",
                    overall_score=0.9,
                    processing_state="processed",
                ),
                Photo(
                    project_id=project["id"],
                    original_path="/tmp/c.jpg",
                    filename="c.jpg",
                    group_id=late.id,
                    ai_recommendation="Pick",
                    overall_score=0.8,
                    processing_state="processed",
                ),
                Photo(
                    project_id=project["id"],
                    original_path="/tmp/ungrouped.jpg",
                    filename="ungrouped.jpg",
                    group_id=None,
                    ai_recommendation="Pick",
                    overall_score=1.0,
                    processing_state="failed",
                ),
            ]
        )
        session.commit()

    groups = client.get(f"/api/projects/{project['id']}/groups").json()
    photos = client.get(f"/api/projects/{project['id']}/photos").json()
    assert [group["sequence"] for group in groups] == [1, 2]
    assert [photo["filename"] for photo in photos] == ["b.jpg", "a.jpg", "c.jpg", "ungrouped.jpg"]


def test_processing_overall_score_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Score idempotence"}).json()

    for index, color in enumerate([(20, 20, 20), (240, 240, 240)]):
        response = client.post(
            f"/api/projects/{project['id']}/imports",
            files=[("files", (f"frame-{index}.jpg", _jpeg(color), "image/jpeg"))],
        )
        assert response.status_code == 201
        _wait_for_job(client, project["id"], response.json()["job"])

    process = client.post(f"/api/projects/{project['id']}/process")
    assert process.status_code == 202
    first_job = _wait_for_job(client, project["id"], process.json())
    assert first_job["status"] == "complete"
    first_photos = {
        photo["id"]: photo["overall_score"]
        for photo in client.get(f"/api/projects/{project['id']}/photos").json()
    }

    process_again = client.post(f"/api/projects/{project['id']}/process")
    second_job = _wait_for_job(client, project["id"], process_again.json())
    assert second_job["status"] == "complete"
    second_photos = {
        photo["id"]: photo["overall_score"]
        for photo in client.get(f"/api/projects/{project['id']}/photos").json()
    }
    assert first_photos == second_photos

    groups = client.get(f"/api/projects/{project['id']}/groups").json()
    assert groups
    summary = groups[0]["score_summary"]
    assert "best_score" in summary
    assert "score_gap" in summary
