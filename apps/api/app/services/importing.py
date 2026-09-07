from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from PIL import AvifImagePlugin, ExifTags, Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func
from sqlmodel import Session, select

from app.ai.embeddings import image_embedding, perceptual_hash
from app.core.app_settings import load_import_workers
from app.core.local_paths import normalize_user_path
from app.db.session import get_engine
from app.image.heif_support import ensure_heif_opener
from app.image.raw_preview import RAW_NO_PREVIEW_REASON, RawPreviewError, extract_raw_preview_image
from app.image.scoring import compute_quality_scores_for_image
from app.models.entities import Photo, PhotoGroup, ProcessingJob, Project, utc_now
from app.services.jobs import (
    TERMINAL_JOB_STATUSES,
    apply_job_checkpoint,
    as_utc,
    claim_job_atomic,
    job_is_stale,
    mark_job_failed,
    progress_percent,
    refresh_job_lease_heartbeat,
    release_stale_interrupted_lease,
)

RAW_EXTENSIONS = {".arw", ".cr3", ".dng", ".nef"}
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif"} | RAW_EXTENSIONS
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
CONTENT_HASH_CHUNK_SIZE = 1024 * 1024
IMPORT_COPY_CHUNK_SIZE = 1024 * 1024
THUMBNAIL_LONG_EDGE = 320
PREVIEW_LONG_EDGE = 1800
THUMBNAIL_WEBP_QUALITY = 82
PREVIEW_WEBP_QUALITY = 88
PREVIEW_WEBP_METHOD = 2
DERIVATIVE_RESAMPLE = Image.Resampling.BICUBIC
DERIVATIVE_REDUCING_GAP = 2.0
IMPORT_JOB_UPDATE_MIN_SECONDS = 0.75
IMPORT_MAX_FILES_PER_REQUEST = 100
PATH_IMPORT_MAX_INPUT_ENTRIES = 5000
PATH_IMPORT_MAX_EXPANDED_FILES = 20000

ensure_heif_opener()
if not AvifImagePlugin.SUPPORTED:
    raise RuntimeError("Pillow AVIF support is required")

ImportProgressCallback = Callable[[str], None]


@dataclass
class ImportStageTiming:
    calls: int = 0
    seconds: float = 0.0


@dataclass
class ImportTimingCollector:
    stages: dict[str, ImportStageTiming] = field(default_factory=dict)

    def record(self, stage: str, seconds: float) -> None:
        current = self.stages.setdefault(stage, ImportStageTiming())
        current.calls += 1
        current.seconds += seconds

    def summary(self) -> dict[str, dict[str, int | float]]:
        return {
            stage: {"calls": timing.calls, "seconds": round(timing.seconds, 6)} for stage, timing in self.stages.items()
        }


@dataclass
class ImportRegistration:
    photo: Photo
    requires_derivatives: bool
    is_new: bool


@dataclass
class ExpandedImportPaths:
    files: list[Path]
    skipped: list[dict[str, str]]


def _path_is_under(path: Path, root: Path) -> bool:
    try:
        return path.resolve().is_relative_to(root.resolve())
    except (OSError, ValueError):
        return False


def expand_import_paths(paths: list[str], project_root: Path) -> ExpandedImportPaths:
    if not paths:
        raise ValueError("At least one path is required")
    if len(paths) > PATH_IMPORT_MAX_INPUT_ENTRIES:
        raise ValueError(
            f"Too many input paths ({len(paths)}). At most {PATH_IMPORT_MAX_INPUT_ENTRIES} entries are allowed."
        )

    resolved_project_root = Path(project_root).resolve()
    collected: list[Path] = []
    skipped: list[dict[str, str]] = []
    seen: set[Path] = set()

    def consider_file(path: Path, *, walked_root: Path | None = None) -> None:
        try:
            resolved = path.resolve()
        except OSError as error:
            raise ValueError(f"Path could not be resolved: {path}") from error
        if walked_root is not None and not _path_is_under(resolved, walked_root):
            return
        try:
            mode = resolved.stat().st_mode
        except FileNotFoundError:
            raise ValueError(f"Path does not exist: {path}") from None
        if not stat.S_ISREG(mode):
            return
        if _path_is_under(resolved, resolved_project_root):
            skipped.append({"filename": resolved.name, "reason": "Source is inside the project folder"})
            return
        if resolved in seen:
            return
        seen.add(resolved)
        if not is_supported_image(resolved.name):
            skipped.append({"filename": resolved.name, "reason": unsupported_image_reason(resolved.name)})
            return
        if resolved.suffix.lower() in RAW_EXTENSIONS:
            try:
                preview = extract_raw_preview_image(resolved)
            except RawPreviewError:
                skipped.append({"filename": resolved.name, "reason": RAW_NO_PREVIEW_REASON})
                return
            preview.close()
        collected.append(resolved)
        if len(collected) > PATH_IMPORT_MAX_EXPANDED_FILES:
            raise ValueError(f"Expansion exceeded {PATH_IMPORT_MAX_EXPANDED_FILES} files")

    for raw in paths:
        candidate = Path(normalize_user_path(raw))
        if not candidate.is_absolute():
            raise ValueError(f"Path must be absolute: {raw}")
        if not candidate.exists():
            raise ValueError(f"Path does not exist: {raw}")
        if candidate.is_dir():
            walked_root = candidate.resolve()
            for dirpath, _dirnames, filenames in os.walk(candidate, followlinks=False):
                current = Path(dirpath)
                for name in filenames:
                    consider_file(current / name, walked_root=walked_root)
        else:
            consider_file(candidate)

    collected.sort(key=lambda item: str(item))
    return ExpandedImportPaths(files=collected, skipped=skipped)


