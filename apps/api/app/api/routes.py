import json
import os
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import case, func
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.origins import desktop_mode_enabled
from app.core.project_roots import register_root, registered_roots
from app.core.version import health_payload, meta_payload
from app.db.session import get_session
from app.models.entities import ExportRecord, Photo, PhotoGroup, ProcessingJob, Project, utc_now
from app.schemas.api import (
    DesktopProjectRootCreate,
    ExportCreate,
    ExportRead,
    GroupRead,
    ImportResult,
    JobRead,
    PathImportRequest,
    PhotoBatchUpdate,
    PhotoRead,
    PhotoStatusCountsRead,
    PhotoUpdate,
    ProjectCreate,
    ProjectRead,
)
from app.services.exporting import (
    EXPORT_CANCEL_REASON,
    ExportCancelled,
    copy_selected_files,
    fail_and_cleanup_export_record,
    finalize_cancelled_export_job,
    request_export_job_cancellation,
    sync_export_job,
    write_selection_csv,
    zip_selected_files,
)
from app.services.importing import (
    IMPORT_MAX_FILES_PER_REQUEST,
    ImportTimingCollector,
    complete_import_job,
    create_import_job,
    create_import_retry_job,
    expand_import_paths,
    import_timing_stage,
    invalidate_project_processing,
    photo_needs_import_retry,
    register_import_file,
    request_import_job_cancellation,
    run_import_derivative_job,
    update_import_job,
)
from app.services.jobs import (
    BLOCKING_JOB_STATUSES,
    STALE_JOB_AFTER,
    as_utc,
    fail_stale_job,
    fail_stale_jobs_for_project,
    job_is_stale,
)
from app.services.processing import (
    create_processing_job,
    project_export_root,
    request_processing_job_cancellation,
    run_processing_job,
)
from app.services.projects import create_project, list_projects

router = APIRouter(prefix="/api")


@router.get("/health")
def api_health_endpoint() -> dict[str, str]:
    return health_payload()


@router.get("/meta")
def api_meta_endpoint() -> dict[str, str | bool]:
    return meta_payload(data_dir=str(get_settings().data_dir), desktop_mode=desktop_mode_enabled())


def _get_project(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_photo(session: Session, project_id: str, photo_id: str) -> Photo:
    photo = session.get(Photo, photo_id)
    if photo is None or photo.project_id != project_id:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


def _export_target(export_root: Path, export_id: str, mode: str) -> Path:
    if mode == "csv":
        return export_root / "csv" / f"selection-{export_id}.csv"
    if mode == "folder":
        return export_root / "folders" / f"selected-{export_id}"
    return export_root / "zip" / f"selected-{export_id}.zip"


def _get_export(session: Session, project_id: str, export_id: str) -> ExportRecord:
    export = session.get(ExportRecord, export_id)
    if export is None or export.project_id != project_id:
        raise HTTPException(status_code=404, detail="Export not found")
    return export


def _get_active_processing_job(session: Session, project_id: str) -> ProcessingJob | None:
    # "interrupted" is treated as in-flight so a new process request cannot race a
    # pending reclaim of this project (#104 fix 5).
    return session.exec(
        select(ProcessingJob)
        .where(ProcessingJob.project_id == project_id)
        .where(ProcessingJob.job_type == "processing")
        .where(ProcessingJob.status.in_(list(BLOCKING_JOB_STATUSES)))
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
    ).first()


def _get_active_import_job(session: Session, project_id: str) -> ProcessingJob | None:
    # "interrupted" is treated as in-flight so a new import request cannot race a
    # pending reclaim of this project (#104 fix 5).
    return session.exec(
        select(ProcessingJob)
        .where(ProcessingJob.project_id == project_id)
        .where(ProcessingJob.job_type == "import")
        .where(ProcessingJob.status.in_(list(BLOCKING_JOB_STATUSES)))
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
    ).first()


def _get_current_active_import_job(session: Session, project_id: str) -> ProcessingJob | None:
    while active_job := _get_active_import_job(session, project_id):
        if job_is_stale(active_job):
            fail_stale_job(session, active_job)
            continue
        return active_job
    return None


def _job_read(job: ProcessingJob) -> JobRead:
    return JobRead(
        id=job.id,
        project_id=job.project_id,
        job_type=job.job_type,
        status=job.status,
        current_step=job.current_step,
        total_items=job.total_items,
        processed_items=job.processed_items,
        failed_items=job.failed_items,
        progress_percent=job.progress_percent,
        error_message=job.error_message,
        cancellation_requested=job.cancellation_requested,
        cancelled_at=job.cancelled_at,
        checkpoint_photo_id=job.checkpoint_photo_id,
        checkpoint_stage=job.checkpoint_stage,
        interrupted_at=job.interrupted_at,
        reclaim_count=job.reclaim_count,
        worker_id=job.worker_id,
        heartbeat_at=job.heartbeat_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        retryable=job.retryable,
    )


def _project_read(session: Session, project: Project, *, sweep_stale: bool = True) -> ProjectRead:
    if sweep_stale:
        _fail_stale_active_jobs(session, project.id)
        session.refresh(project)
    active_import_job = _get_current_active_import_job(session, project.id)
    return ProjectRead(
        id=project.id,
        name=project.name,
        root_path=project.root_path,
        source_mode=project.source_mode,
        source_root_path=project.source_root_path,
        created_at=project.created_at,
        updated_at=project.updated_at,
        total_images=project.total_images,
        processed_images=project.processed_images,
        last_processed_at=project.last_processed_at,
        schema_version=project.schema_version,
        active_import_job=_job_read(active_import_job) if active_import_job else None,
    )


def _fail_stale_active_jobs(session: Session, project_id: str) -> None:
    fail_stale_jobs_for_project(session, project_id)


def _ensure_fresh_job(session: Session, job: ProcessingJob) -> ProcessingJob:
    if job_is_stale(job):
        return fail_stale_job(session, job)
    return job


def _acquire_import_job(
    session: Session,
    project: Project,
    project_id: str,
    job_id: str | None,
    expected_total: int | None,
    request_file_count: int,
) -> ProcessingJob:
    if expected_total is not None and expected_total < request_file_count:
        raise HTTPException(status_code=422, detail="expected_total must be >= the number of files in this request")

    active_import_job = _get_current_active_import_job(session, project_id)
    if job_id:
        job = session.get(ProcessingJob, job_id)
        if job is None or job.project_id != project_id or job.job_type != "import":
            raise HTTPException(status_code=404, detail="Import job not found")
        if job_is_stale(job):
            job = fail_stale_job(session, job)
        if job.status not in {"queued", "running"}:
            raise HTTPException(status_code=409, detail="Import job is no longer accepting files")
        if active_import_job is not None and active_import_job.id != job.id:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Another import job is already running for this project",
                    "job_id": active_import_job.id,
                },
            )
    else:
        if active_import_job is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "An import job is already running for this project",
                    "job_id": active_import_job.id,
                },
            )
        job = create_import_job(session, project, expected_total or request_file_count)

    if expected_total is not None and expected_total > job.total_items:
        job.total_items = expected_total
        job.progress_percent = 0.0
        job.updated_at = utc_now()
        session.add(job)
        session.commit()
        session.refresh(job)
    return job


