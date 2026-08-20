"""Normalize user-supplied local paths for desktop import and project roots."""

from __future__ import annotations

import os
from pathlib import PurePosixPath, PureWindowsPath


def is_windows_absolute_path(raw: str) -> bool:
    parsed = PureWindowsPath(raw)
    return parsed.is_absolute() and bool(parsed.drive)


def normalize_user_path(raw: str) -> str:
    if "\x00" in raw:
        raise ValueError("Path contains a NUL byte")
    if not raw:
        return raw
    if os.name == "nt" or is_windows_absolute_path(raw):
        return str(PureWindowsPath(raw))
    return str(PurePosixPath(raw))
