import csv
import zipfile

from app.services.exporting import csv_safe_cell, write_selection_csv, zip_selected_files


def test_csv_safe_cell_neutralizes_formula_prefixes():
    for prefix in ("=", "+", "-", "@", "\t", "\r"):
        assert csv_safe_cell(f"{prefix}cmd") == f"'{prefix}cmd"
    assert csv_safe_cell("normal.jpg") == "normal.jpg"


def test_write_selection_csv_neutralizes_dangerous_filename(tmp_path):
    target = tmp_path / "selection.csv"
    write_selection_csv(
        target,
        [
            {
                "id": "1",
                "filename": "=cmd|' /C calc'!A0.jpg",
                "original_path": "/tmp/=cmd.jpg",
                "recommendation_explanation": "+dangerous",
                "overall_score": 0.5,
            }
        ],
    )
    with target.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["filename"].startswith("'=")
    assert rows[0]["recommendation_explanation"].startswith("'+")


def test_zip_selected_files_stores_jpeg_without_deflate(tmp_path):
    originals = tmp_path / "originals"
    originals.mkdir()
    source = originals / "frame.jpg"
    source.write_bytes(b"\xff\xd8\xff" + b"0" * 1000)
    target = tmp_path / "out.zip"
    zip_selected_files(
        target,
        [{"filename": "frame.jpg", "original_path": str(source), "project_copy_path": str(source)}],
        project_root=tmp_path,
    )
    with zipfile.ZipFile(target) as archive:
        info = archive.getinfo("frame.jpg")
        assert info.compress_type == zipfile.ZIP_STORED
        assert archive.read("frame.jpg") == source.read_bytes()
