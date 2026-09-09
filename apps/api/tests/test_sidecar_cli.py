import ast
import asyncio
import logging
import os
from pathlib import Path

import pytest
import uvicorn
from fastapi import FastAPI

from app.sidecar_main import (
    announce_ready,
    apply_data_dir,
    bind_listen_socket,
    main,
    parse_args,
    ready_line,
    ready_marker_path,
    serve,
    write_ready_marker,
)


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


def test_announce_ready_writes_marker_and_stderr(tmp_path, capsys):
    line = announce_ready("127.0.0.1", 54321, tmp_path)
    expected = f"FRAMEPILOT_API ready host=127.0.0.1 port=54321 data_dir={tmp_path}"
    assert line == expected
    marker = ready_marker_path(tmp_path)
    assert marker.is_file()
    assert marker.read_text(encoding="utf-8").strip() == expected
    captured = capsys.readouterr()
    assert captured.out.strip() == expected
    assert expected in captured.err
    written = write_ready_marker(tmp_path, "FRAMEPILOT_API ready host=127.0.0.1 port=9 data_dir=/tmp")
    assert written == marker


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
    configured = captured["app"]
    assert configured is not None
    assert not isinstance(configured, str)
    inner = configured.app if hasattr(configured, "app") and not isinstance(configured, FastAPI) else configured
    assert isinstance(inner, FastAPI)

    captured = capsys.readouterr()
    output_lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(output_lines) == 1
    line = output_lines[0]
    assert line.startswith("FRAMEPILOT_API ready host=127.0.0.1 port=")
    assert f"data_dir={tmp_path}" in line
    port_token = line.split("port=", 1)[1].split(" ", 1)[0]
    assert port_token != "0"
    assert port_token.isdigit()
    marker = ready_marker_path(tmp_path)
    assert marker.is_file()
    assert marker.read_text(encoding="utf-8").strip() == line
    assert line in captured.err


def _capture_serve_config(monkeypatch, os_name: str) -> dict[str, object]:
    captured: dict[str, object] = {}

    class FakeConfig:
        def __init__(self, app, **kwargs):
            self.app = app
            captured["kwargs"] = kwargs

    class FakeServer:
        def __init__(self, config):
            self.config = config

        def run(self, sockets=None):
            captured["sockets"] = sockets

    monkeypatch.setattr("app.sidecar_main.os.name", os_name)
    monkeypatch.setattr("app.sidecar_main.uvicorn.Config", FakeConfig)
    monkeypatch.setattr("app.sidecar_main.uvicorn.Server", FakeServer)

    sock = bind_listen_socket("127.0.0.1", 0)
    try:
        serve(FastAPI(), sock)
    finally:
        sock.close()
    return captured


def test_serve_forces_asyncio_loop_on_windows(monkeypatch):
    captured = _capture_serve_config(monkeypatch, "nt")
    assert captured["kwargs"]["loop"] == "asyncio"


def test_serve_uses_auto_loop_off_windows(monkeypatch):
    captured = _capture_serve_config(monkeypatch, "posix")
    assert captured["kwargs"]["loop"] == "auto"


def test_pyinstaller_spec_includes_asyncio_loop_and_httptools_impl():
    spec = Path(__file__).resolve().parents[3] / "packaging" / "pyinstaller" / "framepilot-api.spec"
    text = spec.read_text(encoding="utf-8")
    start = text.index("hiddenimports = [")
    end = text.index("]", start)
    hiddenimports = text[start:end]
    assert '"uvicorn.loops.asyncio"' in hiddenimports
    assert '"uvicorn.protocols.http.httptools_impl"' in hiddenimports
    assert '"PIL.AvifImagePlugin"' in hiddenimports
    assert '"PIL._avif"' in hiddenimports


def test_access_log_fmt_contains_origin_and_ua():
    from app.sidecar_main import _ACCESS_ORIGIN, _ACCESS_UA, OriginAccessFormatter, OriginUaCapture, _stderr_log_config

    config = _stderr_log_config("info")
    fmt = config["formatters"]["access"]["fmt"]
    assert "origin=" in fmt
    assert "ua=" in fmt
    assert config["formatters"]["access"]["()"] == "app.sidecar_main.OriginAccessFormatter"

    formatter = OriginAccessFormatter(fmt="origin=%(origin)s ua=%(ua)s", use_colors=False)
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:1", "POST", "/api/desktop/project-roots", "1.1", 200),
        exc_info=None,
    )
    origin_token = _ACCESS_ORIGIN.set("tauri://localhost")
    ua_token = _ACCESS_UA.set("FramePilot-QA")
    try:
        rendered = formatter.format(record)
    finally:
        _ACCESS_ORIGIN.reset(origin_token)
        _ACCESS_UA.reset(ua_token)
    assert "origin=tauri://localhost" in rendered
    assert "ua=FramePilot-QA" in rendered

    missing = formatter.format(record)
    assert "origin=-" in missing
    assert "ua=-" in missing

    async def inner(scope, receive, send):
        assert _ACCESS_ORIGIN.get() == "https://tauri.localhost"
        assert _ACCESS_UA.get() == "qa-agent"

    async def run_capture():
        wrapper = OriginUaCapture(inner)
        await wrapper(
            {
                "type": "http",
                "headers": [
                    (b"origin", b"https://tauri.localhost"),
                    (b"user-agent", b"qa-agent"),
                ],
            },
            None,
            None,
        )

    asyncio.run(run_capture())


