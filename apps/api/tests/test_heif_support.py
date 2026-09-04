from io import BytesIO

from PIL import Image

from app.image.heif_support import ensure_heif_opener
from app.main import create_app
from app.services.importing import SUPPORTED_EXTENSIONS
from tests.heic_helpers import tiny_heic_bytes


def test_ensure_heif_opener_is_idempotent() -> None:
    ensure_heif_opener()
    ensure_heif_opener()


def test_tiny_heic_opens_as_rgb_after_opener_registration() -> None:
    payload = tiny_heic_bytes(size=(8, 6), color=(12, 34, 56))
    ensure_heif_opener()
    with Image.open(BytesIO(payload)) as opened:
        rgb = opened.convert("RGB")
    assert rgb.size == (8, 6)
    assert rgb.mode == "RGB"


def test_create_app_registers_heif_opener() -> None:
    create_app()
    assert Image.registered_extensions().get(".heic") == "HEIF"
    assert Image.registered_extensions().get(".heif") == "HEIF"


def test_supported_extensions_include_heic_not_avif() -> None:
    assert {".heic", ".heif"}.issubset(SUPPORTED_EXTENSIONS)
    assert ".avif" not in SUPPORTED_EXTENSIONS


def test_heif_opener_does_not_claim_avif() -> None:
    ensure_heif_opener()
    assert Image.registered_extensions().get(".avif") != "HEIF"
