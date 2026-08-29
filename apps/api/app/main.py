from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.meta import router as meta_router
from app.api.routes import router
from app.core.config import get_settings, reset_settings_cache
from app.core.origins import allowed_origins, host_is_allowed
from app.core.version import APP_VERSION, health_payload
from app.db.session import get_engine, init_db
from app.services.jobs import reconcile_active_jobs_on_startup

_db_ready = False


def reset_db_ready_flag() -> None:
    global _db_ready
    _db_ready = False


def ensure_db_ready() -> None:
    """Initialize schema and reconcile leftover active jobs once per process/settings reset."""
    global _db_ready
    if _db_ready:
        return
    init_db()
    with Session(get_engine()) as session:
        reclaim = get_settings().job_reclaim_on_startup
        reconcile_active_jobs_on_startup(session, reclaim=reclaim)
    _db_ready = True


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_db_ready()
    yield


def create_app() -> FastAPI:
    reset_settings_cache()
    reset_db_ready_flag()
    origins = allowed_origins()
    app = FastAPI(title="FramePilot API", version=APP_VERSION, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def require_local_origin(request: Request, call_next):
        if not host_is_allowed(request.headers.get("host")):
            return JSONResponse(
                status_code=403,
                content={"detail": "Host not allowed for local FramePilot API"},
            )
        if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin and origin not in origins:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Origin not allowed for local FramePilot API"},
                )
        return await call_next(request)

    @app.get("/health")
    def health() -> dict[str, str]:
        return health_payload()

    app.include_router(meta_router)
    app.include_router(router)
    ensure_db_ready()
    return app


app = create_app()
