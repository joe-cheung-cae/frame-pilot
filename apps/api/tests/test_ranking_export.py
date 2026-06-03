import csv
import zipfile

from app.services.exporting import copy_selected_files, write_selection_csv, zip_selected_files
from app.services.ranking import final_score, rank_group


def test_rank_group_selects_highest_explainable_score():
    photos = [
        {
            "id": "low",
            "sharpness_score": 0.2,
            "exposure_score": 0.7,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.4,
            "duplicate_penalty": 0.0,
        },
        {
            "id": "high",
            "sharpness_score": 0.9,
            "exposure_score": 0.8,
            "face_quality_score": 0.3,
            "aesthetic_score": 0.6,
            "duplicate_penalty": 0.0,
        },
    ]

    ranked = rank_group(photos)

    assert ranked[0].photo_id == "high"
    assert "highest overall score" in ranked[0].explanation
    assert "sharpness" in ranked[0].explanation


def test_final_score_adjusts_weights_for_landscape_like_photos():
    photo = {
        "id": "landscape",
        "width": 6000,
        "height": 4000,
        "sharpness_score": 0.8,
        "exposure_score": 0.7,
        "contrast_score": 0.6,
        "noise_score": 0.2,
        "face_quality_score": 0.0,
        "aesthetic_score": 0.5,
        "duplicate_penalty": 0.0,
    }

    assert final_score(photo) == 0.649


def test_final_score_adjusts_weights_for_portrait_like_photos():
    photo = {
        "id": "portrait",
        "face_presence": True,
        "sharpness_score": 0.8,
        "exposure_score": 0.7,
        "contrast_score": 0.6,
        "noise_score": 0.2,
        "face_quality_score": 0.8,
        "aesthetic_score": 0.5,
        "duplicate_penalty": 0.0,
    }

    assert final_score(photo) == 0.724


def test_rank_group_prefers_sharp_well_exposed_photo_over_blurry_or_badly_exposed_similar_photo():
    photos = [
        {
            "id": "sharp-balanced",
            "sharpness_score": 0.92,
            "exposure_score": 0.88,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.82,
            "duplicate_penalty": 0.1,
        },
        {
            "id": "blurry",
            "sharpness_score": 0.18,
            "exposure_score": 0.86,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.62,
            "duplicate_penalty": 0.1,
        },
        {
            "id": "underexposed",
            "sharpness_score": 0.9,
            "exposure_score": 0.12,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.3,
            "duplicate_penalty": 0.1,
        },
    ]

    ranked = rank_group(photos)

    assert ranked[0].photo_id == "sharp-balanced"
    assert ranked[0].recommendation == "Pick"
    assert {ranked[1].photo_id, ranked[2].photo_id} == {"blurry", "underexposed"}
    assert all(item.recommendation == "Reject" for item in ranked[1:])
    explanations = {item.photo_id: item.explanation for item in ranked}
    assert "weaker sharpness" in explanations["blurry"]
    assert "weaker exposure" in explanations["underexposed"]


def test_rank_group_rewards_contrast_and_penalizes_noise_risk():
    photos = [
        {
            "id": "clean-contrast",
            "sharpness_score": 0.7,
            "exposure_score": 0.7,
            "contrast_score": 0.9,
            "noise_score": 0.1,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.75,
            "duplicate_penalty": 0.0,
        },
        {
            "id": "flat-noisy",
            "sharpness_score": 0.7,
            "exposure_score": 0.7,
            "contrast_score": 0.2,
            "noise_score": 0.9,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.45,
            "duplicate_penalty": 0.0,
        },
    ]

    ranked = rank_group(photos)

    assert ranked[0].photo_id == "clean-contrast"
    assert "contrast" in ranked[0].explanation
    assert ranked[1].recommendation == "Reject"


def test_rank_group_explains_face_and_eye_quality_when_it_leads():
    photos = [
        {
            "id": "face",
            "sharpness_score": 0.4,
            "exposure_score": 0.4,
            "face_quality_score": 1.0,
            "eye_open_confidence": 0.8,
            "aesthetic_score": 0.4,
            "duplicate_penalty": 0.0,
        },
        {
            "id": "plain",
            "sharpness_score": 0.45,
            "exposure_score": 0.45,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.45,
            "duplicate_penalty": 0.0,
        },
    ]

    ranked = rank_group(photos)

    assert ranked[0].photo_id == "face"
    assert "experimental face and open-eye signals" in ranked[0].explanation


