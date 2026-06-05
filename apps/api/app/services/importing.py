import hashlib
import json
import math
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from PIL import ExifTags, Image, ImageOps, UnidentifiedImageError
from sqlmodel import Session, select

from app.ai.embeddings import image_embedding, perceptual_hash
from app.db.session import get_engine
from app.image.scoring import compute_quality_scores_for_image
from app.models.entities import Photo, PhotoGroup, ProcessingJob, Project, utc_now

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PLANNED_HEIC_EXTENSIONS = {".heic", ".heif"}
PLANNED_RAW_EXTENSIONS = {".arw", ".cr3", ".dng", ".nef"}
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
STALE_IMPORT_JOB_AFTER = 30 * 60

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


def _progress_percent(processed_items: int, failed_items: int, total_items: int) -> float:
    if total_items <= 0:
        return 100.0
    return round(min(100.0, ((processed_items + failed_items) / total_items) * 100), 2)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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
        progress_percent=_progress_percent(0, 0, total_items),
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
        progress_percent=_progress_percent(0, 0, len(photo_ids)),
        started_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def update_import_job(
    session: Session,
    job: ProcessingJob,
    current_step: str,
    processed_items: int | None = None,
    failed_items: int | None = None,
    force: bool = False,
) -> None:
    now = utc_now()
    should_commit = force or (now - _as_utc(job.updated_at)).total_seconds() >= IMPORT_JOB_UPDATE_MIN_SECONDS
    job.current_step = current_step
    if processed_items is not None:
        job.processed_items = processed_items
    if failed_items is not None:
        job.failed_items = failed_items
    job.progress_percent = _progress_percent(job.processed_items, job.failed_items, job.total_items)
    job.updated_at = now
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
    job.completed_at = now
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def import_job_is_stale(job: ProcessingJob, now: datetime | None = None) -> bool:
    if job.job_type != "import" or job.status not in {"queued", "running"}:
        return False
    current_time = _as_utc(now or utc_now())
    return (current_time - _as_utc(job.updated_at)).total_seconds() >= STALE_IMPORT_JOB_AFTER


def fail_stale_import_job(session: Session, job: ProcessingJob) -> ProcessingJob:
    now = utc_now()
    reason = "Import job was interrupted before completion"
    job.status = "failed"
    job.current_step = "failed - stale"
    job.error_message = reason
    job.failed_items = max(0, job.total_items - job.processed_items) if job.total_items else 1
    job.progress_percent = _progress_percent(job.processed_items, job.failed_items, job.total_items)
    job.completed_at = now
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
    if extension in PLANNED_HEIC_EXTENSIONS:
        return "HEIC files are not supported yet; import JPEG, PNG, or WebP files for this release"
    if extension in PLANNED_RAW_EXTENSIONS:
        return "RAW files are not supported yet; import JPEG, PNG, or WebP files for this release"
    return "Only JPEG, PNG, and WebP files are supported"


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
    with Image.open(source_path) as opened:
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


def invalidate_project_processing(session: Session, project: Project) -> None:
    for group in session.exec(select(PhotoGroup).where(PhotoGroup.project_id == project.id)).all():
        session.delete(group)

    photos = session.exec(select(Photo).where(Photo.project_id == project.id)).all()
    for photo in photos:
        photo.group_id = None
        photo.ai_recommendation = "Unreviewed"
        photo.recommendation_explanation = "Processing should be run again after the latest import."
        photo.updated_at = utc_now()
        session.add(photo)

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
        source_path = _unique_path(originals_dir, safe_name)
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
                opened_image = Image.open(source_path)
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
                invalidate_project_processing(session, project)
            project.total_images += 1
            project.updated_at = utc_now()
            session.add(project)

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
    source_path = _unique_path(originals_dir, safe_name)
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
        project.total_images += 1
        project.updated_at = utc_now()
        session.add(project)

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
            opened_image = Image.open(source_path)
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
    now = utc_now()
    job.status = "failed"
    job.current_step = "failed"
    job.error_message = reason
    job.failed_items = max(1, job.total_items - job.processed_items)
    job.progress_percent = _progress_percent(job.processed_items, job.failed_items, job.total_items)
    job.completed_at = now
    job.updated_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _mark_import_photo_failed(session: Session, photo: Photo, reason: str) -> None:
    photo.processing_state = "failed"
    photo.processing_error = reason
    photo.recommendation_explanation = "Import derivative generation failed for this photo."
    photo.updated_at = utc_now()
    session.add(photo)
    session.commit()


def run_import_derivative_job(
    job_id: str,
    photo_ids: list[str],
    initial_skipped: list[dict[str, str]] | None = None,
) -> None:
    skipped = list(initial_skipped or [])
    with Session(get_engine()) as session:
        job = session.get(ProcessingJob, job_id)
        if job is None:
            return
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

        for index, photo_id in enumerate(photo_ids, start=1):
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

        complete_import_job(session, job, processed_count, skipped)
