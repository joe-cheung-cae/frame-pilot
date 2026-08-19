import asyncio

import pytest
from fastapi.testclient import TestClient

from app.core.origins import allowed_origins, host_is_allowed
from app.main import create_app


def _client(tmp_path, monkeypatch, *, desktop: bool = False) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    if desktop:
        monkeypatch.setenv("FRAMEPILOT_DESKTOP", "1")
    else:
        monkeypatch.delenv("FRAMEPILOT_DESKTOP", raising=False)
    return TestClient(create_app())


def _asgi_status(
    app,
    method: str,
    path: str,
    headers: list[tuple[bytes, bytes]] | None = None,
    body: bytes = b"",
) -> int:
    sent: list[dict] = []

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers or [],
        "client": ("127.0.0.1", 123),
        "server": ("127.0.0.1", 8000),
    }
    asyncio.run(app(scope, receive, send))
    start = next(item for item in sent if item["type"] == "http.response.start")
    return start["status"]


def test_allowed_origins_web_only_by_default(monkeypatch):
    monkeypatch.delenv("FRAMEPILOT_DESKTOP", raising=False)
    origins = allowed_origins()
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins
    assert "http://localhost:3100" in origins
    assert "http://127.0.0.1:3100" in origins
    assert "tauri://localhost" not in origins
    assert "http://localhost:1420" not in origins


def test_allowed_origins_include_desktop_when_enabled(monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DESKTOP", "1")
    origins = allowed_origins()
    assert "http://localhost:1420" in origins
    assert "http://127.0.0.1:1420" in origins
    assert "http://tauri.localhost" in origins
    assert "https://tauri.localhost" in origins
    assert "tauri://localhost" in origins


def test_testserver_is_not_allowed_in_production_host_policy():
    assert not host_is_allowed("testserver")
    assert not host_is_allowed("testserver:80")


def test_post_projects_allows_localhost_origin(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/projects",
        json={"name": "Local web"},
        headers={"Origin": "http://localhost:3000", "Host": "127.0.0.1:8000"},
    )
    assert response.status_code == 201


def test_post_projects_rejects_evil_origin(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/projects",
        json={"name": "Evil"},
        headers={"Origin": "https://evil.example", "Host": "127.0.0.1:8000"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Origin not allowed for local FramePilot API"


@pytest.mark.parametrize("origin", ["tauri://localhost", "http://localhost:1420"])
def test_post_projects_rejects_desktop_origin_outside_desktop_mode(tmp_path, monkeypatch, origin):
    client = _client(tmp_path, monkeypatch, desktop=False)
    response = client.post(
        "/api/projects",
        json={"name": "Tauri"},
        headers={"Origin": origin, "Host": "127.0.0.1:8000"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Origin not allowed for local FramePilot API"


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
)
def test_post_projects_allows_desktop_origins_in_desktop_mode(tmp_path, monkeypatch, origin):
    client = _client(tmp_path, monkeypatch, desktop=True)
    response = client.post(
        "/api/projects",
        json={"name": "Tauri"},
        headers={"Origin": origin, "Host": "127.0.0.1:8000"},
    )
    assert response.status_code == 201


def test_post_projects_without_origin_is_allowed(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/projects",
        json={"name": "No origin"},
        headers={"Host": "127.0.0.1:8000"},
    )
    assert response.status_code == 201


def test_get_projects_rejects_non_loopback_host(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    denied = client.get("/api/projects", headers={"Host": "attacker.example"})
    assert denied.status_code == 403
    allowed = client.get("/api/projects", headers={"Host": "127.0.0.1:8000"})
    assert allowed.status_code == 200


def test_get_with_evil_origin_and_loopback_host_is_allowed(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get(
        "/api/projects",
        headers={"Origin": "https://evil.example", "Host": "127.0.0.1:8000"},
    )
    assert response.status_code == 200


def test_desktop_mode_still_rejects_attacker_host(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, desktop=True)
    response = client.get("/api/projects", headers={"Host": "attacker.example"})
    assert response.status_code == 403
    posted = client.post(
        "/api/projects",
        json={"name": "Attacker host"},
        headers={"Host": "attacker.example", "Origin": "tauri://localhost"},
    )
    assert posted.status_code == 403


def test_missing_host_is_rejected_on_get_and_post(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("FRAMEPILOT_DESKTOP", raising=False)
    app = create_app()
    assert _asgi_status(app, "GET", "/api/projects") == 403
    assert (
        _asgi_status(
            app,
            "POST",
            "/api/projects",
            headers=[(b"content-type", b"application/json")],
            body=b'{"name":"Missing host"}',
        )
        == 403
    )


def test_desktop_cors_preflight_for_tauri_origin(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, desktop=True)
    response = client.options(
        "/api/projects",
        headers={
            "Origin": "tauri://localhost",
            "Access-Control-Request-Method": "POST",
            "Host": "127.0.0.1:8000",
        },
    )
    assert response.status_code in {200, 204}
    assert response.headers.get("access-control-allow-origin") == "tauri://localhost"
