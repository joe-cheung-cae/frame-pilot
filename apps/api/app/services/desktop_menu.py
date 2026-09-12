from __future__ import annotations

from collections import deque
from threading import Lock

NAVIGABLE_MENU_COMMANDS = frozenset(
    {"new", "shortcuts", "import", "export", "process", "cull"}
)
MENU_COMMAND_QUEUE_LIMIT = 16

_menu_commands: deque[str] = deque()
_menu_lock = Lock()


def normalize_menu_command(command: str) -> str | None:
    stripped = command.strip()
    if stripped in NAVIGABLE_MENU_COMMANDS:
        return stripped
    return None


def push_menu_command(command: str) -> str | None:
    normalized = normalize_menu_command(command)
    if normalized is None:
        return None
    with _menu_lock:
        if len(_menu_commands) >= MENU_COMMAND_QUEUE_LIMIT:
            _menu_commands.popleft()
        _menu_commands.append(normalized)
    return normalized


def take_menu_command() -> str | None:
    with _menu_lock:
        if not _menu_commands:
            return None
        return _menu_commands.popleft()


def clear_menu_commands() -> None:
    with _menu_lock:
        _menu_commands.clear()
