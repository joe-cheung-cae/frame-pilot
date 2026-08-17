import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    data_dir: Path

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'framepilot.db'}"


@lru_cache
def get_settings() -> Settings:
    data_dir = Path(os.getenv("FRAMEPILOT_DATA_DIR", ".framepilot-data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(data_dir=data_dir)


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
