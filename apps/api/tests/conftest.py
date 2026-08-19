"""Default TestClient Host to loopback so Host-policy tests match production."""

from fastapi.testclient import TestClient

_original_init = TestClient.__init__


def _init_with_loopback(self, *args, **kwargs):
    kwargs.setdefault("base_url", "http://127.0.0.1")
    _original_init(self, *args, **kwargs)


TestClient.__init__ = _init_with_loopback
