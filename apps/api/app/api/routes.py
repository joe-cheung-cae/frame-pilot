import json
import os
import shutil
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import case, func
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.entities import ExportRecord, Photo, PhotoGroup, ProcessingJob, Project, utc_now
from app.schemas.api import (
    ExportCreate,
    ExportRead,
    GroupRead,
    ImportResult,
    JobRead,
    PhotoBatchUpdate,
    PhotoRead,
    PhotoStatusCountsRead,
    PhotoUpdate,
    ProjectCreate,
    ProjectRead,
)
from app.services.exporting import copy_selected_files, write_selection_csv, zip_selected_files
from app.services.importing import (
    ImportTimingCollector,
    complete_import_job,
    create_import_job,
    create_import_retry_job,
    fail_stale_import_job,
    import_job_is_stale,
    import_timing_stage,
    invalidate_project_processing,
    photo_needs_import_retry,
    register_import_file,
    request_import_job_cancellation,
    run_import_derivative_job,
    update_import_job,
)
from app.services.processing import (
    create_processing_job,
    fail_stale_processing_job,
    processing_job_is_stale,
    project_export_root,
    run_processing_job,
)
from app.services.projects import create_project, list_projects

router = APIRouter(prefix="/api")


@router.get("/health")
def api_health_endpoint() -> dict[str, str]:
    return {"status": "ok"}


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


def _remove_partial_export(target: Path, export_root: Path) -> None:
    try:
        resolved_target = target.resolve(strict=True)
        resolved_export_root = export_root.resolve(strict=True)
    except FileNotFoundError:
        return
    if not resolved_target.is_relative_to(resolved_export_root):
        return
    if target.is_symlink():
        target.unlink()
    elif resolved_target.is_dir():
        shutil.rmtree(resolved_target)
    else:
        resolved_target.unlink()


def _get_export(session: Session, project_id: str, export_id: str) -> ExportRecord:
    export = session.get(ExportRecord, export_id)
    if export is None or export.project_id != project_id:
        raise HTTPException(status_code=404, detail="Export not found")
    return export


def _get_active_processing_job(session: Session, project_id: str) -> ProcessingJob | None:
    return session.exec(
        select(ProcessingJob)
        .where(ProcessingJob.project_id == project_id)
        .where(ProcessingJob.job_type == "processing")
        .where(ProcessingJob.status.in_(["queued", "running"]))
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
    ).first()


def _get_active_import_job(session: Session, project_id: str) -> ProcessingJob | None:
    return session.exec(
        select(ProcessingJob)
        .where(ProcessingJob.project_id == project_id)
        .where(ProcessingJob.job_type == "import")
        .where(ProcessingJob.status.in_(["queued", "running"]))
        .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
    ).first()


def _get_current_active_import_job(session: Session, project_id: str) -> ProcessingJob | None:
    while active_job := _get_active_import_job(session, project_id):
        if import_job_is_stale(active_job):
            fail_stale_import_job(session, active_job)
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
        started_at=job.started_at,
        completed_at=job.completed_at,
        retryable=job.retryable,
    )


def _project_read(session: Session, project: Project) -> ProjectRead:
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
    active_jobs = session.exec(
        select(ProcessingJob)
        .where(ProcessingJob.project_id == project_id)
        .where(ProcessingJob.status.in_(["queued", "running"]))
    ).all()
    for job in active_jobs:
        if job.job_type == "import" and import_job_is_stale(job):
            fail_stale_import_job(session, job)
        elif job.job_type == "processing" and processing_job_is_stale(job):
            fail_stale_processing_job(session, job)


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(payload: ProjectCreate, session: Session = Depends(get_session)):
    try:
        return create_project(session, payload.name, payload.root_path)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/projects", response_model=list[ProjectRead])
