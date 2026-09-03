import json
import uuid
from pathlib import Path

from sqlmodel import Session, select

from app.db.session import get_engine
from app.models.entities import Photo, PhotoGroup, ProcessingJob, Project, utc_now
from app.services.grouping import group_similar_photos
from app.services.importing import ensure_photo_derivatives
from app.services.jobs import (
    TERMINAL_JOB_STATUSES,
    claim_job_atomic,
    job_is_stale,
    mark_job_failed,
    progress_percent,
    refresh_job_lease_heartbeat,
    release_stale_interrupted_lease,
)
from app.services.ranking import RankedPhoto, rank_group

# Regenerating derivatives for many missing photos in a single pass with no
# intervening heartbeat refresh can run past JOB_LEASE_STALE_AFTER on large batches, so a
# concurrent stale sweep could fail_stale a job that is still actively regenerating files
# (Bugbot residual fix after #104 / 6b580a8).
DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL = 5

PROCESSING_CANCEL_REASON = "Processing job was cancelled by user request"


def _failed_photo_count_message(count: int) -> str:
    noun = "photo" if count == 1 else "photos"
    return f"{count} {noun} could not be processed"


def _processing_job_cancellation_requested(session: Session, job: ProcessingJob) -> bool:
    session.refresh(job)
    return bool(job.cancellation_requested) and job.status not in TERMINAL_JOB_STATUSES


def _finalize_cancelled_processing_job(session: Session, job: ProcessingJob) -> ProcessingJob:
    now = utc_now()
    reset_project_after_processing_failure(session, job.project_id, PROCESSING_CANCEL_REASON)
    job.status = "cancelled"
    job.current_step = "cancelled"
    job.cancellation_requested = True
    job.cancelled_at = now
    job.completed_at = now
    job.interrupted_at = None
    job.worker_id = None
    job.heartbeat_at = None
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _save_job(
    session: Session,
    job: ProcessingJob,
    current_step: str,
    processed_items: int | None = None,
    failed_items: int | None = None,
) -> bool:
    if _processing_job_cancellation_requested(session, job):
        _finalize_cancelled_processing_job(session, job)
        return False
    if job.status in TERMINAL_JOB_STATUSES:
        return False
    job.current_step = current_step
    if processed_items is not None:
        job.processed_items = processed_items
    if failed_items is not None:
        job.failed_items = failed_items
    job.progress_percent = progress_percent(job.processed_items, job.failed_items, job.total_items)
    job.updated_at = utc_now()
    # Keep a held lease fresh so long processing runs do not look stale mid-flight (#104 fix 1).
    refresh_job_lease_heartbeat(session, job)
    session.add(job)
    session.commit()
    session.refresh(job)
    return True


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
                "lens_model": photo.lens_model,
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


def reset_project_after_processing_failure(session: Session, project_id: str, reason: str) -> None:
    photos = list(session.exec(select(Photo).where(Photo.project_id == project_id)).all())
    for photo in photos:
        photo.group_id = None
        if photo.processing_state in {"processing", "processed"}:
            photo.ai_recommendation = "Unreviewed"
            photo.recommendation_explanation = (
                "Processing was interrupted before this photo completed. Run processing again to retry local analysis."
            )
            photo.processing_state = "imported"
            photo.processing_error = reason
        photo.updated_at = utc_now()
        session.add(photo)
    session.flush()

    for group in session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project_id)).all():
        session.delete(group)

    project = session.get(Project, project_id)
    if project is not None:
        project.processed_images = 0
        project.updated_at = utc_now()
        session.add(project)


def _reset_project_after_processing_failure(session: Session, project_id: str, reason: str) -> None:
    reset_project_after_processing_failure(session, project_id, reason)


def _group_score_summary(group_type: str, ranked: list[RankedPhoto]) -> str:
    recommendation_counts = {"Pick": 0, "Maybe": 0, "Reject": 0, "Unreviewed": 0}
    for item in ranked:
        recommendation_counts[item.recommendation] = recommendation_counts.get(item.recommendation, 0) + 1

    best_score = ranked[0].score if ranked else 0.0
    score_gap = round(best_score - ranked[1].score, 4) if len(ranked) > 1 else 0.0
    if len(ranked) <= 1 or group_type == "single":
        confidence = "low"
        explanation = "Low confidence because this group has no similar alternative to compare."
    elif score_gap >= 0.15:
        confidence = "high"
        explanation = f"High confidence because the top photo leads the next candidate by {score_gap:.2f}."
    elif score_gap >= 0.05:
        confidence = "medium"
        explanation = f"Medium confidence because the top photo leads the next candidate by {score_gap:.2f}."
    else:
        confidence = "low"
        explanation = f"Low confidence because the top candidates are separated by only {score_gap:.2f}."

    summary = {
        "best_score": round(best_score, 4),
        "confidence": confidence,
        "explanation": explanation,
        "recommendation_counts": recommendation_counts,
        "score_gap": score_gap,
        "top_photo_id": ranked[0].photo_id if ranked else None,
    }
    return json.dumps(summary, sort_keys=True)


