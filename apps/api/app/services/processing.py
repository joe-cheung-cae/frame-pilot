import json
from pathlib import Path

from sqlmodel import Session, select

from app.models.entities import Photo, PhotoGroup, ProcessingJob, Project, utc_now
from app.services.grouping import group_similar_photos
from app.services.ranking import rank_group


def process_project(session: Session, project: Project) -> ProcessingJob:
    photos = list(session.exec(select(Photo).where(Photo.project_id == project.id)).all())
    job = ProcessingJob(
        project_id=project.id,
        status="running",
        current_step="grouping",
        total_items=len(photos),
        processed_items=0,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    for existing in session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project.id)).all():
        session.delete(existing)
    session.commit()

    group_inputs = [
        {
            "id": photo.id,
            "filename": photo.filename,
            "capture_time": photo.capture_time,
            "embedding": json.loads(photo.embedding or "[]"),
        }
        for photo in photos
    ]
    photo_map = {photo.id: photo for photo in photos}

    for grouped in group_similar_photos(group_inputs):
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
            photo.updated_at = utc_now()
            session.add(photo)

        group.updated_at = utc_now()
        session.add(group)
        job.processed_items += len(grouped.photo_ids)
        session.add(job)
        session.commit()

    job.status = "complete"
    job.current_step = "complete"
    job.processed_items = len(photos)
    job.updated_at = utc_now()
    project.processed_images = len(photos)
    project.updated_at = utc_now()
    session.add(job)
    session.add(project)
    session.commit()
    session.refresh(job)
    return job


def project_export_root(project: Project) -> Path:
    target = Path(project.root_path) / "exports"
    target.mkdir(parents=True, exist_ok=True)
    return target
