import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.project_roots import clear_registered_roots
from app.main import create_app


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    clear_registered_roots()
    yield tmp_path
    clear_registered_roots()


def _desktop_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DESKTOP", "1")
    return TestClient(create_app())


def _web_client(monkeypatch) -> TestClient:
    monkeypatch.delenv("FRAMEPILOT_DESKTOP", raising=False)
    return TestClient(create_app())


def _outside_dir(data_dir: Path, name: str = "outside-project-root") -> Path:
    path = data_dir.parent / name
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def test_project_root_endpoints_404_when_desktop_unset(data_dir, monkeypatch):
    client = _web_client(monkeypatch)
    outside = _outside_dir(data_dir)

    get_response = client.get("/api/desktop/project-roots")
    post_response = client.post("/api/desktop/project-roots", json={"path": str(outside)})

    assert get_response.status_code == 404
    assert post_response.status_code == 404


def test_create_project_rejects_outside_root_until_registered(data_dir, monkeypatch):
    client = _desktop_client(monkeypatch)
    outside = _outside_dir(data_dir)

    before = client.post("/api/projects", json={"name": "Outside", "root_path": str(outside)})
    assert before.status_code == 422
    assert "allowlisted" in before.json()["detail"]
    assert client.get("/api/projects").json() == []

    registered = client.post("/api/desktop/project-roots", json={"path": str(outside)})
    assert registered.status_code == 201
    assert Path(registered.json()["path"]) == outside

    listed = client.get("/api/desktop/project-roots")
    assert listed.status_code == 200
    assert outside.as_posix() in listed.json()["roots"] or str(outside) in listed.json()["roots"]

    created = client.post("/api/projects", json={"name": "Outside", "root_path": str(outside)})
    assert created.status_code == 201
    assert Path(created.json()["root_path"]) == outside


def _home_outside_data_dir(data_dir: Path, monkeypatch) -> Path:
    # Linux/WSL desktop-dev stores data under the repo, so home is not a
    # parent of data_dir and _is_data_dir_or_parent would not reject it.
    home = data_dir.parent / f"{data_dir.name}-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    resolved = home.resolve()
    assert not data_dir.resolve().is_relative_to(resolved)
    return resolved


def test_register_root_rejects_home_directory_when_data_dir_is_outside_home(data_dir, monkeypatch):
    home = _home_outside_data_dir(data_dir, monkeypatch)
    client = _desktop_client(monkeypatch)

    cases = [str(Path.home()), str(home), os.environ["HOME"], str(home) + os.sep]
    for path in cases:
        response = client.post("/api/desktop/project-roots", json={"path": path})
        assert response.status_code == 422, path
        assert "system directory" in response.json()["detail"]

    listed = client.get("/api/desktop/project-roots")
    assert listed.status_code == 200
    assert listed.json()["roots"] == []


def test_register_root_keeps_subdirectory_of_home(data_dir, monkeypatch):
    home = _home_outside_data_dir(data_dir, monkeypatch)
    pictures = home / "Pictures"
    pictures.mkdir()
    client = _desktop_client(monkeypatch)

    registered = client.post("/api/desktop/project-roots", json={"path": str(pictures)})
    assert registered.status_code == 201
    assert Path(registered.json()["path"]) == pictures


def test_register_root_rejects_system_data_dir_relative_and_file_paths(data_dir, monkeypatch):
    client = _desktop_client(monkeypatch)
    not_a_dir = data_dir / "not-a-directory"
    not_a_dir.write_text("file")

    cases = [
        "/",
        "/etc",
        r"C:\Windows",
        str(data_dir),
        "relative-root",
        str(not_a_dir),
    ]
    for path in cases:
        response = client.post("/api/desktop/project-roots", json={"path": path})
        assert response.status_code == 422, path


def test_registered_roots_survive_create_app_restart(data_dir, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DESKTOP", "1")
    outside = _outside_dir(data_dir, "restart-root")
    first = TestClient(create_app())
    assert first.post("/api/desktop/project-roots", json={"path": str(outside)}).status_code == 201

    restarted = TestClient(create_app())
    listed = restarted.get("/api/desktop/project-roots")
    assert listed.status_code == 200
    roots = listed.json()["roots"]
    assert str(outside) in roots or outside.as_posix() in roots

    created = restarted.post(
        "/api/projects",
        json={"name": "Restarted", "root_path": str(outside), "acknowledge_nonempty": True},
    )
    assert created.status_code == 201


def test_registered_nonempty_root_requires_acknowledge_and_keeps_existing_files(data_dir, monkeypatch):
    client = _desktop_client(monkeypatch)
    outside = _outside_dir(data_dir, "nonempty-root")
    existing = outside / "keep-me.txt"
    existing.write_text("do not touch", encoding="utf-8")
    before = existing.stat()

    registered = client.post("/api/desktop/project-roots", json={"path": str(outside)})
    assert registered.status_code == 201

    without_flag = client.post("/api/projects", json={"name": "Nonempty", "root_path": str(outside)})
    assert without_flag.status_code == 422
    assert without_flag.json()["detail"] == (
        "Project root path is not empty; pass acknowledge_nonempty=true to use it anyway"
    )
    assert existing.read_text(encoding="utf-8") == "do not touch"
    assert existing.stat().st_size == before.st_size
    assert existing.stat().st_mtime_ns == before.st_mtime_ns
    assert client.get("/api/projects").json() == []

    with_flag = client.post(
        "/api/projects",
        json={"name": "Nonempty", "root_path": str(outside), "acknowledge_nonempty": True},
    )
    assert with_flag.status_code == 201
    assert Path(with_flag.json()["root_path"]) == outside
    assert existing.exists()
    assert existing.read_text(encoding="utf-8") == "do not touch"
    assert existing.stat().st_size == before.st_size
    assert existing.stat().st_mtime_ns == before.st_mtime_ns
    assert (outside / "originals").is_dir()


def test_register_root_caps_at_fifty(data_dir, monkeypatch):
    client = _desktop_client(monkeypatch)
    bucket = _outside_dir(data_dir, "root-bucket")
    for index in range(50):
        root = bucket / f"root-{index}"
        root.mkdir()
        response = client.post("/api/desktop/project-roots", json={"path": str(root)})
        assert response.status_code == 201, index

    extra = bucket / "root-50"
    extra.mkdir()
    overflow = client.post("/api/desktop/project-roots", json={"path": str(extra)})
    assert overflow.status_code == 422
    listed = client.get("/api/desktop/project-roots")
    assert len(listed.json()["roots"]) == 50
