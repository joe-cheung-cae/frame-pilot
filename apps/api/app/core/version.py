APP_VERSION = "2.0.0-rc2"
SERVICE_NAME = "framepilot-api"


def health_payload() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION, "service": SERVICE_NAME}


def meta_payload(*, data_dir: str, desktop_mode: bool) -> dict[str, str | bool]:
    return {
        "version": APP_VERSION,
        "service": SERVICE_NAME,
        "data_dir": data_dir,
        "desktop_mode": desktop_mode,
    }