def _skipped_files_message(skipped: list[dict[str, str]]) -> str | None:
    if not skipped:
        return None
    noun = "file" if len(skipped) == 1 else "files"
    names = ", ".join(item["filename"] for item in skipped[:5])
    suffix = "" if len(skipped) <= 5 else f", and {len(skipped) - 5} more"
    return f"{len(skipped)} {noun} skipped: {names}{suffix}"


def create_import_job(session: Session, project: Project, total_items: int) -> ProcessingJob:
    now = utc_now()
    job = ProcessingJob(
        project_id=project.id,
        job_type="import",
        status="running",
        current_step="receive_files",
        total_items=total_items,
        processed_items=0,
        failed_items=0,
        progress_percent=progress_percent(0, 0, total_items),
        started_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def create_import_retry_job(session: Session, project: Project, photo_ids: list[str]) -> ProcessingJob:
    now = utc_now()
    job = ProcessingJob(
        project_id=project.id,
        job_type="import",
        status="running",
        current_step="retry_queued",
        total_items=len(photo_ids),
        processed_items=0,
        failed_items=0,
        progress_percent=progress_percent(0, 0, len(photo_ids)),
        started_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _finalize_cancelled_reclaim_import(session: Session, job: ProcessingJob) -> ProcessingJob:
    """Finalize an interrupted import as cancelled instead of resuming it (#104 fix 3).

    A pending cancel intent must win over reclaim: if cancellation was requested before
    the API restarted, resuming the job would silently ignore the user's cancel request.
    """
    now = utc_now()
    job.status = "cancelled"
    job.current_step = "cancelled"
    job.error_message = "Import job was cancelled before it could be reclaimed"
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


def prepare_interrupted_import_jobs_for_reclaim(
    session: Session,
    *,
    limit: int = 1,
    worker_id: str | None = None,
) -> list[tuple[str, list[str]]]:
    """Reactivate interrupted import jobs for in-process reclaim (Phase 6 / J6.03).

    Returns ``(job_id, photo_ids)`` pairs ready for ``run_import_derivative_job``.
    At most ``limit`` jobs are prepared so only one reclaim runs at a time by default.

    Each candidate row is claimed with a single atomic ``UPDATE ... WHERE status =
    'interrupted'`` before it is mutated, so a concurrent reclaimer (e.g. the API's
    lifespan reclaim thread racing a separately running ``python -m app.worker``) cannot
    also reactivate the same row (#104 fix 2). A job whose cancel was requested before
    the restart is finalized as cancelled rather than resumed (#104 fix 3).

    A row can also be left ``interrupted`` with a foreign, abandoned ``worker_id`` if a
    previous reclaimer crashed after claiming it but before finishing the reclaim; such a
    row is released (via ``release_stale_interrupted_lease``) once its lease heartbeat has
    expired, so a later reclaimer with a new worker id is not permanently locked out
    (#104 residual fix 1).
    """
    jobs = list(
        session.exec(
            select(ProcessingJob)
            .where(ProcessingJob.job_type == "import")
            .where(ProcessingJob.status == "interrupted")
            .order_by(ProcessingJob.interrupted_at, ProcessingJob.created_at, ProcessingJob.id)
        ).all()
    )
    prepared: list[tuple[str, list[str]]] = []
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
            _finalize_cancelled_reclaim_import(session, job)
            continue

        photos = list(
            session.exec(
                select(Photo).where(Photo.project_id == job.project_id).order_by(Photo.created_at, Photo.id)
            ).all()
        )
        photo_ids = [photo.id for photo in photos if photo_needs_import_retry(photo)]
        now = utc_now()
        job.status = "running"
        job.current_step = "reclaim_derivative_generation"
        job.error_message = None
        job.interrupted_at = None
        job.completed_at = None
        job.reclaim_count = int(job.reclaim_count or 0) + 1
        job.total_items = len(photo_ids)
        job.processed_items = 0
        job.failed_items = 0
        job.progress_percent = progress_percent(0, 0, len(photo_ids))
        job.started_at = job.started_at or now
        job.updated_at = now
        session.add(job)
        session.commit()
        session.refresh(job)
        prepared.append((job.id, photo_ids))
    return prepared


def update_import_job(
    session: Session,
    job: ProcessingJob,
    current_step: str,
    processed_items: int | None = None,
    failed_items: int | None = None,
    force: bool = False,
) -> None:
    now = utc_now()
    should_commit = force or (now - as_utc(job.updated_at)).total_seconds() >= IMPORT_JOB_UPDATE_MIN_SECONDS
    job.current_step = current_step
    if processed_items is not None:
        job.processed_items = processed_items
    if failed_items is not None:
        job.failed_items = failed_items
    job.progress_percent = progress_percent(job.processed_items, job.failed_items, job.total_items)
    job.updated_at = now
    # Keep a held lease fresh so long imports do not look stale mid-flight (#104 fix 1).
    refresh_job_lease_heartbeat(session, job)
    session.add(job)
    if should_commit:
        session.commit()
        session.refresh(job)


def complete_import_job(
    session: Session,
    job: ProcessingJob,
    imported_count: int,
    skipped: list[dict[str, str]],
) -> ProcessingJob:
    now = utc_now()
    skipped_count = len(skipped)
    if imported_count:
        job.status = "complete_with_errors" if skipped_count else "complete"
        job.current_step = "complete"
    else:
        job.status = "failed"
        job.current_step = "failed"
    job.processed_items = imported_count
    job.failed_items = skipped_count
    job.progress_percent = 100.0
    job.error_message = _skipped_files_message(skipped)
    job.worker_id = None
    job.heartbeat_at = None
    job.completed_at = now
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def import_job_is_stale(job: ProcessingJob, now: datetime | None = None) -> bool:
    return job.job_type == "import" and job_is_stale(job, now)


def fail_stale_import_job(session: Session, job: ProcessingJob) -> ProcessingJob:
    from app.services.jobs import fail_stale_job

    return fail_stale_job(session, job)


def _cancel_interrupted_import_job(session: Session, job: ProcessingJob) -> ProcessingJob:
    """Cancel an interrupted import immediately (#104 fix 4).

    ``interrupted`` sits in ``TERMINAL_JOB_STATUSES`` so stale sweeps and staleness
    checks leave it alone, but that previously made cancellation a silent no-op that
    still returned success without persisting anything. There is no in-flight worker to
    cooperatively honor a cancel flag here, so finalize the job directly instead of
    waiting for a reclaim pass that may never run.
    """
    now = utc_now()
    job.status = "cancelled"
    job.current_step = "cancelled"
    job.cancellation_requested = True
    job.cancelled_at = now
    job.completed_at = now
    job.interrupted_at = None
    job.error_message = "Import job was cancelled while waiting for local reclaim"
    job.worker_id = None
    job.heartbeat_at = None
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def request_import_job_cancellation(session: Session, job: ProcessingJob) -> ProcessingJob:
    if job.job_type != "import":
        return job
    if job.status == "interrupted":
        return _cancel_interrupted_import_job(session, job)
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


@contextmanager
def import_timing_stage(timing: ImportTimingCollector | None, stage: str) -> Iterator[None]:
    if timing is None:
        yield
        return

    started = time.perf_counter()
    try:
        yield
    finally:
        timing.record(stage, time.perf_counter() - started)


def is_supported_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def unsupported_image_reason(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension in RAW_EXTENSIONS:
        return RAW_NO_PREVIEW_REASON
    return "Only JPEG, PNG, and WebP files are supported"


def _open_imported_image(path: Path) -> Image.Image:
    if path.suffix.lower() in RAW_EXTENSIONS:
        return extract_raw_preview_image(path)
    return Image.open(path)


def _unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / Path(filename).name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    index = 1
    while True:
        next_candidate = directory / f"{stem}-{index}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        index += 1


def _reserve_unique_path(directory: Path, filename: str) -> Path:
    """Atomically reserve a destination path with O_EXCL to avoid overwrite races."""
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    stem = Path(safe_name).stem
    suffix = Path(safe_name).suffix
    index = 0
    while True:
        candidate = directory / safe_name if index == 0 else directory / f"{stem}-{index}{suffix}"
        try:
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return candidate
        except FileExistsError:
            index += 1


def _project_photo_count(session: Session, project_id: str) -> int:
    return int(session.exec(select(func.count()).select_from(Photo).where(Photo.project_id == project_id)).one())


def _sync_project_total_images(session: Session, project: Project) -> None:
    project.total_images = _project_photo_count(session, project.id)
    project.updated_at = utc_now()
    session.add(project)


def _parse_capture_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        return datetime.strptime(value, EXIF_DATETIME_FORMAT)
    except ValueError:
        return None


def _rational_parts(value: object) -> tuple[float, float] | None:
    if isinstance(value, tuple) and len(value) == 2:
        numerator, denominator = value
        if isinstance(numerator, int | float) and isinstance(denominator, int | float) and denominator:
            return float(numerator), float(denominator)

    numerator = getattr(value, "numerator", None)
    denominator = getattr(value, "denominator", None)
    if isinstance(numerator, int | float) and isinstance(denominator, int | float) and denominator:
        return float(numerator), float(denominator)

    return None


def _format_exif_number(value: object, prefer_fraction: bool = False) -> str | None:
    if value is None:
        return None

    parts = _rational_parts(value)
    if parts is not None:
        numerator, denominator = parts
        if prefer_fraction:
            return f"{int(numerator)}/{int(denominator)}"
        number = numerator / denominator
        if number.is_integer():
            return str(int(number))
        return f"{number:.3f}".rstrip("0").rstrip(".")

    return str(value)


def _extract_metadata(image: Image.Image) -> dict:
    raw_exif = image.getexif()
    if not raw_exif:
        return {}

    named = {ExifTags.TAGS.get(key, key): value for key, value in raw_exif.items()}
    capture_time = _parse_capture_time(named.get("DateTimeOriginal")) or _parse_capture_time(named.get("DateTime"))
    return {
        "capture_time": capture_time,
        "camera_model": named.get("Model"),
        "lens_model": named.get("LensModel"),
        "focal_length": _format_exif_number(named.get("FocalLength")),
        "aperture": _format_exif_number(named.get("FNumber")),
        "shutter_speed": _format_exif_number(named.get("ExposureTime"), prefer_fraction=True),
        "iso": int(named["ISOSpeedRatings"]) if isinstance(named.get("ISOSpeedRatings"), int) else None,
    }


def _save_derivatives(
    project_root: Path,
    source: Path,
    image: Image.Image,
    timing: ImportTimingCollector | None = None,
    progress_callback: ImportProgressCallback | None = None,
) -> tuple[Path, Path]:
    thumbnail_dir = project_root / "thumbnails"
    preview_dir = project_root / "previews"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    thumbnail_path = _unique_path(thumbnail_dir, f"{source.stem}.webp")
    preview_path = _unique_path(preview_dir, f"{source.stem}.webp")

    if progress_callback:
        progress_callback("thumbnail_generation")
    with import_timing_stage(timing, "thumbnail_generation"):
        thumb = _make_derivative_image(image, THUMBNAIL_LONG_EDGE)
        thumb.save(thumbnail_path, "WEBP", quality=THUMBNAIL_WEBP_QUALITY)

    if progress_callback:
        progress_callback("preview_generation")
    with import_timing_stage(timing, "preview_generation"):
        preview = _make_derivative_image(image, PREVIEW_LONG_EDGE)
        preview.save(preview_path, "WEBP", quality=PREVIEW_WEBP_QUALITY, method=PREVIEW_WEBP_METHOD)
    return thumbnail_path, preview_path


def _make_derivative_image(image: Image.Image, max_long_edge: int) -> Image.Image:
    target_size = _bounded_derivative_size(image.width, image.height, max_long_edge)
    if target_size == image.size:
        return image.copy()
    return image.resize(
        target_size,
        resample=DERIVATIVE_RESAMPLE,
        reducing_gap=DERIVATIVE_REDUCING_GAP,
    )


def _bounded_derivative_size(width: int, height: int, max_long_edge: int) -> tuple[int, int]:
    requested_edge = math.floor(max_long_edge)
    if requested_edge <= 0:
        raise ValueError("max_long_edge must be greater than zero")
    if requested_edge >= width and requested_edge >= height:
        return width, height

    aspect = width / height
    target_width = requested_edge
    target_height = requested_edge

    def round_aspect(number: float, key) -> int:
        return max(min(math.floor(number), math.ceil(number), key=key), 1)

    if target_width / target_height >= aspect:
        target_width = round_aspect(
            target_height * aspect,
            key=lambda value: abs(aspect - value / target_height),
        )
    else:
        target_height = round_aspect(
            target_width / aspect,
            key=lambda value: 0 if value == 0 else abs(aspect - target_width / value),
        )
    return target_width, target_height


def ensure_photo_derivatives(project: Project, photo: Photo) -> list[str]:
    missing = []
    if not photo.thumbnail_path or not Path(photo.thumbnail_path).is_file():
        missing.append("thumbnail")
    if not photo.preview_path or not Path(photo.preview_path).is_file():
        missing.append("preview")
    if not missing:
        return []

    source_path = Path(photo.project_copy_path or photo.original_path)
    if not source_path.is_file():
        raise ValueError("Copied original file is missing")

    project_root = Path(project.root_path)
    with _open_imported_image(source_path) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        regenerated_thumbnail, regenerated_preview = _save_derivatives(project_root, source_path, image)

    if "thumbnail" in missing:
        photo.thumbnail_path = str(regenerated_thumbnail)
    else:
        regenerated_thumbnail.unlink(missing_ok=True)

    if "preview" in missing:
        photo.preview_path = str(regenerated_preview)
    else:
        regenerated_preview.unlink(missing_ok=True)

    photo.updated_at = utc_now()
    return missing


def _cleanup_paths(*paths: Path | None) -> None:
    for path in paths:
        if path is not None:
            path.unlink(missing_ok=True)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CONTENT_HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_file_to_path(file: BinaryIO, path: Path) -> None:
    with path.open("wb") as handle:
        while chunk := file.read(IMPORT_COPY_CHUNK_SIZE):
            handle.write(chunk)


def _existing_photo_for_content_hash(
    session: Session,
    project_id: str,
    content_hash: str,
    filename: str,
) -> Photo | None:
    candidates = session.exec(
        select(Photo)
        .where(Photo.project_id == project_id)
        .where(Photo.source_identity == f"sha256:{content_hash}")
        .order_by(Photo.created_at, Photo.id)
    ).all()
    for photo in candidates:
        if photo.filename == filename:
            return photo
    return None


def _photo_derivatives_exist(photo: Photo) -> bool:
    return bool(
        photo.thumbnail_path
        and Path(photo.thumbnail_path).is_file()
        and photo.preview_path
        and Path(photo.preview_path).is_file()
    )


def photo_needs_import_retry(photo: Photo) -> bool:
    return photo.processing_state in {"processing", "failed"} or not _photo_derivatives_exist(photo)


def invalidate_project_processing(
    session: Session,
    project: Project,
    *,
    touched_photo_ids: list[str] | None = None,
) -> None:
    """Invalidate processing results.

    When ``touched_photo_ids`` is provided, only those photos lose grouping /
    recommendations so incremental imports keep unaffected groups intact.
    """
    if touched_photo_ids is None:
        photos = list(session.exec(select(Photo).where(Photo.project_id == project.id)).all())
    else:
        touched = set(touched_photo_ids)
        photos = [
            photo
            for photo in session.exec(select(Photo).where(Photo.project_id == project.id)).all()
            if photo.id in touched
        ]

    for photo in photos:
        photo.group_id = None
        photo.ai_recommendation = "Unreviewed"
        photo.recommendation_explanation = "Processing should be run again after the latest import."
        photo.updated_at = utc_now()
        session.add(photo)
    session.flush()

    if touched_photo_ids is None:
        for group in session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project.id)).all():
            session.delete(group)
    else:
        # Drop groups that no longer have any members after the scoped clear.
        remaining_groups = {
            photo.group_id
            for photo in session.exec(select(Photo).where(Photo.project_id == project.id)).all()
            if photo.group_id
        }
        for group in session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project.id)).all():
            if group.id not in remaining_groups:
                session.delete(group)

    project.processed_images = 0
    project.updated_at = utc_now()
    session.add(project)


