import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
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
    PhotoRead,
    PhotoUpdate,
    ProjectCreate,
    ProjectRead,
)
from app.services.exporting import copy_selected_files, write_selection_csv, zip_selected_files
from app.services.importing import import_image_file
from app.services.processing import process_project, project_export_root
from app.services.projects import create_project, list_projects


router = APIRouter(prefix="/api")


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
    session.delete(project)
    session.commit()
    return None


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
            imported.append(import_image_file(session, project, filename, upload.file))
        except ValueError as error:
            skipped.append({"filename": filename, "reason": str(error)})
    if not imported and skipped:
        details = "; ".join(f"{item['filename']}: {item['reason']}" for item in skipped)
        raise HTTPException(status_code=422, detail=details)
    return {"imported": imported, "skipped": skipped}


@router.post("/projects/{project_id}/process", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def process_project_endpoint(project_id: str, session: Session = Depends(get_session)):
    project = _get_project(session, project_id)
    return process_project(session, project)


@router.get("/projects/{project_id}/jobs/{job_id}", response_model=JobRead)
def get_job_endpoint(project_id: str, job_id: str, session: Session = Depends(get_session)):
    job = session.get(ProcessingJob, job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return job


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
    return list(session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project_id).order_by(PhotoGroup.created_at, PhotoGroup.id)).all())


@router.get("/projects/{project_id}/groups/{group_id}", response_model=GroupRead)
def get_group_endpoint(project_id: str, group_id: str, session: Session = Depends(get_session)):
    group = session.get(PhotoGroup, group_id)
    if group is None or group.project_id != project_id:
        raise HTTPException(status_code=404, detail="Photo group not found")
    return group


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
        selected_count=len(photo_dicts),
        statuses=json.dumps(payload.statuses),
        output_path="",
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    target = _export_target(export_root, record.id, payload.mode)

    if payload.mode == "csv":
        output_path = write_selection_csv(target, photo_dicts)
    elif payload.mode == "folder":
        output_path = copy_selected_files(target, photo_dicts)
    else:
        output_path = zip_selected_files(target, photo_dicts)

    record.output_path = str(output_path)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.get("/projects/{project_id}/export/{export_id}", response_model=ExportRead)
def get_export_endpoint(project_id: str, export_id: str, session: Session = Depends(get_session)):
    export = session.get(ExportRecord, export_id)
    if export is None or export.project_id != project_id:
        raise HTTPException(status_code=404, detail="Export not found")
    return export


@router.get("/assets/{project_id}/{kind}/{filename}")
def get_generated_asset(project_id: str, kind: str, filename: str, session: Session = Depends(get_session)):
    project = _get_project(session, project_id)
    if kind not in {"thumbnails", "previews"}:
        raise HTTPException(status_code=404, detail="Asset type not found")
    path = Path(project.root_path) / kind / Path(filename).name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(path)
