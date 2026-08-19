import hashlib
import os
import stat
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app


def _jpeg(color=(90, 110, 70)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (40, 30), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path / "data"))
    return TestClient(create_app())


def _source_fingerprint(path: Path) -> tuple[int, int, str]:
    st = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return st.st_size, st.st_mtime_ns, digest


def test_path_import_does_not_mutate_source_file(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Immutable"}).json()
    source = tmp_path / "card" / "keep.jpg"
    source.parent.mkdir()
    source.write_bytes(_jpeg())
    before = _source_fingerprint(source)
    entries_before = sorted(path.name for path in source.parent.iterdir())

    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(source)], "finalize": True},
    )
    assert response.status_code == 201
    assert _source_fingerprint(source) == before
    assert sorted(path.name for path in source.parent.iterdir()) == entries_before
    copy_path = Path(response.json()["imported"][0]["project_copy_path"])
    assert copy_path.exists()
    if os.name != "nt":
        source_stat = source.stat()
        copy_stat = copy_path.stat()
        assert not (source_stat.st_ino == copy_stat.st_ino and source_stat.st_dev == copy_stat.st_dev)


@pytest.mark.skipif(os.name == "nt" or os.geteuid() == 0, reason="POSIX non-root read-only directory")
def test_path_import_from_readonly_directory(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Readonly"}).json()
    folder = tmp_path / "locked"
    source = folder / "keep.jpg"
    folder.mkdir()
    source.write_bytes(_jpeg((1, 2, 3)))
    before = _source_fingerprint(source)
    folder.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        response = client.post(
            f"/api/projects/{project['id']}/imports/from-paths",
            json={"paths": [str(source)], "finalize": True},
        )
        assert response.status_code == 201
        assert _source_fingerprint(source) == before
    finally:
        folder.chmod(stat.S_IRWXU)


def test_cancel_mid_import_leaves_sources_untouched(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Cancel"}).json()
    first = tmp_path / "one.jpg"
    second = tmp_path / "two.jpg"
    first.write_bytes(_jpeg((4, 5, 6)))
    second.write_bytes(_jpeg((7, 8, 9)))
    before_first = _source_fingerprint(first)
    before_second = _source_fingerprint(second)

    started = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(first)], "finalize": False},
    )
    assert started.status_code == 201
    job_id = started.json()["job"]["id"]
    cancelled = client.post(f"/api/projects/{project['id']}/jobs/{job_id}/cancel")
    assert cancelled.status_code in {200, 202}
    assert _source_fingerprint(first) == before_first
    assert _source_fingerprint(second) == before_second
