from io import BytesIO

from PIL import Image

from app.image.heif_support import ensure_heif_opener


def tiny_heic_bytes(
    *,
    size: tuple[int, int] = (8, 6),
    color: tuple[int, int, int] = (12, 34, 56),
    exif: Image.Exif | None = None,
) -> bytes:
    ensure_heif_opener()
    image = Image.new("RGB", size, color)
    buffer = BytesIO()
    save_kwargs: dict[str, object] = {"format": "HEIF"}
    if exif is not None:
        save_kwargs["exif"] = exif
    image.save(buffer, **save_kwargs)
    return buffer.getvalue()
