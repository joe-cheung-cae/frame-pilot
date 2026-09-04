"""Register pillow-heif as a Pillow opener for HEIC/HEIF stills."""

from __future__ import annotations

import threading

from pillow_heif import register_heif_opener

_lock = threading.Lock()
_registered = False


def ensure_heif_opener() -> None:
    """Register the HEIF opener. Safe to call more than once. Does not register AVIF."""
    global _registered
    if _registered:
        return
    with _lock:
        if _registered:
            return
        register_heif_opener()
        _registered = True
