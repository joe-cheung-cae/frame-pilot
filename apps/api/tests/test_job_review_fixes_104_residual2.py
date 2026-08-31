"""Test for the Bugbot medium residual left after commit 6b580a8.

``ensure_photo_derivatives`` / validation loop in ``process_project`` (around
apps/api/app/services/processing.py:377-395) could run for many photos without
refreshing ``heartbeat_at`` at all - the surrounding stage saves only refresh the lease
once *before* the loop starts and again once the loop has already finished. On a large
batch of photos needing derivative regeneration, this loop alone could outlast
``JOB_LEASE_STALE_AFTER`` with no intervening heartbeat, letting a concurrent stale sweep
(e.g. a ``GET`` job poll) mark the job ``failed - stale`` while the worker is still
actively regenerating files.

The fix refreshes the lease heartbeat (and commits) every
``DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL`` photos inside that loop, plus once more
right after it finishes, instead of only at the surrounding stage boundaries.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

import app.services.processing as processing_module
from app.core.config import reset_settings_cache
from app.main import create_app
from app.services.processing import DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL

PHOTO_COUNT = 3 * DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL - 3


def _jpeg_bytes(color: tuple[int, int, int]) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (48, 32), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def _wait_for_job(client: TestClient, project_id: str, job: dict) -> dict:
    current = job
    for _ in range(20):
        if current["status"] in {"complete", "complete_with_errors", "failed", "cancelled"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        assert response.status_code == 200
        current = response.json()
    return current


def _new_app(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("FRAMEPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP", raising=False)
    reset_settings_cache()
    return TestClient(create_app())


def test_derivative_validation_loop_refreshes_heartbeat_periodically(tmp_path, monkeypatch):
    client = _new_app(tmp_path, monkeypatch)
    project = client.post("/api/projects", json={"name": "Derivative heartbeat"}).json()

    files = [
        (
            "files",
            (
                f"photo-{index}.jpg",
                _jpeg_bytes((index * 17 % 256, index * 41 % 256, index * 61 % 256)),
                "image/jpeg",
            ),
        )
        for index in range(1, PHOTO_COUNT + 1)
    ]
    import_response = client.post(f"/api/projects/{project['id']}/import", files=files)
    assert import_response.status_code == 201
    import_job = _wait_for_job(client, project["id"], import_response.json()["job"])
    assert import_job["status"] in {"complete", "complete_with_errors"}

    first_job = _wait_for_job(client, project["id"], client.post(f"/api/projects/{project['id']}/process").json())
    assert first_job["status"] == "complete"

    photos = client.get(f"/api/projects/{project['id']}/photos").json()
    assert len(photos) == PHOTO_COUNT
    for photo in photos:
        Path(photo["thumbnail_path"]).unlink()
        Path(photo["preview_path"]).unlink()

    events: list[str] = []
    real_refresh = processing_module.refresh_job_lease_heartbeat
    real_ensure_derivatives = processing_module.ensure_photo_derivatives

    def spy_refresh(session, job):
        events.append("refresh")
        return real_refresh(session, job)

    def spy_ensure_derivatives(project_model, photo):
        events.append("derivative_call")
        return real_ensure_derivatives(project_model, photo)

    monkeypatch.setattr(processing_module, "refresh_job_lease_heartbeat", spy_refresh)
    monkeypatch.setattr(processing_module, "ensure_photo_derivatives", spy_ensure_derivatives)

    rerun_job = _wait_for_job(client, project["id"], client.post(f"/api/projects/{project['id']}/process").json())
    assert rerun_job["status"] == "complete"
    assert rerun_job["failed_items"] == 0

    derivative_call_count = events.count("derivative_call")
    assert derivative_call_count == PHOTO_COUNT

    first_call_index = events.index("derivative_call")
    last_call_index = len(events) - 1 - events[::-1].index("derivative_call")

    # Refreshes strictly inside the loop (i.e. interleaved between derivative_call
    # events, not merely bracketing them from the surrounding stage saves) must occur
    # at the configured interval - this is the actual fix under test.
    mid_loop_refreshes = events[first_call_index : last_call_index + 1].count("refresh")
    expected_mid_loop_refreshes = PHOTO_COUNT // DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL
    assert expected_mid_loop_refreshes >= 1, "test batch too small to exercise periodic refresh"
    assert mid_loop_refreshes == expected_mid_loop_refreshes

    # A trailing refresh must also follow immediately once the loop has finished, so a
    # stale sweep racing the very next (non-refreshing) stage cannot fail the job either.
    assert events[last_call_index + 1] == "refresh"

    refreshed_photos = client.get(f"/api/projects/{project['id']}/photos").json()
    for photo in refreshed_photos:
        assert Path(photo["thumbnail_path"]).is_file()
        assert Path(photo["preview_path"]).is_file()
