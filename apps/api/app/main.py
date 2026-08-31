import threading
import uuid
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
from app.services.importing import prepare_interrupted_import_jobs_for_reclaim, run_import_derivative_job
from app.services.jobs import reconcile_active_jobs_on_startup
from app.services.processing import prepare_interrupted_processing_jobs_for_reclaim, run_processing_job

_db_ready = False


def reset_db_ready_flag() -> None:
    global _db_ready
    _db_ready = False


def _schedule_import_reclaim(targets: list[tuple[str, list[str]]], *, worker_id: str) -> None:
    for job_id, photo_ids in targets:
        thread = threading.Thread(
            target=run_import_derivative_job,
            args=(job_id, photo_ids, []),
            kwargs={"worker_id": worker_id},
            daemon=True,
            name=f"framepilot-reclaim-import-{job_id[:8]}",
        )
        thread.start()


def _schedule_processing_reclaim(job_ids: list[str], *, worker_id: str) -> None:
    for job_id in job_ids:
        thread = threading.Thread(
            target=run_processing_job,
            args=(job_id,),
            kwargs={"worker_id": worker_id},
            daemon=True,
            name=f"framepilot-reclaim-process-{job_id[:8]}",
        )
        thread.start()


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


def start_reclaimable_import_jobs() -> list[tuple[str, list[str]]]:
    """Backward-compatible alias for import-only reclaim scheduling."""
    result = start_reclaimable_jobs()
    return result["import"]


def start_reclaimable_jobs() -> dict[str, list]:
    """Prepare and schedule interrupted import/processing reclaim (Phase 6 / J6.03–J6.04).

    Prefers import reclaim in the same startup pass so derivative work finishes before
    grouping rebuild. Only one processing reclaim job is prepared when no import reclaim
    targets exist.

    A worker id is generated once per lifespan reclaim pass and threaded through the
    atomic ``prepare_interrupted_*_for_reclaim`` claim and into the scheduled ``run_*``
    call for the same job, so a job claimed here cannot also be picked up and re-executed
    by a concurrently running ``python -m app.worker`` process (#104 fix 2).
    """
    if not get_settings().job_reclaim_on_startup:
        return {"import": [], "processing": []}
    owner = f"api-reclaim-{uuid.uuid4().hex[:12]}"
    with Session(get_engine()) as session:
        import_targets = prepare_interrupted_import_jobs_for_reclaim(session, worker_id=owner)
        processing_ids: list[str] = []
        if not import_targets:
            processing_ids = prepare_interrupted_processing_jobs_for_reclaim(session, worker_id=owner)
    if import_targets:
        _schedule_import_reclaim(import_targets, worker_id=owner)
    if processing_ids:
        _schedule_processing_reclaim(processing_ids, worker_id=owner)
    return {"import": import_targets, "processing": processing_ids}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_db_ready()
    start_reclaimable_jobs()
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