def import_image_file(
    session: Session,
    project: Project,
    filename: str,
    file: BinaryIO,
    invalidate_processing: bool = True,
    timing: ImportTimingCollector | None = None,
    progress_callback: ImportProgressCallback | None = None,
) -> Photo:
    total_started = time.perf_counter()
    try:
        if progress_callback:
            progress_callback("file_validation")
        if not is_supported_image(filename):
            raise ValueError(unsupported_image_reason(filename))

        project_root = Path(project.root_path)
        safe_name = Path(filename).name
        originals_dir = project_root / "originals"
        originals_dir.mkdir(parents=True, exist_ok=True)
        source_path = _reserve_unique_path(originals_dir, safe_name)
        if progress_callback:
            progress_callback("file_copy_or_register")
        with import_timing_stage(timing, "file_copy"):
            _copy_file_to_path(file, source_path)

        if progress_callback:
            progress_callback("content_hash")
        with import_timing_stage(timing, "content_hash"):
            content_hash = _file_sha256(source_path)
        existing_photo = _existing_photo_for_content_hash(session, project.id, content_hash, safe_name)
        if existing_photo is not None and _photo_derivatives_exist(existing_photo):
            _cleanup_paths(source_path)
            return existing_photo

        thumbnail_path: Path | None = None
        preview_path: Path | None = None
        try:
            if progress_callback:
                progress_callback("image_open")
            with import_timing_stage(timing, "image_open"):
                opened_image = _open_imported_image(source_path)
            with opened_image as opened:
                if progress_callback:
                    progress_callback("metadata_extraction")
                with import_timing_stage(timing, "metadata_extraction"):
                    metadata = _extract_metadata(opened)
                if progress_callback:
                    progress_callback("image_decode")
                with import_timing_stage(timing, "image_decode"):
                    image = ImageOps.exif_transpose(opened).convert("RGB")
                width, height = image.size
                thumbnail_path, preview_path = _save_derivatives(
                    project_root,
                    source_path,
                    image,
                    timing=timing,
                    progress_callback=progress_callback,
                )
                if progress_callback:
                    progress_callback("quality_scoring")
                with import_timing_stage(timing, "quality_scoring"):
                    scores = compute_quality_scores_for_image(image)
                if progress_callback:
                    progress_callback("embedding_generation")
                with import_timing_stage(timing, "embedding_generation"):
                    embedding = image_embedding(image)
                if progress_callback:
                    progress_callback("perceptual_hash")
                with import_timing_stage(timing, "perceptual_hash"):
                    p_hash = perceptual_hash(image)
        except RawPreviewError:
            _cleanup_paths(source_path, thumbnail_path, preview_path)
            raise
        except (UnidentifiedImageError, OSError) as error:
            _cleanup_paths(source_path, thumbnail_path, preview_path)
            raise ValueError("Uploaded file could not be opened as a supported image") from error
        except Exception as error:
            _cleanup_paths(source_path, thumbnail_path, preview_path)
            raise ValueError("Uploaded image could not be processed") from error

        with import_timing_stage(timing, "file_stat"):
            source_stat = source_path.stat()

        if progress_callback:
            progress_callback("db_commit")
        with import_timing_stage(timing, "db_record_create"):
            photo = Photo(
                project_id=project.id,
                original_path=str(source_path),
                project_copy_path=str(source_path),
                source_identity=f"sha256:{content_hash}",
                filename=source_path.name,
                file_ext=source_path.suffix.lower(),
                file_size=source_stat.st_size,
                file_mtime=source_stat.st_mtime,
                content_hash=content_hash,
                width=width,
                height=height,
                thumbnail_path=str(thumbnail_path),
                preview_path=str(preview_path),
                perceptual_hash=p_hash,
                sharpness_score=scores.sharpness_score,
                blur_score=scores.blur_score,
                exposure_score=scores.exposure_score,
                contrast_score=scores.contrast_score,
                noise_score=scores.noise_score,
                face_presence=scores.face_presence,
                face_sharpness_score=scores.face_sharpness_score,
                eye_open_confidence=scores.eye_open_confidence,
                face_quality_score=scores.face_quality_score,
                aesthetic_score=scores.aesthetic_score,
                overall_score=scores.overall_score,
                embedding=json.dumps(embedding),
                **metadata,
            )
            session.add(photo)
            if invalidate_processing:
                invalidate_project_processing(session, project, touched_photo_ids=[photo.id])
            _sync_project_total_images(session, project)

        with import_timing_stage(timing, "db_commit"):
            session.commit()
            session.refresh(photo)
        return photo
    finally:
        if timing is not None:
            timing.record("import_file_total", time.perf_counter() - total_started)


