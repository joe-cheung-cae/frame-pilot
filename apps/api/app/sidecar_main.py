"""Localhost-only FramePilot API sidecar launcher."""

from __future__ import annotations

import argparse
import contextvars
import copy
import os
import socket
from pathlib import Path

import uvicorn

ALLOWED_HOSTS = {"127.0.0.1", "localhost"}
_ACCESS_ORIGIN: contextvars.ContextVar[str] = contextvars.ContextVar("framepilot_access_origin", default="-")
_ACCESS_UA: contextvars.ContextVar[str] = contextvars.ContextVar("framepilot_access_ua", default="-")


class OriginAccessFormatter(uvicorn.logging.AccessFormatter):
    """Access formatter that appends Origin and User-Agent from the ASGI request."""

    def formatMessage(self, record):
        origin = _ACCESS_ORIGIN.get() or "-"
        ua = _ACCESS_UA.get() or "-"
        record.origin = origin
        record.ua = ua
        return super().formatMessage(record)


class OriginUaCapture:
    """ASGI wrapper that records Origin and User-Agent for the access formatter."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        origin = "-"
        ua = "-"
        for key, value in scope.get("headers") or []:
            name = key.decode("latin-1").lower()
            if name == "origin":
                origin = value.decode("latin-1") or "-"
            elif name == "user-agent":
                ua = value.decode("latin-1") or "-"
        origin_token = _ACCESS_ORIGIN.set(origin)
        ua_token = _ACCESS_UA.set(ua)
        try:
            await self.app(scope, receive, send)
        finally:
            _ACCESS_ORIGIN.reset(origin_token)
            _ACCESS_UA.reset(ua_token)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="framepilot-api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args(argv)
    if args.host not in ALLOWED_HOSTS:
        parser.exit(status=2, message=f"error: --host must be 127.0.0.1 or localhost, got {args.host!r}\n")
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        parser.exit(status=2, message="error: --data-dir must be an absolute path\n")
    args.data_dir = str(data_dir)
    return args


def apply_data_dir(data_dir: str | Path) -> None:
    os.environ["FRAMEPILOT_DATA_DIR"] = str(data_dir)


def bind_listen_socket(host: str, port: int) -> socket.socket:
    bind_host = "127.0.0.1" if host in ALLOWED_HOSTS else host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if os.name != "nt":
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind_host, port))
    sock.listen(128)
    return sock


def ready_line(host: str, port: int, data_dir: str | Path) -> str:
    return f"FRAMEPILOT_API ready host={host} port={port} data_dir={data_dir}"


def _stderr_log_config(log_level: str) -> dict:
    config = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
    config["handlers"]["default"]["stream"] = "ext://sys.stderr"
    config["handlers"]["access"]["stream"] = "ext://sys.stderr"
    config["formatters"]["access"]["()"] = "app.sidecar_main.OriginAccessFormatter"
    config["formatters"]["access"]["fmt"] = (
        '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s origin=%(origin)s ua=%(ua)s'
    )
    level = log_level.upper()
    config["loggers"]["uvicorn"]["level"] = level
    config["loggers"]["uvicorn.error"]["level"] = level
    config["loggers"]["uvicorn.access"]["level"] = level
    return config


def serve(app, sock: socket.socket, log_level: str = "info") -> None:
    # Windows packaged builds may not include uvloop; force the asyncio loop there.
    loop = "asyncio" if os.name == "nt" else "auto"
    config = uvicorn.Config(
        OriginUaCapture(app),
        host="127.0.0.1",
        log_level=log_level,
        access_log=True,
        loop=loop,
        log_config=_stderr_log_config(log_level),
    )
    server = uvicorn.Server(config)
    server.run(sockets=[sock])


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    apply_data_dir(args.data_dir)
    from app.main import app

    sock = bind_listen_socket(args.host, args.port)
    try:
        bound_host, bound_port = sock.getsockname()[:2]
        print(ready_line(bound_host, bound_port, args.data_dir), flush=True)
        serve(app, sock, args.log_level)
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
