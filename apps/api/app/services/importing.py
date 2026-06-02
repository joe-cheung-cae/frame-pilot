import json
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ExifTags
import numpy as np
from sqlmodel import Session

from app.ai.embeddings import image_embedding
from app.image.scoring import compute_quality_scores
from app.models.entities import Photo, Project, utc_now


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def is_supported_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def _extract_metadata(image: Image.Image) -> dict:
    raw_exif = image.getexif()
    if not raw_exif:
        return {}

    named = {ExifTags.TAGS.get(key, key): value for key, value in raw_exif.items()}
    return {
        "camera_model": named.get("Model"),
        "lens_model": named.get("LensModel"),
        "focal_length": str(named.get("FocalLength")) if named.get("FocalLength") else None,
        "aperture": str(named.get("FNumber")) if named.get("FNumber") else None,
        "shutter_speed": str(named.get("ExposureTime")) if named.get("ExposureTime") else None,
        "iso": int(named["ISOSpeedRatings"]) if isinstance(named.get("ISOSpeedRatings"), int) else None,
    }


def _save_derivatives(project_root: Path, source: Path, image: Image.Image) -> tuple[Path, Path]:
    thumbnail_path = project_root / "thumbnails" / f"{source.stem}.webp"
    preview_path = project_root / "previews" / f"{source.stem}.webp"

    thumb = image.copy()
    thumb.thumbnail((320, 320))
    thumb.save(thumbnail_path, "WEBP", quality=82)

    preview = image.copy()
    preview.thumbnail((1800, 1800))
    preview.save(preview_path, "WEBP", quality=88)
    return thumbnail_path, preview_path


def import_image_file(session: Session, project: Project, filename: str, file: BinaryIO) -> Photo:
    if not is_supported_image(filename):
        raise ValueError("Only JPEG, PNG, and WebP files are supported")

    project_root = Path(project.root_path)
    safe_name = Path(filename).name
    source_path = project_root / "originals" / safe_name
    source_path.parent.mkdir(parents=True, exist_ok=True)
    with source_path.open("wb") as handle:
        handle.write(file.read())

    with Image.open(source_path) as opened:
        image = opened.convert("RGB")
        width, height = image.size
        thumbnail_path, preview_path = _save_derivatives(project_root, source_path, image)
        scores = compute_quality_scores(np.asarray(image))
        metadata = _extract_metadata(opened)
        embedding = image_embedding(image)

    photo = Photo(
        project_id=project.id,
        original_path=str(source_path),
        filename=safe_name,
        file_size=source_path.stat().st_size,
        width=width,
        height=height,
        thumbnail_path=str(thumbnail_path),
        preview_path=str(preview_path),
        sharpness_score=scores.sharpness_score,
        blur_score=scores.blur_score,
        exposure_score=scores.exposure_score,
        contrast_score=scores.contrast_score,
        noise_score=scores.noise_score,
        face_quality_score=scores.face_quality_score,
        aesthetic_score=scores.aesthetic_score,
        overall_score=scores.overall_score,
        embedding=json.dumps(embedding),
        **metadata,
    )
    session.add(photo)
    project.total_images += 1
    project.processed_images += 1
    project.updated_at = utc_now()
    session.add(project)
    session.commit()
    session.refresh(photo)
    return photo

