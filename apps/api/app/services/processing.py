import json
from pathlib import Path

from sqlmodel import Session, select

from app.db.session import get_engine
from app.models.entities import Photo, PhotoGroup, ProcessingJob, Project, utc_now
from app.services.grouping import group_similar_photos
from app.services.importing import ensure_photo_derivatives
from app.services.ranking import rank_group


def _progress_percent(processed_items: int, failed_items: int, total_items: int) -> float:
    if total_items <= 0:
        return 100.0
    return round(min(100.0, ((processed_items + failed_items) / total_items) * 100), 2)


def _save_job(
    session: Session,
    job: ProcessingJob,
    current_step: str,
    processed_items: int | None = None,
    failed_items: int | None = None,
) -> None:
    job.current_step = current_step
    if processed_items is not None:
        job.processed_items = processed_items
    if failed_items is not None:
        job.failed_items = failed_items
    job.progress_percent = _progress_percent(job.processed_items, job.failed_items, job.total_items)
    job.updated_at = utc_now()
    session.add(job)
    session.commit()
    session.refresh(job)


def _photo_embedding(photo: Photo) -> list[float]:
    raw_embedding = json.loads(photo.embedding or "[]")
    if not isinstance(raw_embedding, list):
        raise ValueError("Stored similarity data is not a list")
    embedding: list[float] = []
    for value in raw_embedding:
        if not isinstance(value, int | float):
            raise ValueError("Stored similarity data contains a non-numeric value")
        embedding.append(float(value))
    return embedding


def _build_group_inputs(photos: list[Photo]) -> tuple[list[dict], list[Photo]]:
    group_inputs = []
    failed_photos = []
    for photo in photos:
        try:
            embedding = _photo_embedding(photo)
        except (json.JSONDecodeError, TypeError, ValueError):
            failed_photos.append(photo)
            continue
        group_inputs.append(
            {
                "id": photo.id,
                "filename": photo.filename,
                "capture_time": photo.capture_time,
                "embedding": embedding,
                "perceptual_hash": photo.perceptual_hash,
                "width": photo.width,
                "height": photo.height,
                "camera_model": photo.camera_model,
                "focal_length": photo.focal_length,
            }
        )
    return group_inputs, failed_photos


def _missing_derivative_paths(photo: Photo) -> list[str]:
    missing = []
    for label, raw_path in (("thumbnail", photo.thumbnail_path), ("preview", photo.preview_path)):
        if not raw_path or not Path(raw_path).is_file():
            missing.append(label)
    return missing


def _mark_photo_failed(session: Session, photo: Photo, reason: str, explanation: str) -> None:
    photo.ai_recommendation = "Unreviewed"
    photo.recommendation_explanation = explanation
    photo.processing_state = "failed"
    photo.processing_error = reason
    photo.updated_at = utc_now()
    session.add(photo)


def _project_processing_is_current(session: Session, project: Project, photos: list[Photo]) -> bool:
    if not photos or project.processed_images != len(photos) or project.total_images != len(photos):
        return False
    if any(photo.processing_state != "processed" or photo.processing_error or not photo.group_id for photo in photos):
        return False

    groups = list(session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project.id)).all())
    return bool(groups) and sum(group.photo_count for group in groups) == len(photos)


