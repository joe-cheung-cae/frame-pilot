import json
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import case
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
    PhotoUpdate,
    ProjectCreate,
    ProjectRead,
)
from app.services.exporting import copy_selected_files, write_selection_csv, zip_selected_files
from app.services.importing import import_image_file, invalidate_project_processing
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
        return export_root / f"selection-{export_id}.csv"
    if mode == "folder":
        return export_root / f"selected-{export_id}"
    return export_root / f"selected-{export_id}.zip"


def _remove_partial_export(target: Path) -> None:
    if target.is_dir() and not target.is_symlink():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()


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


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(payload: ProjectCreate, session: Session = Depends(get_session)):
    return create_project(session, payload.name, payload.root_path)


@router.get("/projects", response_model=list[ProjectRead])
def list_projects_endpoint(session: Session = Depends(get_session)):
    return list_projects(session)


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project_endpoint(project_id: str, session: Session = Depends(get_session)):
    return _get_project(session, project_id)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(project_id: str, session: Session = Depends(get_session)):
    project = _get_project(session, project_id)
    for model in (ExportRecord, ProcessingJob, Photo, PhotoGroup):
        for item in session.exec(select(model).where(model.project_id == project_id)).all():
            session.delete(item)
    session.delete(project)
    session.commit()
    return None


@router.post("/projects/{project_id}/imports", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
@router.post("/projects/{project_id}/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
async def import_photos_endpoint(
    project_id: str,
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session),
):
    project = _get_project(session, project_id)
    imported: list[Photo] = []
    skipped: list[dict[str, str]] = []
    for upload in files:
        filename = upload.filename or "image"
        try:
            imported.append(import_image_file(session, project, filename, upload.file, invalidate_processing=False))
        except ValueError as error:
            skipped.append({"filename": filename, "reason": str(error)})
    if not imported and skipped:
        details = "; ".join(f"{item['filename']}: {item['reason']}" for item in skipped)
        raise HTTPException(status_code=422, detail=details)
    if imported:
        invalidate_project_processing(session, project)
        session.commit()
    return {"imported": imported, "skipped": skipped}


@router.post("/projects/{project_id}/process", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def process_project_endpoint(
    project_id: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    project = _get_project(session, project_id)
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
    return job


@router.get("/projects/{project_id}/jobs", response_model=list[JobRead])
def list_jobs_endpoint(project_id: str, session: Session = Depends(get_session)):
    _get_project(session, project_id)
    return list(
        session.exec(
            select(ProcessingJob)
            .where(ProcessingJob.project_id == project_id)
            .order_by(ProcessingJob.created_at.desc(), ProcessingJob.id.desc())
        ).all()
    )


@router.get("/projects/{project_id}/photos", response_model=list[PhotoRead])
def list_photos_endpoint(project_id: str, session: Session = Depends(get_session)):
    _get_project(session, project_id)
    recommendation_order = case(
        (Photo.ai_recommendation == "Pick", 0),
        (Photo.ai_recommendation == "Maybe", 1),
        (Photo.ai_recommendation == "Unreviewed", 2),
        else_=3,
    )
    return list(
        session.exec(
            select(Photo)
            .where(Photo.project_id == project_id)
            .order_by(Photo.group_id, recommendation_order, Photo.overall_score.desc(), Photo.filename)
        ).all()
    )


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
def list_groups_endpoint(project_id: str, session: Session = Depends(get_session)):
    _get_project(session, project_id)
    return list(
        session.exec(
            select(PhotoGroup).where(PhotoGroup.project_id == project_id).order_by(PhotoGroup.created_at, PhotoGroup.id)
        ).all()
    )


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

    export_root = project_export_root(project)
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
            output_path = copy_selected_files(target, photo_dicts)
        else:
            output_path = zip_selected_files(target, photo_dicts)
    except Exception as error:
        session.rollback()
        _remove_partial_export(target)
        record.status = "failed"
        record.output_path = str(target)
        record.error_message = "Export failed"
        record.completed_at = utc_now()
        session.add(record)
        session.commit()
        raise HTTPException(status_code=500, detail="Export failed") from error

    record.status = "complete"
    record.output_path = str(output_path)
    record.completed_at = utc_now()
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.get("/projects/{project_id}/exports", response_model=list[ExportRead])
@router.get("/projects/{project_id}/export", response_model=list[ExportRead])
def list_exports_endpoint(project_id: str, session: Session = Depends(get_session)):
    _get_project(session, project_id)
    return list(
        session.exec(
            select(ExportRecord).where(ExportRecord.project_id == project_id).order_by(ExportRecord.created_at.desc())
        ).all()
    )


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
    export_root = project_export_root(project).resolve()
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
    asset_root = (Path(project.root_path) / kind).resolve()
    path = asset_root / Path(filename).name
    try:
        resolved_path = path.resolve(strict=True)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Asset not found") from error
    if not resolved_path.is_file() or not resolved_path.is_relative_to(asset_root):
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(resolved_path)
