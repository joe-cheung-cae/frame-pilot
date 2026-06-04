from __future__ import annotations

import argparse
import json
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from PIL import Image, ImageOps

from app.devtools.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_dataset
from app.services.importing import (
    PREVIEW_LONG_EDGE,
    PREVIEW_WEBP_METHOD,
    PREVIEW_WEBP_QUALITY,
    THUMBNAIL_LONG_EDGE,
    THUMBNAIL_WEBP_QUALITY,
    _make_derivative_image,
    _save_derivatives,
)


@dataclass(frozen=True)
class DerivativeGenerationBenchConfig:
    output_dir: Path
    count: int = 12
    width: int = 3000
    height: int = 2000
    jpeg_quality: int = 88


def _validate_config(config: DerivativeGenerationBenchConfig) -> None:
    if config.count <= 0:
        raise ValueError("count must be greater than zero")
    if config.width < 32 or config.height < 32:
        raise ValueError("width and height must be at least 32 pixels")
    if config.jpeg_quality < 1 or config.jpeg_quality > 100:
        raise ValueError("jpeg_quality must be between 1 and 100")


def _empty_stages() -> dict[str, float]:
    return {
        "image_open": 0.0,
        "image_decode": 0.0,
        "orientation_handling": 0.0,
        "rgb_conversion": 0.0,
        "preview_resize": 0.0,
        "preview_webp_encode": 0.0,
        "thumbnail_generation": 0.0,
        "combined_derivative_generation": 0.0,
    }


def _stage_summary(stage_seconds: dict[str, float], count: int) -> dict[str, dict[str, float]]:
    return {
        stage: {
            "seconds": round(seconds, 6),
            "seconds_per_image": round(seconds / count, 6),
        }
        for stage, seconds in stage_seconds.items()
    }


def _size_summary(values: list[int]) -> dict[str, float | int]:
    return {
        "min": min(values),
        "max": max(values),
        "mean": round(mean(values), 2),
        "total": sum(values),
    }


def run_derivative_generation_bench(config: DerivativeGenerationBenchConfig) -> dict:
    _validate_config(config)
    source_dir = config.output_dir / "source"
    breakdown_preview_dir = config.output_dir / "breakdown-previews"
    breakdown_thumbnail_dir = config.output_dir / "breakdown-thumbnails"
    combined_root = config.output_dir / "combined-project"
    breakdown_preview_dir.mkdir(parents=True, exist_ok=True)
    breakdown_thumbnail_dir.mkdir(parents=True, exist_ok=True)
    combined_root.mkdir(parents=True, exist_ok=True)

    paths = generate_synthetic_dataset(
        SyntheticDatasetConfig(
            output_dir=source_dir,
            count=config.count,
            width=config.width,
            height=config.height,
            jpeg_quality=config.jpeg_quality,
        )
    )

    stage_seconds = _empty_stages()
    preview_bytes: list[int] = []
    combined_preview_bytes: list[int] = []
    preview_dimensions: list[tuple[int, int]] = []
    thumbnail_dimensions: list[tuple[int, int]] = []

    for path in paths:
        started = time.perf_counter()
        opened_image = Image.open(path)
        stage_seconds["image_open"] += time.perf_counter() - started

        with opened_image as opened:
            started = time.perf_counter()
            opened.load()
            stage_seconds["image_decode"] += time.perf_counter() - started

            started = time.perf_counter()
            oriented = ImageOps.exif_transpose(opened)
            stage_seconds["orientation_handling"] += time.perf_counter() - started

            started = time.perf_counter()
            image = oriented.convert("RGB")
            stage_seconds["rgb_conversion"] += time.perf_counter() - started

        started = time.perf_counter()
        preview = _make_derivative_image(image, PREVIEW_LONG_EDGE)
        stage_seconds["preview_resize"] += time.perf_counter() - started

        preview_path = breakdown_preview_dir / f"{path.stem}.webp"
        started = time.perf_counter()
        preview.save(preview_path, "WEBP", quality=PREVIEW_WEBP_QUALITY, method=PREVIEW_WEBP_METHOD)
        stage_seconds["preview_webp_encode"] += time.perf_counter() - started
        preview_bytes.append(preview_path.stat().st_size)
        preview_dimensions.append(preview.size)

        thumbnail_path = breakdown_thumbnail_dir / f"{path.stem}.webp"
        started = time.perf_counter()
        thumbnail = _make_derivative_image(image, THUMBNAIL_LONG_EDGE)
        thumbnail.save(thumbnail_path, "WEBP", quality=THUMBNAIL_WEBP_QUALITY)
        stage_seconds["thumbnail_generation"] += time.perf_counter() - started
        thumbnail_dimensions.append(thumbnail.size)

        started = time.perf_counter()
        _combined_thumbnail_path, combined_preview_path = _save_derivatives(combined_root, path, image)
        stage_seconds["combined_derivative_generation"] += time.perf_counter() - started
        combined_preview_bytes.append(combined_preview_path.stat().st_size)

    return {
        "config": {
            "count": config.count,
            "width": config.width,
            "height": config.height,
            "jpeg_quality": config.jpeg_quality,
        },
        "preview_settings": {
            "format": "WEBP",
            "long_edge": PREVIEW_LONG_EDGE,
            "quality": PREVIEW_WEBP_QUALITY,
            "method": PREVIEW_WEBP_METHOD,
        },
        "thumbnail_settings": {
            "format": "WEBP",
            "long_edge": THUMBNAIL_LONG_EDGE,
            "quality": THUMBNAIL_WEBP_QUALITY,
        },
        "timings": {
            "stages": _stage_summary(stage_seconds, config.count),
            "combined_seconds_per_image": round(
                stage_seconds["combined_derivative_generation"] / config.count,
                6,
            ),
        },
        "outputs": {
            "preview_bytes": _size_summary(preview_bytes),
            "combined_preview_bytes": _size_summary(combined_preview_bytes),
            "preview_dimensions": {
                "unique": [list(size) for size in sorted(set(preview_dimensions))],
                "long_edge_bounded": all(max(size) <= PREVIEW_LONG_EDGE for size in preview_dimensions),
            },
            "thumbnail_dimensions": {
                "unique": [list(size) for size in sorted(set(thumbnail_dimensions))],
                "long_edge_bounded": all(max(size) <= THUMBNAIL_LONG_EDGE for size in thumbnail_dimensions),
            },
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark FramePilot thumbnail and preview derivative generation.")
    parser.add_argument("--output", type=Path, help="Directory for generated benchmark images and derivatives.")
    parser.add_argument("--count", default=12, type=int, help="Number of generated images to benchmark.")
    parser.add_argument("--width", default=3000, type=int, help="Generated image width in pixels.")
    parser.add_argument("--height", default=2000, type=int, help="Generated image height in pixels.")
    parser.add_argument("--quality", default=88, type=int, help="Generated JPEG quality, from 1 to 100.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="framepilot-derivative-bench-") as temp_dir:
        output_dir = args.output or Path(temp_dir)
        result = run_derivative_generation_bench(
            DerivativeGenerationBenchConfig(
                output_dir=output_dir,
                count=args.count,
                width=args.width,
                height=args.height,
                jpeg_quality=args.quality,
            )
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