def register_import_file(
    session: Session,
    project: Project,
    filename: str,
    file: BinaryIO,
    timing: ImportTimingCollector | None = None,
    progress_callback: ImportProgressCallback | None = None,
) -> ImportRegistration:
    if progress_callback:
        progress_callback("file_validation")
    if not is_supported_image(filename):
        raise ValueError(unsupported_image_reason(filename))

    project_root = Path(project.root_path)
    safe_name = Path(filename).name
    originals_dir = project_root / "originals"
    originals_dir.mkdir(parents=True, exist_ok=True)
    source_path = _reserve_unique_path(originals_dir, safe_name)
    if progress_callback:
        progress_callback("file_copy_or_register")
    with import_timing_stage(timing, "file_copy"):
        _copy_file_to_path(file, source_path)

    if Path(safe_name).suffix.lower() in RAW_EXTENSIONS:
        try:
            preview = extract_raw_preview_image(source_path)
        except RawPreviewError:
            _cleanup_paths(source_path)
            raise
        preview.close()

    if progress_callback:
        progress_callback("content_hash")
    with import_timing_stage(timing, "content_hash"):
        content_hash = _file_sha256(source_path)
    existing_photo = _existing_photo_for_content_hash(session, project.id, content_hash, safe_name)
    if existing_photo is not None and (
        _photo_derivatives_exist(existing_photo) or existing_photo.processing_state == "processing"
    ):
        _cleanup_paths(source_path)
        return ImportRegistration(photo=existing_photo, requires_derivatives=False, is_new=False)

    with import_timing_stage(timing, "file_stat"):
        source_stat = source_path.stat()

    if progress_callback:
        progress_callback("db_record_create")
    with import_timing_stage(timing, "db_record_create"):
        photo = Photo(
            project_id=project.id,
            original_path=str(source_path),
            project_copy_path=str(source_path),
            source_identity=f"sha256:{content_hash}",
            filename=source_path.name,
            file_ext=source_path.suffix.lower(),
            file_size=source_stat.st_size,
            file_mtime=source_stat.st_mtime,
            content_hash=content_hash,
            processing_state="processing",
            recommendation_explanation="Import derivatives are still being generated.",
        )
        session.add(photo)
        _sync_project_total_images(session, project)

    with import_timing_stage(timing, "db_commit"):
        session.commit()
        session.refresh(photo)
    return ImportRegistration(photo=photo, requires_derivatives=True, is_new=True)


