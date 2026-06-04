import numpy as np
from PIL import Image

from app.image.scoring import (
    SCORING_LONG_EDGE,
    compute_quality_scores,
    compute_quality_scores_for_image,
    normalize_score,
    scoring_image_array,
)


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


def test_quality_scores_include_required_normalized_fields():
    scores = compute_quality_scores(np.full((96, 96, 3), 128, dtype=np.uint8))

    for field in [
        "sharpness_score",
        "blur_score",
        "exposure_score",
        "contrast_score",
        "noise_score",
        "face_sharpness_score",
        "face_quality_score",
        "aesthetic_score",
        "overall_score",
    ]:
        assert 0.0 <= getattr(scores, field) <= 1.0
    assert scores.face_presence is False
    assert scores.eye_open_confidence is None


def test_scoring_is_deterministic_for_same_image():
    image = np.full((128, 128, 3), 180, dtype=np.uint8)
    image[16:112:4, 24:104] = [40, 70, 210]

    assert compute_quality_scores(image) == compute_quality_scores(image)


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


def test_scoring_does_not_mutate_rgb_input():
    image = np.full((96, 96, 3), 180, dtype=np.uint8)
    image[24:72, 32:64] = [205, 142, 96]
    original = image.copy()

    compute_quality_scores(image)

    assert np.array_equal(image, original)


def test_pillow_scoring_uses_bounded_copy_without_mutating_image():
    image = Image.new("RGB", (SCORING_LONG_EDGE + 200, 1000), (128, 128, 128))
    image.putpixel((10, 10), (255, 255, 255))
    original_bytes = image.tobytes()

    scoring_array = scoring_image_array(image)
    scores = compute_quality_scores_for_image(image)

    assert scoring_array.shape[1] == SCORING_LONG_EDGE
    assert scoring_array.shape[0] < image.height
    assert 0.0 <= scores.overall_score <= 1.0
    assert image.size == (SCORING_LONG_EDGE + 200, 1000)
    assert image.tobytes() == original_bytes


def test_pillow_scoring_does_not_modify_source_file(tmp_path):
    source = tmp_path / "source.jpg"
    Image.new("RGB", (SCORING_LONG_EDGE + 200, 1000), (128, 128, 128)).save(source, "JPEG", quality=88)
    before = source.read_bytes()

    with Image.open(source) as opened:
        compute_quality_scores_for_image(opened.convert("RGB"))

    assert source.read_bytes() == before