def _import_result_payload(
    *,
    imported: list[Photo],
    skipped: list[dict[str, str]],
    job: ProcessingJob,
    total_files: int,
    remaining_paths: list[str] | None = None,
    expanded_total: int | None = None,
    timing: ImportTimingCollector | None = None,
    started: float | None = None,
    batch_size: int | None = None,
) -> dict:
    response = {
        "imported": imported,
        "skipped": skipped,
        "job": job,
        "total_files": total_files,
        "accepted_files": len(imported),
        "skipped_files": len(skipped),
        "failed_files": len(skipped),
        "remaining_paths": remaining_paths or [],
        "expanded_total": expanded_total if expanded_total is not None else total_files,
    }
    if timing is not None and started is not None:
        total_seconds = round(time.perf_counter() - started, 6)
        timing.record("import_endpoint_total", total_seconds)
        response["timing"] = {
            "total_files": batch_size if batch_size is not None else total_files,
            "imported_files": len(imported),
            "skipped_files": len(skipped),
            "total_seconds": total_seconds,
            "stages": timing.summary(),
        }
    return response


def _require_desktop_mode() -> None:
    if not desktop_mode_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")


@router.get("/desktop/project-roots")
def list_desktop_project_roots() -> dict[str, list[str]]:
    _require_desktop_mode()
    return {"roots": [str(path) for path in registered_roots()]}