def process_registered_import_photo(
    session: Session,
    project: Project,
    photo: Photo,
    timing: ImportTimingCollector | None = None,
    progress_callback: ImportProgressCallback | None = None,
) -> Photo:
    source_path = Path(photo.project_copy_path or photo.original_path)
    if not source_path.is_file():
        raise ValueError("Copied original file is missing")

    project_root = Path(project.root_path)
    thumbnail_path: Path | None = None
    preview_path: Path | None = None
    try:
        if progress_callback:
            progress_callback("image_open")
        with import_timing_stage(timing, "image_open"):
            opened_image = _open_imported_image(source_path)
        with opened_image as opened:
            if progress_callback:
                progress_callback("metadata_extraction")
            with import_timing_stage(timing, "metadata_extraction"):
                metadata = _extract_metadata(opened)
            if progress_callback:
                progress_callback("image_decode")
            with import_timing_stage(timing, "image_decode"):
                image = ImageOps.exif_transpose(opened).convert("RGB")
            width, height = image.size
            thumbnail_path, preview_path = _save_derivatives(
                project_root,
                source_path,
                image,
                timing=timing,
                progress_callback=progress_callback,
            )
            if progress_callback:
                progress_callback("quality_scoring")
            with import_timing_stage(timing, "quality_scoring"):
                scores = compute_quality_scores_for_image(image)
            if progress_callback:
                progress_callback("embedding_generation")
            with import_timing_stage(timing, "embedding_generation"):
                embedding = image_embedding(image)
            if progress_callback:
                progress_callback("perceptual_hash")
            with import_timing_stage(timing, "perceptual_hash"):
                p_hash = perceptual_hash(image)
    except RawPreviewError:
        _cleanup_paths(thumbnail_path, preview_path)
        raise
    except (UnidentifiedImageError, OSError) as error:
        _cleanup_paths(thumbnail_path, preview_path)
        raise ValueError("Uploaded file could not be opened as a supported image") from error
    except Exception as error:
        _cleanup_paths(thumbnail_path, preview_path)
        raise ValueError("Uploaded image could not be processed") from error

    if progress_callback:
        progress_callback("db_commit")
    with import_timing_stage(timing, "db_commit"):
        photo.width = width
        photo.height = height
        photo.thumbnail_path = str(thumbnail_path)
        photo.preview_path = str(preview_path)
        photo.perceptual_hash = p_hash
        photo.sharpness_score = scores.sharpness_score
        photo.blur_score = scores.blur_score
        photo.exposure_score = scores.exposure_score
        photo.contrast_score = scores.contrast_score
        photo.noise_score = scores.noise_score
        photo.face_presence = scores.face_presence
        photo.face_sharpness_score = scores.face_sharpness_score
        photo.eye_open_confidence = scores.eye_open_confidence
        photo.face_quality_score = scores.face_quality_score
        photo.aesthetic_score = scores.aesthetic_score
        photo.overall_score = scores.overall_score
        photo.embedding = json.dumps(embedding)
        photo.processing_state = "imported"
        photo.processing_error = None
        photo.updated_at = utc_now()
        for field_name, value in metadata.items():
            setattr(photo, field_name, value)
        session.add(photo)
        session.commit()
        session.refresh(photo)
    return photo


