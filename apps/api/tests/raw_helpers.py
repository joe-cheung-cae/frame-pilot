from __future__ import annotations

import struct
from io import BytesIO

from PIL import Image

TYPE_BYTE = 1
TYPE_ASCII = 2
TYPE_SHORT = 3
TYPE_LONG = 4
TYPE_RATIONAL = 5
TYPE_SRATIONAL = 10

TINY_DNG_PREVIEW_SIZE = (16, 12)
TINY_DNG_CFA_SIZE = (32, 24)
TINY_DNG_DATETIME = "2026:01:02 03:04:05"
TINY_DNG_CAMERA_MODEL = "FramePilotCam"


def _encode_value(kind: int, values: object) -> bytes:
    if kind == TYPE_BYTE:
        return bytes(values)  # type: ignore[arg-type]
    if kind == TYPE_ASCII:
        raw = values if isinstance(values, bytes) else str(values).encode("ascii")
        if not raw.endswith(b"\x00"):
            raw += b"\x00"
        return raw
    if kind == TYPE_SHORT:
        return b"".join(struct.pack("<H", int(value)) for value in values)  # type: ignore[union-attr]
    if kind == TYPE_LONG:
        return b"".join(struct.pack("<I", int(value)) for value in values)  # type: ignore[union-attr]
    if kind == TYPE_RATIONAL:
        return b"".join(struct.pack("<II", int(num), int(den)) for num, den in values)  # type: ignore[misc]
    if kind == TYPE_SRATIONAL:
        return b"".join(struct.pack("<ii", int(num), int(den)) for num, den in values)  # type: ignore[misc]
    raise ValueError(f"Unsupported TIFF type {kind}")


def _build_ifd(entries: list[tuple[int, int, object]], data_base: int) -> tuple[bytes, bytes]:
    ordered = sorted(entries, key=lambda item: item[0])
    extras = bytearray()
    encoded: list[tuple[int, int, int, bytes]] = []
    extra_off = data_base + 2 + 12 * len(ordered) + 4
    for tag, kind, values in ordered:
        payload = _encode_value(kind, values)
        count = len(payload) if kind in {TYPE_BYTE, TYPE_ASCII} else len(values)  # type: ignore[arg-type]
        if len(payload) <= 4:
            encoded.append((tag, kind, count, payload + b"\x00" * (4 - len(payload))))
            continue
        encoded.append((tag, kind, count, struct.pack("<I", extra_off + len(extras))))
        extras.extend(payload)
        if len(extras) % 2:
            extras.append(0)

    body = bytearray()
    body.extend(struct.pack("<H", len(encoded)))
    for tag, kind, count, value4 in encoded:
        body.extend(struct.pack("<HHI", tag, kind, count))
        body.extend(value4)
    body.extend(struct.pack("<I", 0))
    return bytes(body), bytes(extras)


