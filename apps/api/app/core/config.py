import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.local_paths import normalize_user_path


class Settings(BaseModel):
    data_dir: Path
    project_root_allowlist: list[Path] = Field(default_factory=list)

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'framepilot.db'}"


@lru_cache
def get_settings() -> Settings:
    data_dir = Path(os.getenv("FRAMEPILOT_DATA_DIR", ".framepilot-data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    allowlist_raw = os.getenv("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST", "")
    allowlist: list[Path] = []
    for item in allowlist_raw.split(os.pathsep):
        stripped = item.strip()
        if not stripped:
            continue
        try:
            cleaned = normalize_user_path(stripped)
        except ValueError:
            continue
        allowlist.append(Path(cleaned).expanduser().resolve())
    return Settings(data_dir=data_dir, project_root_allowlist=allowlist)


def reset_settings_cache() -> None:
    get_settings.cache_clear()
    # Import lazily to avoid a circular import with app.db.session.
    from app.db.session import reset_engine_cache

    reset_engine_cache()
    try:
        from app.main import reset_db_ready_flag

        reset_db_ready_flag()
    except ImportError:
        # app.main may not be importable yet during early bootstrap.
        pass
