from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class QualityScores:
    sharpness_score: float
    blur_score: float
    exposure_score: float
    contrast_score: float
    noise_score: float
    face_quality_score: float
    aesthetic_score: float
    overall_score: float


def normalize_score(value: float, expected_max: float) -> float:
    if expected_max <= 0:
        return 0.0
    return round(float(np.clip(value / expected_max, 0.0, 1.0)), 4)


def _to_luminance(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image.astype(np.float32)
    rgb = image[..., :3].astype(np.float32)
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def _laplacian_variance(gray: np.ndarray) -> float:
    padded = np.pad(gray, 1, mode="edge")
    laplacian = (
        -4 * padded[1:-1, 1:-1]
        + padded[:-2, 1:-1]
        + padded[2:, 1:-1]
        + padded[1:-1, :-2]
        + padded[1:-1, 2:]
    )
    return float(laplacian.var())


def compute_quality_scores(image: np.ndarray) -> QualityScores:
    gray = _to_luminance(image)
    sharpness_score = normalize_score(_laplacian_variance(gray), 1200.0)
    blur_score = round(1.0 - sharpness_score, 4)

    mean_luma = float(gray.mean()) / 255.0
    exposure_score = round(1.0 - min(abs(mean_luma - 0.5) * 2.0, 1.0), 4)
    contrast_score = normalize_score(float(gray.std()), 80.0)

    high_freq = np.abs(gray - gray.mean())
    noise_score = normalize_score(float(np.percentile(high_freq, 95)), 130.0)
    face_quality_score = 0.0
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
        face_quality_score=face_quality_score,
        aesthetic_score=aesthetic_score,
        overall_score=overall_score,
    )

