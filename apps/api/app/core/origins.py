from __future__ import annotations

import os

WEB_ORIGINS = frozenset(
    {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3100",
        "http://127.0.0.1:3100",
    }
)

DESKTOP_ORIGINS = frozenset(
    {
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    }
)

ALLOWED_HOSTNAMES = frozenset({"127.0.0.1", "localhost", "::1", "tauri.localhost"})


def desktop_mode_enabled(environ: dict[str, str] | None = None) -> bool:
    source = os.environ if environ is None else environ
    return source.get("FRAMEPILOT_DESKTOP") == "1"


def allowed_origins(*, desktop: bool | None = None) -> set[str]:
    if desktop is None:
        desktop = desktop_mode_enabled()
    origins = set(WEB_ORIGINS)
    if desktop:
        origins.update(DESKTOP_ORIGINS)
    return origins


def hostname_from_host_header(host_header: str | None) -> str | None:
    if host_header is None:
        return None
    value = host_header.strip()
    if not value:
        return None
    if value.startswith("["):
        end = value.find("]")
        if end == -1:
            return value.lower()
        return value[1:end].lower()
    if value.count(":") == 1:
        return value.rsplit(":", 1)[0].lower()
    return value.lower()


def host_is_allowed(host_header: str | None) -> bool:
    hostname = hostname_from_host_header(host_header)
    if hostname is None:
        return False
    return hostname in ALLOWED_HOSTNAMES
