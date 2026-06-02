from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app


def _image_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (80, 60), color=(120, 150, 90))
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_import_process_update_and_export_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    project = client.post("/api/projects", json={"name": "Smoke test"}).json()

    import_response = client.post(
        f"/api/projects/{project['id']}/import",
        files=[("files", ("frame.jpg", _image_bytes(), "image/jpeg"))],
    )

    assert import_response.status_code == 201
    photo = import_response.json()[0]
    assert photo["filename"] == "frame.jpg"
    assert photo["thumbnail_path"]
    assert photo["preview_path"]

    process_response = client.post(f"/api/projects/{project['id']}/process")
    assert process_response.status_code == 202
    assert process_response.json()["status"] == "complete"

    groups = client.get(f"/api/projects/{project['id']}/groups").json()
    assert len(groups) == 1
    assert groups[0]["representative_photo_id"] == photo["id"]

    update_response = client.patch(
        f"/api/projects/{project['id']}/photos/{photo['id']}",
        json={"user_status": "Pick", "star_rating": 5},
    )
    assert update_response.status_code == 200
    assert update_response.json()["user_status"] == "Pick"

    export_response = client.post(
        f"/api/projects/{project['id']}/export",
        json={"mode": "csv", "statuses": ["Pick"]},
    )
    assert export_response.status_code == 201
    assert export_response.json()["output_path"].endswith("selection.csv")