def _fail_import_job(session: Session, job: ProcessingJob, reason: str) -> ProcessingJob:
    return mark_job_failed(session, job, reason)


def _cancel_import_job(session: Session, job: ProcessingJob, processed_count: int, failed_count: int) -> ProcessingJob:
    now = utc_now()
    job.status = "cancelled"
    job.current_step = "cancelled"
    job.processed_items = processed_count
    job.failed_items = failed_count
    job.progress_percent = progress_percent(processed_count, failed_count, job.total_items)
    job.error_message = "Import job was cancelled by user request"
    job.cancellation_requested = True
    job.cancelled_at = now
    job.completed_at = now
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _import_job_cancellation_requested(session: Session, job: ProcessingJob) -> bool:
    session.refresh(job)
    return job.cancellation_requested and job.status not in TERMINAL_JOB_STATUSES


def _mark_import_photo_failed(session: Session, photo: Photo, reason: str) -> None:
    photo.processing_state = "failed"
    photo.processing_error = reason
    photo.recommendation_explanation = "Import derivative generation failed for this photo."
    photo.updated_at = utc_now()
    session.add(photo)
    session.commit()


def _reset_import_photos_after_crash(session: Session, photo_ids: list[str], reason: str) -> None:
    for photo_id in photo_ids:
        photo = session.get(Photo, photo_id)
        if photo is None:
            continue
        if photo.processing_state == "processing" and _photo_derivatives_exist(photo):
            photo.processing_state = "imported"
            photo.processing_error = None
            photo.recommendation_explanation = "Import derivatives are available."
            photo.updated_at = utc_now()
            session.add(photo)
            continue
        if photo.processing_state in {"processing", "imported"} and not _photo_derivatives_exist(photo):
            photo.processing_state = "failed"
            photo.processing_error = reason
            photo.recommendation_explanation = (
                "Import derivative generation was interrupted. Retry the import job to regenerate local derived files."
            )
            photo.updated_at = utc_now()
            session.add(photo)
    session.commit()


