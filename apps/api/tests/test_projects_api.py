from fastapi.testclient import TestClient

from app.main import create_app


def test_create_and_list_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.post("/api/projects", json={"name": "Wedding selects"})

    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Wedding selects"
    assert created["source_mode"] == "copy"
    assert created["source_root_path"] is None
    assert created["schema_version"] == 2
    assert created["total_images"] == 0
    assert created["processed_images"] == 0
    assert created["last_processed_at"] is None

    list_response = client.get("/api/projects")

    assert list_response.status_code == 200
    projects = list_response.json()
    assert len(projects) == 1
    assert projects[0]["id"] == created["id"]


def test_create_project_rejects_empty_name(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.post("/api/projects", json={"name": "  "})

    assert response.status_code == 422


def test_get_project_returns_404_for_missing_project(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.get("/api/projects/missing")

    assert response.status_code == 404