@router.post("/desktop/project-roots", status_code=status.HTTP_201_CREATED)
def register_desktop_project_root(payload: DesktopProjectRootCreate) -> dict[str, str]:
    _require_desktop_mode()
    try:
        root = register_root(payload.path)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"path": str(root)}


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(payload: ProjectCreate, session: Session = Depends(get_session)):
    try:
        return create_project(
            session,
            payload.name,
            payload.root_path,
            acknowledge_nonempty=payload.acknowledge_nonempty,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/projects", response_model=list[ProjectRead])
def list_projects_endpoint(session: Session = Depends(get_session)):
    """List projects with a read-only query path (no stale-job failure writes).

    Stale queued/running jobs are omitted from ``active_import_job`` here and are
    failed promptly by project detail, jobs endpoints, mutations, and API startup.
    """
    projects = list_projects(session)
    if not projects:
        return []

    project_ids = [project.id for project in projects]
    active_import_by_project: dict[str, ProcessingJob] = {}
    for job in session.exec(
        select(ProcessingJob)
        .where(ProcessingJob.project_id.in_(project_ids))
        .where(ProcessingJob.job_type == "import")
        .where(ProcessingJob.status.in_(list(BLOCKING_JOB_STATUSES)))
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
    ).all():
        # Read-only list path: skip stale jobs for display without writing.
        if job_is_stale(job):
            continue
        active_import_by_project.setdefault(job.project_id, job)

    return [
        ProjectRead(
            id=project.id,
            name=project.name,
            root_path=project.root_path,
            source_mode=project.source_mode,
            source_root_path=project.source_root_path,
            created_at=project.created_at,
            updated_at=project.updated_at,
            total_images=project.total_images,
            processed_images=project.processed_images,
            last_processed_at=project.last_processed_at,
            schema_version=project.schema_version,
            active_import_job=(
                _job_read(active_import_by_project[project.id]) if project.id in active_import_by_project else None
            ),
        )
        for project in projects
    ]


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project_endpoint(project_id: str, session: Session = Depends(get_session)):
    return _project_read(session, _get_project(session, project_id))


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(project_id: str, session: Session = Depends(get_session)):
    project = _get_project(session, project_id)
    for export in session.exec(select(ExportRecord).where(ExportRecord.project_id == project_id)).all():
        session.delete(export)
    for job in session.exec(select(ProcessingJob).where(ProcessingJob.project_id == project_id)).all():
        session.delete(job)
    photos = list(session.exec(select(Photo).where(Photo.project_id == project_id)).all())
    for photo in photos:
        photo.group_id = None
        session.add(photo)
    session.flush()
    for group in session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project_id)).all():
        group.representative_photo_id = None
        session.add(group)
    session.flush()
    for group in session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project_id)).all():
        session.delete(group)
    for photo in photos:
        session.delete(photo)
    session.delete(project)
    session.commit()
    return None


@router.post(
    "/projects/{project_id}/imports",
    response_model=ImportResult,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/projects/{project_id}/import",
    response_model=ImportResult,
    status_code=status.HTTP_201_CREATED,
)
def import_photos_endpoint(
    project_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    job_id: str | None = Form(default=None),
    expected_total: int | None = Form(default=None),
    finalize: bool = Form(default=True),
    include_timing: bool = Query(default=False),
    session: Session = Depends(get_session),
):
    timing_enabled = include_timing or os.environ.get("FRAMEPILOT_IMPORT_TIMING") == "1"
    timing = ImportTimingCollector() if timing_enabled else None
    started = time.perf_counter()
    project = _get_project(session, project_id)

    if not files:
        raise HTTPException(status_code=422, detail="At least one file is required")
    if len(files) > IMPORT_MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Too many files in one request ({len(files)}). "
                f"Upload at most {IMPORT_MAX_FILES_PER_REQUEST} files per request and append with job_id."
            ),
        )

    job = _acquire_import_job(session, project, project_id, job_id, expected_total, len(files))
    batch_size = len(files)
    imported: list[Photo] = []
    derivative_photo_ids: list[str] = []
    newly_imported_ids: list[str] = []
    skipped: list[dict[str, str]] = []
    new_import_count = 0
    failed_count = job.failed_items
    registered_before = 0 if job.current_step.startswith("derivative_generation") else max(0, job.processed_items)

    for index, upload in enumerate(files, start=1):
        filename = upload.filename or "image"
        absolute_index = registered_before + index

        def update_stage(
            stage: str,
            current_index: int = absolute_index,
            current_failed_count: int = failed_count,
        ) -> None:
            update_import_job(
                session,
                job,
                f"{stage} {current_index} of {job.total_items or batch_size}",
                registered_before,
                current_failed_count,
            )

        try:
            before_total = project.total_images
            registration = register_import_file(
                session,
                project,
                filename,
                upload.file,
                timing=timing,
                progress_callback=update_stage,
            )
            photo = registration.photo
            imported.append(photo)
            if registration.requires_derivatives:
                derivative_photo_ids.append(photo.id)
            if registration.is_new and project.total_images > before_total:
                new_import_count += 1
                newly_imported_ids.append(photo.id)
            update_import_job(
                session,
                job,
                f"file_copy_or_register {absolute_index} of {job.total_items or batch_size}",
                registered_before + len(imported),
                failed_count,
                force=True,
            )
        except ValueError as error:
            skipped.append({"filename": filename, "reason": str(error)})
            failed_count += 1
            update_import_job(
                session,
                job,
                f"file_skipped {absolute_index} of {job.total_items or batch_size}",
                registered_before + len(imported),
                failed_count,
                force=True,
            )

    registered_count = registered_before + len(imported)
    update_import_job(
        session,
        job,
        f"receive_files {registered_count} of {job.total_items or registered_count}",
        registered_count,
        failed_count,
        force=True,
    )

    if not imported and skipped and finalize and registered_before == 0:
        complete_import_job(session, job, 0, skipped)
        details = "; ".join(f"{item['filename']}: {item['reason']}" for item in skipped)
        raise HTTPException(status_code=422, detail=details)

    if new_import_count:
        update_import_job(
            session,
            job,
            "processing_invalidation",
            registered_count,
            failed_count,
            force=True,
        )
        with import_timing_stage(timing, "processing_invalidation"):
            invalidate_project_processing(session, project, touched_photo_ids=newly_imported_ids)
        with import_timing_stage(timing, "import_endpoint_commit"):
            session.commit()
        if not finalize:
            update_import_job(
                session,
                job,
                f"receive_files {registered_count} of {job.total_items or registered_count}",
                registered_count,
                failed_count,
                force=True,
            )

    if not finalize:
        return _import_result_payload(
            imported=imported,
            skipped=skipped,
            job=job,
            total_files=batch_size,
            remaining_paths=[],
            expanded_total=batch_size,
            timing=timing,
            started=started,
            batch_size=batch_size,
        )

    pending_derivative_ids = [
        photo.id
        for photo in session.exec(
            select(Photo)
            .where(Photo.project_id == project_id)
            .where(Photo.processing_state == "processing")
            .order_by(Photo.created_at, Photo.id)
        ).all()
    ]
    if pending_derivative_ids:
        update_import_job(session, job, "derivative_generation", 0, failed_count, force=True)
        background_tasks.add_task(run_import_derivative_job, job.id, pending_derivative_ids, skipped)
    else:
        job = complete_import_job(session, job, registered_count, skipped)

    return _import_result_payload(
        imported=imported,
        skipped=skipped,
        job=job,
        total_files=batch_size,
        remaining_paths=[],
        expanded_total=batch_size,
        timing=timing,
        started=started,
        batch_size=batch_size,
    )


