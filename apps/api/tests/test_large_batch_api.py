from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo


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
