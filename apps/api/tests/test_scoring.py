import numpy as np

from app.image.scoring import compute_quality_scores, normalize_score


def test_normalize_score_clamps_values():
    assert normalize_score(-10, 100) == 0.0
    assert normalize_score(50, 100) == 0.5
    assert normalize_score(150, 100) == 1.0


def test_sharp_image_scores_higher_than_blurry_image():
    sharp = np.zeros((96, 96), dtype=np.uint8)
    sharp[::2, :] = 255
    blurry = np.full((96, 96), 128, dtype=np.uint8)

    sharp_scores = compute_quality_scores(sharp)
    blurry_scores = compute_quality_scores(blurry)

    assert sharp_scores.sharpness_score > blurry_scores.sharpness_score
    assert sharp_scores.blur_score < blurry_scores.blur_score
    assert sharp_scores.overall_score > blurry_scores.overall_score
