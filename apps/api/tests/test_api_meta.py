from pathlib import Path

from fastapi.testclient import TestClient

from app.core.version import APP_VERSION, SERVICE_NAME
from app.main import create_app


def _client(tmp_path, monkeypatch, *, data_dir: Path | None = None, desktop: str | None = None) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(data_dir or tmp_path))
    if desktop is None:
        monkeypatch.delenv("FRAMEPILOT_DESKTOP", raising=False)
    else:
        monkeypatch.setenv("FRAMEPILOT_DESKTOP", desktop)
    return TestClient(create_app())


def test_api_meta_returns_monkeypatched_data_dir(tmp_path, monkeypatch):
    data_dir = tmp_path / "custom-data"
    client = _client(tmp_path, monkeypatch, data_dir=data_dir)

    response = client.get("/api/meta")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "version": APP_VERSION,
        "service": SERVICE_NAME,
        "data_dir": str(data_dir.resolve()),
        "desktop_mode": False,
    }


def test_api_meta_desktop_mode_follows_env(tmp_path, monkeypatch):
    unset_client = _client(tmp_path, monkeypatch)
    assert unset_client.get("/api/meta").json()["desktop_mode"] is False

    desktop_client = _client(tmp_path, monkeypatch, desktop="1")
    assert desktop_client.get("/api/meta").json()["desktop_mode"] is True

    disabled_client = _client(tmp_path, monkeypatch, desktop="0")
    assert disabled_client.get("/api/meta").json()["desktop_mode"] is False


def test_health_payloads_do_not_include_meta_fields(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, data_dir=tmp_path / "health-data", desktop="1")
    expected = {"status": "ok", "version": APP_VERSION, "service": SERVICE_NAME}

    for path in ("/health", "/api/health"):
        payload = client.get(path).json()
        assert payload == expected
        assert "data_dir" not in payload
        assert "desktop_mode" not in payload
