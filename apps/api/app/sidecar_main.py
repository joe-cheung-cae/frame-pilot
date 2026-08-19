"""Localhost-only FramePilot API sidecar launcher."""

from __future__ import annotations

import argparse
import copy
import os
import socket
from pathlib import Path

import uvicorn

ALLOWED_HOSTS = {"127.0.0.1", "localhost"}


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
    level = log_level.upper()
    config["loggers"]["uvicorn"]["level"] = level
    config["loggers"]["uvicorn.error"]["level"] = level
    config["loggers"]["uvicorn.access"]["level"] = level
    return config


def serve(app, sock: socket.socket, log_level: str = "info") -> None:
    # Windows packaged builds may not include uvloop; force the asyncio loop there.
    loop = "asyncio" if os.name == "nt" else "auto"
    config = uvicorn.Config(
        app,
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