def test_rank_group_explains_maybe_and_reject_with_metric_context():
    photos = [
        {
            "id": "best",
            "sharpness_score": 0.9,
            "exposure_score": 0.9,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.9,
            "duplicate_penalty": 0.0,
        },
        {
            "id": "close",
            "sharpness_score": 0.8,
            "exposure_score": 0.85,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.85,
            "duplicate_penalty": 0.0,
        },
        {
            "id": "weak",
            "sharpness_score": 0.1,
            "exposure_score": 0.2,
            "face_quality_score": 0.0,
            "aesthetic_score": 0.2,
            "duplicate_penalty": 0.0,
        },
    ]

    ranked = rank_group(photos)

    assert ranked[1].recommendation == "Maybe"
    assert "within" in ranked[1].explanation
    assert "weaker" in ranked[1].explanation
    assert ranked[2].recommendation == "Reject"
    assert "trails the strongest image" in ranked[2].explanation
    assert "weaker" in ranked[2].explanation


def test_write_selection_csv_contains_user_decisions(tmp_path):
    target = tmp_path / "selection.csv"
    photos = [
        {
            "filename": "a.jpg",
            "original_path": "/shoot/a.jpg",
            "user_status": "Pick",
            "star_rating": 5,
            "group_id": "g1",
            "ai_recommendation": "Pick",
            "overall_score": 0.9,
            "sharpness_score": 0.8,
            "exposure_score": 0.7,
            "contrast_score": 0.6,
            "face_presence": True,
            "face_sharpness_score": 0.55,
            "eye_open_confidence": 0.75,
            "face_quality_score": 0.65,
            "width": 4000,
            "height": 3000,
            "recommendation_explanation": "Recommended because it is sharp.",
        },
        {
            "filename": "b.jpg",
            "original_path": "/shoot/b.jpg",
            "user_status": "Reject",
            "star_rating": 1,
            "group_id": "g1",
            "ai_recommendation": "Reject",
            "overall_score": 0.2,
            "sharpness_score": 0.1,
            "exposure_score": 0.3,
            "contrast_score": 0.4,
            "face_presence": False,
            "face_sharpness_score": 0.0,
            "eye_open_confidence": None,
            "face_quality_score": 0.0,
            "width": 4000,
            "height": 3000,
            "recommendation_explanation": "Rejected because it is weaker.",
        },
    ]

    write_selection_csv(target, photos)

    with target.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {
            "filename": "a.jpg",
            "original_path": "/shoot/a.jpg",
            "status": "Pick",
            "star_rating": "5",
            "group_id": "g1",
            "ai_recommendation": "Pick",
            "score": "0.900",
            "sharpness_score": "0.800",
            "exposure_score": "0.700",
            "contrast_score": "0.600",
            "face_presence": "true",
            "face_sharpness_score": "0.550",
            "eye_open_confidence": "0.750",
            "face_quality_score": "0.650",
            "width": "4000",
            "height": "3000",
            "recommendation_explanation": "Recommended because it is sharp.",
        },
        {
            "filename": "b.jpg",
            "original_path": "/shoot/b.jpg",
            "status": "Reject",
            "star_rating": "1",
            "group_id": "g1",
            "ai_recommendation": "Reject",
            "score": "0.200",
            "sharpness_score": "0.100",
            "exposure_score": "0.300",
            "contrast_score": "0.400",
            "face_presence": "false",
            "face_sharpness_score": "0.000",
            "eye_open_confidence": "",
            "face_quality_score": "0.000",
            "width": "4000",
            "height": "3000",
            "recommendation_explanation": "Rejected because it is weaker.",
        },
    ]


def test_folder_export_preserves_files_with_duplicate_names(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = first_dir / "frame.jpg"
    second = second_dir / "frame.jpg"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    copy_selected_files(tmp_path / "selected", [{"original_path": str(first)}, {"original_path": str(second)}])

    assert (tmp_path / "selected" / "frame.jpg").read_bytes() == b"first"
    assert (tmp_path / "selected" / "frame-1.jpg").read_bytes() == b"second"


def test_zip_export_preserves_files_with_duplicate_names(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = first_dir / "frame.jpg"
    second = second_dir / "frame.jpg"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    target = zip_selected_files(
        tmp_path / "selected.zip", [{"original_path": str(first)}, {"original_path": str(second)}]
    )

    with zipfile.ZipFile(target) as archive:
        assert sorted(archive.namelist()) == ["frame-1.jpg", "frame.jpg"]
        assert archive.read("frame.jpg") == b"first"
        assert archive.read("frame-1.jpg") == b"second"
