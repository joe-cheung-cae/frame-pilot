from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import tempfile
import time
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from fastapi.testclient import TestClient

from app.devtools.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_dataset
from app.main import create_app

DEFAULT_EXPORT_MODES = ("csv", "zip", "folder")


@dataclass(frozen=True)
class PerformanceSmokeConfig:
    output_dir: Path
    count: int
    width: int = 96
    height: int = 72
    import_batch_size: int = 100
    export_modes: tuple[str, ...] = DEFAULT_EXPORT_MODES


@dataclass(frozen=True)
class PerformanceSmokeSuiteConfig:
    output_dir: Path
    counts: tuple[int, ...]
    width: int = 96
    height: int = 72
    import_batch_size: int = 100
    export_modes: tuple[str, ...] = DEFAULT_EXPORT_MODES


def _max_rss_mb() -> float:
    rss = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if platform.system() == "Darwin":
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


def _upload_files(paths: list[Path], stack: ExitStack) -> list[tuple[str, tuple[str, BinaryIO, str]]]:
    return [("files", (path.name, stack.enter_context(path.open("rb")), "image/jpeg")) for path in paths]


def _artifact_metric(output_path: str) -> dict[str, int]:
    path = Path(output_path)
    if path.is_dir():
        return {"file_count": sum(1 for item in path.iterdir() if item.is_file())}
    if path.is_file():
        return {"bytes": path.stat().st_size}
    raise FileNotFoundError(f"Export artifact was not written: {output_path}")


def _export_selected_photos(client: TestClient, project_id: str, photo_ids: list[str], modes: tuple[str, ...]) -> dict:
    if not modes:
        return {}

    mark_response = client.patch(
        f"/api/projects/{project_id}/photos/batch",
        json={"photo_ids": photo_ids, "user_status": "Pick"},
    )
    mark_response.raise_for_status()

    exports = {}
    for mode in modes:
        started = time.monotonic()
        response = client.post(f"/api/projects/{project_id}/export", json={"mode": mode, "statuses": ["Pick"]})
        response.raise_for_status()
        record = response.json()
        exports[mode] = {
            **_artifact_metric(record["output_path"]),
            "output_path": record["output_path"],
            "seconds": round(time.monotonic() - started, 3),
            "selected_count": record["selected_count"],
        }
    return exports


def run_performance_smoke(config: PerformanceSmokeConfig) -> dict:
    if config.count <= 0:
        raise ValueError("count must be greater than zero")
    invalid_export_modes = sorted(set(config.export_modes) - set(DEFAULT_EXPORT_MODES))
    if invalid_export_modes:
        raise ValueError(f"export_modes must be one or more of {', '.join(DEFAULT_EXPORT_MODES)}")

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
            with ExitStack() as stack:
                response = client.post(f"/api/projects/{project['id']}/import", files=_upload_files(batch, stack))
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
        photos_response = client.get(f"/api/projects/{project['id']}/photos")
        photos_response.raise_for_status()
        photo_ids = [photo["id"] for photo in photos_response.json()]
        groups_response = client.get(f"/api/projects/{project['id']}/groups")
        groups_response.raise_for_status()
        groups = groups_response.json()

        started = time.monotonic()
        exports = _export_selected_photos(client, project["id"], photo_ids, config.export_modes)
        if exports:
            timings["export_seconds"] = round(time.monotonic() - started, 3)

        return {
            "count": config.count,
            "exports": exports,
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


def run_performance_smoke_suite(config: PerformanceSmokeSuiteConfig) -> dict:
    if not config.counts:
        raise ValueError("counts must include at least one image count")
    invalid_counts = [count for count in config.counts if count <= 0]
    if invalid_counts:
        raise ValueError("counts must be greater than zero")
    if len(set(config.counts)) != len(config.counts):
        raise ValueError("counts must not contain duplicates")

    results = []
    for count in config.counts:
        result = run_performance_smoke(
            PerformanceSmokeConfig(
                output_dir=config.output_dir / f"count-{count:06d}",
                count=count,
                width=config.width,
                height=config.height,
                import_batch_size=config.import_batch_size,
                export_modes=config.export_modes,
            )
        )
        results.append(result)

    return {
        "counts": list(config.counts),
        "output_dir": str(config.output_dir),
        "results": results,
        "status": "complete" if all(result["status"] == "complete" for result in results) else "failed",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local synthetic import/process performance smoke.")
    parser.add_argument("--output", type=Path, help="Directory for generated images and local FramePilot data.")
    count_group = parser.add_mutually_exclusive_group(required=True)
    count_group.add_argument("--count", type=int, help="Number of synthetic images to import and process.")
    count_group.add_argument(
        "--counts",
        nargs="+",
        type=int,
        help="Run multiple image counts in sequence, for example: --counts 100 500 2000.",
    )
    parser.add_argument("--width", default=96, type=int, help="Synthetic image width in pixels.")
    parser.add_argument("--height", default=72, type=int, help="Synthetic image height in pixels.")
    parser.add_argument("--import-batch-size", default=100, type=int, help="Files to upload per import request.")
    parser.add_argument(
        "--export-modes",
        nargs="+",
        default=list(DEFAULT_EXPORT_MODES),
        choices=DEFAULT_EXPORT_MODES,
        help="Export modes to run after processing and marking synthetic photos as Pick.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="framepilot-perf-") as temp_dir:
        output_dir = args.output or Path(temp_dir)
        if args.counts:
            result = run_performance_smoke_suite(
                PerformanceSmokeSuiteConfig(
                    output_dir=output_dir,
                    counts=tuple(args.counts),
                    width=args.width,
                    height=args.height,
                    import_batch_size=args.import_batch_size,
                    export_modes=tuple(args.export_modes),
                )
            )
        else:
            result = run_performance_smoke(
                PerformanceSmokeConfig(
                    output_dir=output_dir,
                    count=args.count,
                    width=args.width,
                    height=args.height,
                    import_batch_size=args.import_batch_size,
                    export_modes=tuple(args.export_modes),
                )
            )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
