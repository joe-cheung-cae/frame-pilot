from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings

SETTINGS_FILENAME = "app_settings.json"
DEFAULT_IMPORT_WORKERS = 1
MIN_IMPORT_WORKERS = 1
MAX_IMPORT_WORKERS = 4


@dataclass(frozen=True, slots=True)
class AppSettings:
    import_workers: int = DEFAULT_IMPORT_WORKERS


def _settings_path() -> Path:
    return get_settings().data_dir / SETTINGS_FILENAME


def clamp_import_workers(value: object) -> int:
    if type(value) is int and MIN_IMPORT_WORKERS <= value <= MAX_IMPORT_WORKERS:
        return value
    return DEFAULT_IMPORT_WORKERS


def load_app_settings() -> AppSettings:
    path = _settings_path()
    if not path.is_file():
        return AppSettings()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return AppSettings()
    if not isinstance(payload, dict):
        return AppSettings()
    return AppSettings(import_workers=clamp_import_workers(payload.get("import_workers")))


def load_import_workers() -> int:
    return load_app_settings().import_workers


def save_app_settings(import_workers: int) -> AppSettings:
    clamped = clamp_import_workers(import_workers)
    if clamped != import_workers:
        raise ValueError("import_workers must be an integer from 1 to 4")
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"import_workers": clamped}, indent=2)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(payload + "\n", encoding="utf-8")
    tmp.replace(path)
    return AppSettings(import_workers=clamped)
