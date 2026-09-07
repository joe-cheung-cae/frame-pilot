import hashlib
import json
import threading
import time
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session, select

from app.api import routes
from app.db.session import get_engine
from app.main import create_app
from app.models.entities import Photo, ProcessingJob
from app.services import importing


def _client(tmp_path, monkeypatch, *, data_dir: Path | None = None) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(data_dir or tmp_path))
    return TestClient(create_app())


def _jpeg(color: tuple[int, int, int] = (120, 150, 90)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (16, 12), color=color).save(buffer, format="JPEG", quality=40)
    return buffer.getvalue()


def _write_jpeg(path: Path, color: tuple[int, int, int] = (120, 150, 90)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_jpeg(color))


def _fingerprint(path: Path) -> tuple[int, int, str]:
    st = path.stat()
    return st.st_size, st.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def _wait_for_job(client: TestClient, project_id: str, job: dict) -> dict:
    current = job
    for _ in range(40):
        if current["status"] in {"complete", "complete_with_errors", "failed", "cancelled", "paused"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


def _capture_background_tasks(monkeypatch) -> list[tuple[object, tuple, dict]]:
    scheduled: list[tuple[object, tuple, dict]] = []

    def capture_background_task(self, func, *args, **kwargs):
        scheduled.append((func, args, kwargs))

    monkeypatch.setattr(routes.BackgroundTasks, "add_task", capture_background_task)
    return scheduled


def _track_process_peak(monkeypatch) -> dict[str, int]:
    original = importing.process_registered_import_photo
    state = {"active": 0, "peak": 0}
    lock = threading.Lock()

    def tracking(*args, **kwargs):
        with lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
        try:
            time.sleep(0.05)
            return original(*args, **kwargs)
        finally:
            with lock:
                state["active"] -= 1

    monkeypatch.setattr(importing, "process_registered_import_photo", tracking)
    return state


def test_get_settings_defaults_to_one_import_worker_when_file_missing(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = client.get("/api/settings")

    assert response.status_code == 200
    assert response.json() == {"import_workers": 1}
    assert not (tmp_path / "app_settings.json").exists()
    meta = client.get("/api/meta").json()
    assert "import_workers" not in meta


def test_get_settings_defaults_to_one_when_file_is_corrupt(tmp_path, monkeypatch):
    (tmp_path / "app_settings.json").write_text("{not-json", encoding="utf-8")
    client = _client(tmp_path, monkeypatch)

    response = client.get("/api/settings")

    assert response.status_code == 200
    assert response.json() == {"import_workers": 1}


def test_patch_settings_persists_import_workers_across_app_recreate(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    for workers in (2, 3, 4):
        patched = client.patch("/api/settings", json={"import_workers": workers})
        assert patched.status_code == 200
        assert patched.json() == {"import_workers": workers}
        payload = json.loads((tmp_path / "app_settings.json").read_text(encoding="utf-8"))
        assert payload == {"import_workers": workers}

        recreated = _client(tmp_path, monkeypatch)
        loaded = recreated.get("/api/settings")
        assert loaded.status_code == 200
        assert loaded.json() == {"import_workers": workers}


def test_patch_settings_empty_body_keeps_current_value(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    assert client.patch("/api/settings", json={"import_workers": 3}).json() == {"import_workers": 3}

    response = client.patch("/api/settings", json={})

    assert response.status_code == 200
    assert response.json() == {"import_workers": 3}


def test_patch_settings_rejects_invalid_import_workers(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    invalid_payloads = [
        {"import_workers": 0},
        {"import_workers": 5},
        {"import_workers": 1.5},
        {"import_workers": "2"},
        {"import_workers": None},
    ]
    for payload in invalid_payloads:
        response = client.patch("/api/settings", json=payload)
        assert response.status_code == 422, payload
    assert client.get("/api/settings").json() == {"import_workers": 1}
    assert not (tmp_path / "app_settings.json").exists()


def test_settings_route_is_available_without_desktop_mode(tmp_path, monkeypatch):
    monkeypatch.delenv("FRAMEPILOT_DESKTOP", raising=False)
    client = _client(tmp_path, monkeypatch)
    assert client.get("/api/settings").status_code == 200
    assert client.patch("/api/settings", json={"import_workers": 2}).status_code == 200


def test_default_import_peak_concurrency_is_one(tmp_path, monkeypatch):
    peak = _track_process_peak(monkeypatch)
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Default workers"}).json()
    card = tmp_path / "card"
    sources = []
    for index in range(4):
        path = card / f"frame-{index}.jpg"
        _write_jpeg(path, (index * 20, 40, 80))
        sources.append(path)
    before_sources = {path: _fingerprint(path) for path in sources}

    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(card)], "finalize": True},
    )
    assert response.status_code == 201
    job = _wait_for_job(client, project["id"], response.json()["job"])
    assert job["status"] == "complete"
    assert peak["peak"] == 1

    originals = Path(project["root_path"]) / "originals"
    for path, expected in before_sources.items():
        assert _fingerprint(path) == expected
        copy_path = originals / path.name
        assert _fingerprint(copy_path)[0] == expected[0]
        assert _fingerprint(copy_path)[2] == expected[2]


def test_import_workers_four_peaks_at_four_and_leaves_originals(tmp_path, monkeypatch):
    peak = _track_process_peak(monkeypatch)
    client = _client(tmp_path, monkeypatch)
    assert client.patch("/api/settings", json={"import_workers": 4}).json() == {"import_workers": 4}
    project = client.post("/api/projects", json={"name": "Four workers"}).json()
    card = tmp_path / "card"
    sources = []
    for index in range(6):
        path = card / f"frame-{index}.jpg"
        _write_jpeg(path, (index * 15, 50, 90))
        sources.append(path)
    before_sources = {path: _fingerprint(path) for path in sources}

    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(card)], "finalize": True},
    )
    assert response.status_code == 201
    imported = response.json()["imported"]
    before_copies = {item["id"]: _fingerprint(Path(item["project_copy_path"])) for item in imported}
    job = _wait_for_job(client, project["id"], response.json()["job"])
    assert job["status"] == "complete"
    assert peak["peak"] == 4
    assert peak["peak"] <= 4

    for path, expected in before_sources.items():
        assert _fingerprint(path) == expected
    for item in imported:
        copy_path = Path(item["project_copy_path"])
        assert _fingerprint(copy_path) == before_copies[item["id"]]