def _project_processing_is_current(session: Session, project: Project, photos: list[Photo]) -> bool:
    if not photos or project.processed_images != len(photos) or project.total_images != len(photos):
        return False
    if any(photo.processing_state != "processed" or photo.processing_error or not photo.group_id for photo in photos):
        return False
    if any(_missing_derivative_paths(photo) for photo in photos):
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
    job.worker_id = None
    job.heartbeat_at = None
    job.completed_at = now
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def processing_job_is_stale(job: ProcessingJob, now=None) -> bool:
    return job.job_type == "processing" and job_is_stale(job, now)


def fail_stale_processing_job(session: Session, job: ProcessingJob) -> ProcessingJob:
    from app.services.jobs import fail_stale_job

    return fail_stale_job(session, job)


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


def request_processing_job_cancellation(session: Session, job: ProcessingJob) -> ProcessingJob:
    if job.job_type != "processing":
        return job
    if job.status == "interrupted":
        now = utc_now()
        reset_project_after_processing_failure(
            session,
            job.project_id,
            "Processing job was cancelled while waiting for local reclaim",
        )
        job.status = "cancelled"
        job.current_step = "cancelled"
        job.cancellation_requested = True
        job.cancelled_at = now
        job.completed_at = now
        job.interrupted_at = None
        job.worker_id = None
        job.heartbeat_at = None
        job.updated_at = now
        session.add(job)
        session.commit()
        session.refresh(job)
        return job
    if job.status in TERMINAL_JOB_STATUSES:
        return job
    now = utc_now()
    job.cancellation_requested = True
    job.current_step = "cancellation_requested"
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def prepare_interrupted_processing_jobs_for_reclaim(
    session: Session,
    *,
    limit: int = 1,
    worker_id: str | None = None,
) -> list[str]:
    """Clear partial groups and reactivate interrupted processing jobs (Phase 6 / J6.04).

    Each candidate row is claimed with a single atomic ``UPDATE ... WHERE status =
    'interrupted'`` before it is mutated, so a concurrent reclaimer (e.g. the API's
    lifespan reclaim thread racing a separately running ``python -m app.worker``) cannot
    also reactivate the same row (#104 fix 2). A job whose cancel was requested before
    the restart is finalized as cancelled rather than re-queued (J7.03).

    A row can also be left ``interrupted`` with a foreign, abandoned ``worker_id`` if a
    previous reclaimer crashed after claiming it but before finishing the reclaim; such a
    row is released (via ``release_stale_interrupted_lease``) once its lease heartbeat has
    expired, so a later reclaimer with a new worker id is not permanently locked out
    (#104 residual fix 1).
    """
    jobs = list(
        session.exec(
            select(ProcessingJob)
            .where(ProcessingJob.job_type == "processing")
            .where(ProcessingJob.status == "interrupted")
            .order_by(ProcessingJob.interrupted_at, ProcessingJob.created_at, ProcessingJob.id)
        ).all()
    )
    prepared: list[str] = []
    for job in jobs:
        if len(prepared) >= limit:
            break
        job = release_stale_interrupted_lease(session, job)
        owner = worker_id or f"reclaim-{uuid.uuid4().hex[:12]}"
        if not claim_job_atomic(
            session,
            job.id,
            worker_id=owner,
            from_statuses=frozenset({"interrupted"}),
        ):
            # Already claimed by a concurrent reclaimer between our read and this write.
            continue
        session.refresh(job)

        if job.cancellation_requested:
            _finalize_cancelled_processing_job(session, job)
            continue

        reason = "Interrupted processing was reclaimed after API restart; rebuilding local groups"
        reset_project_after_processing_failure(session, job.project_id, reason)
        now = utc_now()
        job.status = "queued"
        job.current_step = "reclaim_queued"
        job.error_message = None
        job.interrupted_at = None
        job.completed_at = None
        job.reclaim_count = int(job.reclaim_count or 0) + 1
        job.processed_items = 0
        job.failed_items = 0
        job.progress_percent = 0.0
        job.updated_at = now
        session.add(job)
        session.commit()
        session.refresh(job)
        prepared.append(job.id)
    return prepared