def _complete_unchanged_job(session: Session, job: ProcessingJob, total_items: int) -> ProcessingJob:
    now = utc_now()
    job.status = "complete"
    job.current_step = "complete - no changes"
    job.total_items = total_items
    job.processed_items = total_items
    job.failed_items = 0
    job.progress_percent = 100.0
    job.error_message = None
    job.completed_at = now
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def create_processing_job(session: Session, project: Project) -> ProcessingJob:
    job = ProcessingJob(
        project_id=project.id,
        job_type="processing",
        status="queued",
        current_step="queued",
        total_items=project.total_images,
        processed_items=0,
        failed_items=0,
        progress_percent=0.0,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def run_processing_job(job_id: str) -> None:
    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        if job is None:
            return
        project = session.get(Project, job.project_id)
        if project is None:
            job.status = "failed"
            job.current_step = "failed"
            job.error_message = "Project not found"
            job.completed_at = utc_now()
            job.updated_at = utc_now()
            session.add(job)
            session.commit()
            return
        process_project(session, project, job)


def process_project(session: Session, project: Project, job: ProcessingJob | None = None) -> ProcessingJob:
    photos = list(session.exec(select(Photo).where(Photo.project_id == project.id)).all())
    if job is None:
        job = create_processing_job(session, project)

    job.status = "running"
    job.current_step = "starting"
    job.total_items = len(photos)
    job.processed_items = 0
    job.failed_items = 0
    job.progress_percent = _progress_percent(0, 0, len(photos))
    job.error_message = None
    job.started_at = utc_now()
    job.completed_at = None
    job.updated_at = utc_now()
    session.add(job)
    session.commit()
    session.refresh(job)

    if _project_processing_is_current(session, project, photos):
        return _complete_unchanged_job(session, job, len(photos))

    try:
        _save_job(session, job, "clearing stale groups", 0)
        for existing in session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project.id)).all():
            session.delete(existing)
        for photo in photos:
            photo.group_id = None
            photo.processing_state = "processing"
            photo.processing_error = None
            session.add(photo)
        session.commit()

        _save_job(session, job, "validating generated files", 0)
        derivative_failed_photos = []
        derivative_failed_ids = set()
        for photo in photos:
            missing_derivatives = _missing_derivative_paths(photo)
            if not missing_derivatives:
                continue
            try:
                ensure_photo_derivatives(project, photo)
                session.add(photo)
            except (OSError, ValueError):
                derivative_failed_photos.append(photo)
                derivative_failed_ids.add(photo.id)
                reason = f"Missing generated {' and '.join(missing_derivatives)}"
                _mark_photo_failed(
                    session,
                    photo,
                    reason,
                    "Processing skipped this photo because its generated files could not be rebuilt from the local "
                    "copied original. Reimport the photo to rebuild local derived files.",
                )
        session.commit()

        _save_job(session, job, "validating similarity data", 0, len(derivative_failed_photos))
        candidate_photos = [photo for photo in photos if photo.id not in derivative_failed_ids]
        group_inputs, similarity_failed_photos = _build_group_inputs(candidate_photos)
        for photo in similarity_failed_photos:
            _mark_photo_failed(
                session,
                photo,
                "Stored similarity data is invalid",
                "Processing skipped this photo because its stored similarity data is invalid. Reimport the photo "
                "to rebuild local analysis data.",
            )
        session.commit()

        failed_photos = derivative_failed_photos + similarity_failed_photos

        _save_job(session, job, "grouping photos", 0, len(failed_photos))
        failed_photo_ids = {failed.id for failed in failed_photos}
        photo_map = {photo.id: photo for photo in candidate_photos if photo.id not in failed_photo_ids}
        grouped_photos = group_similar_photos(group_inputs)

        for index, grouped in enumerate(grouped_photos, start=1):
            _save_job(session, job, f"ranking group {index} of {len(grouped_photos)}", job.processed_items)
            group = PhotoGroup(project_id=project.id, group_type=grouped.group_type, photo_count=len(grouped.photo_ids))
            session.add(group)
            session.commit()
            session.refresh(group)

            ranking_input = []
            for photo_id in grouped.photo_ids:
                photo = photo_map[photo_id]
                photo.group_id = group.id
                ranking_input.append(
                    {
                        "id": photo.id,
                        "sharpness_score": photo.sharpness_score,
                        "exposure_score": photo.exposure_score,
                        "contrast_score": photo.contrast_score,
                        "noise_score": photo.noise_score,
                        "face_presence": photo.face_presence,
                        "eye_open_confidence": photo.eye_open_confidence,
                        "face_quality_score": photo.face_quality_score,
                        "aesthetic_score": photo.aesthetic_score,
                        "duplicate_penalty": 0.0 if len(grouped.photo_ids) == 1 else 0.1,
                    }
                )

            ranked = rank_group(ranking_input)
            group.representative_photo_id = ranked[0].photo_id if ranked else None
            for item in ranked:
                photo = photo_map[item.photo_id]
                photo.ai_recommendation = item.recommendation
                photo.recommendation_explanation = item.explanation
                photo.overall_score = max(photo.overall_score, item.score)
                photo.processing_state = "processed"
                photo.processing_error = None
                photo.updated_at = utc_now()
                session.add(photo)

            group.updated_at = utc_now()
            session.add(group)
            processed_items = job.processed_items + len(grouped.photo_ids)
            job.processed_items = processed_items
            job.updated_at = utc_now()
            session.add(job)
            session.commit()

        job.status = "complete"
        job.current_step = "complete"
        job.processed_items = len(group_inputs)
        job.failed_items = len(failed_photos)
        job.progress_percent = 100.0
        if failed_photos:
            job.error_message = f"{len(failed_photos)} photo could not be processed"
        job.completed_at = utc_now()
        project.processed_images = len(group_inputs)
        project.last_processed_at = job.completed_at
        project.updated_at = utc_now()
        session.add(project)
    except Exception as error:
        session.rollback()
        job.status = "failed"
        job.current_step = "failed"
        job.error_message = str(error)
        job.failed_items = max(1, job.total_items - job.processed_items) if job.total_items else 1
        job.progress_percent = _progress_percent(job.processed_items, job.failed_items, job.total_items)
        job.completed_at = utc_now()

    job.updated_at = utc_now()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def project_export_root(project: Project) -> Path:
    target = Path(project.root_path) / "exports"
    target.mkdir(parents=True, exist_ok=True)
    return target
