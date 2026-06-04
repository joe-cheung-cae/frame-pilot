from dataclasses import dataclass

import numpy as np
from PIL import Image

SCORING_LONG_EDGE = 1600
SCORING_RESAMPLE = Image.Resampling.BICUBIC
SCORING_REDUCING_GAP = 2.0


@dataclass(frozen=True)
class QualityScores:
    sharpness_score: float
    blur_score: float
    exposure_score: float
    contrast_score: float
    noise_score: float
    face_presence: bool
    face_sharpness_score: float
    eye_open_confidence: float | None
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


def _bounded_scoring_size(width: int, height: int, long_edge: int = SCORING_LONG_EDGE) -> tuple[int, int]:
    current_long_edge = max(width, height)
    if current_long_edge <= long_edge:
        return width, height

    scale = long_edge / float(current_long_edge)
    return max(1, round(width * scale)), max(1, round(height * scale))


def scoring_image_array(image: Image.Image) -> np.ndarray:
    width, height = image.size
    target_size = _bounded_scoring_size(width, height)
    scoring_image = image if target_size == image.size else image.resize(
        target_size,
        resample=SCORING_RESAMPLE,
        reducing_gap=SCORING_REDUCING_GAP,
    )
    if scoring_image.mode not in {"L", "RGB"}:
        scoring_image = scoring_image.convert("RGB")
    return np.asarray(scoring_image)


def _laplacian_variance(gray: np.ndarray) -> float:
    padded = np.pad(gray, 1, mode="edge")
    laplacian = -4 * padded[1:-1, 1:-1] + padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:]
    return float(laplacian.var())


def _exposure_score(gray: np.ndarray, mean_luma: float | None = None) -> float:
    mean_luma_value = float(gray.mean()) if mean_luma is None else mean_luma
    mean_balance = 1.0 - min(abs(mean_luma_value / 255.0 - 0.5) * 2.0, 1.0)
    clipped_ratio = float(((gray <= 5.0) | (gray >= 250.0)).mean())
    clipping_quality = 1.0 - min(clipped_ratio, 1.0)
    return round(float(np.clip(0.75 * mean_balance + 0.25 * clipping_quality, 0.0, 1.0)), 4)


def _detect_face_signals(
    image: np.ndarray, gray: np.ndarray, sharpness_score: float
) -> tuple[bool, float, float | None, float]:
    if image.ndim < 3:
        return False, 0.0, None, 0.0

    rgb = image[..., :3]
    red = rgb[..., 0]
    green = rgb[..., 1]
    blue = rgb[..., 2]
    skin_mask = (
        (red > 95)
        & (green > 70)
        & (blue > 45)
        & ((np.maximum.reduce([red, green, blue]) - np.minimum.reduce([red, green, blue])) > 15)
        & (red > green)
        & (green >= blue * 0.75)
    )
    ys, xs = np.where(skin_mask)
    skin_ratio = float(skin_mask.mean())
    if skin_ratio < 0.015 or len(xs) < 32:
        return False, 0.0, None, 0.0

    height, width = gray.shape
    left, right = int(xs.min()), int(xs.max())
    top, bottom = int(ys.min()), int(ys.max())
    box_width = max(1, right - left + 1)
    box_height = max(1, bottom - top + 1)
    aspect = box_width / box_height
    box_area_ratio = (box_width * box_height) / float(width * height)
    fill_ratio = len(xs) / float(box_width * box_height)
    looks_like_face = 0.45 <= aspect <= 1.45 and 0.03 <= box_area_ratio <= 0.75 and fill_ratio >= 0.35
    if not looks_like_face:
        return False, 0.0, None, 0.0

    eye_top = top + int(box_height * 0.18)
    eye_bottom = top + int(box_height * 0.55)
    eye_left = left + int(box_width * 0.15)
    eye_right = left + int(box_width * 0.85)
    eye_region = gray[eye_top:eye_bottom, eye_left:eye_right]
    if eye_region.size:
        dark_threshold = max(20.0, float(np.percentile(eye_region, 30)) * 0.75)
        dark_ratio = float((eye_region < dark_threshold).mean())
        eye_open_confidence = round(float(np.clip(dark_ratio * 8.0, 0.0, 1.0)), 4)
    else:
        eye_open_confidence = None

    face_region = gray[top : bottom + 1, left : right + 1]
    face_sharpness_score = normalize_score(_laplacian_variance(face_region), 800.0) if face_region.size else 0.0
    face_quality_score = round(
        float(
            np.clip(
                0.45 * face_sharpness_score + 0.30 * (eye_open_confidence or 0.0) + 0.25 * sharpness_score,
                0.0,
                1.0,
            )
        ),
        4,
    )
    return True, face_sharpness_score, eye_open_confidence, face_quality_score


def compute_quality_scores(image: np.ndarray) -> QualityScores:
    gray = _to_luminance(image)
    sharpness_score = normalize_score(_laplacian_variance(gray), 1200.0)
    blur_score = round(1.0 - sharpness_score, 4)

    mean_luma = float(gray.mean())
    exposure_score = _exposure_score(gray, mean_luma)
    contrast_score = normalize_score(float(gray.std()), 80.0)

    high_freq = np.abs(gray - mean_luma)
    noise_score = normalize_score(float(np.percentile(high_freq, 95)), 130.0)
    face_presence, face_sharpness_score, eye_open_confidence, face_quality_score = _detect_face_signals(
        image, gray, sharpness_score
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


def compute_quality_scores_for_image(image: Image.Image) -> QualityScores:
    return compute_quality_scores(scoring_image_array(image))
