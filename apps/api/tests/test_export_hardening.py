import csv
import zipfile
from unittest.mock import patch

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


def test_zip_selected_files_uses_allow_zip64_for_large_members(tmp_path):
    """Practical Zip64/large-member smoke for #13.

    A full >4GB archive is too slow for CI; timing deltas are N/A here. This covers
    allowZip64=True and multiple large ZIP_STORED JPEG/WebP members with byte-identical extracts.
    """
    originals = tmp_path / "originals"
    originals.mkdir()
    # Several multi-megabyte members exercise large local headers without a multi-GB CI runtime.
    member_size = 8 * 1024 * 1024
    photos = []
    sources: dict[str, Path] = {}
    for index, (name, header) in enumerate(
        (
            ("large-a.jpg", b"\xff\xd8\xff"),
            ("large-b.jpg", b"\xff\xd8\xff"),
            ("large-c.webp", b"RIFF"),
        )
    ):
        path = originals / name
        path.write_bytes(header + bytes([(index + 1) % 256]) * (member_size - len(header)))
        sources[name] = path
        photos.append(
            {
                "filename": name,
                "original_path": str(path),
                "project_copy_path": str(path),
            }
        )

    target = tmp_path / "large-stored.zip"
    with patch("app.services.exporting.zipfile.ZipFile", wraps=zipfile.ZipFile) as zip_file_cls:
        zip_selected_files(target, photos, project_root=tmp_path)

    assert zip_file_cls.call_args.kwargs.get("allowZip64") is True
    assert zip_file_cls.call_args.kwargs.get("compression") == zipfile.ZIP_STORED
    assert target.is_file()
    assert target.stat().st_size > member_size * len(photos)

    with zipfile.ZipFile(target) as archive:
        assert sorted(archive.namelist()) == sorted(sources)
        for name, source in sources.items():
            info = archive.getinfo(name)
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.file_size == member_size
            assert archive.read(name) == source.read_bytes()