from fastapi import APIRouter

from app.core.config import get_settings
from app.core.origins import desktop_mode_enabled
from app.core.version import meta_payload

router = APIRouter()


@router.get("/api/meta")
def api_meta_endpoint() -> dict[str, str | bool]:
    return meta_payload(data_dir=str(get_settings().data_dir), desktop_mode=desktop_mode_enabled())
