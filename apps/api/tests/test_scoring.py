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


def test_exposure_penalizes_clipped_highlights_and_shadows():
    balanced = compute_quality_scores(np.full((96, 96), 128, dtype=np.uint8))
    blown = compute_quality_scores(np.full((96, 96), 252, dtype=np.uint8))
    crushed = compute_quality_scores(np.full((96, 96), 2, dtype=np.uint8))
    high_contrast = np.zeros((96, 96), dtype=np.uint8)
    high_contrast[:, ::2] = 255
    high_contrast_scores = compute_quality_scores(high_contrast)

    assert balanced.exposure_score > high_contrast_scores.exposure_score
    assert high_contrast_scores.exposure_score > blown.exposure_score
    assert high_contrast_scores.exposure_score > crushed.exposure_score


def test_detects_simple_face_and_eye_signals():
    image = np.full((128, 128, 3), 245, dtype=np.uint8)
    yy, xx = np.ogrid[:128, :128]
    face = ((xx - 64) ** 2) / (34**2) + ((yy - 62) ** 2) / (42**2) <= 1
    image[face] = [205, 142, 96]
    image[48:54, 48:56] = [25, 18, 14]
    image[48:54, 72:80] = [25, 18, 14]
    image[78:82, 55:73] = [110, 55, 50]

    scores = compute_quality_scores(image)

    assert scores.face_presence is True
    assert scores.eye_open_confidence is not None
    assert scores.eye_open_confidence > 0.1
    assert scores.face_quality_score > 0


def test_plain_image_has_no_face_signals():
    scores = compute_quality_scores(np.full((96, 96, 3), 128, dtype=np.uint8))

    assert scores.face_presence is False
    assert scores.face_sharpness_score == 0.0
    assert scores.eye_open_confidence is None
    assert scores.face_quality_score == 0.0