def reset_import_photos_after_interrupt(session: Session, project_id: str, reason: str) -> None:
    photo_ids = [photo.id for photo in session.exec(select(Photo).where(Photo.project_id == project_id)).all()]
    _reset_import_photos_after_crash(session, photo_ids, reason)


@dataclass(frozen=True, slots=True)
class _ImportDerivativeTaskResult:
    index: int
    photo_id: str
    kind: str
    filename: str | None = None
    reason: str | None = None


def _run_one_import_derivative_task(project_id: str, photo_id: str, index: int) -> _ImportDerivativeTaskResult:
    with Session(get_engine()) as session:
        photo = session.get(Photo, photo_id)
        project = session.get(Project, project_id)
        if photo is None or project is None or photo.project_id != project.id:
            return _ImportDerivativeTaskResult(index=index, photo_id=photo_id, kind="missing")
        if _photo_derivatives_exist(photo):
            photo.processing_state = "imported"
            photo.processing_error = None
            photo.recommendation_explanation = "Import derivatives are available."
            photo.updated_at = utc_now()
            session.add(photo)
            session.commit()
            return _ImportDerivativeTaskResult(index=index, photo_id=photo.id, kind="already")
        try:
            process_registered_import_photo(session, project, photo)
            return _ImportDerivativeTaskResult(index=index, photo_id=photo.id, kind="processed")
        except ValueError as error:
            _mark_import_photo_failed(session, photo, str(error))
            return _ImportDerivativeTaskResult(
                index=index,
                photo_id=photo.id,
                kind="failed",
                filename=photo.filename,
                reason=str(error),
            )


def _run_import_derivatives_parallel(
    session: Session,
    job: ProcessingJob,
    project: Project,
    photo_ids: list[str],
    skipped: list[dict[str, str]],
    processed_count: int,
    failed_count: int,
    worker_count: int,
) -> None:
    job_lock = threading.Lock()
    total = len(photo_ids)
    remaining = list(enumerate(photo_ids, start=1))
    next_index = 0
    cancelled = False

    def cancel_requested() -> bool:
        with job_lock:
            return _import_job_cancellation_requested(session, job)

    def record_progress(step: str, processed: int, failed: int) -> None:
        with job_lock:
            update_import_job(session, job, step, processed, failed, force=True)

    def apply_checkpoint(photo_id: str) -> None:
        with job_lock:
            apply_job_checkpoint(session, job, photo_id=photo_id, stage="derivative_generation")

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        in_flight: set[Future[_ImportDerivativeTaskResult]] = set()

        def submit_available() -> None:
            nonlocal next_index
            while (not cancelled) and next_index < len(remaining) and len(in_flight) < worker_count:
                index, photo_id = remaining[next_index]
                next_index += 1
                in_flight.add(executor.submit(_run_one_import_derivative_task, project.id, photo_id, index))

        submit_available()
        while in_flight:
            if cancel_requested():
                cancelled = True
            done, pending = wait(in_flight, return_when=FIRST_COMPLETED)
            in_flight = set(pending)
            for future in done:
                result = future.result()
                if result.kind in {"processed", "already"}:
                    processed_count += 1
                    record_progress(
                        f"derivative_generation {result.index} of {total}",
                        processed_count,
                        failed_count,
                    )
                    apply_checkpoint(result.photo_id)
                elif result.kind == "missing":
                    skipped.append({"filename": result.photo_id, "reason": "Registered photo was not found"})
                    failed_count += 1
                    record_progress(f"photo_missing {result.index} of {total}", processed_count, failed_count)
                else:
                    skipped.append(
                        {
                            "filename": result.filename or result.photo_id,
                            "reason": result.reason or "Import derivative generation failed",
                        }
                    )
                    failed_count += 1
                    record_progress(f"file_failed {result.index} of {total}", processed_count, failed_count)
            if not cancelled and cancel_requested():
                cancelled = True
            if not cancelled:
                submit_available()

    if cancelled or cancel_requested():
        _cancel_import_job(session, job, processed_count, failed_count)
        return
    complete_import_job(session, job, processed_count, skipped)


