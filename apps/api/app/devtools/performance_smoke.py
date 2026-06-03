from __future__ import annotations

import argparse
import json
import os
import resource
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from fastapi.testclient import TestClient

from app.devtools.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_dataset
from app.main import create_app


@dataclass(frozen=True)
class PerformanceSmokeConfig:
    output_dir: Path
    count: int
    width: int = 96
    height: int = 72
    import_batch_size: int = 100


def _max_rss_mb() -> float:
    rss = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if os.uname().sysname == "Darwin":
        return round(rss / (1024 * 1024), 2)
    return round(rss / 1024, 2)


def _wait_for_job(client: TestClient, project_id: str, job: dict, timeout_seconds: float = 300.0) -> dict:
    deadline = time.monotonic() + timeout_seconds
    current = job
    while time.monotonic() < deadline:
        if current["status"] in {"complete", "failed"}:
            return current
        response = client.get(f"/api/projects/{project_id}/jobs/{current['id']}")
        response.raise_for_status()
        current = response.json()
        time.sleep(0.05)
    raise TimeoutError(f"Processing job {job['id']} did not finish within {timeout_seconds} seconds")


def _chunked(paths: list[Path], size: int) -> list[list[Path]]:
    if size <= 0:
        raise ValueError("import_batch_size must be greater than zero")
    return [paths[index : index + size] for index in range(0, len(paths), size)]


def run_performance_smoke(config: PerformanceSmokeConfig) -> dict:
    if config.count <= 0:
        raise ValueError("count must be greater than zero")

    data_dir = config.output_dir / "data"
    source_dir = config.output_dir / "source"
    previous_data_dir = os.environ.get("FRAMEPILOT_DATA_DIR")
    os.environ["FRAMEPILOT_DATA_DIR"] = str(data_dir)
    try:
        client = TestClient(create_app())
        timings: dict[str, float] = {}

        started = time.monotonic()
        paths = generate_synthetic_dataset(
            SyntheticDatasetConfig(
                output_dir=source_dir,
                count=config.count,
                width=config.width,
                height=config.height,
            )
        )
        timings["generate_seconds"] = round(time.monotonic() - started, 3)

        project = client.post("/api/projects", json={"name": f"Performance smoke {config.count}"}).json()

        started = time.monotonic()
        imported_count = 0
        for batch in _chunked(paths, config.import_batch_size):
            response = client.post(
                f"/api/projects/{project['id']}/import",
                files=[("files", (path.name, path.read_bytes(), "image/jpeg")) for path in batch],
            )
            response.raise_for_status()
            imported_count += len(response.json()["imported"])
        timings["import_seconds"] = round(time.monotonic() - started, 3)

        started = time.monotonic()
        process_response = client.post(f"/api/projects/{project['id']}/process")
        process_response.raise_for_status()
        job = _wait_for_job(client, project["id"], process_response.json())
        timings["process_seconds"] = round(time.monotonic() - started, 3)

        project_response = client.get(f"/api/projects/{project['id']}")
        project_response.raise_for_status()
        groups_response = client.get(f"/api/projects/{project['id']}/groups")
        groups_response.raise_for_status()
        groups = groups_response.json()

        return {
            "count": config.count,
            "failed_items": job["failed_items"],
            "group_count": len(groups),
            "imported_count": imported_count,
            "max_rss_mb": _max_rss_mb(),
            "output_dir": str(config.output_dir),
            "processed_images": project_response.json()["processed_images"],
            "status": job["status"],
            "timings": timings,
        }
    finally:
        if previous_data_dir is None:
            os.environ.pop("FRAMEPILOT_DATA_DIR", None)
        else:
            os.environ["FRAMEPILOT_DATA_DIR"] = previous_data_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local synthetic import/process performance smoke.")
    parser.add_argument("--output", type=Path, help="Directory for generated images and local FramePilot data.")
    parser.add_argument("--count", required=True, type=int, help="Number of synthetic images to import and process.")
    parser.add_argument("--width", default=96, type=int, help="Synthetic image width in pixels.")
    parser.add_argument("--height", default=72, type=int, help="Synthetic image height in pixels.")
    parser.add_argument("--import-batch-size", default=100, type=int, help="Files to upload per import request.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="framepilot-perf-") as temp_dir:
        output_dir = args.output or Path(temp_dir)
        result = run_performance_smoke(
            PerformanceSmokeConfig(
                output_dir=output_dir,
                count=args.count,
                width=args.width,
                height=args.height,
                import_batch_size=args.import_batch_size,
            )
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
