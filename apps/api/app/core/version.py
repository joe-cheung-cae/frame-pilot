APP_VERSION = "2.0.0-rc2"
SERVICE_NAME = "framepilot-api"


def health_payload() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION, "service": SERVICE_NAME}