def run_processing_job(job_id: str, *, worker_id: str | None = None) -> None:
    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        if job is None:
            return
        # Atomic claim: refuse to run if another executor (e.g. a separately running
        # ``python -m app.worker`` racing the API's own reclaim thread or BackgroundTasks)
        # already holds this job's lease, so the same job never runs twice at once
        # (#104 fix 2). Callers that already claimed this job (prepare_*_for_reclaim,
        # the worker's own queue claim) pass their existing ``worker_id`` explicitly;
        # do not fall back to the job's current lease owner, or an unrelated caller could
        # silently "inherit" someone else's foreign lease just by reading the row.
        owner = worker_id or f"job-runner-{uuid.uuid4().hex[:12]}"
        if not claim_job_atomic(
            session,
            job_id,
            worker_id=owner,
            from_statuses=frozenset({"queued", "running"}),
        ):
            return
        session.refresh(job)
        if _processing_job_cancellation_requested(session, job):
            _finalize_cancelled_processing_job(session, job)
            return
        try:
            project = session.get(Project, job.project_id)
            if project is None:
                mark_job_failed(session, job, "Project not found")
                return
            process_project(session, project, job)
        except Exception as error:
            session.rollback()
            job = session.get(ProcessingJob, job_id)
            if job is None or job.status in TERMINAL_JOB_STATUSES:
                return
            reason = f"Processing worker crashed: {error}"
            reset_project_after_processing_failure(session, job.project_id, reason)
            mark_job_failed(session, job, reason)