def run_import_derivative_job(
    job_id: str,
    photo_ids: list[str],
    initial_skipped: list[dict[str, str]] | None = None,
    *,
    worker_id: str | None = None,
) -> None:
    import_workers = load_import_workers()
    skipped = list(initial_skipped or [])
    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        if job is None:
            return
        # Atomic claim: refuse to run if another executor (e.g. a separately running
        # ``python -m app.worker`` racing the API's own reclaim thread) already holds
        # this job's lease, so the same job never runs twice at once (#104 fix 2).
        # Callers that already claimed this job (prepare_*_for_reclaim) pass their
        # existing ``worker_id`` explicitly; do not fall back to the job's current lease
        # owner, or an unrelated caller could silently "inherit" a foreign lease.
        owner = worker_id or f"job-runner-{uuid.uuid4().hex[:12]}"
        if not claim_job_atomic(
            session,
            job_id,
            worker_id=owner,
            from_statuses=frozenset({"queued", "running"}),
        ):
            return
        session.refresh(job)
        try:
            project = session.get(Project, job.project_id)
            if project is None:
                _fail_import_job(session, job, "Project not found")
                return

            processed_count = 0
            failed_count = len(skipped)
            update_import_job(
                session,
                job,
                "derivative_generation",
                processed_count,
                failed_count,
                force=True,
            )
            if _import_job_cancellation_requested(session, job):
                _cancel_import_job(session, job, processed_count, failed_count)
                return

            if import_workers > 1:
                _run_import_derivatives_parallel(
                    session,
                    job,
                    project,
                    photo_ids,
                    skipped,
                    processed_count,
                    failed_count,
                    import_workers,
                )
                return

            for index, photo_id in enumerate(photo_ids, start=1):
                if _import_job_cancellation_requested(session, job):
                    _cancel_import_job(session, job, processed_count, failed_count)
                    return
                photo = session.get(Photo, photo_id)
                if photo is None or photo.project_id != project.id:
                    skipped.append({"filename": photo_id, "reason": "Registered photo was not found"})
                    failed_count += 1
                    update_import_job(
                        session,
                        job,
                        f"photo_missing {index} of {len(photo_ids)}",
                        processed_count,
                        failed_count,
                        force=True,
                    )
                    continue
                if _photo_derivatives_exist(photo):
                    photo.processing_state = "imported"
                    photo.processing_error = None
                    photo.recommendation_explanation = "Import derivatives are available."
                    photo.updated_at = utc_now()
                    session.add(photo)
                    session.commit()
                    processed_count += 1
                    update_import_job(
                        session,
                        job,
                        f"derivative_generation {index} of {len(photo_ids)}",
                        processed_count,
                        failed_count,
                        force=True,
                    )
                    apply_job_checkpoint(
                        session,
                        job,
                        photo_id=photo.id,
                        stage="derivative_generation",
                    )
                    if _import_job_cancellation_requested(session, job):
                        _cancel_import_job(session, job, processed_count, failed_count)
                        return
                    continue

                def progress_callback(
                    stage: str,
                    current_index: int = index,
                    current_processed_count: int = processed_count,
                    current_failed_count: int = failed_count,
                ) -> None:
                    update_import_job(
                        session,
                        job,
                        f"{stage} {current_index} of {len(photo_ids)}",
                        current_processed_count,
                        current_failed_count,
                    )

                try:
                    process_registered_import_photo(session, project, photo, progress_callback=progress_callback)
                    processed_count += 1
                    update_import_job(
                        session,
                        job,
                        f"derivative_generation {index} of {len(photo_ids)}",
                        processed_count,
                        failed_count,
                        force=True,
                    )
                    apply_job_checkpoint(
                        session,
                        job,
                        photo_id=photo.id,
                        stage="derivative_generation",
                    )
                    if _import_job_cancellation_requested(session, job):
                        _cancel_import_job(session, job, processed_count, failed_count)
                        return
                except ValueError as error:
                    _mark_import_photo_failed(session, photo, str(error))
                    skipped.append({"filename": photo.filename, "reason": str(error)})
                    failed_count += 1
                    update_import_job(
                        session,
                        job,
                        f"file_failed {index} of {len(photo_ids)}",
                        processed_count,
                        failed_count,
                        force=True,
                    )
                    if _import_job_cancellation_requested(session, job):
                        _cancel_import_job(session, job, processed_count, failed_count)
                        return

            complete_import_job(session, job, processed_count, skipped)
        except Exception as error:
            session.rollback()
            job = session.get(ProcessingJob, job_id)
            if job is None or job.status in TERMINAL_JOB_STATUSES:
                return
            reason = f"Import derivative worker crashed: {error}"
            _reset_import_photos_after_crash(session, photo_ids, reason)
            mark_job_failed(session, job, reason)