@router.post(
    "/projects/{project_id}/imports/from-paths",
    response_model=ImportResult,
    status_code=status.HTTP_201_CREATED,
)
def import_photos_from_paths_endpoint(
    project_id: str,
    payload: PathImportRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    project = _get_project(session, project_id)
    # Empty paths are a finalize-only follow-up; they must name an in-flight job.
    if not payload.paths:
        if not payload.finalize or not payload.job_id:
            raise HTTPException(status_code=422, detail="At least one path is required")
        files: list[Path] = []
        skipped: list[dict[str, str]] = []
    else:
        try:
            expanded = expand_import_paths(payload.paths, Path(project.root_path))
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        files = expanded.files
        skipped = list(expanded.skipped)

    consume = files[:IMPORT_MAX_FILES_PER_REQUEST]
    remaining_paths = [str(path) for path in files[IMPORT_MAX_FILES_PER_REQUEST:]]
    expanded_total = len(files)
    planned_total = payload.expected_total if payload.expected_total is not None else expanded_total

    job = _acquire_import_job(session, project, project_id, payload.job_id, planned_total, len(consume))
    if not payload.paths and payload.expected_total is None:
        planned_total = job.total_items
    batch_size = len(consume)
    imported: list[Photo] = []
    newly_imported_ids: list[str] = []
    new_import_count = 0
    failed_count = job.failed_items + len(skipped)
    registered_before = 0 if job.current_step.startswith("derivative_generation") else max(0, job.processed_items)

    for index, source in enumerate(consume, start=1):
        filename = source.name
        absolute_index = registered_before + index

        def update_stage(
            stage: str,
            current_index: int = absolute_index,
            current_failed_count: int = failed_count,
        ) -> None:
            update_import_job(
                session,
                job,
                f"{stage} {current_index} of {job.total_items or batch_size}",
                registered_before,
                current_failed_count,
            )

        try:
            before_total = project.total_images
            with source.open("rb") as handle:
                registration = register_import_file(
                    session,
                    project,
                    filename,
                    handle,
                    progress_callback=update_stage,
                )
            photo = registration.photo
            imported.append(photo)
            if registration.is_new and project.total_images > before_total:
                new_import_count += 1
                newly_imported_ids.append(photo.id)
            update_import_job(
                session,
                job,
                f"file_copy_or_register {absolute_index} of {job.total_items or batch_size}",
                registered_before + len(imported),
                failed_count,
                force=True,
            )
        except ValueError as error:
            skipped.append({"filename": filename, "reason": str(error)})
            failed_count += 1
            update_import_job(
                session,
                job,
                f"file_skipped {absolute_index} of {job.total_items or batch_size}",
                registered_before + len(imported),
                failed_count,
                force=True,
            )

    registered_count = registered_before + len(imported)
    update_import_job(
        session,
        job,
        f"receive_files {registered_count} of {job.total_items or registered_count}",
        registered_count,
        failed_count,
        force=True,
    )

    if not imported and skipped and payload.finalize and registered_before == 0:
        complete_import_job(session, job, 0, skipped)
        details = "; ".join(f"{item['filename']}: {item['reason']}" for item in skipped)
        raise HTTPException(status_code=422, detail=details)

    if new_import_count:
        update_import_job(
            session,
            job,
            "processing_invalidation",
            registered_count,
            failed_count,
            force=True,
        )
        invalidate_project_processing(session, project, touched_photo_ids=newly_imported_ids)
        session.commit()
        if not payload.finalize:
            update_import_job(
                session,
                job,
                f"receive_files {registered_count} of {job.total_items or registered_count}",
                registered_count,
                failed_count,
                force=True,
            )

    if len(payload.paths) == 1 and not project.source_root_path:
        single_input = Path(payload.paths[0])
        if single_input.is_dir():
            project.source_root_path = str(single_input.resolve())
            session.add(project)
            session.commit()

    if not payload.finalize:
        return _import_result_payload(
            imported=imported,
            skipped=skipped,
            job=job,
            total_files=batch_size,
            remaining_paths=remaining_paths,
            expanded_total=planned_total,
        )

    pending_derivative_ids = [
        photo.id
        for photo in session.exec(
            select(Photo)
            .where(Photo.project_id == project_id)
            .where(Photo.processing_state == "processing")
            .order_by(Photo.created_at, Photo.id)
        ).all()
    ]
    if pending_derivative_ids:
        update_import_job(session, job, "derivative_generation", 0, failed_count, force=True)
        background_tasks.add_task(run_import_derivative_job, job.id, pending_derivative_ids, skipped)
    else:
        job = complete_import_job(session, job, registered_count, skipped)

    return _import_result_payload(
        imported=imported,
        skipped=skipped,
        job=job,
        total_files=batch_size,
        remaining_paths=remaining_paths,
        expanded_total=planned_total,
    )


@router.post("/projects/{project_id}/process", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def process_project_endpoint(
    project_id: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    project = _get_project(session, project_id)
    active_import_job = _get_current_active_import_job(session, project_id)
    if active_import_job is not None:
        message = "Import is still running for this project. Wait for the import job to finish before processing."
        raise HTTPException(
            status_code=409,
            detail={
                "message": message,
                "job_id": active_import_job.id,
            },
        )
    if project.total_images <= 0:
        raise HTTPException(status_code=422, detail="Import photos before processing this project")
    active_job = _get_active_processing_job(session, project_id)
    if active_job is not None:
        if job_is_stale(active_job):
            fail_stale_job(session, active_job)
        else:
            return active_job
    job = create_processing_job(session, project)
    background_tasks.add_task(run_processing_job, job.id)
    return job


@router.get("/projects/{project_id}/jobs/{job_id}", response_model=JobRead)
def get_job_endpoint(project_id: str, job_id: str, session: Session = Depends(get_session)):
    job = session.get(ProcessingJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return _ensure_fresh_job(session, job)


@router.post("/projects/{project_id}/jobs/{job_id}/cancel", response_model=JobRead)
def cancel_job_endpoint(
    project_id: str,
    job_id: str,
    response: Response,
    session: Session = Depends(get_session),
):
    job = session.get(ProcessingJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Processing job not found")
    job = _ensure_fresh_job(session, job)
    if job.job_type not in {"import", "processing", "export"}:
        raise HTTPException(
            status_code=422,
            detail="Only import, processing, and export jobs can be cancelled",
        )
    if job.status in {"complete", "complete_with_errors", "failed", "cancelled"}:
        response.status_code = status.HTTP_200_OK
        return job
    # "interrupted" jobs finalize synchronously (no in-flight worker to cooperatively
    # cancel), so report 200 rather than the async-style 202 (#104 fix 4).
    was_interrupted = job.status == "interrupted"
    if job.job_type == "processing":
        result = request_processing_job_cancellation(session, job)
    elif job.job_type == "export":
        result = request_export_job_cancellation(session, job)
    else:
        result = request_import_job_cancellation(session, job)
    response.status_code = status.HTTP_200_OK if was_interrupted else status.HTTP_202_ACCEPTED
    return result


@router.post("/projects/{project_id}/jobs/{job_id}/retry", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def retry_job_endpoint(
    project_id: str,
    job_id: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    project = _get_project(session, project_id)
    job = session.get(ProcessingJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Processing job not found")
    job = _ensure_fresh_job(session, job)
    if job.job_type != "import":
        raise HTTPException(status_code=422, detail="Only import jobs can be retried")
    if not job.retryable:
        raise HTTPException(status_code=409, detail="Import job is not in a retryable state")

    active_job = _get_active_import_job(session, project_id)
    if active_job is not None:
        if job_is_stale(active_job):
            fail_stale_job(session, active_job)
        else:
            raise HTTPException(status_code=409, detail="An import job is already running")

    photos = list(
        session.exec(select(Photo).where(Photo.project_id == project_id).order_by(Photo.created_at, Photo.id)).all()
    )
    retry_photo_ids = [photo.id for photo in photos if photo_needs_import_retry(photo)]
    retry_job = create_import_retry_job(session, project, retry_photo_ids)
    if retry_photo_ids:
        background_tasks.add_task(run_import_derivative_job, retry_job.id, retry_photo_ids, [])
    else:
        retry_job = complete_import_job(session, retry_job, len(photos), [])
    return retry_job


@router.get("/projects/{project_id}/jobs", response_model=list[JobRead])
def list_jobs_endpoint(
    project_id: str,
    limit: int | None = Query(default=None, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    _get_project(session, project_id)
    _fail_stale_active_jobs(session, project_id)
    statement = (
        select(ProcessingJob)
        .where(ProcessingJob.project_id == project_id)
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
    )
    if offset:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    return list(session.exec(statement).all())


@router.get("/projects/{project_id}/photos", response_model=list[PhotoRead])
def list_photos_endpoint(
    project_id: str,
    limit: int | None = Query(default=None, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    _get_project(session, project_id)
    recommendation_order = case(
        (Photo.ai_recommendation == "Pick", 0),
        (Photo.ai_recommendation == "Maybe", 1),
        (Photo.ai_recommendation == "Unreviewed", 2),
        else_=3,
    )
    statement = (
        select(Photo)
        .where(Photo.project_id == project_id)
        .outerjoin(PhotoGroup, Photo.group_id == PhotoGroup.id)
        .order_by(
            case((Photo.group_id.is_(None), 1), else_=0),
            PhotoGroup.sequence,
            PhotoGroup.created_at,
            Photo.group_id,
            recommendation_order,
            Photo.overall_score.desc(),
            Photo.filename,
        )
    )
    if offset:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    return list(session.exec(statement).all())


@router.get("/projects/{project_id}/photos/status-counts", response_model=PhotoStatusCountsRead)
def get_photo_status_counts_endpoint(project_id: str, session: Session = Depends(get_session)):
    _get_project(session, project_id)
    statuses = ["Pick", "Maybe", "Reject", "Unreviewed"]
    counts = {status: 0 for status in statuses}
    rows = session.exec(
        select(Photo.user_status, func.count())
        .where(Photo.project_id == project_id)
        .where(Photo.user_status.in_(statuses))
        .group_by(Photo.user_status)
    ).all()
    for user_status, count in rows:
        counts[user_status] = count
    return counts


@router.get("/projects/{project_id}/photos/{photo_id}", response_model=PhotoRead)
def get_photo_endpoint(project_id: str, photo_id: str, session: Session = Depends(get_session)):
    return _get_photo(session, project_id, photo_id)


@router.patch("/projects/{project_id}/photos/batch", response_model=list[PhotoRead])
def batch_update_photos_endpoint(
    project_id: str,
    payload: PhotoBatchUpdate,
    session: Session = Depends(get_session),
):
    _get_project(session, project_id)
    requested_ids = list(dict.fromkeys(payload.photo_ids))
    photos: list[Photo] = []
    chunk_size = 400
    for start in range(0, len(requested_ids), chunk_size):
        chunk_ids = requested_ids[start : start + chunk_size]
        photos.extend(
            session.exec(select(Photo).where(Photo.project_id == project_id).where(Photo.id.in_(chunk_ids))).all()
        )
    photo_by_id = {photo.id: photo for photo in photos}
    missing_ids = [photo_id for photo_id in requested_ids if photo_id not in photo_by_id]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Photo not found: {missing_ids[0]}")

    update = payload.model_dump(exclude={"photo_ids"}, exclude_unset=True)
    now = utc_now()
    for photo_id in requested_ids:
        photo = photo_by_id[photo_id]
        for key, value in update.items():
            setattr(photo, key, value)
        photo.updated_at = now
        session.add(photo)
    session.commit()
    for photo_id in requested_ids:
        session.refresh(photo_by_id[photo_id])
    return [photo_by_id[photo_id] for photo_id in requested_ids]


@router.patch("/projects/{project_id}/photos/{photo_id}", response_model=PhotoRead)
def update_photo_endpoint(
    project_id: str,
    photo_id: str,
    payload: PhotoUpdate,
    session: Session = Depends(get_session),
):
    photo = _get_photo(session, project_id, photo_id)
    update = payload.model_dump(exclude_unset=True)
    for key, value in update.items():
        setattr(photo, key, value)
    photo.updated_at = utc_now()
    session.add(photo)
    session.commit()
    session.refresh(photo)
    return photo


@router.get("/projects/{project_id}/groups", response_model=list[GroupRead])
def list_groups_endpoint(
    project_id: str,
    limit: int | None = Query(default=None, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    _get_project(session, project_id)
    statement = (
        select(PhotoGroup)
        .where(PhotoGroup.project_id == project_id)
        .order_by(PhotoGroup.sequence, PhotoGroup.created_at, PhotoGroup.id)
    )
    if offset:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    return list(session.exec(statement).all())


@router.get("/projects/{project_id}/groups/{group_id}", response_model=GroupRead)
def get_group_endpoint(project_id: str, group_id: str, session: Session = Depends(get_session)):
    group = session.get(PhotoGroup, group_id)
    if group is None or group.project_id != project_id:
        raise HTTPException(status_code=404, detail="Photo group not found")
    return group


def _fail_stale_exports(session: Session, project_id: str | None = None) -> None:
    statement = select(ExportRecord).where(ExportRecord.status == "running")
    if project_id is not None:
        statement = statement.where(ExportRecord.project_id == project_id)
    now = utc_now()
    stale_ids: list[str] = []
    for record in session.exec(statement).all():
        if as_utc(now) - as_utc(record.created_at) < STALE_JOB_AFTER:
            continue
        fail_and_cleanup_export_record(session, record, "Export was interrupted before completion")
        stale_ids.append(record.id)
    for export_id in stale_ids:
        sync_export_job(
            session,
            export_id,
            status="failed",
            current_step="failed - stale",
            error_message="Export was interrupted before completion",
        )
    session.commit()


def run_export_job(export_id: str, mode: str, photo_dicts: list[dict], project_root: str) -> None:
    from app.db.session import get_engine

    with Session(get_engine()) as session:
        record = session.get(ExportRecord, export_id)
        if record is None:
            return
        project = session.get(Project, record.project_id)
        if project is None:
            record.status = "failed"
            record.error_message = "Project not found"
            record.completed_at = utc_now()
            session.add(record)
            sync_export_job(
                session,
                export_id,
                status="failed",
                current_step="failed",
                error_message="Project not found",
            )
            session.commit()
            return

        job = session.get(ProcessingJob, export_id)
        if job is not None and job.job_type == "export" and job.cancellation_requested:
            finalize_cancelled_export_job(session, job)
            return

        total = len(photo_dicts)
        record.total_count = total
        record.processed_count = 0
        session.add(record)
        session.commit()

        last_progress_commit_at = 0.0
        last_progress_committed = -1

        def progress_callback(processed: int, total_items: int) -> None:
            nonlocal last_progress_commit_at, last_progress_committed, job
            if job is None:
                job = session.get(ProcessingJob, export_id)
            elif job.job_type == "export":
                session.refresh(job)
            if job is not None and job.job_type == "export" and job.cancellation_requested:
                raise ExportCancelled()
            record.processed_count = processed
            record.total_count = total_items
            if job is not None and job.job_type == "export":
                job.processed_items = processed
                job.total_items = total_items
                if job.total_items:
                    job.progress_percent = round(min(100.0, (job.processed_items / job.total_items) * 100), 2)
                job.updated_at = utc_now()
                session.add(job)
            now = time.monotonic()
            should_commit = (
                processed >= total_items
                or processed - last_progress_committed >= 25
                or now - last_progress_commit_at >= 0.25
            )
            if not should_commit:
                return
            session.add(record)
            session.commit()
            last_progress_commit_at = now
            last_progress_committed = processed

        try:
            target = Path(record.output_path)
            if mode == "csv":
                output_path = write_selection_csv(target, photo_dicts, progress_callback=progress_callback)
            elif mode == "folder":
                output_path = copy_selected_files(
                    target, photo_dicts, project_root=Path(project_root), progress_callback=progress_callback
                )
            else:
                output_path = zip_selected_files(
                    target, photo_dicts, project_root=Path(project_root), progress_callback=progress_callback
                )
            record.status = "complete"
            record.output_path = str(output_path)
            record.processed_count = total
            record.total_count = total
            record.error_message = None
            record.completed_at = utc_now()
            session.add(record)
            sync_export_job(
                session,
                export_id,
                status="complete",
                current_step="complete",
                processed_items=total,
                total_items=total,
            )
            session.commit()
        except ExportCancelled:
            session.rollback()
            job = session.get(ProcessingJob, export_id)
            if job is not None and job.job_type == "export":
                finalize_cancelled_export_job(session, job)
                return
            record = session.get(ExportRecord, export_id)
            if record is None:
                return
            fail_and_cleanup_export_record(session, record, EXPORT_CANCEL_REASON, commit=True)
        except Exception as error:
            session.rollback()
            record = session.get(ExportRecord, export_id)
            if record is None:
                return
            error_message = (
                str(error) if isinstance(error, (FileNotFoundError, ValueError)) and str(error) else "Export failed"
            )
            fail_and_cleanup_export_record(session, record, error_message, commit=False)
            sync_export_job(
                session,
                export_id,
                status="failed",
                current_step="failed",
                error_message=error_message,
            )
            session.commit()


@router.post("/projects/{project_id}/exports", response_model=ExportRead, status_code=status.HTTP_201_CREATED)
@router.post("/projects/{project_id}/export", response_model=ExportRead, status_code=status.HTTP_201_CREATED)
def create_export_endpoint(
    project_id: str,
    payload: ExportCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    project = _get_project(session, project_id)
    _fail_stale_exports(session, project_id)
    photos = list(
        session.exec(
            select(Photo)
            .where(Photo.project_id == project_id)
            .where(Photo.user_status.in_(payload.statuses))
            .order_by(Photo.filename)
        ).all()
    )
    photo_dicts = [photo.model_dump() for photo in photos]
    if not photo_dicts:
        raise HTTPException(status_code=422, detail="No photos match the selected export statuses")

    try:
        export_root = project_export_root(project)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    selected_count = len(photo_dicts)
    record = ExportRecord(
        project_id=project_id,
        mode=payload.mode,
        status="running",
        selected_count=selected_count,
        processed_count=0,
        total_count=selected_count,
        statuses=json.dumps(payload.statuses),
        output_path="pending",
    )
    target = _export_target(export_root, record.id, payload.mode)
    record.output_path = str(target)
    now = utc_now()
    job = ProcessingJob(
        id=record.id,
        project_id=project_id,
        job_type="export",
        status="running",
        current_step="exporting",
        total_items=selected_count,
        processed_items=0,
        failed_items=0,
        progress_percent=0.0,
        started_at=now,
    )
    session.add(record)
    session.add(job)
    session.commit()
    session.refresh(record)
    background_tasks.add_task(run_export_job, record.id, payload.mode, photo_dicts, project.root_path)
    return record


@router.get("/projects/{project_id}/exports", response_model=list[ExportRead])
@router.get("/projects/{project_id}/export", response_model=list[ExportRead])
def list_exports_endpoint(
    project_id: str,
    limit: int | None = Query(default=None, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    _get_project(session, project_id)
    _fail_stale_exports(session, project_id)
    statement = (
        select(ExportRecord)
        .where(ExportRecord.project_id == project_id)
        .order_by(ExportRecord.created_at.desc(), ExportRecord.id.desc())
    )
    if offset:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    return list(session.exec(statement).all())


@router.get("/projects/{project_id}/exports/{export_id}", response_model=ExportRead)
@router.get("/projects/{project_id}/export/{export_id}", response_model=ExportRead)
def get_export_endpoint(project_id: str, export_id: str, session: Session = Depends(get_session)):
    return _get_export(session, project_id, export_id)


@router.get("/projects/{project_id}/exports/{export_id}/download")
@router.get("/projects/{project_id}/export/{export_id}/download")
def download_export_endpoint(project_id: str, export_id: str, session: Session = Depends(get_session)):
    project = _get_project(session, project_id)
    export = _get_export(session, project_id, export_id)
    if export.mode not in {"csv", "zip"}:
        raise HTTPException(status_code=422, detail="Folder exports are available at their local output path")
    if export.status != "complete":
        raise HTTPException(status_code=409, detail="Export artifact is not ready for download")

    export_path = Path(export.output_path)
    try:
        export_root = project_export_root(project).resolve()
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Export artifact not found") from error
    try:
        resolved_export_path = export_path.resolve(strict=True)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Export artifact not found") from error

    if not resolved_export_path.is_file() or not resolved_export_path.is_relative_to(export_root):
        raise HTTPException(status_code=404, detail="Export artifact not found")

    media_type = "text/csv" if export.mode == "csv" else "application/zip"
    return FileResponse(resolved_export_path, media_type=media_type, filename=resolved_export_path.name)


@router.get("/assets/{project_id}/{kind}/{filename}")
def get_generated_asset(project_id: str, kind: str, filename: str, session: Session = Depends(get_session)):
    project = _get_project(session, project_id)
    if kind not in {"thumbnails", "previews"}:
        raise HTTPException(status_code=404, detail="Asset type not found")
    try:
        project_root = Path(project.root_path).resolve(strict=True)
        asset_root = (project_root / kind).resolve(strict=True)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Asset not found") from error
    if not asset_root.is_dir() or not asset_root.is_relative_to(project_root):
        raise HTTPException(status_code=404, detail="Asset not found")
    path = asset_root / Path(filename).name
    try:
        resolved_path = path.resolve(strict=True)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Asset not found") from error
    if not resolved_path.is_file() or not resolved_path.is_relative_to(asset_root):
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(resolved_path)
