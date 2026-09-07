from io import BytesIO

from PIL import AvifImagePlugin, Image

from app.image.heif_support import ensure_heif_opener
from app.main import create_app
from app.services.exporting import STORED_IMAGE_EXTENSIONS
from app.services.importing import SUPPORTED_EXTENSIONS
from tests.avif_helpers import tiny_avif_bytes
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


def test_supported_extensions_include_heic_and_avif() -> None:
    assert {".heic", ".heif", ".avif"}.issubset(SUPPORTED_EXTENSIONS)
    assert ".avifs" not in SUPPORTED_EXTENSIONS
    assert ".avif" in STORED_IMAGE_EXTENSIONS
    assert ".avifs" not in STORED_IMAGE_EXTENSIONS


def test_pillow_avif_plugin_is_available() -> None:
    assert AvifImagePlugin.SUPPORTED
    assert Image.registered_extensions().get(".avif") == "AVIF"


def test_tiny_avif_opens_as_rgb() -> None:
    payload = tiny_avif_bytes(size=(8, 6), color=(12, 34, 56))
    with Image.open(BytesIO(payload)) as opened:
        assert opened.format == "AVIF"
        rgb = opened.convert("RGB")
    assert rgb.size == (8, 6)
    assert rgb.mode == "RGB"


def test_heif_opener_does_not_claim_avif() -> None:
    ensure_heif_opener()
    assert Image.registered_extensions().get(".avif") == "AVIF"
    assert Image.registered_extensions().get(".avif") != "HEIF"