def process_project(session: Session, project: Project, job: ProcessingJob | None = None) -> ProcessingJob:
    photos = list(session.exec(select(Photo).where(Photo.project_id == project.id)).all())
    if job is None:
        job = create_processing_job(session, project)

    job.status = "running"
    job.current_step = "starting"
    job.total_items = len(photos)
    job.processed_items = 0
    job.failed_items = 0
    job.progress_percent = progress_percent(0, 0, len(photos))
    job.error_message = None
    job.started_at = utc_now()
    job.completed_at = None
    job.updated_at = utc_now()
    session.add(job)
    session.commit()
    session.refresh(job)

    if _processing_job_cancellation_requested(session, job):
        return _finalize_cancelled_processing_job(session, job)

    if _project_processing_is_current(session, project, photos):
        return _complete_unchanged_job(session, job, len(photos))

    try:
        existing_groups = {
            group.id: group
            for group in session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project.id)).all()
        }
        preserved_photos = [
            photo
            for photo in photos
            if photo.processing_state == "processed"
            and photo.group_id
            and photo.group_id in existing_groups
            and not photo.processing_error
            and not _missing_derivative_paths(photo)
        ]
        preserved_ids = {photo.id for photo in preserved_photos}
        preserved_group_ids = {photo.group_id for photo in preserved_photos if photo.group_id}

        if not _save_job(session, job, "clearing stale groups", 0):
            return job
        work_photos = [photo for photo in photos if photo.id not in preserved_ids]
        for photo in work_photos:
            photo.group_id = None
            photo.processing_state = "processing"
            photo.processing_error = None
            session.add(photo)
        session.flush()
        for existing in list(existing_groups.values()):
            if existing.id not in preserved_group_ids:
                session.delete(existing)
        session.commit()

        if not _save_job(session, job, "validating generated files", len(preserved_photos)):
            return job
        derivative_failed_photos = []
        derivative_failed_ids = set()
        for index, photo in enumerate(work_photos, start=1):
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
            # Keep the lease fresh every few photos so this loop cannot outlast
            # JOB_LEASE_STALE_AFTER without a heartbeat, even when most/all of
            # work_photos need regeneration (Bugbot residual fix after #104 / 6b580a8).
            if index % DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL == 0:
                refresh_job_lease_heartbeat(session, job)
                session.commit()
                if _processing_job_cancellation_requested(session, job):
                    return _finalize_cancelled_processing_job(session, job)
        refresh_job_lease_heartbeat(session, job)
        session.commit()
        if _processing_job_cancellation_requested(session, job):
            return _finalize_cancelled_processing_job(session, job)

        if not _save_job(
            session,
            job,
            "validating similarity data",
            len(preserved_photos),
            len(derivative_failed_photos),
        ):
            return job
        candidate_photos = [photo for photo in work_photos if photo.id not in derivative_failed_ids]
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

        if not _save_job(session, job, "grouping photos", len(preserved_photos), len(failed_photos)):
            return job
        failed_photo_ids = {failed.id for failed in failed_photos}
        photo_map = {photo.id: photo for photo in candidate_photos if photo.id not in failed_photo_ids}
        # group_similar_photos is a single CPU-bound call over the whole batch with no
        # per-item progress callback; on large projects it can run past the lease
        # staleness window with no intervening save, so a concurrent stale sweep could
        # fail_stale this job out from under a worker that is still actively running.
        # Refresh the lease immediately before and after the call instead of relying on
        # the next _save_job, which only fires once grouping has already finished
        # (#104 residual fix 2).
        refresh_job_lease_heartbeat(session, job)
        session.commit()
        if _processing_job_cancellation_requested(session, job):
            return _finalize_cancelled_processing_job(session, job)
        grouped_photos = group_similar_photos(group_inputs)
        refresh_job_lease_heartbeat(session, job)
        session.commit()
        if _processing_job_cancellation_requested(session, job):
            return _finalize_cancelled_processing_job(session, job)
        next_sequence = max(
            (group.sequence for group in existing_groups.values() if group.id in preserved_group_ids),
            default=0,
        )

        for index, grouped in enumerate(grouped_photos, start=1):
            if not _save_job(
                session,
                job,
                f"ranking group {index} of {len(grouped_photos)}",
                job.processed_items,
            ):
                return job
            next_sequence += 1
            group = PhotoGroup(
                project_id=project.id,
                group_type=grouped.group_type,
                sequence=next_sequence,
                photo_count=len(grouped.photo_ids),
            )
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
            group.score_summary = _group_score_summary(grouped.group_type, ranked)
            for item in ranked:
                photo = photo_map[item.photo_id]
                photo.ai_recommendation = item.recommendation
                photo.recommendation_explanation = item.explanation
                photo.overall_score = item.score
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
            if _processing_job_cancellation_requested(session, job):
                return _finalize_cancelled_processing_job(session, job)

        job.status = "complete"
        job.current_step = "complete"
        job.processed_items = len(preserved_ids) + len(group_inputs)
        job.failed_items = len(failed_photos)
        job.progress_percent = 100.0
        if failed_photos:
            job.error_message = _failed_photo_count_message(len(failed_photos))
        job.worker_id = None
        job.heartbeat_at = None
        job.completed_at = utc_now()
        project.processed_images = len(preserved_ids) + len(group_inputs)
        project.last_processed_at = job.completed_at
        project.updated_at = utc_now()
        session.add(project)
    except Exception as error:
        session.rollback()
        failure_reason = str(error)
        reset_project_after_processing_failure(session, project.id, failure_reason)
        job.status = "failed"
        job.current_step = "failed"
        job.error_message = failure_reason
        job.failed_items = max(0, job.total_items - job.processed_items) if job.total_items else 1
        job.progress_percent = progress_percent(job.processed_items, job.failed_items, job.total_items)
        job.worker_id = None
        job.heartbeat_at = None
        job.completed_at = utc_now()

    job.updated_at = utc_now()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def project_export_root(project: Project) -> Path:
    try:
        project_root = Path(project.root_path).resolve(strict=True)
    except FileNotFoundError as error:
        raise ValueError("Project root path is unavailable") from error

    export_root = project_root / "exports"
    export_root.mkdir(parents=True, exist_ok=True)
    resolved_export_root = export_root.resolve(strict=True)
    if not resolved_export_root.is_dir() or not resolved_export_root.is_relative_to(project_root):
        raise ValueError("Project export directory must stay inside the project root")

    for child in ("csv", "zip", "folders"):
        child_root = export_root / child
        child_root.mkdir(parents=True, exist_ok=True)
        resolved_child_root = child_root.resolve(strict=True)
        if not resolved_child_root.is_dir() or not resolved_child_root.is_relative_to(resolved_export_root):
            raise ValueError("Project export directory must stay inside the project root")

    return resolved_export_root
