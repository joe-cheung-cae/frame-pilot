from pathlib import Path

import rawpy
from PIL import ImageOps

from app.image.raw_preview import (
    RAW_DEVELOP_FAILED_REASON,
    RAW_NO_PREVIEW_REASON,
    extract_raw_preview_image,
    open_raw_import_image,
)
from app.services.exporting import STORED_IMAGE_EXTENSIONS
from app.services.importing import RAW_EXTENSIONS, SUPPORTED_EXTENSIONS, unsupported_image_reason
from tests.raw_helpers import (
    TINY_DNG_CFA_SIZE,
    TINY_DNG_PREVIEW_SIZE,
    tiny_dng_bytes,
    tiny_dng_without_preview_bytes,
)


def _track_rawpy_calls(monkeypatch) -> list[str]:
    called: list[str] = []
    original_imread = rawpy.imread

    class TrackingRaw:
        def __init__(self, inner: rawpy.RawPy) -> None:
            self._inner = inner

        def extract_thumb(self):
            called.append("extract_thumb")
            return self._inner.extract_thumb()

        def postprocess(self, *args, **kwargs):
            called.append("postprocess")
            return self._inner.postprocess(*args, **kwargs)

        def __enter__(self):
            self._inner.__enter__()
            return self

        def __exit__(self, *args):
            return self._inner.__exit__(*args)

    def tracking_imread(path):
        return TrackingRaw(original_imread(path))

    monkeypatch.setattr(rawpy, "imread", tracking_imread)
    return called


def test_supported_extensions_include_raw() -> None:
    assert RAW_EXTENSIONS == {".arw", ".cr3", ".dng", ".nef"}
    assert RAW_EXTENSIONS.issubset(SUPPORTED_EXTENSIONS)
    assert RAW_EXTENSIONS.issubset(STORED_IMAGE_EXTENSIONS)


def test_extract_raw_preview_image_returns_preview_rgb(tmp_path: Path) -> None:
    path = tmp_path / "frame.dng"
    path.write_bytes(tiny_dng_bytes(size=TINY_DNG_PREVIEW_SIZE, color=(12, 34, 56)))
    opened = extract_raw_preview_image(path)
    image = ImageOps.exif_transpose(opened).convert("RGB")
    assert image.size == TINY_DNG_PREVIEW_SIZE
    assert image.mode == "RGB"


def test_extract_raw_preview_does_not_call_postprocess(tmp_path: Path, monkeypatch) -> None:
    called = _track_rawpy_calls(monkeypatch)
    path = tmp_path / "frame.dng"
    path.write_bytes(tiny_dng_bytes())
    image = extract_raw_preview_image(path)
    assert called == ["extract_thumb"]
    assert image.size == TINY_DNG_PREVIEW_SIZE


def test_extract_raw_preview_missing_thumb_raises(tmp_path: Path) -> None:
    path = tmp_path / "frame.dng"
    path.write_bytes(tiny_dng_without_preview_bytes())
    try:
        extract_raw_preview_image(path)
    except ValueError as error:
        assert str(error) == RAW_NO_PREVIEW_REASON
    else:
        raise AssertionError("expected no-preview error")


def test_extract_raw_preview_garbage_bytes_raise(tmp_path: Path) -> None:
    path = tmp_path / "frame.dng"
    path.write_bytes(b"not-a-real-raw")
    try:
        extract_raw_preview_image(path)
    except ValueError as error:
        assert str(error) == RAW_NO_PREVIEW_REASON
    else:
        raise AssertionError("expected no-preview error")


def test_open_raw_import_image_demosaics_without_preview(tmp_path: Path, monkeypatch) -> None:
    called = _track_rawpy_calls(monkeypatch)
    payload = tiny_dng_without_preview_bytes()
    path = tmp_path / "frame.dng"
    path.write_bytes(payload)
    opened = open_raw_import_image(path)
    image = ImageOps.exif_transpose(opened).convert("RGB")
    assert called == ["extract_thumb", "postprocess"]
    assert image.mode == "RGB"
    assert image.size == (TINY_DNG_CFA_SIZE[0] // 2, TINY_DNG_CFA_SIZE[1] // 2)
    assert path.read_bytes() == payload


def test_open_raw_import_image_preview_dng_does_not_call_postprocess(tmp_path: Path, monkeypatch) -> None:
    called = _track_rawpy_calls(monkeypatch)
    path = tmp_path / "frame.dng"
    path.write_bytes(tiny_dng_bytes())
    image = open_raw_import_image(path)
    assert called == ["extract_thumb"]
    assert image.size == TINY_DNG_PREVIEW_SIZE


def test_open_raw_import_image_garbage_bytes_raise_develop_failed(tmp_path: Path) -> None:
    path = tmp_path / "frame.dng"
    path.write_bytes(b"not-a-real-raw")
    try:
        open_raw_import_image(path)
    except ValueError as error:
        assert str(error) == RAW_DEVELOP_FAILED_REASON
    else:
        raise AssertionError("expected develop-failed error")


def test_unsupported_image_reason_for_raw_stays_no_preview_message() -> None:
    assert unsupported_image_reason("frame.dng") == RAW_NO_PREVIEW_REASON
    assert unsupported_image_reason("frame.dng") != RAW_DEVELOP_FAILED_REASON
