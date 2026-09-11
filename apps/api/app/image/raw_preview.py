"""Open RAW files: thumb-only helper plus import fallback demosaic."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import rawpy
from PIL import Image

RAW_NO_PREVIEW_REASON = "RAW file has no embedded preview; FramePilot does not demosaic"
RAW_DEVELOP_FAILED_REASON = "RAW file could not be developed; no embedded preview and demosaic failed"

_THUMB_ERRORS = (
    rawpy.LibRawNoThumbnailError,
    rawpy.LibRawUnsupportedThumbnailError,
    rawpy.LibRawError,
    OSError,
)


class RawPreviewError(ValueError):
    """Raised when a RAW file has no extractable embedded preview."""


def _image_from_thumb(thumb: object) -> Image.Image | None:
    if thumb.format == rawpy.ThumbFormat.JPEG:
        image = Image.open(BytesIO(thumb.data))
        image.load()
        return image
    if thumb.format == rawpy.ThumbFormat.BITMAP:
        data = thumb.data
        return Image.fromarray(data.copy() if hasattr(data, "copy") else data)
    return None


def extract_raw_preview_image(path: Path | str) -> Image.Image:
    """Return the embedded JPEG/bitmap preview. Never calls postprocess or demosaic."""
    try:
        with rawpy.imread(str(path)) as raw:
            thumb = raw.extract_thumb()
    except _THUMB_ERRORS as error:
        raise RawPreviewError(RAW_NO_PREVIEW_REASON) from error

    image = _image_from_thumb(thumb)
    if image is None:
        raise RawPreviewError(RAW_NO_PREVIEW_REASON)
    return image


def open_raw_import_image(path: Path | str) -> Image.Image:
    """Return embedded preview RGB, or demosaic when extract_thumb fails.

    Uses one rawpy handle. postprocess only after thumb failure, with locked kwargs.
    """
    try:
        with rawpy.imread(str(path)) as raw:
            try:
                thumb = raw.extract_thumb()
            except _THUMB_ERRORS:
                thumb = None
            if thumb is not None:
                image = _image_from_thumb(thumb)
                if image is not None:
                    return image
            rgb = raw.postprocess(
                use_camera_wb=True,
                no_auto_bright=True,
                output_bps=8,
                half_size=True,
            )
            return Image.fromarray(rgb.copy())
    except RawPreviewError:
        raise
    except (rawpy.LibRawError, OSError, ValueError) as error:
        raise RawPreviewError(RAW_DEVELOP_FAILED_REASON) from error