def test_tauri_spawn_strips_project_root_allowlist():
    source = Path(__file__).resolve().parents[3] / "apps" / "desktop" / "src-tauri" / "src" / "sidecar.rs"
    text = source.read_text(encoding="utf-8")
    fn_start = text.index("pub fn spawn_sidecar(")
    next_item = text.find("\npub ", fn_start + 1)
    spawn_fn = text[fn_start:next_item]
    assert '.env("FRAMEPILOT_DESKTOP", "1")' in spawn_fn
    assert '.env("PYTHONUNBUFFERED", "1")' in spawn_fn
    assert "command.current_dir(dir)" in spawn_fn
    assert "CREATE_NO_WINDOW" in spawn_fn
    assert 'env_remove("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST")' in spawn_fn
    allowlist_remove = spawn_fn.index('env_remove("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST")')
    frozen_branch = spawn_fn.index("} else {")
    assert allowlist_remove < frozen_branch, (
        "FRAMEPILOT_PROJECT_ROOT_ALLOWLIST env_remove must apply to every spawn, not only the frozen PYTHONPATH branch"
    )
    remainder = spawn_fn.replace(
        'env_remove("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST")',
        "",
        1,
    )
    assert "FRAMEPILOT_PROJECT_ROOT_ALLOWLIST" not in remainder
    assert 'env_remove("FRAMEPILOT_DESKTOP_QA")' in spawn_fn
    assert "FRAMEPILOT_DESKTOP_QA" in spawn_fn


def test_windows_packaged_startup_timeout_is_two_minutes():
    source = Path(__file__).resolve().parents[3] / "apps" / "desktop" / "src-tauri" / "src" / "sidecar.rs"
    text = source.read_text(encoding="utf-8")
    assert "pub const STARTUP_TIMEOUT_SECS: u64 = if cfg!(windows) { 120 } else { 15 };" in text
    assert "wait_ready_with_data_dir" in text
    assert "sidecar.ready" in text
    lib = (Path(__file__).resolve().parents[3] / "apps" / "desktop" / "src-tauri" / "src" / "lib.rs").read_text(
        encoding="utf-8"
    )
    assert "wait_ready_with_data_dir(port, STARTUP_TIMEOUT, Some(data_dir))" in lib
    assert "clear_sidecar_ready_marker(data_dir)" in lib


def test_sidecar_smoke_unsets_pythonpath_for_frozen_binary():
    source = Path(__file__).resolve().parents[3] / "scripts" / "sidecar-smoke.sh"
    text = source.read_text(encoding="utf-8")
    assert "use_frozen=1" in text
    assert "unset PYTHONPATH" in text
    export_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("export PYTHONPATH=")]
    assert export_lines == ['export PYTHONPATH="$repo_root/apps/api${PYTHONPATH:+:$PYTHONPATH}"']
    unset_index = text.index("unset PYTHONPATH")
    export_index = text.index(export_lines[0])
    if_frozen_index = text.index('if [[ "$use_frozen" -eq 1 ]]; then')
    else_index = text.index("else", if_frozen_index)
    assert if_frozen_index < unset_index < else_index < export_index


def test_sidecar_smoke_leftover_check_ignores_pgrep():
    source = Path(__file__).resolve().parents[3] / "scripts" / "sidecar-smoke.sh"
    text = source.read_text(encoding="utf-8")
    leftover_start = text.index("Leftover child processes")
    leftover_block = text[text.rindex("if command -v pgrep", 0, leftover_start) : leftover_start]
    assert "pgrep -P $$ -a" in leftover_block
    assert "framepilot-api" in leftover_block
    assert "sidecar_main" in leftover_block
    assert leftover_block.count('leftover="$(pgrep -P $$ || true)"') == 0


def test_desktop_smoke_leftover_check_ignores_pgrep():
    source = Path(__file__).resolve().parents[3] / "tests" / "desktop" / "smoke.sh"
    text = source.read_text(encoding="utf-8")
    leftover_start = text.index("Leftover child processes")
    leftover_block = text[text.rindex("if command -v pgrep", 0, leftover_start) : leftover_start]
    assert "pgrep -P $$ -a" in leftover_block
    assert "framepilot-api" in leftover_block
    assert "sidecar_main" in leftover_block
    assert leftover_block.count('leftover="$(pgrep -P $$ || true)"') == 0
