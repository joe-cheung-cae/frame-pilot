from __future__ import annotations

import argparse
import json
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from app.devtools.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_dataset
from app.image.scoring import (
    QualityScores,
    _detect_face_signals,
    _exposure_score,
    _laplacian_variance,
    _to_luminance,
    compute_quality_scores_for_image,
    normalize_score,
    scoring_image_array,
)


@dataclass(frozen=True)
class QualityScoringBenchConfig:
    output_dir: Path
    count: int = 12
    width: int = 3000
    height: int = 2000
    jpeg_quality: int = 88


def _validate_config(config: QualityScoringBenchConfig) -> None:
    if config.count <= 0:
        raise ValueError("count must be greater than zero")
    if config.width < 32 or config.height < 32:
        raise ValueError("width and height must be at least 32 pixels")
    if config.jpeg_quality < 1 or config.jpeg_quality > 100:
        raise ValueError("jpeg_quality must be between 1 and 100")


def _open_rgb_image(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        return ImageOps.exif_transpose(opened).convert("RGB")


def _compute_current_scores(image: Image.Image) -> QualityScores:
    return compute_quality_scores_for_image(image)


def _compute_legacy_full_resolution_scores(image: Image.Image) -> QualityScores:
    array = np.asarray(image)
    gray = _to_luminance(array)
    sharpness_score = normalize_score(_laplacian_variance(gray), 1200.0)
    blur_score = round(1.0 - sharpness_score, 4)

    mean_luma = float(gray.mean())
    exposure_score = _exposure_score(gray, mean_luma)
    contrast_score = normalize_score(float(gray.std()), 80.0)
    high_freq = np.abs(gray - mean_luma)
    noise_score = normalize_score(float(np.percentile(high_freq, 95)), 130.0)
    face_presence, face_sharpness_score, eye_open_confidence, face_quality_score = _detect_face_signals(
        array, gray, sharpness_score
    )
    aesthetic_score = round((contrast_score + exposure_score) / 2.0, 4)
    overall_score = round(
        0.35 * sharpness_score
        + 0.25 * exposure_score
        + 0.20 * contrast_score
        + 0.10 * aesthetic_score
        - 0.10 * noise_score,
        4,
    )
    overall_score = float(np.clip(overall_score, 0.0, 1.0))

    return QualityScores(
        sharpness_score=sharpness_score,
        blur_score=blur_score,
        exposure_score=exposure_score,
        contrast_score=contrast_score,
        noise_score=noise_score,
        face_presence=face_presence,
        face_sharpness_score=face_sharpness_score,
        eye_open_confidence=eye_open_confidence,
        face_quality_score=face_quality_score,
        aesthetic_score=aesthetic_score,
        overall_score=overall_score,
    )


def _numeric_diff_summary(baseline: list[QualityScores], current: list[QualityScores], field: str) -> dict:
    deltas = [
        float(getattr(new, field)) - float(getattr(old, field))
        for old, new in zip(baseline, current, strict=True)
    ]
    abs_deltas = [abs(delta) for delta in deltas]
    return {
        "mean_delta": round(float(np.mean(deltas)), 6),
        "mean_abs_delta": round(float(np.mean(abs_deltas)), 6),
        "max_abs_delta": round(float(max(abs_deltas, default=0.0)), 6),
    }


def _optional_numeric_diff_summary(baseline: list[QualityScores], current: list[QualityScores], field: str) -> dict:
    comparable = [
        (float(getattr(old, field)), float(getattr(new, field)))
        for old, new in zip(baseline, current, strict=True)
        if getattr(old, field) is not None and getattr(new, field) is not None
    ]
    if not comparable:
        return {"comparable_count": 0, "mean_delta": None, "mean_abs_delta": None, "max_abs_delta": None}

    deltas = [new - old for old, new in comparable]
    abs_deltas = [abs(delta) for delta in deltas]
    return {
        "comparable_count": len(comparable),
        "mean_delta": round(float(np.mean(deltas)), 6),
        "mean_abs_delta": round(float(np.mean(abs_deltas)), 6),
        "max_abs_delta": round(float(max(abs_deltas, default=0.0)), 6),
    }


def _score_diff_summary(baseline: list[QualityScores], current: list[QualityScores]) -> dict:
    numeric_fields = [
        "sharpness_score",
        "blur_score",
        "exposure_score",
        "contrast_score",
        "noise_score",
        "face_sharpness_score",
        "face_quality_score",
        "aesthetic_score",
        "overall_score",
    ]
    return {
        "count": len(current),
        "numeric_fields": {field: _numeric_diff_summary(baseline, current, field) for field in numeric_fields},
        "eye_open_confidence": _optional_numeric_diff_summary(baseline, current, "eye_open_confidence"),
        "face_presence_changed": sum(
            1 for old, new in zip(baseline, current, strict=True) if old.face_presence != new.face_presence
        ),
        "eye_open_none_changed": sum(
            1
            for old, new in zip(baseline, current, strict=True)
            if (old.eye_open_confidence is None) != (new.eye_open_confidence is None)
        ),
    }


def _measure_stage_breakdown(images: list[Image.Image]) -> dict:
    stage_seconds = {
        "scoring_image_array": 0.0,
        "luminance_conversion": 0.0,
        "sharpness_blur": 0.0,
        "exposure_contrast_noise": 0.0,
        "face_signals": 0.0,
    }

    for image in images:
        started = time.perf_counter()
        array = scoring_image_array(image)
        stage_seconds["scoring_image_array"] += time.perf_counter() - started

        started = time.perf_counter()
        gray = _to_luminance(array)
        stage_seconds["luminance_conversion"] += time.perf_counter() - started

        started = time.perf_counter()
        sharpness_score = normalize_score(_laplacian_variance(gray), 1200.0)
        _blur_score = round(1.0 - sharpness_score, 4)
        stage_seconds["sharpness_blur"] += time.perf_counter() - started

        started = time.perf_counter()
        mean_luma = float(gray.mean())
        _exposure = _exposure_score(gray, mean_luma)
        _contrast = normalize_score(float(gray.std()), 80.0)
        high_freq = np.abs(gray - mean_luma)
        _noise = normalize_score(float(np.percentile(high_freq, 95)), 130.0)
        stage_seconds["exposure_contrast_noise"] += time.perf_counter() - started

        started = time.perf_counter()
        _detect_face_signals(array, gray, sharpness_score)
        stage_seconds["face_signals"] += time.perf_counter() - started

    image_count = len(images)
    return {
        stage: {
            "seconds": round(seconds, 6),
            "seconds_per_image": round(seconds / image_count, 6) if image_count else None,
        }
        for stage, seconds in stage_seconds.items()
    }


def run_quality_scoring_bench(config: QualityScoringBenchConfig) -> dict:
    _validate_config(config)
    source_dir = config.output_dir / "source"
    paths = generate_synthetic_dataset(
        SyntheticDatasetConfig(
            output_dir=source_dir,
            count=config.count,
            width=config.width,
            height=config.height,
            jpeg_quality=config.jpeg_quality,
        )
    )
    images = [_open_rgb_image(path) for path in paths]

    current_scores: list[QualityScores] = []
    started = time.perf_counter()
    for image in images:
        current_scores.append(_compute_current_scores(image))
    total_seconds = time.perf_counter() - started

    legacy_scores = [_compute_legacy_full_resolution_scores(image) for image in images]
    sample_count = min(3, len(current_scores))

    return {
        "config": {
            "count": config.count,
            "width": config.width,
            "height": config.height,
            "jpeg_quality": config.jpeg_quality,
        },
        "timings": {
            "total_seconds": round(total_seconds, 6),
            "seconds_per_image": round(total_seconds / len(images), 6),
            "stages": _measure_stage_breakdown(images),
        },
        "score_diff_vs_legacy_full_resolution": _score_diff_summary(legacy_scores, current_scores),
        "sample_scores": [asdict(score) for score in current_scores[:sample_count]],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark FramePilot quality scoring on generated images.")
    parser.add_argument("--output", type=Path, help="Directory for generated benchmark images.")
    parser.add_argument("--count", default=12, type=int, help="Number of generated images to score.")
    parser.add_argument("--width", default=3000, type=int, help="Generated image width in pixels.")
    parser.add_argument("--height", default=2000, type=int, help="Generated image height in pixels.")
    parser.add_argument("--quality", default=88, type=int, help="Generated JPEG quality, from 1 to 100.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="framepilot-scoring-bench-") as temp_dir:
        output_dir = args.output or Path(temp_dir)
        result = run_quality_scoring_bench(
            QualityScoringBenchConfig(
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
