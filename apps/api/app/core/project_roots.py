from __future__ import annotations

import json
import os
import re
from pathlib import Path

from app.core.config import get_settings
from app.core.local_paths import normalize_user_path

BLOCKED_ROOT_NAMES = {"/", "/etc", "/usr", "/bin", "/sbin", "/var", "/System", "/Windows"}

MAX_REGISTERED_ROOTS = 50
REGISTRY_FILENAME = "desktop_project_roots.json"

_WINDOWS_DRIVE_ROOT = re.compile(r"^[A-Za-z]:[\\/]?$")
_WINDOWS_SYSTEM_ROOT = re.compile(r"^[A-Za-z]:[\\/]Windows\\?$", re.IGNORECASE)


def _data_dir() -> Path:
    env = os.getenv("FRAMEPILOT_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return get_settings().data_dir.resolve()


def _registry_path() -> Path:
    return _data_dir() / REGISTRY_FILENAME


def _is_blocked_input(path: str) -> bool:
    stripped = path.strip()
    collapsed = stripped.replace("\\", "/").rstrip("/")
    if stripped in BLOCKED_ROOT_NAMES or collapsed in BLOCKED_ROOT_NAMES:
        return True
    if _WINDOWS_DRIVE_ROOT.fullmatch(stripped) or _WINDOWS_DRIVE_ROOT.fullmatch(collapsed):
        return True
    if _WINDOWS_SYSTEM_ROOT.fullmatch(stripped) or re.fullmatch(r"[A-Za-z]:/Windows", collapsed, flags=re.IGNORECASE):
        return True
    return False


def _is_blocked_resolved(path: Path) -> bool:
    if str(path) in BLOCKED_ROOT_NAMES:
        return True
    if path.anchor and path == Path(path.anchor):
        return True
    parts = path.parts
    if len(parts) == 2 and parts[1].lower() == "windows" and path.parent == Path(path.anchor):
        return True
    return False


def _is_data_dir_or_parent(path: Path, data_dir: Path) -> bool:
    try:
        return data_dir == path or data_dir.is_relative_to(path)
    except (OSError, ValueError):
        return False


def _is_home_directory(path: Path) -> bool:
    try:
        return path == Path.home().expanduser().resolve()
    except OSError:
        return False


def is_blocked_allowlist_root(cleaned: str, resolved: Path, data_dir: Path) -> bool:
    """Return True if an env allowlist entry is too wide to accept.

    Uses the same blocked-name, filesystem-anchor, drive-root, data-dir,
    and home-directory helpers as register_root.
    """
    if _is_blocked_input(cleaned):
        return True
    if _is_blocked_resolved(resolved):
        return True
    if _is_data_dir_or_parent(resolved, data_dir):
        return True
    return _is_home_directory(resolved)


def _load_root_strings() -> list[str]:
    registry = _registry_path()
    if not registry.is_file():
        return []
    try:
        payload = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return []
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = payload.get("roots", [])
    else:
        return []
    if not isinstance(items, list):
        return []
    roots: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str) or not item:
            continue
        try:
            resolved = str(Path(item).expanduser().resolve())
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        roots.append(resolved)
        if len(roots) >= MAX_REGISTERED_ROOTS:
            break
    return roots


def _write_root_strings(roots: list[str]) -> None:
    registry = _registry_path()
    registry.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"roots": roots}, indent=2)
    tmp = registry.with_name(f"{registry.name}.tmp")
    tmp.write_text(payload + "\n", encoding="utf-8")
    tmp.replace(registry)


def registered_roots() -> list[Path]:
    return [Path(item) for item in _load_root_strings()]


def register_root(path: str) -> Path:
    cleaned = normalize_user_path(path)
    if _is_blocked_input(cleaned):
        raise ValueError("Project root path cannot target a system directory")
    candidate = Path(cleaned)
    if not candidate.is_absolute():
        raise ValueError("Project root path must be an absolute local directory")
    try:
        resolved = candidate.resolve()
    except OSError as error:
        raise ValueError("Project root path must be a usable local directory") from error
    if _is_blocked_resolved(resolved):
        raise ValueError("Project root path cannot target a system directory")
    if not resolved.exists() or not resolved.is_dir():
        raise ValueError("Project root path must be a usable local directory")
    data_dir = _data_dir()
    if _is_data_dir_or_parent(resolved, data_dir):
        raise ValueError("Project root path cannot target a system directory")
    if _is_home_directory(resolved):
        raise ValueError("Project root path cannot target a system directory")

    stored = _load_root_strings()
    resolved_key = str(resolved)
    if resolved_key in stored:
        return resolved
    if len(stored) >= MAX_REGISTERED_ROOTS:
        raise ValueError(f"At most {MAX_REGISTERED_ROOTS} desktop project roots can be registered")
    stored.append(resolved_key)
    _write_root_strings(stored)
    return resolved


def clear_registered_roots() -> None:
    registry = _registry_path()
    registry.unlink(missing_ok=True)
    registry.with_name(f"{registry.name}.tmp").unlink(missing_ok=True)
