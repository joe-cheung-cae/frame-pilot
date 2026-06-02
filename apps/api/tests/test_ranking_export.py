import csv
import zipfile

from app.services.exporting import copy_selected_files, write_selection_csv, zip_selected_files
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

    target = zip_selected_files(tmp_path / "selected.zip", [{"original_path": str(first)}, {"original_path": str(second)}])

    with zipfile.ZipFile(target) as archive:
        assert sorted(archive.namelist()) == ["frame-1.jpg", "frame.jpg"]
        assert archive.read("frame.jpg") == b"first"
        assert archive.read("frame-1.jpg") == b"second"
