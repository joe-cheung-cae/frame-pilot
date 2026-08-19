import ast
import os
from pathlib import Path

import pytest
import uvicorn
from fastapi import FastAPI

from app.sidecar_main import apply_data_dir, bind_listen_socket, main, parse_args, ready_line


def test_parse_args_rejects_non_loopback_host(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--host", "0.0.0.0", "--data-dir", str(tmp_path)])
    assert exc_info.value.code == 2

    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--host", "192.168.1.5", "--data-dir", str(tmp_path)])
    assert exc_info.value.code == 2


def test_parse_args_rejects_missing_or_relative_data_dir():
    with pytest.raises(SystemExit) as exc_info:
        parse_args([])
    assert exc_info.value.code == 2

    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--data-dir", "relative/data"])
    assert exc_info.value.code == 2


def test_parse_args_accepts_absolute_data_dir(tmp_path):
    args = parse_args(["--data-dir", str(tmp_path), "--port", "0"])
    assert args.host == "127.0.0.1"
    assert args.port == 0
    assert args.data_dir == str(tmp_path)
    assert args.log_level == "info"


def test_bind_listen_socket_ephemeral_loopback():
    sock = bind_listen_socket("127.0.0.1", 0)
    try:
        host, port = sock.getsockname()[:2]
        assert host == "127.0.0.1"
        assert port != 0
    finally:
        sock.close()


def test_ready_line_uses_actual_port(tmp_path):
    rendered = ready_line("127.0.0.1", 54321, tmp_path)
    assert rendered == f"FRAMEPILOT_API ready host=127.0.0.1 port=54321 data_dir={tmp_path}"


def test_apply_data_dir_before_settings_load(tmp_path, monkeypatch):
    monkeypatch.delenv("FRAMEPILOT_DATA_DIR", raising=False)
    apply_data_dir(tmp_path)
    assert os.environ["FRAMEPILOT_DATA_DIR"] == str(tmp_path)

    from app.core.config import get_settings, reset_settings_cache

    reset_settings_cache()
    settings = get_settings()
    assert Path(settings.data_dir) == Path(tmp_path).resolve()


def test_help_exits_zero():
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--help"])
    assert exc_info.value.code == 0


def test_sidecar_main_does_not_import_app_main_at_module_level():
    source = Path(__file__).resolve().parents[1] / "app" / "sidecar_main.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("app.main"):
            raise AssertionError("sidecar_main must not import app.main at module top level")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "app.main" or alias.name.startswith("app.main."):
                    raise AssertionError("sidecar_main must not import app.main at module top level")


def test_main_passes_fastapi_object_and_ready_line(tmp_path, monkeypatch, capsys):
    captured: dict[str, object] = {}

    def fake_run(self, sockets=None):
        captured["app"] = self.config.app
        captured["sockets"] = sockets
        if sockets:
            for sock in sockets:
                sock.close()

    monkeypatch.setattr(uvicorn.Server, "run", fake_run)
    exit_code = main(["--data-dir", str(tmp_path), "--port", "0"])
    assert exit_code == 0
    assert isinstance(captured["app"], FastAPI)
    assert captured["app"] is not None
    assert not isinstance(captured["app"], str)

    output_lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(output_lines) == 1
    line = output_lines[0]
    assert line.startswith("FRAMEPILOT_API ready host=127.0.0.1 port=")
    assert f"data_dir={tmp_path}" in line
    port_token = line.split("port=", 1)[1].split(" ", 1)[0]
    assert port_token != "0"
    assert port_token.isdigit()