def _jpeg_preview(
    size: tuple[int, int],
    color: tuple[int, int, int],
) -> bytes:
    image = Image.new("RGB", size, color)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def tiny_dng_bytes(
    *,
    size: tuple[int, int] = TINY_DNG_PREVIEW_SIZE,
    color: tuple[int, int, int] = (12, 34, 56),
    include_preview: bool = True,
) -> bytes:
    """Build a tiny DNG in-process (CFA + optional JPEG preview). No camera files."""
    jpeg = _jpeg_preview(size, color) if include_preview else b""
    cfa_w, cfa_h = TINY_DNG_CFA_SIZE
    cfa = bytearray()
    for y in range(cfa_h):
        for x in range(cfa_w):
            cfa.extend(struct.pack("<H", 2000 + (x * 17 + y * 31) % 2000))
    cfa_bytes = bytes(cfa)
    preview_w, preview_h = size
    color_matrix = [
        (98, 100),
        (1, 100),
        (0, 1),
        (0, 1),
        (100, 100),
        (0, 1),
        (0, 1),
        (0, 1),
        (100, 100),
    ]

    header_size = 8
    cfa_off = 0
    jpeg_off = 0
    preview_ifd_off = 0
    ifd0 = extras0 = preview_ifd = extras1 = b""
    for _ in range(8):
        ifd0_entries: list[tuple[int, int, object]] = [
            (254, TYPE_LONG, [0]),
            (256, TYPE_LONG, [cfa_w]),
            (257, TYPE_LONG, [cfa_h]),
            (258, TYPE_SHORT, [16]),
            (259, TYPE_SHORT, [1]),
            (262, TYPE_SHORT, [32803]),
            (271, TYPE_ASCII, "FramePilot"),
            (272, TYPE_ASCII, TINY_DNG_CAMERA_MODEL),
            (273, TYPE_LONG, [cfa_off]),
            (274, TYPE_SHORT, [1]),
            (277, TYPE_SHORT, [1]),
            (278, TYPE_LONG, [cfa_h]),
            (279, TYPE_LONG, [len(cfa_bytes)]),
            (284, TYPE_SHORT, [1]),
            (306, TYPE_ASCII, TINY_DNG_DATETIME),
            (33421, TYPE_SHORT, [2, 2]),
            (33422, TYPE_BYTE, [0, 1, 1, 2]),
            (50706, TYPE_BYTE, [1, 4, 0, 0]),
            (50707, TYPE_BYTE, [1, 3, 0, 0]),
            (50708, TYPE_ASCII, "FramePilot TestCam"),
            (50721, TYPE_SRATIONAL, color_matrix),
            (50728, TYPE_RATIONAL, [(1, 1), (1, 1), (1, 1)]),
            (50778, TYPE_SHORT, [21]),
        ]
        if include_preview:
            ifd0_entries.append((330, TYPE_LONG, [preview_ifd_off]))
        ifd0, extras0 = _build_ifd(ifd0_entries, header_size)
        preview_ifd = b""
        extras1 = b""
        if include_preview:
            preview_entries: list[tuple[int, int, object]] = [
                (254, TYPE_LONG, [1]),
                (256, TYPE_LONG, [preview_w]),
                (257, TYPE_LONG, [preview_h]),
                (258, TYPE_SHORT, [8, 8, 8]),
                (259, TYPE_SHORT, [7]),
                (262, TYPE_SHORT, [2]),
                (273, TYPE_LONG, [jpeg_off]),
                (277, TYPE_SHORT, [3]),
                (278, TYPE_LONG, [preview_h]),
                (279, TYPE_LONG, [len(jpeg)]),
                (284, TYPE_SHORT, [1]),
            ]
            preview_ifd, extras1 = _build_ifd(preview_entries, preview_ifd_off)
        next_cfa_off = header_size + len(ifd0) + len(extras0)
        next_preview_ifd_off = next_cfa_off + len(cfa_bytes)
        next_jpeg_off = next_preview_ifd_off + len(preview_ifd) + len(extras1)
        if (cfa_off, jpeg_off, preview_ifd_off) == (next_cfa_off, next_jpeg_off, next_preview_ifd_off):
            break
        cfa_off, jpeg_off, preview_ifd_off = next_cfa_off, next_jpeg_off, next_preview_ifd_off
    else:
        raise RuntimeError("tiny DNG offsets did not stabilize")

    blob = bytearray()
    blob.extend(b"II")
    blob.extend(struct.pack("<HI", 42, header_size))
    blob.extend(ifd0)
    blob.extend(extras0)
    blob.extend(cfa_bytes)
    if include_preview:
        blob.extend(preview_ifd)
        blob.extend(extras1)
        blob.extend(jpeg)
    return bytes(blob)


def tiny_dng_without_preview_bytes(
    *,
    color: tuple[int, int, int] = (12, 34, 56),
) -> bytes:
    return tiny_dng_bytes(color=color, include_preview=False)
