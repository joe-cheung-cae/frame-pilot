import hashlib
import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import numpy as np
from PIL import ExifTags, Image, ImageOps, UnidentifiedImageError
from sqlmodel import Session, select

from app.ai.embeddings import image_embedding, perceptual_hash
from app.image.scoring import compute_quality_scores
from app.models.entities import Photo, PhotoGroup, Project, utc_now

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PLANNED_HEIC_EXTENSIONS = {".heic", ".heif"}
PLANNED_RAW_EXTENSIONS = {".arw", ".cr3", ".dng", ".nef"}
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
CONTENT_HASH_CHUNK_SIZE = 1024 * 1024
IMPORT_COPY_CHUNK_SIZE = 1024 * 1024
PREVIEW_WEBP_METHOD = 2


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
) -> tuple[Path, Path]:
    thumbnail_dir = project_root / "thumbnails"
    preview_dir = project_root / "previews"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    thumbnail_path = _unique_path(thumbnail_dir, f"{source.stem}.webp")
    preview_path = _unique_path(preview_dir, f"{source.stem}.webp")

    with import_timing_stage(timing, "thumbnail_generation"):
        thumb = image.copy()
        thumb.thumbnail((320, 320))
        thumb.save(thumbnail_path, "WEBP", quality=82)

    with import_timing_stage(timing, "preview_generation"):
        preview = image.copy()
        preview.thumbnail((1800, 1800))
        preview.save(preview_path, "WEBP", quality=88, method=PREVIEW_WEBP_METHOD)
    return thumbnail_path, preview_path


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
) -> Photo:
    total_started = time.perf_counter()
    try:
        if not is_supported_image(filename):
            raise ValueError(unsupported_image_reason(filename))

        project_root = Path(project.root_path)
        safe_name = Path(filename).name
        originals_dir = project_root / "originals"
        originals_dir.mkdir(parents=True, exist_ok=True)
        source_path = _unique_path(originals_dir, safe_name)
        with import_timing_stage(timing, "file_copy"):
            _copy_file_to_path(file, source_path)

        thumbnail_path: Path | None = None
        preview_path: Path | None = None
        try:
            with import_timing_stage(timing, "image_open"):
                opened_image = Image.open(source_path)
            with opened_image as opened:
                with import_timing_stage(timing, "metadata_extraction"):
                    metadata = _extract_metadata(opened)
                with import_timing_stage(timing, "image_decode"):
                    image = ImageOps.exif_transpose(opened).convert("RGB")
                width, height = image.size
                thumbnail_path, preview_path = _save_derivatives(project_root, source_path, image, timing=timing)
                with import_timing_stage(timing, "quality_scoring"):
                    scores = compute_quality_scores(np.asarray(image))
                with import_timing_stage(timing, "embedding_generation"):
                    embedding = image_embedding(image)
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
        with import_timing_stage(timing, "content_hash"):
            content_hash = _file_sha256(source_path)

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
