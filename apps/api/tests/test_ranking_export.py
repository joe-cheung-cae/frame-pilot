import csv

from app.services.exporting import write_selection_csv
from app.services.ranking import rank_group


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
    assert "highest overall technical score" in ranked[0].explanation


def test_write_selection_csv_contains_user_decisions(tmp_path):
    target = tmp_path / "selection.csv"
    photos = [
        {"filename": "a.jpg", "user_status": "Pick", "star_rating": 5, "group_id": "g1", "overall_score": 0.9},
        {"filename": "b.jpg", "user_status": "Reject", "star_rating": 1, "group_id": "g1", "overall_score": 0.2},
    ]

    write_selection_csv(target, photos)

    with target.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {"filename": "a.jpg", "status": "Pick", "star_rating": "5", "group_id": "g1", "score": "0.900"},
        {"filename": "b.jpg", "status": "Reject", "star_rating": "1", "group_id": "g1", "score": "0.200"},
    ]
