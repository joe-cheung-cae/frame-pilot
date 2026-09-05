from io import BytesIO

from PIL import Image


def tiny_avif_bytes(
    *,
    size: tuple[int, int] = (8, 6),
    color: tuple[int, int, int] = (12, 34, 56),
    exif: Image.Exif | None = None,
) -> bytes:
    image = Image.new("RGB", size, color)
    buffer = BytesIO()
    save_kwargs: dict[str, object] = {"format": "AVIF"}
    if exif is not None:
        save_kwargs["exif"] = exif
    image.save(buffer, **save_kwargs)
    return buffer.getvalue()