def test_cancel_import_with_four_workers_waits_in_flight_and_leaves_originals(tmp_path, monkeypatch):
    scheduled = _capture_background_tasks(monkeypatch)
    client = _client(tmp_path, monkeypatch)
    cancel_client = TestClient(create_app())
    assert client.patch("/api/settings", json={"import_workers": 4}).json() == {"import_workers": 4}
    project = client.post("/api/projects", json={"name": "Cancel four workers"}).json()
    card = tmp_path / "card"
    sources = []
    for index in range(6):
        path = card / f"frame-{index}.jpg"
        _write_jpeg(path, (80, index * 10, 40))
        sources.append(path)
    before_sources = {path: _fingerprint(path) for path in sources}

    response = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(card)], "finalize": True},
    )
    assert response.status_code == 201
    job_id = response.json()["job"]["id"]
    copies = [Path(item["project_copy_path"]) for item in response.json()["imported"]]
    before_copies = {path: _fingerprint(path) for path in copies}

    original = importing.process_registered_import_photo
    started = threading.Barrier(5, timeout=10)
    release = threading.Event()
    finished_calls = {"count": 0}
    lock = threading.Lock()

    def gated(*args, **kwargs):
        started.wait()
        assert release.wait(timeout=10)
        result = original(*args, **kwargs)
        with lock:
            finished_calls["count"] += 1
        return result

    monkeypatch.setattr(importing, "process_registered_import_photo", gated)
    task, args, kwargs = scheduled[-1]
    worker = threading.Thread(target=task, args=args, kwargs=kwargs, daemon=True)
    worker.start()
    started.wait()
    cancel_response = cancel_client.post(f"/api/projects/{project['id']}/jobs/{job_id}/cancel")
    assert cancel_response.status_code == 202
    release.set()
    worker.join(timeout=20)
    assert not worker.is_alive()

    cancelled = client.get(f"/api/projects/{project['id']}/jobs/{job_id}").json()
    assert cancelled["status"] == "cancelled"
    assert cancelled["cancellation_requested"] is True
    assert finished_calls["count"] == 4
    for path, expected in before_sources.items():
        assert _fingerprint(path) == expected
    for path, expected in before_copies.items():
        assert _fingerprint(path) == expected


def test_process_twice_reuses_blocking_job_id(tmp_path, monkeypatch):
    scheduled = _capture_background_tasks(monkeypatch)
    client = _client(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Process reuse"}).json()
    card = tmp_path / "one.jpg"
    _write_jpeg(card)
    imported = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(card)], "finalize": True},
    )
    assert imported.status_code == 201
    task, args, kwargs = scheduled[-1]
    task(*args, **kwargs)
    import_job = client.get(f"/api/projects/{project['id']}/jobs/{imported.json()['job']['id']}").json()
    assert import_job["status"] == "complete"

    first = client.post(f"/api/projects/{project['id']}/process")
    assert first.status_code == 202
    second = client.post(f"/api/projects/{project['id']}/process")
    assert second.status_code == 202
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["job_type"] == "processing"


def test_second_import_without_job_id_still_returns_409(tmp_path, monkeypatch):
    _capture_background_tasks(monkeypatch)
    client = _client(tmp_path, monkeypatch)
    assert client.patch("/api/settings", json={"import_workers": 4}).status_code == 200
    project = client.post("/api/projects", json={"name": "Import overlap"}).json()
    first_file = tmp_path / "a.jpg"
    second_file = tmp_path / "b.jpg"
    _write_jpeg(first_file)
    _write_jpeg(second_file)
    first = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(first_file)], "finalize": False},
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/projects/{project['id']}/imports/from-paths",
        json={"paths": [str(second_file)]},
    )
    assert second.status_code == 409
    with Session(get_engine()) as session:
        jobs = session.exec(
            select(ProcessingJob)
            .where(ProcessingJob.project_id == project["id"])
            .where(ProcessingJob.job_type == "import")
        ).all()
        assert len(jobs) == 1
        photos = session.exec(select(Photo).where(Photo.project_id == project["id"])).all()
        assert len(photos) == 1
