from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.api.routes import router
from app.core.config import reset_settings_cache
from app.db.session import get_engine, init_db
from app.services.jobs import fail_active_jobs_on_startup

_db_ready = False


def reset_db_ready_flag() -> None:
    global _db_ready
    _db_ready = False


def ensure_db_ready() -> None:
    """Initialize schema and fail leftover active jobs once per process/settings reset."""
    global _db_ready
    if _db_ready:
        return
    init_db()
    with Session(get_engine()) as session:
        fail_active_jobs_on_startup(session)
    _db_ready = True


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_db_ready()
    yield


def create_app() -> FastAPI:
    reset_settings_cache()
    reset_db_ready_flag()
    app = FastAPI(title="FramePilot API", version="2.0.0-rc2", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3100",
            "http://127.0.0.1:3100",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    ensure_db_ready()
    return app


app = create_app()
