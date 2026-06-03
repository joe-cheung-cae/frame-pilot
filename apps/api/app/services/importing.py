import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import numpy as np
from PIL import ExifTags, Image, ImageOps, UnidentifiedImageError
from sqlmodel import Session, select

from app.ai.embeddings import image_embedding
from app.image.scoring import compute_quality_scores
from app.models.entities import Photo, PhotoGroup, Project, utc_now

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
CONTENT_HASH_CHUNK_SIZE = 1024 * 1024


def is_supported_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


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
        "focal_length": str(named.get("FocalLength")) if named.get("FocalLength") else None,
        "aperture": str(named.get("FNumber")) if named.get("FNumber") else None,
        "shutter_speed": str(named.get("ExposureTime")) if named.get("ExposureTime") else None,
        "iso": int(named["ISOSpeedRatings"]) if isinstance(named.get("ISOSpeedRatings"), int) else None,
    }


def _save_derivatives(project_root: Path, source: Path, image: Image.Image) -> tuple[Path, Path]:
    thumbnail_dir = project_root / "thumbnails"
    preview_dir = project_root / "previews"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    thumbnail_path = _unique_path(thumbnail_dir, f"{source.stem}.webp")
    preview_path = _unique_path(preview_dir, f"{source.stem}.webp")

    thumb = image.copy()
    thumb.thumbnail((320, 320))
    thumb.save(thumbnail_path, "WEBP", quality=82)

    preview = image.copy()
    preview.thumbnail((1800, 1800))
    preview.save(preview_path, "WEBP", quality=88)
    return thumbnail_path, preview_path


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


def _invalidate_project_processing(session: Session, project: Project) -> None:
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


def import_image_file(session: Session, project: Project, filename: str, file: BinaryIO) -> Photo:
    if not is_supported_image(filename):
        raise ValueError("Only JPEG, PNG, and WebP files are supported")

    project_root = Path(project.root_path)
    safe_name = Path(filename).name
    originals_dir = project_root / "originals"
    originals_dir.mkdir(parents=True, exist_ok=True)
    source_path = _unique_path(originals_dir, safe_name)
    with source_path.open("wb") as handle:
        handle.write(file.read())

    thumbnail_path: Path | None = None
    preview_path: Path | None = None
    try:
        with Image.open(source_path) as opened:
            metadata = _extract_metadata(opened)
            image = ImageOps.exif_transpose(opened).convert("RGB")
            width, height = image.size
            thumbnail_path, preview_path = _save_derivatives(project_root, source_path, image)
            scores = compute_quality_scores(np.asarray(image))
            embedding = image_embedding(image)
    except (UnidentifiedImageError, OSError) as error:
        _cleanup_paths(source_path, thumbnail_path, preview_path)
        raise ValueError("Uploaded file could not be opened as a supported image") from error
    except Exception as error:
        _cleanup_paths(source_path, thumbnail_path, preview_path)
        raise ValueError("Uploaded image could not be processed") from error

    source_stat = source_path.stat()
    content_hash = _file_sha256(source_path)

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
    _invalidate_project_processing(session, project)
    project.total_images += 1
    project.updated_at = utc_now()
    session.add(project)
    session.commit()
    session.refresh(photo)
    return photo
