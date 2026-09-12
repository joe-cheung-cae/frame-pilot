from fastapi.testclient import TestClient

from app.main import create_app
from app.services.desktop_menu import (
    MENU_COMMAND_QUEUE_LIMIT,
    clear_menu_commands,
    normalize_menu_command,
    push_menu_command,
    take_menu_command,
)


def _desktop_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DESKTOP", "1")
    clear_menu_commands()
    return TestClient(create_app())


def _web_client(monkeypatch) -> TestClient:
    monkeypatch.delenv("FRAMEPILOT_DESKTOP", raising=False)
    clear_menu_commands()
    return TestClient(create_app())


def test_menu_command_endpoints_404_when_desktop_unset(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = _web_client(monkeypatch)

    get_response = client.get("/api/desktop/menu-command")
    post_response = client.post("/api/desktop/menu-command", json={"command": "import"})

    assert get_response.status_code == 404
    assert post_response.status_code == 404


def test_menu_command_queue_is_fifo_take(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = _desktop_client(monkeypatch)

    empty = client.get("/api/desktop/menu-command")
    assert empty.status_code == 200
    assert empty.json() == {"command": None}
    assert empty.headers["cache-control"] == "no-store"

    first = client.post("/api/desktop/menu-command", json={"command": "import"})
    second = client.post("/api/desktop/menu-command", json={"command": "export"})
    assert first.status_code == 204
    assert second.status_code == 204

    taken_import = client.get("/api/desktop/menu-command")
    taken_export = client.get("/api/desktop/menu-command")
    taken_empty = client.get("/api/desktop/menu-command")
    assert taken_import.json() == {"command": "import"}
    assert taken_export.json() == {"command": "export"}
    assert taken_empty.json() == {"command": None}


def test_menu_command_rejects_unknown_and_native_owned_ids(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    client = _desktop_client(monkeypatch)

    unknown = client.post("/api/desktop/menu-command", json={"command": "open-data-folder"})
    blank = client.post("/api/desktop/menu-command", json={"command": "  "})
    assert unknown.status_code == 422
    assert blank.status_code == 422
    assert client.get("/api/desktop/menu-command").json() == {"command": None}


def test_normalize_menu_command_accepts_navigable_ids():
    assert normalize_menu_command(" import ") == "import"
    assert normalize_menu_command("quit") is None
    clear_menu_commands()
    assert push_menu_command("cull") == "cull"
    assert take_menu_command() == "cull"
    assert take_menu_command() is None


def test_menu_command_queue_drops_oldest_when_full():
    clear_menu_commands()
    for index in range(MENU_COMMAND_QUEUE_LIMIT + 1):
        pushed = push_menu_command("new" if index == 0 else "import")
        assert pushed in {"new", "import"}
    assert take_menu_command() == "import"
    clear_menu_commands()
