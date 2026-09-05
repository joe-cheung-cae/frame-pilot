import os
import stat
from pathlib import Path

import pytest
from PIL import Image

from app.services import importing
from app.services.importing import (
    PATH_IMPORT_MAX_INPUT_ENTRIES,
    RAW_NO_PREVIEW_REASON,
    expand_import_paths,
    unsupported_image_reason,
)
from tests.avif_helpers import tiny_avif_bytes
from tests.heic_helpers import tiny_heic_bytes
from tests.raw_helpers import tiny_dng_bytes, tiny_dng_without_preview_bytes


def _write_jpeg(path: Path, color=(80, 120, 40)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 24), color=color).save(path, format="JPEG")


def test_expand_nested_jpegs_and_skips(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    source = tmp_path / "card"
    _write_jpeg(source / "a.jpg")
    _write_jpeg(source / "nested" / "b.JPG")
    (source / "notes.txt").write_text("skip me", encoding="utf-8")
    (source / "shot.heic").write_bytes(tiny_heic_bytes())
    (source / "frame.dng").write_bytes(b"not-raw")

    expanded = expand_import_paths([str(source)], project_root)

    assert [path.name.lower() for path in expanded.files] == ["a.jpg", "b.jpg", "shot.heic"]
    reasons = {item["filename"]: item["reason"] for item in expanded.skipped}
    assert reasons["notes.txt"] == "Only JPEG, PNG, and WebP files are supported"
    assert reasons["frame.dng"] == RAW_NO_PREVIEW_REASON
    assert reasons["frame.dng"] == unsupported_image_reason("frame.dng")
    assert "shot.heic" not in reasons


def test_expand_includes_avif_and_still_skips_raw(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    source = tmp_path / "card"
    _write_jpeg(source / "a.jpg")
    (source / "still.avif").write_bytes(tiny_avif_bytes())
    (source / "clip.avifs").write_bytes(b"sequence")
    (source / "frame.dng").write_bytes(b"not-raw")

    expanded = expand_import_paths([str(source)], project_root)

    assert [path.name.lower() for path in expanded.files] == ["a.jpg", "still.avif"]
    reasons = {item["filename"]: item["reason"] for item in expanded.skipped}
    assert reasons["clip.avifs"] == "Only JPEG, PNG, and WebP files are supported"
    assert reasons["frame.dng"] == RAW_NO_PREVIEW_REASON
    assert "still.avif" not in reasons


def test_expand_includes_dng_with_preview_and_skips_without(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    source = tmp_path / "card"
    _write_jpeg(source / "a.jpg")
    (source / "frame.dng").write_bytes(tiny_dng_bytes())
    (source / "empty.dng").write_bytes(tiny_dng_without_preview_bytes())
    (source / "garbage.dng").write_bytes(b"not-a-real-raw")

    expanded = expand_import_paths([str(source)], project_root)

    assert [path.name.lower() for path in expanded.files] == ["a.jpg", "frame.dng"]
    reasons = {item["filename"]: item["reason"] for item in expanded.skipped}
    assert reasons["empty.dng"] == RAW_NO_PREVIEW_REASON
    assert reasons["garbage.dng"] == RAW_NO_PREVIEW_REASON
    assert "frame.dng" not in reasons


def test_expand_rejects_relative_missing_and_empty(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    with pytest.raises(ValueError, match="At least one path"):
        expand_import_paths([], project_root)
    with pytest.raises(ValueError, match="absolute"):
        expand_import_paths(["relative.jpg"], project_root)
    with pytest.raises(ValueError, match="does not exist"):
        expand_import_paths([str(tmp_path / "missing.jpg")], project_root)


def test_expand_rejects_too_many_input_entries(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    too_many = [str(tmp_path / f"{index}.jpg") for index in range(PATH_IMPORT_MAX_INPUT_ENTRIES + 1)]
    with pytest.raises(ValueError, match="Too many input paths"):
        expand_import_paths(too_many, project_root)


def test_expand_rejects_too_many_expanded_files(tmp_path, monkeypatch):
    monkeypatch.setattr(importing, "PATH_IMPORT_MAX_EXPANDED_FILES", 2)
    project_root = tmp_path / "project"
    project_root.mkdir()
    folder = tmp_path / "card"
    _write_jpeg(folder / "one.jpg")
    _write_jpeg(folder / "two.jpg")
    _write_jpeg(folder / "three.jpg")
    with pytest.raises(ValueError, match="20000|exceeded|2"):
        expand_import_paths([str(folder)], project_root)


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
def test_expand_does_not_follow_symlink_out(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside = tmp_path / "outside"
    _write_jpeg(outside / "secret.jpg")
    walked = tmp_path / "card"
    walked.mkdir()
    _write_jpeg(walked / "keep.jpg")
    os.symlink(outside / "secret.jpg", walked / "link.jpg")

    expanded = expand_import_paths([str(walked)], project_root)
    assert [path.name for path in expanded.files] == ["keep.jpg"]


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO requires POSIX")
def test_expand_skips_fifo(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    source = tmp_path / "card"
    source.mkdir()
    _write_jpeg(source / "keep.jpg")
    fifo = source / "photo.jpg"
    os.mkfifo(fifo)
    assert stat.S_ISFIFO(fifo.stat().st_mode)

    expanded = expand_import_paths([str(source)], project_root)
    assert [path.name for path in expanded.files] == ["keep.jpg"]


def test_expand_skips_files_inside_project(tmp_path):
    project_root = tmp_path / "project"
    originals = project_root / "originals"
    originals.mkdir(parents=True)
    _write_jpeg(originals / "already.jpg")
    outside = tmp_path / "card" / "keep.jpg"
    _write_jpeg(outside)

    expanded = expand_import_paths([str(originals / "already.jpg"), str(outside)], project_root)
    assert expanded.files == [outside.resolve()]
    assert expanded.skipped[0]["reason"] == "Source is inside the project folder"


def test_expand_is_deterministic_and_dedupes(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    first = tmp_path / "z.jpg"
    second = tmp_path / "a.jpg"
    _write_jpeg(first)
    _write_jpeg(second)
    expanded = expand_import_paths([str(first), str(second), str(first)], project_root)
    assert expanded.files == [second.resolve(), first.resolve()]
