"""Extract LibRaw embedded previews from RAW files. No demosaic."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import rawpy
from PIL import Image

RAW_NO_PREVIEW_REASON = "RAW file has no embedded preview; FramePilot does not demosaic"


class RawPreviewError(ValueError):
    """Raised when a RAW file has no extractable embedded preview."""


def extract_raw_preview_image(path: Path | str) -> Image.Image:
    """Return the embedded JPEG/bitmap preview. Never calls postprocess or demosaic."""
    try:
        with rawpy.imread(str(path)) as raw:
            thumb = raw.extract_thumb()
    except (
        rawpy.LibRawNoThumbnailError,
        rawpy.LibRawUnsupportedThumbnailError,
        rawpy.LibRawError,
        OSError,
    ) as error:
        raise RawPreviewError(RAW_NO_PREVIEW_REASON) from error

    if thumb.format == rawpy.ThumbFormat.JPEG:
        image = Image.open(BytesIO(thumb.data))
        image.load()
        return image
    if thumb.format == rawpy.ThumbFormat.BITMAP:
        return Image.fromarray(thumb.data)
    raise RawPreviewError(RAW_NO_PREVIEW_REASON)
