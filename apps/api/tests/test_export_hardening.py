import csv
import os
import time
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

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
    """Practical Zip64/large-member smoke for #71 / legacy #13.

    Default CI keeps members multi-MB (not >4GB). Opt-in
    ``test_zip_selected_files_zip64_archive_above_4gb`` covers true Zip64 size.
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


def test_zip_stored_is_measurably_faster_than_deflated_with_identical_bytes(tmp_path):
    """ZIP_STORED beats ZIP_DEFLATED for already-compressed JPEG payloads (#71).

    Measured on this host (80×1MiB high-entropy pseudo-JPEG): STORED ~0.05s vs
    DEFLATED ~1.23s (delta ~1.18s). Assert messages record the live before/after
    timing each run for CI evidence.
    """
    originals = tmp_path / "originals"
    originals.mkdir()
    member_count = 80
    member_size = 1024 * 1024
    photos: list[dict] = []
    sources: dict[str, bytes] = {}
    for index in range(member_count):
        name = f"frame-{index:03d}.jpg"
        # High-entropy payload: DEFLATE spends CPU without shrinking, so STORED wins clearly.
        payload = b"\xff\xd8\xff" + os.urandom(member_size - 3)
        path = originals / name
        path.write_bytes(payload)
        sources[name] = payload
        photos.append(
            {
                "filename": name,
                "original_path": str(path),
                "project_copy_path": str(path),
            }
        )

    stored_target = tmp_path / "stored.zip"
    deflated_target = tmp_path / "deflated.zip"

    started = time.perf_counter()
    zip_selected_files(stored_target, photos, project_root=tmp_path)
    stored_seconds = time.perf_counter() - started

    started = time.perf_counter()
    with zipfile.ZipFile(deflated_target, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for photo in photos:
            source = Path(photo["project_copy_path"])
            archive.write(source, arcname=source.name, compress_type=zipfile.ZIP_DEFLATED)
    deflated_seconds = time.perf_counter() - started

    delta = deflated_seconds - stored_seconds
    assert stored_seconds < deflated_seconds, (
        f"ZIP_STORED must be faster than ZIP_DEFLATED for JPEG payloads; "
        f"stored={stored_seconds:.4f}s deflated={deflated_seconds:.4f}s delta={delta:.4f}s"
    )
    # Soft floor: noisy CI hosts can shrink deltas; still require a positive gap.
    assert delta > 0.01, (
        f"timing delta too small to be stable evidence; "
        f"stored={stored_seconds:.4f}s deflated={deflated_seconds:.4f}s delta={delta:.4f}s"
    )

    with zipfile.ZipFile(stored_target) as stored_archive, zipfile.ZipFile(deflated_target) as deflated_archive:
        assert sorted(stored_archive.namelist()) == sorted(sources)
        assert sorted(deflated_archive.namelist()) == sorted(sources)
        for name, expected in sources.items():
            assert stored_archive.getinfo(name).compress_type == zipfile.ZIP_STORED
            assert stored_archive.read(name) == expected
            assert deflated_archive.read(name) == expected


@pytest.mark.slow
def test_zip_selected_files_zip64_archive_above_4gb(tmp_path):
    """Opt-in Zip64 >4GB archive proof (#71). Set FRAMEPILOT_LARGE_ZIP=1 to run.

    Default CI does **not** run this test (too heavy). Default coverage is
    ``test_zip_selected_files_uses_allow_zip64_for_large_members`` (allowZip64 +
    multi-MB STORED members). This opt-in gate proves archives above 4 GiB.
    """
    if os.environ.get("FRAMEPILOT_LARGE_ZIP") != "1":
        pytest.skip("Set FRAMEPILOT_LARGE_ZIP=1 to run >4GB Zip64 proof")

    originals = tmp_path / "originals"
    originals.mkdir()
    four_gib_plus = (4 * 1024 * 1024 * 1024) + 1024
    source = originals / "huge.jpg"
    header = b"\xff\xd8\xff"
    trailer = b"ZIP64-TAIL"
    with source.open("wb") as handle:
        handle.write(header)
        handle.seek(four_gib_plus - len(trailer))
        handle.write(trailer)
    assert source.stat().st_size == four_gib_plus

    target = tmp_path / "zip64-huge.zip"
    with patch("app.services.exporting.zipfile.ZipFile", wraps=zipfile.ZipFile) as zip_file_cls:
        zip_selected_files(
            target,
            [{"filename": source.name, "original_path": str(source), "project_copy_path": str(source)}],
            project_root=tmp_path,
        )

    assert zip_file_cls.call_args.kwargs.get("allowZip64") is True
    assert target.stat().st_size > 4 * 1024 * 1024 * 1024

    with zipfile.ZipFile(target) as archive:
        info = archive.getinfo(source.name)
        assert info.file_size == four_gib_plus
        assert info.compress_type == zipfile.ZIP_STORED
        assert info.file_size > 0xFFFFFFFF
        with archive.open(source.name) as member:
            assert member.read(len(header)) == header
            member.seek(four_gib_plus - len(trailer))
            assert member.read(len(trailer)) == trailer