def list_projects_endpoint(session: Session = Depends(get_session)):
    return [_project_read(session, project) for project in list_projects(session)]


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project_endpoint(project_id: str, session: Session = Depends(get_session)):
    return _project_read(session, _get_project(session, project_id))


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(project_id: str, session: Session = Depends(get_session)):
    project = _get_project(session, project_id)
    for model in (ExportRecord, ProcessingJob, Photo, PhotoGroup):
        for item in session.exec(select(model).where(model.project_id == project_id)).all():
            session.delete(item)
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
    include_timing: bool = Query(default=False),
    session: Session = Depends(get_session),
):
    timing_enabled = include_timing or os.environ.get("FRAMEPILOT_IMPORT_TIMING") == "1"
    timing = ImportTimingCollector() if timing_enabled else None
    started = time.perf_counter()
    project = _get_project(session, project_id)
    total_files = len(files)
    job = create_import_job(session, project, total_files)
    imported: list[Photo] = []
    derivative_photo_ids: list[str] = []
    skipped: list[dict[str, str]] = []
    new_import_count = 0
    failed_count = 0
    for index, upload in enumerate(files, start=1):
        filename = upload.filename or "image"

        def update_stage(
            stage: str,
            current_index: int = index,
            current_failed_count: int = failed_count,
        ) -> None:
            update_import_job(
                session,
                job,
                f"{stage} {current_index} of {total_files}",
                0,
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
            update_import_job(
                session,
                job,
                f"file_copy_or_register {index} of {total_files}",
                0,
                failed_count,
                force=True,
            )
        except ValueError as error:
            skipped.append({"filename": filename, "reason": str(error)})
            failed_count += 1
            update_import_job(
                session,
                job,
                f"file_skipped {index} of {total_files}",
                0,
                failed_count,
                force=True,
            )
    if not imported and skipped:
        complete_import_job(session, job, len(imported), skipped)
        details = "; ".join(f"{item['filename']}: {item['reason']}" for item in skipped)
        raise HTTPException(status_code=422, detail=details)
    if new_import_count:
        update_import_job(
            session,
            job,
            "processing_invalidation",
            0,
            failed_count,
            force=True,
        )
        with import_timing_stage(timing, "processing_invalidation"):
            invalidate_project_processing(session, project)
        with import_timing_stage(timing, "import_endpoint_commit"):
            session.commit()
    if derivative_photo_ids:
        update_import_job(session, job, "derivative_generation", 0, failed_count, force=True)
        background_tasks.add_task(run_import_derivative_job, job.id, derivative_photo_ids, skipped)
    else:
        job = complete_import_job(session, job, len(imported), skipped)
    response = {
        "imported": imported,
        "skipped": skipped,
        "job": job,
        "total_files": total_files,
        "accepted_files": len(imported),
        "skipped_files": len(skipped),
        "failed_files": len(skipped),
    }
    if timing is not None:
        total_seconds = round(time.perf_counter() - started, 6)
        timing.record("import_endpoint_total", total_seconds)
        response["timing"] = {
            "total_files": len(files),
            "imported_files": len(imported),
            "skipped_files": len(skipped),
            "total_seconds": total_seconds,
            "stages": timing.summary(),
        }
    return response


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
        if processing_job_is_stale(active_job):
            fail_stale_processing_job(session, active_job)
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
    if import_job_is_stale(job):
        job = fail_stale_import_job(session, job)
    elif processing_job_is_stale(job):
        job = fail_stale_processing_job(session, job)
    return job


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
    if import_job_is_stale(job):
        job = fail_stale_import_job(session, job)
    elif processing_job_is_stale(job):
        job = fail_stale_processing_job(session, job)
    if job.job_type != "import":
        raise HTTPException(status_code=422, detail="Only import jobs can be cancelled")
    if job.status in {"complete", "complete_with_errors", "failed", "cancelled"}:
        response.status_code = status.HTTP_200_OK
        return job
    response.status_code = status.HTTP_202_ACCEPTED
    return request_import_job_cancellation(session, job)


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
    if import_job_is_stale(job):
        job = fail_stale_import_job(session, job)
    if job.job_type != "import":
        raise HTTPException(status_code=422, detail="Only import jobs can be retried")
    if not job.retryable:
        raise HTTPException(status_code=409, detail="Import job is not in a retryable state")

    active_job = _get_active_import_job(session, project_id)
    if active_job is not None:
        if import_job_is_stale(active_job):
            fail_stale_import_job(session, active_job)
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
        .order_by(Photo.group_id, recommendation_order, Photo.overall_score.desc(), Photo.filename)
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
    photos = list(
        session.exec(select(Photo).where(Photo.project_id == project_id).where(Photo.id.in_(requested_ids))).all()
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
    for photo in photos:
        session.refresh(photo)
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
        select(PhotoGroup).where(PhotoGroup.project_id == project_id).order_by(PhotoGroup.created_at, PhotoGroup.id)
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


@router.post("/projects/{project_id}/exports", response_model=ExportRead, status_code=status.HTTP_201_CREATED)
@router.post("/projects/{project_id}/export", response_model=ExportRead, status_code=status.HTTP_201_CREATED)
def create_export_endpoint(project_id: str, payload: ExportCreate, session: Session = Depends(get_session)):
    project = _get_project(session, project_id)
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
    record = ExportRecord(
        project_id=project_id,
        mode=payload.mode,
        status="running",
        selected_count=len(photo_dicts),
        statuses=json.dumps(payload.statuses),
        output_path="pending",
    )
    target = _export_target(export_root, record.id, payload.mode)
    record.output_path = str(target)
    session.add(record)
    session.commit()
    session.refresh(record)

    try:
        if payload.mode == "csv":
            output_path = write_selection_csv(target, photo_dicts)
        elif payload.mode == "folder":
            output_path = copy_selected_files(target, photo_dicts, project_root=Path(project.root_path))
        else:
            output_path = zip_selected_files(target, photo_dicts, project_root=Path(project.root_path))
    except Exception as error:
        session.rollback()
        _remove_partial_export(target, export_root)
        error_message = (
            str(error) if isinstance(error, (FileNotFoundError, ValueError)) and str(error) else "Export failed"
        )
        record.status = "failed"
        record.output_path = str(target)
        record.error_message = error_message
        record.completed_at = utc_now()
        session.add(record)
        session.commit()
        raise HTTPException(status_code=500, detail=error_message) from error

    record.status = "complete"
    record.output_path = str(output_path)
    record.completed_at = utc_now()
    session.add(record)
    session.commit()
    session.refresh(record)
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
