from dataclasses import asdict

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from app.ai.embeddings import cosine_similarity, image_embedding, perceptual_hash
from app.image.scoring import compute_quality_scores_for_image
from app.services.grouping import SimilarPhotoGroup, group_similar_photos
from app.services.ranking import rank_group


def _mountain_scene(offset: int = 0) -> Image.Image:
    image = Image.new("RGB", (240, 160), (112, 156, 196))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 88, 240, 160), fill=(70, 128, 82))
    draw.polygon([(0, 95), (70 + offset, 42), (140 + offset, 96)], fill=(82, 92, 96))
    draw.polygon([(78 + offset, 96), (164 + offset, 34), (250, 96)], fill=(95, 105, 108))
    draw.rectangle((24 + offset, 112, 84 + offset, 138), fill=(145, 85, 52))
    draw.rectangle((28 + offset, 100, 78 + offset, 116), fill=(168, 42, 36))
    draw.ellipse((184 + offset, 22, 208 + offset, 46), fill=(245, 208, 80))
    for x in range(0, 240, 18):
        x_offset = offset % 9
        draw.line((x + x_offset, 150, x + 8 + x_offset, 146), fill=(35, 75, 48), width=2)
    return image


def _city_scene() -> Image.Image:
    image = Image.new("RGB", (240, 160), (118, 155, 190))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 88, 240, 160), fill=(78, 92, 99))
    for index, x in enumerate(range(20, 210, 24)):
        height = 38 + (index % 3) * 16
        draw.rectangle((x, 88 - height, x + 14, 88), fill=(72 + index * 3, 78 + index * 2, 86 + index))
        draw.rectangle((x + 3, 88 - height + 8, x + 6, 88 - height + 12), fill=(230, 210, 120))
    draw.line((0, 112, 240, 106), fill=(148, 148, 136), width=6)
    draw.ellipse((176, 26, 202, 52), fill=(240, 198, 66))
    return image


def _detailed_market_scene(exposure: float = 1.0, blur_radius: float = 0.0) -> Image.Image:
    image = Image.new("RGB", (240, 160), (120, 150, 180))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 80, 240, 160), fill=(84, 120, 82))
    draw.rectangle((0, 112, 240, 160), fill=(92, 88, 78))
    for x in range(0, 240, 12):
        draw.line((x, 80, x + 18, 35 + (x % 25)), fill=(40 + (x % 60), 70, 50), width=3)
        draw.ellipse((x - 4, 40 + (x % 50), x + 8, 52 + (x % 50)), fill=(30, 110 + (x % 80), 45))
    for x in range(12, 228, 28):
        draw.rectangle((x, 96, x + 18, 132), fill=(150, 82 + (x % 60), 48))
        draw.rectangle((x + 4, 102, x + 8, 108), fill=(235, 230, 160))
        draw.rectangle((x + 11, 116, x + 15, 124), fill=(40, 70, 100))
    for y in range(118, 154, 8):
        draw.line((0, y, 240, y - 10), fill=(180, 170, 140), width=1)
    for index in range(60):
        draw.point(((index * 37) % 240, 85 + (index * 29) % 72), fill=(220, 220, 210))

    if exposure != 1.0:
        image = ImageEnhance.Brightness(image).enhance(exposure)
    if blur_radius:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return image


def _fixture_photo(
    photo_id: str,
    filename: str,
    image: Image.Image,
    capture_time: str | None = None,
    lens_model: str | None = "FramePilot 35mm",
) -> dict[str, object]:
    scores = compute_quality_scores_for_image(image)
    photo: dict[str, object] = {
        "id": photo_id,
        "filename": filename,
        "width": image.width,
        "height": image.height,
        "camera_model": "FramePilotCam",
        "focal_length": "35",
        "perceptual_hash": perceptual_hash(image),
        "embedding": image_embedding(image),
        **asdict(scores),
    }
    if capture_time is not None:
        photo["capture_time"] = capture_time
    if lens_model is not None:
        photo["lens_model"] = lens_model
    return photo


def _grouped_ids(groups: list[SimilarPhotoGroup]) -> set[frozenset[str]]:
    return {frozenset(group.photo_ids) for group in groups}


def _hash_distance(left: dict[str, object], right: dict[str, object]) -> int:
    return (int(str(left["perceptual_hash"]), 16) ^ int(str(right["perceptual_hash"]), 16)).bit_count()


def test_realistic_burst_fixture_groups_frames_with_incomplete_metadata():
    photos = [
        _fixture_photo("walk-01", "DSC_1042.JPG", _mountain_scene(), "2026-02-14T16:02:00"),
        _fixture_photo("walk-02-missing-date", "DSC_1043.JPG", _mountain_scene(offset=1)),
        _fixture_photo(
            "walk-03-missing-lens",
            "DSC_1044.JPG",
            _mountain_scene(offset=2),
            "2026-02-14T16:02:02",
            lens_model=None,
        ),
        _fixture_photo("skyline-01", "DSC_1090.JPG", _city_scene(), "2026-02-14T16:12:00"),
    ]

    groups = group_similar_photos(photos)

    assert _grouped_ids(groups) == {
        frozenset({"walk-01", "walk-02-missing-date", "walk-03-missing-lens"}),
        frozenset({"skyline-01"}),
    }


def test_realistic_lookalike_fixture_avoids_over_merging_when_hashes_disagree():
    overlook = _fixture_photo("trail-overlook", "DSC_2201.JPG", _mountain_scene(), "2026-02-14T17:30:00")
    skyline = _fixture_photo("city-skyline", "DSC_2202.JPG", _city_scene(), "2026-02-14T17:30:04")

    groups = group_similar_photos([overlook, skyline], similarity_threshold=0.96, max_time_gap_seconds=30)

    assert cosine_similarity(overlook["embedding"], skyline["embedding"]) > 0.96
    assert _hash_distance(overlook, skyline) > 8
    assert _grouped_ids(groups) == {frozenset({"trail-overlook"}), frozenset({"city-skyline"})}


def test_realistic_technical_failure_fixture_ranks_blur_and_exposure_explanations():
    photos = [
        _fixture_photo("sharp-balanced", "DSC_3001.JPG", _detailed_market_scene(), "2026-02-14T18:45:00"),
        _fixture_photo(
            "motion-blur",
            "DSC_3002.JPG",
            _detailed_market_scene(blur_radius=3),
            "2026-02-14T18:45:01",
        ),
        _fixture_photo(
            "blown-highlights",
            "DSC_3003.JPG",
            _detailed_market_scene(exposure=2.2),
            "2026-02-14T18:45:02",
        ),
    ]

    ranked = rank_group(photos)
    by_id = {item.photo_id: item for item in ranked}

    assert ranked[0].photo_id == "sharp-balanced"
    assert ranked[0].recommendation == "Pick"
    assert by_id["motion-blur"].recommendation == "Reject"
    assert "weaker sharpness" in by_id["motion-blur"].explanation
    assert by_id["blown-highlights"].recommendation == "Reject"
    assert "weaker exposure" in by_id["blown-highlights"].explanation
