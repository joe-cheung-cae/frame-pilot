import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.local_paths import normalize_user_path


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    data_dir: Path
    project_root_allowlist: list[Path] = Field(default_factory=list)
    # Phase 6 / J6.02: when true, leftover active jobs become status=interrupted for reclaim.
    # Default false preserves fail-and-retry startup behavior.
    job_reclaim_on_startup: bool = False

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
    return Settings(
        data_dir=data_dir,
        project_root_allowlist=allowlist,
        job_reclaim_on_startup=env_flag("FRAMEPILOT_JOB_RECLAIM_ON_STARTUP"),
    )


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
